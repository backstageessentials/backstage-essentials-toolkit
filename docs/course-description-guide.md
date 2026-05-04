# Course Description Guide

A strong course description is the foundation. Every skill in the toolkit reads it. Lessons get drafted from it. Quizzes get written against it. The final assessment tests whether students learned what it promises. A vague description produces vague output across the whole course.

This doc walks through what makes a course description strong, what to include, and what to leave out. Borrowed in spirit from Dan McCreary's course-description-analyzer concept: the description is the contract.

## Where the Course Description Lives

Each course repo has a file at the root called `course-description.md`. The repo-bootstrap skill creates it as a template when you start a new course. You fill it in before any other content gets written.

Other skills read this file by reading the path stored in `course-config.yaml` under the field `course_description_path`. By default that is `./course-description.md`.

## The Three-Part Structure

Every course description has three parts, in order:

1. The Pitch (one paragraph)
2. The Specs (structured fields)
3. The Outcomes (what a student can do after finishing)

Get all three right and the skills downstream produce coherent content. Skip any of them and the output drifts.

## Part 1: The Pitch

One paragraph, 4 to 8 sentences. Covers:

- Who the course is for
- What problem it solves or what skill it teaches
- Why this course is the right way to learn it
- What makes it different from alternatives

Write the pitch as if you are speaking to a real person about whether they should buy the course. Specific beats vague.

Bad pitch:

> This course teaches the fundamentals of live event production. Students will learn essential skills used by industry professionals. Topics include audio, lighting, and stage management.

Good pitch:

> Backstage Essentials is for the new crew member who showed up to their first call and realized nobody is going to teach them anything on the floor. The course covers the actual job: how to take a call, how to load a truck without breaking equipment or yourself, how to read the room when the FOH engineer is stressed, how to walk a stage without dying. It is taught by working hands who have done this for years, not classroom instructors. Students who finish know enough to be hireable on real crews.

The bad version could describe any course on this topic. The good version could only be this course.

## Part 2: The Specs

Structured fields the skills can read directly. Keep these in a consistent format so other skills do not have to guess.

```yaml
course_specs:
  audience:
    age_range: "18 to 45"
    education_level: "high school or higher, no specific degree required"
    domain_background: "no live event experience required, some interest in entertainment or events helpful"
    geographic: "United States, English-speaking"
  prerequisites: "None. The course assumes you can read and follow instructions."
  duration:
    total_hours: 24
    pacing: "self-paced, recommended 4 to 6 weeks"
  format:
    delivery: "video lessons, written content, scenario-based knowledge checks"
    assessment: "knowledge check per unit, 200-question final assessment for course completion"
  pricing:
    model: "one-time purchase"
    target_price_usd: 247
  platform: "thinkific"
  language: "English"
  accessibility:
    closed_captions: true
    transcripts: true
    screen_reader_compatible: true
```

Fill in every field. If a field does not apply, write `not applicable` so future you knows you considered it. Skills will skip fields they do not need but will use everything you provide.

## Part 3: The Outcomes

Outcomes are what a student can do after finishing the course. Not what topics are covered, not what they will know, but what they can do.

Every outcome follows this shape:

> After completing this course, the student can [verb] [object] [under what conditions or to what standard].

The verb is the most important part. Strong verbs produce assessable outcomes. Weak verbs produce mush.

Strong verbs come from the upper levels of Bloom's taxonomy. Pick the verbs that fit your subject:

- **Technical and procedural courses** lean on Apply and Analyze: apply, demonstrate, calculate, build, calibrate, troubleshoot, diagnose, operate.
- **Analytical and interpretive courses** (history, literature, social sciences) lean on Analyze and Evaluate: analyze, compare, contrast, contextualize, interpret, attribute, evaluate, critique, argue, defend, weigh, recommend.
- **Creative and design courses** lean on Create: design, synthesize, compose, construct, develop.
- **K-12 introductory and language courses** legitimately mix in Remember-level verbs (identify, name, recall) when memorization is the actual learning goal. Use them deliberately, not as a fallback for weak outcomes.

Weak verbs to avoid: understand, know, learn, be aware of, appreciate, become familiar with. These are mental states, not observable outcomes, and produce no assessable test.

The conditions or standard part anchors the outcome to something testable.

Bad outcome (technical course):

> Students will understand audio signal flow.

Good outcome (technical course):

> After completing this course, the student can trace a signal from a microphone through a mixer to a powered speaker, identifying every gain stage and naming the most likely failure point at each stage.

The bad version cannot be tested. "Did the student understand it?" has no answer. The good version produces a clear test: hand the student a system, watch them trace it, count what they get right.

Bad outcome (history course):

> Students will appreciate the causes of the American Revolution.

Good outcome (history course):

> After completing this unit, the student can argue, with at least three pieces of primary-source evidence, why a given colony chose to remain loyal or to rebel by 1776.

Same structural rule applies. "Appreciate" is a feeling, not an observable outcome. "Argue with three pieces of evidence" produces a clear test: read what the student wrote, count the evidence, judge whether each piece is on point.

How many outcomes is right? Five to twelve for a course. Fewer than five is probably not enough scope for a real course. More than twelve is probably too much for a student to actually master.

