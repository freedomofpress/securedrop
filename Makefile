DEFAULT_GOAL: help

.PHONY: ci-spinup
ci-spinup: ## Creates AWS EC2 hosts for testing staging environment.
	./devops/scripts/ci-spinup.sh

.PHONY: ci-teardown
ci-teardown: ## Destroy AWS EC2 hosts for testing staging environment.
	./devops/scripts/ci-teardown.sh

.PHONY: ci-run
ci-run: ## Provisions AWS EC2 hosts for testing staging environment.
	./devops/scripts/ci-runner.sh

# Run SpinUP, Playbooks, and Testinfra
.PHONY: ci-go
ci-go: ## Creates, provisions, tests, and destroys AWS EC2 hosts for testing staging environment.
	./devops/scripts/spin-run-test.sh

.PHONY: ci-test
ci-test: ## Tests AWS EC2 hosts for testing staging environment.
	./devops/scripts/spin-run-test.sh only_test

.PHONY: ci-debug
ci-debug: ## Prevents automatic destruction of AWS EC2 hosts on error.
	touch ${HOME}/.FPF_CI_DEBUG

.PHONY: ci-build-only
ci-build-only: ## Kicks off build logic and pulls back deb files.
	./devops/scripts/ci-build_only.sh

.PHONY: docs-lint
docs-lint: ## Check documentation for common syntax errors.
# The `-W` option converts warnings to errors.
# The `-n` option enables "nit-picky" mode.
	make -C docs/ clean && sphinx-build -Wn docs/ docs/_build/html

.PHONY: docs
docs: ## Build project documentation in live reload for editing
# Spins up livereload environment for editing; blocks.
	make -C docs/ clean && sphinx-autobuild docs/ docs/_build/html

.PHONY: flake8
flake8: ## Validates PEP8 compliance for Python source files.
	flake8 --exclude='config.py' testinfra securedrop-admin \
		securedrop/*.py securedrop/management \
		securedrop/tests/functional securedrop/tests/*.py

.PHONY: html-lint
html-lint: ## Validates HTML in web application template files.
	html_lint.py --printfilename --disable=optional_tag,extra_whitespace,indentation \
		securedrop/source_templates/*.html securedrop/journalist_templates/*.html

.PHONY: lint
lint: docs-lint flake8 html-lint ## Runs all linting tools (docs, flake8, HTML).

# Explaination of the below shell command should it ever break.
# 1. Set the field separator to ": ##" and any make targets that might appear between : and ##
# 2. Use sed-like syntax to remove the make targets
# 3. Format the split fields into $$1) the target name (in blue) and $$2) the target descrption
# 4. Pass this file as an arg to awk
# 5. Sort it alphabetically
.PHONY: help
help: ## Print this message and exit.
	@awk 'BEGIN {FS = ":.*?## "} /^[0-9a-zA-Z_-]+:.*?## / {printf "\033[36m%16s\033[0m : %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort
