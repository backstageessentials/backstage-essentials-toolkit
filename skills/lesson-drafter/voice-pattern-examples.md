# Voice Pattern Examples

Reference samples for the lesson-drafter skill. When the skill drafts a lesson, it reads the course's local voice-guide.md as the law. These examples are here as additional pattern-matching anchors for common voice families. The skill picks the closest family to the course's voice, then refines based on the local voice guide.

## Family 1: Adult Trade Training, Conversational Professional

Used by courses aimed at working adults learning a hands-on skill. Direct, no fluff, respects the reader's time and intelligence. Bill Larsen's Backstage Essentials voice fits here.

Sample, on professionalism:

> The call is the moment your reputation either gets built or broken. Vendor names a date. You answer like a professional or you don't. Professional means: yes or no, fast, no maybe-let-me-check-and-get-back-to-you unless you genuinely need to check something. If you have to check, you say what you're checking and when you'll know. Then you actually call back when you said you would. That's it. That's the whole skill.

Pattern notes:
- Lead with the bottom line ("The call is the moment...")
- Short sentences, no hedging
- Concrete examples ("vendor names a date") not abstract advice ("communicate effectively")
- Direct second person ("you")
- Light rhythm in the writing, not robotic
- No em dashes, no formal closings, no exclamation points

## Family 2: High School / Patient Explainer

Used by courses aimed at students 14-18, mixed ability levels. Patient, warm, defines every term clearly, builds confidence.

Sample, on mineral hardness:

> Here's a fact about minerals: some are softer than your fingernail, some are harder than steel. That difference matters because it tells you what the mineral is. The Mohs scale is just a list, 1 through 10, that ranks minerals by how hard they are. Talc is a 1. Diamond is a 10. Your fingernail is somewhere around 2.5. So if you can scratch a mineral with your fingernail, you know it's softer than 2.5.

Pattern notes:
- Clear opening fact, no jargon
- Defines the scale in one sentence
- Specific reference points (talc, diamond, fingernail)
- One concrete experiment the reader can imagine doing
- No condescension, no "you might wonder why"
- Short paragraphs

## Family 3: College Academic, Conversational

Used by undergraduate courses where students have some domain familiarity but the instructor still wants to be approachable. Less formal than a textbook, more rigorous than an explainer.

Sample, on supply and demand:

> Price is information. When the price of coffee goes up, that's not a problem you solve, it's a signal. The signal says: there is less coffee available than people want at the current price. Producers see the signal and grow more coffee. Consumers see it and switch to tea. Within a few months, the system rebalances. The whole machinery of markets is built on this kind of signaling. Learn to read the signals and you understand 80% of microeconomics.

Pattern notes:
- Opens with a thesis ("Price is information")
- Develops it with mechanism, not assertion
- Uses specific industry example (coffee, tea)
- Shows how the system rebalances over time
- Allows itself one big claim at the end ("80% of microeconomics") without hedging
- Paragraphs are longer than Family 1 or 2

## Family 4: Coaching / Performance

Used by courses on sports, music, or other physical performance. Direct, motivational without being phony, focused on what the body or team is doing.

Sample, on flag football coaching:

> Watch the eyes. The receiver always tells you where the ball is going if you know where to look. Most beginner defenders watch the quarterback's arm. The arm is the last thing to commit. The eyes commit two seconds earlier. If you train yourself to look at the quarterback's eyes for the snap, then track which receiver they look at next, you will pick off three balls a season that you would have missed. That's the difference between a defender who plays and one who sits.

Pattern notes:
- Imperative voice ("Watch the eyes")
- Body/action focus
- Specific tactical advice, not generic motivation
- Numerical claim grounded in real experience
- Stakes are clear (plays vs sits) without being dramatic

## Family 5: Reference / Documentation

Used by technical reference courses. Spare, precise, optimized for skimming. Less voice, more structure.

Sample, on Git commit messages:

> A commit message has two parts: a short subject line (50 characters max) and an optional longer body. The subject describes what the commit does, in present tense, without a period. The body explains why, if the why is not obvious from the subject. Write subjects that complete the sentence "If applied, this commit will...". Examples: "Add login form validation." Bad. "Add login form validation". Good (no period). "Fix bug". Bad (vague). "Fix off-by-one error in pagination". Good.

Pattern notes:
- Reads like reference, not prose
- Rules stated as rules
- Examples paired with anti-examples
- Skimmable
- Voice almost disappears, replaced by clarity

## How the Skill Picks a Family

When lesson-drafter runs, it does not literally choose a family. It reads the course's voice-guide.md and produces output matching it. These five families exist as reference patterns for common cases. If the course's voice guide closely matches one family, the lesson-drafter has a stronger pattern to lean on. If the voice guide is genuinely novel, the skill follows the voice guide directly.

## Adding More Families

When a new course establishes a new voice that doesn't fit any family above, add a sixth family here with sample passages. Over time, this file becomes a reference library of voices the toolkit has produced for.
