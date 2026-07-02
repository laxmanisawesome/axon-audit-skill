---
name: axon-audit
description: "Run a multi-agent app audit across 23 dimensions (security, auth, scaling, code quality, cost, compliance). Produces a PDF report with live fact-checked findings, cost-to-fix estimates, and a founder-friendly executive summary. Trigger: 'audit my app', 'run axon-audit on this repo', 'check my security posture', 'I need an app audit'."
version: 1.0.0
author: Lax
license: MIT
metadata:
  hermes:
    tags: [devops, audit, security, mobile, web, scaling, fact-check]
    related_skills: [fact-checker, deep-research, kimi-pdf]
---

# Axon Audit

A 23-agent multi-wave app audit that analyzes code, identifies risks, evaluates scaling, and produces a live-fact-checked PDF report.

## Overview

Axon Audit runs a 5-wave pipeline of parallel subagents. Each wave has a distinct mission:

1. **Reconnaissance** — Maps the app structure, user flows, data inventory, and timeline
2. **Risk Analysis** — Finds problems across 6 dimensions (auth, secrets, scaling, exploits, cost, compliance)
3. **Code Quality** — Identifies dead code, scattered truth, and critical single points of failure
4. **Founder Translation** — Converts technical findings into business impact with fix estimates
5. **Live Fact-Check** — Verifies every claim against live internet docs, CVEs, and benchmarks

After all 5 waves, the Editor-in-Chief agent compiles a PDF report via kimi-pdf.

## When to Use

Load this skill when the user asks to:
- "Audit my app"
- "Run Axon Audit on this codebase"
- "Check my security posture"
- "I need an app audit for my investors"
- "Help me find what breaks when I scale"
- "Review my app before I launch"
- "I want to sell app audits as a service"

**Don't use for:** Single-file scripts, throwaway prototypes, apps with no users and no plans to grow.

## Quick Start (for the main agent)

When invoked, follow this sequence:

1. **Gather brief** — get app name, type (RN/Expo / web / n8n), stage, URL, repo, top concerns. Accept a filled `templates/audit-brief.md` or a quick Q&A.
2. **Initialize workspace**:
   ```bash
   python3 ~/.hermes/skills/devops/axon-audit/scripts/lib.py init --name "..." --type "..." ...
   ```
   Workspace is created at `/root/axon-audits/<slug>-<timestamp>/`.
3. **Run waves** — for each wave (1→5):
   - Read `scripts/orchestrator.md` for the exact batch pattern (3-task max per `delegate_task` call)
   - Before each wave (except Wave 1), run `context --wave N` to assemble `context.json`
   - Launch agents via `delegate_task` in batches of ≤3
   - Mark each agent done via `mark --wave N --agent <slug> --status done`
   - Mark wave done via `mark-wave --wave N --status done` (refuses if agents not all done)
4. **Collect & compile**:
   ```bash
   python3 lib.py collect <workspace>          # → final/all-findings.json
   # Wait for editor-in-chief to write final/report-source.md
   # Then hand to compile-report.py (Weekend 3) for the PDF
   ```
5. **Report status** to the user with `lib.py status <workspace>`.

See `scripts/orchestrator.md` for the full procedure.

## How It Works

### Input

Provide one of:
- A Git repo URL (public) or path to a local codebase
- A deployed app URL (for live probing)
- A paste of key files (package.json, config, nginx, Dockerfile, workflow exports)
- A brief with: app name, type (RN/Expo, web, n8n), stage (pre-launch/live/scaling), known concerns

### Pipeline

```
INPUT → [Wave 1: 4 agents] → [Wave 2: 6 agents] → [Wave 3: 3 agents]
                                                              ↓
OUTPUT ← [Compiler: 1 agent] ← [Wave 5: 6 agents] ← [Wave 4: 4 agents]
```

Each agent runs as an isolated `delegate_task` subagent with its own tools. Wave 5 agents use `web_search` and `web_extract` to fact-check every recommendation against live sources.

### Output

