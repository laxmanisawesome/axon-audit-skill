#!/usr/bin/env python3
"""
test_orchestrator.py — Smoke test for the Axon Audit orchestrator helpers.

Exercises the full happy path without invoking any LLM:
  1. parse_brief() from markdown
  2. AuditWorkspace.init() — create workspace
  3. Write simulated agent outputs
  4. build_context() for each wave
  5. mark_agent / mark_wave / status flow
  6. collect_findings() — aggregate into all-findings.json

Exit code 0 = pass, non-zero = fail.
"""
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

# Make lib importable
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from lib import (
    AuditWorkspace,
    parse_brief,
    make_slug,
    parse_markdown_bullets_under_header,
    WAVES,
    WORKSPACE_ROOT,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_BRIEF = """# Audit Brief — Input Form

## App Info
- **Name:** SampleApp
- **Type:** Web (Next.js)
- **Stage:** Pre-launch
- **URL (if deployed):** https://sample.app
- **Repo URL (if public):** https://github.com/x/sample

## Access
- [x] I can share code via paste
- [ ] I can share a deployed URL for live probing
- [x] I can share key config files (package.json, nginx, Dockerfile, etc.)

## Known Concerns
- [x] Security — worried about data breaches
- [x] Scaling — worried about performance under load
- [ ] Other: payments

## Description
A small Next.js + Postgres app with Stripe billing.
"""

W1_OUTPUTS = {
    "01-cartographer.json": {
        "app_type": "nextjs",
        "framework": "Next.js 14",
        "deps": ["next", "react", "stripe", "pg", "drizzle-orm"],
        "config_files": ["next.config.js", "drizzle.config.ts"],
        "build_commands": ["next build", "vercel deploy"],
        "notes": "App Router, Vercel-deployed",
    },
    "02-tour-guide.md": """# User Journey

## Flow: Signup
1. Land on / → /signup form
2. Submit → /onboarding → /dashboard

**Friction points:** No guest preview
""",
    "03-librarian.json": {
        "data_stores": [{"type": "postgres", "tables": ["users", "subscriptions"]}],
        "services": [{"name": "stripe", "purpose": "billing"}],
        "auth_providers": [{"type": "next-auth"}],
        "apis": [{"endpoint": "/api/checkout", "method": "POST"}],
        "webhooks": [{"path": "/api/stripe/webhook"}],
    },
    "04-timekeeper.md": """# Timeline

**Project created:** 2026-05-01
**Last commit:** 2026-06-10
**Deployment cadence:** Weekly to Vercel
**Stale deps:** next@14.0.4 → 14.2.x available
**Assessment:** Active
""",
}

W2_OUTPUTS = {
    "05-bouncer.md": """# Auth Report

## Severe
- No CSRF token on POST /api/checkout
- /api/admin/* accepts any authenticated user

## Moderate
- Session cookie has no SameSite=Strict

## Informational
- next-auth handles refresh automatically
""",
    "06-locksmith.md": """# Secrets Report

## Exposed Secrets
- STRIPE_SECRET_KEY hardcoded in src/lib/stripe.ts

## Hardcoded Internal URLs
- http://localhost:5432 in docker-compose.yml
""",
    "07-stress-tester.md": """# Scaling Scenarios

## At 1K users
- First to break: nothing, fine on free tier
- Cost: $20/mo

## At 10K users
- First to break: Postgres connection pool
- Cost: $150/mo
""",
    "08-exploit-hunter.md": """# Exploit Report

## Vulnerabilities
| Type | Location | Severity |
|------|----------|----------|
| CSRF | /api/checkout | Severe |
| IDOR | /api/users/[id] | Moderate |
""",
    "09-cost-auditor.md": """# Cost Report

## Current
- Per-user cost: $0.002
- Monthly total: $5

## At 10x users
- Per-user cost: $0.0018

**Runaway risk:** no
""",
    "10-compliance.md": """# Compliance Report

## GDPR
- Account deletion: missing
- Data export: missing

## PII Risks
- Email logged in plain text in /var/log/app.log
""",
}

W3_OUTPUTS = {
    "11-janitor.md": """# Dead Code Report

## Severe
- src/components/OldLanding.tsx: 600 lines unused

## Moderate
- src/utils/oldFormat.ts has 4 unused exports
""",
    "12-archivist.md": """# Ownership Map

## Concept: User role
- Lives in: JWT, Postgres users.role, frontend store
- Conflict: JWT can be stale
""",
    "13-doctor.md": """# Critical Risk

**Component:** Stripe webhook handler
**Why:** Single point of failure for payment reconciliation
**Blast radius:** All revenue
**Fix priority:** immediate
""",
}


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

PASSED = 0
FAILED = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  ✅ {name}")
    else:
        FAILED += 1
        print(f"  ❌ {name}  {detail}")


def main() -> int:
    # Use a temp workspace root so we don't litter /root/axon-audits during test
    tmp_root = Path(tempfile.mkdtemp(prefix="axon-test-"))
    print(f"\n🧪 Axon Audit orchestrator test  |  temp root: {tmp_root}\n")

    # ---- 1. Brief parsing ----------------------------------------------
    print("1. Brief parsing")
    brief = parse_brief(SAMPLE_BRIEF)
    check("name parsed", brief["name"] == "SampleApp", f"got {brief['name']!r}")
    check("type normalized", brief["type"] == "web", f"got {brief['type']!r}")
    check("url captured", brief["url"] == "https://sample.app")
    check("repo captured", brief["repo_url"] == "https://github.com/x/sample")
    check("concerns extracted", brief["concerns"] == ["Security", "Scaling"], f"got {brief['concerns']!r}")
    check("access captured", len(brief["access"]) == 2, f"got {brief['access']!r}")
    check("description captured", "small next.js" in brief["description"].lower(), f"got {brief['description']!r}")

    # ---- 2. Workspace init ---------------------------------------------
    print("\n2. Workspace init")
    ws = AuditWorkspace.init(brief, root=tmp_root / "audit")
    check("workspace created", (ws.root / "brief.json").exists())
    check("manifest created", (ws.root / "manifest.json").exists())
    check("all wave dirs created", all((ws.wave_dir(w["num"])).exists() for w in WAVES))
    check("slug correct", ws.slug.startswith("sampleapp-"), f"got {ws.slug!r}")

    # ---- 3. Write Wave 1 outputs ---------------------------------------
    print("\n3. Write Wave 1 outputs")
    for fname, content in W1_OUTPUTS.items():
        if fname.endswith(".json"):
            ws.write_agent(1, fname.replace(".json", "").split("-", 1)[1].replace("-", "-"), content)
        else:
            agent_slug = fname.replace(".md", "").split("-", 1)[1]
            ws.write_agent(1, agent_slug, content)
    # Verify all 4 wave-1 agent files exist
    for fname in W1_OUTPUTS:
        check(f"  {fname} exists", (ws.wave_dir(1) / fname).exists())

    # ---- 4. Mark wave 1 done -------------------------------------------
    print("\n4. Mark wave 1 done")
    for slug in ["cartographer", "tour-guide", "librarian", "timekeeper"]:
        ws.mark_agent(1, slug, "done")
    try:
        ws.mark_wave(1, "done")
        check("wave 1 marked done", True)
    except ValueError as e:
        check("wave 1 marked done", False, str(e))

    # ---- 5. Build context for wave 2 -----------------------------------
    print("\n5. Build wave 2 context")
    ctx2 = ws.build_context(2)
    check("context has wave_01_recon", "wave_01_recon" in ctx2)
    check("context does NOT have brief (W2)", "brief" not in ctx2)
    check("wave 1 cartographer loaded", "cartographer" in ctx2["wave_01_recon"])
    check("wave 1 deps accessible", "next" in ctx2["wave_01_recon"]["cartographer"]["deps"])

    # ---- 6. Write Wave 2 + 3 outputs ------------------------------------
    print("\n6. Write Wave 2 + 3 outputs")
    for fname, content in W2_OUTPUTS.items():
        slug = fname.replace(".md", "").split("-", 1)[1]
        ws.write_agent(2, slug, content)
    for fname, content in W3_OUTPUTS.items():
        slug = fname.replace(".md", "").split("-", 1)[1]
        ws.write_agent(3, slug, content)

    # Mark all agents done
    for slug in ["bouncer", "locksmith", "stress-tester", "exploit-hunter", "cost-auditor", "compliance"]:
        ws.mark_agent(2, slug, "done")
    ws.mark_wave(2, "done")
    for slug in ["janitor", "archivist", "doctor"]:
        ws.mark_agent(3, slug, "done")
    ws.mark_wave(3, "done")

    # ---- 7. Build context for wave 4 (brief re-injected) ---------------
    print("\n7. Build wave 4 context (with brief)")
    ctx4 = ws.build_context(4)
    check("wave 4 context has brief", "brief" in ctx4)
    check("wave 4 context has wave_01", "wave_01_recon" in ctx4)
    check("wave 4 context has wave_02", "wave_02_risk" in ctx4)
    check("wave 4 context has wave_03", "wave_03_quality" in ctx4)

    # ---- 8. Collect findings --------------------------------------------
    print("\n8. Collect findings")
    findings = ws.collect_findings()
    check("findings collected", len(findings) > 0, f"got {len(findings)}")
    check("all-findings.json written", (ws.root / "final" / "all-findings.json").exists())

    # Verify severity classification
    severities = {f["severity"] for f in findings}
    check("severe findings present", "severe" in severities)
    check("moderate findings present", "moderate" in severities)
    check("informational findings present", "informational" in severities)

    # ---- 9. Status display ---------------------------------------------
    print("\n9. Status display")
    status = ws.status_text()
    check("status shows all 5 waves", all(f"Wave {w['num']}:" in status for w in WAVES))
    check("status shows done waves", "— done" in status)

    # ---- 10. Mark wave done enforcement --------------------------------
    print("\n10. Enforcement: mark-wave refuses if agents not done")
    # Manually reset one agent to pending
    ws.mark_agent(2, "bouncer", "pending")
    try:
        ws.mark_wave(2, "done")
        check("enforcement works", False, "should have raised ValueError")
    except ValueError:
        check("enforcement works", True)
    # Restore
    ws.mark_agent(2, "bouncer", "done")
    ws.mark_wave(2, "done")

    # ---- 11. Mark final --------------------------------------------------
    print("\n11. Mark final")
    ws.mark_final("done", path="/tmp/fake-report.pdf")
    manifest = json.loads((ws.root / "manifest.json").read_text())
    check("final status = done", manifest["final"]["status"] == "done")
    check("final path recorded", manifest["final"]["path"] == "/tmp/fake-report.pdf")
    check("finished_at recorded", "finished_at" in manifest)

    # ---- cleanup ---------------------------------------------------------
    shutil.rmtree(tmp_root, ignore_errors=True)

    # ---- summary ---------------------------------------------------------
    print(f"\n{'=' * 50}")
    print(f"Passed: {PASSED}   Failed: {FAILED}")
    return 0 if FAILED == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
