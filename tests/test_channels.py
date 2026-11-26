from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from conftest import module


@pytest.mark.parametrize("period", ["", "any", "day", "week", "month"])
async def test_channel_time_range_legacy_config_roundtrip_and_backend_value(period):
    p = module.Plugin()
    original = {
        "plugin": {"config_version": "0.1.0"},
        "channels": [{"name": "general", "time_range": period}],
    }
    p.set_plugin_config(original)
    stored = p.get_plugin_config_data()
    assert stored["channels"][0]["time_range"] == (period or "any")
    assert original["channels"][0]["time_range"] == period
    p.set_plugin_config(stored)
    p.search_backend = AsyncMock(return_value={"results": [], "degraded": False, "errors": []})
    await p.search("test")
    expected = "" if period in ("", "any") else period
    assert p.search_backend.await_args.kwargs["time_range"] == expected
    assert (" after:" in p.search_backend.await_args.args[0]) == bool(expected)
    await p.search("test", time_range="day")
    assert p.search_backend.await_args.kwargs["time_range"] == "day"


async def test_channel_fanout_directed_query_and_anonymous_results():
    p = module.Plugin()
    p.set_plugin_config(
        {
            "plugin": {"config_version": "0.1.0"},
            "channels": [
                {"name": "general", "desc": "普通资料"},
                {"name": "game", "desc": "游戏资料", "sites": ["game.example"], "auto_attach": True},
            ],
        }
    )
    p.search_backend = AsyncMock(
        return_value={
            "results": [{"url": "https://game.example/a", "source": "SECRET_BACKEND", "title": "x"}],
            "degraded": True,
            "errors": ["SECRET_BACKEND: failed"],
        }
    )
    value = await p.search("游戏")
    assert p.search_backend.await_count == 2
    assert "site:game.example" in p.search_backend.await_args_list[1].args[0]
    assert "SECRET_BACKEND" not in str(value)
    assert len(value["results"]) == 1
    assert "game：游戏资料" in p.capability_description()


async def test_reader_fallback_reuses_guarded_request_and_no_recursive_fetch():
    p = module.Plugin()
    p.set_plugin_config(
        {
            "plugin": {"config_version": "0.1.0"},
            "reader_fallback": {"enabled": True, "url_prefix": "https://reader.example/", "min_chars": 100},
        }
    )
    p.request = AsyncMock(
        side_effect=[
            (b"<html>shell</html>", "utf-8", "text/html"),
            (b"readable article", "utf-8", "text/plain"),
        ]
    )
    value = await p.fetch("https://page.example/a")
    assert value["text"] == "readable article"
    assert p.request.await_args_list[1].args[0] == "https://reader.example/https://page.example/a"


async def test_background_peek_appends_context_without_sending():
    p = module.Plugin()
    p.set_plugin_config({"plugin": {"config_version": "0.1.0"}, "passive_peek": {"enabled": True}})
    p.fetch = AsyncMock(return_value={"text": "客观背景"})
    p._set_context(
        SimpleNamespace(
            maisaka=SimpleNamespace(context=SimpleNamespace(append=AsyncMock(return_value={"success": True})))
        )
    )
    await p.peek({"session_id": "s", "processed_plain_text": "https://news.example/a"}, "s")
    assert p.ctx.maisaka.context.append.await_args.kwargs["replyable"] is False
    assert p.ctx.maisaka.context.append.await_args.kwargs["source_kind"] == "search_peek"


async def test_channel_language_region_and_period_reach_supported_backend():
    p = module.Plugin()
    p.set_plugin_config(
        {
            "plugin": {"config_version": "0.1.0"},
            "channels": [{"name": "general", "lang": "zh", "region": "CN", "time_range": "week"}],
            "backends": [
                {
                    "name": "credential-slot",
                    "kind": "brave",
                    "endpoint": "https://search.example/query?q={query}",
                }
            ],
        }
    )
    p.request = AsyncMock(
        return_value=(
            b'{"results":[{"url":"https://news.example/a","title":"x"}]}',
            "utf-8",
            "application/json",
        )
    )
    value = await p.search("test")
    url = p.request.await_args.args[0]
    assert "search_lang=zh" in url and "country=CN" in url and "freshness=pw" in url
    assert value["results"][0]["source"] == "general"
