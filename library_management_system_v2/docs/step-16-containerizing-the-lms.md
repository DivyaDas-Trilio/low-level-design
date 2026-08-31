# Step 16 — Containerizing the LMS

*Series: Designing a Library Management System with DDD · Chapter 16 — Part II*

---

This is where "build once, deploy many" (Step 13) stops being a slogan and becomes a file. We package the LMS — its code, its *exact* dependencies, and a Python runtime — into a **container image**: one immutable artifact that runs byte-identically on your laptop, in CI, in staging, and in production. Every step from here (registry, CI, Kubernetes) revolves around this artifact.

---

## 16.1 What a container actually is (and isn't)

A **container** is an isolated process on a shared host kernel, with its *own* filesystem, network, and process view — but **not** its own operating system kernel. That last part is the whole trick. Contrast with a VM:

| | Virtual Machine | Container |
|---|---|---|
| Isolates via | A full guest **OS** + hypervisor | Kernel features (namespaces, cgroups) |
| Contains | OS kernel + libs + app | Just libs + app (shares host kernel) |
| Size | Gigabytes | Tens–hundreds of MB |
| Start time | Minutes | Milliseconds–seconds |
| Density | A few per host | Hundreds per host |

> **Layman analogy 🏠:** a VM is a **separate house** (its own foundation, plumbing, electrical — the OS). A container is a **lockable apartment in a shared building** (its own rooms and door, but sharing the building's foundation — the host kernel). Apartments are cheaper, faster to build, and you fit many in one building — at the cost of sharing some infrastructure.

Two terms students must not confuse:

- **Image** = the immutable *blueprint* — a packaged filesystem + metadata. Built once, stored in a registry.
- **Container** = a *running instance* of an image. You can start many containers from one image (exactly how we'll run 3 LMS replicas in Step 21).

> *Image is to container as class is to object* — a comparison your DDD students will appreciate.

---

## 16.2 Images are built in layers (and why you'll care)

A Docker image is a stack of read-only **layers**, each produced by an instruction in the Dockerfile. Layers are **cached and reused**: if an instruction and everything before it are unchanged, Docker reuses the cached layer instead of re-running it. This single fact dictates how you *order* a Dockerfile — put rarely-changing things early, frequently-changing things late, so most builds reuse most layers.

We'll exploit this below by copying `requirements.txt` (changes rarely) and installing deps *before* copying the source (changes constantly) — so editing a Python file doesn't reinstall every dependency.

---

## 16.3 The LMS Dockerfile (multi-stage, slim, non-root)

```dockerfile
# syntax=docker/dockerfile:1

# ---- Stage 1: builder — install dependencies (with build tools) ----
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .                                   # copied FIRST → cached layer
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

# ---- Stage 2: runtime — only what's needed to RUN ----
FROM python:3.12-slim
# security: create and run as a non-root user
RUN useradd --create-home --uid 1000 appuser
WORKDIR /app
COPY --from=builder /install /usr/local                   # bring in installed deps only
COPY src/ ./src/                                          # app code copied LATE (changes often)
USER appuser                                              # drop root
EXPOSE 8000                                               # documents the port
# production server (Step 14), not the dev server
CMD ["gunicorn", "src.api.main:app", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "-w", "4", "-b", "0.0.0.0:8000"]
```

Walk through *why* each decision was made:

- **Multi-stage build** — Stage 1 has compilers and build tools to install dependencies; the final image copies *only the installed packages*, not the build toolchain. Result: a **smaller, lower-attack-surface** runtime image.
- **`python:3.12-slim` base** — a trimmed Debian image. (For maximum minimalism, **`distroless`** or `alpine` go smaller — with trade-offs around glibc/debugging.) Smaller base = faster pulls, fewer CVEs.
- **`COPY requirements.txt` before `COPY src/`** — the layer-caching lesson from §16.2. Editing a `.py` file rebuilds only the last cheap layer, not the whole dependency install. Builds go from minutes to seconds.
- **Non-root `USER appuser`** — if the app is compromised, the attacker isn't root inside the container. A baseline security control (Step 26 goes deeper).
- **`EXPOSE 8000`** — documentation of the port the app binds (the port-binding factor from Step 14).
- **`CMD` with the production server** — Gunicorn + Uvicorn workers, exactly as Step 14 specified.

### `CMD` vs `ENTRYPOINT` (a common exam question)

- **`CMD`** sets the *default* command, easily overridden at `docker run`.
- **`ENTRYPOINT`** sets a command that always runs, with `CMD` as its default *arguments*.

For a single-purpose web app, a plain `CMD` (as above) is fine and flexible. Use `ENTRYPOINT` when the container *is* one fixed executable and you only ever vary its arguments.

---

## 16.4 `.dockerignore` — small images, no leaked secrets

The **build context** (everything sent to the builder) should exclude junk and — critically — secrets. Without this, your `.env` or `.git` could end up *inside* the image.

```dockerignore
# .dockerignore
.git
.venv
__pycache__
*.pyc
.env                # ← never bake secrets into an image
.pytest_cache
docs/
tests/
*.md
```

> ⚠️ A `.env` copied into an image is a credential leak that ships to every environment and registry. `.dockerignore` it on day one — and remember the image is *inspectable* by anyone who can pull it.

---

## 16.5 Build it, run it, prove it

```bash
# build — tag with the git SHA (the immutable tag philosophy, fully covered in Step 17)
docker build -t lms:$(git rev-parse --short HEAD) -t lms:dev .

# run — inject config via env (Step 14); map the port
docker run --rm -p 8000:8000 \
  -e DATABASE_URL="postgresql://lms:secret@host.docker.internal:5432/lms" \
  -e LOG_LEVEL=INFO \
  lms:dev

# prove it's healthy
curl localhost:8000/healthz     # {"status":"ok"}
curl localhost:8000/readyz      # {"status":"ready"}  (if the DB is reachable)
```

The same image, given different `DATABASE_URL`s, runs against dev SQLite or prod Postgres — **build once, deploy many**, made tangible. Nothing about the image changes between environments; only the injected config does.

### An optional in-image healthcheck

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')"
```

(In Kubernetes we use the *platform's* probes instead — Step 21 — but this is handy for plain Docker/Compose from Step 15.)

---

## 16.6 Image best practices (the checklist)

- [ ] **Small base** (`slim`/`distroless`) — faster pulls, fewer vulnerabilities
- [ ] **Multi-stage** — drop build tools from the runtime image
- [ ] **Non-root user** — never run as root
- [ ] **`.dockerignore`** — no secrets, no junk in the context/image
- [ ] **Order layers cache-friendly** — deps before code
- [ ] **Pin the base image** (ideally by digest: `python:3.12-slim@sha256:…`) for reproducibility
- [ ] **One concern per image** — the API is one image; a worker would be another
- [ ] **No secrets baked in** — config arrives at runtime via env
- [ ] **Scan the image** for CVEs (Trivy) — wired into CI in Step 19
- [ ] **Tag immutably** by commit SHA — Step 17

---

## Promises served

| Promise | How this chapter advanced it |
|---|---|
| **Correct** | One immutable image runs identically everywhere — the literal embodiment of "build once, deploy many." |
| **Survives failure** | A fast, lightweight image starts in seconds, so the orchestrator can recover/scale it quickly (Step 21). |
| **Secure** | Non-root user, minimal base, no secrets baked in, `.dockerignore`, image scanning — attack surface minimized. |
| **Available** | Many containers from one image → the basis for running redundant replicas behind a load balancer. |

## Key takeaways (the transferable lessons)

1. **A container shares the host kernel** (unlike a VM) — that's why it's small and fast. *Image = blueprint; container = running instance* (class vs object).
2. **Images are cached layers** — order the Dockerfile so rarely-changing steps (deps) come before frequently-changing ones (code). It turns minute-long builds into seconds.
3. **Multi-stage + slim base + non-root** is the baseline professional Dockerfile — smaller, faster, safer.
4. **Never bake secrets or junk into the image** — `.dockerignore` and runtime env injection keep the artifact clean and portable.
5. **The image is the immutable artifact** the entire pipeline revolves around — build it once, and prove the same image runs anywhere by varying only injected config.

---

*Next — Step 17: Registry & immutable tagging. The image we just built needs a home and a name. We'll push it to a container registry, and dig into why production must deploy a commit-SHA-pinned tag (never `:latest`) — making every running container traceable to the exact commit that produced it.*
