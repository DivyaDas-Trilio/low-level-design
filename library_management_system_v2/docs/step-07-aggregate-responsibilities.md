# Step 7 — Aggregate Responsibilities

*Series: Designing a Library Management System with DDD · Chapter 7 of 12*

---

We have the *structure* (Steps 5–6): five aggregates, their boundaries, their relationships. Now we give each one a **job description** — the precise behavior it owns — *before* we write a single line of it in Step 8. This is the step that decides whether your domain model is **rich** (objects with behavior that protect themselves) or **anemic** (dumb data bags whose logic leaks into services). It's also where one OOP idea does most of the work:

> **Tell, Don't Ask.** Don't pull an object's data out to make a decision *about* it elsewhere — *tell the object what to do* and let it decide, because it owns the data and the rules.

For each aggregate root we'll write four things, and the fourth is the one people skip:

1. **Commands** it accepts (state-changing behaviors)
2. **Invariants** it guards (from Step 4)
3. **Queries** it can answer about itself
4. **What it must NOT do** (anti-responsibilities — what belongs to *someone else*)

---

## 7.1 The concept: rich vs. anemic, and where to put behavior

**The anemic anti-pattern** is the default trap. It looks like this:

```python
# ❌ Anemic: BookCopy is a dumb data bag; the rule lives in a service
class BookCopy:
    status: str                      # public, anyone can set it to anything

class LendingService:
    def issue(self, copy):
        if copy.status != "AVAILABLE":   # rule floats OUTSIDE the object...
            raise ...
        copy.status = "LOANED"           # ...and anyone could forget this check
```

The problem: the invariant ("only available copies can be issued") lives *outside* the data it protects. Every place that touches `copy.status` must remember the rule. Miss it once → corrupt state.

**The rich alternative** puts behavior with the data it governs:

```python
# ✅ Rich: BookCopy guards its own rule; no one can bypass it
class BookCopy:
    def issue(self):
        if self._status is not CopyStatus.AVAILABLE:
            raise CopyNotAvailableError(self.id)
        self._status = CopyStatus.LOANED
```

**How do you know *which* object gets a responsibility?** Use the GRASP **Information Expert** principle:

> *Assign a responsibility to the class that has the information needed to fulfill it.*

`BookCopy` owns its `status`, so `BookCopy` owns `issue()`. `Loan` owns its `due_date`, so `Loan` answers `is_overdue()`. Simple, and it almost always gives the right home.

---

## 7.2 The responsibility contracts

Here's each aggregate's job description. Method names use our Ubiquitous Language (Step 1).

### `BookCopy` — the physical-item lifecycle

