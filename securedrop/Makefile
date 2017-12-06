TAG ?= $(shell git rev-parse HEAD)
IMAGE = securedrop

.PHONY: assets
assets:
	sass

.PHONY: images
images:
	docker build $(EXTRA_BUILD_ARGS) -f Dockerfile -t $(IMAGE)-test:$(TAG) .

.PHONY: test
test:
	docker run --privileged \
		-e COMMIT_SHA=$(TAG) \
		$(EXTRA_TEST_ARGS) \
		--name $(IMAGE)-test \
		-ti $(IMAGE)-test:$(TAG) \
		./test -v $(TESTFILES)

.PHONY: testclean
testclean:
	-docker rm -f $(IMAGE)-test

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
