# Step 1 — Discovery & Ubiquitous Language

*Series: Designing a Library Management System with DDD · Chapter 1 of 12*

---

When most engineers get an LLD problem, the first thing they type is `class Book:`. That's the mistake. The first thing you should produce isn't code — it's **understanding, written in the language of the business.** This chapter is entirely about thinking, and it's the single highest-leverage step in the whole design. Get the model right on paper and the code almost writes itself. Get it wrong, and no amount of clean code will save you.

We'll do three things:

1. Read the requirements and extract the **Ubiquitous Language**.
2. Find the one modeling insight that everything else hinges on.
3. Make a conscious **strategic** decision about boundaries (subdomains & bounded context).

---

## 1.1 Why "Ubiquitous Language" before anything else

**The concept.** A *Ubiquitous Language* is a single, shared vocabulary used identically by the business and the code. If the librarian says *"issue a book,"* then our method is `issue()` — not `createTransaction()`, not `processCheckout()`. The class is `Loan`, because that's what the librarian's ledger calls it.

**Why it matters.** Every translation between "business words" and "developer words" is a place where bugs and misunderstandings breed. When the code speaks the same language as the people who use it, conversations become precise, requirements map directly onto classes, and onboarding gets dramatically easier. This is the cheapest, most under-used technique in all of software design.

So before modeling, we read [`REQUIREMENTS.md`](../REQUIREMENTS.md) and harvest every meaningful noun and verb into a glossary.

### The glossary

| Term | Meaning in our domain | Watch out for |
|---|---|---|
| **Book** (a.k.a. *Title* / *Work*) | The abstract work — *"Clean Code by Robert C. Martin."* Carries ISBN, author, genre. | This is **not** a physical object. You never "borrow a Book." |
| **Book Copy** | One physical item of a Book sitting on a shelf. This is what gets issued, returned, lost, or damaged. | The rule *"a book can have multiple copies"* lives here. |
| **Member** | A registered person who borrows copies. | Has a hard borrowing limit. |
| **Librarian** | Staff who issues/returns copies, views overdue lists, and marks copies damaged. | An **actor** (system user), not necessarily a domain entity yet. |
| **Admin** | Manages the catalog and membership (add/remove books and members). | Mostly a **role**. |
| **Loan** (a.k.a. *Issue record*) | The fact that a specific **copy** is out to a specific **member**, with a due date. | The beating heart of the system. |
| **Fine** | Money a member owes because a Loan came back late. | ₹5/day; 5-day loan limit. |
| **Due Date** | The date a copy must be returned by. | borrow date + 5 days. |
| **Availability** | Whether a copy can be issued right now. | Driven by the copy's status (loaned / lost / damaged). |

These exact words will become our class names, method names, and module names. That's the whole point — no translation layer between speech and code.

---

## 1.2 The keystone insight: **Book ≠ Book Copy**

Re-read requirement #1: *"A book can have multiple copies."* It looks innocent. It is the most important sentence in the document.

The beginner model is one class with a counter:

```text
Book { title, author, isbn, quantity: int }   ❌
```

It works right up until the business asks a question the model can't answer:

- *"Which specific copy is damaged?"* — `quantity` can't say.
- *"Member X returned a copy — which one, and what condition is it in?"* — can't say.
- *"Copy #3 is lost; hide it from members but show it to the librarian."* (requirement #6) — can't say.

A plain integer throws away the **identity of each physical item**, and several requirements are *about* individual physical items. So we split the concept in two:

- **`Book`** — catalog metadata: title, author, ISBN, genre. There is **one** `Book` per title.
- **`BookCopy`** — a physical item with its **own identity and its own status** (available / loaned / lost / damaged), belonging to a `Book`. There are **many** copies per book.

> **The rule that falls out of this:** *you issue a `BookCopy`, never a `Book`.* A member searches the catalog (Books) but borrows a physical item (a Copy). Almost every later design decision — availability, fines, the lost/damaged visibility rule — depends on getting this split right at Step 1.

This is what "modeling before coding" buys you: we found a structural decision that would have been painful to retrofit, and it cost us nothing but a careful read.

---

## 1.3 Strategic design: subdomains & the bounded-context decision

Full DDD has two halves: **strategic** (how you carve the whole system into boundaries) and **tactical** (the entities/value-objects/aggregates inside a boundary). Most LLD tutorials skip strategic design entirely. We'll do it *briefly and deliberately* — because deciding **not** to split is itself a decision worth making consciously.

### Subdomains — where does the real complexity live?

Breaking the requirements into business areas and labelling each:

| Subdomain | Responsibility | Type | Why |
|---|---|---|---|
| **Lending / Circulation** | Issue, return, due dates, borrowing limits | **Core** | This is the actual problem the library has. Model it with the most care. |
| **Fines / Billing** | Calculate and collect late fees | Supporting | Important, but the rules are simple. |
| **Catalog** | Books, copies, search, availability | Supporting | Mostly CRUD + queries. |
| **Membership** | Members and admin management | Supporting | CRUD. |
| **Notifications** | Tell members about due dates / fines | Generic | Could be any email/SMS provider. |

The payoff: this tells us **where to spend our modeling effort.** We'll lavish attention on **Lending** (aggregates, invariants, state machines, pluggable policies) and keep Catalog/Membership pleasantly boring.

### One bounded context — on purpose

A *bounded context* is an explicit boundary inside which the model and language are perfectly consistent. You could split this system into five microservices. **For this scale, you absolutely should not.**

- 100 members, 500 books, one branch.
- Splitting introduces network calls, distributed transactions, and operational overhead to solve scaling problems **we do not have.**

So the decision: **one bounded context** (the *Library* context), organized internally into modules that mirror the subdomains — `catalog/`, `lending/`, `fines/`, `membership/`. One model, one language, zero network boundaries.

> **Teaching point:** knowing *when not to split* is as much a DDD skill as knowing when to. Reaching for microservices here would be cargo-culting an architecture built for 10M users onto a problem that has 100. Match the design to the scale.

> #### 🌱 Note: the subdomains are your *future* microservice seams
>
> "One bounded context now" doesn't throw the split away — it **defers** it along lines we've already drawn. If this system ever outgrew one deployable, the subdomains above are exactly the **candidate service boundaries**, because each was grouped for *high cohesion inside, low coupling outside* — the precise property you want at a service edge.
>
> The chain has a middle step people skip:
>
> ```
> Subdomain (problem space)  →  Bounded Context (its own model + language + data)  →  Microservice (a deployable)
> ```
>
> A subdomain is only a *candidate*; it becomes a service once you promote it to its **own bounded context** — its own model and data, talking to others through explicit contracts (APIs/events), never shared objects or a shared DB. Today all five live inside the one *Library* context as modules; extraction means promoting one out.
>
> **What keeps that promotion cheap** is the tactical work in later steps — especially **aggregates referencing each other by ID, not by object** (Step 5). `Loan` already holds a `member_id`, not a `Member`, so pulling Membership into its own service just turns a local lookup into a remote one — the seam is *pre-cut*. The thing to watch is any **transaction that spans aggregates** (the `borrow` flow touches BookCopy + Loan): keep those within one subdomain, or a split forces you into sagas / eventual consistency — and *that* cost, not fashion, is what should drive the decision.
>
> **The usual order of departure:** **Notifications** (generic) and **Fines / Billing** leave first; **Lending** (core) is the last thing you'd ever fragment. But **don't pre-split** — keep the seams *visible and clean* (separate modules, by-ID references, no cross-subdomain object reach-ins) so the option stays cheap, and stay a modular monolith until real scaling or team-autonomy pressure forces a split. **The modular monolith *is* the design that keeps microservices a future option without paying their cost today.** (See the aggregate-vs-microservice sidebar in Step 5.)

---

## What we produced in Step 1

- A **Ubiquitous Language** glossary — the vocabulary all our code will speak.
- The keystone modeling decision: **`Book` (catalog) vs `BookCopy` (physical item)**, and the rule *"you issue a copy, not a book."*
- A **subdomain map** that tells us where the modeling effort belongs (Lending is core).
- A conscious strategic decision: **one bounded context, four internal modules** — no microservices.

No code yet, and that's correct. We've removed the most expensive risks — modeling risks — for the price of a careful read and some honest thinking.

## Key takeaways (the transferable lessons)

1. **Start with language, not classes.** A glossary is the cheapest design artifact and the highest-leverage one.
2. **Hunt for the concept the requirements quietly depend on.** Here it was hidden in five words: *"a book can have multiple copies."*
3. **Make boundary decisions explicitly** — including the decision *not* to split. Match architecture to actual scale.

## Principles in play

*OOP and SOLID aren't a separate step — they're the quality bar applied inside every step. Here's what this chapter exercised:*

| Principle | How this step applied it |
|---|---|
| **Abstraction** (OOP) | Splitting `Book` (catalog concept) from `BookCopy` (physical item) — finding the *right* abstraction before writing any code. |
| **SRP** (Single Responsibility) | The subdomain map gives each area exactly one job (Lending, Catalog, Fines, Membership); our modules will mirror it. |
| **KISS / YAGNI** | One bounded context, no microservices — we refused complexity the scale doesn't justify. |
| **Ubiquitous Language** (DDD) | The glossary is the foundation every later principle and pattern builds on. |

---

*Next — Step 2: Use cases & user journeys. We'll turn the requirements into a prioritized list of use cases and walk each actor (Member, Librarian, Admin) through their journey, which is what tells us the behavior our model has to support.*


# Phase-2

** Here we will build mostly code perspective.

## 2.1 what we have done here
    - * Defined Layer for code structure.
    - src
├── api
│   └── __init__.py
├── application
│   └── __init__.py
├── domain
│   └── __init__.py
└── infrastructure
    └── __init__.py
tests
└── __init__.py

## Ubiquituous Language:-
    * Book
    * BookCopy
    * Member
    * Loan
    * Fine
    * ISBN, Money, DueDate
    * 


