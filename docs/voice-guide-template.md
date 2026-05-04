# Voice Guide Template

This is a template. Copy it into your course repo as `voice-guide.md` and fill in the sections. The lesson-drafter skill reads your course's voice-guide.md at run time, so the same skill produces high school geology copy or adult trade training copy depending on which course it is running in.

## How to Use This Template

1. Copy this file from the toolkit into your course repo as `voice-guide.md`
2. Fill in every section honestly. If a section does not apply to your course, write "not applicable" rather than leaving it blank, so future you knows you considered it.
3. Show the filled-in voice guide to a few people in your target audience and ask if it sounds right.
4. Commit the voice guide before drafting any lessons.

A voice guide is a contract. Every lesson the skill drafts will follow it. Every reviewer should hold drafts to it. Every later course in a series should reference it for consistency.

---

# [Your Course Name] Voice Guide

## Audience

Who is reading this course? Be specific. Generic answers like "adults" or "students" are not enough. The skill needs to know enough to make voice decisions.

Specify:

- Age range
- Education level (high school, undergraduate, graduate, professional, no formal education assumed)
- Domain background (beginner, some experience, working professional)
- Reading context (at a desk taking notes, on a phone during a commute, in a workshop with grease on their hands)
- What they hope to gain (certification, skill, hobby enjoyment, job)

Example for an adult-trade-training course (Backstage Essentials, live event production):

> Adults, 18 to 45, high school education or higher, no live event experience required. They are working their first crew jobs or hoping to. They read on phones during downtime between shows or on laptops at home in the evening. They want to be hireable on real crews, not just learn theory.

Example for a high school history course:

> Students, 14 to 17, in a US history elective. Mixed reading levels but most are at grade 9 to 11. They read in class, on a Chromebook, during a 50-minute period, between two other subjects. They are not specialists. They want to pass the unit assessment and find the material interesting enough to keep paying attention. They respond to narrative structure and vivid scenes; they do not respond to abstract theory or textbook prose.

Example for an undergraduate seminar:

> Undergraduates in a 200-level course, ages 19 to 22, with at least one prior college course in the discipline. They read at home, in advance of a discussion-based class. They expect to be challenged with primary sources and competing arguments. They are comfortable with academic register, but not with jargon for its own sake.

## Tone

Pick the tone that fits your audience. Tone is the emotional register the writing carries. Some examples:

- Formal academic (textbook for a college course)
- Conversational professional (industry training for adults)
- Friendly mentor (entry-level skills course for beginners)
- Direct coach (sports coaching, performance training)
- Patient explainer (course teaching kids or true beginners)
- Peer to peer (course aimed at experienced people learning a new tool)

Pick one as the primary tone. You can note secondary tones for specific contexts (for example, "primary tone is conversational professional, but use formal academic when defining technical terms").

Specify:

- Primary tone
- Any secondary tones and when to use them
- Tone things to avoid (lecturing, condescending, overly chummy, etc.)

## Reading Level

What grade or reading level should the prose be aimed at?

For reference:

- Grade 6 to 8: short sentences, common words, no jargon without explanation. Suitable for younger audiences or beginners in any field.
- Grade 9 to 11: longer sentences allowed, mid-level vocabulary, some technical terms with context. Most adult trade training fits here.
- Grade 12 to college: complex sentences, full technical vocabulary, assumes domain familiarity. Most college courses fit here.
- Graduate and beyond: dense prose, specialist vocabulary, assumes advanced background.

Pick a target. The lesson-drafter skill will calibrate sentence length and word choice to match.

Specify:

- Target reading level
- Maximum sentence length (rough guide: at most 30 words for general audiences, at most 20 for younger or beginner audiences)
- How much jargon is allowed and when terms must be defined

## Voice Personality

Beyond tone and reading level, every voice has a personality. Some questions to answer:

- Should the writing have a sense of humor? What kind? (Dry, playful, self-deprecating, none.)
- Should it admit uncertainty out loud, or always sound confident?
- Should it use analogies and metaphors? What kinds? (Physical, abstract, pop culture, sports.)
- Should it use first person ("I"), second person ("you"), third person, or a mix?
- Should it be formal or casual? Contractions or no contractions? Slang allowed or not?
- Should it use lists and bullet points heavily, or favor flowing prose?

