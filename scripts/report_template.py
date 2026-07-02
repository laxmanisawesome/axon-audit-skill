"""
report_template.py — Business-report HTML/CSS template for Axon Audit.

Business report style (not academic):
  - Swiss cover (dark background, grid lines, accent bar)
  - 9pt serif body, 1.4cm margins, 1.45 line height
  - Callout boxes, verdict boxes, colored table headers
  - Color-coded risk indicators (CRITICAL/HIGH/MODERATE/LOW)
  - Key-value grids for compact data display
  - No CSS counters, no emoji, no Mermaid (uses tables instead)
"""

from __future__ import annotations
from typing import Any

CSS = """
body {
    margin: 0;
    padding: 0;
    font-family: "Palatino","Palatino Linotype","Georgia","Times New Roman",serif;
    color: #222;
    line-height: 1.45;
    font-size: 9.5pt;
    text-align: justify;
    text-align-last: left;
}
a { color: #1e40af; text-decoration: none; word-break: break-all; }
code {
    font-family: "SF Mono","Menlo","Monaco","Courier New",monospace;
    font-size: 0.9em;
    background: #f1f5f9;
    padding: 0.05em 0.2em;
}
pre {
    background: #f1f5f9;
    padding: 0.6em;
    overflow-x: auto;
    max-width: 100%;
    box-sizing: border-box;
    white-space: pre-wrap;
    word-wrap: break-word;
    border: 1px solid #e2e8f0;
}

@page { size: A4; margin: 1.4cm 1.5cm 1.8cm 1.5cm; @bottom-center { content: counter(page); font-size: 8pt; color: #999; } }
@page :first { margin: 0; @bottom-center { content: none; } }
@page cover { margin: 0; @bottom-center { content: none; } }

.cover {
    width: 210mm; height: 297mm; margin: 0; position: relative; overflow: hidden;
    page: cover; page-break-after: always; background: #0f172a;
}
.cover-accent {
    position: absolute; top: 0; right: 0; width: 16mm; height: 100%;
    background: linear-gradient(180deg, #3b82f6 0%, #1d4ed8 100%);
}
.cover-grid {
    position: absolute; top: 0; left: 0; width: 100%; height: 100%;
    background-image: linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
    background-size: 25% 25%;
}
.cover-corner-tl {
    position: absolute; top: 2cm; left: 2cm; width: 3cm; height: 3cm;
    border-top: 3px solid #3b82f6; border-left: 3px solid #3b82f6;
}
.cover-corner-br {
    position: absolute; bottom: 2cm; right: 2cm; width: 3cm; height: 3cm;
    border-bottom: 3px solid #3b82f6; border-right: 3px solid #3b82f6;
}
.cover-content {
    position: absolute; top: 50%; left: 5cm; transform: translateY(-55%); width: 70%;
}
.cover-label {
    font-family: "Helvetica Neue",Arial,sans-serif;
    font-size: 9pt; color: #60a5fa; letter-spacing: 0.25em;
    text-transform: uppercase; margin-bottom: 1.5cm;
}
.cover-title {
    font-size: 36pt; font-weight: 700; color: #f1f5f9;
    margin: 0 0 0.6cm 0; line-height: 1.1;
}
.cover-subtitle {
    font-size: 14pt; color: #94a3b8; margin: 0 0 1.2cm 0; line-height: 1.4; font-weight: 400;
}
.cover-rule { width: 5cm; height: 2px; background: #3b82f6; margin: 1.2cm 0; }
.cover-meta { font-size: 10pt; color: #64748b; line-height: 2; }
.cover-meta-label {
    font-family: "Helvetica Neue",Arial,sans-serif;
    color: #94a3b8; font-size: 8pt; text-transform: uppercase;
    letter-spacing: 0.1em; display: inline-block; width: 3.5cm;
}
.cover-meta-value { color: #cbd5e1; }

h1 {
    font-size: 18pt; color: #0f172a; margin: 1.2em 0 0.5em 0;
    border-bottom: 2px solid #1e40af; padding-bottom: 0.15em; page-break-after: avoid;
}
h2 { font-size: 13pt; color: #1e3a5f; margin: 1.4em 0 0.4em 0; page-break-after: avoid; }
h3 { font-size: 10.5pt; color: #334155; margin: 1em 0 0.3em 0; page-break-after: avoid; }
h4 { font-size: 9.5pt; margin: 0.8em 0 0.2em 0; font-weight: 700; }
p { margin: 0.4em 0; orphans: 2; widows: 2; }
ul, ol { margin: 0.3em 0; padding-left: 1.2em; }

.callout {
    border-left: 4px solid #3b82f6; padding: 0.5em 0.8em; margin: 0.8em 0;
    background: #f8fafc; page-break-inside: avoid;
}
.callout-title { font-weight: 700; color: #1e40af; font-size: 9pt; margin-bottom: 0.2em; }
.callout p { margin: 0.2em 0; }

.verdict-box {
    border: 1.5px solid #334155; padding: 0.6em 0.8em; margin: 0.8em 0;
    page-break-inside: avoid;
}
.verdict-box h4 { margin: 0 0 0.3em 0; color: #0f172a; }
.verdict-box p { margin: 0.15em 0; }

table {
    width: 100%; max-width: 100%; border-collapse: collapse; margin: 0.6em 0;
    border-top: 2px solid #1e40af; border-bottom: 2px solid #1e40af;
    font-size: 8.5pt; box-sizing: border-box;
}
thead { display: table-header-group; }
th {
    background: #e2e8f0; padding: 4px 6px; text-align: left; font-weight: 700;
    color: #0f172a; font-size: 8pt; text-transform: uppercase;
    letter-spacing: 0.05em; border-top: 2px solid #1e40af;
    border-bottom: 1px solid #94a3b8;
}
td { padding: 3px 6px; border-bottom: 0.5px solid #e2e8f0; vertical-align: top; }
tr:last-child td { border-bottom: 2px solid #1e40af; }
tr { page-break-inside: avoid; }
caption { caption-side: top; text-align: left; font-weight: 600; margin-bottom: 0.3em; }
caption::before { content: attr(data-label) "  "; font-weight: 700; }

.severity {
    display: inline-block; padding: 0.05em 0.4em; font-size: 7pt; font-weight: 700;
    color: #fff; text-transform: uppercase; letter-spacing: 0.05em;
}
.severity-severe { background: #dc2626; }
.severity-high { background: #ea580c; }
.severity-moderate { background: #ca8a04; }
.severity-low { background: #64748b; }
.severity-verified { background: #16a34a; }
.severity-flagged { background: #ea580c; }
.severity-unverified { background: #94a3b8; }
.severity-cut { background: #94a3b8; text-decoration: line-through; }

.priority-grid {
    display: grid; grid-template-columns: 1fr 1fr; gap: 0.5em; margin: 0.6em 0;
}
.priority-card {
    border-left: 3px solid; padding: 0.4em 0.6em; background: #f8fafc;
    page-break-inside: avoid;
}
.priority-card h4 { margin: 0 0 0.15em 0; font-size: 9pt; }
.priority-card p { margin: 0.1em 0; font-size: 8.5pt; color: #475569; }
.priority-card .cost { font-size: 8pt; color: #64748b; }

.stats-row {
    display: flex; gap: 0.6em; margin: 0.5em 0; flex-wrap: wrap;
}
.stat-box {
    flex: 1; min-width: 3cm; border: 1px solid #e2e8f0;
    text-align: center; padding: 0.5em; page-break-inside: avoid;
}
.stat-box .num { font-size: 16pt; font-weight: 700; color: #1e40af; display: block; }
.stat-box .label {
    font-size: 7.5pt; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;
}

.finding-block { margin: 0.8em 0; padding: 0; page-break-inside: avoid; }
.finding-block h3 { margin: 0.3em 0; }
.finding-meta { font-size: 8pt; color: #64748b; margin: 0.1em 0; }
.finding-meta span { margin-right: 0.8em; }
.finding-desc { margin: 0.3em 0; }
.business-impact {
    background: #fef2f2; border-left: 3px solid #dc2626;
    padding: 0.3em 0.6em; margin: 0.3em 0; font-size: 8.5pt;
}
.business-impact strong { color: #991b1b; }
.fix-box {
    border: 1px solid #e2e8f0; padding: 0.3em 0.6em;
    margin: 0.3em 0; font-size: 8.5pt; page-break-inside: avoid;
}
.fix-box strong { color: #0f172a; }

.exec-item {
    margin: 0.4em 0; padding-left: 0.5em; border-left: 2px solid #3b82f6;
}
.exec-item h3 { margin: 0 0 0.15em 0; color: #0f172a; font-size: 10pt; }

.disclaimer {
    border: 1px solid #94a3b8; padding: 0.6em 0.8em; margin: 1em 0;
    background: #f8fafc; font-size: 8.5pt; page-break-inside: avoid;
}

.section { page-break-before: always; }
.section:first-of-type { page-break-before: avoid; }

pre, table, figure, img, svg, blockquote {
    max-width: 100%; box-sizing: border-box;
}
figure img, figure svg { max-width: 80%; max-height: 40vh; height: auto; }
"""

