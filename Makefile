DEFAULT_GOAL: help
SHELL := /bin/bash
GCLOUD_VERSION := 222.0.0-1
SDROOT := $(shell git rev-parse --show-toplevel)
TAG ?= $(shell git rev-parse HEAD)
STABLE_VER := $(shell cat molecule/shared/stable.ver)

SDBIN := $(SDROOT)/securedrop/bin
DEVSHELL := $(SDBIN)/dev-shell


######################################
#
# Python environments and dependencies
#
######################################

.PHONY: venv
venv: hooks  ## Provision a Python 3 virtualenv for development.
	@echo "███ Preparing Python 3 virtual environment..."
	@$(SDROOT)/devops/scripts/boot-strap-venv.sh
	@echo "Make sure to run: source .venv/bin/activate"
	@echo

.PHONY: update-admin-pip-requirements
update-admin-pip-requirements:  ## Update admin requirements.
	@make -s -C admin update-pip-requirements

.PHONY: update-python3-requirements
update-python3-requirements:  ## Update Python 3 requirements with pip-compile.
	@echo "███ Updating Python 3 requirements files..."
	@SLIM_BUILD=1 $(DEVSHELL) pip-compile --generate-hashes \
		--allow-unsafe \
		--output-file requirements/python3/develop-requirements.txt \
		../admin/requirements-ansible.in \
		../admin/requirements.in \
		requirements/python3/develop-requirements.in
	@SLIM_BUILD=1 $(DEVSHELL) pip-compile --generate-hashes \
		--allow-unsafe \
		--output-file requirements/python3/test-requirements.txt \
		requirements/python3/test-requirements.in
	@SLIM_BUILD=1 $(DEVSHELL) pip-compile --generate-hashes \
				--allow-unsafe \
		--output-file requirements/python3/requirements.txt \
		requirements/python3/requirements.in
	@SLIM_BUILD=1 $(DEVSHELL) pip-compile --generate-hashes \
		--allow-unsafe \
		--output-file requirements/python3/bootstrap-requirements.txt \
		requirements/python3/bootstrap-requirements.in
	@SLIM_BUILD=1 $(DEVSHELL) pip-compile --generate-hashes \
		--allow-unsafe \
		--output-file requirements/python3/translation-requirements.txt \
		requirements/python3/translation-requirements.in

.PHONY: update-pip-requirements
update-pip-requirements: update-admin-pip-requirements update-python3-requirements ## Update all requirements with pip-compile.


#################
#
# Static analysis
#
#################

.PHONY: check-black
check-black: ## Check Python source code formatting with black
	@echo "███ Running black check..."
	@black --check --diff .
	@echo

.PHONY: black
black: ## Update Python source code formatting with black
	@black securedrop .

.PHONY: check-isort
check-isort: ## Check Python import organization with isort
	@echo "███ Running isort check..."
	@isort --check-only --diff .
	@echo

.PHONY: isort
isort: ## Update Python import organization with isort
	@isort .

.PHONY: ansible-config-lint
ansible-config-lint: ## Run custom Ansible linting tasks.
	@echo "███ Linting Ansible configuration..."
	@molecule verify -s ansible-config
	@echo

.PHONY: app-lint
app-lint:  ## Test pylint compliance.
	@echo "███ Linting application code..."
	@cd securedrop && find . -name '*.py' -or -path './scripts/*' | xargs pylint --reports=no --errors-only \
	   --disable=no-name-in-module \
	   --disable=import-error \
	   --disable=no-member \
	   --max-line-length=100
	@echo

.PHONY: app-lint-full
app-lint-full: ## Test pylint compliance, with no checks disabled.
	@echo "███ Linting application code with no checks disabled..."
	@cd securedrop && find . -name '*.py' -or -path './scripts/*' | xargs pylint
	@echo

.PHONY: flake8
flake8:  ## Validate PEP8 compliance for Python source files.
	@echo "███ Running flake8..."
	@flake8
	@echo

