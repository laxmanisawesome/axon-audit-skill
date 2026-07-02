# Multi-Agent Pipeline Pattern — Reusable Recipe

> A class-level design pattern that emerged from building axon-audit. Any future
> skill that needs to orchestrate **N specialized subagents across sequential
> waves** can copy this skeleton instead of re-deriving it.

---

## When This Pattern Fits

Use it when you have a task that decomposes into:
- **Many independent dimensions** of analysis (security, cost, UX, ...) where each needs its own deep-dive
- **Sequential dependencies between groups** (e.g. "first map the codebase, then audit the auth")
- **Live fact-checking** against current docs/CVEs/benchmarks (Wave 5 in axon-audit)

Examples that fit: code audits, content moderation pipelines, marketing-copy review stacks, multi-language translation with quality scoring, vulnerability triage.

Examples that **don't** fit: single-shot questions, anything that fits in one `task` call, anything needing tight inter-agent feedback loops (use orchestrator subagent instead).

---

## The Skeleton (4 artifacts)

```
my-pipeline-skill/
├── SKILL.md                          # main entry point
├── scripts/
│   ├── lib.py                        # I/O helpers + CLI (see below)
│   ├── orchestrator.md               # procedure the main agent follows
│   └── test_pipeline.py              # smoke test (always write one)
├── references/
│   └── (per-wave checklists)         # loaded into subagent context
├── templates/
│   ├── input-form.md                 # user fills this in to start
│   └── agent-prompts/                # one .md per agent, named with number prefix
└── (runtime workspaces created at ~/.<skill>-runs/<slug>-<ts>/)
```

### Artifact 1: `lib.py` (Python helpers + CLI)

The orchestrator is **driven by the main agent**, not by a Python script calling LLM tools.
The `task` tool is an LLM tool — only the main agent loop can call it. So the Python code
just does the file I/O around those calls.

Required CLI subcommands:
- `init` — create the runtime workspace from a brief (md/json/CLI flags)
- `status` — print wave/agent status for the user
- `context --wave N` — assemble `context.json` for wave N from prior wave outputs
- `mark --wave N --agent <slug> --status done` — per-agent status
- `mark-wave --wave N --status done` — wave-level status (with **enforcement**: refuses unless all agents are done)
- `collect` — aggregate all findings into `final/all-findings.json`

Key design rules:
- **Brief parser must handle the user-facing form** (markdown with `- **Key:** Value` bullets). Strip trailing colons from bold keys.
- **Type normalization**: strip parentheticals like `"Web (Next.js)"` before lookup, then have a fallback ("if unrecognized but contains 'web', default to web").
- **Status enforcement**: `mark-wave done` should raise `ValueError` if any agent is not done. Catches the "I forgot to mark agent X" footgun.
- **Brief re-injection in founder/PM waves**: Wave 4 of axon-audit re-includes the original brief in its `context.json` because translation needs the founder context. Encode this as `context_includes_brief: bool` per wave in the wave table.

### Artifact 2: `orchestrator.md` (procedure doc)

This is the **operational manual** the main agent reads at the start of a run. Sections it must contain:

1. Mental model (the wave diagram)
2. Inputs you need from the user
3. Workspace init (one-liner)
4. Which references/checklists to load per app type
5. **Per-wave prompt template** (the exact `task` prompt string shape)
6. **Subagent type per agent** (usually `general` for analysis agents)
7. **Batch pattern** (3 tasks max per response → table showing batch count per wave)
8. Per-wave checklist
9. Failure handling (what to do when an agent returns no file, partial wave failure, etc.)
10. Status reporting format for the user
11. Time budget estimate per wave
12. End-to-end procedure for the Editor / compiler wave

### Artifact 3: `agent-prompts/*.md` (per-agent templates)

One file per agent. Use a numeric prefix (`01-`, `02-`, ...) so filesystem listing is in execution order. Each file has 4 sections:
1. **Role** — persona, one sentence
2. **Input** — what prior artifacts does this agent read?
3. **Task** — numbered list of what to do
4. **Output format** — exact structure (JSON for structured agents, markdown for narrative)

The `## Task` section is what gets pasted verbatim into the `task` tool `prompt` field.

### Artifact 4: `test_*.py` (smoke test)

A self-contained test that exercises the **full happy path** with no LLM calls. Simulates agent outputs with fixture strings, then:
- Verifies workspace scaffolding
- Verifies context aggregation includes/excludes the brief correctly per wave
- Verifies finding collection extracts and classifies properly
- Verifies status display
- Verifies enforcement (mark-wave refuses on incomplete agent set)

Goal: 30+ checks, all passing. Anything you ship without a test will break the first time someone runs it.

---

## Critical Implementation Lessons

### 1. The 3-task-per-call cap is real

