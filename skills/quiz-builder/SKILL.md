---
name: quiz-builder
version: 1.0
description: Generate scenario-based knowledge check questions for a unit
inputs:
  - unit_number: integer, required
  - num_questions: integer, default 8
  - assessment_style: enum (scenario, recall, applied-calculation, mixed), default scenario
  - difficulty_mix: string, default "mostly medium with some easy and hard"
outputs:
  - content/unit-NN-{slug}/knowledge-check.yaml (replaces or appends)
dependencies:
  - course-spec-builder
  - repo-bootstrap
  - lesson-drafter (lessons must exist before writing the questions about them)
phase: 3
status: ready
subject_neutral: true
audience_neutral: true
---

# Quiz Builder

Generates knowledge check questions for a unit. Each question is scenario based by default, with two to four answer choices, one or more marked correct, plus an explanation.

## When to Use

After lessons in a unit are drafted (you can run lesson-drafter to create them), run quiz-builder to generate the unit's knowledge check questions. The questions test whether the student can apply what the lessons taught, not whether they can recite definitions.

Use this skill before sync. Knowledge check files start as empty placeholders from repo-bootstrap. The quiz-builder fills them in.

## Steps

1. Verify required files exist:
   - `course-config.yaml`, `course-description.md`, `voice-guide.md` at the course root
   - The unit folder `content/unit-NN-{slug}/` with at least one lesson in `lessons/`
   - `content/unit-NN-{slug}/knowledge-check.yaml` (placeholder is fine)

2. Read context:
   - From `course-description.md`: audience, learning outcomes
   - From `voice-guide.md`: voice rules, especially anything about question phrasing
   - From `unit.yaml`: unit title, unit-level outcomes
   - From every lesson markdown in the unit's `lessons/` folder: lesson titles and content

3. For each lesson in the unit, identify the testable points. A testable point is a specific judgment, application, or decision the lesson teaches the student to make.

4. Generate `num_questions` questions distributed across the lessons. Default distribution: roughly proportional to lesson length. Two to three questions per lesson is typical.

5. Each question follows this shape:
   - **id:** unique identifier in the format `u{unit_number}-kc-{NN}` where NN is a two-digit number
   - **type:** scenario (default), recall, applied-calculation, or mixed
   - **question:** the prompt, written in the course's voice
   - **choices:** two to four answer options, with `correct: true` or `correct: false` on each
   - **explanation:** why the correct answer is correct, what the wrong answers got wrong
   - **difficulty:** easy, medium, or hard
   - **lesson_ref:** which lesson the question is based on (helps with debugging and revision)

6. Apply the assessment_style:
   - **scenario:** every question is a realistic situation the student might face. The shape stays the same across subjects; only the situation changes. A research-writing course might ask "Your source's wording is distinctive but only the gist matters for your point. Quote, paraphrase, or summarize?"; a stagehand course might ask "You arrive at load-in and see X. What do you do?"
   - **recall:** straight knowledge check. "What is the Mohs hardness of quartz?" or "Which amendment guarantees freedom of the press?"
   - **applied-calculation:** numerical answer. "A 2.0 mol/L solution needs 0.50 mol of solute. How many mL do you measure?" or "If a speaker is 100 watts and the cable run is 50 feet, what gauge wire do you use?"
   - **mixed:** roughly half scenario, with the rest split between recall and applied-calculation

7. Apply the difficulty_mix:
   - "mostly medium with some easy and hard": about 60% medium, 20% easy, 20% hard
   - "all medium": all questions are medium
   - "increasing": easier questions first, harder questions last
   - Custom strings: parse them as English and apply common-sense distribution

8. Verify quality before writing:
   - No two questions have the same id
   - Every question has a question text, at least two choices, and at least one correct choice
   - Explanations are non-empty
   - No question tests something the lessons did not actually teach
   - Voice matches the voice guide

9. Write the output to `content/unit-NN-{slug}/knowledge-check.yaml`:
   - Replace any existing placeholder questions
   - Preserve the existing title and pass_threshold from the file if present
   - Add a `draft: true` flag at the quiz level so course-validator (Phase 5) can flag the file as needing review

