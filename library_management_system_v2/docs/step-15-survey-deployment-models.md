# Step 15 — Survey: The Standard Ways to Run It

*Series: Designing a Library Management System with DDD · Chapter 15 — Part II*

---

With a production-ready app (Step 14), the question becomes: *where and how does it actually run?* There isn't one answer — there's a **spectrum**, from "you manage everything" to "the platform manages everything." This chapter tours the whole landscape so you can *choose deliberately*, then the rest of Part II goes deep on one path.

> **The organizing axis:** as you move up the spectrum, you trade **control** for **lower operational burden**. Neither end is "better" — the right choice depends on your scale, team size, and reliability needs. (This is the delivery-side echo of Part I's *"one bounded context, no microservices for 100 members."* **Match the deployment to the problem.**)

We'll walk it weakest-abstraction-first, each anchored to *how you'd deploy the LMS*.

---

## 15.1 Bare metal / single VM, deployed by hand

You rent a Linux VM (an AWS EC2 instance, a DigitalOcean droplet), SSH in, install Python, copy the code, and run Gunicorn behind **Nginx** (a reverse proxy doing TLS termination, static files, and request buffering), kept alive by **systemd**.

```ini
# /etc/systemd/system/lms.service  — systemd keeps the app running & restarts it
[Service]
ExecStart=/opt/lms/venv/bin/gunicorn src.api.main:app -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000
Restart=always
EnvironmentFile=/opt/lms/.env
[Install]
WantedBy=multi-user.target
```

- ✅ Total control; cheapest at tiny scale; you only need to know Linux.
- ❌ **Manual and fragile** — a "snowflake" server that works because of something someone installed two years ago. No easy scaling, you patch the OS yourself, and every deploy risks downtime.
- **Use when:** a hobby project, a low-stakes internal tool, or *learning the fundamentals*.

---

## 15.2 VM + configuration management / golden images

Same runtime, but you stop doing it by hand. You either automate server setup with **Ansible/Chef/Puppet**, or bake a **golden machine image** (Packer → an AMI) and deploy by launching VMs from it behind a load balancer in an **auto-scaling group**. To deploy a new version, you roll out new VMs and retire the old. This was *the* standard production setup before containers.

- ✅ Reproducible servers, horizontal scaling via the load balancer + ASG, no manual SSH.
- ❌ Machine images are heavy and slow to build; you still own the OS and the VMs; resource-inefficient (typically one app per VM).
- **Use when:** you're committed to VMs, need real reliability, but aren't adopting containers.

---

## 15.3 PaaS (Platform-as-a-Service)

Heroku, Render, Railway, Fly.io, Google App Engine, AWS App Runner. You `git push` (or point the platform at your repo); it builds, runs, scales, restarts, and hands you TLS + a URL. You write a one-line start command and maybe a tiny config file. **The platform is the ops team.**

```yaml
# render.yaml — the ENTIRE "infrastructure" for the LMS on a PaaS
services:
  - type: web
    name: lms
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn src.api.main:app -k uvicorn.workers.UvicornWorker
    envVars:
      - key: DATABASE_URL
        fromDatabase: { name: lms-db, property: connectionString }
```

- ✅ **The fastest path to production.** Servers, TLS, scaling, restarts, log aggregation — all handled. Minimal ops burden; a solo dev can run a real service.
- ❌ Less control, can get pricey as you grow, some vendor lock-in, limited escape hatches for unusual needs.
- **Use when:** startups, MVPs, small teams who want to ship features, not run infrastructure. **An underrated default** — *most apps never need more than this.* The LMS at 100 members would be perfectly happy here.

---

## 15.4 Containers on a single host (Docker / Docker Compose)

You package the app + its *exact* dependencies + runtime into an immutable **container image** (Step 16), and run it with Docker. **Docker Compose** brings up the app *and* its Postgres together with one command — superb for local dev and small single-server production.

```yaml
# docker-compose.yml — LMS + its database, one `docker compose up`
services:
  api:
    build: .
    ports: ["8000:8000"]
    environment:
      DATABASE_URL: postgresql://lms:secret@db:5432/lms
    depends_on: [db]
  db:
    image: postgres:16
    environment: { POSTGRES_USER: lms, POSTGRES_PASSWORD: secret, POSTGRES_DB: lms }
    volumes: ["pgdata:/var/lib/postgresql/data"]
volumes: { pgdata: {} }
```

- ✅ **Kills "works on my machine"** — the image is byte-identical everywhere. Easy local/prod parity; the gateway to orchestration.
- ❌ One host = a single point of failure; no auto-healing or auto-scaling *across* machines.
- **Use when:** dev/test environments, small single-server production, and as the stepping stone to Kubernetes.

---

## 15.5 Container orchestration (Kubernetes, AWS ECS, Nomad)

You run containers across a **cluster** of machines, and the orchestrator handles scheduling, self-healing (restart crashed containers, reschedule off dead nodes), scaling, rolling updates, and service networking. **This is the de-facto standard for serious container workloads** — and our deep-dive from Step 16 on.

- ✅ Self-healing, auto-scaling, zero-downtime deploys, runs the same on any cloud, vast ecosystem.
- ❌ **Significant complexity** — a real learning curve and ongoing operational investment. Easy to adopt *too early*.
- **Use when:** multiple services, genuine scale/reliability needs, and a team to operate it. **Not** for a single small app — that's over-engineering (a PaaS is the right call there).

---

## 15.6 Serverless / Functions (AWS Lambda + API Gateway, Google Cloud Run)

You hand the platform your code (or a container) and it runs it **on demand** — scaling to **zero** when idle, and out to thousands under load. You pay per request. FastAPI runs on Lambda via an adapter (**Mangum**), or more naturally on **Cloud Run / AWS App Runner**, which run a *container* request-by-request.

```python
# Lambda adapter — API Gateway → Lambda → FastAPI
from mangum import Mangum
handler = Mangum(app)
```

- ✅ No servers to manage; scales to zero (cheap when idle); scales out automatically.
- ❌ **Cold starts** (first request after idle is slow), execution time/size limits, statefulness is awkward, and **database connection management is tricky** (many short-lived function instances can storm a DB with connections — needs a proxy/pooler).
- **Use when:** spiky or low traffic, event-driven workloads, glue code. **Cloud Run is a sweet spot** for containerized web apps that want serverless economics without Lambda's quirks.

---

## 15.7 The comparison table (the slide students screenshot)

| Approach | Control | Ops burden | Scaling | Cost at scale | Best for |
|---|---|---|---|---|---|
| Single VM (manual) | Highest | Highest | Manual | Low | Learning, hobby |
| VM + images/ASG | High | High | Auto (coarse) | Medium | Legacy/VM shops |
| **PaaS** | Medium | **Lowest** | Auto | Higher | **Startups, MVPs, most apps** |
| Docker (1 host) | High | Medium | Manual | Low | Dev/test, small prod |
| **Kubernetes / ECS** | High | **High** | **Auto (fine-grained)** | Medium | **Scale, many services** |
| Serverless | Low | Low | Auto (to zero) | Variable | Spiky, event-driven |

### How to actually choose (the decision heuristic)

Ask, in order:

1. **Is it tiny / early / a small team?** → **PaaS.** Don't out-engineer your problem.
2. **Is traffic spiky or event-driven, and statelessness easy?** → **Serverless / Cloud Run.**
3. **Many services, real scale, a team to run it, multi-cloud or on-prem?** → **Kubernetes.**
4. **Just need local prod-parity or one small server?** → **Docker / Compose.**
5. **Stuck on VMs for policy/legacy reasons?** → **VM + images + ASG.**

> **The teaching punchline:** there is no "best" — there is *appropriate for your scale, team, and reliability needs.* A 100-member library belongs on a **PaaS**. We deep-dive **Kubernetes** next not because the LMS needs it, but because it's the most *educational* path: it forces every production promise from Step 13 to become **explicit and visible** — health checks, scaling, rolling updates, networking, secrets — so you learn the concepts in the raw. Once you understand them on Kubernetes, you'll recognize that a PaaS is simply *doing all of this for you behind the curtain.*

---

## Promises served

| Promise | How the *choice* affects it |
|---|---|
| **Available** | Higher up the spectrum (PaaS/K8s) gives redundancy + auto-healing out of the box; a single VM does not. |
| **Survives failure** | Orchestration/serverless reschedule around dead machines; manual VMs need you awake at 3am. |
| **Survives change** | PaaS/K8s give zero-downtime deploys + rollback; manual deploys risk downtime. |
| **(Cost / simplicity)** | Choosing *less* platform than you need is as costly as choosing too much — over-engineering burns team time. |

## Key takeaways (the transferable lessons)

1. **Deployment is a spectrum** from "manage everything" (VM) to "manage nothing" (serverless/PaaS), trading control for lower ops burden.
2. **PaaS is the underrated default** — most apps, including a 100-member LMS, never need more. Reach for Kubernetes only with multiple services, real scale, and a team to run it.
3. **Containers (Docker) are the pivot point** — they kill "works on my machine" and are the gateway to orchestration; learn them regardless of where you deploy.
4. **Serverless trades servers for cold starts and connection-management quirks** — great for spiky/event-driven, awkward for steady stateful web apps (unless Cloud Run).
5. **Match the deployment to the problem** — the same judgment Part I applied to *design*. Over-engineering delivery is a real and common mistake.

---

*Next — Step 16: Containerizing the LMS. We write the Dockerfile — a multi-stage, non-root, slim image — build it, run it, and produce the immutable artifact that every step from here (CI, registries, Kubernetes) revolves around. This is where "build once, deploy many" becomes concrete.*
