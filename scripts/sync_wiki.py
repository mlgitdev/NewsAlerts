#!/usr/bin/env python3
"""Sync documentation from docs/wiki/ to the GitHub Wiki repository (NewsAlerts.wiki.git)."""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def get_gh_token() -> str:
    """Retrieve GitHub token from gh CLI if available, or GITHUB_TOKEN env var."""
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token.strip()
    try:
        res = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            check=True
        )
        return res.stdout.strip()
    except Exception:
        # Check standard installation location on Windows
        gh_win = Path(r"C:\Program Files\GitHub CLI\gh.exe")
        if gh_win.exists():
            try:
                res = subprocess.run(
                    [str(gh_win), "auth", "token"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                return res.stdout.strip()
            except Exception:
                pass
    return ""


def main():
    repo_root = Path(__file__).resolve().parent.parent
    wiki_src = repo_root / "docs" / "wiki"
    if not wiki_src.exists():
        print(f"[!] Error: Wiki source directory does not exist: {wiki_src}", file=sys.stderr)
        sys.exit(1)

    token = get_gh_token()
    if not token:
        print("[!] Error: No GitHub authentication token found via 'gh auth token' or GITHUB_TOKEN.", file=sys.stderr)
        print("Please log in with 'gh auth login' or export GITHUB_TOKEN.", file=sys.stderr)
        sys.exit(1)

    wiki_url = f"https://x-access-token:{token}@github.com/mlgitdev/NewsAlerts.wiki.git"

    # Test if the remote wiki repository exists
    test_res = subprocess.run(
        ["git", "ls-remote", wiki_url],
        capture_output=True,
        text=True
    )

    if test_res.returncode != 0:
        print("[!] Notice: GitHub Wiki git repository is not yet initialized.", file=sys.stderr)
        print("    GitHub only provisions the wiki git backend once the first page is created.", file=sys.stderr)
        print("    --> Please open https://github.com/mlgitdev/NewsAlerts/wiki in your browser,", file=sys.stderr)
        print("        click 'Create the first page' (Title: Home), and click 'Save Page'.", file=sys.stderr)
        print("    --> Then re-run this script to automatically push all wiki pages!", file=sys.stderr)
        sys.exit(2)

    with tempfile.TemporaryDirectory() as tmp_dir:
        clone_path = Path(tmp_dir) / "wiki"
        print(f"[+] Cloning NewsAlerts.wiki.git into temporary workspace...")
        subprocess.run(["git", "clone", wiki_url, str(clone_path)], check=True)

        # Copy all markdown files from docs/wiki/ to the clone
        synced_count = 0
        for f in wiki_src.glob("*.md"):
            dest = clone_path / f.name
            shutil.copy2(f, dest)
            synced_count += 1
            print(f"    Synced: {f.name}")

        # Check git status
        status_res = subprocess.run(
            ["git", "-C", str(clone_path), "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True
        )

        if not status_res.stdout.strip():
            print("[+] All wiki documentation is already up to date!")
            return

        print(f"[+] Committing {synced_count} wiki pages...")
        subprocess.run(["git", "-C", str(clone_path), "add", "."], check=True)
        subprocess.run(
            ["git", "-C", str(clone_path), "commit", "-m", "docs(wiki): synchronize full documentation suite"],
            check=True
        )
        print("[+] Pushing updates to GitHub Wiki...")
        subprocess.run(["git", "-C", str(clone_path), "push", "origin", "HEAD"], check=True)
        print("[OK] Successfully synchronized GitHub Wiki!")


if __name__ == "__main__":
    main()
