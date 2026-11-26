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
