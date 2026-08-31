# Step 3 — Entities & Value Objects

*Series: Designing a Library Management System with DDD · Chapter 3 of 12*

---

We now have a vocabulary (Step 1) and a list of behaviors the system must support (Step 2). Time to decide *what kind of thing* each concept is. In DDD's tactical toolkit, almost everything in your domain is one of two things: an **Entity** or a **Value Object**. Choosing correctly is what makes the eventual code both **safe** (rules can't be violated) and **simple** (less to reason about).

This is the most under-taught distinction in LLD. Most people model *everything* as an entity-with-an-id and miss half the design. Let's not.

---

## 3.1 The two questions

For every concept, ask:

> **Q1 — "If all its attributes change, is it still the same thing?"**
> If **yes**, it has an *identity* → it's an **Entity**.
>
> **Q2 — "If two of them have identical attributes, are they interchangeable?"**
> If **yes**, it's defined purely by its values → it's a **Value Object**.

A classic intuition pump:

- A **person** is an Entity. You change your name, address, even your face over a lifetime — you're still *you*. Identity persists through change.
- A **₹100 note** is a Value Object. Any ₹100 is as good as any other ₹100. You don't track *which specific* note; only the amount matters.

That's the whole core. Everything below is consequences of these two questions.

---

## 3.2 Entity — defined by identity

An **Entity** has a unique identifier that stays constant for its whole life. Its attributes can change; its identity cannot.

| Property | Entity |
|---|---|
| **Equality** | By **ID**. `loan_a == loan_b` iff same id, even if other fields differ. |
| **Mutability** | Mutable — it has a lifecycle (created → changed → archived). |
| **Identity** | Explicit ID assigned at creation, never reused. |
| **Example** | A `Loan` — loan #42 stays loan #42 after it's returned. |

```python
# Illustrative — full version comes in Step 8
class Loan:
    def __init__(self, loan_id: LoanId, ...):
        self.id = loan_id          # identity — fixed for life
        self.status = "ACTIVE"     # state — will change

    def __eq__(self, other):
        return isinstance(other, Loan) and self.id == other.id  # equality BY ID

    def return_copy(self):
        self.status = "RETURNED"   # attributes change, identity does not
```

## 3.3 Value Object — defined by its values

A **Value Object** has no identity. It *is* its attributes. Two value objects with equal attributes are the same value, full stop.

| Property | Value Object |
|---|---|
| **Equality** | By **value**. `Money(5,"INR") == Money(5,"INR")` is `True`. |
| **Mutability** | **Immutable** — to "change" it, you create a new one. |
| **Identity** | None. We don't track *which* ₹5. |
| **Behavior** | Often self-validating + has side-effect-free helper methods. |
| **Example** | `Money`, `ISBN`, `DateRange`. |

```python
from dataclasses import dataclass

@dataclass(frozen=True)   # frozen = immutable + auto value-equality + hashable
class Money:
    amount: int
    currency: str = "INR"

    def __post_init__(self):
        if self.amount < 0:                       # self-validating
            raise ValueError("Money cannot be negative")

    def add(self, other: "Money") -> "Money":
        return Money(self.amount + other.amount)  # returns a NEW value, never mutates
```

> **Why `frozen=True` matters.** Immutability means a Value Object can be **shared freely without fear** — no one can reach in and corrupt it. It also gives you free, correct `==` and hashing. This single decorator buys you a whole category of bug-immunity.

---

## 3.4 Why Value Objects are the secret weapon

Most engineers reach for raw primitives (`str`, `int`, `float`) and scatter validation everywhere. That's called **primitive obsession**, and it's an anti-pattern. Compare:

```python
# ❌ Primitive obsession
def issue(book_id: str, member_id: str, fine: float): ...
issue(member_id, book_id, -5.0)   # args swapped + negative fine — compiles fine, breaks at runtime
```

```python
# ✅ Value Objects
def issue(book_id: BookId, member_id: MemberId, fine: Money): ...
issue(member_id, book_id, ...)    # TYPE ERROR — you literally can't swap them
# and Money(-5) can never exist — it's rejected at construction
```

Value Objects give you three things for free:

1. **Validation in one place.** An `ISBN` is validated once, in its constructor. After that, *every* `ISBN` in the system is guaranteed valid. No defensive `if` checks sprinkled around.
2. **Type safety / no primitive mix-ups.** A `MemberId` can't be passed where a `BookId` is expected. The bug becomes impossible, not just unlikely.
3. **Expressiveness.** `due_date.is_before(today)` reads better than `due_date < datetime.now()` scattered everywhere, and the logic lives in one obvious home.

