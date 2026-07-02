# Axon Audit — Master Agent Rubric

> Defines what each of the 23 agents looks for, their output format, and how data flows between waves.
> Each prompt in `templates/agent-prompts/` derives from this rubric.

---

## Data Flow Between Waves

```
Wave 1 outputs → Wave 2 inputs     (code map, user journey, inventory, timeline)
Wave 2 outputs → Wave 3 inputs     (risk findings, scaling scenarios)
Wave 2 + 3 outputs → Wave 4 inputs (risks + code quality → business translation)
Wave 4 outputs → Wave 5 inputs     (translations → fact-check)
Wave 5 outputs → Compiler          (all verified → final report)
```

Each wave receives the **aggregated JSON** of all prior waves. Every agent's output goes to a named file that the next wave reads.

---

## Agent Rubric

### Wave 1: Reconnaissance

| # | Agent | Looks For | Output Format | Passes To |
|---|-------|-----------|---------------|-----------|
| 1 | Cartographer | App type, framework, build config, dependency list, Expo/EAS config, Dockerfile, nginx config | JSON: `{ app_type, framework, deps: [], config_files: [], build_commands: [] }` | All waves |
| 2 | Tour Guide | User flow completeness: landing → signup → onboarding → core action → payment → result → retention. Missing steps, friction points, dead ends | Markdown: `# User Journey\n\n## Flow: [name]\n1. Step one\n2. Step two\n...\n\n**Friction points:** ...` | Wave 2, 4 |
| 3 | Librarian | Every data store (Mongo, Firestore, SQLite), external service (Stripe, SendGrid, Firebase, AWS), auth provider, third-party API, webhook endpoints | JSON: `{ data_stores: [], services: [], auth_providers: [], apis: [], webhooks: [] }` | All waves |
| 4 | Timekeeper | Git commit frequency, last deploy date, abandoned branches, stale deps (>6 months), deployment methodology | Markdown: `# Timeline\n\n**Last deploy:** ...\n**Commit cadence:** ...\n**Stale deps:** ...` | Wave 2, 3 |

### Wave 2: Risk Analysis

| # | Agent | Looks For | Output Format | Passes To |
|---|-------|-----------|---------------|-----------|
| 5 | Bouncer | AuthN vs AuthZ: missing auth on endpoints, weak password policy, JWT without expiry, no refresh rotation, session fixation, missing MFA, hardcoded tokens | Markdown: `# Auth Report\n\n**Severe:** [items]\n**Moderate:** [items]\n**Info:** [items]` | Wave 4 |
| 6 | Locksmith | Hardcoded API keys in client code, .env in repo, secrets in config files, exposed credentials in n8n workflow exports, Firebase config exposure | Markdown: `# Secrets Report\n\n**Hardcoded keys found:** [list]\n**Exposure level:** [critical/high/medium]` | Wave 4 |
| 7 | Stress Tester | For each scale (1K, 10K, 100K, 1M DAU): DB connection limits, API rate limits, file storage costs, bandwidth, cold start latency, cache hit ratios | Markdown: `# Scaling Scenarios\n\n## At 1K users\n- Breaks: ...\n- Cost: $X/mo\n\n## At 10K users\n...` | Wave 4, 5 |
| 8 | Exploit Hunter | OWASP Top 10: SQL injection, XSS, CSRF, SSRF, IDOR, security misconfig, known-vulnerable deps. Mobile: insecure AsyncStorage, missing cert pinning, deep link abuse | Markdown: `# Exploit Report\n\n**Vulnerabilities:** [list with CVSS-like severity]\n**Affected components:** [list]` | Wave 4, 5 |
| 9 | Cost Auditor | Per-user cost at current scale, at 10x, at 100x. Firestore read amplification, unbounded queries, API call costs, file storage costs, compute costs | Markdown: `# Cost Report\n\n## Current\n- Per-user cost: $X\n- Monthly total: $Y\n\n## At 10x users\n- Per-user cost: $X\n- Monthly total: $Y\n\n**Runaway risk:** [yes/no]` | Wave 4 |
| 10 | Compliance Officer | GDPR: user deletion path, data export, cookie consent. CCPA: opt-out mechanism. Data residency. PII in logs. Third-party data sharing | Markdown: `# Compliance Report\n\n**GDPR:** [pass/fail/warning]\n**CCPA:** [pass/fail/warning]\n**PII risks:** [list]` | Wave 4 |

### Wave 3: Code Quality & Ownership

| # | Agent | Looks For | Output Format | Passes To |
|---|-------|-----------|---------------|-----------|
| 11 | Janitor | Dead code: unused imports, abandoned features, stale TODOs, commented-out code, orphaned API routes, duplicate config | Markdown: `# Dead Code Report\n\n**To delete:** [list]\n**Cleaning estimate:** X hours` | Wave 4 |
| 12 | Archivist | Scattered truth: same data in DB, localStorage, frontend state, and Stripe with no clear single source. Duplicated logic across files. Conflicting naming | Markdown: `# Ownership Map\n\n**Concept: User roles**\n- Lives in: [file A, file B, DB]\n- Conflict: ...\n\n**Concept: Pricing**\n- Lives in: [file C, Stripe, config]\n- Conflict: ...` | Wave 4 |
| 13 | Doctor | The single highest-risk component: auth system, payment processing, user data export, or dependency with no fallback. Blast radius if this fails | Markdown: `# Critical Risk\n\n**Component:** [name]\n**Why:** [explanation]\n**Blast radius:** [description]\n**Fix priority:** [immediate/this-week/this-month]` | Wave 4 |

