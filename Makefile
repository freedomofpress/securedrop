.PHONY: ci-spinup
ci-spinup:
	./devops/scripts/ci-spinup.sh

.PHONY: ci-teardown
ci-teardown:
	./devops/scripts/ci-teardown.sh

.PHONY: ci-run
ci-run:
	./devops/scripts/ci-runner.sh

# Run SpinUP, Playbooks, and Testinfra
.PHONY: ci-go
ci-go:
	./devops/scripts/spin-run-test.sh

.PHONY: ci-test
ci-test:
	./devops/scripts/spin-run-test.sh only_test

.PHONY: ci-debug
ci-debug:
	touch ${HOME}/.FPF_CI_DEBUG

.PHONY: ci-build-only
ci-build-only:
	./devops/scripts/ci-build_only.sh

.PHONY: docs-lint
docs-lint:
# The `-W` option converts warnings to errors.
# The `-n` option enables "nit-picky" mode.
	make -C docs/ clean && sphinx-build -Wn docs/ docs/_build/html

.PHONY: docs
docs:
# Spins up livereload environment for editing; blocks.
	make -C docs/ clean && sphinx-autobuild docs/ docs/_build/html

help:
	@echo Makefile for developing and testing SecureDrop.
	@echo Subcommands:
	@echo "\t docs: Build project documentation in live reload for editing."
	@echo "\t docs-lint: Check documentation for common syntax errors."
	@echo "\t ci-spinup: Creates AWS EC2 hosts for testing staging environment."
	@echo "\t ci-teardown: Destroy AWS EC2 hosts for testing staging environment."
	@echo "\t ci-run: Provisions AWS EC2 hosts for testing staging environment."
	@echo "\t ci-test: Tests AWS EC2 hosts for testing staging environment."
	@echo "\t ci-go: Creates, provisions, tests, and destroys AWS EC2 hosts"
	@echo "\t        for testing staging environment."
	@echo "\t ci-build-only: Kicks off build logic and pulls back deb files."
	@echo "\t ci-debug: Prevents automatic destruction of AWS EC2 hosts on error."
