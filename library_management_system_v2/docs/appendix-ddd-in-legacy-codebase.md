# Appendix — Implementing a Feature in a Messy Existing Codebase with DDD

*A practical, learnable playbook for **brownfield DDD**: adding a clean, well-modeled feature to a legacy / anemic / big-ball-of-mud codebase — without rewriting it. This is a distinct skill set (mostly **strategic DDD** applied to legacy) and a staple of senior work.*

---

## The mindset

You will **not** rewrite the legacy system, and you will **not** let its mess leak into your new feature.

> **Carve a clean island for the new feature, and insulate it from the mess with a translation layer.** Model the new feature properly *inside* the island; talk to the legacy world only through an adapter that translates its ugly shapes into your clean ones.

Three strategic-DDD patterns do the work:

| Pattern | Role |
|---|---|
| **Bubble Context** | a small, clean DDD context for the new feature, insulated from legacy |
| **Anti-Corruption Layer (ACL)** | a translation layer so the legacy model can't corrupt your clean model |
| **Strangler Fig** | (optional, later) grow the clean part and gradually replace the old |

---

## The step-by-step method

### Step 1 — Understand the feature and find its bounded context
- What does the feature *do*? What's its language (new terms)?
- Does it **extend an existing concept** or introduce a **new capability**?
- Decide: a **new bounded context** (the bubble) or an extension of an existing one. A feature with its own rules/language → new bubble context.

### Step 2 — Characterize the mess (map what you must touch)
- Which legacy data/classes does the feature *read* or *write*? (tables, god-classes, global state, direct SQL).
- **Don't try to understand all of it** — only the slice your feature touches.
- Note the ugly shapes: anemic dicts, mixed concerns, no invariants, primitive obsession.

### Step 3 — Draw the seam (define the bubble boundary)
- Decide exactly what lives *inside* your clean context vs. what stays legacy.
- Everything the feature *owns* → inside the bubble (new aggregates/VOs).
- Everything it merely *references* → stays in legacy, reached via the ACL, **by ID**.

### Step 4 — Build the clean model inside the bubble (tactical DDD)
- Full tactical DDD *inside the island*: entities, value objects, aggregates, invariants, domain services.
- Define **ports** (interfaces) in your bubble's domain for anything it needs from the legacy world — expressed in *your* language, not legacy's.

### Step 5 — Build the Anti-Corruption Layer (the ACL adapter)
- Implement each port with an adapter that calls the messy legacy code and **translates** its output into your clean model (VOs/DTOs).
- The ACL is the *only* place that knows the legacy shapes. Nothing legacy passes through it un-translated.

### Step 6 — Wire it in
- The feature reads legacy data **through the ACL** (clean objects come back), does its work in the clean model, and writes back **through the ACL** (translating your model → legacy calls).
- Keep the transaction boundary sane; if writes span legacy + bubble, coordinate carefully (or via events).

### Step 7 — Test at the seam
- Unit-test the clean bubble with plain objects (no legacy, no DB) — fast, because the port is an interface.
- **Contract-test the ACL** against the real legacy to prove the translation holds.

### Step 8 — (Optional) Strangle over time
- Once the bubble is trusted, *route more* through it; gradually move legacy responsibilities behind the clean model until the old code is dead and deletable.

---

## Worked example — adding "Reservations" to a messy legacy library app

**The legacy:** a god-class `BookManager` with methods like `get_book_row(id) -> dict`, direct SQL, anemic dicts, member data as `{"id":..., "mail":..., "blocked":0}`, no invariants.

**The feature:** *a member can reserve a title that's fully loaned out, and is notified when a copy frees up.* Real rules → this earns a clean **Reservations bubble context**.

### 1–3. Seam
- **Inside the bubble (owned):** `Reservation` (aggregate), `ReservationStatus` (VO/enum), `ReservationQueue` logic.
- **Referenced, stays legacy (by ID):** the book and the member — reached via the ACL.

