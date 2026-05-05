# Backstage Essentials Course Builder Toolkit

This is the orchestration playbook. Claude Code reads this file automatically when started in this folder, so anything here is durable instruction for any future Claude Code instance running in the toolkit.

## Identity

This repository is the **Backstage Essentials Course Builder Toolkit**. It is a reusable, subject neutral toolkit for building courses from plain text source files. The CLI wrapper is named `bes` and is registered via `pip install -e .`. Run `bes --help` from anywhere to see the current commands.

The toolkit works for any subject and any publishing target (Thinkific, Canvas, Google Classroom, static web, PDF). Each course is a sibling git repo of this one. Voice is per course, not toolkit baked.

## Available bes Commands

Run any of these from inside a course folder. The toolkit is invoked through them.

| Command | Purpose |
|---------|---------|
| `bes new-course` | Scaffold a new course folder with build spec, config files, and a course CLAUDE.md. |
| `bes new-lesson` | Draft a lesson via the lesson-drafter skill (one lesson at a time). |
| `bes new-quiz` | Generate a unit's knowledge check questions via the quiz-builder skill. |
| `bes add-diagrams` | Add Mermaid diagrams to existing lessons via the diagram-builder skill. |
| `bes add-microsim` | Add an interactive HTML widget to a lesson via the microsim-builder skill. |
| `bes build-final` | Generate the course final assessment question bank via the final-assessment-builder skill. |
| `bes build-course` | Build an entire course end to end (lessons, quizzes, final). |
| `bes export-pdf` | Generate a PDF version of the course via the pdf-sync skill. Works regardless of the course's primary platform. |
| `bes validate` | Lint the course repo for missing fields, broken refs, and draft flags. |
| `bes commit` | Stage changes and commit with a generated or supplied message. |
| `bes push` | Push commits to the GitHub remote. |
| `bes status` | Show pending changes, unsynced content, and last sync time. |

Each command (except validate, commit, push, status) prints a structured prompt describing the work to do. Do not hand that prompt back to Bill. Run the command yourself, capture the prompt, and execute it.

## Orchestration Pattern

When Bill asks for course work in plain English ("draft Unit 2 lesson 1," "add a knowledge check to Unit 3," "build a final"), follow this pattern every time:

1. **Run the appropriate `bes` command via Bash** with the right flags.
2. **Capture the structured prompt** the command prints.
3. **Execute that prompt directly** by reading the referenced skill files in `skills/`, drafting the content per the skill's procedure, and writing the output files.
4. **Show Bill the resulting files** so he can review the diff or open the preview.
5. **Commit and push** the course repo (and toolkit if relevant) without waiting for an explicit ask. Standard message style: imperative mood, why over what, `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>` trailer.

Never make the user paste a prompt manually. The bes prompt is for you, not for Bill.

Routine work that does not need explicit approval first:
- Drafting lessons, quizzes, finals, diagrams, microsims.
- Editing course files, regenerating previews.
- Running `bes validate`, `bes commit`, `bes push` on a course repo.

Still ask before:
- Force pushing, destructive git operations (reset hard, branch delete, rm rf).
- Anything affecting shared infrastructure beyond the local repo.
- Running `bes new-course` outside the user's expected location.

## Skill Reference

Each skill in `skills/` is a self contained capability with its own `SKILL.md`. Read the relevant `SKILL.md` before drafting; do not improvise.

