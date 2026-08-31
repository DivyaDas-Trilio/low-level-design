# Appendix — LLD Techniques, Grouped by the Problem They Solve

*A map of the whole toolbox. LLD design isn't one list of principles — it's several bodies of knowledge (DDD, SOLID, GRASP, GoF patterns, general principles) that you reach for **when a specific problem appears**. Grouping by problem is how to hold them.*

---

## What DDD is

**Domain-Driven Design** = design the software around the *business domain* and its language, so the model directly expresses the rules of the problem. Two halves:

- **Strategic DDD** — the big picture: ubiquitous language, bounded contexts, subdomains, context mapping.
- **Tactical DDD** — the building blocks inside a context: entities, value objects, aggregates, domain services, repositories, factories, domain events.

## It's several toolkits, not one list

| Body | Rough size | What it gives you |
|---|---|---|
| **DDD** (strategic + tactical) | ~8 strategic + ~7 tactical building blocks | how to *model* the domain |
| **SOLID** | 5 principles | how to structure classes for change |
| **GRASP** | 9 principles | how to *assign responsibility* |
| **GoF patterns** | 23 patterns | reusable solutions to recurring designs |
| **General principles** | KISS, YAGNI, DRY, CQS, Tell-Don't-Ask, composition-over-inheritance | restraint + everyday discipline |

There is no single count — it's a *toolbox of toolboxes*. Which is why we group by problem.

---

## The grouping — techniques by the problem they solve

### 1. Discovering & naming the model
*Problem: turn vague requirements into concepts everyone agrees on.*
→ Ubiquitous Language · Bounded Contexts · Subdomains (core / supporting / generic) · Context Mapping. *(strategic DDD)*

### 2. Classifying the building blocks
*Problem: what KIND of thing is each concept?*
→ **Entity vs Value Object** · **Aggregate + Aggregate Root** · Domain Service vs Application Service · Repository. *(tactical DDD)*

### 3. Protecting correctness (invariants)
*Problem: prevent invalid state from ever existing.*
→ Make illegal states unrepresentable · enforce invariants in constructors / guarded methods · VO immutability + self-validation · Encapsulation (private state) · Aggregate as consistency boundary · Fail-fast · named domain exceptions.

### 4. Placing behavior & responsibility
*Problem: which object does what? Avoid anemic data-bags AND god objects.*
→ GRASP (**Information Expert**, Creator, Controller, **High Cohesion**, **Low Coupling**) · **Tell-Don't-Ask** · Rich domain model · **SRP** · **CQS** (command/query separation).

### 5. Absorbing change / extensibility
*Problem: add or swap behavior without editing stable code.*
→ **OCP / LSP / DIP** · **Strategy** (swappable policy) · **State** · **Factory** (creation-with-rules) · Observer / **Domain Events** · **Ports & Adapters** · Dependency Injection.

### 6. Managing dependencies & structure
*Problem: keep coupling low and the codebase navigable.*
→ Layered architecture (domain / application / infrastructure / api) · **Dependency Inversion** (arrows point inward) · **reference other aggregates by ID** · ISP · package-by-subdomain (vertical slices) · hexagonal / clean architecture.

### 7. Concurrency & consistency at scale
*Problem: stay correct under simultaneous access / distribution.*
→ Aggregate as the **unit of concurrency** · **small aggregates** (less contention) · optimistic / pessimistic locking (in infrastructure) · eventual consistency / **sagas** · domain events.

### 8. Restraint / not over-engineering
*Problem: complexity for its own sake.*
→ **KISS · YAGNI · DRY** · composition over inheritance · *"patterns only when a real problem demands them."*

---

## How this maps to the LMS build

| Problem group | What we did |
|---|---|
| 1 Discover | Book vs BookCopy language; five subdomains |
| 2 Classify | `Money`/`ISBN` = VO; `Loan` = entity; 5 aggregates |
| 3 Correctness | `Money` rejects negatives; `Fine` settle-once; private `_status` |
| 4 Responsibility | `Member` has no `can_borrow` (Information Expert); CQS on every method |
| 5 Change | `FineCalculationStrategy`; `Loan.create` factory; ports |
| 6 Dependencies | vertical slices; by-ID references; tiny `shared/` kernel |
| 7 Concurrency | small aggregates; optimistic locking for `borrow` |
| 8 Restraint | `BookCopy` = transition table (not State pattern); no premature microservices |

