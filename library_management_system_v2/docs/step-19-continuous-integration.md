# Step 19 — Continuous Integration (CI)

*Series: Designing a Library Management System with DDD · Chapter 19 — Part II*

---

We can build an image (Step 16) and push it to a registry (Step 17). But *who* decides a change is good enough to build and push? That's **Continuous Integration**: an automated gate that runs on **every push and pull request** — linting, type-checking, testing, building, scanning — and blocks anything that fails from ever reaching production. CI is where quality stops being a hope and becomes a *gate*.

> **The core idea of CI:** integrate small changes *frequently*, and have a machine *prove* each one is safe before it merges. The opposite — long-lived branches merged rarely after manual testing — is where "integration hell" and "works on my machine" live.

---

## 19.1 What CI actually does

On every push/PR, an automated runner executes the early stages of the universal pipeline (Step 13): **BUILD → TEST → PACKAGE**, plus quality and security gates. If *any* gate fails, the pipeline goes red and the change cannot merge.

```
 push / PR ─► checkout ─► install deps ─► LINT ─► TYPE-CHECK ─► TEST ─► BUILD image ─► SCAN ─► PUSH
                                          (ruff)   (mypy)     (pytest)  (Step 16)   (Trivy) (Step 17)
                          └─────────────── any red = blocked from merging ───────────────┘
```

Two ideas make CI valuable:

- **Fast feedback.** A developer learns within minutes that they broke something, while the change is fresh in their head — not days later in staging.
- **Fail fast, fail early.** Cheap checks (lint) run before expensive ones (image build, e2e), so most failures surface in seconds.

---

## 19.2 The test pyramid (and why Part I makes it cheap)

Not all tests are equal. The **test pyramid** says: *many* fast cheap tests at the bottom, *few* slow expensive ones at the top.

```
            ▲  fewer, slower, more realistic, more brittle
         /e2e\        End-to-end: whole system in a test env (a handful)
        /------\
       /contract\     API/contract: hit FastAPI endpoints (some)
      /----------\
     /integration \   App service + real test DB / repos (more)
    /--------------\
   /   unit tests   \ Pure domain: Money, Loan, BorrowingService (MANY, milliseconds)
  ▼------------------  more, faster, cheaper, more stable
```

**Here is where Part I pays a delivery dividend.** Because the domain is *pure* (zero framework imports — Steps 8–9), the bottom of the pyramid is enormous and runs in milliseconds with no infrastructure:

```python
# tests/domain/test_borrowing.py — no DB, no FastAPI, no mocks of frameworks
def test_member_at_limit_cannot_borrow():
    svc = BorrowingService(max_active_loans=2)
    member = Member(MemberId.new(), "Asha", "asha@x.com")
    copy   = BookCopy(CopyId.new(), BookId.new())          # AVAILABLE
    with pytest.raises(BorrowingLimitExceededError):
        svc.check_can_borrow(member, copy, active_loan_count=2)   # already at 2

def test_fine_is_five_rupees_per_day_late():
    assert StandardFineStrategy().calculate(days_overdue=3) == Money.rupees(15)
```

Those tests need *nothing* — no database, no HTTP, no mocking framework. That's the **testability** payoff promised back in Steps 8–9 made concrete: a clean architecture isn't just elegant, it makes the CI pyramid fast and cheap, which makes CI *fast*, which makes developers *run it*.

And the **typed IDs** (Step 8a) pay off in the type-check stage: `mypy` catches a `BookId` passed where a `MemberId` belongs — a whole bug class caught before a test even runs.

The upper layers need a little infrastructure — an **integration test** runs the app service against a real throwaway Postgres (a CI "service container"):

```python
# tests/integration/test_borrow_flow.py
def test_borrow_then_return_late_creates_fine(library_service):   # wired to a test Postgres
    member_id = seed_member(library_service)
    copy_id   = seed_copy(library_service)
    loan_id   = library_service.borrow_book(member_id, copy_id)
    fine_id   = library_service.return_book(loan_id, on_date=due_plus(2))
    assert fine_id is not None        # 2 days late → a fine exists
```

---

## 19.3 The LMS CI pipeline (GitHub Actions)

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]

