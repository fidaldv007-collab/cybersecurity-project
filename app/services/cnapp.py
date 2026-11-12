import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]


def load_json(path: Path):
    """Load a JSON artifact safely."""
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        return None


def get_sbom_summary():
    """Summarize the application's CycloneDX SBOM."""
    path = BASE_DIR / "sbom.cyclonedx.json"
    sbom = load_json(path)

    if not isinstance(sbom, dict):
        return {
            "status": "unknown",
            "components": 0,
            "source": str(path.relative_to(BASE_DIR)),
        }

    components = sbom.get("components", [])

    return {
        "status": "available",
        "components": len(components) if isinstance(components, list) else 0,
        "source": str(path.relative_to(BASE_DIR)),
    }


def get_vulnerability_summary():
    """Summarize findings from the available Trivy image report."""
    path = BASE_DIR / "reports" / "trivy-image.json"
    report = load_json(path)

    summary = {
        "status": "unknown",
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "unknown": 0,
        "source": str(path.relative_to(BASE_DIR)),
    }

    if not isinstance(report, dict):
        return summary

    results = report.get("Results", [])
    if not isinstance(results, list):
        return summary

    for result in results:
        if not isinstance(result, dict):
            continue

        vulnerabilities = result.get("Vulnerabilities") or []
        if not isinstance(vulnerabilities, list):
            continue

        for vulnerability in vulnerabilities:
            if not isinstance(vulnerability, dict):
                continue

            severity = str(vulnerability.get("Severity", "UNKNOWN")).upper()
            key = severity.lower()

            if key in summary and key != "status" and key != "source":
                summary[key] += 1
            else:
                summary["unknown"] += 1

    summary["status"] = "available"
    return summary


def get_triage_summary():
    """Read generated triage records without claiming they are AI-generated."""
    path = BASE_DIR / "reports" / "cnapp" / "triage.json"
    data = load_json(path)

    if not isinstance(data, dict) or not isinstance(data.get("findings"), list):
        return {
            "status": "unknown",
            "method": "rule-based",
            "findings": [],
            "count": 0,
            "source": str(path.relative_to(BASE_DIR)),
            "message": "No valid triage artifact is available.",
        }

    findings = [
        item for item in data["findings"]
        if isinstance(item, dict)
    ]

    return {
        "status": "available",
        "method": data.get("triage_method", "unknown"),
        "findings": findings,
        "count": len(findings),
        "source": str(path.relative_to(BASE_DIR)),
        "generated_at": data.get("generated_at"),
        "disclaimer": data.get("disclaimer", ""),
    }


def get_signature_summary():
    """Load saved Cosign evidence without treating missing evidence as success."""
    path = BASE_DIR / "reports" / "cnapp" / "signature-verification.json"
    record = load_json(path)

    if not isinstance(record, dict):
        return {
            "status": "unknown",
            "message": "No saved signature verification record is available.",
        }

    required = ("image", "digest", "verification_method", "verified_at")
    if (
        record.get("status") != "verified"
        or record.get("artifact_type") != "container_image"
        or not all(isinstance(record.get(key), str) and record[key] for key in required)
        or not record["digest"].startswith("sha256:")
    ):
        return {
            "status": "unknown",
            "message": "The signature verification record is incomplete or invalid.",
        }

    return {
        "status": "verified",
        "image": record["image"],
        "digest": record["digest"],
        "verification_method": record["verification_method"],
        "verified_at": record["verified_at"],
        "message": (
            "A saved successful Cosign verification record is available. "
            "This dashboard does not re-run Cosign automatically."
        ),
    }


def get_dashboard_data():
    """Collect the currently available CNAPP data sources."""
    return {
        "sbom": get_sbom_summary(),
        "vulnerabilities": get_vulnerability_summary(),
        "ai_triage": get_triage_summary(),
        "signature_verification": get_signature_summary(),
    }
