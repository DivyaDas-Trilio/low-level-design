# Part II — Scenarios & Decisions: picking a stack and shipping a change

*Library Management System · Part II, the finale. The six stages —
CODE → BUILD → TEST → PACKAGE → DEPLOY → OBSERVE — laid end to end: a cheat-sheet that maps a
whole stack to your scale, one change walked through the entire pipeline, and the cross-cutting
concerns (security, day-2) that live in every stage at once.*

---

Every prior doc took one **stage** and went deep. This one goes **wide**: it puts the stages back
together. The pipeline is only ever as strong as the seam between two stages, and the seams are
where the real decisions live — *which* build system feeds *which* registry feeds *which* deploy
strategy. There is no single right answer; there is a right answer **for your scale and your
cloud**. So we start with a cheat-sheet, then walk the LMS's ₹5 → ₹6 late-fine change from a git
commit all the way to a percentage of live traffic, then pull out the two concerns that refuse to
sit in one stage: **security** and **day-2 operations**.

---

## 1. Scenario cheat-sheet — match the stack to the scale

Read each **row** as a coherent stack: the tools are chosen to fit *together* at that scale. Don't
mix a FAANG-tier build system onto a startup's problem, or a startup's manual deploy onto a
regulated K8s fleet. Scale **and** cloud posture pick the row.

| Scenario | Build | Test | Package | Deploy | Strategy | Observe |
|---|---|---|---|---|---|---|
| **Startup / one app** | GitHub Actions | unit + Trivy scan | ECR | ECS Fargate or small EKS | Rolling | Datadog / CloudWatch |
| **Mid-size on K8s** | GH Actions (build + scan) | test pyramid + SAST | Harbor / ECR + cosign | Argo CD (GitOps) | Argo Rollouts canary | Prometheus + Grafana + OTel |
| **All-in AWS, no K8s** | CodeBuild | in CodeBuild + scans | ECR | CodePipeline → ECS | CodeDeploy blue/green | CloudWatch + X-Ray |
| **Serverless** | SAM / Serverless Fw | unit + integration | Lambda container image | CodeDeploy | Lambda canary (weighted alias) | X-Ray + CloudWatch |
| **FAANG monorepo** | Bazel | pre/post-submit at scale | internal signed registry | GitOps / custom | canary + feature flags | deep SLOs + metric-based auto-rollback |