Example for a Backstage Essentials course:

> Casual, direct, conversational. Lead with the bottom line, then explain the mechanism. Use physical concrete analogies (lifting a box, running a cable, walking a stage). Admit uncertainty when it exists. Real-time self-corrections are fine. Light humor in service of memory, never at the audience's expense. First and second person. Contractions allowed. No slang specific to subcultures the reader may not be in.

## Influences

Are there writers, speakers, or styles you want the voice to draw from? List them. The skill can reference these patterns.

Examples:

- Richard Feynman's Lectures on Physics (clarity, mechanism, real-time thinking out loud)
- The MIT OpenCourseWare lecture style (rigorous, structured)
- The 37signals blog (direct, opinionated, prose-heavy)
- Anthony Bourdain's writing (sensory, in the room, no romanticizing)
- Brene Brown's books (warm, honest, vulnerable)
- The Wirecutter (helpful, recommendation-driven, plain prose)

For each influence, write one sentence on what specifically you want from it. "I want Feynman's clarity but not his classroom-lecture format" is more useful than just "Feynman."

## Specific Rules

Things you always or never want in the writing. The lesson-drafter skill respects these as hard rules.

Examples:

- No em dashes, en dashes, or hyphens used as separators
- No exclamation points except when quoting someone
- No bullet point lists in the body of a lesson (only in summary sections)
- Every lesson ends with a one-sentence takeaway
- Every technical term gets defined the first time it appears in a lesson
- No second-person condescension ("you might think X, but actually Y" is allowed; "many beginners get this wrong" is not)

Add as many specific rules as you want. The more rules, the more consistent the output, but at some point you constrain the skill so much it cannot write anything natural. Aim for 5 to 15 rules.

## Audience Sensitivities

Anything specific to your audience that the writing should respect. Examples:

- Industry-specific safety: a lesson about working at heights should not joke about falling
- Cultural awareness: a course aimed at international audiences should avoid US-centric idioms
- Trauma awareness: a course on emergency response should handle injury and death respectfully
- Accessibility: a course taught to people with disabilities should avoid metaphors that assume able-bodiedness

If your audience has no special sensitivities to flag, write "no special sensitivities."

## Sample Passages

Provide two or three short sample passages in your target voice. These are the most important part of the voice guide. The skill reads them and pattern-matches.

Each sample is 100 to 300 words. Pick passages on different topics so the skill sees voice consistency across subject matter, not just one topic's vocabulary.

Tip: write the samples yourself rather than borrowing from other writers, even if borrowed samples sound right. The skill is going to imitate these. You want it imitating you, not someone else.

Example, sample 1, on a procedural topic:

> [Insert your sample here. 100 to 300 words. Picks a real topic from your course and writes a paragraph of teaching prose in the target voice.]

Example, sample 2, on an explanatory topic:

> [Insert another sample here. Different topic, same voice.]

Example, sample 3, on an opinion or recommendation:

> [Insert a third sample. Topic where you make a recommendation or take a position.]

## What to Avoid

The mirror image of the voice samples. Things that should not appear in your course's writing.

Pick three to five common voice failure modes for your audience and call them out:

- Overly formal academic phrasing when the audience is professionals in the field
- Empty filler ("In today's fast-paced world..." style openers)
- Hedging that softens every claim ("might possibly perhaps")
- Self-aggrandizing voice ("As a leading expert in...")
- Over-bulleting (bullets where prose would work better)

Add specific examples of phrases or patterns you do not want to see. The skill will avoid them.

## Format Requirements

Beyond voice, are there formatting rules every lesson follows?

- Lesson length (target word count, hard maximum)
- Section structure (introduction, learning objectives, body, summary, etc.)
- Visual elements (when to use tables, when to use code blocks, when to use callouts)
- Heading levels (H1 for lesson title only, H2 for major sections, etc.)

Specify all the format rules here. The skill applies them automatically.

## Final Check

Before you commit this voice guide, read it yourself out loud. If a section sounds vague or contradictory, fix it. If a section sounds too restrictive to write naturally, loosen it.

The voice guide is a living document. Update it after the first few lessons drafted with this skill. Patterns you missed will become obvious. Add them, rerun the lesson-drafter on a few sample topics, see if the voice is closer.

When the voice guide produces drafts you only need to edit lightly, you have it right.
