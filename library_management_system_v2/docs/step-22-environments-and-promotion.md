# Step 22 — Environments & Promotion

*Series: Designing a Library Management System with DDD · Chapter 22 — Part II*

---

We've been saying "dev → staging → prod" since Step 13. Now we make it precise: *what each environment is for, how the same artifact flows through them, and how "promotion" actually works.* The whole chapter is one idea wearing different clothes:

> **The same immutable image (Step 17) flows through every environment unchanged — only configuration differs.** Each environment is a higher-fidelity rehearsal of production, and "promotion" is the gated act of advancing the *same* artifact one stage closer to users.

---

## 22.1 Why multiple environments at all?

You need places to *prove* a change is safe **before** real users feel it. Each environment trades fidelity-to-prod against safety-to-break:

| Environment | Purpose | Fidelity to prod | Safe to break? |
|---|---|---|---|
| **Dev / local** | Inner-loop coding | Low (SQLite, one process) | Totally |
| **CI / test** | Automated gates (Step 19) | Medium (throwaway Postgres) | Totally |
| **Preview / ephemeral** | One environment *per pull request* | Medium–high | Yes |
| **Staging** | Final rehearsal: prod-like, real integrations | **As close to prod as possible** | Mostly |
| **Production** | Real users, real data | — | **No** |

The golden goal is **dev/prod parity** (12-Factor X): keep environments as *similar as practical* so "works in staging" actually predicts "works in prod." The big lever for parity is using the **same image** and the **same backing-service types** (real Postgres everywhere, not SQLite-in-dev/Postgres-in-prod for the parts that matter).

---

## 22.2 The same artifact, different config

This is "build once, deploy many" (Step 13) realized across environments. The image tag is *identical* in staging and prod; what changes is config:

| Concern | Staging | Production |
|---|---|---|
| Image | `lms:sha-9f8c2a1` | **`lms:sha-9f8c2a1`** (same!) |
| Replicas | 1–2 | 3–10 (HPA) |
| Resources | small | sized for load |
| `DATABASE_URL` | staging DB | prod DB |
| Secrets | staging creds | prod creds |
| Log level | `DEBUG` | `INFO` |
| Feature flags | new features ON | gated rollout |

> **The rule restated:** if you ever find yourself *rebuilding* the image for production, stop — you've broken "build once, deploy many," and the thing you tested is no longer the thing you ship. Differences belong in **config**, never in the artifact.

---

## 22.3 Environments in GitOps = folders, promotion = a commit

With the GitOps config repo from Step 20, environments are just **directories** (or branches), each holding that environment's config + the image tag it currently runs:

```
lms-deploy/                       (the config repo)
├── base/                         shared manifests (Deployment, Service, Ingress…)
└── envs/
    ├── staging/
    │   ├── kustomization.yaml    image tag: sha-9f8c2a1  · replicas: 1 · LOG_LEVEL: DEBUG
    │   └── config.yaml
    └── prod/
        ├── kustomization.yaml    image tag: sha-7e1a0b3  · replicas: 3 · LOG_LEVEL: INFO
        └── config.yaml
```

**Promotion** = a commit that copies a *known-good image tag* from one environment folder to the next:

```diff
# lms-deploy/envs/prod/kustomization.yaml  (a promotion PR)
 images:
   - name: ghcr.io/your-org/lms
-    newTag: sha-7e1a0b3        # old prod version
+    newTag: sha-9f8c2a1        # the EXACT tag that passed staging — promoted as-is
```

ArgoCD (Step 20) sees the commit and reconciles prod to match. **Promotion moves a label, not bytes** — it's the same image that ran in staging. And because it's a git commit, promotion is **reviewable, audited, and revertable**.

---

## 22.4 Gates between environments

Promotion isn't automatic all the way to prod — there are **gates**, each a checkpoint that must pass before advancing:

```
 merge to main
   │  CI: lint/type/test/build/scan/push           (Step 19)
   ▼
 STAGING  ── auto-deploy ──►  smoke + integration + (optional) load tests
   │                          must be GREEN
   ▼
 PRODUCTION  ── manual approval / change gate ──►  canary rollout (Step 23)
```

- **dev → staging:** usually **automatic** on merge to `main`.
- **staging → prod:** usually **gated** — automated checks in staging must pass, *and* often a human approval (a "change gate"), especially for regulated or high-risk systems.

The gates are where "Continuous Delivery vs Deployment" (Step 20) is decided: full Continuous *Deployment* removes the manual gate; most teams keep it for prod.

---

## 22.5 Ephemeral / preview environments (the modern superpower)

A powerful pattern: **spin up a full, temporary environment for every pull request**, automatically, and tear it down when the PR merges/closes.

