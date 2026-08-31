# Step 9 — Domain & Application Services

*Series: Designing a Library Management System with DDD · Chapter 9 of 12*

---

In Step 7 several behaviors got pushed *out* of the aggregates because they didn't belong to any single one — "can *this member* borrow *this copy*?", "enforce ≤ 2 active loans." This chapter gives that homeless logic a home. But there's a catch that trips up almost everyone:

> **There are *two* completely different kinds of "service," and conflating them is the most common DDD mistake.**

Your `lld_basics.excalidraw` said *"service layer per aggregate,"* and back in Step 1 I flagged that phrasing as something to split. Here's the split, made concrete.

---

## 9.1 The two services, side by side

| | **Domain Service** | **Application Service** (use case) |
|---|---|---|
| **Layer** | `domain/` (pure) | `application/` |
| **Contains** | **Business rules** that span multiple aggregates | **Orchestration** — the recipe for a use case |
| **Knows about** | Domain objects only | Repositories, transactions, the outside world |
| **Business logic?** | **Yes** — it *is* domain logic | **No** — it only coordinates |
| **State** | Stateless | Stateless |
| **Example** | `BorrowingService.can_borrow(...)` decides eligibility | `borrow_book(member_id, copy_id)` loads, calls, saves |
| **Talks to a database?** | **Never** | Yes (via repository interfaces) |

The cleanest way to remember it:

> **A Domain Service answers a *business question*. An Application Service runs a *use case*.** The domain service *decides*; the application service *orchestrates* (load → decide → mutate → save).

> #### 🤔 Sidebar: why two services and not one?
>
> It feels like bureaucracy until you see what *merging* them costs. The two answer fundamentally different questions — one is **business knowledge** (*"is this allowed?"*), the other is **plumbing** (*"how do I carry out this request, fetch/save/commit?"*). They change for different reasons → SRP says split them.
>
> **Imagine cramming the rules inline into one `borrow_book()`** (mixing `repo.get()`/`repo.save()` with the `if active >= 2` checks). Four problems appear:
>
> 1. **You can't test the rules without a database.** The borrowing policy is tangled with repositories and transactions. A standalone `check_can_borrow(member, copy, count)` tests with three plain objects — zero infrastructure.
> 2. **The rule can't be reused.** A bulk-import, or a *"what can I borrow?"* preview screen, needs the same rule — but it's trapped inside one use case's save-everything machinery.
> 3. **The rules get lost in the noise.** Business policy hides among `get`/`save` boilerplate; a reviewer can't find what matters.
> 4. **The domain stops being pure.** If the rule lives in a service that also calls repositories, your business logic is coupled to infrastructure — and the whole inward-pointing architecture (§9.6) collapses.
>
> **Analogy 🍳:** a domain service is the **chef's judgment** ("needs more salt") — pure expertise, portable to any kitchen. An application service is the **recipe steps** ("fetch from fridge, preheat, plate, serve") — logistics. Cram the judgment into one recipe and it's trapped there; keep it separate and *every* recipe can call on the chef.
>
> **The honest nuance:** **not every use case needs a domain service.** A use case with no cross-aggregate rule (e.g. "update a book's title") just calls `book.update_metadata()` and saves — *no domain service exists*. Create one **only** when there's genuine business logic spanning aggregates. Forcing an empty domain service onto every use case is exactly the *"service layer per aggregate"* over-engineering we flagged in Step 1.

---

## 9.2 The Domain Service — `BorrowingService`

A domain service holds business logic that legitimately spans aggregates. Two design rules keep it clean:

1. **It's stateless** — no fields holding entities between calls; it's pure logic.
2. **It's given the data it needs; it does not fetch it.** No repository access inside a domain service — that keeps it in the pure domain layer and trivially unit-testable. (The *application* service gathers the data and hands it in.)

```python
# lending/domain/borrowing_service.py
from lending.domain.exceptions import (
    BorrowingLimitExceededError, MemberNotActiveError,   # both owned by lending
)

class BorrowingService:
    """Borrowing policy: may a member take another loan?

    Pure & stateless, and GIVEN plain values — never foreign objects (no `Member`,
    no `BookCopy`). So `lending` imports nothing from `membership` or `catalog`,
    keeping the split seam clean (Option 1). rule #4 is configurable, not hard-coded.
    """
    def __init__(self, max_active_loans: int = 2):
        self._max_active_loans = max_active_loans

    def check_can_borrow(self, *, member_active: bool, active_loan_count: int) -> None:
        """Raise a DomainError if the borrow is disallowed; return normally if OK."""
        if not member_active:                              # a membership FACT, passed as a value
            raise MemberNotActiveError("member is blocked")
        if active_loan_count >= self._max_active_loans:    # the ≤ 2 rule (Loan aggregate)
            raise BorrowingLimitExceededError("borrowing limit reached")
        # NOTE: copy availability is the copy's OWN invariant — enforced by copy.issue()
        # at the mutate step (catalog), so the borrowing policy needn't re-check it.
```

