# Step 25 — Observability

*Series: Designing a Library Management System with DDD · Chapter 25 — Part II*

---

The LMS is deployed, scaled, and serving traffic. Then at 2am a member can't return a book and a pager goes off. **Can you find out *what* broke and *why* — fast?** That capability is **observability**, and a system without it is a black box you operate by prayer. This chapter wires it into the LMS.

> **Monitoring vs. observability:** *monitoring* answers questions you knew to ask ("is CPU high?" — known-unknowns). *Observability* lets you ask questions you *didn't* anticipate ("why are *only Premium members in this region* getting fine errors since the last deploy?" — unknown-unknowns). Production breaks in ways you didn't predict, so you need the latter.

---

## 25.1 The three pillars

Observability stands on three complementary data types. You need all three — each answers a different question.

| Pillar | Answers | LMS example | Tooling |
|---|---|---|---|
| **Logs** | "What *happened* (this discrete event)?" | `BorrowingLimitExceededError for member X` | Loki / ELK / CloudWatch |
| **Metrics** | "How *much / how often* (aggregate trend)?" | borrow requests/sec, error rate, p95 latency | **Prometheus** + Grafana |
| **Traces** | "*Where* did this one request spend its time?" | borrow took 2s — 1.8s was the DB call | OpenTelemetry → Jaeger/Tempo |

The mental split: **metrics tell you *something* is wrong (and alert you); traces tell you *where*; logs tell you *why*.** A good debugging session flows metric → trace → log.

---

## 25.2 Logs — structured events (building on Step 14)

We already made logs **structured JSON to stdout** in Step 14. Observability is what you *do* with them: an agent (Fluent Bit) ships them to a store (Loki) where they're **queryable**.

```python
log.info("loan.returned", loan_id=str(loan.id), member_id=str(loan.member_id),
         days_overdue=days, fine_assessed=bool(fine_id), trace_id=current_trace_id())
```

Two rules that make logs actually useful:
- **Structured, not prose.** `{"event":"loan.returned","days_overdue":2}` is queryable; `"Loan 42 returned 2 days late"` is a graveyard.
- **Carry a correlation/trace ID** (`trace_id` above) so you can pivot from a log line to the *whole request's* trace — the glue between the three pillars.

---

## 25.3 Metrics — the numbers you alert on

The app exposes a `/metrics` endpoint; **Prometheus scrapes it** on a schedule; **Grafana** dashboards it; **Alertmanager** pages on it. For FastAPI it's nearly free:

```python
# one line adds request rate, error, and latency metrics + a /metrics endpoint
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)
```

And you add **domain-specific** metrics that matter to *the business*, not just infra:

```python
from prometheus_client import Counter
books_borrowed = Counter("lms_books_borrowed_total", "Books successfully borrowed")
fines_assessed = Counter("lms_fines_assessed_total", "Late fines assessed")
# ... books_borrowed.inc() in the borrow use case
```

**What to measure — two standard recipes:**
- **RED** (for request-driven services like the LMS API): **R**ate (requests/sec), **E**rrors (failures/sec), **D**uration (latency distribution). Track these per endpoint.
- **USE** (for resources like the DB/nodes): **U**tilization, **S**aturation, **E**rrors.

> Measure **business** signals too — "books borrowed per minute" dropping to zero is a louder, truer alarm than "CPU is fine." Infra-green-but-business-zero is a real and dangerous failure mode.

---

## 25.4 Traces — following one request across hops

A **trace** records the path of a *single* request through the system as nested **spans** (API → domain → DB), each timed. It's how you answer "*where* did those 2 seconds go?" OpenTelemetry instruments FastAPI:

```python
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
FastAPIInstrumentor.instrument_app(app)     # spans for HTTP requests
SQLAlchemyInstrumentor().instrument()       # spans for DB queries
```

```
 Trace: POST /loans/borrow            (total 2.1s)
 ├─ span: borrow_book use case        (2.0s)
 │   ├─ span: members.get             (0.1s)
 │   ├─ span: loans.count_active      (1.8s)   ← THE culprit (missing index?)
 │   └─ span: loan INSERT             (0.1s)
```

Traces turn "the borrow endpoint is slow" into "the `count_active` query is slow" in seconds — pointing you straight back to the index from Step 18.

---

