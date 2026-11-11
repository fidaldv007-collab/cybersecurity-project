import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "prepare_dependency_update.py"
)
spec = importlib.util.spec_from_file_location("prepare_dependency_update", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def configure(tmp_path, monkeypatch, plan):
    plan_file = tmp_path / "plan.json"
    plan_file.write_text(json.dumps(plan), encoding="utf-8")

    requirements = tmp_path / "requirements.txt"
    requirements.write_text("demo-package==1.0\n", encoding="utf-8")

    monkeypatch.setattr(sys, "argv", [
        "prepare_dependency_update.py",
        str(plan_file),
        "--requirements", str(requirements),
    ])

    def unexpected_run(*args, **kwargs):
        pytest.fail("Unexpected subprocess execution")

    monkeypatch.setattr(module.subprocess, "run", unexpected_run)

    def temporary_workspace(**kwargs):
        workspace = tmp_path / "candidate"
        workspace.mkdir()
        return str(workspace)

    monkeypatch.setattr(module.tempfile, "mkdtemp", temporary_workspace)
    return requirements


def fix_plan():
    return {
        "status": "fix_planning_required",
        "findings": [{
            "package": "demo-package",
            "installed_version": "1.0",
            "vulnerability_id": "TEST-ONLY-001",
            "fix_versions": ["1.1"],
        }],
        "skipped": [],
    }


def test_no_update_does_not_run_fixer(tmp_path, monkeypatch, capsys):
    original = configure(tmp_path, monkeypatch, {
        "status": "no_update",
        "findings": [],
        "skipped": [],
    })

    module.main()

    assert original.read_text() == "demo-package==1.0\n"
    assert not (tmp_path / "candidate").exists()
    assert "No update needed" in capsys.readouterr().out


def test_manual_review_stops(tmp_path, monkeypatch):
    configure(tmp_path, monkeypatch, {
        "status": "manual_review",
        "findings": [],
        "skipped": [{"name": "unknown-package"}],
    })

    with pytest.raises(SystemExit, match="Manual review"):
        module.main()


def test_missing_fix_stops(tmp_path, monkeypatch):
    plan = fix_plan()
    plan["findings"][0]["fix_versions"] = []
    configure(tmp_path, monkeypatch, plan)

    with pytest.raises(SystemExit, match="no listed fix"):
        module.main()


def test_fix_changes_copy_not_original(tmp_path, monkeypatch):
    original = configure(tmp_path, monkeypatch, fix_plan())

    def fake_fix(command, check):
        assert command[:3] == [sys.executable, "-m", "pip_audit"]
        assert "--fix" in command
        candidate = Path(command[command.index("-r") + 1])
        assert candidate != original
        candidate.write_text("demo-package==1.1\n", encoding="utf-8")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(module.subprocess, "run", fake_fix)

    module.main()

    assert original.read_text() == "demo-package==1.0\n"
    assert (tmp_path / "candidate" / "requirements.txt").read_text() == (
        "demo-package==1.1\n"
    )


def test_failed_fixer_stops(tmp_path, monkeypatch):
    original = configure(tmp_path, monkeypatch, fix_plan())
    monkeypatch.setattr(
        module.subprocess, "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=1),
    )

    with pytest.raises(SystemExit, match="did not complete cleanly"):
        module.main()

    assert original.read_text() == "demo-package==1.0\n"


def test_unchanged_candidate_stops(tmp_path, monkeypatch):
    configure(tmp_path, monkeypatch, fix_plan())
    monkeypatch.setattr(
        module.subprocess, "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0),
    )

    with pytest.raises(SystemExit, match="No dependency changes"):
        module.main()


def test_inconsistent_no_update_stops(tmp_path, monkeypatch):
    plan = fix_plan()
    plan["status"] = "no_update"
    configure(tmp_path, monkeypatch, plan)

    with pytest.raises(SystemExit, match="Inconsistent"):
        module.main()


def test_no_update_writes_json_result(tmp_path, monkeypatch):
    configure(tmp_path, monkeypatch, {
        "status": "no_update",
        "findings": [],
        "skipped": [],
    })
    result_file = tmp_path / "result.json"
    monkeypatch.setattr(
        sys, "argv",
        [*sys.argv, "--result-json", str(result_file)],
    )

    module.main()

    assert json.loads(result_file.read_text()) == {
        "status": "no_update",
        "candidate_path": None,
    }


def test_prepared_candidate_writes_json_result(tmp_path, monkeypatch):
    original = configure(tmp_path, monkeypatch, fix_plan())
    result_file = tmp_path / "result.json"
    monkeypatch.setattr(
        sys, "argv",
        [*sys.argv, "--result-json", str(result_file)],
    )

    def fake_fix(command, check):
        candidate = Path(command[command.index("-r") + 1])
        candidate.write_text("demo-package==1.1\n", encoding="utf-8")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(module.subprocess, "run", fake_fix)

    module.main()

    result = json.loads(result_file.read_text())
    assert result["status"] == "candidate_prepared"
    assert Path(result["candidate_path"]).read_text() == (
        "demo-package==1.1\n"
    )
    assert original.read_text() == "demo-package==1.0\n"


def test_failed_run_removes_stale_json_result(tmp_path, monkeypatch):
    configure(tmp_path, monkeypatch, fix_plan())
    result_file = tmp_path / "result.json"
    result_file.write_text(
        '{"status": "candidate_prepared", "candidate_path": "/old/path"}',
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys, "argv",
        [*sys.argv, "--result-json", str(result_file)],
    )
    monkeypatch.setattr(
        module.subprocess, "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=1),
    )

    with pytest.raises(SystemExit, match="did not complete cleanly"):
        module.main()

    assert not result_file.exists()


@pytest.mark.parametrize("protected_input", ["requirements.txt", "plan.json"])
def test_json_result_cannot_overwrite_inputs(
    tmp_path, monkeypatch, protected_input
):
    configure(tmp_path, monkeypatch, {
        "status": "no_update",
        "findings": [],
        "skipped": [],
    })
    protected = tmp_path / protected_input
    before = protected.read_bytes()
    monkeypatch.setattr(
        sys, "argv",
        [*sys.argv, "--result-json", str(protected)],
    )

    with pytest.raises(SystemExit, match="must not overwrite input"):
        module.main()

    assert protected.read_bytes() == before
