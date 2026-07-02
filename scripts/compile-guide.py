#!/usr/bin/env python3
"""
compile-guide.py — Convert the Axon Audit operator guide (markdown)
into a PDF using the same LaTeX-style template as the audit reports.

Usage:
    python3 compile-guide.py
    python3 compile-guide.py --md /path/to/guide.md --pdf /path/to/out.pdf

Pipeline:
    1. Read markdown
    2. Convert to a structured HTML model (headings, paragraphs, tables, code)
    3. Render via the axon-audit report_template (reuses the same CSS)
    4. Convert HTML to PDF via kimi-pdf's html_to_pdf.js
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

# Reuse the report template
HERE = Path(__file__).resolve().parent
SKILL = Path.home() / ".agents/skills/axon-audit"
sys.path.insert(0, str(SKILL / "scripts"))
from report_template import CSS, _esc, render_toc  # noqa: E402

KIMI_PDF_HTML_TO_PDF = Path.home() / ".agents/skills/kimi-pdf/scripts/html_to_pdf.js"


# ---------------------------------------------------------------------------
# Minimal markdown -> structured model
# ---------------------------------------------------------------------------

def parse_markdown(md: str) -> list[dict[str, Any]]:
    """Parse markdown into a list of block dicts.

    Supported blocks: h1, h2, h3, p, ul, ol, code, table, hr, blockquote.
    Inline: **bold**, `code`, *italic* (not in tables).
    """
    blocks: list[dict[str, Any]] = []
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.rstrip()

        # Blank line
        if not s.strip():
            i += 1
            continue

        # Horizontal rule
        if re.match(r"^\s*---+\s*$", s):
            blocks.append({"type": "hr"})
            i += 1
            continue

        # Headings
        m = re.match(r"^(#{1,4})\s+(.+)$", s)
        if m:
            level = len(m.group(1))
            blocks.append({"type": f"h{level}", "text": m.group(2).strip()})
            i += 1
            continue

        # Code block (fenced)
        if s.strip().startswith("```"):
            lang = s.strip()[3:].strip()
            i += 1
            code_lines = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing fence
            blocks.append({"type": "code", "lang": lang, "text": "\n".join(code_lines)})
            continue

        # Blockquote
        if s.lstrip().startswith(">"):
            quote_lines = []
            while i < len(lines) and lines[i].lstrip().startswith(">"):
                quote_lines.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            blocks.append({"type": "blockquote", "text": "\n".join(quote_lines)})
            continue

        # Table (must have a header row + separator row)
        if "|" in s and i + 1 < len(lines) and re.match(r"^\s*\|?\s*[-:|\s]+\|", lines[i + 1]):
            table_lines = [s]
            i += 1
            # separator
            table_lines.append(lines[i])
            i += 1
            # body rows
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                table_lines.append(lines[i])
                i += 1
            blocks.append({"type": "table", "rows": [_parse_table_row(r) for r in table_lines]})
            continue

        # Unordered list
        if re.match(r"^\s*[-*]\s+", s):
            items = []
            while i < len(lines) and re.match(r"^\s*[-*]\s+", lines[i] or ""):
                items.append(re.sub(r"^\s*[-*]\s+", "", lines[i]).strip())
                i += 1
            blocks.append({"type": "ul", "items": items})
            continue

        # Ordered list
        if re.match(r"^\s*\d+\.\s+", s):
            items = []
            while i < len(lines) and re.match(r"^\s*\d+\.\s+", lines[i] or ""):
                items.append(re.sub(r"^\s*\d+\.\s+", "", lines[i]).strip())
                i += 1
            blocks.append({"type": "ol", "items": items})
            continue

        # Paragraph (collect contiguous non-empty, non-special lines)
        para_lines = [s]
        i += 1
        while i < len(lines):
            nxt = lines[i].rstrip()
            if not nxt.strip():
                break
            if re.match(r"^#{1,4}\s+", nxt) or nxt.strip().startswith("```") \
                    or re.match(r"^\s*[-*]\s+", nxt) or re.match(r"^\s*\d+\.\s+", nxt) \
                    or nxt.lstrip().startswith(">") or "|" in nxt:
                break
            para_lines.append(nxt)
            i += 1
        blocks.append({"type": "p", "text": " ".join(para_lines)})

    return blocks


def _parse_table_row(line: str) -> list[str]:
    """Parse a single markdown table row, stripping leading/trailing pipes."""
    parts = [c.strip() for c in line.strip().strip("|").split("|")]
    return parts


# ---------------------------------------------------------------------------
# Inline rendering (bold, code, italic)
# ---------------------------------------------------------------------------

def render_inline(text: str) -> str:
    """Apply inline markdown to already-escaped text.

    Order matters: escape first, then add HTML tags for inline markup.
    """
    # Code spans: `text` -> <code>text</code>
    text = re.sub(
        r"`([^`]+)`",
        lambda m: f"<code>{m.group(1)}</code>",
        text,
    )
    # Bold: **text** -> <strong>text</strong>
    text = re.sub(
        r"\*\*([^*]+)\*\*",
        lambda m: f"<strong>{m.group(1)}</strong>",
        text,
    )
    # Italic: *text* -> <em>text</em>  (only if not part of **)
    text = re.sub(
        r"(?<!\*)\*([^*]+)\*(?!\*)",
        lambda m: f"<em>{m.group(1)}</em>",
        text,
    )
    return text


def render_paragraph(text: str) -> str:
    return f"<p>{render_inline(_esc(text))}</p>"


def render_heading(level: int, text: str, anchor: str | None = None) -> str:
    tag = f"h{level}"
    anchor_attr = f' id="{anchor}"' if anchor else ""
    return f"<{tag}{anchor_attr}>{render_inline(_esc(text))}</{tag}>"


def render_list(items: list[str], ordered: bool = False) -> str:
    tag = "ol" if ordered else "ul"
    inner = "\n".join(f"    <li>{render_inline(_esc(it))}</li>" for it in items)
    return f"<{tag}>\n{inner}\n</{tag}>"


def render_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    # Row 0 = header, row 1 = separator (---), row 2+ = body
    header = rows[0]
    body = rows[2:] if len(rows) > 2 else []
    thead = "<tr>" + "".join(f"<th>{render_inline(_esc(c))}</th>" for c in header) + "</tr>"
    tbody = "\n".join(
        "<tr>" + "".join(f"<td>{render_inline(_esc(c))}</td>" for c in r) + "</tr>"
        for r in body
    )
    return (
        "<table>\n"
        f"  <thead>{thead}</thead>\n"
        f"  <tbody>{tbody}</tbody>\n"
        "</table>"
    )


def render_code(text: str) -> str:
    return f"<pre><code>{_esc(text)}</code></pre>"


def render_blockquote(text: str) -> str:
    return f"<blockquote><p>{render_inline(_esc(text))}</p></blockquote>"


# ---------------------------------------------------------------------------
# Assemble document
# ---------------------------------------------------------------------------

def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "section"


def render_html(blocks: list[dict[str, Any]], title: str = "Axon Audit Operator Guide") -> str:
    """Render the parsed markdown blocks into a full HTML document."""
    # Section anchors for h2
    body_parts: list[str] = []
    toc_entries: list[tuple[str, str]] = []

    for block in blocks:
        btype = block["type"]
        if btype == "h1":
            # H1 = top-level; only first one becomes cover-ish, rest are major sections
            text = block["text"]
            anchor = slugify(text)
            body_parts.append(render_heading(1, text, anchor=anchor))
            toc_entries.append((anchor, text))
        elif btype == "h2":
            text = block["text"]
            anchor = slugify(text)
            body_parts.append(render_heading(2, text, anchor=anchor))
        elif btype == "h3":
            text = block["text"]
            anchor = slugify(text)
            body_parts.append(render_heading(3, text, anchor=anchor))
        elif btype == "h4":
            body_parts.append(render_heading(4, block["text"]))
        elif btype == "p":
            body_parts.append(render_paragraph(block["text"]))
        elif btype == "ul":
            body_parts.append(render_list(block["items"], ordered=False))
        elif btype == "ol":
            body_parts.append(render_list(block["items"], ordered=True))
        elif btype == "code":
            body_parts.append(render_code(block["text"]))
        elif btype == "table":
            body_parts.append(render_table(block["rows"]))
        elif btype == "blockquote":
            body_parts.append(render_blockquote(block["text"]))
        elif btype == "hr":
            body_parts.append("<hr>")

    body_html = "\n".join(body_parts)

    # Build TOC from h1 + h2 entries
    h1_anchors = [(a, t) for (a, t) in toc_entries]
    toc = render_toc(h1_anchors) if h1_anchors else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{_esc(title)}</title>
<style>{CSS}
/* Guide-specific overrides */
.guide-meta {{ color: #888; font-size: 9.5pt; font-style: italic; margin-top: 0.3em; }}
ol li, ul li {{ margin: 0.3em 0; }}
blockquote {{ border-left: 3px solid #999; padding: 0.4em 1em; margin: 1em 0; color: #555; font-style: italic; }}
</style>
</head>
<body>

<div class="cover">
    <div class="cover-content">
        <div class="cover-eyebrow">Operator Guide</div>
        <h1 class="cover-title">{_esc(title)}</h1>
        <div class="cover-rule"></div>
        <p class="cover-subtitle">Internal. Terse. 6 use cases + worked example.</p>
        <div class="cover-meta">
            <div class="cover-meta-row">
                <span class="cover-meta-label">Skill</span>
                <span class="cover-meta-value">axon-audit</span>
            </div>
            <div class="cover-meta-row">
                <span class="cover-meta-label">Version</span>
                <span class="cover-meta-value">v1.0</span>
            </div>
            <div class="cover-meta-row">
                <span class="cover-meta-label">Generated</span>
                <span class="cover-meta-value">2026-06-18</span>
            </div>
        </div>
    </div>
</div>

<div class="section" id="sec-toc">
    <h1>Contents</h1>
    {toc}
</div>

{body_html}

</body>
</html>
"""


