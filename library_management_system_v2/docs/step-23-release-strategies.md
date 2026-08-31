# Step 23 — Release Strategies

*Series: Designing a Library Management System with DDD · Chapter 23 — Part II*

---

The new image is deployed to production (Steps 21–22). But **deployed ≠ released** (Step 13): the code is *running*, but how much *real user traffic* hits it — and how fast — is a separate, controllable decision. This chapter is the menu of ways to shift traffic onto a new version *safely*, and the one property that matters more than all of them: **fast, reliable rollback.**

> **The goal of every release strategy is to shrink the blast radius of a bad change** — to expose the fewest users, for the shortest time, with the fastest possible undo. Shipping should be *boring and reversible*.

---

## 23.1 The strategies at a glance

| Strategy | How traffic moves | Risk | Rollback | Extra cost |
|---|---|---|---|---|
| **Recreate** | Stop all old, start all new | High (downtime) | Redeploy old | None |
| **Rolling** *(K8s default)* | Replace pods gradually | Low; brief mixed versions | Roll back the Deployment | None |
| **Blue-Green** | Run new fleet alongside old, flip all traffic at once | Very low; instant switch | Flip back instantly | 2× infra briefly |
| **Canary** | Send 1% → 10% → 100% gradually, watching metrics | Lowest; tiny blast radius | Shift traffic back | Some |
| **Feature flags** | Deploy dark, toggle the *feature* per-user at runtime | Decouples release from deploy entirely | Flip the flag off | A flag system |

These aren't mutually exclusive — the pro move (23.7) **combines** them.

---

## 23.2 Recreate — the one to avoid for user-facing apps

Kill every old pod, then start the new ones. There's a **gap with zero running pods → downtime.**

