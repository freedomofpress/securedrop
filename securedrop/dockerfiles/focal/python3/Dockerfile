# ubuntu 20.04 image from 2022-08-01
FROM ubuntu@sha256:a06ae92523384c2cd182dcfe7f8b2bf09075062e937d5653d7d0db0375ad2221
ARG USER_NAME
ENV USER_NAME ${USER_NAME:-root}
ARG USER_ID
ENV USER_ID ${USER_ID:-0}

RUN apt-get update && apt-get install -y \
                       libgtk2.0 apache2-dev coreutils devscripts vim \
                       python3-pip python3-all python3-venv virtualenv libpython3.8-dev libssl-dev \
                       gnupg2 redis-server git xvfb curl wget \
                       x11vnc enchant libffi-dev sqlite3 gettext sudo \
                       # For html5validator.  Used only in "app-page-layout-tests", but we can live
                       # with its being installed along with everything else since it will be
                       # cached along with everything else too.
                       default-jdk \
                       libasound2 libdbus-glib-1-2 libgtk2.0-0 libfontconfig1 libxrender1 \
                       libcairo-gobject2 libgtk-3-0 libstartup-notification0 tor basez

# Current versions of the test browser software. Tor Browser is based
# on a specific version of Firefox, noted in Help > About Tor Browser.
# Ideally we'll keep those in sync.
ENV FF_VERSION 91.12.0esr
ENV GECKODRIVER_VERSION v0.29.1

# Import Tor release signing key
ENV TOR_RELEASE_KEY_FINGERPRINT "EF6E286DDA85EA2A4BA7DE684E2C6E8793298290"
RUN curl -s https://openpgpkey.torproject.org/.well-known/openpgpkey/torproject.org/hu/kounek7zrdx745qydx6p59t9mqjpuhdf | gpg2 --import -

# Fetch latest TBB version (obtained from https://github.com/micahflee/torbrowser-launcher/blob/develop/torbrowser_launcher/common.py#L198) and install Tor Browser
RUN TBB_VERSION=$(curl -s https://aus1.torproject.org/torbrowser/update_3/release/Linux_x86_64-gcc3/x/en-US | grep -oP '(?<=appVersion=")[^"]*' | head -1) && \
    wget https://www.torproject.org/dist/torbrowser/${TBB_VERSION}/tor-browser-linux64-${TBB_VERSION}_en-US.tar.xz && \
    wget https://www.torproject.org/dist/torbrowser/${TBB_VERSION}/tor-browser-linux64-${TBB_VERSION}_en-US.tar.xz.asc && \
    gpg2 --output ./tor.keyring --export ${TOR_RELEASE_KEY_FINGERPRINT} && \
    gpgv --keyring ./tor.keyring tor-browser-linux64-${TBB_VERSION}_en-US.tar.xz.asc tor-browser-linux64-${TBB_VERSION}_en-US.tar.xz && \
    tar -xvJf tor-browser-linux64-${TBB_VERSION}_en-US.tar.xz && \
    mkdir -p /root/.local/tbb && mv tor-browser_en-US /root/.local/tbb && \
    rm -f tor.keyring tor-browser-linux64-${TBB_VERSION}_en-US.tar.xz.asc tor-browser-linux64-${TBB_VERSION}_en-US.tar.xz 

# Import Mozilla release signing key
ENV MOZILLA_RELEASE_KEY_FINGERPRINT "14F26682D0916CDD81E37B6D61B7B526D98F0353"
RUN curl -s https://archive.mozilla.org/pub/firefox/releases/${FF_VERSION}/KEY | gpg2 --import -

# Install the version of Firefox on which Tor Browser is based
RUN curl -LO https://archive.mozilla.org/pub/firefox/releases/${FF_VERSION}/linux-x86_64/en-US/firefox-${FF_VERSION}.tar.bz2 && \
    curl -LO https://archive.mozilla.org/pub/firefox/releases/${FF_VERSION}/linux-x86_64/en-US/firefox-${FF_VERSION}.tar.bz2.asc && \
    gpg2 --output ./mozilla.keyring --export ${MOZILLA_RELEASE_KEY_FINGERPRINT} && \
    gpgv --keyring ./mozilla.keyring firefox-${FF_VERSION}.tar.bz2.asc firefox-${FF_VERSION}.tar.bz2 && \
    tar xjf firefox-*.tar.bz2 && \
    mv firefox /usr/bin && \
    rm -f firefox-${FF_VERSION}.tar.bz2.asc firefox-${FF_VERSION}.tar.bz2 

# Install geckodriver
RUN wget https://github.com/mozilla/geckodriver/releases/download/${GECKODRIVER_VERSION}/geckodriver-${GECKODRIVER_VERSION}-linux64.tar.gz && \
    wget https://github.com/mozilla/geckodriver/releases/download/${GECKODRIVER_VERSION}/geckodriver-${GECKODRIVER_VERSION}-linux64.tar.gz.asc && \
    # geckodriver uses the same key used by Mozilla
    gpgv --keyring ./mozilla.keyring geckodriver-${GECKODRIVER_VERSION}-linux64.tar.gz.asc geckodriver-${GECKODRIVER_VERSION}-linux64.tar.gz && \
    tar -zxvf geckodriver*tar.gz && chmod +x geckodriver && mv geckodriver /bin && \
    rm -f mozilla.keyring geckodriver-${GECKODRIVER_VERSION}-linux64.tar.gz.asc geckodriver-${GECKODRIVER_VERSION}-linux64.tar.gz

COPY requirements requirements
RUN python3 -m venv /opt/venvs/securedrop-app-code && \
    /opt/venvs/securedrop-app-code/bin/pip3 install --no-deps --require-hashes -r requirements/python3/docker-requirements.txt && \
    /opt/venvs/securedrop-app-code/bin/pip3 install --no-deps --require-hashes -r requirements/python3/test-requirements.txt && \
    /opt/venvs/securedrop-app-code/bin/pip3 install --no-deps --require-hashes -r requirements/python3/securedrop-app-code-requirements.txt 

RUN if test $USER_NAME != root ; then useradd --no-create-home --home-dir /tmp --uid $USER_ID $USER_NAME && echo "$USER_NAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers ; fi && \
    cp -r /root/.local /tmp/ && chmod +x /tmp/.local/tbb/tor-browser_en-US/Browser/firefox && chmod -R 777 /tmp/.local && \
    chown -R $USER_NAME.$USER_NAME /tmp/.local/ && \
    chown -R $USER_NAME.$USER_NAME /opt/venvs/securedrop-app-code/

STOPSIGNAL SIGKILL

EXPOSE 8080 8081 5909
