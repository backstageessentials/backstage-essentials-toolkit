# TalentLMS API Notes

Operational notes for working with the TalentLMS REST API. Updated as the sync hits edges.

## Endpoints

Base URL: `https://YOUR-DOMAIN.talentlms.com/api/v1/`

Each TalentLMS account has its own subdomain. The API key is account-scoped; one key per account on the free tier.

Auth: HTTP Basic with the API key as username and any string (or empty) as password. Examples online sometimes use the API key as a query parameter; the toolkit prefers Basic Auth because it matches the Canvas and Thinkific patterns.

Endpoints the sync uses:

- `GET /coursestatus?course_id=NN` — read existing course state for sanity checks
- `POST /coursecreate` — create a course
- `POST /createcoursecategory` — create a category for organizing courses
- `POST /addtocoursecategory` — attach a course to a category
- `POST /createunit` — create a unit (lesson, section header, exam, etc.)
- `POST /createunitfile` — attach the HTML body to a unit
- `POST /createcoursetest` — create a test (quiz) inside a course
- `POST /createtestquestion` — add one question to a test

## Rate Limits

TalentLMS allows roughly 100 to 200 requests per minute on the free tier (varies by account). The sync uses exponential backoff when a 429 lands, and chunks course-final question pushes in batches of 10 with 1-second sleeps between batches.

## Content Quirks

**Form-encoded bodies, not JSON.** TalentLMS POST endpoints expect `application/x-www-form-urlencoded` payloads. The sync passes `data=...` (which `requests` form-encodes) rather than `json=...`. Returning JSON for responses is fine.

**Unit body via /createunitfile.** The `/createunit` call only registers the unit's name and type. To attach the HTML lesson body, follow up with `/createunitfile` against the new unit_id. This is two calls per lesson.

**No native sections.** TalentLMS does not have a section/module concept like Canvas. The sync emits a `text`-type unit named "Unit N: Title" before each course-unit's lesson units so the course outline has visual breaks between units.

**Test answers as flat fields.** `/createtestquestion` expects answers as `answer1`, `answer2`, ... `answerN` rather than a nested array. `correct_answer` is a 1-based index pointing at the correct option. The sync emits single-correct multiple-choice questions; if the source has multiple correct choices, only the first is marked correct on TalentLMS.

**HTML body is rendered as-is.** Mermaid diagrams pre-rendered to inline SVG and MicroSim iframes both work because TalentLMS embeds the HTML payload without sanitization-stripping iframes. Test once on your account; if iframes get stripped, fall back to image-plus-link.

## Error Cases

**401 Unauthorized.** API key is wrong or revoked. Generate a new one in Account, Settings, API.

**403 Forbidden.** API key is valid but the account does not allow the action. The free tier permits everything the sync does; if 403 appears, check whether the account has been downgraded.

**404 Not Found.** Object ID is wrong, or it was deleted. Sync state may be stale. Delete sync-state.json and re-sync.

**422 / 400 Validation error.** Response body usually contains details. Common causes: missing required field, course name already in use, invalid unit type.

**429 Too Many Requests.** Rate limited. The client retries automatically with backoff.

## Fields We Set vs Fields We Leave Default

The sync sets:
- course: `name`, `description`, optional `category_id`
- unit (header): `course_id`, `name`, `type=text`, `description`
- unit (lesson): `course_id`, `name`, `type=web`, `description`
- unit_file: `unit_id`, `content` (HTML)
- test: `course_id`, `name`, `description`, `pass_score`, `shuffle_questions`, `shuffle_answers`, `max_attempts` (when configured)
- test_question: `test_id`, `type=multiple_choice`, `question`, `answer1..N`, `correct_answer`, `explanation`

The sync does NOT set:
- Course pricing, certificate templates, prerequisites
- User enrollment or roles
- Custom course images, banners, intro videos
- Notification settings, email templates
- Content drip schedules

These are deliberately left out because they are subjective and account-specific. The sync handles content; the TalentLMS admin UI handles policy.

## Free Tier Limits

5 users and 10 courses, permanently. Plenty for testing the toolkit. If a course actually goes to learners through TalentLMS, the free tier will not scale; an upgrade to a paid plan is required for more users or courses.

## Tested API Version

These notes are accurate as of May 2026 against the TalentLMS public API documented at https://www.talentlms.com/api. If the API changes substantially, the sync needs updating.