# The --disable=names is required to use the BEM syntax
# # https://csswizardry.com/2013/01/mindbemding-getting-your-head-round-bem-syntax/
.PHONY: html-lint
html-lint:  ## Validate HTML in web application template files.
	@echo "███ Linting application templates..."
	@html_lint.py --printfilename --disable=optional_tag,extra_whitespace,indentation,names,quotation \
		securedrop/source_templates/*.html securedrop/journalist_templates/*.html
	@echo

.PHONY: shellcheck
shellcheck:  ## Lint shell scripts.
	@echo "███ Linting shell scripts..."
	@$(SDROOT)/devops/scripts/shellcheck.sh
	@echo

.PHONY: typelint
typelint:  ## Run mypy type linting.
	@echo "███ Running mypy type checking..."
	@$(SDROOT)/securedrop/bin/run-mypy
	@echo

.PHONY: yamllint
yamllint:  ## Lint YAML files (does not validate syntax!).
	@echo "███ Linting YAML files..."
	@yamllint --strict .
	@echo

.PHONY: lint
lint: ansible-config-lint app-lint check-black check-isort flake8 html-lint shellcheck typelint yamllint ## Runs all lint checks

.PHONY: safety
safety:  ## Run `safety check` to check python dependencies for vulnerabilities.
	@command -v safety || (echo "Please run 'pip install -U safety'."; exit 1)
	@echo "███ Running safety..."
	@for req_file in `find . -type f -name '*requirements.txt'`; do \
		echo "Checking file $$req_file" \
		&& safety check \
		--ignore 42050 \
		--ignore 42926 \
		--ignore 42923 \
		--ignore 45185 \
		--ignore 49337 \
		--ignore 51668 \
		--ignore 52322 \
                --ignore 52495 \
                --ignore 52510 \
                --ignore 52518 \
		--full-report -r $$req_file \
		&& echo -e '\n' \
		|| exit 1; \
	done
	@echo

# Bandit is a static code analysis tool to detect security vulnerabilities in Python applications
# https://wiki.openstack.org/wiki/Security/Projects/Bandit
.PHONY: bandit

bandit: test-config ## Run bandit with medium level excluding test-related folders.
	@command -v bandit || (echo "Please run 'pip install -U bandit'."; exit 1)
	@echo "███ Running bandit..."
	@bandit -ll --exclude ./admin/.tox,./admin/.venv,./admin/.eggs,./molecule,./testinfra,./securedrop/tests,./.tox,./.venv*,securedrop/config.py --recursive .
	@echo "███ Running bandit on securedrop/config.py..."
	@bandit -ll --skip B108 securedrop/config.py
	@echo


# Semgrep is a static code analysis tool to detect security vulnerabilities in Python applications
# This configuration uses the public "p/r2c-security-audit" ruleset
.PHONY: semgrep
semgrep:
	@command -v semgrep || (echo "Please run 'pip install -U semgrep'."; exit 1)
	@echo "███ Running semgrep on securedrop/..."
	@semgrep --exclude "securedrop/tests/" --error --strict --metrics off --max-chars-per-line 200 --verbose --config "p/r2c-security-audit" securedrop
	@echo

#############
#
# Development
#
#############

securedrop/config.py: ## Generate the test SecureDrop application config.
	@echo "███ Generating securedrop/config.py..."
	@cd securedrop && source_secret_key=$(shell head -c 32 /dev/urandom | base64) \
	journalist_secret_key=$(shell head -c 32 /dev/urandom | base64) \
	scrypt_id_pepper=$(shell head -c 32 /dev/urandom | base64) \
	scrypt_gpg_pepper=$(shell head -c 32 /dev/urandom | base64) \
	python -c 'import os; from jinja2 import Environment, FileSystemLoader; \
		 env = Environment(loader=FileSystemLoader(".")); \
		 ctx = {"securedrop_app_gpg_fingerprint": "65A1B5FF195B56353CC63DFFCC40EF1228271441"}; \
		 ctx.update(dict((k, {"stdout":v}) for k,v in os.environ.items())); \
		 ctx = open("config.py", "w").write(env.get_template("config.py.example").render(ctx))'
	@echo >> securedrop/config.py
	@echo "SUPPORTED_LOCALES = $$(if test -f /opt/venvs/securedrop-app-code/bin/python3; then ./securedrop/i18n_tool.py list-locales --python; else DOCKER_BUILD_VERBOSE=false $(DEVSHELL) ./i18n_tool.py list-locales --python; fi)" | sed 's/\r//' >> securedrop/config.py
	@echo

HOOKS_DIR=.githooks

.PHONY: hooks
hooks:  ## Configure Git to use the hooks provided by this repository
	git config core.hooksPath "$(HOOKS_DIR)"

.PHONY: test-config
test-config: securedrop/config.py

.PHONY: dev
dev:  ## Run the development server in a Docker container.
	@echo "███ Starting development server..."
	@OFFSET_PORTS='false' DOCKER_BUILD_VERBOSE='true' SLIM_BUILD=1 $(DEVSHELL) $(SDBIN)/run
	@echo

.PHONY: dev-tor
dev-tor:  ## Run the development server with onion services in a Docker container.
	@echo "███ Starting development server with onion services..."
	@OFFSET_PORTS='false' DOCKER_BUILD_VERBOSE='true' USE_TOR='true' SLIM_BUILD=1 $(DEVSHELL) $(SDBIN)/run
	@echo

.PHONY: demo-landing-page
demo-landing-page: ## Serve the landing page for the SecureDrop demo
	@echo "███ Building Docker image..."
	docker build -t sd-demo-landing-page -f devops/demo/landing-page/Dockerfile .
	@echo "███ Running container and serving on port 8000..."
	docker run -p 8000:8000 sd-demo-landing-page

.PHONY: staging
staging:  ## Create a local staging environment in virtual machines (Focal)
	@echo "███ Creating staging environment on Ubuntu Focal..."
	@$(SDROOT)/devops/scripts/create-staging-env focal
	@echo

.PHONY: testinfra
testinfra:  ## Run infra tests against a local staging environment.
	@echo "███ Creating staging environment..."
	@MOLECULE_ACTION=verify $(SDROOT)/devops/scripts/create-staging-env
	@echo

.PHONY: self-signed-https-certs
self-signed-https-certs:  ## Generate self-signed certs for testing the HTTPS config.
	@echo "███ Generating self-signed HTTPS certs for testing..."
	@$(SDROOT)/devops/generate-self-signed-https-certs.sh
	@echo

.PHONY: clean
clean:  ## DANGER! Delete all uncommitted files, virtual machines, Onion addresses, etc.
	@$(SDROOT)/devops/clean
	@echo

.PHONY: otp
otp: ## Show (and opportunistically copy) the current development OTP (to the clipboard)
	@$(SDROOT)/devops/scripts/otp-code.sh

#########
#
# Testing
#
#########

.PHONY: test
test:  ## Run the test suite in a Docker container.
	@echo "███ Running SecureDrop application tests..."
	@$(DEVSHELL) $(SDBIN)/run-test -v $${TESTFILES:-tests}
	@echo

.PHONY: test-focal
test-focal:  test

.PHONY: validate-test-html
validate-test-html:
	@echo "███ Validating HTML source from $(shell find securedrop/tests/functional/pageslayout/html -name "*.html" | wc -l | xargs echo -n) page-layout test(s)"
	@$(DEVSHELL) html5validator tests/functional/pageslayout/html
	@echo

.PHONY: accessibility-summary
accessibility-summary:
	@echo "███ Processing accessibility results..."
	@$(DEVSHELL) $(SDBIN)/summarize-accessibility-info
	cat securedrop/tests/functional/pageslayout/accessibility-info/summary.txt

.PHONY: docker-vnc
docker-vnc:  ## Open a VNC connection to a running Docker instance.
	@echo "███ Opening VNC connection to dev container..."
	@$(SDROOT)/devops/scripts/vnc-docker-connect.sh
	@echo

.PHONY: upgrade-start
upgrade-start:  ## Create a local apt server for testing upgrades in VMs
	@echo "███ Starting upgrade test environment..."
	molecule converge -s upgrade
	@echo

.PHONY: upgrade-destroy
upgrade-destroy:  ## Destroy an upgrade test environment.
	@echo "███ Destroying upgrade test environment..."
	molecule destroy -s upgrade
	@echo

##############
#
# Localization
#
##############

.PHONY: translate
translate:  ## Update POT files from translated strings in source code.
	@echo "Updating translations..."
	@$(DEVSHELL) $(SDROOT)/securedrop/i18n_tool.py translate-messages --extract-update
	@$(DEVSHELL) $(SDROOT)/securedrop/i18n_tool.py translate-desktop --extract-update
	@echo

.PHONY: translation-test
translation-test:  ## Run page layout tests in all supported languages.
	@echo "Running translation tests..."
	@$(DEVSHELL) $(SDBIN)/translation-test $${LOCALES}
	@echo

.PHONY: list-translators
list-translators:  ## Collect the names of translators since the last merge from Weblate.
	@$(DEVSHELL) $(SDROOT)/securedrop/i18n_tool.py list-translators

.PHONY: list-all-translators
list-all-translators:  ## Collect the names of all translators in the project's history.
	@$(DEVSHELL) $(SDROOT)/securedrop/i18n_tool.py list-translators --all

.PHONY: update-user-guides
update-user-guides:  ## Regenerate docs screenshots. Set DOCS_REPO_DIR to repo checkout root.
ifndef DOCS_REPO_DIR
	$(error DOCS_REPO_DIR must be set to the documentation repo checkout root.)
endif
	@echo "Running page layout tests to update screenshots used in user guide..."
	@$(DEVSHELL) $(SDBIN)/generate-docs-screenshots
	@echo "Copying screenshots..."
	cp securedrop/tests/functional/pageslayout/screenshots/en_US/*.png $${DOCS_REPO_DIR}/docs/images/manual/screenshots
	@echo


###########
#
# Packaging
#
###########

.PHONY: build-debs
build-debs: ## Build and test SecureDrop Debian packages
	@echo "Building SecureDrop Debian packages..."
	@$(SDROOT)/builder/build-debs.sh
	@echo

.PHONY: build-debs-notest
build-debs-notest: ## Build SecureDrop Debian packages without running tests.
	@echo "Building SecureDrop Debian packages, skipping tests..."
	@NOTEST=1 $(SDROOT)/builder/build-debs.sh
	@echo

.PHONY: build-debs-ossec
build-debs-ossec: ## Build OSSEC Debian packages
	@echo "Building OSSEC Debian packages"
	@WHAT=ossec $(SDROOT)/builder/build-debs.sh
	@echo

.PHONY: build-debs-ossec-notest
build-debs-ossec-notest: ## Build OSSEC Debian packages without running tests
	@echo "Building OSSEC Debian packages, skipping tests..."
	@NOTEST=1 WHAT=ossec $(SDROOT)/builder/build-debs.sh
	@echo


########################
#
# Continuous integration
#
########################

.PHONY: ci-go
ci-go:  ## Create, provision, test, and destroy GCE host for testing staging environment.
	@echo "███ Creating GCE host for testing staging environment..."
	@$(SDROOT)/devops/gce-nested/ci-go.sh
	@echo

.PHONY: ci-teardown
ci-teardown:  ## Destroy GCE host for testing staging environment.
	@echo "███ Destroying GCE host for testing staging environment..."
	@$(SDROOT)/devops/gce-nested/gce-stop.sh
	@echo

.PHONY: ci-deb-tests
ci-deb-tests:  ## Test SecureDrop Debian packages in CI environment.
	@echo "███ Running Debian package tests in CI..."
	@$(SDROOT)/devops/scripts/test-built-packages.sh
	@echo

.PHONY: build-gcloud-docker
build-gcloud-docker:  ## Build Docker container for Google Cloud SDK.
	@echo "Building Docker container for Google Cloud SDK..."
	@echo "${GCLOUD_VERSION}" > devops/gce-nested/gcloud-container.ver && \
	@docker build --build-arg="GCLOUD_VERSION=${GCLOUD_VERSION}" \
				 -f devops/docker/Dockerfile.gcloud \
				 -t "quay.io/freedomofpress/gcloud-sdk:${GCLOUD_VERSION}" .
	@echo

.PHONY: vagrant-package
vagrant-package:  ## Package a Vagrant box of the last stable SecureDrop release.
	@echo "███ Packaging Vagrant box of last stable SecureDrop release."
	@devops/scripts/vagrant-package
	@echo

# Explanation of the below shell command should it ever break.
# 1. Set the field separator to ":  ##" and any make targets that might appear between : and ##
# 2. Use sed-like syntax to remove the make targets
# 3. Format the split fields into $$1) the target name (in blue) and $$2) the target description
# 4. Pass this file as an arg to awk
# 5. Sort it alphabetically
# 6. Format columns with colon as delimiter.
.PHONY: help
help:  ## Print this message and exit.
	@printf "Makefile for developing and testing SecureDrop.\n"
	@printf "Subcommands:\n\n"
	@awk 'BEGIN {FS = ":.*?## "} /^[0-9a-zA-Z_-]+:.*?## / {printf "\033[36m%s\033[0m : %s\n", $$1, $$2}' $(MAKEFILE_LIST) \
		| sort \
		| column -s ':' -t
