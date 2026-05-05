"""Main sync entry point.

The sync() function is the top-level entry. Both `bes sync` and the local
shim `scripts/sync.py` end up calling it.

The flow is:

  1. Load course config and credentials.
  2. Test API auth.
  3. Find or create the course on Thinkific.
  4. For each unit: sync the chapter, lessons, knowledge check.
  5. Sync the course final assessment.
  6. Write updated state. Print summary.
"""

import hashlib
import logging
import os
import time
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv

from .content_parser import (
    find_lessons_in_unit,
    find_unit_folders,
    parse_course_final,
    parse_knowledge_check,
    parse_lesson,
    parse_unit_yaml,
)
from .state import (
    get_unit_state,
    lesson_needs_update,
    load_state,
    question_needs_update,
    record_lesson_sync,
    record_question_sync,
    save_state,
)
from .thinkific_client import ThinkificClient, ThinkificError


logger = logging.getLogger(__name__)


class SyncSummary:
    """Tracks counts during a sync run for the final report."""

    def __init__(self):
        self.lessons_created = 0
        self.lessons_updated = 0
        self.lessons_unchanged = 0
        self.questions_pushed = 0
        self.api_calls = 0
        self.errors: list[str] = []

    def print(self, course_url: Optional[str], elapsed_seconds: float):
        print()
        print("Summary:")
        print(f"  Lessons created:    {self.lessons_created}")
        print(f"  Lessons updated:    {self.lessons_updated}")
        print(f"  Lessons unchanged:  {self.lessons_unchanged}")
        print(f"  Questions pushed:   {self.questions_pushed}")
        print(f"  Time:               {elapsed_seconds:.1f} seconds")
        if self.errors:
            print(f"  Errors:             {len(self.errors)}")
            for err in self.errors:
                print(f"    - {err}")
        if course_url:
            print()
            print(f"View your course: {course_url}")


