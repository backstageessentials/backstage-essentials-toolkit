"""Sync state tracking for TalentLMS.

sync-state.json records what got pushed to TalentLMS and when. Used for
change detection (skip unchanged lessons) and recovery (resume after
partial failure).

The file is gitignored because it is machine-specific and contains
TalentLMS object IDs that are tied to a specific TalentLMS account.
"""

import json
from datetime import datetime, timezone
from pathlib import Path


def load_state(course_root: Path) -> dict:
    state_file = course_root / "sync-state.json"
    if not state_file.exists():
        return _empty_state()
    try:
        with state_file.open() as f:
            data = json.load(f)
        if "version" not in data:
            data["version"] = 1
        return data
    except (json.JSONDecodeError, OSError):
        return _empty_state()


def save_state(course_root: Path, state: dict) -> None:
    state["last_sync"] = datetime.now(timezone.utc).isoformat()
    state_file = course_root / "sync-state.json"
    with state_file.open("w") as f:
        json.dump(state, f, indent=2, sort_keys=True)


def _empty_state() -> dict:
    return {
        "version": 1,
        "platform": "talentlms",
        "course_id": None,
        "api_url": None,
        "last_sync": None,
        "units": {},
        "final_assessment": {
            "test_id": None,
            "questions": {},
        },
    }


def get_unit_state(state: dict, unit_slug: str) -> dict:
    if unit_slug not in state["units"]:
        state["units"][unit_slug] = {
            # TalentLMS has no native section concept. The sync emits a
            # text-type "header" unit per course-unit-folder so the course
            # outline has visual breaks. header_unit_id records that header.
            "header_unit_id": None,
            "lessons": {},
            "knowledge_check": {
                "test_id": None,
                "questions": {},
            },
        }
    return state["units"][unit_slug]


def lesson_needs_update(unit_state: dict, lesson_filename: str,
                         current_hash: str, force: bool = False) -> bool:
    if force:
        return True
    record = unit_state["lessons"].get(lesson_filename)
    if not record:
        return True
    return record.get("hash") != current_hash


def record_lesson_sync(unit_state: dict, lesson_filename: str,
                        unit_id: int, content_hash: str) -> None:
    unit_state["lessons"][lesson_filename] = {
        "unit_id": unit_id,
        "hash": content_hash,
    }


def question_needs_update(quiz_state: dict, question_id: str,
                           current_hash: str, force: bool = False) -> bool:
    if force:
        return True
    record = quiz_state["questions"].get(question_id)
    if not record:
        return True
    return record.get("hash") != current_hash


def record_question_sync(quiz_state: dict, question_id: str,
                          api_question_id: int, content_hash: str) -> None:
    quiz_state["questions"][question_id] = {
        "question_id": api_question_id,
        "hash": content_hash,
    }
