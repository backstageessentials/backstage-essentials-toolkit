# Question Patterns

Reference for common question shapes the quiz-builder skill produces. Each pattern includes one example, plus notes on when it works.

## Scenario Question

The student is dropped into a realistic situation and must choose what to do.

```yaml
- id: u1-kc-04
  type: scenario
  difficulty: medium
  question: |
    You arrive at load-in. The senior tech is on the phone, the crew is
    standing around, and the truck door is open with gear inside. What
    do you do first?
  choices:
    - text: "Wait for the senior tech to give direction."
      correct: false
    - text: "Start unloading the truck."
      correct: false
    - text: "Find the production manager and ask where to start."
      correct: true
    - text: "Walk the room to see what the setup looks like."
      correct: false
  explanation: |
    The production manager is the source of authority on a show floor.
    Going to them first establishes that you understand chain of command
    and are ready to work. Waiting wastes time. Starting on your own
    risks moving the wrong gear. Walking the room is fine later, not first.
```

When it works:
- Adult trade training, real job situations
- Coaching, decision-making under pressure
- Any course where applied judgment is the outcome

When it doesn't:
- Pure factual recall (use recall pattern instead)
- Mathematical computation (use applied-calculation pattern instead)

## Recall Question

Tests whether the student remembers a specific fact, definition, or value.

```yaml
- id: u3-kc-02
  type: recall
  difficulty: easy
  question: |
    What is the Mohs hardness of quartz?
  choices:
    - text: "5"
      correct: false
    - text: "7"
      correct: true
    - text: "9"
      correct: false
  explanation: |
    Quartz is 7 on the Mohs scale. It scratches glass (Mohs 5.5) but
    is scratched by topaz (Mohs 8). Memorizing a few anchor points
    on the scale (talc 1, quartz 7, diamond 10) is enough to identify
    most common minerals.
```

When it works:
- High school courses with curriculum-driven facts
- Reference material where the student must memorize specific values
- Vocabulary or terminology checks

When it doesn't:
- Adult professional training (recall is rarely the goal there)
- Subjects where context matters more than specific values

## Applied Calculation

Student computes a specific numerical answer.

```yaml
- id: u2-kc-05
  type: applied-calculation
  difficulty: medium
  question: |
    A speaker is rated at 8 ohms and 100 watts continuous. You need
    to run 100 feet of cable from the amp. What gauge wire do you use
    to keep voltage drop under 5 percent?
  choices:
    - text: "12 AWG"
      correct: true
    - text: "14 AWG"
      correct: false
    - text: "16 AWG"
      correct: false
    - text: "18 AWG"
      correct: false
  explanation: |
    At 100 watts into 8 ohms, current is approximately 3.5 amps. Over
    100 feet, 12 AWG wire has roughly 0.16 ohms of resistance, which
    keeps voltage drop under 5 percent. Higher gauge numbers (16, 18)
    have more resistance and would lose too much power. 14 AWG is
    borderline acceptable for short runs but not ideal here.
```

When it works:
- Engineering, audio engineering, electrical work
- Any course with quantitative judgment
- Scientific reasoning courses

When it doesn't:
- Soft skills, communication, professionalism
- Courses where the student's tools include calculators or reference cards

## Comparative Question

Student compares two or more options and picks the better one.

```yaml
- id: u4-kc-07
  type: scenario
  difficulty: hard
  question: |
    You are mixing front of house for a small acoustic show. The room
    is reflective, the crowd is talking, and the lead vocalist is
    softer than the guitarist. You can adjust either: (a) the vocal
    channel EQ, (b) the vocal channel gain, (c) the mains output level.
    Which do you adjust first and why?
  choices:
    - text: "Vocal EQ to cut frequencies that compete with the guitar."
      correct: true
    - text: "Vocal gain to bring the vocal up."
      correct: false
    - text: "Mains output level to make everything louder."
      correct: false
  explanation: |
    EQ is the right first move. The problem is not loudness, it is
    intelligibility. The vocal is being masked by the guitar in
    overlapping frequency ranges. Raising vocal gain just adds more
    energy in the same frequencies, increasing feedback risk and
    making the mix muddier. Raising mains makes everything louder
    including the talking crowd. Cutting competing frequencies in
    the vocal channel lets the vocal sit clearly without adding
    overall energy.
```

