from typing import Literal

from maibot_sdk import Field, PluginConfigBase
from pydantic import field_validator, model_validator

from .ecosystem import ScopeConfig


class Header(PluginConfigBase):
    name: str = Field(
        default="",
        description="HTTP 请求头名称。",
        json_schema_extra={
            "label": "请求头名",
            "placeholder": "写请求头字段名，如 X-API-Key 或 Authorization",
        },
    )
    value: str = Field(
        default="",
        description="请求头内容；密钥只保存在本地实例里。",
        json_schema_extra={
            "label": "请求头值",
            "input_type": "password",
            "placeholder": "填对应的密钥或 Token（仅存本地）",
        },
    )


class DomainRoute(PluginConfigBase):
    scope: str = Field(default="web", description="搜索能力范围名", json_schema_extra={"label": "范围名"})
    domains: list[str] = Field(
        default_factory=list, description="偏好域名", json_schema_extra={"label": "偏好域名"}
    )


class SearchSource(PluginConfigBase):
    name: str = Field(
        default="",
        description="后端代号，方便能力频道按名字引用。",
        json_schema_extra={
            "label": "后端代号",
            "placeholder": "取个简短英文字母代号（模型看不到），如 main_tavily",
        },
    )
    kind: Literal["duckduckgo", "bing", "json", "searxng", "brave", "exa", "tavily", "host_web"] = Field(
        default="json",
        description="接入协议类型。",
        json_schema_extra={
            "label": "接口类型",
            "enum_labels": {
                "tavily": "tavily（填 api_key 即可，中文事实检索稳）",
                "exa": "exa（填 api_key，语义搜索友好）",
                "brave": "brave（填 api_key）",
                "searxng": "searxng（填自建 SearXNG 接口地址）",
                "host_web": "host_web（直接复用宿主内置联网搜索）",
                "duckduckgo": "duckduckgo（免密钥 HTML 抓取）",
                "bing": "bing（免密钥 HTML 抓取）",
                "json": "json（自定义 JSON 接口模板）",
            },
        },
    )
    endpoint: str = Field(
        default="",
        description="搜索接口地址模板，支持 {query} 占位。",
        json_schema_extra={
            "label": "接口地址",
            "placeholder": "tavily/exa/brave/host_web 可留空；searxng/json 填 https://域名/search?q={query}",
        },
    )
    api_key: str = Field(
        default="",
        description="API 密钥（仅存在本地 config.toml）。",
        json_schema_extra={
            "label": "API 密钥",
            "input_type": "password",
            "placeholder": "需要密钥的类型填这里；免密钥/host_web 留空",
        },
    )
    headers: list[Header] = Field(
        default_factory=list,
        description="需要额外携带的请求头。",
        json_schema_extra={"label": "附加请求头"},
    )

    @field_validator("headers", mode="before")
    @classmethod
    def legacy_headers(cls, value):
        return (
            [{"name": name, "value": text} for name, text in value.items()]
            if isinstance(value, dict)
            else value
        )

    domains: list[str] = Field(
        default_factory=list,
        description="该后端优先照顾的网站域名。",
        json_schema_extra={"label": "优先域名", "hidden": True},
    )
    scopes: list[str] = Field(
        default_factory=list,
        description="限定适用的范围，留空表示全部可用。",
        json_schema_extra={"label": "适用范围", "hidden": True},
    )
    enabled: bool = Field(
        default=True,
        description="是否启用这个搜索后端。",
        json_schema_extra={"label": "启用"},
    )


