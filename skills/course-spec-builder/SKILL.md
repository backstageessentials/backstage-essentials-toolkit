---
name: course-spec-builder
version: 1.0
description: Generate a complete course build spec from a course description and target platform
inputs:
  - course_description_path: file_path, required, default ./course-description.md
  - target_platform: enum (thinkific, canvas, google-classroom, static-web, pdf), required
  - output_format: enum (markdown, docx, both), default both
outputs:
  - docs/build-spec.md
  - docs/build-spec-source/build-spec.docx (if output_format includes docx)
dependencies:
  - none
phase: 2
status: ready
subject_neutral: true
audience_neutral: true
---

# Course Spec Builder

Generates a complete build spec for a new course based on the course description and the target delivery platform.

## When to Use

Run this skill at the very start of a new course project, immediately after `course-description.md` is written and before any other content authoring begins.

The output of this skill is the contract that every later skill follows. lesson-drafter reads it. quiz-builder reads it. The sync skill for the target platform reads it. Get this right and the rest of the course production stays coherent.

Do NOT run this skill if a build spec already exists in the course repo. If you need to regenerate the spec because the course description changed significantly, archive the old spec first by moving it to `docs/build-spec-archive/build-spec-vN.md`.

## Steps

1. Read the course description from the path in `course_description_path` (default `./course-description.md`). Verify the file exists and contains the three required sections: Pitch, Specs, Outcomes. If any section is missing or appears to be the unfilled template, stop and tell the user the course description must be completed first.

2. Read `course-config.yaml` from the repo root if it exists. Extract any fields that affect the spec (course name, slug, units count, completion threshold). If `course-config.yaml` does not exist yet, that is fine. The repo-bootstrap skill will create it after this skill runs.

3. Load the base template from `templates/base-build-spec.md` in this skill folder. This is the universal portion of the spec.

4. Load the platform overlay from `templates/overlay-{target_platform}.md` in this skill folder. This contains platform-specific sections (API notes, content type mappings, sync command examples).

5. Merge the base and the overlay. Insertion points in the base template are marked with `<!-- OVERLAY: section-name -->`. The overlay file has matching section markers. Replace each insertion point with the matching overlay content.

6. Substitute course-specific values throughout the merged spec:
   - `{COURSE_NAME}` becomes the course name from the description
   - `{COURSE_SLUG}` becomes the course slug from `course-config.yaml` or a slug derived from the name
   - `{TARGET_PLATFORM}` becomes the platform name as rendered in prose (e.g., "Thinkific")
   - `{UNIT_COUNT}` becomes the number of units (default 6 if not specified)
   - `{COMPLETION_THRESHOLD}` becomes the completion threshold (default 0.75)
   - `{AUDIENCE_SUMMARY}` becomes a one-sentence audience description from the course description's Specs section
   - `{LEARNING_OUTCOMES_LIST}` becomes a markdown list of the outcomes from the course description

7. Write the merged spec to `docs/build-spec.md`. If the file already exists, ask the user before overwriting.

8. If `output_format` is `docx` or `both`, also generate a Word doc version of the spec at `docs/build-spec-source/build-spec.docx`. Use a clean professional format with Heading 1 and Heading 2 styles, no fancy formatting. The Word version is the human-readable source of truth; the markdown is what other skills read.

9. Show the user a summary: spec generated, target platform, number of sections, location of the output files. Suggest next step: run repo-bootstrap to scaffold the course folder structure.

## Output Format

The build spec is a structured markdown document with these sections, in order:

1. **What This Whole Thing Is, In Plain English** (universal)
2. **Vocabulary You Will See** (universal)
3. **The Big Picture, Step by Step** (universal)
4. **Setting Up GitHub From Your Computer** (universal)
5. **Building the Folder Structure** (universal)
6. **Repo Structure** (universal)
7. **File Formats** (universal, but with platform-specific lesson and assessment formats)
   - 7.6 **Visual Aids** (universal: per-unit list of diagrams and MicroSims; populated as the course evolves)
8. **What the Sync Script Does** (universal)
9. **Platform API Notes** (platform-specific overlay)
10. **Daily Workflow Once Everything is Set Up** (universal, with platform-specific sync command)
11. **Pilot First** (universal)
12. **Risk Notes** (universal, with platform-specific risk additions)
13. **Launch Instruction for Claude Code** (universal)
14. **What to Have Ready Before Build Day** (universal, with platform-specific prerequisites)

The Word version follows the same structure with the same section numbering.

## Examples

### Example 1: Thinkific course

