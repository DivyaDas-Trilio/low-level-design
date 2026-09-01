# ---- config ----
# override the venv path with:  make test VENV=/path/to/.venv
VENV ?= /Users/divyajyotidas/workspace/.venv
PY   := $(VENV)/bin/python

.PHONY: install test cov cov-html demo run clean check help

install:   ## install project + dev deps into the venv
	$(PY) -m pip install -e ".[dev]"

test:      ## run the test suite
	$(PY) -m pytest

cov:       ## tests + coverage (terminal, with missing lines)
	$(PY) -m pytest --cov=src --cov-report=term-missing

cov-html:  ## tests + browsable HTML coverage report
	$(PY) -m pytest --cov=src --cov-report=html
	open htmlcov/index.html

demo:      ## run the CLI demo harness
	$(PY) src/main.py

run:       ## run the FastAPI app (dev, auto-reload)
	$(PY) -m uvicorn app:app --app-dir src --reload

clean:     ## remove caches & coverage artifacts
	rm -rf .pytest_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +

check: test cov   ## run tests + coverage

help:      ## list available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'
