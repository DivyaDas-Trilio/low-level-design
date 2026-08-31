# Step 6 — Relationships Among Aggregates

*Series: Designing a Library Management System with DDD · Chapter 6 of 12*

---

Step 5 gave us five aggregates that point at each other **by ID**. This chapter turns those loose pointers into a precise **relationship map**: *how many* of each (cardinality), *which way* the reference points (direction), and *what kind* of relationship it is (the OOP spectrum — association, aggregation, composition). The output is the skeleton of our **class diagram** and **ER diagram** — the artifacts Step 12 will polish.

There's a neat unifying idea in this step:

> **Inside an aggregate, objects relate by direct reference (composition). Across aggregates, they relate by ID (association). The aggregate boundary *is* the line between those two worlds.**

---

## 6.1 The OOP relationship spectrum (from your LLD notes)

Your `lld_basics.excalidraw` lists six object relationships. Let's define each with an LMS example and — crucially — map it to DDD. They run from *weakest coupling* to *strongest*.

| Relationship | Plain meaning | Lifecycle link? | LMS example | UML arrow |
|---|---|---|---|---|
| **Dependency** | "A *uses* B temporarily" (a parameter, a local var) | none | `BorrowingService` *uses* a `MemberRepository` passed to a method | `- - -▷` (dashed) |
| **Association** | "A is *connected to* B" (knows about it, longer-term) | independent lifecycles | `Loan` is associated with a `Member` (via `member_id`) | `───▶` |
| **Aggregation** | "A *has* B, but B can live without A" (shared/loose ownership) | independent | A `Member` *has* `Loan`s, but a loan's record outlives... (weak "has-a") | `◇───` (hollow diamond) |
| **Composition** | "A *owns* B; B dies with A" (exclusive ownership) | **bound** — part dies with whole | A `Fine` *is composed of* a `Money`; a `Loan` *owns* its `DateRange` | `◆───` (filled diamond) |
| **Inheritance** | "A *is a* B" (subtype) | n/a | `BorrowingLimitExceededError` *is a* `DomainError` | `───▷` (hollow triangle) |
| **Realization** | "A *implements* interface B" | n/a | `InMemoryLoanRepository` *realizes* `LoanRepository` | `- -▷` (dashed triangle) |

**The DDD translation — and this is the key insight:**

