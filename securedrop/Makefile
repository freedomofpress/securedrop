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

.PHONY: test-python3
test-python3: ## Run the Python 3 test suite in a Ubuntu 16.04 (Xenial) dockerized environment
	PYTHON_VERSION=3 ./bin/dev-shell ./bin/run-test -v $${TESTFILES:-tests}

.PHONY: translation-test
translation-test: ## Run all pages-layout tests in all supported languages
	./bin/dev-shell ./bin/translation-test $${TESTFILES:-tests/pageslayout}

.PHONY: dev
dev: ## Run the dev server
	 DOCKER_RUN_ARGUMENTS='-p127.0.0.1:8080:8080 -p127.0.0.1:8081:8081' ./bin/dev-shell ./bin/run

config.py: test-config

.PHONY: test-config
test-config: ## Generate the test config
	@source_secret_key=$(shell head -c 32 /dev/urandom | base64) \
	journalist_secret_key=$(shell head -c 32 /dev/urandom | base64) \
	scrypt_id_pepper=$(shell head -c 32 /dev/urandom | base64) \
	scrypt_gpg_pepper=$(shell head -c 32 /dev/urandom | base64) \
	python -c 'import os; from jinja2 import Environment, FileSystemLoader; \
		 env = Environment(loader=FileSystemLoader(".")); \
		 ctx = {"securedrop_app_gpg_fingerprint": "65A1B5FF195B56353CC63DFFCC40EF1228271441"}; \
		 ctx.update(dict((k, {"stdout":v}) for k,v in os.environ.items())); \
		 ctx = open("config.py", "w").write(env.get_template("config.py.example").render(ctx))'
	@echo >> config.py
	@echo "SUPPORTED_LOCALES = ['ar', 'de_DE', 'es_ES', 'en_US', 'el', 'fr_FR', 'it_IT', 'nb_NO', 'nl', 'pt_BR', 'tr', 'zh_Hant']"  >> config.py

.PHONY: update-user-guides
update-user-guides: ## Runs the page layout tests to regenerate screenshots
	./bin/dev-shell ./bin/update-user-guides

.PHONY: translate
translate: ## Update POT translation files from sources
	./bin/dev-shell ./i18n_tool.py translate-messages --extract-update
	./bin/dev-shell ./i18n_tool.py translate-desktop --extract-update

.PHONY: docker-vnc
docker-vnc: ## Open up a VNC connection to a running docker instance
	../devops/scripts/vnc-docker-connect.sh

# For an explanation of this shell magic, see the Makefile in the root of the repository
.PHONY: help
help: ## Print this message and exit.
	@printf "Makefile for developing and testing SecureDrop.\n"
	@printf "Subcommands:\n\n"
	@awk 'BEGIN {FS = ":.*?## "} /^[0-9a-zA-Z_-]+:.*?## / {printf "\033[36m%s\033[0m : %s\n", $$1, $$2}' $(MAKEFILE_LIST) \
		| sort \
		| column -s ':' -t
