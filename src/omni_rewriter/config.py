"""Environment-only runtime configuration.

No dotenv file is loaded and secret values are represented as ``SecretStr``.
"""

from __future__ import annotations

import os
from typing import Any, Callable, TypeVar

from pydantic import Field, SecretStr

from .backends import ChatBackendConfig
from .models.common import StrictModel

T = TypeVar("T")


def _env(name: str, default: T, parse: Callable[[str], T]) -> T:
    value = os.environ.get(name)
    if value is None:
        return default
    return parse(value)


def _optional(name: str) -> str | None:
    value = os.environ.get(name)
    return value if value else None


def _bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"invalid boolean value for environment variable: {value!r}")


class Settings(StrictModel):
    """Runtime settings read explicitly from supported environment variables."""

    backend_base_url: str = "http://127.0.0.1:8000/v1"
    backend_model: str = "Qwen/Qwen3.5-122B-A10B"
    backend_api_key: SecretStr | None = None
    backend_timeout: float = Field(default=120.0, gt=0)
    backend_retries: int = Field(default=2, ge=0, le=10)
    backend_temperature: float | None = Field(default=0.2, ge=0, le=2)
    backend_max_tokens: int | None = Field(default=None, gt=0)
    enable_thinking: bool | None = False
    max_repairs: int = Field(default=2, ge=0, le=10)

    h3_base_url: str = "http://127.0.0.1:30000"
    h3_api_key: SecretStr | None = None
    h3_timeout: float = Field(default=60.0, gt=0)
    h3_poll_interval: float = Field(default=2.0, gt=0)
    h3_poll_timeout: float = Field(default=900.0, gt=0)
    h3_max_download_bytes: int = Field(default=2 * 1024**3, gt=0)

    minimax_api_key: SecretStr | None = None
    minimax_base_url: str = "https://api.minimax.io"
    minimax_timeout: float = Field(default=60.0, gt=0)
    minimax_poll_interval: float = Field(default=2.0, gt=0)
    minimax_poll_timeout: float = Field(default=900.0, gt=0)

    @classmethod
    def from_env(cls) -> "Settings":
        """Read only OMNI_WRITER_* and MINIMAX_* variables."""

        backend_key = _optional("OMNI_WRITER_BACKEND_API_KEY") or _optional(
            "OMNI_WRITER_API_KEY"
        )
        h3_key = _optional("OMNI_WRITER_H3_API_KEY")
        minimax_key = _optional("MINIMAX_API_KEY")
        max_tokens = _optional("OMNI_WRITER_MAX_TOKENS")
        temperature = _optional("OMNI_WRITER_TEMPERATURE")
        thinking = _optional("OMNI_WRITER_ENABLE_THINKING")
        return cls(
            backend_base_url=os.environ.get(
                "OMNI_WRITER_BACKEND_BASE_URL",
                os.environ.get("OMNI_WRITER_BASE_URL", "http://127.0.0.1:8000/v1"),
            ),
            backend_model=os.environ.get(
                "OMNI_WRITER_BACKEND_MODEL",
                os.environ.get("OMNI_WRITER_MODEL", "Qwen/Qwen3.5-122B-A10B"),
            ),
            backend_api_key=SecretStr(backend_key) if backend_key else None,
            backend_timeout=_env("OMNI_WRITER_TIMEOUT", 120.0, float),
            backend_retries=_env("OMNI_WRITER_RETRIES", 2, int),
            backend_temperature=float(temperature) if temperature else 0.2,
            backend_max_tokens=int(max_tokens) if max_tokens else None,
            enable_thinking=_bool(thinking) if thinking is not None else False,
            max_repairs=_env("OMNI_WRITER_MAX_REPAIRS", 2, int),
            h3_base_url=os.environ.get(
                "OMNI_WRITER_H3_BASE_URL", "http://127.0.0.1:30000"
            ),
            h3_api_key=SecretStr(h3_key) if h3_key else None,
            h3_timeout=_env("OMNI_WRITER_H3_TIMEOUT", 60.0, float),
            h3_poll_interval=_env("OMNI_WRITER_H3_POLL_INTERVAL", 2.0, float),
            h3_poll_timeout=_env("OMNI_WRITER_H3_POLL_TIMEOUT", 900.0, float),
            h3_max_download_bytes=_env(
                "OMNI_WRITER_H3_MAX_DOWNLOAD_BYTES", 2 * 1024**3, int
            ),
            minimax_api_key=SecretStr(minimax_key) if minimax_key else None,
            minimax_base_url=os.environ.get(
                "MINIMAX_API_BASE",
                os.environ.get("MINIMAX_BASE_URL", "https://api.minimax.io"),
            ),
            minimax_timeout=_env("MINIMAX_TIMEOUT", 60.0, float),
            minimax_poll_interval=_env("MINIMAX_POLL_INTERVAL", 2.0, float),
            minimax_poll_timeout=_env("MINIMAX_POLL_TIMEOUT", 900.0, float),
        )

    def chat_backend_config(self) -> ChatBackendConfig:
        return ChatBackendConfig(
            base_url=self.backend_base_url,
            api_key=self.backend_api_key,
            model=self.backend_model,
            timeout=self.backend_timeout,
            retries=self.backend_retries,
            temperature=self.backend_temperature,
            max_tokens=self.backend_max_tokens,
            enable_thinking=self.enable_thinking,
        )

    def h3_client_config(self) -> Any:
        from .adapters.h3 import H3ClientConfig

        return H3ClientConfig(
            base_url=self.h3_base_url,
            api_key=self.h3_api_key,
            timeout=self.h3_timeout,
            poll_interval=self.h3_poll_interval,
            poll_timeout=self.h3_poll_timeout,
            max_download_bytes=self.h3_max_download_bytes,
        )

    def minimax_client_config(self) -> Any:
        from .adapters.minimax import MiniMaxClientConfig
        from .errors import BackendConfigurationError

        if self.minimax_api_key is None:
            raise BackendConfigurationError("MINIMAX_API_KEY is required for MiniMax API calls")
        return MiniMaxClientConfig(
            api_key=self.minimax_api_key,
            base_url=self.minimax_base_url,
            timeout=self.minimax_timeout,
            poll_interval=self.minimax_poll_interval,
            poll_timeout=self.minimax_poll_timeout,
        )
