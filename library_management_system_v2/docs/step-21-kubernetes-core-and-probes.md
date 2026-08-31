# Step 21 — Kubernetes Core & Health Probes

*Series: Designing a Library Management System with DDD · Chapter 21 — Part II*

---

This is the orchestration deep-dive. We've got an immutable image (16/17), a tested pipeline (19), and a GitOps delivery flow (20). Now: *what actually runs the containers, keeps them alive, scales them, and routes traffic?* **Kubernetes** — and we'll build up its core objects one at a time on the LMS, then go deep on the single most-botched concept: **health probes**.

> **What an orchestrator is *for*:** you declare *desired state* ("run 3 healthy copies of the LMS, reachable at this URL"), and Kubernetes runs a **control loop** that continuously makes *actual state* match. A pod crashes? It restarts it. A node dies? It reschedules elsewhere. You scaled to 5? It starts 2 more. You stop telling it *how*; you tell it *what*. (This is the same reconciliation idea GitOps used in Step 20 — Kubernetes is reconciliation all the way down.)

---

## 21.1 The core objects, built up on the LMS

Kubernetes models everything as **declarative objects**. You add them layer by layer:

| Object | What it is | For the LMS |
|---|---|---|
| **Pod** | The smallest unit — one (or few) containers sharing a network/storage | One running LMS container |
| **ReplicaSet** | Keeps *N* identical Pods running | "always 3 LMS pods" (you rarely write this directly) |
| **Deployment** | Manages ReplicaSets + **rolling updates** + rollback | How you actually run + upgrade the LMS |
| **Service** | A stable virtual IP/DNS name load-balancing across healthy Pods | `lms` — a fixed address for the pods |
| **Ingress** | HTTP(S) entry from outside + routing + TLS | `api.library.example.com` → the Service |
| **ConfigMap** | Non-secret config as key/values | `LOG_LEVEL`, `FINE_RATE_PAISE` |
| **Secret** | Sensitive config (base64, ideally encrypted at rest) | `DATABASE_URL`, API keys |
| **HPA** | Auto-scales Pod count on metrics | scale LMS 3→10 on CPU |
| **Namespace** | A virtual cluster for isolation | `lms-staging`, `lms-prod` |

You almost never create a bare Pod — you create a **Deployment**, which creates a ReplicaSet, which creates Pods. Why? Because the Deployment gives you **self-healing** (replaces dead pods) and **rolling updates** (Step 23) for free.

---

## 21.2 The LMS manifests

### Deployment — runs N self-healing copies, upgrades them safely

```yaml
apiVersion: apps/v1
kind: Deployment
metadata: { name: lms, namespace: lms-prod }
spec:
  replicas: 3                                  # 3 copies (safe because stateless — Step 14)
  selector: { matchLabels: { app: lms } }
  strategy:
    type: RollingUpdate                        # zero-downtime upgrades (Step 23)
    rollingUpdate: { maxUnavailable: 0, maxSurge: 1 }
  template:
    metadata: { labels: { app: lms } }
    spec:
      containers:
        - name: lms
          image: ghcr.io/your-org/lms:sha-9f8c2a1   # the immutable SHA tag (Step 17)
          ports: [{ containerPort: 8000 }]
          envFrom:
            - configMapRef: { name: lms-config }    # non-secret config
            - secretRef:    { name: lms-secrets }   # DB URL, keys
          resources:                                 # ← drives scheduling & limits (21.4)
            requests: { cpu: "100m", memory: "128Mi" }
            limits:   { cpu: "500m", memory: "256Mi" }
          startupProbe:                              # ← give slow starts time (21.3)
            httpGet: { path: /healthz, port: 8000 }
            failureThreshold: 30
            periodSeconds: 2
          livenessProbe:                             # ← restart if WEDGED (21.3)
            httpGet: { path: /healthz, port: 8000 }
            periodSeconds: 10
          readinessProbe:                            # ← gate traffic until READY (21.3)
            httpGet: { path: /readyz, port: 8000 }
            periodSeconds: 5
```

### Service — a stable address that load-balances the pods

```yaml
apiVersion: v1
kind: Service
metadata: { name: lms, namespace: lms-prod }
spec:
  selector: { app: lms }                       # routes to pods with label app=lms
  ports: [{ port: 80, targetPort: 8000 }]
```

The Service gives the pods one stable name (`lms`) and **only sends traffic to pods that are *ready***. As pods come and go (deploys, scaling, crashes), the Service tracks the healthy set automatically — clients never chase IPs.

### Ingress — external HTTPS entry + TLS

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: lms
  namespace: lms-prod
  annotations: { cert-manager.io/cluster-issuer: letsencrypt }   # auto-TLS (Step 24)
spec:
  tls: [{ hosts: [api.library.example.com], secretName: lms-tls }]
  rules:
    - host: api.library.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend: { service: { name: lms, port: { number: 80 } } }
```

### ConfigMap & Secret — config injected as env (Step 14)

```yaml
apiVersion: v1
kind: ConfigMap
metadata: { name: lms-config, namespace: lms-prod }
data: { LOG_LEVEL: "INFO", FINE_RATE_PAISE: "500", MAX_ACTIVE_LOANS: "2" }
---
apiVersion: v1
kind: Secret
metadata: { name: lms-secrets, namespace: lms-prod }
type: Opaque
stringData:
  DATABASE_URL: "postgresql://lms:••••@db.internal:5432/lms"   # via Sealed/External Secrets (Step 26)
```

### HPA — scale on load

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata: { name: lms, namespace: lms-prod }
spec:
  scaleTargetRef: { apiVersion: apps/v1, kind: Deployment, name: lms }
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource: { name: cpu, target: { type: Utilization, averageUtilization: 70 } }
```