### 4. Clean model + a port (in *your* language)
```python
# reservations/domain/ports.py  — the bubble OWNS this interface, in ITS language
class CatalogGateway(Protocol):
    def is_fully_loaned(self, book_id: BookId) -> bool: ...
    def title_of(self, book_id: BookId) -> str: ...

class MembershipGateway(Protocol):
    def is_active_member(self, member_id: MemberId) -> bool: ...

# reservations/domain/reservation.py — full tactical DDD, no legacy in sight
class Reservation:
    def __init__(self, id, member_id, book_id, status=ReservationStatus.WAITING): ...
    def fulfill(self) -> None: ...     # guarded transitions (invariants)
    def cancel(self) -> None: ...
```

### 5. The ACL adapter (the *only* place that touches the mess)
```python
# reservations/infrastructure/legacy_acl.py
class LegacyCatalogAdapter(CatalogGateway):        # implements the bubble's port
    def __init__(self, book_manager):              # the legacy god-class
        self._legacy = book_manager

    def is_fully_loaned(self, book_id):
        row = self._legacy.get_book_row(str(book_id))   # ugly legacy dict
        # TRANSLATE legacy shape -> clean answer; the mess stops HERE
        return row["available_copies"] == 0

    def title_of(self, book_id):
        return self._legacy.get_book_row(str(book_id))["ttl"]   # legacy typo'd key, hidden here
```

### 6. Wire it — the feature never sees a legacy dict
```python
# reservations/application/reserve_book.py
class ReserveBookService:
    def __init__(self, reservations, catalog: CatalogGateway, members: MembershipGateway):
        self._reservations, self._catalog, self._members = reservations, catalog, members

    def execute(self, member_id, book_id):
        if not self._members.is_active_member(member_id):   # via ACL — clean bool
            raise MemberNotActiveError(...)
        if not self._catalog.is_fully_loaned(book_id):       # via ACL — clean bool
            raise CopiesAvailableError("borrow directly instead")
        res = Reservation(ReservationId.new(), member_id, book_id)   # clean domain
        self._reservations.save(res)
        return res.id
```

The `Reservation` aggregate and `ReserveBookService` are **pure, clean DDD** — they have *no idea* the catalog is a god-class returning typo'd dicts. That knowledge is quarantined in `LegacyCatalogAdapter`. The mess cannot corrupt the new model.

---

## The full brownfield DDD techniques catalog

The playbook above uses the core combo (**ACL + Bubble Context + Strangler Fig**), but there's a wider toolkit. It comes from two families: **context-mapping patterns** (strategic DDD — *how your clean model relates to the legacy*) and **legacy-evolution tactics** (Fowler & Michael Feathers — *how you change/replace the legacy*). Grouped by purpose:

### Insulate — protect new clean work from the mess
| Technique | What it is | When |
|---|---|---|
| **Anti-Corruption Layer (ACL)** | translation layer; legacy shapes → your clean model & back | you must talk to legacy but refuse to let it leak in (default defensive move) |
| **Bubble Context** | a small clean DDD context for the new feature, behind an ACL | building a new capability in a messy neighborhood |
| **Separate Ways** | decide **not** to integrate; duplicate the little you need | integration cost > value; the link isn't worth the coupling |

### Integrate — define how contexts relate (context-map relationships)
| Technique | What it is | When |
|---|---|---|
| **Conformist** | adopt the legacy model **as-is**, no translation | zero power to change it *and* an ACL isn't worth it (pragmatic surrender) |
| **Customer/Supplier** | downstream gets a negotiated say in upstream's changes | you depend on another team who will accommodate you |
| **Open Host Service (OHS)** | expose a clean, stable **public API** in front of the legacy | many consumers need the legacy → give them one clean door |
| **Published Language** | a well-defined shared **schema** for integration (often with OHS) | formalizing the contract others integrate against |
| **Shared Kernel** | a small shared model two contexts co-own | two contexts genuinely need shared concepts (use sparingly — it couples) |
| **Partnership** | two contexts/teams succeed-or-fail together, coordinate tightly | deeply interdependent features |