> Add `MemberNotActiveError` to `lending/domain/exceptions.py` (it's a *lending* borrowing-policy error — a blocked member being *denied a loan* is a lending decision, expressed over a boolean value, so it stays in `lending`).

This is *pure domain logic*: it encodes the borrowing policy over **plain values** — a membership fact (`member_active`) + the loan count — with **no `Member` or `BookCopy` object**, so `lending` imports nothing from `membership`/`catalog` (the microservice seam stays clean, per Option 1). It touches no database, no framework; test it with a `bool` and an `int`. The *"≤ 2"* rule relocated from `Member` in Step 5 finally lands here.

> **Why pass values, not objects?** In our **vertical-slice** layout, a subdomain must not import another subdomain's internals (that's what keeps each one independently extractable). Handing the service a `Member`/`BookCopy` would make `lending` depend on `membership`/`catalog`. Passing **primitives** (the application service reads `member.is_active` and the loan count, then passes them in) keeps the domain service pure *and* the dependency graph clean.

> **Domain service vs. entity method — how to choose?** If the logic needs data from **one** aggregate, it's a *method on that aggregate* (Information Expert, Step 7). If it needs data from **several** aggregates at once, it's a *domain service*. `check_can_borrow` needs a membership fact *and* the loan count → domain service. `copy.issue()` needs only the copy → entity method.

---

## 9.2.1 FAQ: can an Entity read from a repository / DB / cache?

The rule for domain services in §9.2 — *"given its data, never fetches it"* — applies just as strictly to **entities and value objects**. They're the purest part of the domain, so the answer is blunt:

> **No. An Entity must never reach into a repository, database, or cache.** It only knows its own data and its own rules.

**Why** — three reasons, all the same architecture from §9.6:

1. **Dependency direction.** Dependencies point *inward* (api → application → domain). A repository lives in `infrastructure/`, the outermost ring. An Entity calling it makes the innermost layer depend on the outermost — the arrow reverses and the layering collapses.
2. **It destroys testability.** `Member(...).borrow(copy)` tests with plain objects, no DB, instant. The moment `borrow()` calls a repo, you can't test the rule without standing up (or mocking) persistence.
3. **Hidden I/O.** `loan.return_copy()` *looks* like a pure state change. If it secretly does a DB read, you get surprise latency, failures, and transactions buried inside what reads like business logic.

### So how does an Entity get data it doesn't have?

The principle: **the Entity never fetches — someone outside fetches first and hands the data in.** That someone is the application service (load → decide → mutate → save). Four techniques, in the order you should reach for them:

| Situation | Technique |
|---|---|
| Entity needs another **object** | **Load it in the app service, pass it in** — `def borrow(self, copy: BookCopy)`. The signature *demands* the data, so the Entity can't proceed without being given it. |
| Entity needs **one fact/number** | **Compute it outside, pass the value** — `def borrow(self, copy, active_loan_count: int)`. Hand it the answer, not the data source. |
| Rule spans **two aggregates** | **Domain service**, handed both loaded objects (§9.2) — not an entity method at all. |
| Genuinely needs **lazy / on-demand** lookup | **Inject a domain-defined *port*** (an interface in `domain/`, implemented by infrastructure) — see below. |

```python
# ❌ Entity reaches out — domain now depends on infrastructure
def borrow(self, copy_id, copy_repo):
    copy = copy_repo.get(copy_id)

# ✅ Application loads it; Entity operates only on what it was given
def borrow(self, copy: BookCopy) -> Loan:
    copy.issue()
```

### The rare case: a domain-owned port (Dependency Inversion)

When pre-loading really is awkward and the domain needs a fact at decision time, define an **interface in the domain** that expresses the *need* in domain language — and let infrastructure implement it. The domain depends on the **abstraction**, never on the DB or cache:

```python
# catalog/domain/ports.py — the subdomain OWNS the interface
from shared.ids import CopyId
class CopyAvailability(Protocol):
    def is_available(self, copy_id: CopyId) -> bool: ...

# catalog/infrastructure/ provides a Redis- or DB-backed implementation.
```

This keeps the dependency arrow pointing inward (the SOLID **D**) — the same trick as the `Clock`/`Notifier` ports in §9.4. Reach for it only when techniques 1–3 don't fit; it's heavier.

> **The throughline for your distributed cache, too:** the domain expresses *what* it needs; infrastructure decides *how* to get it. A Redis cache is an implementation detail of a repository or a port — **the Entity never knows Redis exists.** That obliviousness is exactly what keeps `borrow`/`return` pure and fast to test.

---

## 9.3 The Application Service — the use case orchestrator