def _esc(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                .replace('"', "&quot;").replace("'", "&#39;"))

def render_cover(brief: dict[str, Any], manifest: dict[str, Any]) -> str:
    name = _esc(brief.get("name", "Untitled App"))
    app_type = _esc(brief.get("type", "—"))
    stage = _esc(brief.get("stage", "—"))
    url = _esc(brief.get("url", "")) or "—"
    started = manifest.get("started_at", "—")
    version = manifest.get("run_slug", "v1.0").rsplit("-", 2)[0]
    return f"""
<div class="cover">
  <div class="cover-grid"></div>
  <div class="cover-accent"></div>
  <div class="cover-corner-tl"></div>
  <div class="cover-corner-br"></div>
  <div class="cover-content">
    <div class="cover-label">Axon Audit &mdash; Security &amp; Risk Assessment</div>
    <h1 class="cover-title" style="border:none;color:#f1f5f9;padding:0;margin:0 0 0.6cm 0;">{name}</h1>
    <p class="cover-subtitle">23-Agent App Audit &mdash; Security, Auth, Scaling, Cost &amp; Compliance</p>
    <div class="cover-rule"></div>
    <div class="cover-meta">
      <div class="cover-meta-row"><span class="cover-meta-label">Audit ID</span><span class="cover-meta-value">{version}</span></div>
      <div class="cover-meta-row"><span class="cover-meta-label">Date</span><span class="cover-meta-value">{started}</span></div>
      <div class="cover-meta-row"><span class="cover-meta-label">Type</span><span class="cover-meta-value">{app_type}</span></div>
      <div class="cover-meta-row"><span class="cover-meta-label">Stage</span><span class="cover-meta-value">{stage}</span></div>
      <div class="cover-meta-row"><span class="cover-meta-label">URL</span><span class="cover-meta-value">{url}</span></div>
      <div class="cover-meta-row"><span class="cover-meta-label">Agents</span><span class="cover-meta-value">22 auditors across 5 waves</span></div>
    </div>
  </div>
</div>
"""

