# Step 18 — Database & Migrations

*Series: Designing a Library Management System with DDD · Chapter 18 — Part II*

---

The app is stateless, packaged, and tagged. The **database is none of those things** — and it's where most production incidents are born. You can throw away and replace a stateless container freely; you **cannot** throw away your data. This chapter is about evolving the schema *safely* while the system keeps serving — the single hardest part of zero-downtime deployment.

> **The core tension:** during a rolling deploy (Step 23), **old and new versions of your code run *simultaneously* against the *same* database** for a few minutes. Every schema change must be safe for *both* versions at once. Get this wrong and you take an outage mid-deploy.

---

## 18.1 Why the database is special

A stateless app instance is **disposable** — kill it, start a fresh one, no loss. The database is the opposite:

- It holds the **only copy** of truth (the loans, members, fines).
- You can't "roll back" data the way you roll back code — a deleted column takes its data with it.
- It's usually a **single shared resource** that every app instance talks to at once.

So changes to it must be **deliberate, versioned, reversible-in-principle, and backwards-compatible.** That's what migrations give you.

---

## 18.2 Schema migrations: versioned, ordered, in git

A **migration** is a small, ordered, version-controlled script that changes the database schema (or data). The tool for SQLAlchemy (our Step 11 ORM) is **Alembic**. Migrations live *in the repo*, are applied in order, and each one knows how to go `upgrade` (forward) and `downgrade` (back).

```bash
alembic revision --autogenerate -m "create loan table"   # author a migration from model changes
alembic upgrade head                                       # apply all pending migrations
alembic downgrade -1                                       # (in principle) step back one
alembic history                                            # the ordered ledger of changes
```

A generated migration for the LMS `loan` table (mirroring the Step 6 ER diagram):

```python
# migrations/versions/0003_create_loan.py
revision = "0003_create_loan"
down_revision = "0002_create_book_copy"        # ordering: this runs AFTER 0002

def upgrade():
    op.create_table(
        "loan",
        sa.Column("loan_id", sa.String, primary_key=True),
        sa.Column("member_id", sa.String, sa.ForeignKey("member.member_id"), nullable=False),
        sa.Column("copy_id",   sa.String, sa.ForeignKey("book_copy.copy_id"), nullable=False),
        sa.Column("borrow_date", sa.Date, nullable=False),
        sa.Column("due_date",    sa.Date, nullable=False),
        sa.Column("status",     sa.String, nullable=False),
    )
    op.create_index("ix_loan_member_active", "loan", ["member_id", "status"])  # for count_active

def downgrade():
    op.drop_table("loan")
```

> Notice the index `ix_loan_member_active` — it exists because Step 10's `count_active_for_member` query needs it. **Access patterns drive indexes** (the Step 6 persistence note paying off). Without it, counting a member's active loans scans the whole table.

---

## 18.3 The golden rule: backwards-compatible migrations (expand/contract)

Because old and new code run together mid-deploy, **a migration must never break the currently-running version.** The safe technique is **expand/contract** (a.k.a. *parallel change*), spread across **multiple releases**.

### The wrong way (an outage)

Say we want to rename `loan.status` to `loan.state`. The naive migration:

```python
op.alter_column("loan", "status", new_column_name="state")   # ❌ runs in the deploy
```

The instant this runs, every *old* pod still doing `SELECT status FROM loan` **crashes** — and old pods are still serving traffic during a rolling deploy. Instant partial outage.

### The right way — expand → migrate → contract, across releases

**Release 1 — Expand** (add the new, keep the old; both work):
```python
op.add_column("loan", sa.Column("state", sa.String, nullable=True))   # additive, safe
# backfill existing rows (data migration):
op.execute("UPDATE loan SET state = status WHERE state IS NULL")
```
Deploy code that **writes both** `status` and `state`, reads `status`. Old pods still work (they only know `status`); new pods work too.

**Release 2 — Transition:** deploy code that **reads `state`, writes both.** Now nothing depends on `status` for reads.

**Release 3 — Contract** (remove the old, now that no running code uses it):
```python
op.drop_column("loan", "status")   # safe NOW — nothing reads it anymore
```

