# Appendix — Designing a Monolith That Can Become Microservices

*A general architecture note (not tied to one step). The LMS applies these ideas; this is the transferable playbook.*

---

An architect who chooses a **monolith now** but wants **microservices to stay a cheap future option** is describing a **modular monolith**. The entire trick is one mindset:

> **Design each module as if it's already a separate service — just deployed in-process.** Then "going to microservices" changes *how modules talk and deploy*, not *what the code is*.

Get that right and a split is "give a module its own process, database, and network transport" — the domain logic, contracts, and structure stay put.

---

## The principles (ordered by how much pain they save)

1. **Modularize by business capability, not by technical layer.** Top-level structure = bounded contexts / subdomains (`catalog`, `lending`, `billing`), each a **vertical slice** (its own api → application → domain → infrastructure). *Not* `controllers/ services/ models/` folders that mix every feature. Each module = one future service. The single most important decision.

2. **Enforce hard module boundaries — no reaching into internals.** Each module exposes a **public interface/facade**; the rest is private. Module A calls B's *published contract*, never B's entities/repos/tables. In a monolith this discipline **erodes silently** (nothing stops an `import`), so *automate* the check — `import-linter` (Python), ArchUnit (Java), Nx module boundaries (TS). A boundary you don't enforce isn't a boundary.

3. **Each module owns its data — logical database-per-service from day one.** Even in one physical DB: a **schema per module**, and **no cross-module JOINs or foreign keys** across boundaries. Reference other modules' data **by ID**. This is the **hardest thing to retrofit** — a shared table with cross-module FKs is what makes a split take months. Nearly free at the start.

4. **Talk between modules the way services would — even in-process.**
   - *Synchronous:* call B's **interface** through an in-process implementation that could later become an HTTP client. The caller depends on the interface, so in-process → network swaps one adapter, not the caller.
   - *Asynchronous:* publish **domain events** to an in-process bus that could later become Kafka/RabbitMQ. Handlers don't care where the event came from.
   This is what makes the transport swap a *config change*, not a *code change*.

5. **Keep the shared kernel tiny and stable.** Only universal, rarely-changing types (IDs, base error, a few shared value objects). A fat shared kernel is the thing that *won't* separate; everything domain-specific belongs to its module.

6. **Never rely on cross-module ACID transactions.** Keep a transaction **within one module**. Where a flow spans modules, coordinate with **events + eventual consistency (saga)** — or at least design so you *could*. Within-module stays transactional.

7. **Ports & adapters (hexagonal) for all infrastructure.** DB, cache, message bus, external APIs behind interfaces the domain owns. On split, replace an adapter (in-process → network); domain/application code is untouched.

8. **Design module APIs as coarse-grained and remote-shaped.** Pass DTOs/IDs, not internal entities. Make calls chunky (one meaningful operation), not chatty. Add **idempotency** where it'll matter. "In-process, but shaped like it's over a network."

9. **Statelessness + externalized config (12-factor) + observability.** No hidden shared in-memory state between modules; config/secrets from the environment; structured logs with **correlation IDs** from day one, so cross-module tracing works the moment calls become network hops.

---

## What changes vs. what stays on the split (the payoff)

| Stays the same ✅ | Changes 🔧 |
|---|---|
| Domain logic & invariants | Transport: in-process call → HTTP/gRPC/event |
| Module boundaries & public contracts | Deployment: 1 process → N services + gateway |
| By-ID references between modules | Physical data: shared DB → database-per-service |
| Ports (the interfaces) | Adapters behind ports (in-proc → network client) |
| Event definitions & handlers | Event bus: in-memory → real broker |
| — | New: retries, timeouts, saga, tracing, versioning |

If done right, **domain and application code barely move** — you add plumbing at the edges. That is "minimum changes."

---

## The two failure modes to avoid

- **Distributed monolith** (worst outcome): deployment is split, but modules still share a database / call each other's internals / need synchronous chains per request. Microservice pain, none of the benefit. Prevented by principles #2, #3, #4.
- **Premature distribution:** building brokers, gateways, sagas *before* real scale/team pressure. Over-engineering.

---

## The KISS caveat

Do **not** build the distributed machinery upfront. The monolith stays a monolith — one process, one deployment, in-process calls, one physical DB (with logical separation). You pay only for **clean seams**: capability modules, enforced boundaries, data ownership, by-ID references, ports, events. Those are cheap now and are ~90% of the split cost later. **Build the seams, not the plumbing.**

> **One-liner:** organize by business capability into modules with **enforced boundaries, owned data, by-ID references, and port/event-based communication** — then a microservice split is "give a module its own process, database, and network transport," while its domain, contracts, and structure stay put.

---

## What to share across services — and how

Splitting raises a practical question: what happens to shared code and common dependencies? The guiding principle: **shared code = coupling. The more services share, the less independent they are.** So share as little as possible, and share it in the loosest-coupling way that works.

### 1. The shared *kernel* (your own tiny cross-cutting domain code — IDs, base error)

On a split it has three possible fates — pick per type, and prefer the lower-coupling one:

| Fate | When | Coupling |
|---|---|---|
| **Dissolve into primitives** | the type is trivial over the wire (an ID is just a string/UUID in JSON) — each service uses its own local type / plain string at the boundary | none |
| **Duplicate per service** | a 5-line base class; copy it, accept drift | none (drift risk) |
| **Thin versioned library** | genuinely reused, worth central maintenance | some — keep it thin, stable, backward-compatible, independently adopted |

Because we kept the kernel tiny (typed IDs + base error), ours mostly **dissolves** — that was the point of keeping it small.

### 2. Shared *contracts* ≠ shared *kernel*