The application service is the **thin** layer that runs a use case start to finish. Its job is a fixed recipe:

> **load** the aggregates (via repositories) → **decide** (call domain methods / domain services) → **mutate** the aggregates → **save** them → return a result. **It contains no business rules of its own.**

It depends on **repository interfaces** (the ports we'll formally define in Step 10) and on the domain service — all **injected** (Dependency Inversion). It never imports infrastructure.

`borrow`/`return` are **lending use cases**, so this orchestrator lives in `lending/application/`. Note it *does* compose several subdomains — it holds the `member`, `copy`, `loan`, `fine` **repository interfaces** and constructs `Fine` — reaching them through their **public APIs** (entities + repo interfaces). That's allowed at the **application layer** (orchestrating a cross-cutting use case); the strict "no cross-subdomain imports" rule applies to the **domain** layer, which is why `BorrowingService` above took plain values. On a future split, this orchestration is what becomes a **saga** across services.

```python
# lending/application/library_service.py   (composes lending + catalog + fines via their public APIs)
from datetime import date
from shared.ids import MemberId, CopyId, LoanId, FineId
from lending.domain.loan import Loan
from lending.domain.borrowing_service import BorrowingService
from fines.domain.fine import Fine
from fines.domain.fine_calculation import FineCalculationStrategy

class LibraryService:
    def __init__(self, members, copies, loans, fines,      # repository INTERFACES (Step 10)
                 borrowing: BorrowingService,
                 fine_strategy: FineCalculationStrategy,
                 clock):                                    # a Clock port (testable time)
        self._members, self._copies = members, copies
        self._loans, self._fines = loans, fines
        self._borrowing = borrowing
        self._fine_strategy = fine_strategy
        self._clock = clock

    # --- UC-1: borrow a book ---
    def borrow_book(self, member_id: str, copy_id: str) -> str:
        member = self._members.get(MemberId(member_id))      # LOAD
        copy   = self._copies.get(CopyId(copy_id))
        active = self._loans.count_active_for_member(member.id)

        self._borrowing.check_can_borrow(                    # DECIDE (domain service) — VALUES, not objects
            member_active=member.is_active, active_loan_count=active)

        copy.issue()                                          # MUTATE (also guards copy availability)
        loan = Loan.create(member.id, copy.id, self._clock.today())

        self._copies.save(copy)                               # SAVE
        self._loans.save(loan)
        return str(loan.id)

    # --- UC-2 + UC-4: return a book, assess a fine if late ---
    def return_book(self, loan_id: str) -> str | None:
        loan = self._loans.get(LoanId(loan_id))              # LOAD
        copy = self._copies.get(loan.copy_id)

        days_overdue = loan.return_copy(self._clock.today()) # DECIDE (entity: state + fact)
        copy.return_copy()

        fine_id = None
        if days_overdue > 0:                                 # late → POLICY produces Money
            amount = self._fine_strategy.calculate(days_overdue)
            fine = Fine(FineId.new(), loan.member_id, loan.id, amount)
            self._fines.save(fine)
            fine_id = str(fine.id)

        self._loans.save(loan)                               # SAVE
        self._copies.save(copy)
        return fine_id
```

See how **thin** it is — there's not a single business rule in here. "Can they borrow?" is delegated to the domain service; "what does late cost?" is delegated to the strategy; "is the copy issuable?" is guarded inside `copy.issue()`. The application service is pure *choreography*. That thinness is the goal: business rules belong in the domain, never leaked into orchestration.

---

## 9.3.1 Cross-subdomain use cases — where they live and how they compose

`borrow_book` spans **lending + catalog + membership + fines**. A cross-cutting use case must live *somewhere* — here's where, and how it talks to the participants.

### Where it lives — two placements

**Option A — in the subdomain that *owns* the use case (its "center of gravity").** Most cross-cutting use cases have a clear **primary** subdomain; the rest are *participants*. "Borrow" is fundamentally a **Lending** action → `lending/application/`. Ask: *"whose core responsibility is this?"* → it goes there. (This is what we did.)

**Option B — a dedicated top-level orchestration module** (`src/application/` or `src/orchestration/`) that sits above the subdomains and composes them. Use it when there's **no clear owner**, or to keep each subdomain **maximally decoupled** (none depends on another).

| | Option A (owning subdomain) | Option B (orchestration layer) |
|---|---|---|
| When | a clear primary subdomain exists | no clear owner / want subdomains fully decoupled |
| Cost | owner depends on participants (downstream) | an extra layer that knows everyone |
| LMS | ✅ `borrow`/`return` → `lending/application/` | overkill at our scale |

### How it talks to the participants — public APIs only

The **application layer may compose subdomains** (the strict "no cross-subdomain imports" rule is a *domain*-layer rule) — but only through **public APIs**, never internals. Two styles:

- **(a) Direct composition, synchronous** (what we do): the orchestrator holds the participants' **repository/application-service interfaces** (injected) and calls them. Simple, in-process, one transaction — best in a monolith.
- **(b) Event-driven, asynchronous** (looser coupling): the owner does its part, then publishes a **domain event**; participants react and the owner needn't know they exist.
  ```python
  events.publish(LoanReturnedLate(loan_id, member_id, days_overdue=2))
  # fines/ subscribes → assess a Fine   notifications/ subscribes → email the member
  ```
  Lending imports neither `fines` nor `notifications`. Reach for this when reactions multiply.

### Keep the dependency graph acyclic
When `lending/application` depends on `catalog`/`membership`/`fines`, lending is **downstream** (a Customer/Supplier relationship) — fine **as long as it's acyclic**. If a participant ever needed to call back into lending, that **cycle** is a smell → break it with an **event**, or rethink the boundary. Always depend on **public contracts** (interfaces, events), not entity internals.

### What to avoid
- ❌ Cross-cutting logic in any subdomain's **domain** layer (domain stays pure + single-subdomain — that's why `BorrowingService` took *values*).
- ❌ **Cyclic** subdomain dependencies.
- ❌ Reaching into another subdomain's **internals**.

