---
name: final-assessment-builder
version: 1.0
description: Generate the comprehensive course final assessment question bank
inputs:
  - total_questions: integer, default 200
  - questions_per_attempt: integer, default 100
  - distribution: enum (proportional, equal, custom), default proportional
  - custom_distribution: dict, optional (only used when distribution is custom)
  - difficulty_mix: string, default "30 percent easy, 50 percent medium, 20 percent hard"
  - assessment_style: enum (scenario, recall, applied-calculation, mixed), default scenario
outputs:
  - exam/course-final.yaml (replaces existing content)
dependencies:
  - course-spec-builder
  - repo-bootstrap
  - lesson-drafter (lessons must exist)
  - quiz-builder (knowledge checks should exist first; reuse patterns)
phase: 3
status: ready
subject_neutral: true
audience_neutral: true
---

# Final Assessment Builder

Generates the comprehensive end-of-course final assessment. Produces a question bank (default 200 questions) that randomly samples a subset (default 100) on each attempt. The student passes the course by passing the final.

## When to Use

Run this skill once a course is mostly built: lessons are drafted across all units, knowledge checks are populated. The final assessment is the last major content piece.

It is fine to run this skill more than once. Each run regenerates the question bank from scratch. To preserve hand-edited questions, edit the YAML file directly rather than re-running the skill.

## Steps

1. Verify required files exist:
   - `course-config.yaml`, `course-description.md`, `voice-guide.md`
   - `exam/course-final.yaml` (placeholder is fine)
   - All units in `content/` have at least one lesson and a knowledge-check.yaml

2. Read context:
   - From `course-description.md`: audience, all course-level learning outcomes, completion threshold
   - From `voice-guide.md`: voice rules
   - From every `unit.yaml`: unit titles and unit-level outcomes
   - From every lesson markdown: lesson titles and content
   - From every existing `knowledge-check.yaml`: existing question patterns to align with (do not duplicate)

3. Plan the question distribution. Use the `distribution` parameter:
   - **proportional:** questions per unit proportional to (lesson count + content length). A unit with 6 lessons gets more questions than a unit with 1 lesson.
   - **equal:** total_questions divided evenly across units.
   - **custom:** use the `custom_distribution` dict, e.g., `{1: 30, 2: 40, 3: 50, 4: 30, 5: 30, 6: 20}` for total 200.

4. Plan the difficulty distribution within each unit. Default 30 percent easy, 50 percent medium, 20 percent hard. Apply per unit so every unit gets a mix, not just the bank as a whole.

5. For each unit, generate the assigned number of questions:
   - Cover every lesson at least once (no lesson goes untested)
   - Cover every learning outcome at least once
   - Mix question patterns: scenario, comparative, applied calculation as appropriate for the subject
   - Question IDs use format `u{unit_number}-q{NN}` where NN is a two-digit number unique within the unit

6. Critical: avoid duplicating knowledge check questions. The final assessment is broader and goes deeper. Knowledge checks are for unit progression. The final assessment is for course completion.

7. Verify quality before writing:
   - All question IDs unique across the entire bank
   - Total question count matches `total_questions`
   - Every unit represented per the distribution
   - Every lesson tested at least once
   - Every learning outcome tested at least once
   - Difficulty mix roughly matches the requested distribution
   - Voice matches voice guide
   - No two questions are near-duplicates

8. Write the output to `exam/course-final.yaml`:
   - Replace existing questions
   - Preserve `name`, `total_questions_in_bank`, `questions_per_attempt`, `pass_threshold`, `randomize` fields if present
   - Update `total_questions_in_bank` to match what was generated
   - Add `draft: true` flag at the top level

9. Show the user:
   - Total questions generated
   - Distribution by unit
   - Distribution by difficulty
   - Distribution by question pattern
   - Path to the file
   - Suggested next step: review carefully (this is high-stakes content), revise, then commit and sync

## Output Format

