---
name: microsim-builder
version: 1.0
description: Add an interactive MicroSim to a lesson by customizing one of the seven starter templates
inputs:
  - unit_number: integer, required
  - lesson_filename: string, required (e.g. "03-lifting-without-hurting-yourself.md")
  - template_type: enum (signal-flow, calculator, flashcards, decision-tree, timeline, matcher, formula), required
  - sim_filename: string, optional (default: derived from lesson filename and template type)
  - height: integer, default 400 (iframe height in pixels)
outputs:
  - content/unit-NN-{slug}/microsims/{sim_filename}.html (a self-contained HTML file)
  - Updates the lesson markdown by inserting a {{microsim: ...}} reference at the right spot
dependencies:
  - course-spec-builder
  - repo-bootstrap
  - lesson-drafter (the lesson must exist before a MicroSim can be attached)
  - diagram-builder (Phase 6 set up the iframe-style rendering pipeline this reuses)
phase: 7
status: ready
subject_neutral: true
audience_neutral: true
---

# MicroSim Builder

Generates a small interactive HTML widget (a MicroSim) for a lesson. The skill picks one of the seven starter templates, customizes the labels, ranges, and on-screen text to fit the lesson, saves the customized HTML alongside the lesson, and inserts a `{{microsim: ...}}` reference into the lesson markdown so the static-web preview renders it as an iframe.

## When to Use

After lessons in a unit are drafted, run microsim-builder to add an interactive widget where one teaches the concept better than prose or a diagram. The bar is even higher than for a Mermaid diagram: a MicroSim has to teach something the student does by manipulating, not just reading. Most lessons need zero MicroSims. A few earn one.

Use this skill before sync. The static-web preview generator copies the unit's `microsims/` folder alongside the rendered HTML so iframes resolve. A broken MicroSim renders as a 404 in the iframe; the lint pattern below catches this before writing.

