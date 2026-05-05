# PDF Overlay

This file fills in the platform-specific sections of the base build spec when the target platform is PDF. The course-spec-builder skill reads this file and substitutes its sections into the base template at the matching `<!-- OVERLAY: ... -->` markers.

## OVERLAY: api-notes

PDF generation runs locally. There is no remote API, no token, no rate limit. The `bes sync` (or `bes export-pdf`) command produces a single PDF in `build/pdf/<slug>.pdf` and an intermediate HTML file in `build/pdf/<slug>.html` for inspection.

The toolkit uses WeasyPrint as the primary renderer:

- HTML and CSS to PDF via the CSS Paged Media spec
- First-class support for `@page` margin boxes (header, footer, page numbers)
- Resolves a table of contents page numbers via `target-counter()`
- Embeds SVG diagrams and PNG QR codes inline as data URIs

If WeasyPrint cannot import (it depends on Pango/Cairo system libraries), the skill falls back to Google Chrome headless, which most macOS workstations have already. The fallback's output is close to but not identical to WeasyPrint's; for production-quality deliverables, install the WeasyPrint system libs.

Build pipeline at a glance:

1. Read `course-config.yaml` for course metadata and PDF-specific fields
2. Read `course-description.md` for the cover audience tagline and the description page
3. Walk every `content/unit-NN-*` folder, parse unit.yaml, lessons, knowledge-check.yaml
4. Pre-render every Mermaid fence to SVG via `mermaid-cli` (`mmdc`), cached at `.mermaid-svg-cache/` by source hash
5. Pre-render every `{{microsim: ...}}` directive to a QR code (default) or a screenshot
6. Assemble the document: cover, TOC, course description, units, optional final
7. Render to PDF via WeasyPrint (or Chrome headless), save the intermediate HTML alongside

Build time scales with the number of Mermaid diagrams. A typical 6-unit course with 30 lessons and 6-10 diagrams takes 10-30 seconds on first build, a few seconds on incremental rebuilds (the diagram cache is the bottleneck).

## OVERLAY: sync-command

```
python3 scripts/sync.py
```

Or, once the bes command is installed:

```
bes sync           # if course-config.yaml platform is pdf
bes export-pdf     # at any time, regardless of primary platform
```

`bes sync` reads `course-config.yaml`, sees that the platform is `pdf`, and runs the PDF rendering logic from the toolkit's `sync/pdf/` skill. `bes export-pdf` does the same thing but never looks at the platform field, so a Thinkific or Canvas course can produce a downloadable PDF on demand without changing its primary platform.

To inspect the layout without running the renderer (fast iteration on lessons):

```
bes export-pdf --dry-run
```

The intermediate HTML is written to `build/pdf/<slug>.html` and no PDF is generated.

## OVERLAY: platform-risks

- **WeasyPrint system libraries.** WeasyPrint depends on Pango, Cairo, and a few related libs. On macOS that means Homebrew (`brew install pango cairo libffi gdk-pixbuf`); on Linux distros they are usually packaged. If the libs are missing, importing weasyprint raises an OSError and the skill falls back to Chrome headless. Chrome's output is acceptable for workbooks but does not resolve `target-counter()`, so TOC page numbers come out blank. For polished deliverables, install the WeasyPrint system libs.
- **Mermaid CLI dependency.** Diagrams are pre-rendered via `mermaid-cli` (`npm install -g @mermaid-js/mermaid-cli`). Without `mmdc` or `npx`, every diagram becomes a styled source-text fallback in the PDF. The fallback is intentional, not a bug; it keeps builds working on environments without Node.
- **MicroSim degradation.** PDFs cannot run interactive widgets. The default QR strategy gives readers a path back to the live MicroSim hosted on the course's static-web companion. Without the companion deployed, QR codes scan to a 404. The screenshot strategy embeds a static PNG instead, but requires the user to capture screenshots manually first.
- **Page break artifacts.** WeasyPrint occasionally splits a long question or a tall diagram across pages. The CSS uses `page-break-inside: avoid` on questions and diagrams to minimize this, but oversized content still breaks. Shorten the question or split the diagram if you see a bad break.
- **Font embedding.** WeasyPrint embeds the fonts it can find on the system. If a learner opens the PDF on a machine without those fonts, the system-fallback font is substituted. The default CSS uses Helvetica/Arial which is on every consumer system, so this is rarely an issue.
- **Build artifacts in git.** `build/` is gitignored by default. Do not commit the rendered PDF; regenerate it from source for each release. Tag the release in git so the PDF is reproducible from a known commit.
- **Accessibility.** WeasyPrint produces tagged PDFs with reasonable structure for screen readers, but the toolkit does not validate accessibility. If WCAG compliance matters for your audience, run a separate audit (PAC, Adobe Acrobat) before publishing.

## OVERLAY: prerequisites

- Python 3.10 or later, with `pip install -e ~/Code/backstage-essentials-toolkit` already done
- A PDF renderer installed:
  - WeasyPrint (recommended): `pip install weasyprint`. On macOS, install the system libs with `brew install pango cairo libffi gdk-pixbuf`. On Debian/Ubuntu: `apt install libpango-1.0-0 libpangoft2-1.0-0`.
  - Or Google Chrome / Chromium installed (no setup needed if Chrome is already on the machine)
- Mermaid CLI for diagram pre-rendering: `npm install -g @mermaid-js/mermaid-cli` (skip if the course has no Mermaid diagrams; the build still works, diagrams degrade to text)
- `qrcode` Python package (installed automatically when bes is installed, listed in setup.py)
- The .env file has no required values for PDF; the env-example template carries an `OUTPUT_DIR` placeholder for users who want to customize the output location, but the default `build/pdf/` works without any config.
- For QR-strategy MicroSims to scan to working URLs, deploy the static-web companion site first and set `pdf_microsim_base_url` in course-config.yaml to its public URL.
- PDF-specific course-config.yaml fields (all optional, with defaults):
  ```yaml
  course:
    pdf_page_size: "letter"          # or "a4"
    pdf_microsim_strategy: "qr"      # or "screenshot"
    pdf_microsim_base_url: null      # set to your static-web URL for live QR targets
    pdf_include_final: false         # true to embed the final assessment in the PDF (questions only, answers hidden via CSS)
  ```
