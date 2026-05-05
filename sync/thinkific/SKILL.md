---
name: thinkific-sync
version: 1.0
description: Push course content to Thinkific via their REST API
inputs:
  - course_root: folder_path, required, default current working directory
  - dry_run: boolean, default false
  - force_update: boolean, default false
  - units_to_sync: list of integers, optional (sync only specific units; default all)
outputs:
  - Updates a Thinkific course (creates if missing, updates if exists)
  - Console log of operations performed
  - sync-state.json in course root (records what got synced when, for change detection)
dependencies:
  - course-spec-builder (course needs a spec)
  - repo-bootstrap (course needs a populated repo)
phase: 2
status: ready
subject_neutral: true
audience_neutral: true
platform: thinkific
---

# Thinkific Sync

Pushes course content to Thinkific via their REST API. The skill is invoked two ways:

- **bes sync** from inside any course folder: bes reads `course-config.yaml`, sees `platform: thinkific`, and calls this skill.
- **python3 scripts/sync.py** from inside the course folder: the shim sync.py written by repo-bootstrap imports the toolkit and runs this skill.

Both paths run the same code. bes is just easier to type.

## When to Use

After you have a populated course repo (lessons drafted, knowledge checks written, course final populated) and a Thinkific account with API credentials configured in `.env`. Run sync to push your local content to Thinkific.

The first sync is the slowest (creates everything from scratch). Subsequent syncs are fast (only pushes what changed since last sync).

Do NOT run sync if:
- The .env file is missing or has placeholder values
- course-config.yaml is missing or unparseable
- You have not validated the course content first (`bes validate`)

The skill is idempotent. Safe to run repeatedly. Each run makes Thinkific match the local files. No duplicates. No data loss.

## Steps

1. Verify environment:
   - `.env` exists in course root, has THINKIFIC_API_KEY and THINKIFIC_SUBDOMAIN populated with non-placeholder values
   - `course-config.yaml` exists and parses; platform field is `thinkific`
   - All required content files exist (every unit folder has unit.yaml, lessons/, knowledge-check.yaml; exam/course-final.yaml exists)
   
   If any check fails, stop and tell the user what's wrong.

2. Load configuration:
   - Read course-config.yaml for course metadata (name, slug, completion threshold)
   - Read .env for credentials
   - Load sync-state.json from course root if it exists; if missing, this is a first-time sync

3. Test API authentication:
   - Make a single GET request to /courses with the credentials
   - If 401 or 403, stop and tell the user the API key or subdomain is wrong
   - If 429 (rate limited) or other errors, retry with backoff up to 3 times

4. Find or create the course on Thinkific:
   - GET /courses, look for one with matching slug
   - If found: store course_id, plan to UPDATE
   - If not found: POST /courses to create, store the new course_id, plan to CREATE
   - Update sync-state.json with course_id

5. Sync each unit (chapter on Thinkific):
   For each unit folder in content/, in order:
   
   a. Read unit.yaml for unit metadata
   b. Find or create the chapter on Thinkific (POST /chapters or PUT /chapters/{id})
   c. Sync each lesson in the unit's lessons/ folder:
      - Convert markdown to HTML using markdown-it-py
      - Find or create the lesson (POST /contents with content_type: Lesson)
      - Compare local content hash to sync-state.json hash; skip if unchanged unless force_update is true
   d. Sync the unit knowledge check:
      - Find or create the quiz (POST /quizzes)
      - For each question in knowledge-check.yaml:
        - Find or create the question (POST /quiz_questions)
        - Update if changed
   e. Update sync-state.json after each unit completes (so partial failures are recoverable)

6. Sync the course final assessment:
   - Read exam/course-final.yaml
   - Find or create the final quiz on Thinkific
   - Sync questions in batches of 10 with a 1-second sleep between batches (rate limit protection)
   - Update sync-state.json

7. Final report:
   - Number of lessons created
   - Number of lessons updated
   - Number of lessons unchanged (skipped)
   - Number of questions pushed
   - Total API calls made
   - Total time elapsed
   - Any errors or warnings

8. Print the URL of the course on Thinkific so the user can open it in a browser to verify.

## Output Format

### Console output during sync

```
[1/8] Checking environment... OK
[2/8] Loading configuration... OK (course: Backstage Essentials)
[3/8] Testing API auth... OK
[4/8] Finding course on Thinkific... CREATED (course_id: 12345)
[5/8] Syncing units...
  Unit 1: The Professional Foundation
    Chapter created (chapter_id: 678)
    Lesson 1.1: Introduction... CREATED
    Lesson 1.2: The Call... CREATED
    Knowledge check: 8 questions pushed
  Unit 2: Pre-Production
    Chapter created (chapter_id: 679)
    ...
[6/8] Syncing course final... 200 questions in 20 batches (DONE)
[7/8] Writing sync-state.json... OK
[8/8] Done!

Summary:
  Lessons created: 30
  Lessons updated: 0
  Questions pushed: 248
  API calls: 312
  Time: 3 minutes 47 seconds

View your course: https://backstage-essentials.thinkific.com/admin/courses/12345
```

### sync-state.json (after sync)

```json
{
  "course_id": 12345,
  "last_sync": "2026-05-04T14:23:11Z",
  "subdomain": "backstage-essentials",
  "units": {
    "unit-01-professional-foundation": {
      "chapter_id": 678,
      "lessons": {
        "01-introduction.md": {
          "content_id": 1001,
          "hash": "a3f5..."
        }
      },
      "knowledge_check": {
        "quiz_id": 501,
        "questions": {
          "u1-kc-01": {"question_id": 9001, "hash": "b7c2..."}
        }
      }
    }
  },
  "final_assessment": {
    "quiz_id": 502,
    "questions": {
      "u1-q01": {"question_id": 9101, "hash": "..."}
    }
  }
}
```

