DEFAULT_GOAL: help
TAG ?= $(shell git rev-parse HEAD)
IMAGE = securedrop

.PHONY: lint
lint: ## Run the python linter with the project's default error settings
	find . -name '*.py' | xargs pylint --reports=no --errors-only --disable=import-error

.PHONY: lint-full
lint-full:  ## Run the python linter with nothing disabled
	find . -name '*.py' | xargs pylint

.PHONY: images
images: ## Build the docker images
	docker build $(EXTRA_BUILD_ARGS) -f Dockerfile \
	   --build-arg=USER_ID=$(shell id -u) \
	   --build-arg=USER_NAME=$(USER) \
	   -t $(IMAGE)-test:$(TAG) .

TESTFILES ?= tests
.PHONY: test
test: ## Run the test suite in a dockerized environment
	docker run \
		-e COMMIT_SHA=$(TAG) \
		$(EXTRA_TEST_ARGS) \
		--name $(IMAGE)-test \
		-ti $(IMAGE)-test:$(TAG) \
		./bin/test -v $(TESTFILES)

.PHONY: testclean
testclean: ## Remove the docker test image
	-docker rm -f $(IMAGE)-test

.PHONY: dev
dev: ## Run the dev server
	./bin/dev-shell ./manage.py run

config.py: test-config

.PHONY: test-config
test-config: ## Generate the test config
	source_secret_key=$(shell head -c 32 /dev/urandom | base64) \
	journalist_secret_key=$(shell head -c 32 /dev/urandom | base64) \
	scrypt_id_pepper=$(shell head -c 32 /dev/urandom | base64) \
	scrypt_gpg_pepper=$(shell head -c 32 /dev/urandom | base64) \
	python -c 'import os; from jinja2 import Environment, FileSystemLoader; \
         env = Environment(loader=FileSystemLoader(".")); \
         ctx = {"securedrop_app_gpg_fingerprint": "65A1B5FF195B56353CC63DFFCC40EF1228271441"}; \
         ctx.update(dict((k, {"stdout":v}) for k,v in os.environ.iteritems())); \
         ctx = open("config.py", "w").write(env.get_template("config.py.example").render(ctx))'

.PHONY: update-user-guides
update-user-guides: ## Runs the page layout tests to regenerate screenshots
	docker run \
		--name $(IMAGE)-update-user-guides \
		--rm \
		-e USER_ID=$(shell id -u) \
		-v $(shell git rev-parse --show-toplevel):$(shell git rev-parse --show-toplevel) \
		-w $(shell pwd) \
		-ti $(IMAGE)-test:$(TAG) \
		./bin/update-user-guides

# For an explanation of this shell magic, see the Makefile in the root of the repository
.PHONY: help
help: ## Print this message and exit.
	@printf "Makefile for developing and testing SecureDrop.\n"
	@printf "Subcommands:\n\n"
	@awk 'BEGIN {FS = ":.*?## "} /^[0-9a-zA-Z_-]+:.*?## / {printf "\033[36m%s\033[0m : %s\n", $$1, $$2}' $(MAKEFILE_LIST) \
		| sort \
		| column -s ':' -t