This is OOP's **encapsulation** principle doing real work: data + the rules about that data, bundled together and protected.

### But don't wrap *everything* — an Entity is a blend

The lesson above is *not* "every field of an Entity must be a Value Object." Reflexively wrapping every primitive is its own anti-pattern — ceremony that fights KISS/YAGNI. The real rule is sharper:

> **Wrap a primitive in a VO when the value carries rules or meaning. Leave it a primitive when it's a genuinely attribute-less scalar.**

The deciding question — *"does this value have rules or meaning beyond its raw type?"*

**Wrap it** when any of these holds:
- It has **validity rules** — `ISBN` (format/checksum), `Money` (no negatives). Enforced once, at construction.
- It's **mixable with another value of the same primitive type** — `MemberId` and `BookId` are both "a string"; a typed VO makes passing one for the other impossible.
- It has **behavior** — `DateRange.days_overdue(today)` beats `today - due_date` scattered everywhere.
- It's a **fixed set** — `CopyStatus` → enum VO, not a free `str`.

**Leave it primitive** when it's a dumb scalar with no rules, no mix-up risk, no behavior — a book's `page_count: int`, a `description: str`, a `returned: bool`. A `PageCount` class would buy nothing.

So a real Entity is a *blend*:

```python
class Loan:               # Entity
    id:        LoanId      # VO  — typed id, no mix-ups
    copy_id:   CopyId      # VO  — cross-aggregate ref by id
    member_id: MemberId    # VO
    period:    DateRange   # VO  — has rules + behavior
    returned:  bool        # primitive — just a flag, no rules
```

Most of an Entity's *interesting* fields end up as VOs — precisely because the interesting fields are the ones with rules. That's why it *feels* like "Entities are made of Value Objects." But it's earned case by case, never applied reflexively.

---

## 3.5 Classifying every LMS concept

Now we run all of Step 1's glossary through the two questions. This table is the deliverable of Step 3.

| Concept | Verdict | Reasoning |
|---|---|---|
| **`Book`** | **Entity** | Has identity (`BookId`). You can correct its title/genre and it's still that catalog record. |
| **`BookCopy`** | **Entity** | Has identity (`CopyId`) and a *status lifecycle* (available→loaned→damaged). Two copies of the same book are distinct things. |
| **`Member`** | **Entity** | Identity (`MemberId`); long-lived; accumulates loans and fines. |
| **`Loan`** | **Entity** | Identity (`LoanId`); has a lifecycle (active→returned/overdue). The central record. |
| **`ISBN`** | **Value Object** | Defined by its digits; two equal ISBNs are the same; immutable; self-validating (format/checksum). |
| **`Money`** | **Value Object** | ₹5 == ₹5. Arithmetic, no identity. |
| **`DateRange` / loan period** | **Value Object** | The borrow→due window; pure values; handy methods like `days_overdue(today)`. |
| **`BookId`, `CopyId`, `MemberId`, `LoanId`** | **Value Objects** (typed IDs) | Wrapping ids in types kills primitive obsession and makes mix-ups a compile-time impossibility. |
| **`CopyStatus`** | **Value Object** (enum) | A fixed set of values: AVAILABLE / LOANED / LOST / DAMAGED. |
| **`Fine`** | **🤔 borderline — decided below** | |
| **`Librarian`, `Admin`** | **Actors / roles** | They *use* the system. Until we add authentication, they aren't domain entities — just roles that authorize use cases. |

### The borderline case: is `Fine` an Entity or a Value Object?

This is a great teaching example because the answer is *"it depends on a business question,"* and naming that question is the real skill.

- **If** a fine is just "an amount owed because this loan was late," and we never need to track or reference an individual fine on its own → it's a **Value Object** (an amount attached to a Loan/Member).
- **If** the business needs to track each fine's lifecycle — *assessed → partially paid → paid → waived* — refer to it by a receipt number, or report on individual fines → it has identity and a lifecycle → it's an **Entity**.

Looking at our use cases: UC-6 is *"pay a fine,"* which implies a fine has a status (unpaid → paid). That tips it toward **Entity**. **Decision: model `Fine` as an Entity** with a `FineId` and a `status`, holding a `Money` value object inside it. (Notice how an Entity is often *made of* Value Objects — `Fine` *has a* `Money`.)

> **The transferable lesson:** when a classification is ambiguous, the deciding factor is almost always *"does the business need to track this thing's lifecycle or refer to it individually?"* If yes → Entity. If it's just a value in a moment → Value Object.

