# Step 10 — Repositories

*Series: Designing a Library Management System with DDD · Chapter 10 of 12*

---

In Step 9 the application service leaned on `self._members.get(...)`, `self._loans.save(...)`, `self._loans.count_active_for_member(...)` — objects we never defined. Those are **repositories**, and this chapter makes them real. A repository is the seam where the pure domain meets the messy world of storage — and getting it right is what lets us *run the whole system end-to-end* (we do, at the end of this chapter) while keeping the domain blissfully ignorant of databases.

> **A repository gives you the illusion of an in-memory collection of aggregates** — `get` one, `save` one — while hiding *where* they actually live (a dict today, Postgres tomorrow). The domain asks for aggregates by identity and gets domain objects back; it never sees a row, a column, or a SQL string.

---

## 10.1 Three defining rules

**Rule 1 — One repository per *aggregate root*, never per entity or table.** This is the rule people break first. You have `LoanRepository`, not `LoanRepository` + `DateRangeRepository`. Repositories deal in **whole aggregates**: you save a `Loan` (with its value objects inside), you get back a fully-formed `Loan`. The aggregate is the unit of storage, just as it's the unit of consistency (Step 5). We have exactly **five repositories** — one per root.

**Rule 2 — The *interface* lives in the domain; the *implementation* lives in infrastructure.** This is the Dependency Inversion loop from Step 9, finally closed:

```
lending/domain/repository.py                          ← INTERFACE (port)   — the domain owns this
        ▲ implements
lending/infrastructure/in_memory_loan_repository.py   ← IMPLEMENTATION (adapter)
```
*(vertical slice: one repo interface per aggregate root in its subdomain's `domain/`, its implementations in that subdomain's `infrastructure/`. The generic base + `EntityNotFoundError` are cross-cutting → `shared/`.)*

The domain *declares what it needs* ("I must be able to get a loan by id and count a member's active loans"); infrastructure *provides how*. The arrow of dependency points **inward** — infrastructure depends on the domain, never the reverse. This is the **Realization** relationship from Step 6 made concrete.

**Rule 3 — Repositories speak the domain language, not SQL.** A method is `find_active_by_member(member_id)`, not `select_where_status_eq()`. This is also how we answer the "navigate the relationship backwards" question from Step 6 — `Member` doesn't hold a list of loans, so when a use case needs them, it *asks the repository*.

> **Repository ≠ DAO.** A DAO (Data Access Object) is table-shaped: `insert`, `update`, `delete`, rows. A **repository is aggregate-shaped**: it returns domain objects and speaks the Ubiquitous Language. A repository may *use* DAOs/ORM underneath, but its face to the domain is pure.

> #### 🔀 Note: service-first or repository-first?
>
> A natural question, since we built the service (Step 9) *before* this chapter. The puzzle dissolves once you separate a repository's **two halves**:
>
> | Ordering | Verdict |
> |---|---|
> | **Design / intent** | **Service first** — the use cases express *what the system does*, and *they reveal* which queries the repository must offer. |
> | **Dependency** | The repo **interface** must exist for the service to compile — but it is **shaped by** the service's needs. |
> | **Implementation** | **Repository implementation last** — pure infrastructure, bolted on at the edge. |
>
> **The model:** *the service is the customer; the repository interface is its shopping list; the implementation is the store that fills it.* You write the list because the customer needs things (service drives it), but you don't build the store until the list is final. That's **Dependency Inversion**: high-level policy *defines* the interface; low-level detail *conforms* to it.
>
> This is exactly why Step 9's `LibraryService` called `loans.count_active_for_member(...)` **before that method existed** — every repository method in this chapter exists *because a use case demanded it*. Building repositories first would mean guessing query methods nobody needs (a YAGNI trap).
>
> **The precise ordering** (interface ≠ implementation): `use cases → aggregates + repo INTERFACES → services → repo IMPLEMENTATIONS → API/DB`. The interface belongs in the domain (it could even be introduced beside the aggregates in Step 8); only the *implementation* is genuinely "after the service." We folded the interface into this chapter for narrative tidiness.

---

## 10.2 The interfaces (in the domain layer)

A small generic base captures the universal `get`/`save`, and each aggregate adds only the queries its clients actually need — that last part is the **Interface Segregation Principle**: no client should depend on methods it doesn't use.

```python
# shared/exceptions.py  (add one — generic, used by every repo)
class EntityNotFoundError(DomainError): ...
```

