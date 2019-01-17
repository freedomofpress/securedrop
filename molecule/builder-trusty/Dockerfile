# ubuntu:trusty-20190122
FROM ubuntu@sha256:cac55e5d97fad634d954d00a5c2a56d80576a08dcc01036011f26b88263f1578

# additional meta-data makes it easier to clean up, find
LABEL org="Freedom of the Press"
LABEL image_name="trusty-sd-builder-app"

RUN apt-get -y update && apt-get upgrade -y && apt-get install -y \
        aptitude \
        debhelper \
        devscripts \
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
        python \
        python-dev \
        python-pip \
        python-requests \
        rsync \
        ruby \
        secure-delete \
        sudo \
        sqlite \
        unzip \
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/*

RUN paxctl -cm /usr/bin/python2.7 && mkdir -p /tmp/build