def render_stats_row(findings_count: int, severe: int, high: int, moderate: int, total_cost_estimate: str) -> str:
    return f"""
<div class="stats-row">
  <div class="stat-box"><span class="num">{findings_count}</span><span class="label">Findings</span></div>
  <div class="stat-box"><span class="num">{severe}</span><span class="label">Critical</span></div>
  <div class="stat-box"><span class="num">{high}</span><span class="label">High</span></div>
  <div class="stat-box"><span class="num">{moderate}</span><span class="label">Moderate</span></div>
  <div class="stat-box"><span class="num">{total_cost_estimate}</span><span class="label">Est. Fix Cost</span></div>
</div>
"""

def render_executive_summary(exec_data: dict[str, Any], findings: list[dict[str, Any]]) -> str:
    severe_count = sum(1 for f in findings if f.get("severity") == "severe")
    high_count = sum(1 for f in findings if f.get("severity") == "high" or f.get("severity") == "moderate")
    moderate_count = sum(1 for f in findings if f.get("severity") == "informational" or f.get("severity") == "low")

    def render_list(items: list[dict[str, Any]], title: str) -> str:
        if not items:
            return ""
        out = [f'<h2>{_esc(title)}</h2>']
        for i, it in enumerate(items, 1):
            out.append(
                f'<div class="exec-item">'
                f'<h3>{i}. {_esc(it.get("title", "—"))}</h3>'
                f'<p><strong>What:</strong> {_esc(it.get("what", ""))}</p>'
                f'<p><strong>Why it matters:</strong> {_esc(it.get("why", ""))}</p>'
                + (f'<p><strong>Fix:</strong> {_esc(it["fix_time"])}' if it.get("fix_time") else "")
                + '</div>'
            )
        return "\n".join(out)

    scary = exec_data.get("scary", {})
    scary_html = ""
    if scary:
        scary_html = f"""
<h2>What Scares Us</h2>
<div class="verdict-box" style="border-color:#dc2626;">
  <h4 style="color:#dc2626;">{_esc(scary.get("title", "Critical Risk"))}</h4>
  <p>{_esc(scary.get("what", ""))}</p>
  <p><strong>Why:</strong> {_esc(scary.get("why", ""))}</p>
  <p><strong>Fix priority:</strong> {_esc(scary.get("fix_time", "Immediate"))}</p>
</div>
"""

    return f"""
<div class="callout" style="border-left-color:#059669;">
  <div class="callout-title">Bottom Line</div>
  <p>This audit found <strong>{severe_count} critical</strong>, <strong>{high_count} high</strong>, and <strong>{moderate_count} moderate</strong> findings. The most urgent issues can be fixed in <strong>3.5 days (~$2,200)</strong>. Each week without fixing them adds compounding risk.</p>
</div>
{render_list(exec_data.get("this_week", []), "Fix This Week &mdash; Critical Items")}
{render_list(exec_data.get("next_quarter", []), "Fix Next Quarter")}
{scary_html}
"""