A PDF report containing:
- **Executive Summary** — 3 things to fix this week, 2 to plan next quarter, 1 that scares us
- **Per-agent findings** — verdicts with severity classification
- **Cost-to-fix estimates** — in time and money
- **Live fact-checking** — every claim sourced and dated
- **Full agent appendix** — raw outputs for transparency

## Agent Cast

### Wave 1: Reconnaissance
| # | Agent | Role | Output |
|---|-------|------|--------|
| 1 | Cartographer | Maps file tree, frameworks, deps | `code_map.json` |
| 2 | Tour Guide | Walks user flows | `user_journey.md` |
| 3 | Librarian | Lists all datastores/services/APIs | `inventory.json` |
| 4 | Timekeeper | Analyzes git/deployment history | `timeline.md` |

### Wave 2: Risk Analysis
| # | Agent | Role | Output |
|---|-------|------|--------|
| 5 | Bouncer | Auth audit | `auth_report.md` |
| 6 | Locksmith | Secrets/credentials audit | `secrets_report.md` |
| 7 | Stress Tester | Scaling scenarios 1K-1M users | `scaling_scenarios.md` |
| 8 | Exploit Hunter | OWASP + mobile exploit scan | `exploit_report.md` |
| 9 | Cost Auditor | Per-user cost at scale | `cost_report.md` |
| 10 | Compliance Officer | GDPR/CCPA/PII audit | `compliance_report.md` |

### Wave 3: Code Quality
| # | Agent | Role | Output |
|---|-------|------|--------|
| 11 | Janitor | Dead code/unused imports | `dead_code.md` |
| 12 | Archivist | Duplicated logic/ownership map | `ownership_map.md` |
| 13 | Doctor | Critical single-point-of-failure | `critical_risks.md` |

### Wave 4: Founder Translation
| # | Agent | Role | Output |
|---|-------|------|--------|
| 14 | Translator | Technical → business impact | `impact_map.md` |
| 15 | Economist | Cost-to-fix estimates | `cost_to_fix.md` |
| 16 | Storyteller | Executive summary | `executive_summary.md` |
| 17 | Skeptic | Must-have vs nice-to-have | `skeptic_review.md` |

### Wave 5: Live Fact-Check
| # | Agent | Role | Output |
|---|-------|------|--------|
| 18 | Documentarian | Verifies docs/changelogs | `verified_sources.md` |
| 19 | News Hound | CVEs + advisories (30 days) | `cve_report.md` |
| 20 | Benchmarker | Verifies performance claims | `benchmarks.md` |
| 21 | Deprecation Hunter | API deprecation status | `deprecation_report.md` |
| 22 | Contrarian | Argues against every finding | `contrarian_review.md` |
| 23 | Editor-in-Chief | Final compilation + PDF | `final_report.md` |

## Common Pitfalls

1. **Over-trusted agent output.** Always let Wave 5 fact-check. Don't skip it even for a "quick audit."
2. **Missing context.** The audit quality depends on what you feed in. Provide code, config, AND a URL if possible.
3. **Over-engineering findings.** Wave 17 (Skeptic) exists to filter noise. If a finding survives the Skeptic AND the Contrarian, it's real.
4. **Partial pipeline failure.** If Wave 5 fails (network issue, search API down), the audit runs without fact-checking — clearly marked as "unverified" in the report.
5. **Liability.** Every report must include: "This is an AI-assisted audit. No recommendation replaces qualified human review."

### Agent markdown format contract (CRITICAL)

Wave 2 and Wave 3 agent outputs **MUST** use `## Severe` / `## Moderate` / `## Informational` headers followed by `- ` bullets. The bold `**Severe:**` form is silently ignored by `lib.py:collect_findings()` and produces 0 findings. See `references/smoke-test-findings.md` for the full contract and an example.

### kimi-pdf path

The kimi-pdf HTML→PDF converter is at `/root/.agents/skills/kimi-pdf/scripts/html_to_pdf.js` (NOT `/app/.kimi/...`). Run `pdf.sh check` from that directory before relying on it.

## Verification Checklist

