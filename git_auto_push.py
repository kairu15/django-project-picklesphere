#!/usr/bin/env python3
"""
git_auto_push.py - Automatic Git commit & push workflow for PickleSphere.

Detects changes, stages them, generates a commit message, and pushes to the
configured GitHub remote - with user confirmation by default.

USAGE
-----
  python git_auto_push.py --status              Show a git status dashboard
  python git_auto_push.py --push                Detect, commit & push (interactive)
  python git_auto_push.py --push --yes          Fully automatic (no confirmation)
  python git_auto_push.py --push -m "My msg"    Push with a fixed message
  python git_auto_push.py --push --dry-run      Preview everything, change nothing
  python git_auto_push.py --push --branch dev   Push to a feature branch
  python git_auto_push.py --push --tag          Tag vX.Y.Z (auto patch bump) + push
  python git_auto_push.py --push --tag v2.1.0   Tag with explicit version + push
  python git_auto_push.py --push --backup       Create a backup branch before pushing
  python git_auto_push.py --log                 Show recent commit history

CONFIGURATION
-------------
Settings are read from .git_push.ini (committed) and .git_push.local.ini
(git-ignored, takes precedence). Any value can be overridden via environment
variables: GIT_REMOTE_NAME, GIT_BRANCH, GIT_AUTO_PUSH, GIT_COMMIT_FORMAT,
GIT_COMMIT_MESSAGE. See .git_push.ini for details.

SECURITY
--------
No credentials are stored or requested by this script. Git handles
authentication via your OS credential manager, SSH keys, or a Personal
Access Token configured with `git config credential.helper`. Never commit
tokens or passwords to the repository.
"""

from __future__ import annotations

import argparse
import configparser
import datetime as _dt
import os
import re
import subprocess
import sys
from pathlib import Path

# Windows consoles default to cp1252, which cannot encode emoji/box-drawing
# characters. Force UTF-8 output so the dashboard renders correctly everywhere.
if sys.platform == "win32":
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
CONFIG_FILE = ROOT / ".git_push.ini"
LOCAL_CONFIG_FILE = ROOT / ".git_push.local.ini"

AUTO_TAG_PREFIX = "v"          # tags look like v1.2.3
TAG_INCREMENT_MAP = {"major": 0, "minor": 1, "patch": 2}

CONVENTIONAL_TYPES = {
    "feat": "feat",
    "feature": "feat",
    "fix": "fix",
    "bugfix": "fix",
    "docs": "docs",
    "doc": "docs",
    "chore": "chore",
    "refactor": "refactor",
    "test": "test",
    "tests": "test",
    "style": "chore",
    "perf": "refactor",
    "build": "chore",
    "revert": "chore",
    "wip": "chore",
    "update": "chore",
}

# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

class GitError(RuntimeError):
    """Raised when a git command fails in a way we want to handle."""


def run(cmd: list[str], check: bool = True, capture: bool = True) -> subprocess.CompletedProcess:
    """Run a git command. Returns CompletedProcess with stdout decoded."""
    proc = subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=capture,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and proc.returncode != 0:
        raise GitError(_git_error_message(proc))
    return proc


def _git_error_message(proc: subprocess.CompletedProcess) -> str:
    err = (proc.stderr or "").strip() or (proc.stdout or "").strip()
    return f"git {proc.args[1] if len(proc.args) > 1 else 'command'} failed:\n{err}"


def git(*args: str, check: bool = True) -> str:
    """Run `git <args>` and return trimmed stdout."""
    return run(["git", *args], check=check).stdout.strip()


