"""HunyuanImage-3.0 client for its evidence-backed vLLM chat extension."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal

import httpx
from pydantic import Field, SecretStr

from ..models import RewriteRequest
from ..models.common import IMAGE_TASKS, StrictModel
from .base import (
    GenerationConfigurationError,
    GenerationResponseError,
    bearer_headers,
    decode_base64_media,
    request_json,
    v1_url,
)

_IMAGE_CHAT_TEMPLATE = (
    "{% for message in messages %}"
    "{% if message['role'] == 'user' %}"
    "<|startoftext|>{{ message['content'] }}"
    "{% endif %}"
    "{% endfor %}"
)


class HunyuanImageVLLMClientConfig(StrictModel):
    """Configuration matching HunyuanImage-3.0's local vLLM client."""

    base_url: str = Field(default="http://127.0.0.1:8000/v1", min_length=1)
    api_key: SecretStr | None = None
    model: str = Field(default="vllm_hunyuan_image3", min_length=1)
    timeout: float = Field(default=600.0, gt=0)
    max_image_bytes: int = Field(default=64 * 1024**2, gt=0)
    width: int = Field(default=1024, gt=0, le=4096)
    height: int = Field(default=1024, gt=0, le=4096)
    diff_infer_steps: int = Field(default=50, gt=0, le=500)
    use_system_prompt: Literal[
        "None",
        "dynamic",
        "en_vanilla",
        "en_recaption",
        "en_think_recaption",
        "custom",
    ] = "None"


class HunyuanImageVLLMClient:
    """Generate one image through ``task_type=hunyuan_image3``."""

    def __init__(
        self,
        config: HunyuanImageVLLMClientConfig,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.config = config
        self._client = client
        self._owns_client = client is None

    async def __aenter__(self) -> "HunyuanImageVLLMClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None

    def build_payload(
        self,
        request: RewriteRequest,
        prompt: str,
        *,
        width: int | None = None,
        height: int | None = None,
        seed: int | None = None,
        diff_infer_steps: int | None = None,
        task_extra: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        if request.resolved_task not in IMAGE_TASKS:
            raise GenerationConfigurationError("Hunyuan image requires an image RewriteRequest")
        if not prompt.strip():
            raise GenerationConfigurationError("Hunyuan image prompt must not be empty")
        resolved_width = width or _metadata_int(request, "width") or self.config.width
        resolved_height = height or _metadata_int(request, "height") or self.config.height
        resolved_steps = (
            diff_infer_steps
            or _metadata_int(request, "diff_infer_steps")
            or self.config.diff_infer_steps
        )
        if not 1 <= resolved_width <= 4096 or not 1 <= resolved_height <= 4096:
            raise GenerationConfigurationError("Hunyuan image dimensions must be from 1 to 4096")
        if not 1 <= resolved_steps <= 500:
            raise GenerationConfigurationError("Hunyuan diff_infer_steps must be from 1 to 500")
        extra: dict[str, Any] = {
            "diff_infer_steps": resolved_steps,
            "use_system_prompt": self.config.use_system_prompt,
            "bot_task": "image",
            # This is height x width in the upstream Hunyuan vLLM client.
            "image_size": f"{resolved_height}x{resolved_width}",
        }
        if task_extra:
            protected = set(task_extra) & {"bot_task", "image_size"}
            if protected:
                raise GenerationConfigurationError(
                    f"cannot override Hunyuan task fields: {sorted(protected)}"
                )
            extra.update(task_extra)
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": ""},
                {"role": "user", "content": prompt},
            ],
            "max_completion_tokens": 1,
            "temperature": 0,
            "chat_template": _IMAGE_CHAT_TEMPLATE,
            "task_type": "hunyuan_image3",
            "task_extra_kwargs": extra,
        }
        resolved_seed = seed if seed is not None else _metadata_int(request, "seed")
        if resolved_seed is not None:
            payload["seed"] = resolved_seed
        return payload

    async def generate(
        self,
        request: RewriteRequest,
        prompt: str,
        *,
        width: int | None = None,
        height: int | None = None,
        seed: int | None = None,
        diff_infer_steps: int | None = None,
        task_extra: Mapping[str, Any] | None = None,
    ) -> bytes:
        data = await request_json(
            self._get_client(),
            "POST",
            v1_url(self.config.base_url, "/chat/completions"),
            service="HunyuanImage vLLM",
            headers=self._headers(),
            json=self.build_payload(
                request,
                prompt,
                width=width,
                height=height,
                seed=seed,
                diff_infer_steps=diff_infer_steps,
                task_extra=task_extra,
            ),
        )
        image = data.get("image")
        if not isinstance(image, str) or not image:
            raise GenerationResponseError("HunyuanImage vLLM response omitted top-level image")
        return decode_base64_media(
            image,
            max_bytes=self.config.max_image_bytes,
            service="HunyuanImage vLLM",
        )

    def _headers(self) -> dict[str, str]:
        secret = self.config.api_key.get_secret_value() if self.config.api_key is not None else None
        return bearer_headers(secret)

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.config.timeout)
        return self._client


def _metadata_int(request: RewriteRequest, key: str) -> int | None:
    value = request.metadata.get(key)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise GenerationConfigurationError(f"Hunyuan metadata {key!r} must be an integer") from exc
