# CLAUDE.md — Library Management System (v2, DDD build)

A from-scratch Library Management System built as a **learning exercise in tactical DDD**. The
goal is not "a finished app" — it's to show the *thinking* that turns a vague requirements doc
into a clean design, applying DDD / OOP / SOLID / patterns **only where they earn their place**.

## Source of truth

- [`REQUIREMENTS.md`](REQUIREMENTS.md) — stakeholders, user stories, business rules, NFRs, and the
  roadmap/status table. **Check the roadmap table here before starting a step** — it tracks
  where we are.
- [`docs/`](docs/) — the written walkthrough, in two parts. **Part I (design, DDD):**
  `step-01`…`step-12`. **Part II (from code to production):** `part2-00`…`part2-08`, reorganized
  around the pipeline `CODE → BUILD → TEST → PACKAGE → DEPLOY → OBSERVE` — each stage doc covers
  the real ways to do it on a private Kubernetes cluster vs on AWS, and what to opt for. (Part II
  replaced the older 16-file `step-13`…`step-28` set, recoverable from git history.) Read the
  relevant doc before coding a step.

## Tech stack & commands

- Python **3.12+**. Domain layer is **pure Python — zero framework imports**.
- FastAPI + Pydantic for the API layer (thin); pytest for tests.
- `pythonpath = ["src"]`, `testpaths = ["tests"]` (see `pyproject.toml`).

```bash
pip install -e ".[dev]"   # install with dev deps (pytest)
pytest                    # run tests (imports resolve from src/)
```

## Architecture — layering

```
src/
├── domain/          # entities, value objects, aggregates, domain services — PURE, no frameworks
├── application/     # application services: orchestrate use cases across aggregates
├── infrastructure/  # repository implementations, persistence, external adapters
└── api/             # FastAPI controllers — thin; translate HTTP <-> application services
tests/
```

One **bounded context** (the *Library* context) — deliberately **not** microservices for this
scale (~100 members, ~500 books, one branch). Internally organized to mirror four subdomains:
- **Lending / Circulation** — *core*; lavish modeling effort here (aggregates, invariants, state, policies).
- **Catalog**, **Membership** — supporting; keep boringly simple (CRUD + queries).
- **Fines / Billing** — supporting; simple rules.
- **Notifications** — generic.

## Ubiquitous Language (use these exact words as class/method/module names)

- **Book** = the abstract work (title, author, ISBN, genre). One per title. You **never** issue a Book.
- **BookCopy** = a physical item with its own identity + status (available / loaned / lost / damaged).
  **Keystone rule: you issue a `BookCopy`, never a `Book`.** ("A book can have multiple copies.")
- **Member**, **Librarian** (actor), **Admin** (role).
- **Loan** (a.k.a. issue record) = a specific copy out to a specific member, with a due date. Core entity.
- **Fine** = money owed for a late return.
- Value objects: **ISBN**, **Money**, **DueDate**.

## Domain conventions

- **Value objects** are immutable: `@dataclass(frozen=True)`, validate in `__post_init__`.
- **Money is always stored in paise** (`int`), never floats. Use factory `Money.rupees(...)`.
- **References across aggregates are by ID**, never by object reference.
- **One repository per aggregate root**; the repository *interface* lives in `domain/`, the
  implementation in `infrastructure/` (persistence-ignorant ports).
- Patterns (Strategy / State / Factory / Observer) appear **only when a real problem demands them** —
  not preemptively. KISS / YAGNI win by default.

## Business rules (the invariants the model must protect)

- A book can have multiple copies.
- A loan must be returned within **5 days**; fine is **₹5/day** late.
- A member may borrow at most **2 copies** at a time.
- **No renewals.**
- Lost/damaged copies are **hidden from members** but visible to librarians.

## Build status / current position

- Design docs (steps 1–28): **complete prose.**
- Code: just started at step 8a. `src/domain/value_objects/money.py` (`Money` VO) exists.
  `tests/domain/test_money.py` is currently an empty stub (and lacks `tests/domain/__init__.py`).
- Only `REQUIREMENTS.md` is git-tracked so far; `src/`, `tests/`, `docs/`, `pyproject.toml` untracked.