Inputs:
- course_description_path: ./course-description.md (Backstage Essentials live event course)
- target_platform: thinkific
- output_format: both

Outputs: a build spec with all 14 sections, where Section 9 contains the Thinkific API notes (base URL, auth headers, endpoints for courses/chapters/lessons/quizzes), Section 10 ends with `python3 scripts/sync.py` for the daily sync command, and Section 14 lists Thinkific account active and Thinkific API key generated as prerequisites.

### Example 2: Canvas course (college geology)

Inputs:
- course_description_path: ./course-description.md (Introduction to Physical Geology, 200-level college course)
- target_platform: canvas
- output_format: markdown only

Outputs: a build spec with all 14 sections, where Section 9 contains Canvas LMS API notes (base URL, OAuth token auth, endpoints for modules/assignments/quizzes), Section 10 ends with `python3 scripts/sync.py` configured to push to Canvas, and Section 14 lists Canvas instance URL and Canvas API token as prerequisites.

### Example 3: Static web course (free public sound design tutorial)

Inputs:
- course_description_path: ./course-description.md (Free intro to live sound mixing)
- target_platform: static-web
- output_format: docx only

Outputs: a Word doc build spec where Section 9 explains MkDocs configuration and theme choice, Section 10 ends with `mkdocs build && mkdocs gh-deploy` for the daily deploy command, and Section 14 lists GitHub Pages enabled on the repo and a domain configured if applicable.

## Quality Checks

Before declaring the skill complete, verify:

- All `{PLACEHOLDER}` tokens have been replaced with real values. No leftover placeholders in the output.
- All `<!-- OVERLAY: -->` markers have been replaced with actual overlay content. No leftover markers.
- The output spec contains all 14 sections in the correct order.
- The platform-specific sections (9, 10, 12, 14) actually contain platform-appropriate content, not Thinkific content in a Canvas spec or vice versa.
- Section numbering is sequential with no gaps.
- The Word doc version (if generated) opens correctly and shows proper heading styles.

## Common Mistakes

- **Generating a spec from an unfilled course description.** Stop and require the user to complete `course-description.md` first. A spec built from `[Insert your sample here]` placeholder text is worthless.

- **Leaving placeholders in the output.** If `{COURSE_NAME}` appears anywhere in the final spec, the substitution failed. Run a check after merging.

- **Mixing platform overlays.** A Thinkific spec must not contain Canvas API notes. The overlay file for the target platform is the only platform-specific content that should appear.

- **Generating a docx without proper heading styles.** Section headers in the Word doc must use Heading 1 and Heading 2 styles, not bold paragraph text. This matters because other tools may extract structure from the styles.

- **Hardcoding Backstage Essentials specifics.** This skill is subject-neutral. Do not assume the course is about live events. The course description tells the skill what subject the course is about. Use that. Do not let any Backstage Essentials examples leak into a different course's spec.

## Files in This Skill Folder

- `SKILL.md` (this file)
- `templates/base-build-spec.md` (the universal portion of the spec, with overlay markers)
- `templates/overlay-thinkific.md` (Thinkific-specific sections)
- `templates/overlay-canvas.md` (Canvas-specific sections)
- `templates/overlay-google-classroom.md` (Google Classroom-specific sections)
- `templates/overlay-static-web.md` (MkDocs/static site sections)
- `templates/overlay-pdf.md` (PDF generation sections)

The overlay files for non-thinkific platforms are stubs in Phase 2. They get filled in during Phase 4 when those sync skills get built. For Phase 2, only the thinkific overlay is fully populated.

## Changelog

### 1.0 (2026-05-03)
- Initial version
- Base template plus platform overlay architecture
- Thinkific overlay populated; other platform overlays are stubs for Phase 4

### 1.1 (2026-05-04)
- Phase 6: base build spec now includes Section 7.6 Visual Aids, a per-unit
  list of Mermaid diagrams and MicroSims. The diagram-builder and
  microsim-builder skills read and write this section.

### 1.2 (2026-05-04)
- Phase 7: Visual Aids template's `microsims:` list now has a worked
  example with the seven supported template types and the
  `lesson` / `type` / `file` / `purpose` field convention.

### 1.3 (2026-05-05)
- Phase 11: Canvas overlay populated with full API notes, sync command,
  platform risks, and prerequisites alongside the Thinkific overlay.

### 1.4 (2026-05-05)
- Phase 12: PDF overlay populated with renderer notes (WeasyPrint
  primary, Chrome fallback), Mermaid pre-render via mermaid-cli, the
  QR-vs-screenshot MicroSim strategies, and the pdf_* course-config
  fields.
