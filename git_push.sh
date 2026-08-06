#!/bin/bash
# PickleSphere - Convenience wrapper for the auto Git push workflow.
# Usage: ./git_push.sh [--push] [--yes] [-m "message"] [--status] [--log] [--tag] [--backup] [--branch NAME]
# Examples:
#   ./git_push.sh --status          - Show git status dashboard
#   ./git_push.sh --push            - Interactive: review changes, confirm/commit/push
#   ./git_push.sh --push --yes      - Fully automatic (no confirmation)
#   ./git_push.sh --push -m "fix: correct timezone display" - Push with your own message
#   ./git_push.sh --push --tag      - Commit, push, and bump version tag (v1.2.4)
#   ./git_push.sh --log             - Show recent commit history

# Use the venv Python if available, otherwise system python
if [ -x "venv/Scripts/python.exe" ]; then
    PYTHON="venv/Scripts/python.exe"
elif [ -x "venv/bin/python" ]; then
    PYTHON="venv/bin/python"
else
    PYTHON="python"
fi

exec "$PYTHON" git_auto_push.py "$@"
