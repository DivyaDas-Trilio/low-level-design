# Appendix — Strategic DDD: Domain, Subdomain, Bounded Context, Context Map

*The macro half of DDD — how to carve a system into the right boundaries before you write a single class. Tactical DDD (entities/VOs/aggregates) builds the model **inside** one boundary; strategic DDD decides **what** the boundaries are.*

The one mental model to hold throughout:

> **Domain & Subdomain = the *problem* space** (the business — *discovered*).
> **Bounded Context = the *solution* space** (how you model it in software — *designed*).
> **Context Map = how the contexts relate.**

---

## 1. Domain
**Definition:** the entire subject area / business your software serves — the *problem space as a whole*.

- It's the **why** — the business, not the software. You don't *build* a domain; you build software *for* one.
- The outermost box; everything else is a slice of it.

**Examples:** LMS → "running a library." E-commerce → "selling products online."

---

## 2. Subdomain
**Definition:** a distinct sub-area *within* the domain. Domains decompose into subdomains, which exist in the *business* whether or not you write software.

**The three types — the point of the concept (they tell you where to invest):**

| Type | Meaning | Effort |
|---|---|---|
| **Core** | your competitive advantage; the hard, valuable part | model richly (tactical DDD) |
| **Supporting** | necessary but not differentiating; custom but simple | keep boring (CRUD) |
| **Generic** | a solved problem | buy / use off-the-shelf |

- **"Core" is company-specific.** Payments is *generic* for a shop (use Stripe) but *core* for a bank/Stripe itself.

**Examples:** LMS → Lending (core), Catalog/Membership (supporting), Notifications (generic).

---

## 3. Bounded Context
**Definition:** an explicit boundary within which **one model and one ubiquitous language are consistent and unambiguous**. The *solution space*.

- Defining idea: **the same word means different things in different contexts**; a bounded context is where a term has *one* precise meaning.
- It prevents the **god-model** — one giant class trying to be everything to everyone.
- Ideally each context has its **own model, language, data, and team**.

**Subdomain vs Bounded Context:**
- Subdomain = problem-space slice (*what the business does*) — discovered.
- Bounded Context = solution-space boundary (*how you model it*) — designed.
- **Aim for 1:1** (one context per subdomain); a legacy monolith cramming many subdomains into one context is a smell (the "big ball of mud").

**Example:** LMS → **one** Library context (deliberate, at ~100-member scale); the 5 subdomains are internal modules.

---

## 4. Context Map
**Definition:** the diagram/document showing **all bounded contexts and the relationships between them** — both *technical* (integration) and *organizational* (team dynamics).

- Each interacting pair gets a **named integration pattern** + a direction.
- **Direction — Upstream (U) → Downstream (D):** the upstream context provides/influences; the downstream consumes and must adapt. Changes flow *downhill*. (Some relationships are peer/symmetric instead.)

### Upstream / Downstream — the direction concept (in depth)

Borrowed from a **river** — it's about *influence/dependency*, not (necessarily) data-flow direction.

```
      UPSTREAM  ────────────►  DOWNSTREAM
   (source of the water)      (receives the water)
```
Whatever happens **upstream flows down**; **downstream cannot affect upstream** (pollute the river upstream and everyone below suffers — nothing below changes the water above).

> **Upstream** = provides / influences (a model, data, an API), changes on its own terms. **Downstream** = depends on / consumes it, and must **adapt** when upstream changes.

The essence is an **asymmetry of influence**: upstream changes → downstream must react; downstream changes → upstream is unaffected. **Upstream holds the power; downstream carries the risk.**