class Channel(PluginConfigBase):
    name: str = Field(
        default="general",
        description="对外暴露的能力代号（比如 general、game、meme、wiki）。",
        json_schema_extra={
            "label": "频道代号",
            "placeholder": "写能力用途英文短名，如 general、game、meme、wiki",
        },
    )
    desc: str = Field(
        default="查网页资料、百科知识与近期动态",
        description="告诉模型这个频道擅长查什么，绝对不要写谷歌/必应/Tavily 等品牌名。",
        json_schema_extra={
            "label": "能力说明",
            "placeholder": "向模型介绍该能力用途，如：查游戏攻略、角色机制与官方公告",
        },
    )
    auto_attach: bool = Field(
        default=False,
        description="打开后，每次常规搜索都会自动顺带把这路频道一起查了。",
        json_schema_extra={"label": "默认顺带查"},
    )
    sites: list[str] = Field(
        default_factory=list,
        description="只填域名就能自动按 site: 定向搜索，无需单配 API。",
        json_schema_extra={
            "label": "限定网站",
            "placeholder": "填网站域名即可限定站内搜索，如 wiki.biligame.com；不限则留空",
        },
    )
    backends: list[str] = Field(
        default_factory=list,
        description="按优先顺序填引擎凭证池里的后端代号；留空自动复用通用后端。",
        json_schema_extra={
            "label": "指定后端",
            "placeholder": "填下方引擎池里的后端代号（按故障切换顺序）；留空自动复用默认后端",
        },
    )
    time_range: Literal["any", "day", "week", "month"] = Field(
        default="any",
        description="偏好的信息新旧范围。",
        json_schema_extra={
            "label": "时效偏好",
            "enum_labels": {
                "any": "any（不限时间）",
                "day": "day（尽量查一天内新内容）",
                "week": "week（近一周内）",
                "month": "month（近一月内）",
            },
        },
    )
    lang: str = Field(
        default="",
        description="偏好搜索语言代码，如 zh 或 en。",
        json_schema_extra={"label": "偏好语言", "placeholder": "选填语言代码，如 zh、en、ja；留空不限制"},
    )
    region: str = Field(
        default="",
        description="偏好地区代码，如 cn 或 jp。",
        json_schema_extra={"label": "偏好地区", "placeholder": "选填地区代码，如 cn、us、jp；留空不限制"},
    )


class ReaderConfig(PluginConfigBase):
    """普通抓取拿到的正文较少时（例如前端动态渲染页面），可改用外部 Reader 服务提取正文。所有请求均受公网地址与容量限制保护。"""

    __ui_label__ = "网页正文提取"
    enabled: bool = Field(
        default=False,
        description="普通抓取正文少于阈值字数时，改用 Reader 服务重抓。",
        json_schema_extra={
            "label": "启用正文提取",
            "order": 1,
            "hint": "默认关闭；经常抓取到空白动态页面时可开启。",
        },
    )
    url_prefix: str = Field(
        default="",
        description="Reader 转换接口前缀，会把目标网页链接直接拼在末尾。",
        json_schema_extra={
            "label": "Reader 前缀",
            "order": 2,
            "placeholder": "填写 Reader 服务地址前缀，如 https://r.jina.ai/",
            "hint": "开启后必填，必须是公网 http/https 地址；程序会在原 URL 前直接拼上该前缀抓取。",
        },
    )
    min_chars: int = Field(
        default=100,
        ge=0,
        le=2000,
        description="普通抓取拿回来的正文少于多少字时触发降级重抓。",
        json_schema_extra={
            "label": "触发降级字数",
            "order": 3,
            "hint": "单位：字数（默认 100）。正常新闻或词条通常远超 100 字，只有前端空壳页面才会低于该阈值。",
        },
    )


