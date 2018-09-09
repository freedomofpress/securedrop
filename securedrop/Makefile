DEFAULT_GOAL: help
TAG ?= $(shell git rev-parse HEAD)
IMAGE = securedrop

.PHONY: lint
lint: ## Run the python linter with the project's default error settings
	find . -name '*.py' | xargs pylint --reports=no --errors-only \
	   --disable=import-error \
	   --disable=no-name-in-module \
	   --disable=unexpected-keyword-arg \
	   --disable=too-many-function-args \
	   --disable=import-error \
	   --max-line-length=100

.PHONY: lint-full
lint-full:  ## Run the python linter with nothing disabled
	find . -name '*.py' | xargs pylint

.PHONY: test
test: ## Run the test suite in a Ubuntu 16.04 (Xenial) dockerized environment
	./bin/dev-shell ./bin/run-test -v $${TESTFILES:-tests}

.PHONY: test-trusty
test-trusty: ## Run the test suite in a Ubuntu 14.04 (Trusty) dockerized environment (to be removed April 30, 2019)
	BASE_OS=trusty ./bin/dev-shell ./bin/run-test -v $${TESTFILES:-tests}

.PHONY: translation-test
translation-test: ## Run all pages-layout tests in all supported languages
	./bin/dev-shell ./bin/translation-test $${TESTFILES:-tests/pageslayout}

.PHONY: dev
dev: ## Run the dev server
	 DOCKER_RUN_ARGUMENTS='-p127.0.0.1:8080:8080 -p127.0.0.1:8081:8081 -p127.0.0.1:5901:5901' ./bin/dev-shell ./bin/run

.PHONY: update-user-guides
update-user-guides: ## Runs the page layout tests to regenerate screenshots
	./bin/dev-shell ./bin/update-user-guides

.PHONY: translate
translate: ## Update POT translation files from sources
	./bin/dev-shell ./i18n_tool.py translate-messages --extract-update
	./bin/dev-shell ./i18n_tool.py translate-desktop --extract-update

# For an explanation of this shell magic, see the Makefile in the root of the repository
.PHONY: help
help: ## Print this message and exit.
	@printf "Makefile for developing and testing SecureDrop.\n"
	@printf "Subcommands:\n\n"
	@awk 'BEGIN {FS = ":.*?## "} /^[0-9a-zA-Z_-]+:.*?## / {printf "\033[36m%s\033[0m : %s\n", $$1, $$2}' $(MAKEFILE_LIST) \
		| sort \
		| column -s ':' -t
