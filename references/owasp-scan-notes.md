# OWASP Top 10 — Condensed for Agent Use

## A01: Broken Access Control
- **What to check:** Can user A access user B's data? Can a free user access premium features? Can an anonymous user hit admin endpoints?
- **Common signs:** IDs in URLs that aren't validated, frontend-only permission checks, missing role verification on server endpoints

## A02: Cryptographic Failures
- **What to check:** Passwords stored in plain text? Tokens in URL params? Data transmitted over HTTP? Weak TLS version?
- **Common signs:** `http://` instead of `https://`, `password` field in DB without hash, hardcoded JWT secrets

## A03: Injection
- **What to check:** SQL queries using string concatenation? NoSQL queries with user input? Command execution with unsanitized input?
- **Common signs:** `.exec(` or `.query(` with `${var}` interpolation, raw `eval()` calls

## A04: Insecure Design
- **What to check:** No rate limiting on auth? No MFA for admin? Missing "forgot password" security? No audit trail for sensitive actions?
- **Common signs:** Login without lockout, password reset without token validation, no request logging

## A05: Security Misconfiguration
- **What to check:** Debug mode on in production? Default credentials? Directory listing enabled? Error stack traces visible? Unnecessary open ports? CORS `*`?
- **Common signs:** `debug: true`, `NODE_ENV=development`, default passwords in config

## A06: Vulnerable Components
- **What to check:** Outdated dependencies? Known CVEs? Unmaintained libraries? Pinned versions that haven't been updated in 2+ years?
- **Common signs:** `package.json` with old versions, no `npm audit` or `yarn audit` in CI

## A07: Identification and Auth Failures
- **What to check:** Weak passwords allowed? No account lockout? Session not invalidated on logout? JWT with no expiry? Session fixation possible?
- **Common signs:** Passwords < 8 chars accepted, infinite session lifetime, no "logout all devices"

## A08: Software and Data Integrity Failures
- **What to check:** CI/CD pipeline without signature verification? Dependencies from untrusted sources? Unvalidated auto-updates?
- **Common signs:** Direct git dependencies from random repos, no lockfile, `curl | bash` installs

## A09: Security Logging and Monitoring Failures
- **What to check:** No logging of auth failures? No alerts on suspicious activity? Logs not retained? No monitoring of critical actions (payment, account deletion)?
- **Common signs:** No log aggregation, no alerting, logs that show plaintext PII

## A10: SSRF
- **What to check:** Does the app fetch user-supplied URLs? Are there internal network requests that could be redirected?
- **Common signs:** Webhook handlers that fetch URLs from user input, image proxy endpoints
