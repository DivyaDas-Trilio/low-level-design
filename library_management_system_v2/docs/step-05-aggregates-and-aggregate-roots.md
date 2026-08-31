# Step 5 — Aggregates & Aggregate Roots

*Series: Designing a Library Management System with DDD · Chapter 5 of 12*

---

This is the chapter most people get wrong, and getting it right is what separates a model that *scales and stays correct* from one that turns into a tangled object soup. In Step 4 we found invariants and noted that some of them **span more than one object**. An **Aggregate** is the answer to the question those spanning invariants raise: *"which objects must change together, as one consistent unit?"*

If you remember one sentence from this whole series, make it this:

> **You don't pick aggregate boundaries by taste — you derive them from your invariants and your concurrency needs.**

---

## 5.1 The concept: aggregate = a consistency boundary

An **Aggregate** is a cluster of entities and value objects that we treat as **a single unit for the purpose of data changes**. It has:

- a boundary (what's inside vs. outside), and
- one **Aggregate Root** — a single entity that is the *only* legal entry point. Everything outside the aggregate may hold a reference to the **root only**, never to its internal members.

Why a single entry point? Because the root is the **guardian of the aggregate's invariants**. If outsiders could reach inside and poke a child object directly, no one could guarantee the rules. By forcing every change through the root, the root gets to enforce consistency on every operation.

**Layman's analogy — an order at a restaurant 🍽️.** An *Order* is an aggregate. It contains *line items* (2 pizzas, 1 coke). You never phone the kitchen and say "change line item #3 directly" — you talk to the *Order* ("add a pizza," "cancel the coke"), and the Order keeps its own total consistent. The line items are protected inside; the Order is the root you talk to. Reaching past the Order to mutate a line item is how totals get corrupted.

---

## 5.1.1 What can live inside an aggregate?

A natural question: is an aggregate always *one* entity, or can it hold several? The answer:

> An aggregate is, in general, **one root entity + zero-or-more child entities + their value objects** — a cluster treated as one unit.

| Composition | Possible? | Example |
|---|---|---|
| One entity alone | ✅ | A `Book` with no children |
| One entity + its VOs | ✅ | `Loan` + its `DateRange`, `LoanStatus` |
| **Multiple entities** + VOs | ✅ | An `Order` (root) + many `OrderLine` child entities, each holding `Money` |
| Another aggregate root pulled *inside* | ❌ | Reference it **by ID** instead (§5.4) |

So yes — an aggregate **can** contain multiple entities plus value objects. But there's a sharp constraint on *which* entities are allowed inside, and it's the most common place people go wrong.

### The trap: "all the entities that touch each other"

In our domain a `Loan` references a `Member` and a `BookCopy`. Does that make all three *one* aggregate? **No.**

> An aggregate isn't "every entity that touches another." It's "the entities a **single invariant** must keep mutually consistent."

`Member` and `BookCopy` each have an **independent lifecycle** and their own invariants → each is its **own** aggregate root. A `Loan` doesn't *contain* them; it references them **by ID** (`member_id`, `copy_id`). So they're **three separate aggregates pointing at each other by ID**, not one big one. The multiple-entities-inside case (like `Order` + `OrderLine`) only happens when the children have **no life of their own** — an order line is meaningless apart from its order, so it lives inside.

### The test for "inside or outside the boundary?"

> **Does this object have a life of its own — its own identity that other parts of the system refer to independently?**
> - **Yes** → it's its own aggregate root. Reference it **by ID**. (Member, BookCopy, Loan, Fine.)
> - **No, it exists only as part of its parent** → it's a child entity *inside* the parent's aggregate. (An `OrderLine` inside an `Order`.)

Notice the consequence for *our* LMS: every lending entity (`Member`, `BookCopy`, `Loan`, `Fine`) has a strong independent life, so each is its **own** small aggregate — we end up with **no multi-entity aggregates at all**. That's not a coincidence; §5.3 derives exactly why, and it's the healthy default. Multi-entity aggregates are the exception you reach for only when a shared invariant forces it.

---

## 5.2 The four rules of aggregate design

These come from Vaughn Vernon (*Implementing DDD*) and they're the practical heart of this step:

1. **Protect true invariants inside one consistency boundary.** If two pieces of data must *always* agree, they belong in the same aggregate, changed in the same transaction.
2. **Design *small* aggregates.** The default mistake is making aggregates too big (e.g., "Library contains all Books contains all Copies contains all Loans"). Big aggregates are slow to load, lock huge swaths of data, and cause contention. Prefer the smallest boundary that still protects a true invariant.
3. **Reference other aggregates by identity (ID), not by object.** A `Loan` holds a `MemberId`, not a `Member` object. (Section 5.4 — the most important mechanical rule.)
4. **One transaction = one aggregate.** A single business operation should modify exactly one aggregate. When a rule spans aggregates, coordinate them with a *domain service* and/or accept *eventual consistency* — don't try to transactionally update many aggregates at once.

Rules 2 and 3 work together: keeping aggregates small *requires* referencing the others by ID instead of swallowing them.

---

## 5.3 Deriving the LMS aggregates (the interesting part)

Let's walk the real reasoning, including a genuine design tension.

### Catalog: are `BookCopy` objects *inside* the `Book` aggregate?

Tempting design: `Book` is the root and **contains** its `BookCopy` children. But apply the rules:

- **Is there a true invariant binding a Book to all its copies transactionally?** Not really. There's no rule like "the book's X must always equal the sum of its copies' Y." A book is just metadata; copies are physical items.
- **Concurrency check:** copies change status *constantly* (every issue/return). If `Book` were the root, issuing one copy would mean loading and locking the *entire* book with *all* its copies — high contention for no benefit.

So by rules 2 + 4, we **split them**:

- **`Book`** — its own small aggregate (catalog metadata).
- **`BookCopy`** — its own small aggregate that references its `Book` **by `BookId`**. It owns its status lifecycle independently.

> This is exactly Vernon's lesson: people *start* by nesting everything, then refactor to small aggregates referencing by ID. We'll just start small.

> #### 📌 Sidebar: what is "high contention"?
>
> **Contention** = multiple operations competing for the same resource at the same time, so they have to wait for one another. *High* contention = lots of competition for one thing = lots of waiting.
>
> **Analogy 🚪:** one bathroom is fine for one person all day (no contention), but the same bathroom shared by 50 people on a coffee break is high contention — a queue forms and everyone waits.
>
> **Why aggregate size drives it:** to change an aggregate, you must lock the *whole* aggregate (that's how consistency is guaranteed). So if `Book` owned all 5 copies of a popular title:
>
> ```
> A borrows copy #1  → locks the entire Book (all 5 copies)
> B borrows copy #3  → must WAIT for A (same Book locked)
> C returns copy #2  → must WAIT too
> ```
>
> Three operations on three *different* physical copies — no real conflict — yet forced to queue on one lock. That's high contention. Split `BookCopy` into its own small aggregate and each copy locks independently:
>
> ```
> A borrows copy #1  → locks only copy #1  ✅
> B borrows copy #3  → locks only copy #3  ✅ runs in parallel
> C returns copy #2  → locks only copy #2  ✅ runs in parallel
> ```
>
> **Rule of thumb:** big aggregates create high contention (unrelated operations fight over one lock); small aggregates reduce it. This is a major reason DDD says *"design small aggregates."*

### Lending: the `Member` ↔ `Loan` tension

Step 4 pinned the *"≤ 2 active loans"* invariant to `Member`. That suggests `Member` should **contain** its loans. But there's a competing pull:

| If loans live *inside* Member (Member is root of both) | If `Loan` is its **own** aggregate (references `MemberId`) |
|---|---|
| ✅ "≤ 2 active loans" is a *true* in-boundary invariant, trivially enforced in `Member.borrow()`. | ✅ Small aggregates; the overdue-loans query (UC-5) reads loans directly without scanning every member. |
| ✅ One transaction updates one aggregate. | ✅ Issuing/returning a loan doesn't lock the whole member record. |
| ❌ Loading a member drags in all their loan history; the overdue query must scan members. | ❌ "≤ 2 active loans" now spans two aggregates — no longer a single-boundary invariant. |

**Our decision: `Loan` is its own aggregate root**, referencing `MemberId` and `CopyId` by ID. We favor small aggregates (rule 2) and the fact that loans have a strong independent lifecycle and are queried on their own (overdue list).

**But that means honestly revisiting Step 4.** With this boundary, *"≤ 2 active loans"* is **not** a single-aggregate invariant anymore — it spans Member and Loans. So its enforcement moves to a **borrowing domain service** (Step 9) that, inside the borrow operation, counts the member's active loans before creating a new `Loan`. At our scale (100 members) a simple transactional count-and-check is perfectly safe.

> **This is real design maturing in front of you.** Step 4's "owner" column was the *first cut*. Learning the small-aggregate rule refined it: the *rule* is still about the member, but its *enforcement* relocated. That's normal and healthy — DDD is iterative, not a straight line.

### Fines

`Fine` has its own lifecycle (unpaid → paid, UC-6) and is referenced individually. **It's its own aggregate root**, referencing the `MemberId` and `LoanId` that produced it by ID.

---

> ## ⚠️ Important note — a spanning invariant does **not** automatically make one aggregate
>
> This is the single most misread step in the chain, so pin it down. The full arc across Steps 3→4→5:
>
> 1. **Invariants live in the object that owns the data — entity *or* value object.** VO-level (`Money ≥ 0`, `ISBN` well-formed) enforced in the VO constructor; entity-level ("issue only if `AVAILABLE`") enforced in the entity's method. Enforced so they're *impossible to break* (constructor / guarded method / remove the illegal operation).
>
> 2. **A single invariant that spans multiple objects signals a *consistency requirement* — not, by itself, a single aggregate.** That's the first-cut instinct from Step 4, and it's only half the story.
>
> 3. **Whether the spanning objects fuse into one aggregate or stay separate is decided by *lifecycle independence* + the *keep-aggregates-small* preference:**
>
> | When the spanning objects… | Result |
> |---|---|
> | have **no life of their own** (child is meaningless apart from parent — `Order` + `OrderLine`) | **one aggregate** — parent is root, child lives inside |
> | each have a **strong independent lifecycle** (queried, referenced, changed on their own) | **separate aggregates** + the rule moves to a **domain service** |
>
> 4. **Our `Member` + `Loan` is the second case — and it's the whole lesson.** Step 4 pinned *"≤ 2 active loans"* to `Member` and it *looked* like Member-contains-Loans. But `Loan` has its own lifecycle and is queried on its own (overdue list), and we prefer small aggregates → `Loan` became its **own** aggregate referencing `MemberId` by ID. The invariant didn't vanish; it **relocated** to the borrowing **domain service** (Step 9) that counts active loans during the borrow.
>
> **The rule to carry forward:** *spanning invariant ≠ guaranteed single aggregate.* It might instead be **separate aggregates + a domain service**. Lifecycle independence and small-aggregate preference make the call — never "they touch, so they merge."

---

## 5.3.1 When invariants *overlap* — how to choose the boundary

A spanning invariant signals a boundary (§5.3) — but what if **two** invariants overlap the same entities and suggest *different* groupings? Say invariant A spans `{X, Y}` and B spans `{Y, Z}`. Aggregates must be **disjoint** (every entity has exactly one home), so you can't put `Y` in two overlapping aggregates. You must arbitrate — and the tool is **consistency strength**.

### Rank each invariant: strong vs eventual

For every invariant ask:

> **"If this rule were violated for a moment, is that a disaster — or acceptable as long as we fix it soon?"**

- **Disaster → strong (transactional) consistency** — must hold at *every* commit.
- **Acceptable-and-reconciled → eventual consistency** — may be briefly false, fixed async.

> **The rule:** only **strong** invariants draw aggregate boundaries. **Eventual** invariants are *allowed* to span aggregates and are enforced **outside** the boundary — by a **domain service** (checked at operation time) or **domain events / a saga** (reconciled after). They do **not** force a merge.

### Resolving the overlap
1. Of the overlapping invariants, **which truly needs strong consistency?** That one wins — `Y` lives in *its* aggregate.
2. The other becomes **eventual** — it spans aggregates, enforced by a service/events. No merge.
3. Usually **only one** of two overlapping invariants is genuinely strong; ask the domain expert — most "must always hold" rules tolerate eventual consistency on inspection.

**E-commerce example:** `order.total == sum(line_items)` (violation = wrong money = **strong**) → Order + LineItems = one aggregate. `qty ≤ stock` (a momentary oversell is **acceptable** → eventual) → Inventory stays its *own* aggregate, enforced by a reservation process. `LineItem` is claimed by the *strong* invariant → it lives in Order; the overlap dissolves because the two invariants had different strength.

**LMS example:** add "member with unpaid fines over ₹X can't borrow" on top of "≤ 2 active loans" — both overlap `Member`. Neither needs *transactional* consistency across aggregates (both are borrow-time policy) → Member, Loan, Fine stay **separate aggregates**, and *both* rules live in the **`BorrowingService`**. Overlapping invariants → enforced in a service, **not** merged.

### If two invariants *both* truly need strong consistency over overlapping sets
Rare. (1) **Challenge it** — re-ask the business; usually one can be eventual. (2) If both are genuinely transactional → the boundary may need the **union** (bigger aggregate) — but that's a *last resort and a smell* (contention, poor scale). (3) Or it's a **modeling problem** — a missing concept, or `Y` is really a shared *value object* copied into both, not a shared entity. **Bias to small aggregates + eventual consistency.**

> **The overlap rule in one line:** overlapping invariants don't mean overlapping aggregates — **rank them by consistency strength, let only the strong (transactional) ones draw boundaries**, give the shared entity to the aggregate whose *strong* invariant needs it, and enforce every *eventual* invariant across aggregates via a domain service or events — never by merging into a mega-aggregate.

---

## 5.3.2 Deriving aggregates from invariants — and what "lifecycle" really means

The procedure, distilled:

1. **Find the spanning invariants.** A single invariant that touches more than one entity marks those entities as aggregate *candidates* — a consistency-boundary is implied there.
2. **Apply the lifecycle test to the entities it spans:**
   - **One of them has no life of its own** → **club them into one aggregate** — a single consistency boundary; changes are **atomic** (all-or-nothing). (`Order` + `OrderLine`.)
   - **Both have independent lifecycles** → **separate aggregates**, referenced **by ID**; the spanning invariant **relocates** to a domain service / events (eventual or operation-time consistency, not one transaction). (`Member` + `Loan`.)

### What "independent lifecycle" actually means (the deciding test)

This is the part people get wrong. **Lifecycle is *not* "does a user interact with it."** It means:

> Does this entity have a **life of its own** — its **own identity**, created / changed / queried / referenced **independently** of the other?

- **Yes, independent existence** → its own aggregate (by ID).
- **No — it only exists as *part of* its parent** (meaningless alone; born and destroyed *with* the parent) → inside the parent's aggregate.

**Two counterexamples that kill the "user interaction" misconception:**
- A user *interacts* with an **`OrderLine`** (adds/removes items), yet it has **no independent lifecycle** — it lives and dies with its `Order` → it goes **inside** the Order aggregate.
- No user directly manipulates a **`Loan`** as a standalone object, yet it **has** an independent lifecycle — created, transitions states, appears in the overdue query, referenced by a `Fine` → it's its **own** aggregate.

So the signal is **independent identity and existence over time** ("is it referenced and managed on its own?") — *not* whether a user clicks on it.

### When lifecycle and a strong invariant collide
A spanning invariant may *want* strong consistency (→ one aggregate) while the entities have independent lifecycles (→ separate). **Lifecycle independence wins → keep them separate**, and *downgrade the invariant to service/eventual enforcement* — exactly the `Member`/`Loan` decision (§5.3). (When *two* invariants conflict, rank by consistency strength — §5.3.1.)

---

## 5.3.3 How a spanning invariant is *implemented* (in code)

A spanning invariant is implemented in **two different places** depending on whether the entities share one aggregate or live in separate ones.

### Case 1 — spans entities *inside one aggregate* → the **root** enforces it

Example: an `Order` (root) + `OrderLine` children, invariant *"total must never exceed a cap"* (and *"total = sum of lines"*).

```python
class OrderLine:                      # CHILD — local identity, lives inside Order
    def __init__(self, line_id: int, product_id, unit_price: Money, qty: int):
        self.id = line_id             # LOCAL id (unique only within this order)
        self.product_id, self.unit_price, self.qty = product_id, unit_price, qty
    @property
    def subtotal(self) -> Money:
        return self.unit_price.multiply(self.qty)

class Order:                          # AGGREGATE ROOT (the parent)
    MAX_TOTAL = Money.rupees(50_000)
    def __init__(self, order_id, customer_id):
        self.id, self.customer_id = order_id, customer_id
        self._lines: list[OrderLine] = []      # children PRIVATE — no outside access

    def add_line(self, product_id, unit_price: Money, qty: int) -> None:
        prospective = self.total.add(unit_price.multiply(qty))
        if prospective.amount > self.MAX_TOTAL.amount:      # ← INVARIANT enforced in the ROOT
            raise OrderTotalExceededError(f"total would exceed {self.MAX_TOTAL}")
        self._lines.append(OrderLine(len(self._lines) + 1, product_id, unit_price, qty))

    @property
    def total(self) -> Money:                              # "total == sum(lines)" TRUE BY CONSTRUCTION
        return sum((ln.subtotal for ln in self._lines), Money(0))
```

The three moves: **(1)** children are **private** (can't be mutated behind the root's back); **(2)** all changes go **through root methods** — the one place the rule is checked, on every mutation; **(3)** *"total = sum(lines)"* is made **unrepresentable-when-wrong** by *deriving* `total` rather than storing it. One aggregate = one consistency boundary → all atomic.

### Case 2 — spans entities in *separate aggregates* → a **domain service** enforces it

Our *"≤ 2 active loans"* spans `Member` + `Loan` (separate aggregates). It can't be a method on either → a stateless domain service, **given** the data:

```python
class BorrowingService:                     # domain service — pure, no state, no repo
    def __init__(self, max_active_loans: int = 2):
        self._max = max_active_loans
    def check_can_borrow(self, member: Member, copy: BookCopy, active_loan_count: int) -> None:
        if not member.is_active:            raise MemberBlockedError(str(member.id))
        if not copy.is_available:           raise CopyNotAvailableError(str(copy.id))
        if active_loan_count >= self._max:  raise BorrowingLimitExceededError(str(member.id))  # ← spanning invariant
```

The application service supplies the count (from a repo) and orchestrates:
```python
active = self._loans.count_active_for_member(member.id)   # data gathered here
self._borrowing.check_can_borrow(member, copy, active)    # spanning invariant checked
```
The service is **handed** the objects + count (holds no repository → pure/testable), and the rule is enforced at **operation time**, not as one atomic transaction over both aggregates.

### The rule
| Invariant spans… | Enforced in… | Why |
|---|---|---|
| entities **inside one aggregate** (root + children) | the **aggregate root's methods** (private children, all changes through the root, derive-don't-store) | one consistency boundary → atomic, immediate |
| entities in **separate aggregates** | a **domain service** (given the data), called by the application service | no single entity has the data; separate boundaries → operation-time / eventual |

> *Where* a spanning invariant is enforced follows directly from *whether the entities share one consistency boundary* — the **root** if they do, a **domain service** if they don't.

---

## 5.4 The cardinal rule: reference other aggregates by ID

This is the rule that, once internalized, makes everything click.

```python
# ❌ Object reference — drags another aggregate inside this one
class Loan:
    def __init__(self, member: Member, copy: BookCopy):
        self.member = member   # now Loan "contains" a whole Member + BookCopy
        self.copy = copy       # huge object graph, unclear boundaries, lock contention

# ✅ Reference by identity — a clean, small boundary
class Loan:
    def __init__(self, loan_id: LoanId, member_id: MemberId, copy_id: CopyId, period: DateRange):
        self.id = loan_id
        self.member_id = member_id   # just an ID — Member lives in its own aggregate
        self.copy_id = copy_id       # just an ID — BookCopy lives in its own aggregate
        self.period = period
        self.status = LoanStatus.ACTIVE
```

**Why by-ID is the right default:**

1. **Small, loadable aggregates.** A `Loan` is tiny — a few ids and a date range. You never accidentally load half the database.
2. **Clear transaction boundaries.** You change one aggregate per transaction; the ids tell you what's *outside* your boundary.
3. **Forces you through repositories.** To act on the member behind `member_id`, you must fetch it via its repository — which keeps the layering honest (Step 10).
4. **Decoupling.** Aggregates can be stored, cached, even moved to separate stores independently. (We won't, at this scale — but the design doesn't fight you if needs change.)

> **Mental test:** if you're holding another aggregate's *object* and calling its methods, you've probably merged two aggregates by accident. Hold the *ID* and look the other one up.

---

## 5.5 The LMS aggregate map

Five small aggregates, all cross-references by ID:

```
┌─────────────┐        ┌──────────────────┐
│   Book      │        │    BookCopy      │
│ (root)      │◄───────│ (root)           │   BookCopy.book_id ──► Book
│ metadata,   │ by id  │ status lifecycle │
│ ISBN (VO)   │        │ CopyStatus (VO)  │
└─────────────┘        └──────────────────┘
                              ▲
                              │ copy_id (by id)
┌─────────────┐        ┌──────────────────┐
│   Member    │◄───────│      Loan        │   Loan.member_id ──► Member
│ (root)      │ by id  │ (root)           │   Loan.copy_id   ──► BookCopy
│ profile     │        │ DateRange (VO)   │
└─────────────┘        │ LoanStatus (VO)  │
       ▲               └──────────────────┘
       │ member_id (by id)
┌──────┴──────┐
│   Fine      │   Fine.member_id ──► Member
│ (root)      │   Fine.loan_id   ──► Loan
│ Money (VO)  │
└─────────────┘
```

| Aggregate (root) | Contains (VOs) | References by ID | Guards |
|---|---|---|---|
| **Book** | `ISBN`, title, author, genre | — | catalog metadata correctness |
| **BookCopy** | `CopyStatus` | `BookId` | I-2/I-7: only `AVAILABLE` copies can be issued |
| **Member** | profile fields | — | member-level state |
| **Loan** | `DateRange`, `LoanStatus` | `MemberId`, `CopyId` | I-3/I-8: due-date set at creation, no double-return |
| **Fine** | `Money`, status | `MemberId`, `LoanId` | I-5: amount never negative |

**Cross-aggregate rules → domain services (Step 9):**
- *"≤ 2 active loans"* (Member + Loan) → **borrowing service**
- *"can this member borrow this copy?"* (Member + BookCopy + Loan) → **borrowing service**

> #### 🧭 Sidebar: is an aggregate a microservice? (No — and why that matters)
>
> A tempting leap once you have five aggregates: *"in microservices, each aggregate becomes its own service, right?"* **No — that's one of the most damaging DDD misconceptions.** An aggregate is far too small to be a service.
>
> The right granularity, largest to smallest:
>
> ```
> Bounded Context   ← a microservice maps here (at most)
>    └── contains several Aggregates
>           └── each contains entities + value objects
> ```
>
> - An **aggregate** is a *consistency boundary* — a few objects that change together in **one transaction**.
> - A **bounded context** is a *meaning boundary* — a whole subdomain with its own ubiquitous language. **That's** the unit a microservice aligns with (at most).
>
> **Why "one aggregate = one service" is a trap.** Make each of our five aggregates its own service and the *borrow* use case (Member + BookCopy + Loan) explodes into **three network round-trips** with failure/retry/latency on each — and what was one local DB transaction now needs a **distributed saga**. Enormous complexity, for ~100 members. You'd have torn apart things designed to change together and maximized coupling *across the network* — the opposite of the goal.
>
> **The useful truth:** aggregates still guide *where* a split is safe. Because they already reference each other **by ID, not by object** (§5.4), the seams between them are clean — so **a service boundary should fall *between* aggregates, never *through* one.** You never split a single aggregate across two services (that puts one transaction across the network). Aggregates are the *grain*; a service cut follows the grain, but each service holds *many* grains.
>
> **For our LMS** (per CLAUDE.md): **one bounded context — the *Library* context — = one deployable** (we chose a modular monolith, not microservices, for this scale). All five aggregates live inside it; the subdomains (Lending, Catalog, Membership, Fines, Notifications) are internal modules. If this ever went distributed, we'd split along **subdomain / bounded-context** lines (a *Lending* service, a *Catalog* service) — each owning **several** aggregates — never one service per aggregate.
>
> **One-liner:** a microservice ≈ a **bounded context** (a subdomain) containing *many* aggregates; an aggregate is a transactional unit — keep it whole inside one service, and let service boundaries fall *between* aggregates.

---

## 5.6 How a borrow flows across small aggregates

Because aggregates are small and referenced by ID, the *borrow* use case becomes a clear choreography (orchestrated by the application service in Step 10, using a domain service for the cross-aggregate rule):

```
borrow(member_id, copy_id):
  member = members.get(member_id)        # load Member aggregate
  copy   = copies.get(copy_id)           # load BookCopy aggregate
  active = loans.count_active(member_id)  # query across Loan aggregate

  # cross-aggregate rule (domain service):
  if active >= 2:            raise BorrowingLimitExceededError
  if not copy.is_available:  raise CopyNotAvailableError

  copy.issue()                            # mutate BookCopy (its own invariant I-2)
  loan = Loan.create(member_id, copy_id)  # create Loan (its own invariant I-3)

  copies.save(copy)                       # persist each aggregate
  loans.save(loan)
```

Notice: each aggregate guards *its own* invariant (`copy.issue()` refuses an unavailable copy; `Loan.create` sets the due date), while the *cross-aggregate* rule lives in the service. Clean separation — and it sets up Steps 9 & 10 precisely.

---

## 5.7 Quick-reference checklist — designing aggregates

Everything in this chapter, distilled to a checklist you can run against any model.

**Deriving the boundary**
1. **Derive boundaries, don't pick by taste** — from invariants + concurrency needs.
2. **A single invariant spanning multiple objects** is the signal a consistency boundary lives there.
3. **Spanning invariant ≠ automatic single aggregate.** Decide by lifecycle: child with *no life of its own* → one aggregate (child inside); each with an *independent lifecycle* → separate aggregates + a **domain service** for the rule.
4. **Inside-or-outside test:** *"Does this object have a life of its own that others reference independently?"* Yes → its own root; No → child inside the parent.

**Structure**
5. **Aggregate = the cluster (boundary); aggregate root = the single entry entity (gatekeeper).** The root is *part of* the aggregate.
6. **Exactly one root per aggregate.** Outsiders reference/call the **root only** — never reach inside to a child.
7. **An aggregate may hold multiple entities + VOs** — but only entities bound by a shared invariant *and* lacking independent identity.

**The four classic rules**
8. **Protect true invariants inside one boundary** — data that must always agree changes together.
9. **Design small aggregates** — default to one entity; add more only when an invariant forces it. Small = fast load, low contention, clear transactions.
10. **Reference other aggregates by ID, never by object** (`Loan` holds `member_id`, not a `Member`).
11. **One transaction = one aggregate.** Cross-aggregate rules → domain service (+ eventual consistency at scale). Know the rule *and its reason* before bending it.

**Invariants & purity**
12. **Invariants live in the owning object — entity *or* VO.** Enforce impossible-to-break: constructor / guarded method / remove the illegal operation.
13. **The root guards the aggregate's invariants** on every operation — that's *why* it's the only entry point.
14. **One repository per aggregate root** (interface in `domain/`, impl in `infrastructure/`); the whole aggregate loads/saves as one unit through the root.
15. **Keep the domain pure** — no repo/DB/cache/framework inside entities; the application service *hands data in*.

**Concurrency (around the aggregate, not inside it)**
16. **The aggregate is the unit of concurrency control** — small boundaries lock independently (low contention).
17. **The entity declares the invariant; it does NOT enforce concurrency.** A service-side check does **0%** of race prevention — both racers pass it.
18. **The race lives at the shared resource** (DB row, file, cache key — not process memory). Enforce there, with that resource's native atomic mechanism.
19. **Prefer: don't-share > atomic operation > explicit lock.** Lock only for multi-step critical sections, keyed per-aggregate (never one global lock).
20. **Division of labor:** entity = *what's* consistent · boundary = *what unit* to guard · application service = *coordinate* (transaction, retry) · infrastructure-behind-a-port = *how* to enforce.

**Mental tests**
- *"Holding another aggregate's object and calling its methods?"* → you've probably merged two aggregates; hold the ID and look it up.
- *"What's the smallest box such that everything an invariant touches lives inside it?"* → that box is the aggregate.
- **Design is iterative** — boundaries shift as you learn ("Member owns ≤ 2 loans" → "Loan is its own root, rule in a service"). That's maturing, not backtracking.

---

## Principles in play

| Principle | How this step applied it |
|---|---|
| **Encapsulation** (OOP) | The aggregate root is the only entry point; internal members are unreachable from outside, so invariants can't be bypassed. |
| **High cohesion / low coupling** | Small aggregates keep tightly-related data together (cohesion) and reference everything else by ID (loose coupling). |
| **SRP** | Each aggregate guards its own invariant; cross-aggregate rules are pushed out to domain services rather than bloating a root. |
| **KISS / YAGNI** | We chose small aggregates + a simple transactional count for "≤ 2 loans" rather than over-engineering distributed consistency the scale doesn't need. |
| **Iterative design** | We openly refined Step 4's invariant ownership once the small-aggregate rule revealed a better boundary. |

## Key takeaways (the transferable lessons)

1. **An aggregate is a consistency boundary**, and the **root is its single guardian** — all changes go through the root, so invariants can't be bypassed.
2. **Derive boundaries from invariants + concurrency, not taste.** Things that must stay transactionally consistent go together; everything else gets its own boundary.
3. **Prefer small aggregates.** The common mistake is making them too big. Small = fast to load, less contention, clearer transactions.
4. **Reference other aggregates by ID, never by object.** This is what keeps aggregates small and transactions clean — and it forces honest layering through repositories.
5. **One transaction, one aggregate.** Cross-aggregate rules move to domain services (and, at larger scale, eventual consistency) — not multi-aggregate transactions.
6. **Boundaries can shift as you learn.** Refining Step 4's "Member owns ≤ 2 loans" into "Loan is its own aggregate, rule enforced by a service" is design maturing, not backtracking.

---

*Next — Step 6: Relationships among Aggregates. We formalize the by-ID references into a proper relationship map — cardinalities (one Book → many Copies, one Member → many Loans), navigation direction, and the OOP distinctions your notes list (association vs aggregation vs composition) — producing the skeleton of our class/ER diagram.*
