ARG UBUNTU_VERSION=focal
FROM securedrop-slim-${UBUNTU_VERSION}-py3

RUN apt-get update  && apt-get install -y \
    libgtk2.0 devscripts xvfb x11vnc \
    # For html5validator.  Used only in "app-page-layout-tests", but we can live
    # with its being installed along with everything else since it will be
    # cached along with everything else too.
    default-jdk \
    # For diffoscope:
    libarchive13 libmagic1 \
    libasound2-dev libdbus-glib-1-2 libgtk2.0-0 libfontconfig1 libxrender1 \
    libcairo-gobject2 libgtk-3-0 libstartup-notification0 npm && \
    npm install --global html_codesniffer@2.5.1

# Current versions of the test browser software. Tor Browser is based
# on a specific version of Firefox - we download both for generic and TBB testing

# We should use the version of geckodriver corresponding to the above Firefox version.
ENV GECKODRIVER_VERSION v0.35.0

# Import Tor release signing key
ENV TOR_RELEASE_KEY_FINGERPRINT "EF6E286DDA85EA2A4BA7DE684E2C6E8793298290"
RUN curl -s https://openpgpkey.torproject.org/.well-known/openpgpkey/torproject.org/hu/kounek7zrdx745qydx6p59t9mqjpuhdf | gpg2 --import -

# Fetch latest TBB version (obtained from https://github.com/micahflee/torbrowser-launcher/blob/develop/torbrowser_launcher/common.py#L198) and install Tor Browser
RUN TBB_VERSION=$(curl -s https://aus1.torproject.org/torbrowser/update_3/release/Linux_x86_64-gcc3/x/ALL | grep -oP '(?<=appVersion=")[^"]*' | head -1) && \
    wget https://www.torproject.org/dist/torbrowser/${TBB_VERSION}/tor-browser-linux-x86_64-${TBB_VERSION}.tar.xz && \
    wget https://www.torproject.org/dist/torbrowser/${TBB_VERSION}/tor-browser-linux-x86_64-${TBB_VERSION}.tar.xz.asc && \
    gpg2 --output ./tor.keyring --export ${TOR_RELEASE_KEY_FINGERPRINT} && \
    gpgv --keyring ./tor.keyring tor-browser-linux-x86_64-${TBB_VERSION}.tar.xz.asc tor-browser-linux-x86_64-${TBB_VERSION}.tar.xz && \
    tar -xvJf tor-browser-linux-x86_64-${TBB_VERSION}.tar.xz && \
    mkdir -p /root/.local/tbb && mv tor-browser /root/.local/tbb && \
    rm -f tor.keyring tor-browser-linux-x86_64-${TBB_VERSION}.tar.xz.asc tor-browser-linux-x86_64-${TBB_VERSION}.tar.xz


# Import Mozilla release signing key and install the version of Firefox on which
# Tor Browser is based
ENV MOZILLA_RELEASE_KEY_FINGERPRINT "14F26682D0916CDD81E37B6D61B7B526D98F0353"

RUN FF_VERSION=$(curl -s https://aus1.torproject.org/torbrowser/update_3/release/Linux_x86_64-gcc3/x/ALL | grep -oP '(?<=platformVersion=")[^"]*' | head -1)esr && \
curl -s https://archive.mozilla.org/pub/firefox/releases/${FF_VERSION}/KEY | gpg2 --import - && \
curl -LO https://archive.mozilla.org/pub/firefox/releases/${FF_VERSION}/linux-x86_64/en-US/firefox-${FF_VERSION}.tar.bz2 && \
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

RUN cp -r /root/.local /tmp/ && chmod +x /tmp/.local/tbb/tor-browser/Browser/firefox && chmod -R 777 /tmp/.local && \
    chown -R $USER_NAME.$USER_NAME /tmp/.local/

STOPSIGNAL SIGKILL

EXPOSE 8080 8081 5909
