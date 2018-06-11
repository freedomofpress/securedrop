DATE_STR := $(shell date +"%Y_%m_%d")

.PHONY: build-container
build-container: ## Build container utilized for debian pkg building
	docker build --no-cache -t quay.io/freedomofpress/sd-docker-builder:$(DATE_STR) .

.PHONY: push-container
push-container: ## Push todays labeled build image to quay
	@./push.sh

.PHONY: help
help: ## Print this message and exit.
	@printf "Molecule scenario for building container that handles deb creation.\n"
	@printf "Subcommands:\n\n"
	@awk 'BEGIN {FS = ":.*?## "} /^[0-9a-zA-Z_-]+:.*?## / {printf "\033[36m%s\033[0m : %s\n", $$1, $$2}' $(MAKEFILE_LIST) \
		| sort \
		| column -s ':' -t
