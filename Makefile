DEFAULT_GOAL: help
SHELL := /bin/bash
GCLOUD_VERSION := 222.0.0-1
PWD := $(shell pwd)
TAG ?= $(shell git rev-parse HEAD)
STABLE_VER := $(shell cat molecule/shared/stable.ver)

.PHONY: ci-go
ci-go: ## Creates, provisions, tests, and destroys GCE host for testing staging environment.
	./devops/gce-nested/ci-go.sh

.PHONY: ci-teardown
ci-teardown: ## Destroys GCE host for testing staging environment.
	./devops/gce-nested/gce-stop.sh

.PHONY: ci-lint
ci-lint: ## Runs linting in linting container.
	devops/scripts/dev-shell-ci run make --keep-going lint typelint

.PHONY: ci-deb-tests
ci-deb-tests: ## Runs deb tests in ci
	@./devops/scripts/test-built-packages.sh

.PHONY: install-mypy
install-mypy: ## pip install mypy in a dedicated python3 virtualenv
	if [[ ! -d .python3/.venv ]] ; then \
	  virtualenv --python=python3 .python3/.venv && \
	  .python3/.venv/bin/pip3 install mypy ; \
	fi

.PHONY: typelint
typelint: install-mypy ## Runs type linting
	.python3/.venv/bin/mypy ./securedrop ./admin
	.python3/.venv/bin/mypy --disallow-incomplete-defs --disallow-untyped-defs ./securedrop/rm.py

.PHONY: ansible-config-lint
ansible-config-lint: ## Runs custom Ansible env linting tasks.
	molecule verify -s ansible-config

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
	flake8

.PHONY: app-lint
app-lint: ## Tests pylint lint rule compliance.
	cd securedrop && make lint

