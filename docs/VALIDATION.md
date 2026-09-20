# Validation

Run `make test lint demo-bad-deploy demo-unsafe-plan`. A real remediation claim requires a kind workload, alert evidence, approval, Kubernetes API action, and health verification recorded with exact commands. Record versions, services, results, failure/rollback evidence, and environment assumptions; never fabricate validation.

## Clean-Room Validation

Do not populate this section until executed. Record: date, commit SHA, OS/environment, Docker/kind/Kubernetes and key dependency versions where applicable; clean starting state; exact install/bootstrap/smoke/demo/failure/validation/cleanup commands; observed results; post-cleanup absence verification; and the second-bootstrap result. No prior local state or fabricated evidence is acceptable.
