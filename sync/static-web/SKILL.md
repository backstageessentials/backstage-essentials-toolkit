---
name: static-web-sync
version: 0.2
description: Render a course to static HTML pages with Mermaid diagram support
inputs:
  - course_root: folder_path, required, default current working directory
  - output_dir: folder_path, default ./preview
  - units_to_render: list of integers, optional (default: all)
outputs:
  - One HTML file per unit at output_dir/unit-NN-preview.html
  - Each HTML page is fully self-contained except for the Mermaid CDN script
dependencies:
  - course-spec-builder
  - repo-bootstrap
phase: 6
status: ready
subject_neutral: true
audience_neutral: true
platform: static-web
---

# Static Web Sync

Renders the course's units to standalone HTML pages. The same code generates the local preview pages and (when invoked with a deploy target) ships pages to a static site.

This is the **Phase 6 implementation**. Sync to a hosted target (GitHub Pages, Netlify, etc.) is still Phase 4 work; this skill currently produces preview HTML files locally. The rendering pipeline is the part Phase 7 (MicroSims) will reuse.

## When to Use

After lessons and knowledge checks are populated. Run before showing a unit to a stakeholder for review, after running `bes add-diagrams` to confirm Mermaid blocks render, or any time you want to eyeball the unit on the page rather than as a markdown source.

Do NOT use this skill if:
- The unit has no lessons yet (preview will be empty)
- The lesson markdown does not parse (run `bes validate` first)

## Steps

1. Verify environment:
   - `course-config.yaml` exists and parses
   - At least one unit folder under `content/`

2. Load configuration:
   - Read course-config.yaml for course metadata (name, slug)
   - Read course-description.md for the tagline (the first paragraph after the H1)

3. For each unit folder (filtered by `units_to_render` if provided):
   - Read `unit.yaml` for unit number and title
   - List lessons in `lessons/`, sorted by filename
   - Read each lesson's frontmatter and body
   - Read `knowledge-check.yaml`

4. Render the page using the template in `lib/preview.py`. The template:
   - Inlines the brand CSS (white background, near-black text, magenta D6006C accent)
   - Includes the Mermaid CDN script in `<head>`
   - For each lesson, renders the markdown body with markdown-it
   - For each ` ```mermaid ` fenced code block in the markdown, emits a `<div class="mermaid">...</div>` instead of a `<pre><code>...</code></pre>`. The Mermaid CDN script then turns that div into rendered SVG client-side.
   - Centers diagrams horizontally via the `.mermaid` CSS rule
   - For each knowledge check question, renders a collapsible `<details>` element with the question, choices, correct answer, and explanation
   - Initializes Mermaid at the end of `<body>` with brand theme variables

5. Write one HTML file per unit to `output_dir/unit-NN-preview.html`.

6. Show the user a summary: number of pages rendered, paths, and a hint about opening them in a browser.

## Mermaid Rendering

Mermaid blocks in lessons look like:

````markdown
```mermaid
flowchart TD
    A[Step] --> B{Decision?}
```
````

The renderer recognizes the `mermaid` info string on a fenced code block and emits:

```html
<div class="mermaid">
flowchart TD
    A[Step] --> B{Decision?}
</div>
```

The CSS centers and bounds the diagram:

```css
.mermaid {
  margin: 1.5em auto;
  text-align: center;
  display: flex;
  justify-content: center;
  font-family: system-ui, -apple-system, "Segoe UI", Inter, Helvetica, Arial, sans-serif;
}
.mermaid svg {
  max-width: 100%;
  height: auto;
}
```

The Mermaid library is loaded from the CDN in `<head>`:

```html
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
```

And initialized at the end of `<body>` with brand theme variables:

```html
<script>
mermaid.initialize({
  startOnLoad: true,
  theme: 'base',
  themeVariables: {
    primaryColor: '#FFFFFF',
    primaryTextColor: '#0A0A0A',
    primaryBorderColor: '#D6006C',
    lineColor: '#0A0A0A',
    tertiaryColor: '#F8F8F8',
    fontFamily: 'system-ui, -apple-system, "Segoe UI", Inter, Helvetica, Arial, sans-serif'
  }
});
</script>
```

## Why CDN, Not Inlined

The CDN approach assumes the reviewer has internet when they open the preview. That is true for local review and almost all stakeholder-share scenarios.

For truly offline / air-gapped previews, swap in a build-time pre-render via `@mermaid-js/mermaid-cli`. The renderer detects a `--prerender` flag and substitutes inline SVG in place of the `.mermaid` div. This is documented in `lib/preview.py` but not the default path.

## Thinkific Note

Thinkific's lesson sandbox may strip or sandbox the `<script>` tag for the Mermaid CDN, so on Thinkific the recommended pattern is to pre-render Mermaid to inline SVG before pushing. The Thinkific sync target handles that conversion at sync time. The static-web preview pipeline does not need that conversion since it runs in a normal browser.

## Files in This Skill Folder

- `SKILL.md` (this file)
- `lib/preview.py` (the HTML preview generator)
- `lib/__init__.py`

## Changelog

### 0.1 (Phase 4 placeholder)
- Stub only.

### 0.2 (2026-05-04, Phase 6)
- Initial real implementation.
- Renders one HTML page per unit with brand CSS, Mermaid CDN, and the
  collapsible knowledge-check pattern from the test course's preview.
- Mermaid blocks render as `<div class="mermaid">` so the Mermaid library
  turns them into SVG client-side.