| Skill folder | Purpose |
|--------------|---------|
| `skills/course-spec-builder/` | Generate the course build spec (docs/build-spec.md) from a course description and target platform. |
| `skills/repo-bootstrap/` | Scaffold the course repo folder structure (course-config.yaml, content/, exam/, scripts/, etc.). |
| `skills/lesson-drafter/` | Draft one lesson markdown file in the course's voice. Reads voice-guide.md, course-description.md, and the unit's other lessons. |
| `skills/quiz-builder/` | Generate unit knowledge check questions in scenario, recall, applied calculation, or mixed style. |
| `skills/final-assessment-builder/` | Generate the course final assessment question bank (typically 200 questions, 50 sampled per attempt across 3 retest attempts). |
| `skills/diagram-builder/` | Add Mermaid diagrams to existing lessons where they earn their place. Lints syntax before writing. |
| `skills/microsim-builder/` | Add interactive HTML widgets (MicroSims) to a lesson by customizing one of seven starter templates. |
| `skills/course-validator/` | Deep validation of the course repo (voice checks, coverage, draft flag review) beyond what bes validate catches. |

Each skill reads voice and audience context from the course folder it runs in, so the same skill produces different output for different courses.

## Voice Rules at the Toolkit Level

When working in a course folder:

1. **Always read that course's `voice-guide.md`** before generating any content. It is the authoritative source for tone, register, sentence length, banned phrases, and lesson shape. The toolkit is subject neutral and audience neutral; the course's voice guide tells you whether you are writing for adult professionals, high school students, undergraduates, hobbyists, or coaches.
2. **Apply any rules from the course's own `CLAUDE.md`** in addition to the toolkit's CLAUDE.md. The course CLAUDE.md takes precedence on course specific rules; this file takes precedence on toolkit orchestration.
3. **Author defaults that bind only when no voice guide rule covers the case.** Treat these as Bill's personal toolkit defaults, not as universal toolkit rules. A course voice guide that says otherwise wins:
   - No em dashes, no en dashes, no hyphens used as separators in prose. Use commas, colons, periods.
   - Bottom line first sentence in every lesson.
   - Plain text questions only. No markdown styling inside question text.
   - Trim by default. Whichever version is shorter, use that one, unless the longer one is genuinely clearer.

The casual, peer-to-peer, Feynman-style register that fits Bill's adult-trade work is **not** a toolkit default. If a course's voice guide calls for formal academic, K-12, narrative-historical, or any other register, write in that register. Do not import a working-tech voice into a high school history course.

## Validation Pattern

When Bill asks to verify, audit, or check a course:

1. Run `bes validate` first (and `bes status` if relevant).
2. Show the issues in a short summary.
3. Wait for direction before fixing anything. Validation is diagnostic, not automatic.

If Bill explicitly asks to fix what validate found, then fix and commit per the orchestration pattern.

## File Creation Pattern

Always create the file the prompt describes. Never just describe what would be in it. Bill will not paste content from a transcript into a file by hand.

- For drafted lessons: write the markdown file at the path the lesson-drafter skill computed.
- For diagrams: edit the lesson markdown in place, never produce a "here is what the diagram would look like" block.
- For microsims: copy the template, edit the customize block, save the customized HTML, then edit the lesson markdown to add the iframe directive.
- For previews: write the HTML to the course's `preview/` folder.
- For commits: create the actual commit. Do not show the proposed message and stop.

## Course Location Pattern

A course always lives as a **sibling folder of the toolkit**, not inside it. Standard layout:

```
~/Code/
  backstage-essentials-toolkit/    <- this folder
  live-event-technician-test-course/
  some-future-course/
```

When you run `bes new-course`, run it from `~/Code` so the new folder lands as a sibling. Do not create courses inside `backstage-essentials-toolkit/`. The toolkit is reusable across courses; courses are not nested in it.

## Standing Reference

- The toolkit's plan and roadmap docs are in `docs/`. The Visual Aids Roadmap (`docs/Backstage_Essentials_Toolkit_VisualAidsRoadmap.docx`) covers the Phase 6 and Phase 7 visual content work that is now complete.
- Examples live in `examples/`. The `sample-course-with-diagrams/` example shows what good Mermaid and a formula MicroSim look like in real lesson context.
- The reference implementation course is `live-event-technician-test-course/` (sibling folder, not in this repo).

When in doubt, read the SKILL.md of the relevant skill before improvising. Skills are the contract; this file is the orchestration glue.
