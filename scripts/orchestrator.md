# Axon Audit — Orchestrator Procedure

> This document is the **operational manual** for the main Hermes agent when running an Axon Audit.
> Read this top-to-bottom at the start of an audit run. Follow the steps in order.
> The actual `delegate_task` calls are made by **you** (the main agent) — this file just tells you how.

---

## 0. Mental Model

```
Brief ──→ Wave 1 (4 agents) ──→ Wave 2 (6 agents) ──→ Wave 3 (3 agents)
                                                          ↓
Final PDF ← Compiler ← Wave 5 (6 agents) ← Wave 4 (4 agents)
```

- **Waves run sequentially.** Each wave reads the prior wave's `context.json` (and writes its own).
- **Agents within a wave run in parallel** (subject to the 3-task-per-batch limit).
- **All outputs are files on disk.** Subagents read from and write to a workspace directory.
- **delegate_task cap = 3 tasks per call.** With 23 agents, expect **9 batches**:
  | Wave | Agents | Batches |
  |------|--------|---------|
  | 1 | 4 | 2 (3+1) |
  | 2 | 6 | 2 (3+3) |
  | 3 | 3 | 1 (3) |
  | 4 | 4 | 2 (3+1) |
  | 5 | 6 | 2 (3+3) |

---

## 1. Inputs You Need

Before starting, gather from the user:

1. **Audit brief** — either:
   - A filled-in `templates/audit-brief.md` (preferred for first-time users)
   - Or a quick Q&A: app name, type, stage, URL, repo, top concerns
2. **Access to code** — paste, repo path on disk, or repo URL

If the user gave you a brief, parse it. If they gave you answers in chat, build a brief dict directly.

---

## 2. Step 1: Initialize Workspace

Run:
```bash
python3 ~/.hermes/skills/devops/axon-audit/scripts/lib.py init \
  --name "MyApp" --type "rn-expo" --stage "live" \
  --url "https://myapp.com" --repo "https://github.com/x/y" \
  --concern "security" --concern "scaling" \
  --description "..." 
```

Or with a brief file:
```bash
python3 ~/.hermes/skills/devops/axon-audit/scripts/lib.py init --brief /path/to/brief.md
```

**Output:** a workspace path like `/root/axon-audits/myapp-20260618-143012/`. Note this. All subsequent steps use it.

The workspace is created with this layout:
```
<workspace>/
├── brief.json
├── manifest.json
├── waves/
│   ├── 01-recon/  (4 agent files + context.json)
│   ├── 02-risk/   (6 agent files + context.json)
│   ├── 03-quality/(3 agent files + context.json)
│   ├── 04-translate/ (4 agent files + context.json)
│   └── 05-verify/ (6 agent files + context.json)
└── final/
```

---

## 3. Step 2: Load Skill Prompts and References

Before the first wave, load the relevant checklist into your context:

- **If `app_type == "rn-expo"`** → `skill_view("axon-audit")` already loaded; then read `references/rn-firebase-checklist.md`
- **If `app_type == "web"`** → read `references/web-checklist.md`
- **If `app_type == "n8n"`** → read `references/web-checklist.md` (it covers general API patterns)

These are passed to subagents via the `context` field on `delegate_task`.

---

## 4. Step 3: Build Wave Context (Before Each Wave)

Before launching a wave, build its `context.json`:

```python
import sys; sys.path.insert(0, "/root/.hermes/skills/devops/axon-audit/scripts")
from lib import AuditWorkspace
ws = AuditWorkspace.from_path("/root/axon-audits/<slug>")
ws.build_context(wave_num=N)
```

