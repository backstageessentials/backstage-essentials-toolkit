"""Main Canvas sync entry point.

The sync() function is the top-level entry. Both `bes sync` (when the course
platform is canvas) and the local shim `scripts/sync.py` end up calling it.

Flow:
  1. Load course config and credentials from .env.
  2. Test API auth (or skip in dry-run).
  3. Find or create the course under canvas_account_id.
  4. Push course-description.md as the syllabus_body.
  5. For each unit: create the module, sync each lesson as a Canvas page,
     attach pages to the module, sync the knowledge-check quiz.
  6. Sync the course final as a Canvas quiz with a question group that
     picks N from M (the bank model).
  7. Write updated state. Print summary.

Dry-run mode runs the same flow but never hits the network. The CanvasClient
records every would-be request and returns deterministic stub responses, so
the orchestration can be exercised end to end against a real course repo
with no Canvas account at all.
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

from .canvas_client import CanvasClient, CanvasError
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
    ModeMismatchError,
    assert_mode_compatible,
    get_unit_state,
    lesson_needs_update,
    load_state,
    question_needs_update,
    record_lesson_sync,
    record_question_sync,
    save_state,
)

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

    api_url = os.getenv("CANVAS_API_URL", "")
    api_token = os.getenv("CANVAS_API_TOKEN", "")

    if not dry_run:
        if not api_token or api_token.startswith("your_"):
            print("  CANVAS_API_TOKEN missing or still a placeholder. Edit .env first.")
            return 1
        if not api_url or api_url.startswith("https://your-"):
            print("  CANVAS_API_URL missing or still a placeholder. Edit .env first.")
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
    if course_meta.get("platform") != "canvas":
        print(f"  course-config.yaml platform is '{course_meta.get('platform')}', not 'canvas'.")
        return 1

    # Phase 15: two modes.
    # - create mode: canvas_account_id is set; toolkit creates a fresh course.
    # - update mode: canvas_course_id is set; toolkit pushes into an existing
    #   course where the user already has teacher rights.
    account_id_raw = course_meta.get("canvas_account_id")
    existing_course_id_raw = course_meta.get("canvas_course_id")

    if account_id_raw is not None and existing_course_id_raw is not None:
        print("  course-config.yaml has BOTH canvas_account_id and "
              "canvas_course_id. Pick one. See SKILL.md.")
        return 1
    if account_id_raw is None and existing_course_id_raw is None:
        print("  course-config.yaml needs either canvas_account_id (create-new "
              "mode, admin) or canvas_course_id (update-existing mode, teacher).")
        return 1

    if existing_course_id_raw is not None:
        sync_mode = "update"
        try:
            existing_course_id = int(existing_course_id_raw)
        except (TypeError, ValueError):
            print(f"  canvas_course_id must be an integer, got "
                  f"{existing_course_id_raw!r}.")
            return 1
        account_id = None
        print(f"  OK (course: {course_name}, mode: update, "
              f"canvas_course_id: {existing_course_id})")
    else:
        sync_mode = "create"
        account_id = str(account_id_raw)
        existing_course_id = None
        print(f"  OK (course: {course_name}, mode: create, "
              f"canvas_account_id: {account_id})")

    if dry_run:
        print()
        print("DRY RUN: validating content and recording API payloads but not pushing.")
        print()

    print("[3/8] Testing API auth...")
    try:
        client = CanvasClient(
            api_url=api_url or "https://canvas.instructure.com",
            api_token=api_token or "dry-run-placeholder",
            account_id=account_id,
            dry_run=dry_run,
        )
        if not client.test_auth():
            print("  API auth failed. Check CANVAS_API_TOKEN and CANVAS_API_URL.")
            return 1
    except CanvasError as e:
        print(f"  {e}")
        return 1
    print("  OK")
    summary.api_calls += 1

    state = load_state(course_root)
    state["platform"] = "canvas"
    state["api_url"] = client.api_url
    state["account_id"] = account_id

    # Phase 15: refuse to silently flip mode or target between syncs.
    try:
        assert_mode_compatible(
            state, sync_mode,
            current_course_id=existing_course_id,
            current_account_id=account_id,
        )
    except ModeMismatchError as e:
        print(f"  {e}")
        return 1

    if sync_mode == "update":
        print("[4/8] Attaching to existing Canvas course...")
        course_url = None
        try:
            # Verify the user has access to the course before pushing
            # 200 questions into nothing.
            client.get_course(existing_course_id)
            summary.api_calls += 1
            course_id = existing_course_id
            state["course_id"] = course_id
            state["mode"] = "update"
            print(f"  OK (course_id: {course_id})")
            course_url = client.admin_url_for_course(course_id)

            # Update the syllabus from course-description.md.
            desc_path_str = course_meta.get("description_path",
                                              "./course-description.md")
            desc_path = Path(desc_path_str)
            if not desc_path.is_absolute():
                desc_path = course_root / desc_path
            syllabus_html = parse_course_description(desc_path)
            if syllabus_html:
                client.update_course_syllabus(course_id, syllabus_html)
                summary.api_calls += 1
                print("  Syllabus updated from course-description.md")
        except CanvasError as e:
            print(f"  Failed: {e}")
            print(f"  In update-existing mode, the toolkit needs teacher "
                  f"access to course_id {existing_course_id}. Verify the ID "
                  f"is correct and that your CANVAS_API_TOKEN belongs to a "
                  f"user listed as a teacher on that course.")
            return 1
    else:
        print("[4/8] Finding or creating course on Canvas...")
        course_url = None
        try:
            existing = client.find_course_by_code(account_id, course_slug)
            summary.api_calls += 1
            if existing:
                course_id = existing["id"]
                state["course_id"] = course_id
                print(f"  Found (course_id: {course_id})")
            else:
                new_course = client.create_course(
                    account_id=account_id,
                    name=course_name,
                    course_code=course_slug,
                )
                summary.api_calls += 1
                course_id = new_course["id"]
                state["course_id"] = course_id
                print(f"  Created (course_id: {course_id})")
            state["mode"] = "create"
            course_url = client.admin_url_for_course(course_id)

            # Push course description as syllabus_body.
            desc_path_str = course_meta.get("description_path",
                                              "./course-description.md")
            desc_path = Path(desc_path_str)
            if not desc_path.is_absolute():
                desc_path = course_root / desc_path
            syllabus_html = parse_course_description(desc_path)
            if syllabus_html:
                client.update_course_syllabus(course_id, syllabus_html)
                summary.api_calls += 1
                print("  Syllabus updated from course-description.md")
        except CanvasError as e:
            print(f"  Failed: {e}")
            return 1

    print("[5/8] Syncing units (modules + pages + quizzes)...")
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

        try:
            if unit_state["module_id"]:
                module_id = unit_state["module_id"]
            else:
                module = client.create_module(course_id, unit_title,
                                               position=unit_num or 0)
                module_id = module["id"]
                unit_state["module_id"] = module_id
                summary.api_calls += 1
                print(f"    Module created (module_id: {module_id})")
        except CanvasError as e:
            summary.errors.append(f"Unit {unit_num} module: {e}")
            save_state(course_root, state)
            continue

        # Sync each lesson as a Canvas page, then attach to the module.
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
                if existing_record.get("page_url"):
                    client.update_page(
                        course_id=course_id,
                        page_url=existing_record["page_url"],
                        title=lesson.title,
                        body_html=lesson.body_html,
                    )
                    page_url = existing_record["page_url"]
                    page_id = existing_record.get("page_id", 0)
                    summary.lessons_updated += 1
                    summary.api_calls += 1
                    print(f"    Lesson {lesson.title}: UPDATED")
                else:
                    new_page = client.create_page(
                        course_id=course_id,
                        title=lesson.title,
                        body_html=lesson.body_html,
                        published=False,
                    )
                    page_url = new_page.get("url") or lesson.page_url
                    page_id = new_page.get("id") or 0
                    summary.lessons_created += 1
                    summary.api_calls += 1

                    # Attach the new page to its module.
                    client.add_module_item(
                        course_id=course_id,
                        module_id=module_id,
                        title=lesson.title,
                        item_type="Page",
                        page_url=page_url,
                        position=lesson.order or None,
                    )
                    summary.api_calls += 1
                    print(f"    Lesson {lesson.title}: CREATED")

                record_lesson_sync(unit_state, lesson_filename,
                                    page_url, page_id, lesson.content_hash)
            except CanvasError as e:
                summary.errors.append(f"Lesson {lesson_path}: {e}")
            save_state(course_root, state)

        # Knowledge check quiz attached to the module.
        kc_path = unit_folder / "knowledge-check.yaml"
        if kc_path.exists():
            kc = parse_knowledge_check(kc_path)
            if kc:
                _sync_quiz(client, course_id, module_id, kc,
                           unit_state["knowledge_check"], summary, force_update,
                           attach_to_module=True)
        save_state(course_root, state)

    print("[6/8] Syncing course final...")
    final_path = course_root / "exam" / "course-final.yaml"
    if final_path.exists():
        final = parse_course_final(final_path)
        if final:
            # The course final is a single quiz with a question group that
            # samples N of M. Read counts from the YAML.
            with final_path.open() as f:
                final_data = yaml.safe_load(f) or {}
            final_meta = final_data.get("final_assessment", {})
            pick_count = final_meta.get("questions_per_attempt", 100)
            _sync_final_quiz(client, course_id, final, state["final_assessment"],
                             summary, force_update, pick_count=pick_count,
                             pass_threshold=final.pass_threshold,
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
        # Drop the recorded payloads next to sync-state.json so the user can
        # inspect what would have been sent.
        recorded_path = course_root / "sync-state.dry-run.json"
        with recorded_path.open("w") as f:
            json.dump({
                "platform": "canvas",
                "api_calls": summary.api_calls,
                "recorded_requests": client.recorded,
            }, f, indent=2, sort_keys=False)
        print(f"  Dry-run payloads written to {recorded_path.name}")

    print("[8/8] Done!")
    summary.print(course_url, time.time() - start_time, dry_run=dry_run)

    return 0 if not summary.errors else 1


def _sync_quiz(client: CanvasClient, course_id: int, module_id: int,
                quiz_content, quiz_state: dict, summary: SyncSummary,
                force_update: bool, attach_to_module: bool):
    """Sync a knowledge-check quiz, attached to its unit's module."""
    try:
        if not quiz_state.get("quiz_id"):
            quiz = client.create_quiz(
                course_id=course_id,
                title=quiz_content.title,
                quiz_type="assignment",
                pass_threshold=quiz_content.pass_threshold,
                shuffle_answers=getattr(quiz_content, "randomize", True),
                allowed_attempts=getattr(quiz_content, "max_attempts", None),
            )
            quiz_state["quiz_id"] = quiz["id"]
            summary.api_calls += 1
            if attach_to_module:
                client.add_module_item(
                    course_id=course_id,
                    module_id=module_id,
                    title=quiz_content.title,
                    item_type="Quiz",
                    content_id=quiz["id"],
                )
                summary.api_calls += 1
        quiz_id = quiz_state["quiz_id"]
    except CanvasError as e:
        summary.errors.append(f"Quiz {quiz_content.title}: {e}")
        return

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
                    course_id=course_id,
                    quiz_id=quiz_id,
                    question_id=existing["question_id"],
                    question_name=q_id,
                    question_text=q_text,
                    choices=choices,
                )
                api_q_id = existing["question_id"]
            else:
                new_q = client.add_quiz_question(
                    course_id=course_id,
                    quiz_id=quiz_id,
                    question_name=q_id,
                    question_text=q_text,
                    choices=choices,
                )
                api_q_id = new_q["id"]
            record_question_sync(quiz_state, q_id, api_q_id, q_hash)
            summary.questions_pushed += 1
            summary.api_calls += 1
        except CanvasError as e:
            summary.errors.append(f"Question {q_id}: {e}")

    print(f"    Quiz {quiz_content.title}: questions synced")


