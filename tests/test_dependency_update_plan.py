import importlib.util
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "dependency_update_plan.py"
)
spec = importlib.util.spec_from_file_location("dependency_update_plan", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
make_plan = module.make_plan


def test_clean_report_needs_no_update():
    report = {
        "dependencies": [
            {"name": "demo-package", "version": "1.0", "vulns": []}
        ]
    }

    plan = make_plan(report)

    assert plan["status"] == "no_update"
    assert plan["dependency_count"] == 1
    assert plan["findings"] == []
    assert plan["skipped"] == []


def test_vulnerability_requires_fix_planning():
    report = {
        "dependencies": [
            {
                "name": "demo-package",
                "version": "1.0",
                "vulns": [
                    {
                        "id": "TEST-ADVISORY-001",
                        "aliases": ["TEST-ALIAS-001"],
                        "fix_versions": ["1.1"],
                    }
                ],
            }
        ]
    }

    plan = make_plan(report)

    assert plan["status"] == "fix_planning_required"
    assert plan["findings"][0]["package"] == "demo-package"
    assert plan["findings"][0]["fix_versions"] == ["1.1"]


def test_skipped_dependency_requires_manual_review():
    report = {
        "dependencies": [
            {
                "name": "unknown-package",
                "skip_reason": "Example: package could not be audited",
            }
        ]
    }

    plan = make_plan(report)

    assert plan["status"] == "manual_review"
    assert len(plan["skipped"]) == 1


def test_vulnerability_without_fix_is_not_marked_clean():
    report = {
        "dependencies": [
            {
                "name": "demo-package",
                "version": "1.0",
                "vulns": [
                    {
                        "id": "TEST-ADVISORY-002",
                        "fix_versions": [],
                    }
                ],
            }
        ]
    }

    plan = make_plan(report)

    assert plan["status"] == "fix_planning_required"
    assert plan["findings"][0]["fix_versions"] == []


@pytest.mark.parametrize(
    "report",
    [
        {},
        {"dependencies": []},
        {"dependencies": "invalid"},
        {"dependencies": [{"name": "demo-package", "version": "1.0"}]},
    ],
)
def test_invalid_report_is_rejected(report):
    with pytest.raises(ValueError):
        make_plan(report)
