"""
report_template.py — HTML/CSS template for Axon Audit reports.

The template is a single self-contained HTML file. The kimi-pdf conversion
script (html_to_pdf.js) injects Paged.js automatically — DO NOT load it here.

Constraints followed (from kimi-pdf HTML route):
  - No CSS counters (Paged.js breaks them). Numbers written explicitly in HTML.
  - No emoji or decorative icons (font issues on Linux). Glyphs use text + CSS borders.
  - LaTeX academic style: three-line tables, light gray code, no shadows, no rounded borders.
  - All block elements max-width: 100% to prevent overflow.
  - body { text-align: justify; text-align-last: left } to prevent justified short lines.
  - Cover uses body{margin:0} + @page :first { margin: 0 } for full-bleed.
  - Page numbers via @page { @bottom-center { content: counter(page) } }.
  - Section IDs at container top for clickable cross-references.
"""

from __future__ import annotations
from typing import Any


# ---------------------------------------------------------------------------
# CSS — single string, embedded in the HTML head
# ---------------------------------------------------------------------------

CSS = """
/* --- Base reset (CRITICAL for cover full-bleed) --- */
body {
    margin: 0;
    padding: 0;
    font-family: "Liberation Serif", "DejaVu Serif", Georgia, "Times New Roman", serif;
    color: #222;
    line-height: 1.55;
    font-size: 11pt;
    text-align: justify;
    text-align-last: left;
}
a { color: #1a5490; text-decoration: none; word-break: break-all; }
a:hover { text-decoration: underline; }
code { font-family: "Liberation Mono", "DejaVu Sans Mono", monospace; font-size: 0.9em;
       background: #f5f5f5; padding: 0.1em 0.3em; border-radius: 0; }
pre { background: #f5f5f5; padding: 0.8em; overflow-x: auto; max-width: 100%;
      white-space: pre-wrap; word-wrap: break-word; border: 1px solid #ddd; }
pre code { background: transparent; padding: 0; }

/* --- Page setup --- */
@page {
    size: A4;
    margin: 2.5cm 2cm 2.5cm 2cm;
    @bottom-center { content: counter(page); font-size: 9pt; color: #888; }
}
@page :first { margin: 0; @bottom-center { content: none; } }
@page cover { margin: 0; @bottom-center { content: none; } }

/* --- Cover --- */
.cover {
    width: 210mm; height: 297mm; margin: 0; position: relative; overflow: hidden;
    page: cover; page-break-after: always; background: white;
}
.cover-content {
    position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
    text-align: center; width: 80%;
}
.cover-eyebrow {
    font-size: 11pt; color: #888; letter-spacing: 0.2em; text-transform: uppercase;
    margin-bottom: 1.5cm;
}
.cover-title {
    font-size: 32pt; font-weight: 700; color: #1a1a1a; margin: 0 0 0.5cm 0;
    line-height: 1.15;
}
.cover-subtitle {
    font-size: 16pt; color: #555; margin: 0 0 2.5cm 0; line-height: 1.4;
    font-style: italic;
}
.cover-rule {
    width: 4cm; height: 2px; background: #1a1a1a; margin: 0 auto 1.5cm auto;
}
.cover-meta {
    font-size: 12pt; color: #444; line-height: 1.9;
}
.cover-meta-row { margin: 0.2cm 0; }
.cover-meta-label { color: #888; font-size: 10pt; text-transform: uppercase;
                    letter-spacing: 0.1em; display: inline-block; width: 4cm; }
.cover-meta-value { color: #222; font-weight: 500; }

/* --- Typography --- */
h1, h2, h3, h4 { color: #1a1a1a; line-height: 1.25; page-break-after: avoid; }
h1 { font-size: 24pt; margin: 1.5em 0 0.6em 0; border-bottom: 2px solid #1a1a1a; padding-bottom: 0.2em; }
h2 { font-size: 17pt; margin: 1.8em 0 0.5em 0; }
h3 { font-size: 13pt; margin: 1.4em 0 0.4em 0; }
h4 { font-size: 11pt; margin: 1.2em 0 0.3em 0; font-weight: 700; }
p { margin: 0.6em 0; orphans: 2; widows: 2; }

/* --- Three-line tables (LaTeX booktabs) --- */
table {
    width: 100%; max-width: 100%; border-collapse: collapse; margin: 1em 0;
    border: none; border-top: 2px solid #1a1a1a; border-bottom: 2px solid #1a1a1a;
    overflow-x: auto;
}
thead th {
    border-bottom: 1.5px solid #1a1a1a; padding: 0.5em 0.7em; text-align: left;
    font-weight: 700; font-size: 10.5pt; background: transparent;
}
tbody td {
    border: none; padding: 0.5em 0.7em; vertical-align: top; font-size: 10.5pt;
}
tbody tr { page-break-inside: avoid; }
tbody tr:nth-child(even) td { background: #fafafa; }
caption {
    caption-side: top; text-align: left; font-weight: 600; font-size: 10.5pt;
    margin-bottom: 0.4em; color: #333;
}
caption::before { content: attr(data-label) "  "; font-weight: 700; }

/* --- Severity badges (no emoji, use text + border) --- */
.severity {
    display: inline-block; padding: 0.05em 0.5em; font-size: 9.5pt; font-weight: 700;
    border: 1.5px solid; line-height: 1.3; letter-spacing: 0.05em;
}
.severity-severe { color: #b00020; border-color: #b00020; background: #fff5f5; }
.severity-moderate { color: #c75b00; border-color: #c75b00; background: #fff8f0; }
.severity-informational { color: #2e7d32; border-color: #2e7d32; background: #f5fbf5; }
.severity-unverified { color: #555; border-color: #555; background: #f5f5f5; }
.severity-verified { color: #2e7d32; border-color: #2e7d32; background: #f5fbf5; }
.severity-flagged { color: #c75b00; border-color: #c75b00; background: #fff8f0; }
.severity-cut { color: #999; border-color: #999; background: #f5f5f5; text-decoration: line-through; }

/* --- Finding card (LaTeX theorem style, not UI card) --- */
.finding {
    border-left: 3px solid #1a1a1a; padding: 0.4em 0 0.4em 1em; margin: 1.2em 0;
    page-break-inside: avoid;
}
.finding-severe { border-left-color: #b00020; }
.finding-moderate { border-left-color: #c75b00; }
.finding-informational { border-left-color: #2e7d32; }
.finding-title { font-weight: 700; font-size: 12pt; margin: 0 0 0.3em 0; }
.finding-meta { font-size: 9.5pt; color: #666; margin: 0.3em 0; }
.finding-section { margin: 0.6em 0 0 0; }
.finding-section-label { font-weight: 700; color: #444; font-size: 10pt;
                          text-transform: uppercase; letter-spacing: 0.05em; }

/* --- Section dividers --- */
.section { page-break-before: always; }
.section:first-of-type { page-break-before: avoid; }

/* --- TOC --- */
.toc { list-style: none; padding: 0; margin: 1em 0; }
.toc li { margin: 0.4em 0; }
.toc a { display: flex; align-items: baseline; color: #222; }
.toc-num { display: inline-block; width: 2em; color: #888; }
.toc-title { flex: 1; }
.toc-dots { flex: 0 1 auto; border-bottom: 1px dotted #ccc; margin: 0 0.4em; min-width: 1em; }
.toc-page { color: #888; font-variant-numeric: tabular-nums; }

/* --- Quote / disclaimer box --- */
.disclaimer {
    border: 1px solid #999; padding: 0.8em 1em; margin: 1.5em 0;
    background: #fafafa; font-size: 10pt; line-height: 1.5;
    page-break-inside: avoid;
}
.disclaimer-title { font-weight: 700; color: #555; margin-bottom: 0.3em; font-size: 10.5pt;
                     text-transform: uppercase; letter-spacing: 0.05em; }

/* --- Executive summary list (3+2+1 pattern) --- */
.exec-section { margin: 1.2em 0; }
.exec-section-title { font-size: 13pt; font-weight: 700; margin-bottom: 0.4em;
                      padding-bottom: 0.2em; border-bottom: 1px solid #ddd; }
.exec-item { margin: 0.6em 0; padding-left: 1.6em; position: relative; }
.exec-item-num { position: absolute; left: 0; font-weight: 700; color: #1a1a1a; }
.exec-item-title { font-weight: 600; }
.exec-item-meta { font-size: 9.5pt; color: #666; margin-top: 0.2em; }

/* --- Overflow guards (CRITICAL per kimi-pdf route) --- */
pre, table, figure, img, svg, .mermaid, blockquote, .equation {
    max-width: 100%; box-sizing: border-box;
}
figure img, figure svg { max-width: 80%; max-height: 40vh; height: auto; }
.katex-display { overflow-x: auto; }
code { word-break: break-word; }

/* --- Agent appendix --- */
.agent-section { margin: 1.5em 0; page-break-inside: avoid; }
.agent-header { display: flex; align-items: baseline; gap: 0.6em; }
.agent-name { font-size: 12pt; font-weight: 700; color: #1a1a1a; }
.agent-wave { font-size: 9pt; color: #888; text-transform: uppercase; letter-spacing: 0.1em; }
.agent-content {
    margin-top: 0.5em; padding: 0.6em 0.8em; background: #fafafa;
    border-left: 2px solid #ccc; font-size: 10pt; line-height: 1.5;
    white-space: pre-wrap; word-wrap: break-word; max-width: 100%;
}
.agent-content h1, .agent-content h2, .agent-content h3 {
    font-size: 11pt; margin: 0.6em 0 0.3em 0; border: none; padding: 0;
    page-break-after: avoid;
}
.agent-content h2 { font-size: 10.5pt; }
.agent-content h3 { font-size: 10pt; }
.agent-content table { font-size: 9.5pt; }
"""


