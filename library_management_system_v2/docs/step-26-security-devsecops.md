# Step 26 — Security Across the Pipeline (DevSecOps)

*Series: Designing a Library Management System with DDD · Chapter 26 — Part II*

---

The most common security mistake isn't a missing firewall — it's treating security as a **final gate** ("we'll do a pentest before launch") instead of a thread woven through *every* stage. **DevSecOps** means each step we've built — code, image, registry, deploy, runtime, edge — has its own security control, so a failure at one layer is caught by another.

> **Two principles run through this whole chapter:**
> **(1) Shift left** — catch issues as early (and cheap) as possible; a vulnerable dependency caught in CI costs minutes, the same one caught in production costs an incident.
> **(2) Defense in depth** — assume any single control will fail, and layer them so the next one still protects you.

We'll walk the pipeline stage by stage; each stage gets a control.

---

## 26.1 The layered view (the map)

```
 CODE/DEPS ─► IMAGE ─► SUPPLY CHAIN ─► SECRETS ─► RUNTIME/CLUSTER ─► EDGE ─► DATA
   SAST,      scan,     SBOM,           manager,   RBAC, NetworkPol,  TLS,    encrypt
   dep-scan   non-root  sign+verify     rotation   PodSecurity        authz   at rest
```

| Stage | Threat it addresses | Control |
|---|---|---|
| Code & deps | Vulnerable code / libraries | SAST, dependency scanning |
| Image | Vulnerable OS packages, root | CVE scan, minimal + non-root + read-only |
| Supply chain | Tampered/unknown artifacts | SBOM, signing, signature verification |
| Secrets | Leaked credentials | Secret manager, rotation, no secrets in git/image |
| Runtime/cluster | Lateral movement, privilege escalation | RBAC, NetworkPolicy, Pod Security |
| Edge | Unauthorized access, abuse | TLS, authn/authz, rate limiting, WAF |
| Data | Breach, PII exposure | Encryption at rest, masking, encrypted backups |

---

## 26.2 Code & dependencies (shift furthest left)

Most of your code *is* other people's code (dependencies). Two automated controls, on every PR (Step 19):

- **Dependency scanning** — flag known-vulnerable libraries. **Dependabot** opens PRs to bump them; **`pip-audit`** fails CI on a known CVE in `requirements.txt`.
- **SAST** (Static Application Security Testing) — scan *your* code for risky patterns (injection, hardcoded secrets). Tools: `bandit` (Python), Semgrep, CodeQL.

```yaml
# add to the CI from Step 19
- run: pip-audit -r requirements.txt        # fail on a vulnerable dependency
- run: bandit -r src/                         # static security scan of our code
```

> Bonus: a **secret scanner** (gitleaks, GitHub secret scanning) in CI catches an accidentally-committed password *before* it merges — the single most common real-world leak.

---

## 26.3 Image security (Step 16, hardened)

The Dockerfile choices from Step 16 were security choices:

- **Minimal base** (`slim`/distroless) → fewer packages → fewer CVEs.
- **Non-root user** → a compromised app isn't root in the container.
- **Scan the image** for CVEs in CI (**Trivy**, from Step 19) and **continuously at rest** in the registry (Step 17) — a CVE disclosed *after* you shipped still gets flagged.

Tighten further at runtime via the pod spec:

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  readOnlyRootFilesystem: true        # app can't write to its own filesystem
  allowPrivilegeEscalation: false
  capabilities: { drop: ["ALL"] }      # drop all Linux capabilities
