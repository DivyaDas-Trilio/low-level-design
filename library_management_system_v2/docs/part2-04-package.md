# Part II — PACKAGE: the immutable artifact, the registry, and the supply chain

*Library Management System · Part II, stage 4 of 6. TEST gated the merge; PACKAGE freezes what
passed into one shippable thing and puts it somewhere trustworthy.*

---

BUILD produced an image and TEST let it through the gates. PACKAGE answers: **what exactly do we
ship, where does it live, and how do we prove it wasn't tampered with?** The answer is one
**versioned, immutable, SHA-tagged container image** in a registry that sits next to the runtime,
signed and scanned on the way in. Everything downstream — every environment, every rollback —
points at *that* artifact by digest. Get this stage right and "build once, deploy many" stops
being a slogan and becomes a guarantee.

---

## 1. The immutable artifact — one thing, frozen

The unit of shipping for the LMS is **one container image**, built once, tagged by the git commit
that produced it:

```
lms:sha-abc123        # abc123 = the exact commit; this tag never moves, never gets rebuilt
```

**Immutable** means: once `sha-abc123` is pushed, that tag *never* points at different bytes.
Rebuilding the same source could pull newer base-image layers or transitive deps and quietly
produce a *different* image — so we don't rebuild. The image that passed TEST **is** the image
that reaches prod, byte-for-byte.

**Why immutability makes "build once, deploy many" trustworthy.** The whole promise —
*the tested image is the shipped image* — collapses the moment any environment can rebuild or
overwrite. Immutability is the enforcement mechanism: dev, staging, and prod all pull the same
`sha-abc123`; only **config** (env vars, secrets) differs. That is what kills *"but it worked in
staging."*

