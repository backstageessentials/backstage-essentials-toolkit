"""Main TalentLMS sync entry point.

The sync() function is the top-level entry. Both `bes sync` (when the
course platform is talentlms) and the local shim `scripts/sync.py` end
up calling it.

Flow:
  1. Load course config and credentials from .env.
  2. Test API auth (or skip in dry-run).
  3. Find or create the course on TalentLMS.
  4. For each unit folder: emit a header unit (text type), then a content
     unit per lesson with HTML body, then a knowledge-check test.
  5. Sync the course final as a TalentLMS test.
  6. Write updated state. Print summary.

Dry-run mode runs the same flow but never hits the network. The
TalentLMSClient records every would-be request and returns deterministic
stub responses, so the orchestration can be exercised end to end against
a real course repo with no TalentLMS account at all.
"""

import hashlib
import json
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
    parse_course_description,
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
from .talentlms_client import TalentLMSClient, TalentLMSError

logger = logging.getLogger(__name__)


class SyncSummary:
    def __init__(self):
        self.lessons_created = 0
        self.lessons_updated = 0
        self.lessons_unchanged = 0
        self.questions_pushed = 0
        self.api_calls = 0
        self.errors: list[str] = []

    def print(self, course_url: Optional[str], elapsed_seconds: float,
              dry_run: bool = False):
        print()
        print("Summary:")
        print(f"  Lessons created:    {self.lessons_created}")
        print(f"  Lessons updated:    {self.lessons_updated}")
        print(f"  Lessons unchanged:  {self.lessons_unchanged}")
        print(f"  Questions pushed:   {self.questions_pushed}")
        print(f"  API calls:          {self.api_calls}")
        print(f"  Time:               {elapsed_seconds:.1f} seconds")
        if self.errors:
            print(f"  Errors:             {len(self.errors)}")
            for err in self.errors:
                print(f"    - {err}")
        if dry_run:
            print()
            print("DRY RUN: no requests were sent. Recorded payloads were validated only.")
        if course_url and not dry_run:
            print()
            print(f"View your course: {course_url}")