**How to read the table.** Left-to-right is the *pipeline*; top-to-bottom is *increasing scale and
governance*. Notice what **stays constant** down every column: an immutable SHA-tagged image, a
scan before it ships, `/healthz` + `/readyz`, structured logs. What **changes** is the machinery
around those constants — a startup's Rolling update and a FAANG canary-with-flags are the *same
idea* (don't expose all users to new code at once) at two very different price points.

> 🎯 **Interview flag — "design the CI/CD for X."** The senior move is to *ask the scale first*,
> then pick a **row**, then justify each cell against that scale. Naming Argo CD for a two-person
> startup, or a manual `kubectl apply` for a regulated fleet, is the tell that you're pattern-
> matching tools instead of matching them to constraints.

> **What to opt for:** **match delivery to scale AND cloud.** Cloud posture picks the column tools
> (ECR+CodeDeploy on AWS, Harbor+Argo on self-managed K8s); scale picks the row (Rolling for one
> app, canary+flags+auto-rollback when a bad minute costs real money). Adopt the next row's
> machinery only when the *pain* of the current row shows up — not before.

---

## 2. Life of a change — ₹5 → ₹6 late fine, end to end

A librarian tells us the late fine is going up: **₹5/day → ₹6/day**. It's a one-line config
change. Watch it travel all six stages — and watch the same **immutable image** carry it, deployed
dark, released gradually.

**Stage 0 — CODE.** The fine rate is *configuration*, not code, so the domain rule
(`Money.rupees(6)` per day late) reads its value from config, not a hard-coded literal. The
developer changes the value in the config source, opens a PR. The **domain layer stays pure** —
this is exactly why the fine rate lives in config: a policy tweak must not require touching (or
re-testing the internals of) the lending aggregate.

**Stage 1 — BUILD.** CI builds one container image and tags it by the commit:
`lms:sha-9f3c1a`. This tag will *never* move. From here on, "the change" **is** that image plus a
config value — nothing rebuilds downstream.

**Stage 2 — TEST.** The pyramid runs against `sha-9f3c1a`: unit tests assert a 3-day-late loan now
owes ₹18 not ₹15; integration tests hit a real SQL repo; a Trivy scan gates the image. Green
merge → the image is blessed.

**Stage 3 — PACKAGE.** `lms:sha-9f3c1a` is pushed to the registry (Harbor on private K8s, ECR on
AWS), **cosign-signed**, SBOM-attached, scanned at the boundary, and tag-immutability locks the
bytes. Dev, staging, prod will all pull *this* digest; only the `LATE_FINE_PAISE=600` config
differs between them.

**Stage 4 — DEPLOY (deploy ≠ release).** The image is rolled onto infrastructure with the new
config, but **traffic is not yet cut over**. This is the crucial split:
- **Private-K8s path:** the change is a git commit to the manifests/Helm values repo
  (`image: lms:sha-9f3c1a`, `LATE_FINE_PAISE: 600`). **Argo CD** notices the drift and **pulls** it
  into the cluster. New pods start, pass `/readyz`, join the service. An **Argo Rollouts canary**
  sends **5%** of members to the new fine logic first.
- **AWS path:** **CodePipeline** ships the ECR image to **ECS**; **CodeDeploy blue/green** spins up
  a green task set beside blue and shifts a weighted slice of traffic. (Serverless equivalent: a
  **weighted Lambda alias** at 5%.)

Behind both, a **feature flag** (`fine_v2`) gates the *behavior* independently of the *deploy* —
so we can dark-ship the pods first and flip the rate for 5% of members second, and flip it **off
instantly** without a redeploy if something looks wrong.

**Stage 5 — OBSERVE (release gradually, auto-rollback).** Structured **JSON logs** carry the loan
id, member id, and computed fine; dashboards watch error rate, p99 latency, and a fine-specific
metric ("fines computed / disputed"). The canary holds at 5% → 25% → 50% → 100% **only while the
SLOs stay green**. A regression — 5xx spike, latency breach, a flood of fine disputes — trips
**metric-based auto-rollback**: Argo Rollouts / CodeDeploy re-points at the previous SHA
(`lms:sha-…prev`) with **no human in the loop**, and the flag flips off. Rollback is trivial
*precisely because* PACKAGE froze an immutable prior image to fall back to.

**The whole arc in one line:** *one immutable image, config per environment, deployed dark,
released gradually, watched by SLOs, rolled back automatically.* That is Part II.

---

## 3. Cross-cutting: Security (DevSecOps) — woven, not bolted on

Security is not a stage; it's a **property of every stage**. Bolting a scan onto the end is the
anti-pattern. Shift it left *and* keep it at the boundaries.

| Where | Control | LMS example |
|---|---|---|
| **CODE** | SAST + dependency scan on PR; **no secrets in git** | `LATE_FINE_PAISE` in config, DB password from a manager |
| **BUILD** | pinned base image, minimal layers, provenance | distroless-ish `lms` image, SBOM generated |
| **PACKAGE** | image scan + **cosign sign** + tag immutability | unsigned image is refused at admission |
| **DEPLOY** | least-privilege identity, network segmentation | K8s RBAC / IAM role, `NetworkPolicy` |
| **RUNTIME** | TLS everywhere, secret rotation, audit logs | ingress TLS terminates in front of the API |

**Secrets come from a manager, never from an image or a git repo.** The LMS DB credential lives in
**Vault** or **AWS Secrets Manager**; on K8s the **External Secrets Operator** syncs it into a
mounted secret at runtime. The image ships with *zero* secrets baked in — that's what lets one
immutable image run in every environment.

**Scan at every stage, not just one:** SAST on the code, dependency/CVE scan on the libraries,
image scan on the artifact (and *again continuously* in the registry, since CVEs surface after
push). **Least privilege everywhere:** the API pod gets an IAM role / K8s ServiceAccount scoped to
exactly what it needs, `NetworkPolicy` limits which pods can reach the DB, ingress terminates TLS.
**Image signing** (cosign) plus an admission policy means the cluster *refuses* to run anything the
pipeline didn't produce — provenance enforced by the platform, not by trust.

> 🎯 **Interview flag — "where does security live in your pipeline?"** The wrong answer names one
> stage. The right answer is **DevSecOps: a control at every seam** — SAST at CODE, scan+sign at
> PACKAGE, RBAC/NetworkPolicy at DEPLOY, secrets-manager + TLS at RUNTIME — with the strongest
> gates at the **registry and admission boundaries** because that's what actually blocks a bad
> artifact from running.

---

## 4. Cross-cutting: Day-2 operations — getting to prod is day 1

Shipping the ₹6 change is **day 1**. Keeping the LMS *up, recoverable, and affordable* for the next
three years is **day 2** — and day 2 is where most of the real work lives.

| Concern | What it means | LMS-scale answer |
|---|---|---|
| **Backups & restore drills** | backups you've *never restored* aren't backups | nightly DB snapshot; **quarterly restore drill** to a scratch env |
| **Runbooks** | the 3 a.m. fix, written down | "fines look wrong → flip `fine_v2` off, roll back SHA" |
| **On-call & incident response** | who gets paged, and the blameless post-mortem after | one rotation at this scale; severity levels + PIR template |
| **Capacity & cost** | right-size before you're surprised | ~100 members → small; watch DB connections, not CPU vanity |
| **Disaster recovery** | defined RTO/RPO, not hope | RPO = last nightly snapshot; RTO = restore-drill-proven |

**Backups are only real once a restore has succeeded.** A snapshot nobody has ever restored is a
guess; the **restore drill** is the test. **Runbooks** turn a rare, high-stress failure into a
checklist — the ₹6 rollback runbook is exactly the "life of a change" arc read backwards. **On-call
+ blameless post-mortems** convert every incident into a fix and a new alert. **Capacity/cost** at
LMS scale is modest, but the discipline (know your limiting resource — here, DB connections) is the
same one that scales. And **DR** is just backups + a proven restore + a stated RTO/RPO.

> **What to opt for:** treat **day-2 as a design input, not an afterthought.** Ship nothing you
> can't *observe* (structured logs + `/healthz`/`/readyz`), *roll back* (immutable prior image),
> and *recover* (a restore you've actually run). Getting to prod is day 1; **staying up is day 2**,
> and day 2 never ends.

---

## 5. Interview Q&A — the questions this series answers

**Q: "How do you deploy to Kubernetes?"**
**Pull-based GitOps** (Argo CD / Flux). The desired state — image SHA + config — is a git commit;
the in-cluster controller *pulls* it and reconciles. Git is the audit log and the rollback
mechanism (revert the commit); no CI system needs cluster credentials. Contrast the anti-pattern:
CI running `kubectl apply` (**push**), which spreads cluster creds into the pipeline and leaves no
record of what's actually running.

**Q: "Blue-green vs canary?"**
**Blue-green** stands up a full second environment and flips 100% of traffic at once — instant
cutover, instant rollback, but double the resources and *every* user hits the new code
simultaneously. **Canary** shifts a *small percentage* first (5% → 25% → …) and watches SLOs before
proceeding — cheaper and it limits blast radius, at the cost of a slower, more complex rollout.
Blue-green for a clean atomic switch; **canary when you want to catch a bad release on 5% of users,
not 100%** — which is why the ₹6 change went canary.

**Q: "How do you ship a risky change safely?"**
Separate **deploy from release**. *Deploy* the immutable image dark (nobody's traffic on it yet),
then *release* it gradually with a **feature flag** + **canary**, watching SLOs, with
**metric-based auto-rollback** armed. The flag flips behavior off in seconds without a redeploy;
the canary limits blast radius; auto-rollback removes the human from the critical minute. That's
the ₹5 → ₹6 playbook.

**Q: "How do you avoid environment-drift bugs ('works in staging, breaks in prod')?"**
**Build once, deploy many.** One immutable, SHA-tagged image (`lms:sha-9f3c1a`) is the *same bytes*
in dev, staging, and prod; only **config** (env vars, secrets from a manager) differs per
environment. Drift dies because there's nothing left to drift — the tested artifact *is* the shipped
artifact.

**Q: "Liveness vs readiness probes?"**
**Liveness (`/healthz`)** answers *"is this process wedged and in need of a restart?"* — it must be
**cheap and dependency-free**. **Readiness (`/readyz`)** answers *"can I serve traffic right now?"*
— it **checks dependencies** (DB reachable, migrations done) and, when it fails, pulls the pod out
of the load balancer *without* restarting it. **Conflating them causes outages:** put a DB check in
liveness and a brief DB blip restart-loops every pod at once, turning a recoverable dependency hiccup
into a full outage.

> 🎯 **Interview flag — the meta-answer.** Nearly every CI/CD question resolves to one of three
> principles: **build once / deploy many** (kills drift), **deploy ≠ release** (kills risky
> cutover), and **observe → auto-rollback** (kills long outages). Name the principle, *then* the
> tool.

---

## Key takeaways

1. **Match the stack to the scale AND the cloud.** The cheat-sheet rows are coherent stacks; the
   columns share the same constants (immutable image, scan, `/healthz`+`/readyz`, structured logs)
   and differ only in machinery. Adopt the next row up only when the pain arrives.
2. **A change is one immutable image + config.** The ₹5 → ₹6 fine travels all six stages as
   `lms:sha-9f3c1a`; nothing downstream rebuilds, and config (`LATE_FINE_PAISE`) is the only thing
   that differs per environment.
3. **Deploy ≠ release.** Deploy dark, release gradually (canary + feature flag), auto-rollback on
   SLO regression. Rollback is trivial because PACKAGE froze an immutable prior image.
4. **Security is every stage** (DevSecOps): secrets from a manager, scan+sign at the boundaries,
   least-privilege identity and network, TLS — woven through, not bolted on.
5. **Day-2 is the real job.** Backups proven by restore drills, runbooks, on-call + blameless
   PIRs, capacity/cost, DR with a stated RTO/RPO. Getting to prod is day 1; staying up is day 2.
6. **Three principles answer most interview questions:** build once / deploy many, deploy ≠
   release, observe → auto-rollback. Name the principle, then the tool.

---

*This closes the six-stage journey: CODE → BUILD → TEST → PACKAGE → DEPLOY → OBSERVE, tied together
by a change that started as one librarian's request and ended as a percentage of live traffic,
watched and reversible. The design in Part I gave us something worth shipping; Part II is how it
ships, safely, and keeps running.*

*Part II complete.*
