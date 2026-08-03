"""Deterministic single-case and JSONL-manifest evaluation."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Mapping, Protocol, runtime_checkable

from .models import BaseRewrite, Ref2VARewrite
from .models.validation import REFERENCE_RE, SHOT_RE, labels_in
from .service import validate_output, validation_error


@runtime_checkable
class Evaluator(Protocol):
    def evaluate(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        """Return JSON-serializable evaluation results."""


@runtime_checkable
class Judge(Protocol):
    """Optional local or remote judge; deterministic evaluation never requires one."""

    def judge(
        self,
        payload: Mapping[str, Any],
        deterministic_result: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Return additional JSON-serializable metrics."""


class BasicEvaluator:
    """Deterministic schema, reference, timeline and completeness evaluator."""

    def __init__(self, judge: Judge | None = None) -> None:
        self.judge = judge

    def evaluate(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        try:
            output, _ = validate_output(payload)
        except (ValueError, TypeError) as exc:
            return {
                "evaluator": "basic",
                **validation_error(exc),
                "metrics": {
                    "schema_pass": False,
                    "field_completeness": 0.0,
                    "missing_fields": _missing_fields(payload),
                    "reference_count": _reference_count(payload),
                    "timeline_pass": False,
                },
            }
        text = output.render()
        model_data = output.model_dump(mode="json")
        required = tuple(output.__class__.model_fields)
        missing = [
            field
            for field in required
            if field not in model_data or model_data[field] in (None, "", [], {})
        ]
        references = labels_in(text)
        definitions = (
            labels_in(output.subject_definitions) if isinstance(output, Ref2VARewrite) else set()
        )
        shots = list(SHOT_RE.finditer(text))
        result: dict[str, Any] = {
            "evaluator": "basic",
            "valid": True,
            "metrics": {
                "schema_pass": True,
                "timeline_pass": bool(shots),
                "field_completeness": (len(required) - len(missing)) / len(required),
                "missing_fields": missing,
                "characters": len(text),
                "shot_count": len(shots),
                "timed_shot_count": sum(match["time"] is not None for match in shots),
                "reference_count": len(REFERENCE_RE.findall(text)),
                "unique_references": sorted(references),
                "defined_references": sorted(definitions),
                "undefined_references": sorted(references - definitions)
                if isinstance(output, Ref2VARewrite)
                else [],
                "task": output.task.value if isinstance(output, BaseRewrite) else "ref2va",
            },
        }
        if self.judge is not None:
            result["judge"] = dict(self.judge.judge(payload, result))
        return result

    def evaluate_manifest(
        self,
        source: str | Path | Iterable[Mapping[str, Any]],
    ) -> dict[str, Any]:
        """Evaluate JSONL records (or mappings) and return cases plus aggregate counts."""

        records: list[tuple[int, Mapping[str, Any] | Exception]] = []
        if isinstance(source, (str, Path)):
            path = Path(source)
            for line_number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if not line.strip():
                    continue
                try:
                    value = json.loads(line)
                    if not isinstance(value, Mapping):
                        raise TypeError("manifest record must be a JSON object")
                    records.append((line_number, value))
                except (json.JSONDecodeError, TypeError) as exc:
                    records.append((line_number, exc))
        else:
            records.extend(enumerate(source, start=1))

        cases: list[dict[str, Any]] = []
        for line_number, value in records:
            if isinstance(value, Exception):
                result = {
                    "evaluator": "basic",
                    "valid": False,
                    "errors": [{"type": type(value).__name__, "msg": str(value)}],
                }
            else:
                result = self.evaluate(value)
            cases.append({"line": line_number, **result})
        passed = sum(bool(case["valid"]) for case in cases)
        return {
            "evaluator": "basic",
            "manifest": True,
            "valid": passed == len(cases) and bool(cases),
            "summary": {
                "total": len(cases),
                "passed": passed,
                "failed": len(cases) - passed,
            },
            "cases": cases,
        }


def _output_mapping(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    output = payload.get("output", payload)
    return output if isinstance(output, Mapping) else {}


def _missing_fields(payload: Mapping[str, Any]) -> list[str]:
    output = _output_mapping(payload)
    is_ref = "subject_definitions" in output
    required = tuple(Ref2VARewrite.model_fields) if is_ref else tuple(BaseRewrite.model_fields)
    return [field for field in required if output.get(field) in (None, "", [], {})]


def _reference_count(payload: Mapping[str, Any]) -> int:
    return len(REFERENCE_RE.findall(json.dumps(_output_mapping(payload), ensure_ascii=False)))