# The --disable=names is required to use the BEM syntax
# # https://csswizardry.com/2013/01/mindbemding-getting-your-head-round-bem-syntax/
.PHONY: html-lint
html-lint: ## Validates HTML in web application template files.
	html_lint.py --printfilename --disable=optional_tag,extra_whitespace,indentation,names \
		securedrop/source_templates/*.html securedrop/journalist_templates/*.html

.PHONY: yamllint
yamllint: ## Lints YAML files (does not validate syntax!)
	./devops/scripts/yaml-lint.sh

.PHONY: shellcheck
shellcheck: ## Lints Bash and sh scripts.
	./devops/scripts/shellcheck.sh

.PHONY: shellcheckclean
shellcheckclean: ## Cleans up temporary container associated with shellcheck target.
	@docker rm -f shellcheck-targets

.PHONY: lint
lint: docs-lint app-lint flake8 html-lint yamllint shellcheck ansible-config-lint ## Runs all linting tools (docs, pylint, flake8, HTML, YAML, shell, ansible-config).

.PHONY: build-debs
build-debs: ## Builds and tests debian packages
	@./devops/scripts/build-debs.sh

.PHONY: build-debs-notest
build-debs-notest: ## Builds and tests debian packages (sans tests)
	@./devops/scripts/build-debs.sh notest

.PHONY: build-gcloud-docker
build-gcloud-docker: ## Build docker container for gcloud sdk
	echo "${GCLOUD_VERSION}" > devops/gce-nested/gcloud-container.ver && \
	docker build --build-arg="GCLOUD_VERSION=${GCLOUD_VERSION}" \
				 -f devops/docker/Dockerfile.gcloud \
				 -t "quay.io/freedomofpress/gcloud-sdk:${GCLOUD_VERSION}" .

.PHONY: safety
safety: ## Runs `safety check` to check python dependencies for vulnerabilities
	pip install --upgrade safety && \
		for req_file in `find . -type f -name '*requirements.txt'`; do \
			echo "Checking file $$req_file" \
			&& safety check --full-report -r $$req_file \
			&& echo -e '\n' \
			|| exit 1; \
		done
# Bandit is a static code analysis tool to detect security vulnerabilities in Python applications
# https://wiki.openstack.org/wiki/Security/Projects/Bandit
.PHONY: bandit
bandit: ## Run bandit with medium level excluding test-related folders
	pip install --upgrade pip && \
        pip install --upgrade bandit!=1.6.0 && \
	bandit --recursive . --exclude admin/.tox,admin/.venv,admin/.eggs,molecule,testinfra,securedrop/tests,.tox,.venv -ll

.PHONY: update-pip-requirements
update-pip-requirements: ## Updates all Python requirements files via pip-compile.
	make -C admin update-pip-requirements
	pip-compile --output-file securedrop/requirements/develop-requirements.txt \
		admin/requirements-ansible.in \
		securedrop/requirements/develop-requirements.in
	pip-compile --output-file securedrop/requirements/test-requirements.txt \
		securedrop/requirements/test-requirements.in
	pip-compile --output-file securedrop/requirements/securedrop-app-code-requirements.txt \
		securedrop/requirements/securedrop-app-code-requirements.in

.PHONY: libvirt-share
libvirt-share: ## Configure ACLs to allow RWX for libvirt VM (e.g. Admin Workstation)
	@find "$(PWD)" -type d -and -user $$USER -exec setfacl -m u:libvirt-qemu:rwx {} +
	@find "$(PWD)" -type f -and -user $$USER -exec setfacl -m u:libvirt-qemu:rw {} +

.PHONY: self-signed-https-certs
self-signed-https-certs: ## Generates self-signed certs for TESTING the HTTPS config
	@echo "Generating self-signed HTTPS certs for testing..."
	@./devops/generate-self-signed-https-certs.sh

.PHONY: vagrant-package
vagrant-package: ## Package up a vagrant box of the last stable SD release
	@devops/scripts/vagrant-package

.PHONY: staging
staging: ## Creates local staging environment in VM, autodetecting platform
	@./devops/scripts/create-staging-env

.PHONY: clean
clean: ## DANGER! Purges all site-specific info and developer files from project.
	@./devops/clean

# Xenial upgrade targets
.PHONY: upgrade-start
upgrade-start: ## Boot up an upgrade test base environment using libvirt
	@SD_UPGRADE_BASE=$(STABLE_VER) molecule converge -s upgrade

.PHONY: upgrade-start-qa
upgrade-start-qa: ## Boot up an upgrade test base env using libvirt in remote apt mode
	@SD_UPGRADE_BASE=$(STABLE_VER) QA_APTTEST=yes molecule converge -s upgrade

.PHONY: upgrade-destroy
upgrade-destroy: ## Destroy up an upgrade test base environment
	@SD_UPGRADE_BASE=$(STABLE_VER) molecule destroy -s upgrade

.PHONY: upgrade-test-local
upgrade-test-local: ## Once an upgrade environment is running, force upgrade apt packages (local pkgs)
	@molecule side-effect -s upgrade

.PHONY: upgrade-test-qa
upgrade-test-qa: ## Once an upgrade environment is running, force upgrade apt packages (from qa server)
	@QA_APTTEST=yes molecule converge -s upgrade -- --diff -t apt
	@QA_APTTEST=yes molecule side-effect -s upgrade

.PHONY: fetch-tor-packages
fetch-tor-packages: ## Retrieves the most recent Tor packages for Xenial, for apt repo
	@./devops/scripts/fetch-tor-packages.sh

# Explaination of the below shell command should it ever break.
# 1. Set the field separator to ": ##" and any make targets that might appear between : and ##
# 2. Use sed-like syntax to remove the make targets
# 3. Format the split fields into $$1) the target name (in blue) and $$2) the target descrption
# 4. Pass this file as an arg to awk
# 5. Sort it alphabetically
# 6. Format columns with colon as delimiter.
.PHONY: help
help: ## Print this message and exit.
	@printf "Makefile for developing and testing SecureDrop.\n"
	@printf "Subcommands:\n\n"
	@awk 'BEGIN {FS = ":.*?## "} /^[0-9a-zA-Z_-]+:.*?## / {printf "\033[36m%s\033[0m : %s\n", $$1, $$2}' $(MAKEFILE_LIST) \
		| sort \
		| column -s ':' -t
