# Step 2 — Use Cases & User Journeys

*Series: Designing a Library Management System with DDD · Chapter 2 of 12*

---

In Step 1 we learned *what the words mean*. Now we learn *what the system has to do*. This is the bridge between a requirements document (a flat list of wishes) and a design (objects with behavior). We do it in two passes:

1. **Use cases** — the discrete things an actor can accomplish, prioritized.
2. **User journeys** — walking each actor through a flow step by step, including the decision points and failure paths.

Why both? A use case says *"a member can return a book."* A journey says *"…and here's what the system checks, what can go wrong, and what happens to the data along the way."* The journey is where the **behavior** hides — and behavior is exactly what our entities and aggregates will have to provide in later steps.

---

## 2.1 The concept: a use case is a goal, not a click

**A use case = one actor + one goal + a meaningful outcome.** "Member searches the catalog" is a use case (goal: find a book). "Member clicks the search button" is not — it's a UI detail. We model goals, because goals are stable; UIs change every year.

Three actors drive our system (from Step 1's glossary):

- **Member** — the borrower.
- **Librarian** — the operator at the desk.
- **Admin** — the manager of catalog and people.

> **A note on prioritization.** Not all use cases are equal. We tag each one against the **subdomain map from Step 1**: the *core* subdomain (Lending) gets our deepest modeling effort; *supporting* ones (Catalog, Membership) stay simple. Prioritizing now stops us from over-engineering CRUD and under-engineering the flows that actually carry business rules.

---

## 2.2 The prioritized use-case list

Extracted directly from the User Stories in [`REQUIREMENTS.md`](../REQUIREMENTS.md) and tagged by actor, subdomain, and priority.

| # | Use case | Actor | Subdomain | Priority |
|---|---|---|---|---|
| UC-1 | **Issue a copy** to a member | Member / Librarian | **Lending (core)** | 🔴 P0 |
| UC-2 | **Return a copy** | Member / Librarian | **Lending (core)** | 🔴 P0 |
| UC-3 | **Check availability** of a book | Librarian / Member | Lending / Catalog | 🔴 P0 |
| UC-4 | **Calculate & assess late fine** on return | System / Librarian | **Fines (core-ish)** | 🔴 P0 |
| UC-5 | **List overdue loans** (due date passed) | Librarian | Lending | 🟠 P1 |
| UC-6 | **Pay a fine** | Member | Fines | 🟠 P1 |
| UC-7 | **Search / filter the catalog** | Member | Catalog | 🟠 P1 |
| UC-8 | **Mark a copy as damaged** (and lost) | Librarian | Catalog | 🟠 P1 |
| UC-9 | **Add / remove / update books & copies** | Admin | Catalog | 🟢 P2 |
| UC-10 | **Add / remove members** | Admin | Membership | 🟢 P2 |
| UC-11 | **Notify member** of due date / fine | System | Notifications (generic) | 🟢 P2 |

**How to read the priorities:**

- **P0 (🔴)** — the lending loop. If issue / return / availability / fine don't work, there is no product. These four carry almost every business rule and deserve the most careful modeling.
- **P1 (🟠)** — important supporting flows that lean on P0 (overdue list, paying fines, search, damage).
- **P2 (🟢)** — administrative CRUD and notifications. Necessary, but low complexity — we will *not* gold-plate these.

> **Renewal is deliberately absent.** Requirement #5 says *"books cannot be renewed."* The absence of a "renew" use case is itself a design statement — and in Step 8 we'll see that *not adding a `renew()` method* is how the model enforces that rule. Sometimes the cleanest way to enforce a rule is to make the illegal operation un-expressible.

---

## 2.3 User journeys

A journey walks one use case end to end: the **happy path**, the **checks** the system performs, and the **failure paths**. Watch for the checks especially — each one is a future **invariant** (Step 4) or a piece of **domain logic** (Steps 5–9).

### Journey A — Member borrows a book (UC-3 → UC-1)

```
Member: "I want 'Clean Code'."
  │
  ├─ 1. Search the catalog by title          ── UC-7 (Catalog)
  │       → system shows the Book + how many copies are AVAILABLE
  │         (lost/damaged copies are HIDDEN from the member — rule #6)
  │
  ├─ 2. Request to borrow an available copy   ── UC-1 (Lending)
  │
  ├─ 3. System runs the borrowing checks:
  │       ┌───────────────────────────────────────────────┐
  │       │ CHECK a: Is a copy actually available?          │ ← BookCopy invariant
  │       │ CHECK b: Does the member have < 2 active loans? │ ← Member invariant (rule #4)
  │       │ CHECK c: Does the member have unpaid fines?     │ ← (policy question — we'll decide)
  │       └───────────────────────────────────────────────┘
  │
  ├─ 4a. All pass → create a LOAN
  │        • mark the copy LOANED
  │        • set due date = today + 5 days  (rule #2)
  │        • member now has +1 active loan
  │
  └─ 4b. Any fails → reject with a clear reason
           ("no copies available" / "borrowing limit reached" / "settle fines first")
```

**What this journey reveals for the model:**
- A `Loan` is *created* by this flow — it ties one `Member` to one `BookCopy` with a due date.
- The "max 2 active loans" check needs the member to *know its own active loans* → hint that **Member is an aggregate root** (Step 5).
- "Mark the copy loaned" and "is it available?" are behaviors on **BookCopy**, not free-floating code.

### Journey B — Member returns a book (UC-2 → UC-4)

```
Member hands a copy back to the Librarian.
  │
  ├─ 1. Find the active LOAN for this copy
  │
  ├─ 2. Compute lateness:
  │        days_late = max(0, today − due_date)
  │
  ├─ 3a. On time (days_late = 0) → close the loan, no fine
  │
  ├─ 3b. Late → assess a FINE                 ── UC-4 (Fines)
  │        fine = ₹5 × days_late              (rule #3)
  │        attach the fine to the member's account
  │
  ├─ 4. Mark the copy AVAILABLE again
  │        • member's active-loan count −1
  │        • loan transitions to RETURNED
  │
  └─ 5. (later) member PAYS the fine          ── UC-6
```

**What this journey reveals:**
- Fine calculation is a **rule that might change** (₹5 today, ₹10 tomorrow, grace periods later). That's a flashing sign for the **Strategy pattern** (introduced in Step 8 when we write the domain classes) — we keep the *what* (calculate a fine) stable and make the *how* swappable.
- A `Loan` has **states** (active → returned/overdue) → hint at the **State pattern** in Step 8.
- "Assess fine" and "mark copy available" must happen *together and consistently* → a transaction/consistency concern that aggregates (Step 5) exist to solve.

### Journey C — Librarian's day (UC-5, UC-8)

```
Morning:
  ├─ View the OVERDUE list                     ── UC-5
  │     → all loans where due_date < today and still active
  │     → system can notify those members        ── UC-11
  │
During the day:
  ├─ Inspect a returned copy; if damaged →
  │     mark the copy DAMAGED (or LOST)        ── UC-8
  │       • a damaged/lost copy is NOT issuable
  │       • it stays VISIBLE to the librarian but HIDDEN from members (rule #6)
```

**What this reveals:**
- The librarian sees a **superset** of what members see. The visibility rule is *per copy status*, confirming again that `BookCopy` status is a first-class concept (the Step 1 keystone paying off).
- "Overdue list" is a **query**, not a command — a hint that we'll separate read concerns from write concerns later.

### Journey D — Admin maintenance (UC-9, UC-10)

```
Admin:
  ├─ Add a new Book to the catalog, with N copies   ── UC-9
  ├─ Add / increase / remove copies of a Book        ── UC-9
  └─ Add or remove a Member                          ── UC-10
```

Deliberately boring — straightforward create/update/delete. We tagged these P2 precisely so we don't waste design budget here. **Recognizing what is simple is a design skill too.**

---

## 2.4 What the journeys handed us

Without writing a line of code, the journeys surfaced the raw material for the next six steps:

| Observation from a journey | Where it pays off |
|---|---|
| "Member has < 2 active loans" check | **Invariant** (Step 4), **Member aggregate** (Step 5) |
| "Is this copy available?" / "mark loaned/available/damaged" | **BookCopy** behavior + status (Steps 3–4) |
| Fine = ₹5 × days_late, *and the rule may change* | **Strategy pattern** (Step 8) |
| Loan goes active → returned / overdue | **State pattern** (Step 8) |
| "Assess fine **and** free the copy together" | **Aggregate consistency** (Step 5) |
| Members see less than librarians | **Query filtering** + read/write split (Step 11) |
| No "renew" use case exists | Enforce rule #5 by *omission* (Step 8) |

---

## Key takeaways (the transferable lessons)

1. **Model goals, not clicks.** Use cases capture what stays stable; UI flows don't.
2. **Prioritize against your subdomain map.** Pour effort into the *core* (Lending); keep *supporting* CRUD boring on purpose. Knowing what's simple is half the skill.
3. **Journeys are where behavior hides.** Every *check* in a happy path is a future invariant; every *"this might change"* is a future pattern; every *"these must happen together"* is a future aggregate boundary.
4. **An absent use case can be a design decision.** "No renewals" is enforced by making renewal un-expressible, not by adding a guard.

## Principles in play

| Principle | How this step applied it |
|---|---|
| **SRP** (Single Responsibility) | A use case = one actor + one goal — each captures a single, well-scoped responsibility. |
| **YAGNI / KISS** | P2 admin CRUD kept deliberately boring; we refused to gold-plate Catalog/Membership. |
| **OCP** (foreshadowed) | Spotting *"the fine rule may change"* flags where Open/Closed (via the Strategy pattern) will be needed — Step 8. |
| **Prioritization** | Modeling effort is directed at the *core* subdomain (Lending), per the Step 1 map — not spread evenly. |

---

## Note — how much time to spend on Steps 1 & 2

**In an LLD interview (~45–60 min): Steps 1+2 together ≈ 8–12 min, max ~15.**

| Step | Time | What you actually do |
|---|---|---|
| 1 — language + keystone | 3–5 min | Clarify scope, list key nouns/verbs, *nail the one keystone insight* (here: Book ≠ BookCopy). Skip the formal subdomain table — just say "core loop is lending, rest is CRUD." |
| 2 — use cases + journeys | 5–8 min | List use cases, mark the core ones, walk **one or two** journeys aloud (happy path + checks). |

The trap is spending 25 min here and never reaching code. Get to classes by ~minute 15.

**As learning / a real design doc: time is the wrong metric — completeness is.** Step 1 is the
highest-leverage step (a modeling mistake here is the most expensive to retrofit). Budget ~30–60 min
of real thinking per step the first few times; it drops fast as the muscle forms.

**Calibration rule (both settings):**
> Stop Step 1 the moment you've found the **keystone insight** and can name your entities in the
> business's words. Stop Step 2 the moment **one core journey has surfaced its checks** (each check
> is a future invariant — the raw material the next steps consume). Still going after that? You're
> polishing, not designing.

**Caveat:** the *first* time on a new problem type it feels slow — that's correct. Speed comes from
pattern recognition across problems (parking lot, elevator, BookMyShow…), not from rushing the
thinking. After ~5–10 problems, Steps 1+2 collapse to a confident few minutes.

---

*Next — Step 3: Entities & Value Objects. We take every concept from our glossary and ask the two questions that decide its fate — "does it have a lifelong identity?" (Entity) or "is it just its values?" (Value Object) — and we'll see why getting this split right is what makes the code both safe and simple.*
