# Part II — Release Strategies: How a New Version Takes Over Traffic

*Library Management System · Part II, the release half of DEPLOY (CODE → BUILD → TEST → PACKAGE → DEPLOY → OBSERVE).*

---

`part2-05` got a new image **running** in the cluster. This doc answers the other half of DEPLOY:
**how users start hitting it** — and how you claw that back in seconds when it misbehaves. The
whole discipline hangs on one distinction most engineers blur, so we start there.

---

## 1. Deploy ≠ Release — the split that makes shipping safe

- **Deploy** = the new version is **running** in prod. Zero users routed to it. A pure
  infrastructure event — reversible, invisible, boring.
- **Release** = **users are routed** to that running version. A traffic event — the moment risk
  becomes real.

Collapse the two ("push to prod") and every deploy is a coin-flip in front of live users. Separate
them and you get the core move of safe shipping: **deploy dark, then release gradually** — ship the
bits with nobody watching, then open the tap by 1%, watching metrics, ready to close it.

**LMS running example.** Raising the late fine **₹5/day → ₹6/day** is a *config* change on one
**immutable image** (the rate lives in versioned config, not code — see `part2-01`). The image
doesn't change; the value it reads does. So we **deploy the image dark** (nobody sees ₹6), then
**release the ₹6 rate gradually** to a slice of members while watching fine-dispute and
return-rate metrics. That is this entire doc in one sentence. Everything below is *how* you open
the tap.

🎯 **Interview flag:** "What's the difference between deploy and release?" is a warm-up that
separates seniors from juniors. Deploy = running; release = users routed. Naming that split — and
that feature flags / traffic weights are what let you do release without another deploy — is the
signal.

---

## 2. The strategies

Six ways a new version takes over, from crudest to most surgical.

**Recreate.** Kill all old pods, then start the new ones. Simple, but there's a **downtime window**
and no gradual exposure. Dev/staging only, or a stateful app that flatly cannot run two versions at
once.
- *Cost:* none. *Rollback:* redeploy old (with downtime). *Opt for:* non-prod, or a hard
  single-version constraint.

**Rolling update.** Replace pods **a few at a time** — new ones come up healthy, old ones drain,
until the fleet is all-new. **Kubernetes' default**, needs **no extra infrastructure**, zero
downtime. But rollout and release are welded together (every replaced pod serves real traffic), so
a bad version reaches users progressively, and **rollback means rolling forward again** with the old
image — minutes, not seconds.
- *Cost:* none. *Rollback:* roll back the Deployment (slow-ish). *Opt for:* the **default** for
  stateless, low-risk changes.

**Blue-Green.** Stand up a **full second environment** (green) alongside live (blue), test green in
isolation, then **flip the load balancer** so 100% of traffic cuts to green at once. Rollback is
**instant** — flip back to blue, which is still warm. The price is **2× capacity** during the
switch, and the cutover is all-or-nothing (no gradual exposure).
- *Cost:* 2× infra. *Rollback:* instant (flip LB). *Opt for:* you need **instant rollback** and can
  afford double capacity.

**Canary.** Route a **tiny slice first — 1% → 10% → 100%** — automatically **watching metrics** (error
rate, latency, business KPIs) at each step, promoting only if healthy and **auto-aborting** on
regression. The safest for high-risk changes because the **blast radius is bounded** to the current
weight. Needs **traffic-splitting** (mesh or weighted ingress) **and metric analysis** to be real —
a canary nobody measures is just a slow rolling update.
- *Cost:* modest (split + analysis tooling). *Rollback:* shift weight to 0% (fast). *Opt for:*
  **high-risk, user-facing** changes.

**Feature flags.** Deploy the code **dark**; **toggle it on at runtime** per cohort — no redeploy to
turn it on or off. This **fully decouples deploy from release** (§1) and works at a *finer grain*
than pod-level strategies: you can gate the ₹6 fine to "members created after date X" or flip a
**kill-switch** in one API call. Complements canary rather than replacing it.
- *Cost:* a flag service + cleanup discipline. *Rollback:* flip the flag (instant). *Opt for:*
  **gradual / A-B rollouts** and kill-switches.