10. Show the user a summary:
    - Number of questions generated
    - Distribution by lesson and difficulty
    - Path to the file
    - Suggested next step: review the questions, revise, then commit

## Output Format

```yaml
quiz:
  title: "Unit {N} Knowledge Check"
  pass_threshold: 0.7
  draft: true
  questions:
    - id: u1-kc-01
      type: scenario
      difficulty: medium
      lesson_ref: "01-introduction.md"
      question: |
        You arrive 10 minutes late to a 6 AM call.
        The crew chief is mid-brief. What do you do?
      choices:
        - text: "Apologize once and get to work without explanation."
          correct: true
        - text: "Explain that traffic was bad."
          correct: false
        - text: "Wait until the brief ends to introduce yourself."
          correct: false
      explanation: |
        Crew chiefs want execution, not excuses. A short apology
        and immediate action shows you understand the priority.
        Excuses waste time and signal that you do not get it.
        Waiting until the brief ends is also a missed signal.

    - id: u1-kc-02
      type: scenario
      difficulty: easy
      lesson_ref: "02-the-call.md"
      question: |
        A vendor calls and asks if you can work next Saturday.
        You are not sure of your schedule. What do you say?
      choices:
        - text: "Maybe, let me check and get back to you."
          correct: false
        - text: "I need to check my schedule and will call you back by 5 PM today."
          correct: true
        - text: "I can probably make it work."
          correct: false
      explanation: |
        Specific commitments build trust. A vague maybe makes the
        vendor uncertain whether to keep looking. Promising a
        callback by a specific time is professional and gives the
        vendor the information they need.
```

## Examples

### Example 1: Backstage Essentials Unit 1, default settings

Inputs: unit_number 1, num_questions 8, scenario style.

Output: 8 questions in `content/unit-01-{slug}/knowledge-check.yaml`. Each is a realistic situation a new crew member might face. Voice matches Bill's casual direct adult-trade-training tone.

### Example 2: High school geology Unit 3, recall mix

Inputs: unit_number 3, num_questions 10, mixed style.

Output: 10 questions, roughly half scenario ("You find a mineral that scratches glass but not quartz. What is its hardness range?") and half recall ("What is the Mohs hardness of feldspar?"). Voice matches the patient explainer style.

### Example 3: Coaching course Unit 4, increasing difficulty

Inputs: unit_number 4, num_questions 12, scenario style, "increasing" difficulty.

Output: 12 questions, easier ones first (basic recognition of a play), harder ones last (multi-decision scenario under time pressure). Voice matches the coaching family.

## Quality Checks

Before writing the file:

- All question IDs unique
- Every question has at least one correct choice
- No question references content that was not in the lessons
- Explanations explain why, not just restate the correct answer
- Voice matches the voice guide
- Difficulty distribution roughly matches the requested mix
- No two questions are near-duplicates of each other

## Common Mistakes

- **Testing recall when the assessment style is scenario.** A scenario question puts the student in a situation. "What is the definition of X" is recall, even if you wrap it in a fake scenario.

- **Plausible wrong answers.** The wrong choices should be wrong but tempting. If all wrong answers are obviously wrong, the question is too easy regardless of stated difficulty. Common pattern: one obviously wrong, two plausible-but-wrong, one correct.

- **Trick questions.** Questions where the trick is wordplay or grammar, not the actual subject matter, are bad questions. Test the skill, not the reading comprehension.

- **Explanations that just say "B is correct."** The explanation should teach something, even to a student who got the question right. Why was B correct? What principle does it illustrate? Why was A wrong?

- **Questions about content the lessons did not teach.** If a quiz question tests knowledge not covered in the lessons, the test is unfair. Always reference which lesson teaches each question's content.

- **All questions the same difficulty.** A unit with twelve identical-difficulty questions does not assess range. Hit easy, medium, and hard.

## Files in This Skill Folder

- `SKILL.md` (this file)
- `question-patterns.md` (common patterns for scenario questions, recall questions, etc.)
- `bloom-verbs-reference.md` (which Bloom's verbs map to which question types)

## Changelog

### 1.0 (2026-05-04)
- Initial version
- Reads voice guide and lessons to build context
- Outputs knowledge-check.yaml with `draft: true` flag
