# Step 13 — The Path to Production: The Mental Model

*Series: Designing a Library Management System with DDD · Chapter 13 — **Part II: Delivery begins***

---

Steps 1–12 designed and built the system. It runs in pure Python on your laptop. But "it runs on my laptop" and "it reliably serves real users" are separated by a chasm — and that chasm is where most engineers have their biggest blind spots. **Part II of this series crosses it.** Same app, now taken all the way to production.

This first chapter installs the *mental model* — the vocabulary and the spine — that every later production chapter hangs off. No tools yet, exactly like Step 1 was no code yet. Get the model right and the tooling becomes obvious.

---

## 13.1 "Production" is a set of promises, not a place

The first thing to unlearn: students think "deploying" means "copying my code to a server." That's not production. **Production is a set of promises you make to users** — and *every* technique in Part II exists to keep one of them:

| Promise | Plain meaning | Kept by (later steps) |
|---|---|---|
| **Available** | Reachable almost always | redundancy, health checks, zero-downtime deploys |
| **Correct** | The right version, right config, right data | immutable artifacts, migrations, config management |
| **Survives change** | Ship new versions safely; undo bad ones fast | release strategies, rollback |
| **Survives failure** | A crash / dead machine / traffic spike doesn't take it down | orchestration, auto-healing, autoscaling |
| **Observable** | When it breaks, you can see *what* and *why* | logs, metrics, traces, alerting |
| **Secure** | Secrets safe, attack surface minimal | secret managers, scanning, least privilege |

> **The recurring question for the whole of Part II:** for every tool or step we introduce, ask *"which promise does this keep?"* If a technique doesn't serve one of these, it's ceremony. This is the delivery-side echo of the design series' *"which principle drove this decision?"*

---

## 13.2 The universal pipeline (every approach is a variation of this)

Whether you deploy by hand to one VM or run a 50-service Kubernetes fleet, **every change travels the same eight stages.** Memorize this spine — the rest of Part II is just *how* each stage is implemented:

```
  CODE → BUILD → TEST → PACKAGE → RELEASE → DEPLOY → RUN → OBSERVE
   │       │       │       │          │         │       │       │
 commit  install  unit/  produce a  choose    put the  serve   logs,
 to git  deps /   integ. versioned  the       artifact traffic metrics,
         compile  tests  artifact   version   on infra         traces
                                    to ship                       │
                                                          ┌───────┘
                                                  feedback / rollback
```

- **CODE** — a change committed to version control.
- **BUILD** — resolve dependencies, compile/assemble. For the LMS: `pip install` into an image.
- **TEST** — automated gates (the test pyramid, Step 19). Fail here and nothing ships.
- **PACKAGE** — produce *one* versioned, immutable artifact (a container image, Step 16).
- **RELEASE** — decide *which* artifact version is the one to ship.
- **DEPLOY** — place that artifact on infrastructure so it's running.
- **RUN** — it serves real traffic, kept alive and scaled.
- **OBSERVE** — watch it; feed problems back into a fix or a rollback.

Every production system you'll ever see is some concrete spelling of these eight words.

---

## 13.3 Two ideas that thread through everything

These two principles separate professional delivery from "copy files and pray." Internalize them now; we'll invoke them in nearly every later chapter.

### (a) Build once, deploy many

You build **one** immutable artifact and promote that *exact same* artifact through every environment: dev → staging → production.

```
   build ONE image  ──►  test it in staging  ──►  promote the SAME image to prod
   (never rebuild per environment)
```

You **never rebuild** per environment. Why? Because rebuilding means the thing you tested is not byte-for-byte the thing you shipped — and that gap is the birthplace of *"but it worked in staging!"* incidents. The artifact is frozen; **only configuration changes** between environments (the 12-Factor lesson, Step 14).

### (b) Deploy ≠ Release

This distinction is subtle and powerful:

- **Deploy** = the new code is *running* on infrastructure.
- **Release** = *users are actually being sent to it.*

Decoupling them is the foundation of safe shipping. You can **deploy** the new "renew a book" feature to production but **release** it to only staff, then 5% of members, then everyone — and switch it off instantly if fines start miscalculating. *Deploy is a mechanical act; release is a business decision.* Canary, blue-green, and feature flags (Step 23) are all machinery for separating the two.

> **Anchor to the LMS:** imagine raising the fine from ₹5 to ₹6. *Deploying* means the ₹6 code is live on the servers. *Releasing* means real members start being charged ₹6. You want to deploy it cautiously and release it gradually while watching the metrics — not flip a switch and hope.

---

## 13.4 Where Part II is going (the roadmap)

The same "survey the landscape, then go deep on one path" structure, anchored to the LMS:

| Step | Chapter | Theme |
|---|---|---|
| **13** | The mental model *(this one)* | Promises + the universal pipeline |
| 14 | Production-readiness (12-Factor) | Make the *app* deployable |
| 15 | Survey: the standard ways to run it | VM → PaaS → Docker → K8s → serverless + trade-offs |
| 16 | Containerizing the LMS | The Dockerfile |
| 17 | Registry & immutable tagging | The artifact store |
| 18 | Database & migrations | The stateful, scary part |
| 19 | Continuous Integration (CI) | The quality gate + test pyramid |
| 20 | Continuous Delivery & GitOps | Getting the artifact running |
| 21 | Kubernetes core + health probes | The orchestration deep-dive |
| 22 | Environments & promotion | dev → staging → prod |
| 23 | Release strategies | Rolling / blue-green / canary / flags |
| 24 | Networking, TLS, scaling & the DB reality | Traffic + the bottleneck |
| 25 | Observability | Logs, metrics, traces, SLOs |
| 26 | Security across the pipeline (DevSecOps) | Woven through, not bolted on |
| 27 | Day 2: reliability & operations | Backups, runbooks, incidents |
| 28 | Finale: the life of one code change | End-to-end + teaching notes |

Steps 15 is the **survey** (all standard approaches, trade-offs); Steps 16–27 are the **deep dive** on the modern container → CI/CD → Kubernetes → observe path, the most *educational* one because it makes every production promise explicit.

---

## Promises served by this chapter

*(Part II's version of the design series' "Principles in play" — for each chapter, which production promises it advances.)*

| Promise | How this chapter set it up |
|---|---|
| **All of them** | This chapter is the lens: every later technique will be justified by *"which promise does it keep?"* |
| **Correct** | "Build once, deploy many" — the same artifact everywhere kills environment-drift bugs. |
| **Survives change** | "Deploy ≠ release" — the foundation for shipping without fear and undoing instantly. |

## Key takeaways (the transferable lessons)

1. **Production is promises, not a place.** Available, correct, survives-change, survives-failure, observable, secure — every tool serves one of these. Keep asking which.
2. **One pipeline underlies everything:** CODE → BUILD → TEST → PACKAGE → RELEASE → DEPLOY → RUN → OBSERVE. All approaches are variations on this spine.
3. **Build once, deploy many.** Freeze the artifact; change only config between environments. Rebuilding per environment is how "works in staging" lies to you.
4. **Deploy ≠ release.** Getting code *running* and sending *users* to it are separable acts — and separating them is the root of safe delivery.
5. **Match the delivery to the scale** (foreshadow) — exactly as we matched the *design* to the scale in Part I. There is no universally "best" deployment; there's appropriate.

---

*Next — Step 14: Production-readiness (the 12-Factor prerequisites). Before any deployment approach works well, the app itself must be built to be deployed: config from the environment, statelessness, health checks, graceful shutdown, structured logs, a real server. We'll apply each to the LMS and produce a production-readiness checklist.*
