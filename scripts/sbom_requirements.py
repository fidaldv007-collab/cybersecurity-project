import argparse
import json
import re
from pathlib import Path
from urllib.parse import unquote

parser = argparse.ArgumentParser(
    description="Extract pinned Python dependencies from a CycloneDX SBOM."
)
parser.add_argument("sbom")
parser.add_argument("--output", required=True)
args = parser.parse_args()

with open(args.sbom, encoding="utf-8") as f:
    sbom = json.load(f)

if sbom.get("bomFormat") != "CycloneDX":
    raise SystemExit("ERROR: Expected a CycloneDX SBOM")

packages = {}
for component in sbom.get("components", []):
    purl = component.get("purl") or ""
    if not purl.startswith("pkg:pypi/"):
        continue

    identity = purl.removeprefix("pkg:pypi/").split("#", 1)[0].split("?", 1)[0]
    name, separator, version = identity.rpartition("@")
    name, version = unquote(name), unquote(version)

    if (
        not separator
        or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name)
        or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.!+_-]*", version)
    ):
        raise SystemExit(f"ERROR: Unsupported Python package URL: {purl}")

    name = re.sub(r"[-_.]+", "-", name).lower()
    if name in packages and packages[name] != version:
        raise SystemExit(f"ERROR: Multiple versions found for {name}")
    packages[name] = version

if not packages:
    raise SystemExit("ERROR: No Python packages found in SBOM")

output = Path(args.output)
output.write_text(
    "".join(f"{name}=={version}\n" for name, version in sorted(packages.items())),
    encoding="utf-8",
)
print(f"Prepared {len(packages)} Python packages for auditing")