```
 open PR #142 ─► CI builds lms:sha-pr142 ─► deploy to a fresh namespace `lms-pr-142`
              ─► reviewers test the LIVE feature at pr-142.preview.library.example.com
 close PR     ─► namespace deleted, resources reclaimed
```

- Reviewers test the *running* feature, not just the diff.
- It's possible *because* the app is stateless + containerized + templated (everything we built): a new environment is just "the same manifests in a new namespace with a new tag."
- Keep them cheap (1 replica, shared/seeded DB) and **time-boxed** so they don't pile up cost.

---

## 22.6 The data problem (the part people botch)

Code promotes cleanly; **data does not.**

- **Staging needs prod-*like* data** — same shapes, similar volume — or you won't catch the migration that locks a 100M-row table (Step 18). But you **must not** copy raw production data into a lower environment: that leaks PII (member emails) into a less-secure place. The answer is **anonymized/masked** copies or synthetic seed data.
- **Never run experiments against the prod database** "just to check." Lower environments exist precisely so you don't.
- **Each environment has its own database** (and its own secrets). Promotion advances *code/config*, never live data.

---

## 22.7 Isolation: namespaces vs clusters

How separate should environments be?

- **Namespaces in one cluster** (`lms-staging`, `lms-prod`) — cheap, simple, fine for many teams; isolate with RBAC + NetworkPolicies + resource quotas.
- **Separate clusters per environment** — stronger blast-radius isolation (a staging mistake can't touch prod's control plane); more cost/ops. Common to at least isolate **prod in its own cluster**.

Match the isolation to your risk tolerance — the recurring "match it to the need" theme.

> #### 🧭 Box: "environment ≠ cluster" — you do NOT need 3 clusters
>
> A common misread: *"3 environments means 3 Kubernetes clusters."* It doesn't. An **environment is a *logical* concept** (a place to run a version with its own config + data); **how you isolate it physically is a separate decision** with a spectrum:
>
> | Isolation choice | Looks like | Cost / isolation |
> |---|---|---|
> | **Namespaces in ONE cluster** | `lms-dev` / `lms-staging` / `lms-prod` namespaces, separated by RBAC + NetworkPolicy + quotas | Cheapest; weakest blast-radius isolation |
> | **Prod separate, rest shared** | one `non-prod` cluster (dev+staging) + a dedicated `prod` cluster | Common sweet spot |
> | **One cluster per environment** | 3 clusters | Strongest; 3× control-plane cost + ops |
>
> **What real teams actually do:**
> - **Dev is usually not a cluster at all** — it's your **laptop** (`docker compose`, or local `kind`/`minikube`). Each dev has their own; you don't pay for a per-person dev cluster.
> - **Staging + prod** are the ones on real infrastructure; a very common setup is **two** clusters: `non-prod` (staging + preview envs) and a dedicated `prod`.
>
> **The recommendation:** *at minimum, isolate **production*** (its own cluster, or at least its own namespace + its own DB + its own secrets); everything below prod can share. Match isolation to risk and budget.
>
> **For our LMS (100 members):** you need **zero** dedicated clusters — **dev = laptop, staging + prod = a PaaS** (Step 15). Three K8s clusters for a library app is the deployment-side version of "microservices for 100 members." We teach Kubernetes to make the concepts *explicit*, not because this app needs three clusters.
>
> **Bottom line:** *3 logical environments — yes (test artifacts through staging before prod). 3 physical clusters — almost never; isolate prod, share the rest, keep dev local.*

---

## Promises served

| Promise | How this chapter advanced it |
|---|---|
| **Correct** | The *same* tested image runs everywhere; only config differs — staging genuinely predicts prod. |
| **Survives change** | Gated promotion (staging green → prod approval) catches problems before users do; each promotion is a revertable commit. |
| **Secure** | Per-env databases/secrets + anonymized lower-env data keep PII out of less-trusted places. |
| **(Velocity)** | Preview environments let reviewers test live features fast, without risking shared environments. |

## Key takeaways (the transferable lessons)

1. **Environments are higher-fidelity rehearsals of prod.** Maximize dev/prod parity so "works in staging" actually predicts production.
2. **The same image flows through all environments — only config differs.** Rebuilding per environment breaks "build once, deploy many" and the staging→prod prediction.
3. **In GitOps, environments are folders and promotion is a gated git commit** that moves a known-good tag forward — reviewable, audited, revertable.
4. **Gate the path to prod:** auto to staging, automated checks + (usually) a human approval before prod.
5. **Promote code, not data.** Each env has its own DB; staging needs prod-*like* (anonymized) data; never experiment on prod, never copy raw PII down.

---

*Next — Step 23: Release strategies. The image is deployed to prod — but how do you shift real user *traffic* onto it safely? Recreate vs rolling vs blue-green vs canary vs feature flags, the deploy-≠-release distinction made operational, and how to roll back in seconds when a release goes wrong.*