def is_git_repo() -> bool:
    return run(["git", "rev-parse", "--is-inside-work-tree"], check=False).returncode == 0


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def load_config() -> dict:
    """Merge defaults, .git_push.ini, .git_push.local.ini, then env overrides."""
    cfg = {
        "remote": "origin",
        "repository_url": "",
        "branch": "main",
        "auto_push": "false",
        "commit_format": "{type}: {summary}",
        "auto_tag": "false",
    }
    parser = configparser.ConfigParser()
    for path in (CONFIG_FILE, LOCAL_CONFIG_FILE):
        if path.exists():
            try:
                parser.read(path, encoding="utf-8")
            except configparser.Error as exc:
                print(f"⚠️  Could not parse {path.name}: {exc}")
                continue
            if parser.has_section("git"):
                cfg.update({k: v for k, v in parser.items("git") if v.strip()})

    # Environment overrides (highest priority)
    env_map = {
        "GIT_REMOTE_NAME": "remote",
        "GIT_BRANCH": "branch",
        "GIT_AUTO_PUSH": "auto_push",
        "GIT_COMMIT_FORMAT": "commit_format",
    }
    for env_key, cfg_key in env_map.items():
        if os.environ.get(env_key):
            cfg[cfg_key] = os.environ[env_key]

    cfg["auto_push"] = str(cfg.get("auto_push", "false")).strip().lower() in ("1", "true", "yes", "on")
    cfg["auto_tag"] = str(cfg.get("auto_tag", "false")).strip().lower() in ("1", "true", "yes", "on")
    return cfg


def load_repository_url(cfg: dict) -> str:
    """Resolve the repository URL from config or the actual remote."""
    if cfg.get("repository_url"):
        return cfg["repository_url"]
    try:
        return git("remote", "get-url", cfg["remote"])
    except GitError:
        return ""


# ---------------------------------------------------------------------------
# Change detection & summary
# ---------------------------------------------------------------------------

def get_changes() -> list[tuple[str, str]]:
    """Return [(status, path)] for all changes (staged + unstaged + untracked)."""
    out = git("status", "--porcelain", "--untracked-files=all")
    changes = []
    for line in out.splitlines():
        if not line.strip():
            continue
        status = line[:2]
        path = line[3:]
        # Renames show as 'R  old -> new'; keep both paths for the summary
        if " -> " in path:
            for part in path.split(" -> "):
                changes.append((status, part.strip()))
        else:
            changes.append((status, path.strip()))
    return changes


def has_changes(changes: list) -> bool:
    return bool(changes)


def describe_change(status: str) -> str:
    status = status.strip()
    if status.startswith("??"):
        return "new file"
    if "D" in status:
        return "deleted"
    if "A" in status:
        return "new file"
    if "R" in status:
        return "renamed"
    if "M" in status:
        return "modified"
    if "C" in status:
        return "copied"
    return "changed"


def top_level_dirs(changes: list) -> list[str]:
    """Unique top-level directories of changed paths (files at root are 'root')."""
    dirs = []
    for _status, path in changes:
        parts = Path(path).parts
        top = parts[0] if len(parts) > 1 else "root"
        if top not in dirs:
            dirs.append(top)
    return dirs


def _titleize(name: str) -> str:
    words = re.split(r"[_\-.]+", name)
    words = [w for w in words if w]
    if not words:
        return "Project"
    stopwords = {"py", "html", "js", "css", "sh", "md", "sql", "txt", "ini", "json"}
    words = [w for w in words if w.lower() not in stopwords]
    if not words:
        return "Project files"
    return " ".join(w[:1].upper() + w[1:] for w in words)


def _detect_type(changes: list) -> str:
    """Heuristic conventional-commit type based on what changed."""
    paths_lc = {Path(p).as_posix().lower() for _s, p in changes}

    if any("migration" in p or "/migrations/" in p for p in paths_lc):
        return "feat"
    if any(p.endswith(".md") or p.startswith("docs/") for p in paths_lc):
        return "docs"
    if any(p.startswith("test") or "test" in p for p in paths_lc):
        return "test"
    # Django/regular source changes
    for p in paths_lc:
        if p.endswith((".py", ".html", ".js", ".css")):
            return "feat"
    return "chore"


