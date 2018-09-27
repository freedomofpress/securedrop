# ubuntu:14.04 as of 2018-06-19
FROM ubuntu@sha256:885bb6705b01d99544ddb98cbe4e4555d1efe1d052cef90832e72a0688ac6b37
ARG USER_NAME
ENV USER_NAME ${USER_NAME:-root}
ARG USER_ID
ENV USER_ID ${USER_ID:-0}

RUN apt-get update && \
    apt-get install -y devscripts \
                       python-pip libpython2.7-dev libssl-dev secure-delete \
                       gnupg2 ruby redis-server git xvfb haveged curl \
                       gettext paxctl tightvncserver enchant libffi-dev sqlite3 wget \
                       libasound2 libdbus-glib-1-2 libgtk2.0-0 libfontconfig1 libxrender1 \
                       libcairo-gobject2 libgtk-3-0 libstartup-notification0

RUN gem install sass -v 3.4.23

ENV FF_ESR_VER 60.2.0esr
RUN curl -LO https://ftp.mozilla.org/pub/firefox/releases/${FF_ESR_VER}/linux-x86_64/en-US/firefox-${FF_ESR_VER}.tar.bz2 && \
    curl -LO https://ftp.mozilla.org/pub/firefox/releases/${FF_ESR_VER}/linux-x86_64/en-US/firefox-${FF_ESR_VER}.tar.bz2.asc && \
    gpg --recv-key --keyserver keys.gnupg.net 0x61B7B526D98F0353 && \
    gpg --verify firefox-${FF_ESR_VER}.tar.bz2.asc && \
    tar xjf firefox-*.tar.bz2 && \
    mv firefox /usr/bin && \
    paxctl -cm /usr/bin/firefox/firefox

COPY ./tor_project_public.pub /opt/

ENV TBB_VERSION 8.0.1
RUN gpg --import /opt/tor_project_public.pub && \
    wget  https://www.torproject.org/dist/torbrowser/${TBB_VERSION}/tor-browser-linux64-${TBB_VERSION}_en-US.tar.xz && \
    wget https://www.torproject.org/dist/torbrowser/${TBB_VERSION}/tor-browser-linux64-${TBB_VERSION}_en-US.tar.xz.asc && \
    gpg --verify tor-browser-linux64-${TBB_VERSION}_en-US.tar.xz.asc tor-browser-linux64-${TBB_VERSION}_en-US.tar.xz

RUN tar -xvJf tor-browser-linux64-${TBB_VERSION}_en-US.tar.xz && \
    mkdir -p /root/.local/tbb && mv tor-browser_en-US /root/.local/tbb &&\
    paxctl -cm /root/.local/tbb/tor-browser_en-US/Browser/firefox.real && \
    paxctl -cm /root/.local/tbb/tor-browser_en-US/Browser/libnspr4.so && \
    paxctl -cm /root/.local/tbb/tor-browser_en-US/Browser/plugin-container

ENV GECKODRIVER_CHECKSUM=9d80799bff034eda2a233493a78e3250b7c6118c9010ec37a871783081963fda
RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.22.0/geckodriver-v0.22.0-linux64.tar.gz && \
    shasum -a 256 geckodriver*tar.gz && \
    echo "${GECKODRIVER_CHECKSUM}  geckodriver-v0.22.0-linux64.tar.gz" | shasum -a 256 -c - && \
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
RUN cp -r /root/.local /tmp/ && chmod +x /tmp/.local/tbb/tor-browser_en-US/Browser/firefox && chmod -R 777 /tmp/.local
RUN chown -R $USER_NAME.$USER_NAME /tmp/.local/

STOPSIGNAL SIGKILL

EXPOSE 8080 8081 5901
