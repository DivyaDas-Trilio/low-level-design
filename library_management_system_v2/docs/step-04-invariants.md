# Step 4 — Invariants

*Series: Designing a Library Management System with DDD · Chapter 4 of 12*

---

We have entities and value objects (Step 3). Now we make them **safe**. An *invariant* is a rule that must be true *at all times* — and the whole game of domain modeling is to design objects so that breaking an invariant is **impossible**, not merely *discouraged*. This is the chapter where "correct by construction" stops being a slogan and becomes concrete.

It's also the chapter that secretly designs Step 5: the invariants that must hold *together* are exactly what define an **aggregate boundary**.

---

## 4.1 The concept: an invariant is a truth that never breaks

> **An invariant is a condition about your domain that must hold true before and after *every* operation — never temporarily false where anyone can observe it.**

Examples in plain English:

- "A member never has more than 2 active loans." (Not "we try to prevent it" — it must *never* be observably true that a member has 3.)
- "Money is never negative."
- "A loan's due date is always after its borrow date."

The contrast with ordinary "checks" is the key insight: a check that lives in a controller or a service can be **forgotten** at the next call site. An invariant enforced *inside the object that owns the data* can **never** be bypassed — because there's no way to reach the data except through the object.

### Invariant vs. input validation — not the same thing

People conflate these. They're different jobs:

| | Input validation | Invariant |
|---|---|---|
| **Question** | "Is this *input* well-formed?" | "Is this *object* in a legal state?" |
| **Lives in** | The edge (API layer, DTOs) | The domain object itself |
| **Example** | "Is `days` a positive integer?" | "Is the borrow→due window ≥ 1 day?" |
| **If violated** | Reject the request (400) | A bug — the model should have made it impossible |

Validation stops *garbage from outside*. Invariants protect *the integrity of the model itself*. You need both, but invariants are the ones DDD cares about most.

---

## 4.2 The principle: make illegal states unrepresentable

The best invariant is one you don't have to *check* because the design won't let the bad state exist. Three escalating techniques:

1. **Enforce in the constructor.** If an object can't be *born* invalid, you never have to re-check it. (`Money(-5)` throws — so a negative Money simply never exists anywhere in the system.)
2. **Enforce in every mutating method.** State changes only through methods that re-assert the invariant. No public setters that let callers poke the object into an illegal state.
3. **Remove the illegal operation entirely.** The cleanest enforcement of "loans cannot be renewed" is to *not write a `renew()` method*. You can't misuse what doesn't exist.

```python
class BookCopy:
    def issue(self) -> None:
        # Invariant: a copy can only be issued if it is AVAILABLE
        if self.status is not CopyStatus.AVAILABLE:
            raise CopyNotAvailableError(self.id)   # refuse — never enter an illegal state
        self.status = CopyStatus.LOANED
```

Notice there is **no** `self.status = LOANED` reachable from outside. The only path to "loaned" runs through `issue()`, which guards the rule. The illegal transition isn't *discouraged* — it's *unreachable*.

---

## 4.3 The LMS invariant catalog