# ---------------------------------------------------------------------------
# HTML builders — each returns a string of HTML
# ---------------------------------------------------------------------------

def _esc(text: str) -> str:
    """HTML-escape text."""
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                .replace('"', "&quot;").replace("'", "&#39;"))


def render_cover(brief: dict[str, Any], manifest: dict[str, Any]) -> str:
    name = _esc(brief.get("name", "Untitled App"))
    app_type = _esc(brief.get("type", "—"))
    stage = _esc(brief.get("stage", "—"))
    url = _esc(brief.get("url", "")) or "—"
    description = _esc(brief.get("description", ""))
    started = manifest.get("started_at", "—")
    version = manifest.get("run_slug", "v1.0").rsplit("-", 2)[0]
    return f"""
<div class="cover">
    <div class="cover-content">
        <div class="cover-eyebrow">App Audit Report</div>
        <h1 class="cover-title">{name}</h1>
        <div class="cover-rule"></div>
        <p class="cover-subtitle">{description if description else "23-agent multi-wave audit with live fact-checking"}</p>
        <div class="cover-meta">
            <div class="cover-meta-row">
                <span class="cover-meta-label">Type</span>
                <span class="cover-meta-value">{app_type}</span>
            </div>
            <div class="cover-meta-row">
                <span class="cover-meta-label">Stage</span>
                <span class="cover-meta-value">{stage}</span>
            </div>
            <div class="cover-meta-row">
                <span class="cover-meta-label">URL</span>
                <span class="cover-meta-value">{url}</span>
            </div>
            <div class="cover-meta-row">
                <span class="cover-meta-label">Generated</span>
                <span class="cover-meta-value">{started}</span>
            </div>
            <div class="cover-meta-row">
                <span class="cover-meta-label">Report</span>
                <span class="cover-meta-value">{version} · v1.0</span>
            </div>
        </div>
    </div>
</div>
"""