# ---------------------------------------------------------------------------
# PDF conversion
# ---------------------------------------------------------------------------

def html_to_pdf(html_path: Path, pdf_path: Path) -> None:
    if not KIMI_PDF_HTML_TO_PDF.exists():
        raise FileNotFoundError(
            f"kimi-pdf html_to_pdf.js not found at {KIMI_PDF_HTML_TO_PDF}"
        )
    cmd = ["node", str(KIMI_PDF_HTML_TO_PDF), str(html_path), "--output", str(pdf_path)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if result.returncode != 0:
        print("STDOUT:", result.stdout, file=sys.stderr)
        print("STDERR:", result.stderr, file=sys.stderr)
        raise RuntimeError(f"PDF conversion failed (exit {result.returncode})")
    out_lines = [l for l in result.stdout.splitlines() if l.strip()][-10:]
    for line in out_lines:
        print(f"  {line}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="compile-guide")
    p.add_argument("--md", default=str(Path.home() / "axon-audit-operator-guide.md"), help="Input markdown path")
    p.add_argument("--pdf", default=str(Path.home() / "axon-audit-operator-guide.pdf"), help="Output PDF path")
    p.add_argument("--html-only", action="store_true", help="Only render HTML, skip PDF")
    p.add_argument("--keep-html", action="store_true", help="Keep intermediate HTML")
    args = p.parse_args(argv)

    md_path = Path(args.md)
    pdf_path = Path(args.pdf)

    if not md_path.exists():
        print(f"ERROR: markdown not found: {md_path}", file=sys.stderr)
        return 1

    md = md_path.read_text()
    blocks = parse_markdown(md)
    html = render_html(blocks)

    html_path = pdf_path.with_suffix(".html")
    html_path.write_text(html)
    print(f"OK Parsed {len(blocks)} blocks from {md_path}")
    print(f"  HTML: {html_path} ({len(html):,} chars)")

    if args.html_only:
        print("  --html-only set, skipping PDF.")
        return 0

    print(f"  Converting to PDF: {pdf_path}")
    html_to_pdf(html_path, pdf_path)
    print(f"  Done: {pdf_path}")

    if not args.keep_html:
        html_path.unlink()
        print(f"  Cleaned up intermediate HTML")

    return 0


if __name__ == "__main__":
    sys.exit(main())
