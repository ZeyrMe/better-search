import pytest
from conftest import module


@pytest.fixture
def plugin():
    instance = module.Plugin()
    instance.set_plugin_config({"plugin": {"config_version": "0.1.0"}})
    return instance


def test_clean_text_removes_script_and_navigation():
    assert (
        module.clean_text("<nav>menu</nav><main>Hello <b>world</b></main><script>x()</script>")
        == "Hello world"
    )


@pytest.mark.asyncio
async def test_json_source_fallback_and_cache(plugin, monkeypatch):
    from test_better_search.config_models import SearchSource

    plugin.config.sources = [SearchSource(name="local", kind="json", endpoint="https://x.test?q={query}")]
    calls = []

    async def fake_request(url, *, headers=None, payload=None):
        calls.append(url)
        return b'{"results":[{"title":"A","url":"https://example.com/a"}]}', "utf-8", "application/json"

    monkeypatch.setattr(plugin, "request", fake_request)
    first = await plugin.search("hello")
    second = await plugin.search("hello")
    assert first["results"][0]["title"] == "A"
    assert second == first
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_fetch_rejects_non_http(plugin):
    result = await plugin.fetch("file:///etc/passwd")
    assert not result["success"]


def test_canonical_url_drops_tracking_query():
    assert (
        module.canonical_url("https://Example.com/a?utm_source=x&keep=1#fragment")
        == "https://Example.com/a?keep=1"
    )


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost/",
        "http://127.0.0.1/",
        "http://10.2.3.4/",
        "http://172.16.1.1/",
        "http://192.168.1.1/",
        "http://169.254.169.254/",
        "http://[::1]/",
        "http://[fe80::1]/",
        "http://[fc00::1]/",
        "http://[::ffff:127.0.0.1]/",
        "http://224.0.0.1/",
        "http://router.local/",
        "http://localhost./",
        "http://user:pass@example.com/",
        "http://intranet/",
    ],
)
def test_canonical_url_rejects_non_public_destinations(url):
    with pytest.raises(ValueError):
        module.canonical_url(url)


@pytest.mark.asyncio
async def test_dns_private_address_is_rejected_before_connection(plugin, monkeypatch):
    import socket

    monkeypatch.setattr(
        module.socket,
        "getaddrinfo",
        lambda *a, **k: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.168.1.1", 80))],
    )
    response = await plugin.fetch("http://public.example/")
    assert not response["success"]
    assert "非公网" in response["error"]


@pytest.mark.asyncio
async def test_public_dns_is_pinned_and_redirect_to_private_is_rejected(plugin, monkeypatch):
    import socket

    import httpx

    calls = []
    monkeypatch.setattr(
        module.socket,
        "getaddrinfo",
        lambda *a, **k: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.215.14", 443))],
    )

    def handler(request):
        calls.append(request)
        return httpx.Response(302, headers={"location": "http://127.0.0.1/admin"})

    plugin.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        result = await plugin.fetch("https://public.example/")
    finally:
        await plugin.on_unload()
    assert not result["success"]
    assert len(calls) == 1
    assert calls[0].url.host == "93.184.215.14"
    assert calls[0].headers["host"] == "public.example"
    assert calls[0].extensions["sni_hostname"] == "public.example"


@pytest.mark.asyncio
async def test_every_redirect_resolves_and_validates_dns(plugin, monkeypatch):
    import socket

    import httpx

    seen = []

    def resolve(host, *args, **kwargs):
        seen.append(host)
        return [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                6,
                "",
                ("93.184.215.14" if host == "public.example" else "10.0.0.1", 443),
            )
        ]

    monkeypatch.setattr(module.socket, "getaddrinfo", resolve)
    plugin.client = httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(302, headers={"location": "https://rebind.example/"})
        )
    )
    try:
        result = await plugin.fetch("https://public.example/")
    finally:
        await plugin.on_unload()
    assert not result["success"]
    assert seen == ["public.example", "rebind.example"]


@pytest.mark.asyncio
async def test_tavily_adapter_uses_json_post(plugin, monkeypatch):
    from test_better_search.config_models import SearchSource

    plugin.config.sources = [
        SearchSource(
            name="tavily", kind="tavily", endpoint="https://api.tavily.com/search", api_key="instance-key"
        )
    ]
    calls = []

    async def request(url, *, headers=None, payload=None):
        calls.append(payload)
        return (
            b'{"results":[{"title":"A","url":"https://example.com/a","content":"summary"}]}',
            "utf-8",
            "application/json",
        )

    monkeypatch.setattr(plugin, "request", request)
    result = await plugin.search("hello")
    assert result["available"]
    assert calls == [{"api_key": "instance-key", "query": "hello", "max_results": 5}]
    assert result["results"][0]["snippet"] == "summary"


@pytest.mark.asyncio
@pytest.mark.parametrize("location", ["http://public.example/search", "https://other.example/search"])
async def test_api_credentials_do_not_follow_scheme_or_origin_changes(plugin, monkeypatch, location):
    import socket

    import httpx

    calls = []
    monkeypatch.setattr(
        module.socket,
        "getaddrinfo",
        lambda *a, **k: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.215.14", 443))],
    )

    def handler(request):
        calls.append(request)
        return httpx.Response(307, headers={"location": location})

    plugin.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(ValueError, match="凭据"):
            await plugin.request("https://public.example/search", payload={"api_key": "instance-key"})
    finally:
        await plugin.on_unload()
    assert len(calls) == 1
    assert calls[0].headers["connection"] == "close"


def test_legacy_domain_and_header_config_survives_sdk_normalization():
    plugin = module.Plugin()
    plugin.set_plugin_config(
        {
            "plugin": {"config_version": "0.1.0"},
            "scope_domains": {"wiki": ["wiki.example"]},
            "sources": [{"name": "test", "headers": {"X-Test": "opaque"}}],
        }
    )
    stored = plugin.get_plugin_config_data()
    assert "scope_domains" not in stored
    assert stored["domain_routes"] == [{"scope": "wiki", "domains": ["wiki.example"]}]
    assert stored["sources"][0]["headers"] == [{"name": "X-Test", "value": "opaque"}]
    plugin.set_plugin_config(stored)
    assert plugin.config.scope_domains["wiki"] == ["wiki.example"]
