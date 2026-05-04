# Backstage Essentials — Reference Material

These files are reference material from the **first attempt** at building the
Backstage Essentials course, before this toolkit existed. The original
`backstage-essentials-course` repo has since been retired in favor of building
courses through the toolkit.

They are kept here as worked examples of the **input shapes** the toolkit
works with, so a future course author (including Bill himself) can see what a
real, hand-written build spec, course config, and curriculum sketch look like.

## Files

- **`build-spec-v3.md`** — The hand-written technical build spec for
  Backstage Essentials, v3. This is the kind of document the
  `course-spec-builder` skill now produces from a course description, voice
  guide, and target platform. Use it as a reference for the level of detail and
  structure a good build spec should have.

- **`Backstage_Essentials_Course_BuildSpec_Chromebook_v3.docx`** — The original
  Word version of the v3 build spec. Kept alongside the markdown so the
  document history is preserved.

- **`proavcourses-original-curriculum.md`** — A curriculum sketch from the
  pro-AV-courses brainstorm, reflecting the original unit/lesson breakdown
  before the toolkit's structure was settled. Useful as a "here's what an
  unstructured curriculum dump looks like" example.

- **`course-config-example.yaml`** — The hand-edited `course-config.yaml`
  from the original course repo. The `repo-bootstrap` skill now generates
  this file from a template, but this version shows what a fully populated
  config looks like for a real course.

## How to use these

**These are references, not starting files.** When Bill is ready to build
the real Backstage Essentials course through the toolkit, the workflow is:

1. Run `bes new-course` (Phase 3+) to scaffold a fresh course repo from the
   toolkit's templates.
2. Open these files alongside the new repo and use them as a guide for
   what to fill in — voice, depth, structure, unit boundaries.
3. Do **not** copy these files into the new course repo wholesale. Let the
   toolkit's skills regenerate equivalent files so the course stays in sync
   with current toolkit conventions.

If anything in these references contradicts current toolkit guidance (in
`docs/` or in a skill's `SKILL.md`), the toolkit guidance wins — these
files are frozen at the point the original course repo was retired.