---

## Not every problem needs DDD — match the approach to the problem *type*

DDD is **not universal.** It targets one class of problem (complex business rules) and is over-engineering elsewhere. You categorize each **part** of a system by the *kind* of problem it is, and pick the technique that fits:

| Problem type | Technique | Exact name |
|---|---|---|
| **Business-heavy** (complex, evolving rules) | rich OO domain model | **Domain Model** pattern → this is what **DDD** builds |
| **Simple CRUD** (object ≈ table, little behavior) | procedural per use-case, or object-persists-itself | **Transaction Script** / **Active Record** (framework/ORM-supported) |
| **Algorithm-heavy** | data structures + algorithms, plain functions | **DS&A** + **procedural/functional design** (Big-O thinking, not domain modeling) |

### Fowler's domain-logic spectrum

Martin Fowler (*Patterns of Enterprise Application Architecture*) names this exactly — organize domain logic by its *complexity*:

```
simple logic ───────────────────────────► complex logic
Transaction Script  →  Table Module  →  Domain Model (DDD)
```

- **Transaction Script** — one procedure per operation; simple, no rich model. Good for CRUD / simple logic.
- **Table Module** — one class per table.
- **Domain Model** — rich OO model with entities/aggregates/invariants. Good for complex logic. ← **DDD**

**Fowler's guidance (and ours):** use the **simplest** pattern the logic allows; reach for **Domain Model / DDD only when complexity justifies its cost.**

### You categorize *parts*, not whole systems

Real systems are mixtures — apply a different pattern per part:

- **Lending** (LMS core) = business-heavy → **Domain Model / DDD** (aggregates, invariants, Strategy/State).
- **Catalog / Membership** = supporting, near-CRUD → deliberately **lightweight** (Transaction-Script/Active-Record-ish).
- A hypothetical **recommendation engine** = algorithm-heavy → **DS&A**, not domain modeling.

One system can run all three at once, each where it fits — which is why our supporting subdomains stay "boringly simple" while the core is richly modeled.

> **The key correction to "just layer DDD onto everything":** there is **no universal method.** Diagnose the problem *type* first, then pick the matching approach — **Domain Model (DDD)** for complex domains, **Transaction Script / Active Record** for CRUD, **DS&A** for algorithms. Knowing when *not* to use DDD is as much design maturity as knowing how.

---

## Applying DDD to a feature in an *existing* product

Features (not greenfield) are the normal case, and DDD applies — but *how* depends on the **feature's size** and the **health of the existing codebase**.

### Scale DDD to the feature

| Feature | Approach |
|---|---|
| **Small** (a field, a CRUD screen, a flag) | **Don't force DDD** — extend the existing entity / add the column. Full tactical DDD here is over-engineering (KISS/YAGNI). |
| **Large** (a new capability with real rules — "reservations", "tiers") | **Run the mini DDD loop:** language → classify (entity/VO) → invariants → aggregate → responsibilities → code. Likely a **new aggregate**, maybe a **new subdomain/bounded context**. |

Reflex: *is the feature's hard part behavior/rules?* → DDD. *Just data/CRUD?* → Transaction Script / add-a-field.

### It depends on the existing codebase's health

- **Already DDD / clean-layered** → the feature **slots in**: a new aggregate + repository, referenced **by ID**, no cross-boundary reach-ins. New features are *additions*, not surgery.
- **Legacy / anemic / big ball of mud** → you can't do clean DDD in isolation (the mess leaks in). Use **context-mapping integration tactics**:
  - **Bubble Context** — a small *clean* DDD context for the new feature, insulated from the legacy model.
  - **Anti-Corruption Layer (ACL)** — a translation layer so the legacy model can't corrupt your new one.
  - **Strangler Fig** — grow the clean part and gradually replace the old around it.

### Decide first: existing context, or new one?

