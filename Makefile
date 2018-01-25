DEFAULT_GOAL: help
SHELL := /bin/bash
PWD := $(shell pwd)
TAG ?= $(shell git rev-parse HEAD)

.PHONY: ci-spinup
ci-spinup: ## Creates AWS EC2 hosts for testing staging environment.
	./devops/scripts/ci-spinup.sh

.PHONY: ci-teardown
ci-teardown: ## Destroy AWS EC2 hosts for testing staging environment.
	./devops/scripts/ci-teardown.sh

.PHONY: ci-run
ci-run: ## Provisions AWS EC2 hosts for testing staging environment.
	./devops/scripts/ci-runner.sh

.PHONY: ci-go
ci-go: ## Creates, provisions, tests, and destroys AWS EC2 hosts for testing staging environment.
	@if [[ "${CIRCLE_BRANCH}" != docs-* ]]; then molecule test -s aws; else echo Not running on docs branch...; fi

.PHONY: ci-lint-image
ci-lint-image: ## Builds linting container.
	docker build $(EXTRA_BUILD_ARGS) -t securedrop-lint:${TAG} -f devops/docker/Dockerfile.linting .

.PHONY: ci-lint
ci-lint: ## Runs linting in linting container.
	docker run --rm -ti -v /var/run/docker.sock:/var/run/docker.sock securedrop-lint:${TAG}

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
	make -C docs/ clean && sphinx-autobuild `[ $(PWD) = /vagrant ] && echo '--host 0.0.0.0'` docs/ docs/_build/html

.PHONY: flake8
flake8: ## Validates PEP8 compliance for Python source files.
	flake8 --exclude='config.py' testinfra securedrop/securedrop-admin \
		securedrop/*.py securedrop/management \
		securedrop/journalist_app/*.py \
		securedrop/source_app/*.py securedrop/tests/pages-layout/*.py \
		securedrop/tests/functional/*.py securedrop/tests/*.py

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
# Prune the `.venv/` dir if it exists, since it contains pip-installed files
# and is not subject to our linting. Using grep to filter filepaths since
# `-regextype=posix-extended` is not cross-platform.
	@find "$(PWD)" -path "$(PWD)/.venv" -prune -o -type f \
		| grep -E '^.*\.ya?ml' | xargs yamllint -c "$(PWD)/.yamllint"

.PHONY: shellcheck
shellcheck: ## Lints Bash and sh scripts.
# Omitting the `.git/` directory since its hooks won't pass validation, and we
# don't maintain those scripts. Omitting the `.venv/` dir because we don't control
# files in there. Omitting the ossec packages because there are a LOT of violations,
# and we have a separate issue dedicated to cleaning those up.
	@docker create -v /mnt --name shellcheck-targets circleci/python:2 /bin/true 2> /dev/null || true
	@docker cp $(PWD)/. shellcheck-targets:/mnt/
	@find "." \( -path "./.venv" -o -path "./install_files/ossec-server" \
		-o -path "./install_files/ossec-agent" \) -prune \
		-o -type f -and -not -ipath '*/.git/*' -exec file --mime {} + \
		| perl -F: -lanE '$$F[1] =~ /x-shellscript/ and say $$F[0]' \
		| xargs docker run --rm --volumes-from shellcheck-targets \
		-t koalaman/shellcheck:v0.4.6 \
		-x --exclude=SC1091,SC2001,SC2064,SC2181

.PHONY: shellcheckclean
shellcheckclean: ## Cleans up temporary container associated with shellcheck target.
	@docker rm -f shellcheck-targets

.PHONY: lint
lint: docs-lint app-lint flake8 html-lint yamllint shellcheck ansible-config-lint ## Runs all linting tools (docs, pylint, flake8, HTML, YAML, shell, ansible-config).

.PHONY: docker-build-ubuntu
docker-build-ubuntu: ## Builds SD Ubuntu docker container
	@docker build -t quay.io/freedomofpress/ubuntu:trusty -f molecule/builder/Dockerfile molecule/builder

.PHONY: build-debs
build-debs: ## Builds and tests debian packages
	@if [[ "${CIRCLE_BRANCH}" != docs-* ]]; then molecule test -s builder; else echo Not running on docs branch...; fi

.PHONY: safety
safety: ## Runs `safety check` to check python dependencies for vulnerabilities
	@for req_file in `find . -type f -name '*requirements.txt'`; do \
		echo "Checking file $$req_file" \
		&& safety check --full-report -r $$req_file \
		&& echo -e '\n' \
		|| exit 1; \
	done

.PHONY: update-pip-requirements
update-pip-requirements: ## Updates all Python requirements files via pip-compile.
	pip-compile --generate-hashes --output-file securedrop/requirements/admin-requirements.txt \
		securedrop/requirements/ansible.in
	pip-compile --output-file securedrop/requirements/develop-requirements.txt \
		securedrop/requirements/ansible.in \
		securedrop/requirements/develop-requirements.in
	pip-compile --output-file securedrop/requirements/test-requirements.txt \
		securedrop/requirements/test-requirements.in
	pip-compile --output-file securedrop/requirements/securedrop-app-code-requirements.txt \
		securedrop/requirements/securedrop-app-code-requirements.in

.PHONY: libvirt-share
libvirt-share: ## Configure ACLs to allow RWX for libvirt VM (e.g. Admin Workstation)
	@find "$(PWD)" -type d -and -user $$USER -exec setfacl -m u:libvirt-qemu:rwx {} +
	@find "$(PWD)" -type f -and -user $$USER -exec setfacl -m u:libvirt-qemu:rw {} +

.PHONY: translate
translate: ## Update POT translation files from sources
	@cd securedrop ; ./manage.py translate-messages --extract-update
	@cd securedrop ; ./manage.py translate-desktop --extract-update

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
