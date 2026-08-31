# Step 24 — Networking, TLS, Scaling & the Database Reality

*Series: Designing a Library Management System with DDD · Chapter 24 — Part II*

---

The LMS is running on Kubernetes with safe releases. Two practical questions remain: **how does a user's request physically reach it (securely)?** and **what happens when there are a lot of users?** The first half is networking + TLS; the second is scaling — ending with the chapter's most important lesson: **your stateless app scales trivially, but your database does not, and the database is where scaling actually gets hard.**

---

## 24.1 The full network path (the journey of one request)

```
 user's browser
   │  1. DNS:  api.library.example.com → an IP
   ▼
 Cloud Load Balancer (L4/L7)                    ← the public entry IP
   │  2. forwards to the cluster
   ▼
 Ingress Controller (Nginx / Traefik / cloud)   ← 3. terminates TLS, routes by host/path
   │
   ▼
 Service `lms` (ClusterIP)                        ← 4. load-balances across READY pods
   │
   ▼
 Pod (gunicorn → uvicorn workers → FastAPI)       ← 5. handles the request → domain → DB
```

Each hop is a thing you configure:

- **DNS** maps your domain to the load balancer's IP (an `A`/`CNAME` record at your DNS provider, often automated by **external-dns**).
- **Load balancer** spreads traffic and is the stable public entry point. **L4** balances TCP (fast, dumb); **L7** understands HTTP (routes by host/path, the ingress's job).
- **Ingress controller** is the cluster's HTTP front door — it does host/path routing, TLS termination, and often rate limiting (Step 26). The `Ingress` object (Step 21) is the *rules*; the controller is the *engine* that enforces them.
- **Service** gives the pods one stable virtual IP and load-balances to **ready** pods only.
- **Pod** finally runs your code.

### Service types (a frequent point of confusion)

| Type | Reachable from | Use |
|---|---|---|
| **ClusterIP** (default) | inside the cluster only | the LMS Service — fronted by the Ingress |
| **NodePort** | a port on every node | rarely used directly; building block |
| **LoadBalancer** | the internet (provisions a cloud LB) | exposing a Service directly without an Ingress |

For an HTTP app you almost always use **ClusterIP + Ingress**, not a `LoadBalancer` per service (one shared ingress LB is cheaper and does TLS/routing for everything).

---

## 24.2 TLS — HTTPS, issued and renewed automatically

Every production endpoint must be **HTTPS** — encrypted in transit (protects member data, credentials, and is table stakes for browsers/SEO). The standard setup:

- **TLS terminates at the ingress** — the ingress controller holds the certificate, decrypts incoming HTTPS, and forwards plain HTTP to pods inside the (trusted) cluster network. (For stricter zero-trust, you re-encrypt pod-to-pod with a service mesh — overkill for the LMS.)
- **Certificates are issued and renewed automatically** by **cert-manager** + **Let's Encrypt**. You declare a certificate; cert-manager proves domain ownership, obtains the cert, stores it in a Secret, and **auto-renews** before expiry. No more "the site went down because the cert expired" incidents.

```yaml
# cert-manager issues + auto-renews the cert referenced by the Ingress (Step 21)
apiVersion: cert-manager.io/v1
kind: Certificate
metadata: { name: lms-tls, namespace: lms-prod }
spec:
  secretName: lms-tls                      # the Ingress's tls.secretName
  dnsNames: [api.library.example.com]
  issuerRef: { name: letsencrypt, kind: ClusterIssuer }
```

> The `cert-manager.io/cluster-issuer: letsencrypt` annotation on the Step 21 Ingress is what wires this up. TLS becomes a declarative, self-healing detail — exactly the kind of toil you want automated away.

---

## 24.3 Scaling the app tier (the easy half)

Because the LMS is **stateless** (Step 14), scaling out is trivial — any request can hit any pod:

- **Horizontal scaling (scale *out*)** — add more pods. The **HPA** (Step 21) does this automatically on CPU/memory or custom metrics (e.g. requests/sec, p95 latency). Preferred: many small interchangeable copies.
- **Vertical scaling (scale *up*)** — give each pod more CPU/RAM. Limited (a machine has a ceiling) and disruptive (restart to resize); used to *right-size*, not as the main lever.
- **Cluster autoscaler** — when the HPA wants more pods than the nodes can fit, the cluster autoscaler **adds nodes** (and removes them when idle). Two layers: HPA scales *pods*, cluster autoscaler scales *machines*.

```
 traffic ↑  →  HPA adds pods  →  nodes full?  →  cluster autoscaler adds nodes
 traffic ↓  →  HPA removes pods →  nodes idle?  →  cluster autoscaler removes nodes
```

This part is genuinely easy — *and it's easy entirely because of the stateless design from Part I.* Stateful apps can't do this.

---

## 24.4 The database reality (the hard half — the headline)

Here's the lesson students must internalize:

> **You can scale the app tier to 100 pods in minutes — and then they all hammer one database, which falls over.** The stateless tier scales out effortlessly; the **stateful database is the real bottleneck**, and scaling it is fundamentally harder because it holds state that must stay consistent.

### The first thing that breaks: connection storms

A Postgres instance has a **hard cap on concurrent connections** (often ~100). Do the math: 20 app pods × a pool of 20 connections each = **400 connections** → the database refuses new ones → outage. Scaling the app *out* can *kill* the database.

**The fix: a connection pooler** (**PgBouncer**) sits between the app and Postgres, multiplexing thousands of app-side connections onto a small set of real database connections. Plus: bound each pod's pool size sensibly.

```
 [40 pods × small pool] ──► PgBouncer ──► [ ~50 real Postgres connections ]
                            (multiplexes; absorbs the storm)
```

### The levers for database scale (in order of reach-for)

| Lever | What it does | When |
|---|---|---|
| **Right-size + tune** | Bigger DB instance, good indexes (Step 18), tuned config | First, always |
| **Connection pooling** (PgBouncer) | Stops connection storms | As soon as you run multiple pods |
| **Caching** (Redis) | Serve hot reads from memory, skip the DB | Read-heavy hot data (e.g. catalog search) |
| **Read replicas** | Replicate to read-only copies; send reads there, writes to primary | Read-heavy load (our library is read-heavy: searches ≫ borrows) |
| **Vertical scaling** | A bigger database machine | Cheap early win; has a ceiling |
| **Sharding / partitioning** | Split data across multiple databases | **Last resort** — huge complexity; only at massive scale |

**Caching pattern (cache-aside)** for the LMS catalog search:
```python
def search_books(keyword):
    if (hit := cache.get(keyword)) is not None:
        return hit                          # served from Redis, DB untouched
    result = book_repo.search(keyword)      # miss → hit the DB
    cache.set(keyword, result, ttl=300)     # populate for next time
    return result
```
(Caching introduces **invalidation** — stale data when a book changes — so cache only what tolerates slight staleness. "There are only two hard problems…")

### The reality check for *our* LMS

> 100 members, 500 books, library reads ≫ writes. A **single, well-sized, well-indexed Postgres needs none of this.** Connection pooling the moment you run >1 pod, maybe a small read cache for search — that's it. Read replicas, sharding, and Redis clusters would be **over-engineering** — the same "match it to the scale" judgment from Part I. We teach the levers so you *recognize the bottleneck and know the ladder*, not so you climb it prematurely.

---

## Promises served

| Promise | How this chapter advanced it |
|---|---|
| **Available** | LB + ingress + ready-only Service routing keep traffic flowing to healthy pods; HPA + cluster autoscaler absorb load. |
| **Secure** | TLS everywhere, auto-issued/renewed by cert-manager — no expiry outages, encrypted in transit. |
| **Survives failure** | Autoscaling + pooling protect the app *and* the database under spikes instead of collapsing. |
| **Correct** | Caching done with explicit TTL/invalidation keeps reads fast without silently serving stale data. |

## Key takeaways (the transferable lessons)

1. **Know the request path** — DNS → load balancer → ingress (TLS) → Service → Pod — because every hop is something you configure and debug.
2. **Terminate TLS at the ingress and automate certs** (cert-manager + Let's Encrypt) — certificate management becomes a self-healing, declarative detail.
3. **The stateless app tier scales out trivially** (HPA for pods, cluster autoscaler for nodes) — *because* of the Part I stateless design.
4. **The database is the real bottleneck.** Scaling the app out can *crush* the DB via connection storms — front it with a **pooler**, then reach for caching → read replicas → (last resort) sharding.
5. **Match the scaling to the scale.** A 100-member LMS needs a single tuned Postgres + a pooler, not a sharded cluster. Know the ladder; don't climb it early.

---

*Next — Step 25: Observability. Everything's running and scaling — but when something breaks at 2am, can you see *what* and *why*? The three pillars (logs, metrics, traces) wired into the LMS, SLOs/SLIs that turn the library's NFRs into numbers, and alerting on the symptoms users actually feel.*
