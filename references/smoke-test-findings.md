# Smoke Test Findings — 2026-06-18

Lessons from running the Axon Audit pipeline end-to-end on a synthetic
TestApp workspace (`/root/axon-audits/testapp-20260618-151915/`). Future
runs of `compile-report.py` should not have to rediscover these.

---

## Environment

- **kimi-pdf path:** `/root/.agents/skills/kimi-pdf/scripts/html_to_pdf.js`
  (NOT `/app/.kimi/...` — the kimi-pdf skill lives under `.agents/`).
  The full PDF toolchain is in that directory (`pdf.sh`, `html_to_pdf.js`,
  `paged.polyfill.js`). Run `pdf.sh check` to verify node + playwright +
  chromium are installed.
- **Output goes to:** `<workspace>/final/audit-report.pdf`
- **Intermediate HTML kept at:** `<workspace>/final/report.html`

---

## Format contracts agent markdown MUST follow

`lib.py:collect_findings()` calls `parse_markdown_bullets_under_header()`
to extract findings from Wave 2 and Wave 3 agent outputs. The parser:

1. Looks for `## Severe`, `## Moderate`, or `## Informational` headers
   (case-insensitive, exact match on the stripped header).
2. Collects lines beginning with `- ` or `* ` bullets until the next
   `## ` / `### ` header at the same or shallower depth.

**Wrong format (silently produces 0 findings):**
```markdown
**Severe:**
- finding one
- finding two
```

**Correct format:**
```markdown
## Severe

- finding one
- finding two
```

This is the most common reason `lib.py collect` returns 0 findings.

---

## lib.py API gotchas

- `AuditWorkspace.wave_dir(wave_num)` returns a Path but does NOT create
  the directory. Use `ws.write_agent(...)` to write content — it creates
  the directory and the file atomically.
- `ws.mark_agent(wave_num, agent_slug, status)` takes the **slug**
  (`"bouncer"`), NOT the agent number (`5`).
- There is no `ws.save_all_findings()` method. Use the `lib.py collect`
  subcommand (or `ws.collect_findings()` directly) to auto-derive
  findings from the agent markdown.
- `ws.mark_wave(wave_num, "done")` raises `ValueError` if any agent in
  that wave isn't already `done`. Always mark agents first.

---

## compile-report.py bugs fixed during smoke test

1. **Page header duplication.** `@page { @top-center { content: string(doctitle) } }`
   combined with `h1 { string-set: doctitle content() }` caused every
   section title to render twice (once in the page header, once on the
   page). **Fix:** removed the running header entirely — the section h1
   on each page already provides navigation.
2. **Scary section missing from exec summary.** `build_executive_summary()`
   only parsed the Doctor agent's `## Component:` field for the Scary
   item; the Storyteller's `## Scary thing` section was ignored.
   **Fix:** parse the Storyteller's Scary section first, fall back to
   Doctor only if missing. Also made `_parse_storyteller_items()`
   accept single-item sections without a `### N.` header.
3. **Verification status always "unverified".** `_load_all_findings()`
   read `all-findings.json` and `build_findings_summary()` re-read it
   separately, so the verification-threading step mutated findings that
   the summary table never saw. **Fix:** thread findings as a list
   parameter between the two functions.

---

## Known limitations

- **Verification accuracy ~70%.** The Editor-in-Chief's "Surviving
  findings:" list uses a fuzzy word-overlap match against the
  auto-generated finding IDs (F001, F002, ...). The Editor prompt
  should reference `all-findings.json` directly to use exact IDs.
- **Detailed findings show `—` for Business Impact / Cost to Fix**
  unless the Translator/Economist outputs use the same word-form as the
  finding's `raw` field. The fuzzy match needs ≥2 common words.
- **Some blank pages reported** (P2, P29 in the test PDF) — these are
  page-break artifacts at section boundaries with very short content.
  Cosmetic only, doesn't affect deliverable quality.
- **Cover version stamp is wrong.** It uses `run_slug.rsplit('-', 2)[0]`
  which strips the timestamp, not a real semantic version.

---

## Reusable smoke-test fixture

`scripts/smoke_fixture.py` is a runnable fixture that populates a
workspace with realistic agent outputs, marks everything done, and
calls `lib.py collect` to produce 30 findings. Use it to verify the
compiler after any change to `compile-report.py` or `report_template.py`.

The fixture is at `scripts/smoke_fixture.py`. Copy it into a workspace,
edit the `WORKSPACE` path, and run it. Then run `compile-report.py`
on that workspace. Full smoke-test sequence:

```bash
# Init
python3 ~/.hermes/skills/devops/axon-audit/scripts/lib.py init \
    --name "TestApp" --type "rn-expo" --stage "live" \
    --url "https://testapp.example.com"

# Populate
cp ~/.hermes/skills/devops/axon-audit/scripts/smoke_fixture.py \
    /root/axon-audits/<workspace>/_populate.py
# Edit WORKSPACE in _populate.py
python3 /root/axon-audits/<workspace>/_populate.py

# Compile
python3 ~/.hermes/skills/devops/axon-audit/scripts/compile-report.py \
    /root/axon-audits/<workspace>
```

Expected: 33-page PDF, ~270 KB, 30 findings, 23 agent appendix entries.
