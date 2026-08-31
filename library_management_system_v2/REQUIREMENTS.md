1. Who are the stakeholders ?
   1. members
   2. Administrators
   3. Librarians

2. What is the core business problems that we are solving ?
   1. Librarian has to go to each rack and see by himself if book/s asked is available or not.
   2. Librarian need to see book issues logs to find out who issued book.
   3. librarian needs to find out if books issued is returned or not.
   4. maintaining of books issues and return add late fine.

3. User Story:-
   1. As a Librarian, I want to see if a book is available or not.
      1. If Book is available, then i eligible for issuing else not.
   2. As a librarian, I want to see all the lists of books whose due date is passed
   3. As a librarian, i want system should calculate late fine charges and notify user.
   4. As a system Admin, I should have access to add more books, delete books, update quantity of books.
   5. As a system admin, i should be able to add/delete members to the system.
   6. As a member, I should be able to list/search books of my choice based on filters.
   7. As a member, I should be able to issue a book.
   8. As a member, i want to return book
   9. As a member, i want to pay fines.
   10. As a librarian, i want to mark boo as damaged.

4. Business Rules:-
   1. A book can have multiple copies.
   2. A book once issued, must returned within 5 days.
   3. A fine will be charged Rs 5/per day.
   4. A member can borrow 2 books at a time.
   5. No books cannot be renewed.
   6. Lost/damaged books will be not listed to member but are visible to librarian

5. Non-Functional Requiremts.
   1. 100 members should access this system for 1st phase of system.
   2. 500 Books will be there in library.
   3. it should be 24/7 available.


For my Reference:-
 ┌───────────────────┬───────────────────────────────────────┬───────────────────┐
  │     Your step     │            We'll do it as             │      Status       │
  ├───────────────────┼───────────────────────────────────────┼───────────────────┤
  │ 1. Read docs      │ + Ubiquitous Language glossary        │ ✅ done (last     │
  │                   │                                       │ msg)              │
  ├───────────────────┼───────────────────────────────────────┼───────────────────┤
  │ 2. Use cases &    │ Use-case list + actor journeys        │ ⬅️ let's do this  │
  │ user journey      │                                       │ next              │
  ├───────────────────┼───────────────────────────────────────┼───────────────────┤
  │ 3. Find           │                                       │ partly done       │
  │ Domains/Entities  │ Entities + Value Objects (split out)  │ (classification   │
  │                   │                                       │ table)            │
  ├───────────────────┼───────────────────────────────────────┼───────────────────┤
  │ 4. Invariants     │ state now ✅ / enforce during step 8  │ half done         │
  ├───────────────────┼───────────────────────────────────────┼───────────────────┤
  │ 5. Group into     │ Aggregate boundaries + roots          │ pending           │
  │ Aggregates        │                                       │                   │
  ├───────────────────┼───────────────────────────────────────┼───────────────────┤
  │ 6. Relationships  │ by-ID references, not object refs     │ pending           │
  │ among Aggregates  │ (I'll teach why)                      │                   │
  ├───────────────────┼───────────────────────────────────────┼───────────────────┤
  │ 7.                │                                       │                   │
  │ Responsibilities  │ what each root owns/protects          │ pending           │
  │ per Aggregate     │                                       │                   │
  ├───────────────────┼───────────────────────────────────────┼───────────────────┤
  │ 8. Identify &     │ code: VOs → entities → aggregates,    │                   │
  │ write domain      │ enforce invariants here               │ pending           │
  │ classes           │                                       │                   │
  ├───────────────────┼───────────────────────────────────────┼───────────────────┤
  │ 9. Services       │ split: Domain Services vs Application │ pending           │
  │                   │  Services                             │                   │
  ├───────────────────┼───────────────────────────────────────┼───────────────────┤
  │ 10. Repository    │ one repo per aggregate root,          │ pending           │
  │ layer             │ interface in domain                   │                   │
  ├───────────────────┼───────────────────────────────────────┼───────────────────┤
  │ 11.               │ FastAPI thin layer                    │ pending           │
  │ Controllers/API   │                                       │                   │
  ├───────────────────┼───────────────────────────────────────┼───────────────────┤
  │ 12. Artifacts     │ class diagram, ER diagram, activity   │ we'll generate as │
  │                   │ diagram, dir structure                │  we go            │
  ├───────────────────┼───────────────────────────────────────┼───────────────────┤
  │                   │ SOLID + patterns                      │                   │
  │ (woven in)        │ (Strategy/State/Factory/Observer)     │ per-step          │
  │                   │ when a real problem demands           │                   │
  └───────────────────┴───────────────────────────────────────┴───────────────────┘

   

