# ubuntu:trusty-20180531
FROM ubuntu@sha256:885bb6705b01d99544ddb98cbe4e4555d1efe1d052cef90832e72a0688ac6b37

# additional meta-data makes it easier to clean up, find
LABEL org="Freedom of the Press"
LABEL image_name="trusty-sd-builder-app"

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
