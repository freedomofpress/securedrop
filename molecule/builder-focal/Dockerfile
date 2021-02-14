# ubuntu:focal-20200720
FROM ubuntu@sha256:60f560e52264ed1cb7829a0d59b1ee7740d7580e0eb293aca2d722136edb1e24


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
        haveged \
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


# TEMPORARY: install dh-virtualenv from debian unstable, pending focal package:
# https://github.com/spotify/dh-virtualenv/issues/298
RUN echo "deb http://archive.ubuntu.com/ubuntu/ groovy universe" > /etc/apt/sources.list.d/ubuntu-groovy.list
COPY aptpreferences.conf /etc/apt/preferences.d/ubuntu-groovy

RUN apt-get update && apt-get install -y dh-virtualenv

RUN paxctl -cm /usr/bin/python3.8 && mkdir -p /tmp/build
RUN apt-get clean \
        && rm -rf /var/lib/apt/lists/*
