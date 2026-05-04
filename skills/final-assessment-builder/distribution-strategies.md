# Distribution Strategies

How to think about distributing questions across units in a course final.

## Proportional (Default)

Each unit gets a question count proportional to its weight in the course. Weight is calculated from:

- Number of lessons in the unit
- Total word count of the lessons
- Number of distinct learning outcomes the unit covers

Heavier units (more content, more outcomes) get more questions. Lighter units get fewer.

Best for: most courses. The student studies more for heavy units, so the test reflects that.

Example, 200 questions, 6 units:
- Unit 1 (6 lessons, 5000 words, 4 outcomes): weight 100
- Unit 2 (4 lessons, 3500 words, 3 outcomes): weight 70
- Unit 3 (5 lessons, 4500 words, 4 outcomes): weight 90
- Unit 4 (5 lessons, 4000 words, 3 outcomes): weight 80
- Unit 5 (4 lessons, 3500 words, 3 outcomes): weight 70
- Unit 6 (3 lessons, 2500 words, 2 outcomes): weight 50

Total weight: 460. Questions per unit (rounded): 43, 30, 39, 35, 30, 22 = 199. Adjust by 1 to hit exactly 200.

## Equal

Each unit gets total_questions divided by unit count. Round any remainders to the larger units.

Best for: courses where all units are roughly equal in scope, or where the instructor wants the assessment to be visibly fair across units regardless of length.

Example, 200 questions, 6 units: 33 per unit, with 2 extras given to the largest two units.

## Custom

The author specifies a dict mapping unit number to question count.

Best for: courses with a specific assessment philosophy. Example: a coaching course where the foundational unit (Unit 1) gets disproportionately many questions because it underlies everything else.

```yaml
custom_distribution:
  1: 50  # heavy weight on foundations
  2: 30
  3: 30
  4: 30
  5: 30
  6: 30
```

Total: 200.

## Combining Distribution with Difficulty

Each strategy above just says how many questions per unit. Within each unit, apply the difficulty mix separately. So a unit with 40 questions and a 30-50-20 difficulty mix produces 12 easy, 20 medium, 8 hard.

## Special Considerations

### Single-question outcomes

Some learning outcomes are very narrow (single fact, single decision). Other outcomes are broad (multiple skills bundled together). Avoid forcing a 1-to-1 question-to-outcome mapping for narrow outcomes; one question is enough. Multiple-question coverage is for broad outcomes.

### Skipped lessons

If you decided not to write a lesson on a particular sub-topic, the final assessment should not test it. Always cross-reference what lessons exist before generating the bank.

### High-stakes outcomes

If an outcome is critical (safety-related, decision-under-pressure), give it disproportionately many questions even in proportional or equal distribution. Override the formula.

### Redundancy

A bank of 200 questions on 30 lessons means roughly 6-7 questions per lesson on average. Some lessons probably warrant 10. Some warrant 3. Use the lesson's importance, not just its size.
