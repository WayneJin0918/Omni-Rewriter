from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType


def _load_checker() -> ModuleType:
    path = Path(__file__).parents[1] / "scripts/check_model_contribution.py"
    spec = importlib.util.spec_from_file_location("check_model_contribution", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CHECKER = _load_checker()


def test_non_model_pr_requires_exactly_one_category() -> None:
    body = """
- Category:
  - [ ] Video
  - [ ] Image
  - [ ] Unified
  - [x] Not applicable
"""
    assert CHECKER.validate_pr_body(body) == []


def test_model_pr_requires_contract_fields() -> None:
    body = """
- Category:
  - [x] Video
  - [ ] Image
  - [ ] Unified
  - [ ] Not applicable
- Model / family:
- Public evidence URL:
- Contribution scope:
- PE status:
- Adapter status:
- Live runtime status:
"""
    errors = CHECKER.validate_pr_body(body)
    assert len(errors) == 6


def test_complete_model_pr_contract_passes() -> None:
    body = """
- Category:
  - [ ] Video
  - [x] Image
  - [ ] Unified
  - [ ] Not applicable
- Model / family: FLUX.1 Kontext
- Public evidence URL: https://github.com/black-forest-labs/flux
- Contribution scope: profile / validator / renderer / fixtures
- PE status: implemented
- Adapter status: not included
- Live runtime status: not tested
"""
    assert CHECKER.validate_pr_body(body) == []


def test_model_pr_requires_tests_and_docs() -> None:
    body = "- [x] Unified"
    errors = CHECKER.validate_changed_files(body, ["src/omni_rewriter/prompts.py"])
    assert errors == [
        "Model contributions must add or update a Python test under tests/",
        "Model contributions must update documentation or the support/backlog matrix",
    ]
