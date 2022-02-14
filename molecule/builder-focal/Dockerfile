# ubuntu:focal-20210921
FROM ubuntu@sha256:3555f4996aea6be945ae1532fa377c88f4b3b9e6d93531f47af5d78a7d5e3761


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
        libssl-dev \
        make \
        paxctl \
        python3-all \
        python3-pip \
        python3-setuptools \
        python3-venv \
        rsync \
        ruby \
        sqlite \
        sudo \
        tzdata \
        libevent-dev \
        unzip


# TEMPORARY: install dh-virtualenv from unstable Ubuntu release, pending focal package:
# https://github.com/spotify/dh-virtualenv/issues/298
RUN echo "deb http://archive.ubuntu.com/ubuntu/ impish universe main" > /etc/apt/sources.list.d/ubuntu-impish.list
COPY dh-virtualenv.pref /etc/apt/preferences.d/

RUN apt-get update && apt-get install -y dh-virtualenv

ENV RUST_VERSION 1.58.1
ENV RUSTUP_VERSION 1.24.3
ENV RUSTUP_INIT_SHA256 3dc5ef50861ee18657f9db2eeb7392f9c2a6c95c90ab41e45ab4ca71476b4338

# Install Rust for building cryptography
RUN TMPDIR=`mktemp -d` && cd ${TMPDIR} \
        && curl --proto '=https' --tlsv1.2 -OO -sSf https://static.rust-lang.org/rustup/archive/${RUSTUP_VERSION}/x86_64-unknown-linux-gnu/rustup-init \
        && echo "${RUSTUP_INIT_SHA256} *rustup-init" | sha256sum -c - \
        && chmod +x rustup-init \
        && ./rustup-init --default-toolchain=${RUST_VERSION} -y \
        && cd && rm -rf ${TMPDIR}

RUN echo "source $HOME/.cargo/env" >> $HOME/.bashrc

RUN paxctl -cm /usr/bin/python3.8 && mkdir -p /tmp/build
RUN apt-get clean \
        && rm -rf /var/lib/apt/lists/*
