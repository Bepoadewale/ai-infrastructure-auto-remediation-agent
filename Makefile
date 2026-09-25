VENV ?= .venv
PYTHON ?= $(VENV)/bin/python
export PYTHONPATH := control-plane/src
.PHONY: install test lint bootstrap-local smoke demo-remediation demo-rollback demo-image-recovery demo-stale-plan verify clean-local

install:
	@if [ -x $(VENV)/bin/python ] && ! $(VENV)/bin/python -c 'import sys; raise SystemExit(sys.version_info[:2] != (3, 12))'; then rm -rf $(VENV); fi
	python3.12 -m venv $(VENV)
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e '.[dev]'

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check control-plane/src tests local

bootstrap-local:
	./scripts/bootstrap-local.sh

smoke:
	./scripts/smoke.sh

demo-remediation:
	./scripts/demo-remediation.sh

demo-rollback:
	./scripts/demo-rollback.sh

demo-image-recovery:
	./scripts/demo-image-recovery.sh

demo-stale-plan:
	./scripts/demo-stale-plan.sh

verify: test lint

clean-local:
	./scripts/clean-local.sh
