# ADR 005: Explicit run logging over implicit middleware

- **Status:** Accepted
- **Date:** 2026-04-18
- **Deciders:** Simon Mathiasen
- **Depends on:** [ADR 003](./003-orm-and-migrations.md)

## Context

Fase 1.5 introduces persistence to every tool endpoint: each call to
`/api/analyze`, `/api/extract`, `/api/summarize`, `/api/process`, `/api/pipeline`
and `/api/chat` must produce a row in the `runs` table. This record feeds the
run-history sidebar in the UI, future cost dashboards, and the audit log.

Two obvious ways to implement it:

1. **Middleware/decorator pattern.** A single `@log_run` decorator (or FastAPI
   middleware) wraps each endpoint. The endpoint code is untouched; logging
   happens transparently.
2. **Explicit service call.** Each endpoint calls `log_run(db, ...)` directly
   after the tool executes, passing the inputs and outputs it knows about.

The first approach is tempting because it removes ~3 lines of boilerplate from
every endpoint. But "tempting" is often a warning sign in infrastructure code.

## Decision

**Use explicit `log_run(db, ...)` calls in each endpoint.** Rejected the
middleware/decorator approach for this phase.

Concretely:

```python
@router.post("/analyze")
def analyze(req: AnalyzeRequest, db: Session = Depends(get_db)) -> ToolResponse:
    start = time.perf_counter()
    try:
        result = handle_analyze(req.text, focus=req.focus)
        status = "success"
        error_message = None
    except Exception as exc:
        result = None
        status = "error"
        error_message = str(exc)
        raise
    finally:
        duration_ms = int((time.perf_counter() - start) * 1000)
        log_run(
            db,
            tool_name="analyze",
            input_payload=req.model_dump(),
            output_payload=result,
            duration_ms=duration_ms,
            status=status,
            error_message=error_message,
        )
    return ToolResponse(success=True, data=result)
```

## Consequences

### Positive

- **Readable.** Anyone opening a router sees exactly what is logged. No
  spooky action at a distance.
- **Debuggable.** If a run is missing from the DB, there is one place to look:
  the endpoint that should have called `log_run`. No tracing through
  middleware layers.
- **Flexible per endpoint.** The `chat` endpoint streams via SSE and needs to
  log *after* the stream finishes, not before. An explicit call makes this
  trivial; middleware would need special handling.
- **Failure-tolerant.** `log_run` is best-effort — if the DB is down, the
  user-facing response still works. Middleware that tries to log "around" a
  response is harder to make failure-tolerant without careful thought.
- **Easier to evolve.** When Fase 5 adds token tracking or cost attribution,
  new fields are added to the `log_run` call site — no middleware changes.

### Negative

- **Boilerplate.** ~8-12 lines per endpoint (timer, try/except/finally,
  log_run call). For 6 endpoints that's ~60 lines of repeated structure.
- **Easy to forget.** A new endpoint added later might not call `log_run`.
  Mitigated by documenting the convention and adding a test that counts
  runs after hitting each endpoint.
- **Coupling.** Routers now depend on both the agent tools *and* the
  persistence layer. Acceptable coupling — routers are the orchestration
  layer and orchestrating logging is part of their job.

### Neutral

- If the boilerplate genuinely becomes painful (3+ new endpoint types per
  month), we can introduce a small helper like `with logged_run(db, "tool"):`
  context manager. That would be a *refinement* of this decision, not a
  reversal — the logging is still explicit, just wrapped in a context manager
  for ergonomics.

## Alternatives considered

- **FastAPI middleware that logs every request.** Rejected: too coarse. It
  would log `GET /`, static file requests, health checks — all noise. And
  it would need request-body inspection to get the tool inputs, which means
  reading the request body twice (brittle).

- **Decorator `@logged(tool_name)`.** Rejected because the SSE chat endpoint
  doesn't fit — the logging must happen after the async generator completes,
  not after the view function returns.

- **AOP-style automatic logging via class decoration.** Rejected as overkill
  for 6 endpoints.

- **Database trigger on INSERT.** Not applicable — we're logging *that* a run
  happened, not a data-change event.

## References

- [ADR 003 — ORM and migrations](./003-orm-and-migrations.md) (parent)
- [app/services/runs.py](../../app/services/runs.py) — the `log_run` helper