def _sync_final_quiz(client: CanvasClient, course_id: int, quiz_content,
                      quiz_state: dict, summary: SyncSummary, force_update: bool,
                      pick_count: int, pass_threshold: float,
                      batch_size: int, batch_sleep: float, dry_run: bool):
    """Sync the course final as a quiz with a question group that picks N of M."""
    try:
        if not quiz_state.get("quiz_id"):
            quiz = client.create_quiz(
                course_id=course_id,
                title=quiz_content.title,
                quiz_type="assignment",
                pass_threshold=pass_threshold,
                shuffle_answers=getattr(quiz_content, "randomize", True),
                allowed_attempts=getattr(quiz_content, "max_attempts", None),
            )
            quiz_state["quiz_id"] = quiz["id"]
            summary.api_calls += 1
            # Question group that randomly picks pick_count from the bank.
            group = client.create_quiz_question_group(
                course_id=course_id,
                quiz_id=quiz["id"],
                name=f"{quiz_content.title} bank",
                pick_count=pick_count,
            )
            quiz_state["group_id"] = group.get("id")
            summary.api_calls += 1
        quiz_id = quiz_state["quiz_id"]
    except CanvasError as e:
        summary.errors.append(f"Final quiz {quiz_content.title}: {e}")
        return

    pushed_in_batch = 0
    for q in quiz_content.questions:
        q_id = q.get("id")
        if not q_id:
            summary.errors.append(f"Final question without id")
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
                    course_id=course_id,
                    quiz_id=quiz_id,
                    question_id=existing["question_id"],
                    question_name=q_id,
                    question_text=q_text,
                    choices=choices,
                )
                api_q_id = existing["question_id"]
            else:
                new_q = client.add_quiz_question(
                    course_id=course_id,
                    quiz_id=quiz_id,
                    question_name=q_id,
                    question_text=q_text,
                    choices=choices,
                )
                api_q_id = new_q["id"]
            record_question_sync(quiz_state, q_id, api_q_id, q_hash)
            summary.questions_pushed += 1
            summary.api_calls += 1
            pushed_in_batch += 1
            if batch_size and pushed_in_batch >= batch_size:
                if not dry_run:
                    time.sleep(batch_sleep)
                pushed_in_batch = 0
        except CanvasError as e:
            summary.errors.append(f"Final question {q_id}: {e}")

    print(f"    Final {quiz_content.title}: {summary.questions_pushed} questions total so far")
