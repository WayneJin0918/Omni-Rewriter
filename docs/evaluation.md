# Evaluation

Omni-Writer's built-in evaluator measures deterministic structural conformance. It does not
generate a video and is not a substitute for perceptual, semantic, safety, or human evaluation.

## Single case

Pass a direct rewrite object or a request/output envelope:

```bash
omni-writer eval output.json
```

The envelope form is preferable because it also checks that task and duration match the request:

```json
{
  "request": {
    "prompt": "A kite rises.",
    "duration_seconds": 6
  },
  "output": {
    "task": "t2va",
    "duration_seconds": 6,
    "integrated_multimodal_description": "[Shot 1] A kite rises into a clear sky.",
    "overall_soundscape": "Soft wind.",
    "non_diegetic_music": "Gentle strings."
  }
}
```

A successful case reports:

- `schema_pass`: output satisfies the strict Pydantic and H3 grammar.
- `timeline_pass`: at least one valid shot exists.
- `field_completeness` and `missing_fields`.
- rendered character, shot, timed-shot, and reference counts.
- unique, defined, and undefined references.
- resolved output task.

An invalid case reports structured validation errors plus conservative failure metrics.

## JSONL manifests

Each non-empty line must be a JSON object accepted by the single-case evaluator:

```bash
omni-writer eval examples/fixtures/manifest.jsonl --manifest
```

The result contains every case with its source line number and an aggregate total/passed/failed
summary. The command exits nonzero if any case fails, the manifest is empty, or malformed input
prevents a case from validating. This makes it suitable for CI format-regression gates.

## Python interface

```python
from omni_writer.evaluator import BasicEvaluator

result = BasicEvaluator().evaluate(payload)
manifest_result = BasicEvaluator().evaluate_manifest("cases.jsonl")
```

Applications may supply a `Judge` implementation. Its JSON-serializable result is added under
`judge`, while deterministic metrics remain unchanged:

```python
from collections.abc import Mapping
from typing import Any


class MyJudge:
    def judge(
        self,
        payload: Mapping[str, Any],
        deterministic_result: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        return {"review_required": deterministic_result["metrics"]["shot_count"] < 2}
```

Judge implementations are application-owned. If a judge calls a remote model, disclose that data
flow, pin the judge version/configuration, bound cost and retries, and do not compare its numbers
as if they were deterministic.

## Reproducible evaluation practice

1. Version the request set and expected acceptance criteria.
2. Keep model checkpoint, serving flags, prompts, Omni-Writer version, and sampling settings fixed.
3. Preserve raw writer responses separately from validated outputs, subject to privacy policy.
4. Run deterministic validation before expensive video generation.
5. For generated video, add blinded human review and/or separately validated perceptual metrics
   for prompt adherence, temporal consistency, reference retention, audio, artifacts, and safety.
6. Report failures and excluded samples; do not publish only aggregate pass rates.

## What the metrics do not prove

A passing output can still describe an implausible, unsafe, biased, copyrighted, or
prompt-inconsistent video. It can also perform differently across H3 service versions. Character
and shot counts are diagnostics, not quality scores. Undefined-reference checks cover local label
grammar, not whether the referenced identity is visually retained.
