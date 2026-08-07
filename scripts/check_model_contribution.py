#!/usr/bin/env python3
"""Validate the model-contribution contract used by local checks and GitHub PRs."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

CATEGORIES = ("Video", "Image", "Unified", "Not applicable")
BACKLOG_MODELS = (
    "Wan2.2",
    "HunyuanVideo",
    "CogVideoX",
    "LTX-Video",
    "Mochi 1",
    "Step-Video",
    "FLUX.1 / Kontext",
    "Stable Diffusion 3.5",
    "Kolors",
    "PixArt-Sigma",
    "Sana",
    "Show-o2",
    "Emu3",
    "Janus-Pro",
    "BAGEL",
    "OmniGen2",
)
REQUIRED_FIELDS = (
    "Model / family",
    "Public evidence URL",
    "Contribution scope",
    "PE status",
    "Adapter status",
    "Live runtime status",
)
PLACEHOLDERS = {"", "n/a", "none", "todo", "tbd", "-"}


def _field(body: str, name: str) -> str:
    match = re.search(
        rf"^- {re.escape(name)}:[ \t]*([^\r\n]*)$",
        body,
        flags=re.MULTILINE,
    )
    if match is None:
        return ""
    return re.sub(r"<!--.*?-->", "", match.group(1)).strip()


def validate_pr_body(body: str) -> list[str]:
    errors: list[str] = []
    selected = [
        category
        for category in CATEGORIES
        if re.search(
            rf"^\s*-\s*\[[xX]\]\s*{re.escape(category)}\s*$",
            body,
            flags=re.MULTILINE,
        )
    ]
    if len(selected) != 1:
        errors.append(
            "PR body must select exactly one model category: Video, Image, Unified, "
            "or Not applicable"
        )
        return errors
    if selected[0] == "Not applicable":
        return errors

    values = {name: _field(body, name) for name in REQUIRED_FIELDS}
    for name, value in values.items():
        if value.lower() in PLACEHOLDERS:
            errors.append(f"PR body field '{name}' must be completed for model contributions")

    evidence = values["Public evidence URL"]
    if evidence and not re.search(r"https://", evidence):
        errors.append("Public evidence URL must include at least one https:// link")

    allowed_scope = {
        "routing",
        "schema",
        "profile",
        "validator",
        "renderer",
        "fixtures",
        "adapter",
    }
    scope_tokens = set(re.findall(r"[a-z_]+", values["Contribution scope"].lower()))
    if values["Contribution scope"] and not scope_tokens.intersection(allowed_scope):
        errors.append(
            "Contribution scope must name at least one of: "
            + ", ".join(sorted(allowed_scope))
        )
    return errors


def changed_files(root: Path, base_sha: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base_sha}...HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def validate_changed_files(body: str, files: list[str]) -> list[str]:
    selected_model_category = any(
        re.search(rf"^\s*-\s*\[[xX]\]\s*{category}\s*$", body, flags=re.MULTILINE)
        for category in CATEGORIES[:3]
    )
    if not selected_model_category:
        return []

    errors: list[str] = []
    if not any(path.startswith("tests/") and path.endswith(".py") for path in files):
        errors.append("Model contributions must add or update a Python test under tests/")
    if not any(
        path.startswith("docs/") or path in {"README.md", "README_zh.md", "ROADMAP.md"}
        for path in files
    ):
        errors.append("Model contributions must update documentation or the support/backlog matrix")
    return errors


def validate_repository(root: Path) -> list[str]:
    errors: list[str] = []
    required = (
        root / "docs/community-models.md",
        root / "docs/community-models_zh.md",
        root / ".cursor/skills/omni-rewriter-model-contribution/SKILL.md",
        root / ".cursor/skills/omni-rewriter-model-contribution/CONTRIBUTION_TEMPLATE.md",
    )
    for path in required:
        if not path.is_file():
            errors.append(f"Missing contribution file: {path.relative_to(root)}")

    for relative in ("docs/community-models.md", "docs/community-models_zh.md"):
        path = root / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for category in ("Video", "Image", "Unified"):
            if category not in text:
                errors.append(f"{relative} is missing the {category} board")
        for model in BACKLOG_MODELS:
            if model not in text:
                errors.append(f"{relative} is missing backlog model {model}")

    readme_sections = {
        "README.md": "## Model ecosystem",
        "README_zh.md": "## 模型生态",
    }
    for relative, section in readme_sections.items():
        text = (root / relative).read_text(encoding="utf-8")
        if section not in text:
            errors.append(f"{relative} is missing the unified model ecosystem section")
        for model in BACKLOG_MODELS:
            if model not in text:
                errors.append(f"{relative} is missing community backlog model {model}")
    return errors


def _load_event(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("GitHub event payload must be a JSON object")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--event", type=Path)
    parser.add_argument("--base-sha")
    args = parser.parse_args()

    root = args.root.resolve()
    errors = validate_repository(root)
    event_path = args.event
    if event_path is None and os.getenv("GITHUB_EVENT_PATH"):
        event_path = Path(os.environ["GITHUB_EVENT_PATH"])

    if event_path is not None:
        event = _load_event(event_path)
        pull_request = event.get("pull_request")
        if isinstance(pull_request, dict):
            body = pull_request.get("body")
            body_text = body if isinstance(body, str) else ""
            errors.extend(validate_pr_body(body_text))
            base_sha = args.base_sha
            if base_sha is None:
                base = pull_request.get("base")
                if isinstance(base, dict) and isinstance(base.get("sha"), str):
                    base_sha = base["sha"]
            if base_sha:
                errors.extend(
                    validate_changed_files(body_text, changed_files(root, base_sha))
                )

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Model contribution contract: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