### On a microservice split
- Option A + sync → the owner service calls the others over the network, or a **saga** for the multi-step transaction.
- Event-driven → in-process events become **real broker events** (the cleanest split; publishers/subscribers unchanged).
- Option B → the orchestration module becomes an **orchestrator / saga coordinator** service.

> **In one line:** a cross-subdomain use case lives in the **application layer of the subdomain that owns it** (its center of gravity), or a **dedicated orchestration module** when there's no owner; it reaches participants only through their **public APIs** — **synchronously** (injected interfaces) in a monolith, or via **domain events** for looser coupling — keeping the dependencies **acyclic**. The application layer may compose subdomains; the domain layer may not.

---

## 9.3.2 When a domain service needs data from *multiple subdomains*

A follow-on doubt: a domain service is pure and can't import another subdomain — so what if the rule needs data from entities in **different** subdomains? Separate three cases:

| Case | Where the entities are | How it's handled |
|---|---|---|
| **1** | multiple entities **inside one aggregate** (root + children) | the **aggregate root** handles it — no service needed |
| **2** | multiple aggregates **in the same subdomain** | a **domain service** takes the actual **aggregate objects** (same subdomain → importing them is fine) |
| **3** | entities **across subdomains** | the domain service is **given values**, never the foreign objects ← *your case* |

### Case 3 — pass values, not foreign entities (Option 1)

The **application service** may touch many subdomains; it **loads** each aggregate, **extracts** what's needed, and passes **primitives/VOs** — never the foreign entity:

```python
# lending/application — MAY touch many subdomains
member = self._members.get(member_id)         # membership repo
active = self._loans.count_active(member.id)   # lending repo
self._borrowing.check_can_borrow(              # → lending domain service gets VALUES
    member_active=member.is_active, active_loan_count=active)
```
```python
# lending/domain/borrowing_service.py — sees only bool + int → imports NO other subdomain
def check_can_borrow(self, *, member_active: bool, active_loan_count: int) -> None: ...
```

### If it needs a *lot* of cross-subdomain data → a small DTO/VO
Passing ten primitives gets ugly. Define a small **value object / read-model DTO** the service *owns* (in its subdomain or `shared/`), and have the application service **map the foreign entity → that DTO** (a mini anti-corruption translation):

```python
# lending/domain — a VALUE the lending service understands (not membership's Member)
@dataclass(frozen=True)
class BorrowerSnapshot:
    is_active: bool
    tier: MemberTier            # lending/shared-owned enum, not membership.Member

# application service maps membership's Member -> lending's BorrowerSnapshot
snap = BorrowerSnapshot(is_active=member.is_active, tier=map_tier(member.tier))
self._borrowing.check_can_borrow(snap, active)
```
The domain service depends on **its own DTO**, never on `membership.Member`.

### Gather vs decide
| Job | Who |
|---|---|
| Load entities from **multiple subdomains**; extract values / map to a DTO | **application service** (may touch many subdomains) |
| **Decide** the rule over those values | **domain service** (pure, given values/DTO, single-subdomain) |

> **In one line:** a domain service never receives a foreign entity — when a rule needs cross-subdomain data, the **application service loads the foreign aggregates and hands the service plain *values* (or maps them into a small DTO/VO the service owns)**. Gather in the application layer, decide in the domain layer; the service sees `bool`/`int`/its-own-DTO, never `membership.Member` or `catalog.BookCopy`.

---

## 9.3.3 Ways one subdomain connects to another — monolith vs microservices

