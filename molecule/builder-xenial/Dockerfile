# ubuntu:xenial-20200902
FROM ubuntu@sha256:3dd44f7ca10f07f86add9d0dc611998a1641f501833692a2651c96defe8db940

# additional meta-data makes it easier to clean up, find
LABEL org="Freedom of the Press"
LABEL image_name="xenial-sd-builder-app"

RUN apt-get -y update && apt-get upgrade -y && apt-get install -y \
        apache2-dev \
        coreutils \
        debhelper \
        devscripts \
        dh-python \
        dh-systemd \
        dh-virtualenv \
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
        python3-venv \
        rsync \
        ruby \
        sqlite \
        sudo \
        tzdata \
        unzip \
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/*

RUN paxctl -cm /usr/bin/python3.5 && mkdir -p /tmp/build
