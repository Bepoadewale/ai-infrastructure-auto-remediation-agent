# Definition of Done

# Portfolio Complete — Local-First Scope Gate

- [ ] kind runs real faulty workloads, including multiple relevant failures such as bad deployment, CrashLoop, saturation, or dependency failure. *(One bad-deployment/readiness regression is executed; second class remains.)*
- [x] Prometheus produces an incident signal; cluster evidence is collected through Kubernetes APIs.
- [x] Diagnosis uses observed evidence; deterministic policy remains authority and records preconditions/risk.
- [x] At least one bounded remediation changes real Kubernetes state and verification proves recovery.
- [x] Dangerous remediation is approval-required; stale state is unit-tested before mutation. *(Cluster stale-plan validation remains to be added.)*
- [ ] Failed remediation rolls back safely where relevant.
- [ ] Cooldown, action/change budgets, repeated-incident protection, and lifecycle concurrency prevent loops.
- [x] Persistent audit and appropriate incident/remediation metrics are observable.
- [ ] Reproducible alert → evidence → diagnosis → plan → policy → mutation → verification demo and meaningful unit/integration/E2E/failure tests pass with CI green.
- [x] README/status distinguish real kind execution from unexecuted cloud/multi-cluster adapters.

## Maturity Levels

- **FOUNDATION:** architecture and domain logic exist.
- **PARTIALLY VALIDATED:** deterministic loop or integration evidence exists, but core cluster story is incomplete.
- **LOCAL END-TO-END VALIDATED:** success path runs locally with material failure/recovery/observability gaps.
- **PORTFOLIO COMPLETE — LOCAL-FIRST SCOPE:** all gates are executed with evidence.

# Clean-Room Reproducibility Gate

`PORTFOLIO COMPLETE — LOCAL-FIRST SCOPE` requires two executed clean-room cycles: clone → install → bootstrap kind, monitoring, fixture workload → smoke → alert/evidence/diagnosis/policy/remediation/verification demo → rollback or safe-failure demo → validation → project-scoped cleanup → second clean bootstrap/demo. Planned commands: `make install`, `make bootstrap-local`, `make smoke`, `make demo-remediation`, `make demo-rollback`, `make verify`, `make clean-local`.

- [ ] Clean clone/bootstrap has no hidden state; primary and failure demos pass.
- [ ] Cleanup removes only this project and unrelated resources survive.
- [ ] Post-cleanup absence and second bootstrap/demo are recorded in `docs/VALIDATION.md`.
