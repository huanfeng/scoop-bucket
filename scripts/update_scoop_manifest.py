"""Generate or update a Scoop manifest JSON file.

Usage:
    python scripts/update_scoop_manifest.py \
        --app <name> --version <ver> --url <download_url> \
        --hash <sha256> --bin <exe1,exe2> \
        [--description <desc>] [--homepage <url>] [--license <id>]

If bucket/<app>.json already exists, existing fields are preserved
but version/url/hash/bin are always overwritten.
"""

import argparse
import json
import sys
from pathlib import Path

BUCKET_DIR = Path(__file__).resolve().parent.parent / "bucket"


def build_manifest(args, existing: dict | None = None) -> dict:
    manifest = existing or {}

    # Always overwrite these core fields
    manifest["version"] = args.version
    manifest["architecture"] = {
        "64bit": {
            "url": args.url,
            "bin": args.bin.split(","),
            "hash": args.hash,
        }
    }

    # Metadata: overwrite if provided, keep existing otherwise
    if args.description:
        manifest["description"] = args.description
    if args.homepage:
        manifest["homepage"] = args.homepage
    if args.license:
        manifest["license"] = args.license

    return manifest


def main():
    parser = argparse.ArgumentParser(description="Update Scoop manifest")
    parser.add_argument("--app", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--hash", required=True)
    parser.add_argument("--bin", required=True, help="Comma-separated binary names")
    parser.add_argument("--description", default="")
    parser.add_argument("--homepage", default="")
    parser.add_argument("--license", default="")
    args = parser.parse_args()

    manifest_path = BUCKET_DIR / f"{args.app}.json"

    existing = None
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            existing = json.load(f)

    manifest = build_manifest(args, existing)

    BUCKET_DIR.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Updated {manifest_path.relative_to(BUCKET_DIR.parent)}")


if __name__ == "__main__":
    main()