def sync(course_root: Path = None, dry_run: bool = False,
         force_update: bool = False, units_to_sync: Optional[list[int]] = None) -> int:
    """Top-level sync entry. Returns exit code (0 success, 1 failure)."""
    if course_root is None:
        course_root = Path.cwd()
    course_root = Path(course_root).resolve()

    start_time = time.time()
    summary = SyncSummary()

    print(f"[1/8] Checking environment in {course_root}...")

    # Verify required files
    config_file = course_root / "course-config.yaml"
    if not config_file.exists():
        print(f"  Missing course-config.yaml in {course_root}")
        return 1

    # Load .env (will silently do nothing if .env is missing)
    load_dotenv(course_root / ".env")

    api_key = os.getenv("THINKIFIC_API_KEY", "")
    subdomain = os.getenv("THINKIFIC_SUBDOMAIN", "")

    if not api_key or api_key.startswith("your_"):
        print("  THINKIFIC_API_KEY missing or still a placeholder. Edit .env first.")
        return 1
    if not subdomain or subdomain.startswith("your_"):
        print("  THINKIFIC_SUBDOMAIN missing or still a placeholder. Edit .env first.")
        return 1

    print("  OK")

    print("[2/8] Loading configuration...")
    with config_file.open() as f:
        config = yaml.safe_load(f) or {}
    course_meta = config.get("course", {})
    course_name = course_meta.get("name")
    course_slug = course_meta.get("slug")
    if not course_name or not course_slug:
        print("  course-config.yaml missing required fields (name, slug).")
        return 1
    if course_meta.get("platform") != "thinkific":
        print(f"  course-config.yaml platform is '{course_meta.get('platform')}', not 'thinkific'.")
        return 1
    print(f"  OK (course: {course_name})")

    if dry_run:
        print()
        print("DRY RUN: validating content but not pushing to Thinkific.")
        print()

    print("[3/8] Testing API auth...")
    try:
        client = ThinkificClient(api_key, subdomain)
        if not client.test_auth():
            print("  API auth failed. Check THINKIFIC_API_KEY and THINKIFIC_SUBDOMAIN.")
            return 1
    except ThinkificError as e:
        print(f"  {e}")
        return 1
    print("  OK")
    summary.api_calls += 1

    state = load_state(course_root)
    course_url = None

    if dry_run:
        print("[4/8] (skipped in dry run)")
        print("[5/8] Validating units...")
        unit_folders = find_unit_folders(course_root / "content")
        for unit_folder in unit_folders:
            unit_data = parse_unit_yaml(unit_folder / "unit.yaml")
            unit_num = unit_data.get("number", "?")
            print(f"  Unit {unit_num}: {unit_data.get('title', unit_folder.name)}")
            for lesson_path in find_lessons_in_unit(unit_folder):
                try:
                    lesson = parse_lesson(lesson_path)
                    print(f"    {lesson.title} (would sync)")
                except Exception as e:
                    summary.errors.append(f"Lesson {lesson_path}: {e}")
        print("[6/8] (skipped in dry run)")
        print("[7/8] (skipped in dry run)")
        print("[8/8] Dry run complete.")
        summary.print(course_url, time.time() - start_time)
        return 0 if not summary.errors else 1

    print("[4/8] Finding course on Thinkific...")
    try:
        existing = client.find_course_by_slug(course_slug)
        summary.api_calls += 1
        if existing:
            course_id = existing["id"]
            state["course_id"] = course_id
            state["subdomain"] = subdomain
            print(f"  Found (course_id: {course_id})")
        else:
            new_course = client.create_course(
                name=course_name,
                slug=course_slug,
                description=course_meta.get("description", ""),
            )
            summary.api_calls += 1
            course_id = new_course["id"]
            state["course_id"] = course_id
            state["subdomain"] = subdomain
            print(f"  Created (course_id: {course_id})")
        course_url = client.admin_url_for_course(course_id)
    except ThinkificError as e:
        print(f"  Failed: {e}")
        return 1

    print("[5/8] Syncing units...")
    unit_folders = find_unit_folders(course_root / "content")
    for unit_folder in unit_folders:
        unit_data = parse_unit_yaml(unit_folder / "unit.yaml")
        unit_num = unit_data.get("number")
        unit_title = unit_data.get("title", unit_folder.name)
        unit_slug = unit_folder.name

        # Filter by units_to_sync if specified
        if units_to_sync and unit_num not in units_to_sync:
            continue

        print(f"  Unit {unit_num}: {unit_title}")

        unit_state = get_unit_state(state, unit_slug)

        # Find or create the chapter
        try:
            if unit_state["chapter_id"]:
                chapter_id = unit_state["chapter_id"]
            else:
                chapter = client.create_chapter(course_id, unit_title, position=unit_num or 0)
                chapter_id = chapter["id"]
                unit_state["chapter_id"] = chapter_id
                summary.api_calls += 1
                print(f"    Chapter created (chapter_id: {chapter_id})")
        except ThinkificError as e:
            summary.errors.append(f"Unit {unit_num} chapter: {e}")
            save_state(course_root, state)
            continue

        # Sync each lesson
        for lesson_path in find_lessons_in_unit(unit_folder):
            try:
                lesson = parse_lesson(lesson_path)
                lesson_filename = lesson_path.name

                if not lesson_needs_update(unit_state, lesson_filename, lesson.content_hash, force_update):
                    summary.lessons_unchanged += 1
                    print(f"    Lesson {lesson.title}: unchanged")
                    continue

                existing_record = unit_state["lessons"].get(lesson_filename)
                if existing_record and existing_record.get("content_id"):
                    client.update_lesson(
                        content_id=existing_record["content_id"],
                        name=lesson.title,
                        body_html=lesson.body_html,
                    )
                    record_lesson_sync(unit_state, lesson_filename,
                                        existing_record["content_id"], lesson.content_hash)
                    summary.lessons_updated += 1
                    summary.api_calls += 1
                    print(f"    Lesson {lesson.title}: UPDATED")
                else:
                    new_lesson = client.create_lesson(
                        chapter_id=chapter_id,
                        name=lesson.title,
                        body_html=lesson.body_html,
                        position=lesson.order or 0,
                    )
                    record_lesson_sync(unit_state, lesson_filename,
                                        new_lesson["id"], lesson.content_hash)
                    summary.lessons_created += 1
                    summary.api_calls += 1
                    print(f"    Lesson {lesson.title}: CREATED")
            except ThinkificError as e:
                summary.errors.append(f"Lesson {lesson_path}: {e}")

            save_state(course_root, state)  # save after each lesson for recovery

        # Sync the unit knowledge check
        kc_path = unit_folder / "knowledge-check.yaml"
        if kc_path.exists():
            kc = parse_knowledge_check(kc_path)
            if kc:
                _sync_quiz(client, chapter_id, kc, unit_state["knowledge_check"],
                           summary, force_update, position=99)
        save_state(course_root, state)

    print("[6/8] Syncing course final...")
    final_path = course_root / "exam" / "course-final.yaml"
    if final_path.exists():
        final = parse_course_final(final_path)
        if final:
            # The course final attaches to the course, not a chapter. Thinkific
            # treats it as a final quiz at the course level. Implementation
            # detail: in practice, create a final chapter for it.
            final_chapter_state = state.get("final_chapter", {})
            if not final_chapter_state.get("chapter_id"):
                try:
                    chapter = client.create_chapter(course_id, "Course Final", position=999)
                    final_chapter_state["chapter_id"] = chapter["id"]
                    state["final_chapter"] = final_chapter_state
                    summary.api_calls += 1
                except ThinkificError as e:
                    summary.errors.append(f"Final chapter: {e}")
                    final_chapter_state = None
            if final_chapter_state and final_chapter_state.get("chapter_id"):
                _sync_quiz(client, final_chapter_state["chapter_id"], final,
                           state["final_assessment"], summary, force_update,
                           position=0, batch_size=10, batch_sleep=1.0)
            save_state(course_root, state)
        else:
            print("  No questions in course-final.yaml yet, skipping.")
    else:
        print("  No exam/course-final.yaml, skipping.")

    print("[7/8] Writing sync-state.json...")
    save_state(course_root, state)
    print("  OK")

    print("[8/8] Done!")
    summary.print(course_url, time.time() - start_time)

    return 0 if not summary.errors else 1


