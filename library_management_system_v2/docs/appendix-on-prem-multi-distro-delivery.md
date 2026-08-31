# Appendix — Delivering an On-Prem Product to Multiple Private-Cloud Distros

*A short companion to Part II. The SaaS path (Steps 13–24) assumes **you** own the infrastructure. Shipping a product **into** customer-controlled, heterogeneous private clouds (e.g. OpenStack: Canonical / Red Hat / Kolla) inverts that. This is the compact survival guide.*

---

## The one principle

> **Keep ONE distro-agnostic product core; isolate every distro difference behind the thinnest possible per-distro integration adapter.**

It's Part I's **ports & adapters**, applied to *delivery*: your services are the core; each distro's deployment mechanism is an adapter. Maximize the shared core, minimize the per-distro layer — that layer is what multiplies your cost.

## How you ship into each distro (its *native* tooling)

| Distro | Native deploy tool | You deliver |
|---|---|---|
| **Canonical** | Juju + MAAS | a **subordinate charm** (rides on `nova-compute`/`cinder`) + control-plane charm; snaps/debs |
| **Red Hat OSP 16/17** | director (TripleO) | **certified container images** + **THT environment files** (Ansible/ExtraConfig) |
| **Red Hat RHOSO 18+** | OpenShift + Operators | a certified **Operator (OLM)** + EDPM Ansible for data-plane agents |
| **Kolla** | kolla-ansible | **container images** + `globals.yml` overrides / custom playbooks |

Same product binaries/images; thin per-distro *wiring* to inject and connect them.

## The two matrices to manage

1. **Packaging matrix** — artifacts per distro (images, charms, operator bundle, THT, ansible). *Minimize by sharing one image; keep only the wiring per-distro.*
2. **Support matrix** — `product version × OpenStack release × distro × distro version`. You **can't** support all combos: publish an explicit, versioned support matrix; **pin and gate**; deprecate as upstream EOLs.

## Pipeline (build once, test the matrix, publish to channels)

```
 build artifacts ONCE → test against REFERENCE deployments of EACH distro
   (install + backup/restore + UPGRADE tests, per OpenStack release)
   → publish to per-distro channels (Red Hat certified registry · Charmhub · Quay · repos)
   → customer installs via THEIR own tool
```
The **reference-cloud test lab** (real Canonical/RHOSP/Kolla clouds across releases) *is* the quality bar.

## What's different from SaaS (the gotchas)

- **Customer installs & upgrades**, on *their* schedule, coupled to *their* OpenStack lifecycle. Their deploy tool (Juju config / THT params / `globals.yml` / operator CR) is the **single source of truth** for config.
- **Upgrades must be backwards-compatible** across versions (expand/contract from Step 18) — old agents talk to a new control plane mid-upgrade.
- **Air-gapped is first-class**: offline bundles, mirrored/private registries, no phone-home.
- **You don't operate it** → invest in **diagnostic/support bundles** (one-command log+config+version collector), observability that plugs into *their* stack, signed artifacts + SBOMs, **certification** (Red Hat/Canonical), and per-distro docs + tested upgrade runbooks.

## Mental model

> SaaS deploys **one system you operate**; an on-prem product **manufactures artifacts customers install** into clouds you don't control. **One core + thin per-distro adapters; build once, test against a reference-cloud matrix, publish to native channels; pin a support matrix; and invest in upgrades, air-gap, diagnostics, and certification.**
