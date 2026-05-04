# Canvas Overlay (stub, Phase 4)

This overlay is a placeholder. The full Canvas content gets written when the sync/canvas skill is built in Phase 4.

For now, generating a build spec with target_platform: canvas produces a working spec with these stub sections. The spec is usable as a planning document but cannot drive a real Canvas sync until Phase 4 ships.

## OVERLAY: api-notes

Canvas LMS exposes a REST API for managing courses, modules, assignments, and quizzes.

The full API notes will be filled in during Phase 4. For now, planning placeholder:

- Base URL: `https://your-institution.instructure.com/api/v1/`
- Authentication: Bearer token in Authorization header
- Endpoints used: courses, modules, module_items, assignments, quizzes, quiz_questions
- Common Cartridge export available as an alternative to direct API push

## OVERLAY: sync-command

```
# Not yet implemented (Phase 4)
# Will be: bes sync (reads course-config.yaml platform field, calls sync/canvas)
```

## OVERLAY: platform-risks

Detailed risks will be documented in Phase 4 when the sync/canvas skill is built. Expected risk areas:

- Canvas instances vary by institution. Some features (LTI tools, specific quiz types) require institution-level enablement.
- Canvas API tokens are tied to a specific user account. If the token holder leaves the institution, the integration breaks.
- Common Cartridge export is a useful fallback if direct API access is restricted.

## OVERLAY: prerequisites

- Canvas instance URL for your institution.
- Canvas API access token. Generated from Account, Settings, New Access Token.
- Course shell created in Canvas (the sync script populates content; it does not create the course shell from scratch).
- Decided whether content goes in a published or unpublished course state.
