.DEFAULT_GOAL = help

COVERAGE      := coverage
HOOKS         := hooks
INSTALL       := install
MUSTPASS      := $(HOOKS) $(COVERAGE)

format: ## Format code with respect to linters
	poetry run isort .
	poetry run black .

clean: ## Remove previous coverage data
	find . -type f -name '*pyc' -exec rm -rf {} \;
	find . -type d -name '__pycache__' -prune -exec rm -rf {} \;
	find . \( -name '*bundle*' -o -name '*requirements.txt' \) -exec rm -rf {} \+ 2> /dev/null
	$(COVERAGE) erase

$(COVERAGE): clean  ## Run code coverage
	$(COVERAGE) run --source . -p -m pytest -svv $(subst -,/,$*) || true
	$(COVERAGE) combine .
	$(COVERAGE) report -i --fail-under=100 --show-missing $(find . -type f -name *.py)

$(HOOKS): ## Run pre-commit hooks
	poetry run pre-commit run --all-files

$(INSTALL): $(INSTALL_DEPS) ## Install all project dependencies
	poetry run pre-commit install
	poetry install

test-build-$(DEV): $(MUSTPASS) ## Test build dev

test-build-$(PROD): $(MUSTPASS) ## Test build prod

publish:  ## Publish to CodeArtifact
	poetry publish --build