"""Sync all app manifests to their latest GitHub release.

Reads the apps.jsonc registry, queries GitHub API for the latest release of each app
(or a single app if --app is specified), downloads the asset, computes sha256,
and updates the manifest via update_scoop_manifest.py.

Usage:
    python scripts/sync_all_manifests.py [--app <name>]

Requires: GITHUB_TOKEN env var (for API rate limits).
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
# Deliberately not named .json: Scoop's bucket CI validates every *.json file
# touched by a commit against the manifest schema, and this registry is not a
# manifest, so a .json name makes the Tests workflow fail on every edit.
APPS_FILE = SCRIPTS_DIR / "apps.jsonc"


def get_latest_release(repo: str, token: str | None) -> dict:
    """Fetch latest release info from GitHub API."""
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github.v3+json")
    if token:
        req.add_header("Authorization", f"token {token}")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def download_and_hash(url: str, token: str | None) -> str:
    """Download a file and return its sha256 hash."""
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/octet-stream")
    if token:
        req.add_header("Authorization", f"token {token}")
    sha256 = hashlib.sha256()
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name
        with urllib.request.urlopen(req) as resp:
            while chunk := resp.read(8192):
                sha256.update(chunk)
                tmp.write(chunk)
    os.unlink(tmp_path)
    return sha256.hexdigest()


def sync_app(app: str, config: dict, token: str | None) -> bool:
    """Sync a single app. Returns True if updated."""
    repo = config["repo"]
    print(f"[{app}] Checking {repo} ...")

    try:
        release = get_latest_release(repo, token)
    except Exception as e:
        print(f"[{app}] Failed to fetch latest release: {e}", file=sys.stderr)
        return False

    # Strip leading 'v' from tag name
    version = release["tag_name"].lstrip("v")

    # Check if already up-to-date
    manifest_path = SCRIPTS_DIR.parent / "bucket" / f"{app}.json"
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            current = json.load(f)
        if current.get("version") == version:
            print(f"[{app}] Already at {version}, skipping")
            return False

    asset_name = config["asset_name"].replace("{version}", version)
    download_url = f"https://github.com/{repo}/releases/download/v{version}/{asset_name}"

    print(f"[{app}] Updating to {version}, downloading {asset_name} ...")
    try:
        file_hash = download_and_hash(download_url, token)
    except Exception as e:
        print(f"[{app}] Failed to download asset: {e}", file=sys.stderr)
        return False

    # Call update_scoop_manifest.py
    cmd = [
        sys.executable, str(SCRIPTS_DIR / "update_scoop_manifest.py"),
        "--app", app,
        "--version", version,
        "--url", download_url,
        "--hash", file_hash,
        "--bin", config["bin"],
        "--description", config.get("description", ""),
        "--homepage", config.get("homepage", ""),
        "--license", config.get("license", ""),
    ]
    subprocess.run(cmd, check=True)
    print(f"[{app}] Updated to {version}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Sync manifests to latest releases")
    parser.add_argument("--app", help="Only sync this app (default: all)")
    args = parser.parse_args()

    with open(APPS_FILE, "r", encoding="utf-8") as f:
        apps = json.load(f)

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Warning: GITHUB_TOKEN not set, API rate limits may apply", file=sys.stderr)

    if args.app:
        if args.app not in apps:
            print(f"Error: app '{args.app}' not found in apps.jsonc", file=sys.stderr)
            sys.exit(1)
        sync_app(args.app, apps[args.app], token)
    else:
        updated = 0
        for app, config in apps.items():
            if sync_app(app, config, token):
                updated += 1
        print(f"\nDone. {updated}/{len(apps)} apps updated.")


if __name__ == "__main__":
    main()
