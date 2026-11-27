# 更好的搜索（better-search）

更自然的搜索，以及更丰富的搜索配置与网页抓取

## 功能介绍

- **免配置开箱即用**：默认自带公开免密钥降级搜索源；配置多后端时按频道设定顺序自动故障转移。
- **按用途划分搜索频道**：只向模型暴露能力频道代号与说明（如 `general`、`game`、`wiki`），不暴露底层搜索引擎名称。
- **站点自动限定与并发**：在频道中配置 `sites` 域名后自动拼接 `site:` 检索；勾选 `auto_attach` 可在通用搜索时自动附带查询。
- **安全网页抓取与可选扩展**：内置公网 IP / DNS / 字节上限校验，支持动态页面 Reader 降级和可选后台自动补充背景信息。

## 如何使用

1. 将 `better-search/` 放入宿主 `plugins/` 目录并重启（建议在 `model_config.toml` 中清空 `web_search` 任务，避免重复）。
2. 在 **搜索频道** 中维护需要的搜索用途与限定网站；若有 Tavily、Exa、Brave 或 SearXNG 等后端，可在 **搜索引擎配置** 中添加。
3. 在顶部控制台点击 **一键后端连通检查** 确认各个后端工作正常。

<details>
<summary>config.toml 配置示例</summary>

```toml
enabled = true

[[backends]]
name = "main_search"
kind = "tavily"                                      # duckduckgo | bing | searxng | brave | exa | tavily | json | host_web
api_key = "YOUR_API_KEY"

[[channels]]
name = "general"
desc = "查网页资料、百科知识与近期动态"
auto_attach = false
backends = ["main_search"]

[[channels]]
name = "game"
desc = "查游戏攻略、角色机制与官方公告"
auto_attach = false
sites = ["wiki.biligame.com", "zh.moegirl.org.cn"]

[[channels]]
name = "wiki"
desc = "查词条与百科解释"
auto_attach = true
sites = ["zh.wikipedia.org"]
```

</details>

## 配置说明

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `channels` | `[general]` | 搜索频道列表，支持指定限定域名、时效、语言、地区和并发开关 |
| `backends` | `[]` | 搜索引擎列表，支持 8 种协议；留空时自动使用免密钥默认源 |
| `reader_fallback` | 默认关闭 | 高级设置：普通抓取正文过短时，拼接 Reader 前缀重新提取正文 |
| `passive_peek` | 默认关闭 | 高级设置：开启后台自动搜索后，可异步抓取链接或陌生词背景写入上下文 |
| `timeout_seconds` | `8.0` | 高级设置：单个搜索源或网页请求超时时间（秒） |
| `cache_minutes` | `30` | 高级设置：搜索结果和网页正文在内存中的缓存时长（分钟） |

## 命令与工具

| 类别 | 名称 | 说明 |
|---|---|---|
| 对话工具 | `smart_search(query, category, site, time_range)` | 按频道、指定站点和时间范围联网搜索资料 |
| 对话工具 | `smart_fetch(url)` | 抓取并提取指定网页的正文内容（带内存缓存） |
| 联动 API | `query(...)` / `fetch(url)` | 供 `mai-insights` 等插件调用检索与原文补全 |
| WebUI 控件 | `一键后端连通检查` / `清空搜索与正文缓存` | 测试各搜索源可用性并查看模型当前可见的频道说明 |

<details>
<summary>开发与自检</summary>

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r .github/requirements-ci.txt
.venv/bin/python scripts/check.py
```

</details>
