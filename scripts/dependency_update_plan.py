import argparse
import json
from pathlib import Path

def make_plan(report):
    dependencies = report.get("dependencies")
    if not isinstance(dependencies, list) or not dependencies:
        raise ValueError("Audit report has no valid dependency list")

    skipped = []
    findings = []

    for dependency in dependencies:
        if dependency.get("skip_reason"):
            skipped.append({
                "name": dependency.get("name"),
                "reason": dependency["skip_reason"],
            })
            continue

        vulns = dependency.get("vulns")
        if not isinstance(vulns, list):
            raise ValueError("Dependency has no valid vulnerability list")

        for vulnerability in vulns:
            findings.append({
                "package": dependency["name"],
                "installed_version": dependency.get("version"),
                "vulnerability_id": vulnerability["id"],
                "aliases": vulnerability.get("aliases", []),
                "fix_versions": vulnerability.get("fix_versions", []),
            })

    if skipped:
        status = "manual_review"
    elif findings:
        status = "fix_planning_required"
    else:
        status = "no_update"

    return {
        "status": status,
        "dependency_count": len(dependencies),
        "findings": findings,
        "skipped": skipped,
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("audit_report")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with open(args.audit_report, encoding="utf-8") as f:
        plan = make_plan(json.load(f))

    Path(args.output).write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8"
    )
    print("Decision:", plan["status"])
    print("Vulnerability findings:", len(plan["findings"]))
    print("Skipped dependencies:", len(plan["skipped"]))

if __name__ == "__main__":
    main()
