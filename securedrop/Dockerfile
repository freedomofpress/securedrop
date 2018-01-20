# ubuntu:14.04 as of 2017-12-15
FROM ubuntu@sha256:084989eb923bd86dbf7e706d464cf3587274a826b484f75b69468c19f8ae354c

RUN apt-get update && \
    apt-get install -y python-pip libpython2.7-dev libssl-dev secure-delete \
                       gnupg2 ruby redis-server firefox git xvfb haveged curl \
                       gettext paxctl x11vnc enchant

RUN gem install sass -v 3.4.23

ENV FIREFOX_CHECKSUM=88d25053306d33658580973b063cd459a56e3596a3a298c1fb8ab1d52171d860
RUN curl -LO https://launchpad.net/~ubuntu-mozilla-security/+archive/ubuntu/ppa/+build/9727836/+files/firefox_46.0.1+build1-0ubuntu0.14.04.3_amd64.deb && \
    shasum -a 256 firefox*deb && \
    echo "${FIREFOX_CHECKSUM}  firefox_46.0.1+build1-0ubuntu0.14.04.3_amd64.deb" | shasum -a 256 -c - && \
    dpkg -i firefox*deb && apt-get install -f && \
    paxctl -cm /usr/lib/firefox/firefox

#
# This can be removed when upgrading to something more recent than trusty
#
RUN echo deb http://archive.ubuntu.com/ubuntu/ xenial main > /etc/apt/sources.list.d/xenial.list && \
    apt-get update && \
    apt-get install -y gettext && \
    rm /etc/apt/sources.list.d/xenial.list && \
    apt-get update

COPY requirements requirements
RUN pip install -r requirements/securedrop-app-code-requirements.txt && \
    pip install -r requirements/test-requirements.txt

WORKDIR /app

RUN mkdir -p /var/lib/securedrop/store /var/lib/securedrop/keys
COPY ./tests/files/test_journalist_key.pub /var/lib/securedrop/keys
RUN gpg --homedir /var/lib/securedrop/keys --import /var/lib/securedrop/keys/test_journalist_key.pub

COPY static static
COPY sass sass
RUN sass --force --stop-on-error --update sass:static/css --style compressed

COPY . /app
RUN make test-config && ./manage.py reset

RUN ./manage.py --verbose translate-messages --compile

EXPOSE 8080 8081 5901

CMD ["./manage.py", "run"]
