# 0006 — Agents as a 24/7 autonomous workforce via job queue

**Status:** Accepted (architecture decision); Implementation: Phase 2
**Date:** 2026-04-27

## Context

The vision for the platform is agents that operate continuously — processing a queue of tickets, specs, or questions 24 hours a day, 7 days a week, without human initiation per task. The current MVP (Minimum Viable Product) runs agents on-demand (CLI invocation). This ADR documents the architectural decision for the 24/7 model.

Requirements for continuous operation:
- **Idempotency**: the same job processed twice must produce the same result (no duplicates)
- **Resumability**: a failed mid-workflow job can be restarted from the last checkpoint, not from scratch
- **Backpressure**: workers should not be overwhelmed if job volume spikes
- **Observability**: every job's trace must be correlated end-to-end in LangFuse

## Decision

The 24/7 workforce model uses a **job queue + stateless workers + LangGraph checkpointer**:

1. **Job queue**: Postgres-based (using the same Postgres already in the compose stack). Each job row contains: `id`, `type` (e.g., `dev_agent`), `payload` (JSON), `idempotency_key` (unique per logical task), `status` (`pending | running | done | dead`), `created_at`, `updated_at`.

2. **Workers**: stateless Python processes that poll the queue (`SELECT ... FOR UPDATE SKIP LOCKED`), execute the agent workflow, and mark jobs `done` or `dead` (after N retries).

3. **LangGraph checkpointer**: `SqliteSaver` in development, `PostgresSaver` in production. Each job passes a `thread_id = idempotency_key` to LangGraph. If a worker crashes mid-workflow, the next worker picks up the job and LangGraph resumes from the last saved checkpoint — not from scratch.

4. **Trace correlation**: the `idempotency_key` is passed as `trace_id` to LangFuse so every span in a job's workflow is correlated under a single trace.

```
Job queue (Postgres)
      |  poll (FOR UPDATE SKIP LOCKED)
Worker (stateless Python process)
      |  thread_id = idempotency_key
LangGraph Supervisor -> agents
      |  checkpointed in Postgres
LangFuse (trace_id = idempotency_key)
```

## Alternatives considered

| Alternative | Reason not chosen |
|-------------|-------------------|
| Redis Streams | Excellent for high-throughput streaming. Adds a new service (Redis) to the stack. Since Postgres is already running, a Postgres-based queue avoids the extra dependency for the MVP. Can migrate later if throughput requires it. |
| Celery + Redis/RabbitMQ | Full-featured but heavyweight. Adds Celery worker, beat scheduler, broker, and result backend — 3-4 new services. Overengineered for initial scale. |
| Cloud queues (SQS, Cloud Tasks) | Valid for production cloud deployments. Breaks local reproducibility requirement (ADR 0007). Add as a config option later. |
| Simple cron | No retry, no idempotency, no checkpointing. Suitable only for one-shot scheduled tasks, not continuous workforce. |

## Consequences

**Positive:**
- Single new Postgres table — no new infrastructure service needed for Phase 2.
- `FOR UPDATE SKIP LOCKED` is a battle-tested pattern for Postgres-based queues (used by Que, GoodJob, Sidekiq-Pro).
- LangGraph checkpointing means worker crashes are not catastrophic — work is not lost.
- Idempotency key prevents duplicate processing even if a job is re-queued.
- Full trace correlation in LangFuse from job enqueue to agent completion.

**Negative / trade-offs:**
- Postgres is not designed for high-throughput queuing (> ~1000 jobs/sec). At that scale, migrate to Redis Streams or SQS.
- Workers must be careful to handle `FOR UPDATE SKIP LOCKED` correctly to avoid deadlocks.
- `PostgresSaver` for LangGraph checkpointing requires a schema migration.

**Risks:**
- Idempotency key uniqueness must be enforced at the application level AND via a Postgres UNIQUE constraint.
- Long-running agent workflows may hold a Postgres row lock for minutes. Tune `lock_timeout`.
