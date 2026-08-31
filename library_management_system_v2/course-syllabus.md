# LLD Course — Syllabus (Foundation + Advanced)

Two-tier low-level-design curriculum. Foundation teaches the *tools*; Advanced teaches *judgment, trade-offs, evolution, and scale*. Each module lists **topics + the learning outcome** (doubles as a marketing bullet).

---

# 🎓 Foundation Course — "LLD: Learn the Tools"

**Audience:** college students, 0–2 yrs · **Goal:** go from "I can code" to "I can design a class model." · **~5000 INR**

### Module 0 — How to Think About Design *(orientation)*
- What LLD is, why it matters, LLD in interviews.
- **Outcome:** understand the map of the course and what "good design" means.

### Module 1 — OOP Fundamentals
- Encapsulation, abstraction, inheritance, polymorphism.
- **Composition over inheritance**; interfaces vs abstract classes.
- **Outcome:** model real things as classes with the right relationships.

### Module 2 — Design Principles
- **SOLID** (5) with before/after code.
- **GRASP** (Information Expert, Creator, Controller, High Cohesion, Low Coupling) — *responsibility assignment*.
- **KISS · DRY · YAGNI · CQS · Law of Demeter.**
- **Outcome:** judge whether a class is well-formed and place responsibility correctly.

### Module 3 — UML & Diagramming
- Class, sequence, use-case diagrams; reading & drawing them.
- **Outcome:** communicate a design visually (interview-critical).

### Module 4 — Design Patterns
- **Creational** (Factory, Builder, Singleton), **Structural** (Adapter, Decorator, Composite, Facade), **Behavioural** (Strategy, State, Observer, Template).
- Each taught as "the problem it solves," not memorization.
- **Outcome:** recognize the recurring problem and apply the right pattern.

### Module 5 — Concurrency Basics
- Threads, locks, race conditions, thread-safety, immutability.
- **Outcome:** spot and fix a basic race condition.

### Module 6 — How to Approach an LLD Problem *(the method)*
- Requirements → identify entities/value objects → responsibilities → classes → refine.
- **Outcome:** a repeatable process for any "design X" prompt.

### Module 7 — Design Approaches by Problem Type
- **Business-heavy → Domain Model (intro to DDD):** entities, value objects, basic aggregates.
- **Simple CRUD → Data-Centric:** Transaction Script / Active Record.
- **Algorithm-heavy → Procedural / DS&A.**
- **Fowler's spectrum** — pick the simplest that fits.
- **Outcome:** choose the *right approach* for the problem, not one-size-fits-all.

### Module 8 — Projects (one per approach)
- **8.1 Library Management System** → Domain Model (DDD).
- **8.2 CRUD app** (URL shortener / blog admin) → data-centric.
- **8.3 Rate limiter / parking lot** → procedural / DS&A.
- **Outcome:** built one system in each style — the thesis *felt*, not just heard.

---

# 🚀 Advanced Course — "LLD Mastery: Trade-offs, Scale & Evolution"

**Audience:** 7–8 yrs · **Goal:** from "I know the patterns" to "I make and defend architectural decisions." · **Prereq:** Foundation-level fluency assumed — no re-teaching OOP/SOLID. · **Price meaningfully higher.**

### Module 1 — Strategic DDD
- Bounded contexts, **context mapping**, subdomain distillation (core/supporting/generic), ubiquitous language at scale, anti-corruption layers.
- **Outcome:** carve a large domain into contexts and defend the boundaries.

### Module 2 — Advanced Tactical DDD
- Aggregate **design trade-offs** (sizing, consistency boundaries), domain events, eventual consistency, **CQRS**, **Event Sourcing** — and when each is *overkill*.
- **Outcome:** design aggregates and choose event-driven modeling deliberately.

### Module 3 — Architecture Styles
- Layered vs **Hexagonal / Clean / Onion**; ports & adapters; dependency direction as a design lever.
- **Outcome:** structure a system for testability and framework independence.

### Module 4 — Modular Monolith → Microservices *(flagship)*
- Vertical slices, tiny shared kernel, **reference-by-ID**, split-readiness; **north-south vs east-west**; database-per-service; **sagas**; what to share (kernel vs contracts vs libraries).
- **Outcome:** design a monolith that splits into services with *minimum* change — and know when *not* to split.

### Module 5 — Distributed Systems for Designers
- Consistency models, **idempotency**, the fallacies of distributed computing; resilience: **circuit breaker, bulkhead, retry/backoff, timeouts.**
- **Outcome:** design across a network without building a distributed monolith.

### Module 6 — Advanced Concurrency
- Optimistic vs pessimistic locking, **where the guard belongs** (entity vs service vs infra), shared-resource contention, actor model, lock-free basics.
- **Outcome:** guarantee correctness under concurrency across processes.

### Module 7 — API & Contract Design
- Versioning, **backward compatibility**, REST vs gRPC vs events, contract evolution.
- **Outcome:** design contracts that evolve without breaking consumers.

### Module 8 — Trade-off Analysis & Decision-Making *(the meta-skill)*
- **Architecture Decision Records (ADRs)**, evaluating options against quality attributes, **the cost of abstraction**, when a pattern/DDD is over-engineering.
- **Outcome:** make, document, and defend a design decision.

### Module 9 — Refactoring & Legacy Evolution
- **Strangler fig**, anti-corruption layer, incremental migration, **anemic → rich model**, breaking a big ball of mud.
- **Outcome:** improve a production system safely, in steps.

### Module 10 — Testing Strategy at Scale
- Test pyramid, **contract testing**, testing across service boundaries, TDD on real systems, test doubles (fakes vs mocks).
- **Outcome:** a testing strategy that scales with the architecture.

### Module 11 — Production Readiness & Observability
- 12-factor, logging/metrics/**tracing + correlation IDs**, config/secrets, health checks.
- **Outcome:** design systems that are operable and debuggable in production.

### Module 12 — Design Leadership
- Running **design reviews**, critiquing others' designs, communicating trade-offs to stakeholders, writing design docs, mentoring.
- **Outcome:** lead design, not just do it.

### Module 13 — Capstone (evolution, not greenfield)
- **13.1 Grow the LMS:** monolith → modular monolith → microservices.
- **13.2 Refactor:** legacy anemic / Active-Record codebase → Domain Model.
- **13.3 Design under change:** ship v1, a new requirement forces a redesign — graded on *adaptation*.
- **Outcome:** evolve real systems under changing requirements.

---

## Positioning notes

1. **Clean seam between the courses:** Foundation ends at "intro to DDD + pick an approach"; Advanced *starts* at strategic DDD and never re-teaches basics. No overlap, clear upgrade path.
2. **Pedagogy differs by tier:** Foundation = lecture + build. Advanced = critique-3-designs, refactoring exercises, ambiguous open-ended prompts, evolution projects. Seniors pay for *judgment*, not syllabus.
3. **Reusable assets already written:**
   - `docs/appendix-modular-monolith-to-microservices.md` → Advanced Module 4.
   - `docs/appendix-lld-techniques-map.md` → Advanced Modules 1 & 8 (and Foundation Module 7).
   - The LMS build (`docs/step-01..12`, `src/`) → Foundation Project 8.1 + Advanced Capstone 13.1.

## Possible follow-ups
- Per-module hour/duration estimates.
- Foundation-vs-Advanced comparison table for the landing page.
- A one-paragraph course hook per tier.
