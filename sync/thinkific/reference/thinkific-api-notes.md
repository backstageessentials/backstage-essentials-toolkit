# Thinkific API Notes

Operational notes for working with the Thinkific public API. Updated as we hit edges.

## Endpoints

Base URL: `https://api.thinkific.com/api/public/v1/`

Auth: two custom headers
- `X-Auth-API-Key`: your API key
- `X-Auth-Subdomain`: your Thinkific subdomain (the part before .thinkific.com in your URL)

The endpoints we use:

- `GET /courses`: list courses
- `POST /courses`: create
- `PUT /courses/{id}`: update
- `GET /chapters?course_id={id}`: list chapters in a course
- `POST /chapters`: create chapter (a chapter is a unit in our model)
- `PUT /chapters/{id}`: update
- `POST /contents`: create lesson (set content_type to Lesson, body to HTML)
- `PUT /contents/{id}`: update lesson
- `POST /quizzes`: create quiz
- `POST /quiz_questions`: create question
- `PUT /quiz_questions/{id}`: update question

## Rate Limits

Thinkific allows roughly 120 requests per minute per API key. The sync skill stays well under by:

- Using batches of 10 questions with 1-second sleeps for the course final
- Using exponential backoff when 429 is returned
- Honoring the `Retry-After` header if present

## Content Quirks

**Lesson body must be HTML, not markdown.** The sync skill converts markdown via markdown-it-py. The API accepts HTML in the `lesson.body` field of a POST /contents request.

**Images need to be hosted.** Thinkific does not pull images from your repo. Either upload them to Thinkific's media library first via POST /file_uploads and reference the returned URL, or host on a CDN you control.

**Quiz questions support multiple choice (single answer or multiple correct), true/false, and free response.** The sync skill uses `multiple_choice` with one or more `correct: true` answers.

**Pass percentages are integers, not decimals.** Convert 0.75 to 75 when posting.

## Error Cases

**401 Unauthorized.** API key is wrong or revoked. Generate a new one in Settings, Code & Analytics, API Keys.

**403 Forbidden.** API key is valid but lacks permissions for the action. Check API key scopes.

**404 Not Found.** Object ID is wrong, or it was deleted. Sync state may be stale. Delete sync-state.json and re-sync.

**422 Unprocessable Entity.** Validation error. Response body will contain details. Common causes: missing required field, slug already in use by another course, body too long.

**429 Too Many Requests.** Rate limited. The client retries automatically with backoff.

## Fields We Set vs Fields We Leave Default

The sync skill sets:
- course: name, slug, description
- chapter: name, position, course_id
- lesson: name, position, body (HTML), chapter_id
- quiz: name, position, chapter_id, pass_percentage, max_attempts (when YAML sets it), randomize_questions, randomize_answers
- quiz_question: prompt, type, answers (with text and correct), explanation

**Field name caveat for `max_attempts`.** The public API has historically used both `max_attempts` and `number_of_attempts` depending on the documentation revision. The sync skill currently posts `max_attempts`. If Thinkific rejects the request with a 422, swap the key in `thinkific_client.create_quiz` to whatever the current API rev expects.

The sync skill does NOT set:
- Course pricing (set in Thinkific admin UI)
- Course publishing state (managed in admin UI)
- Course images, banners, promotional video
- Drip schedules, prerequisites, certificates
- User access settings

These are deliberately left out because they are fast-moving and subjective. The sync handles content. The Thinkific admin UI handles everything else.

## Tested API Version

These notes are accurate as of May 2026 against the public API documented at https://developers.thinkific.com/api/. If the API changes substantially, the sync skill needs updating.
