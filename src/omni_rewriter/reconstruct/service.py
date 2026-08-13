"""Reconstruct entry points: observation JSON or local mp4 → validated H3 t2va PE."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ..agent import RewriteResult
from ..backends import ChatBackend, OpenAICompatibleBackend
from ..config import Settings
from ..errors import ReconstructError
from ..models import RewriteRequest, TaskType
from ..models.observation import VideoObservation, bind_probe_duration
from ..service import expand as expand_service
from .evidence import EvidencePack, EvidencePackConfig, build_evidence_pack
from .observe import observe_pack


@dataclass(frozen=True, slots=True)
class ReconstructResult:
    observation: VideoObservation
    rewrite: RewriteResult
    request: RewriteRequest
    pack: EvidencePack | None = None


def observation_to_request(observation: VideoObservation) -> RewriteRequest:
    """Turn a grounded observation into a t2va RewriteRequest with no media."""

    prompt = (
        "Reconstruct this observed clip as H3 t2va prompt-expansion. "
        "duration_seconds is ffprobe ground truth and must not change. "
        "Do not invent shots or times outside the observation. "
        "Preserve inferred=false dialogue verbatim as <d>[Language] …</d>. "
        "Inferred dialogue may be kept as legal <d> lines. "
        "Describe appearance only; do not name celebrities or trademarks. "
        "Expand ≠ generate.\n\n"
        f"{observation.model_dump_json(indent=2)}"
    )
    return RewriteRequest(
        prompt=prompt,
        duration_seconds=observation.duration_seconds,
        task=TaskType.T2VA,
        metadata={
            "video_pe_profile": "h3",
            "reconstruct": "v1-t2va",
        },
    )


async def reconstruct(
    *,
    source: Path | None = None,
    observation: VideoObservation | None = None,
    pack_dir: Path | None = None,
    settings: Settings | None = None,
    backend: ChatBackend | None = None,
    pack_config: EvidencePackConfig | None = None,
    pack_only: bool = False,
) -> ReconstructResult | EvidencePack:
    """Run pack / observe / expand. ``pack_only`` returns the evidence pack."""

    if pack_only:
        if source is None:
            raise ReconstructError("pack-only reconstruct requires a local video path")
        if pack_dir is None:
            raise ReconstructError("pack-only reconstruct requires pack_dir")
        return build_evidence_pack(source, pack_dir, pack_config)

    if observation is None and source is None:
        raise ReconstructError("reconstruct requires a video path or a VideoObservation")

    pack: EvidencePack | None = None
    if source is not None:
        if pack_dir is None:
            raise ReconstructError("video reconstruct requires pack_dir")
        pack = build_evidence_pack(source, pack_dir, pack_config)
        if observation is None:
            observation = await _observe(pack, settings=settings, backend=backend)
        else:
            observation = bind_probe_duration(observation, pack.probe.duration_seconds)
    assert observation is not None
    request = observation_to_request(observation)
    if pack is not None:
        metadata = dict(request.metadata)
        metadata["aspect_ratio"] = _aspect_ratio_label(pack.probe.width, pack.probe.height)
        metadata["short_edge"] = "768"
        request = request.model_copy(update={"metadata": metadata})
    rewrite = await expand_service(request, settings)
    return ReconstructResult(
        observation=observation,
        rewrite=rewrite,
        request=request,
        pack=pack,
    )


def _aspect_ratio_label(width: int, height: int) -> str:
    """Nearest common H3 aspect from the source probe (not a generate guarantee)."""

    if height <= 0:
        return "16:9"
    ratio = width / height
    candidates = {
        "16:9": 16 / 9,
        "9:16": 9 / 16,
        "1:1": 1.0,
        "4:3": 4 / 3,
        "3:4": 3 / 4,
        "21:9": 21 / 9,
    }
    return min(candidates, key=lambda key: abs(candidates[key] - ratio))


def result_payload(result: ReconstructResult) -> dict[str, object]:
    """CLI/HTTP JSON for a completed reconstruct (no JPEG bytes)."""

    rendered = result.rewrite.output.render()
    payload: dict[str, object] = {
        "observation": json.loads(result.observation.model_dump_json()),
        "request": json.loads(result.request.model_dump_json(exclude={"resolved_task"})),
        "output": result.rewrite.output.model_dump(mode="json"),
        "analysis": result.rewrite.analysis.model_dump(mode="json"),
        "repairs": result.rewrite.repairs,
        "run_id": result.rewrite.run_id,
        "rendered_text": rendered,
        "h3_text": rendered,
    }
    if result.pack is not None:
        payload["evidence"] = result.pack.summary()
    return payload


async def _observe(
    pack: EvidencePack,
    *,
    settings: Settings | None,
    backend: ChatBackend | None,
) -> VideoObservation:
    owns_backend = backend is None
    active = backend or OpenAICompatibleBackend(
        (settings or Settings.from_env()).chat_backend_config()
    )
    try:
        return await observe_pack(pack, active)
    finally:
        close = getattr(active, "aclose", None)
        if owns_backend and callable(close):
            await close()