def generate_commit_message(changes: list, commit_format: str, fixed_message: str = "") -> str:
    """Build a commit message from the changed files."""
    if fixed_message:
        return fixed_message.strip()

    module_map: dict[str, list[str]] = {}
    for status, path in changes:
        parts = Path(path).parts
        module = _titleize(parts[0]) if len(parts) > 1 else None
        module_map.setdefault(module, []).append((status, path))

    module_names = [m for m in module_map if m]
    if module_names:
        if len(module_names) == 1:
            name = module_names[0]
            suffix = "" if name.lower().endswith("module") else " module"
            summary = f"Update {name}{suffix}"
        elif len(module_names) == 2:
            summary = f"Update {module_names[0]} and {module_names[1]} modules"
        else:
            summary = f"Update {', '.join(module_names[:2])} and {len(module_names) - 2} more modules"
    else:
        summary = "Update project files"

    # Add detail for small changes
    if len(changes) <= 3:
        details = []
        for status, path in changes:
            details.append(f"{describe_change(status).split()[0]} {Path(path).name}")
        summary += " (" + ", ".join(details) + ")"

    ctype = _detect_type(changes)
    scope_part = module_names[0] if module_names else ""

    try:
        message = commit_format.format(type=ctype, scope=scope_part, summary=summary)
    except (KeyError, IndexError):
        message = f"{ctype}: {summary}"
    # Collapse awkward double spaces when {scope} is empty (e.g. "feat : ")
    message = re.sub(r"\s+:", ":", message)
    message = re.sub(r":\s{2,}", ": ", message)
    return message.strip()


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def print_changes(changes: list) -> None:
    if not changes:
        print("   (no changes)")
        return
    for status, path in changes:
        sym = {
            "M": "M", "A": "A", "D": "D", "R": "R", "C": "C", "??": "??",
        }.get(status.strip(), "?")
        print(f"   {sym:>2}  {path}")


def confirm(message: str, yes: bool) -> str:
    """Interactive confirm/edit/cancel flow. Returns 'push' or 'cancel'."""
    if yes:
        return "push"
    while True:
        print()
        print(f"   Suggested commit message:  \"{message}\"")
        print()
        print("   [p] Push with this message")
        print("   [e] Edit commit message")
        print("   [c] Cancel")
        choice = input("   Choice (p/e/c): ").strip().lower()
        if choice in ("p", "push", ""):
            return "push"
        if choice in ("e", "edit"):
            new_msg = input("   New commit message: ").strip()
            if new_msg:
                message = new_msg
                continue
            print("   ⚠️  Empty message - keeping the suggested one.")
            continue
        if choice in ("c", "cancel"):
            return "cancel"
        print("   ⚠️  Invalid choice - enter p, e, or c.")


# ---------------------------------------------------------------------------
# Git operations
# ---------------------------------------------------------------------------

def current_branch() -> str:
    try:
        return git("branch", "--show-current")
    except GitError:
        return ""


def branch_exists(branch: str) -> bool:
    out = git("branch", "--list", branch, check=False)
    return bool(out.strip())


def ensure_staged(message: str) -> bool:
    """Stage everything and commit. Returns True if a commit was created."""
    git("add", "-A")
    try:
        git("commit", "-m", message)
    except GitError as exc:
        # Nothing staged (e.g. only file mode/line ending noise)
        if "nothing to commit" in str(exc).lower() or "no changes added" in str(exc).lower():
            print("\n   ℹ️  Nothing to commit - working tree is clean after staging.")
            return False
        raise
    return True


def push(remote: str, branch: str) -> None:
    """Push, handling common failures with clear guidance."""
    proc = run(["git", "push", remote, branch], check=False)
    if proc.returncode == 0:
        return

    err = (proc.stderr or "") + "\n" + (proc.stdout or "")
    low = err.lower()

    if "authentication failed" in low or "could not read username" in low or "could not read password" in low:
        print("\n   ❌ Authentication failed.")
        print("      Fixes (choose one):")
        print("        • Windows: run `git config --global credential.helper manager` then push once and sign in")
        print("        • Or use a PAT: `git remote set-url origin https://<TOKEN>@github.com/OWNER/REPO.git`")
        print("          (better: store it in the credential manager, not the URL)")
        print("        • Or switch to SSH: `git remote set-url origin git@github.com:OWNER/REPO.git`")
        raise GitError("authentication failed")

    if "could not resolve host" in low or "unable to access" in low or "network is unreachable" in low:
        print("\n   ❌ Network error - could not reach the remote repository.")
        print("      Check your internet connection and that the URL is correct:")
        print(f"      `git remote -v`  →  {load_repository_url(load_config())}")
        raise GitError("network error")

    if "non-fast-forward" in low or "fetch first" in low or "rejected" in low or "diverged" in low:
        print("\n   ❌ Push rejected (non-fast-forward). Your local branch is behind the remote.")
        print("      Fix: pull the latest changes with rebase, then retry:")
        print(f"      git pull --rebase {remote} {branch}")
        print(f"      python git_auto_push.py --push")
        raise GitError("non-fast-forward")

    # Fallback: show raw error
    print("\n   ❌ Push failed:")
    print("      " + (proc.stderr or proc.stdout or "").strip().replace("\n", "\n      "))
    raise GitError("push failed")


