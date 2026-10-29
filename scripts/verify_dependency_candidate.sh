#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
REQUIREMENTS="${1:-$ROOT/requirements.txt}"
AUDIT_PYTHON="${AUDIT_PYTHON:-python3}"

if [[ ! -f "$REQUIREMENTS" ]]; then
    echo "ERROR: Requirements file not found" >&2
    exit 1
fi

WORKSPACE="$(mktemp -d /tmp/dependency-verification.XXXXXX)"
trap 'rm -rf -- "$WORKSPACE"' EXIT

# Use one snapshot for both the audit and sandbox tests.
cp -- "$REQUIREMENTS" "$WORKSPACE/requirements.txt"

echo "Running fresh dependency audit..."
"$AUDIT_PYTHON" -m pip_audit \
    -r "$WORKSPACE/requirements.txt" \
    --strict \
    --format json \
    --output "$WORKSPACE/audit.json"

"$AUDIT_PYTHON" "$ROOT/scripts/dependency_update_plan.py" \
    "$WORKSPACE/audit.json" \
    --output "$WORKSPACE/plan.json"

"$AUDIT_PYTHON" - "$WORKSPACE/plan.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    plan = json.load(f)

if (
    plan.get("status") != "no_update"
    or plan.get("findings")
    or plan.get("skipped")
):
    raise SystemExit("STOP: Candidate did not pass dependency verification")

print("PASS: Fresh audit has no findings or skipped dependencies")
PY

bash "$ROOT/scripts/test_dependency_candidate.sh" \
    "$WORKSPACE/requirements.txt"

echo "PASS: Fresh audit and sandbox tests completed."
echo "No PR created; human review is still required before merging."
