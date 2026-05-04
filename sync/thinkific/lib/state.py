"""Sync state tracking.

sync-state.json records what got pushed to Thinkific and when. Used for
change detection (skip unchanged lessons) and recovery (resume after partial
failure).

The file is gitignored because it's machine-specific and contains Thinkific
object IDs that are tied to a specific Thinkific account.
"""

import json
from datetime import datetime, timezone
from pathlib import Path


def load_state(course_root: Path) -> dict:
    """Load sync-state.json from the course root. Returns empty dict if missing."""
    state_file = course_root / "sync-state.json"
    if not state_file.exists():
        return _empty_state()
    try:
        with state_file.open() as f:
            data = json.load(f)
        # Migrate old shapes if needed (future-proofing)
        if "version" not in data:
            data["version"] = 1
        return data
    except (json.JSONDecodeError, OSError):
        return _empty_state()


def save_state(course_root: Path, state: dict) -> None:
    """Save state to sync-state.json. Updates last_sync timestamp."""
    state["last_sync"] = datetime.now(timezone.utc).isoformat()
    state_file = course_root / "sync-state.json"
    with state_file.open("w") as f:
        json.dump(state, f, indent=2, sort_keys=True)


def _empty_state() -> dict:
    """An initial state for a never-synced course."""
    return {
        "version": 1,
        "course_id": None,
        "subdomain": None,
        "last_sync": None,
        "units": {},
        "final_assessment": {
            "quiz_id": None,
            "questions": {},
        },
    }


def get_unit_state(state: dict, unit_slug: str) -> dict:
    """Get the state for a unit, creating an empty entry if missing."""
    if unit_slug not in state["units"]:
        state["units"][unit_slug] = {
            "chapter_id": None,
            "lessons": {},
            "knowledge_check": {
                "quiz_id": None,
                "questions": {},
            },
        }
    return state["units"][unit_slug]


def lesson_needs_update(unit_state: dict, lesson_filename: str,
                         current_hash: str, force: bool = False) -> bool:
    """Decide whether to push a lesson based on hash comparison."""
    if force:
        return True
    lesson_record = unit_state["lessons"].get(lesson_filename)
    if not lesson_record:
        return True  # never synced
    return lesson_record.get("hash") != current_hash


def record_lesson_sync(unit_state: dict, lesson_filename: str,
                        content_id: int, content_hash: str) -> None:
    """Record that a lesson got synced."""
    unit_state["lessons"][lesson_filename] = {
        "content_id": content_id,
        "hash": content_hash,
    }


def question_needs_update(quiz_state: dict, question_id: str,
                           current_hash: str, force: bool = False) -> bool:
    """Decide whether to push a quiz question."""
    if force:
        return True
    record = quiz_state["questions"].get(question_id)
    if not record:
        return True
    return record.get("hash") != current_hash


def record_question_sync(quiz_state: dict, question_id: str,
                          api_question_id: int, content_hash: str) -> None:
    """Record that a quiz question got synced."""
    quiz_state["questions"][question_id] = {
        "question_id": api_question_id,
        "hash": content_hash,
    }
