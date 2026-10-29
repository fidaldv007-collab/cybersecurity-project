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
