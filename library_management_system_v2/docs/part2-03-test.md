# Part II — TEST: The Quality Gate

*Library Management System · Part II, stage 3 of the pipeline CODE → BUILD → TEST → PACKAGE →
DEPLOY → OBSERVE. This is the gate every change must pass before it's allowed to become an
artifact.*

---

TEST is not "we have some tests." It's the **automated gate** that decides whether a change is
allowed to move on to PACKAGE. Everything here answers one question: *what must be true before we
trust this commit enough to build an immutable image from it and ship it?* Two forces shape the
answer — **cost** (fast feedback keeps developers merging) and **confidence** (catch the bug on
the branch, not in prod). The whole discipline is buying the most confidence per second of gate
time.

---

## 1. The test pyramid — shape follows cost

The pyramid is a **cost/speed model**, not a religion. Tests at the bottom are cheap, fast, and
numerous; the ones at the top are slow, brittle, and few. You want most of your confidence coming
from the cheap layer.

```
        ╱ e2e / API ╲          few · slow · brittle · real HTTP
      ╱───────────────╲
    ╱   contract (Pact) ╲      few · pin cross-service shapes
  ╱───────────────────────╲
 ╱  integration (services)  ╲  some · app svc over repos
╱─────────────────────────────╲
     unit (pure domain)         MANY · ms · no I/O · no mocks
```

| Layer | What it tests in the LMS | Speed | Deps |
|---|---|---|---|
| **Unit** | `Money`, `ISBN`, `DueDate`, `Loan` invariants — pure domain | microseconds | none |
| **Integration** | application services (issue-copy, return-copy, assess-fine) over in-memory repos | milliseconds | wiring |
| **Contract** | Pact between a service and its consumers, *if* they deploy independently | fast | pact broker |
| **e2e / API** | FastAPI routes end-to-end over HTTP (`httpx`/TestClient) | seconds | full app |

**Why the LMS base is trivially cheap.** The domain layer was built with **zero framework
imports** — entities and value objects are plain Python. That's the payoff arriving now: you test
a `Loan` returning after 6 days and assert a ₹5-late fine with a **direct function call and an
assert** — no database, no HTTP, no mocks, no fixtures. Fast, deterministic, and there's nothing
to stub because the domain has no I/O. **That wide, no-mock base IS the cheap gate** — the reason
you can afford to run it on every push.

**Integration sits one layer up.** Application services orchestrate across aggregates (borrow-cap
of 2, hide lost/damaged copies from members). Those you test against the **in-memory repos** the
app already ships — same interface as a real DB, no I/O cost. The four vertical slices —
**catalog, membership, lending, fines** — each get a thin integration band; lending gets the most,
because it's the core subdomain where the invariants live.

**Contract tests** only earn their place once a piece deploys on its own schedule (an extracted
notifications service, say). For today's modular monolith they'd be pure ceremony — **YAGNI**.
Named here so you know the layer exists and *when* it turns on.

> **What to opt for:** invest lavishly in the unit base where the domain is pure (it's nearly free
> and catches the most bugs per second), a **thin** integration band over in-memory repos, and a
> **handful** of e2e tests for the critical user journeys only (issue → return → fine). Resist
> the "ice-cream cone" — a top-heavy suite of slow, flaky e2e tests is the most common and most
> expensive test-strategy mistake.

🎯 **Interview flag — the pyramid + where validation lives.** Be ready to draw the pyramid *and*
tie it to Part I's validation split: **syntactic/shape validation lives at the API edge**
(Pydantic rejects a malformed ISBN string, a negative quantity, a missing field — a *400*), while
**semantic/business-rule validation lives in the domain** (borrow-cap of 2, no-renewals, 5-day
due window — a *422/409*). This tells you *what to test where*: shape rules → fast API/unit tests
at the edge; business invariants → pure-domain unit tests at the base. Conflating the two (putting
business rules in the controller, or shape-checks deep in the domain) is exactly the design smell
interviewers probe for.

---

## 2. Static & security gates — shift left

Not every gate runs code. The cheapest defect is the one caught **before** a test even executes.
These run in parallel with the pyramid and block the same merge.

