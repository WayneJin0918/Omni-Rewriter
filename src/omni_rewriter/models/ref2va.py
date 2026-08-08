"""Six-section full-reference H3 output."""

import re
from decimal import Decimal

from pydantic import Field, model_validator

from .common import StrictModel
from .validation import labels_in, validate_markup, validate_reference_numbering, validate_timeline

SUMMARY_TYPES = {
    "keyframe completion",
    "reference generation",
    "video editing",
    "video continuation",
    "audio reuse",
    "audio reference",
}
VISUAL_RETENTION = {
    "fully_preserved",
    "partially_preserved",
    "attribute_transfer",
    "weak_reference",
}
AUDIO_RETENTION = {"fully_copy", "partially_copy", "reference", "weak_reference"}
DEFINITION_RE = re.compile(
    r"^(<(?P<kind>Subject|Picture|Video|Audio) [1-9]\d*>)\s+.+$", re.MULTILINE
)
RETENTION_RE = re.compile(
    r"^(<(?P<kind>Subject|Picture|Video|Audio) [1-9]\d*>)(?:\s+\([^)]*\))?:\s+"
    r"(?P<marker>[a-z_]+)\s+-\s+.+$",
    re.MULTILINE,
)


class Ref2VARewrite(StrictModel):
    """Validated six-section rewrite for arbitrary reference media."""

    duration_seconds: Decimal = Field(gt=0)
    subject_definitions: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    retention_analysis: str = Field(min_length=1)
    detailed_description: str = Field(min_length=1)
    overall_soundscape: str = Field(min_length=1)
    non_diegetic_music: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_h3_grammar(self) -> "Ref2VARewrite":
        combined = "\n".join(
            (
                self.subject_definitions,
                self.summary,
                self.retention_analysis,
                self.detailed_description,
                self.overall_soundscape,
                self.non_diegetic_music,
            )
        )
        validate_timeline(self.detailed_description, self.duration_seconds)
        validate_markup(self.detailed_description)
        validate_reference_numbering(combined)

        summary_match = re.match(r"^\[([^\[\]\r\n]+)\]\s+\S", self.summary)
        if not summary_match:
            raise ValueError("summary must begin with a bracketed task-type prefix")
        task_types = summary_match.group(1).split(" + ")
        if len(task_types) != len(set(task_types)) or not set(task_types) <= SUMMARY_TYPES:
            raise ValueError("summary contains duplicate or unsupported task types")

        definitions = list(DEFINITION_RE.finditer(self.subject_definitions))
        if not definitions:
            raise ValueError("subject_definitions requires one labeled definition per line")
        definition_lines = [line for line in self.subject_definitions.splitlines() if line.strip()]
        if len(definitions) != len(definition_lines):
            raise ValueError("every subject_definitions line must begin with one reference label")
        primary = {match.group(1) for match in definitions}
        known = labels_in(self.subject_definitions)
        used = labels_in(combined) - known
        if used:
            raise ValueError(f"undefined reference labels: {sorted(used)}")

        retention = list(RETENTION_RE.finditer(self.retention_analysis))
        retention_lines = [line for line in self.retention_analysis.splitlines() if line.strip()]
        if len(retention) != len(retention_lines):
            raise ValueError("every retention_analysis line must use a labeled retention marker")
        retained = {match.group(1) for match in retention}
        if retained != primary:
            raise ValueError("retention_analysis must contain exactly one entry per definition")
        if len(retention) != len(retained):
            raise ValueError("retention_analysis contains duplicate labels")
        for match in retention:
            allowed = AUDIO_RETENTION if match["kind"] == "Audio" else VISUAL_RETENTION
            if match["marker"] not in allowed:
                raise ValueError(
                    f"invalid retention marker {match['marker']!r} for {match['kind']}"
                )
        if "<d>" in self.overall_soundscape or "<d>" in self.non_diegetic_music:
            raise ValueError("dialogue belongs only in detailed_description")
        return self

    def render(self) -> str:
        """Render the six sections in H3 order."""

        sections = (
            ("subject_definitions", self.subject_definitions),
            ("summary", self.summary),
            ("retention_analysis", self.retention_analysis),
            ("detailed_description", self.detailed_description),
            ("overall_soundscape", self.overall_soundscape),
            ("non_diegetic_music", self.non_diegetic_music),
        )
        return "\n\n".join(f"{name}:\n{value}" for name, value in sections)