The `task` tool supports up to 3 parallel calls per response for most users. **23 agents at 3-per-response = 9 batches, not 1 big call.** Plan the batch pattern from the start:

| Wave agents | Batches |
|-------------|---------|
| 4 | 2 (3+1) |
| 6 | 2 (3+3) |
| 3 | 1 (3) |
| 4 | 2 (3+1) |
| 6 | 2 (3+3) |
| **23 total** | **9 batches** |

### 2. Subagents write files, not return strings

The orchestrator's contract with each subagent is: **write a file at a known path in a known format.** The subagent's return value is a 1-paragraph summary for the user — the orchestrator never parses it. This is the only way to keep the pipeline robust to subagents going off-script.

### 3. Context handoff via files, not via `context` field

The `task` tool `prompt` field is for **prompt context** (the role, the task, the format). **Data flows through files.** Each wave's `context.json` lives at `<workspace>/waves/<NN>-<slug>/context.json` and contains:
- The brief (for waves that need founder context)
- All prior wave outputs (parsed JSON or raw markdown)

This means the orchestrator's I/O step is:
1. Read prior wave files → build next wave's `context.json`
2. Pass the file **path** (not the content) to the subagent in its `context` string
3. Subagent reads the file itself

Avoids token blowup and keeps subagent memory clean.

### 4. Per-agent status + per-wave status (separate)

You need both. Per-agent is the source of truth; per-wave is a derived view. The enforcement in `mark-wave done` is the bridge: it refuses to flip the wave to done unless every agent is individually done. This catches "I forgot agent 17" silently otherwise.

### 5. JSON agents vs markdown agents

Some agents output structured data (cartographer → dep list, librarian → inventory). Others output narrative (skeptic, storyteller). The skill should know which is which:
- **JSON agents**: cartographer, librarian (and any agent whose output is consumed by code, not humans)
- **Markdown agents**: everyone else

JSON agents write `.json` files; markdown agents write `.md` files. The orchestrator's `build_context` reads each correctly.

### 6. Test before you trust

A 35-check smoke test caught 3 real bugs during axon-audit Weekend 2:
- Markdown brief parser didn't handle `- **Key:** Value` (regex missed the colon inside `**...**`)
- `parse_brief()` treated string as path even when it was markdown content
- `mark-wave done` allowed incomplete waves until we added enforcement

Without the test, these would have shipped as "works on my machine" footguns.

---

## Anti-Patterns to Avoid

| Don't | Do instead |
|-------|-----------|
| Build a Python script that calls LLM tools | Build helpers; let the main agent drive the `task` tool |
| Pass prior wave outputs through the prompt text | Pass the **file path**; subagent reads it |
| Trust a subagent's return string | Require a file at a known path; ignore the return |
| Try to fit 23 agents in one response | Plan for ~9 batches (3-task cap) |
| Let `mark-wave done` succeed with pending agents | Enforce: refuse unless all agents are done |
| Build the whole skill before testing | Write the smoke test alongside `lib.py` |
| Use one global status flag | Per-agent + per-wave, with enforcement between them |
| Forget the user-facing form | Always have a `templates/input-form.md` users can fill in |

---

## Copy-This Checklist (for your next pipeline skill)

When you start a new multi-agent pipeline skill, copy this checklist:

- [ ] `scripts/lib.py` with subcommands: `init`, `status`, `context`, `mark`, `mark-wave`, `mark-final`, `collect`
- [ ] `scripts/orchestrator.md` with 12 sections (mental model → end-to-end procedure)
- [ ] `templates/agent-prompts/` with one .md per agent, numeric prefix
- [ ] `templates/input-form.md` (the user-facing form)
- [ ] `scripts/test_*.py` with 30+ checks, exercises full happy path
- [ ] Per-wave table in `lib.py` with `(num, slug, fname, fmt, context_includes_brief)` for each agent
- [ ] Markdown brief parser handles `- **Key:** Value` syntax (with `rstrip(":")` on the captured key)
- [ ] Type normalization with parenthetical stripping + fallback
- [ ] `mark-wave done` enforcement (raises `ValueError` if any agent is not done)
- [ ] Status display with ✅/⏳/❌ glyphs per agent
- [ ] Finding collector walks waves 2+3, extracts bullets under `## Severe` / `## Moderate` / `## Informational` headers
- [ ] SKILL.md has a "Quick Start (for the main agent)" section at the top
- [ ] Per-runtime workspace at `~/.<skill>-runs/<slug>-<ts>/`, never in the skill dir
- [ ] Test passes 30+/30+ before you ship

---

## Reference Implementation

**axon-audit** is the canonical example: 23 agents, 5 waves, 9 batches, file-based handoff, 35/35 test pass rate. Copy its structure when building the next pipeline.
