# Voice Checks Reference

Heuristics the course-validator skill uses when checking voice consistency. These are starting patterns, not absolute rules. The course's local voice-guide.md always wins.

## Banned Phrase Detection

The voice guide may list specific phrases the author wants flagged. Common patterns:

| Pattern | Why Authors Ban It |
|---------|---------------------|
| "in today's fast-paced world" | Empty filler |
| "at the end of the day" | Empty filler |
| "needless to say" | Self-contradicting |
| "low-hanging fruit" | Tired metaphor |
| "as we all know" | Condescending or wrong |
| "very unique" | Logical error (unique is binary) |
| Em dash (—) | Stylistic choice for some authors |
| En dash (–) | Stylistic choice for some authors |
| Hyphen as separator (e.g., "thing - other thing") | Stylistic choice |
| Exclamation points | Stylistic choice; cheapen prose |
| All-caps words for emphasis | Stylistic choice |

The validator scans every lesson body for these. Each match is reported with location and the surrounding sentence so the author can fix it.

## Sentence Length

Most voice guides specify a maximum sentence length. Common targets:

| Audience | Typical Max |
|----------|-------------|
| Grade 6 to 8 | 20 words |
| Grade 9 to 11 | 25 words |
| Grade 12 to college | 30 words |
| Adult professional | 30 words |
| Graduate / specialist | 40 words |

The validator counts sentences over the limit. Report breakdown:
- Over 5% of sentences over limit: warning
- Over 15% of sentences over limit: error

Suggested fix in the report: "Sentence X is N words long. Consider splitting at the comma or breaking the clause into a separate sentence."

## Reading Level Estimation

Use the Flesch-Kincaid Grade Level formula:

`grade_level = 0.39 * (total_words / total_sentences) + 11.8 * (total_syllables / total_words) - 15.59`

For each lesson, calculate the grade level of the body content. Compare to the voice guide's target.

| Drift | Severity |
|-------|----------|
| Within 1 grade of target | OK |
| 1 to 2 grades above target | Info |
| 2 to 3 grades above target | Warning |
| More than 3 grades above target | Error |

Note: most courses err toward higher grade levels (more complex prose) than the target. Drift below the target is unusual but also worth flagging.

## Tone Heuristics

Tone is fuzzy. The validator checks crude signals:

**Formality signals:**
- Contractions: "you're," "don't," "it's"
- Casual: "yeah," "okay," "stuff"
- Formal: "shall," "thereby," "moreover," "furthermore"
- Pronouns: "I," "you," "we" (informal); "one" (formal)

**Voice family signals:**
- Adult trade training: high contractions, second person, short sentences
- High school explainer: low contractions, simple vocabulary, encouraging phrases
- Academic: low contractions, third person or impersonal, longer sentences
- Coaching: imperative voice, second person, urgency

If the voice guide specifies a target voice family, the validator counts these signals and flags significant drift.

## Voice Sample Comparison

If the voice guide includes sample passages, the validator can compare lessons against them. This is the highest-quality check but the slowest.

Heuristic: extract sentence patterns from the voice samples (average length, vocabulary distribution, presence of contractions, sentence types). Compare each lesson's metrics. Lessons that fall significantly outside the voice samples' metric ranges are flagged.

This is not a stylometric proof, just a sanity check. The validator marks these as info or warning, never error, since false positives are common.

## What the Validator Does Not Check

These are explicitly out of scope:

- Subjective quality of writing ("is this lesson good")
- Factual accuracy of content (the validator does not know the subject matter)
- Engagement or pacing (subjective)
- Technical accuracy of code samples or formulas (the validator is not a domain expert)

Those checks remain the human reviewer's job. The validator catches mechanical and structural issues, freeing the reviewer to focus on substance.
