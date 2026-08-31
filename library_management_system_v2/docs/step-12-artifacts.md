# Step 12 — Artifacts (Finale)

*Series: Designing a Library Management System with DDD · Chapter 12 of 12*

---

Your `lld_basics.excalidraw` ends the DDD process with a checklist of deliverables: *class diagrams, ER diagrams, a user-journey/activity view, and the directory structure + framework*. This closing chapter produces all of them in one place — a reference you can hand to a new engineer (or a blog reader) — and then steps back for a retrospective: **every design decision, mapped to the principle that drove it.**

(Diagrams use Mermaid, which renders on GitHub. For Substack/LinkedIn, export them as images.)

---

## 12.1 Final directory structure

```
library_management_system_v2/
├── REQUIREMENTS.md
├── docs/                                  ← this 12-part series
└── src/
    ├── domain/                            ← PURE business logic (no framework imports)
    │   ├── ids.py                         BookId, CopyId, MemberId, LoanId, FineId
    │   ├── enums.py                       CopyStatus, LoanStatus, FineStatus
    │   ├── value_objects.py               Money, ISBN, DateRange
    │   ├── exceptions.py                  DomainError hierarchy
    │   ├── entities/
    │   │   ├── book.py · book_copy.py · member.py · fine.py
    │   │   ├── loan.py                     (aggregate root)
    │   │   └── loan_state.py               State pattern: ActiveState, ReturnedState
    │   ├── services/
    │   │   ├── borrowing.py                BorrowingService (domain service)
    │   │   └── fine_calculation.py         FineCalculationStrategy (+ Standard/Grace/Capped)
    │   └── repositories/                   ← INTERFACES (ports)
    │       ├── base.py                     Repository[ID, T]
    │       └── {book,book_copy,member,loan,fine}_repository.py
    ├── application/                        ← use-case orchestration
    │   ├── services.py                     LibraryService
    │   ├── dtos.py                          LoanView, ReturnView
    │   └── ports.py                         Clock, Notifier
    ├── infrastructure/                     ← ADAPTERS (implementations)
    │   ├── memory/                          InMemory*Repository
    │   └── sql/                             Sql*Repository (when a real DB is added)
    ├── api/                                ← thin HTTP layer
    │   ├── main.py · dtos.py · errors.py · dependencies.py
    │   └── controllers/                     book · loan · member
    └── composition.py                      ← composition root (wires it all)
```

The layout *is* the architecture: four layers, dependencies pointing inward, `domain/` importing nothing.

---

## 12.2 Use-case view (actors → use cases)

```mermaid
flowchart LR
    Member([Member]) --> UC1[Borrow a copy]
    Member --> UC2[Return a copy]
    Member --> UC6[Pay a fine]
    Member --> UC7[Search catalog]
    Librarian([Librarian]) --> UC3[Check availability]
    Librarian --> UC5[List overdue loans]
    Librarian --> UC8[Mark copy damaged/lost]
    Admin([Admin]) --> UC9[Manage books & copies]
    Admin --> UC10[Manage members]
    UC2 --> UC4[Assess late fine]
    System([System]) --> UC11[Notify member]
```

---

## 12.3 Domain class diagram

```mermaid
classDiagram
    class Book {
        +BookId id
        +ISBN isbn
        +str title
        +str author
        +update_metadata()
        +matches(keyword) bool
    }
    class BookCopy {
        +CopyId id
        +BookId book_id
        -CopyStatus _status
        +issue()
        +return_copy()
        +mark_damaged()
        +mark_lost()
        +is_available bool
        +is_visible_to_member bool
    }
    class Member {
        +MemberId id
        -bool _active
        +is_active bool
        +block()
        +unblock()
    }
    class Loan {
        +LoanId id
        +MemberId member_id
        +CopyId copy_id
        +DateRange period
        -LoanState _state
        +create()$ Loan
        +return_copy(on_date) int
        +is_overdue(as_of) bool
        +days_overdue(as_of) int
    }
    class Fine {
        +FineId id
        +MemberId member_id
        +LoanId loan_id
        -Money _amount
        -FineStatus _status
        +pay()
        +waive()
    }
    class Money { +int amount\n+str currency\n+add()\n+multiply() }
    class ISBN { +str value }
    class DateRange { +date start\n+date end\n+days_overdue(as_of) }
    class LoanState { <<abstract>>\n+return_copy(loan, on_date) }
    class BorrowingService { +check_can_borrow(member, copy, count) }
    class FineCalculationStrategy { <<abstract>>\n+calculate(days) Money }

    Book *-- ISBN : composition
    BookCopy ..> Book : book_id (by ID)
    Loan ..> Member : member_id (by ID)
    Loan ..> BookCopy : copy_id (by ID)
    Loan *-- DateRange : composition
    Loan *-- LoanState : State pattern
    Fine ..> Member : member_id (by ID)
    Fine ..> Loan : loan_id (by ID)
    Fine *-- Money : composition
    BorrowingService ..> Member : reads
    BorrowingService ..> BookCopy : reads
```

