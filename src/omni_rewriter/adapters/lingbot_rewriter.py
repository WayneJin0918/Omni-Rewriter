"""Optional two-stage OpenAI-compatible client for LingBot caption rewriting."""

from __future__ import annotations

import json
from typing import Any, Literal

import httpx
from pydantic import Field, model_validator

from ..backends import ChatBackendConfig, OpenAICompatibleBackend
from ..errors import BackendConfigurationError, StructuredOutputError
from ..models.common import StrictModel
from ..models.lingbot import LingBotCaption, LingBotCaptionContent

LingBotMode = Literal["t2i", "t2v", "ti2v"]


class LingBotRewriterConfig(StrictModel):
    """Separate endpoints/models preserve base-expand and LoRA-map semantics."""

    expand_base: ChatBackendConfig
    map_lora: ChatBackendConfig
    max_expanded_chars: int = Field(default=20_000, gt=0, le=100_000)

    @model_validator(mode="after")
    def require_distinct_stages(self) -> "LingBotRewriterConfig":
        expand_identity = (self.expand_base.base_url.rstrip("/"), self.expand_base.model)
        map_identity = (self.map_lora.base_url.rstrip("/"), self.map_lora.model)
        if expand_identity == map_identity:
            raise ValueError(
                "expand_base and map_lora must use different endpoints or model identifiers"
            )
        return self


class LingBotRewriteResult(StrictModel):
    mode: LingBotMode
    detailed_caption: str = Field(min_length=1)
    caption: LingBotCaption


class LingBotRewriterClient:
    """Run expansion on the base VLM, then schema mapping on its LoRA."""

    def __init__(
        self,
        config: LingBotRewriterConfig,
        *,
        expand_client: httpx.AsyncClient | None = None,
        map_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.config = config
        self._expand = OpenAICompatibleBackend(config.expand_base, client=expand_client)
        self._map = OpenAICompatibleBackend(config.map_lora, client=map_client)

    async def __aenter__(self) -> "LingBotRewriterClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._expand.aclose()
        await self._map.aclose()

    async def rewrite(
        self,
        prompt: str,
        *,
        mode: LingBotMode = "t2v",
        duration: float | None = 5,
        first_frame_url: str | None = None,
    ) -> LingBotRewriteResult:
        if not prompt.strip():
            raise BackendConfigurationError("LingBot rewrite prompt must not be empty")
        if mode == "t2i":
            if duration is not None:
                raise BackendConfigurationError("LingBot t2i rewrite must omit duration")
            if first_frame_url is not None:
                raise BackendConfigurationError("LingBot t2i rewrite does not accept a first frame")
        else:
            if duration is None or duration <= 0:
                raise BackendConfigurationError("LingBot video rewrite requires positive duration")
            if mode == "ti2v" and first_frame_url is None:
                raise BackendConfigurationError("LingBot ti2v rewrite requires first_frame_url")
            if mode == "t2v" and first_frame_url is not None:
                raise BackendConfigurationError("first_frame_url is only valid for ti2v")

        detailed = (
            await self._expand.complete(
                [
                    {
                        "role": "system",
                        "content": self._expand_instruction(mode),
                    },
                    {
                        "role": "user",
                        "content": self._user_content(
                            prompt,
                            duration=duration,
                            first_frame_url=first_frame_url,
                        ),
                    },
                ]
            )
        ).strip()
        if not detailed:
            raise StructuredOutputError("LingBot base expansion returned empty text")
        if len(detailed) > self.config.max_expanded_chars:
            raise StructuredOutputError("LingBot base expansion exceeded configured size")

        raw_mapping = await self._map.complete(
            [
                {
                    "role": "system",
                    "content": self._map_instruction(mode, duration),
                },
                {"role": "user", "content": f"DETAILED CAPTION:\n{detailed}"},
            ],
            response_model=LingBotCaptionContent,
        )
        try:
            content = LingBotCaptionContent.model_validate_json(self._json_text(raw_mapping))
            caption = LingBotCaption(caption=content, duration=duration)
        except (ValueError, TypeError) as exc:
            raise StructuredOutputError("LingBot LoRA mapping returned invalid caption JSON") from exc
        return LingBotRewriteResult(
            mode=mode,
            detailed_caption=detailed,
            caption=caption,
        )

    @staticmethod
    def _expand_instruction(mode: LingBotMode) -> str:
        kind = "still-image" if mode == "t2i" else "video"
        return (
            f"Expand the user request into one faithful, detailed English {kind} caption. "
            "Preserve identities, counts, text, spatial constraints, and requested actions. "
            "For video, make timing explicit and ignore audio. Return prose only."
        )

    @staticmethod
    def _map_instruction(mode: LingBotMode, duration: float | None) -> str:
        if mode == "t2i":
            temporal = "This is a still image: do not add actions or timestamps."
        else:
            temporal = (
                f"This is a {duration:g}-second video. Include timestamped actions within "
                "that duration and use the video comprehensive_description object."
            )
        return (
            "Map the detailed caption faithfully into the provided LingBot JSON schema. "
            "Complete omitted visual attributes without contradicting the prose. "
            f"{temporal} Return JSON only."
        )

    @staticmethod
    def _user_content(
        prompt: str,
        *,
        duration: float | None,
        first_frame_url: str | None,
    ) -> str | list[dict[str, Any]]:
        text = prompt if duration is None else f"{prompt}\n\nVideo Duration: {duration:g} seconds"
        if first_frame_url is None:
            return text
        return [
            {"type": "image_url", "image_url": {"url": first_frame_url}},
            {"type": "text", "text": text},
        ]

    @staticmethod
    def _json_text(raw: str) -> str:
        text = raw.strip()
        if text.startswith("```"):
            first_newline = text.find("\n")
            if first_newline < 0 or not text.endswith("```"):
                raise StructuredOutputError("LingBot mapping returned an incomplete JSON fence")
            text = text[first_newline + 1 : -3].strip()
        try:
            decoded = json.loads(text)
        except json.JSONDecodeError as exc:
            raise StructuredOutputError("LingBot mapping returned malformed JSON") from exc
        if not isinstance(decoded, dict):
            raise StructuredOutputError("LingBot mapping must return a JSON object")
        return json.dumps(decoded, ensure_ascii=False)