| Gate | Purpose | Tools |
|---|---|---|
| **Lint** | style, dead code, obvious smells | `ruff`, `flake8` |
| **Type-check** | catch type errors statically (a poor-man's proof) | `mypy`, `pyright` |
| **Format** | no bikeshedding in review | `black`, `ruff format` |
| **SAST** | scan *our* source for vuln patterns (injection, secrets) | CodeQL, SonarQube, Bandit |
| **Dependency scan** | known CVEs in *libraries* we pull | Snyk, Dependabot, `pip-audit` |
| **Image scan** | CVEs in the OS/base layers of the built image | Trivy, Grype |
| **Secret scan** | no keys/tokens committed | gitleaks, trufflehog |

**Shift-left / DevSecOps** is the whole idea: move security and quality checks *left* on the
timeline — into the PR, run by the developer's own pipeline — instead of a security team's audit
weeks later. A CVE flagged on the branch costs minutes; the same CVE found in prod costs an
incident. Type-checking earns special mention for the LMS: because the domain is pure typed
Python, `mypy` in `--strict` acts as a **free extra test layer** — many "did I pass paise or
rupees?" bugs never reach a unit test because the types don't line up.

🎯 **Interview flag — "shift security left."** Say the phrase and mean it: security is a
**pipeline gate**, not a release checklist. SAST scans *your code*, dependency/image scans scan
*what you didn't write* (the supply chain — the larger attack surface). Naming both halves —
first-party vs supply-chain — is what separates a real answer from a buzzword.

---

## 3. Merge gates — pre-submit vs post-submit

The single most important design choice in TEST: **which checks block a merge, and which run
after it.** Get this wrong and either bugs leak to `main` (too few pre-submit) or nobody can ship
(too many, too slow).

| | **Pre-submit** (blocks the merge) | **Post-submit** (runs after merge / nightly) |
|---|---|---|
| **Contains** | unit + integration + lint + type + fast scans | full e2e, load/perf, deep image scans, cross-browser |
| **Budget** | must be **fast** — target < ~10 min | can be slow — minutes to hours |
| **On failure** | red PR, merge blocked | alert + auto-revert / rollback the merge |
| **Why** | protect `main`; keep developers unblocked | catch what's too expensive to gate on every PR |

**The rule:** the merge path must stay fast, so gate it on the cheap-but-high-signal layers (unit
+ integration + scans) and push the slow, expensive e2e/load suites to **post-merge on `main`** or
a **nightly** run against staging. `main` must be **always shippable** — but "shippable" is
enforced by a fast gate plus a fast post-merge safety net, not by making every developer wait an
hour.

**Two operational realities that decide whether the gate is trusted:**

- **Flaky-test quarantine.** A test that passes and fails non-deterministically is *worse than no
  test* — it trains the team to ignore red. The moment a test flakes, **quarantine** it (move it
  out of the blocking set, file a ticket, fix or delete). A gate people routinely re-run "because
  it's probably flaky" has already stopped being a gate.
- **Sharding & parallelism.** Keep the wall-clock budget by splitting the suite across runners —
  `pytest-xdist` for local parallelism, CI matrix/sharding to fan tests across machines. Speed is
  a feature: a 30-minute gate gets bypassed, a 5-minute gate gets respected.

---

## 4. Two-cloud lens — running the gate

Same gate, different plumbing on a self-managed **Kubernetes** cluster versus **AWS**.

| Concern | Private cloud (Kubernetes) | Public cloud (AWS) |
|---|---|---|
| **CI runner** | Tekton / Argo Workflows / GitHub Actions runners in-cluster | CodeBuild |
| **SAST + scans** | CodeQL/Sonar + Trivy/Snyk (same tools, self-hosted) | same tools, in CodeBuild stages |
| **e2e environment** | ephemeral **namespace** per PR, torn down after | ephemeral ECS / preview env per PR |
| **Gating** | branch protection + required checks (GitHub) or Tekton pipeline result | CodePipeline stage approval / required checks |
| **Test data** | seeded in-namespace fixtures | seeded task/preview env |

The portable insight: the **tools are the same** (CodeQL, Trivy, pytest run identically) — only the
**runner and the ephemeral-environment mechanism** differ. On K8s you spin a throwaway *namespace*
per PR; on AWS you spin a throwaway *preview environment*. Either way the e2e suite runs against a
real, isolated, disposable copy of the app — never against staging or prod.

> **What to opt for:** gate merges on **unit + integration + static/security scans** — the fast,
> high-signal set — and keep that path under ~10 minutes. Push **slow e2e and load tests to
> post-merge or nightly** against an ephemeral environment. Use the same scanning tools on both
> clouds; let only the runner (Tekton/Argo/Actions vs CodeBuild) and the ephemeral-env mechanism
> (namespace vs preview env) vary.

---

## 5. Where the LMS is today — and the real gap

Honest status: the pure-domain design has made the **cheap base essentially free to build**, but
the **suite itself is thin** — `tests/domain/test_money.py` is a stub and `tests/domain/` isn't
even a package yet. That's the actual gap. The architecture already paid for a fast gate; the
tests to fill it are what's missing.

**The build-out order that follows the pyramid:**

1. **Unit, bottom-up** — value objects first (`Money`, `ISBN`, `DueDate`), then the `Loan`
   aggregate's invariants (5-day window, ₹5/day fine, borrow-cap). No mocks. This is the bulk.
2. **Integration** — application services over in-memory repos, one thin band per slice
   (catalog, membership, lending, fines), heaviest on lending.
3. **e2e** — a *handful* of FastAPI route tests for the golden path: issue a copy → return late →
   fine assessed.
4. **Static/security** — wire `ruff`, `mypy --strict`, and Trivy/pip-audit into the same CI job.
5. **Gate it** — mark 1, 2, 4 as required pre-submit checks; run 3 post-merge.

---

## Key takeaways

1. **The pyramid is a cost model** — most confidence from the cheap, fast, no-mock base; few slow
   e2e tests at the top. Avoid the top-heavy ice-cream cone.
2. **Pure domain = a free wide base.** Zero framework imports mean invariants test with a plain
   assert — the LMS's biggest testing advantage.
3. **Validation splits by layer** — shape/syntactic at the API edge (Pydantic → 400), semantic/
   business-rule in the domain (invariants → 422/409). That split tells you *what to test where*.
4. **Shift security left** — SAST (your code) + dependency/image scanning (supply chain) are
   pipeline gates, not a pre-release audit.
5. **Fast pre-submit, heavy post-submit** — gate merges on unit + integration + scans under
   ~10 min; push slow e2e/load to post-merge or nightly against ephemeral environments.
6. **Guard the gate's credibility** — quarantine flaky tests on sight; shard for speed. A gate
   people re-run or wait an hour for is no gate at all.
7. **The LMS's real gap is the suite, not the design** — the architecture bought a cheap gate;
   the tests to fill it are the outstanding work.

---

*Next — `part2-04-package`: the PACKAGE stage — turning a passing commit into one immutable,
SHA-tagged, signed container image that travels every environment unchanged.*
