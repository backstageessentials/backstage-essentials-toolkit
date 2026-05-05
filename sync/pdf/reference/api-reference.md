# PDF Sync Reference

This skill produces PDFs locally. There is no remote API. Notes here cover the renderer choice, the system dependencies it expects, and the build-time tool chain (`mermaid-cli`, `qrcode`, etc.).

## Renderer

Primary: **WeasyPrint** (https://weasyprint.org). HTML+CSS to PDF via the CSS Paged Media spec, with first-class support for:

- `@page` margin boxes (header/footer, page-relative content)
- `target-counter()` for the table of contents
- `page-break-inside: avoid` and `break-inside: avoid` for diagrams and questions
- Embedded SVG (Mermaid output) and PNG (QR codes, screenshots)
- Custom font embedding via `@font-face`

Install:

```
pip install weasyprint
```

WeasyPrint is pure Python *code* but binds to native libraries via cffi:

- macOS: `brew install pango cairo libffi gdk-pixbuf libxml2`
- Debian/Ubuntu: `apt install libpango-1.0-0 libpangoft2-1.0-0`
- RHEL/Fedora: `dnf install pango`

If those libraries are missing, importing weasyprint raises `OSError: cannot load library 'libgobject-2.0-0'`. The skill catches that and falls back automatically; see below.

## Fallback: Chrome headless

When WeasyPrint cannot import (typical on a fresh macOS without Homebrew), the skill shells out to Chrome:

```
google-chrome --headless=new --no-pdf-header-footer --print-to-pdf=output.pdf file://input.html
```

Chrome resolves the same intermediate HTML file. The output is close to but not identical to WeasyPrint's: Chrome uses a slightly different page-break model and ignores some CSS Paged Media features (notably `target-counter()` for TOC page numbers, which renders blank). For day-to-day workbook builds this is usually acceptable; for production deliverables, use WeasyPrint.

The skill prefers `CHROME_PATH` env var, then `google-chrome`/`chromium`/`chrome` on PATH, then the standard macOS app bundle path. No Chrome → the skill emits a clear error pointing at install options.

## Mermaid pre-rendering

Mermaid diagrams are rendered to SVG before WeasyPrint runs, since WeasyPrint cannot run JavaScript. We use `@mermaid-js/mermaid-cli` (the `mmdc` command):

```
npm install -g @mermaid-js/mermaid-cli
```

If `mmdc` is not on PATH, the skill tries `npx @mermaid-js/mermaid-cli` so first-time users do not need a global install. SVGs are cached at `<course-root>/.mermaid-svg-cache/` (gitignored, regenerable). Hash-keyed so changing a diagram's source forces a re-render.

If neither `mmdc` nor `npx` is available, each Mermaid block becomes a styled fallback block in the PDF showing the source text and a clear "Mermaid CLI not installed" note. The PDF still builds.

Brand theme is baked into a Mermaid config JSON at render time (pink #D6006C border, white fill, near-black text) so every diagram in the PDF looks consistent and matches the static-web previews.

## QR codes

The default MicroSim strategy is QR. We use the pure-Python `qrcode` package with PIL:

```
pip install "qrcode[pil]"
```

Each QR code is generated in memory, encoded as base64 PNG, and embedded inline in the HTML as a `data:` URI. No external assets, the PDF is self-contained.

Set `pdf_microsim_base_url` in course-config.yaml to the URL of the course's static-web companion site. The QR target becomes:

```
{pdf_microsim_base_url}/unit-NN-microsims/{filename}
```

Example: `https://courses.example.com/live-event/unit-01-microsims/lifting-form.html`.

If `pdf_microsim_base_url` is not set, the skill emits a placeholder block explaining what to set. The PDF still builds.

## Screenshots (alternate MicroSim strategy)

If `pdf_microsim_strategy: screenshot`, the skill looks for `<course-root>/microsim-screenshots/<microsim-stem>.png` (where stem is the filename without `.html`). Found → embedded as inline PNG. Not found → falls back to QR for that MicroSim. The build does not stop on missing screenshots; it logs and continues.

Capturing screenshots is manual: run the MicroSim in a browser, take a clean screenshot of the initial state, drop it in the folder. A future Phase may automate this via Playwright; for now it is intentional manual work to keep the dependency footprint small.

## Page geometry

`pdf_page_size` accepts `letter` (default) or `a4`, mapped to CSS Paged Media sizes (`Letter`, `A4`). Margins are 0.75in top, 0.7in left/right, 0.9in bottom (room for the footer). Footer content:

- Bottom-left: course title
- Bottom-center: copyright line
- Bottom-right: `current / total` page numbers

These are CSS values written into the stylesheet at build time so both renderers pick them up.

## Final assessment inclusion

`pdf_include_final: true` includes the course final at the back of the PDF. Default is `false` because the final is meant to be taken in a controlled environment, not used as a study aid. When included, the final's answer blocks are hidden via CSS (`.final-section .kc-answer { display: none }`). The questions are visible; the answers are not.

## Output layout

Default output directory is `<course-root>/build/pdf/`. Two files written per build:

- `<slug>.html` — the intermediate HTML the renderer consumed (kept for inspection and so users can see exactly what changed)
- `<slug>.pdf` — the rendered PDF

Both files are regenerable from the source repo. They are ignored by the toolkit's gitignore template (`build/` excluded by default).
