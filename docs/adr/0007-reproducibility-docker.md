# 0007 — Full local reproducibility via Docker Compose

**Status:** Accepted
**Date:** 2026-04-27

## Context

A portfolio project that requires manual environment setup is not demonstrable in an interview, not shareable with collaborators, and not trustworthy as a reference architecture. The project must be runnable from a clean machine in two commands.

## Decision

All external services (Postgres, Qdrant, LangFuse) run via **`docker compose -f infra/docker-compose.yml up -d`**. The only host dependency is Docker Desktop and Python 3.11+. The entire setup sequence is:

```bash
git clone <repo>
cd framework_multiagentes
cp .env.example .env     # edit OPENAI_API_KEY
make setup               # docker compose up -d + pip install -e .[dev]
make run-dev-agent SPEC=cases/dev_agent/examples/feature_health.md
```

No absolute paths in code. No cloud accounts required. No manual service setup.

## Alternatives considered

| Alternative | Reason not chosen |
|-------------|-------------------|
| Cloud-hosted services (RDS, Qdrant Cloud, LangFuse Cloud) | Requires accounts, credentials, and network access. Breaks reproducibility for reviewers without those accounts. |
| Conda environment | Solves Python dependencies but not service dependencies (Postgres, Qdrant, LangFuse). |
| Devcontainer (VS Code) | Excellent for team onboarding but adds complexity for simple demonstration. Can be added as an enhancement. |
| Manual installation guide | Error-prone, OS-specific, and creates "works on my machine" problems. |

## Consequences

**Positive:**
- `make setup` is the single entry point. No hidden steps.
- `.env.example` documents every required variable. No undocumented secrets.
- Docker Compose services have `healthcheck` — dependent services wait for readiness.
- Pinned image versions (`postgres:16`, `qdrant/qdrant:v1.13.2`) prevent surprises from upstream updates.

**Negative / trade-offs:**
- Requires Docker Desktop (3+ GB). Not suitable for very constrained environments.
- Local Docker performance on macOS with Apple Silicon may differ from Linux production. Use `platform: linux/amd64` in compose if needed.

**Risks:**
- Docker image versions must be periodically updated for security patches. The CI pipeline should include a weekly image-pull test.
