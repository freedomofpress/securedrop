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
