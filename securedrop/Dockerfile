# ubuntu:14.04 as of 2017-11-15
FROM ubuntu@sha256:f6eed4def93a3b54da920737f0abf1a8cae2e480bb368280c898265fcaf910a3

RUN apt-get update # 2017-11-15
RUN apt-get install -y \
	python-pip libpython2.7-dev libssl-dev secure-delete gnupg2 ruby redis-server
# refs securedrop/issues/1594
RUN gem install sass -v 3.4.23

# test requirements:
RUN apt-get install -y firefox
RUN apt-get install -y git xvfb haveged curl gettext paxctl
RUN apt-get install -y x11vnc

# pinned firefox version for selenium compatibility. See bd795e2f5865b4f6e6e1b88bcbbacef704675c74
ENV FIREFOX_CHECKSUM=88d25053306d33658580973b063cd459a56e3596a3a298c1fb8ab1d52171d860
RUN curl -LO https://launchpad.net/~ubuntu-mozilla-security/+archive/ubuntu/ppa/+build/9727836/+files/firefox_46.0.1+build1-0ubuntu0.14.04.3_amd64.deb && \
    shasum -a 256 firefox*deb && \
    echo "${FIREFOX_CHECKSUM}  firefox_46.0.1+build1-0ubuntu0.14.04.3_amd64.deb" | shasum -a 256 -c - && \
    dpkg -i firefox*deb && apt-get install -f && \
    paxctl -cm /usr/lib/firefox/firefox

#
# This can be removed when upgrading to something more recent than trusty
#
RUN echo deb http://archive.ubuntu.com/ubuntu/ xenial main > /etc/apt/sources.list.d/xenial.list
RUN apt-get update
RUN apt-get install -y gettext
RUN rm /etc/apt/sources.list.d/xenial.list
RUN apt-get update

COPY requirements requirements
RUN pip install -r requirements/securedrop-app-code-requirements.txt

# test requirements:
RUN pip install -r requirements/test-requirements.txt

WORKDIR /app

COPY static static
COPY sass sass
RUN sass --force --stop-on-error --update sass:static/css --style compressed

RUN mkdir -p /var/lib/securedrop/store /var/lib/securedrop/keys
COPY ./tests/files/test_journalist_key.pub /var/lib/securedrop/keys
RUN gpg --homedir /var/lib/securedrop/keys --import /var/lib/securedrop/keys/test_journalist_key.pub

COPY . /app

RUN make test-config
RUN ./manage.py reset

EXPOSE 8080 8081
EXPOSE 5901

CMD ["./manage.py", "run"]
