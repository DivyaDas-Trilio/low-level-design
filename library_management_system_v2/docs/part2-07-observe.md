# Part II — OBSERVE: knowing what production is doing

*Library Management System · Part II, stage 6 of six (CODE → BUILD → TEST → PACKAGE → DEPLOY →
**OBSERVE**). The last stage — and the one that loops back: what we observe here is what DEPLOY
reads to promote or roll back.*

---

DEPLOY got a new version running. OBSERVE answers the only question that matters next: *is it
actually healthy for real users, and how do we know before they tell us?* The LMS already emits the
raw material — **structured JSON logs to stdout** via `logging_setup.py` (`{"event":"app.startup",...}`),
plus `/healthz` and `/readyz` probes and env-driven config. What's missing is the other two pillars
(metrics, traces) and the *judgement layer* on top: SLOs, alerts, and the feedback wire back into
the pipeline. This stage builds that.

---

## 1. The three pillars

Observability is conventionally split into three signal types. They answer **different** questions;
you need all three, and confusing them is a classic anti-pattern (e.g. trying to compute a
request-rate metric by grepping logs).

| Pillar | Shape | Answers | LMS today |
|---|---|---|---|
| **Logs** | Discrete, timestamped events (structured JSON) | *What exactly happened on this one request/error?* | ✅ JSON to stdout via `logging_setup.py`, captured by the platform |
| **Metrics** | Numeric time-series, aggregated | *How is the system behaving in aggregate — rate, errors, latency, saturation?* | ⏳ next step: RED metrics |
| **Traces** | One request stitched across services/spans | *Where did the time go / where did it fail in a multi-hop request?* | ⏳ next step: OpenTelemetry spans |

**Logs** are what the LMS already does right: structured (JSON, not free text), to **stdout** (not
files — the app never manages log rotation), and the platform ships them off-box. Structured means
you can query `event="loan.overdue"` instead of regexing a string.

**Metrics** are cheap, aggregated, and the backbone of alerting. Two standard framings:
- **RED** (for request-driven services like the LMS): **R**ate (requests/sec), **E**rrors (failed/sec),
  **D**uration (latency distribution). This is the natural next instrumentation step for the API.
- **USE** (for resources): **U**tilization, **S**aturation, **E**rrors — CPU, memory, DB connections.

**Traces** matter the moment a request fans out (API → domain service → DB → notification). A trace
carries a request-scoped ID across every hop so you can see *which* span was slow. For a single-service
LMS the payoff is smaller today, but instrumenting now is what makes it free when a second service
appears.

🎯 **Interview flag — "the three pillars."** Near-guaranteed in any SRE/infra interview. The strong
answer isn't just naming them — it's stating *what each answers and when it's the right tool*: metrics
tell you **something is wrong** (aggregate, alertable), traces tell you **where** (which hop), logs
tell you **exactly what** (the specific event/stack trace). Rate → localize → root-cause.

---

## 2. Tooling — instrument once, wire to a backend

The winning move is to **decouple instrumentation from the backend**. Instrument the app with
**OpenTelemetry (OTel)** — the vendor-neutral, CNCF standard — and you can point the same telemetry
at Prometheus, Jaeger, CloudWatch, or Datadog by changing a collector config, not code. This is the
"build once, deploy many" principle (BUILD stage) applied to observability.

**On Kubernetes (self-managed, open-source):**
| Signal | Tool | How |
|---|---|---|
| Metrics | **Prometheus** + **Grafana** | Prometheus scrapes a `/metrics` endpoint; Grafana dashboards it |
| Logs | **Loki** or **ELK** (Elasticsearch/Kibana) | **Fluent Bit** tails stdout → ships to the store |
| Traces | **OpenTelemetry** → **Jaeger** or **Tempo** | App emits spans via OTel SDK → collector → trace store |

**On AWS (managed):**
- **CloudWatch** — logs *and* metrics in one service (Container Insights auto-collects from ECS/EKS).
- **X-Ray** — distributed tracing.
- Still instrument with **OTel**: the OTel Collector exports straight to CloudWatch/X-Ray, so you
  keep portability.

**Managed all-in-one** — **Datadog**, **Grafana Cloud**, New Relic, Honeycomb: one agent, all three
pillars, no infra to run. You pay per host/GB instead of operating Prometheus/Loki yourself. For a
small team this is often the right trade — buy the platform, spend the saved ops time on the product.

> **What to opt for:** **Prometheus + Grafana + OpenTelemetry** on self-managed Kubernetes;
> **CloudWatch + X-Ray** (or **Datadog**) when you're AWS-native or want managed. Regardless of
> backend, **instrument the app with OpenTelemetry** — it's the one decision that keeps you from
> being locked to a vendor. For the LMS specifically: add a Prometheus `/metrics` endpoint (RED)
> next, then OTel spans.

---

## 3. SLIs / SLOs / error budgets — the judgement layer

Raw signals don't tell you whether to page someone at 3am. You need **targets**.

- **SLI (Service Level Indicator)** — a *measured* number that reflects user experience. For the LMS:
  **request error rate** (`5xx / total`) and **latency** (p95 / p99 of `/loans`, `/return`).
- **SLO (Service Level Objective)** — the *target* for an SLI. E.g. "99.9% of requests succeed" and
  "p99 latency < 300ms, measured over 30 days."
