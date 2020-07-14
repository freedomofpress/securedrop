# ubuntu:xenial-20190122
# FROM ubuntu@sha256:e4a134999bea4abb4a27bc437e6118fdddfb172e1b9d683129b74d254af51675
FROM ubuntu:focal


# additional meta-data makes it easier to clean up, find
LABEL org="Freedom of the Press"
LABEL image_name="focal-sd-builder-app"
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get -y update && apt-get upgrade -y && apt-get install -y \
        apache2-dev \
        aptitude \
        coreutils \
        debhelper \
        devscripts \
        dh-python \
        dh-systemd \
        gdb \
        git \
        gnupg2 \
        haveged \
        inotify-tools \
        libffi-dev \
        libssl-dev \
        make \
        ntp \
        paxctl \
        python3-all \
        python3-pip \
        python3-setuptools \
        rsync \
        ruby \
        sqlite \
        sudo \
        tzdata \
	libevent-dev \
        unzip 


# TEMPORARY: install dh-virtualenv from debian unstable
# No pubkey verification is performed on this package, using only for
# research spike on focal package support.
RUN curl -s https://deb.debian.org/debian/pool/main/d/dh-virtualenv/dh-virtualenv_1.2-1_all.deb -o /tmp/dh-virtualenv_1.2-1_all.deb
RUN apt install -y /tmp/dh-virtualenv_1.2-1_all.deb

RUN paxctl -cm /usr/bin/python3.8 && mkdir -p /tmp/build
RUN apt-get clean \
        && rm -rf /var/lib/apt/lists/*
