# Lesson Shape Templates

The lesson-drafter skill produces lessons in three shapes depending on the `lesson_type` input. This file is a reference for what each shape looks like.

## Shape 1: Text Lesson

The default. A markdown lesson the student reads. Best for explanatory content, conceptual material, or step-by-step procedures that don't need video.

```markdown
---
title: "{Lesson Title}"
order: {N}
type: text
duration_minutes: {target_minutes}
unit: {unit_number}
learning_outcome: "{outcome}"
draft: true
---

# {Lesson Title}

{Bottom-line takeaway, 1 to 2 sentences. The reader should know after this paragraph what the lesson is about and why it matters.}

## {First major section}

{Body paragraphs. Concrete examples, in the course's voice.}

## {Second major section}

{Build on the first section. Add depth, not repetition.}

## What this means for you

{One short paragraph reinforcing the learning outcome. The student leaves knowing what they should be able to do.}

{One-sentence transition or takeaway.}
```

Word count: typically 500 to 1500 depending on target.

## Shape 2: Video Script

A script the instructor or narrator reads on camera. Voice is more conversational than text because it's meant to be spoken. Includes optional cues for the camera or editor.

```markdown
---
title: "{Lesson Title}"
order: {N}
type: video-script
duration_minutes: {target_minutes}
unit: {unit_number}
learning_outcome: "{outcome}"
draft: true
---

# {Lesson Title}

**Estimated runtime:** {duration_minutes} minutes
**Production notes:** {any specific shooting or editing notes}

---

**[INTRO]**

{Opening line, spoken to camera. Bottom line, conversational.}

**[MAIN POINT 1]**

{Spoken paragraph. Shorter sentences than written prose. Read it out loud to test.}

**[B-ROLL CUE]**

(If relevant: a note for the editor about visuals to layer over this section.)

**[MAIN POINT 2]**

{Continue the script. Use natural transitions like "So here's the thing..." or "Now watch this..." that work spoken.}

**[OUTRO]**

{One-sentence wrap. Transition to the next lesson if appropriate.}

---
```

Word count: scale to roughly 130-150 words per minute of speech (typical conversational pace). A 5-minute video script is around 700 words.

## Shape 3: Hybrid

A combination: text content with embedded video clips, interactive elements, or downloadable resources. Most flexible. Used when the topic genuinely benefits from multiple media.

```markdown
---
title: "{Lesson Title}"
order: {N}
type: hybrid
duration_minutes: {target_minutes}
unit: {unit_number}
learning_outcome: "{outcome}"
draft: true
embedded_media:
  - type: video
    src: "TBD"
    description: "{What the video shows}"
    estimated_duration: 3
  - type: download
    src: "TBD"
    description: "{What the download is, e.g., a checklist or template}"
---

# {Lesson Title}

{Bottom-line takeaway, 1 to 2 sentences.}

## {First section, text}

{Read this part. It sets up the video.}

> **VIDEO:** {Description of what the video covers, ~3 minutes. Insert real link here when produced.}

## {Section after the video}

{Build on what the video showed. Reinforce the key point.}

> **DOWNLOAD:** {Description of the resource. Insert real link when ready.}

## What this means for you

{Short paragraph reinforcing outcome.}
```

Word count target applies to the text portion only. Video and download are separate.

## When to Use Which Shape

| Use Case | Shape |
|----------|-------|
| Explaining a concept, principle, or set of facts | Text |
| Demonstrating a physical skill (knot tying, mixing audio, etc.) | Video Script |
| Walking through software steps where you need to see the screen | Video Script |
| Procedure with a checklist or template the student keeps | Hybrid |
| Topic with multiple sub-skills, some readable and some watchable | Hybrid |
| Most lessons in most courses | Text |

When in doubt, default to Text. It's the cheapest to produce, easiest to revise, and works on every platform. Add video later if a specific lesson genuinely benefits from it.

## Length Guidance

These are starting targets. Each course's voice guide may override.

- **Text lesson:** 500 to 1500 words. Aim for 800 by default.
- **Video script:** 130 to 150 words per intended minute of video. A 5-minute video is roughly 700 words. A 12-minute video is roughly 1700 words.
- **Hybrid:** text portion 300 to 800 words plus the video (separate). The text should stand alone as useful, with the video as enhancement.

If a target word count is given as input, the skill respects it. If not, the skill defaults based on the shape.