When average CPU crosses 70%, Kubernetes adds pods (up to 10); when load drops, it removes them (down to 3). This works *only because the app is stateless* (Step 14) — any new pod is interchangeable. (Scaling depth + the database bottleneck: Step 24.)

> **Don't hand-write all this per environment.** Template it with **Helm** (a chart + per-env `values.yaml`) or **Kustomize** (a base + overlays), so staging and prod share one definition differing only in replica counts, resources, and config. This is what the GitOps config repo (Step 20) actually contains.

---

## 21.3 Health probes — the most-botched concept (deep dive)

This is the payoff of the `/healthz` and `/readyz` endpoints we built in Step 14. Kubernetes has **three** probes, and confusing them causes real outages.

| Probe | Question | If it FAILS, Kubernetes… | LMS endpoint |
|---|---|---|---|
| **startupProbe** | "Has it finished booting *yet*?" | keeps waiting (won't kill a slow starter) | `/healthz` |
| **livenessProbe** | "Is the process **wedged**?" | **kills & restarts** the pod | `/healthz` |
| **readinessProbe** | "Can it serve **right now**?" | **stops sending traffic** (keeps it running) | `/readyz` |

**The crucial distinction — and the classic disaster:**

- **Liveness must be cheap and dependency-free.** It answers "is *this process* stuck?" If you make liveness check the **database**, then when the DB has a brief blip, **every pod fails liveness at once → Kubernetes restarts the entire fleet → a restart-loop outage** — turning a 5-second DB hiccup into a full outage. *Never check dependencies in liveness.* (This is exactly why Step 14's `/healthz` returns `ok` with no DB call.)
- **Readiness checks dependencies.** It answers "can I *serve* right now?" If the DB is unreachable, the pod fails readiness → the **Service stops routing to it** but **leaves it running**, so it recovers and rejoins automatically when the DB returns. No restart, no data loss, graceful degradation.
- **Startup probe** protects **slow-booting** apps: until it passes, liveness/readiness are suspended, so a slow start isn't mistaken for a hang and killed.

> **The mental model:** *liveness = "should I restart you?" · readiness = "should I send you traffic?" · startup = "are you done booting?"* Mixing the first two is the single most common Kubernetes production mistake — call it out hard when teaching.

These probes are also what make **rolling deploys zero-downtime** (Step 23): a new pod gets traffic *only* after its readiness probe passes, and the old pod stops getting traffic *before* it's torn down.

---

## 21.4 Resource requests & limits (scheduling + safety)

```yaml
resources:
  requests: { cpu: "100m", memory: "128Mi" }   # what the pod is GUARANTEED (used for scheduling)
  limits:   { cpu: "500m", memory: "256Mi" }    # the hard CEILING
```

- **Requests** tell the scheduler how much to reserve → which node has room. Set too low and nodes get overpacked and thrash; too high and you waste money.
- **Limits** are hard caps. Exceed the **memory** limit → the container is **OOMKilled** (terminated). Exceed the **CPU** limit → it's **throttled** (slowed, not killed).
- Requests vs limits also set the pod's **Quality of Service** class, which decides who gets evicted first when a node runs out of memory.

> Knowing your app's real CPU/memory profile (the "resource needs known" checkbox from Step 14) is what lets you set these sanely. Guess wrong and you get either OOMKills or a huge cloud bill.

---

## 21.5 How a request reaches the LMS (the whole path)

```
 user → DNS (api.library.example.com) → cloud Load Balancer
      → Ingress controller (terminates TLS, routes by host/path)
      → Service `lms` (load-balances across READY pods)
      → a Pod (gunicorn + uvicorn workers) → FastAPI → domain → DB
```

Every hop is one of the objects above. **Managed Kubernetes** (EKS/GKE/AKS) runs the control plane for you — you bring nodes and workloads; the cloud runs the brain. Self-managed (kubeadm) means you operate the control plane too — rarely worth it.

---

## Promises served

| Promise | How this chapter advanced it |
|---|---|
| **Available** | Deployment + Service keep N healthy replicas behind one stable address; readiness gates traffic to only-ready pods. |
| **Survives failure** | Self-healing: crashed pods restart, dead-node pods reschedule; liveness restarts wedged processes. |
| **Survives change** | RollingUpdate strategy + probes give zero-downtime deploys and one-command rollback (Step 23). |
| **(Efficiency)** | Requests/limits pack workloads onto nodes safely; the HPA scales with demand. |

## Key takeaways (the transferable lessons)

1. **Kubernetes is a reconciliation loop:** you declare desired state; it continuously makes actual state match (self-healing, scaling, rescheduling).
2. **You run a Deployment, not bare Pods** — it gives self-healing + rolling updates; a Service gives a stable address that routes only to *ready* pods.
3. **The three probes are not interchangeable.** Liveness = "restart me if wedged" (cheap, **no dependency checks**); readiness = "send me traffic only when I can serve" (checks deps); startup = "I'm still booting." Checking the DB in *liveness* causes fleet-wide restart-loop outages.
4. **Requests guide scheduling; limits are hard caps** (memory over-limit = OOMKill, CPU over-limit = throttle). Know your app's profile.
5. **Template per-environment with Helm/Kustomize** — one definition, many environments — which is exactly what the GitOps config repo holds.

---

*Next — Step 22: Environments & promotion. We formalize the dev → staging → prod pipeline — what each environment is for, how the *same* image (Step 17) flows through them changing only config, and how promotion works as a gated git commit in the GitOps repo (Step 20).*