---

## 3.6 How they relate — can an Entity and a Value Object exist independently?

A fair question once you notice that *both* are just Python classes: if the difference isn't syntax, what *is* the relationship between them?

**Entities hold Value Objects — composition.** VOs are the building blocks; Entities are the things built from them, using VOs to describe their state instead of bare `int`/`str`. In our model: `Loan` *has a* `DateRange`, `Fine` *has* `Money`, `Book` *has an* `ISBN`. The VO is an **attribute of** the Entity.

Now the independence question, where they genuinely differ:

| | Exists independently? | Why |
|---|---|---|
| **Entity** | **Yes** | It has its own identity + lifecycle. You create it, store and fetch it *by ID*, follow it as it changes, delete it. A `Loan` is a thing in its own right. |
| **Value Object** | **No (not meaningfully)** | It has no identity and no lifecycle of its own — it's always a *value of* something. Its lifetime is **contained inside** its owner. You'd never persist a loose `Money` of ₹50 with its own id, floating free. |

> You *can* write `Money.rupees(50)` on its own line — Python won't stop you. But it has no meaning to **persist or track** alone, the way an Entity does. A VO is born, used, and discarded as part of its owner.

**The consequence that falls straight out of this:** because a VO has no identity, you **never mutate it in place — you replace it.** To change a fine's amount you assign a whole new `Money`; you don't reach inside the old one. That's exactly why `frozen=True` (§3.3) is safe and correct, not a limitation.

The analogy that makes it stick: an **Entity is a noun** you can point to and follow over time (*a member, a loan*); a **Value Object is a measurement or description** *of* that noun (*an amount, a date, an ISBN*). You don't store "175 cm" in a database with its own id and lifecycle — it's always *somebody's* height.

### "But values change in real life" — what if a VO needs to be modified?

A `Member` has an `Email` (a VO). A year later they want a different email. If VOs are immutable, how?

The resolution is a rule, not a workaround:

> You **don't modify the VO — you replace it.** The *Entity* swaps its reference to a brand-new VO.

The value `"alice@old.com"` never morphs into `"alice@new.com"` — those are two different values, forever. What changes is *which* email the Member points at. And the Member is an **Entity**, which is allowed to change — that's its whole nature.

```python
class Member:                       # Entity — mutable, has a lifecycle
    def change_email(self, new_email: Email) -> None:
        self._email = new_email     # rebind to a NEW VO, don't mutate the old one
```

```python
member.email.address = "alice@new.com"     # ❌ wrong — and frozen=True forbids it anyway
member.change_email(Email("alice@new.com"))  # ✅ right — hand the Entity a new value
```

Why this is *better*, not a compromise:

1. **The change flows through an Entity method.** `change_email(...)` is a real domain action — the natural home for rules ("can't reuse the same address," notify, log). Mutating a raw field would bypass all of it.
2. **The new value is validated at construction.** `Email("not-an-email")` is rejected the instant it's built, so the Member can never hold an invalid email, even mid-change.
3. **No aliasing surprises.** Anyone still holding the old `Email` keeps a stable, correct `"alice@old.com"` — they aren't silently rewritten.

The mental model is just **variable reassignment**, scaled up: `x = "a"; x = "b"` doesn't mutate the string `"a"` — it points `x` at a different string. Likewise, the address `"123 Main St"` doesn't *become* `"456 Oak Ave"`; you now *point at* a different address.

In one sentence: **the Entity mutates (it has a lifecycle); the Value Object it holds does not (it gets replaced).**

---

## 3.7 The shape of the model so far

Putting the verdicts together, here's the conceptual map (relationships come in Steps 5–6, so treat the arrows as informal for now):

```
Book  (Entity)
  └── has many ──> BookCopy (Entity, has CopyStatus)
                        ▲
                        │ refers to
Member (Entity) ──┐     │
                  ├── Loan (Entity) ── covers ──> one BookCopy
                  │       └── has ──> DateRange (VO: borrow_date..due_date)
                  └── owes ──> Fine (Entity) ── has ──> Money (VO)

Value Objects woven throughout: ISBN, Money, DateRange, CopyStatus,
and the typed IDs (BookId, CopyId, MemberId, LoanId, FineId).
```

Entities are the *nouns with a story over time*; Value Objects are the *descriptive, interchangeable pieces* they're built from. A healthy domain model is usually **a few entities, made of many value objects** — if everything is an entity, you've probably missed some value objects.

---

## 3.8 Practice — classify these yourself

