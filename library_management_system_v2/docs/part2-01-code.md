# Part II — CODE: Version Control, Branching, and Feature Flags

*Library Management System · Part II, stage 1 of six (CODE → BUILD → TEST → PACKAGE → DEPLOY → OBSERVE).*

---

The pipeline starts where every change is born: **a commit**. CODE is the cheapest stage to get
right and the most expensive to get wrong — a bad branching model quietly taxes every later stage
with merge pain, stale environments, and "which version is actually in prod?" This doc decides
**how source is versioned, how branches flow to `main`, one repo or many, and how `main` stays
always-shippable** for our Python/FastAPI LMS.

---

## 1. Version control is the source of truth

**Git** is non-negotiable — distributed, cheap branches, the substrate every CI/CD tool assumes.
The choice is the *host*, and it's mostly an ecosystem decision, not a Git decision:

| Host | Fits when | Comes with |
|---|---|---|
| **GitHub** | default; strongest ecosystem | Actions (CI), Packages, CodeQL, Dependabot |
| **GitLab** | want one tool for repo + CI + registry + security | built-in CI, container registry, self-host option |
| **Bitbucket** | already on Atlassian (Jira/Confluence) | Pipelines, tight Jira linking |

The repo is the **single source of truth** not just for code but — critically — for the LMS's
**business policy that is now config**: the `₹5/day` fine rate and the `borrow-limit = 2`. These
live as versioned config in Git, reviewed like code, not hard-coded and not hand-edited in prod.

> **What to opt for:** GitHub unless an existing Atlassian or self-hosted-GitLab investment already
> anchors the team. Don't split the difference across hosts.

---

## 2. Branching models — trunk-based vs GitFlow

This is the central decision of the CODE stage.

**Trunk-based development.** Everyone integrates into a single `main` (the "trunk"). Branches are
**short-lived** (hours to ~2 days), merge to `main` **daily or faster**, and `main` is **always
releasable**. Incomplete work is hidden behind **feature flags** (§4), not held on a long branch.

**GitFlow.** Long-lived parallel branches: `main` (released), `develop` (integration), plus
`feature/*`, `release/*`, and `hotfix/*`. Work accumulates on `develop`, is stabilized on a
`release/*` branch, then merged to `main` and tagged. Structured, ceremonial, and **slow to
integrate**.

| | Trunk-based | GitFlow |
|---|---|---|
| **Branch lifetime** | hours–2 days | days–weeks |
| **Integration** | continuous (daily to `main`) | batched via `develop`/`release` |
| **`main` state** | always releasable | released; work lives on `develop` |
| **Merge conflicts** | small, frequent, cheap | large, rare, painful |
| **Hides unfinished work with** | feature flags | branches |
| **Best for** | continuous delivery, web services | versioned/on-prem releases on a cadence |

**Why trunk-based for the LMS.** It's a continuously-delivered web service (single deployable),
small team, and we want changes like the fine-rate bump flowing to prod within the day. Long-lived
branches would just manufacture merge conflicts across our vertical slices (catalog / membership /
lending / fines).

**When GitFlow genuinely fits:** you ship **versioned software on a release cadence** — an on-prem
product where customers run v2.3 while you maintain v2.2 (see `appendix-on-prem-multi-distro-delivery`).
Then `release/*` and `hotfix/*` branches earn their keep. For a service you deploy yourself, they
don't.

🎯 **Interview flag:** "trunk-based vs GitFlow" is one of the most common CI/CD interview questions.
The senior answer isn't "trunk-based is better" — it's *"trunk-based for continuously-deployed
services; GitFlow only when you support multiple shipped versions in the field."* Tie the branching
model to the **release model**, not to taste.

> **What to opt for:** **trunk-based + short-lived branches + feature flags** for anything you
> continuously deliver. Reserve GitFlow for versioned/on-prem software shipped on a cadence.

---

## 3. Protecting the trunk

"`main` always releasable" is a promise you **enforce with tooling**, not with etiquette. On the
default branch, require:

- **Pull request + review** before merge (no direct pushes to `main`).
- **Required status checks** — CI build, test pyramid, and security scans must be green (these are
  the BUILD/TEST stages, `part2-02`/`03`) before merge is allowed.
- **Linear history / up-to-date branch** so what you tested is what you merge.
- **Signed commits** (`git commit -S`, GPG/SSH/Sigstore) so authorship is verifiable — the first
  link in the supply-chain-integrity story that continues with image signing in `part2-04`.