### Wave 4: Founder Translation

| # | Agent | Looks For | Output Format | Passes To |
|---|-------|-----------|---------------|-----------|
| 14 | Translator | For each finding in Waves 2+3: what business impact? (users lost, revenue at risk, launch delay, legal exposure, breach cost) | Markdown: `# Impact Map\n\n## Finding: [name]\n**Technical:** ...\n**Business impact:** ...\n**Urgency:** [immediate/this-week/this-month]` | Wave 5 |
| 15 | Economist | For each finding: time to fix (hours/days), cost to fix (developer hours + infra), cost of not fixing (churn, breach, downtime) | Markdown: `# Cost to Fix\n\n## Finding: [name]\n**Fix estimate:** X hours\n**Fix cost:** $Y\n**Cost of ignoring:** $Z` | Wave 5 |
| 16 | Storyteller | Synthesize all findings into: 3 things to fix this week, 2 to plan next quarter, 1 that scares us | Markdown: `# Executive Summary\n\n## This week\n1. ...\n2. ...\n3. ...\n\n## Next quarter\n1. ...\n2. ...\n\n## Scary thing\n...` | Wave 5 |
| 17 | Skeptic | Reviews every finding. Which are must-have vs nice-to-have? Which are overblown? Which lack evidence? | Markdown: `# Skeptic Review\n\n**Must-fix:** [list]\n**Nice-to-have:** [list]\n**Overblown:** [list with reasons]` | Wave 5 |

### Wave 5: Live Fact-Check

| # | Agent | Looks For | Output Format | Passes To |
|---|-------|-----------|---------------|-----------|
| 18 | Documentarian | For every API/library/service referenced: fetch CURRENT docs + changelog. Confirm the recommendation matches latest version best practices | Markdown: `# Verified Sources\n\n## API/Library: [name]\n**Docs URL:** ...\n**Version used:** X → **Latest:** Y\n**Changelog notes:** ...\n**Verdict:** [recommendation accurate / outdated / wrong]` | Compiler |
| 19 | News Hound | Recent CVEs (last 30 days) on every dependency. Breaking changes. Security advisories. Zero-day disclosures | Markdown: `# CVE Report\n\n## Dependency: [name]\n**CVE:** [id]\n**Severity:** [critical/high/medium]\n**Affects your version?** [yes/no/fix available]` | Compiler |
| 20 | Benchmarker | For every performance/scaling claim: search for recent benchmarks. Is "X is faster than Y" still true? | Markdown: `# Benchmarks\n\n## Claim: [text]\n**Search result:** ...\n**Verdict:** [confirmed/outdated/contradicted]` | Compiler |
| 21 | Deprecation Hunter | For every API/library/service: is it deprecated? Is there a migration path? End-of-life date? | Markdown: `# Deprecation Report\n\n## API/Library: [name]\n**Status:** [active/deprecating/deprecated]\n**EOL date:** ...\n**Migration path:** ...` | Compiler |
| 22 | Contrarian | Actively argues against every finding. "Why is this wrong in THIS specific context? What's the counter-argument?" | Markdown: `# Contrarian Review\n\n## Finding: [name]\n**Counter-argument:** ...\n**Weakness in the recommendation:** ...\n**Context where this is wrong:** ...` | Compiler |
| 23 | Editor-in-Chief | Reviews ALL wave outputs. Decides: which findings survive fact-checking, which get flagged, which get cut. Compiles final report structure | Markdown: `# Final Report\n\n**Surviving findings:** [count]\n**Flagged (needs human review):** [list]\n**Cut (insufficient evidence):** [list]` | → Compiler → PDF |

---

## Severity Classification

Each finding in Waves 2-3 should be classified:

| Severity | Meaning | Example | Response |
|----------|---------|---------|----------|
| 🔴 Severe | Will cause user harm or data loss | Hardcoded API keys, no auth on payment APIs | Fix this week |
| 🟠 Moderate | Will cause problems under load or at next milestone | Missing indexes, N+1 queries, no rate limiting | Fix next sprint |
| 🟢 Informational | Good to know, low urgency | Dead code, stale TODOs, deprecation warnings | Fix when convenient |

## Cross-References

- `templates/agent-prompts/*.md` — Each agent's full prompt template
- `references/rn-firebase-checklist.md` — RN/Expo/Firebase specific checks
- `references/web-checklist.md` — Web app specific checks
- `references/scaling-math.md` — Capacity planning formulas
- `references/owasp-scan-notes.md` — OWASP Top 10 reference
- `references/report-template.md` — Final PDF report template