class PeekConfig(PluginConfigBase):
    """收到网页链接或聊天提及陌生词时，异步在后台抓取或搜索背景资料写入上下文，不打断正常对话。"""

    __ui_label__ = "后台自动搜索"
    enabled: bool = Field(
        default=False,
        description="开启后根据聊天内容自动在后台搜索或抓取背景资料写入上下文。",
        json_schema_extra={
            "label": "启用后台搜索",
            "order": 1,
            "hint": "默认关闭（通常由模型按需调用 smart_search 即可）；需要提前补充链接或新词背景时开启。",
        },
    )
    trigger: Literal["url", "unknown_term"] = Field(
        default="url",
        description="决定什么情况触发后台自动搜索。",
        json_schema_extra={
            "label": "触发方式",
            "order": 2,
            "enum_labels": {
                "url": "url（仅在消息包含 HTTP 链接时抓取标题和正文）",
                "unknown_term": "unknown_term（由小模型判断消息中是否有需要查背景的新词）",
            },
            "hint": "url 模式不消耗模型额度；unknown_term 会调用指定小模型判断是否值得搜索。",
        },
    )
    model_task: str = Field(
        default="",
        description="用于判断该不该后台搜的小模型任务名，留空用宿主默认模型。",
        json_schema_extra={
            "label": "判断模型任务",
            "order": 3,
            "placeholder": "写 model_config.toml 里的任务名（如 utils）；留空沿用宿主默认模型",
            "hint": "建议填轻量低价模型任务（如 flash / utils），只在 trigger=unknown_term 时调用。",
        },
    )
    cooldown_seconds: float = Field(
        default=600,
        ge=1,
        le=86400,
        description="同一个会话间隔多少秒才允许再次后台自动搜索。",
        json_schema_extra={
            "label": "单聊冷却秒数",
            "order": 4,
            "hint": "单位：秒（默认 600 秒 = 10 分钟），防止群友连发链接或刷屏时反复触发后台查询。",
        },
    )
    max_chars: int = Field(
        default=500,
        ge=50,
        le=2000,
        description="塞进聊天上下文里的背景卡片最多保留多少字。",
        json_schema_extra={
            "label": "卡片字数上限",
            "order": 5,
            "hint": "单位：字数（默认 500）。卡片以只读客观背景注入且不可直接回复。",
        },
    )
    max_pending: int = Field(
        default=4,
        ge=1,
        le=32,
        description="最多同时后台任务",
        json_schema_extra={"label": "后台并发上限", "hidden": True},
    )
    timeout_seconds: float = Field(
        default=45,
        ge=1,
        le=120,
        description="后台任务超时",
        json_schema_extra={"label": "后台超时秒数", "hidden": True},
    )
    instruction: str = Field(
        default='看看这段对话里有没有提到大家可能不太熟的新梗、刚出的作品或具体新闻。需要查一下背景就返回 JSON {"query":"搜索词"}，不需要就返回 {"query":""}。对话：',
        description="让轻量模型判断是否值得后台查背景的提示语。",
        json_schema_extra={
            "label": "判断提示词",
            "order": 6,
            "hint": "必须要求返回含 query 字段的 JSON，空字符串代表不用查。",
        },
    )


class PluginInfo(PluginConfigBase):
    config_version: str = Field(default="0.1.0", description="配置版本，由 Runner 管理")