This file lives in the course root, gitignored (it's machine-specific).

## Examples

### Example 1: First time sync

State: brand new course, just finished writing Unit 1 lessons and knowledge check. Want to push to a Thinkific test account.

Command:

```
bes sync
```

Result: course gets created on Thinkific, Unit 1 chapter created, all Unit 1 lessons created as drafts, knowledge check quiz created with all questions. Empty units 2-6 are not touched. The course_final has zero questions yet so nothing pushes for it.

### Example 2: Update one unit's lessons

State: course is on Thinkific. You revised three lessons in Unit 3. Want to push the changes.

Command:

```
bes sync
```

Result: lessons in unit 3 that changed are updated (content hash changed). All other lessons skipped. Total time: a few seconds.

### Example 3: Force update everything

State: you upgraded the markdown converter and want all lesson HTML regenerated and pushed even though the source markdown didn't change.

Command:

```
bes sync --force-update
```

Result: every lesson, every question gets re-pushed regardless of hash comparison. Slow but exhaustive.

### Example 4: Sync only specific units

State: course is fully built but you want to verify just unit 4 against the test Thinkific course.

Command:

```
bes sync --units 4
```

Or multiple units:

```
bes sync --units 1,2,4
```

Result: only the specified units are touched. Other units left as-is.

## Final Assessment Retest Behavior (Phase 14)

When `exam/course-final.yaml` carries the Phase 14 retest fields, the Thinkific sync configures what Thinkific natively supports:

- `max_attempts` from the YAML is set on the quiz so Thinkific enforces the attempt limit server-side.
- `randomize_questions` and `randomize_answers` are both turned on so each attempt sees the questions and choices in a different order.

### Statistical, not strict, overlap

**Thinkific does not enforce a hard cap on question overlap between attempts.** It picks `questions_per_attempt` randomly from the bank each time. With a 200-question bank, 50 questions per attempt, and 3 attempts, the expected pairwise overlap between any two attempts is roughly 25 percent of the per-attempt size (~12 questions). That exceeds the static-web target's 10 percent default and cannot be tightened from the public API.

For most K-12 and corporate-training contexts this is acceptable. If your course is high-stakes certification with a strict overlap requirement:

- Use the static-web target instead, which enforces the cap exactly via in-browser sampling.
- Or, build a custom Thinkific integration via their LTI tool that draws from pre-partitioned bank slices.

The sync skill does not implement either workaround. It does set the LMS-supported limits and document the gap here so course owners know what they get.

### Field name caveat

The Thinkific public API has used both `max_attempts` and `number_of_attempts` as the field name across documentation revisions. The sync skill currently posts `max_attempts`. If Thinkific returns 422 on the create_quiz call, swap the key in `thinkific_client.create_quiz` to whatever the current API rev expects, and update the api-notes reference doc.

## Quality Checks

Before declaring sync complete, verify:

- All API calls returned success codes (2xx) or were retried successfully
- sync-state.json was updated with the latest IDs
- No content was deleted from Thinkific (the skill never deletes, only creates and updates)
- The console summary numbers add up (lessons created + updated + unchanged equals total lessons in repo)
- The course URL is reachable

## Common Mistakes

- **Pushing to production accidentally.** Always test against a Thinkific test course first. Set `THINKIFIC_SUBDOMAIN` to a test environment for the first sync. Once verified, switch to production.

- **Missing markdown features.** markdown-it-py does not support every markdown extension by default. If a lesson uses tables, footnotes, or special blocks, enable the appropriate plugin. Test rich content on a single lesson before relying on it.

- **Image references that break.** If lesson markdown references local image paths like `./images/foo.jpg`, those paths will not work after sync because Thinkific does not host local files. Either upload images to Thinkific media first and reference the returned URL, or host on a CDN. Decide once for the course.

- **Hitting rate limits.** Thinkific allows ~120 requests per minute. A naive sync of 200 questions makes 200 requests. The script chunks in batches of 10 with 1-second sleeps to stay safe. Do not increase batch size without testing.

- **Trusting the dry run completely.** A dry run validates content but does not catch all API errors (auth, network, server-side validation). After dry run passes, do a real sync to a test course before production.

- **Deleting content from Thinkific to "reset."** The sync skill is idempotent; you do not need to reset. If you really need to delete a course, do it through Thinkific's admin UI, then delete sync-state.json from your repo, then sync again.

## Files in This Skill Folder

- `SKILL.md` (this file)
- `lib/sync.py` (the actual implementation Python module)
- `lib/thinkific_client.py` (REST API wrapper)
- `lib/content_parser.py` (markdown to HTML conversion, frontmatter handling)
- `lib/state.py` (sync-state.json read/write)
- `templates/sync-shim.py` (the thin wrapper written into course repos as scripts/sync.py)
- `reference/thinkific-api-notes.md` (notes on quirks of the Thinkific API)

The shim template is what repo-bootstrap copies into a new course's scripts/sync.py. It imports the toolkit's lib/sync.py and calls it. So the course repo's sync.py is just two lines once installed.

## Changelog

### 1.0 (2026-05-04)
- Initial version
- Supports create and update
- Idempotent via sync-state.json hash comparison
- Rate-limit aware (chunks questions in batches of 10)

### 1.1 (2026-05-05, Phase 14)
- create_quiz now sets max_attempts (when YAML configures it),
  randomize_questions, and randomize_answers.
- SKILL.md documents the statistical-overlap gap on Thinkific:
  random sampling means retests overlap roughly 25 percent on
  average for the default 200/50/3 setup, exceeding the static-web
  target's 10 percent cap. Acceptable for most contexts, not for
  strict certification.
- Both bes sync and standalone python3 scripts/sync.py paths supported
