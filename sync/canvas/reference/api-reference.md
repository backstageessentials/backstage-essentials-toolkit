# Canvas LMS API Reference

Operational notes for the Canvas REST API endpoints used by the Phase 11 sync skill. Updated as we hit edges.

## Endpoints

Base URL: `https://<your-canvas-host>/api/v1/`

For the standard Instructure-hosted instance: `https://canvas.instructure.com/api/v1/`. For institutional instances, replace the host with the institution's Canvas domain (e.g., `https://example.instructure.com/api/v1/` or a custom subdomain).

### Auth

Single header on every request:

```
Authorization: Bearer <CANVAS_API_TOKEN>
```

The token is generated manually by the user from Account, Settings, New Access Token. See SKILL.md for the full step-by-step.

### Endpoints we use

- `GET /users/self`: cheap auth probe; returns the token holder's user record
- `GET /accounts/:account_id/courses`: list courses in an account, paginated
- `POST /accounts/:account_id/courses`: create a course (body: `{"course": {"name", "course_code"}}`)
- `PUT /courses/:id`: update course fields, including `syllabus_body`
- `POST /courses/:id/modules`: create a module (a unit in our model)
- `POST /courses/:id/modules/:mid/items`: attach a page or quiz to a module
- `POST /courses/:id/pages`: create a wiki page (lesson)
- `PUT /courses/:id/pages/:url`: update a page by its slug
- `POST /courses/:id/quizzes`: create a classic quiz
- `POST /courses/:id/quizzes/:qid/questions`: create a quiz question
- `PUT /courses/:id/quizzes/:qid/questions/:qqid`: update a question
- `POST /courses/:id/quizzes/:qid/groups`: create a question group inside a quiz (used for the course final's pick-N-of-M behavior)
- `POST /courses/:id/files`: request an upload URL for a file (Phase 11 records this for future MicroSim/image work but does not perform step 2 of the upload)

## Rate Limits

Canvas allows roughly 200 requests per minute per user token. The sync skill stays under by:

- Using batches of 10 question pushes with 1-second sleeps for the course final
- Exponential backoff when 429 is returned
- Honoring the `Retry-After` header if present

If your institution has tighter limits, lower the batch size in `lib/sync.py`.

## Content Quirks

**Pages take HTML, not markdown.** The sync skill converts lesson markdown to HTML via markdown-it-py before posting. Canvas accepts a wide subset of HTML in `wiki_page.body`.

**Page slugs are generated from the title.** Canvas computes `page_url` from the page title (e.g., "Lesson 1: Introduction" -> "lesson-1-introduction"). The sync skill pre-computes the same slug locally so a freshly created page can be attached to a module without an extra round trip. If two lessons share the same title, Canvas appends `-1`, `-2`; rename one of the lessons to keep the local slug aligned.

**Classic quizzes vs New Quizzes.** Phase 11 uses classic quizzes (`/courses/:id/quizzes`). New Quizzes is a separate API and a separate UI under the LTI tool model. Classic is more stable and adequate for the assessment patterns this toolkit produces. If an institution requires New Quizzes, that is a future Phase.

**Multiple-choice answer format.** Each answer is `{"answer_text": str, "answer_weight": 100|0}`. Canvas treats any answer with positive weight as correct. The sync skill emits 100 for correct, 0 for incorrect.

**Question groups for sampling.** A quiz can contain "groups" that randomly pick N questions out of M at attempt time. The course final uses one group with `pick_count = questions_per_attempt` (default 100) and the full bank as members.

**Module items: Page vs Quiz.** When attaching a page to a module, the request body must include `page_url` (the page slug). When attaching a quiz, use `content_id` (the quiz's numeric id). Mixing these up returns 400.

**Course `course_code` is the slug we anchor on.** Canvas exposes `course_code` as a free-form short code for the course. The sync skill writes the course slug here so subsequent syncs can find an existing course by code without scanning every course in the account.

## Error Cases

**401 Unauthorized.** Token is wrong, expired, or revoked. Generate a new one in Settings, New Access Token.

**403 Forbidden.** Token is valid but lacks permissions for the action. Common cause: trying to create a course in an account the token holder does not have rights to. Ask your Canvas admin which `account_id` you can use.

**404 Not Found.** Object ID is wrong, deleted, or in a different account. Sync state may be stale. Delete sync-state.json and re-sync.

**422 Unprocessable Entity.** Validation error. Response body usually contains details. Common causes: course_code already in use in another account section, page title collisions, missing required field.

**429 Too Many Requests.** Rate limited. The client retries automatically with backoff.

## Fields We Set vs Fields We Leave Default

The sync skill sets:
- course: `name`, `course_code`, `syllabus_body`
- module: `name`, `position`
- module_item: `title`, `type`, `page_url` or `content_id`, `position`
- page: `title`, `body`, `published` (default false)
- quiz: `title`, `quiz_type`, `shuffle_answers`, `description`, `show_correct_answers`, `scoring_policy`, `allowed_attempts` (when YAML sets max_attempts)
- question: `question_name`, `question_text`, `question_type`, `points_possible`, `answers`
- question_group: `name`, `pick_count`, `question_points`

The sync skill does NOT set:
- Course term, dates, restrictions, enrollment settings
- Course availability or publishing state (set in Canvas UI after content syncs)
- Grading schemes, late policies, gradebook settings
- Outcomes, rubrics, learning mastery
- LTI tools, external apps
- Custom course navigation or hidden tabs
- Files (image/MicroSim upload) beyond the placeholder request

These are deliberately left out because they are institution-specific and fast-moving. The sync handles content; the Canvas UI handles policy.

## Tested API Version

These notes are accurate as of May 2026 against the Canvas REST API documented at https://canvas.instructure.com/doc/api/. Canvas occasionally retires endpoints; if a sync starts failing, check the API changelog at https://github.com/instructure/canvas-lms/releases for breaking changes.

## OAuth2 Note

Canvas also supports OAuth2 for tokens, which avoids manual generation but requires registering the toolkit as a developer key in the institution's Canvas admin. Phase 11 deliberately uses the manual token path because it works on every Canvas instance without admin involvement. If a specific institution requires OAuth2, that is a future Phase.
