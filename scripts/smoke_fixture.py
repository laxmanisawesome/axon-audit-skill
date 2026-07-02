#!/usr/bin/env python3
"""
Smoke-test fixture for Axon Audit — populate a workspace with realistic
agent outputs, mark all 23 agents done, auto-collect findings via lib.py,
then run compile-report.py to verify the end-to-end PDF pipeline.

Usage:
    # 1. Init the workspace
    python3 ~/.agents/skills/axon-audit/scripts/lib.py init \\
        --name "TestApp" --type "rn-expo" --stage "live" \\
        --url "https://testapp.example.com" \\
        --description "Synthetic smoke-test workspace"

    # 2. Copy this script into the new workspace, edit WORKSPACE path, run it
    cp ~/.agents/skills/axon-audit/scripts/smoke_fixture.py \\
        ~/.axon-audits/<workspace>/_populate.py
    # Edit the WORKSPACE constant at the top of the copied script
    python3 ~/.axon-audits/<workspace>/_populate.py

    # 3. Compile
    python3 ~/.agents/skills/axon-audit/scripts/compile-report.py \\
        ~/.axon-audits/<workspace>

Expected: 30+ page PDF, ~270 KB, 30 findings, 23 agent appendix entries.
"""
import subprocess
import sys
from pathlib import Path

# EDIT THIS for each smoke-test run
WORKSPACE = Path.home() / ".axon-audits/testapp-20260618-151915"  # noqa: E402
SCRIPTS = Path.home() / ".agents/skills/axon-audit/scripts"
sys.path.insert(0, str(SCRIPTS))
import lib  # noqa: E402

ws = lib.AuditWorkspace.from_path(WORKSPACE)


# --- Wave 1: Reconnaissance ---
# Format contract: agent markdown MUST use `## Severe` / `## Moderate` /
# `## Informational` headers followed by `- ` bullets. The bold
# `**Severe:**` form is NOT parsed by lib.py's parse_markdown_bullets_under_header().
ws.write_agent(1, "cartographer", {
    "app_type": "rn-expo",
    "framework": "expo-sdk-50",
    "deps": ["expo", "expo-router", "firebase", "expo-secure-store", "stripe"],
    "config_files": ["app.json", "eas.json", "firebase.json"],
    "build_commands": ["eas build --platform ios", "eas build --platform android"],
})
ws.write_agent(1, "tour-guide", """# User Journey

## Flow: Onboarding
1. Splash screen
2. Sign up with email

## Flow: Core Action
1. Home feed
2. Tap item
3. Detail view

## Friction points

- Email verification is required before profile setup
- No "remember me" - session expires every 7 days
""")
ws.write_agent(1, "librarian", {
    "data_stores": [
        {"name": "Firestore", "type": "cloud-nosql", "used_for": "user profiles, posts, comments"},
    ],
    "services": [
        {"name": "Firebase Auth", "purpose": "authentication"},
        {"name": "Stripe", "purpose": "payments"},
    ],
    "auth_providers": ["email-password", "google-oauth"],
    "apis": ["firestore-rest", "stripe-rest"],
    "webhooks": ["stripe-payment-events"],
})
ws.write_agent(1, "timekeeper", """# Timeline

**Last deploy:** 2026-05-12
**Commit cadence:** ~3 commits/week, slowing
""")

# --- Wave 2: Risk Analysis ---
ws.write_agent(2, "bouncer", """# Auth Report

## Severe

- No MFA on user accounts despite storing payment methods
- Auth tokens stored in AsyncStorage (not SecureStore) - extractable on rooted devices
- Session refresh tokens never rotate

## Moderate

- No rate limiting on login endpoint
- Password reset link expires after 24h (too long)

## Informational

- No password complexity requirements
""")
ws.write_agent(2, "locksmith", """# Secrets Report

## Severe

- Hardcoded Stripe live key in app.config.js (should be test key)

## Moderate

- Firebase config exposed without domain restriction

## Informational

- No .env.example file for new developers
""")
ws.write_agent(2, "stress-tester", """# Scaling Scenarios

## Severe

- At 100K users: single region, no CDN, no caching layer. Total collapse.

## Moderate

- At 10K users: Firestore read amplification on home feed query

## Informational

- Cold start latency on iOS above 200ms
""")
ws.write_agent(2, "exploit-hunter", """# Exploit Report

## Severe

- Stripe webhook does not verify signatures - fake events could be injected
- Missing deep link validation on `myapp://` scheme - could be hijacked

## Moderate

- AsyncStorage tokens extractable on rooted/jailbroken devices - CVSS 7.1
- No CSRF protection on POST endpoints

## Informational

- Verbose error messages leak stack traces in production
""")
ws.write_agent(2, "cost-auditor", """# Cost Report

## Moderate

- Firestore unbounded queries on home feed will explode at scale

## Informational

- No image optimization on user uploads
- Stripe fees higher than necessary due to international cards
""")
ws.write_agent(2, "compliance", """# Compliance Report

## Severe

- No user data export endpoint (GDPR Article 15 violation)

## Moderate

- User deletion path takes 30 days to complete (GDPR allows 30 days max)
- No opt-out mechanism for analytics data sale (CCPA)

## Informational

- PII stored in plaintext in Firestore user docs
""")

