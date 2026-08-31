# Step 17 — Registry & Immutable Tagging

*Series: Designing a Library Management System with DDD · Chapter 17 — Part II*

---

The image from Step 16 lives on your laptop. To deploy it anywhere — CI, staging, Kubernetes — it needs **a home and a name**. That home is a **container registry**, and how you *name* (tag) images is the difference between a traceable, reproducible system and a mystery. This is a short chapter with one big discipline: **never deploy `:latest`.**

---

## 17.1 What a registry is

A **container registry** is a versioned artifact store for images — `git` for built images, essentially. It's where the "build once" artifact (Step 13) lives so that "deploy many" can pull it.

```
   docker build  →  docker push  →  [REGISTRY]  →  docker pull  →  run anywhere
                                   (the single source
                                    of truth for artifacts)
```

The common ones:

| Registry | Notes |
|---|---|
| **Docker Hub** | The default public registry; free public repos, rate-limited pulls. |
| **GitHub Container Registry (GHCR)** | `ghcr.io`; integrates with GitHub Actions — our choice for the LMS. |
| **AWS ECR / GCP Artifact Registry / Azure ACR** | Cloud-native, private, IAM-integrated; what you use in that cloud. |
| **Self-hosted (Harbor)** | On-prem, with built-in scanning & signing. |

**Public vs private:** public repos are pullable by anyone (fine for open source); production app images live in **private** registries gated by credentials/IAM.

---

## 17.2 Anatomy of an image name

```
   ghcr.io / your-org / lms : sha-9f8c2a1
   └──┬───┘ └───┬────┘ └┬─┘   └────┬─────┘
   registry  namespace  repo      tag
```

And the part that matters most for correctness — the **digest**:

```
   ghcr.io/your-org/lms@sha256:3b1f...e9   ← content-addressed, TRULY immutable
```

- A **tag** (`:sha-9f8c2a1`, `:1.4.2`) is a *human-friendly pointer* — and a pointer **can be moved** to a different image later.
- A **digest** (`@sha256:…`) is a cryptographic hash of the image *content* — it can **never** point to anything else. Same digest = byte-for-byte the same image, guaranteed.

> **The key realization:** *tags are mutable labels; digests are immutable identities.* Production-grade systems pin deployments to **digests** (or treat SHA tags as if immutable) so "what's running" is provable.

---

## 17.3 Pushing the LMS image

```bash
# authenticate (a token, not your password)
echo $GITHUB_TOKEN | docker login ghcr.io -u your-username --password-stdin

# tag the local image for the registry, using the git commit SHA
docker tag lms:dev ghcr.io/your-org/lms:sha-$(git rev-parse --short HEAD)

# push
docker push ghcr.io/your-org/lms:sha-9f8c2a1
```

In practice you don't do this by hand — **CI does it on every merge** (Step 19). The manual commands are just to show the mechanics.

---

## 17.4 The tagging discipline (the heart of this chapter)

### ❌ Why `:latest` is a production trap

`:latest` is just a tag that conventionally points at "the most recent push" — but it's a **moving target**:

- Two servers pulling `lms:latest` an hour apart can get **different images**. So much for "build once, deploy many."
- You **can't tell what's actually running** — "latest" today ≠ "latest" last week. Debugging a prod incident becomes archaeology.
- **Rollback is undefined** — roll back to *which* `latest`?
- Kubernetes may or may not re-pull it depending on `imagePullPolicy`, giving you *inconsistent* fleets.

> **Rule: never deploy `:latest` to production.** It's fine for local scratch work; it's poison for reproducibility.

### ✅ Tag by commit SHA (the workhorse)

```
ghcr.io/your-org/lms:sha-9f8c2a1
```

Every image is tagged with the **git commit** that built it. Now any running container is traceable to the *exact* source — `git checkout 9f8c2a1` shows you precisely what's live. This is the single most useful tag in a CI/CD pipeline.

### ✅ Semantic version tags (for humans & releases)

```
ghcr.io/your-org/lms:1.4.2     # MAJOR.MINOR.PATCH for releases/changelogs
```

SHA tags are for *machines and traceability*; semver tags are for *humans and release communication*. You can apply both to the same image.

### Environment tags are *pointers*, not builds

A useful pattern: `:staging` and `:prod` are **moving pointers** that you *retag onto an existing SHA image* to record "what's deployed where" — you never *build* a separate prod image. This is **promotion**:

```bash
# promote the EXACT image that passed staging to production — same content, new pointer
docker buildx imagetools create \
  --tag ghcr.io/your-org/lms:prod \
  ghcr.io/your-org/lms:sha-9f8c2a1        # re-points, copies no bytes (same digest)
```

> **This is "build once, deploy many" enforced at the registry:** the bytes that ran in staging are *identical* to the bytes promoted to prod — you only moved a label. No rebuild, no drift.

---

## 17.5 Registry mechanics worth knowing

- **Layer dedup:** images share layers; pushing a new LMS image only uploads the *changed* layers (usually just your code layer), not the whole Python base. Pulls are fast for the same reason.
- **Retention / garbage collection:** registries fill up. Set policies to prune old untagged images (but **keep enough history to roll back**).
- **Scanning at rest:** most registries can scan stored images for new CVEs continuously (a vuln disclosed *after* you pushed still gets flagged). Pairs with the build-time scan in Step 19.
- **Signing (preview):** you can cryptographically **sign** images (cosign/Sigstore) and have the cluster *verify* signatures at deploy, so only trusted images run (Step 26).
- **Pull secrets:** Kubernetes needs registry credentials (an `imagePullSecret`) to pull from a private registry (Step 21).

---

## Promises served

| Promise | How this chapter advanced it |
|---|---|
| **Correct** | SHA/digest tags make "what's running" provable and traceable to a commit — the enforcement point of "build once, deploy many." |
| **Survives change** | Immutable tags make rollback well-defined: redeploy a previous SHA. `:latest` makes rollback meaningless. |
| **Secure** | Private registries + scanning-at-rest + (later) signature verification gate what can run. |
| **Available** | Layer dedup → fast pulls → fast scale-up and recovery. |

## Key takeaways (the transferable lessons)

1. **A registry is `git` for images** — the artifact store where "build once" lives so "deploy many" can pull.
2. **Tags are mutable pointers; digests are immutable identities.** Pin production to a SHA tag or digest so what's running is provable.
3. **Never deploy `:latest`.** It's a moving target that destroys reproducibility, traceability, and rollback.
4. **Tag by commit SHA** for traceability (machines) and **semver** for releases (humans) — both on the same image.
5. **Promotion = retagging the same image**, not rebuilding. Moving a `:staging` → `:prod` pointer onto an existing digest is "build once, deploy many" enforced at the registry.

---

*Next — Step 18: Database & migrations. The app is stateless and packaged, but the database is not — and it's where most production incidents happen. We'll cover schema migrations (Alembic), the backwards-compatible expand/contract pattern that makes zero-downtime deploys safe, and why migrations run as a separate step, not at app startup.*
