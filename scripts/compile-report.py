#!/usr/bin/env python3
"""
compile-report.py — Convert an Axon Audit workspace into a final PDF report.

Usage:
    python3 compile-report.py <workspace>
    python3 compile-report.py /root/axon-audits/myapp-20260618-121928
    python3 compile-report.py <workspace> --html-only
    python3 compile-report.py <workspace> --output /path/to/report.pdf

Pipeline:
    1. Read brief.json, manifest.json, all-findings.json
    2. Walk waves/*/*.md to get all agent outputs
    3. Build the executive summary (3+2+1 pattern) from storyteller + doctor outputs
    4. Build the detailed-findings list from all-findings.json + impact map + contrarian
    5. Render HTML via report_template.render_html()
    6. Convert HTML to PDF via kimi-pdf's html_to_pdf.js
    7. Write <workspace>/final/audit-report.pdf (or --output path)
    8. Update manifest via mark_final
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from lib import AuditWorkspace, WAVES, write_json  # noqa: E402
from report_template import render_html  # noqa: E402

# Path to kimi-pdf's HTML→PDF converter
KIMI_PDF_HTML_TO_PDF = Path("/root/.agents/skills/kimi-pdf/scripts/html_to_pdf.js")


# ---------------------------------------------------------------------------
# Data mapping
# ---------------------------------------------------------------------------

def load_workspace(workspace: Path) -> AuditWorkspace:
    return AuditWorkspace.from_path(workspace)


def collect_agent_outputs(ws: AuditWorkspace) -> list[dict[str, Any]]:
    """Walk all wave outputs and return [{num, name, wave, content, status}]"""
    out = []
    for wave in WAVES:
        wdir = ws.wave_dir(wave["num"])
        for (num, slug, fname, fmt) in wave["agents"]:
            fpath = wdir / fname
            content = ""
            if fpath.exists():
                try:
                    content = fpath.read_text()
                except Exception:  # noqa: BLE001
                    content = "(could not read output)"
            else:
                content = "(no output written — agent may have failed)"
            agent_status = ws.manifest["waves"][str(wave["num"])]["agents"][str(num)]["status"]
            out.append({
                "num": num,
                "name": slug,
                "wave": wave["num"],
                "file": fname,
                "content": content,
                "status": agent_status,
            })
    return out


def get_agent_output(ws: AuditWorkspace, wave_num: int, slug: str) -> str:
    """Read a specific agent's output file as text. Returns '' if missing."""
    try:
        wave = next(w for w in WAVES if w["num"] == wave_num)
        agent = next(a for a in wave["agents"] if a[1] == slug)
        path = ws.wave_dir(wave_num) / agent[2]
        return path.read_text() if path.exists() else ""
    except (StopIteration, FileNotFoundError):
        return ""


def build_executive_summary(ws: AuditWorkspace) -> dict[str, Any]:
    """Parse the storyteller's output into {this_week, next_quarter, scary}.

    Falls back to top-severity findings if no storyteller output.
    """
    story = get_agent_output(ws, 4, "storyteller")
    critical = get_agent_output(ws, 3, "doctor")

    exec_data: dict[str, Any] = {"this_week": [], "next_quarter": [], "scary": {}}

    if story:
        # Parse the storyteller's structured output
        for section_key, header in [("this_week", "this week"), ("next_quarter", "next quarter")]:
            block = _extract_section(story, header)
            items = _parse_storyteller_items(block)
            exec_data[section_key] = items[:3 if section_key == "this_week" else 2]

        # "Scary" comes from the Storyteller's "## Scary thing" section
        scary_block = _extract_section(story, "scary thing")
        if scary_block:
            scary_items = _parse_storyteller_items(scary_block)
            if scary_items:
                exec_data["scary"] = scary_items[0]

    # Fallback: if no scary yet, try the Doctor (Wave 3, agent 13)
    if not exec_data.get("scary") and critical:
        m = re.search(r"## Component:\s*(.+?)\n\*\*Why:\*\*\s*(.+?)(?:\n|$)", critical)
        if m:
            exec_data["scary"] = {
                "title": m.group(1).strip(),
                "what": m.group(2).strip(),
                "why": "Single point of failure — if it goes down, the business stops",
                "fix_time": "Immediate",
            }

    # Fallbacks: if no storyteller, use top findings
    if not exec_data["this_week"] and not exec_data["scary"]:
        findings = _load_all_findings(ws)
        severe = [f for f in findings if f.get("severity") == "severe"][:3]
        moderate = [f for f in findings if f.get("severity") == "moderate"][:2]
        exec_data["this_week"] = [_finding_to_exec_item(f) for f in severe]
        exec_data["next_quarter"] = [_finding_to_exec_item(f) for f in moderate]
        if severe:
            exec_data["scary"] = _finding_to_exec_item(severe[0])

    return exec_data