# ---------------------------------------------------------------------------
# Optional features: tag, backup, log
# ---------------------------------------------------------------------------

def latest_tag() -> str:
    out = git("tag", "--sort=-v:refname", check=False)
    for tag in out.splitlines():
        if re.match(rf"^{re.escape(AUTO_TAG_PREFIX)}\d+\.\d+\.\d+$", tag.strip()):
            return tag.strip()
    return ""


def next_tag(part: str = "patch") -> str:
    """Compute the next version tag (v1.2.3 -> v1.2.4 for patch)."""
    latest = latest_tag()
    if latest:
        nums = [int(n) for n in latest[len(AUTO_TAG_PREFIX):].split(".")]
    else:
        nums = [0, 1, 0]
    idx = TAG_INCREMENT_MAP.get(part, 2)
    nums[idx] += 1
    for i in range(idx + 1, 3):
        nums[i] = 0
    return f"{AUTO_TAG_PREFIX}{'.'.join(str(n) for n in nums)}"


def create_tag(tag: str) -> None:
    existing = git("tag", "--list", tag, check=False)
    if existing.strip():
        print(f"   ⚠️  Tag '{tag}' already exists - skipping tag creation.")
        return
    git("tag", "-a", tag, "-m", f"Release {tag}")
    git("push", "origin", tag)
    print(f"   🏷️  Tagged and pushed {tag}")


def create_backup_branch(branch: str) -> str:
    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    name = f"backup/{branch}-{stamp}"
    git("branch", name)
    print(f"   💾 Backup branch created: {name}")
    return name


def show_log(limit: int = 10) -> None:
    print("Recent commits:")
    print("---------------")
    out = git("log", f"--oneline", "-n", str(limit), "--decorate")
    print("\n".join(f"   {line}" for line in out.splitlines()))


# ---------------------------------------------------------------------------
# Status dashboard
# ---------------------------------------------------------------------------

def show_status(cfg: dict) -> int:
    print()
    print("=" * 56)
    print("  🏓  PickleSphere - Git Status Dashboard")
    print("=" * 56)

    if not is_git_repo():
        print("\n   ❌ Not a git repository.")
        print("      Run: git init && git remote add origin <repo-url> && git branch -M main")
        return 1

    branch = current_branch() or "(detached HEAD)"
    remote_url = load_repository_url(cfg)
    print(f"\n   Repository : {ROOT}")
    print(f"   Branch     : {branch}")
    print(f"   Remote     : {cfg['remote']} -> {remote_url or '<not configured>'}")

    # Ahead/behind vs upstream
    try:
        git("rev-parse", f"@{cfg['branch']}@{'{u}'}", check=False)  # probe upstream
        ahead_behind = git("rev-list", "--left-right", "--count", f"{branch}...{cfg['remote']}/{cfg['branch']}", check=False)
        if ahead_behind:
            ahead, behind = ahead_behind.split()
            print(f"   Sync       : {ahead} ahead, {behind} behind of {cfg['remote']}/{cfg['branch']}")
    except GitError:
        print(f"   Sync       : (no upstream tracking set)")

    # Last commit
    last = git("log", "-1", "--format=%h %s", check=False)
    if last:
        print(f"   Last commit: {last}")

    # Changes
    changes = get_changes()
    print(f"\n   Changes    : {len(changes)} file(s) pending")
    print_changes(changes)
    print()

    if changes:
        msg = generate_commit_message(changes, cfg["commit_format"])
        print(f"   Suggested message: \"{msg}\"")
    return 0


# ---------------------------------------------------------------------------
# Main push flow
# ---------------------------------------------------------------------------

