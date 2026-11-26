# 更好的搜索

`zeyr.better-search` · 多引擎搜索与正文抓取。

开发基线 MaiBot 1.4.8 / SDK 2.23.0。可独立安装，其他 zeyr 插件仅通过公开 API 自动联动。

第三批已实现：配置驱动的 DuckDuckGo/Bing/JSON/可配置 API 源、scope 路由、失败降级、偏好域名排序、结果和正文缓存、URL 规范化、响应大小限制、正文抓取和脚本/导航去噪，提供 `query` / `fetch` API 及 `smart_search` / `smart_fetch` 工具。默认不主动注入聊天；搜索源为空时只在工具被调用时访问默认搜索地址。

安装时将整个目录同步到宿主 plugins；运行 config.toml 由 SDK 生成。实例名单、个人资料和密钥只填运行配置，不提交。

检查：`python -m pytest`，开发依赖见 pyproject.toml。
