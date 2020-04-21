DEFAULT_GOAL: help

.PHONY: lint
lint: ## Run all linters
	@echo "\n    ►►► securedrop/Makefile is deprecated. Run 'make lint' in the repo root. ◀◀◀\n"
	make -C .. lint

.PHONY: lint-full
lint-full:  ## Run the python linter with nothing disabled
	@echo "\n    ►►► securedrop/Makefile is deprecated. Run 'make app-lint-full' in the repo root. ◀◀◀\n"
	make -C .. app-lint-full

.PHONY: test
test: ## Run the test suite in a Ubuntu 16.04 (Xenial) dockerized environment
	@echo "\n    ►►► securedrop/Makefile is deprecated. Run 'make $@' in the repo root. ◀◀◀\n"
	make -C .. $@

.PHONY: translation-test
translation-test: ## Run all pages-layout tests in all supported languages
	@echo "\n    ►►► securedrop/Makefile is deprecated. Run 'make $@' in the repo root. ◀◀◀\n"
	make -C .. $@

.PHONY: list-translators
list-translators: ## Collect the names of translators since the last merge from Weblate
	@echo "\n    ►►► securedrop/Makefile is deprecated. Run 'make $@' in the repo root. ◀◀◀\n"
	make -C .. $@


.PHONY: list-all-translators
list-all-translators: ## Collect the names of all translators in the project's history
	@echo "\n    ►►► securedrop/Makefile is deprecated. Run 'make $@' in the repo root. ◀◀◀\n"
	make -C .. $@


.PHONY: dev
dev: ## Run the dev server
	@echo "\n    ►►► securedrop/Makefile is deprecated. Run 'make $@' in the repo root. ◀◀◀\n"
	make -C .. $@

config.py: test-config

.PHONY: test-config
test-config: ## Generate the test config
	@echo "\n    ►►► securedrop/Makefile is deprecated. Run 'make $@' in the repo root. ◀◀◀\n"
	make -C .. $@

.PHONY: update-user-guides
update-user-guides: ## Runs the page layout tests to regenerate screenshots
	@echo "\n    ►►► securedrop/Makefile is deprecated. Run 'make $@' in the repo root. ◀◀◀\n"
	make -C .. $@

.PHONY: translate
translate: ## Update POT translation files from sources
	@echo "\n    ►►► securedrop/Makefile is deprecated. Run 'make $@' in the repo root. ◀◀◀\n"
	make -C .. $@

.PHONY: docker-vnc
docker-vnc: ## Open up a VNC connection to a running docker instance
	@echo "\n    ►►► securedrop/Makefile is deprecated. Run 'make $@' in the repo root. ◀◀◀\n"
	make -C .. $@

# For an explanation of this shell magic, see the Makefile in the root of the repository
.PHONY: help
help: ## Print this message and exit.
	@echo "\n    ►►► securedrop/Makefile is deprecated. Run 'make $@' in the repo root. ◀◀◀\n"

	@printf "Makefile for developing and testing SecureDrop. ◀◀◀\n"
	@printf "Subcommands:\n ◀◀◀\n"
	@awk 'BEGIN {FS = ":.*?## "} /^[0-9a-zA-Z_-]+:.*?## / {printf "\033[36m%s\033[0m : %s ◀◀◀\n", $$1, $$2}' $(MAKEFILE_LIST) \
		| sort \
		| column -s ':' -t