There are **two kinds of "connect":** a *passive reference* (domain level) and *active communication* (application level / events). Each in-process way in a **modular monolith** has a network counterpart in **microservices** — which is what makes a clean monolith a lift-out.

- **Passive reference (domain level):** A holds B's **ID** (`member_id`), no object link. Same in *both* worlds — how the domain "knows about" B without depending on it.
- **Active communication (application level / events):** A actually invokes or reacts to B. This is what differs by transport.

### Modular monolith (in-process)
| Way | How | Style |
|---|---|---|
| Reference by ID | A stores B's id; looks it up when needed | passive |
| Call B's **application service** | A's app layer calls B's use-case API | sync, direct |
| Call B's **repository interface** | A's app layer loads B's aggregate via B's port | sync, direct |
| **Port / gateway (ACL)** | A defines an interface in *its* language; an adapter calls B | sync, decoupled |
| **In-process domain events** | A publishes; B subscribes & reacts (in-memory bus) | **async, decoupled** |
| Shared kernel | A & B share a tiny common model (IDs, base types) | shared code |

### Microservices (across the network)
| Way | How | Style |
|---|---|---|
| Reference by ID | store B's id; call/cache B's data | passive |
| **REST / gRPC / GraphQL** | A calls B's API | sync request/response |
| **Message broker (events)** | Kafka / RabbitMQ / SNS-SQS — publish/subscribe | **async, decoupled** |
| Message queue (commands) | point-to-point command to B | async |
| API Gateway / BFF | fronts & composes services | sync, edge |
| Data replication / CDC | B's data streamed to A's read store | async, read-optimized |
| Saga | coordinate a transaction spanning services | async, multi-step |
| Service mesh | (plumbing) mTLS, retries, discovery | infra |

### The mapping — monolith → microservice
| Modular monolith | → Microservices |
|---|---|
| Reference by ID | Reference by ID (remote lookup / cache) |
| Direct call to B's app service | **REST / gRPC** call to B's service |
| B's repository interface | B's **service API** (no shared DB) |
| Port / gateway (ACL) | same ACL — adapter calls **over the network** |
| **In-process domain event** | **broker event** (Kafka/RabbitMQ) — pub/sub unchanged |
| Synchronous composition | **API composition** or a **saga** |
| Shared kernel | published **shared library** (or duplicate) |

### Sync vs async (the choice underneath)
| | Synchronous (call & wait) | Asynchronous (events) |
|---|---|---|
| Coupling | tighter (B down ⇒ A blocked) | looser (A doesn't know B) |
| Consistency | immediate-ish | eventual |
| Use when | A needs an **immediate answer** | reactions/notifications, no immediate answer |
| Example | "is this copy available?" | "LoanReturnedLate → assess fine, notify" |

### Rules that hold in both worlds
- The **domain layer never calls another subdomain** — only **by-ID** references. Active connection is **application-layer** (sync) or **events** (async).
- Talk through **public contracts** (app-service API, repo interface, event schema, ACL port) — never another subdomain's **internals**.
- Keep the graph **acyclic**; break cycles with **events**. **Prefer async/events** for the loosest coupling and cleanest split.

> **In one line:** connection = **passive by-ID (domain, same in both)** + **active comms (application/events)**. In a monolith that's an in-process **direct call** (to B's app service / repo interface / an ACL port) or an **in-process event**; in microservices the same becomes **REST/gRPC** (sync) or a **broker event / saga** (async) — a 1:1 mapping. Always via **public contracts**, never internals; prefer **events** for decoupling.

---

## 9.4 Two supporting ports: `Clock` and `Notifier`