Short-lived branches make this cheap: small diffs review fast and rarely go stale.

---

## 4. Feature flags — keep the trunk always-releasable

Trunk-based has one obvious tension: **if unfinished code lands on `main` daily, how is `main` still
releasable?** The answer is **feature flags** (feature toggles). Merge the code *dark* — present but
switched off — and turn it on later, independent of the deploy.

This is exactly the **deploy ≠ release** split from the overview, made concrete:

- **Deploy** = the new code is running in prod (flag off — nobody sees it).
- **Release** = flip the flag to route users to it — gradually, per-segment, instantly reversible.

For the LMS, the `₹5 → ₹6` fine change ships behind a flag: deployed and idle, then enabled for 5%
of members while we watch metrics, then everyone — with a **kill-switch** if fines look wrong. No
redeploy to turn it off.

| Feature-flag service | Note |
|---|---|
| **LaunchDarkly** | managed SaaS; richest targeting/rollout |
| **Unleash** | open-source, self-hostable |
| **AWS AppConfig** | native on AWS; validated config rollout |

Flags are the **mechanism behind progressive delivery** — canary and gradual rollout in `part2-06`
build directly on them. (Keep them short-lived: a flag that outlives its rollout becomes debt —
remove it once the feature is fully on.)

🎯 **Interview flag:** if asked "how do you keep trunk shippable while merging unfinished work?" or
"how do you decouple deploy from release?", the one-word answer is **feature flags** — then name the
kill-switch and the flag-cleanup discipline.

---

## 5. Monorepo vs polyrepo

**Where does the code physically live?**

- **Monorepo** — one repo for many deployables. Atomic cross-cutting changes, one source of truth,
  easy shared code. At Google/Meta scale it needs **Bazel-class** build tooling (Bazel, Buck) for
  fast incremental, cache-aware builds across a huge tree.
- **Polyrepo** — one repo per service. Clean ownership boundaries and independent CI, at the cost of
  cross-repo coordination for shared changes.

> **What to opt for:** the LMS is a **single vertical-slice modular monolith** — it's **one repo**
> either way, and the question barely arises. Don't reach for Bazel-class tooling: that's a
> monorepo-at-scale answer (thousands of engineers, hundreds of services). For us, plain
> GitHub + a single `pyproject.toml` build is correct. Revisit only if the monolith is ever split
> into services (see `appendix-modular-monolith-to-microservices`).

---

## 6. The two-cloud lens — CODE stage

| Concern | Private cloud (Kubernetes) | Public cloud (AWS) |
|---|---|---|
| **Repo hosting** | self-hosted GitLab / GitHub Enterprise | AWS CodeCommit or GitHub |
| **Branch protection / required checks** | GitLab/GitHub rules; CI must pass | same (GitHub) or CodeCommit + CodePipeline approvals |
| **Signed commits** | GPG/SSH keys, org-enforced | same; keys in AWS-managed identities |
| **Feature-flag service** | Unleash (self-hosted) | LaunchDarkly or **AWS AppConfig** |

The Git workflow is **identical** on both clouds — CODE is the stage that varies *least* between
private and public. What changes downstream is where the image is built and how it's deployed, not
how source is branched.

> **What to opt for:** on private K8s, **self-hosted GitLab + Unleash** keeps everything in your
> trust boundary; all-in on AWS, **GitHub + AWS AppConfig** (or LaunchDarkly) is the least-friction
> path. Either way the branching model — trunk-based — stays the same.

---

## Key takeaways

1. **Git is the source of truth** — including the LMS's now-config business policy (fine rate,
   borrow limit), versioned and reviewed like code.
2. **Trunk-based + short-lived branches + feature flags** for continuous delivery; **GitFlow only**
   for versioned/on-prem software shipped on a cadence.
3. **`main` always releasable** is *enforced* — PR review, required checks, signed commits — not
   requested politely.
4. **Feature flags are the mechanism behind "deploy ≠ release"** and the foundation for canary/
   progressive delivery in `part2-06`.
5. **Monorepo vs polyrepo doesn't bite us** — the modular monolith is one repo; Bazel-class tooling
   is a Google/Meta-scale answer, not ours.
6. **CODE varies least across clouds** — same Git workflow on K8s and AWS; only the host and
   flag-service names change.

---

*Next — `part2-02-build`: the BUILD stage — 12-factor app-readiness, the CI engine, and turning a
commit into one immutable, SHA-tagged image.*
