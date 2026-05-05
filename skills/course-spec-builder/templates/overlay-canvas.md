# Canvas Overlay

This file fills in the platform-specific sections of the base build spec when the target platform is Canvas. The course-spec-builder skill reads this file and substitutes its sections into the base template at the matching `<!-- OVERLAY: ... -->` markers.

## OVERLAY: api-notes

Canvas LMS exposes a REST API for managing courses, modules, pages, quizzes, and quiz questions. The sync script uses this API to push your file content to your Canvas instance.

- **Base URL:** `https://<your-canvas-host>/api/v1/` (e.g., `https://canvas.instructure.com/api/v1/` for the hosted Instructure instance, or your institution's Canvas domain)
- **Authentication:** Bearer token in the `Authorization` header. The token is generated manually from your Canvas account: Account, Settings, New Access Token. Treat the token like a password; it grants the same permissions as the user who created it.

Endpoints used by the sync script:

- **Courses:** `POST /accounts/:account_id/courses` to create, `PUT /courses/:id` to update fields including `syllabus_body`
- **Modules (units):** `POST /courses/:id/modules` to create one module per unit
- **Module items:** `POST /courses/:id/modules/:mid/items` to attach pages and quizzes to their unit's module
- **Pages (lessons):** `POST /courses/:id/pages` to create, `PUT /courses/:id/pages/:url` to update. Body is HTML, derived from your lesson markdown.
- **Quizzes:** `POST /courses/:id/quizzes` to create the classic quiz container, `POST /courses/:id/quizzes/:qid/questions` for each question, and `POST /courses/:id/quizzes/:qid/groups` to create a question group that randomly picks N from M (used for the course final's bank model)

Rate limits: roughly 200 requests per minute per user token. The sync script uses exponential backoff and chunks final-assessment question pushes in batches of 10 with a 1-second sleep between batches.

Content quirks:

- Lesson page bodies are HTML, not markdown. The sync script converts your lesson markdown to HTML using markdown-it-py before posting.
- Page slugs are derived from the page title. The sync script pre-computes the same slug locally so a freshly created page can be attached to a module without an extra round trip.
- Classic quizzes are used (not New Quizzes). Classic is more stable and adequate for the multiple-choice patterns this toolkit produces.
- Multiple-choice answers use Canvas's `answer_text` and `answer_weight` (100 for correct, 0 for incorrect).
- The course final is a single quiz with a question group whose `pick_count` matches `questions_per_attempt` from your course-final.yaml. Canvas randomizes the sample at attempt time.

If a sync fails partway through, the script logs which object was being created when the failure happened. Rerun after fixing the issue. The script is idempotent: it skips already-created objects via sync-state.json hash comparison and picks up where it left off.

## OVERLAY: sync-command

```
python3 scripts/sync.py
```

Or, once the bes command is installed:

```
bes sync
```

`bes sync` reads `course-config.yaml`, sees that the platform is `canvas`, and runs the Canvas sync logic from the toolkit's `sync/canvas/` skill. Same end result, less typing.

For a safe first pass without touching Canvas:

```
bes sync --dry-run
```

This validates content, builds every API payload, and writes them to `sync-state.dry-run.json` for inspection. No requests are sent.

## OVERLAY: platform-risks

- **API token security.** The Canvas access token grants the same permissions as the user who created it. If the token leaks, anyone holding it can read or modify the courses that user can access. Keep it in `.env` (gitignored) and rotate when staff turns over.
- **Account ID required.** Canvas accounts are hierarchical. The sync needs `canvas_account_id` in `course-config.yaml` to know which account to create the course under. On the Instructure-hosted instance, the root account ID is `1`. On institutional instances, ask your Canvas admin which sub-account ID you have rights to use.
- **Quiz format choice.** Phase 11 uses classic quizzes. New Quizzes is the future direction, but classic is more stable and the API is more established. Migrate later if an institution requires New Quizzes.
- **Rate limits per token.** The default 200 requests per minute leaves headroom for a typical 6-unit course sync. If your institution has tighter quotas (some do), lower the batch size in scripts/sync.py.
- **HTML rendering quirks.** Canvas pages support a wide subset of HTML, but some institutions sandbox iframes (which affects MicroSim embeds) or strip script tags (which affects unrendered Mermaid). Test rich content on a sandbox course before relying on it.
- **Image and MicroSim hosting.** Canvas does not pull from your repo. Images and MicroSim HTML referenced by lessons need to be uploaded as Canvas Files (POST `/courses/:id/files`) or hosted externally. Phase 11 records the upload request but defers the second-step PUT; manual upload via the Canvas UI is the workaround until that is wired up.
- **Course publishing state.** The sync script creates pages as unpublished by default. Publish from the Canvas UI when you are ready. The sync never auto-publishes a course.
- **Data export and portability.** Canvas supports Common Cartridge export, but your authoritative source is the markdown and YAML in your repo. If you ever leave Canvas, point the sync script at a different platform and the content moves with you.

## OVERLAY: prerequisites

- Canvas account active. A free Canvas Free For Teachers account or your institution's Canvas instance both work.
- Canvas instance URL identified. The hostname before `/api/v1/`. For the hosted instance: `https://canvas.instructure.com`. For an institution: your school's Canvas domain.
- Canvas account ID identified. On hosted Canvas the root account ID is typically `1`. On an institution, ask a Canvas admin for the sub-account ID you can create courses under.
- Canvas API access token generated. Account, Settings, New Access Token. Save the value in 1Password the moment Canvas shows it; the token cannot be retrieved later.
- The .env file in your course repo populated with:
  ```
  CANVAS_API_URL=https://your-canvas-host
  CANVAS_API_TOKEN=your_token_here
  ```
- The `canvas_account_id` field added to course-config.yaml under the `course:` block.
- Verified `.env` is in `.gitignore` so the token never gets committed.
- Decided whether the course will be Published or Unpublished after content syncs. The sync script does not auto-publish; you control publishing from the Canvas UI.
