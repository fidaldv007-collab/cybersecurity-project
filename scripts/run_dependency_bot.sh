# Week 3 demo trigger marker
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
AUDIT_PYTHON="${AUDIT_PYTHON:-python3}"
SBOM="${1:?Usage: bash scripts/run_dependency_bot.sh SBOM_FILE}"

WORKSPACE="$(mktemp -d /tmp/dependency-bot.XXXXXX)"
echo "Run reports: $WORKSPACE"

"$AUDIT_PYTHON" "$ROOT/scripts/sbom_requirements.py" \
    "$SBOM" \
    --output "$WORKSPACE/sbom-requirements.txt"

"$AUDIT_PYTHON" - \
    "$ROOT/requirements.txt" \
    "$WORKSPACE/sbom-requirements.txt" <<'PY'
import re
import sys

def read_pins(path):
    pins = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            match = re.fullmatch(
                r"([A-Za-z0-9][A-Za-z0-9._-]*)==([A-Za-z0-9][A-Za-z0-9.!+_-]*)",
                line,
            )
            if not match:
                raise SystemExit("STOP: Only simple pinned requirements supported")
            name, version = match.groups()
            name = re.sub(r"[-_.]+", "-", name).lower()
            if name in pins and pins[name] != version:
                raise SystemExit("STOP: Conflicting requirement versions")
            pins[name] = version
    return pins

if read_pins(sys.argv[1]) != read_pins(sys.argv[2]):
    raise SystemExit("STOP: SBOM and current requirements do not match")
print("PASS: SBOM matches current requirements")
PY

AUDIT_EXIT=0
"$AUDIT_PYTHON" -m pip_audit \
    -r "$WORKSPACE/sbom-requirements.txt" \
    --no-deps --disable-pip --strict \
    --format json \
    --output "$WORKSPACE/audit.json" \
    || AUDIT_EXIT=$?

if [[ "$AUDIT_EXIT" -ne 0 && "$AUDIT_EXIT" -ne 1 ]]; then
    echo "STOP: Audit command failed" >&2
    exit 1
fi

"$AUDIT_PYTHON" "$ROOT/scripts/dependency_update_plan.py" \
    "$WORKSPACE/audit.json" \
    --output "$WORKSPACE/plan.json"

"$AUDIT_PYTHON" "$ROOT/scripts/prepare_dependency_update.py" \
    "$WORKSPACE/plan.json" \
    --requirements "$ROOT/requirements.txt" \
    --result-json "$WORKSPACE/candidate-result.json"

CANDIDATE="$("$AUDIT_PYTHON" - "$WORKSPACE/candidate-result.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    result = json.load(f)

if result["status"] == "no_update":
    print("")
elif result["status"] == "candidate_prepared" and result["candidate_path"]:
    print(result["candidate_path"])
else:
    raise SystemExit("STOP: Unexpected candidate result")
PY
)"

if [[ -z "$CANDIDATE" ]]; then
    if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
        echo "update_ready=false" >> "$GITHUB_OUTPUT"
    fi
    echo "DONE: No security update needed. No PR created."
    exit 0
fi

AUDIT_PYTHON="$AUDIT_PYTHON" \
    bash "$ROOT/scripts/verify_dependency_candidate.sh" "$CANDIDATE"

cp -- "$CANDIDATE" "$WORKSPACE/verified-requirements.txt"
if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
    echo "update_ready=true" >> "$GITHUB_OUTPUT"
    echo "candidate_path=$WORKSPACE/verified-requirements.txt" >> "$GITHUB_OUTPUT"
fi
echo "VERIFIED CANDIDATE: $WORKSPACE/verified-requirements.txt"
echo "PR automation is not connected yet."