```

---

## 26.4 Supply-chain security (the modern frontier)

After incidents like SolarWinds and Log4Shell, *"is this artifact what I think it is, and where did it come from?"* became central. Three controls:

- **SBOM** (Software Bill of Materials) — a manifest of *everything* in your image. When the next Log4Shell drops, you can answer "are we affected?" in seconds by querying SBOMs instead of guessing.
- **Signing** — cryptographically **sign** images (**cosign**/Sigstore) at build, and **verify the signature at deploy** via an admission controller, so the cluster runs **only images your pipeline produced** — a swapped/tampered image is rejected.
- **Provenance (SLSA)** — attest *how/where* the artifact was built (which commit, which CI run), making the build chain auditable.

```bash
cosign sign   ghcr.io/your-org/lms:sha-9f8c2a1         # in CI, after build
cosign verify ghcr.io/your-org/lms:sha-9f8c2a1         # admission controller, at deploy
```

---

## 26.5 Secrets management

The rule from Step 14, now with the machinery:

- **Never** in code, image, or git. (Secret scanning in CI enforces this.)
- Stored in a **secret manager** — HashiCorp **Vault**, AWS/GCP secret managers, or Kubernetes Secrets (encrypt etcd at rest!).
- **For GitOps** (Step 20), where everything is in git: **Sealed Secrets** (encrypt so only the cluster can decrypt — safe to commit) or the **External Secrets Operator** (git holds a *reference*; the value is pulled from Vault at apply time).
- **Rotation** — secrets have a lifecycle; rotate regularly and on any suspected exposure.
- **Least privilege** — each component reads only the secrets it needs; the LMS app sees `DATABASE_URL`, nothing else.

---

## 26.6 Runtime & cluster security (limit the blast radius)

Assume a pod *will* be compromised — and contain it:

- **RBAC (least privilege)** — the LMS service account can do the minimum (it probably needs *no* Kubernetes API access at all). Don't hand pods cluster-admin "to make it work."
- **NetworkPolicies (zero-trust networking)** — by default, deny all; then allow only what's needed. The LMS pod may talk to **Postgres and the ingress** and *nothing else* — so a compromised pod can't pivot to other services.

  ```yaml
  # default-deny + allow only LMS → Postgres
  kind: NetworkPolicy
  spec:
    podSelector: { matchLabels: { app: lms } }
    policyTypes: [Egress]
    egress:
      - to: [{ podSelector: { matchLabels: { app: postgres } } }]
        ports: [{ port: 5432 }]
  ```

- **Pod Security Standards** — enforce `restricted` (no privileged containers, non-root, no host mounts) cluster-wide.
- **Admission control** — **OPA Gatekeeper / Kyverno** reject non-compliant workloads at deploy ("no image without a signature," "no container as root," "must set resource limits"). Policy as code.

---

## 26.7 Edge security (the front door)

Where users (and attackers) meet the system:

- **TLS everywhere** (Step 24) — encrypted in transit, auto-renewed.
- **Authentication & authorization** — this is where Step 11's **actors → roles** (Member/Librarian/Admin) become real access control: verify *who* (tokens/OIDC) and enforce *what they may do* at the API. (Rule #6's visibility filter lives here too.)
- **Rate limiting** — at the ingress, to blunt brute-force and abuse (a member can't hammer the borrow endpoint 10k times/sec).
- **WAF** (Web Application Firewall) — filters common attacks (injection, bad bots) before they reach the app.

---

## 26.8 Data security

- **Encryption at rest** — the database and backups are encrypted on disk (member emails, loan history are PII).
- **Minimize & mask PII** — collect only what you need; mask it in lower environments (the Step 22 data lesson) and in logs (never log a raw password or full PII).
- **Encrypted, access-controlled backups** (Step 27) — a backup is a copy of all your data; treat it with the same care as the primary.

---

## Promises served

| Promise | How this chapter advanced it |
|---|---|
| **Secure** | The entire chapter — defense in depth across code, image, supply chain, secrets, runtime, edge, data. |
| **Correct** | Signature verification ensures only *your* validated artifacts run; admission control blocks misconfigured ones. |
| **Survives failure** | Least-privilege RBAC + NetworkPolicies contain a breach to one pod instead of the whole cluster. |
| **Observable** | Security events (failed auth, policy denials, secret access) feed the same logging/alerting from Step 25. |

## Key takeaways (the transferable lessons)

1. **Security is woven through every stage, not a final gate.** Shift left (catch early/cheap) and layer controls (defense in depth) so one failure isn't catastrophic.
2. **Most controls reuse work you've already done:** CI scans deps & images, the Dockerfile is non-root/minimal, the registry signs, GitOps handles secrets — security rides the pipeline you built.
3. **Supply chain matters now:** SBOMs (answer "are we affected?" instantly), signing + verification (only your artifacts run), provenance (auditable builds).
4. **Contain the blast radius at runtime:** least-privilege RBAC + default-deny NetworkPolicies + Pod Security mean a compromised pod can't roam.
5. **Secrets never touch code/image/git** — a manager + rotation + least-privilege access; and the edge is where Step 11's roles become real authz.

---

*Next — Step 27: Day 2 — reliability & operations. Shipping is Day 1; *running* it for years is Day 2, and usually the harder part: backups & tested restores, disaster recovery, runbooks, on-call & incident response, blameless post-mortems, and capacity/cost management.*
