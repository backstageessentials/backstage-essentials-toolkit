---
name: lesson-drafter
version: 1.0
description: Draft a lesson markdown file in the course's voice, ready for human review
inputs:
  - unit_number: integer, required
  - lesson_topic: string, required (a sentence describing what the lesson covers)
  - learning_outcome: string, required (the specific outcome this lesson supports, in Bloom's verb form)
  - target_word_count: integer, default 800
  - target_minutes: integer, default 12 (estimated reading time)
  - lesson_order: integer, optional (default to next available position in the unit)
  - lesson_type: enum (text, video-script, hybrid), default text
outputs:
  - content/unit-NN-{slug}/lessons/NN-{lesson-slug}.md
dependencies:
  - course-spec-builder (course needs a spec)
  - repo-bootstrap (course needs the folder structure)
phase: 3
status: ready
subject_neutral: true
audience_neutral: true
---

# Lesson Drafter

Drafts a lesson markdown file based on a topic, learning outcome, and the course's local voice guide. The output is a draft for human review, never a final.

## When to Use

Run this skill any time you need a new lesson drafted. Run it before the lesson exists in `content/unit-NN-{slug}/lessons/`. The skill creates a new file. It does not modify existing lessons; for that, edit the file directly.

The skill respects the course's local voice guide. The same skill produces high school geology copy or adult trade training copy depending on which course it runs in.

Do NOT use this skill if:
- `voice-guide.md` has not been filled in yet (the skill needs voice instructions to produce anything coherent)
- `course-description.md` has not been filled in (the skill needs audience and outcome context)

## Steps

1. Verify required inputs:
   - `unit_number` is a positive integer
   - `lesson_topic` is a sentence, not a single word
   - `learning_outcome` uses a Bloom's-taxonomy upper-level verb (apply, demonstrate, evaluate, design, troubleshoot, recommend, defend, build, calibrate, diagnose). Reject weak verbs (understand, know, learn, be aware of). If the user passes a weak verb, suggest a strong replacement and ask them to confirm.

2. Find the course root by walking up from cwd until course-config.yaml is found.

3. Read `course-config.yaml`. Confirm the unit_number exists in the course (units field). If not, stop and tell the user.

4. Read `course-description.md`. Extract:
   - Audience summary (age range, education, domain background)
   - Reading level target
   - Course-level learning outcomes (so this lesson's outcome aligns with one of them)

5. Read `voice-guide.md`. Extract:
   - Audience and tone
   - Reading level
   - Voice personality details
   - Influences
   - Specific rules (especially "things never to do")
   - Sample passages
   - Format requirements (headers, sentence length, lesson structure)
   
   If voice-guide.md is unfilled or contains template placeholders, stop and tell the user the voice guide must be completed first.

6. Read the unit's `unit.yaml` to get unit title and learning outcomes context.

7. Read other lessons in the unit's `lessons/` folder if any exist, to understand:
   - What topics have been covered (avoid repetition)
   - What writing conventions the unit is using
   - What position number to use for the new lesson

8. Draft the lesson using all of the above context. The draft must:
   - Match the voice guide exactly (tone, reading level, sentence length rules, banned phrases)
   - Open with the bottom-line takeaway in 1 to 2 sentences
   - Develop the topic with concrete examples and physical analogies appropriate for the audience
   - Reference the learning outcome explicitly so the student knows what they should be able to do after
   - Include 1 to 3 short sections under H2 headings (no H1 inside the lesson body, the H1 is the title)
   - End with a one-sentence takeaway or transition
   - Stay within target_word_count plus or minus 20%

9. Consider whether a Mermaid diagram would help this lesson. A diagram earns
   its place when the lesson describes:
   - A process with branching decisions (flowchart)
   - An interaction between two or more parties over time (sequence)
   - A thing that lives in different states (state diagram)
   - A small set of related entities where the relationships matter (class diagram)

   If yes, include one Mermaid block at the appropriate spot in the lesson
   body, with a one-sentence intro line ending in a colon above it. Follow
   the patterns and syntax in `skills/diagram-builder/diagram-patterns.md`
   and `skills/diagram-builder/mermaid-syntax-reference.md`. Most lessons
   need zero or one diagram; do not force a diagram into a narrative or
   single-concept lesson. The diagram-builder skill can also be run later
   to add diagrams to existing lessons (`bes add-diagrams`), so when in
   doubt, leave it out and let the human decide.

10. Consider whether a MicroSim would teach a concept in this lesson better
    than text or a diagram. A MicroSim earns its place when the student
    learns by *manipulating*: clicking flashcards, dragging signal-flow
    chips, scrubbing a timeline, sliding values into a formula. If yes,
    do NOT generate the MicroSim here; the lesson-drafter does not write
    HTML widgets. Instead, mark the slot in the lesson markdown so the
    microsim-builder skill (Phase 7) can fill it in later:

    ```
    {{microsim: TODO type=flashcards purpose="Cycle through the four
    methods and recall when each fits."}}
    ```

    The `TODO` filename signals the slot is unfilled. The `type=` is one
    of `signal-flow`, `calculator`, `flashcards`, `decision-tree`,
    `timeline`, `matcher`, `formula`. The `purpose=` line is one
    sentence describing what the MicroSim should teach. Place the slot
    under the section where the concept lives, with one sentence of
    prose introducing it.

    Most lessons need zero MicroSims; one is the upper bound. When in
    doubt, leave the slot out and let the human decide later via
    `bes add-microsim`.

11. Write the lesson markdown file:
   - File path: `content/unit-NN-{unit-slug}/lessons/{lesson-order}-{topic-slug}.md`
   - Frontmatter at the top with title, order, type, duration_minutes
   - Body content as the drafted lesson

12. Show the user a summary:
    - Lesson title
    - File path created
    - Word count
    - Whether a diagram was included (and what type)
    - Whether a MicroSim slot was marked (and what type)
    - Suggested next step: read the draft, revise, then commit

## Output Format

A markdown file with this structure:

```markdown
---
title: "{Generated lesson title}"
order: {N}
type: text
duration_minutes: {target_minutes}
unit: {unit_number}
learning_outcome: "{the outcome this lesson supports}"
draft: true
---

# {Lesson Title}

{Bottom-line takeaway in 1 to 2 sentences. The reader should know after this paragraph what the lesson is about and why it matters.}

## {First major section}

{Body paragraphs. Concrete, in the course's voice, with physical examples and analogies appropriate for the audience.}

## {Second major section}

{More body content. Build on the first section, do not just restate it.}

{Optional: a one-sentence intro ending in a colon, followed by a Mermaid
diagram in a fenced ```mermaid``` block, when the section describes a
process, lifecycle, or interaction that prose cannot teach as cleanly.
See skills/diagram-builder/ for the patterns and syntax.}

## What this means for you

{One short paragraph reinforcing the learning outcome. The student leaves knowing what they should be able to do.}

{One-sentence transition or takeaway.}
```

The `draft: true` field in the frontmatter is a flag that the lesson has not yet been reviewed by a human. The course-validator skill (Phase 5) flags any lessons with `draft: true` as needing review before sync.

## Examples

### Example 1: Backstage Essentials, professionalism lesson

Inputs:
- unit_number: 1
- lesson_topic: "How to take a call from a vendor or production company"
- learning_outcome: "Demonstrate professional phone etiquette when receiving a call for crew work"
- target_word_count: 700

Voice context: Bill's adult trade training voice. Casual, direct, Feynman-influenced, no em dashes.

Output: A 700-word lesson titled something like "The Call: How to Take One." Opens with the bottom line ("The call is the moment your reputation either gets built or broken. Here's what good crew do."). Includes specific examples (vendor names a date, what to ask, how to confirm). Ends with a one-sentence takeaway about the next lesson.

### Example 2: High school geology, mineral identification lesson

Inputs:
- unit_number: 3
- lesson_topic: "Using the Mohs hardness scale to identify minerals"
- learning_outcome: "Apply the Mohs scale to rank an unknown mineral against reference samples"
- target_word_count: 600

Voice context: Patient explainer for 14 to 16 year olds, grade 9 reading level, clear definitions for every term.

Output: A 600-word lesson opening with the takeaway ("If you can scratch one mineral with another, the one doing the scratching is harder. That's the whole idea behind the Mohs scale."). Builds with simple physical experiments students can do. Ends with a transition to the next lesson on mineral classification.

## Quality Checks

Before declaring the lesson drafted, verify:

- The frontmatter has all required fields (title, order, type, duration_minutes, unit, learning_outcome, draft: true)
- The body matches the voice guide (skim for banned phrases, em dashes if forbidden, sentence length, etc.)
- The bottom line is in the first 1-2 sentences
- The lesson references its learning outcome
- Word count is within target_word_count plus or minus 20%
- No content from other courses leaked in
- No "TODO" or placeholder text in the body

## Common Mistakes

- **Writing in a generic voice instead of the course's voice.** The voice guide is the law. If the voice guide says "no em dashes," there are no em dashes. If the voice guide says "lead with the bottom line," the first sentence is the bottom line.

- **Writing about the topic instead of producing the outcome.** A lesson that just describes a topic does not teach. The lesson must show the student doing the outcome (apply, demonstrate, etc.) by the end.

- **Hedging.** Drafts that say "you might want to consider possibly thinking about" are not useful. Confident voice if the voice guide says confident voice.

- **Reusing examples across lessons.** If Lesson 1 uses a particular example, Lesson 2 should not use the same example unless it is genuinely the best illustration. Read existing lessons in the unit before drafting.

- **Drift in length.** A 1500-word draft when target was 700 is not a longer draft, it is a different lesson. Stay in range.

- **Mixing audiences.** A lesson aimed at 14-year-olds should not have college-level vocabulary because the lesson-drafter "could." The voice guide is the constraint.

- **Forcing a diagram into every lesson.** Most lessons do not need one. A diagram earns its place by teaching a structure prose cannot teach as cleanly: branching decisions, cross-actor exchanges, lifecycles. A bulleted list dressed up as boxes-and-arrows is worse than the original list. If unsure, leave it out and let the diagram-builder skill decide later.

- **Writing the MicroSim, not just marking the slot.** The lesson-drafter never writes HTML widgets. A MicroSim slot is a `{{microsim: TODO type=... purpose="..."}}` placeholder. The microsim-builder skill (run later) reads the slot, picks the right template, customizes the labels in the lesson's voice, and fills in the iframe. The lesson-drafter's job ends at marking the slot.

## Files in This Skill Folder

- `SKILL.md` (this file)
- `voice-pattern-examples.md` (sample passages from different voices to help calibrate, since this skill needs to handle many)
- `lesson-shape-templates.md` (different structures for text vs video-script vs hybrid lessons)

## Changelog

### 1.0 (2026-05-04)
- Initial version
- Reads voice-guide.md and course-description.md from the course repo
- Outputs draft lessons with `draft: true` flag in frontmatter

### 1.1 (2026-05-04)
- Phase 6: lesson-drafter now considers whether a Mermaid diagram fits the
  lesson and embeds one inline when it does. References the diagram-builder
  skill's patterns and syntax. Most lessons still get zero diagrams; this
  step exists so the easy wins do not have to wait for a separate
  diagram-builder pass.

### 1.2 (2026-05-04)
- Phase 7: lesson-drafter now considers whether a MicroSim would teach a
  concept better by manipulation, and if so, marks a `{{microsim: TODO
  type=... purpose=...}}` slot in the lesson body. The lesson-drafter does
  not write the MicroSim itself; that is the microsim-builder skill's
  job, run later via `bes add-microsim`.
