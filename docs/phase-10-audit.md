# Phase 10 Audit Report: Subject Neutrality

**Date:** 2026-05-04
**Scope:** Every skill, command, example, and doc in the toolkit
**Reference:** `docs/Backstage_Essentials_Toolkit_Phase10_SubjectNeutrality.docx`

The toolkit's stated architectural decision: subject neutral, audience neutral, multi platform. Voice is per course, not toolkit baked. The audit found that the decision was true in spirit but leaked in detail. Stagehand vocabulary, an adult-trade-training register, and a verb list weighted toward technical skills had crept into the canonical reference docs and the per-course CLAUDE.md template. This report documents what was found and what was changed.

## Summary by Severity

| Category | High | Medium | Low | Total findings |
|---|---|---|---|---|
| Hardcoded references | 11 | 13 | 8 | 32 |
| Examples need a second domain | 3 | 1 | 0 | 4 |
| Voice assumptions baked in | 1 | 3 | 1 | 5 |
| Default verb / pattern coverage | 4 | 3 | 0 | 7 |
| Audience assumptions | 1 | 3 | 2 | 6 |
| **Total** | **20** | **23** | **11** | **54** |

The 20 high-severity findings would have either blocked a non-trade course outright or pushed a non-trade course author into an off-voice register without recourse. They are all addressed in this commit. The 23 medium-severity findings were partially addressed in this commit and partially deferred (see Open items). The 11 low-severity findings are cosmetic and were left unchanged where they sit alongside paired non-trade examples.

## Files Changed in This Audit

```
CLAUDE.md
bes/commands/new_lesson.py
docs/course-description-guide.md
docs/voice-guide-template.md
skills/course-spec-builder/templates/base-build-spec.md
skills/course-validator/SKILL.md
skills/course-validator/coverage-strategies.md
skills/diagram-builder/diagram-patterns.md
skills/diagram-builder/mermaid-syntax-reference.md
skills/lesson-drafter/SKILL.md
skills/microsim-builder/SKILL.md
skills/microsim-builder/microsim-patterns.md
skills/microsim-builder/simulation-types-reference.md
skills/quiz-builder/bloom-verbs-reference.md
skills/quiz-builder/question-patterns.md
skills/repo-bootstrap/templates/course-claude.template.md
docs/phase-10-audit.md (new)
```

## Highest-Leverage Fixes (Top 6)

These six fixes had the broadest reach because they sit in templates or canonical references that every future course inherits.

### 1. Per-course CLAUDE.md template

**File:** `skills/repo-bootstrap/templates/course-claude.template.md`

The Standing Voice Rules section asserted "Casual, direct, Feynman influenced voice" and "Hyphens in compound words (load in, sound check, FOH engineer) are fine" as defaults that drop into every new course. A K-12 history or formal academic course would inherit a working-tech register before its author wrote a single line of voice-guide.md.

**Fix:** Renamed the section to "Defaults If voice-guide.md Is Unfinished," removed the trade examples and the Feynman line, added an explicit note that K-12, undergraduate, formal-academic, and other audiences should override the defaults via voice-guide.md.

### 2. MicroSim canonical Customize blocks

**File:** `skills/microsim-builder/simulation-types-reference.md`

Five of the seven templates led with a trade-specific Customize block (`signal-flow-visualizer` was audio signal flow; `circuit-load-calculator` was a 20A circuit with watts and amps; `timeline-scrubber` was Show Day; `drag-and-drop-matcher` was XLR / NL4 / TRS; `formula-explorer` was voltage drop). The skill imitates whatever lands first.

**Fix:** Each of those five templates now leads with a subject-neutral Customize block (generic input/output IDs, generic stage names, generic variables and a placeholder formula), followed by 2-4 worked examples covering history, biology, civics, finance, the live-event tech course, and the coffee sample. Same structural shape, no canonical bias toward one domain.

### 3. Bloom verb suggestion lists across four files

**Files:** `skills/quiz-builder/bloom-verbs-reference.md`, `skills/lesson-drafter/SKILL.md`, `bes/commands/new_lesson.py`, `docs/course-description-guide.md`

Every author-facing verb list led with `apply, demonstrate, evaluate, design, troubleshoot, recommend, defend, build, calibrate, diagnose`. Seven of those ten are technical or trade leaning. Historical, analytical, and interpretive verbs (`compare, contrast, contextualize, interpret, attribute, argue, weigh, synthesize, critique`) were absent from the headline list.

**Fix:** Expanded each list to span Apply, Analyze, Evaluate, and Create level verbs grouped by subject family. Added an explicit note that K-12 introductory and language courses legitimately use Remember-level verbs (identify, name, recall) when memorization is the actual goal. The CLI prompt in `bes new-lesson` now shows verbs grouped by Bloom level rather than as one trade-leaning short list.

### 4. quiz-builder/question-patterns.md

**File:** `skills/quiz-builder/question-patterns.md`

Four of the five question patterns (Scenario, Applied Calculation, Comparative, Multi-Step Scenario) had only trade-domain worked examples. A history or literature course author looking for a comparative question template would find an audio mixing scenario.

**Fix:** Paired the Comparative pattern with a humanities worked example (two historians offering competing causal arguments). Added a Pattern Selection by Subject row for "Humanities / history / literature" that points to comparative + interpretive scenario. Followed with an explicit note that the toolkit relies on the same scenario and comparative templates regardless of subject; only the content of the scenarios changes.

### 5. diagram-builder canonical Class Diagram and Linear Pipeline examples

