# Designing a Library Management System with Domain-Driven Design

> A from-scratch, step-by-step LLD walkthrough where we apply **DDD, OOP, SOLID, and design patterns** *only where they earn their place* — and write the reasoning down as we go.

This is a learning series. Each step is a self-contained chapter: a little theory (just enough for the step we're on), then we apply it to a real Library Management System and explain *why* every decision was made. The goal is not "a finished app" — it's to show the **thinking** that turns a vague requirements doc into a clean, maintainable design.

## The problem

A single library wants to stop doing everything by hand: checking shelf availability, tracking who has what, knowing what's overdue, and charging late fines. Full requirements live in [`../REQUIREMENTS.md`](../REQUIREMENTS.md). Scale is deliberately modest — ~100 members, ~500 books, one branch, 24/7 uptime.

## The method

We follow a tactical-DDD sequence (adapted from my own LLD notes), with a few refinements folded in:

| Step | Chapter | What we produce |
|---|---|---|
| 0 | [End-to-end flow (primer)](step-00-end-to-end-flow.md) | How one request travels api → application → domain → infrastructure (the picture the rest slots into) |
| 1 | [Discovery & Ubiquitous Language](step-01-discovery-and-ubiquitous-language.md) | Glossary, subdomains, the bounded-context decision |
| 2 | [Use cases & user journeys](step-02-use-cases-and-user-journeys.md) | Prioritized use cases, actor journeys |
| 3 | [Entities & Value Objects](step-03-entities-and-value-objects.md) | Concept classification |
| 4 | [Invariants](step-04-invariants.md) | The rules the model must never break |
| 5 | [Aggregates & roots](step-05-aggregates-and-aggregate-roots.md) | Consistency boundaries |
| 6 | [Relationships among aggregates](step-06-relationships-among-aggregates.md) | Reference-by-ID rules |
| 7 | [Aggregate responsibilities](step-07-aggregate-responsibilities.md) | What each root owns |
| 8a | [Domain classes: value objects, IDs & exceptions](step-08a-domain-classes-value-objects.md) | Code: the immutable foundation |
| 8b | [Domain classes: aggregate roots & patterns](step-08b-domain-classes-aggregate-roots-and-patterns.md) | Code: entities + Strategy + State |
| 9 | [Domain & Application services](step-09-domain-and-application-services.md) | Orchestration vs cross-aggregate logic |
| 10 | [Repositories](step-10-repositories.md) | Persistence-ignorant ports |
| 11 | [Controllers / API](step-11-controllers-and-api.md) | Thin FastAPI layer |
| 12 | [Artifacts (finale)](step-12-artifacts.md) | Class / ER / activity diagrams, directory structure, retrospective |

Design patterns (Strategy, State, Factory, Observer, …) appear **inside the steps where a real design problem demands them** — never for their own sake. SOLID is a constant background check.

### Part II — From Code to Production (delivery)

Same app, taken from laptop to live — reorganized around the **pipeline every change travels**:
`CODE → BUILD → TEST → PACKAGE → DEPLOY → OBSERVE`. Each doc asks: *what are the real ways to do
this stage, how does it differ on a private Kubernetes cluster vs on AWS, and — given a scenario —
what do you opt for?*

| Doc | Stage | Theme |
|---|---|---|
| [Overview](part2-00-overview.md) | — | Promises · the 6-stage pipeline · deploy≠release · the K8s-vs-AWS lens |
| [CODE](part2-01-code.md) | CODE | Version control, trunk-based vs GitFlow, monorepo, feature flags |
| [BUILD](part2-02-build.md) | BUILD | 12-factor app-readiness + CI + multi-stage image build |
| [TEST](part2-03-test.md) | TEST | The test pyramid + the scans that gate a merge |
| [PACKAGE](part2-04-package.md) | PACKAGE | Registry, immutable SHA tags, signing & scanning |
| [DEPLOY](part2-05-deploy.md) | DEPLOY | Push vs GitOps · runtimes (K8s/ECS/Lambda) · environments · the database |
| [Release strategies](part2-06-release-strategies.md) | DEPLOY (release) | Rolling / blue-green / canary / feature flags |
| [OBSERVE](part2-07-observe.md) | OBSERVE | Logs, metrics, traces, SLOs, and the auto-rollback feedback loop |
| [Scenarios & decisions](part2-08-scenarios-and-decisions.md) | all | Scenario cheat-sheet + security/day-2 + interview Q&A |

Two interactive companions accompany Part II: **The Delivery Line** (the flow) and **Ways to Production** (the decision-map).

**Appendix:** [Delivering an on-prem product to multiple private-cloud distros](appendix-on-prem-multi-distro-delivery.md) — when *customers* install your product into heterogeneous OpenStack clouds (Canonical / Red Hat / Kolla) you don't control. A compact companion to Part II.

## Guiding principles

- **Ubiquitous Language first.** Code uses the words the business uses.
- **Model on paper before code.** The expensive mistakes are modeling mistakes.
- **Patterns are a response to a problem, not a starting point.** YAGNI and KISS win by default.
- **Match the design to the scale.** No microservices for a 100-member library.

## Terminology: domain vs domain model vs domain layer

"Domain" is an overloaded word — and these three are *not* the same thing. Keeping them straight prevents a lot of confusion:

| Term | What it actually is | LMS example |
|---|---|---|
| **Domain** | The real-world **problem / subject area** the software is about. A concept, not code. | "Running a library — lending books to members." |
| **Subdomain** | A slice of that domain. | Lending, Catalog, Fines, Membership. |
| **Domain Model** | The **code representation** of the domain, built *from* entities, value objects, aggregates, domain services, and domain events. | `Book`, `Member`, `Loan` (entities) + `ISBN`, `Money` (value objects) + the rules connecting them. |
| **Domain Layer** | The **architectural layer** that holds the domain model (separate from application / infrastructure / API). | The `domain/` package — pure Python, zero framework imports. |

> **So entities + value objects don't *make* a domain — they're the building blocks you use to *model* one.** A domain *model* is built from entities, value objects, **aggregates, domain services, and domain events** — not just the first two.
>
> One-line hook: **Domain** = the problem · **Domain model** = the objects you build to capture it · **Domain layer** = where that model lives in code.

**Layman's intuition — think of cooking 🍳:**
> - **Domain** = *"Italian cooking"* — the whole subject. An idea you can't touch.
> - **Subdomain** = a slice: pasta, pizza, desserts.
> - **Domain Model** = a specific **recipe** — the ingredients and steps that capture how to make the dish.
> - **Domain Layer** = the **recipe card filed in your recipe box** — where that recipe physically lives, separate from your shopping list and kitchen tools.
>
> Ingredients like flour and eggs are the **entities + value objects** — what the recipe is *built from*. But flour + eggs isn't a recipe, and a recipe isn't "Italian cooking." Saying *"entities + value objects = a domain"* is like saying *"flour + eggs = Italian cooking."* Three different levels: **the thing → a representation of it → where you keep that representation.**

## Tech stack

Python 3, FastAPI + Pydantic for the API layer, pytest for tests. The domain layer stays pure Python with zero framework imports.

---

*Series status: ✅ COMPLETE — Part I (design, Steps 1–12) + Part II (from code to production, `part2-00`…`part2-08`) + on-prem appendix. The LMS was designed with DDD and taken end-to-end to production.*