jobs:
  quality-and-test:
    runs-on: ubuntu-latest
    services:                                  # a throwaway Postgres for integration tests
      postgres:
        image: postgres:16
        env: { POSTGRES_USER: lms, POSTGRES_PASSWORD: test, POSTGRES_DB: lms_test }
        ports: ["5432:5432"]
        options: >-
          --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12", cache: "pip" }   # cache deps → faster runs
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: ruff check src/                    # 1. lint        (fastest — fail first)
      - run: mypy src/                          # 2. type-check  (typed IDs shine here)
      - run: pytest --cov=src --cov-fail-under=85   # 3. unit + integration tests
        env: { DATABASE_URL: "postgresql://lms:test@localhost:5432/lms_test" }

  build-scan-push:
    needs: quality-and-test                     # ONLY if all gates pass
    if: github.ref == 'refs/heads/main'         # build artifacts only on main
    runs-on: ubuntu-latest
    permissions: { contents: read, packages: write }
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with: { registry: ghcr.io, username: ${{ github.actor }}, password: ${{ secrets.GITHUB_TOKEN }} }
      - uses: docker/build-push-action@v6
        with:
          push: true
          tags: ghcr.io/${{ github.repository }}:sha-${{ github.sha }}   # immutable SHA tag (Step 17)
          cache-from: type=gha                  # reuse Docker layer cache across runs
          cache-to: type=gha,mode=max
      - name: Scan image for CVEs
        uses: aquasecurity/trivy-action@master
        with: { image-ref: "ghcr.io/${{ github.repository }}:sha-${{ github.sha }}", exit-code: "1", severity: "HIGH,CRITICAL" }
```

Note the ordering — **lint → type-check → test → build → scan → push** — cheapest first, so failures surface in seconds; the image (the expensive artifact) is built and pushed **only on `main`, only after every gate is green**.

---

## 19.4 The practices that make CI work

- **Branch protection / required checks.** Configure the repo so a PR **cannot merge** unless CI is green. The gate is only real if it's *enforced* — otherwise it's a suggestion.
- **Trunk-based development.** Small, frequent merges to `main` behind short-lived branches keep integrations tiny and conflicts rare. (The alternative, long-lived feature branches à la heavy GitFlow, defers integration pain until it's huge.)
- **Speed is a feature.** Cache dependencies and Docker layers (shown above). A slow CI gets bypassed or ignored; a fast one gets trusted. Aim for minutes, not tens of minutes.
- **Reproducibility.** Pinned dependencies (Step 14) + a fixed runner image mean CI tests the *same* thing every time. Flaky, environment-dependent tests erode trust in the whole gate.
- **Coverage as a guardrail, not a religion.** `--cov-fail-under=85` prevents coverage from silently rotting; chasing 100% is usually waste.
- **CI builds the artifact CD ships.** The image CI pushes (SHA-tagged) is the *exact* one promoted through environments (Step 20) — "build once, deploy many" starts here.

---

## Promises served

| Promise | How this chapter advanced it |
|---|---|
| **Correct** | Automated lint/type/test gates prove each change before it can merge — quality becomes a gate, not a hope. |
| **Survives change** | Fast, trustworthy tests let you change confidently and frequently (trunk-based), shrinking risky big-bang merges. |
| **Secure** | Image CVE scanning (Trivy) + dependency checks block known-vulnerable artifacts at the gate. |
| **(Velocity)** | Fast feedback + caching keep the pipeline quick, so the team actually relies on it. |

## Key takeaways (the transferable lessons)

1. **CI is an enforced quality gate on every change** — integrate small and often, and let a machine prove each change is safe before merge.
2. **The test pyramid:** many fast unit tests, few slow e2e tests. **Part I's pure domain makes the base huge and instant** — clean architecture *is* fast CI.
3. **Order checks cheapest-first** (lint → type → test → build → scan) so failures surface in seconds; build the image only on `main`, only when green.
4. **Enforce the gate** with branch protection — an unenforced check is just advice.
5. **CI produces the immutable artifact** (SHA-tagged image) that the rest of the pipeline promotes — this is where "build once" begins.

---

*Next — Step 20: Continuous Delivery & GitOps. CI produced a tested, scanned, tagged image; CD gets it *running*. We'll contrast push-based deploys with the modern **GitOps** model (Git as the single source of truth, an in-cluster agent like ArgoCD reconciling the cluster to match) and see how a deploy becomes a git commit — and a rollback a git revert.*
