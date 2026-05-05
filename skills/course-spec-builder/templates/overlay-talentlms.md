# TalentLMS Overlay

This file fills in the platform-specific sections of the base build spec when the target platform is TalentLMS. The course-spec-builder skill reads this file and substitutes its sections into the base template at the matching `<!-- OVERLAY: ... -->` markers.

## OVERLAY: api-notes

TalentLMS exposes a REST API for managing courses, units, tests, and questions. The sync script uses this API to push your file content to your TalentLMS site.

- **Base URL:** `https://YOUR-DOMAIN.talentlms.com/api/v1/`
- **Authentication:** HTTP Basic Auth with the API key as the username and any string (or empty) as the password. The sync script handles this; you only paste the URL and key into `.env`.

Endpoints used by the sync script:

- **Courses:** `POST /coursecreate` to create, `GET /coursestatus?course_id=NN` to verify
- **Units:** `POST /createunit` (each unit is a lesson, header, or exam)
- **Unit body:** `POST /createunitfile` with the HTML body as a follow-up to /createunit
- **Tests:** `POST /createcoursetest` to create the test container, then `POST /createtestquestion` once per question

Rate limits: 100 to 200 requests per minute on the free tier. The sync script uses exponential backoff to stay under the limit. Pushing a 200-question final assessment hits the rate limiter, so the script chunks the requests in batches of 10 with a one-second sleep between batches.

Content quirks:

- Lesson body content is HTML, not markdown. The sync script converts lesson markdown to HTML using markdown-it-py before posting.
- POST endpoints expect form-encoded bodies, not JSON. The sync handles this; the difference matters only if you script against the API by hand.
- TalentLMS has no native section or module concept. The sync emits a text-type "Unit N: Title" header unit before each course-unit's lessons so the course outline has visual breaks.
- Test questions are emitted as multiple-choice with `answer1` through `answerN` flat fields and a 1-based `correct_answer` index. Multi-correct questions get only the first correct choice marked.
- Image references in lesson markdown should point at HTTPS URLs TalentLMS can fetch. Local image paths will not resolve once the lesson is on TalentLMS.

If a sync fails partway through, the script logs which object was being created. Rerun after fixing the issue; the script is idempotent and resumes where it left off.

## OVERLAY: sync-command

```
python3 scripts/sync.py
```

Or, once the bes command is installed:

```
bes sync
```

`bes sync` reads `course-config.yaml`, sees that the platform is `talentlms`, and runs the TalentLMS sync logic from the toolkit's `sync/talentlms/` skill. Same end result, less typing.

## OVERLAY: platform-risks

- **Free tier limits.** TalentLMS allows 5 users and 10 courses on the permanent free tier. Plenty for testing the toolkit and small offerings; not a path for paid course delivery at scale.
- **API quota.** The free tier's per-minute request quota is generous but finite. A full course sync (6 units, 30 lessons, 200 final-assessment questions) takes about half a minute on the free tier. Do not run sync in tight loops.
- **Test endpoint speed.** Pushing many questions to one test can be slow. The sync chunks the pushes in batches of 10 with a one-second sleep between batches. Adjust the batch size in scripts/sync.py if needed.
- **No native sections.** TalentLMS does not group lessons under modules. The sync emits a text-type header unit per course-unit. If you need a different layout, rearrange in the TalentLMS admin UI after sync.
- **Single-correct multiple choice.** TalentLMS classic multiple-choice marks one correct answer. Multi-correct course-final questions get the first correct choice marked; the rest are demoted to wrong on TalentLMS. Switch the type at the TalentLMS UI level if real multi-correct is needed.
- **HTML rendering.** Markdown-to-HTML via markdown-it-py is reliable for typical lesson content. Test rich features (tables, footnotes, custom blocks, MicroSim iframes) on a test course before relying on them.
- **Data export.** TalentLMS does provide a data export, but the real backup is your markdown and YAML in this repo. If you ever leave TalentLMS, point sync at a different platform and the content moves with you.

## OVERLAY: prerequisites

- TalentLMS account active. Sign up at https://www.talentlms.com on the free plan.
- Subdomain chosen during signup. Your account URL is `https://YOUR-DOMAIN.talentlms.com`.
- API key generated. In TalentLMS admin, go to Account & Settings, API. Copy the key. Save it in 1Password.
- The .env file in your course repo populated with:
  ```
  TALENTLMS_API_URL=https://YOUR-DOMAIN.talentlms.com
  TALENTLMS_API_KEY=your_key_here
  ```
- Verified the .env file is in .gitignore so it never gets committed.
- Decided enrollment policy. The sync script does not handle user invitations, drip schedules, or certificate templates. Those are configured in TalentLMS's web interface after the content is up.
