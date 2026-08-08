from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from fastapi.testclient import TestClient
from typer.testing import CliRunner

from omni_rewriter.agent import AnalysisPlan, RewriteResult
from omni_rewriter.api import create_app
from omni_rewriter.cli import app
from omni_rewriter.config import Settings
from omni_rewriter.errors import BackendResponseError
from omni_rewriter.evaluator import BasicEvaluator
from omni_rewriter.models import BaseRewrite


def result(
    base_output: dict[str, Any],
    analysis_output: dict[str, Any],
) -> RewriteResult:
    return RewriteResult(
        output=BaseRewrite.model_validate(base_output),
        analysis=AnalysisPlan.model_validate(analysis_output),
        repairs=0,
        run_id="run-1",
    )


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def test_cli_validate_and_h3(tmp_path: Path, base_output: dict[str, Any]) -> None:
    source = tmp_path / "output.json"
    write_json(source, base_output)
    runner = CliRunner()
    response = runner.invoke(app, ["validate", str(source)])
    assert response.exit_code == 0
    assert json.loads(response.stdout)["valid"] is True
    rendered = runner.invoke(app, ["validate", str(source), "--output", "h3"])
    assert rendered.exit_code == 0
    assert "integrated_multimodal_description:" in rendered.stdout


def test_cli_validate_failure(tmp_path: Path) -> None:
    source = tmp_path / "bad.json"
    write_json(source, {"task": "t2va"})
    response = CliRunner().invoke(app, ["validate", str(source)])
    assert response.exit_code == 1
    assert '"valid": false' in response.stderr


def test_cli_eval_and_manifest(tmp_path: Path, base_output: dict[str, Any]) -> None:
    source = tmp_path / "output.json"
    write_json(source, base_output)
    response = CliRunner().invoke(app, ["eval", str(source)])
    assert response.exit_code == 0
    assert json.loads(response.stdout)["metrics"]["schema_pass"] is True

    manifest = tmp_path / "cases.jsonl"
    manifest.write_text(
        json.dumps(base_output) + "\n" + json.dumps({"task": "t2va"}) + "\n",
        encoding="utf-8",
    )
    batch = CliRunner().invoke(app, ["eval", str(manifest), "--manifest"])
    assert batch.exit_code == 1
    assert json.loads(batch.stdout)["summary"] == {"total": 2, "passed": 1, "failed": 1}


def test_cli_expand(
    monkeypatch: Any,
    tmp_path: Path,
    base_output: dict[str, Any],
    analysis_output: dict[str, Any],
) -> None:
    async def fake_expand(*_: Any) -> RewriteResult:
        return result(base_output, analysis_output)

    monkeypatch.setattr("omni_rewriter.cli.expand_service", fake_expand)
    source = tmp_path / "request.json"
    write_json(source, {"prompt": "A kite rises.", "duration_seconds": 6})
    response = CliRunner().invoke(app, ["expand", str(source)])
    assert response.exit_code == 0
    assert json.loads(response.stdout)["run_id"] == "run-1"


def test_fastapi_endpoints(
    base_output: dict[str, Any],
    analysis_output: dict[str, Any],
) -> None:
    async def fake_expand(*_: Any) -> RewriteResult:
        return result(base_output, analysis_output)

    client = TestClient(create_app(Settings(), expander=fake_expand))
    assert client.get("/health").json() == {"status": "ok"}
    expanded = client.post(
        "/v1/expand",
        json={"prompt": "A kite rises.", "duration_seconds": 6},
    )
    assert expanded.status_code == 200
    assert expanded.json()["run_id"] == "run-1"
    validated = client.post("/v1/validate", json=base_output)
    assert validated.status_code == 200
    assert validated.json()["valid"] is True
    invalid = client.post("/v1/validate", json={"task": "t2va"})
    assert invalid.status_code == 422


def test_fastapi_maps_backend_error() -> None:
    async def fail(*_: Any) -> RewriteResult:
        raise BackendResponseError("offline")

    response = TestClient(create_app(Settings(), expander=fail)).post(
        "/v1/expand",
        json={"prompt": "A kite rises.", "duration_seconds": 6},
    )
    assert response.status_code == 502
    assert response.json()["detail"] == "offline"


def test_evaluator_metrics_and_optional_judge(base_output: dict[str, Any]) -> None:
    class LocalJudge:
        def judge(
            self,
            payload: Mapping[str, Any],
            deterministic_result: Mapping[str, Any],
        ) -> Mapping[str, Any]:
            assert payload
            assert deterministic_result["valid"]
            return {"coherence": 1.0}

    evaluation = BasicEvaluator(LocalJudge()).evaluate(base_output)
    assert evaluation["metrics"]["field_completeness"] == 1.0
    assert evaluation["metrics"]["timeline_pass"] is True
    assert evaluation["metrics"]["shot_count"] == 2
    assert evaluation["judge"] == {"coherence": 1.0}


def test_evaluator_manifest_parse_error(
    tmp_path: Path,
    base_output: dict[str, Any],
) -> None:
    manifest = tmp_path / "bad.jsonl"
    manifest.write_text(json.dumps(base_output) + "\n{bad\n", encoding="utf-8")
    result_value = BasicEvaluator().evaluate_manifest(manifest)
    assert result_value["summary"] == {"total": 2, "passed": 1, "failed": 1}
    assert result_value["cases"][1]["line"] == 2


def test_original_example_manifest() -> None:
    manifest = Path(__file__).parents[1] / "tests" / "fixtures" / "manifest.jsonl"
    result_value = BasicEvaluator().evaluate_manifest(manifest)
    assert result_value["valid"] is True
    assert result_value["summary"] == {"total": 5, "passed": 5, "failed": 0}
