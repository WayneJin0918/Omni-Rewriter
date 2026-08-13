"""Local-clip reconstruct (v2pe): evidence pack → observation → H3 t2va PE.

Expand ≠ generate. The source mp4 is never inlined into ``expand``.
"""

from .evidence import EvidencePack, EvidencePackConfig, ProbeInfo, build_evidence_pack
from .replay import (
    clamp_h3_pe_for_generate,
    clamp_request_for_h3,
    envelope_for_h3_replay,
    h3_replay_window_seconds,
)
from .service import ReconstructResult, observation_to_request, reconstruct

__all__ = [
    "EvidencePack",
    "EvidencePackConfig",
    "ProbeInfo",
    "ReconstructResult",
    "build_evidence_pack",
    "clamp_h3_pe_for_generate",
    "clamp_request_for_h3",
    "envelope_for_h3_replay",
    "h3_replay_window_seconds",
    "observation_to_request",
    "reconstruct",
]
