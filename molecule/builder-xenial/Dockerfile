# ubuntu:xenial-20190122
FROM ubuntu@sha256:e4a134999bea4abb4a27bc437e6118fdddfb172e1b9d683129b74d254af51675

# additional meta-data makes it easier to clean up, find
LABEL org="Freedom of the Press"
LABEL image_name="xenial-sd-builder-app"

RUN apt-get -y update && apt-get upgrade -y && apt-get install -y \
        apache2-dev \
        aptitude \
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
        rsync \
        ruby \
        sqlite \
        sudo \
        tzdata \
        unzip \
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/*

RUN paxctl -cm /usr/bin/python3.5 && mkdir -p /tmp/build
