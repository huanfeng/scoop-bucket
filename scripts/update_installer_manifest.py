"""Bump a hand-written manifest (installer-based apps) to a new version.

update_scoop_manifest.py generates whole manifests for portable zip apps and
always rewrites `architecture` with a `bin` list. Apps that run their own
installer (installer/uninstaller scripts, no `bin`) are written by hand
instead, so this script touches only version, url and hash, and keeps every
other field as is.

The new URL comes from the manifest's own `autoupdate` url template, the same
one Scoop's checkver uses, so the template lives in one place. The hash is
computed by downloading that URL rather than trusted from the caller.

Usage:
    python scripts/update_installer_manifest.py --app <name> --version <ver>
"""

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

BUCKET_DIR = Path(__file__).resolve().parent.parent / "bucket"
ARCH = "64bit"


def sha256_of_url(url: str) -> str:
    sha256 = hashlib.sha256()
    req = urllib.request.Request(url, headers={"User-Agent": "scoop-bucket-updater"})
    with urllib.request.urlopen(req) as resp:
        while chunk := resp.read(1 << 16):
            sha256.update(chunk)
    return sha256.hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Bump an installer-based manifest")
    parser.add_argument("--app", required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()

    manifest_path = BUCKET_DIR / f"{args.app}.json"
    if not manifest_path.exists():
        sys.exit(f"{manifest_path.name} not found: add the manifest by hand first")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    try:
        template = manifest["autoupdate"]["architecture"][ARCH]["url"]
        arch = manifest["architecture"][ARCH]
    except KeyError:
        sys.exit(f"{manifest_path.name} has no autoupdate url / architecture for {ARCH}")
    if "bin" in arch:
        sys.exit(f"{manifest_path.name} looks like a portable app: use update_scoop_manifest.py")

    url = template.replace("$version", args.version)
    print(f"Downloading {url}")
    arch["url"] = url
    arch["hash"] = sha256_of_url(url)
    manifest["version"] = args.version

    with open(manifest_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, indent=4, ensure_ascii=False)
        f.write("\n")
    print(f"Updated {manifest_path.relative_to(BUCKET_DIR.parent)}: {args.version} {arch['hash']}")


if __name__ == "__main__":
    main()
