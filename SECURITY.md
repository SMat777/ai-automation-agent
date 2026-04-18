# Security Policy

Security is treated as a first-class concern in this project. This document
describes what we protect, how to report vulnerabilities, and the threat model
that guides design decisions.

## Supported versions

This project is pre-1.0 and under active development. Only the `main` branch
receives security updates. If you are running a fork or an older version,
please rebase onto `main` before reporting issues.

## Reporting a vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Instead, email **simon.mathiasen.dev@gmail.com** with:

- A description of the vulnerability
- Steps to reproduce
- Your assessment of impact (who is affected, what can an attacker do?)
- Any suggested fix, if you have one

**What you can expect:**

- Acknowledgement within 72 hours
- A first assessment within 7 days
- A fix (or a mitigation + ETA) within 30 days for high-severity issues
- Credit in the release notes unless you prefer to remain anonymous

Please do not exploit or disclose the vulnerability publicly until we have
released a fix.

## Scope

In scope:

- The web application served by FastAPI (`server.py`, `app/` once restructured)
- The AI agent code (`agent/`)
- The automation pipeline (`automation/`)
- The Docker images and deployment configuration
- The frontend (XSS, CSRF, insecure URL handling)

Out of scope:

- Third-party services (Anthropic API, GitHub API, JSONPlaceholder) — report to them
- Denial of service from obvious resource exhaustion (LLM costs, massive uploads) — we will add limits but not treat "spam the API with huge documents" as a vulnerability
- Vulnerabilities in outdated dependencies that are already flagged by `pip-audit` / `npm audit`

## Threat model (current)

> Note: this model reflects the *current* architecture (pre-persistence). It will be
> extended as Fase 1-8 of the upgrade plan introduce authentication, file upload,
> and deployment.

### Assets we protect

| Asset                     | Why it matters                                  |
|---------------------------|-------------------------------------------------|
| The Anthropic API key     | Direct financial exposure (token cost abuse)    |
| User-pasted document text | May contain PII, business secrets, contracts    |
| Server integrity          | An attacker running arbitrary code on our host  |
| Downstream tool integrity | Preventing prompt injection from calling tools it shouldn't |

### Threats considered (STRIDE)

| Threat                   | Example                                                    | Mitigation                                         |
|--------------------------|------------------------------------------------------------|----------------------------------------------------|
| **S**poofing             | Attacker pretends to be a legitimate frontend              | Same-origin policy, CORS allow-list (hardened in Fase 2) |
| **T**ampering            | Attacker modifies a request in flight                      | HTTPS (enforced at deployment); input validation via Pydantic |
| **R**epudiation          | User denies having run a tool                              | Audit log (added in Fase 1)                        |
| **I**nformation disclosure | Error message leaks internal paths or API key            | Generic error responses; env vars never logged     |
| **D**enial of service    | Massive upload exhausts memory                             | Request size limits (added in Fase 3)              |
| **E**levation of privilege | Tool misuse to run arbitrary subprocess                  | `run_pipeline` is constrained to a whitelist of pipeline names |

### Known weaknesses (tracked)

- `CORSMiddleware` is currently wide open (`allow_origins=["*"]`). Tightened in Fase 2.
- No authentication or rate-limiting. Added in Fase 2.
- `run_pipeline` shells out via `subprocess` — safe today because `pipeline` is
  whitelisted, but this is the highest-risk code path and is explicitly called out.
- No structured logging yet — a successful attack would be hard to reconstruct.
  Added in Fase 5.

## Secure development practices

- **Dependency scanning.** `pip-audit` and `npm audit` run in CI on every push.
  High-severity findings block merges.
- **Static analysis.** `ruff` (lint), `mypy` (types), `eslint` (TS). Configured to
  fail CI on violations.
- **Secret scanning.** GitHub's built-in secret scanning is enabled. Any committed
  secret triggers a block and a rotation request.
- **No secrets in the repo.** All secrets come from environment variables.
  `.env.example` documents each required variable; `.env` is gitignored.
- **Principle of least privilege.** The deployed app runs as a non-root user
  in a slim container (Fase 8).

## LLM-specific considerations

The app wraps a large language model. This introduces class-specific risks that
OWASP has catalogued as the **OWASP LLM Top 10**. Addressed in Fase 4–5:

- **Prompt injection** — user-supplied text cannot escape system-prompt boundaries;
  delimiters and role separation are used throughout.
- **Insecure output handling** — markdown rendering sanitises links (only `http(s)://`
  allowed, preventing `javascript:` XSS).
- **Sensitive information disclosure** — the agent is instructed never to echo back
  API keys or internal configuration.
- **Model denial of service** — per-user rate limits + token budget caps.

## Governance

This project aspires to SOC 2-informed discipline even as a hobby/showcase
project. Concretely:

- **Security** — see above
- **Availability** — deployed instance targets 99% uptime; runbook in `docs/RUNBOOK.md`
- **Processing integrity** — validation in Pydantic/Zod; tested with property-based tests
- **Confidentiality** — no document content logged; audit log omits payloads
- **Privacy** — users can delete their account and all associated data (Fase 2)

These are aspirations that will be met progressively. Each upgrade phase should
strengthen at least one of these pillars — see `docs/adr/` for specifics.

---

*Last updated: 2026-04-18. This document is a living artifact and is updated
alongside the threat model as the architecture evolves.*