**Shadow (mirror).** **Copy** live production traffic to the new version, whose responses are
**discarded** — users are unaffected. Proves the new version under **real load and real payloads**
before any user sees it. Great for perf/regression validation; overkill for a config bump, and you
must guard against double **side-effects** (don't let the shadow write fines twice).
- *Cost:* mirror infra; side-effect care. *Rollback:* n/a (no user traffic). *Opt for:*
  **de-risking** before a real release.

### Strategy comparison

| Strategy | How | Cost | Rollback | Opt for when |
|---|---|---|---|---|
| **Recreate** | down, then up | none | redeploy old (downtime) | dev/staging; single-version-only apps |
| **Rolling** | replace pods gradually | none (K8s default) | roll back Deployment (minutes) | default for stateless, low-risk |
| **Blue-Green** | 2 full envs, flip LB | 2× capacity | **instant** (flip back) | need instant rollback, can pay 2× |
| **Canary** | 1%→10%→100%, watch metrics | split + analysis | shift weight to 0% (fast) | high-risk, user-facing changes |
| **Feature flags** | deploy dark, toggle per cohort | flag service | flip flag (instant) | gradual / A-B, kill-switch |
| **Shadow** | mirror prod traffic, discard | mirror infra | n/a (no user impact) | validate under real load first |

🎯 **Interview flag — blue-green vs canary.** Both give safe rollback; the trade-off is **capacity
vs gradualness**. Blue-green = **instant** switch and instant revert, but **all-or-nothing** and
**2× infra**. Canary = **gradual** exposure with a **bounded blast radius** and cheap infra, but
rollback is "shift weight back," not a single flip, and it **needs metric analysis** to mean
anything. Seniors pick canary when the change is risky and you want to *observe* before full
exposure; blue-green when the environment is expensive to reason about and you want a clean, instant
revert.

---

## 3. Progressive-delivery tooling

Canary and gradual rollout aren't hand-rolled — you drive them with a controller that owns the
weight steps, the analysis, and the auto-abort.

**Kubernetes.**
- **Argo Rollouts** or **Flagger** — a `Rollout`/`Canary` CRD replaces the plain Deployment and
  automates the weight steps, metric queries, and promotion/abort.
- **Traffic splitting** comes from a **service mesh** (Istio, Linkerd) or **ingress weighting**
  (NGINX/Gateway API canary annotations) — the mesh/ingress is what actually sends 10% of requests
  to the new pods.
- **Metric analysis** wires the controller to **Prometheus** (the OBSERVE stage, `part2-07`): the
  rollout promotes only if the queries stay green.

**AWS.**
- **CodeDeploy** does **canary** and **blue/green** natively for ECS/Lambda (traffic-shift configs
  like `Canary10Percent5Minutes`), with **CloudWatch alarms** as the auto-rollback trigger.
- **Lambda weighted aliases** shift a % of invocations to a new version.
- **ALB weighted target groups** split HTTP traffic across old/new target groups for a canary on
  EC2/ECS.

> **What to opt for:** on K8s, **Argo Rollouts + Prometheus analysis** over a mesh or weighted
> ingress; on AWS, **CodeDeploy** traffic-shifting with **CloudWatch-alarm auto-rollback**. In both
> cases the non-negotiable is **automated abort on an SLO/metric regression** — a canary a human has
> to babysit is a canary that rolls back too late.

---

## 4. The two-cloud lens — how each strategy is implemented

| Concern | Private cloud (Kubernetes) | Public cloud (AWS) |
|---|---|---|
| **Rolling** | Deployment `strategy: rollingUpdate` (maxSurge/maxUnavailable) | ECS rolling update (minHealthy/maxPercent) |
| **Blue-Green** | two Services + label flip, or **Argo Rollouts** blueGreen | **CodeDeploy** blue/green (ECS/Lambda) |
| **Canary** | **Argo Rollouts / Flagger** + mesh (Istio/Linkerd) or ingress weights | **CodeDeploy** canary, or **ALB weighted target groups** |
| **Feature flags** | **Unleash** (self-hosted) | **LaunchDarkly** / **AWS AppConfig** |
| **Metric analysis / abort** | Prometheus queries in the Rollout | CloudWatch alarms on the deployment |
| **Traffic split primitive** | mesh / Gateway API weighting | ALB weights / Lambda alias weights |

The **strategy is portable — the primitive isn't**. "Canary" means the same thing on both clouds; on
K8s the weight lives in a mesh, on AWS it lives in an ALB or CodeDeploy config. Pick the strategy
from the risk of the change, then map it to whichever primitive the platform gives you.

---

## 5. Decision matrix — scenario → strategy

| Scenario | Strategy |
|---|---|
| Dev/staging refresh, downtime fine | **Recreate** |
| Routine stateless change, low risk (e.g. a UI copy tweak) | **Rolling** (K8s default) |
| Risky migration where you must revert in seconds | **Blue-Green** |
| High-risk user-facing change, want bounded blast radius | **Canary** with metric analysis |
| Gradual / per-cohort or A-B rollout, need a kill-switch | **Feature flags** |
| Prove a new version under real load before any user sees it | **Shadow** |
| **The LMS ₹5 → ₹6 fine bump** | **Feature flag (deploy dark) + canary release** with auto-rollback |

The LMS row is the synthesis: the ₹6 rate ships **dark behind a flag**, is **released to a canary
slice** of members while fine-dispute and return metrics are watched, and **auto-rolls back** (flip
the flag / shift weight to 0) on any regression — no redeploy, seconds to revert.

> **What to opt for:**
> - **Rolling** as the **default** — stateless, low-risk, no extra infra.
> - **Blue-Green** when you need **instant rollback** and can afford **2× capacity**.
> - **Canary** for **high-risk, user-facing** changes where you want to observe before full exposure.
> - **Feature flags** for **gradual / A-B** rollouts and runtime kill-switches.
> - The **FAANG default for a risky change: canary + feature flags with automated rollback on SLO
>   regression** — deploy dark, release gradually, let metrics (not a human) decide.

🎯 **Interview flag — "How do you ship a risky change safely?"** The highest-signal answer stacks the
mechanisms: **deploy dark behind a feature flag → release via a gradual canary → auto-rollback on
SLO regression**. It names the deploy≠release split, bounds the blast radius, decouples release from
deploy, and hands the go/no-go to metrics. Anchor it in the LMS ₹6 fine change and you've shown you
can apply it, not just recite it.

---

## Key takeaways

1. **Deploy ≠ release.** Deploy = running; release = users routed. Separating them — **deploy dark,
   release gradually** — is the root of safe shipping.
2. **Match strategy to risk.** Rolling by default; blue-green for instant rollback at 2× cost;
   canary for high-risk user-facing changes; feature flags for gradual/A-B and kill-switches;
   shadow to de-risk under real load.
3. **Blue-green vs canary** is **capacity vs gradualness** — instant all-or-nothing flip vs bounded,
   measured exposure.
4. **Progressive delivery is a controller's job** — Argo Rollouts/Flagger + mesh on K8s, CodeDeploy
   on AWS — and its non-negotiable is **automated abort on SLO regression**.
5. **Strategy is portable, the primitive isn't** — "canary" is the same idea; the traffic split
   lives in a mesh (K8s) or an ALB/alias (AWS).
6. **The FAANG default** for anything risky: **canary + feature flags + auto-rollback**, exactly
   how the LMS ships ₹5 → ₹6.

---

*Next — `part2-07-observe`: the OBSERVE stage — metrics, logs, and traces, and how the SLOs that
auto-rollback a canary get measured in the first place.*
