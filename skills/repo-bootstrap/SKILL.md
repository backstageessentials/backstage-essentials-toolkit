---
name: repo-bootstrap
version: 1.0
description: Scaffold a new course repo with folders, config files, and placeholders based on a build spec
inputs:
  - build_spec_path: file_path, required, default ./docs/build-spec.md
  - course_description_path: file_path, required, default ./course-description.md
  - voice_guide_path: file_path, optional, default ./voice-guide.md
  - target_platform: enum (thinkific, canvas, google-classroom, static-web, pdf), required
  - unit_count: integer, default 6
  - unit_titles: list of strings, optional
  - confirm_before_writing: boolean, default true
outputs:
  - course-config.yaml
  - .gitignore
  - .env.example
  - requirements.txt
  - README.md
  - content/unit-NN-{slug}/ folders (one per unit)
  - content/unit-NN-{slug}/unit.yaml (one per unit)
  - content/unit-NN-{slug}/lessons/ (empty folder per unit)
  - content/unit-NN-{slug}/knowledge-check.yaml (placeholder per unit)
  - exam/course-final.yaml (placeholder)
  - scripts/sync.py (placeholder)
  - scripts/validate.py (placeholder)
  - scripts/helpers/ (empty folder)
dependencies:
  - course-spec-builder (or a hand-written build spec)
phase: 2
status: ready
subject_neutral: true
audience_neutral: true
---

# Repo Bootstrap

Scaffolds the folder structure and config files for a new course repo. Reads the build spec to know what to create.

## When to Use

Run this skill once per course, immediately after course-spec-builder has produced a build spec and the course description and voice guide are in place.

Do NOT run this skill if the course repo already has content. It is meant for fresh, empty repos. If you accidentally run it on a populated repo, files will be overwritten and you will lose work. The skill checks for existing content and asks before proceeding, but caution is warranted.

## Steps

1. Verify required files exist:
   - The build spec at `build_spec_path` (default `./docs/build-spec.md`)
   - The course description at `course_description_path` (default `./course-description.md`)
   - Optionally the voice guide at `voice_guide_path` (default `./voice-guide.md`)
   
   If the build spec is missing, stop and tell the user to run course-spec-builder first. If the course description is missing, stop and tell the user to write it using the toolkit's `docs/course-description-guide.md` as reference. The voice guide is technically optional for bootstrap, but if missing, warn the user that the lesson-drafter skill will not work later.

