"""Thin wrapper around git operations.

We shell out to git rather than using GitPython because git is always
installed where bes runs and the operations we need are simple.
"""

import subprocess
from pathlib import Path
from typing import Optional


class GitError(Exception):
    """Raised when a git command fails."""


def run_git(args: list[str], cwd: Path) -> tuple[int, str, str]:
    """Run a git command. Returns (exit_code, stdout, stderr)."""
    result = subprocess.run(
        ["git"] + args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def is_git_repo(path: Path) -> bool:
    """True if path is inside a git repository."""
    code, _, _ = run_git(["rev-parse", "--is-inside-work-tree"], cwd=path)
    return code == 0


def has_uncommitted_changes(path: Path) -> bool:
    """True if there are uncommitted changes (staged or unstaged)."""
    code, stdout, _ = run_git(["status", "--porcelain"], cwd=path)
    if code != 0:
        return False
    return bool(stdout.strip())


def list_changed_files(path: Path) -> list[str]:
    """Return a list of changed files (relative paths)."""
    code, stdout, _ = run_git(["status", "--porcelain"], cwd=path)
    if code != 0:
        return []
    files = []
    for line in stdout.splitlines():
        # Format is "XY filename" where XY is the status code
        if len(line) > 3:
            files.append(line[3:].strip())
    return files


def stage_all(path: Path) -> bool:
    """Stage all changes. Returns True on success."""
    code, _, _ = run_git(["add", "-A"], cwd=path)
    return code == 0


def commit(path: Path, message: str) -> tuple[bool, str]:
    """Commit staged changes with a message. Returns (success, output)."""
    code, stdout, stderr = run_git(["commit", "-m", message], cwd=path)
    output = stdout if code == 0 else (stderr or stdout)
    return code == 0, output


def push(path: Path) -> tuple[bool, str]:
    """Push to origin. Returns (success, output)."""
    code, stdout, stderr = run_git(["push"], cwd=path)
    output = stdout if code == 0 else (stderr or stdout)
    return code == 0, output


def current_branch(path: Path) -> Optional[str]:
    """Return the current branch name, or None if detached HEAD."""
    code, stdout, _ = run_git(["branch", "--show-current"], cwd=path)
    if code != 0 or not stdout:
        return None
    return stdout


def commits_ahead_of_origin(path: Path) -> int:
    """Count commits on the local branch that are not on origin/branch."""
    branch = current_branch(path)
    if not branch:
        return 0
    code, stdout, _ = run_git(
        ["rev-list", "--count", f"origin/{branch}..HEAD"],
        cwd=path,
    )
    if code != 0:
        return 0
    try:
        return int(stdout.strip())
    except ValueError:
        return 0


def auto_commit_message(path: Path) -> str:
    """Generate a commit message from the diff if the user did not provide one.

    Simple heuristic: count what changed, summarize.
    """
    files = list_changed_files(path)
    if not files:
        return "Update content"

    # Categorize changes
    lessons = [f for f in files if "/lessons/" in f and f.endswith(".md")]
    quizzes = [f for f in files if "knowledge-check" in f or "course-final" in f]
    config = [f for f in files if f.endswith(".yaml") and "/lessons/" not in f]
    docs = [f for f in files if f.startswith("docs/") or f == "README.md"]

    parts = []
    if lessons:
        parts.append(f"{len(lessons)} lesson{'s' if len(lessons) != 1 else ''}")
    if quizzes:
        parts.append(f"{len(quizzes)} quiz file{'s' if len(quizzes) != 1 else ''}")
    if config:
        parts.append(f"{len(config)} config")
    if docs:
        parts.append(f"{len(docs)} doc{'s' if len(docs) != 1 else ''}")

    if not parts:
        return f"Update {len(files)} files"

    return f"Update {', '.join(parts)}"