class Config(PluginConfigBase):
    scope: ScopeConfig = Field(default_factory=ScopeConfig, description="独立控制哪些群或人允许用搜索")
    show_advanced: bool = Field(
        default=False,
        description="展开网页正文提取、后台自动搜索与缓存超时等高阶选项。",
        json_schema_extra={
            "label": "显示高级设置",
            "order": 9,
            "hint": "不配搜索引擎也可使用免密钥默认源直接搜索；需要调超时、缓存或开启网页提取/后台搜索时再展开。",
        },
    )
    plugin: PluginInfo = Field(default_factory=PluginInfo)
    enabled: bool = Field(
        default=True,
        description="开启后可使用多源联网搜索与网页正文抓取。",
        json_schema_extra={
            "label": "启用搜索",
            "order": 1,
            "hint": "为避免与宿主自带搜索工具重复，切换使用本插件时建议清空 model_config.toml 中的 web_search 任务。",
        },
    )
    channels: list[Channel] = Field(
        default_factory=lambda: [Channel()],
        description="按用途分类配置搜索频道；模型只看到频道代号与说明。",
        json_schema_extra={
            "label": "搜索频道",
            "order": 2,
            "hint": "新建垂直频道（如 game、wiki）并填写限定网站后，会自动使用通用后端拼接 site: 检索；勾选默认顺带查则在常规搜索时并发查询。",
        },
    )
    backends: list[SearchSource] = Field(
        default_factory=list,
        description="集中配置搜索接口与密钥，各频道按代号复用；留空则使用默认免密钥搜索。",
        json_schema_extra={
            "label": "搜索引擎配置",
            "order": 3,
            "hint": "留空也可直接使用；推荐配置稳定的后端（如 tavily / searxng / host_web）并在控制台测试连通性。",
        },
    )
    reader_fallback: ReaderConfig = Field(default_factory=ReaderConfig)
    passive_peek: PeekConfig = Field(default_factory=PeekConfig)
    sources: list[SearchSource] = Field(
        default_factory=list,
        description="旧版搜索源兼容字段。",
        json_schema_extra={"label": "兼容旧搜索源", "hidden": True},
    )
    preferred_domains: list[str] = Field(
        default_factory=list,
        description="旧版偏好站点兼容字段。",
        json_schema_extra={"label": "兼容旧站点", "hidden": True},
    )
    domain_routes: list[DomainRoute] = Field(
        default_factory=list,
        description="旧版能力范围与偏好站点条目兼容字段。",
        json_schema_extra={"label": "兼容旧路由", "hidden": True},
    )
    timeout_seconds: float = Field(
        default=8.0,
        ge=1,
        le=30,
        description="单个搜索引擎或网页抓取最多等待多少秒后切换备选。",
        json_schema_extra={
            "label": "请求超时秒数",
            "hint": "单位：秒（默认 8 秒）。一个源超时后会立刻故障切换到同频道的下一个备选后端。",
        },
    )
    max_results: int = Field(
        default=5,
        ge=1,
        le=20,
        description="每次搜索最多取回几条结果。",
        json_schema_extra={
            "label": "最多返回条数",
            "hint": "单位：条（默认 5 条）。设太大容易让 Planner 上下文变长。",
        },
    )
    cache_minutes: int = Field(
        default=30,
        ge=0,
        le=1440,
        description="同一搜索词和同一网页正文在内存里缓存多少分钟。",
        json_schema_extra={
            "label": "结果缓存分钟",
            "hint": "单位：分钟（默认 30）；填 0 关闭缓存，WebUI 控制台可随时手动清空。",
        },
    )
    max_cache_entries: int = Field(
        default=128,
        ge=1,
        le=1000,
        description="缓存条目上限",
        json_schema_extra={"label": "缓存条目上限", "hidden": True},
    )
    max_body_chars: int = Field(
        default=12000,
        ge=1000,
        le=50000,
        description="正文上限",
        json_schema_extra={"label": "正文最大字数", "hidden": True},
    )
    max_response_bytes: int = Field(
        default=2000000,
        ge=1000,
        le=10000000,
        description="单次下载字节上限",
        json_schema_extra={"label": "下载字节上限", "hidden": True},
    )
    user_agent: str = Field(
        default="zeyr-better-search/0.1",
        description="请求 User-Agent",
        json_schema_extra={"label": "请求 UA", "hidden": True},
    )
    default_sources: list[SearchSource] = Field(
        default_factory=lambda: [
            SearchSource(
                name="duckduckgo", kind="duckduckgo", endpoint="https://html.duckduckgo.com/html/?q={query}"
            ),
            SearchSource(name="bing", kind="bing", endpoint="https://www.bing.com/search?q={query}"),
        ],
        description="零配置搜索源与降级次序",
        json_schema_extra={"label": "免配兜底链", "hidden": True},
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy(cls, values):
        if isinstance(values, dict):
            values = dict(values)
            if "scope_domains" in values and "domain_routes" not in values:
                values["domain_routes"] = [
                    {"scope": scope, "domains": domains} for scope, domains in values["scope_domains"].items()
                ]
            if isinstance(values.get("channels"), list):
                values["channels"] = [
                    {**channel, "time_range": "any"}
                    if isinstance(channel, dict) and channel.get("time_range") == ""
                    else channel
                    for channel in values["channels"]
                ]
        return values

    @model_validator(mode="after")
    def unique_channels(self):
        names = [row.name for row in self.channels]
        if not names or any(not name for name in names) or len(names) != len(set(names)):
            raise ValueError("频道名不能为空或重复，至少保留一个频道")
        backend_names = [row.name for row in self.backends]
        if len(backend_names) != len(set(backend_names)):
            raise ValueError("后端名不能重复")
        for channel in self.channels:
            if any(name not in backend_names for name in channel.backends):
                raise ValueError("频道引用不存在的后端")
        return self

    @property
    def scope_domains(self):
        return {row.scope: row.domains for row in self.domain_routes}


_BASIC_FIELDS = ["enabled", "show_advanced", "channels", "backends"]
for _name, _field in Config.model_fields.items():
    if _name not in _BASIC_FIELDS and _name != "plugin":
        _field.json_schema_extra = {
            **(_field.json_schema_extra or {}),
            "depends_on": "show_advanced",
            "depends_value": True,
        }
Config.model_rebuild(force=True)

for _model in list(globals().values()):
    if isinstance(_model, type) and issubclass(_model, PluginConfigBase):
        for _field_name, _field_info in _model.model_fields.items():
            _field_info.json_schema_extra = {
                "label": _field_info.description or _field_name,
                **(_field_info.json_schema_extra or {}),
            }
        _model.model_rebuild(force=True)
