# Step 0 — End-to-End: How a Request Flows Through the Layers

*A primer before the deep dives. This shows a **complete vertical slice** — one use case travelling through all four layers — so the later steps (which build each layer in isolation) have a picture to slot into. Read it once; refer back whenever "which layer does this go in?" comes up.*

The use case: **Register a member.** (`Book`, `Member`, `Fine` and the value objects are built in steps 8a–8b; here we assume them and focus on the *flow*.)

---

## The vertical slice

Every subdomain is a self-contained slice with the same four layers:

```
membership/
├── domain/
│   ├── member.py           # entity + invariants (pure)
│   ├── email.py            # value object
│   └── repository.py       # repository INTERFACE (a port)      ← domain owns this
├── application/
│   └── register_member.py  # the use case (application service)
├── infrastructure/
│   ├── in_memory_member_repository.py   # impl for tests/dev
│   └── sql_member_repository.py         # impl — THE DB LOGIC lives here
└── api/
    └── routes.py           # REST controller (thin)
```

The golden rule that makes it work: **dependencies point inward.** `api → application → domain ← infrastructure`. The domain depends on nothing; infrastructure depends on the domain (it *implements* the domain's interfaces).

---

## 1. `domain/repository.py` — the repository **interface** (no SQL)

The domain declares *what it needs* from persistence, in its own language, returning domain objects.

```python
from abc import ABC, abstractmethod
from shared.ids import MemberId
from membership.domain.member import Member

class MemberRepository(ABC):
    """Port: what the domain NEEDS from persistence. Knows nothing about SQL/rows."""
    @abstractmethod
    def get(self, member_id: MemberId) -> Member | None: ...
    @abstractmethod
    def save(self, member: Member) -> None: ...
    @abstractmethod
    def exists_email(self, email: str) -> bool: ...
```

## 2. `application/register_member.py` — the use case (orchestration, no SQL)

Load/check → decide (domain) → save. Depends on the **interface**, injected.

```python
from membership.domain.member import Member
from membership.domain.email import EmailAddress
from membership.domain.repository import MemberRepository
from membership.domain.exceptions import EmailAlreadyRegisteredError

class RegisterMemberService:
    def __init__(self, members: MemberRepository):     # depends on the INTERFACE (injected)
        self._members = members

    def execute(self, name: str, email: str) -> str:
        email_vo = EmailAddress(email)                       # 1. validate (domain VO)
        if self._members.exists_email(email_vo.value):       # 2. business check (via repo)
            raise EmailAlreadyRegisteredError(email_vo.value)
        member = Member.register(name, email_vo)             # 3. DOMAIN creates it (invariants)
        self._members.save(member)                           # 4. persist (via repo)
        return str(member.id)
```

## 3. `infrastructure/sql_member_repository.py` — the ONLY place DB logic lives

SQL, the connection, and the **row ↔ domain object mapping** (the Data Mapper role).

```python
from membership.domain.repository import MemberRepository
from membership.domain.member import Member
from membership.domain.email import EmailAddress
from membership.domain.enums import MemberStatus
from shared.ids import MemberId

class SqlMemberRepository(MemberRepository):
    def __init__(self, conn):
        self._conn = conn

    def get(self, member_id: MemberId) -> Member | None:
        row = self._conn.execute(
            "SELECT id, name, email, status FROM members WHERE id = ?", (str(member_id),)
        ).fetchone()
        return self._to_domain(row) if row else None

    def save(self, member: Member) -> None:
        self._conn.execute(
            "INSERT INTO members (id, name, email, status) VALUES (?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET name=excluded.name, "
            "email=excluded.email, status=excluded.status",
            (str(member.id), member.name, member.email.value, member._status.value),
        )
        self._conn.commit()

    def exists_email(self, email: str) -> bool:
        return self._conn.execute(
            "SELECT 1 FROM members WHERE email = ?", (email,)
        ).fetchone() is not None

    def _to_domain(self, row) -> Member:                 # reconstitute the aggregate from a row
        m = Member(MemberId(row["id"]), row["name"], EmailAddress(row["email"]))
        if row["status"] == MemberStatus.BLOCKED.value:
            m.block()
        return m
```

## 4. A second impl — `in_memory_member_repository.py` (same interface, no DB)

```python
class InMemoryMemberRepository(MemberRepository):
    def __init__(self):
        self._store: dict[str, Member] = {}
    def get(self, member_id):      return self._store.get(str(member_id))
    def save(self, member):        self._store[str(member.id)] = member
    def exists_email(self, email): return any(m.email.value == email for m in self._store.values())
```

The application service **can't tell which impl it got** — that's the payoff.

## 5. `api/routes.py` — the REST controller (thin)

Parse → call the use case → map result/errors to HTTP. No logic.

```python
@router.post("/members", status_code=201)
def register_member(body: RegisterMemberRequest,
                    service: RegisterMemberService = Depends(get_service)):
    try:
        member_id = service.execute(body.name, body.email)
        return {"id": member_id}
    except DomainError as e:                          # map any domain error → 400
        raise HTTPException(status_code=400, detail=str(e))
```

## 6. Composition root (`main.py`) — where infra plugs into the interface

The **one** place that names the concrete implementation.

```python
conn = sqlite3.connect("library.db")
member_repo = SqlMemberRepository(conn)                  # choose the impl HERE
register_service = RegisterMemberService(member_repo)    # inject
# tests do:  RegisterMemberService(InMemoryMemberRepository())
```

---

## The complete flow (end to end)

```
HTTP POST /members {name, email}
  │
  ▼  api/routes.py            parse request
  ▼  application/RegisterMemberService.execute()
        ├─ EmailAddress(email)          ── domain VO validates format
        ├─ members.exists_email(...)    ── repo INTERFACE → SqlMemberRepository → SELECT   (infra/DB)
        ├─ Member.register(name, email) ── domain creates a valid Member (invariants)
        └─ members.save(member)         ── repo INTERFACE → SqlMemberRepository → INSERT   (infra/DB)
  ▼  api returns 201 {id}
```

## Where everything goes (the reference)

| Concern | Layer |
|---|---|
| SQL / connection / row-mapping | **infrastructure** only (`SqlMemberRepository`) |
| Repository **interface** (port) | **domain** (`repository.py`) |
| Repository **implementation** (adapter) | **infrastructure** |
| Orchestration (load → decide → save) | **application** |
| Business rules / invariants | **domain** (`Member`, `EmailAddress`) |
| HTTP ↔ application translation | **api** |
| Choosing the concrete repo (DI) | **composition root** (`main.py`) |

## Transactions
Here `save()` commits for simplicity. For a multi-step use case (e.g. `borrow` touches `BookCopy` **and** `Loan`), the **application service** owns the transaction boundary — wrap the whole `execute()` in one unit of work so it all commits or rolls back together.

> **The payoff:** swap `SqlMemberRepository` → `InMemoryMemberRepository` (or Postgres → Mongo) and **domain + application don't change a line** — because they depend on the *interface*, and DB logic is quarantined in the infrastructure adapter. That's Dependency Inversion buying you testability and swappability.

---

*Next: the step-by-step build. Steps 1–7 design the model on paper; steps 8a–8b write the domain; step 9 the services; step 10 the repositories (the interfaces above); step 11 the API. This primer is the picture they all slot into.*