def _sync_quiz(client: ThinkificClient, chapter_id: int, quiz_content,
               quiz_state: dict, summary: SyncSummary, force_update: bool,
               position: int, batch_size: int = 0, batch_sleep: float = 0.0):
    """Sync a quiz (knowledge check or course final).

    batch_size and batch_sleep let the course final throttle requests.
    """
    try:
        if not quiz_state.get("quiz_id"):
            quiz = client.create_quiz(
                chapter_id=chapter_id,
                name=quiz_content.title,
                position=position,
                pass_threshold=quiz_content.pass_threshold,
                max_attempts=getattr(quiz_content, "max_attempts", None),
                randomize_questions=getattr(quiz_content, "randomize", True),
                randomize_answers=getattr(quiz_content, "randomize", True),
            )
            quiz_state["quiz_id"] = quiz["id"]
            summary.api_calls += 1
        quiz_id = quiz_state["quiz_id"]
    except ThinkificError as e:
        summary.errors.append(f"Quiz {quiz_content.title}: {e}")
        return

    pushed_in_batch = 0
    for q in quiz_content.questions:
        q_id = q.get("id")
        if not q_id:
            summary.errors.append(f"Question without id in {quiz_content.title}")
            continue

        q_text = q.get("question", "")
        choices = q.get("choices", [])
        explanation = q.get("explanation", "")
        q_hash = hashlib.sha256(
            (q_text + str(choices) + explanation).encode("utf-8")
        ).hexdigest()[:16]

        if not question_needs_update(quiz_state, q_id, q_hash, force_update):
            continue

        try:
            existing = quiz_state["questions"].get(q_id)
            if existing and existing.get("question_id"):
                client.update_quiz_question(
                    question_id=existing["question_id"],
                    question_text=q_text,
                    choices=choices,
                    explanation=explanation,
                )
                api_q_id = existing["question_id"]
            else:
                new_q = client.add_quiz_question(
                    quiz_id=quiz_id,
                    question_text=q_text,
                    choices=choices,
                    explanation=explanation,
                )
                api_q_id = new_q["id"]
            record_question_sync(quiz_state, q_id, api_q_id, q_hash)
            summary.questions_pushed += 1
            summary.api_calls += 1
            pushed_in_batch += 1
            if batch_size and pushed_in_batch >= batch_size:
                time.sleep(batch_sleep)
                pushed_in_batch = 0
        except ThinkificError as e:
            summary.errors.append(f"Question {q_id}: {e}")

    print(f"    {quiz_content.title}: {summary.questions_pushed} questions total so far")
