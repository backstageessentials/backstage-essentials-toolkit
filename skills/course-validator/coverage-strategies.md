# Coverage Strategies

How the course-validator skill checks whether learning outcomes are actually covered by lessons and tested by questions. Coverage gaps are one of the most common content problems and one of the hardest to spot manually.

## The Three Coverage Layers

A learning outcome is "covered" when it appears in all three layers:

1. **Stated** in course-description.md or unit.yaml
2. **Taught** by at least one lesson
3. **Tested** by at least one quiz question

Missing any layer is a problem with a different fix:

- Stated but not taught: write a lesson, or remove the outcome
- Taught but not stated: add the outcome to the description, or rewrite the lesson to address a stated outcome
- Stated and taught but not tested: write a quiz question, or accept the gap if the outcome is small

## How to Detect Each Layer

### Stated (always exists)

Read course-description.md. Look for the "Outcomes" or "Learning Outcomes" section. Each item there is a course-level outcome.

Read every unit.yaml. The `learning_outcomes` field lists unit-level outcomes.

### Taught (look in two places)

Strongest signal: a lesson's frontmatter `learning_outcome` field matches the outcome text or a substring of it.

```yaml
---
title: "Diagnosing Wireless Mic Dropout"
learning_outcome: "Troubleshoot a dropped wireless mic during a live show"
---
```

Weaker but useful signal: the outcome's keywords appear in the lesson body.

If the outcome is "Troubleshoot a dropped wireless mic during a live show," the keywords are wireless, mic, dropout, live, show, troubleshoot. A lesson that uses these terms likely covers the outcome even if the frontmatter doesn't say so.

The validator should look at both signals. Frontmatter is authoritative; body content is supporting evidence.

### Tested (look in question fields)

Each quiz question has a `learning_outcome_ref` field:

```yaml
- id: u3-q05
  learning_outcome_ref: "Troubleshoot a dropped wireless mic during a live show"
  ...
```

Match question outcomes to course outcomes. A perfect string match is best. A substring or close match is acceptable but should produce a warning ("close match found, verify manually").

## Coverage Reporting

Report coverage as a matrix:

| Outcome | Stated | Taught | Tested | Status |
|---------|--------|--------|--------|--------|
| "Demonstrate professional conduct on a real show floor" | Yes | Lesson 1.1, 1.2 | Q u1-kc-01, u1-q05 | OK |
| "Trace an audio signal end to end" | Yes | (none) | Q u3-q12 | TAUGHT MISSING |
| "Calibrate a console for a specific room" | Yes | Lesson 4.3 | (none) | TESTED MISSING |
| "Network audio principles" | Yes | (none) | (none) | UNCOVERED |

Status values:

- **OK:** all three layers present
- **TAUGHT MISSING:** stated and tested but no lesson teaches it. Worst case: you're testing students on something they were never shown.
- **TESTED MISSING:** stated and taught but no question. Less critical, but the student gets no signal that the outcome matters.
- **UNCOVERED:** stated only. The outcome is in the course description but nothing implements it.
- **ORPHAN LESSON:** a lesson exists but its frontmatter outcome doesn't match any stated outcome. Either the lesson is off-topic or the description needs updating.
- **ORPHAN QUESTION:** a question references an outcome not in any description. Same fix.

## Fuzzy Matching

Outcome text rarely matches exactly between description, lesson frontmatter, and question fields. Normalize for comparison:

- Lowercase
- Strip punctuation
- Treat synonyms as matches: troubleshoot / diagnose / debug, demonstrate / show / perform, etc.
- Treat substrings as matches if 80% of the words overlap

Report exact matches as confident, fuzzy matches as "close match found" with both texts shown so the author can verify.

## Per-Unit Coverage

Repeat the same analysis for each unit individually. Unit-level outcomes are more granular and easier to check.

For each unit:
- Every unit-level outcome is covered by at least one lesson in that unit
- Every unit-level outcome is tested by at least one knowledge check question in that unit
- If a unit's lessons collectively don't address the unit's outcomes, the unit needs revision

## Course Final Coverage

Final assessment coverage is broader. Across the entire question bank:

- Every course-level outcome has at least one question
- Distribution: no outcome should have only 1 question if `total_questions` is 100+ (suggests the outcome is undervalued)
- High-stakes outcomes (flagged in voice-guide.md or course-description.md) should have 5+ questions each

## When to Be Strict vs Lenient

Default mode: warn on coverage gaps but don't fail. Authors are still drafting and gaps are expected mid-build.

Strict mode (`--severity_threshold: error`): fail on any uncovered outcome. Use before launch.

Even in strict mode, allow opt-out: a course-description.md can include an outcome with the field `coverage_optional: true` and the validator skips it. Used for stretch outcomes that the course aspires to but doesn't formally test.

## Limits of Automated Coverage Checking

The validator cannot verify the *quality* of coverage. A lesson can claim to teach an outcome without actually teaching it well. A question can claim to test an outcome without actually testing it. Mechanical match is the floor, not the ceiling.

The human reviewer still has to read the content and decide whether the coverage is real. The validator's job is to flag the obvious gaps, not to certify quality.