def render_toc(sections: list[tuple[str, str]]) -> str:
    """sections = [(id, title), ...]"""
    items = "\n".join(
        f'    <li><a href="#{sid}"><span class="toc-num">{i+1}.</span>'
        f'<span class="toc-title">{_esc(title)}</span>'
        f'<span class="toc-dots"></span><span class="toc-page"></span></a></li>'
        for i, (sid, title) in enumerate(sections)
    )
    return f"""
<ul class="toc">
{items}
</ul>
"""


def render_executive_summary(exec_data: dict[str, Any]) -> str:
    """exec_data = { this_week: [...], next_quarter: [...], scary: {...} }
    Each item: {title, what, why, fix_time}
    """
    def render_list(items: list[dict[str, Any]]) -> str:
        if not items:
            return "<p><em>No items.</em></p>"
        out = []
        for i, it in enumerate(items, 1):
            out.append(
                f'<div class="exec-item">'
                f'<span class="exec-item-num">{i}.</span>'
                f'<span class="exec-item-title">{_esc(it.get("title", "—"))}</span>'
                f'<div class="exec-item-meta">'
                f'<strong>What:</strong> {_esc(it.get("what", "—"))}<br>'
                f'<strong>Why:</strong> {_esc(it.get("why", "—"))}'
                + (f'<br><strong>Fix time:</strong> {_esc(it["fix_time"])}' if it.get("fix_time") else "")
                + '</div></div>'
            )
        return "\n".join(out)

    return f"""
<div class="exec-section">
    <h3 class="exec-section-title">This Week — Severe, High ROI</h3>
    {render_list(exec_data.get("this_week", []))}
</div>
<div class="exec-section">
    <h3 class="exec-section-title">Next Quarter — Strategic</h3>
    {render_list(exec_data.get("next_quarter", []))}
</div>
<div class="exec-section">
    <h3 class="exec-section-title">What Scares Us — Critical Risk</h3>
    {render_list([exec_data["scary"]] if exec_data.get("scary") else [])}
</div>
"""


