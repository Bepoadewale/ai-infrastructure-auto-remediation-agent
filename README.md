# Governed AI SRE Auto-Remediation Platform

A local-first control plane that investigates Kubernetes incidents and performs only bounded, policy-authorized remediation. It gives an AI-style investigator read-only evidence access; deterministic policy, a separate approver, stale-state checks, and an allowlisted executor remain the authority for writes.

```text
Prometheus alert → incident → Kubernetes evidence → deterministic diagnosis
→ immutable plan/preconditions → approval → bounded Kubernetes action
→ readiness verification → durable audit + metrics
```

## What it allows—and what it refuses

The local demo can inspect the `sre-remediation` namespace and execute one of four explicit actions: rollback a known checkout fixture, bounded scale, restart a Deployment, or delete a failed Pod. It cannot run arbitrary shell commands, pass through `kubectl`, delete namespaces, obtain cluster-admin credentials, or approve its own production change. A production action is denied until a separate approver authorizes the exact persisted plan; changed Kubernetes resource state causes a stale-plan rejection.

## Executed local demonstration

The primary demo creates a real kind cluster, deploys a healthy checkout fixture and Prometheus, injects a readiness regression, waits for the `CheckoutUnavailable` Prometheus alert, gathers Deployment/Pod/Event evidence through the Kubernetes API, requires production approval, patches the previous-known-good health setting, and waits for the Deployment to become Ready.

```bash
make install
make bootstrap-local
make smoke
make demo-rollback      # unapproved production mutation returns 403
make demo-remediation   # real Kubernetes rollback and readiness verification
make verify
make clean-local
```

`make clean-local` deletes only the `ai-sre-remediation` kind cluster and this repository's `.local` state; it does not prune Docker globally or touch unrelated clusters.

## Local architecture

- FastAPI control plane with SQLite-backed incident, plan, approval, and timeline persistence.
- Kubernetes Python client with exact action allowlist and resource-version preconditions.
- Prometheus scraping the fixture and evaluating the alert rule.
- Prometheus metrics at `/metrics`; audit timeline at `/api/v1/incidents/{id}/timeline`.
- A deliberately tiny Python fixture image—this is an infrastructure-control demo, not a production workload benchmark.

## Evidence boundary

See [implementation status](docs/IMPLEMENTATION_STATUS.md) and [validation evidence](docs/VALIDATION.md). Multi-cluster operation, enterprise incident tooling, cloud credentials, and autonomous arbitrary remediation are not implemented or claimed.
