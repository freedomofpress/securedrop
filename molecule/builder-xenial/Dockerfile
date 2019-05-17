# ubuntu:xenial-20190122
FROM ubuntu@sha256:e4a134999bea4abb4a27bc437e6118fdddfb172e1b9d683129b74d254af51675

# additional meta-data makes it easier to clean up, find
LABEL org="Freedom of the Press"
LABEL image_name="xenial-sd-builder-app"

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
        python-wheel \
        rsync \
        ruby \
        secure-delete \
        sqlite \
        sudo \
        tzdata \
        unzip \
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/*

RUN paxctl -cm /usr/bin/python2.7 && mkdir -p /tmp/build