```yaml
final_assessment:
  name: "{COURSE_NAME} Course Final"
  total_questions_in_bank: 200
  questions_per_attempt: 100
  pass_threshold: 0.75
  randomize: true
  draft: true
  questions:
    - id: u1-q01
      unit: 1
      difficulty: easy
      type: scenario
      lesson_ref: "01-introduction.md"
      learning_outcome_ref: "Demonstrate professional conduct on a real show floor"
      question: |
        It is your first day on a crew. The senior tech is busy
        and the rest of the crew is unloading a truck. What do you do?
      choices:
        - text: "Wait near the senior tech for instructions."
          correct: false
        - text: "Join the unloading crew and ask what to grab."
          correct: true
        - text: "Take a break until someone tells you to start."
          correct: false
      explanation: |
        Joining the working crew shows initiative and lets you
        contribute immediately. The senior tech will pull you for
        specific tasks when ready. Waiting passively wastes time.
        Taking a break on day one signals you do not understand
        the urgency of show prep.

    - id: u3-q15
      unit: 3
      difficulty: hard
      type: applied-calculation
      lesson_ref: "04-cable-runs.md"
      learning_outcome_ref: "Trace an audio signal end to end"
      question: |
        A 4 ohm load is connected via 75 feet of 14 AWG cable.
        Current is 5 amps. What is the approximate voltage drop?
      choices:
        - text: "0.5 volts"
          correct: false
        - text: "1.9 volts"
          correct: true
        - text: "3.8 volts"
          correct: false
        - text: "7.6 volts"
          correct: false
      explanation: |
        14 AWG cable has approximately 0.0025 ohms per foot.
        75 feet times 2 (round trip) is 150 feet, total resistance
        0.375 ohms. Voltage drop equals current times resistance,
        5 amps times 0.375 ohms equals about 1.9 volts.
```

## Examples

### Example 1: Backstage Essentials, default settings

Inputs: total_questions 200, distribution proportional, difficulty_mix default, scenario style.

The course has 6 units. Proportional distribution might give: Unit 1: 35, Unit 2: 30, Unit 3: 40, Unit 4: 35, Unit 5: 35, Unit 6: 25 (total 200). Each unit gets a 30-50-20 difficulty mix. All scenario based.

### Example 2: High school geology, mixed style

Inputs: total_questions 100, distribution equal, mixed style, "30 easy 50 medium 20 hard".

The course has 8 units. Equal distribution: 12 or 13 questions per unit, totaling 100. Mix of scenario and recall. Difficulty mix applied per unit.

### Example 3: Coaching course, custom distribution

Inputs: total_questions 150, distribution custom, custom_distribution {1: 20, 2: 25, 3: 30, 4: 30, 5: 25, 6: 20}, scenario style, "20 easy 60 medium 20 hard".

Six units, custom counts. All scenario. Slightly harder mix because the audience is experienced coaches.

## Quality Checks

Before writing the file:

- All IDs unique across the bank
- Total matches input target
- Per-unit counts match the distribution plan
- Every lesson has at least one question
- Every learning outcome has at least one question
- Difficulty mix is within 5 percentage points of target per unit
- No question text appears identical or near-identical in two questions
- No question references content that does not exist in the lessons
- The bank is large enough that questions_per_attempt random sampling produces meaningful variety. If total_questions is less than 1.5 times questions_per_attempt, warn the user.

## Common Mistakes

- **Duplicating knowledge check questions in the final.** Knowledge checks test unit progression. The final tests course completion. Different roles, different questions. The final goes broader and deeper.

- **Uneven coverage.** A 200-question final where Unit 6 has only 5 questions and Unit 1 has 50 is broken. Distribute thoughtfully.

- **Question count too low for randomization.** If total_questions equals questions_per_attempt, every student sees every question. Defeats the purpose of randomization. Total should be at least 1.5x and ideally 2x the per-attempt count.

- **Hard questions are not the same as long questions.** A hard question tests subtle judgment, not the student's reading endurance. Keep wording crisp.

- **Questions about content the lessons did not teach.** The final cannot test material that was never covered. If you want to add a topic, write a lesson first.

- **Voice drift.** A 200-question bank takes a while to generate. Voice can slip. Spot-check every 25 questions to make sure the voice is still on.

## Files in This Skill Folder

- `SKILL.md` (this file)
- `distribution-strategies.md` (how to think about question distribution across units)

## Changelog

### 1.0 (2026-05-04)
- Initial version
- Reads voice guide, course description, all lessons, all knowledge checks for context
- Outputs course-final.yaml with `draft: true` flag
