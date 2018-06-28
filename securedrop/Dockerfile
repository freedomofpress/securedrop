# ubuntu:14.04 as of 2018-06-19
FROM ubuntu@sha256:885bb6705b01d99544ddb98cbe4e4555d1efe1d052cef90832e72a0688ac6b37
ARG USER_NAME
ENV USER_NAME ${USER_NAME:-root}
ARG USER_ID
ENV USER_ID ${USER_ID:-0}

RUN apt-get update && \
    apt-get install -y devscripts \
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

RUN apt-get install -y wget libasound2 libdbus-glib-1-2 libgtk2.0-0 libfontconfig1 libxrender1

RUN gpg --keyserver=hkp://ipv4.pool.sks-keyservers.net --recv-keys EF6E286DDA85EA2A4BA7DE684E2C6E8793298290 && \
    wget  https://www.torproject.org/dist/torbrowser/7.5.6/tor-browser-linux64-7.5.6_en-US.tar.xz && \
    wget https://www.torproject.org/dist/torbrowser/7.5.6/tor-browser-linux64-7.5.6_en-US.tar.xz.asc && \
    gpg --verify tor-browser-linux64-7.5.6_en-US.tar.xz.asc tor-browser-linux64-7.5.6_en-US.tar.xz

RUN tar -xvJf tor-browser-linux64-7.5.6_en-US.tar.xz && \
    mkdir -p /root/.local/tbb && mv tor-browser_en-US /root/.local/tbb &&\
    paxctl -cm /root/.local/tbb/tor-browser_en-US/Browser/firefox && \
    paxctl -cm /root/.local/tbb/tor-browser_en-US/Browser/plugin-container

ENV GECKODRIVER_CHECKSUM=3154274c050d724eb2f4e8986a58ed37c0138b48304692bf7eeed827a5e82319
RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.17.0/geckodriver-v0.17.0-linux64.tar.gz && \
    shasum -a 256 geckodriver*tar.gz && \
    echo "${GECKODRIVER_CHECKSUM}  geckodriver-v0.17.0-linux64.tar.gz" | shasum -a 256 -c - && \
    tar -zxvf geckodriver*tar.gz && chmod +x geckodriver && mv geckodriver /bin && \
    paxctl -cm /bin/geckodriver


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

RUN if test $USER_NAME != root ; then useradd --no-create-home --home-dir /tmp --uid $USER_ID $USER_NAME && echo "$USER_NAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers ; fi

STOPSIGNAL SIGKILL

EXPOSE 8080 8081 5901
