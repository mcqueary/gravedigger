.PHONY: test test-unit test-integration run help fmt install-editable lint git-setup clean all

# same as `export PYTHONPATH="$PWD:$PYTHONPATH"`
# see also https://stackoverflow.com/a/18137056
mkfile_path := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PYTHONPATH:=$(PYTHONPATH):$(mkfile_path)

VENV?=.venv
PIP=$(VENV)/bin/pip
PY=$(VENV)/bin/python

all: ; $(info $$PYTHONPATH is [${PYTHONPATH}])

help: ## list targets with short description
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9._-]+:.*?## / {printf "\033[1m\033[36m%-38s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

cov: ## run pytest coverage report
	. $(VENV)/bin/activate && pytest --cov tests/ && coveralls

run: ## sample run
	. $(VENV)/bin/activate && $(PY) graver/app.py -i input.txt

test-unit: $(info $$PYTHONPATH is [${PYTHONPATH}])
	. $(VENV)/bin/activate && pytest -rA -vvs --log-level INFO tests/unit

test-integration: $(info $$PYTHONPATH is [${PYTHONPATH}])
	. $(VENV)/bin/activate && pytest -rA -vvs --log-level INFO tests/integration

test: test-unit test-integration

lint: ## run flake8 to check the code
	. $(VENV)/bin/activate && flake8 --max-line-length 88 src tests

install-editable:
	. $(VENV)/bin/activate && pip install -e .

fmt: ## run black to format the code
	. $(VENV)/bin/activate && isort src tests
	. $(VENV)/bin/activate && black -q --line-length 88 src tests

$(VENV)/init: ## init the virtual environment
	python3 -m venv $(VENV)
	touch $@

$(VENV)/requirements: requirements.txt $(VENV)/init ## install requirements
	$(PIP) install -r $<
	touch $@

clean: ## clean up test outputs and other temporary files
	rm -f *.csv
	rm -f *.db
