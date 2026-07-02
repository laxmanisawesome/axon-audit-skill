# Axon Audit — Hermes Agent Skill

A **23-agent, 5-wave multi-agent app audit pipeline** for [Hermes Agent](https://hermes-agent.nousresearch.com). Analyzes codebases (web / React Native / Expo / n8n) across security, auth, scaling, code quality, cost, and compliance — produces a live fact-checked PDF report with cost-to-fix estimates.

## Quick Install

```bash
hermes skills tap add laxmanisawesome/axon-audit-skill
hermes skills install axon-audit
```

Or install directly:

```bash
hermes skills install https://raw.githubusercontent.com/laxmanisawesome/axon-audit-skill/main/SKILL.md
```

## Usage

Load the skill in any Hermes session:

```
/skill axon-audit
```

Then trigger with something like:

- *"Audit my app"*
- *"Run Axon Audit on this codebase"*
- *"Check my security posture"*
- *"I need an app audit"*

## Pipeline Overview

| Wave | What it does | Agents |
|------|-------------|--------|
| **1 — Reconnaissance** | Maps structure, user flows, data inventory, timeline | 4 |
| **2 — Risk Analysis** | Auth, secrets, scaling, exploits, cost, compliance | 6 |
| **3 — Code Quality** | Dead code, ownership, single-points-of-failure | 3 |
| **4 — Founder Translation** | Business impact, cost-to-fix, exec summary, skeptic filter | 4 |
| **5 — Live Fact-Check** | Verifies every claim against live CVEs, docs, benchmarks | 6 |

## Output

A PDF report containing:
- **Executive Summary** — 3 things to fix this week, 2 to plan next quarter, 1 that scares us
- **Per-agent findings** — verdicts with severity classification
- **Cost-to-fix estimates** — in time and money
- **Live fact-checking** — every claim sourced and dated
- **Full agent appendix** — raw outputs for transparency

## Requirements

- Hermes Agent (v1.0+)
- Python 3.10+
- `delegate_task` tool enabled
- `kimi-pdf` skill (for PDF compilation)

## License

MIT
