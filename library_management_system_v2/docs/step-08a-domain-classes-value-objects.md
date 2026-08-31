# Step 8a — Writing the Domain Classes: Value Objects, IDs & Exceptions

*Series: Designing a Library Management System with DDD · Chapter 8a of 12*

---

The thinking is done (Steps 1–7). Now we write code — and we build **bottom-up**, because that's the dependency order: value objects depend on nothing, entities depend on value objects, services depend on entities. This chapter lays the **foundation**: the immutable, dependency-free building blocks that everything else is made of.

> **Why foundation-first?** If `Money` guarantees it can never be negative, then *every* entity that holds a `Money` inherits that guarantee for free. Get the small immutable pieces airtight, and the big mutable pieces have far less to worry about.

We'll write four things, in order: the **package layout**, **domain exceptions**, **typed IDs**, **status enums**, then the real **value objects** (`Money`, `ISBN`, `DateRange`).

---

## 8a.1 The package layout — and the role of each layer

Before the domain package, the bigger picture: the whole `src/` tree is four layers plus `tests/`, and one rule governs all of them.

> **Dependencies point *inward*. `domain` is the centre and depends on nothing. Everything depends on the domain; the domain depends on no one.**

```
   api ──► application ──► domain ◄── infrastructure
  (HTTP)   (use cases)    (rules)    (DB / adapters)
                            ▲
                       depends on NOTHING
```

| Layer | Its job | May import | LMS example |
|---|---|---|---|
| **`api/`** | The HTTP edge — **thin** translator: parse request, validate *input* (not invariants), call an application service, map result/`DomainError` → HTTP status. No business logic, no orchestration. | application, FastAPI/Pydantic | `POST /loans` controller → `400` on `DomainError` |
| **`application/`** | Orchestrate each use case — **load → decide → mutate → save**; the **transaction boundary**. Holds repositories (injected). Contains *no* business rules. | domain, repo *interfaces* | `borrow_book()`, `return_book()` |
| **`domain/`** | The business rules — entities, value objects, aggregates, domain services, repo *interfaces*. **Pure Python, zero framework imports.** | **nothing** | `BookCopy.issue()`, `Money`, `BorrowingService` |
| **`infrastructure/`** | Concrete *implementations* of the domain's interfaces — real persistence, locks, external systems ("behind the port"). | domain + real tech (DB, Redis, SMTP) | `SqlLoanRepository`, `RedisLockManager`, `SystemClock` |
| **`tests/`** | Verify each layer; mirrors `src/`. Domain tests run with plain objects (no DB/mocks); application tests use fake/in-memory repos; only infra tests touch real I/O. | the layer under test | `tests/domain/test_money.py` |

**The mental model:** `domain` = *what's true* · `application` = *what to do, in what order* · `infrastructure` = *how it physically happens* · `api` = *how the outside world asks* · `tests` = *proof it all holds.* The arrows always point at the domain — that's what keeps the rules pure and everything else swappable.

**Why this is the payoff, not bureaucracy:** because the domain imports nothing, the bulk of your tests (the domain) are instant and mock-free; you can swap Postgres for SQLite or FastAPI for a CLI by touching only the outer rings; and a reviewer always knows where a given concern lives. The layering *buys* testability, swappability, and navigability — it isn't ceremony for its own sake.

### This chapter's corner: the `domain` package — organized *by subdomain*

Everything in 8a lives in the `domain` layer — pure Python, **zero framework imports**. But there's a second, deliberate organizing decision *inside* `domain/`: we package **by subdomain (bounded-context module)**, not by technical type.

```
src/domain/
├── shared/          # the ONLY shared kernel — keep it tiny + stable
│   ├── ids.py           # EntityId + BookId, CopyId, MemberId, LoanId, FineId   (8a.3)
│   └── exceptions.py    # DomainException / DomainError base                    (8a.2)
├── catalog/         # book.py · bookcopy.py · isbn.py · enums.py(CopyStatus) · exceptions.py
├── lending/         # loan.py · daterange.py · enums.py(LoanStatus) · exceptions.py
├── fines/           # fine.py · money.py · enums.py(FineStatus) · exceptions.py
├── membership/      # member.py
└── notifications/   # placeholder (generic subdomain — no code yet)
    # each subdomain will also hold ITS OWN repository interfaces (Step 10)
    # and domain services (Step 9) — a full vertical slice, no central repositories/ or services/
```

