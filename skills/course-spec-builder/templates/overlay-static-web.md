# Static Web Overlay (stub, Phase 4)

This overlay is a placeholder. The full static web content gets written when the sync/static-web skill is built in Phase 4.

The static web target produces an MkDocs site or similar, deployable to GitHub Pages, Netlify, or any static hosting.

## OVERLAY: api-notes

No API. Content is built locally and deployed as static files.

The build process:

1. mkdocs.yml config defines navigation, theme, and plugins.
2. MkDocs reads the lesson markdown files and assembles a static site.
3. Output goes to a `site/` folder.
4. Deploy to hosting via `mkdocs gh-deploy` (for GitHub Pages) or by pushing the `site/` folder to your hosting provider.

## OVERLAY: sync-command

```
# Build the site locally:
mkdocs build

# Or deploy directly to GitHub Pages:
mkdocs gh-deploy

# Once bes sync supports static-web (Phase 4):
# bes sync   (reads course-config.yaml, builds and deploys)
```

## OVERLAY: platform-risks

- MkDocs has many themes and plugins. Pick a theme early and stick with it. Switching themes mid-course can break formatting.
- Quiz functionality on a static site requires JavaScript. Options: a self-hosted JS quiz library, an embedded service (like Google Forms), or skipping interactive quizzes entirely.
- GitHub Pages has a 1 GB repo size limit and a 100 MB per-file limit. Plan media hosting accordingly.
- Search functionality on static sites is JavaScript-based and works on the client side. Large courses may need an external search service.

## OVERLAY: prerequisites

- Decided which static site generator (MkDocs is the default, but Hugo, Jekyll, or Docusaurus work too).
- Decided which theme.
- Decided the deployment target (GitHub Pages, Netlify, Cloudflare Pages, custom).
- If using a custom domain, DNS configured to point at the hosting provider.
