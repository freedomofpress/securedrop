DATE_STR := $(shell date +"%Y_%m_%d")
BUILDER_IMAGE ?= "quay.io/freedomofpress/sd-docker-builder-xenial:$(DATE_STR)"

.PHONY: build-container
build-container: ## Build Docker image for Debian package creation
	@echo "███Building Docker image $(BUILDER_IMAGE) for Debian package creation..."
	@docker build --no-cache -t $(BUILDER_IMAGE) .

.PHONY: push-container
push-container: ## Push the Docker image for Debian package creation to quay.io
	@echo "███Pushing Docker image for Debian package creation to quay.io..."
	@./push.sh

.PHONY: help
help: ## Print this message and exit.
	@printf "Molecule scenario for building a Docker container for Debian package creation.\n"
	@printf "Subcommands:\n\n"
	@awk 'BEGIN {FS = ":.*?## "} /^[0-9a-zA-Z_-]+:.*?## / {printf "\033[36m%s\033[0m : %s\n", $$1, $$2}' $(MAKEFILE_LIST) \
		| sort \
		| column -s ':' -t
