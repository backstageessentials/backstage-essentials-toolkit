# Google Classroom Overlay (stub, Phase 4)

This overlay is a placeholder. The full Google Classroom content gets written when the sync/google-classroom skill is built in Phase 4.

## OVERLAY: api-notes

Google Classroom uses Google's APIs for managing courses, coursework, and announcements. Authentication is via OAuth 2.0.

Full API notes filled in during Phase 4. Known constraints:

- The Classroom API does not currently support creating quizzes directly. Quizzes are typically built as Google Forms and linked from coursework.
- Course materials can be linked from Google Drive, which gives flexibility but adds a dependency.

## OVERLAY: sync-command

```
# Not yet implemented (Phase 4)
```

## OVERLAY: platform-risks

- API limitations on quiz creation may require a hybrid approach: Classroom for assignment management, Google Forms for assessment.
- Domain admin permissions may be required for some API operations in Google Workspace for Education environments.
- OAuth tokens for service accounts have specific scoping requirements.

## OVERLAY: prerequisites

- Google Workspace for Education account with appropriate permissions, or a personal Google account if your audience can use one.
- Google Cloud project with Classroom API enabled.
- OAuth credentials configured for the application.
- Classroom course shell created.
