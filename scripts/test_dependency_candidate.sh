#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
REQUIREMENTS="${1:-$ROOT/requirements.txt}"

if [[ ! -f "$REQUIREMENTS" ]]; then
    echo "ERROR: Requirements file not found: $REQUIREMENTS" >&2
    exit 1
fi

WORKSPACE="$(mktemp -d /tmp/dependency-sandbox.XXXXXX)"
IMAGE="cybersecurity-dependency-test:$(date +%s)-$$"

cleanup() {
    docker image rm "$IMAGE" >/dev/null 2>&1 || true
    rm -rf -- "$WORKSPACE"
}
trap cleanup EXIT

cp -- "$REQUIREMENTS" "$WORKSPACE/requirements.txt"
cp -- "$ROOT/Dockerfile.dependency-sandbox" "$WORKSPACE/Dockerfile"
cp -R -- "$ROOT/app" "$WORKSPACE/app"
cp -R -- "$ROOT/scripts" "$WORKSPACE/scripts"
cp -R -- "$ROOT/tests" "$WORKSPACE/tests"

echo "Building test image from selected requirements..."
docker build -t "$IMAGE" "$WORKSPACE"

echo "Running tests with restricted container settings..."
docker run --rm \
    --network none \
    --read-only \
    --tmpfs /tmp:rw,noexec,nosuid,size=128m,mode=1777 \
    --cap-drop ALL \
    --security-opt no-new-privileges=true \
    --pids-limit 128 \
    --memory 512m \
    --cpus 1 \
    "$IMAGE"

echo "PASS: Sandbox tests passed for the selected requirements."
