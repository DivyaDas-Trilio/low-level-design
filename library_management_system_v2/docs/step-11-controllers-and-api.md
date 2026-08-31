# Step 11 — Controllers / API

*Series: Designing a Library Management System with DDD · Chapter 11 of 12*

---

The domain is built, the use cases orchestrate, the repositories persist. The last layer is the **front door**: an HTTP API that turns web requests into application-service calls and turns the results (and errors) back into HTTP responses. The single most important property of this layer:

> **The API layer is a *thin adapter*. It translates between HTTP and the application service — and does nothing else.** No business rules, no orchestration. If you see an `if` about borrowing limits in a controller, it's in the wrong place.

In hexagonal-architecture terms this is a **driving adapter** (it drives the application from outside), and like the repository it sits at the *edge* — the domain neither knows nor cares that HTTP exists.

```
src/
├── shared/                          ids · exceptions · Repository base
├── catalog/ · lending/ · fines/ · membership/     each: domain/ application/ infrastructure/ api/
│       └── <subdomain>/api/     ← THIS STEP (per subdomain)
│           ├── dtos.py                 request/response models (Pydantic)
│           └── <x>_controller.py       the subdomain's router
├── api/                         ← app-level API glue (cross-cutting)
│   ├── errors.py                    DomainError → HTTP (maps errors from every subdomain)
│   └── dependencies.py              DI wiring (FastAPI Depends → composition root)
├── composition.py               the composition root (build_library_service)
└── main.py                      FastAPI app: include routers + install error handlers
```
*(Vertical slice: each subdomain owns its **DTOs + controller** in its own `api/`; the **error handler, DI provider, and app assembly** are cross-cutting → a small top-level `api/` + `main.py`.)*

---

## 11.1 DTOs — and why the API must NOT expose domain objects

A **DTO** (Data Transfer Object) is a flat, serializable shape for crossing a boundary. The API defines its own DTOs (Pydantic models) for requests and responses — and deliberately **never** returns a domain entity directly.

```python
# lending/api/dtos.py   (each subdomain has its own; BookResponse lives in catalog/api/dtos.py)
from datetime import date
from pydantic import BaseModel

class BorrowRequest(BaseModel):
    member_id: str
    copy_id: str

class LoanResponse(BaseModel):
    loan_id: str
    member_id: str
    copy_id: str
    due_date: date
    status: str

class ReturnResponse(BaseModel):
    loan_id: str
    days_overdue: int
    fine_amount: str | None      # e.g. "₹10.00", or null if returned on time

class BookResponse(BaseModel):
    book_id: str
    title: str
    author: str
    isbn: str
    available_copies: int
```

**Why not just return the `Loan` entity?** Four reasons, and they're the same reasons every layer in this series has its own types:

1. **Decoupling the contract from the model.** Your HTTP API is a *public contract*. If clients serialize a `Loan` directly, then renaming a private field or refactoring the entity **breaks every client**. A DTO lets the domain evolve freely behind a stable contract.
2. **Security / leakage.** Domain objects carry internals you don't want on the wire (private `_state` objects, the whole `DateRange`, methods). A DTO exposes *only* what the client should see.
3. **Shape mismatch.** Clients want `available_copies: 3` (a computed number); the domain has five separate `BookCopy` aggregates. The DTO is where that translation happens.
4. **No behavior on the wire.** Entities have methods and invariants; JSON can't carry those. Forcing entities through serialization produces anemic, broken half-objects.

> **The rule:** *map at the boundary.* Domain entities live in the domain; DTOs live at the edges; you translate between them in the controller (or a small mapper). Entities never cross outward.

---

## 11.2 Mapping domain errors to HTTP status codes

Remember the `DomainError` hierarchy from 8a? Here's the payoff. One exception handler maps the *whole* hierarchy to HTTP, with specific overrides — and it embodies the **Open/Closed Principle**: a brand-new domain error automatically gets a sensible response without touching the handler.

```python
# api/errors.py   (app-level — maps errors from every subdomain)
from fastapi import Request
from fastapi.responses import JSONResponse
from shared.exceptions import DomainError, EntityNotFoundError
from catalog.domain.exceptions import CopyNotAvailableError, IllegalStatusTransitionError
from lending.domain.exceptions import BorrowingLimitExceededError
from fines.domain.exceptions import FineAlreadySettledError

# specific overrides; anything else falls through to 400
_STATUS = {
    EntityNotFoundError:          404,   # not found
    CopyNotAvailableError:        409,   # conflict — copy already loaned
    BorrowingLimitExceededError:  409,   # conflict — at the 2-book limit
    FineAlreadySettledError:      409,
    IllegalStatusTransitionError: 409,
}

def install_error_handlers(app):
    @app.exception_handler(DomainError)
    async def handle_domain_error(request: Request, exc: DomainError):
        status = next((code for typ, code in _STATUS.items() if isinstance(exc, typ)), 400)
        return JSONResponse(
            status_code=status,
            content={"error": type(exc).__name__, "detail": str(exc)},
        )
```