- **Small feature** → usually extends an **existing aggregate/context** (respect its boundaries + language).
- **Large feature** → if it speaks a genuinely different language / has its own rules, give it its **own bounded context** (new module), integrated via ACL/events — don't jam it into an existing aggregate and bloat it.

### The realistic constraint

You **inherit** the schema, conventions, and model — rarely greenfield purity. So apply DDD **pragmatically**: model the new feature cleanly where it matters, wrap the legacy interface in an ACL, and don't boil the ocean (no whole-product rewrite to ship one feature).

> **One-liner:** DDD applies to features too — **scale it to the feature** (small → extend/CRUD; large → mini DDD loop, maybe a new context) and **adapt to the codebase's health** (clean → slots in as a by-ID module; messy → a *bubble context* behind an *anti-corruption layer*, grown via *strangler fig*). Decide whether it extends an existing context or deserves a new one, and stay pragmatic.

---

## HLD first or LLD first?

Neither strictly first — **they're iterative, but the *first* stroke is a lightweight HLD.**

> Start with a **rough HLD** (just enough to find the boundaries) → go **deep in LLD** → let LLD findings **refine the HLD**. A loop, not one-way.

**Why a thin HLD first:** you can't sensibly design a class model until you know *which component it lives in* and *what talks to it*. HLD sets the components/contexts, communication, data, and boundaries that LLD needs as context. Designing classes before boundaries risks building the right model in the wrong box.

**Why not a *full* HLD first:** that's waterfall. LLD teaches you things that correct the HLD — exactly what happened in this build: step 4 said "Member owns loans," and step 5's detailed modeling **moved** it. Keep the first HLD pass *thin* and expect to revise it.

**The sequence:**
```
1. Requirements & scope       — what it must do, scale, constraints
2. HLD (lightweight)          — components/contexts, communication, data, boundaries
3. LLD (deep, per component)  — entities, aggregates, invariants, patterns
   └─► feeds back & refines HLD when a boundary turns out wrong
4. Iterate 2 ↔ 3 until stable
```

**Scale decides the ratio (diagnosis again):**

| Situation | Where to start |
|---|---|
| Large distributed system (many services, teams, scale) | **HLD-led** — boundaries/communication dominate the risk |
| Single app / one component / **LLD interview** | jump almost straight to **LLD** — HLD is one box |
| This LMS | one-sentence HLD ("one bounded context, modular monolith", step 1) → ~90% of effort in LLD |

**Interview note:** an **HLD interview** ("design Twitter") wants components/APIs/data-stores/scale/trade-offs — barely any classes; an **LLD interview** ("design a parking lot / booking system") wants classes/relationships/patterns/some concurrency and assumes the HLD box is given. Know which you're in.

> **Through-line:** thin HLD to find boundaries → deep LLD to build inside them → loop back when LLD reveals a better boundary. **Strategic DDD (bounded contexts) is the bridge** between HLD and LLD. Never fully finish one before touching the other — design is iterative, and boundaries shifting as you learn is a feature, not a failure.

---

## The mental model

> DDD gives you the *modeling* vocabulary (groups 1–2); SOLID / GRASP / patterns give you the *structuring* tools (groups 4–6); general principles keep you honest (group 8) — and you reach for each **when its specific problem shows up**, never as a checklist. That "problem → technique" reflex *is* design maturity.

## The decision reflex (use this at the desk)

When designing a piece, ask **which problem am I solving right now?**
- *"What kind of thing is this?"* → group 2 (Entity/VO/Aggregate).
- *"How do I stop it going invalid?"* → group 3 (invariants/encapsulation).
- *"Where does this behavior belong?"* → group 4 (Information Expert / Tell-Don't-Ask).
- *"This rule might change."* → group 5 (Strategy / OCP).
- *"These two things are getting tangled."* → group 6 (by-ID / DIP / boundaries).
- *"Two requests could collide."* → group 7 (aggregate + locking).
- *"Am I adding a pattern with no real problem?"* → group 8 (KISS/YAGNI — stop).

Related: [`appendix-modular-monolith-to-microservices.md`](appendix-modular-monolith-to-microservices.md) (groups 6–7 at architecture scale).
