# Web App Specific Audit Checks

## General
- Is HTTPS enforced? TLS version 1.2+?
- CSP headers present and restrictive?
- CORS configured properly? Not `Access-Control-Allow-Origin: *` for production
- Rate limiting on auth endpoints? Login brute force protection?
- Session management: timeout configured? Secure + HttpOnly cookies?
- Error handling: stack traces leaking to client?
- Logging: PII in logs? Structured logging enabled?

## Deployment
- Reverse proxy (nginx/Caddy): correct config? Rate limiting? Websocket support?
- Dockerfile: multi-stage build? Not running as root? No secrets in layers?
- CI/CD: automated tests run before deploy? Rollback strategy documented?
- Health check endpoints: `/health` or `/ready` returning status?
- Monitoring: error tracking, uptime monitoring, alerting configured?

## Auth
- OAuth2 PKCE flow used (not implicit flow)?
- JWT: short expiry (15 min)? Refresh token rotation?
- MFA: offered for admin accounts?
- Password policy: minimum length, common password check?
- Session invalidation on password change?

## Data
- Database backups: automated? Encrypted? Tested restore?
- Query parameterization: prepared statements used everywhere?
- ORM: N+1 detection enabled?
- Migration: schema changes are reversible?
- Secrets: in environment variables, not code or config files?
