from typing import Literal

from maibot_sdk import Field, PluginConfigBase
from pydantic import field_validator, model_validator

from .ecosystem import ScopeConfig


class Header(PluginConfigBase):
    name: str = Field(default="", description="请求头名")
    value: str = Field(default="", description="请求头内容；密钥只填写在实例")


class DomainRoute(PluginConfigBase):
    scope: str = Field(default="web", description="搜索能力范围名")
    domains: list[str] = Field(default_factory=list, description="偏好域名")


class SearchSource(PluginConfigBase):
    name: str = Field(default="", description="来源名")
    kind: Literal["duckduckgo", "bing", "json", "searxng", "brave", "exa", "tavily", "host_web"] = Field(
        default="json", description="搜索适配器"
    )
    endpoint: str = Field(default="", description="搜索地址模板，支持 {query} 和 {scope}")
    api_key: str = Field(default="", description="API 密钥，仅实例配置")
    headers: list[Header] = Field(default_factory=list, description="额外请求头条目")

    @field_validator("headers", mode="before")
    @classmethod
    def legacy_headers(cls, value):
        return (
            [{"name": name, "value": text} for name, text in value.items()]
            if isinstance(value, dict)
            else value
        )

    domains: list[str] = Field(default_factory=list, description="此源优先处理的域名")
    scopes: list[str] = Field(default_factory=list, description="此源适用的 scope；空表示全部")
    enabled: bool = Field(default=True, description="启用")


class Channel(PluginConfigBase):
    name: str = Field(default="general", description="能力频道名；向模型展示")
    desc: str = Field(default="通用互联网资料和实时事实", description="能力说明；不填后端名称")
    auto_attach: bool = Field(default=False, description="默认通用查询时自动并行附带")
    sites: list[str] = Field(default_factory=list, description="域名列表；自动拼接 site: 定向")
    backends: list[str] = Field(default_factory=list, description="按顺序引用凭证池后端名；空复用通用后端")
    time_range: Literal["any", "day", "week", "month"] = Field(default="any", description="默认时效")
    lang: str = Field(default="", description="偏好语言")
    region: str = Field(default="", description="偏好地区")


class ReaderConfig(PluginConfigBase):
    __ui_label__ = "正文降级"
    enabled: bool = Field(default=False, description="正文过短时使用 Reader")
    url_prefix: str = Field(default="", description="Reader 转换前缀；拼接原 URL；仍经公网检查")
    min_chars: int = Field(default=100, ge=0, le=2000, description="触发正文降级的字数阈值")


class PeekConfig(PluginConfigBase):
    __ui_label__ = "静默读空气"
    enabled: bool = Field(default=False, description="后台搜抓并插入客观卡片")
    trigger: Literal["url", "unknown_term"] = Field(default="url", description="URL 或轻量模型判定新话题")
    model_task: str = Field(default="", description="轻量模型任务")
    cooldown_seconds: float = Field(default=600, ge=1, le=86400, description="每会话冷却")
    max_chars: int = Field(default=500, ge=50, le=2000, description="背景卡片上限")
    max_pending: int = Field(default=4, ge=1, le=32, description="最多同时后台任务")
    timeout_seconds: float = Field(default=45, ge=1, le=120, description="后台任务超时")
    instruction: str = Field(
        default='判断这段对话是否谈论新梗、具体新闻且需要背景核实。只返回 JSON：{"query":"需要搜索的词或空字符串"}。对话：',
        description="轻量判断要求",
    )


class PluginInfo(PluginConfigBase):
    config_version: str = Field(default="0.1.0", description="配置版本，由 Runner 管理")


class Config(PluginConfigBase):
    scope: ScopeConfig = Field(default_factory=ScopeConfig, description="独立会话与用户生效范围")
    show_advanced: bool = Field(default=False, description="显示高级设置")
    plugin: PluginInfo = Field(default_factory=PluginInfo)
    enabled: bool = Field(default=True, description="启用插件")
    channels: list[Channel] = Field(
        default_factory=lambda: [Channel()], description="向模型匿名声明的搜索能力"
    )
    backends: list[SearchSource] = Field(
        default_factory=list, description="集中后端凭证池；空使用免 Key 默认链"
    )
    reader_fallback: ReaderConfig = Field(default_factory=ReaderConfig)
    passive_peek: PeekConfig = Field(default_factory=PeekConfig)
    sources: list[SearchSource] = Field(default_factory=list, description="搜索源；空时使用默认源")
    preferred_domains: list[str] = Field(default_factory=list, description="偏好站点")
    domain_routes: list[DomainRoute] = Field(default_factory=list, description="能力范围与偏好站点条目")
    timeout_seconds: float = Field(default=8.0, ge=1, le=30, description="单源网络超时")
    max_results: int = Field(default=5, ge=1, le=20, description="最大结果数")
    cache_minutes: int = Field(default=30, ge=0, le=1440, description="搜索和正文缓存时间")
    max_cache_entries: int = Field(default=128, ge=1, le=1000, description="缓存条目上限")
    max_body_chars: int = Field(default=12000, ge=1000, le=50000, description="正文上限")
    max_response_bytes: int = Field(default=2000000, ge=1000, le=10000000, description="单次下载字节上限")
    user_agent: str = Field(default="zeyr-better-search/0.1", description="请求 User-Agent")
    default_sources: list[SearchSource] = Field(
        default_factory=lambda: [
            SearchSource(
                name="duckduckgo", kind="duckduckgo", endpoint="https://html.duckduckgo.com/html/?q={query}"
            ),
            SearchSource(name="bing", kind="bing", endpoint="https://www.bing.com/search?q={query}"),
        ],
        description="零配置搜索源与降级次序",
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


# SDK labels otherwise fall back to Python field names in top-level sections.
for _model in list(globals().values()):
    if isinstance(_model, type) and issubclass(_model, PluginConfigBase):
        for _field_name, _field_info in _model.model_fields.items():
            _field_info.json_schema_extra = {
                "label": _field_info.description or _field_name,
                **(_field_info.json_schema_extra or {}),
            }
        _model.model_rebuild(force=True)