Do NOT use this skill if:
- The lesson does not exist yet (run lesson-drafter first)
- `voice-guide.md` has not been filled in (the MicroSim's UI text follows voice rules)
- The lesson is purely narrative (a MicroSim with no manipulation to do is not a MicroSim)

## Verify Don't Think

This skill follows the verify-don't-think pattern. Every step has a concrete check. The skill never guesses. If a check fails, stop and tell the user, do not paper over it.

## Steps

1. Verify required files exist:
   - `course-config.yaml`, `course-description.md`, `voice-guide.md` at the course root
   - The unit folder `content/unit-NN-{slug}/`
   - The lesson markdown file at `content/unit-NN-{slug}/lessons/{lesson_filename}`
   - The template at `skills/microsim-builder/templates/{template_type}-{base_name}.html` (see Template Names below)

2. Read context, the same way diagram-builder and lesson-drafter do:
   - From `course-description.md`: audience, learning outcomes
   - From `voice-guide.md`: voice rules (especially anything about UI labels, button text, register)
   - From the lesson markdown: title, learning outcome, body content
   - From `unit.yaml`: unit title, unit-level outcomes

3. Verify the template fits the lesson. See `microsim-patterns.md` for the catalog. Hard rules:
   - **signal-flow**: lesson teaches how a signal or flow moves through stages with inputs and outputs
   - **calculator**: lesson teaches a numeric relationship the student should be able to plug values into
   - **flashcards**: lesson teaches a set of terms or facts the student should be able to recall
   - **decision-tree**: lesson teaches a branching decision rule the student should walk through
   - **timeline**: lesson teaches a process with stages over time the student should scrub through
   - **matcher**: lesson teaches a set of pairs (term to definition, fixture to use case) the student should be able to match
   - **formula**: lesson teaches a formula and the student should explore how variables affect output

   If the lesson does not fit any template, stop and tell the user. Do not force a fit.

4. Read the chosen template HTML file as a string. Templates live in `skills/microsim-builder/templates/`.

5. Customize the template. Each template has a `<!-- CUSTOMIZE -->` block at the top of `<script>` that contains a JavaScript object with the labels, ranges, and choices. The skill rewrites that object only. The rest of the template is untouched.

   For every string the skill writes into the customize block, apply the voice guide rules:
   - Same register as the lesson (peer-to-peer, formal, classroom, whatever the guide says)
   - Same banned phrases (no em dashes if forbidden, no marketing voice, etc.)
   - Same reading level
   - Short, action-oriented for button labels: "Reveal", "Next", "Reset". Long descriptive labels for context-setting text where it helps.

6. Write the lint check before saving:
   - The customized HTML parses as well-formed HTML (closing tags balanced, no broken JS)
   - The customize block is still well-formed JavaScript (run a quick string sanity check, see "Lint Pattern" below)
   - The required template fields are all present and non-empty
   - No `<!-- CUSTOMIZE` or `END CUSTOMIZE -->` markers leak into the output (the markers are inside a JS comment so they survive but should be confined to the script tag)

   If the lint fails, rewrite or stop. Never write a broken MicroSim.

7. Save the customized HTML to `content/unit-NN-{slug}/microsims/{sim_filename}.html`. Create the `microsims/` folder if it does not exist.

8. Insert the `{{microsim: ...}}` reference into the lesson markdown:
   - Pick the insertion point the same way diagram-builder picks a diagram spot: after the H2 (or H3) heading whose section is about the simulated concept, after the first paragraph of that section, never as the very first thing in the lesson, never inside the wrap section.
   - The line is just the directive on its own paragraph: `{{microsim: pick-a-method-flashcards.html height=420}}`
   - A one-sentence intro line ending in a colon goes above it, in the lesson's voice.

9. Set `draft: true` on the lesson's frontmatter if it is not already true, since the MicroSim counts as new draft content needing review.

10. Show the user a summary:
    - Lesson modified: file path, the MicroSim type and filename
    - Any quality concerns (UI text the skill flagged but did not fix, voice deviations, etc.)
    - Suggested next step: render the unit preview, click around the MicroSim, then commit

## Template Names

The seven templates in `templates/` are:

| `template_type` arg | Template filename                              |
|---------------------|------------------------------------------------|
| `signal-flow`       | `signal-flow-visualizer.html`                  |
| `calculator`        | `circuit-load-calculator.html`                 |
| `flashcards`        | `flashcard-deck.html`                          |
| `decision-tree`     | `decision-tree-explorer.html`                  |
| `timeline`          | `timeline-scrubber.html`                       |
| `matcher`           | `drag-and-drop-matcher.html`                   |
| `formula`           | `formula-explorer.html`                        |

## Customize Block Pattern

Every template has exactly one customize block at the top of its `<script>`:

```html
<script>
// <!-- CUSTOMIZE -->
const CONFIG = {
  title: "Method Flashcards",
  intro: "Click a card to see the method that fits the morning.",
  // ... template-specific fields ...
};
// END CUSTOMIZE -->

// ... template machinery the skill never touches ...
</script>
```

The skill rewrites the `CONFIG` object only. The machinery below `// END CUSTOMIZE -->` is the rendering and interaction logic, written once per template and shared across all customizations.

## Lint Pattern

Before writing, the skill runs these checks against the customized HTML:

1. **Doctype** is present: starts with `<!DOCTYPE html>`.
2. **Tag balance**: counts of `<html>` / `</html>`, `<head>` / `</head>`, `<body>` / `</body>`, `<script>` / `</script>` all match.
3. **Customize block exists**: contains both `<!-- CUSTOMIZE -->` and `END CUSTOMIZE -->` markers, in that order.
4. **CONFIG is a JS object**: between the markers, the substring after `const CONFIG = ` and before `;` parses as a JSON-shaped string when comments are removed. (Loose check; real syntax errors will still surface in the browser, but obvious typos like missing commas inside the customize block get caught.)
5. **No template placeholders leak**: no `{TITLE}`, `{INTRO}`, `{ITEMS}`, etc. left in the output.

```python
def lint_microsim(html: str) -> list[str]:
    errors = []
    if not html.lstrip().lower().startswith("<!doctype html>"):
        errors.append("missing <!DOCTYPE html>")
    for opener, closer in [("<html", "</html>"), ("<head>", "</head>"),
                            ("<body>", "</body>"), ("<script", "</script>")]:
        if html.count(opener) != html.count(closer):
            errors.append(f"unbalanced {opener}/{closer}")
    if "<!-- CUSTOMIZE -->" not in html or "END CUSTOMIZE -->" not in html:
        errors.append("missing CUSTOMIZE markers")
    for placeholder in ["{TITLE}", "{INTRO}", "{ITEMS}", "{LABEL}",
                         "{MIN}", "{MAX}", "{STEP}", "{UNIT}"]:
        if placeholder in html:
            errors.append(f"unfilled placeholder: {placeholder}")
    return errors
```

## Examples

### Example 1: Live event tech, lifting lesson, calculator

Inputs:
- unit_number: 1
- lesson_filename: "03-lifting-without-hurting-yourself.md"
- template_type: calculator
- sim_filename: "lift-decision-calculator.html"

The lesson covers the lift decision rule: roll, lift solo, or call a team. There is a numeric component (load weight, distance), so a calculator fits.

The skill customizes circuit-load-calculator.html into a "Lift Cost Calculator": sliders for load weight (10-300 lbs) and walk distance (5-50 ft), output is the team-lift recommendation plus a back-strain index. UI labels follow the test course's voice guide (a casual, peer-to-peer, working-tech register). A different course's UI labels would follow that course's voice guide.

Output: `content/unit-01-safety-and-site-awareness/microsims/lift-decision-calculator.html` plus a `{{microsim: ...}}` directive inserted in the lesson under the "How to Lift Solo" section.

### Example 2: Coffee brewing sample course, method lesson, flashcards

Inputs:
- unit_number: 1
- lesson_filename: "01-pick-a-method.md"
- template_type: flashcards
- sim_filename: "method-flashcards.html"

The lesson teaches four methods (pour-over, espresso, drip, French press) and when each fits. Flashcards fit: each card is a method, the front shows the method name, the flip shows when to pick it.

Output: `examples/sample-course-with-diagrams/content/unit-01-getting-started/microsims/method-flashcards.html` with four cards, the customize block populated with method names and "when to pick" descriptions in the coffee voice.

### Example 3: High school geology, plate tectonics lesson, signal-flow

Inputs:
- unit_number: 4
- lesson_filename: "02-plate-boundaries.md"
- template_type: signal-flow
- sim_filename: "boundary-types.html"

The lesson teaches three plate-boundary types (convergent, divergent, transform) and their outputs (mountains, rifts, fault lines). Signal-flow fits: drag a plate-motion arrow onto a boundary, see what it produces.

Output: `content/unit-04-plate-tectonics/microsims/boundary-types.html` with three input arrows (push, pull, slide) and three boundary outputs.

## Quality Checks

Before declaring the skill done, verify:

- The customized HTML parses as valid HTML (use the lint pattern above)
- The MicroSim opens in a browser as a standalone file (test it)
- All UI text matches the voice guide (skim labels, instructions, button text)
- The lesson markdown's `{{microsim: ...}}` directive points at the file that was just written
- The lesson's `draft: true` flag is set
- The static-web preview generator produces an iframe at the right spot when run

## Common Mistakes

- **Forcing a MicroSim into a lesson that does not need one.** Most lessons do not. The bar is "the student learns by manipulating." If reading the prose teaches the concept fully, skip.

- **Off-voice UI text.** A button labeled "Submit your answer" in a lesson whose voice guide calls for casual, direct prose reads like a corporate training widget. A button labeled "Pick" in a lesson whose voice guide calls for formal academic register reads as flippant. Match the voice guide for every label.

- **Customizing the machinery, not just the customize block.** The template machinery is shared. Edits there break the template for every other lesson. Stay inside the `<!-- CUSTOMIZE -->` block.

- **Leaving placeholders.** `{TITLE}`, `{INTRO}`, etc. that survive into the output are visible bugs. The lint pattern catches them; do not skip the lint.

- **Putting the iframe directive at the very top or very bottom of the lesson.** The MicroSim is a synthesis, not an introduction. Prose first, then the directive, then prose.

- **Choosing the wrong template.** A lesson about a numeric formula gets a `formula` template, not a `calculator`. A lesson about a process over time gets a `timeline`, not a `signal-flow`. See `microsim-patterns.md` for the disambiguation.

- **Skipping the lint.** A broken MicroSim shows as a 404 inside the iframe. The reader sees a blank box. The lint catches the obvious failures before the file gets written.

## Files in This Skill Folder

- `SKILL.md` (this file)
- `microsim-patterns.md` (which template fits which content shape)
- `p5js-template-reference.md` (cheat sheet for p5.js patterns: setup, draw, sliders, mouse interaction)
- `simulation-types-reference.md` (catalog of the seven templates with screenshots-in-prose)
- `templates/signal-flow-visualizer.html`
- `templates/circuit-load-calculator.html`
- `templates/flashcard-deck.html`
- `templates/decision-tree-explorer.html`
- `templates/timeline-scrubber.html`
- `templates/drag-and-drop-matcher.html`
- `templates/formula-explorer.html`

## Changelog

### 1.0 (2026-05-04)
- Initial version
- Seven templates, each a self-contained HTML file under 350 lines
- p5.js loaded via CDN (matches the Mermaid CDN stance from Phase 6)
- Customize-block pattern keeps customization isolated from machinery
- Lint pattern runs before writing; broken MicroSims never get committed
