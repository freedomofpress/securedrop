# ubuntu:xenial-20181218
FROM ubuntu@sha256:b967b9f2a5625231a22db642609e61b7b1a5481128f51fe771e91bb92e0a35d0

# additional meta-data makes it easier to clean up, find
LABEL org="Freedom of the Press"
LABEL image_name="xenial-sd-builder-app"

RUN apt-get -y update && apt-get upgrade -y && apt-get install -y \
        aptitude \
        devscripts \
        git \
        gdb \
        gnupg2 \
        haveged \
        libffi-dev \
        libssl-dev \
        make \
        ntp \
        inotify-tools \
        paxctl \
        python \
        python-dev \
        python-pip \
        rsync \
        ruby \
        secure-delete \
        sqlite \
        unzip \
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/*

RUN paxctl -cm /usr/bin/python2.7 && mkdir -p /tmp/build
