# Step 28 — Finale: The Life of One Code Change

*Series: Designing a Library Management System with DDD · Chapter 28 — Part II finale*

---

We've built the whole path to production piece by piece. This finale makes it *one motion*: we follow a single change — *raise the LMS late fine from ₹5 to ₹6* — through **every** stage of Part II, then step back for a retrospective and the teaching notes to run this as a course.

---

## 28.1 The life of one code change (end-to-end)

```
 1.  Dev edits FINE_RATE config + a domain test; opens a Pull Request.            (Step 14, 19)
 2.  CI runs: ruff → mypy → pytest. The pure-domain fine test catches a
       mistake → fix → green. Then build image, Trivy-scan, cosign-sign, push
       ghcr.io/org/lms:sha-9f8c2a1 to the registry.                              (Step 16,17,19,26)
 3.  PR reviewed & merged to main.                                               (Step 19)
 4.  A bot bumps the image tag in the GitOps config repo (staging overlay).      (Step 20,22)
 5.  ArgoCD sees the commit → runs the migration Job (PreSync) → rolls out
       to STAGING. Readiness probes pass; smoke + integration tests green.       (Step 18,20,21,22)
 6.  Manual approval gate → a PR promotes the SAME tag into the prod overlay.    (Step 22)
 7.  ArgoCD applies to PROD as a CANARY: 5% of borrow/return traffic → v2.       (Step 23)
 8.  Prometheus/Grafana: error rate & latency steady; fines now compute at ₹6;
       business metric "fines assessed" healthy; SLO intact.                     (Step 25)
 9.  Argo Rollouts auto-widens 5% → 25% → 50% → 100%; old ReplicaSet kept at 0
       for instant rollback.                                                     (Step 23)
 10. Had any SLO breached, Alertmanager pages on-call; rollback = shift traffic
       back / `kubectl rollout undo` / `git revert` — seconds.                   (Step 23,25,27)
 11. Members now pay ₹6/day late — and every hop is traceable to commit 9f8c2a1
       via the SHA tag, the trace IDs, and the git history.                      (Step 17,20,25)
```

One config change rode the entire machine — **and every Part-0/13 promise was kept**: available (canary, no downtime), correct (immutable artifact + safe migration), survives-change (instant rollback armed), observable (metrics gated the rollout), secure (scanned + signed + secrets managed).

---

## 28.2 The complete pipeline (one diagram)

```
        ┌── DEV ──┐   ┌──────────── CI (Step 19) ───────────┐   ┌── REGISTRY ──┐
 code → │ 12-factor│ → │ lint→type→test→build→scan→sign→push │ → │ sha-tagged   │
        │ (Step14) │   └─────────────────────────────────────┘   │ image (17)   │
        └──────────┘                                              └──────┬───────┘
                                                                         │ CI bumps tag
                                                          ┌──────────────▼───────────────┐
                                                          │  GitOps config repo (Step 20) │
                                                          │   envs/staging  envs/prod     │
                                                          └──────────────┬────────────────┘
                                                                 ArgoCD reconciles
                            ┌────────────────────────────────────────────▼─────────────────────┐
                            │  KUBERNETES (Step 21)  — migrate Job → rolling/canary (Step 23)    │
                            │  Deployment · Service · Ingress(TLS,24) · HPA · probes · NetworkPol │
                            └───────────────────────────────┬───────────────────────────────────┘
                                user → DNS → LB → Ingress → Service → Pods (Step 24)
                            ┌───────────────────────────────▼───────────────────────────────────┐
                            │  OBSERVE (25): logs+metrics+traces · SLOs · alerts                  │
                            │  SECURE (26) & OPERATE (27): RBAC/NetPol · backups · on-call · DR   │
                            └────────────────────────────────────────────────────────────────────┘
                                              feedback / rollback ↺
```

---

## 28.3 Retrospective: decision → promise served

Part II's heart in one table — *why*, not just *what*:

| Decision | Promise served | Step |
|---|---|---|
| 12-Factor: config from env, stateless | Correct, Survives-failure | 14 |
| Liveness ≠ readiness probes | Available (no restart-loops) | 14, 21 |
| Immutable, SHA-tagged image; never `:latest` | Correct (traceable, reproducible) | 16, 17 |
| Multi-stage, non-root, scanned image | Secure | 16, 26 |
| Backwards-compatible (expand/contract) migrations | Available (zero-downtime) | 18 |
| Migrations as a pre-deploy Job, not at startup | Survives-failure (no fleet crash-loop) | 18 |
| CI quality gate on every PR | Correct | 19 |
| GitOps: git = source of truth | Correct, Observable (audit log) | 20 |
| Deploy = commit, rollback = revert | Survives-change | 20, 23 |
| Same image promoted through environments | Correct (staging predicts prod) | 22 |
| Canary + feature flags | Survives-change (tiny blast radius) | 23 |
| Fast rollback as the master capability | Survives-change | 23 |
| Stateless app → horizontal autoscaling | Available | 24 |
| Pooler + caching for the DB bottleneck | Available (DB survives scale) | 24 |
| Three pillars + SLOs + symptom alerts | Observable, Available | 25 |
| Shift-left + defense-in-depth security | Secure | 26 |
| Tested backups, DR drills, blameless post-mortems | Survives-failure | 27 |

## 28.4 Where each tool lives (the stack map)