# --- Wave 3: Code Quality ---
ws.write_agent(3, "janitor", """# Dead Code Report

## Moderate

- Entire src/legacy/ directory imported by nothing (1,200 LOC)

## Informational

- src/utils/old-format.ts replaced 8 months ago
- 14 stale TODO comments
""")
ws.write_agent(3, "archivist", """# Ownership Map

## Moderate

- User role lives in three places: Firestore, AsyncStorage, JWT
- Subscription tier: Firestore, Stripe, AsyncStorage - three sources
- User preferences: Firestore, AsyncStorage, React state - three sources
""")
ws.write_agent(3, "doctor", """# Critical Risk

**Component:** Firestore security rules

**Why:** All data is publicly readable. Misconfigured rules allow any authenticated user to read/write any document.

**Blast radius:** Total data breach.

**Fix priority:** Immediate - fix today.
""")

# --- Wave 4: Founder Translation ---
ws.write_agent(4, "translator", """# Impact Map

## Finding: Firestore security rules allow public read/write
**Business impact:** Total data breach possible.
**Urgency:** Immediate

## Finding: Auth tokens in AsyncStorage
**Business impact:** Account takeover for ~5-10% of users.
**Urgency:** This week

## Finding: Stripe webhook signature not verified
**Business impact:** Attacker can grant themselves any subscription tier.
**Urgency:** This week
""")
ws.write_agent(4, "economist", """# Cost to Fix

## Finding: Firestore security rules
**Fix estimate:** 2 hours
**Cost of ignoring:** $50,000+

## Finding: Auth tokens in AsyncStorage
**Fix estimate:** 4 hours

## Finding: Stripe webhook signature
**Fix estimate:** 1 hour
""")
ws.write_agent(4, "storyteller", """# Executive Summary

## This week
### 1. Firestore security rules are wide open
**What:** Every collection in your database can be read and written by any logged-in user.
**Why:** Total data exposure. GDPR/CCPA fines + class action risk.
**Fix time:** 2 hours

### 2. Stripe webhook doesn't verify signatures
**What:** Your payment webhook accepts any POST that looks like a Stripe event.
**Why:** Anyone can grant themselves a paid subscription.
**Fix time:** 1 hour

### 3. Auth tokens stored insecurely on device
**What:** Login tokens are in AsyncStorage.
**Why:** Account takeover for a small percentage of users.
**Fix time:** 4 hours

## Next quarter
### 1. Home feed query doesn't paginate
**What:** Your main feed query has no cursor.
**Why:** Customer-facing breakage at 10K posts.
**Fix time:** 6 hours

### 2. GDPR data export endpoint missing
**What:** No way for users to request a copy of their data.
**Why:** Regulatory risk.
**Fix time:** 8 hours

## Scary thing
**What:** The Firestore security rules are so broken that this app cannot legally operate in the EU under GDPR.
**Why:** Regulatory shutdown risk.
**Fix time:** Immediate
""")
ws.write_agent(4, "skeptic", """# Skeptic Review

**Must-fix:**
- Firestore security rules
- Stripe webhook signature
- Auth token storage
- GDPR data export

**Nice-to-have:**
- Home feed pagination
- Triple source of truth
""")

# --- Wave 5: Live Fact-Check ---
ws.write_agent(5, "documentarian", """# Verified Sources

## API/Library: expo-secure-store
**Verdict:** Recommendation accurate.
""")
ws.write_agent(5, "news-hound", """# CVE Report

No critical CVEs.
""")
ws.write_agent(5, "benchmarker", """# Benchmarks

## Claim: AsyncStorage is slower than SecureStore
**Verdict:** Confirmed.
""")
ws.write_agent(5, "deprecation-hunter", """# Deprecation Report

No deprecations affecting recommendations.
""")
ws.write_agent(5, "contrarian", """# Contrarian Review

## Finding: Firestore security rules
**Verdict:** Real, urgency depends on review capacity.

## Finding: Auth tokens in AsyncStorage
**Verdict:** Real but urgency depends on app type.

## Finding: Stripe webhook signature
**Verdict:** Real, easy fix, should still be done.

## Finding: Home feed query
**Verdict:** Defer to next quarter.

## Finding: GDPR data export missing
**Verdict:** Still legally required, do it.
""")
ws.write_agent(5, "editor-in-chief", """# Final Report

**Surviving findings:** 6
- F001: No MFA on user accounts despite storing payment methods
- F002: Auth tokens stored in AsyncStorage (not SecureStore)
- F013: Stripe webhook does not verify signatures
- F007: Hardcoded Stripe live key in app.config.js
- F021: No user data export endpoint (GDPR Article 15 violation)
- F018: Firestore unbounded queries on home feed will explode at scale

**Methodology:** 23 agents, 5 waves, full verification.

**Flagged:** None.

**Cut:** None.
""")

# Mark all 5 waves done
for wave_num in [1, 2, 3, 4, 5]:
    ws.mark_wave(wave_num, "done")

print(f"OK Workspace populated: {WORKSPACE}")
print(f"   - 23 agent output files written")
print(f"   - All agents marked done")
print(f"   - All 5 waves marked done")

# Run lib.py collect to auto-extract findings (generates final/all-findings.json)
result = subprocess.run(
    [sys.executable, str(SCRIPTS / "lib.py"), "collect", str(WORKSPACE)],
    capture_output=True, text=True,
)
print("\n--- lib.py collect ---")
print(result.stdout)
if result.returncode != 0:
    print("STDERR:", result.stderr)
    sys.exit(1)

# Show the collected findings
import json  # noqa: E402
findings_file = WORKSPACE / "final" / "all-findings.json"
if findings_file.exists():
    data = json.loads(findings_file.read_text())
    print(f"\nOK {data.get('count', 0)} findings collected:")
    for f in data.get("findings", [])[:5]:
        print(f"  [{f['id']}] [{f['severity']:13s}] {f['raw'][:70]}")
    if data.get("count", 0) > 5:
        print(f"  ... and {data['count'] - 5} more")
