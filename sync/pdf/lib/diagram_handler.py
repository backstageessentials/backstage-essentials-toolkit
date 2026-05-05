"""Mermaid to SVG conversion at build time.

Lessons in the course repo embed Mermaid diagrams as fenced code blocks:

    ```mermaid
    flowchart TD
        A --> B
    ```

For HTML previews, the Mermaid CDN renders these in the browser. PDFs are
static, so we have to pre-render each block to SVG before WeasyPrint runs.
We shell out to `@mermaid-js/mermaid-cli` (`mmdc`), which is a Node tool the
user installs once via npm. If it is not available we degrade gracefully:
the diagram becomes a small placeholder block, the rest of the PDF still
builds.

Brand colors come from the same palette static-web uses (#D6006C pink,
near-black text, white background). They are baked into a Mermaid theme
config file so every diagram in the PDF looks consistent.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
from html import escape as _esc
from pathlib import Path

logger = logging.getLogger(__name__)


_MERMAID_THEME = {
    "theme": "base",
    "themeVariables": {
        "primaryColor": "#FFFFFF",
        "primaryTextColor": "#0A0A0A",
        "primaryBorderColor": "#D6006C",
        "lineColor": "#0A0A0A",
        "tertiaryColor": "#F8F8F8",
        "fontFamily": "Helvetica, Arial, sans-serif",
    },
}


_FENCE_RE = re.compile(
    r"^```mermaid[ \t]*\n(.*?)\n```\s*$",
    re.DOTALL | re.MULTILINE,
)


class MermaidUnavailable(RuntimeError):
    """Raised when mmdc cannot be invoked. Sync falls back to placeholders."""


def find_mmdc() -> str | None:
    """Locate the mermaid-cli binary. Honors PATH, then npx as fallback."""
    direct = shutil.which("mmdc")
    if direct:
        return direct
    npx = shutil.which("npx")
    if npx:
        # npx will fetch mermaid-cli on demand; record its path so the
        # subprocess call below knows to invoke it via npx.
        return npx
    return None


def _mmdc_command(mmdc_path: str, input_file: Path, output_file: Path,
                   config_file: Path) -> list[str]:
    """Build the argv for the chosen mmdc invocation."""
    if mmdc_path.endswith("npx"):
        return [mmdc_path, "-y", "@mermaid-js/mermaid-cli", "-i", str(input_file),
                "-o", str(output_file), "-c", str(config_file), "-b", "transparent"]
    return [mmdc_path, "-i", str(input_file), "-o", str(output_file),
            "-c", str(config_file), "-b", "transparent"]


def render_mermaid_to_svg(source: str, cache_dir: Path,
                            mmdc_path: str | None = None) -> str | None:
    """Render one Mermaid source block to SVG.

    Caches SVGs by hash of the source so repeated builds are fast. Returns
    None on failure (caller should emit a placeholder).
    """
    if mmdc_path is None:
        mmdc_path = find_mmdc()
    if not mmdc_path:
        raise MermaidUnavailable(
            "Could not find mermaid-cli (mmdc) or npx. Install with "
            "`npm install -g @mermaid-js/mermaid-cli`."
        )

    cache_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]
    cached = cache_dir / f"diagram-{digest}.svg"
    if cached.exists():
        return cached.read_text(encoding="utf-8")

    # Isolate npm's cache to a per-course location so a broken global
    # ~/.npm (root-owned, mixed permissions) does not block diagram
    # rendering. Honor an explicit override if the caller already set it.
    env = os.environ.copy()
    npm_cache = cache_dir / "npm-cache"
    npm_cache.mkdir(parents=True, exist_ok=True)
    env.setdefault("NPM_CONFIG_CACHE", str(npm_cache))

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        in_file = tmp / "in.mmd"
        out_file = tmp / "out.svg"
        cfg_file = tmp / "config.json"
        in_file.write_text(source, encoding="utf-8")
        cfg_file.write_text(json.dumps(_MERMAID_THEME), encoding="utf-8")

        cmd = _mmdc_command(mmdc_path, in_file, out_file, cfg_file)
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=180,
                check=False, env=env,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning(f"mmdc invocation failed: {e}")
            return None

        if result.returncode != 0 or not out_file.exists():
            logger.warning(
                f"mmdc returned {result.returncode}; stderr: {result.stderr[:300]}"
            )
            return None

        svg = out_file.read_text(encoding="utf-8")
        cached.write_text(svg, encoding="utf-8")
        return svg


def expand_mermaid_blocks(markdown_text: str, cache_dir: Path,
                            mmdc_path: str | None = None) -> str:
    """Replace every ```mermaid``` fence in markdown_text with an inline SVG.

    Failed renders fall back to a styled placeholder block so the rest of
    the lesson keeps rendering. The function never raises; it logs on
    failure.
    """
    if mmdc_path is None:
        try:
            mmdc_path = find_mmdc()
        except MermaidUnavailable:
            mmdc_path = None

    def replace(match: re.Match) -> str:
        source = match.group(1)
        if not mmdc_path:
            return _placeholder_block(source, "Mermaid CLI not installed")

        try:
            svg = render_mermaid_to_svg(source, cache_dir, mmdc_path=mmdc_path)
        except MermaidUnavailable as e:
            return _placeholder_block(source, str(e))

        if svg is None:
            return _placeholder_block(source, "Diagram failed to render")
        # Strip XML preamble so weasyprint embeds it cleanly.
        svg = re.sub(r"^<\?xml[^>]*\?>\s*", "", svg)
        return f'<div class="diagram">\n{svg}\n</div>'

    return _FENCE_RE.sub(replace, markdown_text)


def _placeholder_block(source: str, reason: str) -> str:
    """Render a styled placeholder for a Mermaid block we could not render."""
    safe_source = _esc(source.strip())
    safe_reason = _esc(reason)
    return (
        '<div class="diagram diagram-fallback">\n'
        f'  <p class="diagram-fallback-note"><strong>Diagram (text fallback)</strong>'
        f'<br><em>{safe_reason}</em></p>\n'
        f'  <pre class="diagram-source">{safe_source}</pre>\n'
        "</div>"
    )
