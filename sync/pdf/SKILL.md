---
name: pdf-sync
version: 1.0
description: Generate a PDF version of the course (workbook, offline backup, instructor packet)
inputs:
  - course_root: folder_path, required, default current working directory
  - dry_run: boolean, default false (write intermediate HTML only, skip the PDF render)
  - output_dir: folder_path, default <course-root>/build/pdf
outputs:
  - <output_dir>/<course-slug>.pdf
  - <output_dir>/<course-slug>.html (the intermediate HTML the renderer consumed)
  - <course-root>/.mermaid-svg-cache/diagram-*.svg (cached pre-rendered diagrams)
dependencies:
  - course-spec-builder (course needs a spec)
  - repo-bootstrap (course needs a populated repo)
  - WeasyPrint (Python; optional system libs Pango/Cairo) OR Google Chrome / Chromium
  - mermaid-cli via npm or npx (only if the course uses Mermaid diagrams)
  - qrcode Python package (for the default QR microsim strategy)
phase: 12
status: ready
subject_neutral: true
audience_neutral: true
platform: pdf
---

# PDF Sync

Generates a PDF version of the course as a workbook, offline backup, or instructor-led delivery packet. Two ways to invoke:

- **bes sync** when the course's `course-config.yaml` has `platform: pdf`. The platform router calls this skill.
- **bes export-pdf** at any time, regardless of the course's primary platform. Useful when a Thinkific or Canvas course also needs a downloadable PDF.

Both paths run the same code. `bes export-pdf` does not change the course's platform setting; it only runs the renderer.

## When to Use

- The course is feature-complete enough to be useful as a standalone packet (lessons drafted, knowledge checks populated, optional course final).
- A client or learner has asked for a PDF deliverable.
- You want a permanent, offline backup of the course state at a point in time.

Do NOT run sync if:

- Course content is still placeholder text. The PDF will be a polished record of unfinished work.
- The MicroSim base URL is not set and the strategy is QR. The PDF will build but every MicroSim will be a placeholder caption pointing at unfilled config.

## Auth

None. PDFs are built locally. There is no API and no token.

## Steps

1. Verify environment:
   - `course-config.yaml` exists and parses
   - `content/unit-*/` folders exist
   - At least one renderer is available: WeasyPrint (preferred) or Google Chrome / Chromium (fallback)
   - `mermaid-cli` (`mmdc`) is on PATH, or `npx` is on PATH (only required if the course uses Mermaid diagrams)

2. Load configuration:
   - Read `course-config.yaml` for course metadata and PDF-specific fields:
     - `pdf_page_size`: "letter" (default) or "a4"
     - `pdf_microsim_strategy`: "qr" (default) or "screenshot"
     - `pdf_microsim_base_url`: where the live MicroSim companion site is hosted (required for QR codes to scan to something useful)
     - `pdf_include_final`: false (default) or true to include the course final at the back
   - Read `course-description.md` to populate the audience tagline on the cover and the course-description section
   - Read every `content/unit-NN-*/unit.yaml`, the lessons under each, and `knowledge-check.yaml`

3. Pre-render diagrams:
   - Find every ` ```mermaid ` fence in lesson markdown
   - Cache by source hash at `.mermaid-svg-cache/`
   - Shell out to `mmdc -i in.mmd -o out.svg -c <theme.json>` with the Backstage Essentials theme (pink border, white fill, near-black text)
   - On `mmdc` failure, fall back to a styled "diagram fallback" block showing the source

4. Pre-render MicroSim references:
   - For each `{{microsim: filename.html}}` directive in lesson markdown:
     - Strategy `qr`: generate a QR code data URI linking to `<pdf_microsim_base_url>/unit-NN-microsims/<filename>`
     - Strategy `screenshot`: embed `microsim-screenshots/<stem>.png` if present, else fall back to QR
     - `TODO` directives become unfilled-slot placeholders so authors see what is missing

5. Assemble the HTML document. Section order:
   - Cover page (title, audience, version, author, date, copyright; no footer)
   - Table of contents (auto-generated from units and lessons; page numbers resolved by the renderer)
   - Course description page
   - One page-breaking section per unit: header, learning outcomes, lessons (with diagrams and MicroSims inline), knowledge check in study format
   - Optional course final, if `pdf_include_final: true`. Questions visible, answers hidden via CSS.

6. Render to PDF:
   - Try WeasyPrint first
   - If WeasyPrint cannot import (system libs missing), shell out to Chrome headless
   - If neither works, write only the intermediate HTML and emit a clear error with install options

7. Write outputs:
   - `<output_dir>/<slug>.pdf`
   - `<output_dir>/<slug>.html` (kept for inspection, regeneratable)

8. Print the path to the PDF and a one-line summary (file size, renderer used, page size, elapsed time).

## Knowledge checks in study format

PDFs cannot hide content interactively, so knowledge-check answers go directly under each question, in a colored block. The block is page-break-protected so the answer stays with the question. Course finals (when included) hide their answers via CSS so the PDF can be used as a take-home test packet.

## Output Format

### Console output during sync

```
[pdf export] course_root=/Users/x/Code/my-course
[1/4] Building HTML document...
  OK (My Course, page size Letter, microsims via qr)
  Intermediate HTML: build/pdf/my-course.html