- [ ] Input provided (code paste, repo URL, deployed URL, or all three)
- [ ] All 5 waves executed (check for failed agents)
- [ ] Wave 5 fact-checking completed (verified_sources.md exists)
- [ ] Editor-in-Chief has compiled final report
- [ ] PDF generated and delivered
- [ ] Disclaimer present in output
- [ ] Smoke test on a fixture before running on real code (recommended)

## Smoke Test

A synthetic workspace at `/root/axon-audits/testapp-*/` validates the
end-to-end pipeline without running real agents. The reusable fixture
is at `scripts/smoke_fixture.py`.

```bash
# 1. Init workspace
python3 scripts/lib.py init --name TestApp --type rn-expo --stage live \
    --url https://testapp.example.com

# 2. Populate with synthetic outputs (30 agent files + findings)
cp scripts/smoke_fixture.py /root/axon-audits/<workspace>/_populate.py
# Edit WORKSPACE in _populate.py to match your new workspace path
python3 /root/axon-audits/<workspace>/_populate.py

# 3. Auto-collect findings from agent markdown
python3 scripts/lib.py collect /root/axon-audits/<workspace>

# 4. Compile to PDF
python3 scripts/compile-report.py /root/axon-audits/<workspace>
```

Expected output: 33-page PDF (~270 KB) with cover, exec summary
(3+2+1), findings table (30 rows), detailed findings, agent appendix
(23 entries), disclaimer.

**Smoke-test discoveries and known limitations** are documented in
`references/smoke-test-findings.md` — including the markdown format
contract, lib.py API gotchas, three compile-report.py bugs found and
fixed during testing, and the ~70% verification accuracy caveat. Read
it before changing the compiler or running on a real codebase.

## Related Skills

- **fact-checker** — Standalone claim verification. Used as reference for Wave 5 agent design.
- **deep-research** — Multi-agent parallel research pattern. Same architecture used for each wave.
- **kimi-pdf** — PDF report generation for the final output.

**Reusable pattern** (extracted from this skill): see `references/multi-agent-pipeline-pattern.md` for the generic recipe — any skill that orchestrates N subagents across sequential waves can copy this skeleton.

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/lib.py` | Workspace lifecycle, I/O helpers, context aggregation, finding collection |
| `scripts/orchestrator.md` | Step-by-step procedure the main Hermes agent follows (reads `delegate_task` as the orchestrator) |
| `scripts/compile-report.py` | Compiles all wave outputs → HTML → PDF report |
| `scripts/report_template.py` | LaTeX-style HTML/CSS template (kimi-pdf compatible) |
| `scripts/smoke_fixture.py` | Reusable smoke-test fixture — populates a workspace with realistic agent outputs and triggers `lib.py collect`. Copy into a new workspace, edit `WORKSPACE`, run. |
| `scripts/test_orchestrator.py` | 35 unit tests for `lib.py` (run: `python3 scripts/test_orchestrator.py`) |
| `scripts/write-prompts.py` | One-off generator for the 23 agent prompt files. (Already used; re-run only if templates change.) |

## References

| File | Purpose |
|------|---------|
| `references/agent-rubric.md` | Master rubric defining all 23 agents |
| `references/rn-firebase-checklist.md` | RN/Expo/Firebase specific checks |
| `references/web-checklist.md` | General web app checks |
| `references/scaling-math.md` | Capacity planning formulas |
| `references/owasp-scan-notes.md` | OWASP Top 10 condensed for agent use |
| `references/report-template.md` | PDF report structure template |
| `references/smoke-test-findings.md` | **Read before changing the compiler.** Documents 3 bugs found + fixed in `compile-report.py` during the 2026-06-18 smoke test, the markdown format contract agent outputs MUST follow, lib.py API gotchas, and known limitations (~70% verification accuracy). |
| `references/multi-agent-pipeline-pattern.md` | **Reusable recipe** for any future multi-agent pipeline skill (procedure doc + I/O helpers + 3-task batching + wave context handoff + enforcement). Reference implementation = this skill. |

## Templates

| File | Purpose |
|------|---------|
| `templates/audit-brief.md` | Input form — what the user fills in to start an audit |
| `templates/agent-prompts/*.md` | Per-agent prompt templates for `delegate_task` |
