from typing import Literal

from maibot_sdk import Field, PluginConfigBase


class SearchSource(PluginConfigBase):
    name: str = Field(default="", description="来源名")
    kind: Literal["duckduckgo", "bing", "json"] = Field(default="duckduckgo", description="适配器")
    endpoint: str = Field(default="", description="搜索地址模板，使用 {query}")
    domains: list[str] = Field(default_factory=list, description="偏好域名")
    enabled: bool = Field(default=True, description="启用")


class PluginInfo(PluginConfigBase):
    config_version: str = Field(default="0.1.0", description="配置版本，由 Runner 管理")


class Config(PluginConfigBase):
    show_advanced: bool = Field(default=False, description="显示高级设置")
    plugin: PluginInfo = Field(default_factory=PluginInfo)
    enabled: bool = Field(default=True, description="启用插件")
    sources: list[SearchSource] = Field(default_factory=list, description="搜索源")
    preferred_domains: list[str] = Field(default_factory=list, description="偏好站点")
    timeout_seconds: float = Field(default=8.0, ge=1, le=30, description="网络超时")
    max_results: int = Field(default=5, ge=1, le=20, description="最大结果数")
    cache_minutes: int = Field(default=30, ge=0, le=1440, description="结果缓存时间")
    max_body_chars: int = Field(default=12000, ge=1000, le=50000, description="正文上限")


_BASIC_FIELDS = ["enabled", "show_advanced", "sources"]
for _name, _field in Config.model_fields.items():
    if _name not in _BASIC_FIELDS and _name != "plugin":
        _field.json_schema_extra = {
            **(_field.json_schema_extra or {}),
            "depends_on": "show_advanced",
            "depends_value": True,
        }
Config.model_rebuild(force=True)