- **App:** FastAPI · Gunicorn/Uvicorn · pydantic-settings · structlog · Alembic
- **Package:** Docker (multi-stage) · GHCR/ECR (registry) · cosign (signing) · Trivy (scan)
- **CI:** GitHub Actions · ruff · mypy · pytest · pip-audit · bandit
- **CD:** ArgoCD/Flux (GitOps) · Helm/Kustomize (templating) · Argo Rollouts (canary)
- **Run:** Kubernetes · cert-manager (TLS) · HPA + cluster autoscaler · PgBouncer
- **Observe:** Prometheus · Grafana · Loki · OpenTelemetry · Jaeger/Tempo · Alertmanager
- **Operate:** Vault/Sealed-Secrets · OPA-Gatekeeper/Kyverno · PagerDuty · backup tooling

*(Reminder: at the LMS's actual scale, a **PaaS** does most of this for you. We used the explicit stack to make every concept visible — Step 15's punchline.)*

---

## 28.5 Teaching notes (running this as a course)

### Module sequence (with a lab each)

1. **Mental model + 12-Factor** (13–14) → lab: make the LMS 12-factor (env config, health checks).
2. **Docker** (16) → lab: write the Dockerfile, run with Compose + Postgres.
3. **Registry & CI** (17, 19) → lab: a pipeline that tests, builds, tags, pushes.
4. **Survey + the PaaS fast path** (15) → lab: ship the LMS to Render/Fly in 15 min *before* the hard path.
5. **Kubernetes** (21) → labs: manifests → probes → rolling update → HPA → ingress+TLS.
6. **DB & migrations** (18) → lab: an expand/contract migration with a rolling deploy.
7. **CD/GitOps** (20, 22) → lab: ArgoCD watching a config repo; promote staging→prod.
8. **Release strategies** (23) → lab: run a canary; force a rollback.
9. **Observability** (25) → lab: add metrics + a Grafana dashboard + one symptom alert.
10. **Security & Day 2** (26, 27) → lab: scan + sign an image; add a NetworkPolicy; write a runbook; test a restore.

### The pitfalls to call out explicitly

- **Deploying `:latest`** → untraceable, no rollback. Tag by SHA.
- **Liveness probe that checks the database** → a DB blip restart-loops the whole fleet.
- **Destructive migration in the same release as the code** → breaks old pods mid-rollout.
- **A stateful app** (local files/sessions) → can't scale horizontally.
- **Secrets in the image or git** → the classic breach.
- **Adopting Kubernetes for one small app** → the deployment-side "microservices for 100 members."
- **Alerting on causes, not symptoms** → alert fatigue → missed real incidents.
- **An untested backup** → not a backup.

### The exam-style throughline questions

- *For any tool: which of the six promises does it keep?* (Step 13's lens)
- *What's the difference between deploy and release?* (Step 13, 23)
- *Why must migrations be backwards-compatible?* (Step 18)
- *Liveness vs readiness — and what breaks if you confuse them?* (Step 21)
- *Why is the database the bottleneck when the app scales fine?* (Step 24)

---

## 28.6 The throughline — Part I and Part II are one discipline

> **Good *design* (Part I) and good *delivery* (Part II) are the same discipline at two altitudes: isolate what changes, behind stable boundaries.**
>
> - Part I put **persistence behind a repository interface** and **policy behind a strategy** — so the database and the fine-rate could change without touching the core.
> - Part II put **storage behind a container**, **config behind the environment**, **the database choice behind the composition root**, and **distro/platform behind adapters** — so *where and how* it runs could change without touching the code.
>
> Both halves are the same move: **find what varies, wrap it in a boundary, and keep the core stable.** And both halves end on the same judgment — **match the solution to the scale.** A 100-member library needs one bounded context (not microservices) *and* a PaaS (not a Kubernetes fleet). The senior skill, in design and in delivery alike, is knowing what to leave out.

And the goal of all of it:

> **Boring is the target.** A change should flow from a developer's keyboard to a member paying ₹6 — tested, scanned, signed, canaried, observed, and instantly reversible — without anyone holding their breath. *Excitement in production is a synonym for an outage.*

---

## Promises served

| Promise | How the finale tied it together |
|---|---|
| **All six** | The end-to-end trace showed every promise kept by a *combination* of stages — that's defense in depth for delivery. |

## Key takeaways

1. **One change touches every stage** — and each stage keeps a specific promise; production reliability is the *composition* of all of them.
2. **Traceability is the connective tissue** — the SHA tag, trace IDs, and git history make any running behavior explainable back to a commit.
3. **The whole pipeline exists to make change boring and reversible** — small, tested, observable, instantly rolled back.
4. **Match delivery to scale** — the explicit K8s stack is the teaching tool; a PaaS is the right answer for this app.
5. **Design and delivery are one discipline:** isolate what varies behind boundaries, keep the core stable, and leave out what the scale doesn't need.

---

## Series complete 🎉

**Part I (Steps 1–12):** designed the LMS with DDD — from ubiquitous language to a running, persistence-ignorant domain.
**Part II (Steps 13–28):** delivered it to production — from a 12-factor app to a canaried, observed, operable system — with an [appendix](appendix-on-prem-multi-distro-delivery.md) for the on-prem multi-distro case.

The app you *designed* is the app you *shipped*. Clean architecture and clean delivery turned out to be the same idea, applied twice. **Go build — and ship — something.**
