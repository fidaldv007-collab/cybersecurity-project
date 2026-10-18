# Week 1 Contribution: Secure CI/CD and Supply Chain Security

## 1. Overview

This contribution implements a GitHub Actions CI/CD workflow for the DevSecOps demo application. The workflow automates application testing, security checks, SBOM generation, container image publishing, and Cosign image signing and verification.

## 2. CI/CD Security Controls

The workflow includes:

- Automated Python dependency installation and application tests.
- Bandit static application security testing.
- `pip-audit` dependency vulnerability scanning.
- Application health-check validation.
- GitHub Actions permissions for repository access and container publishing.

## 3. Software Bill of Materials (SBOM)

Syft/CycloneDX is integrated into the workflow to generate a software bill of materials. The generated SBOM is uploaded as a GitHub Actions artifact for review and auditing.

## 4. Container Image Publishing

The workflow builds the Docker image and publishes it to GitHub Container Registry (GHCR) on push events.

## 5. Cosign Image Signing and Verification

Cosign is integrated into the CI workflow to:

1. Sign the published container image using a private key stored in GitHub Actions secrets.
2. Verify the image signature using the repository's public key, `cosign.pub`.
3. Run verification against the image digest produced by the image-build step.

Private signing keys and passwords are stored as GitHub Actions secrets and must not be committed to the repository.

## 6. Validation Results

- Python application tests: 2 tests passed locally.
- Bandit: no issues reported in the validated application scan.
- `pip-audit`: no known vulnerabilities reported for the checked requirements at the time of testing.
- GitHub Actions: the automated signing and verification workflow completed successfully.

## 7. Known Limitations and Next Steps

- Review and narrow workflow permissions to the minimum required for each job or step.
- Confirm SBOM generation runs for every intended commit and covers the required dependency scope.
- Extend signing and verification to pipeline artifacts such as the SBOM if required.
- Review and remediate the container vulnerabilities identified by Trivy.
- Add deployment enforcement that rejects unsigned images when deployment enforcement is implemented.

## 8. Evidence

Repository: https://github.com/fidaldv007-collab/cybersecurity-project

Branch: `member3`

Workflow: GitHub Actions — DevSecOps CI
