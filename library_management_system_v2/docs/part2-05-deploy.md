# Part II — DEPLOY: Mechanism, Runtime, Environments, and the Database

*Library Management System · Part II, stage 5 of six (CODE → BUILD → TEST → PACKAGE → DEPLOY → OBSERVE).*

---

PACKAGE handed us **one immutable artifact** — the image `lms:sha-<gitsha>` sitting in a registry.
DEPLOY is the act of getting that exact image **running on infrastructure**: choosing the *mechanism*
that applies it, the *runtime* that hosts it, the *environments* it flows through, and — the part
everyone underestimates — the *stateful database* underneath it. This doc decides all four for our
Python/FastAPI LMS, on a private Kubernetes cluster and on AWS.

---

## 1. Deploy ≠ Release (recap)

**Deploy** = the new code is *running* on infrastructure. **Release** = *users are actually routed to
it.* These are separable acts, and this doc owns only the first half — **getting `lms:sha-<gitsha>`
running, healthy, and reachable in an environment.** *How* you then shift live traffic onto it —
rolling, blue-green, canary, feature flags — is the **release** half, and it gets its own doc.

> This doc is the "make it run" mechanics. The "route users to it safely" strategies are
> **`part2-06-release-strategies`** — every time this doc says *"then traffic shifts"*, that's the
> forward reference.

---

## 2. Mechanism — push vs pull (GitOps)

The first decision: **who applies the manifests to the cluster, and from where?** Two paradigms.

**Push.** CI, having built the image, reaches *into* the cluster and applies the change —
`kubectl apply`, `helm upgrade`, `aws ecs update-service`. The pipeline is the actor; it must **hold
cluster/cloud credentials**. Simple, imperative, and the default most teams start with.

**Pull (GitOps).** A **controller living inside the cluster** continuously reconciles *actual* state
toward *desired* state declared in a Git repo. CI's job ends at "commit the new image tag to the
config repo"; the in-cluster agent (Argo CD / Flux) notices the diff and pulls it in. Nobody pushes;
the cluster **converges**.

| | Push | Pull (GitOps) |
|---|---|---|
| **Actor** | CI reaches into cluster | in-cluster controller reconciles |
| **Credentials** | CI holds cluster creds (broad blast radius) | none leave the cluster; agent reads Git |
| **Source of truth** | whatever CI last ran | **Git — always** |
| **Drift** | undetected; manual `kubectl edit` survives | **auto-detected and healed** back to Git |
| **Rollback** | re-run an old pipeline | **`git revert`** — desired state rewinds |
| **Audit** | pipeline logs | Git history = full change log |

**Tooling by cloud.** On Kubernetes: **Argo CD** or **Flux**. On AWS-native (no K8s):
**CodePipeline + CodeDeploy** orchestrate the push into ECS/Lambda. Multi-cloud / large orgs:
**Spinnaker**.

**Why GitOps wins for anything on K8s.** Git becomes the single source of truth, drift **self-heals**
(someone hand-edits a Deployment at 2am — Argo reverts it), **no CI creds sit in the cluster** (shrinks
blast radius), and rollback is the most boring, most reviewable operation there is: **`git revert`**.
For the LMS, promoting `lms:sha-abc123` is a one-line PR bumping the image tag in the config repo;
merging it *is* the deploy.

🎯 **Interview flag:** "push vs pull deployment" (a.k.a. "what is GitOps?") is a top CI/CD question.
The senior framing: *push* means CI holds cluster credentials and imperatively applies; *pull/GitOps*
means an in-cluster controller reconciles declared state from Git, so **Git is truth, drift self-heals,
credentials never leave the cluster, and rollback is `git revert`.* Name Argo CD/Flux and you're done.

> **What to opt for:** on Kubernetes, **GitOps (Argo CD or Flux)** — pull, not push. If you're
> all-in on AWS with no Kubernetes, **CodePipeline + CodeDeploy** is the native push pipeline and is
> the right call there. Don't bolt a GitOps controller onto a plain-ECS shop just for fashion.

---

## 3. Runtime — where the image actually runs

The mechanism applies *objects*; the runtime is *what those objects are*. On Kubernetes the LMS is a
small, standard set of primitives — and each maps cleanly onto an AWS equivalent:

| Kubernetes object | Job | AWS (ECS/Fargate) equivalent |
|---|---|---|
| **Deployment** | declares N replicas of `lms:sha-<gitsha>`, manages rollout | ECS **Service** |
| **Pod / container** | the running image | ECS **Task** |
| **Service** | stable in-cluster virtual IP / load-balancing | Target Group |
| **Ingress** | external HTTP routing, TLS termination | **ALB** + listener rules |
| **HPA** | scale replicas on CPU/latency | **Service Auto Scaling** |
| **liveness probe** `/healthz` | restart a wedged container | ALB/ECS health check |
| **readiness probe** `/readyz` | gate traffic until deps are ready | Target Group health check |

