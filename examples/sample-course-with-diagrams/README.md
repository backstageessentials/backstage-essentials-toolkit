# Sample Course with Diagrams

This is a small, frozen sample course used as a worked example for the
`diagram-builder` skill (Phase 6). It is not a real course and not a
template to fork. It exists so Claude Code can pattern-match what good
Mermaid in a lesson looks like.

The subject is **Home Coffee Brewing Basics**, a deliberately low-stakes,
domain-neutral topic that exercises the three most useful Mermaid types:

- **Flowchart** for the "which method should I use?" decision
- **Sequence diagram** for the brew-over-time interaction
- **State diagram** for the bean's lifecycle from roasted to brewed

## Files

- `course-config.yaml` — minimal course config, platform = static-web.
- `course-description.md` — one-paragraph course description.
- `voice-guide.md` — voice guide (short, declarative, second person).
- `content/unit-01-getting-started/`
  - `unit.yaml` — unit metadata.
  - `knowledge-check.yaml` — placeholder, no questions; this sample is
    about diagram patterns, not assessment patterns.
  - `lessons/01-pick-a-method.md` — flowchart example.
  - `lessons/02-the-brew.md` — sequence diagram example.
  - `lessons/03-the-bean.md` — state diagram example.

## How to use these

Read alongside `skills/diagram-builder/SKILL.md` and
`skills/diagram-builder/diagram-patterns.md`. Each lesson here shows one
diagram type in real lesson context: how the prose introduces the
diagram, how the intro line ends in a colon, how node labels match the
voice guide, and how the diagram is followed by prose that uses it
rather than re-stating it.

Do **not** copy these files into a new course. Let the toolkit's
`bes new-course` and the diagram-builder skill produce equivalent
material in your course's voice. These files are a reference, not a
starting point.
