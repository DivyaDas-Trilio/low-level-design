# Step 14 — Production-Readiness: The 12-Factor Prerequisites

*Series: Designing a Library Management System with DDD · Chapter 14 — Part II*

---

Before *any* deployment approach (Step 15 onward) works well, the **app itself must be built to be deployed**. You can have the slickest Kubernetes cluster on earth and still be dead in the water if your app writes sessions to local disk or reads its database password from a hard-coded string. This chapter makes the LMS *deployable* — and the canonical guide is the **[12-Factor App](https://12factor.net/)**, a set of principles for apps that run cleanly on modern platforms.

We won't recite all twelve dogmatically; we'll apply the ones that *matter*, each anchored to the LMS, and finish with a checklist you can hand to students.

> **The throughline:** a production-ready app is one that makes **no assumptions about the machine it runs on** and keeps **no important state inside itself**. Everything else follows from those two ideas.

---

## 14.1 Config & secrets come from the environment

**The principle (Factor III):** anything that varies between environments — the database URL, log level, even the fine rate — lives in the **environment**, never in code. This is *the* factor that makes "build once, deploy many" (Step 13) possible: the *same* image reads `DATABASE_URL` from the environment and connects to dev's SQLite or prod's Postgres without a rebuild.

```python
# src/config.py — config is read from the environment, with safe dev defaults
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///./dev.db"   # dev default; prod sets DATABASE_URL env var
    log_level: str = "INFO"
    fine_rate_paise: int = 500                  # ₹5/day — even a business policy is config
    max_active_loans: int = 2                   # rule #4, now tunable without a deploy

    class Config:
        env_file = ".env"                       # local-dev convenience ONLY (never committed)

settings = Settings()
```

**Secrets are config, but special.** A DB password is config — but you must *never* put it in code, in the image, or in git. Secrets come from a **secret manager** (Kubernetes Secrets, AWS Secrets Manager, Vault) and are injected as environment variables or mounted files **at runtime** (Step 26 goes deep). The rule: `git grep` for a password should return *nothing*.

> ⚠️ **The classic breach:** committing `.env` (with real creds) to git. Add it to `.gitignore` *and* `.dockerignore` on day one. We already did in the Dockerfile chapter's `.dockerignore`.

---

## 14.2 The processes are stateless (so you can run many)

**The principle (Factor VI):** the app is a **stateless process**. It keeps nothing important in memory or on local disk between requests — all persistent state lives in a **backing service** (the database, a cache). Any request can hit *any* instance.

**Our LMS is already stateless** — and not by luck, but because of the DDD design in Part I: all state lives behind repository interfaces (Step 10), in the database. There's no in-process session, no user data cached in a module global, no file written locally that a later request depends on.

> 🔗 **The critical connection back to Step 10:** this is *exactly* where the **in-memory repository must be swapped for the SQL one**. An `InMemoryLoanRepository` stores loans in a Python `dict` *inside one process* — run three copies of the app and each has its *own* dict, so a loan created on pod A is invisible to pod B. In-memory state is **not shareable**. Statelessness means: *state goes to a shared backing service*, and the `dict` repo was always a dev/test stand-in. The interface doesn't change — only the adapter (Step 11's `SqlLoanRepository`).

**Why this is the single most important factor for scaling:** if every request can be served by any instance, you can run 1 or 100 copies behind a load balancer and they're interchangeable. Stateful apps can't do this — and almost every scaling and reliability technique in later chapters *assumes* statelessness.

---

## 14.3 Backing services are attached resources

**The principle (Factor IV):** the database, cache, message queue, email provider — each is an **attached resource**, reached via a URL/credentials from config, and **swappable without a code change**. Swapping dev's local Postgres for prod's managed RDS is purely a config change (a different `DATABASE_URL`).

This is the *operational* twin of Step 10's Dependency Inversion: the domain depends on a repository *interface*; the deployment depends on a database *URL*. Both make the concrete backing store a detail chosen at the edge.

---

## 14.4 Disposability: fast startup, graceful shutdown

**The principle (Factor IX):** processes are **disposable** — they can be started or stopped at a moment's notice. The orchestrator (Step 21) will start, kill, move, and scale your process *constantly*. So:

