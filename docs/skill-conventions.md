# Skill Conventions

How to write a SKILL.md file for the toolkit. Every skill in the `skills/` and `sync/` folders follows this format. Reading this doc once is enough to understand any skill in the toolkit.

## What a Skill Is

A skill is a folder containing a `SKILL.md` file plus any supporting templates, references, or examples. The SKILL.md tells Claude Code what the skill does, what input it needs, and what output to produce.

When someone runs the skill, Claude Code reads the SKILL.md and follows the instructions. The skill is the playbook, Claude Code is the player.

## File Format

A SKILL.md has two parts: YAML frontmatter at the top, then a markdown body.

```yaml
---
name: course-spec-builder
version: 1.0
description: Generate a course build spec from a short course description
inputs:
  - course_name: string, required
  - subject: string, required
  - target_audience: string, required
  - target_platform: enum (thinkific, canvas, google-classroom, static-web, pdf), required
  - unit_count: integer, default 6
outputs:
  - docs/build-spec.md
  - docs/build-spec-source/build-spec.docx
dependencies:
  - none
phase: 2
---

# Course Spec Builder

Generates a complete build spec for a new course based on the inputs.

## When to Use

Use this skill at the very start of a new course project, before any content is written. The output of this skill is the contract that all later skills follow.

## Steps

1. Read all inputs from the user...

(rest of the body)
```

## Frontmatter Fields

Every skill must have these fields in the frontmatter:

### Required Fields

**name** (string)
The skill name. Must match the folder name (a skill in `skills/course-spec-builder/` has name `course-spec-builder`). Lowercase with hyphens. No spaces, no underscores.

**version** (string)
Semantic version of the skill. Start at 1.0. Bump the minor version (1.1, 1.2) for additions. Bump the major version (2.0) for breaking changes that would affect courses already built with the skill.

**description** (string)
One sentence explaining what the skill does. Shows up in `bes help` and skill catalogs. Keep it under 80 characters.

**inputs** (list)
What the skill needs from the user or from other skills. Each input has a name, a type, and a required/optional flag. Specify a default for optional inputs.

Valid input types: string, integer, boolean, enum, file_path, folder_path, yaml, markdown.

For enum inputs, list the valid values in parentheses.

**outputs** (list)
What the skill produces. Each output is a file path relative to the course repo root. If the skill modifies files instead of creating them, say so: `outputs: - existing course-config.yaml (modified)`.

**phase** (integer)
Which phase of the build order this skill belongs to. From the toolkit plan: 1 is documentation, 2 is scaffolding skills, 2.5 is the bes wrapper, 3 is content skills, 4 is additional sync targets, 5 is polish.

### Optional Fields

**dependencies** (list)
Other skills that must run before this one. Use the skill names. Default is `none`.

Example:

```yaml
dependencies:
  - course-spec-builder
  - repo-bootstrap
```

**status** (enum: draft, ready, deprecated)
Whether the skill is ready to use. Default is `ready`. Mark as `draft` while building, `deprecated` when superseded.

**subject_neutral** (boolean)
Whether the skill works for any subject (default true) or is locked to a specific subject area (false). Most skills are neutral. The very rare subject-specific skill should set this to false and document why in the body.

**audience_neutral** (boolean)
Same idea for audience. Most skills work for any audience because voice is per-course. Default true.

## Body Format

After the frontmatter, the markdown body is the actual instructions Claude Code follows. Use these sections in order:

### # [Skill Name]
The first H1 is the skill name as a friendly title. Sentence case is fine here.

### ## When to Use
One paragraph explaining when this skill is the right tool. Include when NOT to use it if there is a similar skill that might be confused for this one.

### ## Steps
A numbered list of what Claude Code should do, in order. Each step is one to three sentences. Be specific. Vague steps produce vague output.

If a step requires reading a file from the course repo, say so explicitly: "Read `course-config.yaml` and extract the `voice_guide_path` field."

If a step requires writing a file, specify the path and format: "Write the result to `content/unit-01/lessons/01-introduction.md` as markdown with YAML frontmatter."

### ## Output Format
Specifies the exact format of each output file. For YAML outputs, show the full schema. For markdown outputs, show the expected structure with headers and any required sections.

### ## Examples
At least one fully worked example: realistic inputs in, realistic outputs out. Two or three examples is better, especially if the skill produces different output for different subject areas or audiences.

### ## Quality Checks
Things Claude Code should verify before declaring the skill complete. Examples: "Confirm every lesson has a learning_outcome field," "Confirm no two questions in the bank have the same id."

### ## Common Mistakes
Mistakes the skill should avoid. Examples: "Do not generate quiz questions that ask about content not in the lesson. Do not write lessons longer than the duration_minutes field allows."

## Supporting Files in a Skill Folder

A skill folder can contain more than just SKILL.md.

**templates/** (optional folder)
Files that get copied into the course repo as starting points. The repo-bootstrap skill, for example, has templates for course-config.yaml, .gitignore, and README.

**reference/** (optional folder)
Background information Claude Code reads to do its job but does not copy anywhere. The sync/thinkific skill, for example, has reference docs on the Thinkific API.

**examples/** (optional folder)
Worked examples showing the skill in action with different inputs.

**voice-examples.md** (optional file, content skills only)
Sample passages in different voices to help the lesson-drafter skill understand voice variations. Used at run time when the course's voice-guide.md is being interpreted.

## Versioning a Skill

Skills evolve. When you change a skill, bump the version field and add a changelog at the bottom of the SKILL.md.

```markdown
## Changelog

### 1.2 (2026-06-15)
- Added support for video lesson type
- Improved error handling when course-config.yaml is missing fields

### 1.1 (2026-06-08)
- Added the dependencies field to inputs

### 1.0 (2026-06-01)
- Initial version
```

## Testing a Skill

Before marking a skill as `status: ready`, test it on at least two different inputs. For example, the lesson-drafter skill should produce sensible output for both a Backstage Essentials live event lesson and a high school geology lesson, since the toolkit is subject-neutral.

The course-validator skill (when built) will catch most common skill bugs. Until then, manual verification is the path.

## Naming a New Skill

Three rules for picking a skill name:

1. Verb-noun or noun-noun, lowercase, hyphenated. Examples: `course-spec-builder`, `lesson-drafter`, `quiz-builder`. Bad examples: `make_lesson`, `LessonGenerator`, `bsm`.

2. Specific enough to be unambiguous. `quiz-builder` is good. `builder` is bad.

3. Subject-neutral when possible. `lesson-drafter` works for any subject. `live-event-lesson-drafter` does not.

## Adding a Skill to the Toolkit

When building a new skill:

1. Create the folder under `skills/` (or `sync/` for platform sync skills)
2. Create SKILL.md following this format
3. Create supporting files (templates, references, examples) as needed
4. Test the skill manually
5. Add an entry to `docs/bes-command-reference.md` if a new bes command wraps it
6. Commit with the message "Add [skill-name] skill"
