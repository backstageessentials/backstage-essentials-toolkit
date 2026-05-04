# Thinkific Overlay

This file fills in the platform-specific sections of the base build spec when the target platform is Thinkific. The course-spec-builder skill reads this file and substitutes its sections into the base template at the matching `<!-- OVERLAY: ... -->` markers.

## OVERLAY: api-notes

Thinkific exposes a REST API for managing courses, chapters, lessons, and quizzes. The sync script uses this API to push your file content to your Thinkific site.

- **Base URL:** `https://api.thinkific.com/api/public/v1/`
- **Authentication headers:**
  - `X-Auth-API-Key`: your API key from Thinkific Settings, Code & Analytics, API Keys
  - `X-Auth-Subdomain`: your Thinkific subdomain (the prefix before .thinkific.com in your site URL)

Endpoints used by the sync script:

- **Courses:** `POST /courses` to create, `PUT /courses/{id}` to update
- **Chapters:** `POST /chapters` (a chapter is a unit in our model)
- **Lessons:** `POST /contents` with `content_type: Lesson` and the lesson body as HTML
- **Quizzes:** `POST /quizzes` to create the quiz container, then `POST /quiz_questions` once per question

Rate limits: roughly 120 requests per minute. The sync script uses exponential backoff to stay under the limit. Pushing a 200-question final assessment hits the rate limiter, so the script chunks the requests with a small sleep between batches.

Content quirks:

- Lesson body content is HTML, not markdown. The sync script converts your lesson markdown to HTML using markdown-it-py before posting.
- Image references in lesson markdown must point to URLs Thinkific can fetch. The simplest path is uploading images to Thinkific's media library first via `POST /file_uploads`, then referencing the returned URL in the lesson body.
- Quiz questions support multiple choice, single answer, and free response. The sync script uses scenario-based multiple choice with one correct answer by default.

If a sync fails partway through, the script logs which object was being created when the failure happened. Rerun the script after fixing the issue. The script is idempotent: it will skip already-created objects and pick up where it left off.

## OVERLAY: sync-command

```
python3 scripts/sync.py
```

Or, once the bes command is installed:

```
bes sync
```

`bes sync` reads `course-config.yaml`, sees that the platform is `thinkific`, and runs the Thinkific sync logic from the toolkit's `sync/thinkific/` skill. Same end result, less typing.

## OVERLAY: platform-risks

- **API quota:** Thinkific's rate limits are reasonable but not unlimited. A full course sync (6 units, 30 lessons, 200 final assessment questions) takes a few minutes because of the rate limiter. Do not run sync in tight loops.
- **Quiz endpoint speed:** Pushing many questions to one quiz can be slow. The sync script chunks the requests in batches of 10 with a one-second sleep between batches. Adjust the batch size in scripts/sync.py if needed.
- **HTML rendering:** Markdown to HTML conversion via markdown-it-py is reliable for typical lesson content (headings, lists, code blocks, links, images). Test rich content (tables, embedded video, complex formatting) on your test Thinkific course before assuming it will render correctly in a real course.
- **Plan limits:** Thinkific's free trial and Basic plan have limits on student count and storage. Verify your plan covers your expected enrollment before launching.
- **Data export:** Thinkific does provide a data export feature, but it is platform-specific. Your real backup is the markdown and YAML files in your repo. If you ever leave Thinkific, point the sync script at a different platform and the content moves with you.

## OVERLAY: prerequisites

- Thinkific account active. Free trial is fine for initial testing.
- Thinkific subdomain decided. The first part of your URL (e.g., `backstage-essentials.thinkific.com`).
- Thinkific API key generated. Go to Settings, Code & Analytics, API Keys, click Add API Key. Copy the key. Save it in 1Password.
- The .env file in your course repo populated with:
  ```
  THINKIFIC_API_KEY=your_key_here
  THINKIFIC_SUBDOMAIN=your_subdomain_here
  ```
- Verified the .env file is in .gitignore so it never gets committed.
- Decided the course price (or free) and how students will enroll. The sync script does not handle pricing or enrollment automation. Those are configured in Thinkific's web interface after the course content is up.
