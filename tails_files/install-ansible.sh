#!/bin/bash
#
#
# Setup virtualenv environment and install ansible

export ANSIBLE_BASE="install_files/ansible-base"

setup_python_deps() {
	which virtualenv &> /dev/null || sudo su -c "echo '### Downloading depedencies'; \
						     apt-get update && \
						     apt-get install -y \
						     python-virtualenv \
						     python-pip \
						     ccontrol \
						     virtualenv \
                             libffi-dev \
						     libssl-dev \
						     libpython2.7-dev"
}

setup_ansible() {
	if [ ! -d ./.venv/bin/activate ]; then
		virtualenv &> /dev/null || setup_python_deps
		torify virtualenv .venv
	fi

	. ./.venv/bin/activate
    torify pip install -r "$ANSIBLE_BASE/requirements.txt" --require-hashes
	echo "SD pre-reqs successfully installed/updated"
}


ls .venv/bin/ansible &> /dev/null
if [ "$?" == "0" ]; then
	if [ "$1" == "update" ]; then
		. ./.venv/bin/activate && torify pip install -U -r install_files/ansible-base/requirements.txt --require-hashes
	else
		echo "SD pre-reqs already installed"
	fi
else
	setup_ansible
fi
