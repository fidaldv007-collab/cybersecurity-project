# Week 1 Contribution: Secure CI/CD and Supply Chain Security

## 1. Overview

This contribution implements a GitHub Actions CI/CD pipeline for the DevSecOps demo application. The pipeline automates application testing, security scanning, CycloneDX SBOM generation, container image publishing, and cryptographic signing and verification.

## 2. CI/CD Security Controls

The workflow includes:

- Automated Python dependency installation and application tests using pytest.
- Static application security testing using Bandit.
- Dependency vulnerability auditing using `pip-audit`.
- An automated application health check.
- Job-level permissions to follow the principle of least privilege.

The workflow separates testing and scanning from container publishing and signing. The testing job has read-only repository permissions, while the publishing job receives package-write permission when required.

## 3. Software Bill of Materials (SBOM)

The workflow generates a CycloneDX JSON SBOM using the Anchore SBOM GitHub Action, which uses Syft for software inventory generation.

The SBOM is uploaded as a GitHub Actions artifact and transferred to the publishing job. It is then cryptographically signed using Cosign and verified using the repository's public key.

The artifact is retained for 14 days.

## 4. Container Image Publishing

The workflow builds the Docker image and publishes it to GitHub Container Registry (GHCR) on push events to the configured branches.

The publishing job uses the image digest produced by the build action for signing and verification. This binds verification to the specific image content rather than relying only on a mutable tag.

## 5. Cosign Image Signing and Verification

Cosign is integrated into the pipeline to:

1. Sign the published container image using a private key stored in GitHub Actions secrets.
2. Sign the generated SBOM and produce a signature bundle.
3. Verify the container image signature using `cosign.pub`.
4. Verify the SBOM signature bundle against the original SBOM using `cosign.pub`.

The private signing key and its password are stored in GitHub Actions secrets. The private key must never be committed to the repository. Only the public verification key is committed.

## 6. Validation Results

- **Automated tests:** Two application tests are included.
- **Bandit:** Previously reported no issues in the validated application scan.
- **Dependency audit:** `pip-audit` previously reported no known vulnerabilities for the checked requirements at the time of testing.
- **SBOM generation:** Integrated into the testing job.
- **Image signing:** Integrated into the publishing job.
- **SBOM signing:** Integrated using Cosign's blob-signing functionality.
- **Signature verification:** Image and SBOM verification steps are integrated into the workflow.
- **GitHub Actions:** The updated workflow completed successfully after the job separation and signing changes.

Successful workflow execution confirms that the configured steps passed for that run. It does not establish that the container image is free from vulnerabilities.

## 7. Known Limitations and Next Steps

- Review workflow permissions and action permissions further, including whether individual steps can use narrower permissions.
- Confirm the required SBOM coverage for every intended commit and pull request.
- Review and assess the high-severity container vulnerabilities previously identified by Trivy; document remediation decisions and any accepted risks.
- Add policy enforcement to reject unsigned images and images that fail defined vulnerability thresholds before deployment.
- Extend supply-chain controls to additional pipeline artifacts if required by the project specification.
- Document test evidence, false positives, remediation results, and known detection gaps.

## 8. Evidence

Repository: https://github.com/fidaldv007-collab/cybersecurity-project

Branch: `member3`

Workflow: GitHub Actions — DevSecOps CI

Latest workflow change commit: `ec769f1`




---

# Week 4 — Task 1: Unified CNAPP Dashboard

## Objective

Implement a unified Cloud-Native Application Protection Platform (CNAPP) dashboard that consolidates SBOM data, container vulnerability findings, signature-verification evidence, and security triage results.

## Work Completed

### 1. Dashboard and API

Implemented the dashboard and API functionality in `app/main.py`, with data consolidation handled by `app/services/cnapp.py`.

Endpoints:

- `/` — application root
- `/health` — health check
- `/api/cnapp` — consolidated CNAPP data in JSON format
- `/dashboard` — CNAPP dashboard interface

### 2. SBOM Integration

Integrated component information from `sbom.cyclonedx.json` into the dashboard.

### 3. Vulnerability Findings

Integrated Trivy scan results from `reports/trivy-image.json`, with severity-based summaries.

The report used during implementation contained 172 findings:

| Severity | Count |
|---|---:|
| Critical | 0 |
| High | 48 |
| Medium | 60 |
| Low | 61 |
| Unknown | 3 |
| Total | 172 |

These counts describe the report used during testing and may change when the scan is regenerated.

### 4. Security Triage

Implemented `scripts/generate_cnapp_triage.py` to generate `reports/cnapp/triage.json` from Trivy findings.

The current triage logic uses rule-based priority assignments:

- Critical and High → P1
- Medium and Unknown → P2
- Low → P3

Unknown-severity findings are flagged for manual investigation.

**Limitation:** This is rule-based triage, not genuine AI-generated analysis. AI model or service integration remains outstanding if required by the assignment.

### 5. Signature-Verification Evidence

Integrated saved Cosign verification evidence from `reports/cnapp/signature-verification.json`.

The dashboard displays the recorded image, digest, verification method, timestamp, and status.

The displayed result is historical evidence; loading the dashboard does not execute Cosign or re-verify the image.

### 6. Automated Tests

Updated `tests/test_main.py` to cover the application routes, CNAPP API response, and dashboard.

Local validation completed successfully:

- Four automated tests passed.
- `/dashboard` returned HTTP 200.
- `/api/cnapp` returned HTTP 200 and valid JSON.
- `/health` returned HTTP 200.
- `git diff --cached --check` passed before the implementation commit.

### 7. CI Workflow

Updated `.github/workflows/ci.yml` to upload SBOM and signature-related evidence as a GitHub Actions artifact with a 14-day retention period.

The remote workflow should be checked in GitHub Actions to confirm successful execution and artifact upload.

## Files Added or Modified

- `app/main.py`
- `app/services/cnapp.py`
- `reports/cnapp/signature-verification.json`
- `reports/cnapp/triage.json`
- `scripts/generate_cnapp_triage.py`
- `tests/test_main.py`
- `.github/workflows/ci.yml`

## Git Details

- Branch: `member3`
- Implementation commit: `370e2e7`
- Commit message: `feat: add unified CNAPP security dashboard`
- Status: committed and pushed to the remote branch

## Recommended Follow-Up

1. Confirm whether actual AI-generated triage is required.
2. If required, implement and validate an AI integration while distinguishing model-generated recommendations from rule-based priorities.
3. Verify the CI workflow and artifact upload in GitHub Actions.
4. Re-run Cosign verification when appropriate and refresh the saved evidence.
5. Coordinate further changes with the team before merging into the integration branch.

## Summary

The CNAPP dashboard consolidates SBOM information, vulnerability findings, signature-verification evidence, and rule-based security triage. Local endpoint checks and automated tests passed. Genuine AI triage and remote CI validation remain follow-up items.
