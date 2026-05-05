---
name: canvas-sync
version: 1.0
description: Push course content to Canvas LMS via the REST API
inputs:
  - course_root: folder_path, required, default current working directory
  - dry_run: boolean, default false
  - force_update: boolean, default false
  - units_to_sync: list of integers, optional (sync only specific units; default all)
outputs:
  - Updates a Canvas course (creates if missing, updates if exists)
  - Console log of operations performed
  - sync-state.json in course root (records what got synced when, for change detection)
  - sync-state.dry-run.json in course root when dry_run is true (records every API payload that would have been sent)
dependencies:
  - course-spec-builder (course needs a spec)
  - repo-bootstrap (course needs a populated repo)
phase: 11
status: ready
subject_neutral: true
audience_neutral: true
platform: canvas
---

# Canvas Sync

Pushes course content to Canvas LMS via its REST API. The skill is invoked two ways:

- **bes sync** from inside any course folder: bes reads `course-config.yaml`, sees `platform: canvas`, and calls this skill.
- **python3 scripts/sync.py** from inside the course folder: the shim sync.py written by repo-bootstrap imports the toolkit and runs this skill.

Both paths run the same code. bes is just easier to type.

## When to Use

After you have a populated course repo (lessons drafted, knowledge checks written, course final populated) and a Canvas account with an access token configured in `.env`. Run sync to push your local content to Canvas.

The first sync is the slowest (creates everything from scratch). Subsequent syncs are fast (only pushes what changed since last sync).

Do NOT run sync if:
- The .env file is missing or has placeholder values
- course-config.yaml is missing, unparseable, or missing `canvas_account_id`
- You have not validated the course content first (`bes validate`)

The skill is idempotent. Safe to run repeatedly. Each run makes Canvas match the local files. No duplicates. No data loss.

## Authentication: Manual Access Token

Canvas supports two auth patterns: a manual access token and a full OAuth2 flow. Phase 11 implements only the manual token pattern. OAuth2 is deferred until a specific institution requires it.

To generate a token:

