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
    plugin.config.sources = [
        module.config_models.SearchSource(name="local", kind="json", endpoint="https://x.test?q={query}")
    ]
    calls = []

    def fake_fetch(url, timeout):
        calls.append(url)
        return b'{"results":[{"title":"A","url":"https://example.com/a"}]}', "utf-8", "application/json"

    monkeypatch.setattr(module, "fetch_url", fake_fetch)
    first = await plugin.search("hello")
    second = await plugin.search("hello")
    assert first["results"][0]["title"] == "A"
    assert second == first
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_fetch_rejects_non_http(plugin):
    result = await plugin.fetch("file:///etc/passwd")
    assert not result["success"]
