# Part II — BUILD: from source to an immutable image

*Library Management System · Part II, stage 2 of six (CODE → **BUILD** → TEST → PACKAGE → DEPLOY
→ OBSERVE). Part I built the app; here we turn that source into something deployable.*

---

BUILD has two halves that get conflated. First, **is the app even buildable/deployable?** — the
12-factor readiness work that must be true *in the code* before any pipeline can help. Second, the
**mechanical build** — CI resolves dependencies and assembles, then packages the result as one
SHA-tagged container image. Skip the first half and you get an app that "builds" but can't survive
a scheduler killing it, a config change, or a second replica. So we do readiness first.

---

## 1. App-readiness first — the 12-factor essentials

A pipeline can't *make* an app cloud-ready; the app has to already obey a handful of contracts.
These are the ones that matter for a service like the LMS. **The LMS already does all of these** —
that's the point of Part I ending where it did.

| Contract | What it means | LMS reality |
|---|---|---|
| **Config from env** (12-factor III) | No hostnames, secrets, or tunables baked into code | `config.py` reads `DATABASE_URL`, `LOG_LEVEL`, `FINE_RATE_PAISE`, `MAX_ACTIVE_LOANS` from env |
| **Stateless processes** | A process keeps nothing durable in memory or local disk | Loans/fines live in the DB, not process memory — any replica serves any request |
| **Logs to stdout** | The app never manages log files | `logging_setup.py` emits structured JSON to stdout; the platform captures it |
| **Health probes** | The platform can ask "alive?" and "ready?" | `/healthz` (liveness) + `/readyz` (readiness, checks DB reachability) |
| **Port binding** | The app *is* the server; it binds a port | gunicorn + uvicorn workers bind `0.0.0.0:$PORT` |
| **Graceful shutdown** | On `SIGTERM`, stop taking work, drain in-flight, exit | gunicorn traps `SIGTERM`, stops accepting, lets workers finish, then exits |
| **Pinned deps** | Byte-identical dependency tree every build | fully pinned `requirements.txt` (== versions, ideally hashes) |

**Why statelessness is the master key.** Every other scaling and resilience move — run N replicas,
kill and reschedule a pod, roll out a new version one instance at a time, autoscale on load —
*depends on any request being serviceable by any process*. The moment a server holds session state
or an in-memory cache that clients rely on, you can't add a second replica without sticky routing,
and you can't kill a pod without losing data. State goes to the DB (or Redis); the app processes
stay disposable.

🎯 **Interview flag — "config from env" and "statelessness."** Two of the most reliably asked
production-readiness questions. Config-from-env (12-factor III) is *why the same image runs in dev,
staging, and prod* — only the injected env differs, which is what makes "build once, deploy many"
possible. Statelessness is *why horizontal scaling works at all*. If you can articulate that chain
— env config → one immutable image → stateless replicas → horizontal scale — you've answered half
the "how would you deploy this?" question before it's finished.

> **What to opt for:** treat these seven as **non-negotiable entry criteria** for the build stage.
> They're cheap in Python/FastAPI and impossible to retrofit cleanly under load. A service that
> isn't stateless and config-driven isn't "not yet optimized" — it's not deployable.

**Graceful shutdown, concretely.** When Kubernetes (or ECS) rolls out a new version, it sends
`SIGTERM` and waits `terminationGracePeriodSeconds` before `SIGKILL`. gunicorn's default `SIGTERM`
handling is exactly right: stop accepting new connections, let in-flight requests on the uvicorn
workers finish, then exit 0. That's what turns a rollout into a *zero-downtime* rollout — a request
mid-flight when a pod is replaced doesn't get dropped.

---

## 2. The CI build — resolve deps + assemble

The mechanical job: check out the commit, install the pinned dependencies into a clean
environment, and produce the artifacts the later stages consume. For an interpreted stack like
Python there's no compile step, so "build" here means **dependency resolution + environment
assembly**, then handing off to the image build (§3).

| CI engine | Best fit | Note |
|---|---|---|
| **GitHub Actions** | Repo already on GitHub; small–mid teams | Managed runners, huge action ecosystem; default choice for the LMS |
| **GitLab CI** | GitLab-hosted; integrated registry | `.gitlab-ci.yml`, built-in container registry |
| **Jenkins** | Legacy / heavily customized on-prem | Maximum flexibility, maximum maintenance |
| **Bazel** | Monorepo at scale; polyglot; needs hermetic, cached, incremental builds | Overkill for one service — earns its place across hundreds |

For the LMS — one FastAPI service — a managed CI (GitHub Actions) resolving `requirements.txt` and
driving a Docker build is the whole story. **Bazel is the wrong tool here**; it pays off only when
a monorepo's build graph makes incremental, hermetic, cache-shared builds worth the setup cost.

> **What to opt for:** **managed CI (GitHub Actions) by default.** Reach for Jenkins only when
> you're already invested in it, and for Bazel only at monorepo scale where hermeticity and
> build-graph caching actually pay back.

---

## 3. The image build — multi-stage, non-root, small

The output of BUILD is **one immutable artifact**: a container image tagged `lms:sha-<gitsha>`.
The tag is the git SHA so the running image traces back to an exact commit — no `:latest`
ambiguity. The image is built **multi-stage** so the shipped layer carries the app and its runtime
deps, and *nothing else* — no compiler, no pip cache, no build tooling.

