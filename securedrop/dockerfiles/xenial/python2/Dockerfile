# ubuntu 16.04 image from 2019-03-12
FROM ubuntu@sha256:58d0da8bc2f434983c6ca4713b08be00ff5586eb5cdff47bcde4b2e88fd40f88
ARG USER_NAME
ENV USER_NAME ${USER_NAME:-root}
ARG USER_ID
ENV USER_ID ${USER_ID:-0}

# If running grsecurity kernel on the host, Memprotect must be disabled on mono-sgen in the container
RUN apt-get update && \
    apt-get install -y paxctl && \
    { apt-get install -y libgtk2.0 || echo 'libgtk2.0 was not installed'; } && \
    paxctl -cm /usr/bin/mono-sgen && dpkg-reconfigure mono-runtime-sgen && \
    apt-get install -y devscripts vim \
                       python-pip libpython2.7-dev libssl-dev secure-delete \
                       gnupg2 ruby redis-server git xvfb haveged curl wget \
                       gettext paxctl x11vnc enchant libffi-dev sqlite3 gettext sudo \
                       libasound2 libdbus-glib-1-2 libgtk2.0-0 libfontconfig1 libxrender1 \
                       libcairo-gobject2 libgtk-3-0 libstartup-notification0 tor

RUN gem install sass -v 3.4.23

ENV FF_ESR_VER 60.6.1esr
RUN curl -LO https://ftp.mozilla.org/pub/firefox/releases/${FF_ESR_VER}/linux-x86_64/en-US/firefox-${FF_ESR_VER}.tar.bz2 && \
    curl -LO https://ftp.mozilla.org/pub/firefox/releases/${FF_ESR_VER}/linux-x86_64/en-US/firefox-${FF_ESR_VER}.tar.bz2.asc && \
    gpg --recv-key --keyserver gpg.mozilla.org 0x61B7B526D98F0353 && \
    gpg --verify firefox-${FF_ESR_VER}.tar.bz2.asc && \
    tar xjf firefox-*.tar.bz2 && \
    mv firefox /usr/bin && \
    paxctl -cm /usr/bin/firefox/firefox

COPY ./tor_project_public.pub /opt/

ENV TBB_VERSION 8.5.1
RUN gpg --import /opt/tor_project_public.pub && \
    wget  https://www.torproject.org/dist/torbrowser/${TBB_VERSION}/tor-browser-linux64-${TBB_VERSION}_en-US.tar.xz && \
    wget https://www.torproject.org/dist/torbrowser/${TBB_VERSION}/tor-browser-linux64-${TBB_VERSION}_en-US.tar.xz.asc && \
    gpg --verify tor-browser-linux64-${TBB_VERSION}_en-US.tar.xz.asc tor-browser-linux64-${TBB_VERSION}_en-US.tar.xz && \
    tar -xvJf tor-browser-linux64-${TBB_VERSION}_en-US.tar.xz && \
    mkdir -p /root/.local/tbb && mv tor-browser_en-US /root/.local/tbb &&\
    paxctl -cm /root/.local/tbb/tor-browser_en-US/Browser/firefox.real && \
    paxctl -cm /root/.local/tbb/tor-browser_en-US/Browser/libnspr4.so && \
    paxctl -cm /root/.local/tbb/tor-browser_en-US/Browser/plugin-container

ENV GECKODRIVER_CHECKSUM=03be3d3b16b57e0f3e7e8ba7c1e4bf090620c147e6804f6c6f3203864f5e3784
RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.24.0/geckodriver-v0.24.0-linux64.tar.gz && \
    shasum -a 256 geckodriver*tar.gz && \
    echo "${GECKODRIVER_CHECKSUM}  geckodriver-v0.24.0-linux64.tar.gz" | shasum -a 256 -c - && \
    tar -zxvf geckodriver*tar.gz && chmod +x geckodriver && mv geckodriver /bin && \
    paxctl -cm /bin/geckodriver

COPY requirements requirements

RUN pip install --require-hashes -r requirements/securedrop-app-code-requirements.txt && \
    pip install -r requirements/test-requirements.txt && \
    pip install --upgrade setuptools  # Fixes #4036 pybabel requires latest version of setuptools


RUN pip install supervisor

RUN if test $USER_NAME != root ; then useradd --no-create-home --home-dir /tmp --uid $USER_ID $USER_NAME && echo "$USER_NAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers ; fi && \
    cp -r /root/.local /tmp/ && chmod +x /tmp/.local/tbb/tor-browser_en-US/Browser/firefox && chmod -R 777 /tmp/.local && \
    chown -R $USER_NAME.$USER_NAME /tmp/.local/

STOPSIGNAL SIGKILL

EXPOSE 8080 8081 5909