- **Start fast** — boot in seconds, so scaling up and recovering from crashes is quick. (Don't do heavy work at import time.)
- **Shut down gracefully** — on `SIGTERM`, *stop taking new requests, finish in-flight ones, close DB connections,* then exit. A process that's killed mid-request corrupts user experience (a half-finished borrow).

```python
# graceful lifecycle in FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    # --- startup --- (open the DB connection pool, etc.)
    yield
    # --- shutdown --- (drain in-flight work, dispose the pool, flush logs)
    await engine.dispose()

app = FastAPI(lifespan=lifespan)
```

When Kubernetes sends `SIGTERM`, it also stops routing new traffic (via the readiness probe) and waits a grace period — so a well-behaved app finishes cleanly. This is what makes zero-downtime rolling deploys (Step 23) actually zero-downtime.

---

## 14.5 Logs are event streams to stdout (never files)

**The principle (Factor XI):** the app **does not manage log files**. It writes its logs as a stream of events to **stdout**, and the platform captures, routes, and stores them. The app shouldn't know or care whether logs end up in a file, Loki, or CloudWatch.

And make them **structured (JSON)**, not free-text — so they're *queryable* ("every `BorrowingLimitExceededError` for member X in the last hour"). Free-text logs are a graveyard; structured logs are a database.

```python
import logging, structlog   # structlog or json_log_formatter

logging.basicConfig(level=settings.log_level, handlers=[logging.StreamHandler()])  # → stdout
log = structlog.get_logger()
log.info("loan.created", loan_id=str(loan.id), member_id=str(member.id), due=str(due))
# → {"event":"loan.created","loan_id":"...","member_id":"...","due":"...","level":"info"}
```

---

## 14.6 Health checks (the platform's eyes)

Not strictly a 12-Factor item, but **essential** for production readiness — it's how the platform knows whether to route traffic to you or restart you. **Two distinct endpoints** (the distinction is load-bearing in Step 21):

```python
# api/health.py
@router.get("/healthz")        # LIVENESS — "is the process alive?" cheap, NO dependencies
def liveness():
    return {"status": "ok"}

@router.get("/readyz")         # READINESS — "can I serve traffic right now?" checks deps
def readiness(svc = Depends(get_service)):
    svc.ping_database()        # if the DB is unreachable, we are NOT ready
    return {"status": "ready"}
```

> **Why two, and why the difference matters:** *liveness* must be cheap and dependency-free — if you fail liveness because the DB blipped, the platform restarts every pod and you get a restart-loop outage. *Readiness* checks dependencies — if the DB is down, you stop *receiving* traffic but keep running, ready to recover. Conflating them is one of the most common production mistakes (we'll hammer this in Step 21).

---

## 14.7 A production-grade server (not the dev server)

The development server (`uvicorn main:app --reload`) is single-process, auto-reloading, and **not** built for production load. In production you run **Gunicorn managing multiple Uvicorn workers** — multiple processes to use all CPU cores, with timeouts and graceful shutdown:

```bash
gunicorn src.api.main:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 4 \                # ~ (2 × cores) + 1; tune to your CPU
  --bind 0.0.0.0:8000 \        # Factor VII: bind to a PORT (port binding)
  --timeout 30 --graceful-timeout 30
```

`--bind 0.0.0.0:8000` is **Factor VII (port binding)**: the app is self-contained and exports its service by binding to a port — it doesn't rely on being injected into an external web server.

---

## 14.8 Reproducible builds: pin your dependencies

**The principle (Factor II — dependencies):** declare dependencies **explicitly and exactly**, so a build is reproducible byte-for-byte. A loose `fastapi` can resolve to a different version next week and silently break you. Pin versions (a lockfile, or pinned `requirements.txt`):

```
# requirements.txt — pinned for reproducibility
fastapi==0.115.0
uvicorn[standard]==0.30.6
gunicorn==23.0.0
pydantic==2.9.2
pydantic-settings==2.5.2
sqlalchemy==2.0.35
alembic==1.13.3        # migrations (Step 18)
```

Reproducible builds are what make "build once, deploy many" *trustworthy* — the image you tested is provably the image you ship.

---

## The production-readiness checklist (hand this to students)

- [ ] **Config & secrets from the environment** — nothing hard-coded; `.env` git-ignored
- [ ] **Stateless** — all state in a backing service; in-memory repo swapped for SQL
- [ ] **Backing services attached via config** — DB swappable by changing a URL
- [ ] **Fast startup + graceful shutdown** on `SIGTERM`
- [ ] **Structured logs to stdout** — no app-managed files
- [ ] **`/healthz` (liveness) + `/readyz` (readiness)** endpoints, correctly distinguished
- [ ] **Production server** — Gunicorn + Uvicorn workers, binds to a `PORT`
- [ ] **Pinned dependencies** — reproducible builds
- [ ] **Migrations automated & backwards-compatible** (Step 18)
- [ ] **Resource needs known** (CPU/memory) for sizing (Step 21)

When every box is ticked, the app is ready to be packaged and shipped by *any* of the approaches in Step 15.

---

## Promises served

| Promise | How this chapter advanced it |
|---|---|
| **Correct** | Config (not code) per environment + pinned deps → the same artifact behaves predictably everywhere. |
| **Survives failure** | Statelessness + graceful shutdown → instances are disposable and interchangeable; crashes don't lose state. |
| **Available** | Health checks let the platform route around unhealthy instances and recover them. |
| **Observable** | Structured logs to stdout make behavior queryable. |
| **Secure** | Secrets out of code/image/git, sourced from a manager at runtime. |

## Key takeaways (the transferable lessons)

1. **A deployable app makes no assumptions about its machine and keeps no state inside itself.** Those two ideas generate almost every 12-Factor rule.
2. **Config (incl. secrets) lives in the environment** — that's what lets one immutable artifact run everywhere. Secrets never touch code, image, or git.
3. **Statelessness is the master key to scaling** — and it's exactly why the in-memory repo from Step 10 must become the SQL repo. State belongs in a shared backing service.
4. **Liveness ≠ readiness.** One asks "alive?" (cheap, no deps), the other "ready to serve?" (checks deps). Confusing them causes restart-loop outages.
5. **Run a real server and pin your dependencies** — reproducibility is what makes "build once, deploy many" trustworthy.

---

*Next — Step 15: Survey of the standard ways to run it. With a production-ready app in hand, we tour the full spectrum of deployment models — single VM, VM + images, PaaS, Docker on one host, Kubernetes/ECS, and serverless — each anchored to how you'd actually deploy the LMS, with a trade-offs table to decide which fits a given problem.*