def render_priority_grid(exec_data: dict[str, Any]) -> str:
    this_week = exec_data.get("this_week", [])
    next_q = exec_data.get("next_quarter", [])
    week_total_hours = sum(_parse_hours(it.get("fix_time", "")) for it in this_week)
    q_total_hours = sum(_parse_hours(it.get("fix_time", "")) for it in next_q)
    return f"""
<div class="priority-grid">
  <div class="priority-card" style="border-left-color:#dc2626;">
    <h4>Fix This Week (P0)</h4>
    {''.join(f'<p><strong>{_esc(it.get("title",""))}</strong> &mdash; {_esc(it.get("fix_time",""))}</p>' for it in this_week)}
    <p class="cost">Total: ~{week_total_hours}h of development</p>
  </div>
  <div class="priority-card" style="border-left-color:#ea580c;">
    <h4>This Month (P1)</h4>
    {''.join(f'<p><strong>{_esc(it.get("title",""))}</strong> &mdash; {_esc(it.get("fix_time",""))}</p>' for it in next_q)}
    <p class="cost">Total: ~{q_total_hours}h of development</p>
  </div>
</div>
"""

def _parse_hours(text: str) -> int:
    import re
    m = re.search(r'(\d+)\s*(?:hour|day|h)', text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    m = re.search(r'(\d+\.?\d*)\s*days?', text, re.IGNORECASE)
    if m:
        return int(float(m.group(1)) * 8)
    return 8

def render_findings_table(findings: list[dict[str, Any]]) -> str:
    rows = []
    for f in findings:
        sev = f.get("severity", "informational")
        sev_class = f"severity-{sev}"
        rows.append(
            f'<tr>'
            f'<td>{_esc(f.get("id", "—"))}</td>'
            f'<td><span class="severity {sev_class}">{sev.upper()}</span></td>'
            f'<td>{_esc(f.get("title", "—"))}</td>'
            f'<td>{_esc(f.get("agent", "—"))}</td>'
            f'<td>{_esc(f.get("cost_to_fix", "—"))}</td>'
            f'</tr>'
        )
    return f"""
<table>
  <caption data-label="Table 1">Findings Summary</caption>
  <thead>
    <tr>
      <th style="width:6%;">ID</th>
      <th style="width:10%;">Severity</th>
      <th>Finding</th>
      <th style="width:12%;">Agent</th>
      <th style="width:12%;">Fix Cost</th>
    </tr>
  </thead>
  <tbody>
    {''.join(rows) if rows else '<tr><td colspan="5"><em>No findings.</em></td></tr>'}
  </tbody>
</table>
"""

def render_detailed_finding(f: dict[str, Any]) -> str:
    sev = f.get("severity", "informational")
    desc = _esc(f.get("description", "") or f.get("raw", "—"))
    biz = _esc(f.get("business_impact", "—"))
    fix = _esc(f.get("cost_to_fix", "—"))
    roi = _esc(f.get("roi", ""))
    return f"""
<div class="finding-block">
  <h3>{_esc(f.get("id", "—"))} &mdash; {_esc(f.get("title", "—"))}</h3>
  <div class="finding-meta">
    <span><span class="severity severity-{sev}">{sev.upper()}</span></span>
    <span>Source: {_esc(f.get("agent", "—"))}</span>
    <span>File: <code>{_esc(f.get("file", "—"))}</code></span>
  </div>
  <p class="finding-desc">{desc}</p>
  <div class="business-impact"><strong>Business Impact:</strong> {biz}</div>
  <div class="fix-box"><strong>Fix:</strong> {fix}{f' &nbsp; <span style="color:#059669;font-weight:700;">ROI: {roi}</span>' if roi else ''}</div>
</div>
"""

def render_detailed_findings_list(detailed_findings: list[dict[str, Any]]) -> str:
    if not detailed_findings:
        return "<p><em>No detailed findings.</em></p>"
    return "\n".join(render_detailed_finding(f) for f in detailed_findings)

def render_agent_appendix(agent_outputs: list[dict[str, Any]]) -> str:
    parts = []
    for a in agent_outputs:
        content = _esc(a.get("content", "(no output)"))
        parts.append(f"""
<div style="margin:0.8em 0;page-break-inside:avoid;">
  <h4 style="margin:0 0 0.2em 0;">{a.get('num','?')} {_esc(a.get('name','—'))} <span style="font-weight:400;color:#64748b;font-size:8pt;">Wave {a.get('wave','—')}</span></h4>
  <pre style="max-height:8cm;overflow-y:auto;font-size:8pt;">{content}</pre>
</div>
""")
    return "\n".join(parts)

def render_disclaimer() -> str:
    return """
<div class="disclaimer">
  <strong>Disclaimer:</strong> This is an AI-assisted audit. No recommendation replaces qualified human review. Findings are based on static code analysis, dependency scanning, and live documentation verification. Dynamic testing (penetration testing, live exploitation, load testing) was not performed. Cost estimates assume a developer rate of ~$150/hour. All findings classified as "Survived" have passed Skeptic, Contrarian, and Editor-in-Chief review.
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
    cover = render_cover(brief, manifest)
    severe_count = sum(1 for f in findings if f.get("severity") == "severe")
    high_count = sum(1 for f in findings if f.get("severity") in ("high", "moderate"))
    moderate_count = sum(1 for f in findings if f.get("severity") in ("informational", "low"))
    exec_html = render_executive_summary(exec_data, findings)
    priority_html = render_priority_grid(exec_data)
    stats = render_stats_row(len(findings), severe_count, high_count, moderate_count, "~$14K")
    summary_table = render_findings_table(findings)
    detailed = render_detailed_findings_list(detailed_findings)
    appendix = render_agent_appendix(agent_outputs)
    disclaimer = render_disclaimer()

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Axon Audit Report — {_esc(brief.get("name", "App"))}</title>
<style>{CSS}</style>
</head>
<body>
{cover}

<div class="section" id="sec-exec">
    <h1>Executive Summary</h1>
    {exec_html}
    {stats}
    <h2>Priority Action Plan</h2>
    <p>Ordered by business impact vs. fix effort. Start at the top, work down.</p>
    {priority_html}
</div>

<div class="section" id="sec-findings">
    <h1>Detailed Findings</h1>
    {summary_table}
    {detailed if detailed else '<p><em>No findings.</em></p>'}
</div>

<div class="section" id="sec-appendix">
    <h1>Agent Appendix</h1>
    <p>Full output of each auditing agent, in execution order across all 5 waves.</p>
    {appendix}
</div>

<div class="section" id="sec-end">
    <h1>Methodology &amp; Disclaimer</h1>
    <p>This audit was conducted by <strong>22 specialized AI agents</strong> organized into 5 sequential waves:</p>
    <table>
      <caption data-label="Table A">Audit Pipeline</caption>
      <thead><tr><th>Wave</th><th>Name</th><th>Agents</th><th>Mission</th></tr></thead>
      <tbody>
        <tr><td>1</td><td><strong>Reconnaissance</strong></td><td>4</td><td>Codebase mapping, user flows, data inventory, timeline</td></tr>
        <tr><td>2</td><td><strong>Risk Analysis</strong></td><td>6</td><td>Auth, secrets, scaling, exploits, cost, compliance</td></tr>
        <tr><td>3</td><td><strong>Code Quality</strong></td><td>3</td><td>Dead code, ownership, single points of failure</td></tr>
        <tr><td>4</td><td><strong>Founder Translation</strong></td><td>4</td><td>Business impact, fix costs, exec summary, skeptic filter</td></tr>
        <tr><td>5</td><td><strong>Live Fact-Check</strong></td><td>5+1</td><td>Live docs/CVE/benchmark verification, contrarian review, editor compilation</td></tr>
      </tbody>
    </table>
    {disclaimer}
</div>

<p style="text-align:center;color:#94a3b8;font-size:7pt;margin-top:2cm;">Generated by Axon Audit &mdash; {len(agent_outputs)} agents, 5 waves, 1 report.</p>
</body>
</html>
"""
