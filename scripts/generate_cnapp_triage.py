#!/usr/bin/env python3
"""Generate transparent, rule-based triage from a Trivy JSON report."""

import json
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SOURCE = BASE_DIR / "reports" / "trivy-image.json"
OUTPUT = BASE_DIR / "reports" / "cnapp" / "triage.json"

SEVERITY_PRIORITY = {
    "CRITICAL": 1,
    "HIGH": 2,
    "MEDIUM": 3,
    "LOW": 4,
    "UNKNOWN": 5,
}


def main():
    if not SOURCE.is_file():
        raise SystemExit(f"Trivy report not found: {SOURCE}")

    try:
        report = json.loads(SOURCE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Cannot read Trivy report: {exc}") from exc

    if not isinstance(report, dict) or not isinstance(report.get("Results"), list):
        raise SystemExit("Invalid Trivy report: expected a Results list")

    findings = []
    seen = set()

    for result in report["Results"]:
        if not isinstance(result, dict):
            continue

        target = result.get("Target", "Unknown target")
        result_type = result.get("Type", "unknown")

        for vulnerability in result.get("Vulnerabilities") or []:
            if not isinstance(vulnerability, dict):
                continue

            vuln_id = vulnerability.get("VulnerabilityID") or "UNKNOWN-ID"
            package = vulnerability.get("PkgName") or "unknown-package"
            installed = vulnerability.get("InstalledVersion") or "unknown"
            fixed = vulnerability.get("FixedVersion")
            severity = str(vulnerability.get("Severity") or "UNKNOWN").upper()

            # Avoid duplicate entries within this report.
            identity = (target, result_type, vuln_id, package, installed)
            if identity in seen:
                continue
            seen.add(identity)

            if severity not in SEVERITY_PRIORITY:
                severity = "UNKNOWN"

            if severity in {"CRITICAL", "HIGH"} and fixed:
                priority = "P1"
                recommendation = (
                    f"Plan an expedited upgrade of {package} to {fixed}; "
                    "validate compatibility and rerun the scan."
                )
            elif severity in {"CRITICAL", "HIGH"}:
                priority = "P1"
                recommendation = (
                    f"Investigate {package} urgently. Trivy reports no fixed "
                    "version; check vendor advisories and available mitigations."
                )
            elif severity == "MEDIUM" and fixed:
                priority = "P2"
                recommendation = (
                    f"Upgrade {package} to {fixed}, then rerun the scan."
                )
            elif severity == "MEDIUM":
                priority = "P2"
                recommendation = (
                    f"Review exposure and vendor guidance for {package}; "
                    "no fixed version is listed in this report."
                )
            elif severity == "LOW" and fixed:
                priority = "P3"
                recommendation = (
                    f"Schedule an upgrade of {package} to {fixed}."
                )
            elif severity == "LOW":
                priority = "P3"
                recommendation = (
                    f"Review the low-severity finding for {package}; "
                    "no fixed version is listed in this report."
                )
            else:
                priority = "P2"
                recommendation = (
                    f"Manually investigate the reported issue affecting "
                    f"{package}; its severity is unknown, so do not assume "
                    "it is low risk."
                )

            findings.append({
                "id": vuln_id,
                "package": package,
                "installed_version": installed,
                "fixed_version": fixed or None,
                "severity": severity,
                "priority": priority,
                "target": target,
                "target_type": result_type,
                "title": vulnerability.get("Title") or "",
                "recommendation": recommendation,
                "triage_method": "rule-based",
            })

    findings.sort(
        key=lambda item: (
            item["priority"],
            SEVERITY_PRIORITY.get(item["severity"], 5),
            item["package"],
            item["id"],
        )
    )

    output = {
        "schema_version": 1,
        "triage_method": "rule-based",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": str(SOURCE.relative_to(BASE_DIR)),
        "finding_count": len(findings),
        "findings": findings,
        "disclaimer": (
            "Priorities are rule-based recommendations, not AI-generated "
            "judgments. Validate exploitability, deployment exposure, and "
            "business impact before making remediation decisions."
        ),
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(output, indent=2) + "\n",
        encoding="utf-8",
    )

    counts = {}
    for finding in findings:
        key = finding["severity"]
        counts[key] = counts.get(key, 0) + 1

    print(f"Generated: {OUTPUT.relative_to(BASE_DIR)}")
    print(f"Findings triaged: {len(findings)}")
    print("Severity counts:", json.dumps(counts, sort_keys=True))
    print("Triage method: rule-based (not AI-generated)")


if __name__ == "__main__":
    main()
