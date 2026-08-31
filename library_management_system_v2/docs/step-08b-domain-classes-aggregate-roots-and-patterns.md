# Step 8b — Writing the Domain Classes: Aggregate Roots & Patterns

*Series: Designing a Library Management System with DDD · Chapter 8b of 12*

---

8a gave us airtight value objects. Now we compose them into the **aggregate roots** — the behavior-rich entities that enforce every Step-7 contract — and we introduce two design patterns **exactly where the design demanded them**:

- the **Strategy** pattern for fine calculation (the *"₹5/day might change"* policy seam), and
- the **State** pattern for the loan lifecycle (the *active → returned/overdue* transitions).

A reminder of the discipline from your notes: *patterns appear only when a real design problem appears.* So we'll first build the entities with the **simplest thing that works**, and reach for a pattern only when the simple thing starts to hurt. Watching *when* that happens is the real lesson.

```
src/domain/
├── entities/
│   ├── book.py · book_copy.py · member.py · fine.py
│   ├── loan.py
│   └── loan_state.py            # ← State pattern
└── services/
    └── fine_calculation.py      # ← Strategy pattern
```

---

## 8b.1 The entity skeleton: identity & equality

Every entity shares two traits from Step 3: a typed **identity**, and **equality by that identity** (not by attributes). We'll repeat this shape in each class:

```python
def __eq__(self, other) -> bool:
    return isinstance(other, BookCopy) and self.id == other.id
def __hash__(self) -> int:
    return hash(self.id)
```

> Why not a shared `Entity` base class? We could, but explicit is fine here and avoids inheritance gymnastics. (KISS — a base class earns its place only when the shared behavior grows.)

---

## 8b.2 `BookCopy` — a state machine via a transition table