- **Error budget** — the inverse of the SLO. 99.9% availability = **0.1% allowed failure** ≈ 43 min/month.
  As long as you're under budget, ship features fast. Burn the budget → freeze risky releases and
  spend effort on reliability. It turns "how reliable?" from an argument into a number.

**Alert on symptoms, not causes.** Page on things the *user feels* — error-rate up, latency up, SLO
budget burning fast — **not** on internal causes like "CPU at 80%" or "a pod restarted." High CPU
that hurts nobody is noise; paging on it trains engineers to ignore alerts (alert fatigue). Cause
metrics belong on **dashboards for debugging**, not in the pager.

**Paging path:** the metrics backend evaluates alert rules → **Alertmanager** (Prometheus) or
**CloudWatch Alarms** (AWS) fires → routes to **PagerDuty** / Opsgenie for on-call escalation.

🎯 **Interview flag — SLI/SLO/error budget + "alert on symptoms not causes."** Two of the most-tested
SRE concepts. Be ready to (1) define an SLI/SLO for a given service off the top of your head — for a
web API it's almost always **availability + latency percentile** — and (2) explain *why* symptom-based
alerting beats cause-based: it maps directly to user pain, cuts false pages, and error budgets give an
objective, non-emotional trigger for the "ship vs. stabilize" decision.

---

## 4. The feedback loop — OBSERVE drives DEPLOY

This is what closes the pipeline into a loop rather than a line. **Progressive delivery** (canary /
blue-green from the DEPLOY stage) is only safe *because* OBSERVE gives it a signal to judge against.

The mechanism — **automated canary analysis**:
1. DEPLOY sends a small slice of traffic (say 10%) to the new version.
2. A controller — **Argo Rollouts**, **Flagger**, or **AWS CodeDeploy** — queries the **metrics**
   from §1–2 (error rate, p99 latency) for the canary vs. the stable version.
3. Canary healthy against the SLI thresholds → **auto-promote** (shift more traffic, then 100%).
   Canary breaching thresholds → **auto-rollback** to the previous good version — no human in the loop.

So the OBSERVE signals aren't just for dashboards and 3am pages; they are the **decision input** that
makes a release self-driving. A bad deploy is caught and reverted in minutes by a machine reading the
same RED metrics an engineer would have eyeballed.

🎯 **Interview flag — "how does observability power progressive delivery?"** The senior answer draws
the full loop: *you can't safely do canary/auto-rollback without good SLIs, because the rollout
controller's promote/abort decision is literally a query against your metrics.* This ties OBSERVE back
to DEPLOY and shows you see the pipeline as a **closed feedback loop**, not six independent stages.

---

## 5. The two-cloud lens — OBSERVE

| Concern | Private cloud (Kubernetes) | Public cloud (AWS) |
|---|---|---|
| **Metrics** | Prometheus + Grafana | CloudWatch Metrics (Container Insights) |
| **Logs** | Loki / ELK via **Fluent Bit** (tails stdout) | CloudWatch Logs |
| **Traces** | **OpenTelemetry** → Jaeger / Tempo | AWS X-Ray (OTel-compatible) |
| **Dashboards** | Grafana | CloudWatch Dashboards |
| **Alerting** | Alertmanager → **PagerDuty** | CloudWatch Alarms → **PagerDuty** |
| **Canary analysis** | Argo Rollouts / Flagger reading Prometheus | CodeDeploy reading CloudWatch |

The split is the same pattern as every other stage: **self-managed open-source stack vs. managed
cloud service**. And the same escape hatch applies — instrument with **OpenTelemetry** and the app
code is identical across both columns; only the collector export target changes. That portability is
the whole reason to prefer OTel over a vendor SDK.

> **What to opt for:** **Prometheus/Grafana + OpenTelemetry** on Kubernetes; **CloudWatch/X-Ray or
> Datadog** on AWS. Whichever backend: **instrument with OpenTelemetry for portability**, **define
> SLOs and alert on symptoms** (user-facing latency/errors, not CPU), and **wire canary auto-rollback
> to the real metrics** so a bad deploy reverts itself.

---

## Key takeaways

1. **Three pillars, three questions.** Metrics say *something is wrong* (aggregate, alertable), traces
   say *where* (which hop), logs say *exactly what* (the event). The LMS already nails logs (structured
   JSON to stdout); RED metrics + OTel traces are the next step.
2. **Instrument with OpenTelemetry.** It decouples instrumentation from backend — the same code feeds
   Prometheus/Jaeger or CloudWatch/X-Ray or Datadog. Vendor lock-in avoided by one decision.
3. **SLIs → SLOs → error budgets** turn "reliable enough?" into a number, and gate the ship-vs-stabilize
   call objectively.
4. **Alert on symptoms, not causes** — page on user-facing error rate and latency; keep CPU/restart
   metrics on debugging dashboards. This is how you avoid alert fatigue.
5. **OBSERVE closes the loop into DEPLOY.** Canary controllers (Argo Rollouts / Flagger / CodeDeploy)
   read these metrics to auto-promote or auto-rollback — observability is what makes progressive
   delivery safe and self-driving.

---

*Next — `part2-08-scenarios-and-decisions`: putting the six stages together — end-to-end scenarios and
the decision tree for choosing tools and trade-offs across the whole pipeline.*
