#!/usr/bin/env python3
"""Bump bucket/fetchart.json to the latest fetchart release.

The manifest is only bumped once the GitHub release exe exists for the new
version. Its url and hash are rewritten; the hash comes from the GitHub asset
digest, or from downloading and hashing the exe when no digest is given.

Usage:
    bump.py [MANIFEST] [--version X.Y.Z] [--dry-run]

Writes `bumped=true|false` and `version=...` to $GITHUB_OUTPUT when set.
Uses $GH_TOKEN / $GITHUB_TOKEN for the GitHub API when available.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request

REPO = "SamuelArther/fetchart"
EXE_ASSET = "fetchart-windows.exe"


def http_get(url, accept=None, auth=False):
    req = urllib.request.Request(url, headers={"User-Agent": "scoop-bucket-bump"})
    if accept:
        req.add_header("Accept", accept)
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if auth and token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def get_json(url, auth=False):
    try:
        return json.loads(http_get(url, "application/json", auth))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def vtuple(v):
    return tuple(int(p) if p.isdigit() else p for p in re.split(r"[.\-]", v))


def latest_github_version():
    rel = get_json(f"https://api.github.com/repos/{REPO}/releases/latest", auth=True)
    return rel["tag_name"].lstrip("v") if rel else None


def release_exe(version):
    """Return (url, sha256) of the release exe, or None if it isn't published yet."""
    rel = get_json(f"https://api.github.com/repos/{REPO}/releases/tags/v{version}", auth=True)
    if not rel:
        return None
    for asset in rel.get("assets", []):
        if asset["name"] == EXE_ASSET and asset.get("state", "uploaded") == "uploaded":
            url = asset["browser_download_url"]
            digest = asset.get("digest") or ""
            if digest.startswith("sha256:"):
                return url, digest.split(":", 1)[1]
            return url, hashlib.sha256(http_get(url)).hexdigest()
    return None


def set_output(**kw):
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            for k, v in kw.items():
                f.write(f"{k}={v}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", nargs="?", default="bucket/fetchart.json")
    ap.add_argument("--version", help="target version (default: latest GitHub release)")
    ap.add_argument("--dry-run", action="store_true", help="print the new manifest instead of writing it")
    args = ap.parse_args()

    with open(args.manifest, encoding="utf-8") as f:
        manifest = json.load(f)
    cur = manifest["version"]
    target = args.version or latest_github_version()
    print(f"manifest: {cur}  latest release: {target}")

    if not target or vtuple(target) <= vtuple(cur):
        print("up to date")
        set_output(bumped="false", version=cur)
        return 0

    exe = release_exe(target)
    if not exe:
        print(f"{target}: {EXE_ASSET} not published yet; skipping")
        set_output(bumped="false", version=cur)
        return 0

    url, sha = exe
    expected = manifest["autoupdate"]["url"].replace("$version", target)
    if url != expected:
        raise SystemExit(f"release url {url} does not match autoupdate url {expected}")
    manifest["version"] = target
    manifest["url"] = url
    manifest["hash"] = sha

    out = json.dumps(manifest, indent=4, ensure_ascii=False) + "\n"
    if args.dry_run:
        sys.stdout.write(out)
    else:
        with open(args.manifest, "w", encoding="utf-8", newline="\n") as f:
            f.write(out)
    print(f"bumped {cur} -> {target}: {url} {sha}")
    set_output(bumped="true", version=target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