| | |
|---|---|
| **Commands** | `issue()` · `return_copy()` (→ available) · `mark_damaged()` · `mark_lost()` |
| **Guards** | I-2/I-7: only an `AVAILABLE` copy can be issued; only legal status transitions allowed |
| **Queries** | `is_available` · `is_visible_to_member` (derived from status — supports rule #6) |
| **Must NOT** | create `Loan`s · calculate fines · know about `Member` · decide *who* may borrow it |

> The whole status lifecycle lives here, and **nowhere else** can change a copy's status. That single fact enforces invariants I-2 and I-7 for the entire system.

### `Loan` — the borrowing record's lifecycle

| | |
|---|---|
| **Commands** | `create(...)` (factory; sets due date = borrow + 5) · `return_copy(on_date)` (→ returned, reports lateness) · `mark_overdue()` |
| **Guards** | I-3: due date fixed at creation · I-8: cannot return an already-returned loan · legal state transitions only · **no `renew()` method exists** (enforces rule #5 by omission) |
| **Queries** | `is_overdue(today)` · `days_overdue(today)` · `due_date` · `status` |
| **Must NOT** | change the `BookCopy`'s status itself · **calculate the fine *amount*** · check the member's borrowing limit |

> ⚠️ **The most important "must not" in the whole design:** `Loan` reports `days_overdue` — a *fact*. It does **not** turn that into ₹ — that's a *policy*. The `Loan` says "12 days late"; the **fine Strategy** (Step 8) decides "12 × ₹5 = ₹60." Keeping the fact (Loan) separate from the policy (Strategy) is exactly the invariant-vs-policy split from Step 4, now expressed as a responsibility boundary.

### `Member` — narrower than you'd expect

| | |
|---|---|
| **Commands** | `register(...)` · `update_profile(...)` · `block()` / `unblock()` (if a member is suspended) |
| **Guards** | member-level validity (e.g. valid email); active/blocked status |
| **Queries** | `is_active` · profile getters |
| **Must NOT** | **count its own active loans** · hold a list of `Loan`s · decide borrowing eligibility *alone* |

> 🔑 **A deliberately surprising contract.** Intuition says `Member.can_borrow()` should check "< 2 active loans." But loans live in their *own* aggregate (Step 5), so `Member` **cannot** answer that by itself — it doesn't (and shouldn't) hold the loans. `Member` only owns *member-level* facts (am I active? am I blocked?). The "< 2 active loans" part comes from the **Loan repository**, and the two are combined by a **domain service** (next section). This is the aggregate boundary from Step 5 showing up as a responsibility limit.

### `Fine` — the debt's lifecycle

| | |
|---|---|
| **Commands** | `pay(amount)` · `waive()` |
| **Guards** | I-5: amount never negative (via `Money`) · cannot pay an already-settled fine · legal transitions (unpaid → paid / waived) |
| **Queries** | `is_paid` · `balance` · `amount` |
| **Must NOT** | calculate its *own* amount from scratch (it's *given* an amount produced by the fine Strategy) · know `Loan` internals |

### `Book` — catalog metadata

| | |
|---|---|
| **Commands** | `update_metadata(...)` (correct title/genre/author) |
| **Guards** | I-6: valid `ISBN`; non-empty title/author |
| **Queries** | `matches(filter)` (supports search UC-7) · getters |
| **Must NOT** | manage its copies (separate aggregate) · know about loans or members |

---

## 7.3 What no single aggregate owns → Domain Services

Notice a pattern in all those "Must NOT" rows: several real behaviors don't fit *inside any one aggregate* because they **span two or more**. Those are not homeless — they belong to **Domain Services** (Step 9). Collecting them now:

| Cross-aggregate behavior | Why no single aggregate owns it | Lands in |
|---|---|---|
| "Can *this member* borrow *this copy*?" | needs `Member` (active?) + `BookCopy` (available?) + `Loan` count (< 2?) | **BorrowingService** |
| "Turn *days overdue* into a *fine amount*" | a swappable *policy*, not an entity's fact | **FineCalculationStrategy** |
| "Enforce ≤ 2 active loans on borrow" | spans `Member` + `Loan` aggregates | **BorrowingService** |

> **The transferable lesson:** writing the "Must NOT" list isn't bureaucracy — it's how you *discover your domain services*. Every responsibility you push *out* of an aggregate has to land *somewhere*, and that somewhere is a service. Skipping the "must not" column is how aggregates quietly bloat into god-objects.

---

## 7.4 Command-Query Separation (a cheap discipline that pays off)

You'll have noticed each contract separates **Commands** (change state, return nothing) from **Queries** (return data, change nothing). That's **CQS** — *a method should either do something or answer something, never both.*

```python
copy.issue()              # command  → changes state, returns nothing
copy.is_available         # query    → returns a fact, changes nothing
```

Why bother? Queries become **safe to call freely** (no side effects to fear), commands become the **only** places state changes (easy to reason about and test). It's a small rule that makes a model dramatically easier to understand — and it's free.

---

## 7.5 The contracts at a glance

```
Book        : update_metadata · matches(filter)            | guards ISBN
BookCopy    : issue · return_copy · mark_damaged/lost       | guards "AVAILABLE-only" lifecycle
Member      : register · update_profile · block/unblock     | guards member status  (NOT loan count!)
Loan        : create · return_copy · mark_overdue           | guards due-date & no-double-return, NO renew
              · is_overdue / days_overdue  (reports FACTS, not ₹)
Fine        : pay · waive                                   | guards "never negative", settle-once

Cross-aggregate (→ services, Step 9):
  BorrowingService          : can_member_borrow? · enforce ≤2 active loans
  FineCalculationStrategy   : days_overdue → Money  (the ₹5/day POLICY, swappable)
```

Every aggregate is now a **behavioral contract**, not just a data shape. Step 8 is "merely" translating these contracts into Python — the thinking is done.

---

## Principles in play

| Principle | How this step applied it |
|---|---|
| **Tell, Don't Ask** (OOP) | Behavior placed with the data it governs (`copy.issue()`), instead of pulling state out into a service to decide. |
| **Information Expert** (GRASP) | Each responsibility assigned to the class that holds the data needed for it. |
| **Rich domain model** (anti-anemic) | Aggregates carry behavior + invariants; they aren't dumb data bags. |
| **SRP** | Each aggregate owns one cohesive job; cross-aggregate work is pushed to services via the "must not" list. |
| **CQS** | Commands change state and return nothing; queries return data and change nothing. |
| **Separation of policy vs fact** | `Loan` reports `days_overdue` (fact); the Strategy turns it into money (policy) — wired in Step 8. |

## Key takeaways (the transferable lessons)

1. **Decide behavior before writing code.** A contract (commands / invariants / queries / must-not) makes Step 8 mechanical.
2. **Put behavior where the data lives** (Information Expert) and **tell objects what to do** instead of asking for their data — that's what makes a model *rich* instead of *anemic*.
3. **The "must NOT" column is the valuable one.** It keeps aggregates from bloating and *discovers your domain services* — every pushed-out responsibility lands in a service.
4. **Separate facts from policies as responsibilities.** `Loan` knows it's 12 days late (fact); it does not know that costs ₹60 (policy). That boundary is what makes the rule swappable.
5. **Apply CQS everywhere.** Commands do; queries answer; never both.

---

*Next — Step 8: Writing the Domain Classes. The payoff chapter — we turn every contract above into real Python: value objects first, then entities/aggregate roots enforcing their invariants, and we introduce the **Strategy** pattern (fine calculation) and the **State** pattern (loan lifecycle) exactly where the contracts demanded them.*
