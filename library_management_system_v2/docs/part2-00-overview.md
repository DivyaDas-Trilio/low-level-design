# Part II — From Code to Production: Overview

*Library Management System · Part II opens here. Part I (steps 1–12) designed and built the
app; Part II takes it to production.*

---

Part I ended with an app that **runs on a laptop** in pure Python. Part II answers the only
question that matters next: **how does that code actually reach production — reliably, safely,
and the way real teams do it — on a private Kubernetes cluster and on AWS?**

This part is deliberately reorganized around the **pipeline every change travels**, not around a
tool checklist. For each stage we ask three things: *what are the real ways to do it, how does it
differ between private cloud (K8s) and public cloud (AWS), and — given a scenario — what do you
opt for?*

---

## 1. Production is a set of promises, not a place

"Deploying" is not "copying code to a server." **Production is a set of promises to users**, and
every technique in Part II exists to keep one of them:

| Promise | Plain meaning | Kept by |
|---|---|---|
| **Available** | Reachable almost always | redundancy, health probes, zero-downtime deploys |
| **Correct** | Right version, right config, right data | immutable artifacts, migrations, config-from-env |
| **Survives change** | Ship safely; undo fast | release strategies, rollback |
| **Survives failure** | A crash/spike doesn't take it down | orchestration, auto-healing, autoscaling |
| **Observable** | When it breaks, you see what & why | logs, metrics, traces, SLOs |
| **Secure** | Secrets safe, surface minimal | secret managers, scanning, least privilege |

> **The recurring question for all of Part II:** for every tool or step, ask *"which promise does
> this keep?"* If it serves none of them, it's ceremony.

---

## 2. The pipeline — six stages every change travels

```
  CODE  →  BUILD  →  TEST  →  PACKAGE  →  DEPLOY  →  OBSERVE
   │         │        │         │           │          │
 commit    CI +     gates    one immutable  onto      logs, metrics,
 to git    image    (pyramid  SHA-tagged    infra +   traces → feed
           build     + scans)  artifact      running   back / rollback
                                              │            │
                                              └── release ─┘  (deploy ≠ release)
```

Whether you deploy by hand to one VM or run a Kubernetes fleet, every change travels these six
stages. Five are a **tooling** choice; **DEPLOY** is where the **strategy** choices live —
because *deploy* (code running) and *release* (users routed to it) are separable acts.

Each later doc in Part II owns one stage (DEPLOY gets two — mechanism, then release strategies).

---

## 3. Two ideas that thread through everything

### (a) Build once, deploy many
Build **one** immutable artifact (a SHA-tagged container image) and promote that *exact same*
image through dev → staging → prod. **Never rebuild per environment** — the thing you tested must
be byte-for-byte the thing you ship. Only **configuration** changes between environments. This is
what kills *"but it worked in staging!"*

### (b) Deploy ≠ Release
- **Deploy** = the new code is *running* on infrastructure.
- **Release** = *users are actually being sent to it.*

Decoupling them is the root of safe shipping — and the whole point of the release strategies
(canary, blue-green, feature flags) in `part2-06`.

> **LMS anchor:** raising the late fine **₹5 → ₹6**. *Deploying* means the ₹6 code is live on the
> servers; *releasing* means real members start being charged ₹6. You deploy cautiously and
> release gradually while watching metrics — you don't flip a switch and hope. (And because the
> fine rate is **config**, not code, even this is an env change on one immutable image.)

---

## 4. The two-cloud lens (used in every stage doc)

The same six stages look different on a self-managed **Kubernetes** cluster (private cloud) versus
on **AWS** (public cloud). This is the map every following doc fills in for its stage:

| Stage | Private cloud (Kubernetes) | Public cloud (AWS) |
|---|---|---|
| **CODE** | Git (GitHub/GitLab), trunk-based | same |
| **BUILD** | CI + Kaniko/BuildKit in-cluster (or GitHub Actions) | CodeBuild |
| **TEST** | CI test pyramid + Trivy/CodeQL | same (in CodeBuild) |
| **PACKAGE** | image → Harbor / self-hosted registry | image → Amazon ECR |
| **DEPLOY** | GitOps: Argo CD / Flux | CodePipeline + CodeDeploy (or EKS + Argo) |
| **OBSERVE** | Prometheus + Grafana + Loki + OTel | CloudWatch + X-Ray |

> **What to opt for (the through-line):** on a private K8s cluster, the spine is **GitOps
> (Argo CD/Flux)**; all-in on AWS without Kubernetes, it's **CodePipeline + ECS + CodeDeploy**;
> **EKS** lets you use K8s tooling on AWS. The *same* immutable image travels either path — only
> config differs.

---

## 5. How to read Part II

| Doc | Stage | You'll be able to decide |
|---|---|---|
| `part2-01-code` | **CODE** | branching model, monorepo vs polyrepo, where feature flags fit |
| `part2-02-build` | **BUILD** | app-readiness (12-factor), CI engine, how/where the image is built |
| `part2-03-test` | **TEST** | the test pyramid + which scans gate a merge |
| `part2-04-package` | **PACKAGE** | registry, immutable tagging, signing/scanning |
| `part2-05-deploy` | **DEPLOY** | push vs GitOps, runtime (K8s/ECS/Lambda), environments, the database |
| `part2-06-release-strategies` | **DEPLOY (release)** | rolling / blue-green / canary / feature flags — what to opt for |
| `part2-07-observe` | **OBSERVE** | logs/metrics/traces, SLOs, and the auto-rollback feedback loop |
| `part2-08-scenarios-and-decisions` | **all** | the scenario cheat-sheet, security/day-2, and interview answers |

Two companion **interactive artifacts** accompany this part: *The Delivery Line* (the flow) and
*Ways to Production* (the decision-map). The docs are their written form.

---

## Key takeaways

1. **Production is promises, not a place.** Every tool serves one of six promises — keep asking which.
2. **One pipeline underlies everything:** CODE → BUILD → TEST → PACKAGE → DEPLOY → OBSERVE.
3. **Build once, deploy many** — freeze the artifact, change only config between environments.
4. **Deploy ≠ release** — separating "running" from "serving users" is the root of safe delivery.
5. **Match delivery to scale and cloud** — there's no universally best stack, only the appropriate one; the K8s-vs-AWS lens runs through every stage.

---

*Next — `part2-01-code`: the CODE stage — version control, branching models, and how teams keep
`main` always shippable.*