def _extract_section(text: str, header: str) -> str:
    """Extract text under a '## Header' section until the next '## ' header."""
    lines = text.splitlines()
    out = []
    capturing = False
    for line in lines:
        s = line.strip()
        if s.lower().startswith("## "):
            if capturing:
                break
            if header.lower() in s.lower():
                capturing = True
                continue
        if capturing:
            out.append(line)
    return "\n".join(out)


def _parse_storyteller_items(block: str) -> list[dict[str, str]]:
    """Parse numbered subsections from a storyteller block.

    Pattern A:  ### 1. [title]
                **What:** ...
                **Why:** ...
                **Fix time:** ...

    Pattern B (scary section, single item, no number header):
                **What:** ...
                **Why:** ...
    """
    items = []
    # Split on ### N.
    parts = re.split(r"###\s*\d+\.\s*", block)
    for part in parts[1:]:
        title_match = re.match(r"([^\n]+)", part.strip())
        if not title_match:
            continue
        title = title_match.group(1).strip()
        what = _extract_field(part, "What")
        why = _extract_field(part, "Why")
        fix_time = _extract_field(part, "Fix time")
        items.append({"title": title, "what": what, "why": why, "fix_time": fix_time})

    # If no numbered sections but the block has What/Why fields, treat as a single item
    if not items and ("What:" in block or "Why:" in block):
        what = _extract_field(block, "What")
        why = _extract_field(block, "Why")
        fix_time = _extract_field(block, "Fix time")
        if what or why:
            items.append({
                "title": "Critical risk",
                "what": what,
                "why": why,
                "fix_time": fix_time or "Immediate",
            })
    return items


def _extract_field(text: str, field: str) -> str:
    m = re.search(rf"\*\*{field}:\*\*\s*(.+?)(?:\n|$)", text)
    return m.group(1).strip() if m else "—"


def _finding_to_exec_item(f: dict[str, Any]) -> dict[str, str]:
    return {
        "title": f.get("title") or f.get("raw", "")[:60] + "...",
        "what": f.get("raw", "—")[:200],
        "why": f.get("business_impact", "See detailed findings"),
        "fix_time": f.get("cost_to_fix", "TBD"),
    }


