"""MicroSim references in PDF context.

Lessons mark MicroSims with the directive:

    {{microsim: foo.html height=400}}
    {{microsim: TODO type=flashcards purpose="..."}}

In an HTML preview these become live <iframe> embeds. PDFs cannot host
interactive widgets, so we degrade. Two strategies, configurable per
course via course-config.yaml's `pdf_microsim_strategy`:

- `qr` (default): generate a QR code that links to the MicroSim hosted at
  the course's static-web URL, embed it inline with a caption.
- `screenshot`: embed a pre-captured PNG screenshot of the MicroSim's
  initial state if the course has one in `microsim-screenshots/`. Falls
  back to QR if no screenshot is available.

The QR code points at a course-relative URL the user supplies via
`pdf_microsim_base_url` in course-config.yaml. If no base URL is set we
emit a placeholder caption so the PDF still builds. The output should
make it clear what the missing piece is.
"""

from __future__ import annotations

import base64
import io
import logging
import re
from html import escape as _esc
from pathlib import Path

import qrcode

logger = logging.getLogger(__name__)


_MICROSIM_RE = re.compile(r"\{\{microsim:\s*([^\s}]+)([^}]*)\}\}")


def _parse_attrs(attr_str: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    pairs = re.findall(r'(\w+)=("([^"]*)"|(\S+))', attr_str)
    for key, _full, quoted, plain in pairs:
        attrs[key] = quoted if quoted else plain
    return attrs


def _qr_data_uri(url: str, box_size: int = 6) -> str:
    """Encode a URL as a QR code, return a data: URI suitable for <img src=...>."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0A0A0A", back_color="#FFFFFF")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _png_data_uri(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def render_microsim_block(filename: str, attrs: dict[str, str], unit_number: int,
                            strategy: str, base_url: str | None,
                            screenshot_dir: Path | None) -> str:
    """Render one {{microsim: ...}} directive into HTML for the PDF.

    `strategy` is "qr" or "screenshot". If "screenshot" is requested but
    no screenshot file exists, we fall back to "qr". If "qr" is requested
    but no base_url is configured, we emit a placeholder caption.
    """
    purpose = attrs.get("purpose", "").strip()
    sim_type = attrs.get("type", "").strip()
    label = filename
    if filename.upper() == "TODO":
        # The lesson author has not built this MicroSim yet.
        return _todo_placeholder(sim_type, purpose)

    chosen_strategy = strategy
    screenshot_path: Path | None = None
    if chosen_strategy == "screenshot" and screenshot_dir is not None:
        candidate = screenshot_dir / f"{Path(filename).stem}.png"
        if candidate.exists():
            screenshot_path = candidate
        else:
            logger.warning(
                f"MicroSim screenshot missing for {filename}; "
                f"falling back to QR. Expected at {candidate}."
            )
            chosen_strategy = "qr"

    caption_bits = []
    if purpose:
        caption_bits.append(_esc(purpose))
    caption_bits.append(
        f'<span class="microsim-filename">{_esc(label)}</span>'
    )
    caption_html = " <br> ".join(caption_bits)

    if chosen_strategy == "screenshot" and screenshot_path is not None:
        data_uri = _png_data_uri(screenshot_path)
        return (
            '<figure class="microsim microsim-screenshot">\n'
            f'  <img src="{data_uri}" alt="MicroSim screenshot: {_esc(filename)}">\n'
            '  <figcaption>\n'
            f'    <strong>Interactive simulation:</strong> {caption_html}<br>\n'
            f'    <em>Static screenshot. The live version is on the course '
            'companion site.</em>\n'
            '  </figcaption>\n'
            '</figure>'
        )

    # QR strategy (default).
    if not base_url:
        return _qr_unconfigured_placeholder(filename, purpose)

    sim_url = _build_sim_url(base_url, unit_number, filename)
    qr_uri = _qr_data_uri(sim_url)
    return (
        '<figure class="microsim microsim-qr">\n'
        f'  <img src="{qr_uri}" alt="QR code linking to live MicroSim: {_esc(filename)}">\n'
        '  <figcaption>\n'
        f'    <strong>Interactive simulation:</strong> {caption_html}<br>\n'
        f'    <em>Scan the QR code or open <code>{_esc(sim_url)}</code> to use it.</em>\n'
        '  </figcaption>\n'
        '</figure>'
    )


def _build_sim_url(base_url: str, unit_number: int, filename: str) -> str:
    base = base_url.rstrip("/")
    return f"{base}/unit-{unit_number:02d}-microsims/{filename}"


def _todo_placeholder(sim_type: str, purpose: str) -> str:
    sim_type = sim_type or "?"
    purpose = purpose or "(no purpose given)"
    return (
        '<div class="microsim microsim-todo">\n'
        f'  <p><strong>MicroSim slot ({_esc(sim_type)}):</strong> '
        f'{_esc(purpose)}</p>\n'
        f'  <p><em>Unfilled. Run <code>bes add-microsim</code> to build it '
        'before publishing the PDF.</em></p>\n'
        '</div>'
    )


def _qr_unconfigured_placeholder(filename: str, purpose: str) -> str:
    purpose_html = f"<br>{_esc(purpose)}" if purpose else ""
    return (
        '<div class="microsim microsim-todo">\n'
        f'  <p><strong>MicroSim:</strong> {_esc(filename)}{purpose_html}</p>\n'
        '  <p><em>QR strategy selected but <code>pdf_microsim_base_url</code> is '
        'not set in course-config.yaml. Set it to the public URL of your '
        'static-web companion site to embed scannable QR codes.</em></p>\n'
        '</div>'
    )


def expand_microsim_directives(markdown_text: str, unit_number: int,
                                 strategy: str, base_url: str | None,
                                 screenshot_dir: Path | None) -> str:
    """Replace every {{microsim: ...}} directive in markdown_text with HTML."""

    def replace(match: re.Match) -> str:
        first = match.group(1).strip()
        attrs = _parse_attrs(match.group(2))
        return render_microsim_block(
            filename=first,
            attrs=attrs,
            unit_number=unit_number,
            strategy=strategy,
            base_url=base_url,
            screenshot_dir=screenshot_dir,
        )

    return _MICROSIM_RE.sub(replace, markdown_text)
