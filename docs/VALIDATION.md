# Validation

Run `make install`, `make bootstrap-local`, `make smoke`, `make demo-rollback`, `make demo-remediation`, and `make verify`. The primary demo uses a real kind workload, Prometheus alert evidence, approval, Kubernetes API action, and health verification. Record versions, services, results, failure/rollback evidence, and environment assumptions; never fabricate validation.

## Clean-Room Validation

Executed 2026-09-25 on macOS with Docker Desktop 29.0.1, kind 0.30.0, kubectl 1.34.1,
and Python 3.12.12. `make cleanroom-validate` executed two independent cycles of:
`clean-local`, `bootstrap-local`, `smoke`, `demo-rollback`, `demo-remediation`,
`demo-image-recovery`, `demo-stale-plan`, `verify`, and `clean-local`.

Both cycles completed successfully (19:11:38Z and 19:13:30Z). Each final cleanup confirmed
that `ai-sre-remediation` was absent from `kind get clusters`; no project `.local` runtime
state remained. Per-cycle logs are retained in `.local-validation/`.