The controller below has **zero try/except** — it just calls the service and lets domain errors bubble to this one handler. A new rule like `MemberBlockedError` needs *no handler change* (it defaults to 400); to give it 403, you add **one line** to `_STATUS`. That's OCP at the error boundary, exactly as promised in 8a.

---

## 11.3 Dependency wiring

FastAPI's `Depends` is how the composition root (Step 10) reaches the controllers. For our in-memory store we want a single shared instance:

```python
# api/dependencies.py   (app-level)
from functools import lru_cache
from composition import build_library_service              # Step 10's composition root
from lending.application.library_service import LibraryService

@lru_cache                                            # one shared instance (in-memory store)
def get_service() -> LibraryService:
    return build_library_service()
```

> With a **real database** (next section), you'd instead build a fresh service *per request* with a request-scoped DB session, so each request is its own Unit of Work / transaction. The controllers don't change — only this provider does.

---

## 11.4 The controllers — thin by construction

```python
# lending/api/loan_controller.py
from fastapi import APIRouter, Depends
from lending.api.dtos import BorrowRequest, LoanResponse, ReturnResponse
from api.dependencies import get_service
from lending.application.library_service import LibraryService

router = APIRouter(prefix="/loans", tags=["lending"])

@router.post("/borrow", response_model=LoanResponse, status_code=201)
def borrow(req: BorrowRequest, svc: LibraryService = Depends(get_service)):
    view = svc.borrow_book(req.member_id, req.copy_id)        # → application DTO (LoanView)
    return LoanResponse(**view.__dict__)                       # map app DTO → API DTO

@router.post("/{loan_id}/return", response_model=ReturnResponse)
def return_book(loan_id: str, svc: LibraryService = Depends(get_service)):
    view = svc.return_book(loan_id)
    return ReturnResponse(
        loan_id=view.loan_id,
        days_overdue=view.days_overdue,
        fine_amount=view.fine_amount,
    )
```

That's the entire controller: parse the request DTO → call one service method → map the result to a response DTO. **No business logic.** If a borrow is illegal, the domain raises, the handler from §11.2 catches it, and the client gets a clean `409`. (This implies the Step 9 service now returns small **application DTOs** — `LoanView`, `ReturnView` — rather than bare strings; that application-layer mapping keeps domain entities from leaking even one layer out.)

---

## 11.5 Rule #6, finally — visibility as a *query/role* concern

Back in Step 4 we set rule #6 aside, insisting that *"lost/damaged copies are hidden from members but visible to librarians"* is **not** a domain invariant — it's a **read/authorization concern**. Here is where it correctly lives: in the API layer, driven by the caller's **role**.

```python
# catalog/api/book_controller.py
@router.get("/books/{book_id}/copies", response_model=list[CopyResponse])
def list_copies(book_id: str, role: str = "member",       # role comes from auth in real code
                svc: LibraryService = Depends(get_service)):
    copies = svc.list_copies(book_id)
    if role == "member":
        copies = [c for c in copies if c.is_visible_to_member]   # rule #6 — query filter
    # librarian/admin see everything, including LOST/DAMAGED
    return [CopyResponse.from_view(c) for c in copies]
```

This is the clean resolution of a decision we made seven steps ago: the *domain* enforces "a damaged copy can't be issued" (invariant I-2/I-7, inside `BookCopy`); the *API* enforces "members don't even see it" (a presentation filter). **Two different concerns, two different layers — never mixed.** That separation is why the rule was deliberately *not* baked into the entity.

> The three **actors** from Step 1 (Member / Librarian / Admin) finally become **roles** here, deciding which endpoints and which data each caller may access. Real authentication (tokens, login) is a generic subdomain we'd plug in — intentionally out of scope for the core modeling exercise.

---

## 11.6 Assembling the app — and where the real database drops in

```python
# main.py   (top-level app assembly)
from fastapi import FastAPI
from api.errors import install_error_handlers
from lending.api import loan_controller
from catalog.api import book_controller
from membership.api import member_controller

app = FastAPI(title="Library Management System", version="2.0.0")
install_error_handlers(app)
app.include_router(loan_controller.router)
app.include_router(book_controller.router)
app.include_router(member_controller.router)
```

**Swapping the in-memory store for Postgres** touches only the *outermost* layer — proof that Steps 1–10 are storage-agnostic:

```python
# lending/infrastructure/sql_loan_repository.py  (NEW — implements the SAME interface)
class SqlLoanRepository(LoanRepository):
    def __init__(self, session): self._session = session
    def get(self, id): ...                # SQLAlchemy query → reconstruct Loan aggregate
    def save(self, loan): ...             # persist aggregate
    def count_active_for_member(self, member_id): ...   # SQL COUNT
    def find_overdue(self, as_of): ...    # SQL WHERE due_date < :as_of

# change ONLY the composition root:
def build_library_service(session):
    return LibraryService(
        SqlMemberRepository(session), SqlBookCopyRepository(session),
        SqlLoanRepository(session), SqlFineRepository(session),
        BorrowingService(), StandardFineStrategy(), SystemClock(),
    )
```

