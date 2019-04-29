# ubuntu 14.04 image from 2019-03-12
FROM ubuntu@sha256:6612de24437f6f01d6a2988ed9a36b3603df06e8d2c0493678f3ee696bc4bb2d
ARG USER_NAME
ENV USER_NAME ${USER_NAME:-root}
ARG USER_ID
ENV USER_ID ${USER_ID:-0}

RUN apt-get update && \
    apt-get install -y devscripts vim \
                       python-pip libpython2.7-dev libssl-dev secure-delete \
                       gnupg2 ruby redis-server firefox git xvfb haveged curl \
                       gettext paxctl x11vnc enchant libffi-dev sqlite3

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
RUN pip install -U setuptools==40.8.0 && \
    pip install -r requirements/securedrop-app-code-requirements.txt && \
    pip install -r requirements/test-requirements.txt

RUN pip install supervisor

RUN if test $USER_NAME != root ; then useradd --no-create-home --home-dir /tmp --uid $USER_ID $USER_NAME && echo "$USER_NAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers ; fi

STOPSIGNAL SIGKILL

EXPOSE 8080 8081 5901