2. Read the build spec. Extract:
   - Course name (from the H1 at the top)
   - Course slug (derived from name or from course-config if it exists)
   - Target platform (from the build spec or from the input parameter)
   - Unit count (from the input parameter or from the build spec's repo structure section)

3. Read the course description. Extract:
   - Audience summary
   - Learning outcomes
   - Specs (price, duration, format, etc.)

4. If `unit_titles` is not provided, prompt the user for unit titles. Provide a sensible default list ("Unit 1," "Unit 2," etc.) but encourage the user to give real titles before proceeding. Better unit titles produce better folder slugs.

5. Check whether the current directory is already a git repo. If yes, check whether it is empty (only README and .git folder). If the repo has substantive content, ask the user before proceeding. Make this confirmation prominent: "This repo appears to have content. Bootstrap will overwrite files. Continue? (y/N)"

6. If `confirm_before_writing` is true, show the user the planned file list and ask for confirmation before any writes. List every file and folder that will be created.

7. Generate the file tree. Create files in this order so partial failures are recoverable:
   
   a. Top-level config files first:
      - `course-config.yaml` (populated with course name, slug, platform, completion threshold, units count, and paths to course-description.md and voice-guide.md). When `target_platform` is `canvas`, also write a top-level `canvas_account_id` field under the `course:` block, defaulted to `1` with a comment instructing the user to replace it with the right Canvas account ID for their instance.
      - `.gitignore` (with .env, .DS_Store, __pycache__, sync-state.json, sync-state.dry-run.json, .claude/settings.local.json, and editor cruft)
      - `.env.example` (copy `templates/env-example/{target_platform}.env`. For Thinkific that is `THINKIFIC_API_KEY` and `THINKIFIC_SUBDOMAIN`. For Canvas that is `CANVAS_API_URL` and `CANVAS_API_TOKEN`. Each platform template carries the comments the user needs.)
      - `requirements.txt` (with pyyaml, requests, markdown-it-py for all platforms; add platform-specific libraries as needed)
      - `README.md` (with course name, one-paragraph summary from the description, link to docs/build-spec.md, and platform info)

   b. Content folders next:
      - `content/unit-NN-{slug}/` for each unit, where NN is two-digit zero-padded number and slug is derived from the unit title
      - Inside each unit folder: `unit.yaml`, `lessons/` (empty folder), `knowledge-check.yaml` (placeholder)

   c. Exam folder:
      - `exam/course-final.yaml` (placeholder with the schema from the build spec, no actual questions)

   d. Scripts folder:
      - `scripts/sync.py` (placeholder with a comment explaining the sync skill writes the real implementation)
      - `scripts/validate.py` (placeholder)
      - `scripts/helpers/` (empty folder with .gitkeep)

8. After writing all files, run `git status` to show the user what was created. Suggest the next step: review the placeholders, then commit with a message like "Initial folder structure" and push.

9. Show a summary: number of files created, number of unit folders, location of the build spec, suggested next step (run lesson-drafter to start writing content, or commit and push first).

## Output Format

### course-config.yaml

```yaml
course:
  name: "{COURSE_NAME}"
  slug: "{COURSE_SLUG}"
  description_path: "./course-description.md"
  voice_guide_path: "./voice-guide.md"
  build_spec_path: "./docs/build-spec.md"
  platform: "{TARGET_PLATFORM}"
  completion_threshold: 0.75
  units: {UNIT_COUNT}
  
  # Optional fields, populated from course-description if available
  price_usd: {PRICE_OR_NULL}
  duration_hours: {DURATION_OR_NULL}
  language: "{LANGUAGE_OR_DEFAULT_EN}"
```

### unit.yaml (per unit)

```yaml
unit:
  number: {N}
  title: "{UNIT_TITLE}"
  description: ""
  learning_outcomes: []
```

The description and learning_outcomes fields start empty. The author fills them in as they design each unit.

### knowledge-check.yaml (per unit, placeholder)

```yaml
quiz:
  title: "Unit {N} Knowledge Check"
  pass_threshold: 0.7
  questions: []
```

Empty questions list. The quiz-builder skill populates these later.

### exam/course-final.yaml (placeholder)

```yaml
final_assessment:
  name: "{COURSE_NAME} Course Final"
  total_questions_in_bank: 200
  questions_per_attempt: 100
  pass_threshold: 0.75
  randomize: true
  questions: []
```

### .gitignore

```
.env
.env.local
.DS_Store
__pycache__/
*.pyc
sync-state.json
.claude/settings.local.json
.vscode/
.idea/
*.swp
node_modules/
```

### .env.example (Thinkific example)

```
# Copy this file to .env and fill in your actual values.
# .env is gitignored and never committed.

THINKIFIC_API_KEY=your_api_key_here
THINKIFIC_SUBDOMAIN=your_subdomain_here
```

The exact contents depend on the target platform. Each platform's required secrets are different.

### .env.example (Canvas example)

```
CANVAS_API_URL=https://your-canvas-host
CANVAS_API_TOKEN=your_api_token_here
```

For Canvas, also add `canvas_account_id: <id>` to course-config.yaml under the `course:` block. The validator refuses to sync a Canvas course without it.

### requirements.txt

```
pyyaml>=6.0
requests>=2.31
markdown-it-py>=3.0
python-dotenv>=1.0
```

Plus any platform-specific libraries (e.g., none additional for Thinkific; google-api-python-client for Google Classroom).

### README.md

```markdown
# {COURSE_NAME}

{ONE_SENTENCE_SUMMARY_FROM_DESCRIPTION}

## Status

Active development. Built on the [Backstage Essentials Course Builder Toolkit](https://github.com/backstageessentials/backstage-essentials-toolkit).

## Structure

- `course-description.md`: audience, outcomes, scope.
- `voice-guide.md`: how the writing should sound.
- `docs/build-spec.md`: the technical spec for this course.
- `content/`: lessons and knowledge checks per unit.
- `exam/course-final.yaml`: comprehensive final assessment.
- `scripts/`: sync and validation scripts.

## Daily Workflow

```
cd {COURSE_SLUG}
git pull
claude
```

Then ask Claude Code to draft a lesson, write quiz questions, or sync to {TARGET_PLATFORM}.

## Platform

This course deploys to {TARGET_PLATFORM}.
```

## Examples

### Example 1: Backstage Essentials course on Thinkific

Inputs:
- build_spec_path: ./docs/build-spec.md
- course_description_path: ./course-description.md
- voice_guide_path: ./voice-guide.md
- target_platform: thinkific
- unit_count: 6
- unit_titles: ["Professional Foundation", "Pre-Production", "Load-In", "Systems Build", "Show Day", "Strike and Wrap"]

Outputs: A repo with content/ folders unit-01-professional-foundation through unit-06-strike-and-wrap, course-config.yaml configured for Thinkific, .env.example with THINKIFIC_API_KEY and THINKIFIC_SUBDOMAIN.

### Example 2: High school geology course on Canvas

Inputs:
- target_platform: canvas
- unit_count: 8
- unit_titles: ["What Geology Studies", "Minerals", "Rocks", "Plate Tectonics", "Earthquakes and Volcanoes", "Weathering and Erosion", "Earth's Resources", "Earth in the Solar System"]

Outputs: A repo with eight unit folders, course-config.yaml configured for Canvas (including a `canvas_account_id` field placeholder for the user to fill in), .env.example with `CANVAS_API_URL` and `CANVAS_API_TOKEN`.

### Example 3: Sound mixing tutorial as static web

Inputs:
- target_platform: static-web
- unit_count: 4
- unit_titles: ["Signal Flow", "Gain Staging", "EQ", "Dynamics"]

Outputs: A repo with four unit folders, course-config.yaml configured for static-web, no .env file needed (no API keys for static-web), an extra mkdocs.yml stub at the root.

## Quality Checks

- All folders created. Use `find . -type d` to verify.
- All placeholder files created with valid YAML or markdown content. Use `python -c "import yaml; yaml.safe_load(open('course-config.yaml'))"` to verify YAML files parse.
- No leftover `{PLACEHOLDER}` tokens in any file.
- The `.env.example` matches the target platform's required secrets.
- The `.gitignore` includes `.env` so the real secrets never get committed.
- Unit folder slugs are URL-safe (lowercase, hyphenated, no special characters).

## Common Mistakes

- **Writing over an existing course repo.** Always check for existing content and confirm before writing. The user may have local changes that have not been committed yet.

- **Hardcoding paths.** Use the paths from course-config.yaml so other skills find the right files. Do not assume `./course-description.md` if the config says somewhere else.

- **Generating sync.py with real implementation.** The repo-bootstrap skill creates a placeholder. The actual sync logic is generated later by the platform sync skill (sync/thinkific, sync/canvas, etc.) so it stays current with each platform's API.

- **Forgetting platform-specific .env.example.** A Thinkific course needs THINKIFIC_API_KEY; a Canvas course needs CANVAS_API_TOKEN. Generic .env.example with placeholder names is wrong; the file should be specific to the target platform.

- **Empty unit titles.** If the user does not provide unit titles, fall back to "Unit 1," "Unit 2," etc., but warn loudly that they should rename these before drafting content. Slug like `unit-01-unit-01` is bad.

## Files in This Skill Folder

- `SKILL.md` (this file)
- `templates/course-config.template.yaml`
- `templates/gitignore.template`
- `templates/env-example/` (one file per platform: thinkific.env, canvas.env, etc.)
- `templates/requirements.template.txt`
- `templates/readme.template.md`
- `templates/unit.template.yaml`
- `templates/knowledge-check.template.yaml`
- `templates/course-final.template.yaml`
- `templates/sync-placeholder.py`
- `templates/validate-placeholder.py`

## Changelog

### 1.0 (2026-05-03)
- Initial version
- Supports Thinkific platform fully; other platforms supported with generic .env.example

### 1.1 (2026-05-05)
- Phase 11: Canvas .env.example uses `CANVAS_API_URL` and `CANVAS_API_TOKEN`
  (manual access token pattern). When `target_platform` is `canvas`, the
  generated course-config.yaml also gets a `canvas_account_id` field with a
  default of `1` and a comment pointing to the institution's Canvas admin.
  sync-state.dry-run.json added to .gitignore so dry-run inspection files
  stay out of git.