> 🎯 **Interview flag — immutable artifacts / "build once, deploy many."** High-signal. Be ready
> to say *why*: reproducible deploys, trivial rollback (just re-point at the previous SHA),
> byte-identical staging↔prod, and a clean audit trail (tag = commit = what's running).

**Never `latest` in prod.** `latest` is a *mutable* tag — it silently moves to whatever was pushed
most recently, so two clusters pulling `latest` an hour apart can run different code. You lose
reproducibility, rollback ("roll back to *which* `latest`?"), and audit. Pin to the **digest**
(`lms@sha256:…`) or the immutable SHA tag; treat `latest` as a dev convenience only.

| Tag style | Mutable? | Use in prod? | Why |
|---|---|---|---|
| `latest` | yes | **never** | moves under you; unreproducible |
| `v1.4` (semver) | often re-pushed | release naming only | human-friendly, but can be overwritten |
| `sha-abc123` | **no** (with tag immutability on) | **yes** | 1:1 with a commit; audit + rollback |
| `@sha256:…` (digest) | no (content-addressed) | **strongest** | pins exact bytes regardless of tag |

---

## 2. The registry — where the artifact lives

The image needs a home: an OCI **container registry**. Two rules decide *which* one:

1. **Put the registry next to the runtime.** Pulls should be same-region, same-network — fast,
   cheap, and not dependent on an external hop during a deploy or a node scale-up.
2. **One source of truth** that CI pushes to and every environment pulls from.

| Runtime | Registry to reach for | Why |
|---|---|---|
| Self-managed **Kubernetes** (on-prem/private) | **Harbor** (self-hosted) | runs in your cluster/DC; built-in scanning, RBAC, signing, replication |
| **EKS / ECS / Lambda** (AWS) | **Amazon ECR** | same account/region as the runtime; IAM-native auth |
| **GKE / generic** | Artifact Registry / GHCR | co-located with GCP; GHCR handy when CI is GitHub Actions |

For the LMS: on the private-K8s path the image lands in **Harbor**; on AWS it lands in **ECR**.
Same `sha-abc123` tag either way — the registry changes, the artifact identity does not.

> **What to opt for:** **registry next to the runtime** — ECR for EKS/ECS, Harbor for on-prem
> K8s, GHCR/Artifact Registry when they're the co-located choice. Don't pull prod images across
> the public internet from an unrelated registry.

---

## 3. Supply-chain security — prove the artifact is trustworthy

The registry is also the **supply-chain checkpoint**. An unsigned, unscanned image is an unknown;
four controls turn it into a known-good artifact. These are non-negotiable on the push path.

**(a) Sign it — cosign / Sigstore.** After push, sign the image so downstream can verify *origin
and integrity*: this artifact came from our pipeline and hasn't been altered.

```
cosign sign  lms@sha256:…      # signature stored alongside the image
cosign verify lms@sha256:…     # admission control / deploy step verifies before running
```

Kubernetes can **enforce** this with a policy controller (Kyverno / Sigstore policy-controller)
that refuses to run unsigned images; keyless signing (Sigstore OIDC) avoids managing private keys.

**(b) Describe it — SBOM (syft).** Generate a **Software Bill of Materials** — the full inventory
of packages and versions in the image — and attach it as an attestation. When the next Log4Shell
drops, the SBOM answers *"are we affected, and where?"* in seconds instead of a frantic audit.

```
syft lms@sha256:… -o spdx-json > sbom.json
cosign attest --predicate sbom.json lms@sha256:…
```

**(c) Scan on push — Trivy / ECR scan / Inspector.** Scan the image for known CVEs **at the
registry boundary**, not just in CI. Harbor runs **Trivy** on push and can block the pull; **ECR
enhanced scanning** (backed by **Amazon Inspector**) scans continuously — so a CVE disclosed
*after* push still surfaces on an already-stored image.

**(d) Lock it down — tag immutability + pull auth.**
- **Tag immutability** (a registry setting in both Harbor and ECR): once `sha-abc123` exists, it
  **cannot be overwritten**. This is what makes rule 1 (immutable artifact) *enforced*, not merely
  a convention.
- **Pull auth without static creds:** on K8s use **`imagePullSecrets`** (short-lived / rotated,
  or a credential-helper); on AWS, the node/pod **IAM role → ECR** grants pull rights natively —
  **no long-lived credentials baked into manifests or images.**

> 🎯 **Interview flag — software supply-chain security.** Signing (cosign/Sigstore), SBOM (syft),
> and scan-on-push (Trivy/Inspector) are exactly what interviewers probe post-SolarWinds/Log4Shell.
> Frame it as **provenance + inventory + vulnerability gating**, and mention *tag immutability* and
> *no static pull creds* as the enforcement that makes the rest real.

---

## 4. Private cloud (K8s) vs public cloud (AWS)

| Concern | Private cloud (Kubernetes) | Public cloud (AWS) |
|---|---|---|
| **Registry** | Harbor / self-hosted | Amazon ECR |
| **Tagging** | immutable git-SHA (`lms:sha-abc123`) | immutable git-SHA (`lms:sha-abc123`) — **same** |
| **Signing** | cosign / Sigstore | cosign / Sigstore — **same** |
| **Vuln scan** | Trivy (in Harbor, scan-on-push) | ECR enhanced scanning / Amazon Inspector |
| **SBOM** | syft → cosign attestation | syft → cosign attestation (or ECR-native) — **same** |
| **Tag immutability** | Harbor repo setting | ECR "immutable tags" setting |
| **Pull auth** | `imagePullSecrets` (rotated) | IAM role → ECR (no static creds) |
| **Enforcement** | Kyverno / policy-controller blocks unsigned/unscanned | ECR pull-through + admission on EKS |

**Read the columns, not the cells.** The *artifact* and the *supply-chain discipline* (SHA tag,
cosign, SBOM, scan-on-push, tag immutability) are **identical across clouds** — that's the point of
a portable OCI image. Only the **hosting and auth plumbing** (Harbor vs ECR, `imagePullSecrets` vs
IAM) is cloud-specific.

> **What to opt for:**
> - **Registry next to the runtime** — ECR for EKS/ECS, Harbor on-prem.
> - **Always** immutable SHA tags + **sign** + **scan-on-push** — on every image, no exceptions.
> - **Enable tag immutability** in the registry so the convention is enforced by the platform.
> - **Block the deploy** of any image that is unsigned, unscanned, or over your CVE threshold —
>   the gate belongs at the registry/admission boundary, not in a human's memory.
> - **No static credentials** — IAM roles on AWS, rotated `imagePullSecrets` on K8s.

---

## Key takeaways

1. **Ship one immutable, SHA-tagged image** (`lms:sha-abc123`); the tested image *is* the shipped
   image. **Never `latest` in prod** — pin the SHA or the digest.
2. **Immutability is what makes "build once, deploy many" trustworthy** — same bytes dev→staging→
   prod, only config differs; rollback is just re-pointing at a prior SHA.
3. **Put the registry next to the runtime** — Harbor on-prem, ECR on AWS — same artifact identity
   either way.
4. **Secure the supply chain on the push path:** cosign/Sigstore signing (provenance), syft SBOM
   (inventory), Trivy/Inspector scan-on-push (vulnerabilities), plus tag immutability and no static
   pull creds.
5. **Enforce, don't trust:** block deploys of unsigned/unscanned/vulnerable images at the
   registry/admission boundary. The discipline is identical across clouds; only the plumbing differs.

---

*Next — `part2-05-deploy`: the DEPLOY stage — how the frozen artifact reaches running
infrastructure (push vs GitOps), the runtime (K8s / ECS / Lambda), environments, and the database.*
