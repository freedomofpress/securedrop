FROM ubuntu:focal

# additional meta-data makes it easier to clean up, find
LABEL org="Freedom of the Press"
LABEL image_name="focal-sd-builder-app"

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get -y update && apt-get upgrade -y && apt-get install -y \
        apache2-dev \
        coreutils \
        debhelper \
        devscripts \
        dh-python \
        dh-systemd \
        gdb \
        git \
        gnupg2 \
        inotify-tools \
        libffi-dev \
        libpcre2-dev \
        libssl-dev \
        make \
        pkg-config \
        python3-all \
        python3-pip \
        python3-setuptools \
        python3-venv \
        python3-virtualenv \
        rsync \
        sqlite \
        sudo \
        tzdata \
        libevent-dev \
        unzip \
        zlib1g-dev

ENV RUST_VERSION 1.78.0
ENV RUSTUP_VERSION 1.24.3
ENV RUSTUP_INIT_SHA256 3dc5ef50861ee18657f9db2eeb7392f9c2a6c95c90ab41e45ab4ca71476b4338
ENV RUSTUP_HOME /opt/rustup
ENV CARGO_HOME /opt/cargo

# Install Rust using the same steps as <https://github.com/rust-lang/docker-rust>
# 1) Download rustup-init and verify it matches hardcoded checksum
# 2) Run it to install rustup and the rustc/cargo "minimal" toolchain
# 3) Add `/opt/cargo/bin` to $PATH, which is where cargo & rustc are installed
RUN TMPDIR=`mktemp -d` && cd ${TMPDIR} \
        && curl --proto '=https' --tlsv1.2 -OO -sSf https://static.rust-lang.org/rustup/archive/${RUSTUP_VERSION}/x86_64-unknown-linux-gnu/rustup-init \
        && echo "${RUSTUP_INIT_SHA256} *rustup-init" | sha256sum -c - \
        && chmod +x rustup-init \
        && ./rustup-init --default-toolchain=${RUST_VERSION} --profile minimal -y \
        && cd && rm -rf ${TMPDIR}
ENV PATH "$PATH:/opt/cargo/bin/"

# Turn the ossec key into a keyring
COPY OSSEC-ARCHIVE-KEY.asc /tmp/OSSEC-ARCHIVE-KEY.asc
RUN gpg --import /tmp/OSSEC-ARCHIVE-KEY.asc && gpg --export > /ossec.gpg \
        && rm -rf /tmp/OSSEC-ARCHIVE-KEY.asc /root/.gnupg

COPY build-debs-ossec.sh /build-debs-ossec
COPY build-debs-securedrop.sh /build-debs-securedrop
COPY dep-check.sh /dep-check
