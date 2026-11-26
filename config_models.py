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
    kind: Literal["duckduckgo", "bing", "json", "searxng", "brave", "exa", "tavily"] = Field(
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


class PluginInfo(PluginConfigBase):
    config_version: str = Field(default="0.1.0", description="配置版本，由 Runner 管理")


class Config(PluginConfigBase):
    scope: ScopeConfig = Field(default_factory=ScopeConfig, description="独立会话与用户生效范围")
    show_advanced: bool = Field(default=False, description="显示高级设置")
    plugin: PluginInfo = Field(default_factory=PluginInfo)
    enabled: bool = Field(default=True, description="启用插件")
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
        if isinstance(values, dict) and "scope_domains" in values and "domain_routes" not in values:
            values = {
                **values,
                "domain_routes": [
                    {"scope": scope, "domains": domains} for scope, domains in values["scope_domains"].items()
                ],
            }
        return values

    @property
    def scope_domains(self):
        return {row.scope: row.domains for row in self.domain_routes}


_BASIC_FIELDS = ["enabled", "show_advanced", "sources", "preferred_domains"]
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
