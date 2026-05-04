# PDF Overlay (stub, Phase 4)

This overlay is a placeholder. The full PDF generation content gets written when the sync/pdf skill is built in Phase 4.

The PDF target produces one or more PDF files from the course content. Useful as a workbook companion to a course on another platform, or as a standalone deliverable.

## OVERLAY: api-notes

No API. Content is built locally and produces PDF files.

Options for PDF generation:

- Pandoc with LaTeX: high quality typography, more setup.
- WeasyPrint: HTML and CSS to PDF, easier setup, decent quality.
- ReportLab: Python library, fully programmatic, good for highly custom layouts.

The sync/pdf skill in Phase 4 will pick a default and document the choice.

## OVERLAY: sync-command

```
# Once implemented:
# bes sync   (generates PDFs based on course-config.yaml)
```

## OVERLAY: platform-risks

- PDF generation is fiddly. Page breaks, image placement, font embedding all require attention.
- Different generators produce different output for the same source. Pick one early and test thoroughly.
- Large PDFs (over 100 pages) take time to generate. Plan for build times when iterating.
- Accessibility (screen reader friendly PDFs, tagged structure) requires extra configuration.

## OVERLAY: prerequisites

- Decided which PDF generator (Pandoc, WeasyPrint, ReportLab).
- For Pandoc with LaTeX: a LaTeX distribution installed (TeX Live or similar).
- For WeasyPrint: WeasyPrint installed via pip.
- A page template or stylesheet defining layout (header, footer, margins, fonts).
- Decided whether to produce one PDF per unit or one combined PDF for the whole course.