**Files:** `skills/diagram-builder/diagram-patterns.md`, `skills/diagram-builder/mermaid-syntax-reference.md`

The canonical Class Diagram example was a live-audio system (Mic / Stagebox / FOHConsole / Mains). The canonical Linear Pipeline was Load-In to Strike. Both files said things like "Most live-event signal-flow uses, plain --> is enough." That framing assumed the toolkit's primary audience is live event tech.

**Fix:** The canonical Class Diagram example is now the three branches of the US federal government (Legislature / Executive / Judiciary), with the live-audio example included as a second worked example. The canonical Linear Pipeline is now "how a bill becomes a law," with show-day as a second worked example. Removed the "Most live-event signal-flow uses" framing.

### 6. base-build-spec.md visual_aids YAML

**File:** `skills/course-spec-builder/templates/base-build-spec.md`

The visual_aids YAML example referenced specific lesson filenames from the live-event course (`03-lifting-without-hurting-yourself.md`, `02-ppe-what-to-wear-when.md`). Every new course's build spec inherits this template, so the trade lesson filenames would surface in the build spec of any course built with the toolkit until the author overwrites them.

**Fix:** Replaced the visual_aids example with subject-neutral lesson filenames (`02-key-events.md`, `03-major-stages.md`) and purposes ("Decision flow the student should walk through," "Linear pipeline showing the stages of the process or period"). Added a note clarifying that the filenames are placeholders.

## Medium-Severity Fixes (Selected)

These were addressed in the same commit because they cluster naturally with the high-severity work.

### MicroSim "peer-to-peer working-tech voice" framing

`skills/microsim-builder/SKILL.md` and `skills/microsim-builder/microsim-patterns.md` referred to "peer-to-peer working-tech voice" as the contrast point for off-voice UI text. That phrasing reads as if working-tech voice is the toolkit's assumed norm and any other voice is a deviation. Reworded both to refer to "the course's voice guide" as the universal contrast point, with examples spanning casual-direct and formal-academic registers.

### Course validator examples

`skills/course-validator/SKILL.md` and `skills/course-validator/coverage-strategies.md` used Backstage Essentials as the canonical course in their sample reports and matrices ("Course: Backstage Essentials," "Demonstrate professional conduct on a real show floor," "Trace an audio signal end to end"). The sample reports now use a generic course name and history-leaning sample outcomes, with the trade examples present alongside as second illustrations where useful.

### Voice guide template

`docs/voice-guide-template.md` showed exactly one example audience (an adult-trade-training audience). A K-12 or undergraduate author had no model. Added two more example audience blocks: a high school US history class and an undergraduate seminar.

### Course description guide bad/good outcome

`docs/course-description-guide.md` showed one bad/good outcome pair (audio signal flow). Added a parallel bad/good pair from a history course (appreciate causes of the Revolution vs. argue with three pieces of evidence why a colony rebelled).

### MicroSim Best fits bullets

`skills/microsim-builder/microsim-patterns.md` had Best fits bullets that were trade leaning for every template. Each Best fits list now includes at least one humanities or science bullet (literary devices, historical figures, organelles, ethical frameworks, narrative arcs, population math, neural pathways, etc.).

## Open Items

These low-severity findings were left unchanged in this commit because they sit alongside paired non-trade examples already and cosmetic fixes would not change behavior:

- `examples/backstage-essentials-walkthrough.md`: a TODO stub. Not flagged as a problem because it is clearly a placeholder.
- `examples/backstage-essentials-reference/`: a frozen reference of the original course's hand-written build spec. Per the audit instructions, this stays.
- `skills/lesson-drafter/voice-pattern-examples.md`: lists five voice families, one of which is named for Bill Larsen's voice. This is correct because the file's purpose is to show the toolkit handles many voices.
- `skills/repo-bootstrap/SKILL.md` Example 1 (Backstage Essentials course): paired with a high school geology and a sound mixing example. Acceptable.
- `skills/lesson-drafter/SKILL.md` Example 1 (Backstage Essentials professionalism lesson): paired with a high school geology example. Acceptable.

## Changes Not Made

A few audit findings were intentionally left in place:

- The toolkit-root `CLAUDE.md` now flags its voice rules as Bill's personal toolkit defaults. The defaults themselves (no em dashes, bottom-line first, plain text questions, default to trim) are kept because they are Bill's standing rule; the audit's recommended fix was to reframe rather than remove, and that is what was done. The audit did note that the casual / Feynman / peer-to-peer language was specifically out of place at this layer; that is what got removed.
- The Backstage Essentials live-event course remains the toolkit's first reference implementation and is referenced in `examples/` and in worked examples in skill files. Per the audit instructions, the audit did not require removing it; only adding alongside it.

## Validation Plan

Phase 10 Part 2 was originally scoped to build a US History sample course exercising every toolkit feature, with the goal of catching any audit miss. Bill skipped Part 2 on review of this audit, judging that the structural fixes covered the surface area Part 2 would have stressed: a sample course would have re-surfaced the per-course CLAUDE.md template (fixed), the headline Bloom verb list (fixed), the canonical MicroSim Customize blocks (fixed), the canonical diagram examples (fixed), and the build-spec visual_aids placeholders (fixed). With no remaining surface to stress, building a sample course was deemed unnecessary cost.

If a real non-trade course is built later and surfaces a new finding, this audit will be amended.

## Authoring Note

Bill's standing rule against em dashes, en dashes, and hyphens used as separators in prose was honored throughout this commit, including in this audit report.
