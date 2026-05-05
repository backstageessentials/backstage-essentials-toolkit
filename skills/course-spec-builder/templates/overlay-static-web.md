# Static Web Overlay

This file fills in the platform-specific sections of the base build spec when the target platform is Static Web. The course-spec-builder skill reads this file and substitutes its sections into the base template at the matching `<!-- OVERLAY: ... -->` markers.

The static-web target produces a self-contained multi-page HTML bundle that you deploy to any static host: GitHub Pages, Netlify, Cloudflare Pages, S3 + CloudFront, or a school's own web server. There is no platform API to call. The "sync" step is local rendering plus a file copy to your host.

## OVERLAY: api-notes

No platform API. The static-web target is a renderer, not a remote sync. Everything happens locally and the resulting folder is what you publish.

The renderer lives in `sync/static-web/lib/` inside the toolkit. It reads your course repo and writes a multi-page HTML bundle into `preview/`:

- **`index.html`** — course landing page. Magenta hero banner with course title, tagline (pulled from the first paragraph of `course-description.md`), and meta items (unit count, "final included" badge). Below the hero, a responsive grid of unit cards with hover lift, rotating accent stripes, learning-outcome summary, and lesson count.
- **`unit-N.html`** — one page per unit. Compact hero with the course name as eyebrow and the unit title as H1. Sticky left sidebar lists every unit (current highlighted) and every lesson within the current unit, with a localStorage-backed progress check next to viewed lessons. Lesson content renders as cards with a type icon (text / video / interactive inferred from body), an estimated reading time (words / 200, rounded up), and a CSS drop cap on the first paragraph. Knowledge check renders inline at the bottom of the unit.
- **`final.html`** — the course final assessment in test mode (one-shot, no answer reveal during the attempt; retest logic from Phase 14 wired up via localStorage).
- **`unit-NN-microsims/`** — per-unit folders containing the MicroSim HTML files referenced by lesson iframes.

Visual polish (Phase 18) is on by default. Hero, unit cards, lesson cards, sticky sidebar, branded footer, subtle scroll animations, drop caps, and pull-quote styling all render with no course-config changes. Animations are disabled when `prefers-reduced-motion` is set. Mobile breakpoints collapse the sidebar to a hamburger and stack cards single-column under 900px.

Mermaid diagrams render client-side via the Mermaid CDN. MicroSims render in same-origin iframes from the unit's microsims folder. Both are part of the rendered bundle; nothing extra to wire up.

## OVERLAY: sync-command

```
bes preview
```

`bes preview` renders the full multi-page bundle into `./preview/`. Open `preview/index.html` in a browser to walk the course as a learner would. Re-run after editing lessons, knowledge checks, diagrams, or MicroSims.

For the final-only fast loop:

```
bes preview-final
```

Writes `preview/final-preview.html` with just the course final in test mode. Useful while iterating on the assessment bank.

To publish, copy or push the rendered bundle to your host:

```
# GitHub Pages (gh-pages branch pattern):
cp -R preview/* /path/to/gh-pages-checkout/
cd /path/to/gh-pages-checkout && git add -A && git commit -m "Update site" && git push

# Netlify drop / CLI:
netlify deploy --dir=preview --prod

# Plain rsync to a school web server:
rsync -avz preview/ user@server:/var/www/course-name/
```

`bes sync` does not yet route the static-web platform; deploy is a manual file copy. If a deploy step gets wired into the toolkit later, this overlay will document it.

For a safe content check before publishing:

```
bes validate
```

Runs the same lint pass every other platform uses (missing fields, broken refs, draft flags). Catches problems that the static-web renderer would otherwise silently include in the bundle.

## OVERLAY: platform-risks

- **No platform chrome.** LMS targets like Canvas and Thinkific bring their own banners, gradebooks, and navigation. The static-web target has none of that, so the toolkit's own visual polish is the visual presence. If you turn polish off (or the CSS fails to load), the page reads as a wireframe. Verify the rendered bundle looks finished before sharing the URL.
- **Cover image weight.** If `cover_image_url` points at a 5 MB photo, the hero takes forever to load. Aim for ~200 KB compressed (WebP or optimized JPEG). The renderer does not resize for you.
- **Inter font dependency.** The polish design uses the Inter font (weights 400 and 800), loaded from Google Fonts. If your audience is on a network that blocks Google Fonts, the fallback stack still renders, but the typography is less tight. Bundle the font subset locally if that is a concern.
- **Mermaid CDN dependency.** Diagrams require `mermaid.min.js` from a CDN. Air-gapped networks need to vendor the script and edit the script tag, or skip Mermaid blocks entirely.
- **localStorage scope.** Progress checkmarks and retest attempt counts are stored in localStorage keyed by course slug. Clearing browser storage resets them. This is fine for a self-paced public site; institutions that need server-tracked progress should pick an LMS target instead.
- **MicroSim iframe origin.** Iframes are same-origin (`unit-NN-microsims/foo.html`), which works on every host. If your host enforces a strict Content-Security-Policy that bans iframes, MicroSims will not render. Most static hosts do not set CSP by default; if yours does, allowlist `frame-src 'self'`.
- **No auth, no enrollment, no completion tracking.** Anyone with the URL sees the whole course. Knowledge checks and the final assessment grade locally in the browser; results never leave the device. If you need gated access, an LMS target is the right tool.
- **Search.** The static-web bundle does not ship a search index. For small courses (under ~12 units) browsing via the sidebar is fine. For larger courses, plan an external search service or switch to an LMS target.

## OVERLAY: prerequisites

- Decided which static host you will publish to: GitHub Pages, Netlify, Cloudflare Pages, S3, school web server, or just sharing `preview/index.html` locally.
- If using a custom domain: DNS configured to point at the hosting provider, and HTTPS enabled at the host (most modern hosts do this automatically).
- Optional `tagline` set in `course-config.yaml`. One short sentence shown as the hero subtitle on the landing page. Skip this field to let the renderer auto-extract the first sentence of `course-description.md`.
- Optional `cover_image_url` chosen and added to `course-config.yaml`. Path is relative to `preview/index.html` after the bundle is copied to the host (a `./assets/cover.jpg` entry expects `preview/assets/cover.jpg` to exist). Skip this field to render the default magenta gradient hero.
- Optional `logo_url` chosen and added to `course-config.yaml`. Same path rules. Skip this field to render the footer without a logo.
- Optional `brand_secondary_color` chosen and added to `course-config.yaml`. CSS color string, hex preferred. Used as a complementary accent on alternating unit cards. Defaults to a lighter shade of the brand magenta.
- Optional `author_credit` and `license_text` set in `course-config.yaml` if the footer should attribute someone other than "Backstage Essentials LLC" or carry a license line (e.g., "CC BY-NC-SA 4.0").
- A modern browser available for previewing. Chrome, Firefox, Safari, and Edge all render the bundle correctly. The renderer does not target IE.
