TAG ?= $(shell git rev-parse HEAD)
IMAGE = securedrop

.PHONY: lint
lint:
	find . -name '*.py' | xargs pylint --reports=no --errors-only --disable=import-error

.PHONY: lint-full
lint-full:
	find . -name '*.py' | xargs pylint

.PHONY: assets
assets:
	sass

.PHONY: images
images:
	find . -name '*.pyc' | xargs --no-run-if-empty rm
	docker build $(EXTRA_BUILD_ARGS) -f Dockerfile -t $(IMAGE)-test:$(TAG) .

TESTFILES ?= tests
.PHONY: test
test:
	docker run \
		-e COMMIT_SHA=$(TAG) \
		$(EXTRA_TEST_ARGS) \
		--name $(IMAGE)-test \
		-ti $(IMAGE)-test:$(TAG) \
		./bin/test -v $(TESTFILES)

.PHONY: testclean
testclean:
	-docker rm -f $(IMAGE)-test

.PHONY: dev
dev:
	docker run \
		-p8080:8080 -p8081:8081 \
		$(EXTRA_DEV_ARGS) \
		-v $(shell pwd):/app \
		--rm \
		-ti $(IMAGE)-test:$(TAG) \
		./bin/dev

.PHONY: dev-shell
dev-shell:
	docker run \
		-p8080:8080 -p8081:8081 \
		$(EXTRA_DEV_ARGS) \
		-v $(shell pwd):/app \
		-ti $(IMAGE)-test:$(TAG) \
		bash

config.py: test-config

.PHONY: test-config
test-config:
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
update-user-guides:
	docker run \
		--name $(IMAGE)-update-user-guides \
		--rm \
		-e USER_ID=$(shell id -u) \
		-v $(shell git rev-parse --show-toplevel):$(shell git rev-parse --show-toplevel) \
		-w $(shell pwd) \
		-ti $(IMAGE)-test:$(TAG) \
		./bin/update-user-guides