Our `/healthz` (liveness) and `/readyz` (readiness) endpoints — which **already exist** — are what
make zero-downtime rollout possible: Kubernetes won't send traffic to a Pod until `/readyz` passes,
and restarts one whose `/healthz` goes red. (Right now `/readyz` just returns OK; once the SQL
repository lands in §5 it will do a real `SELECT 1` — see below.)

**Three runtimes, when to pick each:**

| Runtime | Pick when | Cost of the choice |
|---|---|---|
| **Kubernetes / EKS** | you want portability, rich ecosystem, GitOps, multi-service future | most operational surface to run |
| **ECS / Fargate** | AWS-only, want containers without managing a control plane | AWS lock-in; less ecosystem |
| **Lambda (serverless)** | spiky/low traffic, event-driven, want zero idle cost | cold starts, 15-min cap, model doesn't fit a stateful web API well |

> **What to opt for:** for the LMS — a small, always-on stateful web service — **EKS with GitOps** if
> the org already runs Kubernetes; **ECS/Fargate** if it's AWS-native and doesn't want a K8s control
> plane. **Skip Lambda** here: a persistent FastAPI app with DB connections and steady traffic is a
> poor fit for a function runtime. The image `lms:sha-<gitsha>` is *byte-identical* across all three —
> only the wrapper differs.

🎯 **Interview flag:** "EKS vs ECS/Fargate vs Lambda" tests whether you match *runtime to workload*.
Answer by workload shape: **long-running stateful service → EKS or ECS/Fargate**; **bursty/event-driven,
tolerant of cold starts → Lambda**. Reach for EKS specifically when you want K8s portability and
ecosystem; ECS/Fargate when you want containers with the least AWS-managed control-plane overhead.

---

## 4. Environments & promotion

**One immutable image, many environments.** The *same* `lms:sha-<gitsha>` that passed tests flows
`dev → staging → prod` **unchanged** — this is "build once, deploy many" from the overview. What
differs between environments is **only configuration**, injected as env vars:

- `LMS_DATABASE_URL` — points at the dev / staging / prod database
- `LMS_LOG_LEVEL` — `DEBUG` in dev, `INFO` in prod
- `LMS_FINE_RATE_PAISE` — the ₹5/day fine as config, not code (so a policy change is an env change)

Rebuilding per environment reintroduces "but it worked in staging!" — the artifact is frozen; **only
the env changes.**

**Isolation — how hard is the wall between environments?**

| | Kubernetes | AWS |
|---|---|---|
| **Light isolation** | separate **namespaces** in one cluster | separate resources in one account |
| **Strong isolation (prod)** | **separate cluster** for prod | **separate AWS account** for prod |

**Promotion mechanics.** With GitOps, promoting to the next environment is a **PR against the config
repo** that bumps the image tag in that environment's overlay; **Argo ApplicationSets** template the
same app across environments so the promotion is a reviewed, reverible Git change. On AWS-native,
promotion is **CodePipeline stages** (`Dev → Staging → Prod`) with **manual approval gates** between
them.

🎯 **Interview flag:** "how do you isolate environments?" — the senior answer talks **blast radius**:
namespaces are convenient but share a control plane and node pool, so a bad prod change (or a noisy
neighbor, or an RBAC slip) can bleed across. For **prod**, prefer a **separate cluster (K8s) or a
separate AWS account (AWS)** so a mistake in dev/staging *cannot* physically reach prod. Isolation is a
blast-radius decision, not a tidiness one.

> **What to opt for:** dev + staging share a cluster/account via **namespaces**; **prod gets its own
> cluster (K8s) or its own AWS account (AWS)**. Promote by **GitOps PR / ApplicationSets** on K8s, or
> **CodePipeline stages with an approval gate** on AWS. Same image throughout — only config moves.

---

## 5. The database — the stateful, scary part

Everything above is **stateless**: kill a Pod, another identical one takes its place. The database is
the opposite — it holds the only thing you can't recreate, so it gets the most caution in the whole
pipeline. This is also **exactly where the LMS stops being a toy**: today repositories sit behind
interfaces with an **in-memory adapter**; the real database lands when we implement
**`SqlLoanRepository` / `SqlBookRepository`** against those *same interfaces* — the domain layer
never learns the difference. And it's the moment `/readyz` starts doing a real **`SELECT 1`** instead
of returning a bare OK.

### 5a. Hosting — managed vs self-hosted