def render_findings_table(findings: list[dict[str, Any]]) -> str:
    """findings = [{id, severity, title, agent, cost_to_fix, verified}]"""
    rows = []
    for f in findings:
        sev = f.get("severity", "informational")
        sev_class = f"severity-{sev}"
        verified = f.get("verified", "unverified")
        v_class = f"severity-{verified}"
        rows.append(
            f'<tr>'
            f'<td>{_esc(f.get("id", "—"))}</td>'
            f'<td><span class="severity {sev_class}">{sev.upper()}</span></td>'
            f'<td>{_esc(f.get("title", "—"))}</td>'
            f'<td>{_esc(f.get("agent", "—"))}</td>'
            f'<td>{_esc(f.get("cost_to_fix", "—"))}</td>'
            f'<td><span class="severity {v_class}">{verified.upper()}</span></td>'
            f'</tr>'
        )
    return f"""
<table>
    <caption data-label="Table 1">Findings Summary</caption>
    <thead>
        <tr>
            <th style="width:8%">ID</th>
            <th style="width:12%">Severity</th>
            <th>Finding</th>
            <th style="width:14%">Agent</th>
            <th style="width:12%">Cost to Fix</th>
            <th style="width:14%">Verified</th>
        </tr>
    </thead>
    <tbody>
        {"".join(rows) if rows else '<tr><td colspan="6"><em>No findings.</em></td></tr>'}
    </tbody>
</table>
"""


def render_detailed_finding(f: dict[str, Any]) -> str:
    """One finding block. f has: id, severity, title, description, business_impact,
    cost_to_fix, cost_of_ignoring, verification, contrarian (optional)"""
    sev = f.get("severity", "informational")
    sev_class = f"finding-{sev}"
    return f"""
<div class="finding {sev_class}">
    <h3 class="finding-title" id="{_esc(f.get("id", ""))}">
        [{_esc(f.get("id", "—"))}] {_esc(f.get("title", "—"))}
        &nbsp;<span class="severity severity-{sev}">{sev.upper()}</span>
    </h3>
    <div class="finding-meta">
        Agent: {_esc(f.get("agent", "—"))} · Wave: {_esc(str(f.get("wave", "—")))} ·
        Verified: {_esc(f.get("verification", "unverified"))}
    </div>
    <div class="finding-section">
        <span class="finding-section-label">Technical Description</span>
        <p>{_esc(f.get("description", "—"))}</p>
    </div>
    <div class="finding-section">
        <span class="finding-section-label">Business Impact</span>
        <p>{_esc(f.get("business_impact", "—"))}</p>
    </div>
    <div class="finding-section">
        <span class="finding-section-label">Cost to Fix</span>
        <p>{_esc(f.get("cost_to_fix", "—"))}</p>
    </div>
    <div class="finding-section">
        <span class="finding-section-label">Cost of Ignoring</span>
        <p>{_esc(f.get("cost_of_ignoring", "—"))}</p>
    </div>
    {f'''<div class="finding-section">
        <span class="finding-section-label">Counter-argument (Contrarian)</span>
        <p>{_esc(f.get("contrarian", "—"))}</p>
    </div>''' if f.get("contrarian") else ""}
</div>
"""


