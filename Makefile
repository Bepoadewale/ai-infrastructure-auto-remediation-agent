PYTHON ?= python3
export PYTHONPATH := control-plane/src
.PHONY: test lint demo-bad-deploy demo-unsafe-plan
test:
	$(PYTHON) -m pytest -q
lint:
	$(PYTHON) -m ruff check control-plane/src tests
demo-bad-deploy:
	$(PYTHON) -m pytest tests/test_loop.py::test_bad_deployment_requires_approval_then_recovers -q
demo-unsafe-plan:
	$(PYTHON) -m pytest tests/test_loop.py::test_unsafe_action_is_not_a_capability -q