- ✅ Dead simple; fine when brief downtime is acceptable (internal batch tool, a maintenance window).
- ❌ **Downtime.** Unacceptable for a 24/7 service (the LMS NFR: "available 24/7").
- Only choose it deliberately, e.g. when old and new genuinely *cannot* run simultaneously (a breaking schema change you couldn't expand/contract — which Step 18 teaches you to avoid).

---

## 23.3 Rolling update — the sensible default (and K8s's default)

Replace pods **a few at a time**: start a new pod, wait for its **readiness probe** (Step 21) to pass, route traffic to it, then retire an old pod — repeat until all are new. This is the strategy in our Step 21 Deployment:

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxUnavailable: 0     # never drop below desired capacity (no capacity loss)
    maxSurge: 1           # at most 1 extra pod at a time (one-in, one-out)
```

```
 [v1][v1][v1]  →  [v1][v1][v1][v2]  →  [v1][v1][v2]  →  ...  →  [v2][v2][v2]
                  surge +1, v2 ready    retire a v1                all new
```

- ✅ **Zero downtime, no extra infra**, built in. The right default for most services.
- ⚠️ **Old and new versions serve simultaneously** during the roll — which is *exactly* why migrations must be backwards-compatible (Step 18) and APIs must not break contracts mid-roll.
- **Rollback:** `kubectl rollout undo deployment/lms` instantly shifts back to the previous ReplicaSet (which K8s kept around).

```bash
kubectl rollout status deployment/lms   # watch it progress
kubectl rollout undo deployment/lms     # one-command rollback
```

---

## 23.4 Blue-Green — instant switch, instant undo

Run **two complete production environments**: **blue** (current) and **green** (new). Deploy and fully test green while blue still serves *all* traffic. Then flip the Service/Ingress to point at green — **all at once**.

```
        ┌─ blue  (v1)  ◄── 100% traffic        flip      blue  (v1)   0%
 LB ────┤                              ──────────────►              
        └─ green (v2)   0% (warming)            LB ────► green (v2) 100%
```

- ✅ **Instant cutover and instant rollback** (flip back to blue). Green is fully validated before any user sees it.
- ❌ **Double the infrastructure** during the overlap; database schema must work for both blue and green (expand/contract again).
- **Use when:** you want a clean, atomic switch and can afford 2× capacity briefly.

---

## 23.5 Canary — the gold standard for risk control

Release to a **small fraction of real users first**, watch the metrics, then widen only if healthy. (Named after canaries in coal mines — a small early-warning sample.)

```
 5% → [watch error rate, latency, business metrics] → 25% → [watch] → 50% → 100%
  │                                                                              
  └─ metrics bad at ANY step? → shift traffic back to old version → done (tiny blast radius)
```

For the LMS fine-rate change: send **5% of borrow/return traffic** to the new version, confirm fines compute correctly and latency holds, then ramp. If error rate spikes at 5%, only 5% of users were affected and you roll back in seconds.

- ✅ **Smallest blast radius**; catches problems real traffic reveals that staging didn't.
- ❌ More complex; needs good **observability** (Step 25) to judge "is the canary healthy?", and traffic-splitting machinery.
- **Tooling:** **Argo Rollouts** or **Flagger** automate this — they shift traffic in steps, *query Prometheus* for your success metrics, and **auto-promote or auto-rollback** based on thresholds:

```yaml
# Argo Rollouts canary (sketch): automated, metrics-gated promotion
strategy:
  canary:
    steps:
      - setWeight: 5
      - pause: { duration: 5m }      # bake; analysis runs against Prometheus
      - setWeight: 25
      - pause: { duration: 5m }
      - setWeight: 50
      - pause: { duration: 5m }
    analysis:                         # auto-rollback if error-rate SLO breaches
      templates: [{ templateName: error-rate-check }]
```

---

## 23.6 Feature flags — the cleanest deploy/release split

A **feature flag** wraps new behavior in a runtime toggle. You **deploy** the code with the feature **off** ("dark"), then **release** it by flipping the flag — for specific users, a percentage, or everyone — *without another deploy.*

```python
# the LMS "renew a book" feature, shipped dark, released gradually
if flags.enabled("renew_books", member_id):
    return self.renew_loan(loan_id)        # new path — off by default
raise FeatureNotAvailableError()           # everyone else, unchanged
```

```
 deploy code (flag OFF for all)  ──►  flag ON for staff  ──►  5% of members  ──►  100%
                                                                                    │
                                              fines miscalculate? → flip flag OFF (instant, no deploy)
```

- ✅ **Total decouple of deploy from release**; instant kill-switch; per-user/segment targeting; enables trunk-based dev (merge unfinished work safely behind a flag); A/B testing.
- ❌ Flags accumulate as **tech debt** if never removed — they add branches to your code. Discipline: remove a flag once the feature is fully rolled out.
- **Tooling:** LaunchDarkly, Unleash, Flagsmith, or a simple home-grown config-driven check.

> This is the purest expression of Step 13's *deploy ≠ release*: the ₹6 fine code can be *live on every pod* while *zero members* are charged ₹6 — until you decide, per cohort, to turn it on.

---

## 23.7 Combine them (what good teams actually do)

These layer:

> **Roll out the *artifact* with a canary (or rolling) update, and gate the *feature* behind a flag.** The deploy is de-risked by canary; the feature release is de-risked by the flag. You can roll back the *infrastructure* (`rollout undo`) **and** the *behavior* (flag off) independently.

---

## 23.8 Rollback is the feature that matters most

Every strategy above is, fundamentally, about **making rollback cheap and fast**. The single most important production capability is: *when a release goes wrong, undo it in seconds, before most users notice.*

| Mechanism | Rollback action | Speed |
|---|---|---|
| Rolling (K8s) | `kubectl rollout undo` | seconds |
| GitOps (Step 20) | `git revert` the deploy commit | seconds–minutes |
| Blue-Green | flip the Service back to blue | instant |
| Canary | shift traffic weight back to old | seconds |
| Feature flag | turn the flag off | instant, no deploy |

> **Teaching point:** a team's deploy *frequency* matters far less than its **rollback speed and failure rate** (two of the four DORA metrics). Ship small, ship reversibly. "We deploy carefully once a quarter" is *more* dangerous than "we deploy 20×/day with instant rollback" — small reversible changes fail small.

---

## Promises served

| Promise | How this chapter advanced it |
|---|---|
| **Available** | Rolling/blue-green/canary all keep the service up *during* a release — no downtime to switch versions. |
| **Survives change** | The entire chapter: shrink blast radius (canary/flags) + make rollback instant — shipping becomes low-risk. |
| **Correct** | Canary validates against *real* traffic before full exposure, catching what staging missed. |
| **Observable** | Canary/automated rollback depend on metrics (Step 25) to judge a release's health. |

## Key takeaways (the transferable lessons)

1. **Deploy ≠ release.** Getting code running and exposing users to it are separate, controllable acts — release strategies are how you control the second.
2. **Rolling is the sensible default** (zero-downtime, no extra infra); **blue-green** for atomic cutover; **canary** for the smallest blast radius; **feature flags** to fully decouple release from deploy.
3. **Old + new run together** during rolling/blue-green/canary — which is why backwards-compatible migrations and API contracts (Step 18) are non-negotiable.
4. **Combine them:** canary the artifact, flag the feature — roll back infra and behavior independently.
5. **Rollback speed is the master metric.** Ship small, reversible changes; the ability to undo in seconds matters more than how often you deploy.

---

*Next — Step 24: Networking, TLS, scaling & the database reality. How traffic actually reaches the LMS (DNS → load balancer → ingress → service → pod), how TLS is issued and renewed automatically, how the stateless app scales horizontally — and the hard truth that the **database is the real bottleneck**, with the levers (pooling, replicas, caching) to deal with it.*