Notice `self._clock.today()` instead of `date.today()`. Calling the real clock directly inside logic makes it **untestable** (you can't test "what happens 6 days later"). So time becomes an injected **port** — a tiny abstraction (DIP again):

```python
# application/ports.py   (app-level port, shared across subdomains)
from datetime import date
class Clock:                                   # interface (port)
    def today(self) -> date: ...

class SystemClock(Clock):                       # real implementation
    def today(self) -> date:
        from datetime import date as _d
        return _d.today()

class FixedClock(Clock):                        # test implementation
    def __init__(self, d: date): self._d = d
    def today(self) -> date: return self._d
```

The notification requirement (UC-11) works the same way — a `Notifier` port the application service calls after assessing a fine or finding overdue loans. The domain stays oblivious to *how* notification happens (email? SMS?).

> **Aside — Domain Events / Observer (optional next-level decoupling).** Instead of the application service calling the `Notifier` directly, the domain could raise a `LoanReturnedLate` *event* that a notification handler *observes*. That's the **Observer pattern**, and it decouples "what happened" from "who reacts." It's the right move once reactions multiply (notify + log + update stats). At our scale, a direct `Notifier` call is simpler (KISS) — but knowing where Events would slot in is the point.

---

## 9.5 The transaction boundary (and an honest caveat)

The application service is also the **transaction boundary** (the "Unit of Work"): everything in one method call commits together or not at all. If `loans.save(loan)` fails, the `copy.issue()` must roll back too.

But notice `borrow_book` modifies **two** aggregates (`BookCopy` *and* `Loan`) in one transaction. Step 5's rule was *"one transaction = one aggregate."* So are we cheating?

**Honestly, slightly — and on purpose.** The strict rule exists to avoid distributed-transaction pain at large scale. At our scale (one database, 100 members), wrapping both saves in a single local DB transaction is simple, correct, and fine. The rule's *spirit* — "don't span aggregates across a network/service boundary" — we fully respect (everything's one local context).

> **The transferable lesson:** know the rule *and* its reason, so you can tell when bending it is safe. "One aggregate per transaction" is about avoiding distributed coordination; with a single local database it's a guideline, not a law. At a scale that needed independent services, we'd switch to **domain events + eventual consistency** — and that decision would be driven by scale, not dogma.

---

## 9.5.1 Concurrency: who actually prevents a race?

The transaction boundary above raises a question that trips up almost everyone: when two requests hit the same data at once, *which layer* stops them from corrupting it? The answer reshuffles a lot of intuitions, so we'll build it carefully.

### The entity declares the invariant — it does **not** enforce concurrency

`BookCopy.issue()` guards "a copy is issued only if `AVAILABLE`." That's the invariant — *what* consistent means. But the entity is **pure**: no locks, no transactions, no threads (those would drag infrastructure into the domain, §9.2.1). So the entity says *what* must hold; it cannot, by itself, make it hold when two callers race.

### The race — and why the service-side check does **0%** to stop it

Take the invariant *"one copy → at most one member."* Two members request the same copy simultaneously:

```
Worker 1                              Worker 2
────────────────────────────────────────────────────────────
get copy → AVAILABLE
check: available? ✅ PASS             get copy → AVAILABLE
                                      check: available? ✅ PASS   ← also passes!
copy.issue()                          copy.issue()
save                                  save
────────────────────────────────────────────────────────────
One copy, issued to TWO members. 💥
```

The crucial, counter-intuitive point: **the `if copy.is_available` check provides zero race protection.** Each worker runs it in its own memory, on a value read *before* either wrote — so both pass. The check is **business logic** (reject an already-loaned copy in the normal case; return a clean `CopyNotAvailableError`), **not** concurrency control. It is *not* "step one" of a two-step defense — it contributes nothing to the race.

> **The misconception to kill:** "check at the service, then lock at the DB as a double guarantee." Wrong framing. The service check does **0%** of race prevention; the shared-layer mechanism does **100%**. They're different jobs — the check decides *whether allowed*, the lock makes that decision *hold under concurrency*. You need both, but only one prevents the race.

### Where the race actually lives: the shared resource

"Separate processes don't share memory, so how is a race even possible?" — the right instinct (a race needs a shared resource), pointed at the wrong place. Two workers share **no memory** but they share the **database row**. *That row* is the contended resource; the race lives in the read→write gap against it:

```
t1  W1: SELECT copy → AVAILABLE
t2  W2: SELECT copy → AVAILABLE      ← stale: W1 hasn't written yet
t5  W1: UPDATE → LOANED
t6  W2: UPDATE → LOANED              ← clobbers W1
```

The invariant is a statement about the **persisted** state, not about either process's memory — so process isolation does nothing. This is also why an in-process `threading.Lock` is useless across workers: it lives in the *unshared* layer (one process's memory). **The guard must live where the sharing happens.**

### The general principle (not just databases)

A race needs a **shared resource** + an **overlapping read-modify-write window**. So:

> **Enforce concurrency at the shared resource itself, using whatever atomic mechanism that resource provides.** Whoever owns the contended thing is the only one who can serialize access to it — and the guard must be visible to *everyone* who can touch it.

| Shared resource | Its native atomic mechanism |
|---|---|
| **Database row** | optimistic `version` / `SELECT … FOR UPDATE` |
| **File** | OS file locks (`flock`/`fcntl`); atomic `rename()` |
| **Cache (Redis)** | `SETNX`, `INCR`, Lua scripts, `WATCH`/`MULTI`, Redlock |
| **In-process memory** (single process only) | `threading.Lock` / `RLock` |
| **Filesystem dir as mutex** | atomic `mkdir` / `O_CREAT|O_EXCL` lock-file |
| **Listening socket across workers** | kernel (`SO_REUSEPORT`); otherwise one owner + a queue |

### Don't reflexively reach for a lock — the real goal is *atomicity*

A lock is one way to get atomicity, rarely the best:

