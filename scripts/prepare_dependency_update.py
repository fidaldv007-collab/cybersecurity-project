import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Prepare dependency fixes in a temporary working copy."
    )
    parser.add_argument("plan")
    parser.add_argument("--requirements", default="requirements.txt")
    parser.add_argument("--result-json")
    args = parser.parse_args()

    result_path = (
        Path(args.result_json).resolve() if args.result_json else None
    )
    if result_path:
        protected = {
            Path(args.plan).resolve(),
            Path(args.requirements).resolve(),
        }
        if result_path in protected:
            raise SystemExit("ERROR: Result must not overwrite input files")
        result_path.unlink(missing_ok=True)

    def write_result(status, candidate_path=None):
        if result_path:
            result_path.write_text(
                json.dumps({
                    "status": status,
                    "candidate_path": candidate_path,
                }, indent=2) + "\n",
                encoding="utf-8",
            )

    with open(args.plan, encoding="utf-8") as f:
        plan = json.load(f)

    status = plan.get("status")
    findings = plan.get("findings")
    skipped = plan.get("skipped")

    if not isinstance(findings, list) or not isinstance(skipped, list):
        raise SystemExit("ERROR: Invalid update plan")

    if skipped or status == "manual_review":
        raise SystemExit("STOP: Manual review required")

    if status == "no_update":
        if findings:
            raise SystemExit("ERROR: Inconsistent update plan")
        write_result("no_update")
        print("No update needed; requirements unchanged; no PR needed.")
        return

    if status != "fix_planning_required" or not findings:
        raise SystemExit("ERROR: Unsupported or inconsistent update plan")

    if any(not finding.get("fix_versions") for finding in findings):
        raise SystemExit(
            "STOP: At least one vulnerability has no listed fix; review required"
        )

    source = Path(args.requirements).resolve()
    if not source.is_file():
        raise SystemExit("ERROR: Requirements file not found")

    workspace = Path(tempfile.mkdtemp(prefix="dependency-update-"))
    candidate = workspace / "requirements.txt"
    shutil.copy2(source, candidate)

    print(f"Temporary candidate: {candidate}", flush=True)

    result = subprocess.run(
        [
            sys.executable, "-m", "pip_audit",
            "-r", str(candidate), "--fix",
        ],
        check=False,
    )

    if result.returncode != 0:
        raise SystemExit(
            "STOP: Fix attempt did not complete cleanly; do not use candidate"
        )

    if candidate.read_bytes() == source.read_bytes():
        raise SystemExit("STOP: No dependency changes were produced")

    write_result("candidate_prepared", str(candidate))
    print("Candidate prepared; fresh audit and application tests still required.")
    print("Original requirements unchanged. No PR created.")


if __name__ == "__main__":
    main()
