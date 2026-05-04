---
name: course-validator
version: 1.0
description: Deep validation of course content (coverage, voice, drafts, cross-references)
inputs:
  - course_root: folder_path, optional, defaults to current working directory
  - report_format: enum (terminal, markdown, json), default terminal
  - severity_threshold: enum (info, warning, error), default warning
  - check_voice: boolean, default true
  - check_coverage: boolean, default true
outputs:
  - Terminal report by default, or docs/validation-report.md if report_format is markdown, or docs/validation-report.json if json
dependencies:
  - course-spec-builder
  - repo-bootstrap
phase: 5
status: ready
subject_neutral: true
audience_neutral: true
---

# Course Validator

Comprehensive validation of a course before sync. Goes far deeper than the basic `bes validate` Phase 2.5 stand-in.

## When to Use

Run this skill before `bes sync` to catch problems that would otherwise show up only on the platform or, worse, in front of students. Specifically run it:

- After completing a unit (validates the unit's content quality)
- Before pushing to a test platform (catches structural issues)
- Before pushing to production (catches everything)
- Periodically during long authoring projects (catches drift early)

The Phase 2.5 `bes validate` is fine for everyday quick checks. This skill is the deep version. It takes longer to run but produces a much more useful report.

## Steps

1. Find the course root (cwd by default, walk up to find course-config.yaml).

2. Run all the Phase 2.5 checks first (file structure, frontmatter, quiz YAML basics). If those fail, stop and report. Deep checks below are only meaningful after structure is sound.

3. Read all course content into memory:
   - course-config.yaml
   - course-description.md (extract Pitch, Specs, Outcomes)
   - voice-guide.md (extract specific rules, banned phrases, sample passages)
   - Every unit.yaml (titles, learning outcomes)
   - Every lesson markdown (frontmatter + body)
   - Every knowledge-check.yaml (questions)
   - exam/course-final.yaml (the bank)

4. Run the deep checks:

### 4a. Coverage Check

For every course-level learning outcome (from course-description.md):
- Is at least one lesson tagged with this outcome (in frontmatter `learning_outcome` field)?
- Is at least one knowledge check question tagged with this outcome?
- Is at least one final assessment question tagged with this outcome?

Report any uncovered outcomes as errors.

For every unit-level learning outcome (from unit.yaml):
- Is the unit's content actually covering it? Check lesson titles and frontmatter for matching keywords.
- Is the unit's knowledge check testing it?

Report mismatches as warnings.

For every lesson:
- Does the lesson have at least one knowledge check question that references it (`lesson_ref` field)?
- Does the lesson appear in at least one final assessment question's `lesson_ref`?

Report orphan lessons as warnings.

### 4b. Voice Consistency Check

For every lesson's body content, check against voice-guide.md rules:

- **Banned phrases:** scan the body for any phrase explicitly forbidden in voice-guide.md (e.g., "in today's fast-paced world", em dashes, exclamation points if banned, etc.). Each banned phrase found is an error.
- **Sentence length:** if voice-guide.md specifies max sentence length, count sentences over the limit. More than 5 percent of sentences over the limit is a warning. More than 15 percent is an error.
- **Reading level:** estimate via Flesch-Kincaid or similar. If voice-guide.md specifies a target reading level, lessons that drift more than 2 grade levels above target are warnings.
- **Tone consistency:** check for tone signals (formality of pronouns, presence of contractions, etc.) against the voice guide. Significant drift is a warning.

For each rule violation, report:
- Which lesson
- The exact offending text
- The rule it violates
- Suggested fix

This is the most LLM-judgment-heavy part of the skill, so it produces fuzzy assessments. Tag each as info, warning, or error based on confidence.

### 4c. Draft Status Check

Scan every lesson and quiz for `draft: true`:
- Lessons with `draft: true`: list them as info-level. Drafts are expected before sync; this just reminds the author.
- Knowledge check files with `draft: true` at the quiz level: list as info.
- course-final.yaml with `draft: true`: list as info.

If `--severity_threshold: error` and any drafts exist, fail validation. Otherwise just report counts.

### 4d. Cross-Reference Check

For every quiz question:
- Does its `lesson_ref` field match an actual lesson file in the unit?
- Does its `learning_outcome_ref` field match an actual outcome in the course?

For every lesson's `learning_outcome` frontmatter field:
- Does it match an outcome in either course-description.md or unit.yaml?

Report mismatches as errors.

### 4e. Word Count Compliance

For every lesson:
- Read the target_word_count from frontmatter or default (800)
- Count actual body word count (excluding frontmatter and headers)
- Flag lessons more than 30 percent above or below target as warnings

### 4f. Question Quality Heuristics

For every quiz question:
- **Choice differentiation:** are the wrong answers obviously wrong (single-word answers, opposite-of-correct) or plausibly wrong (similar tone, similar length)? Obvious-wrong choices are warnings.
- **Explanation length:** explanations under 30 words are likely too thin. Warning.
- **Trick questions:** look for grammar tricks (negation, double negation, "all of the above except"). These are warnings; voice guide may explicitly allow or forbid them.
- **Question length:** questions over 100 words are likely too long. Warning.

### 4g. External Link and Image Check

For every lesson body:
- Find all markdown links: `[text](url)`
- For external links (http or https): all must be HTTPS. HTTP links are warnings.
- For image references `![alt](path)`: if path is relative, the file must exist in the course repo. If path is absolute or external, must be HTTPS.

Report broken or insecure links as errors.

5. Aggregate results:
   - Count by severity (info, warning, error)
   - Group by check type and by lesson/quiz file
   - Calculate an overall pass/fail based on `severity_threshold`

6. Write the report:
   - **Terminal format (default):** Rich-formatted output with colors, grouped by severity. Show summary first, then drill-down details.
   - **Markdown format:** Write to docs/validation-report.md. Same content but in a portable doc format.
   - **JSON format:** Write to docs/validation-report.json. Same content as a machine-readable structured object. Useful for CI integration later.

7. Return appropriate exit code:
   - 0 if no issues at or above severity_threshold
   - 1 if any errors at or above severity_threshold

## Output Format (Terminal)

```
COURSE VALIDATION REPORT
========================

Course: Sample Course
Path: /home/student/Code/sample-course
Date: 2026-05-04

SUMMARY
-------
Errors:    2
Warnings:  7
Info:      12

ERRORS
------
1. Coverage: Course-level outcome "Argue, with evidence, why a colony chose to remain loyal or to rebel by 1776" is not covered by any lesson.
   Suggested fix: Add a lesson that supports this outcome, or remove the outcome from course-description.md.

2. Cross-reference: Question u5-q12 references lesson_ref "08-late-stage-events.md" but that file does not exist in unit-05.
   Suggested fix: Update lesson_ref to a real lesson, or create the missing lesson.

WARNINGS
--------
3. Voice (unit-01/lessons/02-key-actors.md): Sentence 14 is 47 words long. Voice guide says max 30. Consider splitting.
   Offending text: "When the delegates met they had to consider not only the political implications but also..."
4. Word count: unit-02/lessons/03-major-events.md is 1450 words, target was 800. Consider trimming or splitting.
... [and so on]

INFO
----
12 lessons still have draft: true.
3 knowledge check files still have draft: true.
exam/course-final.yaml still has draft: true.

OVERALL: FAIL (2 errors at severity_threshold: warning)
```

## Output Format (Markdown)

A more polished version of the terminal output. Saved to `docs/validation-report.md`.

```markdown
# Validation Report: Sample Course

**Date:** 2026-05-04
**Severity threshold:** warning
**Result:** FAIL

## Summary

| Severity | Count |
|----------|-------|
| Errors | 2 |
| Warnings | 7 |
| Info | 12 |

## Errors

### 1. Coverage gap: outcome not addressed by any lesson

**Outcome:** "Argue, with evidence, why a colony chose to remain loyal or to rebel by 1776"

This outcome is listed in `course-description.md` but no lesson references it.

**Suggested fix:**
- Add a lesson supporting this outcome, or
- Remove this outcome from `course-description.md`.

### 2. Broken cross-reference

**Location:** `exam/course-final.yaml`, question `u5-q12`
**Field:** `lesson_ref: "08-late-stage-events.md"`
**Issue:** This file does not exist in `unit-05`.

**Suggested fix:** Update `lesson_ref` to a real lesson, or create the missing lesson.

## Warnings

[continues...]

## Info

- 12 lessons still have `draft: true`
- 3 knowledge check files still have `draft: true`
- `exam/course-final.yaml` still has `draft: true`

These are not blocking, but indicate content has not been reviewed yet.

## Overall

**FAIL** (2 errors at severity_threshold: warning)
```

## Examples

### Example 1: Healthy course passes validation

State: every outcome is covered, voice matches the guide, no broken refs, drafts are flagged as info.

Result: 0 errors, 0 warnings, 4 info items (4 drafts). Overall PASS. The author can sync.

### Example 2: Mid-development course

State: half the lessons drafted, no questions yet, voice is good where it exists.

Result: 0 errors, 6 warnings (uncovered outcomes), 8 info items (drafts). Overall PASS at default severity (errors only). FAIL at strict severity. The author knows they have work to do but the course is not actively broken.

### Example 3: Pre-launch validation

State: course is fully drafted, ready for first sync. Severity threshold strict.

Result: 0 errors. 1 warning (one lesson is 12% over target word count). 0 info (no drafts left, all reviewed). Overall PASS in strict mode. Ready to sync.

## Quality Checks

The validator is checking the course, but the validator itself can have bugs. Self-checks:

- The validator should never crash on incomplete content. Missing files, empty quizzes, etc. should produce informative messages, not stack traces.
- The validator should respect the voice guide. If the voice guide says "no em dashes," the validator flags em dashes. If the voice guide does not mention them, the validator does not.
- The validator should never modify course content. It only reads.

## Common Mistakes

- **Hardcoding voice rules.** The validator must read voice-guide.md for each course. A rule that "all courses ban em dashes" is wrong. Bill's voice guide bans them; another author's might not.

- **Crying wolf on coverage.** Not every learning outcome needs a dedicated lesson. Some are integrated across multiple lessons. The validator's coverage check should look for the outcome in any lesson's content, not just the frontmatter `learning_outcome` field. Use both signals.

- **Voice judgment with too much confidence.** Voice consistency is fuzzy. Mark voice flags as warnings or info, rarely errors, unless the voice guide explicitly forbids the specific thing.

- **Missing the helpful explanation.** Every error and warning should include a suggested fix. "Sentence too long" without "consider splitting" is half a flag.

- **Performance.** A 200-question final assessment plus 30 lessons can take a few minutes to validate fully. Show progress so the user knows the validator is working, not stuck.

## Files in This Skill Folder

- `SKILL.md` (this file)
- `voice-checks-reference.md` (heuristics for common voice rules)
- `coverage-strategies.md` (different ways to verify outcome coverage)

## Changelog

### 1.0 (2026-05-04)
- Initial version
- All seven check types implemented (coverage, voice, drafts, cross-references, word count, question quality, links)
- Three output formats (terminal, markdown, JSON)
- Three severity levels (info, warning, error)