```python
# shared/repository.py   (generic base — shared kernel, used by every subdomain)
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

ID = TypeVar("ID")
T  = TypeVar("T")

class Repository(ABC, Generic[ID, T]):
    """Collection-like abstraction over one aggregate root."""
    @abstractmethod
    def get(self, id: ID) -> T: ...          # raises EntityNotFoundError if missing
    @abstractmethod
    def save(self, aggregate: T) -> None: ...  # insert-or-update (upsert)
```

```python
# lending/domain/repository.py
from abc import abstractmethod
from datetime import date
from shared.repository import Repository
from shared.ids import LoanId, MemberId
from lending.domain.loan import Loan

class LoanRepository(Repository[LoanId, Loan]):
    # aggregate-specific queries — only what real use cases need (ISP)
    @abstractmethod
    def count_active_for_member(self, member_id: MemberId) -> int: ...   # UC-1 borrowing limit
    @abstractmethod
    def find_overdue(self, as_of: date) -> list[Loan]: ...               # UC-5 overdue list
```

```python
# each in its OWN subdomain's domain/repository.py (same shape):
#   catalog/domain/repository.py     → BookRepository, BookCopyRepository
#   membership/domain/repository.py  → MemberRepository
#   fines/domain/repository.py       → FineRepository
# (IDs come from shared.ids, so no cross-subdomain imports)
class BookRepository(Repository[BookId, Book]):
    @abstractmethod
    def search(self, keyword: str) -> list[Book]: ...                    # UC-7 search

class BookCopyRepository(Repository[CopyId, BookCopy]):
    @abstractmethod
    def find_available_for_book(self, book_id: BookId) -> list[BookCopy]: ...  # UC-3

class MemberRepository(Repository[MemberId, Member]):
    ...  # get/save are enough

class FineRepository(Repository[FineId, Fine]):
    @abstractmethod
    def find_unpaid_by_member(self, member_id: MemberId) -> list[Fine]: ...     # UC-6
```

Each interface lists *exactly* the queries the use cases from Step 2 require — no speculative methods (YAGNI). When Step 11 needs a new query, we add it here, driven by a real use case.

---

## 10.3 The in-memory implementations (in infrastructure)

Now the adapters. A `dict` keyed by id *is* a perfectly good aggregate store for development and tests — and crucially, it lets us run the entire system **with no database at all**. (At our scale of 100 members / 500 books, an in-memory store is arguably even production-viable for a single instance — but Step 11 notes the swap to a real DB.)

```python
# lending/infrastructure/in_memory_loan_repository.py
from datetime import date
from lending.domain.repository import LoanRepository
from shared.ids import LoanId, MemberId
from lending.domain.loan import Loan
from lending.domain.enums import LoanStatus
from shared.exceptions import EntityNotFoundError

class InMemoryLoanRepository(LoanRepository):
    def __init__(self):
        self._store: dict[LoanId, Loan] = {}

    def get(self, id: LoanId) -> Loan:
        try:
            return self._store[id]
        except KeyError:
            raise EntityNotFoundError(f"Loan {id} not found")

    def save(self, loan: Loan) -> None:
        self._store[loan.id] = loan                       # upsert

    def count_active_for_member(self, member_id: MemberId) -> int:
        return sum(1 for ln in self._store.values()
                   if ln.member_id == member_id and ln.status is LoanStatus.ACTIVE)

    def find_overdue(self, as_of: date) -> list[Loan]:
        return [ln for ln in self._store.values() if ln.is_overdue(as_of)]
```

```python
# catalog/infrastructure/in_memory_bookcopy_repository.py  (others follow the identical pattern)
class InMemoryBookCopyRepository(BookCopyRepository):
    def __init__(self): self._store: dict[CopyId, BookCopy] = {}
    def get(self, id):  
        try: return self._store[id]
        except KeyError: raise EntityNotFoundError(f"Copy {id} not found")
    def save(self, copy): self._store[copy.id] = copy
    def find_available_for_book(self, book_id):
        return [c for c in self._store.values()
                if c.book_id == book_id and c.is_available]   # also respects rule #6
```

The other three (`Book`, `Member`, `Fine`) are the same `dict` + query shape — mechanical. Notice the repositories use the **typed IDs as dict keys**, which works precisely because we made them frozen/hashable back in 8a. Small foundational decisions paying compound interest.

> **What's missing vs. a real DB?** Transactions. An in-memory dict can't roll back a half-finished `borrow_book`. A real implementation (SQLAlchemy in Step 11) wraps `borrow_book`'s saves in a single DB transaction — a **Unit of Work**. The *interfaces don't change*; only the adapter does. That's the whole point of the seam.

---

## 10.3.1 Where do DB models (ORM) go? — and why keep them separate