def do_push(cfg: dict, args: argparse.Namespace) -> int:
    branch = args.branch or cfg["branch"]
    remote = cfg["remote"]

    print()
    print("=" * 56)
    print("  🚀  PickleSphere - Auto Git Push")
    print("=" * 56)

    # 1. Sanity checks
    if not is_git_repo():
        print("\n   ❌ Not a git repository.")
        print("      Run: git init && git branch -M main && git remote add origin <repo-url>")
        return 1

    try:
        remote_url = git("remote", "get-url", remote)
    except GitError:
        print(f"\n   ❌ Remote '{remote}' is not configured.")
        print(f"      Add it with: git remote add {remote} <repository-url>")
        print("      Or set GIT_REMOTE_NAME / [git] remote in .git_push.ini")
        return 1
    print(f"\n   Remote : {remote} -> {remote_url}")
    print(f"   Branch : {branch}")

    # 2. Detect changes
    changes = get_changes()
    if not changes:
        print("\n   ✅ Working tree is clean - nothing to commit or push.")
        try:
            git("rev-parse", "--abbrev-ref", f"{branch}@{{u}}", check=False)
            git("push", remote, branch)
            print(f"   ✅ Pushed (no new commit needed).")
        except GitError:
            print("   (Nothing to push.)")
        return 0

    print(f"\n   Changes detected: {len(changes)} file(s)")
    print_changes(changes)

    # 3. Backup (optional)
    if args.backup:
        try:
            create_backup_branch(branch)
        except GitError as exc:
            print(f"\n   ⚠️  Backup branch failed: {exc}")
            return 1

    # 4. Commit message
    message = generate_commit_message(changes, cfg["commit_format"], args.message or os.environ.get("GIT_COMMIT_MESSAGE", ""))

    # 5. Dry-run
    if args.dry_run:
        print(f"\n   [DRY RUN] Would commit & push:  \"{message}\"")
        if args.tag:
            tag = args.tag if isinstance(args.tag, str) and args.tag not in ("patch", "minor", "major") else next_tag(args.tag if isinstance(args.tag, str) else "patch")
            print(f"   [DRY RUN] Would tag & push:    {tag}")
        print("\n   (dry run - no changes were made)")
        return 0

    # 6. Confirmation (unless --yes or auto_push config)
    decision = confirm(message, yes=args.yes or cfg["auto_push"])
    if decision == "cancel":
        print("\n   ✖️  Cancelled - no changes were made.")
        return 1

    # 7. Stage & commit
    print("\n   Staging and committing...")
    try:
        if not ensure_staged(message):
            return 0
    except GitError as exc:
        print(f"\n   ❌ Commit failed: {exc}")
        return 1
    print(f"   ✅ Committed: \"{message}\"")

    # 8. Optional version tag
    if args.tag:
        tag = args.tag if isinstance(args.tag, str) and args.tag not in ("patch", "minor", "major") else next_tag(args.tag if isinstance(args.tag, str) else "patch")
        print(f"\n   Creating release tag {tag}...")
        try:
            create_tag(tag)
        except GitError as exc:
            print(f"\n   ⚠️  Tag failed (commit was kept): {exc}")

    # 9. Push
    print(f"\n   Pushing to {remote}/{branch}...")
    try:
        push(remote, branch)
    except GitError:
        return 1

    print("\n   ✅ Successfully pushed!")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="git_auto_push",
        description="Automatic Git commit & push workflow for PickleSphere.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--status", action="store_true", help="Show git status dashboard")
    parser.add_argument("--log", action="store_true", help="Show recent commit history")
    parser.add_argument("--push", action="store_true", help="Detect changes, commit & push")
    parser.add_argument("-m", "--message", help="Fixed commit message (skips generation)")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation (auto mode)")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without doing anything")
    parser.add_argument("-b", "--branch", help="Branch to push to (default: from config)")
    parser.add_argument("--tag", nargs="?", const="patch", help="Create & push a version tag (vX.Y.Z, or auto: patch/minor/major)")
    parser.add_argument("--backup", action="store_true", help="Create a backup branch before pushing")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cfg = load_config()

    if args.status:
        return show_status(cfg)
    if args.log:
        show_log()
        return 0
    if args.push:
        return do_push(cfg, args)

    build_parser().print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
