# Omni-Rewriter repository-understanding baseline

**Source:** [`e4613085f5f3b0213cb567e3f1e6021ea7c22ead`](https://github.com/WayneJin0918/Omni-Rewriter/tree/e4613085f5f3b0213cb567e3f1e6021ea7c22ead) (`main` at intake)
**Mode:** static-only; generated from Git objects, not mutable working-tree source bytes.

## What it is
Omni-Rewriter is a Python 3.11+ typed prompt-expansion harness: a `RewriteRequest` is analyzed by an OpenAI-compatible Writer, drafted into a profile-specific JSON structure, deterministically validated and boundedly repaired, then rendered to prompt text/JSON. The checked-in architecture explicitly separates `expand` from media generation: adapters are optional, explicit consumers of rendered output ([`docs/architecture.md:3-10`](../../../architecture.md#scope), [`src/omni_rewriter/service.py:29-42`](../../../../src/omni_rewriter/service.py)).

## Entry points and static flow
- **CLI:** `omni-rewriter` binds to `omni_rewriter.cli:main` ([`pyproject.toml:62-63`](../../../../pyproject.toml), [`src/omni_rewriter/cli.py:52-107`](../../../../src/omni_rewriter/cli.py)). It exposes `expand`, `validate`, `eval`, and `reconstruct`.
- **HTTP:** optional FastAPI app factory `create_app` wires `/health`, `/v1/expand`, `/v1/validate`, and `/v1/reconstruct` ([`src/omni_rewriter/api.py:29-112`](../../../../src/omni_rewriter/api.py)).
- **Core lifecycle:** `service.expand` composes an `OpenAICompatibleBackend`, `MediaPreparer`, and `RewriteAgent` ([`src/omni_rewriter/service.py:29-42`](../../../../src/omni_rewriter/service.py)); the agent implements Analyze → Draft → Validate → bounded Repair → Complete ([`src/omni_rewriter/agent.py:102-246`](../../../../src/omni_rewriter/agent.py)).
- **Typed profiles:** strict request routing chooses H3, Seedance, LTX, Seedream, or Qwen-Image output paths ([`src/omni_rewriter/models/request.py:34-102`](../../../../src/omni_rewriter/models/request.py), [`src/omni_rewriter/agent.py:105-128`](../../../../src/omni_rewriter/agent.py)).
- **Reconstruction:** a local clip can be statically traced through evidence-pack → `VideoObservation` → H3 `t2va` request; source video is not inlined into `expand` ([`src/omni_rewriter/reconstruct/service.py:28-96`](../../../../src/omni_rewriter/reconstruct/service.py)).

## Trust boundaries visible in source
Caller input and local/remote/data-URI media cross `MediaPreparer`, which imposes MIME/byte limits and rejects non-public resolved remote addresses by default ([`src/omni_rewriter/media_input.py:46-54`](../../../../src/omni_rewriter/media_input.py), [`src/omni_rewriter/media_input.py:195-212`](../../../../src/omni_rewriter/media_input.py)). The API factory disables local-file media unless an environment variable is enabled ([`src/omni_rewriter/api.py:20-46`](../../../../src/omni_rewriter/api.py)). Backend and adapter results are treated as separately validated/error-mapped boundaries in source. The FastAPI factory itself contains no built-in authentication, authorization, rate limiting, moderation, or TLS according to the architecture document ([`docs/architecture.md:155-164`](../../../architecture.md)).

## Quality and delivery surface
The repository ships a composite GitHub Action that installs the package and validates JSON envelopes ([`action.yml:25-56`](../../../../action.yml)); CI statically declares model-contribution checks, ruff, mypy, pytest/coverage, and a distribution build ([`.github/workflows/ci.yml:15-43`](../../../../.github/workflows/ci.yml)). Tests/fixtures and docs are substantial repository components; gallery media is tracked presentation material and was not semantically parsed.

## Graph artifacts
- [Knowledge graph](../../../../.understand-anything/knowledge-graph.json) — SHA-256 `5f0c62d58c42571df329a7e57ed0cbc6a9fccb1af4585edc27f6a9cf3f3cd5f3`
- [Domain graph](../../../../.understand-anything/domain-graph.json) — SHA-256 `66334cb6cf848d6bf8d44ff3916d554ef424a510aa011df137852dcb82d06c05`
- [Metadata](../../../../.understand-anything/meta.json)

## Deliberately not run
No dependency installation, package import, project script, test, server, dashboard, ffmpeg process, model runtime, generation adapter, or external/provider API was executed. This baseline therefore documents static structure and declared contracts only—not live reachability, compatibility, operational readiness, or model quality.
