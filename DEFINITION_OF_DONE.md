# Definition of Done

# Portfolio Complete — Local-First Scope Gate

- [x] kind runs real faulty workloads: readiness regression and image-pull failure, each recovered by bounded remediation.
- [x] Prometheus produces an incident signal; cluster evidence is collected through Kubernetes APIs.
- [x] Diagnosis uses observed evidence; deterministic policy remains authority and records preconditions/risk.
- [x] At least one bounded remediation changes real Kubernetes state and verification proves recovery.
- [x] Dangerous remediation is approval-required; changed cluster state rejects stale plans.
- [x] Unsafe/unapproved remediation fails safely before mutation; approved recovery restores the verified fixture.
- [x] Fingerprint deduplication, atomic cooldown, and persistent action budget guard repeated/concurrent mutations.
- [x] Persistent audit and appropriate incident/remediation metrics are observable.
- [x] Reproducible alert → evidence → diagnosis → plan → policy → mutation → verification demo and meaningful unit/integration/E2E/failure tests pass locally; CI retains the portable suite.
- [x] README/status distinguish real kind execution from unexecuted cloud/multi-cluster adapters.

## Maturity Levels

- **FOUNDATION:** architecture and domain logic exist.
- **PARTIALLY VALIDATED:** deterministic loop or integration evidence exists, but core cluster story is incomplete.
- **LOCAL END-TO-END VALIDATED:** success path runs locally with material failure/recovery/observability gaps.
- **PORTFOLIO COMPLETE — LOCAL-FIRST SCOPE:** all gates are executed with evidence.

# Clean-Room Reproducibility Gate

`PORTFOLIO COMPLETE — LOCAL-FIRST SCOPE` requires two executed clean-room cycles: clone → install → bootstrap kind, monitoring, fixture workload → smoke → alert/evidence/diagnosis/policy/remediation/verification demo → rollback or safe-failure demo → validation → project-scoped cleanup → second clean bootstrap/demo. Planned commands: `make install`, `make bootstrap-local`, `make smoke`, `make demo-remediation`, `make demo-rollback`, `make verify`, `make clean-local`.

- [x] Two clean bootstrap cycles have no hidden state; primary and failure demos pass.
- [x] Cleanup removes only the named kind cluster and repository `.local` state.
- [x] Post-cleanup absence and second bootstrap/demo are recorded in `docs/VALIDATION.md`.