Now the deliverable: every rule from `REQUIREMENTS.md` and every *check* we found in the Step 2 journeys, pinned to the **single object responsible for guarding it**. (This "who owns it" column is gold — it's the blueprint for Steps 5 and 8.)

| # | Invariant | Owner | Enforced how |
|---|---|---|---|
| I-1 | A member has **≤ 2 active loans** | **`Member`** | `Member.borrow()` checks count before adding a loan |
| I-2 | A copy is issued **only if `AVAILABLE`** | **`BookCopy`** | `BookCopy.issue()` guards on status |
| I-3 | A loan's **due date = borrow date + 5 days** | **`Loan`** | set at construction; no setter to change it |
| I-4 | A loan's **due date is after its borrow date** | **`DateRange` (VO)** | constructor rejects inverted ranges |
| I-5 | **Money is never negative** | **`Money` (VO)** | constructor rejects `amount < 0` |
| I-6 | An **ISBN is always well-formed** | **`ISBN` (VO)** | constructor validates format/checksum |
| I-7 | A **damaged/lost copy is never issuable** | **`BookCopy`** | covered by I-2 (only `AVAILABLE` issues) |
| I-8 | A **returned loan can't be returned again** | **`Loan`** | `Loan.return_copy()` guards on status |
| I-9 | A **loan always references a real member and a real copy** | **`Loan` construction** | required, non-null ids at creation |
| I-10 | A fine's **amount = ₹5 × days_overdue, never negative** | **`Money`** (≥0) + **fine policy** (the ×5) | amount as `Money`; the *rate* is a policy (see note) |

### Two nuances worth slowing down for

**(a) Not every "rule" is an invariant — some are *policies*.**
Look at I-10. *"Money is never negative"* is an invariant: it can never legitimately change. But *"the rate is ₹5/day"* is a **policy** — a business decision that may well change (₹10 next year, a grace period, premium-member discounts). Invariants get **baked into objects**; policies get **pulled out into something swappable**. That instinct — "this number might change" — is precisely the trigger for the **Strategy pattern (Step 8)**. Don't hard-code a policy as if it were an invariant.

**(b) Rule #6 (lost/damaged hidden from members) is *not* an invariant.**
It's a **read/query concern** — *who is allowed to see what* — not a truth about an object's internal state. The *invariant* part is "a damaged copy isn't issuable" (I-7). The *visibility* part ("members don't see it in search results") belongs to the query layer in Step 11. Keeping these separate stops you from contaminating the domain model with presentation rules.

---

## 4.4 Classifying invariants by scope — this is what designs Step 5

Here's the move that makes the next chapter almost automatic. Sort the invariants by **how much they touch**:

| Scope | Invariants | Implication |
|---|---|---|
| **Within a single Value Object** | I-4, I-5, I-6 | Trivially enforced in the VO constructor. Done. |
| **Within a single Entity** | I-2, I-3, I-7, I-8 | Enforced in that entity's own methods. Self-contained. |
| **Spans an Entity + its children** | **I-1** (Member must know *all its active loans* to count them) | ⚠️ This needs a **consistency boundary** — the entity and the things it must keep consistent with itself form an **Aggregate**. |
| **Spans two independent things** | "is *this* member allowed to borrow *this* copy?" | Belongs to a **Domain Service** (Step 5) — no single entity owns both sides. |

That third row is the whole reason aggregates exist. To guarantee "≤ 2 active loans," the `Member` must be the single gatekeeper through which loans are added — otherwise two simultaneous borrow operations could each see "1 loan" and both succeed, producing 3. **The set of objects that must stay mutually consistent = one aggregate, with one entity as its guardian (the aggregate root).** That's Step 5.

> **The transferable lesson:** you don't *choose* aggregate boundaries by taste — you *derive* them from your invariants. Find the rules that span more than one object; draw the boundary around exactly the objects each rule touches.

---

## 4.5 Domain exceptions: invariants need a voice

When an invariant is violated by a legitimate-but-disallowed request (e.g. a member at their limit tries to borrow), the object should refuse with a **meaningful domain exception**, not a generic `ValueError` or a silent `return False`.

```python
# domain/exceptions.py
class DomainError(Exception):
    """Base for all domain rule violations."""

class BorrowingLimitExceededError(DomainError): ...
class CopyNotAvailableError(DomainError): ...
class LoanAlreadyReturnedError(DomainError): ...
```

Why named exceptions? Because the API layer (Step 11) can map each to the right HTTP response and a clear message, and because the *name itself documents the rule*. `raise BorrowingLimitExceededError` tells the next reader exactly which invariant just protected the system. This is SRP and readability working together.

---

## Principles in play

| Principle | How this step applied it |
|---|---|
| **Encapsulation** (OOP) | Invariants live *inside* the object that owns the data; there's no public path to an illegal state. |
| **SRP** | Each invariant has exactly one owner; named domain exceptions each describe one violated rule. |
| **OCP** (foreshadowed) | Separating *policy* (₹5 rate — may change) from *invariant* (Money ≥ 0 — never changes) marks the future Strategy seam (Step 8). |
| **Fail-fast** | Constructors reject illegal values at birth, so the rest of the system never re-checks them. |
| **Separation of concerns** | Visibility (rule #6) is recognized as a *query* concern, kept out of the domain model. |

## Key takeaways (the transferable lessons)

1. **An invariant must be impossible to break, not just discouraged.** Enforce it inside the owning object — constructors, mutating methods, or by removing the illegal operation entirely.
2. **Invariant ≠ input validation.** Validation guards the edges; invariants guard the model's integrity. Different homes, both needed.
3. **Separate invariants from policies.** "Never negative" is an invariant (bake it in). "₹5/day" is a policy (make it swappable). Confusing the two leads to hard-coded business rules you can't change.
4. **Invariants design your aggregates.** Sort rules by scope: the ones that span an entity *and the things it must stay consistent with* define an aggregate boundary — derived, not guessed.
5. **Give invariants a voice.** Named domain exceptions document the rule and let outer layers respond intelligently.

---

*Next — Step 5: Aggregates & Aggregate Roots. We take the "spanning" invariants we just found and draw consistency boundaries around them — deciding that `Member` guards its loans and `Loan` is its own root — and we learn the single most important aggregate rule: keep them small and reference other aggregates by ID, not by object.*