[2/4] Rendering PDF (trying WeasyPrint)...
  OK (rendered with weasyprint)
[3/4] Verifying output...
  OK (847.2 KB)
[4/4] Done!

Summary:
  Course:    My Course
  Output:    /Users/x/Code/my-course/build/pdf/my-course.pdf
  Renderer:  weasyprint
  Page size: Letter
  Time:      6.2 seconds
```

### Files written

```
build/pdf/
├── my-course.html      <- the intermediate HTML the renderer consumed
└── my-course.pdf       <- the rendered PDF
```

Both files regenerate on every run. They are gitignored by default (`build/` is excluded by the toolkit's gitignore template).

## Examples

### Example 1: Generate a PDF for a Canvas course

State: course is on Canvas. A client asked for a PDF version.

Command:

```
bes export-pdf
```

Result: PDF generated at `build/pdf/<slug>.pdf`. The course-config.yaml platform stays `canvas`. No state changes.

### Example 2: Course where PDF is the primary delivery

State: the course is meant to be a downloadable PDF only (no LMS, no website).

course-config.yaml:

```yaml
course:
  name: "Example Workbook"
  slug: "example-workbook"
  platform: "pdf"
  pdf_page_size: "letter"
  pdf_microsim_strategy: "qr"
  pdf_microsim_base_url: "https://courses.example.com/example-workbook"
  pdf_include_final: false
```

Command:

```
bes sync
```

Result: same as Example 1, but invoked through the platform router.

### Example 3: Final included as a take-home test

State: course is meant to be self-paced; you want the final at the back of the PDF for the learner to take.

course-config.yaml adds:

```yaml
  pdf_include_final: true
```

Result: final appears as the last section. Question text is visible; the "Answer:" blocks are hidden via the `.final-section .kc-answer { display: none }` rule so the PDF can be used as a printable test.

### Example 4: Inspect the HTML without rendering

```
bes export-pdf --dry-run
```

Result: the intermediate HTML is written but no PDF is generated. Useful for fast iteration on layout while building out lessons.

## Quality Checks

Before declaring the PDF done, verify:

- The cover page has the correct title, author, version, and date
- The table of contents lists every unit and lesson with page numbers (WeasyPrint only; Chrome's TOC numbers will be blank)
- Every lesson is on its expected unit, in the expected order
- Mermaid diagrams render as embedded SVGs, not as fallback text blocks
- MicroSim QR codes scan to working URLs (test at least one)
- Knowledge checks include the question, the answer block, and the explanation
- The course final is omitted unless `pdf_include_final: true` is set
- Page footer shows course title, copyright, and page numbers (cover page is exempt)

## Common Mistakes

- **WeasyPrint imports but pages render blank.** Pango is loaded but a font is missing. Install a sans-serif font system-wide or change the CSS `font-family` to a font you have.

- **Chrome fallback used unintentionally.** Chrome cannot resolve `target-counter()`, so TOC page numbers are blank. If TOC numbers matter, install WeasyPrint's system libs and rerun.

- **Diagrams render as text fallback.** `mmdc` is not on PATH. Run `npm install -g @mermaid-js/mermaid-cli` or rely on `npx` (slower first run, no global install needed).

- **QR codes scan to a 404.** `pdf_microsim_base_url` is set, but the course's static-web companion is not deployed yet. Deploy the static-web sync first, then regenerate the PDF.

- **Final answers are visible.** The CSS rule that hides `.final-section .kc-answer` was overridden by inline styles or by a custom stylesheet. Check the rendered HTML.

- **Page breaks split a question or diagram.** The CSS uses `page-break-inside: avoid` for `.kc-list > li` and `.diagram`. If you see breaks anyway, the element is taller than one page; shorten the question or split the diagram.

- **Build is slow.** Mermaid renders are the bottleneck. The cache at `.mermaid-svg-cache/` makes re-runs fast; do not delete it between builds. If the cache directory is missing, every diagram re-renders.

## Files in This Skill Folder

- `SKILL.md` (this file)
- `lib/pdf_builder.py` (entry points: `sync()` for `bes sync`, `export_pdf()` for `bes export-pdf`)
- `lib/layout.py` (HTML document assembly: cover, TOC, units, knowledge checks, optional final)
- `lib/style.css` (brand stylesheet: colors, typography, page geometry, headers, footers)
- `lib/diagram_handler.py` (Mermaid → SVG via mmdc, with caching and fallback)
- `lib/microsim_handler.py` (MicroSim → QR or screenshot)
- `templates/sync-shim.py` (the per-course `scripts/sync.py` wrapper for PDF courses)
- `reference/api-reference.md` (renderer choice, system deps, build-time tools)

## Changelog

### 1.0 (2026-05-05)
- Initial version
- WeasyPrint primary, Chrome headless fallback
- Mermaid via mermaid-cli with hash-keyed SVG cache
- MicroSim via QR (default) or screenshot
- Cover, TOC with target-counter() page numbers, course description, per-unit pages, optional final
- Both `bes sync` (when platform is pdf) and `bes export-pdf` (regardless of platform) wired up