| Concern | Private cloud (Kubernetes) | Public cloud (AWS) |
|---|---|---|
| **Hosting** | Postgres **operator** (CloudNativePG / Zalando) or a **StatefulSet**, *or* an external managed DB | **RDS** / **Aurora** (managed) |
| **Migrations** | **Alembic** run as a **pre-deploy Job** / init container | **Alembic** as a one-off **ECS task** / **CodeBuild** step |
| **Backups** | operator snapshots / **Velero** volume backups | **RDS snapshots + PITR** (point-in-time recovery) |
| **Connection** | `LMS_DATABASE_URL` from a **Secret** | `LMS_DATABASE_URL` from a **Secret** — *same* |

**Prefer managed even on Kubernetes.** Running Postgres yourself in-cluster (StatefulSet + operator)
is *possible* and the operators (CloudNativePG, Zalando) are genuinely good — but you inherit
failover, backup verification, patching, and storage tuning. For a ~100-member LMS, that's effort
spent on undifferentiated heavy lifting. **RDS/Aurora (or an external managed Postgres even from a
K8s cluster) buys back all of it.** The application doesn't care: it reads `LMS_DATABASE_URL` from a
Secret either way.

🎯 **Interview flag:** "would you run your database inside Kubernetes?" — the strong answer is *"usually
no — prefer managed (RDS/Aurora), even when the app runs on K8s."* K8s is built for **stateless,
fungible** workloads; stateful data wants careful failover and backups that managed services already
solve. Reach for an in-cluster operator only with a real reason (air-gapped, cost at scale, strict data
residency) — and know you're taking on day-2 database operations when you do.

### 5b. Migrations — expand → migrate → contract

The dangerous coupling: **schema and code deploy at different instants**, and during a rollout **old
and new code run simultaneously**. A migration that drops or renames a column the still-running old
Pods depend on causes errors mid-deploy. The discipline that avoids this is **backward-compatible,
multi-step migrations** — the **expand → contract** pattern:

1. **Expand** — add the new schema (new nullable column / new table) **without removing anything**.
   Both old and new code work against it.
2. **Migrate** — deploy code that writes/reads the new shape; backfill data.
3. **Contract** — only *after* the new code is fully rolled out and stable, a *later* deploy removes
   the old column.

Migrations run **as a gate *before* the new app rolls out** — a pre-deploy Alembic Job (K8s) or a
one-off ECS/CodeBuild task (AWS) — never from inside the app on startup (N replicas racing to migrate
is a corruption bug). Because each step is backward-compatible, **rollback stays safe**: reverting the
app doesn't strand it against a schema it can't use.

🎯 **Interview flag:** "how do you do a zero-downtime schema change?" — say **expand/contract**: never
rename or drop in the same deploy as the code that stops needing the column. Add-first, ship code,
remove-later, across *separate* deploys — so old and new code coexist safely during every rollout and
rollback. This is the single most common database-in-CI/CD question.

### 5c. Backups

Backups are non-negotiable and **must be restore-tested** (an untested backup is a hope, not a
backup). Managed makes this cheap: **RDS/Aurora automated snapshots + point-in-time recovery**;
in-cluster, **operator-managed snapshots or Velero** volume backups. Either way, know your RPO/RTO
before you need them.

> **What to opt for:** **managed Postgres (RDS/Aurora) even when the app runs on Kubernetes** —
> hand off failover, patching, and backups. Do migrations with **Alembic as a pre-deploy gate** using
> **expand → contract** so old and new code coexist safely. Keep `LMS_DATABASE_URL` in a Secret, and
> restore-test backups on a schedule. The `SqlLoanRepository` swap changes *infrastructure only* —
> the domain interfaces, and every test against them, are untouched.

---

## Key takeaways

1. **Deploy ≠ release** — this doc gets `lms:sha-<gitsha>` *running and healthy*; routing users to it
   (rolling / blue-green / canary / flags) is **`part2-06`**.
2. **Pull beats push on K8s** — **GitOps (Argo CD/Flux)**: Git is truth, drift self-heals, no CI creds
   in-cluster, rollback = `git revert`. AWS-native without K8s: **CodePipeline + CodeDeploy**.
3. **Match runtime to workload** — long-running stateful service → **EKS or ECS/Fargate**; skip Lambda
   for a persistent DB-backed API. The image is byte-identical across all three.
4. **One immutable image, config-only differences** across dev → staging → prod; **isolate prod by
   blast radius** — separate cluster (K8s) or separate account (AWS).
5. **The database is the scary part** — prefer **managed (RDS/Aurora) even on K8s**, migrate with
   **Alembic expand→contract gated before rollout**, and back up with PITR. This is where the LMS's
   in-memory repos become **`SqlLoanRepository`** (interface unchanged) and **`/readyz` starts doing a
   real `SELECT 1`**.

---

*Next — `part2-06-release-strategies`: the DEPLOY (release) half — rolling, blue-green, canary, and
feature flags, and — given a scenario — what to opt for.*
