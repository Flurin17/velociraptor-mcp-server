.PHONY: dev test build release clean health fmt lint

VENV?=.venv
PY?=$(VENV)/bin/python
PIP?=$(VENV)/bin/pip

venv:
	python3 -m venv $(VENV)
	$(PIP) install -U pip

dev: venv
	$(PIP) install -e .[dev]

lint: dev
	$(VENV)/bin/pre-commit run --all-files

fmt: dev
	$(VENV)/bin/black mcp_server tests
	$(VENV)/bin/ruff check --fix mcp_server tests

test: dev
	$(PY) -m pytest -q

health: dev
	$(PY) test_api.py --config velociraptor_lab/volumes/api/api.config.yaml --query "SELECT * FROM clients()"

build: dev
	rm -rf dist build velociraptor_mcp_server.egg-info
	$(PY) -m build --no-isolation
	$(PY) -m twine check dist/*

release: VERSION?=
release:
	@if [ -z "$(VERSION)" ]; then echo "VERSION is required, e.g. make release VERSION=0.1.6"; exit 1; fi
	$(PY) scripts/release.py $(VERSION)
	git add pyproject.toml mcp_server/__init__.py README.md
	git commit -m "Release $(VERSION)"
	git tag -a v$(VERSION) -m "v$(VERSION)"
	git push origin main
	git push origin v$(VERSION)

clean:
	rm -rf dist build velociraptor_mcp_server.egg-info $(VENV)