When it works:
- Mid to upper-level courses
- Any subject where multiple valid options exist and judgment is the skill

When it doesn't:
- Beginner courses where students do not yet have the framework to compare
- Topics where there is one correct answer regardless of context

### Same Pattern, Humanities Subject

The comparative shape is not specific to technical content. A history or literature course uses the same shape:

```yaml
- id: u4-kc-08
  type: scenario
  difficulty: hard
  question: |
    Two historians explain the colonial decision to declare independence in
    1776. Historian A argues that the Coercive Acts of 1774 were the
    decisive cause, since they collapsed the consent of the governed.
    Historian B argues that the decisive cause was the Continental
    Congress, since it gave the colonies a coordinating body capable
    of independent action. Which argument better fits the evidence
    presented in the lesson, and why?
  choices:
    - text: "Historian A. Without the Coercive Acts, the Continental Congress would not have convened."
      correct: true
    - text: "Historian B. Coordination, not grievance, is what turned protest into a state."
      correct: false
    - text: "Both are equally strong; the question cannot be resolved from the evidence."
      correct: false
  explanation: |
    Historian A's argument is the stronger fit for the lesson's evidence.
    The Coercive Acts triggered the First Continental Congress as a
    direct response, so coordination followed grievance rather than
    preceding it. Historian B's claim is plausible in isolation but
    inverts the chronology shown in the primary sources. The "both
    equally strong" choice is a hedge that does not engage with the
    sequence the lesson establishes.
```

## Multi-Step Scenario

A scenario question that breaks into smaller pieces. Used sparingly because it gets long.

```yaml
- id: u5-kc-09
  type: scenario
  difficulty: hard
  question: |
    Show day. Doors open in 30 minutes. The lead vocalist's wireless
    mic just went dead. You have one spare wireless mic on a different
    frequency band, and one wired SM58. The vocalist is rehearsing on
    stage right now. What is the right move?
  choices:
    - text: "Swap to the spare wireless during rehearsal, troubleshoot the dead one off-stage during the show."
      correct: true
    - text: "Hand the vocalist the wired SM58 for now."
      correct: false
    - text: "Stop rehearsal to troubleshoot the dead wireless."
      correct: false
    - text: "Wait until rehearsal ends and decide then."
      correct: false
  explanation: |
    The right move is the one that keeps rehearsal moving and gets a
    working mic in the vocalist's hands fast. Swapping the spare during
    rehearsal accomplishes both. The wired SM58 limits stage movement
    and is a clear downgrade. Stopping rehearsal wastes the vocalist's
    warmup. Waiting until rehearsal ends gives you no time to fix the
    real problem before doors. Always handle the immediate need first,
    troubleshoot in parallel.
```

When it works:
- Advanced courses where students should handle multi-variable decisions
- Capstone questions in a final assessment
- Used sparingly: too many of these is exhausting

## Pattern Selection by Difficulty

| Difficulty | Recommended Pattern |
|------------|---------------------|
| Easy | Recall, simple scenario |
| Medium | Scenario, comparative, applied calculation |
| Hard | Multi-step scenario, comparative with all-plausible options |

## Pattern Selection by Subject

| Subject Type | Mostly Use |
|--------------|-----------|
| Trade / professional skills | Scenario |
| K-12 academic | Recall + simple scenario |
| College academic (sciences) | Comparative + applied calculation |
| Humanities / history / literature | Comparative + interpretive scenario (analyze a passage, evaluate competing arguments, attribute a source) |
| Coaching / performance | Scenario + multi-step scenario |
| Reference / documentation | Recall |

These are starting points. The voice guide and audience details from the course should refine them. A humanities course built with the toolkit relies on the same scenario and comparative templates as a trade course; the content of the scenarios differs, the question shape does not.