> **Two ways to package — and why we chose this one.** You can group code *by technical type* (`entities/`, `value_objects/`, `enums/` — every subdomain's classes mixed together) or *by subdomain* (`catalog/`, `lending/`, … — each a self-contained slice). By-type is the common tutorial default, but it **scatters one subdomain across five folders** and the structure tells you nothing about what the system *does*. By-subdomain gives **high cohesion** (everything about Lending in one place), **"screaming architecture"** (the folders name the business, not the framework), and — the reason that matters most below — it makes the bounded-context boundaries *tangible* instead of theoretical. This is exactly what Step 1 called for ("modules that mirror the subdomains").

#### Why this layout is microservice-friendly (the load-bearing reason)

We deliberately keep this a **modular monolith** at our scale (Step 1 / the Step-5 aggregate-vs-microservice sidebar). But the *point* of packaging by subdomain is that a future split into microservices becomes a **lift-out**, not a rewrite. That works only if two rules hold:

1. **A subdomain never imports another subdomain's internals.** No `lending` importing `catalog.Book`. If it did, they'd be welded at compile time and couldn't be separated. Subdomains talk **only** by (a) **IDs by value**, (b) **published interfaces/contracts**, (c) **domain events** (later).
2. **The shared kernel stays tiny and stable.** A big shared kernel is the thing that *doesn't* split — so `shared/` holds only the universal, rarely-changing types: the typed IDs and the base exception.

Putting the **typed IDs in `shared/`** is what turns rule #1 into a clean fact rather than a hope. The dependency graph becomes a star with **no subdomain → subdomain edges**:

```
catalog  ─┐
lending  ─┤
fines    ─┼──►  shared        (EntityId + typed IDs + DomainError base)
membership┤
notifications┘
        NO edges between subdomains
```

Because every subdomain depends *only* on `shared`, each one is **independently extractable**. At split time:
- `shared/` becomes a thin published "contracts" library each service depends on (or each service re-declares the ID as a string wrapper — over the wire it's just a UUID);
- cross-subdomain references are **already by ID** (`Loan` holds `member_id`, never a `Member`), so a local lookup becomes a remote call/event **without changing the domain logic**;
- the transaction that spans aggregates (`borrow` touches BookCopy + Loan) is *within one subdomain* (Lending), so it stays a local transaction — the split doesn't force a distributed saga.

> **The one-liner:** package by subdomain, let each subdomain depend only on a tiny `shared` kernel, and reference other subdomains **by ID only** — then "extract a microservice" is "move the folder," not "untangle the codebase." We stay a monolith today (KISS/YAGNI for ~100 members) while keeping the split a cheap future option.

---

## 8a.2 Domain exceptions — giving invariants a voice

We promised in Step 4 that violated invariants would raise **named** domain errors (not generic `ValueError`). Start here, because every other file imports these.

The **base** lives in the shared kernel (everyone derives from it); the **specific** errors live *with the subdomain that raises them*.

```python
# domain/shared/exceptions.py  — the base, in the shared kernel
class DomainException(Exception):
    """Base class for domain exceptions."""

class DomainError(DomainException):
    """Base class for every domain rule violation."""
```

```python
# domain/catalog/exceptions.py
from domain.shared.exceptions import DomainError
class InvalidISBNError(DomainError): ...              # I-6
class CopyNotAvailableError(DomainError): ...          # I-2 / I-7
class IllegalStatusTransitionError(DomainError): ...

# domain/lending/exceptions.py
from domain.shared.exceptions import DomainError
class InvalidDateRangeError(DomainError): ...          # I-4
class LoanAlreadyReturnedError(DomainError): ...        # I-8
class BorrowingLimitExceededError(DomainError): ...     # rule #4

# domain/fines/exceptions.py
from domain.shared.exceptions import DomainError
class NegativeMoneyError(DomainError): ...             # I-5
class FineAlreadySettledError(DomainError): ...
```

**Why a hierarchy — and why split this way?** Three payoffs:

1. The **name documents the rule.** `raise BorrowingLimitExceededError` tells the next reader exactly which invariant fired — no comment needed.
2. The API layer (Step 11) can catch the *base* `DomainError` and map it to a `400 Bad Request` in one place, while still special-casing specific ones. That's the **Open/Closed Principle** at the error-handling boundary: add a new domain error and the generic handler already covers it.
3. **Only the base is shared** — each subdomain owns its own errors and depends only on `domain.shared`. That's the microservice-friendly boundary from §8a.1: when a subdomain leaves, its exceptions go with it.

---

## 8a.3 Typed IDs — killing primitive obsession

From Step 3: a `MemberId` must not be interchangeable with a `BookId`, even though both are just strings underneath. We get that with a tiny frozen base class.

These live in **`domain/shared/ids.py`** — the shared kernel — precisely because IDs are how subdomains reference each other *without* importing each other's internals (§8a.1).

```python
# domain/shared/ids.py
import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class EntityId:
    """Base for all typed identifiers. Immutable, value-equal, hashable."""
    value: str

    @classmethod
    def new(cls) -> "EntityId":
        return cls(str(uuid.uuid4()))      # generate a fresh unique id

    def __str__(self) -> str:
        return self.value


class BookId(EntityId): ...
class CopyId(EntityId): ...
class MemberId(EntityId): ...
class LoanId(EntityId): ...
class FineId(EntityId): ...
```

**The subtle bit that makes this work.** `@dataclass(frozen=True)` generates an `__eq__` that *also checks the class*. So:

```python
BookId("abc") == BookId("abc")     # True  — same type, same value
BookId("abc") == CopyId("abc")     # False — DIFFERENT TYPES, never equal
```

That second line is the whole point: even with identical underlying strings, a `BookId` and a `CopyId` are **never** equal, and a type checker will reject passing one where the other is expected. The "swapped the arguments" bug from Step 3 becomes *impossible*.

- `frozen=True` → immutable (a Value Object trait) + auto `__hash__` (so IDs work as dict keys / in sets — important for repositories in Step 10).
- `EntityId.new()` → the one place IDs are minted, using `uuid4` so they're unique without a database round-trip.

---

## 8a.4 Status enums — the legal vocabulary of state

Three of our aggregates have a lifecycle. The *set of legal states* is itself a value — model it as an `Enum`, not loose strings (a string lets you typo `"DAMGED"` and crash at runtime; an enum can't).

Each status enum lives **with the subdomain that owns that lifecycle** — `CopyStatus` in `catalog/`, `LoanStatus` in `lending/`, `FineStatus` in `fines/`.

```python
# domain/catalog/enums.py
from enum import Enum
class CopyStatus(Enum):
    AVAILABLE = "available"
    LOANED    = "loaned"
    LOST      = "lost"
    DAMAGED   = "damaged"

# domain/lending/enums.py
from enum import Enum
class LoanStatus(Enum):
    ACTIVE    = "active"
    RETURNED  = "returned"
    OVERDUE   = "overdue"

# domain/fines/enums.py
from enum import Enum
class FineStatus(Enum):
    UNPAID = "unpaid"
    PAID   = "paid"
    WAIVED = "waived"
```

These enums are the alphabet; in 8b the entities define the *grammar* — which transitions between these states are legal (the State pattern). Defining the vocabulary separately keeps that grammar readable — and each enum ships with its own subdomain.

---

## 8a.5 The value objects

Now the real building blocks. Each one is **immutable, self-validating, and equal-by-value** — the Step 3 definition, made concrete. Each VO lives **with its subdomain** (`Money` in `fines/`, `ISBN` in `catalog/`, `DateRange` in `lending/`) and imports only from its own subdomain + `domain.shared`.

### `Money` — never negative, arithmetic without surprises

```python
# domain/fines/money.py
from dataclasses import dataclass
from domain.fines.exceptions import NegativeMoneyError


@dataclass(frozen=True)
class Money:
    amount: int                 # store paise/cents as int — NEVER float for money
    currency: str = "INR"

    def __post_init__(self):
        # Invariant I-5: money is never negative
        if self.amount < 0:
            raise NegativeMoneyError(f"Money cannot be negative: {self.amount}")

    # --- factory for readability ---
    @classmethod
    def rupees(cls, rupees: int) -> "Money":
        return cls(rupees * 100)            # ₹5 -> 500 paise

    # --- side-effect-free operations: return NEW Money, never mutate ---
    def add(self, other: "Money") -> "Money":
        self._same_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def multiply(self, factor: int) -> "Money":
        return Money(self.amount * factor, self.currency)

    def _same_currency(self, other: "Money") -> None:
        if self.currency != other.currency:
            raise ValueError("Cannot mix currencies")

    def __str__(self) -> str:
        return f"₹{self.amount / 100:.2f}"
```

Three deliberate choices worth calling out:

1. **`int`, never `float`, for money.** Floats can't represent `0.1` exactly — `0.1 + 0.2 != 0.3`. Storing the smallest unit (paise) as an integer makes money arithmetic exact. This is a classic real-world bug avoided by design.
2. **Operations return a *new* `Money`.** `add`/`multiply` never mutate `self` — they hand back a fresh value. That's what "immutable" means in practice, and it's why a `Money` can be shared without defensive copying.
3. **The invariant lives in `__post_init__`.** A negative `Money` cannot be *constructed*, so it cannot exist anywhere in the system. No downstream check ever needs to re-verify it.

### `ISBN` — valid by construction

```python
# domain/catalog/isbn.py
from dataclasses import dataclass
from domain.catalog.exceptions import InvalidISBNError


@dataclass(frozen=True)
class ISBN:
    value: str

    def __post_init__(self):
        normalized = self.value.replace("-", "").replace(" ", "")
        # Invariant I-6: an ISBN is 10 or 13 digits (last char of ISBN-10 may be 'X')
        if len(normalized) not in (10, 13) or not normalized[:-1].isdigit():
            raise InvalidISBNError(f"Invalid ISBN: {self.value!r}")
        # frozen=True blocks normal assignment, so set via object.__setattr__
        object.__setattr__(self, "value", normalized)
```

Once an `ISBN` object exists, it is **guaranteed well-formed** — every consumer can trust it blindly. The `object.__setattr__` trick is just how you assign inside a frozen dataclass's `__post_init__` (here, to store the cleaned-up form). We keep validation pragmatic (length + digits) rather than a full checksum — *match the rigor to the need* (KISS).

### `DateRange` — the loan window, and where lateness is computed

```python
# domain/lending/daterange.py
from dataclasses import dataclass
from datetime import date, timedelta
from domain.lending.exceptions import InvalidDateRangeError


@dataclass(frozen=True)
class DateRange:
    start: date                  # borrow date
    end: date                    # due date

    def __post_init__(self):
        # Invariant I-4: a loan window must end after it starts
        if self.end < self.start:
            raise InvalidDateRangeError(f"due date {self.end} precedes borrow date {self.start}")

    @classmethod
    def for_loan(cls, borrow_date: date, loan_days: int) -> "DateRange":
        """Factory encoding business rule #2: due = borrow + N days."""
        return cls(borrow_date, borrow_date + timedelta(days=loan_days))

    # --- query: how many days overdue, as of some date (a FACT, not a fine) ---
    def days_overdue(self, as_of: date) -> int:
        return max(0, (as_of - self.end).days)

    def is_overdue(self, as_of: date) -> bool:
        return as_of > self.end
```

This little VO is doing real domain work:

- `for_loan(borrow_date, 5)` encodes **rule #2** ("return within 5 days") as a named factory — the `5` will be supplied by a loan policy in 8b, *not* hard-coded here, so the window length stays configurable.
- `days_overdue()` returns a **fact** ("12 days late"). Recall the Step 7 contract: the `Loan` will expose this, but it will **not** turn it into money — that's the fine **Strategy** (8b). The fact lives here; the policy lives there. The separation starts at this method.

---

## 8a.6 What the foundation guarantees

With ~80 lines of code we've created a layer where **whole categories of bugs are now impossible**:

| Bug class | Why it can't happen now |
|---|---|
| Negative fine / balance | `Money` rejects it at construction |
| Passing a `BookId` where a `MemberId` is expected | Distinct types; type checker / `==` refuse it |
| Malformed ISBN flowing through the system | `ISBN` validates on creation |
| A due date before the borrow date | `DateRange` rejects it |
| Float rounding errors in money | We store integer paise |
| Typo'd status string (`"DAMGED"`) | `CopyStatus` enum has no such member |

Every one of these is caught **at the boundary of creation**, so the entities we build in 8b can simply *assume* their value objects are valid and focus on their own, higher-level rules.

---

## 8a.7 How to use these pieces: behavior-first entity design

Now that the building blocks exist, a note on *how* to write the entities that consume them (8b) — because the order you design in matters.

> **Behavior first, attributes second.** Decide what the entity *does* and what it must *protect*; let the attributes fall out of what that behavior needs. Starting from a list of fields is the road to an **anemic** data-bag model.

The method, in order:

1. **Identity** — it's an entity, so settle its typed id immediately (`BookId`, `FineId`).
2. **Behavior / the contract** — the real work, and it's exactly the Step-7 contract: the **commands** it accepts, the **invariants** it guards, the **queries** it answers, and what it must **NOT** do.
3. **Attributes — derived from steps 1–2.** Add a field *only because* some behavior or invariant requires it. The litmus test per field: *"which behavior or invariant needs this?"* If the answer is "none, it just seemed like data we'd have" → don't add it (YAGNI).
4. **Implement** — constructor (enforce construction-time invariants), commands (guarded, private state), queries (CQS).

### Choosing each attribute's type (the three-way decision)

Once a behavior tells you an attribute is needed, decide *what kind* it is. The deciding word is **identity / lifecycle**:

| The attribute… | → It is a… | How it's held | Example |
|---|---|---|---|
| has its **own identity + lifecycle**, referenced independently | **separate Entity / aggregate** | **by ID** — never embedded as an object | `Loan` holds `member_id` (Member is its own entity) |
| has **rules / meaning** but **no identity**, immutable, equal-by-value | **Value Object** (a field) | as a field | `Money`, `ISBN`, `DateRange`, status enums |
| is a **dumb scalar** with no rules | **primitive** | as a field | `title: str`, `page_count: int` |

> ⚠️ **Common inversion to avoid:** "has its own lifecycle → make it a VO" is **backwards**. A Value Object has *no* identity and *no* lifecycle — having a lifecycle is precisely what makes something an **Entity** (held by ID), not a VO. Lifecycle → entity; value-without-identity → VO; bare scalar → primitive.

### Sanity-check against `Fine`

We built `Fine` (8b) exactly this way — behavior drove every field:
- "settle-once" invariant → needs `_status` → fixed value set, no identity → **VO (enum)**.
- "is *given* its amount" → needs `_amount` → rules but no identity → **VO (`Money`)**, and a *constructor param*, not computed.
- references a Member who has their **own** lifecycle → **separate entity, held as `member_id` (by ID)** — not embedded, not a VO.
- the Fine's own identity → its **typed id** (`FineId`).

No stray attributes; each one traces back to a behavior or invariant.

---

## Principles in play

| Principle | How this step applied it |
|---|---|
| **Encapsulation / fail-fast** (OOP) | Each VO validates in its constructor; invalid values can never be constructed, so they never propagate. |
| **Immutability** | `frozen=True` everywhere; operations return new objects — safe sharing, free hashing/equality. |
| **SRP** | One file/type per concern: exceptions, ids, enums, values — each with a single reason to change. |
| **OCP** | The `DomainError` hierarchy lets the API map errors generically; new errors slot in without changing the handler. |
| **KISS** | Pragmatic ISBN validation, simple typed-ID base class — rigor matched to need, no gold-plating. |
| **Separation of fact vs policy** | `DateRange.days_overdue()` computes the *fact*; the *₹ policy* is deferred to the Strategy in 8b. |

## Key takeaways (the transferable lessons)

1. **Build bottom-up.** Value objects depend on nothing, so they come first; airtight foundations shrink what the rest of the system must guard.
2. **Make illegal values unconstructable.** Validate in `__post_init__`; a negative `Money` or bad `ISBN` simply cannot exist.
3. **Store money as integers, never floats.** Exactness by design beats rounding-bug whack-a-mole.
4. **Typed IDs eliminate a whole bug class** — identical strings of different types are never equal, and the type checker enforces it.
5. **Enums, not strings, for states.** The set of legal states is itself a value; an enum makes typos impossible and sets up the State pattern.

---

*Next — Step 8b: the Aggregate Roots & Patterns. We compose these value objects into the behavior-rich entities (`Book`, `BookCopy`, `Member`, `Loan`, `Fine`), enforce every Step-7 contract in code, and introduce the **Strategy** pattern for fine calculation and the **State** pattern for the loan lifecycle — exactly where the design called for them.*
