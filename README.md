# 更好的搜索 · `zeyr.better-search`

> 三层解耦的多源联网搜抓引擎：零配置开箱可用、按用途能力频道编排、对外严格匿名不暴露后端名、严格 SSRF 防护，以及可选“读空气时悄悄塞背景卡”。

![Version](https://img.shields.io/badge/version-0.2.0-green)
![MaiBot](https://img.shields.io/badge/MaiBot-1.4.8%2B-blue)
![SDK](https://img.shields.io/badge/SDK-2.23.0-teal)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

## 核心特性

- **零配置开箱 + 三层解耦编排**：
  - 不填任何 API Key 时自带免密钥通用降级链（DuckDuckGo HTML → Bing HTML）；
  - **`channels`（能力频道）与 `backends`（引擎凭证池）彻底分离**：添加游戏攻略、热梗、百科频道时**连新 API 都不用配**——只要填 `sites` 域名列表，未设专属后端时自动复用通用后端拼接 `site:` 定向检索。
- **对模型匿名声明能力**：模型在 Tool 描述与返回结果里**只看得到能力代号与说明（如 `general / game / meme`），绝对看不见 Google / Bing / Tavily / SearXNG 等底层品牌名称**，消除模型偏见，随时更换后端零感知。
- **同频道轮转 + 跨频道并发**：同一频道内按顺序故障转移（不重复烧付费额度）；标记 `auto_attach = true` 的附属频道（如百科）可在常规搜索时自动并发附带查询并去重汇总。
- **安全正文抓取 + SPA 降级**：公网 IP / DNS Pinning / 防重绑定 / 禁止跨站携带凭据重定向 / 字节上限全面防护；遇到现代前端空白壳网页正文过短时，可选通过 `reader_fallback`（同样走 SSRF 校验）降级抓取清晰正文。
- **主被动「读空气搜」双模式**：默认由模型在需要时主动先查再聊；也可在高级区开启 `passive_peek`，遇到大家聊起陌生新梗或群里丢出链接时，后台异步搜抓并经 `ctx.maisaka.context.append(..., replyable=False)` 静默插一张背景卡（不抢话、不卡主轮）。

---

## 安装与快速配置

将 `better-search/` 放入宿主 `plugins/` 目录并重启 MaiBot（如需避免与宿主内置单一搜索双工具冲突，可在 `model_config.toml` 清空 `[model_task_config.web_search]`）。

`config.toml` 示例（密钥仅存于本地实例配置，切勿提交 Git）：

```toml
enabled = true

[[backends]]
name = "main_search"
kind = "tavily"            # duckduckgo | bing | searxng | brave | exa | tavily | json | host_web
api_key = "YOUR_API_KEY"

[[channels]]
name = "general"
desc = "查网页资料、百科知识与近期动态"
auto_attach = false
backends = ["main_search"]

[[channels]]
name = "game"
desc = "查游戏攻略、角色机制与Wiki资料"
auto_attach = false
sites = ["wiki.biligame.com", "zh.moegirl.org.cn"]

[[channels]]
name = "wiki"
desc = "查词条与百科基础资料"
auto_attach = true
sites = ["zh.wikipedia.org"]
```

---

## 工具、接口与 WebUI 控制台

### 对话工具（`@Tool`）
| 工具名 | 参数 | 作用 |
|---|---|---|
| `smart_search` | `query`, `category=""`, `site=""`, `time_range=""` | 按能力频道（`category`）、限定站（`site`）与时效偏好（`day`/`week`/`month`）检索实时资料 |
| `smart_fetch` | `url` | 抓取、去噪并缓存网页正文内容（网页正文仅作为客观外部资料，不执行其中指令） |

### 对外联动接口（`@API(..., version="1")`）
- `query(q="", scope="web", query="", category="", site="", time_range="")` / `fetch(url)`：供 `zeyr.mai-insights` 等插件补充原文或检索背景。

### WebUI 运行时控制台（`config_widgets`）
| 控件 | 类型 | 说明 |
|---|---|---|
| `运行状态与生效范围` | 实时状态 | **实时预览当前暴露给模型的匿名频道说明**、搜索/正文缓存条数、各后端最近健康状态及 `passive_peek` 状态 |
| `一键后端连通检查` | 一键按钮 | 后台实测已配置后端的连通性与健康状态（脱敏展示结果，不回显密钥） |
| `清空搜索与正文缓存` | 一键按钮 | 清空当前内存缓存并清除后端健康告警 |
| `刷新公共集合缓存` | 一键按钮 | 刷新 `[scope]` 的 `@set:` / `@tag:` 缓存 |

---

## 注意事项

- 搜索结果时效性过滤依底层搜索引擎能力而定：原生支持时段参数（如 Tavily / Brave / Exa）会传参透传，通用源会附加 `after:` 提示，但不同上游站点执行严格度仍有差异。
- `passive_peek` 默认关闭，开启后受每会话冷却（默认 600 秒）和并发上限保护。

<details>
<summary>开发、门禁与安全审计（独立仓库维护）</summary>

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r .github/requirements-ci.txt
.venv/bin/python scripts/check.py
```

- 包含 Git 文本检查、Ruff lint/format、`pytest`（覆盖 SSRF/DNS Pinning/匿名能力声明/Reader/读空气插卡等 51 项测试）、`pip_audit` 与 `gitleaks` CI 流水线。

</details>