`domain/` and `application/` don't move a line. The `LoanRepository` *interface* is unchanged; only a new *adapter* appears, and the composition root picks it. Each request gets its own `session` → a per-request transaction (the Unit of Work the in-memory store couldn't provide). **That** is the entire reason we built persistence behind an interface.

---

## 11.7 The api layer as the HLD ↔ LLD seam (+ production concerns)

Everything above (DTOs, controllers, DI, error-mapping) is the *minimum*. A real production api layer carries much more — and noticing *what kind* of concern each is clarifies the whole architecture:

> **The api/edge is the seam where HLD meets LLD.** It's where architectural + cross-cutting concerns become concrete code (or point at the platform), while the **inner layers stay pure** — which is *why* these concerns concentrate at the edge.

### The production api-layer checklist, by category

**1. HLD decisions → implemented *at the edge* (middleware/dependencies):**
auth (authn + authz), rate limiting, API **versioning**, observability (metrics/tracing), health/readiness probes.

**2. HLD/infra → handled *outside* the app (not in this layer at all):**
TLS/HTTPS, the **API gateway**, load balancing, **service mesh** (mTLS/retries), WAF. These live in the gateway/proxy/platform (k8s, Istio) — Part II territory.

**3. LLD (code design) → genuinely this layer:**
DTO design, controller structure, the `DomainError`→HTTP mapping, DI wiring, entity↔DTO mappers, pagination *implementation*.

**4. Cross-cutting concerns (orthogonal to both — the "AOP" category):**
logging, **correlation/request IDs**, auth checks, tracing — applied *once* as middleware, cutting across every request.

### Also typically needed (production hardening)
Consistent error envelope (RFC 7807 `problem+json`), **pagination/filtering/sorting** on list endpoints, **idempotency keys** (safe `POST` retries), CORS, security headers, gzip, request size limits/timeouts, per-request DB session (transaction scope), graceful shutdown. FastAPI gives **request/response validation + OpenAPI docs + DI + async** for free; you add the rest.

### Where each lives
| Concern | Home |
|---|---|
| auth, logging, correlation IDs, CORS, rate limit, compression | **middleware / dependencies** (app-wide, once) |
| versioning, pagination, error format, idempotency | **api-layer conventions** (LLD) |
| TLS, gateway, mesh, load balancing | **outside the app** — gateway / platform (HLD/ops) |
| health, metrics, tracing | app-level + platform |

**None of it touches `domain`/`application`/`infrastructure`.** Controllers stay thin — the cross-cutting stuff is middleware, not `if`s in each endpoint.

### The KISS caveat
Don't build all of this upfront. Add per real need, and push what you can to the **gateway/platform** (TLS, rate-limiting, some auth). For this build, *controllers + DTOs + DI + the one error handler* is the right scope — the rest is production hardening layered at the edge later.

> **The insight:** **inner layers = LLD** (business modeling, kept pure); **the edge = where HLD/ops concerns attach** — in code (middleware/DTOs) or by pointing at the platform (gateway/mesh). The api layer is precisely the meeting point of the two, which is why "design the domain first, harden the edge last" works.

---

## Principles in play

| Principle | How this step applied it |
|---|---|
| **Separation of concerns / thin adapter** | Controllers only translate HTTP ↔ service calls; zero business logic at the edge. |
| **OCP** (SOLID) | One `DomainError` handler maps the whole hierarchy; new errors default sensibly, specifics are a one-line add. |
| **DIP** | Controllers depend on the application service via `Depends`; the DB is chosen at the composition root, invisible to inner layers. |
| **Information hiding / security** | DTOs expose only the public contract; domain entities never cross the wire. |
| **Separation of invariant vs. visibility** | Rule #6 resolved as a *role-based query filter* in the API, not a domain rule — the Step 4 decision paying off. |
| **KISS** | Real auth left as a pluggable generic subdomain; we model the core, not the ceremony. |

## Key takeaways (the transferable lessons)

1. **The API is a thin translating adapter.** HTTP in → service call → DTO out. Any business logic here is misplaced.
2. **Never serialize domain entities.** DTOs decouple your public contract from your model, hide internals, and reshape data for clients — map at the boundary.
3. **Map errors once, centrally.** A `DomainError`-to-HTTP handler keyed on the exception hierarchy is OCP in action — new rules need no handler edits.
4. **Authorization/visibility is an edge concern.** Rule #6 lives here as a role filter; the domain only owns the *invariant* (can't issue a damaged copy). Different concerns, different layers.
5. **Swapping the database touches only the composition root.** That the inner layers don't move is the dividend of every interface and inward-pointing dependency we built.

---

*Next — Step 12 (finale): Artifacts. We collect everything into the deliverables your `lld_basics.excalidraw` asks for — the class diagram, ER diagram, a use-case/activity view, and the final directory structure — plus a retrospective tying each design decision back to the principle that drove it.*