**Test to find the direction:** *"If A changes, must B adapt — but not the reverse?"* → then **A is upstream, B is downstream.** (It's about *who is forced to adapt to whom* — usually, but not always, matching data flow.)

**Examples:**
| Upstream | Downstream | Why |
|---|---|---|
| Stripe (payment provider) | your Ordering context | Stripe changes its API → *you* adapt; you can't make Stripe change |
| Catalog | Ordering | Catalog defines products; Ordering consumes them by ID |
| Identity | everyone | Identity owns auth; consumers conform to its tokens/API |

**Why direction decides the pattern** — the downstream's options depend on its power relative to upstream:

| Downstream's situation | Pattern |
|---|---|
| No power; upstream won't change (external vendor) | **Conformist** (accept) or **Anti-Corruption Layer** (translate & protect) |
| Some negotiating power (cooperative same-company team) | **Customer/Supplier** |
| Upstream wants to serve many consumers well | **Open Host Service + Published Language** |

So "which pattern?" always starts with "**who's upstream?**" — the direction sets the power dynamic, and the power dynamic picks the integration style. **Peer** relationships (Partnership, Shared Kernel) have *no* up/down — both sides influence each other.

### The named relationship patterns

**Upstream–Downstream (directional):**
| Name | What it means | Downstream's stance |
|---|---|---|
| **Customer/Supplier** | D depends on U, but D has **negotiating power**; U agrees to consider D's needs | collaborative |
| **Conformist** | D **adopts U's model as-is** — no translation, no say | surrender (U holds the power) |
| **Anti-Corruption Layer (ACL)** | D **translates** U's model into its own — protects itself from U's mess | defensive |
| **Open Host Service (OHS)** | U exposes a **clean public API** for many consumers | U as a good provider |
| **Published Language** | U publishes a **formal shared schema** (often with OHS) — OpenAPI, event spec | the contract they integrate on |

**Peer / symmetric:**
| Name | What it means |
|---|---|
| **Partnership** | two contexts/teams **succeed or fail together**, coordinate tightly, mutual dependency |
| **Shared Kernel** | two contexts **co-own a small shared subset** of the model (couples them — use sparingly) |

**No integration:**
| Name | What it means |
|---|---|
| **Separate Ways** | deliberately **don't integrate** — duplicate the little you need (integration cost > value) |

**Anti-pattern (a label you put *on* the map):**
| Name | What it means |
|---|---|
| **Big Ball of Mud** | a region with no clear boundaries/model — mark it so you *contain* it, don't spread it |

*(These are the same patterns as the brownfield catalog in `appendix-ddd-in-legacy-codebase.md` — integrating with a legacy context is just a special case of context mapping.)*

**Example:** LMS today is trivial (one context, no map). If split later: Lending ← Customer/Supplier ← Catalog (by-ID), Lending → Fines (events), everyone → Notifications (events), and any external provider wrapped in an ACL.

### The patterns in depth — when / how / why / example

**A. Upstream–Downstream family (directional)**

**Customer/Supplier**
- *When:* U–D, **same org**, downstream has *legitimate needs upstream can accommodate*; cooperative, downstream has some power.
- *How:* downstream's requirements enter upstream's backlog; upstream commits to a stable interface; changes negotiated; **downstream's tests guard the contract**.
- *Why:* gives downstream a voice **without merging** contexts.
- *Example:* Ordering (customer) needs a new field from Catalog (supplier); it enters Catalog's backlog; Catalog adds it, API stays stable.

**Conformist**
- *When:* U–D, downstream has **no power**, upstream **won't adapt** — **and** upstream's model is good enough that translating isn't worth it.
- *How:* downstream **adopts upstream's model as-is**, no translation.
- *Why:* cheapest when you can't change upstream and its model is acceptable. *Trade-off:* coupled to upstream's model; its changes ripple in.
- *Example:* using a government tax API's data structures directly.

**Anti-Corruption Layer (ACL)**
- *When:* U–D, can't change upstream, **and** its model is messy/foreign and would corrupt yours.
- *How:* a **translation layer** — adapters convert upstream shapes ↔ your model; your domain never sees upstream concepts.
- *Why:* protects your model's integrity; **isolates upstream changes** to the ACL.
- *Example:* Reservations wrapping legacy `BookManager`; Ordering wrapping Stripe.
- *Conformist vs ACL:* accept (cheap, coupled) vs translate-&-protect (a layer, stays clean).

**Open Host Service (OHS)**
- *When:* an upstream has **many consumers**; per-consumer integration is unsustainable.
- *How:* publish a **stable, general-purpose public API**, versioned + backward-compatible.
- *Why:* one clean interface instead of N bespoke ones; consumers decouple from internals.
- *Example:* an Identity service's public OAuth API; Stripe itself.

**Published Language**
- *When:* parties exchange data in a **shared format** (esp. with OHS / many consumers/orgs).
- *How:* a **formal documented schema** (OpenAPI, protobuf, HL7 FHIR, a canonical event schema); each side translates at its edge.
- *Why:* a stable contract **no context owns internally** — integrate without coupling internal models.
- *Example:* a canonical `OrderPlaced` event schema on the bus.
- *OHS vs Published Language:* the **door** (service/API) vs the **language at the door** (schema) — usually together.

**B. Symmetric family (peers — no up/down)**

**Partnership**
- *When:* two contexts **deeply interdependent** — succeed/fail together; changes usually co-occur.
- *How:* synchronized releases, joint planning, shared integration tests, mutual commitment.
- *Why:* when coupling is genuinely bidirectional, pretending one is upstream fails.
- *Example:* Inventory ↔ Fulfillment. *Watch:* needing it everywhere = boundaries may be wrong.

**Shared Kernel**
- *When:* a shared model subset that's wasteful/error-prone to duplicate; teams can coordinate.
- *How:* a **small, co-owned** shared piece; changes need **both** teams' agreement; keep minimal.
- *Why:* avoids diverging a shared concept — **but couples** the contexts, so keep it tiny.
- *Example:* our `shared/` kernel (IDs + base error).
- *Shared Kernel vs Published Language:* share **code** (tight) vs share a **schema** (loose — prefer this when you can).

**C. No relationship**

**Separate Ways**
- *When:* **no compelling reason to integrate** — cost > value, or needs are independent.
- *How:* deliberately don't integrate; duplicate any small overlap.
- *Why:* integration always costs; if benefit is small, avoiding it is correct.
- *Example:* two departments each tracking "satisfaction" their own way. *"The best integration is sometimes none."*

**D. Anti-pattern**

**Big Ball of Mud**
- *When:* you **identify** (not choose) a boundary-less, tangled region.
- *How:* mark it; **draw a boundary (usually an ACL)** so its mess can't spread; plan to strangle it.
- *Why:* naming it lets you **contain** it and evolve it out.
- *Example:* the legacy monolith — wrap in an ACL, grow clean contexts around it (Strangler Fig).

### Decision guide
```
Two contexts interact?
├─ No / not worth it            → Separate Ways
├─ Mutual & interdependent      → Partnership (peers)
├─ Share a small model          → Shared Kernel (co-own, tiny)  [prefer Published Language]
└─ One depends on the other (U→D):
     Can I (downstream) influence upstream?
     ├─ Yes (same org, cooperative)  → Customer/Supplier
     └─ No:
          Upstream's model acceptable to use directly?
          ├─ Yes → Conformist (cheap, coupled)
          └─ No  → Anti-Corruption Layer (translate & protect)
     Am I (upstream) serving many consumers? → Open Host Service + Published Language
     Is the other side a hopeless mess?      → Big Ball of Mud → wrap in ACL, strangle
```
> **Through-line:** direction (U/D) + your **power** + how **messy/shared** the models are pick the pattern. Downstream *with* power → Customer/Supplier; *without* → Conformist (accept) or ACL (protect); upstream serving many → OHS + Published Language; true peers → Partnership or Shared Kernel; not worth it → Separate Ways; a mess → contain as Big Ball of Mud behind an ACL.

---

## How they nest

```
DOMAIN  (the whole business)                                     ← problem space
  └─ SUBDOMAINS  (slices: Core / Supporting / Generic)           ← DISCOVERED
         │  ideally aligned 1:1 with ↓
  └─ BOUNDED CONTEXTS  (model + language boundaries in software) ← DESIGNED / solution space
         └─ CONTEXT MAP  (how contexts relate: ACL, OHS, events, Partnership…)
```

The trap all four guard against: a **single monolithic model** trying to mean everything to everyone. Subdomains find the seams; bounded contexts enforce them; the context map governs traffic across them.

---

## How to find bounded contexts (solution space) *from* subdomains (problem space)

Subdomains don't automatically become contexts — they're the **first-cut hypothesis** you then refine with signals.

### The method
1. **Start with subdomains** — assume one context per subdomain (the draft).
2. **The linguistic test (primary signal):** *where does a term's meaning change?* Same word → different meaning = **different contexts**.
   - Same word, different meaning (polyseme) → **split**.
   - Different words, same concept (synonyms) → a boundary needing **translation**.
3. **Event Storming:** map domain events on a timeline, add commands/actors/aggregates, **cluster** them; clusters = candidate contexts; **pivotal events/handoffs** = seams.
4. **Cohesion & coupling:** concepts that change together, reference each other, share invariants → same context; a chunk with a different model/lifecycle → its own context.
5. **Teams (Conway's Law):** align contexts with **team ownership**; a model two teams fight over → split.
6. **Rate-of-change & data ownership:** things that change for the same reason at the same rate belong together; a context owns its data.
7. **Validate** each candidate: one language? one model? one owner? clean, few integration points?
8. **Iterate** — boundaries shift as you learn.

### Signals a boundary is wrong
| Symptom | Meaning | Fix |
|---|---|---|
| God-model; each consumer uses only *some* fields | merged contexts that should split | **split** on the linguistic seam |
| Same term forced to mean two things | boundary runs *through* a concept | **split** |
| Two "contexts" always change together, can't deploy independently | split something cohesive | **merge** / Partnership |
| One model fought over by two teams | boundary ignores org reality | **split** on team lines |

> **Language is the knife.** Aim for one context per subdomain, but let the *ubiquitous language* — not the org chart or a diagram — draw the final line.

---

## Worked example — e-commerce (large online retailer)

**Domain:** selling products online.

### Subdomains (⚠️ "core" is company-specific — assuming logistics/personalization-driven)
| Subdomain | Type |
|---|---|
| Fulfillment / Logistics | 🔴 Core |
| Recommendations / Personalization | 🔴 Core |
| Pricing / Promotions | 🟡 Supporting (or core) |
| Catalog, Inventory, Cart, Ordering, Shipping, Reviews, Search | 🟡 Supporting |
| Payments, Identity, Notifications, Tax, Carrier integration | 🟢 Generic |

### Bounded contexts (mostly 1:1, cut where language changes)
Catalog · Inventory · Pricing · Cart · Ordering/Checkout · Payment · Fulfillment · Shipping · Recommendations · Reviews · Search · Identity · Notification.

**Divergences from 1:1:** the *Ordering* subdomain often splits into **Cart + Checkout + Order** contexts; *Fulfillment* may span **Fulfillment + Shipping**. Not always 1:1 — cut on language.

### The payoff — same word, different model

**"Product":**
| Context | means |
|---|---|
| Catalog | title, description, images, category |
| Inventory | SKU, stock count, warehouse location |
| Pricing | cost, margin, discount eligibility |
| Shipping | weight, dimensions, fragile/hazardous |
| Recommendations | a feature vector / "also bought" |

**"Order":**
| Context | means |
|---|---|
| Ordering | line items, totals, status |
| Payment | an amount to charge + transaction |
| Fulfillment | a pick-list for the warehouse |
| Shipping | a parcel with address + tracking number |

Forcing one universal `Product`/`Order` class is the god-model. Each context keeps its own small model; they reference each other **by ID** (`product_id`, `order_id`).

### Context map
```
Catalog ──(U)──► Cart ──► Ordering ──┬─ACL─► Payment ─ACL─► [Stripe]
Inventory ──(U)──► Ordering          ├──────► Fulfillment ──► Shipping ─ACL─► [Carriers]
Pricing ──(U)──► Cart/Ordering       └─events─► Notification
Identity ──OHS + Published Language──► everyone
Ordering ──events──► Recommendations
```
Ordering is downstream of Catalog/Inventory/Pricing; external Payment/Carriers are wrapped in **anti-corruption layers**; Identity is an **Open Host Service**; events fan out (async) to Recommendations/Notification.

---

## How the LMS applies this
- **Domain:** running a library.
- **Subdomains:** Lending (core), Catalog & Membership (supporting), Fines (supporting), Notifications (generic).
- **Bounded context:** **one** (Library) — the linguistic test found *no* meaning-shift (Book/Member/Loan mean one thing throughout), one team, small scale → splitting would add cost for no benefit. The subdomains are internal modules **and** the future split seams.
- **Context map:** trivial today; would materialize (ACL/events between Lending/Catalog/Fines/Notifications) only on a microservice split.

> **One-liner:** **Domain** = the business; **Subdomains** = its slices tagged core/supporting/generic (where to invest) — *discovered*; **Bounded Contexts** = software boundaries where *one language* holds, cut **where a term's meaning changes** — *designed*, aim 1:1 with subdomains; **Context Map** = how the contexts integrate (ACL/OHS/events/Partnership…). Find contexts by starting from subdomains and cutting on **language**, confirmed by event clustering, cohesion, teams, and rate-of-change.

*Related: `appendix-lld-techniques-map.md` (where strategic DDD sits in the toolbox), `appendix-modular-monolith-to-microservices.md` (contexts as service seams), `appendix-ddd-in-legacy-codebase.md` (context-mapping applied to legacy).*
