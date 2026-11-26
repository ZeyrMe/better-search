<div align="center">

# 更好的搜索 · `zeyr.better-search`

**零配即用的多源搜抓引擎：按用途编排能力频道，对模型保密底层搜索引擎名，还支持静默读空气插卡**

![Version](https://img.shields.io/badge/version-0.2.0-brightgreen)
![MaiBot](https://img.shields.io/badge/MaiBot-1.4.8%2B-2f81f7)
![SDK](https://img.shields.io/badge/SDK-2.23.0-0e8a16)
![Standalone](https://img.shields.io/badge/独立运行-支持-blue)

[为什么用它](#为什么用它) · [3 步快速开始](#3-步快速开始) · [配置项说明](#常用配置项说明) · [工具与控制台](#工具接口与控制台) · [FAQ](#常见疑问)

</div>

---

## 为什么用它

| 常见问题 | 单一内置搜索的局限 | **更好的搜索（`zeyr.better-search`）** |
|---|---|---|
| 只有一种源，挂了就瞎 | 某个搜索引擎抽风或限流时直接报空 | 支持在 **`backends` 引擎池**配多源按序故障转移；**不填任何密钥也有免 Key 默认链** |
| 想搜特定圈子/百科站点 | 每次得祈祷模型自己拼对 `site:`，或者为每个垂类单接接口 | 只需在 **能力频道** 填 `sites` 域名列表，自动用现有通用后端拼 `site:` 定向检索 |
| 模型死盯着引擎品牌看 | 模型被内置提示误导以为某引擎不行或暴露真名 | 工具描述与结果里**只看得到能力代号（如 `game / wiki`）**，随时更换引擎零感知 |
| 抓现代网页抓出一堆空壳 | 纯 HTML 解析经常只抓回空白模板 | 支持可选 **Reader 降级（`reader_fallback`）**，全程受公网 IP / SSRF / 字节上限校验 |

---

## 3 步快速开始

### WebUI 上手（推荐）
1. 将 `better-search/` 放入宿主 `plugins/` 并重启（建议在 `model_config.toml` 清空 `[model_task_config.web_search]` 避免与自带搜索工具冲突）。
2. 打开 **更好的搜索** 配置页：不配置密钥已可直接使用；若你有 Tavily / Exa / Brave / 自建 SearXNG 等，点进 **引擎凭证池** 添一条；也可直接勾选 `host_web` 复用宿主原有联网搜索。
3. 在 **搜索能力频道** 添加垂类用途（例如建一条 `game`，写清楚擅长查游戏攻略并填几个 Wiki 域名），然后在顶部控制台点 **一键后端连通检查** 确认绿灯，顺便核对模型实际可见的能力描述。

<details>
<summary>手改 config.toml 示例（附完整注释）</summary>

```toml
enabled = true

[[backends]]
name = "main_search"
kind = "tavily"                                      # duckduckgo | bing | searxng | brave | exa | tavily | json | host_web
api_key = "YOUR_API_KEY"                             # 密钥仅保存于本地运行配置，勿提交仓库

[[channels]]
name = "general"
desc = "查网页资料、百科知识与近期动态"
auto_attach = false
backends = ["main_search"]                           # 留空自动使用上面通用或免 Key 默认源

[[channels]]
name = "game"
desc = "查游戏攻略、角色机制与官方公告"              # 切忌出现引擎品牌名
auto_attach = false                                  # 由模型按需点选
sites = ["wiki.biligame.com", "zh.moegirl.org.cn"]   # 只填域名即可，自动复用通用后端拼 site: 检索

[[channels]]
name = "wiki"
desc = "查词条与客观百科解释"
auto_attach = true                                   # 平时一般搜索时自动并发顺带查一遍
sites = ["zh.wikipedia.org"]
```

</details>

---

## 常用配置项说明

| 配置项 | 默认值 | 怎么填与效果说明 |
|---|---|---|
| `channels` | `[general]` | 能力频道列表；`auto_attach` 开启会在通用搜索时并发附带查；支持预设 `time_range`、`lang`、`region` |
| `backends` | `[]` | 引擎凭证池，支持 8 种适配器；留空则使用免 Key 默认通用源 |
| `reader_fallback` | 默认关闭 | 高级设置：抓正文少于 `min_chars`（默认 100）时拼接 `url_prefix` 重抓，适合前端动态网页 |
| `passive_peek` | 默认关闭 | 高级设置：可选静默读空气，收到 URL（零模型开销）或新梗话题时异步搜完以 `replyable=False` 插卡入上下文 |
| `timeout_seconds` | `8.0` | 高级设置：单源网络超时秒数，超时自动切换下一个备选后端 |
| `cache_minutes` | `30` | 高级设置：相同查询与网页正文缓存时间（分钟） |

---

## 工具、接口与控制台

| 类别 | 名称 | 说明 |
|---|---|---|
| **对话工具** | `smart_search(query, category, site, time_range)` | 按能力频道、特定站点和时效（`day`/`week`/`month`）检索实时资料 |
| **对话工具** | `smart_fetch(url)` | 抓取并去噪网页正文（经公网 DNS Pinning / 防重绑定 / 禁止跨站携凭据重定向校验） |
| **联动 API** | `query(...)` / `fetch(url)` | 供 `zeyr.mai-insights` 等伙伴插件补全原文 |
| **WebUI 控制台** | `运行状态与生效范围` + 按钮 | 实时预览**暴露给模型的匿名能力描述**、各后端健康度；支持 `一键后端连通检查` 与 `清空搜索与正文缓存` |

---

## 常见疑问

- **Q：不填任何 `backends` 直接启用能搜吗？**
  可以。插件内置 DuckDuckGo HTML 与 Bing HTML 顺序降级；但如果宿主机网络访问外部免 Key 搜索不稳定，建议在 `backends` 里配一个带密钥的源或自建 SearXNG。
- **Q：`time_range` 是不是所有搜索引擎都会严格过滤？**
  Tavily / Brave / Exa 支持透传时效参数，普通通用源会附带通用时间提示，实际精确度以上游支持为准。

<details>
<summary>开发、门禁与安全审计</summary>

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r .github/requirements-ci.txt
.venv/bin/python scripts/check.py
```

</details>