def sync(course_root: Path = None, dry_run: bool = False,
         force_update: bool = False,
         units_to_sync: Optional[list[int]] = None) -> int:
    """Top-level sync entry. Returns exit code (0 success, 1 failure)."""
    if course_root is None:
        course_root = Path.cwd()
    course_root = Path(course_root).resolve()

    start_time = time.time()
    summary = SyncSummary()

    print(f"[1/8] Checking environment in {course_root}...")

    config_file = course_root / "course-config.yaml"
    if not config_file.exists():
        print(f"  Missing course-config.yaml in {course_root}")
        return 1

    load_dotenv(course_root / ".env")

    api_url = os.getenv("TALENTLMS_API_URL", "")
    api_key = os.getenv("TALENTLMS_API_KEY", "")

    if not dry_run:
        if not api_key or api_key.startswith("your_"):
            print("  TALENTLMS_API_KEY missing or still a placeholder. Edit .env first.")
            return 1
        if not api_url or api_url.startswith("https://your-"):
            print("  TALENTLMS_API_URL missing or still a placeholder. Edit .env first.")
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
    if course_meta.get("platform") != "talentlms":
        print(f"  course-config.yaml platform is "
              f"'{course_meta.get('platform')}', not 'talentlms'.")
        return 1
    print(f"  OK (course: {course_name})")

    if dry_run:
        print()
        print("DRY RUN: validating content and recording API payloads but not pushing.")
        print()

    print("[3/8] Testing API auth...")
    try:
        client = TalentLMSClient(
            api_url=api_url or "https://example.talentlms.com",
            api_key=api_key or "dry-run-placeholder",
            dry_run=dry_run,
        )
        if not client.test_auth():
            print("  API auth failed. Check TALENTLMS_API_KEY and TALENTLMS_API_URL.")
            return 1
    except TalentLMSError as e:
        print(f"  {e}")
        return 1
    print("  OK")
    summary.api_calls += 1

    state = load_state(course_root)
    state["platform"] = "talentlms"
    state["api_url"] = client.api_url

    print("[4/8] Finding or creating course on TalentLMS...")
    course_url = None
    description_path_str = course_meta.get(
        "description_path", "./course-description.md"
    )
    description_path = Path(description_path_str)
    if not description_path.is_absolute():
        description_path = course_root / description_path
    description_html = parse_course_description(description_path)

    try:
        if state.get("course_id"):
            # Course already exists from a prior sync.
            course_id = state["course_id"]
            client.course_status(course_id)
            summary.api_calls += 1
            print(f"  Found (course_id: {course_id})")
        else:
            new_course = client.create_course(
                name=course_name,
                description=description_html,
            )
            summary.api_calls += 1
            course_id = new_course["id"]
            state["course_id"] = course_id
            print(f"  Created (course_id: {course_id})")
        course_url = client.admin_url_for_course(course_id)
    except TalentLMSError as e:
        print(f"  Failed: {e}")
        return 1

    print("[5/8] Syncing units (header + lessons + knowledge check)...")
    unit_folders = find_unit_folders(course_root / "content")
    for unit_folder in unit_folders:
        unit_data = parse_unit_yaml(unit_folder / "unit.yaml")
        unit_num = unit_data.get("number")
        unit_title = unit_data.get("title", unit_folder.name)
        unit_slug = unit_folder.name

        if units_to_sync and unit_num not in units_to_sync:
            continue

        print(f"  Unit {unit_num}: {unit_title}")
        unit_state = get_unit_state(state, unit_slug)

        # TalentLMS has no native sections. Emit a header text unit so the
        # course outline has visual breaks between course-units.
        try:
            if not unit_state.get("header_unit_id"):
                header = client.create_unit(
                    course_id=course_id,
                    name=f"Unit {unit_num}: {unit_title}" if unit_num
                          else unit_title,
                    unit_type="text",
                    description=unit_data.get("description", "") or "",
                )
                unit_state["header_unit_id"] = header["id"]
                summary.api_calls += 1
                print(f"    Header unit created (id: {header['id']})")
        except TalentLMSError as e:
            summary.errors.append(f"Unit {unit_num} header: {e}")
            save_state(course_root, state)
            continue

        # Sync each lesson as a TalentLMS web-content unit.
        for lesson_path in find_lessons_in_unit(unit_folder):
            try:
                lesson = parse_lesson(lesson_path)
                lesson_filename = lesson_path.name

                if not lesson_needs_update(unit_state, lesson_filename,
                                            lesson.content_hash, force_update):
                    summary.lessons_unchanged += 1
                    print(f"    Lesson {lesson.title}: unchanged")
                    continue

                existing_record = unit_state["lessons"].get(lesson_filename) or {}
                if existing_record.get("unit_id"):
                    # TalentLMS does not expose a clean "update unit body"
                    # endpoint on its public API. Re-uploading the file
                    # payload to the same unit is the workaround.
                    client.create_unit_file(
                        unit_id=existing_record["unit_id"],
                        content_html=lesson.body_html,
                    )
                    unit_id = existing_record["unit_id"]
                    summary.lessons_updated += 1
                    summary.api_calls += 1
                    print(f"    Lesson {lesson.title}: UPDATED")
                else:
                    new_unit = client.create_unit(
                        course_id=course_id,
                        name=lesson.title,
                        unit_type="web",
                        description="",
                    )
                    unit_id = new_unit["id"]
                    summary.api_calls += 1

                    client.create_unit_file(
                        unit_id=unit_id,
                        content_html=lesson.body_html,
                    )
                    summary.api_calls += 1
                    summary.lessons_created += 1
                    print(f"    Lesson {lesson.title}: CREATED")

                record_lesson_sync(unit_state, lesson_filename,
                                    unit_id, lesson.content_hash)
            except TalentLMSError as e:
                summary.errors.append(f"Lesson {lesson_path}: {e}")
            save_state(course_root, state)

        # Knowledge-check test.
        kc_path = unit_folder / "knowledge-check.yaml"
        if kc_path.exists():
            kc = parse_knowledge_check(kc_path)
            if kc:
                _sync_test(client, course_id, kc,
                            unit_state["knowledge_check"], summary,
                            force_update)
        save_state(course_root, state)

    print("[6/8] Syncing course final...")
    final_path = course_root / "exam" / "course-final.yaml"
    if final_path.exists():
        final = parse_course_final(final_path)
        if final:
            _sync_test(client, course_id, final,
                        state["final_assessment"], summary,
                        force_update,
                        batch_size=10, batch_sleep=1.0,
                        dry_run=dry_run)
            save_state(course_root, state)
        else:
            print("  No questions in course-final.yaml yet, skipping.")
    else:
        print("  No exam/course-final.yaml, skipping.")

    print("[7/8] Writing sync-state.json...")
    save_state(course_root, state)
    print("  OK")

    if dry_run:
        recorded_path = course_root / "sync-state.dry-run.json"
        with recorded_path.open("w") as f:
            json.dump({
                "platform": "talentlms",
                "api_calls": summary.api_calls,
                "recorded_requests": client.recorded,
            }, f, indent=2, sort_keys=False)
        print(f"  Dry-run payloads written to {recorded_path.name}")

    print("[8/8] Done!")
    summary.print(course_url, time.time() - start_time, dry_run=dry_run)

    return 0 if not summary.errors else 1


def _sync_test(client: TalentLMSClient, course_id: int, quiz_content,
                quiz_state: dict, summary: SyncSummary, force_update: bool,
                batch_size: int = 0, batch_sleep: float = 0.0,
                dry_run: bool = False):
    """Sync a quiz (knowledge check or course final) as a TalentLMS test."""
    try:
        if not quiz_state.get("test_id"):
            test = client.create_course_test(
                course_id=course_id,
                name=quiz_content.title,
                description="",
                pass_score=int(quiz_content.pass_threshold * 100),
                shuffle_questions=getattr(quiz_content, "randomize", True),
                shuffle_answers=getattr(quiz_content, "randomize", True),
                max_attempts=getattr(quiz_content, "max_attempts", None),
            )
            quiz_state["test_id"] = test["id"]
            summary.api_calls += 1
        test_id = quiz_state["test_id"]
    except TalentLMSError as e:
        summary.errors.append(f"Test {quiz_content.title}: {e}")
        return

    pushed_in_batch = 0
    for q in quiz_content.questions:
        q_id = q.get("id")
        if not q_id:
            summary.errors.append(
                f"Question without id in {quiz_content.title}"
            )
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
            new_q = client.create_test_question(
                test_id=test_id,
                question_text=q_text,
                choices=choices,
                explanation=explanation,
            )
            api_q_id = new_q.get("id", 0)
            record_question_sync(quiz_state, q_id, api_q_id, q_hash)
            summary.questions_pushed += 1
            summary.api_calls += 1
            pushed_in_batch += 1
            if batch_size and pushed_in_batch >= batch_size:
                if not dry_run:
                    time.sleep(batch_sleep)
                pushed_in_batch = 0
        except TalentLMSError as e:
            summary.errors.append(f"Question {q_id}: {e}")

    print(f"    Test {quiz_content.title}: questions synced")
