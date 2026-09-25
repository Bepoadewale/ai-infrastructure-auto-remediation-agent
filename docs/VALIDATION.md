# Validation

Run `make install`, `make bootstrap-local`, `make smoke`, `make demo-rollback`, `make demo-remediation`, and `make verify`. The primary demo uses a real kind workload, Prometheus alert evidence, approval, Kubernetes API action, and health verification. Record versions, services, results, failure/rollback evidence, and environment assumptions; never fabricate validation.

## Clean-Room Validation

Do not populate this section until executed. Record: date, commit SHA, OS/environment, Docker/kind/Kubernetes and key dependency versions where applicable; clean starting state; exact install/bootstrap/smoke/demo/failure/validation/cleanup commands; observed results; post-cleanup absence verification; and the second-bootstrap result. No prior local state or fabricated evidence is acceptable.
