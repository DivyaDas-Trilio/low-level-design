# Step 20 — Continuous Delivery & GitOps

*Series: Designing a Library Management System with DDD · Chapter 20 — Part II*

---

CI (Step 19) produced a tested, scanned, SHA-tagged image sitting in the registry. **CD is how that image gets *running*** in front of users. This chapter covers the two ways to do it — the older **push** model and the modern **GitOps** (pull) model — and shows how, with GitOps, *a deploy becomes a git commit and a rollback becomes a git revert.*

---

## 20.1 Delivery vs. Deployment (a vocabulary fix)

Two terms students conflate:

- **Continuous *Delivery*** — every change that passes CI is **automatically made ready to release**; the actual push to prod is a **deliberate action** (a button, an approval).
- **Continuous *Deployment*** — every change that passes CI goes **all the way to production automatically**, no human in the loop.

Most serious systems run **Delivery to production** (auto-deploy to staging, a gate before prod) and reserve full **Deployment** for lower-risk services. Same `CD` acronym, different amount of automation at the last mile.

---

## 20.2 Two models: push vs. pull (GitOps)

### Push-based CD (the older way)

The CI/CD pipeline, after building the image, reaches *into* the cluster and applies the change:

```
 CI builds image ─► pipeline runs `kubectl apply` / `helm upgrade` against the cluster
```

- ✅ Simple, linear, easy to start.
- ❌ **The pipeline needs cluster credentials** (a juicy secret to leak). No automatic **drift detection** — if someone hand-edits the cluster, nothing notices. The cluster's true state isn't recorded anywhere authoritative.

### Pull-based CD = GitOps (the modern standard)

You describe the **desired state** of the cluster *declaratively in a git repo*, and an **agent running inside the cluster** (ArgoCD or Flux) continuously **pulls** that repo and **reconciles** the live cluster to match it.

```
 CI builds image ─► bumps the image tag in the GIT config repo ─► commit
                                                                    │
        ┌───────────────────────────────────────────────────────── ▼
   ArgoCD (in-cluster) sees the commit ─► applies it ─► cluster now matches git
        └────────── continuously re-checks & corrects drift ──────────┘
```

---

## 20.3 The GitOps principles (the part worth memorizing)

1. **Declarative.** The entire desired state of the system is expressed as data (Kubernetes YAML), not scripts.
2. **Versioned & immutable in Git.** Git is the **single source of truth** for *what should be running*. The cluster is downstream of git.
3. **Pulled automatically.** An in-cluster agent applies changes — no external system holds cluster credentials.
4. **Continuously reconciled.** The agent constantly compares desired (git) vs. actual (cluster) and **corrects drift** — if someone manually fiddles with the cluster, it's reverted to match git.

The consequences are lovely:

- **Deploy = `git commit`.** Shipping is a pull request to the config repo.
- **Rollback = `git revert`.** Undo is reverting that commit; the agent reconciles back. No special tooling.
- **The git history *is* the deploy history** — a perfect, signed, reviewable audit log of every change to production.
- **No cluster creds in CI** — CI only needs write access to the config repo, shrinking the blast radius.

---

## 20.4 The two-repo pattern (anchored to the LMS)

GitOps usually splits into **two repos** with different lifecycles:

| Repo | Holds | Changed by |
|---|---|---|
| **App repo** (`lms`) | Source code, Dockerfile, CI | Developers writing features |
| **Config repo** (`lms-deploy`) | Kubernetes manifests / Helm values per environment | CI (image bumps) + ops (infra changes) |

The end-to-end flow for shipping an LMS change:

```
1. Dev merges code to lms/main
2. CI (Step 19): test → build → push  ghcr.io/org/lms:sha-9f8c2a1
3. CI commits to lms-deploy: set image tag to sha-9f8c2a1 in envs/staging/
4. ArgoCD notices the commit on lms-deploy → applies to the STAGING namespace
5. Smoke tests pass → a PR promotes the same tag into envs/prod/  (the gate)
6. ArgoCD applies to PROD → cluster now runs sha-9f8c2a1
```

A minimal ArgoCD **Application** that watches the staging path:

```yaml
# argocd/lms-staging.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata: { name: lms-staging }
spec:
  source:
    repoURL: https://github.com/your-org/lms-deploy
    path: envs/staging                     # the manifests ArgoCD reconciles
    targetRevision: main
  destination:
    server: https://kubernetes.default.svc
    namespace: lms-staging
  syncPolicy:
    automated: { prune: true, selfHeal: true }   # auto-apply + correct drift + remove deleted objects
```

And the one line CI actually changes in the config repo (often via Kustomize/Helm values):

```yaml
# lms-deploy/envs/staging/kustomization.yaml
images:
  - name: ghcr.io/your-org/lms
    newTag: sha-9f8c2a1        # ← CI bumps THIS; ArgoCD does the rest
```

> **Environments are just folders** (`envs/staging`, `envs/prod`) — or branches — in the config repo. **Promotion is a commit** that copies a tag from one folder to another (the registry-level promotion from Step 17, now expressed in git). Step 22 expands on this.

---

## 20.5 Realities & caveats

- **Secrets in GitOps.** You can't commit raw secrets to a git repo. Solutions: **Sealed Secrets** (encrypt secrets so only the cluster can decrypt; safe to commit) or the **External Secrets Operator** (git holds a *reference*; the value is fetched from Vault/cloud secret manager at apply time). Covered in Step 26.
- **The migration ordering problem (Step 18).** The DB migration Job must run *before* the new pods. With ArgoCD this is an **ArgoCD sync hook** (a `PreSync` hook runs the migration Job, then the app rollout proceeds).
- **GitOps shines with Kubernetes**, but the *principle* (declarative desired state in git, reconciled automatically) generalizes — Terraform for cloud infra is the same idea for non-K8s resources.
- **Push-based is fine for simple setups.** GitOps is the standard for fleets and teams; for one small service a PaaS's built-in `git push` deploy (Step 15) already *is* a simple GitOps-like flow. Match the tooling to the scale — again.

---

## Promises served

| Promise | How this chapter advanced it |
|---|---|
| **Correct** | Git is the single source of truth; the cluster is *reconciled* to match it, and drift is auto-corrected. |
| **Survives change** | Deploy = commit, **rollback = `git revert`** — undo is trivial and well-defined. |
| **Observable / auditable** | The git history *is* the deployment history — every prod change is reviewed, signed, and traceable. |
| **Secure** | No cluster credentials in CI (pull, not push); secrets handled via sealed/external secrets. |

## Key takeaways (the transferable lessons)

1. **Delivery ≠ Deployment:** delivery keeps every change *releasable* (push at will); deployment ships to prod *automatically*. Most teams auto-deploy to staging, gate prod.
2. **GitOps makes Git the single source of truth**, with an in-cluster agent (ArgoCD/Flux) **pulling** and **reconciling** the cluster to match — no cluster creds in CI, automatic drift correction.
3. **Deploy = commit, rollback = revert.** The git history becomes a perfect, reviewable audit log of production.
4. **Two repos:** code (app) and manifests (config). **CI bumps the image tag in the config repo; the agent applies it.** Promotion is a commit moving a tag between environment folders.
5. **Match the tooling to scale** — full GitOps for fleets; a PaaS's built-in deploy is already a lightweight version for one small app.

---

*Next — Step 21: Kubernetes core + health probes. The orchestration deep-dive — Pods, Deployments, Services, Ingress, ConfigMaps/Secrets, and the HPA, applied to the LMS — plus the load-bearing distinction between **liveness** and **readiness** probes that ties straight back to the `/healthz` and `/readyz` endpoints from Step 14.*