1. Sign in to your Canvas instance (e.g., `https://canvas.instructure.com` or your institution's domain).
2. Click **Account** in the global nav, then **Settings**.
3. Scroll to **Approved Integrations** and click **+ New Access Token**.
4. Give the token a purpose ("backstage essentials toolkit") and an optional expiration date. Leave expiration blank only if your institution's policy allows it.
5. Click **Generate Token** and copy the token immediately. Canvas only shows the value once.
6. Paste the token into your course's `.env`:

   ```
   CANVAS_API_URL=https://canvas.instructure.com
   CANVAS_API_TOKEN=paste_your_token_here
   ```

   Replace `canvas.instructure.com` with your institution's Canvas domain if you are not on the hosted instance.

7. Verify `.env` is gitignored (it is, by default in repos this toolkit creates). Never commit a token.

Canvas tokens grant the same permissions as the user who created them. Treat them like a password. Rotate them when staff turns over and revoke unused tokens from the same Approved Integrations page.

## Steps

1. Verify environment:
   - `.env` exists in course root, has `CANVAS_API_URL` and `CANVAS_API_TOKEN` populated with non-placeholder values
   - `course-config.yaml` exists and parses; `platform` is `canvas`; `canvas_account_id` is set
   - All required content files exist (every unit folder has unit.yaml, lessons/, knowledge-check.yaml; exam/course-final.yaml exists)

   If any check fails, stop and tell the user what is wrong.

2. Load configuration:
   - Read course-config.yaml for course metadata (name, slug, completion threshold, canvas_account_id)
   - Read .env for credentials
   - Load sync-state.json from course root if it exists; if missing, this is a first-time sync

3. Test API authentication:
   - Make a single GET request to `/users/self`
   - If 401 or 403, stop and tell the user the token is wrong or revoked
   - If 429 (rate limited) or 5xx, retry with backoff up to 3 times

4. Find or create the course:
   - GET `/accounts/:account_id/courses`, look for one with matching `course_code` (we use the course slug as the code)
   - If found: store course_id, plan to UPDATE
   - If not found: POST `/accounts/:account_id/courses` to create, store the new course_id, plan to CREATE
   - PUT `/courses/:course_id` to set `syllabus_body` from course-description.md (rendered to HTML)
   - Update sync-state.json with course_id

5. Sync each unit (module on Canvas):
   For each unit folder in content/, in order:

   a. Read unit.yaml for unit metadata
   b. Find or create the module on Canvas (POST `/courses/:id/modules`)
   c. Sync each lesson in the unit's lessons/ folder:
      - Convert markdown to HTML using markdown-it-py
      - Create the page with POST `/courses/:id/pages` (or update existing with PUT `/courses/:id/pages/:url`)
      - Attach new pages to the module via POST `/courses/:id/modules/:mid/items` with `type: Page`
      - Compare local content hash to sync-state.json hash; skip if unchanged unless force_update is true
   d. Sync the unit knowledge check:
      - Create the quiz with POST `/courses/:id/quizzes` (`quiz_type: assignment`, `shuffle_answers: true`)
      - Attach the quiz to the module via a module item
      - For each question in knowledge-check.yaml:
        - Create with POST `/courses/:id/quizzes/:qid/questions` (`question_type: multiple_choice_question`)
        - Update if changed
   e. Update sync-state.json after each unit completes (so partial failures are recoverable)

6. Sync the course final assessment:
   - Read exam/course-final.yaml
   - Create the final quiz on Canvas
   - Create a question group inside the quiz that picks N of M (the bank model: e.g. 100 picked from 200)
   - Sync questions in batches of 10 with a 1-second sleep between batches (rate-limit protection)
   - Update sync-state.json

7. Final report:
   - Number of lessons created, updated, unchanged
   - Number of questions pushed
   - Total API calls made
   - Total time elapsed
   - Any errors or warnings

8. Print the URL of the course on Canvas so the user can open it in a browser to verify.

## Dry Run Mode

`bes sync --dry-run` (or `python3 scripts/sync.py --dry-run`) runs the entire orchestration without sending any HTTP requests. The CanvasClient records every payload that would have been sent and returns deterministic stub IDs so the rest of the flow can run end to end.

After a dry run completes, two files exist:

- `sync-state.json`: structurally what state would look like if the run had happened
- `sync-state.dry-run.json`: a flat list of every API call that would have been made, in order, with method, path, and JSON body

Inspect `sync-state.dry-run.json` to confirm payloads look correct before doing a real sync. Delete both files when done with the dry run.

Dry run is the right way to test changes against the live event reference course without needing a Canvas sandbox account.

## Output Format

### Console output during sync

```
[1/8] Checking environment in /Users/x/Code/my-course... OK
[2/8] Loading configuration... OK (course: My Course, account: 1)
[3/8] Testing API auth... OK
[4/8] Finding or creating course on Canvas... CREATED (course_id: 1001)
  Syllabus updated from course-description.md
[5/8] Syncing units (modules + pages + quizzes)...
  Unit 1: The Professional Foundation
    Module created (module_id: 1002)
    Lesson Introduction: CREATED
    Lesson The Call: CREATED
    Quiz Unit 1 Knowledge Check: questions synced
  Unit 2: Pre-Production
    ...
[6/8] Syncing course final... 200 questions in 20 batches (DONE)
[7/8] Writing sync-state.json... OK
[8/8] Done!

Summary:
  Lessons created: 30
  Lessons updated: 0
  Questions pushed: 248
  API calls: 322
  Time: 2 minutes 14 seconds

View your course: https://canvas.instructure.com/courses/1001
```

### sync-state.json (after sync)

```json
{
  "version": 1,
  "platform": "canvas",
  "course_id": 1001,
  "api_url": "https://canvas.instructure.com/api/v1",
  "account_id": "1",
  "last_sync": "2026-05-04T14:23:11Z",
  "units": {
    "unit-01-professional-foundation": {
      "module_id": 1002,
      "lessons": {
        "01-introduction.md": {
          "page_url": "introduction",
          "page_id": 2001,
          "hash": "a3f5..."
        }
      },
      "knowledge_check": {
        "quiz_id": 3001,
        "questions": {
          "u1-kc-01": {"question_id": 5001, "hash": "b7c2..."}
        }
      }
    }
  },
  "final_assessment": {
    "quiz_id": 3010,
    "group_id": 4001,
    "questions": {}
  }
}
```

This file lives in the course root, gitignored (machine-specific).

## Examples

### Example 1: First time sync

State: brand new course, finished writing Unit 1 lessons and knowledge check. Want to push to a Canvas test instance.

Command:

```
bes sync
```

Result: course gets created in Canvas, Unit 1 module created, all Unit 1 lessons created as unpublished pages and attached to the module, knowledge check quiz created with all questions. Empty units 2-6 are not touched. The course final has zero questions yet so nothing pushes for it.

### Example 2: Update one unit's lessons

State: course is on Canvas. You revised three lessons in Unit 3.

Command:

```
bes sync
```

Result: lessons in unit 3 that changed are updated (content hash changed). All other lessons skipped. Total time: a few seconds.

### Example 3: Force update everything

```
bes sync --force-update
```

Result: every lesson, every question gets re-pushed regardless of hash comparison. Slow but exhaustive.

### Example 4: Sync only specific units

```
bes sync --units 1,2,4
```

Result: only the specified units are touched.

### Example 5: Validate payloads without sending

```
bes sync --dry-run
```

Result: full orchestration runs against your repo with stubbed responses. `sync-state.dry-run.json` lists every API call that would have been made. No Canvas account required.

## Final Assessment Retest Behavior (Phase 14)

When `exam/course-final.yaml` carries the Phase 14 retest fields, the Canvas sync configures what classic Canvas Quizzes natively support:

- `allowed_attempts` from the YAML's `max_attempts` is set on the quiz so Canvas enforces the cap server-side. Canvas convention: pass any positive integer to cap, or `-1` for unlimited.
- `shuffle_answers` stays on; the `pick_count` on the question group already randomizes which questions a student sees per attempt.

### Statistical, not strict, overlap

**Canvas does not enforce a hard cap on question overlap between attempts.** The question group draws `questions_per_attempt` randomly from the bank each attempt. With a 200-question bank, 50 questions per attempt, and 3 attempts, the expected pairwise overlap between any two attempts is roughly 25 percent of the per-attempt size (~12 questions). That exceeds the static-web target's 10 percent default and cannot be tightened from the public Canvas Quizzes API.

For most course contexts this is fine. If your course is high-stakes certification with a strict overlap requirement:

- Use the static-web target instead, which enforces the cap exactly via in-browser sampling.
- Or, manually create N separate quizzes (one per attempt) each drawing from a pre-partitioned slice of the bank. Heavy lift, not implemented automatically by this sync.

### New Quizzes vs Classic

This sync uses classic quizzes. New Quizzes (the LTI tool) supports more granular randomization but is a separate API and a separate UI. If your institution mandates New Quizzes, that path is a future Phase.

## Quality Checks

Before declaring sync complete, verify:

- All API calls returned success codes (2xx) or were retried successfully
- sync-state.json was updated with the latest IDs
- No content was deleted from Canvas (the skill never deletes, only creates and updates)
- The console summary numbers add up
- The course URL is reachable

## Common Mistakes

- **Pushing to production accidentally.** Always test against a Canvas sandbox or free trial first. Many institutions provide a sandbox account separate from the production instance. Use it.

- **Wrong account_id.** Canvas accounts are hierarchical. `canvas_account_id: 1` works on hosted Canvas (the "Site Admin" account). On an institution instance, ask your Canvas admin for the right sub-account ID. The wrong account_id leads to 401 or 404 on course creation.

- **Missing `canvas_account_id` in course-config.yaml.** The sync skill will refuse to run without it. Add it to course-config.yaml under the `course:` block.

- **Content references that break.** If lesson markdown references local images or MicroSim files, those paths will not resolve once the page is on Canvas. Either upload to Canvas Files first and reference the returned URL, or host externally. Phase 11 does not auto-upload media; that is a future enhancement.

- **Hitting rate limits.** Canvas allows about 200 requests per minute per user. The script chunks question pushes in batches of 10 with 1-second sleeps. Do not increase batch size without testing.

- **Trusting dry run completely.** Dry run validates content and payload shape but does not catch all server-side validation errors (account permissions, quota, plugin restrictions). After dry run passes, do a real sync to a sandbox before production.

- **Iframe sandboxing.** Some institutional Canvas configurations sandbox iframes. MicroSim embeds may need to fall back to image-plus-link if iframes do not render. Phase 11 emits the iframe markup; test on the target Canvas before relying on it.

## Files in This Skill Folder

- `SKILL.md` (this file)
- `lib/sync.py` (the actual implementation Python module)
- `lib/canvas_client.py` (REST API wrapper, with dry-run support)
- `lib/content_parser.py` (markdown to HTML conversion, frontmatter handling, page slugging)
- `lib/state.py` (sync-state.json read/write)
- `templates/sync-shim.py` (the thin wrapper written into course repos as scripts/sync.py)
- `reference/api-reference.md` (cheat sheet for Canvas endpoints used)

The shim template is what repo-bootstrap copies into a new course's scripts/sync.py. It imports the toolkit's `sync.canvas.lib.sync()` and calls it.

## Changelog

### 1.0 (2026-05-05)
- Initial version
- Course/module/page/quiz/question support via Canvas REST API v1
- Manual access token authentication
- Idempotent via sync-state.json hash comparison
- Dry-run mode that records every would-be API call to sync-state.dry-run.json
- Question groups for course final (pick N of M)
- Rate-limit aware (chunks final questions in batches of 10)

### 1.1 (2026-05-05, Phase 14)
- create_quiz now sets allowed_attempts (when YAML configures it)
  on both unit knowledge checks and the course final.
- SKILL.md documents the statistical-overlap gap on Canvas: random
  pick_count means retests overlap roughly 25 percent on average for
  the default 200/50/3 setup, exceeding the static-web target's
  10 percent cap. Strict overlap requires the static-web target or
  manual per-attempt quizzes drawing from pre-partitioned bank slices.
