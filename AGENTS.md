# AI Infrastructure Auto-Remediation Agent — Agent Guide

Mission: investigate incidents from evidence and execute only bounded, policy-authorized remediation with verification and audit.

Stack: Python 3.12, FastAPI, deterministic local executor, Kubernetes/Prometheus contracts.

Commands: `make test`, `make lint`, `make demo-bad-deploy`, `make demo-unsafe-plan`.

Rules: diagnosis is not authority; never add arbitrary shell/kubectl or autonomous approval; distinguish local executor from Kubernetes; no secrets/main pushes; meaningful changes require tests and factual status updates.

Completion rule: do not mark **PORTFOLIO COMPLETE — LOCAL-FIRST SCOPE** unless `DEFINITION_OF_DONE.md` has executed evidence. Deterministic simulations, manifests, policy classes, unit tests, and documentation do not prove remediation. The alert → evidence → policy → real cluster mutation → verification story must run locally; cloud/multi-cluster adapters stay explicit.

## Clean-room reproducibility

Clean-room reproducibility is a mandatory completion criterion. Do not mark this repository
`PORTFOLIO COMPLETE — LOCAL-FIRST SCOPE` until a new engineer can reproduce the platform from a
clean project state using documented commands, execute the primary and required failure demos, run
validation, and safely tear down only this project's local resources. Do not infer reproducibility
from an existing developer environment; execute it after project-specific cleanup.
