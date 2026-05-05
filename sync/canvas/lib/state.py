"""Sync state tracking for Canvas.

sync-state.json records what got pushed to Canvas and when. Used for change
detection (skip unchanged lessons) and recovery (resume after partial failure).

The file is gitignored because it is machine-specific and contains Canvas
object IDs that are tied to a specific Canvas account/instance.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


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
        "platform": "canvas",
        "course_id": None,
        "api_url": None,
        "account_id": None,
        # Phase 15: which mode this course was synced in.
        # "create" - course was created via canvas_account_id
        # "update" - course was attached via canvas_course_id (existing course)
        "mode": None,
        "last_sync": None,
        "units": {},
        "final_assessment": {
            "quiz_id": None,
            "questions": {},
        },
    }


class ModeMismatchError(Exception):
    """Raised when a sync run uses a different mode than the previous sync."""


def assert_mode_compatible(state: dict, current_mode: str,
                            current_course_id: Optional[int] = None,
                            current_account_id: Optional[str] = None) -> None:
    """Raise ModeMismatchError if state recorded a different mode previously.

    Mode flips would mean pushing into a different Canvas course than the
    last sync touched, which is almost always a config mistake. Fail loud
    rather than silently re-creating content in the wrong place.
    """
    prior_mode = state.get("mode")
    if prior_mode is None:
        return  # First sync; any mode is fine.
    if prior_mode == current_mode:
        # Same mode; verify the target hasn't changed.
        if current_mode == "create":
            prior_account = state.get("account_id")
            if prior_account and current_account_id and \
               str(prior_account) != str(current_account_id):
                raise ModeMismatchError(
                    f"sync-state.json was created against canvas_account_id="
                    f"{prior_account}, but course-config.yaml now lists "
                    f"canvas_account_id={current_account_id}. If you really "
                    f"want to push to a different account, delete "
                    f"sync-state.json first (you will lose the change-tracking "
                    f"and re-create everything)."
                )
        elif current_mode == "update":
            prior_course_id = state.get("course_id")
            if prior_course_id and current_course_id and \
               int(prior_course_id) != int(current_course_id):
                raise ModeMismatchError(
                    f"sync-state.json was created against canvas_course_id="
                    f"{prior_course_id}, but course-config.yaml now lists "
                    f"canvas_course_id={current_course_id}. If you really "
                    f"want to push to a different course, delete "
                    f"sync-state.json first (you will lose the change-tracking "
                    f"and re-create everything)."
                )
        return
    # Mode flip.
    raise ModeMismatchError(
        f"sync-state.json records mode='{prior_mode}' from a previous sync, "
        f"but course-config.yaml is now configured for mode='{current_mode}'. "
        f"Pick one and stick with it for this course. To switch modes, "
        f"delete sync-state.json (you will lose the change-tracking and "
        f"re-create or re-touch everything on the next sync)."
    )


def get_unit_state(state: dict, unit_slug: str) -> dict:
    if unit_slug not in state["units"]:
        state["units"][unit_slug] = {
            "module_id": None,
            "lessons": {},
            "knowledge_check": {
                "quiz_id": None,
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
                        page_url: str, page_id: int, content_hash: str) -> None:
    unit_state["lessons"][lesson_filename] = {
        "page_url": page_url,
        "page_id": page_id,
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