What services genuinely must agree on is **API/event schemas** (OpenAPI, protobuf, event definitions) — *versioned interface definitions*, **not** shared domain code. The logic behind each contract stays private to its service. When `lending` calls `catalog`, they share the *contract*, not `catalog`'s `BookCopy` class.

### 3. Common *third-party* / platform libraries

Different problem from the kernel. **Standardize the *choice*, not a forced shared artifact:**

| Bucket | Approach |
|---|---|
| Trivial ubiquitous libs (http client, JSON, pydantic) | each service **declares its own**; standardize the *choice* via a guideline |
| Cross-cutting glue (logging/tracing/auth/error-format) | a **thin, backward-compatible internal "platform"/starter library** *or* a **service template (golden path)** |
| Pure-infra concerns (mTLS, retries, rate-limiting, tracing) | push **out of the app** into a **sidecar / service mesh** — not a library at all |

Align versions with a **recommended BOM / constraints file** (recommendation, not mandate), never a lockstep "everyone on 2.0 by Friday."

### Who maintains what — the ownership rule

> Every service is **independently deployed and independently chooses its dependency versions**. But shared *internal* code is **maintained centrally (one owner, one versioned artifact) and consumed independently** — not re-implemented per team. The independence is in **adoption timing**, not in re-maintaining the same code N times. (Duplication-per-service is a separate, deliberate choice reserved for trivial things.)

**The trap:** a fat "common" library everyone must upgrade in lockstep — that re-couples the services you split apart. Keep shared libraries thin, stable, backward-compatible, and independently adoptable; prefer templates + guidelines + a BOM over a mandatory runtime bundle.

---

## Internal vs public APIs — north-south and east-west

Not every service is meant for end users. `fines` and `notifications`, for example, are called by *other services*, never directly by a member. Two kinds of traffic:

- **North-south** = external clients ↔ the system, through a **public API gateway**. What end users hit.
- **East-west** = service ↔ service, *inside* the system. Never touches the public internet.

### How a service stays internal (not exposed to end users)

You don't rely on "please don't call it" — you make it **unreachable** from outside at the network layer:

1. **No public ingress.** Only the gateway (and the public services it fronts) gets a public route. An internal service gets a **cluster-internal address only** (e.g. Kubernetes `ClusterIP` `fines.internal`, not a `LoadBalancer`/`Ingress`) — there's no public URL to hit.
2. **The gateway exposes only public endpoints** and does not proxy internal ones — so `fines`' API is invisible to users.
3. **Network policy / service mesh** (Istio/Linkerd): "`fines` accepts traffic only from `lending`/`membership`," enforced with **mTLS + authorization policies**. Even inside the cluster, only allowed callers get through.
4. **Service identity, not user identity.** Internal calls authenticate with **service credentials** (mTLS certs / service accounts / internal tokens) — a different auth path from end-user JWTs.

### How services talk east-west (prefer async)

- **Asynchronous (events) — preferred:** `lending` publishes `LoanReturnedLate`; `fines` subscribes and assesses the fine. `lending` needn't know `fines` exists → maximum independence, and `fines` can be down without blocking a return.
- **Synchronous (internal HTTP/gRPC):** when an immediate answer is needed (`lending` calls `fines.internal/assess`). Simpler, but couples them at request time.

### A service can be internal-only, public-only, or both

- **Internal-only:** `fines`, `notifications` — no public route.
- **Public + internal:** `catalog` exposes search to users *and* answers "is copy X available?" to `lending`.
- **Member-facing views of internal data:** a user *can* see their fines — not by calling `fines`, but via the **gateway / BFF** (backend-for-frontend), which makes the east-west call and returns a member-friendly response. The user only ever hits the gateway.

The internal API still has a **contract** — just a *private* one, with a few known consumers, so it can evolve faster than a public north-south API (which needs versioning + backward-compat).

### How this maps to the monolith today (no new machinery)

- **`api/` layer** = north-south (exposed to users).
- **A module calling another module's interface / publishing an in-process event** = east-west (internal).

`lending` telling `fines` to assess a fine is, today, an **in-process call or in-process domain event**. On a split it becomes an **east-west network call or broker event**, and you simply *don't expose* `fines` on the gateway. The code doesn't change — only transport and routing config.

> **One-liner:** internal (east-west) traffic never goes through the public gateway and isn't exposed to users — internal services get a **cluster-internal address only**, protected by **network policy / mesh mTLS + service identity**, and talk via **internal HTTP/gRPC or (preferably) events**. Users reach only the **gateway**, which fronts public services and makes the east-west calls on their behalf. In the monolith, "internal call" is just calling another module's interface / an in-process event.

---

## How the LMS applies this

- **Capability modules:** `domain/` is organized by subdomain (`catalog`, `lending`, `fines`, `membership`, `notifications`) — each a future service (see step-08a §8a.1).
- **Enforced boundary:** no subdomain imports another subdomain's internals; every subdomain depends only on the tiny `shared/` kernel (typed IDs + base error).
- **By-ID references:** `Loan` holds `member_id`/`copy_id`, never a `Member`/`BookCopy` object (step 5–6).
- **Within-module transaction:** the `borrow` flow's aggregates (BookCopy + Loan) sit in one subdomain (Lending), so it stays a local transaction rather than a cross-service saga (step-5 aggregate-vs-microservice sidebar).
- **Still a monolith on purpose:** one bounded context, one deployable, for ~100 members (step 1) — the split is kept a cheap option, not built prematurely.

*The outer layers (`api/`, `application/`, `infrastructure/`) should follow the same subdomain-aligned seams so a split is a lift-out across all four layers, not just the domain.*