def render_agent_appendix(agent_outputs: list[dict[str, Any]]) -> str:
    """agent_outputs = [{num, name, wave, status, content, verification}]"""
    parts = []
    for a in agent_outputs:
        verification = a.get("verification", "unverified")
        v_class = f"severity-{verification}"
        # Escape and lightly format agent markdown (very basic — just escape for now)
        # Full markdown→HTML conversion is a big lift; for the appendix we keep
        # the raw markdown text inside <pre> so it's readable. The actual agent
        # outputs are markdown, and the appendix is the raw output, so monospace
        # is appropriate.
        content = _esc(a.get("content", "(no output)"))
        parts.append(f"""
<div class="agent-section">
    <div class="agent-header">
        <span class="agent-name">{a['num']:02d} {_esc(a.get("name", "—"))}</span>
        <span class="agent-wave">Wave {_esc(str(a.get("wave", "—")))}</span>
        <span class="severity {v_class}">{verification.upper()}</span>
    </div>
    <div class="agent-content">{content}</div>
</div>
""")
    return "\n".join(parts)


def render_disclaimer() -> str:
    return """
<div class="disclaimer">
    <div class="disclaimer-title">Disclaimer</div>
    <p>This report was generated by an AI-assisted audit system. Recommendations should be
    reviewed by a qualified professional before implementation. The authors assume no liability
    for damages arising from the use or misuse of this report.</p>
    <p style="margin-top:0.5em;"><strong>Methodology:</strong> 23 agents across 5 waves
    (Reconnaissance, Risk Analysis, Code Quality, Founder Translation, Live Fact-Check).
    Each finding is verified against live internet sources (docs, CVEs, benchmarks,
    deprecation status). Findings that survive the Skeptic (must-fix vs nice-to-have)
    and the Contrarian (counter-arguments) make it into the final report.</p>
</div>
"""


def render_html(
    brief: dict[str, Any],
    manifest: dict[str, Any],
    exec_data: dict[str, Any],
    findings: list[dict[str, Any]],
    detailed_findings: list[dict[str, Any]],
    agent_outputs: list[dict[str, Any]],
) -> str:
    """Assemble the full report HTML."""
    cover = render_cover(brief, manifest)
    sections = [
        ("sec-exec",     "Executive Summary"),
        ("sec-summary",  "Findings Summary"),
        ("sec-detailed", "Detailed Findings"),
        ("sec-appendix", "Agent Reports (Appendix)"),
        ("sec-end",      "Disclaimer & Methodology"),
    ]
    toc = render_toc(sections)
    exec_html = render_executive_summary(exec_data)
    summary_table = render_findings_table(findings)
    detailed = "\n".join(render_detailed_finding(f) for f in detailed_findings)
    appendix = render_agent_appendix(agent_outputs)
    disclaimer = render_disclaimer()

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Axon Audit — {_esc(brief.get("name", "App"))}</title>
<style>{CSS}</style>
</head>
<body>
{cover}

<div class="section" id="sec-toc">
    <h1>Contents</h1>
    {toc}
</div>

<div class="section" id="sec-exec">
    <h1>1. Executive Summary</h1>
    {exec_html}
</div>

<div class="section" id="sec-summary">
    <h1>2. Findings Summary</h1>
    {len(findings)} findings &middot; {sum(1 for f in findings if f.get("severity") == "severe")} severe ·
    {sum(1 for f in findings if f.get("severity") == "moderate")} moderate ·
    {sum(1 for f in findings if f.get("severity") == "informational")} informational
    {summary_table}
</div>

<div class="section" id="sec-detailed">
    <h1>3. Detailed Findings</h1>
    {detailed if detailed else '<p><em>No findings to detail.</em></p>'}
</div>

<div class="section" id="sec-appendix">
    <h1>4. Agent Reports (Appendix)</h1>
    <p>Full output of each of the 23 agents, with verification status from the Live Fact-Check wave.</p>
    {appendix}
</div>

<div class="section" id="sec-end">
    <h1>5. Disclaimer &amp; Methodology</h1>
    {disclaimer}
</div>

</body>
</html>
"""
