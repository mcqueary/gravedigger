NAME := graver
INSTALL_STAMP := .install.stamp
POETRY := $(shell command -v poetry 2> /dev/null)
VENV?=.venv

SRC := src/$(NAME)

.PHONY: test run build help fmt install install-editable lint git-setup clean realclean all commitizen
.DEFAULT_GOAL := help

.PHONY: help
help: ## list targets with short description
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9._-]+:.*?## / {printf "\033[1m\033[36m%-38s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: install
install: $(INSTALL_STAMP) ## install project using `which poetry` from pyproject.toml
$(INSTALL_STAMP): pyproject.toml poetry.lock
	@if [ -z $(POETRY) ]; then echo "Poetry could not be found. See https://python-poetry.org/docs/"; exit 2; fi
	$(POETRY) --version
	poetry install --with dev,test --no-ansi --no-interaction --verbose
	touch $(INSTALL_STAMP)

.PHONY: lint
lint: $(INSTALL_STAMP) ## run flake8 to check the code
	$(POETRY) run isort --profile=black --lines-after-imports=2 --check-only tests $(SRC)
	$(POETRY) run black --check tests $(SRC) --diff
	$(POETRY) run flake8 tests $(SRC) --count --select=E9,F63,F7,F82 --show-source --statistics
	$(POETRY) run flake8 tests $(SRC) --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
	$(POETRY) run mypy tests $(SRC) --ignore-missing-imports

.PHONY: fmt
fmt: $(INSTALL_STAMP) ## run black to format the code
	$(POETRY) run isort --profile=black --lines-after-imports=2 tests $(SRC)
	$(POETRY) run black --line-length 88 $(SRC) tests

.PHONY: test
test: $(INSTALL_STAMP) tests ## run pytest
	$(POETRY) run pytest tests --cov-report term-missing --cov-fail-under 100 --cov $(NAME) --durations=10 $(ARGS)

.PHONY: test-verbose
test-verbose: tests ## run pytest
	$(POETRY) run pytest -rA -vvs --log-level INFO $(ARGS)

.PHONY: build
build: ## export requirements.txt (for standard pip install) and build dist
	$(POETRY) export -f requirements.txt --output requirements.txt
	$(POETRY) build

.PHONY: clean
clean: ## Delete cache and other temporary files
	find . -type d -name "__pycache__" | xargs rm -rf {};
	rm -rf .install.stamp .coverage .mypy_cache $(VERSION_FILE)

.PHONY: realclean
realclean: clean ## clean up everything produced by the install and build
	rm -rf dist/
	rm -rf $(VENV)
	rm -f *.csv *.db *.log* tests/*.log* tests/*.db

.PHONY: vcrclean
vcrclean: ## clean up VCR.py cassettes
	rm -f tests/fixtures/vcr_cassettes/* tests/fixtures/cassettes/*

.PHONY: commitizen
commitizen:
	@cz check --commit-msg-file .git/COMMIT_EDITMSG
