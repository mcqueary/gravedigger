.PHONY: test run build help fmt install install-editable lint git-setup clean realclean all commitizen cov coveralls

# same as `export PYTHONPATH="$PWD:$PYTHONPATH"`
# see also https://stackoverflow.com/a/18137056
mkfile_path := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PYTHONPATH:=$(PYTHONPATH)
PACKAGES:=src/graver

VENV?=.venv
PIP=$(VENV)/bin/pip
PY=$(VENV)/bin/python
POETRY=$(VENV)/bin/poetry
VCR_CASSETTES=$(mkfile_path)tests/fixtures/vcr_cassettes/

all: ; $(info $$PYTHONPATH is [${PYTHONPATH}])

help: ## list targets with short description
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9._-]+:.*?## / {printf "\033[1m\033[36m%-38s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

cov: ## run pytest coverage report
	$(POETRY) run pytest --cov=graver --cov-report term-missing

coveralls: ## report coverage data to coveralls.io
	$(POETRY) run coveralls

test: ## run pytest
	$(POETRY) run pytest -rA -vvs --log-level INFO

lint: ## run flake8 to check the code
	$(POETRY) run flake8 $(PACKAGES) tests --count --select=E9,F63,F7,F82 --show-source --statistics
	$(POETRY) run flake8 $(PACKAGES) tests --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics
	$(POETRY) run deadcode $(PACKAGES)

install: ## install project using `which poetry` from pyproject.toml
	poetry install --with dev,test

fmt: ## run black to format the code
	$(POETRY) run isort $(PACKAGES) tests
	$(POETRY) run black -q --line-length 88 $(PACKAGES) tests

$(VENV)/init: ## init the virtual environment via standard pip
	python3.12 -m venv $(VENV)
	touch $@
	. $(VENV)/bin/activate && pip install -U pip
	. $(VENV)/bin/activate && pip install -r requirements.txt

$(VENV)/requirements: requirements.txt $(VENV)/init ## install requirements
	$(PIP) install -r $<
	touch $@

build: ## export requirements.txt (for standard pip install) and build dist
	$(POETRY) export -f requirements.txt --output requirements.txt
	$(POETRY) build

commitizen:
	@cz check --commit-msg-file .git/COMMIT_EDITMSG

clean: ## clean up test outputs and other temporary files
	rm -f *.csv
	rm -f *.db
	rm -f tests/*.log
	rm -f tests/*.db
	rm -f *.log*

realclean: clean ## clean up everything produced by the install and build
	rm -rf dist/
	rm -rf $(VENV)

vcrclean:
	rm -f $(VCR_CASSETTES)/*