`*--` (composition) = inside an aggregate (Step 6); `..>` (dependency/by-ID) = across aggregates. Five single-entity aggregates, every cross-reference an ID.

## 12.4 Pattern & layer diagram

```mermaid
classDiagram
    class FineCalculationStrategy { <<interface>> }
    class StandardFineStrategy
    class GracePeriodFineStrategy
    class CappedFineStrategy
    FineCalculationStrategy <|.. StandardFineStrategy : Strategy
    FineCalculationStrategy <|.. GracePeriodFineStrategy
    FineCalculationStrategy <|.. CappedFineStrategy

    class LoanRepository { <<interface>> }
    class InMemoryLoanRepository
    class SqlLoanRepository
    LoanRepository <|.. InMemoryLoanRepository : Repository
    LoanRepository <|.. SqlLoanRepository

    class LibraryService
    LibraryService ..> LoanRepository : depends on interface (DIP)
    LibraryService ..> FineCalculationStrategy : depends on interface (DIP)
    LibraryService ..> BorrowingService
```

---

## 12.5 ER diagram (the persistence view)

```mermaid
erDiagram
    BOOK ||--o{ BOOK_COPY : "has copies"
    MEMBER ||--o{ LOAN : "borrows"
    BOOK_COPY ||--o{ LOAN : "is loaned in"
    LOAN ||--o| FINE : "may incur"
    MEMBER ||--o{ FINE : "owes"

    BOOK { string book_id PK
           string isbn
           string title
           string author }
    BOOK_COPY { string copy_id PK
                string book_id FK
                string status }
    MEMBER { string member_id PK
             string name
             bool active }
    LOAN { string loan_id PK
           string member_id FK
           string copy_id FK
           date borrow_date
           date due_date
           string status }
    FINE { string fine_id PK
           string member_id FK
           string loan_id FK
           int amount
           string status }
```

Every by-ID reference became a foreign key; every aggregate root became a table — exactly as Step 6 predicted.

## 12.6 Activity diagram — the *borrow* flow

```mermaid
flowchart TD
    A[POST /loans/borrow] --> B[Load Member, Copy; count active loans]
    B --> C{Member active?}
    C -- no --> E1[409 MemberBlocked]
    C -- yes --> D{Copy available?}
    D -- no --> E2[409 CopyNotAvailable]
    D -- yes --> F{Active loans < 2?}
    F -- no --> E3[409 BorrowingLimitExceeded]
    F -- yes --> G[copy.issue → LOANED]
    G --> H[Loan.create due = today + 5]
    H --> I[save copy + loan]
    I --> J[201 LoanResponse]
```

The three diamonds are the `BorrowingService` rules; everything below them is orchestration. Decisions = domain, steps = application.

---

## 12.7 Retrospective: decision → principle

The heart of the series in one table — *why* each decision was made, not just *what*:

| Decision | Driven by | Step |
|---|---|---|
| Built a glossary before any class | Ubiquitous Language | 1 |
| Split `Book` vs `BookCopy` | The right abstraction; per-copy rules | 1 |
| One bounded context, no microservices | KISS / match design to scale | 1 |
| `Money`/`ISBN`/typed IDs as value objects | Encapsulation, kill primitive obsession | 3, 8a |
| Invariants enforced in constructors/methods | Make illegal states unrepresentable | 4, 8 |
| Separated "₹5/day" (policy) from "Money ≥ 0" (invariant) | Policy vs invariant → Strategy seam | 4, 8b |
| Five small aggregates, reference by ID | Small aggregates, low coupling, low contention | 5 |
| `Member` does **not** count its own loans | Aggregate boundary as a responsibility limit | 5, 7 |
| Unidirectional by-ID references | Single source of truth, small aggregates | 6 |
| Rich entities with guarded commands | Tell-Don't-Ask, Information Expert, anti-anemic | 7, 8 |
| `BookCopy` = transition table, not State pattern | KISS — no divergent per-state behavior | 8b |
| Fine calculation as a Strategy | OCP / LSP / DIP — swappable policy | 8b |
| `Loan.create()` factory | Guarantee creation invariants | 8b |
| Domain service vs application service split | SRP — rules vs orchestration | 9 |
| `Clock`/`Notifier` ports | DIP, testability | 9 |
| Repository interface in domain, impl in infra | DIP, persistence ignorance | 10 |
| DTOs at the API; entities never serialized | Information hiding, stable contract | 11 |
| One `DomainError` → HTTP handler | OCP at the error boundary | 11 |
| Rule #6 as a role-based query filter | Separation of invariant vs visibility | 4, 11 |

## 12.8 Where each pattern & principle lives

- **OOP:** Encapsulation (every VO/entity), Composition over inheritance (entities ◆ VOs), Abstraction (Book/BookCopy), Tell-Don't-Ask (entity commands).
- **SOLID:** SRP (layers, services), OCP (fine Strategy, error handler), LSP (strategies/repos substitutable), ISP (per-aggregate repo interfaces), DIP (repos, ports, composition root).
- **GoF patterns:** **Strategy** (fine calc), **State** (loan lifecycle), **Factory Method** (`Loan.create`), **Repository** (persistence), plus the **Decorator** idea in `CappedFineStrategy` and where **Observer** would slot in (domain events for notifications).
- **GRASP:** Information Expert (responsibility placement).
- **Restraint principles:** KISS / YAGNI / DRY throughout — the reason we *didn't* use microservices, *didn't* force the State pattern on `BookCopy`, and *didn't* build a domain-event bus we don't yet need.

---

## 12.9 What we'd build next (and what we deliberately didn't)

Honest scope boundaries — each one a *conscious* deferral, not an oversight:

| Deferred | Why it was right to defer | When to add it |
|---|---|---|
| Real database (SQL) | Persistence is a detail; in-memory ran the whole model | Step 11's adapter swap — interfaces ready |
| Authentication/roles | Generic subdomain, not core | Plug in at the API edge |
| Domain events + Observer | KISS — one notifier call suffices now | When reactions multiply (notify + log + stats) |
| CQRS / read models | No read/write scaling pressure at 100 members | If queries dwarf writes |
| Tests | (You'd write these alongside — pure domain makes them trivial) | Continuously |

> The recurring theme of the whole series: **every "we didn't do X" was a decision, justified by scale and the problem at hand — not a gap.** Knowing what to leave out is the senior skill.

---

## 12.10 The one-paragraph summary of the whole journey

We started with a flat requirements doc and a temptation to type `class Book`. Instead we built a **shared language**, mapped the **use cases**, classified concepts into **entities and value objects**, pinned down **invariants**, derived **aggregate boundaries** from those invariants, formalized **relationships by ID**, wrote each aggregate's **responsibilities**, then turned all of it into **code** — value objects, rich entities, the **Strategy** and **State** patterns where (and only where) a real problem demanded them. We gave cross-aggregate logic a home in **domain services**, orchestrated use cases in **thin application services**, hid storage behind **repository interfaces**, and exposed it all through a **thin API** — with SOLID as the constant background check and design patterns earning their place rather than being imposed. The result runs in pure Python, swaps its database with a one-line change, and — most importantly — **reads like the business it models.**

---

*Series complete. Thank you for following along — the design is done, the model is sound, and every decision has a reason you can point to. Go build something.*