1. **Don't share at all** (best). Give each worker its own resource / partition. No sharing → no race → no lock. This is the small-aggregate lesson (§5.2): borrowing copy #1 and copy #3 touch different rows and never collide.
2. **Use an atomic operation** (next best). `UPDATE … WHERE version=?`, Redis `INCR`, atomic `rename()` — the resource guarantees the read-modify-write is indivisible; no explicit lock.
3. **Lock** (last resort). Only for a multi-step critical section no single atomic op covers — and then key the lock per-aggregate (per `copy_id`), never one global lock that serializes the whole library.

### The division of labor (the model to keep)

> - **Entity** (`BookCopy`) — defines *what* consistent means (the invariant). Pure.
> - **Aggregate boundary** — defines *what unit* to guard (one `BookCopy` = one lockable unit). Small boundaries → independent locks → low contention.
> - **Application service** — *coordinates*: opens the transaction / acquires the guard around the whole check→mutate→save critical section, and *reacts* to conflicts (catch `ConcurrencyError`, retry or fail the use case).
> - **Infrastructure, behind a port** — supplies the *atomic mechanism* the shared resource offers (DB version check in the repository; a `LockManager` adapter for Redis/threading). The domain never knows whether the shared thing is a row, a file, or a Redis key.

### Concretely, for *this* system (multiple workers, one shared DB)

`threading.Lock` is out — separate processes don't share it. The clean default is **DB-level optimistic locking**: a `version` column the repository checks on save (`UPDATE … WHERE id=? AND version=?`); the loser gets 0 rows → `ConcurrencyError` → the application service retries or fails. The entity may *hold* a `version` field but does nothing with it; the repository does the compare-and-set; the service reacts. Reach for a distributed lock (Redis behind a `LockManager` port) only to guard something the DB can't see. Same layering as always — **domain pure, mechanism in infrastructure, coordination in the service.**

```python
# application service — coordinates; the DB enforces
def borrow_book(self, member_id, copy_id):
    copy = self._copies.get(CopyId(copy_id))      # load (carries version)
    self._borrowing.check_can_borrow(...)          # business check (NOT race protection)
    copy.issue()                                   # entity invariant
    loan = Loan.create(member_id, copy.id, self._clock.today())
    try:
        self._copies.save(copy)                    # repo: UPDATE ... WHERE version=? (the real guard)
        self._loans.save(loan)
    except ConcurrencyError:
        ... # retry, or surface "please try again"
```

> **The one-liner:** the invariant check tells you *whether* an operation is allowed; the shared-resource mechanism (DB version/lock, file lock, atomic cache op) makes that check *hold under concurrency*. The service decides and coordinates; the shared layer enforces.

---

## 9.5.2 Which layer handles concurrency? (quick reference)

A common question after §9.5.1: *is concurrency handled in the application layer, not the domain service?* Yes to "not the domain service" — but it's split across **two** outer layers. Neither the entity **nor** the domain service ever touches concurrency (they stay pure); it's **coordinated** by the application service and **enforced** by infrastructure.

| Layer | Role in concurrency |
|---|---|
| **Entity** | declares the **invariant** (`copy.issue()` guards availability). **No** concurrency. |
| **Domain service** | the **business rule** over values (`check_can_borrow`). **No** concurrency. |
| **Application service** | **coordinates** — opens the transaction / unit of work, and **reacts** to conflicts (catch `ConcurrencyError`, retry or fail). |
| **Infrastructure (DB / repo)** | **enforces** — the actual atomic guarantee: optimistic `version` check or pessimistic lock. |

**Why never in the domain service:** it's stateless, pure, and *given values* — no repo, no DB, no transaction. A lock there would break its purity **and** be useless, since the race lives at the **shared resource** (the DB row), not in a pure function (recall §9.5.1: the check does 0%, the DB does 100%).

> **In one line:** concurrency is **never in the domain** (entity or domain service — both stay pure); it is **coordinated by the application service** (transaction boundary + retry-on-conflict) and **enforced by infrastructure** (DB version/lock). "At the application layer" is right for *coordination*; the *actual guarantee* is in infrastructure.

---

## 9.5.3 Exception handling: raise low, handle high — and exception *translation*

Two different actions get confused: **raising** (throw — "a rule was violated") vs **handling** (catch + decide what to do). The default flow:

> **Raise low, handle high.** The **domain raises**; the application service and controller **propagate** (no catch); the **edge** (controller handler / `main.py`) **handles** — maps to HTTP / prints. The domain never catches its own errors.

### Inner layers may catch — but only to *act*, then re-raise/convert (never swallow)

| Layer | Catch? | For what |
|---|---|---|
| **Domain** | almost never | it *raises*; prefer a `Result`/`Optional` return over exception-based control flow |
| **Application** | yes, when it can *act* | retry, transaction rollback, saga/compensation, degrade a non-critical step — then **re-raise/convert** |
| **Infrastructure** | yes, to *translate* | raw infra error → domain error, then raise |
| **Edge** | yes, to *respond* | map to HTTP / print — the final catch |