Cluster outcomes by unit if you want, or list them as a flat list. Either works.

Example outcome list for an adult-trade-training course (Backstage Essentials, live event production):

```yaml
learning_outcomes:
  - "Demonstrate professional conduct on a real show floor: arriving prepared, communicating clearly, taking direction without ego."
  - "Identify and mitigate the most common site safety hazards before they cause injury."
  - "Make go or no go safety decisions under time pressure when a senior crew member is not available to consult."
  - "Load and unload a truck efficiently without damaging equipment or injuring crew."
  - "Trace an audio signal end to end and isolate the most likely failure point at each gain stage."
  - "Set up a basic lighting rig for a small event including patching, focus, and cable management."
  - "Hang and align a video projection screen and adjust keystone for a clean image."
  - "Run a smooth load-in for a small event from arrival through doors."
  - "Manage a breakout room turnover between sessions including AV reset and basic troubleshooting."
  - "Strike and pack a show floor in a way that protects equipment and respects the warehouse."
  - "Navigate hierarchy, communication norms, and unspoken rules well enough to be invited back for the next call."
```

Example outcome list for a high school history course (US History, American Revolution unit):

```yaml
learning_outcomes:
  - "Compare colonial life before and after the Seven Years War, citing at least three changes British policy introduced after 1763."
  - "Interpret the colonial response to the Stamp Act, the Townshend Acts, and the Tea Act using primary sources from at least two perspectives."
  - "Argue, with evidence, why a given colony chose to remain loyal or to rebel by 1776."
  - "Contextualize the events at Lexington, Concord, and Bunker Hill within the broader breakdown of British colonial authority."
  - "Evaluate the strategic significance of Saratoga and Yorktown, weighing the role of diplomacy alongside the role of arms."
  - "Synthesize a short argument identifying the single most important cause of American independence and defending the choice against at least one alternative."
```

Example outcome list for an undergraduate science course (introductory geology):

```yaml
learning_outcomes:
  - "Apply the Mohs scale to rank an unknown mineral against reference samples."
  - "Compare igneous, sedimentary, and metamorphic rock formation in terms of source, process, and identifying features."
  - "Interpret a stratigraphic column to reconstruct a sequence of geological events."
  - "Evaluate competing hypotheses for a regional landscape feature using field evidence."
  - "Calculate the rate of plate motion from radiometric and paleomagnetic data."
  - "Diagnose the most likely formation history of a hand sample given hardness, streak, cleavage, and texture."
```

Same toolkit, three different subjects, three different verb mixes. The course's voice guide and the audience drive which verbs are right; the toolkit does not assume.

## What to Leave Out of the Course Description

Things that do NOT belong in the description:

- Lesson-level detail. The lessons themselves are written later. The description sets scope, not contents.
- Marketing fluff. "World-class instructors," "industry-leading curriculum," "transformative experience." These are not falsifiable. They produce nothing the skills can act on.
- Hedge words. "Comprehensive yet accessible," "rigorous but approachable." Pick one.
- The author's biography. Goes in a separate `about.md` if needed, not in the course description.
- Pricing rationale. Just the price, not the justification for the price.

## Iterating on the Description

The first version of your course description is almost never the final version. Workflow:

1. Write a first draft. Time-box it. 30 minutes.
2. Show it to two or three people in your target audience. Ask: "Would you buy this? If yes, what convinced you? If no, what is missing or unclear?"
3. Revise based on feedback.
4. Run the (future) course-description-analyzer skill against it for a quality score and specific suggestions.
5. Once you have a description that scores well and gets nods from real audience members, commit it and move to building the course.

Do not start writing lessons from a weak description. Lessons drafted against a vague description will be vague. You will rewrite them later. Cheaper to fix the description first.

## Common Pitfalls

**Trying to please everyone.** A course description that promises something for beginners, intermediate, and advanced learners pleases nobody. Pick one audience, exclude the others by name if needed.

**Promising more than you can deliver.** If your course is 24 hours of content, do not promise mastery of a topic that takes 200 hours to master. Set the right expectation. "After this course, you can take entry-level crew jobs" is true and useful. "After this course, you can run any major tour" is false and damaging.

**Outcomes that are actually topics.** "Students will learn about microphones" is a topic, not an outcome. "Students can match a microphone to an instrument or voice based on its frequency response, polar pattern, and durability needs" is an outcome.

**Outcomes too detailed for course scope.** Each outcome should be testable in a reasonable assessment. If an outcome would take 50 questions to fully assess, split it into smaller outcomes.

**Description does not match the actual course.** Sometimes the course evolves during authoring and the description gets stale. Update the description when the course changes. Do not let them drift.

## When the Description Is Done

You know the description is done when:

- A friendly stranger could read it and explain back to you who the course is for and what they will be able to do after finishing.
- The skills downstream produce content that actually fits the description without you having to keep correcting them.
- You can defend every outcome in front of a domain expert who might say "that is not actually achievable in 24 hours." (If you cannot defend it, fix it.)

A course description is short. It is not the longest part of building a course. But it is the part that determines whether the rest of the work pays off, so spend the time on it before spending time on lessons.
