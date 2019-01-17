# ubuntu 16.04 image - 01-2019
FROM ubuntu@sha256:b967b9f2a5625231a22db642609e61b7b1a5481128f51fe771e91bb92e0a35d0
ARG USER_NAME
ENV USER_NAME ${USER_NAME:-root}
ARG USER_ID
ENV USER_ID ${USER_ID:-0}

RUN apt-get update && \
    apt-get install -y devscripts \
                       python-pip libpython2.7-dev libssl-dev secure-delete \
                       gnupg2 ruby redis-server firefox git xvfb haveged curl \
                       gettext paxctl x11vnc enchant libffi-dev sqlite3 gettext sudo

ENV FIREFOX_CHECKSUM=179647c2d47e2acf2cf3596f21c8cbea8eda4b271d4d09d7b18be55553751912
RUN curl -LO https://launchpad.net/~ubuntu-mozilla-security/+archive/ubuntu/ppa/+build/11952510/+files/firefox-locale-en_51.0.1+build2-0ubuntu0.16.04.2_amd64.deb && \
    shasum -a 256 firefox*deb && \
    echo "${FIREFOX_CHECKSUM}  firefox-locale-en_51.0.1+build2-0ubuntu0.16.04.2_amd64.deb" | shasum -a 256 -c - && \
    dpkg -i firefox*deb && apt-get install -f && \
    paxctl -cm /usr/lib/firefox/firefox

RUN gem install sass -v 3.4.23

COPY requirements requirements
RUN pip install -r requirements/securedrop-app-code-requirements.txt && \
    pip install -r requirements/test-requirements.txt

RUN pip install --upgrade setuptools

RUN if test $USER_NAME != root ; then useradd --no-create-home --home-dir /tmp --uid $USER_ID $USER_NAME && echo "$USER_NAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers ; fi

STOPSIGNAL SIGKILL

EXPOSE 8080 8081 5901
