#!/usr/bin/env python3
"""
Axon Audit — Library Helpers
=============================

I/O helpers for the Axon Audit orchestrator. The orchestrator is driven
by a main OpenCode agent (which calls the `task` tool); these helpers do
the file scaffolding and context-aggregation that surround those calls.

Public API:
    AuditWorkspace  — represents one audit run, owns its directory tree
    parse_brief()   — parse a brief from markdown, JSON, or CLI dict
    build_context() — assemble context.json for a wave from prior outputs
    save_finding()  — append a normalized finding to all-findings.json
    write_manifest() — update the run-level manifest.json

Workspace layout (created by init_workspace):
    ~/.axon-audits/<slug>-<YYYYMMDD-HHMMSS>/
    ├── brief.json
    ├── manifest.json
    ├── waves/
    │   ├── 01-recon/
    │   │   ├── 01-cartographer.json
    │   │   ├── 02-tour-guide.md
    │   │   ├── 03-librarian.json
    │   │   ├── 04-timekeeper.md
    │   │   └── context.json           # inputs for Wave 2
    │   ├── 02-risk/
    │   │   ├── 05-bouncer.md
    │   │   ├── ... (06..10)
    │   │   └── context.json
    │   ├── 03-quality/   (11, 12, 13)
    │   ├── 04-translate/ (14, 15, 16, 17)
    │   └── 05-verify/    (18, 19, 20, 21, 22, 23)
    └── final/
        ├── all-findings.json
        └── report-source.md           # markdown source for compile-report.py
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

WORKSPACE_ROOT = Path.home() / ".axon-audits"
SKILL_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = SKILL_ROOT / "templates" / "agent-prompts"
REFERENCES_DIR = SKILL_ROOT / "references"

# Wave → (slug, agent definitions)  agent definitions are (num, slug, file, fmt)
# fmt = "json" or "md"
WAVES: list[dict[str, Any]] = [
    {
        "num": 1,
        "slug": "recon",
        "name": "Reconnaissance",
        "agents": [
            (1, "cartographer", "01-cartographer.json", "json"),
            (2, "tour-guide",   "02-tour-guide.md",     "md"),
            (3, "librarian",    "03-librarian.json",    "json"),
            (4, "timekeeper",   "04-timekeeper.md",     "md"),
        ],
        "context_includes_brief": True,
    },
    {
        "num": 2,
        "slug": "risk",
        "name": "Risk Analysis",
        "agents": [
            (5,  "bouncer",        "05-bouncer.md",         "md"),
            (6,  "locksmith",      "06-locksmith.md",       "md"),
            (7,  "stress-tester",  "07-stress-tester.md",   "md"),
            (8,  "exploit-hunter", "08-exploit-hunter.md",  "md"),
            (9,  "cost-auditor",   "09-cost-auditor.md",    "md"),
            (10, "compliance",     "10-compliance.md",      "md"),
        ],
        "context_includes_brief": False,
    },
    {
        "num": 3,
        "slug": "quality",
        "name": "Code Quality & Ownership",
        "agents": [
            (11, "janitor",   "11-janitor.md",   "md"),
            (12, "archivist", "12-archivist.md", "md"),
            (13, "doctor",    "13-doctor.md",    "md"),
        ],
        "context_includes_brief": False,
    },
    {
        "num": 4,
        "slug": "translate",
        "name": "Founder Translation",
        "agents": [
            (14, "translator", "14-translator.md", "md"),
            (15, "economist",  "15-economist.md",  "md"),
            (16, "storyteller", "16-storyteller.md", "md"),
            (17, "skeptic",    "17-skeptic.md",    "md"),
        ],
        "context_includes_brief": True,  # founder context re-injected here
    },
    {
        "num": 5,
        "slug": "verify",
        "name": "Live Fact-Check",
        "agents": [
            (18, "documentarian",     "18-documentarian.md",     "md"),
            (19, "news-hound",        "19-news-hound.md",        "md"),
            (20, "benchmarker",       "20-benchmarker.md",       "md"),
            (21, "deprecation-hunter","21-deprecation-hunter.md","md"),
            (22, "contrarian",        "22-contrarian.md",        "md"),
            (23, "editor-in-chief",   "23-editor-in-chief.md",   "md"),
        ],
        "context_includes_brief": False,
    },
]

# Human-friendly labels for severity levels
SEVERITIES = {"severe", "moderate", "informational", "info"}
SEVERITY_GLYPH = {"severe": "🔴", "moderate": "🟠", "informational": "🟢", "info": "🟢"}


# ---------------------------------------------------------------------------
# AuditWorkspace
# ---------------------------------------------------------------------------

@dataclass
class AuditWorkspace:
    """Represents one in-progress audit run."""

    root: Path
    slug: str
    brief: dict[str, Any]
    manifest: dict[str, Any] = field(default_factory=dict)

    # ---- factory ----------------------------------------------------------

    @classmethod
    def from_path(cls, path: str | Path) -> "AuditWorkspace":
        """Reattach to an existing workspace by path."""
        root = Path(path)
        if not (root / "manifest.json").exists():
            raise FileNotFoundError(f"No manifest at {root}")
        manifest = json.loads((root / "manifest.json").read_text())
        brief = json.loads((root / "brief.json").read_text())
        return cls(root=root, slug=manifest["run_slug"], brief=brief, manifest=manifest)

    @classmethod
    def init(cls, brief: dict[str, Any], root: Path | None = None) -> "AuditWorkspace":
        """Create a fresh audit workspace on disk."""
        slug = make_slug(brief.get("name") or "untitled-app")
        ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        run_slug = f"{slug}-{ts}"
        root = root or WORKSPACE_ROOT / run_slug
        root.mkdir(parents=True, exist_ok=True)
        (root / "waves").mkdir(exist_ok=True)
        (root / "final").mkdir(exist_ok=True)

        # Write brief.json
        write_json(root / "brief.json", brief)

        # Scaffold wave directories
        for wave in WAVES:
            wdir = root / "waves" / f"{wave['num']:02d}-{wave['slug']}"
            wdir.mkdir(parents=True, exist_ok=True)
            # Touch context.json with a placeholder so downstream readers don't 404
            write_json(wdir / "context.json", {"_status": "pending", "wave": wave["num"]})

        manifest = {
            "run_slug": run_slug,
            "slug": slug,
            "started_at": dt.datetime.now().isoformat(timespec="seconds"),
            "brief_path": "brief.json",
            "waves": {
                str(w["num"]): {
                    "name": w["name"],
                    "agents": {
                        str(num): {"name": name, "status": "pending", "file": fname, "format": fmt}
                        for (num, name, fname, fmt) in w["agents"]
                    },
                }
                for w in WAVES
            },
            "final": {"status": "pending"},
        }
        write_json(root / "manifest.json", manifest)

        return cls(root=root, slug=run_slug, brief=brief, manifest=manifest)

    # ---- i/o --------------------------------------------------------------

    def wave_dir(self, wave_num: int) -> Path:
        wave = next(w for w in WAVES if w["num"] == wave_num)
        return self.root / "waves" / f"{wave_num:02d}-{wave['slug']}"

    def agent_path(self, wave_num: int, agent_slug: str) -> Path:
        wave = next(w for w in WAVES if w["num"] == wave_num)
        agent = next(a for a in wave["agents"] if a[1] == agent_slug)
        return self.wave_dir(wave_num) / agent[2]

    def write_agent(self, wave_num: int, agent_slug: str, content: str | dict) -> Path:
        """Write an agent's output. If content is a dict and format is json, dump as JSON."""
        wave = next(w for w in WAVES if w["num"] == wave_num)
        agent = next(a for a in wave["agents"] if a[1] == agent_slug)
        path = self.agent_path(wave_num, agent_slug)
        if agent[3] == "json":
            if isinstance(content, str):
                # try to parse as JSON first
                try:
                    content = json.loads(content)
                except json.JSONDecodeError:
                    # store as string under "raw"
                    content = {"raw": content}
            write_json(path, content)
        else:
            path.write_text(content if isinstance(content, str) else json.dumps(content, indent=2))
        self.mark_agent(wave_num, agent_slug, "done")
        return path

    def mark_agent(self, wave_num: int, agent_slug: str, status: str, note: str = "") -> None:
        self.manifest["waves"][str(wave_num)]["agents"][str(
            next(a[0] for a in WAVES[wave_num - 1]["agents"] if a[1] == agent_slug)
        )]["status"] = status
        if note:
            self.manifest["waves"][str(wave_num)]["agents"][str(
                next(a[0] for a in WAVES[wave_num - 1]["agents"] if a[1] == agent_slug)
            )]["note"] = note
        write_json(self.root / "manifest.json", self.manifest)

    def mark_wave(self, wave_num: int, status: str) -> None:
        wave = next(w for w in WAVES if w["num"] == wave_num)
        if status == "done":
            # enforce: all agents must be done
            agents = self.manifest["waves"][str(wave_num)]["agents"]
            not_done = [n for n, a in agents.items() if a["status"] != "done"]
            if not_done:
                raise ValueError(
                    f"Cannot mark Wave {wave_num} done: agents {not_done} not done. "
                    f"Mark each agent individually first."
                )
        self.manifest["waves"][str(wave_num)]["status"] = status
        write_json(self.root / "manifest.json", self.manifest)

    def mark_final(self, status: str, path: str = "") -> None:
        self.manifest["final"]["status"] = status
        if path:
            self.manifest["final"]["path"] = path
        self.manifest["finished_at"] = dt.datetime.now().isoformat(timespec="seconds")
        write_json(self.root / "manifest.json", self.manifest)

    # ---- aggregation ------------------------------------------------------

    def build_context(self, wave_num: int) -> dict[str, Any]:
        """Assemble context.json for `wave_num` from prior wave outputs."""
        wave = next(w for w in WAVES if w["num"] == wave_num)
        ctx: dict[str, Any] = {
            "wave": wave_num,
            "wave_name": wave["name"],
            "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        }

        if wave["context_includes_brief"]:
            ctx["brief"] = self.brief

        # Pull in all prior wave outputs
        for prior_wave in WAVES:
            if prior_wave["num"] >= wave_num:
                break
            wave_key = f"wave_{prior_wave['num']:02d}_{prior_wave['slug']}"
            ctx[wave_key] = {}
            for (num, slug, fname, fmt) in prior_wave["agents"]:
                fpath = self.root / "waves" / f"{prior_wave['num']:02d}-{prior_wave['slug']}" / fname
                if not fpath.exists():
                    ctx[wave_key][slug] = {"_missing": True, "expected_path": str(fpath)}
                    continue
                try:
                    if fmt == "json":
                        ctx[wave_key][slug] = json.loads(fpath.read_text())
                    else:
                        ctx[wave_key][slug] = fpath.read_text()
                except Exception as e:  # noqa: BLE001
                    ctx[wave_key][slug] = {"_error": str(e), "_path": str(fpath)}

        write_json(self.wave_dir(wave_num) / "context.json", ctx)
        return ctx

    def collect_findings(self) -> list[dict[str, Any]]:
        """Walk all wave outputs and extract structured findings.

        A "finding" is anything that looks like a security/risk/quality issue.
        We pull them from:
          - Wave 2 risk reports (primary)
          - Wave 3 quality reports
          - Wave 4 impact map (links findings to business impact)
          - Wave 5 verified_sources, cve_report, deprecation_report (verification)
        """
        findings: list[dict[str, Any]] = []
        idx = 0

        # --- Wave 2 risk findings -----------------------------------------
        risk_wave = next(w for w in WAVES if w["num"] == 2)
        for (num, slug, fname, fmt) in risk_wave["agents"]:
            fpath = self.wave_dir(2) / fname
            if not fpath.exists():
                continue
            text = fpath.read_text() if fmt == "md" else json.dumps(json.loads(fpath.read_text()), indent=2)
            for sev in ("Severe", "Moderate", "Informational"):
                bucket = parse_markdown_bullets_under_header(text, sev)
                for item in bucket:
                    idx += 1
                    findings.append({
                        "id": f"F{idx:03d}",
                        "wave": 2,
                        "agent": slug,
                        "severity": sev.lower(),
                        "raw": item,
                        "verification": "unverified",
                    })

        # --- Wave 3 quality findings --------------------------------------
        for (num, slug, fname, fmt) in next(w for w in WAVES if w["num"] == 3)["agents"]:
            fpath = self.wave_dir(3) / fname
            if not fpath.exists():
                continue
            text = fpath.read_text() if fmt == "md" else json.dumps(json.loads(fpath.read_text()), indent=2)
            for sev in ("Severe", "Moderate", "Informational"):
                bucket = parse_markdown_bullets_under_header(text, sev)
                for item in bucket:
                    idx += 1
                    findings.append({
                        "id": f"F{idx:03d}",
                        "wave": 3,
                        "agent": slug,
                        "severity": sev.lower(),
                        "raw": item,
                        "verification": "unverified",
                    })

        write_json(self.root / "final" / "all-findings.json", {
            "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
            "count": len(findings),
            "findings": findings,
        })
        return findings

    # ---- reporting -------------------------------------------------------

    def status_text(self) -> str:
        lines = [f"# Audit Status — {self.slug}", ""]
        for wave in WAVES:
            wdir = self.wave_dir(wave["num"])
            status = self.manifest["waves"].get(str(wave["num"]), {}).get("status", "pending")
            lines.append(f"## Wave {wave['num']}: {wave['name']} — {status}")
            for (num, slug, fname, fmt) in wave["agents"]:
                a = self.manifest["waves"][str(wave["num"])]["agents"][str(num)]
                glyph = {"pending": "⏳", "running": "🔄", "done": "✅", "failed": "❌"}.get(a["status"], "?")
                lines.append(f"  {glyph} {num:02d} {slug:20s} {a['status']}")
            lines.append("")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Brief parsing
# ---------------------------------------------------------------------------

def parse_brief(source: str | Path | dict) -> dict[str, Any]:
    """Parse a brief from any of: dict, JSON file, markdown form, or YAML.

    - If `source` is a dict, normalize and return.
    - If `source` is a path to an existing file, read it.
    - If `source` is a string that looks like a file path and exists, treat as path.
    - Otherwise treat as raw markdown text.
    """
    if isinstance(source, dict):
        return _normalize_brief(source)

    if isinstance(source, str):
        # If it has newlines or starts with '#', it's markdown content
        if "\n" in source or source.lstrip().startswith("#"):
            return _normalize_brief(_parse_markdown_brief(source))
        # Otherwise treat as path
        p = Path(source)
    else:
        p = source

    if not p.exists():
        raise FileNotFoundError(f"Brief source not found: {source}")

    text = p.read_text()
    if p.suffix in (".json",):
        return _normalize_brief(json.loads(text))
    if p.suffix in (".yaml", ".yml"):
        try:
            import yaml  # type: ignore
            return _normalize_brief(yaml.safe_load(text))
        except ImportError:
            raise RuntimeError("PyYAML not installed; save brief as JSON or use --name flag")
    # Markdown form
    return _normalize_brief(_parse_markdown_brief(text))


def _parse_markdown_brief(text: str) -> dict[str, Any]:
    """Crack the audit-brief.md form into a dict.

    Handles two patterns for "## App Info":
        - **Name:** TestApp          (bullet + bold key + value)
        Name: TestApp                 (plain key: value)

    Handles checkbox lines in "## Access" and "## Known Concerns".
    Handles bullet lines (and "Description:" prefix-less prose) under "## Description".
    """
    out: dict[str, Any] = {
        "name": "", "type": "", "stage": "", "url": "", "repo_url": "",
        "concerns": [], "access": [], "description": "",
    }
    current_section = None
    desc_lines: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("## "):
            # Flush description from previous section
            if current_section == "description" and desc_lines:
                out["description"] = " ".join(desc_lines).strip()
                desc_lines = []
            current_section = s[3:].lower()
            continue
        if not s or s.startswith("# "):
            continue
        # checkbox lines
        if s.startswith("- [x]") or s.startswith("- [X]") or s.startswith("- [ ]"):
            checked = s.startswith("- [x]") or s.startswith("- [X]")
            label = re.sub(r"^-\s*\[[ xX]\]\s*", "", s).strip()
            # strip leading "Other: " for concerns
            if current_section == "known concerns":
                key = "concerns"
                if checked:
                    # extract the topic name (before em-dash or colon)
                    topic = re.split(r"[—:-]", label, 1)[0].strip()
                    if topic and topic.lower() != "other":
                        out[key].append(topic)
            elif current_section == "access" and checked:
                out["access"].append(label)
            continue
        # plain bullet under description
        if s.startswith("- ") and current_section == "description":
            desc_lines.append(s[2:].strip())
            continue
        # plain prose under description (no leading "- ")
        if current_section == "description":
            desc_lines.append(s)
        # key:value lines under "## App Info"  (with or without leading "- ")
        if current_section == "app info" and ":" in s:
            content = s.lstrip("- ").strip()
            m = re.match(r"\*\*(.+?)\*\*\s*:?\s*(.*)", content)
            if m:
                key = m.group(1).strip().rstrip(":").lower()
                val = m.group(2).strip()
            else:
                # plain "Key: Value"
                k, _, v = content.partition(":")
                key = k.strip().lower()
                val = v.strip()
            mapping = {
                "name": "name", "type": "type", "stage": "stage",
                "url (if deployed)": "url", "repo url (if public)": "repo_url",
            }
            if key in mapping and val:
                out[mapping[key]] = val
    # tail-flush for description
    if current_section == "description" and desc_lines:
        out["description"] = " ".join(desc_lines).strip()
    return out


def _normalize_brief(raw: dict[str, Any]) -> dict[str, Any]:
    """Apply defaults and normalize keys."""
    out = {
        "name":       raw.get("name", "untitled-app"),
        "type":       raw.get("type", "web"),
        "stage":      raw.get("stage", "pre-launch"),
        "url":        raw.get("url", ""),
        "repo_url":   raw.get("repo_url") or raw.get("repo", ""),
        "concerns":   list(raw.get("concerns", [])),
        "access":     list(raw.get("access", [])),
        "description": raw.get("description", ""),
        "raw":        raw,  # preserve original
    }
    # Map common type aliases — also strip parentheticals like "Web (Next.js)"
    raw_type = re.sub(r"\s*\(.*?\)\s*", " ", out["type"].lower()).strip()
    type_map = {
        "rn": "rn-expo", "expo": "rn-expo", "rn/expo": "rn-expo", "react-native": "rn-expo",
        "next": "web", "remix": "web", "vite": "web", "next.js": "web",
        "web": "web", "n8n": "n8n", "other": "other",
    }
    out["type"] = type_map.get(raw_type, out["type"])
    # If still unrecognized but contains "web", default to web
    if out["type"] not in {"rn-expo", "web", "n8n", "other"} and "web" in raw_type:
        out["type"] = "web"
    return out


# ---------------------------------------------------------------------------
# Context helpers
# ---------------------------------------------------------------------------

def build_wave_context(workspace: AuditWorkspace, wave_num: int) -> dict[str, Any]:
    """Public wrapper around AuditWorkspace.build_context."""
    return workspace.build_context(wave_num)


def parse_markdown_bullets_under_header(text: str, header: str) -> list[str]:
    """Extract bullet items that fall under a specific header (case-insensitive).

    Handles '## Header' through next '## ' or '### ' (depending on depth).
    Returns list of bullet lines without the leading '- '.
    """
    lines = text.splitlines()
    target = header.lower()
    out: list[str] = []
    in_section = False
    section_depth = None
    for line in lines:
        s = line.rstrip()
        stripped = s.lstrip("#").strip()
        level = len(s) - len(s.lstrip("#"))
        if s.startswith("#"):
            if in_section and level <= section_depth:
                break
            if stripped.lower() == target:
                in_section = True
                section_depth = level
            elif in_section and level <= section_depth:
                # moved past
                break
            continue
        if not in_section:
            continue
        if not s.strip():
            continue
        # collect bullets and any non-empty line that looks like a finding
        if s.lstrip().startswith("- "):
            out.append(s.lstrip()[2:].strip())
        elif s.lstrip().startswith("* "):
            out.append(s.lstrip()[2:].strip())
    return out


# ---------------------------------------------------------------------------
# Slug + small utilities
# ---------------------------------------------------------------------------

def make_slug(name: str) -> str:
    """Turn an app name into a filesystem-safe slug."""
    s = re.sub(r"[^a-zA-Z0-9-]+", "-", name.strip().lower())
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "app"


def short_hash(text: str, n: int = 6) -> str:
    return hashlib.sha1(text.encode()).hexdigest()[:n]


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# CLI subcommands (used by main agent or by the user directly)
# ---------------------------------------------------------------------------

def cmd_init(args: argparse.Namespace) -> int:
    """Create a new audit workspace from a brief source."""
    if args.brief:
        brief = parse_brief(args.brief)
    else:
        brief = _normalize_brief({
            "name": args.name or "untitled-app",
            "type": args.type or "web",
            "stage": args.stage or "pre-launch",
            "url": args.url or "",
            "repo_url": args.repo or "",
            "concerns": args.concern or [],
            "description": args.description or "",
        })
    ws = AuditWorkspace.init(brief, root=Path(args.root) if args.root else None)
    print(f"Created audit workspace: {ws.root}")
    print(f"Slug: {ws.slug}")
    print(f"Next: load orchestrator.md, then run Wave 1.")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Print status of an existing audit workspace."""
    root = Path(args.workspace)
    if not (root / "manifest.json").exists():
        print(f"No manifest at {root}", file=sys.stderr)
        return 1
    manifest = json.loads((root / "manifest.json").read_text())
    brief = json.loads((root / "brief.json").read_text())
    print(f"# Audit: {manifest['run_slug']}")
    print(f"# App:   {brief.get('name', '?')} ({brief.get('type', '?')})")
    print()
    for w in WAVES:
        wkey = str(w["num"])
        wstate = manifest["waves"].get(wkey, {})
        wstatus = wstate.get("status", "pending")
        glyph = {"pending": "⏳", "running": "🔄", "done": "✅", "failed": "❌"}.get(wstatus, "?")
        print(f"{glyph} Wave {w['num']}: {w['name']}  — {wstatus}")
        for (num, slug, fname, fmt) in w["agents"]:
            a = wstate.get("agents", {}).get(str(num), {})
            s = a.get("status", "pending")
            sg = {"pending": "⏳", "running": "🔄", "done": "✅", "failed": "❌"}.get(s, "?")
            print(f"    {sg} {num:02d} {slug:20s} {s}")
    final = manifest.get("final", {})
    print()
    print(f"Final: {final.get('status', 'pending')}  {final.get('path', '')}")
    return 0


def cmd_collect(args: argparse.Namespace) -> int:
    """Aggregate all findings from a workspace."""
    root = Path(args.workspace)
    brief = json.loads((root / "brief.json").read_text())
    ws = AuditWorkspace(root=root, slug=root.name, brief=brief)
    findings = ws.collect_findings()
    print(f"Collected {len(findings)} findings into {root}/final/all-findings.json")
    return 0


def cmd_context(args: argparse.Namespace) -> int:
    """Build context.json for a specific wave."""
    ws = AuditWorkspace.from_path(args.workspace)
    ctx = ws.build_context(args.wave)
    print(f"Built context for Wave {args.wave}: {ws.wave_dir(args.wave) / 'context.json'}")
    print(f"Keys: {list(ctx.keys())}")
    return 0


def cmd_mark(args: argparse.Namespace) -> int:
    """Mark an agent's status. Usage: --wave 2 --agent bouncer --status done"""
    ws = AuditWorkspace.from_path(args.workspace)
    ws.mark_agent(args.wave, args.agent, args.status, note=args.note or "")
    print(f"Wave {args.wave} / {args.agent} → {args.status}")
    return 0


def cmd_mark_wave(args: argparse.Namespace) -> int:
    """Mark a wave's status."""
    ws = AuditWorkspace.from_path(args.workspace)
    try:
        ws.mark_wave(args.wave, args.status)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print(f"Wave {args.wave} → {args.status}")
    return 0


def cmd_mark_final(args: argparse.Namespace) -> int:
    """Mark the final report status."""
    ws = AuditWorkspace.from_path(args.workspace)
    ws.mark_final(args.status, path=args.path or "")
    print(f"Final → {args.status} {args.path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="axon-audit", description="Axon Audit orchestrator CLI")
    sub = p.add_subparsers(dest="cmd")

    pi = sub.add_parser("init", help="Initialize a new audit workspace")
    pi.add_argument("--brief", help="Path to brief file (md/json/yaml)")
    pi.add_argument("--name", help="App name (overrides brief)")
    pi.add_argument("--type", help="App type: rn-expo, web, n8n, other")
    pi.add_argument("--stage", help="Stage: pre-launch, live, scaling")
    pi.add_argument("--url", help="Deployed URL")
    pi.add_argument("--repo", help="Repo URL")
    pi.add_argument("--concern", action="append", help="Known concern (repeat for multiple)")
    pi.add_argument("--description", help="Description text")
    pi.add_argument("--root", help="Override workspace root path")
    pi.set_defaults(func=cmd_init)

    ps = sub.add_parser("status", help="Show status of an audit workspace")
    ps.add_argument("workspace", help="Path to workspace root")
    ps.set_defaults(func=cmd_status)

    pc = sub.add_parser("collect", help="Aggregate findings into all-findings.json")
    pc.add_argument("workspace", help="Path to workspace root")
    pc.set_defaults(func=cmd_collect)

    pwc = sub.add_parser("context", help="Build context.json for a wave")
    pwc.add_argument("workspace", help="Path to workspace root")
    pwc.add_argument("--wave", type=int, required=True, help="Wave number (1-5)")
    pwc.set_defaults(func=cmd_context)

    pma = sub.add_parser("mark", help="Mark an agent's status")
    pma.add_argument("workspace", help="Path to workspace root")
    pma.add_argument("--wave", type=int, required=True)
    pma.add_argument("--agent", required=True, help="Agent slug (e.g. bouncer)")
    pma.add_argument("--status", required=True, choices=["pending", "running", "done", "failed"])
    pma.add_argument("--note", help="Optional note")
    pma.set_defaults(func=cmd_mark)

    pmw = sub.add_parser("mark-wave", help="Mark a wave's overall status")
    pmw.add_argument("workspace", help="Path to workspace root")
    pmw.add_argument("--wave", type=int, required=True)
    pmw.add_argument("--status", required=True, choices=["pending", "running", "done", "failed"])
    pmw.set_defaults(func=cmd_mark_wave)

    pmf = sub.add_parser("mark-final", help="Mark the final report status")
    pmf.add_argument("workspace", help="Path to workspace root")
    pmf.add_argument("--status", required=True, choices=["pending", "done", "failed"])
    pmf.add_argument("--path", help="Path to final PDF/markdown")
    pmf.set_defaults(func=cmd_mark_final)

    args = p.parse_args(argv)
    if not hasattr(args, "func"):
        p.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