- **Composition** = *inside an aggregate*. The part has no independent identity or lifecycle; it's owned exclusively by the root and dies with it. → Entities composing **Value Objects** (`Fine ◆── Money`, `Loan ◆── DateRange`).
- **Association / Aggregation** = *across aggregate boundaries*. Both sides have independent lifecycles, so we **reference by ID**, never by object (Step 5's cardinal rule). → `Loan ──▶ Member` (by `member_id`).
- **Realization** = our **repository pattern** (Step 10): concrete classes implement domain interfaces.
- **Dependency** = how **services** get their collaborators (Step 9), enabling Dependency Inversion.
- **Inheritance** = used sparingly — mainly our **exception hierarchy**. (We prefer composition over inheritance for domain logic; recall Step 3.)

> **Rule of thumb:** *Composition lives inside aggregates; association/aggregation crosses between them.* If you find yourself wanting composition (a direct object reference, shared lifecycle) across an aggregate boundary, that's a signal the two things might actually belong in the *same* aggregate — go back and re-check Step 5.

### Within-aggregate vs. across-aggregate relationships

There are actually **two relationship regimes**, and the aggregate boundary is the switch between them. This matters the moment an aggregate contains more than one *entity*.

| | **Within an aggregate** (root ↔ child entity) | **Across aggregates** |
|---|---|---|
| Reference style | **Direct object reference** (`self._copies: list[BookCopy]`) | **By ID** (`copy_id: CopyId`) |
| Identity scope | **Local** — unique only inside the aggregate (copy #3 *of this book*) | **Global** (a system-wide UUID) |
| Who may call its methods | **Only the root** — outsiders go through the root | Each reached via its own repository |
| Lifecycle | Child created/deleted by the root, **dies with it** (composition) | Independent lifecycles |
| Persistence | Whole aggregate **loaded & saved as one unit** | One repository per root |

**A crucial observation about *our* model:** every aggregate we built (`Book`, `BookCopy`, `Member`, `Loan`, `Fine`) is a **single entity composed only of value objects** — none contains another *entity*. So our only intra-aggregate relationship is entity → value object (composition, `◆`). We **dissolved the child-entity problem entirely** by keeping aggregates small (Step 5) and referencing everything else by ID. That's a feature, not a gap.

**If we *had* chosen the alternative** — `Book` as a root that *contains* its `BookCopy` children — the within-aggregate rules would apply, and you'd never touch a copy directly:

```python
class Book:                                   # aggregate ROOT
    def __init__(self, book_id, isbn, title):
        self.id, self.isbn, self.title = book_id, isbn, title
        self._copies: dict[int, BookCopy] = {}    # children by LOCAL id (object refs)

    def add_copy(self) -> int:                    # children created THROUGH the root
        local_no = len(self._copies) + 1          # local identity, not a global UUID
        self._copies[local_no] = BookCopy(local_no)
        return local_no

    def issue_copy(self, copy_no: int) -> None:   # ALL child ops go through the root
        self._copies[copy_no].issue()             # outsiders can't reach the copy directly

    @property
    def available_count(self) -> int:             # an invariant SPANNING children
        return sum(c.is_available for c in self._copies.values())
```

> **The strategy in one line:** *inside* an aggregate → object references + local identity + root-mediated access, saved as one unit; *across* aggregates → by-ID references + global identity + separate repositories. And the best first move is to make aggregates small enough that you have **no child entities at all** — which is exactly what we did.

---

## 6.2 Cardinality — how many of each?

Now we pin down the numbers. Read `1 ──< *` as "one-to-many."

| Relationship | Cardinality | Meaning |
|---|---|---|
| `Book` → `BookCopy` | **1 ──< \*** | One book (title) has many physical copies. |
| `BookCopy` → `Loan` | **1 ──< \*** over time, **1 ── 0..1** *active* | A copy has many loans across its life, but **at most one active loan** at any moment. |
| `Member` → `Loan` | **1 ──< \*** over time, **1 ── 0..2** *active* | A member has many loans historically, but **0 to 2 active** (the borrowing-limit rule). |
| `Loan` → `Fine` | **1 ── 0..1** | A loan produces at most one fine (only if returned late). |
| `Member` → `Fine` | **1 ──< \*** | A member can accumulate many fines over time. |

Notice how the **invariants from Step 4 show up as cardinality constraints**: "≤ 2 active loans" *is* the `0..2` on the active `Member → Loan` relationship; "a copy can only be issued if available" *is* the `0..1` active loan per copy. Cardinality and invariants are two views of the same rules.

---

## 6.3 Direction — which way does the reference point?

This is subtle and important. A relationship can be **unidirectional** (A knows B, but B doesn't know A) or **bidirectional** (both know each other). **In DDD we strongly prefer unidirectional references across aggregates**, and we point them in the direction the *child* depends on the *parent*.

```
Book        ◄────────  BookCopy     (BookCopy holds book_id; Book doesn't list its copies)
Member      ◄────────  Loan         (Loan holds member_id; Member doesn't hold a loan list)
BookCopy    ◄────────  Loan         (Loan holds copy_id)
Member      ◄────────  Fine         (Fine holds member_id)
Loan        ◄────────  Fine         (Fine holds loan_id)
```

**Why the "many" side holds the reference (and not the other way):**

- If `Member` held a `List[Loan]`, then loading a member would tempt you to load all their loans — re-creating the big-aggregate problem we rejected in Step 5. Keeping the reference on `Loan` keeps `Member` small.
- **Bidirectional references are a trap.** If `Member` knows its `Loan`s *and* each `Loan` knows its `Member`, you now have two places that can disagree, and updates must keep both in sync. Unidirectional = one source of truth.
- **"But how does a member find their loans then?"** Through a **query on the repository**: `loan_repository.find_active_by_member(member_id)`. The relationship is navigated via the repository, not via an in-memory object graph. This is the practical consequence of "reference by ID."

> **Transferable lesson:** *navigation direction is a design decision, not an afterthought.* Point references from the dependent (many) side to the stable (one) side, keep them unidirectional, and let repositories answer the "give me the other direction" questions.

---

## 6.4 The class diagram skeleton

Putting cardinality + direction + relationship-type together (`◆` = composition / inside aggregate; `──▶` = association by ID / across aggregates):

```
        ╔═══════════════ AGGREGATE BOUNDARIES (║) ═══════════════╗

  ║ Book ║            ║ BookCopy ║              ║ Member ║
  ┌──────────┐        ┌───────────────┐        ┌──────────┐
  │ id:BookId│        │ id:CopyId     │        │ id:MemberId
  │ ◆ ISBN   │◄───────│ book_id ─────▶│        │ name,... │
  │ title    │ assoc. │ ◆ CopyStatus  │        └──────────┘
  │ author   │ (id)   └───────────────┘             ▲
  └──────────┘              ▲                        │ member_id (assoc, id)
                            │ copy_id (assoc, id)    │
                       ┌────┴──────────────┐    ┌────┴───────────┐
                       │       Loan        │───▶│ (Member, by id)│
                       │ id:LoanId         │    └────────────────┘
                       │ member_id ───────▶│
                       │ copy_id   ───────▶│
                       │ ◆ DateRange       │         ║ Fine ║
                       │ ◆ LoanStatus      │    ┌──────────────────┐
                       └───────────────────┘◄───│ id:FineId        │
                                  loan_id (id)   │ member_id ──────▶│
                                                 │ loan_id   ──────▶│
                                                 │ ◆ Money          │
                                                 │ status           │
                                                 └──────────────────┘

  ◆ = composition (Value Object inside the aggregate; dies with the root)
  ──▶ = association across aggregates (held as an ID, resolved via a repository)
```

Every `◆` is *inside* a boundary; every `──▶` *crosses* one. That visual rule is the whole chapter in one picture.

---

## 6.5 The ER diagram skeleton

The same model from a *persistence* angle (foreign keys are how "reference by ID" looks in a database). This previews Step 10/11.

```
BOOK(book_id PK, isbn, title, author, genre)
        │ 1
        │
        │ *                              ┌────────────────────────────────┐
BOOK_COPY(copy_id PK, book_id FK → BOOK, status)                          │
        │ 1                                                               │
        │                                                                 │
        │ *                                                               │
LOAN(loan_id PK, member_id FK → MEMBER, copy_id FK → BOOK_COPY,           │
     borrow_date, due_date, status)                                       │
        │ 1                                                               │
        │                                                                 │
        │ 0..1                                                            │
FINE(fine_id PK, member_id FK → MEMBER, loan_id FK → LOAN, amount, currency, status)

MEMBER(member_id PK, name, email, ...) ──1──< LOAN, ──1──< FINE
```

**The pleasing part:** every "by-ID reference" from the domain becomes a **foreign key** in the database, and every aggregate root becomes (roughly) its own **table** with its own primary key. The clean domain boundaries translate directly into a clean schema — no accident, that's the payoff of doing Step 5 properly.

> #### 🗄️ Note: when does persistence / the ERD actually enter the picture?
>
> **DDD is "persistence-ignorant" — the domain is designed as if the database doesn't exist, and storage is plugged in last.** So why is there an ERD *here*, in Step 6?
>
> Because there are **two different uses** of an ERD, and this is the harmless one:
>
> - ✅ **As a sanity check (what we just did).** A quick sketch to *confirm* our aggregate boundaries map onto a sane schema. If you *can't* draw clean foreign keys here, it's a smell that your aggregates (Step 5) are wrong. The ERD is validating the model, not designing storage.
> - ❌ **As the source of truth (NOT yet).** Committing to columns, indexes, normalization, and ORM mappings now would couple our business logic to a storage decision far too early.
>
> **The real persistence design happens later:**
> - **Step 10 — Repositories:** define persistence-ignorant repository *interfaces* in the domain (we now know exactly what each aggregate must load/save), plus simple in-memory implementations.
> - **Step 11 — Infrastructure/API:** the concrete database, real tables/ORM mappings, and indexes for hot queries (e.g. the overdue-loans lookup).
>
> **Why defer?** Storage is a reversible detail; the model isn't. ERDs are shaped by *access patterns*, which only become clear after use cases + aggregates are settled. And keeping the domain DB-free is what makes it pure and unit-testable (zero framework imports).
>
> **Rule of thumb:** is the hard part the *behavior/rules* or the *data/queries*? Behavior-heavy systems (like this LMS) → **model the domain first, persist last.** Data-/reporting-heavy systems (warehouses, analytics) → storage and access patterns legitimately move earlier, because the data model *is* the core domain.

---

## Principles in play

| Principle | How this step applied it |
|---|---|
| **Low coupling** | Unidirectional, by-ID references across aggregates — no tangled bidirectional object graphs to keep in sync. |
| **High cohesion** | Composition (`◆`) keeps a root and its value objects tightly together inside one boundary. |
| **Composition over inheritance** (OOP) | Inheritance is confined to the exception hierarchy; the domain is built by composing VOs into entities. |
| **DIP (preview)** | "Realization" relationships (repos implementing domain interfaces) set up Dependency Inversion for Step 10. |
| **SRP** | Repositories — not the entities — answer "navigate the relationship the other way," keeping entities focused on behavior. |

## Key takeaways (the transferable lessons)

1. **The aggregate boundary is the line between two relationship worlds:** composition (direct reference, shared lifecycle) *inside*; association by ID *across*.
2. **Cardinality and invariants are the same rules seen twice.** "≤ 2 active loans" is the `0..2` on the active `Member → Loan` edge.
3. **Point references from the many side to the one side, and keep them unidirectional.** It keeps aggregates small and gives you a single source of truth.
4. **Navigate "the other direction" via repositories, not object graphs.** `find_active_by_member(member_id)` replaces a `member.loans` list.
5. **Clean aggregate boundaries become a clean schema for free** — by-ID references turn into foreign keys, roots into tables.

---

*Next — Step 7: Aggregate Responsibilities. We give each aggregate root a crisp job description — the commands it accepts, the invariants it guards, and (just as importantly) what it must NOT do — turning the structural map into a behavioral contract, ready to become code in Step 8.*