Run each through the two questions from §3.1 (*"same thing if attributes change?"* → Entity; *"interchangeable if attributes match?"* → VO). Decide before peeking. The borderline ones (★) are the real workout — there the skill is *naming the business question that decides it*.

**Part A — outside the library (build general intuition)**
1. A **passport number**
2. A **passport** (the physical booklet)
3. A **GPS coordinate** (latitude, longitude)
4. A **bank account**
5. A **₹500 transaction** on that account ★
6. An **email address**
7. A **shopping cart** ★
8. A **colour** (`#FF5733`)

**Part B — inside our LMS**
9. A **`Genre`** (Fiction / Science / History …)
10. A **`Reservation`** — a member's hold on a title that's currently all loaned out ★
11. A **`Notification`** sent to a member ★
12. A **phone number** stored on a `Member`

<details>
<summary><b>Answers & reasoning</b> (try first!)</summary>

**Part A**
1. **VO** — it *is* its digits; two equal numbers are the same; never changes.
2. **Entity** — a specific issued booklet with a lifecycle (valid → expired → renewed → revoked); you track *that* one.
3. **VO** — defined wholly by its two numbers; immutable; (12.97, 77.59) == (12.97, 77.59).
4. **Entity** — must be *yours*; identity + lifecycle (balance changes, account persists).
5. ★ **Usually an Entity.** Tempting to call it "just an amount + date" (VO), but the business almost always needs to reference, reverse, or audit *that specific* transaction → it has an id and a lifecycle. (If you truly only ever sum amounts and never refer to one, it could be a VO — *that's* the deciding question.)
6. **VO** — defined by its string; self-validating (format); immutable. (It becomes an *attribute* of a Member entity.)
7. ★ **Entity.** A cart is followed over time (items added/removed, then checked out → becomes an order). Identity + lifecycle. The *line items* inside it lean VO-ish.
8. **VO** — `#FF5733` is its value; interchangeable; immutable.

**Part B**
9. **VO** (enum) — a fixed set of interchangeable values, like `CopyStatus` in §3.5.
10. ★ **Entity.** A reservation has a lifecycle — *waiting → fulfilled → expired/cancelled* — and a position in a queue you refer back to. Same logic that made `Fine` an Entity (§3.5).
11. ★ **Depends on the business question.** If you only ever fire-and-forget a message, the *content* is a **VO**. If you must track *sent → delivered → read* or let a user see their notification history → it gains identity and lifecycle → **Entity**. (This is the generic-subdomain "Notifications" from CLAUDE.md — we'll likely keep it simple.)
12. **VO** — like the email: it *is* its digits, self-validating, immutable; lives as an attribute of the `Member`.

**Pattern to notice:** every ★ resolved the same way — *"does the business need to track this thing's states or refer to it individually?"* Yes → Entity; no → Value Object. That single question settles almost every hard case.

</details>

---

## Key takeaways (the transferable lessons)

1. **Two questions decide everything.** *Same thing even if attributes change?* → Entity (equality by ID, mutable). *Just its values?* → Value Object (equality by value, immutable).
2. **Value Objects are the under-used half.** They concentrate validation in one place, kill primitive obsession, and make whole categories of bugs impossible. Reach for them aggressively.
3. **Make IDs into types.** `MemberId` instead of `str` turns "passed the wrong id" from a runtime bug into a compile-time error.
4. **Ambiguous? Ask about lifecycle.** If the business tracks a thing's states or refers to it individually, it's an Entity (that's why `Fine` became one). Otherwise it's a Value Object.
5. **Entities are made of Value Objects.** A `Fine` *has a* `Money`; a `Loan` *has a* `DateRange`. Few entities, many value objects, is the healthy shape.

## Principles in play

| Principle | How this step applied it |
|---|---|
| **Encapsulation** (OOP) | Value Objects bundle data **with** its validation rules (`Money` rejects negatives inside its own constructor) — invalid values can't exist. |
| **SRP** (Single Responsibility) | One concept, one job — `ISBN` validates ISBNs and knows nothing about loans or members. |
| **Composition over inheritance** (OOP) | Entities are built *from* value objects (`Fine` has-a `Money`, `Loan` has-a `DateRange`) — no deep inheritance trees. |
| **Type safety / fail-fast** | Typed IDs (`MemberId` vs raw `str`) turn wrong-argument bugs into compile-time errors and kill primitive obsession. |

---

*Next — Step 4: Invariants. We take the business rules and pin each one to the exact object responsible for guarding it — the rules that the model must make literally impossible to violate. This is where "safe by construction" gets real, and it sets up the aggregate boundaries in Step 5.*
