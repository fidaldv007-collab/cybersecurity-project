# Week 2 Contribution: Security Assessment, SBOM Validation, and Policy Enforcement

## 1. Overview

This contribution completes the Week 2 DevSecOps security assessment and supply chain compliance checks for the `member4` branch of the `cybersecurity-project` repository. The work covers local vulnerability assessments, software bill of materials (SBOM) validation, static application security testing (SAST), custom policy enforcement using Open Policy Agent (OPA), and comprehensive documentation.

## 2. CI/CD & Local Security Controls

The local security evaluation includes:

- Static application security testing (SAST) on application source code using Bandit v1.9.4.
- Container filesystem and dependency vulnerability auditing using Trivy v0.66.0.
- Secret scanning across repository files to prevent sensitive data leakage.
- Local Open Policy Agent (OPA) policy creation for vulnerability-based deployment blocking.

All security tools were executed directly within the Kali Linux virtual environment to establish baseline security posture before branch integration.

## 3. Software Bill of Materials (SBOM)

The software supply chain inventory was generated using Syft to produce a standardized CycloneDX JSON SBOM (`sbom.json`).

- The local filesystem scan indexed all project components and cataloged **39 packages**.
- The generated SBOM provides clear visibility into third-party Python dependencies and structural components.
- The `sbom.json` file is retained locally in the workspace root for verification against build and deployment policies.

## 4. Static Application Security Testing (SAST) & Vulnerability Auditing

Local scans were conducted across the application codebase (`app/`) and dependency manifests (`requirements.txt`):

1. **Bandit SAST Triage:** Executed across Python source code in `app/`. The scan checked 8 lines of code and reported **0 security issues** across all severity levels (High, Medium, Low).
2. **Trivy Filesystem & Secret Scan:** Performed a full filesystem scan (`trivy fs .`) against `requirements.txt` via `pip`. Scanned packages showed **0 vulnerabilities** and **0 secret leaks**.

## 5. OPA Policy Enforcement

Open Policy Agent (OPA) policy enforcement was introduced under `policy/image_policy.rego` to define automated security guardrails:

1. Establishes default deny rules for container image deployment evaluation.
2. Formulates explicit `deny` logic that flags and blocks any deployment input containing `CRITICAL` severity vulnerabilities.
3. Provides an `allow` rule triggered only when zero critical findings are present in the scan input.

## 6. Validation Results

- **Trivy FS Scan:** Successfully downloaded vulnerability database (`mirror.gcr.io/aquasec/trivy-db:2`) and confirmed 0 vulnerabilities and 0 secrets in `requirements.txt`.
- **Syft SBOM:** Successfully indexed the repository and generated `sbom.json` containing 39 cataloged packages.
- **Bandit Triage:** Completed SAST scan on `app/` with 0 issues identified.
- **OPA Policy:** Created `policy/image_policy.rego` defining critical vulnerability guardrails.
- **Git Synchronization:** All local commits, security policies, generated SBOM, and documentation were successfully pushed to the remote branch.

Successful local validation confirms that the current codebase meets all defined Week 2 security criteria.

## 7. Known Limitations and Next Steps

- Expand Trivy scanning coverage to include full container image builds alongside filesystem scans.
- Integrate the custom OPA Rego policy directly into the main GitHub Actions CI workflow for automated PR evaluation.
- Perform automated testing of OPA policy evaluations using sample Trivy JSON scan outputs.
- Coordinate with team members to merge `member4` security enhancements into the main project pipeline.

## 8. Evidence

Repository: https://github.com/fidaldv007-collab/cybersecurity-project

Branch: `member4`

Author: Ananthu Harikumar (`ananthuharikumar36`)

Environment: Kali Linux (`ananthu@vbox`)

Documentation File: `docs/week2-contribution.md`
## 9. Post-Scan Vulnerability Remediation

After updating the Trivy vulnerability database, a rescan identified one CRITICAL vulnerability in `certifi` (GHSA-6q48-6c7w-9gw2).

The dependency was upgraded from `certifi==2026.7.22` to `certifi==2026.10.19` in `requirements.txt`.

A follow-up `trivy fs .` scan confirmed that the CRITICAL vulnerability was resolved and the project returned to a clean security state.
