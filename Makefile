.PHONY: test test-unit test-integration run help fmt install-editable lint git-setup clean all commitizen coveralls

# same as `export PYTHONPATH="$PWD:$PYTHONPATH"`
# see also https://stackoverflow.com/a/18137056
mkfile_path := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PYTHONPATH:=$(PYTHONPATH):$(mkfile_path):$(mkfile_path)graver
PACKAGES:=graver

VENV?=.venv
PIP=$(VENV)/bin/pip
PY=$(VENV)/bin/python

all: ; $(info $$PYTHONPATH is [${PYTHONPATH}])

help: ## list targets with short description
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9._-]+:.*?## / {printf "\033[1m\033[36m%-38s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

cov: ## run pytest coverage report
	. $(VENV)/bin/activate && pytest --cov=graver --cov-report term-missing

coveralls: ## report coverage data to coveralls.io
	. $(VENV)/bin/activate && coveralls

test-unit: ## run pytest unit tests only
	. $(VENV)/bin/activate && pytest -rA -vvs --log-level INFO --without-integration

test-integration: ## run pytest integration tests
	. $(VENV)/bin/activate && pytest -rA -vvs --log-level INFO --with-integration

test: ## run pytest
	. $(VENV)/bin/activate && pytest -rA -vvs --log-level INFO

lint: ## run flake8 to check the code
	. $(VENV)/bin/activate && flake8 $(PACKAGES) tests --count --select=E9,F63,F7,F82 --show-source --statistics
	. $(VENV)/bin/activate && flake8 $(PACKAGES) tests --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics

install-editable:
	. $(VENV)/bin/activate && pip install -e .

fmt: ## run black to format the code
	. $(VENV)/bin/activate && isort $(PACKAGES) tests
	. $(VENV)/bin/activate && black -q --line-length 88 $(PACKAGES) tests

$(VENV)/init: ## init the virtual environment
	python3 -m venv $(VENV)
	touch $@

$(VENV)/requirements: requirements.txt $(VENV)/init ## install requirements
	$(PIP) install -r $<
	touch $@

commitizen:
	@cz check --commit-msg-file .git/COMMIT_EDITMSG

clean: ## clean up test outputs and other temporary files
	rm -f *.csv
	rm -f *.db