### Exception translation (infrastructure → domain) — the key one

A **repository implementation** catches a raw infra exception and converts it into a **domain error**, so inner/edge code deals in meaningful terms, not leaky DB errors (this keeps Repository ≠ DAO):

```python
# infrastructure — translate at the boundary
def save(self, member: Member) -> None:
    try:
        self._session.add(_to_record(member)); self._session.commit()
    except IntegrityError:
        raise DuplicateEmailError(member.email.value)   # infra error → DOMAIN error, then raise
```
Now the edge's one `DomainError` handler maps `DuplicateEmailError` to a `409` — it never sees a SQL `IntegrityError`.

### Application-layer catches that are legitimate

**Retry** a transient failure, re-raise on give-up:
```python
for attempt in range(3):
    try:
        copy = self._copies.get(cid); copy.issue(); self._copies.save(copy); break
    except ConcurrencyError:
        if attempt == 2: raise            # acted (retried); still surface the failure
```

**Graceful degradation** of a *non-critical* dependency (don't fail the core use case):
```python
self._loans.save(loan)                    # core succeeded
try:
    self._notifier.send(...)              # optional side effect
except NotificationError:
    log.warning("notify failed")          # log + continue — the borrow still succeeds
```
(Legitimate because notification isn't essential to "borrow"; a *core* failure would still propagate.)

### The anti-pattern
```python
try: do_something()
except SomeError: pass          # ❌ swallow — hides the failure (worst of all)
```
Catch-and-swallow or blanket log-and-continue masks real bugs. Catch **only where you can act**, and then **re-raise or convert**.

> **In one line:** **raise low, handle high** — the domain raises, inner layers propagate, the edge catches to respond. Inner layers catch **only to act**: the **application service** for retry / rollback / compensation / degrading non-critical steps, and **infrastructure** to *translate* raw infra errors into domain errors (e.g. `IntegrityError → DuplicateEmailError`) — always **re-raising or converting**, never swallowing.

---

## 9.6 The layered picture so far

```
┌──────────────────────────────────────────────────────────┐
│ application/   LibraryService (use cases), ports (Clock…)  │  orchestration, transactions
│   depends ↓ on interfaces only                              │
├──────────────────────────────────────────────────────────┤
│ domain/        entities · value objects · BorrowingService │  PURE business logic,
│                · FineCalculationStrategy · repo INTERFACES  │  zero framework imports
└──────────────────────────────────────────────────────────┘
        ▲ implemented by
┌──────────────────────────────────────────────────────────┐
│ infrastructure/  repository implementations (Step 10–11)   │  adapters
└──────────────────────────────────────────────────────────┘

Dependencies point INWARD: application → domain ; infrastructure → domain.
The domain depends on NOTHING.
```

This is the **Dependency Inversion Principle** at the architecture scale: high-level policy (domain) defines interfaces; low-level details (infrastructure) implement them. We'll make those repository interfaces concrete in Step 10.

---

## Principles in play

| Principle | How this step applied it |
|---|---|
| **SRP / separation of concerns** | Domain service = *decide*; application service = *orchestrate*. Neither does the other's job. |
| **DIP** (SOLID) | Application service depends on injected repository **interfaces**, the domain service, a `Clock` and `Notifier` port — never concretes. |
| **Rich domain, thin application** | Business rules live in domain (services + entities); the use-case layer holds zero rules. |
| **Testability** | Pure domain service tests with plain objects; `FixedClock` makes time-dependent logic deterministic. |
| **KISS / YAGNI** | Direct `Notifier` call over a full domain-event bus at this scale — with a clear note on when Events earn their place. |
| **Open/Closed** | The fine **Strategy** is injected, so changing fine policy never touches the use case. |

## Key takeaways (the transferable lessons)

1. **Domain service vs. application service is the distinction to internalize.** Domain service answers a *business question* (and lives in the pure domain); application service *orchestrates a use case* (load → decide → mutate → save) and holds **no** business rules.
2. **Domain services are given their data, not handed a repository.** That keeps them pure and unit-testable; the application service does the fetching.
3. **Use a domain service only for logic that spans aggregates.** Single-aggregate logic stays a method on the aggregate (Information Expert).
4. **Inject your ports** — repositories, clock, notifier. Dependencies point inward; the domain depends on nothing.
5. **Know rules *and their reasons*.** "One aggregate per transaction" guards against distributed coordination; with one local DB, bending it is safe — and scale, not dogma, decides when to switch to events.

---

*Next — Step 10: Repositories. We formally define the repository interfaces the application service has been leaning on (one per aggregate root), write simple in-memory implementations to run everything end-to-end, and see the Repository pattern + Dependency Inversion click into place.*