def build_findings_summary(all_findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert loaded findings into summary table rows."""
    rows = []
    for f in all_findings:
        raw = f.get("raw", "")
        title = raw[:100] + ("..." if len(raw) > 100 else "")
        rows.append({
            "id": f.get("id", "—"),
            "severity": f.get("severity", "informational"),
            "title": title,
            "agent": f.get("agent", "—"),
            "cost_to_fix": "—",
            "verified": f.get("verification", "unverified"),
        })
    return rows


def build_detailed_findings(ws: AuditWorkspace, all_findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compose detailed-finding blocks from the impact map (Wave 4) + raw findings.

    Each finding pulls:
      - title, description, business_impact, cost_to_fix, cost_of_ignoring from
        the impact map or from cost_to_fix
      - contrarian counter-argument from the contrarian output (Wave 5)
    """
    # Read impact map, cost_to_fix, and contrarian outputs
    impact_text = get_agent_output(ws, 4, "translator")
    cost_text = get_agent_output(ws, 4, "economist")
    contrarian_text = get_agent_output(ws, 5, "contrarian")

    # Parse impact map: ## Finding: [title]\n  **Severity:** ...\n  **Business impact:** ...
    impact_entries = _parse_impact_map(impact_text)
    cost_entries = _parse_cost_to_fix(cost_text)
    contrarian_entries = _parse_contrarian(contrarian_text)

    detailed = []
    for f in all_findings:
        raw = f.get("raw", "")
        # Match against impact entries by fuzzy title match
        match = _fuzzy_match(raw, impact_entries) or _fuzzy_match(raw, cost_entries)
        cost_match = _fuzzy_match(raw, cost_entries)
        contra_match = _fuzzy_match(raw, contrarian_entries)

        detailed.append({
            "id": f.get("id", "—"),
            "severity": f.get("severity", "informational"),
            "title": _shorten(raw, 80),
            "agent": f.get("agent", "—"),
            "wave": f.get("wave", "—"),
            "verification": f.get("verification", "unverified"),
            "description": raw,
            "business_impact": match.get("business_impact", "—") if match else "—",
            "cost_to_fix": cost_match.get("fix_estimate", "—") if cost_match else "—",
            "cost_of_ignoring": cost_match.get("cost_of_ignoring", "—") if cost_match else "—",
            "contrarian": contra_match.get("counter_argument", "") if contra_match else "",
        })
    return detailed


def _parse_impact_map(text: str) -> list[dict[str, str]]:
    """Parse translator output into {title, business_impact, urgency} entries."""
    entries = []
    blocks = re.split(r"##\s*Finding:\s*", text)
    for block in blocks[1:]:
        title_match = re.match(r"([^\n]+)", block.strip())
        if not title_match:
            continue
        title = title_match.group(1).strip()
        entries.append({
            "title": title,
            "business_impact": _extract_field(block, "Business impact"),
            "urgency": _extract_field(block, "Urgency"),
        })
    return entries


def _parse_cost_to_fix(text: str) -> list[dict[str, str]]:
    """Parse economist output into {title, fix_estimate, cost_of_ignoring} entries."""
    entries = []
    blocks = re.split(r"##\s*Finding:\s*", text)
    for block in blocks[1:]:
        title_match = re.match(r"([^\n]+)", block.strip())
        if not title_match:
            continue
        title = title_match.group(1).strip()
        entries.append({
            "title": title,
            "fix_estimate": _extract_field(block, "Fix estimate"),
            "cost_of_ignoring": _extract_field(block, "Cost of ignoring"),
        })
    return entries


def _parse_contrarian(text: str) -> list[dict[str, str]]:
    """Parse contrarian output into {title, counter_argument} entries."""
    entries = []
    blocks = re.split(r"##\s*Finding:\s*", text)
    for block in blocks[1:]:
        title_match = re.match(r"([^\n]+)", block.strip())
        if not title_match:
            continue
        title = title_match.group(1).strip()
        entries.append({
            "title": title,
            "counter_argument": _extract_field(block, "Counter-argument"),
        })
    return entries


def _fuzzy_match(raw: str, entries: list[dict[str, str]]) -> dict[str, str] | None:
    """Find the entry whose title has the most word overlap with raw text."""
    if not entries:
        return None
    raw_words = set(re.findall(r"\w+", raw.lower()))
    raw_words.discard("the")
    if not raw_words:
        return None
    best = None
    best_score = 0
    for entry in entries:
        title_words = set(re.findall(r"\w+", entry["title"].lower()))
        if not title_words:
            continue
        score = len(raw_words & title_words)
        if score > best_score:
            best = entry
            best_score = score
    # Require at least 2 words in common
    return best if best_score >= 2 else None


def _shorten(text: str, n: int) -> str:
    text = text.strip()
    return text[:n] + ("..." if len(text) > n else "")


def _load_all_findings(ws: AuditWorkspace) -> list[dict[str, Any]]:
    """Read all-findings.json and return the findings list.

    Verification status is threaded from the editor-in-chief output:
    findings listed in the "Surviving findings" section are marked verified.
    """
    path = ws.root / "final" / "all-findings.json"
    if not path.exists():
        return []
    findings = json.loads(path.read_text()).get("findings", [])

    # Read editor-in-chief output to thread verification status
    eic_text = get_agent_output(ws, 5, "editor-in-chief")
    surviving_titles: set[str] = set()
    flagged_titles: set[str] = set()
    cut_titles: set[str] = set()
    if eic_text:
        # Editor-in-chief uses **Surviving findings:**, **Flagged:**, **Cut:**
        # (bolded pseudo-headers, with optional count after the colon).
        # Also accept ## headers for flexibility.
        def _find_block(text: str, label: str) -> str | None:
            pat = rf"(?:#+\s*|\*\*)\s*{label}.*?(?:\*\*|\n)"
            m = re.search(pat, text, re.DOTALL | re.IGNORECASE)
            if not m:
                return None
            # Take everything from end of this match to the next blank-line + bold/header, or EOF
            start = m.end()
            end_match = re.search(
                r"\n\s*\n(?:\*\*|##)", text[start:], re.IGNORECASE
            )
            end = start + end_match.start() if end_match else len(text)
            return text[start:end]

        surviving_block = _find_block(eic_text, "Surviving findings")
        flagged_block = _find_block(eic_text, "Flagged")
        cut_block = _find_block(eic_text, "Cut")
        for block_text, target in [
            (surviving_block, surviving_titles),
            (flagged_block, flagged_titles),
            (cut_block, cut_titles),
        ]:
            if block_text:
                for line in block_text.splitlines():
                    line = line.strip().lstrip("-").lstrip("•").strip()
                    if line:
                        # Strip the "F1:" or "F1 " prefix
                        cleaned = re.sub(r"^F\d+[:\s\-]+", "", line)
                        # Strip severity parens like "(SEVERE) - VERIFIED"
                        cleaned = re.sub(
                            r"\s*\([A-Z]+\)\s*-\s*[A-Z]+\s*$",
                            "",
                            cleaned,
                            flags=re.IGNORECASE,
                        )
                        # Strip trailing status like " - VERIFIED", " - Confirmed, defer"
                        cleaned = re.sub(
                            r"\s*-\s*(Verified|Confirmed|Cut|Flagged|Overblown).*$",
                            "",
                            cleaned,
                            flags=re.IGNORECASE,
                        )
                        # Use first 5-6 significant words for matching
                        sig_words = " ".join(cleaned.split()[:6]).lower()
                        if sig_words and len(sig_words) > 5:
                            target.add(sig_words)

    # Match findings against the editor's lists using word overlap
    def _normalize(text: str) -> set[str]:
        """Lowercase words, drop short/stop words."""
        stop = {"the", "a", "an", "is", "are", "in", "on", "of", "for", "to", "and", "or"}
        return {w for w in re.findall(r"\w+", text.lower()) if w not in stop and len(w) > 2}

    def _find_in_editor(raw: str) -> str:
        raw_words = _normalize(raw)
        if not raw_words:
            return "unverified"
        best_match = "unverified"
        best_overlap = 0
        for title, status in [
            *((t, "verified") for t in surviving_titles),
            *((t, "flagged") for t in flagged_titles),
            *((t, "cut") for t in cut_titles),
        ]:
            title_words = _normalize(title)
            overlap = len(raw_words & title_words)
            # Need at least 2 words in common
            if overlap >= 2 and overlap > best_overlap:
                best_match = status
                best_overlap = overlap
        return best_match

    for f in findings:
        f["verification"] = _find_in_editor(f.get("raw", ""))
    return findings


# ---------------------------------------------------------------------------
# PDF conversion
# ---------------------------------------------------------------------------

def html_to_pdf(html_path: Path, pdf_path: Path) -> None:
    """Run kimi-pdf's html_to_pdf.js to convert HTML to PDF."""
    if not KIMI_PDF_HTML_TO_PDF.exists():
        raise FileNotFoundError(
            f"kimi-pdf html_to_pdf.js not found at {KIMI_PDF_HTML_TO_PDF}. "
            f"Check that kimi-pdf is installed."
        )
    cmd = ["node", str(KIMI_PDF_HTML_TO_PDF), str(html_path), "--output", str(pdf_path)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if result.returncode != 0:
        print("STDOUT:", result.stdout, file=sys.stderr)
        print("STDERR:", result.stderr, file=sys.stderr)
        raise RuntimeError(f"PDF conversion failed (exit {result.returncode})")
    # Print only the last few lines of output (page count, warnings)
    out_lines = [l for l in result.stdout.splitlines() if l.strip()][-10:]
    for line in out_lines:
        print(f"  {line}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="compile-report",
        description="Compile an Axon Audit workspace into a PDF report",
    )
    p.add_argument("workspace", help="Path to audit workspace")
    p.add_argument("--output", "-o", help="Override output PDF path (default: <workspace>/final/audit-report.pdf)")
    p.add_argument("--html-only", action="store_true", help="Only render HTML, skip PDF conversion")
    p.add_argument("--keep-html", action="store_true", help="Keep the intermediate HTML file (for debugging)")
    args = p.parse_args(argv)

    ws = load_workspace(Path(args.workspace))
    print(f"Compiling report for: {ws.slug}")
    print(f"  Workspace: {ws.root}")

    # 1. Gather data
    print("  Reading workspace data...")
    exec_data = build_executive_summary(ws)
    all_findings = _load_all_findings(ws)
    summary_rows = build_findings_summary(all_findings)
    detailed = build_detailed_findings(ws, all_findings)
    agent_outputs = collect_agent_outputs(ws)
    print(f"  Findings: {len(all_findings)} | Detailed: {len(detailed)} | Agents: {len(agent_outputs)}")

    # 2. Render HTML
    print("  Rendering HTML...")
    html = render_html(
        brief=ws.brief,
        manifest=ws.manifest,
        exec_data=exec_data,
        findings=summary_rows,
        detailed_findings=detailed,
        agent_outputs=agent_outputs,
    )
    html_path = ws.root / "final" / "report.html"
    html_path.write_text(html)
    print(f"  HTML: {html_path} ({len(html):,} chars)")

    if args.html_only:
        print("  --html-only set, skipping PDF conversion.")
        return 0

    # 3. Convert to PDF
    pdf_path = Path(args.output) if args.output else (ws.root / "final" / "audit-report.pdf")
    print(f"  Converting to PDF: {pdf_path}")
    html_to_pdf(html_path, pdf_path)

    # 4. Mark final in manifest
    ws.mark_final("done", path=str(pdf_path))
    print(f"  Done. PDF: {pdf_path}")

    if not args.keep_html:
        # Keep HTML for debugging but mention it
        print(f"  Intermediate HTML: {html_path} (use --html-only next time)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
