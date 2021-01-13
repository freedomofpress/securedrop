# ubuntu 16.04 image from 2019-03-12
FROM ubuntu@sha256:58d0da8bc2f434983c6ca4713b08be00ff5586eb5cdff47bcde4b2e88fd40f88
ARG USER_NAME
ENV USER_NAME ${USER_NAME:-root}
ARG USER_ID
ENV USER_ID ${USER_ID:-0}

# If running grsecurity kernel on the host, Memprotect must be disabled on mono-sgen in the container
RUN apt-get update && apt-get install -y paxctl && \
    { apt-get install -y libgtk2.0 || echo 'libgtk2.0 was not installed'; } && \
    paxctl -cm /usr/bin/mono-sgen && dpkg-reconfigure mono-runtime-sgen && \
    apt-get install -y apache2-dev coreutils devscripts dh-virtualenv vim \
                       python3-pip python3-all python3-venv virtualenv libpython3.5-dev libssl-dev \
                       gnupg2 ruby redis-server git xvfb haveged curl wget \
                       gettext paxctl x11vnc enchant libffi-dev sqlite3 gettext sudo \
                       libasound2 libdbus-glib-1-2 libgtk2.0-0 libfontconfig1 libxrender1 \
                       libcairo-gobject2 libgtk-3-0 libstartup-notification0 tor

RUN gem install sass -v 3.4.23

# Current versions of the test browser software. Tor Browser is based
# on a specific version of Firefox, noted in Help > About Tor Browser.
# Ideally we'll keep those in sync.
ENV FF_VERSION 78.6.1esr
ENV GECKODRIVER_VERSION v0.28.0
ENV TBB_VERSION 10.0.8

# Import Tor release signing key
ENV TOR_RELEASE_KEY_FINGERPRINT "EF6E286DDA85EA2A4BA7DE684E2C6E8793298290"
RUN curl -s https://openpgpkey.torproject.org/.well-known/openpgpkey/torproject.org/hu/kounek7zrdx745qydx6p59t9mqjpuhdf | gpg2 --import -

# Install Tor Browser
RUN wget https://www.torproject.org/dist/torbrowser/${TBB_VERSION}/tor-browser-linux64-${TBB_VERSION}_en-US.tar.xz && \
    wget https://www.torproject.org/dist/torbrowser/${TBB_VERSION}/tor-browser-linux64-${TBB_VERSION}_en-US.tar.xz.asc && \
    gpg2 --verify tor-browser-linux64-${TBB_VERSION}_en-US.tar.xz.asc 2>&1 | grep "Primary key fingerprint:" | sed -e 's/Primary key fingerprint: //' -e 's/ //g' | tail -1 | grep -qE "${TOR_RELEASE_KEY_FINGERPRINT}" && \
    tar -xvJf tor-browser-linux64-${TBB_VERSION}_en-US.tar.xz && \
    mkdir -p /root/.local/tbb && mv tor-browser_en-US /root/.local/tbb &&\
    paxctl -cm /root/.local/tbb/tor-browser_en-US/Browser/firefox.real && \
    paxctl -cm /root/.local/tbb/tor-browser_en-US/Browser/libnspr4.so && \
    paxctl -cm /root/.local/tbb/tor-browser_en-US/Browser/plugin-container

# Import Mozilla release signing key
ENV MOZILLA_RELEASE_KEY_FINGERPRINT "14F26682D0916CDD81E37B6D61B7B526D98F0353"
RUN curl -s https://archive.mozilla.org/pub/firefox/releases/${FF_VERSION}/KEY | gpg2 --import -

# Install the version of Firefox on which Tor Browser is based
RUN curl -LO https://archive.mozilla.org/pub/firefox/releases/${FF_VERSION}/linux-x86_64/en-US/firefox-${FF_VERSION}.tar.bz2 && \
    curl -LO https://archive.mozilla.org/pub/firefox/releases/${FF_VERSION}/linux-x86_64/en-US/firefox-${FF_VERSION}.tar.bz2.asc && \
    gpg2 --verify firefox-${FF_VERSION}.tar.bz2.asc 2>&1 | grep "Primary key fingerprint:" | sed -e 's/Primary key fingerprint: //' -e 's/ //g' | tail -1 | grep -qE "${MOZILLA_RELEASE_KEY_FINGERPRINT}" && \
    tar xjf firefox-*.tar.bz2 && \
    mv firefox /usr/bin && \
    paxctl -cm /usr/bin/firefox/firefox

# Install geckodriver
RUN wget https://github.com/mozilla/geckodriver/releases/download/${GECKODRIVER_VERSION}/geckodriver-${GECKODRIVER_VERSION}-linux64.tar.gz && \
    wget https://github.com/mozilla/geckodriver/releases/download/${GECKODRIVER_VERSION}/geckodriver-${GECKODRIVER_VERSION}-linux64.tar.gz.asc && \
    gpg2 --verify geckodriver-${GECKODRIVER_VERSION}-linux64.tar.gz.asc && \
    tar -zxvf geckodriver*tar.gz && chmod +x geckodriver && mv geckodriver /bin && \
    paxctl -cm /bin/geckodriver

COPY requirements requirements
RUN python3 -m venv /opt/venvs/securedrop-app-code && \
    /opt/venvs/securedrop-app-code/bin/pip3 install --no-deps --require-hashes -r requirements/python3/docker-requirements.txt && \
    /opt/venvs/securedrop-app-code/bin/pip3 install --no-deps --require-hashes -r requirements/python3/securedrop-app-code-requirements.txt && \
    /opt/venvs/securedrop-app-code/bin/pip3 install --no-deps --require-hashes -r requirements/python3/test-requirements.txt

RUN if test $USER_NAME != root ; then useradd --no-create-home --home-dir /tmp --uid $USER_ID $USER_NAME && echo "$USER_NAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers ; fi && \
    cp -r /root/.local /tmp/ && chmod +x /tmp/.local/tbb/tor-browser_en-US/Browser/firefox && chmod -R 777 /tmp/.local && \
    chown -R $USER_NAME.$USER_NAME /tmp/.local/ && \
    chown -R $USER_NAME.$USER_NAME /opt/venvs/securedrop-app-code/

STOPSIGNAL SIGKILL

EXPOSE 8080 8081 5909