The in-memory repos above store live domain objects in a `dict`, so there's no "DB model" yet. But the moment you move to a real database (Step 11), a second kind of model appears — and **where it lives, and keeping it separate from the domain entity, is the decision that preserves everything we've built.**

There are **two different "models"** — don't conflate them:

| Model | What it is | Lives in |
|---|---|---|
| **Domain model** (`Loan`, `Member`) | the entity with behavior + invariants — **pure**, no ORM/DB annotations | `domain/` |
| **Persistence model** (`LoanRecord` / ORM class / table mapping) | how the data is *stored* — columns, table name, ORM mapping | `infrastructure/` |
| **Schema / migrations** (`CREATE TABLE`, Alembic) | the DDL | `infrastructure/` (e.g. `infrastructure/migrations/`) |

> **Rule: keep the domain model separate from the persistence model.** Do **not** put SQLAlchemy `Base` / Django `Model` / `@Column` on your domain `Loan` — that welds the domain to the ORM and breaks the "pure Python, zero framework imports" promise (§10.1). The repository **implementation maps between the two** — the **Data Mapper** pattern.

```
lending/domain/loan.py                          Loan            ← pure entity (no ORM)
lending/domain/repository.py                    LoanRepository  ← interface (port)
        ▲ implemented by
lending/infrastructure/models.py                LoanRecord      ← ORM/DB model (columns, table)  ← DB MODEL HERE
lending/infrastructure/sql_loan_repository.py   SqlLoanRepository ← maps Loan ⇄ LoanRecord
lending/infrastructure/migrations/              schema / DDL
```

```python
# lending/infrastructure/models.py — the persistence model (SQLAlchemy)
class LoanRecord(Base):
    __tablename__ = "loans"
    id         = Column(String, primary_key=True)
    member_id  = Column(String, index=True)
    copy_id    = Column(String)
    start_date = Column(Date); due_date = Column(Date)
    status     = Column(String)

# lending/infrastructure/sql_loan_repository.py — the adapter maps between the two worlds
class SqlLoanRepository(LoanRepository):
    def save(self, loan: Loan) -> None:
        rec = LoanRecord(id=str(loan.id), member_id=str(loan.member_id),
                         copy_id=str(loan.copy_id), status=loan.status.value, ...)  # domain → DB model
        self._session.merge(rec); self._session.commit()
    def get(self, id: LoanId) -> Loan:
        rec = self._session.get(LoanRecord, str(id)) or _raise_not_found(id)
        return self._to_domain(rec)                                                 # DB model → domain
```

**Why this separation is worth the mapping code:**
- The domain stays **pure and testable** (the same reason the in-memory repo works with plain objects).
- You can **change the schema** (denormalize, add indexes, switch Postgres→Mongo) without touching a domain rule.
- The ORM's concerns (lazy loading, sessions, columns) never leak into the model.

**The honest trade-off** (the Active Record question from earlier): some frameworks push you to make the ORM class *be* the domain object (annotate the entity directly). Less code, but it **couples the domain to the ORM** — fine for simple CRUD, wrong for a rich domain. We keep them separate on purpose.

> **In short:** the repository **interface** is a domain port (`domain/`); the **DB/ORM models, schema, and migrations** are persistence details (`infrastructure/`), kept *separate* from the domain entity; and the repository **implementation maps domain ⇄ persistence** (Data Mapper). Step 11 swaps the in-memory adapter for exactly this SQL adapter — and nothing in `domain/` or `application/` changes.

---

## 10.4 The composition root — wiring it all together

Everything has depended on interfaces and injected collaborators. *Somewhere* the concrete objects must be created and wired — that single place is the **composition root** (in `main`/startup, the outermost layer). It's the only place that knows *both* the interfaces and the implementations.

```python
# composition root (e.g. in main.py / a factory)
def build_library_service() -> LibraryService:
    members = InMemoryMemberRepository()
    books   = InMemoryBookRepository()
    copies  = InMemoryBookCopyRepository()
    loans   = InMemoryLoanRepository()
    fines   = InMemoryFineRepository()

    return LibraryService(
        members, copies, loans, fines,
        borrowing=BorrowingService(max_active_loans=2),
        fine_strategy=StandardFineStrategy(),
        clock=SystemClock(),
    )
```

To switch to Postgres later, you change **this function only** — swap `InMemoryLoanRepository()` for `SqlLoanRepository(session)`. Nothing in `domain/` or `application/` moves. *That* is Dependency Inversion delivering on its promise.

### What "composition root" actually means