```
 Release 1: add `state`, backfill, write both ──► Release 2: read `state`, write both ──► Release 3: drop `status`
 (each release is safe for the code running before AND after it)
```

> **The principle, generalized:** *never make a destructive or incompatible schema change in the same release as the code that needs the new shape.* Add → shift → remove, each step compatible with the version running beside it. This is exactly what makes zero-downtime deploys possible.

**Safe by themselves** (additive): adding a nullable column, adding a table, adding an index (use `CONCURRENTLY` on Postgres to avoid locking). **Dangerous** (need expand/contract): renaming/dropping columns, changing types, adding a `NOT NULL` without a default, adding a unique constraint to existing data.

---

## 18.4 Run migrations as a *separate* step — never at app startup

A tempting anti-pattern is running `alembic upgrade head` inside the app's startup code. **Don't.** With multiple pods (Step 21):

- **All N pods race** to run the same migration simultaneously → lock contention, errors, partial application.
- A migration failure becomes a **crash-loop** of your whole fleet, not a clean, visible failure.
- Startup gets slow and unpredictable, breaking liveness/readiness timing.

Instead, run migrations as a **discrete, one-shot step that completes *before* the new pods start** — a Kubernetes **Job** (or an init container, or a CI/CD pipeline stage):

```yaml
# migrate-job.yaml — runs once, to completion, before the app rollout
apiVersion: batch/v1
kind: Job
metadata: { name: lms-migrate-0003 }
spec:
  backoffLimit: 1
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: migrate
          image: ghcr.io/your-org/lms:sha-9f8c2a1   # SAME image, different command
          command: ["alembic", "upgrade", "head"]
          envFrom: [{ secretRef: { name: lms-secrets } }]
```

The CD pipeline (Step 20) sequences it: **run migration Job → wait for success → roll out new app pods.** One runner, one transaction, visible success/failure.

---

## 18.5 The other database realities

- **Forward-only in production.** Tidy `downgrade()` scripts are great in dev, but in prod you rarely "un-migrate" — you **roll forward** with a new corrective migration. (Un-applying a migration that already deleted data can't bring the data back.) Treat down-migrations as a dev convenience, not a prod safety net.
- **Back up before migrating.** Always have a tested, recent backup before a schema change. An untested backup is not a backup (Step 27).
- **Test migrations in staging first** against production-like data and volume — a migration that's instant on 100 rows can lock a table for minutes on 100 million.
- **Connection pooling.** The DB has a hard cap on connections. Many app pods × a pool each can exhaust it (a "connection storm"). Bound your pool and, at scale, front Postgres with **PgBouncer**. (Full scaling treatment in Step 24.)
- **Migrations vs. data migrations.** *Schema* migrations change structure (add column); *data* migrations change/backfill content (`UPDATE loan SET state = status`). Big backfills should be **batched** so they don't lock the table or blow up memory.

---

## Promises served

| Promise | How this chapter advanced it |
|---|---|
| **Correct** | Versioned, ordered migrations make schema changes deliberate, reviewable, and reproducible across environments. |
| **Available** | Expand/contract + a pre-deploy migration Job = schema evolves with **zero downtime**, even with old+new code coexisting. |
| **Survives change** | Forward-only roll-forward + backups give a safe path when a change goes wrong. |
| **Survives failure** | Migrations as a discrete step fail *visibly* instead of crash-looping the fleet. |

## Key takeaways (the transferable lessons)

1. **The database is the one thing you can't throw away** — so its changes must be versioned, ordered, and backwards-compatible.
2. **Old and new code run together mid-deploy** — every migration must be safe for *both*. That constraint drives everything else.
3. **Expand → migrate → contract, across releases.** Add the new, shift code to it, then remove the old. Never destroy in the same release that needs the new shape.
4. **Run migrations as a separate one-shot step**, before the app rollout — never at app startup, or N pods will race and crash-loop.
5. **Roll forward, not back; back up first; test on prod-like data.** And let access patterns (Step 10's queries) drive your indexes.

---

*Next — Step 19: Continuous Integration (CI). Every push gets automatically linted, type-checked, tested, built into the image (Step 16), scanned, and pushed (Step 17). We'll build the LMS's GitHub Actions pipeline and see why the pure-domain architecture from Part I makes the test pyramid fast and cheap.*
