---
name: talentlms-sync
version: 1.0
description: Push course content to TalentLMS via the REST API
inputs:
  - course_root: folder_path, required, default current working directory
  - dry_run: boolean, default false
  - force_update: boolean, default false
  - units_to_sync: list of integers, optional (sync only specific units; default all)
outputs:
  - Updates a TalentLMS course (creates if missing, updates if exists)
  - Console log of operations performed
  - sync-state.json in course root (records what got synced when, for change detection)
  - sync-state.dry-run.json when dry_run is true (records every API payload that would have been sent)
dependencies:
  - course-spec-builder (course needs a spec)
  - repo-bootstrap (course needs a populated repo)
phase: 16
status: ready
subject_neutral: true
audience_neutral: true
platform: talentlms
---

# TalentLMS Sync

Pushes course content to TalentLMS via its REST API. The skill is invoked two ways:

- **bes sync** from inside any course folder: bes reads `course-config.yaml`, sees `platform: talentlms`, and calls this skill.
- **python3 scripts/sync.py** from inside the course folder: the shim sync.py written by repo-bootstrap imports the toolkit and runs this skill.

Both paths run the same code. bes is just easier to type.

## Why TalentLMS

Among the major hosted LMS platforms, TalentLMS is the only one with a permanent free tier that includes full API access. That makes it the realistic free path for end-to-end live LMS validation of the toolkit. Canvas needs admin rights; Thinkific gates the API behind a paid plan.

Free tier limits: 5 users and 10 courses. Plenty for testing and small-scale offerings; not a scaling target for paid course delivery.

## When to Use

After you have a populated course repo (lessons drafted, knowledge checks written, course final populated), a TalentLMS account, and an API key configured in `.env`. Run sync to push your local content to TalentLMS.

The first sync is the slowest (creates everything from scratch). Subsequent syncs are fast (only push what changed since last sync).

Do NOT run sync if:
- The .env file is missing or has placeholder values
- course-config.yaml is missing, unparseable, or has `platform` set to something other than `talentlms`
- You have not validated the course content first (`bes validate`)

The skill is idempotent. Safe to run repeatedly. Each run makes TalentLMS match the local files. No duplicates. No data loss.

## Authentication: Sign Up and API Key

TalentLMS uses HTTP Basic Auth where the username is your API key and the password is any string. The toolkit handles the auth headers; you only need to put the URL and key into `.env`.

### Signup flow