Or via CLI (Wave 1 doesn't need this — its context IS the brief):
```bash
python3 -c "import sys; sys.path.insert(0,'/root/.hermes/skills/devops/axon-audit/scripts'); from lib import AuditWorkspace; AuditWorkspace.from_path('$WS').build_context(2)"
```

The context aggregates:
- `brief` (always, for Waves 1 and 4)
- `wave_01_recon` (all 4 Wave 1 outputs)
- `wave_02_risk` (all 6 Wave 2 outputs)
- etc.

This is the **single file** you pass to subagents as their input.

---

## 5. Step 4: Launch Wave Agents (delegate_task)

For each wave, you build a `tasks` array of 1-3 agents and call `delegate_task`.

### Prompt template per agent

```
ROLE: <agent name>
APP: <brief.name> (<brief.type>, <brief.stage>)
DEPLOYED URL: <brief.url>
REPO: <brief.repo>

CONTEXT FILES (read these first):
- /root/axon-audits/<slug>/waves/<NN>-<slug>/context.json
- ~/.hermes/skills/devops/axon-audit/templates/agent-prompts/<prompt-file>
- ~/.hermes/skills/devops/axon-audit/references/<relevant-checklist>.md (if applicable)

TASK (from agent prompt):
<copy/paste the ## Task section from the agent's prompt file>

OUTPUT REQUIREMENT:
- Write your full output to: /root/axon-audits/<slug>/waves/<NN>-<slug>/<agent-file>
- Use the EXACT output format from the prompt template (JSON for cartographer/librarian; markdown for the rest)
- The file path and format are mandatory — the next wave reads it.

Return a 1-paragraph summary of what you found. The orchestrator reads only the file, not your return value.
```

### Toolsets per agent

| Wave | Agent | Toolsets |
|------|-------|----------|
| 1 | cartographer, librarian, timekeeper, tour-guide | `["file", "terminal", "search"]` |
| 2 | bouncer, locksmith, exploit-hunter, compliance | `["file", "terminal", "search"]` |
| 2 | stress-tester, cost-auditor | `["file", "terminal", "search"]` |
| 3 | janitor, archivist, doctor | `["file", "terminal", "search"]` |
| 4 | translator, economist, storyteller, skeptic | `["file", "terminal"]` |
| 5 | documentarian, news-hound, benchmarker, deprecation-hunter | `["file", "terminal", "web"]` |
| 5 | contrarian, editor-in-chief | `["file", "terminal", "web"]` |

### Batch pattern

```python
# Example: Wave 1, batch 1
delegate_task(
    tasks=[
        {"goal": "<cartographer prompt>", "context": "<shared context>", "toolsets": ["file","terminal","search"]},
        {"goal": "<tour-guide prompt>",   "context": "<shared context>", "toolsets": ["file","terminal","search"]},
        {"goal": "<librarian prompt>",    "context": "<shared context>", "toolsets": ["file","terminal","search"]},
    ]
)
# Then batch 2 with timekeeper (only 1 left)
```

**Do NOT exceed 3 tasks per call.** Split if a wave has more.

### After each agent returns

The subagent's job is to **write a file**. After `delegate_task` returns, you:
1. Verify the file exists at the expected path.
2. Mark it done in the manifest (lib.py handles this if you used `ws.write_agent()`).
3. If the file is missing or empty → mark failed, log, continue with others.

---

## 6. Step 5: Per-Wave Checklist

| Wave | # Agents | Pre-step | Parallelism | Special |
|------|----------|----------|-------------|---------|
| 1 | 4 | none (uses brief directly) | 3 + 1 | All agents read source code |
| 2 | 6 | `build_context(2)` | 3 + 3 | 4 risk agents (bouncer, locksmith, exploit-hunter, compliance) + 2 economics (stress, cost) |
| 3 | 3 | `build_context(3)` | 3 | Pure code analysis — needs no Wave 4 input |
| 4 | 4 | `build_context(4)` | 3 + 1 | Needs brief re-injected (founder context) |
| 5 | 6 | `build_context(5)` | 3 + 3 | All need `web` tools; contrarian + editor-in-chief can be a final pair |

---

## 7. Step 6: After All Waves — Collect & Report

### 7a. Aggregate findings
```bash
python3 ~/.hermes/skills/devops/axon-audit/scripts/lib.py collect /root/axon-audits/<slug>
```
This walks all wave outputs and builds `final/all-findings.json`.

### 7b. Wait for editor-in-chief
The editor-in-chief (agent 23) is the **last** agent in Wave 5. It produces `final/report-source.md` — the final report in markdown form.

If editor-in-chief did not produce that file, **you (main agent)** must:
1. Read `all-findings.json` + the storyteller's output + contrarian review
2. Synthesize a `final/report-source.md` using the structure in `references/report-template.md`
3. Write it to `<workspace>/final/report-source.md`

### 7c. Hand off to compile-report.py
Once `report-source.md` exists, hand it to Weekend 3's `compile-report.py` to generate the PDF.

### 7d. Mark final done
```bash
python3 -c "from lib import AuditWorkspace; ..."
```
Update manifest to mark the run complete with the PDF path.

---

## 8. Failure Handling

| Failure | What to do |
|---------|------------|
| Subagent returns but no file written | Mark failed; do NOT re-run automatically — note it and proceed. The next wave will work with `_missing: true` in context. |
| Wave 2 partial failure (e.g. 4/6 done) | Continue. The remaining agents' `_missing: true` flags will appear in context. Skeptic (Wave 4) will catch over-reliance on missing data. |
| Wave 5 web search fails | Documentarian/News-Hound may return empty. Their outputs are marked "unverified" by the editor. The report still ships. |
| Entire wave fails | Mark wave `failed`, write a note in `manifest.json`, and surface to the user. Suggest retrying individual agents. |
| Output format wrong (e.g. JSON agent returned markdown) | Read the file, attempt best-effort parse, log a warning. Don't block the pipeline. |

---

## 9. Status Reporting

After each wave, print to the user:
```
✅ Wave 1 (Reconnaissance) — 4/4 agents done
   ✓ cartographer, tour-guide, librarian, timekeeper
   Next: Wave 2 (Risk Analysis) — 6 agents
```

If any agent failed:
```
⚠️ Wave 2 (Risk Analysis) — 5/6 agents done
   ✓ bouncer, locksmith, exploit-hunter, cost-auditor, compliance
   ✗ stress-tester (timed out — continuing without it)
   Next: Wave 3 (Code Quality)
```

---

## 10. End-to-End Time Budget

For a small-to-medium app (RN/Expo, ~5K LOC, ~50 deps):
- Wave 1: ~3-5 min (4 agents in parallel, 2 batches)
- Wave 2: ~5-8 min (6 agents, 2 batches)
- Wave 3: ~3-4 min (3 agents, 1 batch)
- Wave 4: ~4-6 min (4 agents, 2 batches)
- Wave 5: ~6-10 min (6 agents, 2 batches, with web search)
- **Total: ~25-35 min** for a full audit

Larger apps scale roughly linearly with code size.

---

## 11. Quick-Reference: The 23 Agent Files

```
WAVE 1 — RECONNAISSANCE
  01-cartographer.json   02-tour-guide.md
  03-librarian.json      04-timekeeper.md
WAVE 2 — RISK ANALYSIS
  05-bouncer.md          06-locksmith.md
  07-stress-tester.md    08-exploit-hunter.md
  09-cost-auditor.md     10-compliance.md
WAVE 3 — CODE QUALITY
  11-janitor.md          12-archivist.md
  13-doctor.md
WAVE 4 — FOUNDER TRANSLATION
  14-translator.md       15-economist.md
  16-storyteller.md      17-skeptic.md
WAVE 5 — LIVE FACT-CHECK
  18-documentarian.md    19-news-hound.md
  20-benchmarker.md      21-deprecation-hunter.md
  22-contrarian.md       23-editor-in-chief.md
```

---

## 12. Integration with Other Skills

- **fact-checker** — Wave 5's documentarian/news-hound use the same pattern.
- **kimi-pdf** — Weekend 3's compile-report.py uses it to generate the PDF.
- **delegate_task** — Every subagent is a `delegate_task` call (no recursion).
