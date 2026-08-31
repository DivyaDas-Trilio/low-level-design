# Step 27 — Day 2: Reliability & Operations

*Series: Designing a Library Management System with DDD · Chapter 27 — Part II*

---

Everything so far got the LMS *shipped*. But shipping is **Day 1**. **Day 2** is *running it for years* — and it's usually the harder, longer, less-glamorous part where reliability is actually won or lost. A system that deploys beautifully but can't recover from a failed disk, or whose team drowns in 3am pages, is not production-ready.

> **Day 1 is "does it work?" Day 2 is "does it keep working — through failures, growth, staff turnover, and 3am incidents — without burning out the team?"** This chapter is the operational discipline that answers yes.

---

## 27.1 Backups & restores — and the rule everyone learns the hard way

The database holds the only copy of truth (Step 18). It *will* eventually be corrupted, deleted, or lost. Backups are the safety net — with one brutal caveat:

> **An untested backup is not a backup.** The classic disaster: nightly backups ran "successfully" for two years, then a real restore is attempted during an incident — and the backups were empty/corrupt/incompatible the whole time. **Restores must be tested regularly**, ideally automated, or you don't actually have backups.

Two numbers define your requirements (decide them deliberately, per the LMS's "24/7" NFR):

- **RPO (Recovery Point Objective)** — how much *data* can you afford to lose? "At most 1 hour" ⇒ back up at least hourly.
- **RTO (Recovery Time Objective)** — how *fast* must you recover? "Within 30 minutes" ⇒ your restore process must be that fast (which shapes the backup *type*).

Layers: automated **snapshots** + **continuous WAL/transaction-log archiving** (point-in-time recovery), stored **off-site / cross-region**, **encrypted** (Step 26), and **periodically test-restored**.

---

## 27.2 Disaster recovery (DR)

Backups handle data loss; **DR** handles losing a whole region/datacenter. The spectrum (more resilience = more cost — match it to the stakes):

| Strategy | How | RTO | Cost |
|---|---|---|---|
| **Backup & restore** | Restore into a new region from backups | Hours | $ |
| **Pilot light** | Minimal standby (DB replicating), scale up on failover | ~30–60 min | $$ |
| **Warm standby** | Scaled-down full copy running, scale up on failover | Minutes | $$$ |
| **Active-active** | Full capacity in multiple regions simultaneously | ~0 | $$$$ |

For a 100-member library, **backup & restore** (or pilot light) is appropriate — active-active multi-region would be wild over-engineering. Whatever you choose, **run a DR drill** periodically; an untested DR plan is fiction.

---

## 27.3 Runbooks — operational knowledge that isn't in someone's head

A **runbook** is a written, step-by-step guide for a specific operational task or alert: *"if `BorrowErrorRateHigh` fires → check recent deploys → if a deploy correlates, `kubectl rollout undo` → if DB connections maxed, check the pooler → escalate to DBA if…"*

- Turns tribal knowledge into a **repeatable procedure** anyone on-call can follow at 3am.
- Each **alert** (Step 25) should link to its runbook.
- The best runbooks are **executable** — automate the steps until the runbook becomes a script (and eventually, auto-remediation).

---

## 27.4 On-call & incident response

When something breaks, you need a *practiced* response, not improvisation:

- **On-call rotation** — a fair schedule so someone is always responsible (and no one is *always* responsible → burnout).
- **Severity levels** — SEV1 (full outage, all-hands) … SEV3 (minor) — so response matches impact.
- **Incident Commander** — one person *coordinates* (not necessarily fixes); separates "running the incident" from "debugging it." Critical for big incidents.
- **Clear comms** — a status channel, stakeholder updates, a status page for users.
- **Mitigate first, fix later** — during an incident, **stop the bleeding** (roll back, fail over, disable the feature flag) *before* root-causing. Restore service, then investigate.

> Notice how much of incident response *reuses Part II*: rollback (Step 23), feature-flag kill switch (Step 23), observability to diagnose (Step 25). Day 2 cashes in the checks you wrote on Day 1.

---

## 27.5 Blameless post-mortems

After every significant incident, write a **post-mortem**: timeline, impact, root cause, and — most importantly — **action items to prevent recurrence**.

> **Blameless** is the load-bearing word. The goal is to fix the *system*, not punish a *person*. "Engineer X ran the wrong command" is useless; "the system *allowed* a destructive command with no confirmation, and the runbook was ambiguous" is fixable. Blame makes people hide mistakes; blamelessness surfaces them so you can engineer them out. A culture that punishes incidents gets *fewer reports*, not fewer incidents.

---

## 27.6 Reliability engineering (the SRE mindset)

- **Reliability is a feature with a budget.** The **error budget** (Step 25) governs the tension between shipping fast and staying up: budget healthy → ship boldly; budget burning → freeze features, fix reliability. It turns "stability vs. velocity" from an argument into a *number*.
- **Eliminate toil.** Toil = manual, repetitive, automatable operational work. It scales with traffic and burns people out. Systematically **automate it away** (the runbook → script → auto-remediation progression). If you do something manually twice, script it the third time.
- **Chaos engineering** (advanced) — *deliberately* inject failures (kill a pod, add DB latency) in a controlled way to prove your resilience holds *before* a real incident tests it. "Hope" is not a recovery strategy.

---

## 27.7 Capacity, cost & maintenance (the quiet, continuous work)

- **Capacity planning** — watch growth trends; provision ahead of demand so you don't get caught flat. (The HPA/autoscaler from Step 24 handle spikes; *planning* handles the slow climb.)
- **Cost / FinOps** — cloud bills balloon silently. Right-size resources (Step 21 requests/limits), scale down non-prod off-hours, clean up orphaned resources, watch the bill. Over-provisioning is the deployment-side waste twin of over-engineering.
- **Ongoing maintenance** — OS/dependency patching (Dependabot, Step 26), certificate rotation (cert-manager auto, Step 24), Kubernetes version upgrades, database minor upgrades. Most should be **automated**; the rest belong on a schedule, not "whenever we remember."

---

## Promises served

| Promise | How this chapter advanced it |
|---|---|
| **Survives failure** | Tested backups + DR (data loss & region loss) + chaos testing make recovery real, not theoretical. |
| **Available** | Practiced incident response + runbooks + "mitigate first" minimize downtime when things break. |
| **Survives change** | Error budgets govern velocity-vs-stability; post-mortems engineer out repeat failures. |
| **(Sustainability)** | Toil reduction, fair on-call, and cost control keep the *team and the budget* healthy long-term. |

## Key takeaways (the transferable lessons)

1. **Day 2 is the hard part.** Shipping is the beginning; running reliably for years — through failures, growth, and turnover — is where production is truly judged.
2. **An untested backup isn't a backup.** Test restores regularly; define RPO/RTO deliberately; rehearse DR. Recovery you haven't practiced is fiction.
3. **Make operational knowledge explicit** — runbooks linked from alerts, practiced incident response with an incident commander, *mitigate before you root-cause*.
4. **Post-mortems are blameless** — fix the system, not the person; blame buys silence, not safety.
5. **Reliability is a budgeted feature; eliminate toil; control cost.** Automate the repetitive work away and treat the error budget as the dial between shipping and stabilizing.

---

*Next — Step 28 (finale): The life of one code change, end-to-end. We trace a single change — raising the LMS fine from ₹5 to ₹6 — through *every* stage of Part II (commit → CI → registry → GitOps → canary → observe → done), plus a Part II retrospective and teaching notes to close out the path to production.*