### Replace / migrate — evolve the legacy *out*
| Technique | What it is | When |
|---|---|---|
| **Strangler Fig** | grow the new system around the old, route more to it over time, until the old is dead & deletable | replacing a legacy system incrementally, safely |
| **Branch by Abstraction** | introduce an abstraction over the thing to replace; swap implementations behind it while both run | replacing a component in-place, no long-lived branch |

### Make it safe to change — Feathers' legacy techniques
| Technique | What it is | When |
|---|---|---|
| **Characterization tests** | tests capturing the legacy's *current* behavior (even if "wrong") as a safety net | before changing any untested legacy code |
| **Seams** | points where you can insert new behavior/tests without editing the mess in place | to get legacy under test / inject your ACL |

### Recover structure — distill the model out of the mud
| Technique | What it is |
|---|---|
| **Extract Bounded Context / Extract Module** | pull a cohesive chunk out into its own clean boundary |
| **Refactoring toward deeper insight** | improve the model incrementally as understanding grows (DDD is iterative) |

### How to choose
```
Can I change the legacy?
├─ No, and can't even wrap it well → Conformist (adopt as-is) or Separate Ways (duplicate)
├─ No, but I can wrap it          → Anti-Corruption Layer + Bubble Context
└─ Yes, over time                 → Strangler Fig / Branch by Abstraction
                                     (first: Characterization tests + Seams to make it safe)

Exposing the legacy to many consumers? → Open Host Service + Published Language
```
The spectrum runs **cooperative** (Partnership, Shared Kernel) → **defensive** (ACL, Bubble) → **surrender** (Conformist) → **avoidance** (Separate Ways). Position depends on: *can you change it?* × *how bad is it?* × *is the relationship worth the coupling?*

> **Catalog one-liner:** **insulate** (ACL · Bubble Context · Separate Ways) + **integrate** (Conformist · Customer/Supplier · OHS · Published Language · Shared Kernel · Partnership) + **replace** (Strangler Fig · Branch by Abstraction) + **make-safe** (Characterization tests · Seams) + **recover** (Extract Context · refactor toward insight). Core defensive combo = **ACL + Bubble Context**; core migration move = **Strangler Fig**.

---

## Pitfalls / anti-patterns

- ❌ **No ACL — using legacy objects directly** in your new code. The mess leaks in; your clean model rots. *Always translate at the boundary.*
- ❌ **Big-bang rewrite** to "do it properly." Enormous risk, no incremental value. Use bubble + strangler instead.
- ❌ **Over-modeling a small feature.** If it's a field or a CRUD screen, just extend the legacy — a bubble context is overkill (KISS).
- ❌ **Leaky ports** — a port method that returns a legacy dict. Ports speak *your* language only (clean VOs/DTOs).
- ❌ **Trying to understand the whole legacy.** Map only the slice your feature touches.

## When NOT to do this
- **Small feature** (add a column, a flag, a simple screen) → just extend the legacy code. Bubble + ACL is over-engineering.
- Reserve this playbook for a **feature with real rules** worth modeling cleanly, living in a messy neighborhood.

> **The one-liner:** to add a well-designed feature to a messy codebase, **build a clean DDD bubble context for it, define ports in your own language, and reach the legacy world only through an anti-corruption layer that translates its ugly shapes into your clean model** — test the bubble with plain objects and contract-test the ACL, then optionally strangle the legacy over time. Model cleanly inside the island; quarantine the mess at the boundary; never rewrite the ocean.

*Related: strategic DDD / context mapping (`appendix-lld-techniques-map.md` → "Applying DDD to a feature in an existing product"), ports & adapters, and the Strangler Fig / refactoring topics.*