- **Not a directory** — it's a *concept*: the **single place where the whole object graph is assembled** (concretes created + injected). Usually **one function/file**, not a folder.
- **Where** — the **outermost layer**, the entry point: `main.py`, a `bootstrap.py`/`container.py`, the web-app startup, or a `cli.py`. Run **once at startup**, before any use case executes.
- **Why it exists** — everything else depends on **interfaces** and receives collaborators via **injection**; but *something* must actually **instantiate** the concretes and plug them in. That's the composition root — the **only place that knows both the interfaces *and* the implementations.**
- **The payoff** — one place to **swap implementations** (in-memory ↔ SQL, `SystemClock` ↔ `FixedClock`), while every inner layer stays oblivious to which DB/framework you chose.
- **Each entry point has one** (often sharing a `build_*` factory):

  | Entry point | Its composition root |
  |---|---|
  | REST app | FastAPI startup / a `deps.py` factory |
  | CLI (`cli.py`) | calls `build_library_service()` in `main()` |
  | Tests | a fixture wiring **in-memory** repos + `FixedClock` |

- **The name:** *composition* (it assembles the object graph) + *root* (at the top/entry of the app).

> **In one line:** the composition root is the **single outermost function/file** (like this `build_library_service()`) where concretes are **created and injected** to build the object graph — the only place that knows both interfaces and implementations, so it's where you choose in-memory vs SQL while the inner layers stay oblivious. Not a directory.

---

## 10.5 Running the whole system end-to-end

With repositories in place, every layer from Steps 1–9 connects. Here's the full lending loop actually executing:

```python
svc = build_library_service()

# --- seed (Admin use cases UC-9, UC-10) ---
asha = Member(MemberId.new(), "Asha", "asha@example.com")
svc._members.save(asha)                                   # (via an admin service in real code)

book = Book(BookId.new(), ISBN("978-0132350884"), "Clean Code", "Robert C. Martin")
svc._books.save(book)
copy = BookCopy(CopyId.new(), book.id)
svc._copies.save(copy)

# --- UC-1: borrow ---
loan_id = svc.borrow_book(str(asha.id), str(copy.id))
# → BorrowingService approves (active=0 < 2, member active, copy available)
# → copy.issue() flips it to LOANED; Loan.create() sets due = today + 5
# → trying to borrow a 3rd active book later raises BorrowingLimitExceededError

# --- UC-2 + UC-4: return (say 7 days later, 2 days late) ---
fine_id = svc.return_book(loan_id)
# → loan.return_copy() computes days_overdue = 2 (the FACT)
# → StandardFineStrategy.calculate(2) = ₹10 (the POLICY)  → a Fine is saved
# → copy.return_copy() flips it back to AVAILABLE
```

Every design decision from the series is firing here: typed IDs, the `Book`/`BookCopy` split, the borrowing domain rule, the State transition on `Loan`, the fine **Strategy**, the repository seam — all working together, with **zero database and zero framework**. That's the proof the model is sound: it *runs* in pure Python.

---

## Principles in play

| Principle | How this step applied it |
|---|---|
| **DIP** (SOLID) | Repository **interfaces in the domain**, **implementations in infrastructure** — the dependency arrow points inward; the composition root is the only place that knows both. |
| **ISP** (SOLID) | Each repository exposes only the queries its real use cases need — no fat, do-everything interface. |
| **Persistence ignorance** | Domain & application work against `dict`-backed repos identically to a future SQL store; swapping is a one-function change. |
| **Repository pattern** | Collection-like access to whole aggregates; one repo per aggregate root; domain language, not SQL. |
| **YAGNI** | Query methods added only when a Step-2 use case demands them — no speculative API. |
| **Testability** | In-memory repos make the entire system runnable and unit-testable with no infrastructure. |

## Key takeaways (the transferable lessons)

1. **One repository per aggregate root**, dealing in whole aggregates — not one per table or per entity.
2. **Interface in the domain, implementation in infrastructure.** That single split is Dependency Inversion, and it's what makes storage a swappable detail.
3. **Repositories speak the domain language** and answer the "navigate backwards" queries (`find_active_by_member`) that by-ID references (Step 6) deliberately can't.
4. **Segregate interfaces (ISP):** each repo exposes only the queries its clients use; add methods when a real use case appears, not before.
5. **The composition root is where abstractions meet concretes** — keep that wiring in one outermost place, and the inner layers never learn what database you chose.
6. **If it runs in pure Python with in-memory repos, your model is sound.** Persistence and frameworks are details bolted on at the edge.

---

*Next — Step 11: Controllers / API. The final layer — a thin FastAPI adapter that turns HTTP requests into application-service calls, maps domain exceptions to status codes, defines request/response DTOs (Pydantic), and shows where a real database swaps in. After that, Step 12 collects the artifacts (diagrams + directory structure).*
