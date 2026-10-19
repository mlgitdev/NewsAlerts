#!/usr/bin/env bash
# NewsAlerts Git Worktree Automation for Bash (Linux & macOS)
# Usage:
#   ./scripts/worktree.sh new <branch-name> [base-branch]
#   ./scripts/worktree.sh list
#   ./scripts/worktree.sh remove <branch-or-folder> [-f|--force]
#   ./scripts/worktree.sh merge-back <source-branch> <target-branch>

set -e

GIT_COMMON_DIR="$(git rev-parse --git-common-dir 2>/dev/null || true)"
if [ -z "$GIT_COMMON_DIR" ]; then
    echo "[-] Error: Not inside a git repository." >&2
    exit 1
fi
REPO_ROOT="$(cd "$GIT_COMMON_DIR/.." && pwd)"

WORKTREES_DIR="$REPO_ROOT/.worktrees"

show_usage() {
    echo ""
    echo "NewsAlerts Git Worktree Helper (Bash)"
    echo "===================================="
    echo "Manages isolated development worktrees without dirtying the main repository root."
    echo ""
    echo "Usage:"
    echo "  ./scripts/worktree.sh new <branch-name> [base-branch]     Create a new worktree under .worktrees/"
    echo "  ./scripts/worktree.sh list                                List all active worktrees"
    echo "  ./scripts/worktree.sh remove <branch-or-folder> [-f]      Safely remove a worktree"
    echo "  ./scripts/worktree.sh merge-back <source> <target>        Merge sub-branch back into target feat/ branch"
    echo "  ./scripts/worktree.sh prune                               Prune deleted worktree references"
    echo ""
    echo "Naming Conventions:"
    echo "  Features:    feat/<short-descriptor>   (e.g. feat/vwap-filter)"
    echo "  Bug Fixes:   fix/<short-descriptor>    (e.g. fix/tape-timestamp)"
    echo "  Major Epics: major/<short-descriptor>  (e.g. major/v3-redesign)"
    echo "  Sub-tasks:   sub/<feature>/<task>      (e.g. sub/vwap-filter/tests)"
    echo ""
}

sanitize_branch() {
    echo "$1" | sed 's|[/\\:]|-|g' | tr -cd '[:alnum:]_.-'
}

ACTION="${1:-help}"
BRANCH="$2"
BASE="${3:-main}"
FORCE=0

for arg in "$@"; do
    if [ "$arg" = "-f" ] || [ "$arg" = "--force" ]; then
        FORCE=1
    fi
done

case "$ACTION" in
    new)
        if [ -z "$BRANCH" ]; then
            echo "[-] Error: Missing required <branch-name>." >&2
            exit 1
        fi
        FOLDER_NAME="$(sanitize_branch "$BRANCH")"
        TARGET_PATH="$WORKTREES_DIR/$FOLDER_NAME"

        if [ -d "$TARGET_PATH" ]; then
            echo "[-] Error: Worktree directory already exists: $TARGET_PATH" >&2
            exit 1
        fi

        mkdir -p "$WORKTREES_DIR"

        if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
            echo "[+] Adding worktree for existing branch '$BRANCH' at $TARGET_PATH..."
            git worktree add "$TARGET_PATH" "$BRANCH"
        else
            echo "[+] Creating new branch '$BRANCH' from '$BASE' in worktree at $TARGET_PATH..."
            git worktree add -b "$BRANCH" "$TARGET_PATH" "$BASE"
        fi

        echo ""
        echo "Worktree ready!"
        echo "Location: $TARGET_PATH"
        echo "Branch:   $BRANCH"
        echo ""
        echo "To start working in this worktree:"
        echo "  cd \"$TARGET_PATH\""
        echo ""
        ;;

    list)
        echo ""
        echo "Active Git Worktrees:"
        git worktree list
        echo ""
        ;;

    remove)
        if [ -z "$BRANCH" ]; then
            echo "[-] Error: Missing required <branch-or-folder>." >&2
            exit 1
        fi
        FOLDER_NAME="$(sanitize_branch "$BRANCH")"
        TARGET_PATH="$WORKTREES_DIR/$FOLDER_NAME"

        if [ ! -d "$TARGET_PATH" ] && [ -d "$WORKTREES_DIR/$BRANCH" ]; then
            TARGET_PATH="$WORKTREES_DIR/$BRANCH"
        fi

        if [ ! -d "$TARGET_PATH" ]; then
            echo "[-] Error: Worktree directory not found: $TARGET_PATH" >&2
            exit 1
        fi

        echo "[+] Removing worktree at $TARGET_PATH..."
        if [ "$FORCE" -eq 1 ]; then
            git worktree remove --force "$TARGET_PATH"
        else
            git worktree remove "$TARGET_PATH"
        fi
        git worktree prune
        echo "[✓] Worktree removed and pruned successfully."
        ;;

    merge-back)
        if [ -z "$BRANCH" ] || [ -z "$3" ] || [ "$3" = "-f" ]; then
            echo "[-] Error: Usage: ./scripts/worktree.sh merge-back <source-branch> <target-branch>" >&2
            exit 1
        fi
        SOURCE="$BRANCH"
        TARGET="$3"
        echo "[+] Merging sub-branch '$SOURCE' into target '$TARGET'..."
        git checkout "$TARGET"
        git merge --no-ff "$SOURCE" -m "feat(worktree): merge $SOURCE into $TARGET"
        echo "[✓] Successfully merged $SOURCE into $TARGET."
        echo "You can now push '$TARGET' or open a PR."
        ;;

    prune)
        git worktree prune
        echo "[✓] Worktree list pruned."
        ;;

    help|*)
        show_usage
        ;;
esac