1. Sign up at [https://www.talentlms.com](https://www.talentlms.com). Pick the free plan.
2. Confirm your email and choose your subdomain when prompted. Your account URL is `https://YOUR-DOMAIN.talentlms.com`. Your API base URL is `https://YOUR-DOMAIN.talentlms.com/api/v1`.
3. Sign in and open **Account & Settings** → **API**.
4. Copy the API key TalentLMS shows you. The free tier gives you a single key. Treat it like a password.
5. Paste the values into the course's `.env`:

   ```
   TALENTLMS_API_URL=https://YOUR-DOMAIN.talentlms.com
   TALENTLMS_API_KEY=paste_your_api_key_here
   ```

   The sync auto-appends `/api/v1` to the URL if you leave it off.

6. Confirm `.env` is gitignored (it is in any course bootstrapped by this toolkit). Never commit a key.

If you ever rotate the key (Account & Settings → API → Generate new), update `.env` and re-run sync. Sync state on disk stays valid; only the credential changed.

## Steps

1. Verify environment:
   - `.env` exists in course root, has `TALENTLMS_API_URL` and `TALENTLMS_API_KEY` populated with non-placeholder values
   - `course-config.yaml` exists and parses; `platform` is `talentlms`
   - All required content files exist (every unit folder has unit.yaml, lessons/, knowledge-check.yaml; exam/course-final.yaml exists)

   If any check fails, stop and tell the user what is wrong.

2. Load configuration:
   - Read course-config.yaml for course metadata (name, slug, completion_threshold)
   - Read .env for credentials
   - Load sync-state.json from course root if it exists; if missing, this is a first-time sync

3. Test API authentication:
   - Cheap GET against `/users/id:1` (a real account always has a user with id 1, the admin). 401/403 means the key is wrong; any other response means auth worked.

4. Find or create the course:
   - If sync-state.json already has a course_id, hit `GET /coursestatus?course_id=NN` to confirm it still exists and we have access.
   - Otherwise `POST /coursecreate` with the course name and the rendered course-description.md as the description.

5. Sync each unit:
   For each unit folder in content/, in order:

   a. `POST /createunit` with `type=text`, name "Unit N: Title" — this is the section-header unit (TalentLMS has no native section concept).
   b. For each lesson markdown file:
      - Convert markdown to HTML with markdown-it-py.
      - `POST /createunit` with `type=web`, name = lesson title.
      - `POST /createunitfile` with `unit_id` and the HTML body.
      - Compare local content hash to sync-state.json hash; skip if unchanged unless force_update is true.
   c. Sync the unit knowledge-check:
      - `POST /createcoursetest` with course_id, name, pass_score, shuffle flags.
      - For each question: `POST /createtestquestion` with the multiple-choice payload (answer1..N + correct_answer index).
   d. Update sync-state.json after each unit completes (so partial failures are recoverable).

6. Sync the course final assessment:
   - `POST /createcoursetest` for the final test, with shuffle flags and `max_attempts` set from the YAML's Phase 14 fields when present.
   - Push questions in batches of 10 with 1-second sleeps between batches (rate-limit protection).
   - Update sync-state.json.

7. Final report:
   - Number of lessons created, updated, unchanged
   - Number of questions pushed
   - Total API calls made
   - Total time elapsed
   - Any errors or warnings

8. Print the URL of the course on TalentLMS so the user can open it in a browser to verify.

## Dry Run Mode

`bes sync --dry-run` (or `python3 scripts/sync.py --dry-run`) runs the entire orchestration without sending any HTTP requests. The TalentLMSClient records every payload that would have been sent and returns deterministic stub IDs so the rest of the flow can run end to end.

After a dry run completes, two files exist:

- `sync-state.json`: structurally what state would look like if the run had happened
- `sync-state.dry-run.json`: a flat list of every API call that would have been made, in order, with method, path, and body

Inspect `sync-state.dry-run.json` to confirm payloads look correct before doing a real sync. Delete both files when done with the dry run.

Dry run is the right way to test toolkit changes against the live event reference course without needing a TalentLMS account.

## Output Format

### Console output during sync

```
[1/8] Checking environment in /Users/x/Code/my-course... OK
[2/8] Loading configuration... OK (course: My Course)
[3/8] Testing API auth... OK
[4/8] Finding or creating course on TalentLMS... Created (course_id: 1001)
[5/8] Syncing units (header + lessons + knowledge check)...
  Unit 1: The Professional Foundation
    Header unit created (id: 1002)
    Lesson Introduction: CREATED
    Lesson The Call: CREATED
    Test Unit 1 Knowledge Check: questions synced
  Unit 2: Pre-Production
    ...
[6/8] Syncing course final... 200 questions in 20 batches (DONE)
[7/8] Writing sync-state.json... OK
[8/8] Done!

Summary:
  Lessons created: 30
  Lessons updated: 0
  Lessons unchanged: 0
  Questions pushed: 248
  API calls: 320
  Time: 28.4 seconds

View your course: https://your-domain.talentlms.com/admin/courses/id:1001
```

### sync-state.json (after sync)

```json
{
  "version": 1,
  "platform": "talentlms",
  "course_id": 1001,
  "api_url": "https://your-domain.talentlms.com/api/v1",
  "last_sync": "2026-05-05T22:14:08.123456+00:00",
  "units": {
    "unit-01-the-professional-foundation": {
      "header_unit_id": 1002,
      "lessons": {
        "01-introduction.md": {"unit_id": 1003, "hash": "abc123..."}
      },
      "knowledge_check": {
        "test_id": 1010,
        "questions": {
          "u1-kc-01": {"question_id": 2001, "hash": "xyz789..."}
        }
      }
    }
  },
  "final_assessment": {
    "test_id": 1100,
    "questions": {
      "u1-q01": {"question_id": 3001, "hash": "..."}
    }
  }
}
```

## Examples

### Example 1: First time sync

Inputs: a populated course repo, .env with valid TALENTLMS_API_URL and TALENTLMS_API_KEY, sync-state.json missing.

Result: course created on TalentLMS, all units, lessons, knowledge checks, and the final pushed. sync-state.json written with object IDs.

### Example 2: Update one unit's lessons

You revised three lessons in Unit 3. Run `bes sync` again. The skill loads sync-state.json, sees that only those three lessons' content hashes changed, sends UPDATEs for those three, and reports "26 unchanged, 3 updated."

### Example 3: Force update everything

`bes sync --force` re-pushes every lesson and quiz question regardless of hash. Useful after a TalentLMS-side schema change or if state drifts out of sync.

### Example 4: Sync only specific units

`bes sync --units 1,2,4` syncs Units 1, 2, and 4 only. Other units left as-is.

## Limitations

**No native sections.** TalentLMS does not have a module/section concept. The sync emits a text-type "Unit N: Title" header unit per course-unit so the outline has visual breaks. If you would prefer a different layout, the workaround is post-sync manual reorganization in the TalentLMS admin UI.

**Single-correct multiple choice only.** The toolkit's question shape supports multiple correct answers; TalentLMS classic multiple-choice only marks one as correct. The sync uses the first correct choice and ignores the rest. If you need real multi-correct questions, switch the question type at the TalentLMS UI level after sync.

**No unit-body update endpoint.** TalentLMS's public API does not document a clean "update existing unit body" call. The sync re-uploads the file payload via `/createunitfile` against the existing unit_id, which works but may double-count storage on the account. Use `--force` sparingly.

**Free tier ceiling.** 5 users, 10 courses, permanent. Test cleanly within those limits; do not plan paid course delivery against the free tier.

## Quality Checks

Before declaring sync complete, verify:

- All API calls returned 2xx (or were retried successfully)
- sync-state.json was updated with the latest IDs
- No content was deleted from TalentLMS (the skill never deletes, only creates and updates)
- The console summary numbers add up
- The course URL is reachable

## Common Mistakes

- **Pushing to production accidentally.** Test against the free tier first. Once the free-tier sync looks right, decide whether to upgrade or migrate.

- **TALENTLMS_API_URL with a trailing slash or missing scheme.** The sync normalizes (`https://your-domain.talentlms.com/api/v1`), but typos like `your-domain.talentlms.com` (no scheme) or extra path segments cause auth-test failures. Paste exactly what TalentLMS shows in the admin URL bar.

- **Free tier course-count limit hit.** TalentLMS rejects course creation with a clear error once you have 10 courses on the account. Delete a stale test course or upgrade.

- **Markdown features that markdown-it-py does not enable.** Tables, footnotes, and special blocks need extensions enabled. Test rich content on a single lesson before relying on it.

- **MicroSim iframes stripped by content sanitization.** Some account-level security configurations strip iframes. Test once on your account; if iframes do not render, fall back to image-plus-link.

## Files in This Skill Folder

- `SKILL.md` (this file)
- `lib/sync.py` (the actual implementation Python module)
- `lib/talentlms_client.py` (REST API wrapper, with dry-run support)
- `lib/content_parser.py` (markdown to HTML conversion, frontmatter handling)
- `lib/state.py` (sync-state.json read/write)
- `templates/sync-shim.py` (the thin wrapper written into course repos as scripts/sync.py)
- `reference/api-reference.md` (cheat sheet for TalentLMS endpoints used)

## Changelog

### 1.0 (2026-05-05, Phase 16)
- Initial version
- Course / unit-header / lesson-unit / test / question support via TalentLMS REST API
- HTTP Basic Auth, idempotent via sync-state.json hash comparison
- Dry-run mode that records every would-be API call to sync-state.dry-run.json
- Phase 14 retest fields (`max_attempts`, `randomize`) passed through to TalentLMS test creation
- Rate-limit aware (chunks final-assessment questions in batches of 10)