`BookCopy` has the richest *status* lifecycle. But it has **no divergent behavior per state** — issuing, returning, damaging are simple transitions. So the simplest correct tool is a **transition table** guarding which moves are legal. This is a lightweight state machine — *not* the full State pattern (we'll see why Loan is different).

```python
# domain/entities/book_copy.py
from ..ids import CopyId, BookId
from ..enums import CopyStatus
from ..exceptions import CopyNotAvailableError, IllegalStatusTransitionError

# The "grammar": which status moves are legal (the enums in 8a were the alphabet)
_LEGAL_MOVES = {
    CopyStatus.AVAILABLE: {CopyStatus.LOANED, CopyStatus.DAMAGED, CopyStatus.LOST},
    CopyStatus.LOANED:    {CopyStatus.AVAILABLE, CopyStatus.DAMAGED, CopyStatus.LOST},
    CopyStatus.DAMAGED:   {CopyStatus.AVAILABLE},   # repaired back into circulation
    CopyStatus.LOST:      set(),                     # terminal
}


class BookCopy:
    def __init__(self, copy_id: CopyId, book_id: BookId,
                 status: CopyStatus = CopyStatus.AVAILABLE):
        self.id = copy_id
        self.book_id = book_id            # cross-aggregate reference BY ID (Step 6)
        self._status = status             # private — only methods may change it

    def __eq__(self, other): return isinstance(other, BookCopy) and self.id == other.id
    def __hash__(self):      return hash(self.id)

    # --- queries (CQS) ---
    @property
    def status(self) -> CopyStatus:       return self._status
    @property
    def is_available(self) -> bool:       return self._status is CopyStatus.AVAILABLE
    @property
    def is_visible_to_member(self) -> bool:               # supports rule #6
        return self._status in (CopyStatus.AVAILABLE, CopyStatus.LOANED)

    # --- commands (CQS) ---
    def issue(self) -> None:
        if not self.is_available:                          # invariant I-2 / I-7
            raise CopyNotAvailableError(str(self.id))
        self._move_to(CopyStatus.LOANED)

    def return_copy(self) -> None: self._move_to(CopyStatus.AVAILABLE)
    def mark_damaged(self) -> None: self._move_to(CopyStatus.DAMAGED)
    def mark_lost(self) -> None:    self._move_to(CopyStatus.LOST)

    def _move_to(self, target: CopyStatus) -> None:
        if target not in _LEGAL_MOVES[self._status]:
            raise IllegalStatusTransitionError(f"{self._status.value} → {target.value}")
        self._status = target
```

Notice the contract from Step 7 enforced exactly: `is_visible_to_member` implements rule #6, `issue()` guards I-2, and **`_status` is private** so the only way to change it is through a guarded command. There is no path to an illegal state.

---

## 8b.3 `Book`, `Member`, `Fine` — small, focused entities

### `Book` — catalog metadata + search

```python
# domain/entities/book.py
from ..ids import BookId
from ..value_objects import ISBN

class Book:
    def __init__(self, book_id: BookId, isbn: ISBN, title: str, author: str, genre: str | None = None):
        if not title.strip():  raise ValueError("Book title cannot be empty")
        if not author.strip(): raise ValueError("Book author cannot be empty")
        self.id, self.isbn = book_id, isbn
        self.title, self.author = title.strip(), author.strip()
        self.genre = genre.strip() if genre else None

    def __eq__(self, other): return isinstance(other, Book) and self.id == other.id
    def __hash__(self):      return hash(self.id)

    def update_metadata(self, *, title=None, genre=None) -> None:   # command
        if title is not None:
            if not title.strip(): raise ValueError("title cannot be empty")
            self.title = title.strip()
        if genre is not None: self.genre = genre.strip()

    def matches(self, keyword: str) -> bool:                        # query — supports UC-7
        k = keyword.lower()
        return k in self.title.lower() or k in self.author.lower()
```

### `Member` — deliberately narrow (the Step-7 surprise, in code)

```python
# domain/entities/member.py
from ..ids import MemberId

class Member:
    def __init__(self, member_id: MemberId, name: str, email: str, active: bool = True):
        self.id, self.name, self.email = member_id, name, email
        self._active = active

    def __eq__(self, other): return isinstance(other, Member) and self.id == other.id
    def __hash__(self):      return hash(self.id)

    @property
    def is_active(self) -> bool: return self._active
    def block(self)   -> None:   self._active = False
    def unblock(self) -> None:   self._active = True

    # NOTE: there is intentionally NO can_borrow() / active-loan count here.
    # Loans are a separate aggregate (Step 5); eligibility is decided by
    # BorrowingService (Step 9). Member only owns MEMBER-level facts.
```

That missing method is the design talking. The aggregate boundary from Step 5 shows up here as an *absence* — and the comment makes the intent explicit for the next reader.

### `Fine` — settle-once lifecycle, holding a `Money`

```python
# domain/entities/fine.py
from ..ids import FineId, MemberId, LoanId
from ..enums import FineStatus
from ..value_objects import Money
from ..exceptions import FineAlreadySettledError

class Fine:
    def __init__(self, fine_id: FineId, member_id: MemberId, loan_id: LoanId,
                 amount: Money, status: FineStatus = FineStatus.UNPAID):
        self.id = fine_id
        self.member_id, self.loan_id = member_id, loan_id   # by-ID refs (Step 6)
        self._amount, self._status = amount, status

    def __eq__(self, other): return isinstance(other, Fine) and self.id == other.id
    def __hash__(self):      return hash(self.id)

    @property
    def amount(self) -> Money:  return self._amount
    @property
    def is_paid(self) -> bool:  return self._status is FineStatus.PAID

    def pay(self) -> None:
        self._require_unpaid(); self._status = FineStatus.PAID
    def waive(self) -> None:
        self._require_unpaid(); self._status = FineStatus.WAIVED

    def _require_unpaid(self) -> None:
        if self._status is not FineStatus.UNPAID:
            raise FineAlreadySettledError(str(self.id))
```

`Fine` is *given* its `amount` (a `Money` produced by the Strategy below) — it never computes the ₹ itself. Exactly the Step-7 "must not."

---

## 8b.4 The Strategy pattern — fine calculation (the policy seam)

**The problem (recap).** "₹5/day" is a *policy* that will change (₹10 next year, grace periods, member discounts). If we hard-code it inside `Loan` or `Fine`, every change means editing core entities — a violation of the **Open/Closed Principle**.

**The pattern.** Define a small *interface* for "calculate a fine," and make each policy a separate, swappable implementation. The entities depend on the *abstraction*, never a concrete rate.

```python
# domain/services/fine_calculation.py
from abc import ABC, abstractmethod
from ..value_objects import Money


class FineCalculationStrategy(ABC):
    """Turns a FACT (days overdue) into a POLICY outcome (money owed)."""
    @abstractmethod
    def calculate(self, days_overdue: int) -> Money: ...


class StandardFineStrategy(FineCalculationStrategy):
    """Business rule #3: ₹5 per day late."""
    _RATE = Money.rupees(5)
    def calculate(self, days_overdue: int) -> Money:
        return self._RATE.multiply(max(0, days_overdue))
```

Now the OCP payoff — **adding a new policy touches no existing code**:

```python
class GracePeriodFineStrategy(FineCalculationStrategy):
    def __init__(self, grace_days: int = 2, rate: Money = Money.rupees(5)):
        self._grace, self._rate = grace_days, rate
    def calculate(self, days_overdue: int) -> Money:
        chargeable = max(0, days_overdue - self._grace)
        return self._rate.multiply(chargeable)

class CappedFineStrategy(FineCalculationStrategy):
    def __init__(self, inner: FineCalculationStrategy, cap: Money):
        self._inner, self._cap = inner, cap            # also the Decorator idea!
    def calculate(self, days_overdue: int) -> Money:
        fine = self._inner.calculate(days_overdue)
        return self._cap if fine.amount > self._cap.amount else fine
```

```python
# choosing a policy is a one-line swap — no entity changes:
strategy = StandardFineStrategy()                       # today
# strategy = GracePeriodFineStrategy(grace_days=3)      # tomorrow, zero ripple
fine_amount = strategy.calculate(loan.days_overdue(today))   # FACT -> POLICY -> Money
```

**Why this is textbook DDD + SOLID:**
- **OCP**: open for extension (new strategies), closed for modification (existing ones untouched).
- **LSP**: any `FineCalculationStrategy` is substitutable — the caller can't tell which it got.
- **DIP**: the calculation depends on the `FineCalculationStrategy` abstraction, not a hard-coded ₹5.
- And it consumes the **fact** (`days_overdue` from the `DateRange`/`Loan`) and produces the **policy** result (`Money`) — the fact/policy split from Steps 4 & 7, finally wired together.

---

## 8b.5 The State pattern — the loan lifecycle

**The Loan is different from BookCopy.** Its key operation — `return_copy()` — *behaves differently depending on state*:

- in **ACTIVE**: returning is allowed and computes lateness;
- in **RETURNED**: returning again is an error (invariant I-8).

When **behavior diverges by state** (not just "is this move legal?"), that's the signal for the **State pattern**: give each state its own class that knows how to behave, and let the entity delegate to its current state object.

### First — the simple version (and why it's often enough)

```python
# the "good enough" approach for few states
class Loan:
    def return_copy(self, on_date: date) -> int:
        if self._status is LoanStatus.RETURNED:
            raise LoanAlreadyReturnedError(str(self.id))     # I-8
        days_overdue = self.period.days_overdue(on_date)     # the FACT
        self._status = LoanStatus.RETURNED
        return days_overdue
```

For three states this is honestly *fine*. But let's build the State pattern properly so you know it — and then weigh the trade-off.

### The State pattern version

```python
# domain/entities/loan_state.py
from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import date
from ..enums import LoanStatus
from ..exceptions import LoanAlreadyReturnedError


class LoanState(ABC):
    @abstractmethod
    def status(self) -> LoanStatus: ...
    @abstractmethod
    def return_copy(self, loan: "Loan", on_date: date) -> int: ...


class ActiveState(LoanState):
    def status(self): return LoanStatus.ACTIVE
    def return_copy(self, loan, on_date) -> int:
        days_overdue = loan.period.days_overdue(on_date)     # behavior: compute lateness
        loan._set_state(ReturnedState())                     # transition
        return days_overdue


class ReturnedState(LoanState):
    def status(self): return LoanStatus.RETURNED
    def return_copy(self, loan, on_date) -> int:
        raise LoanAlreadyReturnedError(str(loan.id))         # behavior: refuse
```

```python
# domain/entities/loan.py
from __future__ import annotations
from datetime import date
from ..ids import LoanId, MemberId, CopyId
from ..value_objects import DateRange
from ..enums import LoanStatus
from .loan_state import LoanState, ActiveState

class Loan:
    def __init__(self, loan_id: LoanId, member_id: MemberId, copy_id: CopyId,
                 period: DateRange, state: LoanState | None = None):
        self.id = loan_id
        self.member_id, self.copy_id = member_id, copy_id     # by-ID refs
        self.period = period                                  # DateRange VO
        self._state: LoanState = state or ActiveState()

    def __eq__(self, other): return isinstance(other, Loan) and self.id == other.id
    def __hash__(self):      return hash(self.id)

    @property
    def status(self) -> LoanStatus:  return self._state.status()
    def is_overdue(self, as_of: date) -> bool:
        return self.status is LoanStatus.ACTIVE and self.period.is_overdue(as_of)
    def days_overdue(self, as_of: date) -> int:               # the FACT (Step 7)
        return self.period.days_overdue(as_of)

    def return_copy(self, on_date: date) -> int:              # delegates to current state
        return self._state.return_copy(self, on_date)

    def _set_state(self, state: LoanState) -> None:           # only states call this
        self._state = state

    # --- factory: encodes business rule #2 (due = borrow + N) ---
    @classmethod
    def create(cls, member_id: MemberId, copy_id: CopyId,
               borrow_date: date, loan_days: int = 5) -> "Loan":
        period = DateRange.for_loan(borrow_date, loan_days)
        return cls(LoanId.new(), member_id, copy_id, period)
```

`Loan.create(...)` is a **Factory Method** — it's the *only* way to mint a loan, and it guarantees the due-date invariant (I-3) at birth. The `return_copy` call simply delegates to whatever state the loan is in; the *state object* decides what happens. Adding an `OverdueState` with its own behavior later means adding one class — no edits to `Loan`.

### The honest trade-off (this is the real lesson)

> **Did the Loan *need* the State pattern? For two states — arguably no.** The simple `if status == RETURNED: raise` version is shorter and clearer. The State pattern earns its keep when:
> - states multiply (5+), **and**
> - each state has genuinely **divergent behavior** across several operations, **and**
> - you keep adding states over time.
>
> We built it here so you can *recognize* the pattern and the smell that justifies it — sprawling `if/elif status ==` chains repeated across many methods. If you ever see that, reach for State. If you don't, the enum-guard version is the KISS-correct choice. **Knowing a pattern includes knowing when *not* to use it.**

---

## 8b.5b Note: do *all* design patterns live in `domain/`?

A fair question after writing Strategy and State here: does every pattern we build belong in the domain layer? **No.** A design pattern is just a structuring technique — *where* it lives depends on *what concern it solves*, not on the fact that it's "a pattern."

> **A pattern's home = the layer of the concern it addresses.** Business behavior → `domain/`. Persistence / external systems / wiring → the outer layers.

| Pattern | Concern it solves | Lives in |
|---|---|---|
| **Strategy** (`FineCalculationStrategy`) | a *business policy* (₹/day) | **`domain/`** (services) |
| **State** (`LoanState`) | the loan's *business behavior* per state | **`domain/`** (entities) |
| **Factory Method** (`Loan.create`, `Money.rupees`) | enforce *creation invariants* | **`domain/`** |
| **Repository — *interface* (port)** | what the domain *needs* to load/save | **`domain/`** |
| **Repository — *implementation*** | *how* it persists (SQL / in-memory) | **`infrastructure/`** |
| **Adapter / Ports** (`Clock`, `Notifier`, `LockManager` impls) | talking to the outside world | **`infrastructure/`** |
| **Observer / Domain Events** | event *definition* vs *handlers* | event in `domain/`, handlers in `application/` |
| **DI / composition root** | wiring concretes into interfaces | **`api/` / `application/`** |
| **DTO / Mapper** | HTTP ↔ domain translation | **`api/`** |

**Repository proves the point** — the same pattern deliberately straddles two layers: the *interface* (`LoanRepository`) in `domain/` (what the domain needs), the *implementation* (`SqlLoanRepository`) in `infrastructure/` (how it persists). That split is Dependency Inversion in action.

**Two look-alike patterns can land in different layers** depending on what they model: a Strategy for *fine calculation* is `domain/` (a business policy), but a Strategy for *retry-backoff* on a failed DB write is `infrastructure/` (a technical concern). Same pattern, different concern, different home.

> **The litmus test:** *"If I swapped the database / web framework / email provider, would this pattern change?"* **No → it's a business rule → `domain/`** (Strategy-for-policy, State, Factory, Repository interface). **Yes → it's a technical detail →** `infrastructure/` / `application/` / `api/` (Repository impl, Adapters, DI, DTOs). Most of *our* visible patterns are domain ones — but never assume "pattern ⇒ domain"; follow the concern.

---

## 8b.6 How a `return` reads now (preview of Step 9–10)

With the entities + Strategy in place, the *return-a-book* use case becomes a short, readable choreography (orchestration belongs to the application service in Step 10):

```python
loan  = loans.get(loan_id)                    # Loan aggregate
copy  = copies.get(loan.copy_id)              # BookCopy aggregate (by id)

days_overdue = loan.return_copy(today)        # Loan: state transition + FACT
copy.return_copy()                            # BookCopy: back to AVAILABLE

if days_overdue > 0:                          # late → assess a fine
    amount = fine_strategy.calculate(days_overdue)        # POLICY -> Money
    fine = Fine(FineId.new(), loan.member_id, loan.id, amount)
    fines.save(fine)

loans.save(loan); copies.save(copy)
```

Each aggregate guards its own invariant; the Strategy owns the policy; the service just *orchestrates*. The clean seams from Steps 4–7 are paying off in readable code.

---

## Principles in play

| Principle | How this step applied it |
|---|---|
| **Rich domain model / Tell-Don't-Ask** | Entities carry behavior + guard their own invariants; callers tell them what to do (`copy.issue()`, `loan.return_copy()`). |
| **OCP + LSP + DIP** (SOLID) | The **Strategy** pattern: new fine policies extend without modifying; any strategy is substitutable; entities depend on the abstraction. |
| **State pattern** (GoF) | Loan delegates state-dependent behavior to state objects — *with an explicit discussion of when it's overkill*. |
| **Factory Method** | `Loan.create()` is the single, invariant-guaranteeing way to build a loan. |
| **Encapsulation** | Private `_status`/`_state`; the only mutations are guarded commands. |
| **KISS / YAGNI** | `BookCopy` uses a simple transition table (no pattern); we flag where the State pattern would be over-engineering. |

## Key takeaways (the transferable lessons)

1. **Compose entities from value objects**, give them identity + equality-by-id, and keep their mutable state **private** behind guarded commands.
2. **Reach for a pattern only when the simple thing hurts.** `BookCopy` (no divergent behavior) → transition table; `Loan` (divergent `return` behavior) → a candidate for State.
3. **Strategy turns a policy into a swappable object** — the cleanest expression of OCP/LSP/DIP, and the home for every "this rule might change."
4. **Factory methods protect creation invariants.** `Loan.create()` guarantees the due date; you can't make an invalid loan.
5. **Knowing a pattern includes knowing when not to use it.** We built State, then argued the enum-guard version is often better. Judgment > dogma.

---

*Next — Step 9: Domain & Application Services. We give a home to the cross-aggregate logic the entities deliberately refused — the `BorrowingService` (can this member borrow? enforce ≤ 2 active loans) — and draw the crucial line between **domain services** (business rules spanning aggregates) and **application services** (use-case orchestration + transactions).*
