.PHONY: test run help fmt install-editable lint git-setup clean

# same as `export PYTHONPATH="$PWD:$PYTHONPATH"`
# see also https://stackoverflow.com/a/18137056
mkfile_path := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PYTHONPATH:=$(PYTHONPATH):$(mkfile_path)graver

VENV?=.venv
PIP=$(VENV)/bin/pip
PY=$(VENV)/bin/python

help: ## list targets with short description
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9._-]+:.*?## / {printf "\033[1m\033[36m%-38s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

cov: ## run pytest coverage report
	. $(VENV)/bin/activate && pytest --cov=graver tests/ --cov=soup tests/ --cov=db tests/ --cov=memorial tests/

run: ## sample run
	. $(VENV)/bin/activate && $(PY) graver/app.py -i input.txt

test: ## run pytest
	. $(VENV)/bin/activate && pytest -rA -vvs --log-level INFO

lint: ## run flake8 to check the code
	. $(VENV)/bin/activate && flake8 --max-line-length 88 graver tests

install-editable:
	. $(VENV)/bin/activate && pip install -e .

fmt: ## run black to format the code
	. $(VENV)/bin/activate && black -q --line-length 88 graver tests

$(VENV)/init: ## init the virtual environment
	python3 -m venv $(VENV)
	touch $@

$(VENV)/requirements: requirements.txt $(VENV)/init ## install requirements
	$(PIP) install -r $<
	touch $@

clean: ## clean up test outputs and other temporary files
	rm -f *.csv
	rm -f *.db