## 25.5 SLIs, SLOs & error budgets — defining "good" as a number

You can't manage reliability you haven't quantified. Turn the LMS's **non-functional requirements** (Step 1: "100 members, 24/7 available") into numbers:

- **SLI** (Indicator) — a *measured* signal: *"% of borrow requests that succeed in < 300ms."*
- **SLO** (Objective) — the *target* for an SLI: *"99.9% of borrow requests succeed in < 300ms over 30 days."*
- **Error budget** — the allowed shortfall: 99.9% ⇒ **0.1%** may fail. That budget is something you **spend deliberately** — on risky deploys, experiments — and when it's exhausted, you *stop shipping features and fix reliability*.

> This is the bridge from Part I's NFRs to Part II's operations: the vague "24/7 available" becomes a measurable SLO with a budget that governs how aggressively you can change the system. SLOs make reliability a *negotiable, visible* quantity instead of an argument.

---

## 25.6 Alerting — page on symptoms, not causes

Metrics are only useful if they *wake the right person at the right time*. The cardinal rule:

> **Alert on symptoms users feel, not on internal causes.**

- ✅ **Page on:** error rate up, latency past the SLO, "books-borrowed/min dropped to zero," error budget burning fast. These mean *users are hurting.*
- ❌ **Don't page on:** "a pod restarted," "CPU 80%," "one node rebooted." If Kubernetes self-healed and users felt nothing, that's a *dashboard*, not a 2am page.

Why it matters: **alert fatigue** is a real outage cause. If people get paged for non-events, they start ignoring pages — and miss the real one. Every alert should be **actionable** and tied to **user impact**. Route them (Alertmanager → PagerDuty/Opsgenie) with severities; reserve paging for "humans must act now."

```yaml
# Prometheus alert — symptom-based, tied to the SLO
- alert: BorrowErrorRateHigh
  expr: rate(http_requests_total{path="/loans/borrow",status=~"5.."}[5m]) > 0.01
  for: 5m
  labels: { severity: page }
  annotations: { summary: "Borrow error rate > 1% for 5m — users can't borrow" }
```

---

## 25.7 Putting it together — a 2am debugging flow

```
 1. ALERT fires: "borrow error rate > 1%" (a METRIC crossed the SLO)        ← symptom
 2. Grafana dashboard: errors started at 02:14, right after deploy sha-9f8c2a1
 3. Open a TRACE of a failing borrow: the loans.count_active span errors
 4. Pivot via trace_id to the LOGS: "OperationalError: too many connections"  ← cause
 5. Fix: connection pool too large for the new replica count (Step 24) → roll back / tune
```

Metric → dashboard → trace → log → cause → rollback. **That** is observability earning its keep — and notice it leans on everything prior: the SHA tag (17) to identify the deploy, the trace/log correlation, the rollback (23), the pooling lesson (24).

---

## Promises served

| Promise | How this chapter advanced it |
|---|---|
| **Observable** | The whole chapter — logs (why), metrics (how much), traces (where) make the black box transparent. |
| **Available** | SLO-based alerting catches degradation early; symptom alerts mean you act on real user pain, fast. |
| **Survives change** | Metrics gate canary releases (Step 23) and reveal a bad deploy within minutes for rollback. |
| **Correct** | Business metrics (books borrowed/min) catch "infra green, product broken" failures monitoring misses. |

## Key takeaways (the transferable lessons)

1. **Observability > monitoring:** build the ability to ask questions you *didn't* foresee, because that's how production actually breaks.
2. **Three pillars, three jobs:** **metrics** say *something's* wrong, **traces** say *where*, **logs** say *why* — correlate them with a shared trace ID.
3. **Measure business signals, not just infra.** "Books borrowed/min → 0" is a truer alarm than "CPU is fine."
4. **Turn NFRs into SLOs with error budgets** — reliability becomes a measurable, spendable quantity that governs how fast you ship.
5. **Alert on user-felt symptoms, not internal causes.** Actionable, impact-based pages only — alert fatigue is itself an outage risk.

---

*Next — Step 26: Security across the pipeline (DevSecOps). Security isn't a final gate — it's woven through every stage we've built: dependency & image scanning, minimal/non-root containers, supply-chain signing & SBOMs, secret management, least-privilege RBAC and NetworkPolicies, and TLS/auth at the edge.*
