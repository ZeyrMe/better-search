# 更新日志 · 更好的搜索 (`zeyr.better-search`)

本日志遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 规范。

## [0.2.0] - 2026-11-27

### 新增
- **三层剥洋葱能力编排**：分离 `channels`（能力频道）与 `backends`（引擎凭证池），支持同频道顺序故障切换、`auto_attach` 跨频道并发附带以及零额外 API 的 `sites` 自动 `site:` 定向拼装。
- **对模型严格匿名**：动态生成的工具描述、搜索结果与报错信息仅保留能力代号，全面移除底层引擎品牌名，同时保留 `host_web` 复用宿主搜索协议。
- **高频定向与正文降级**：`smart_search` 支持 `query` / `category` / `site` / `time_range` 与语言/地区偏好透传（兼容旧 `scope` 与 `q`）；新增可选 `reader_fallback`（同样受公网 SSRF/字节上限校验）。
- **可选静默读空气（`passive_peek`）**：支持在检测到 URL 或新梗话题时后台异步搜抓并写入不可回复上下文卡片。
- **独立范围 `[scope]` 与 WebUI 控制台**：新增匿名能力预览面板、一键后端连通检查与清空缓存按钮。

### 优化
- **WebUI 表单大幅精简**：隐藏旧版 `sources` / `preferred_domains` / `domain_routes` / `default_sources` 及内部缓存保护字段；`scope_domains` 与 `headers` 自动从旧字典格式无缝迁移并补齐中文短标题；润色 `Channel.desc` 与 `passive_peek` 判定提示词。

### 修复
- 下拉时效默认选项统一改用非空 `any`，兼容迁移旧配置中的空字符串值。

## [0.1.0] - 2026-11-26

### 新增
- 初始开发版本：多源降级搜索、公网 DNS Pinning / SSRF 网页正文抓取、LRU 缓存与 `query`/`fetch` API。
