# MicroSim Patterns

Reference for picking the right template for a lesson. Each pattern shows the lesson shape that calls for it, what the student does inside the MicroSim, and what would be wrong with picking a different template.

The default order of preference:

1. **flashcards** for memorization-style content (terms, methods, definitions)
2. **decision-tree** for branching rules the student should walk through
3. **calculator** for numeric inputs that produce a numeric output
4. **formula** for relationships where the student should see *why* an output changes
5. **signal-flow** for stage-and-input-and-output shapes
6. **timeline** for processes that unfold over time
7. **matcher** for paired-association content

When in doubt, pick the simpler template. Flashcards beat decision-tree if the lesson is really about recall. Calculator beats formula if the lesson does not actually teach the formula's structure.

## Flashcards

Use when the lesson teaches a set of terms, methods, or facts the student should be able to recall.

The student does:
- Click a card to flip it
- Mark "got it" or "missed"
- Cycle through the deck and see a final score

Best fits:
- Method-selection lessons (which brewing method, which fixture, which connector)
- Vocabulary or terminology lessons across any subject (literary devices, scientific terms, historical names, foreign-language words)
- Identification lessons (this is a sonnet vs a haiku; this is sedimentary vs igneous; this is a stagehand-grade SM58 vs a U87)

When it does not fit:
- Lessons about decisions, not facts (use decision-tree)
- Lessons about how a relationship changes (use formula or calculator)

## Decision Tree

Use when the lesson teaches a branching rule the student should be able to walk down.

The student does:
- Read a question
- Click a yes/no or multi-choice answer
- Land on the next question or a terminal recommendation

Best fits:
- "Should I lift this solo or call a team?" style decisions
- Compliance flows ("when do I escalate?")
- Troubleshooting flows ("the gear is not working, walk through the checks")
- Argumentative or interpretive flows ("you are a delegate at the Continental Congress, what do you argue?")
- Source-evaluation flows ("is this primary or secondary, and how do you know?")
- Ethical decision frameworks ("what does this case study call for?")

When it does not fit:
- Lessons where the answer depends on a numeric value (use calculator)
- Lessons where the student needs to memorize the steps, not just walk them (use flashcards)

## Calculator

Use when the lesson teaches a numeric relationship the student should be able to plug values into.

The student does:
- Move sliders or type numbers into inputs
- See a computed output update live
- Often: see a status message change ("under capacity" / "over capacity")

Best fits:
- Electrical load math (fixture watts, breaker amps)
- Audio gain-staging math
- Cost calculations, finance problems (compound interest, loan payments)
- Chemistry concentration and stoichiometry
- Physics motion problems (speed, acceleration, kinetic energy)
- Population math (how many soldiers can a colony field, how many votes are needed)
- Speed/time/distance problems

When it does not fit:
- The lesson is about *why* the formula works, not *what value* it produces (use formula instead)
- The lesson has no numeric output (use decision-tree)

## Formula

Use when the lesson teaches a formula and the student should see how each variable affects the output, not just compute one answer.

The student does:
- Move a slider for each variable
- Watch the output number AND a small plot or visualization update
- Build intuition for which variable matters most

Best fits:
- Physics relationships (F = ma, V = IR)
- Audio relationships (gain = log10(power))
- Geometry (area, volume as a function of dimensions)

When it does not fit:
- The lesson is about plugging in one number and reading the output (use calculator)
- The lesson has no underlying formula (use signal-flow or matcher)

The difference between calculator and formula: calculator is a tool ("here's the answer"). Formula is an explainer ("here's how the answer changes").

## Signal Flow

Use when the lesson teaches how a signal or material moves through stages with inputs and outputs.

The student does:
- Drag input elements to slots
- See the path light up as the signal propagates
- Spot where the signal would break

Best fits:
- Audio signal flow (mic to stagebox to console to mains)
- Lighting signal flow (console to node to fixture)
- How a bill becomes a law (chamber to committee to floor to other chamber to president)
- Neural pathway lessons (sensory neuron through interneuron to motor neuron)
- Water cycle, supply chain, manufacturing pipeline
- Material flow in any "input goes through stages and comes out as output" lesson

When it does not fit:
- The lesson teaches a decision, not a path (use decision-tree)
- The lesson teaches a numeric formula (use calculator or formula)

## Timeline

Use when the lesson teaches a process that unfolds over time and the student should see what is happening at each moment.

The student does:
- Drag a scrubber or click stage buttons
- See the state of the world at that moment
- Spot transitions that change the state

Best fits:
- Show day phases (load-in, sound check, doors, show, strike)
- Lifecycles (the bean from roasted to brewed; cell division phases; star formation)
- Historical chronologies (the war years, the Reconstruction era, the build-up to a revolution)
- Narrative arcs in literature
- Multi-step procedures where the student should see each step's effect

When it does not fit:
- The lesson is a static decision rule (use decision-tree)
- The lesson teaches a numeric output (use calculator)

The difference between timeline and signal-flow: timeline is one stage moving through time. Signal-flow is one signal moving through stages.

## Matcher

Use when the lesson teaches a set of paired associations (term to definition, fixture to use case, role to responsibility).

The student does:
- Drag a card from the left column
- Drop it on its match in the right column
- Get feedback (match correct, match incorrect, snap back)

Best fits:
- Vocabulary lessons where definitions and terms can be confused
- Role-and-responsibility lessons (FOH does X, monitor world does Y; or executive branch does X, legislative branch does Y)
- Tool-and-job lessons (this gear is for this purpose)
- Literary devices to definitions, historical figures to events, organelles to functions
- Authors to works, primary sources to time periods, treaties to outcomes

When it does not fit:
- The lesson is recall-only with no pairing structure (use flashcards)
- The associations are part of a larger process (use timeline)

## Choosing Between Close Matches

| If the content is about... | Pick |
|----------------------------|------|
| Recalling N facts | flashcards |
| Walking down a decision | decision-tree |
| Computing one number | calculator |
| Understanding why a number changes | formula |
| A signal through stages | signal-flow |
| A stage through time | timeline |
| Pairs of associations | matcher |

When two templates fit equally, pick the simpler one. The lesson is the teacher; the MicroSim is the practice.

## Anti-Patterns

- **A MicroSim that just re-states the lesson.** A flashcard deck where each card is a section heading from the lesson teaches nothing. The cards should make the student do something the prose did not: practice, recall, apply.

- **A MicroSim with no failure mode.** If every input produces a "you got it" message, the student is not being challenged. A good MicroSim has wrong answers, edge cases, or values that visibly fail.

- **A MicroSim with twenty knobs.** Five sliders is the upper bound for usable. Past that, the student spends more time figuring out the UI than the concept. Trim by default.

- **A MicroSim that runs the lesson's whole arc.** One MicroSim, one focused practice. If the lesson covers three concepts, that is three MicroSims (and probably too many for one lesson).

- **Voice mismatch in UI labels.** A button labeled "Continue your learning journey" in a lesson whose voice guide calls for short, casual, direct prose. Or "Submit answer" in a course whose voice guide calls for formal academic register. The MicroSim feels grafted on. Match the voice guide every time.
