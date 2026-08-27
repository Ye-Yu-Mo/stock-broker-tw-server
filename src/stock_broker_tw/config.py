"""Central configuration loading using pydantic-settings.

The configuration is read from a TOML file (``config/default.toml`` by default),
then overridden by environment variables (``YUANTA_*``) and ``.env``.

Supported environment variable examples::

    YUANTA_SERVER__HOST=0.0.0.0
    YUANTA_SERVER__API_TOKEN=change-me
    YUANTA_YUANTA__ENVIRONMENT=UAT
    YUANTA_ACCOUNT__ACCOUNT=S98875005091
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, ClassVar

from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)
from pydantic_settings.sources.providers.dotenv import DotEnvSettingsSource
from pydantic_settings.sources.providers.env import EnvSettingsSource


class ServerConfig(BaseModel):
    """HTTP server and operational settings."""

    host: str = "127.0.0.1"
    port: int = 8000
    api_token: str = ""
    log_level: str = "INFO"
    log_json: bool = True


class YuantaConfig(BaseModel):
    """Yuanta Spark API connection settings."""

    environment: str = "UAT"
    spark_api_dir: str | None = None
    login_timeout: float = 15.0
    log_type: str = "COMMON"
    pmm_server_check: bool = False


class AccountConfig(BaseModel):
    """Default trading account credentials used when API request omits them."""

    account: str = ""
    password: str = ""
    pfx_path: str | None = None
    pfx_pass: str | None = None


class AuditConfig(BaseModel):
    """Audit log settings."""

    enabled: bool = True
    file: str | None = None


_LEGACY_ENV_MAP: dict[str, dict[str, str]] = {
    "server": {
        "host": "yuanta_host",
        "port": "yuanta_port",
        "api_token": "yuanta_api_token",
        "log_level": "yuanta_log_level",
        "log_json": "yuanta_log_json",
    },
    "account": {
        "account": "yuanta_account",
        "password": "yuanta_password",
        "pfx_path": "yuanta_pfx_path",
        "pfx_pass": "yuanta_pfx_pass",
    },
    "yuanta": {
        "environment": "yuanta_env",
        "spark_api_dir": "yuanta_spark_api_dir",
        "login_timeout": "yuanta_login_timeout",
    },
    "audit": {
        "enabled": "yuanta_audit_enabled",
        "file": "yuanta_audit_file",
    },
}


class _LegacyEnvMixin:
    """Support the M1 flat ``YUANTA_*`` variables alongside nested names."""

    def get_field_value(self, field, field_name):
        mapping = _LEGACY_ENV_MAP.get(field_name)
        if mapping:
            data: dict[str, Any] = {}
            for subfield, env_name in mapping.items():
                value = self.env_vars.get(env_name)
                if value is not None:
                    data[subfield] = value
            if data:
                return data, field_name, True
        return super().get_field_value(field, field_name)

    def decode_complex_value(self, field_name, field, value):
        if isinstance(value, dict):
            return value
        return super().decode_complex_value(field_name, field, value)


class CompatEnvSettingsSource(_LegacyEnvMixin, EnvSettingsSource):
    """Environment source that accepts M1 flat ``YUANTA_*`` variables."""


class CompatDotEnvSettingsSource(_LegacyEnvMixin, DotEnvSettingsSource):
    """Dotenv source that accepts M1 flat ``YUANTA_*`` variables."""


class Settings(BaseSettings):
    """Application settings root model."""

    # Class-level override used by ``load_settings()`` so callers can point at
    # a custom TOML file without mutating process-wide state permanently.
    _toml_file: ClassVar[str] = "config/default.toml"

    model_config = SettingsConfigDict(
        env_prefix="YUANTA_",
        env_nested_delimiter="__",
        env_file=".env",
        extra="ignore",
    )

    server: ServerConfig = ServerConfig()
    yuanta: YuantaConfig = YuantaConfig()
    account: AccountConfig = AccountConfig()
    audit: AuditConfig = AuditConfig()

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        toml_file = settings_cls._toml_file
        if toml_file == "config/default.toml":
            toml_file = os.environ.get("YUANTA_CONFIG", toml_file)
        toml_source = TomlConfigSettingsSource(settings_cls, toml_file=toml_file)
        # Order: init > env > dotenv > toml > file-secrets.  This gives env vars
        # and explicit constructor values priority over TOML defaults.
        return (
            init_settings,
            CompatEnvSettingsSource(
                settings_cls,
                case_sensitive=env_settings.case_sensitive,
                env_prefix=env_settings.env_prefix,
                env_nested_delimiter=env_settings.env_nested_delimiter,
                env_ignore_empty=env_settings.env_ignore_empty,
                env_parse_none_str=env_settings.env_parse_none_str,
                env_parse_enums=env_settings.env_parse_enums,
            ),
            CompatDotEnvSettingsSource(
                settings_cls,
                env_file=dotenv_settings.env_file,
                env_file_encoding=dotenv_settings.env_file_encoding,
                case_sensitive=dotenv_settings.case_sensitive,
                env_prefix=dotenv_settings.env_prefix,
                env_nested_delimiter=dotenv_settings.env_nested_delimiter,
                env_ignore_empty=dotenv_settings.env_ignore_empty,
                env_parse_none_str=dotenv_settings.env_parse_none_str,
                env_parse_enums=dotenv_settings.env_parse_enums,
            ),
            toml_source,
            file_secret_settings,
        )


def load_settings(config_path: str | Path | None = None) -> Settings:
    """Load settings from a TOML file plus environment variables.

    ``config_path`` defaults to ``YUANTA_CONFIG`` or ``config/default.toml``.
    """
    path = config_path or os.environ.get("YUANTA_CONFIG", "config/default.toml")
    previous_toml_file = Settings._toml_file
    try:
        Settings._toml_file = str(path)
        return Settings()
    finally:
        Settings._toml_file = previous_toml_file