```dockerfile
# ---- builder stage: has pip + build tooling ----
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
# install into an isolated prefix we can copy out
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- runtime stage: slim, no build tooling ----
FROM python:3.12-slim AS runtime
# create + use a non-root user
RUN useradd --create-home --uid 10001 appuser
WORKDIR /app
COPY --from=builder /install /usr/local
COPY src/ ./src/
USER appuser                     # never run as root
ENV PORT=8000
EXPOSE 8000
# gunicorn manages uvicorn workers; binds 0.0.0.0:$PORT
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", "api.main:app"]
```

**Why multi-stage matters** (three payoffs at once):

- **Smaller** — the builder stage's compilers, headers, and pip cache never reach the final image.
  Less to pull, faster to start, cheaper to store.
- **More secure** — a smaller image is a smaller attack surface. No compiler or package manager in
  the runtime layer means fewer CVEs and fewer tools for an attacker to pivot with. **distroless**
  goes further: no shell, no package manager at all.
- **Reproducible** — pinned `requirements.txt` + a pinned base tag (ideally a digest) makes the
  build deterministic: same source → same image.

**Non-root `USER`** is the other must. A container that runs as root and gets compromised gives an
attacker root inside the namespace and a head start on escaping it. Run as an unprivileged UID;
pair it with a read-only root filesystem at deploy time.

🎯 **Interview flag — "why multi-stage builds?"** The clean answer is the three payoffs above:
**small, secure, reproducible.** A strong follow-up: *slim vs distroless* — slim keeps a shell
(easier to debug, e.g. `kubectl exec` + `sh`); distroless drops it (smaller, safer, but you debug
via ephemeral containers). Knowing the trade-off, not just the buzzword, is what's being tested.

**Where the image actually gets built** — three real options:

| Build engine | Where it runs | Why pick it |
|---|---|---|
| **Docker / BuildKit** | On the CI runner | Default; fast, great caching (`buildx`). Needs access to a Docker daemon |
| **Kaniko** | **Inside the cluster**, rootless | Builds images with **no Docker daemon** — safe in a K8s pod where mounting the host socket is a no-go |
| **AWS CodeBuild** | AWS-managed build service | AWS-native; integrates with ECR, CodePipeline, IAM out of the box |

Kaniko exists because the "obvious" way to build in-cluster — mounting the host's Docker socket
into a build pod — hands that pod effective root on the node. Kaniko builds from a Dockerfile
**without a daemon and without privilege**, which is exactly what you want when the build itself
runs as a Kubernetes workload (e.g. under Tekton or Argo Workflows).

---

## 4. The two-cloud lens — BUILD

| Concern | Private cloud (Kubernetes) | Public cloud (AWS) |
|---|---|---|
| **CI engine** | Tekton / Argo Workflows (in-cluster), or GitHub Actions | CodeBuild (+ CodePipeline) |
| **Image build** | **Kaniko** (rootless, in-cluster) or BuildKit on a runner | CodeBuild, or `docker buildx` |
| **Base image** | distroless / `-slim` | distroless / `-slim` — **same** |
| **Build cache** | Registry-backed layer cache (BuildKit `--cache-to/from`); Bazel remote cache at scale | CodeBuild local/S3 cache; ECR layer reuse |
| **Output tag** | `lms:sha-<gitsha>` → Harbor / self-hosted registry | `lms:sha-<gitsha>` → Amazon ECR |

The decision that actually splits the two columns is **where the build runs and whether it needs a
Docker daemon.** In-cluster on K8s → Kaniko (rootless, daemonless). AWS-native → CodeBuild. On a
plain CI runner either way → BuildKit. The *base image* and the *tagging scheme* are identical
across both — the artifact is portable; only the machinery that stamps it differs.

> **What to opt for:** **always** multi-stage + distroless/slim + non-root + pinned deps —
> non-negotiable regardless of cloud. For the engine: **managed CI (GitHub Actions)** by default;
> **Kaniko** when the build must run *inside* the cluster (no daemon, no privilege); **CodeBuild**
> when you're AWS-native and want first-class ECR/IAM/CodePipeline integration. The immutable
> `lms:sha-<gitsha>` image is the same either way — that's what lets it travel every later stage
> unchanged.

---

## Key takeaways

1. **Readiness precedes the pipeline.** Config-from-env, stateless processes, logs to stdout,
   health probes, port binding, graceful `SIGTERM`, pinned deps — true *in the code* first. The
   LMS already satisfies all seven.
2. **Statelessness is the master key** — it's the precondition for replicas, rescheduling, rolling
   updates, and autoscaling. State lives in the DB, not the process.
3. **CI = resolve deps + assemble.** Managed CI (GitHub Actions) by default; Bazel only at monorepo
   scale.
4. **The artifact is one multi-stage, non-root, SHA-tagged image** — small, secure, reproducible.
   Build it once as `lms:sha-<gitsha>` and never rebuild per environment.
5. **Cloud changes the machinery, not the artifact** — Kaniko/BuildKit in-cluster vs CodeBuild on
   AWS, but the same distroless/slim, non-root image travels both paths.

---

*Next — `part2-03-test`: the TEST stage — the test pyramid and the security/quality scans that gate
a merge before the image is allowed to ship.*
