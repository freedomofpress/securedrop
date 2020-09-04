# ubuntu:xenial-20200902
FROM ubuntu@sha256:3dd44f7ca10f07f86add9d0dc611998a1641f501833692a2651c96defe8db940

# additional meta-data makes it easier to clean up, find
LABEL org="Freedom of the Press"
LABEL image_name="xenial-sd-builder-app"

RUN apt-get -y update && apt-get upgrade -y && apt-get install -y \
        apache2-dev \
        apt-transport-https \
        aptitude \
        coreutils \
        curl \
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
        unzip \
        virtualenv

#install dh-virtualenv from debian unstable
RUN curl https://ftp-master.debian.org/keys/archive-key-10.asc -o /tmp/debian-stable-archive-pubkey.asc && \
        apt-key add /tmp/debian-stable-archive-pubkey.asc
RUN echo "deb https://deb.debian.org/debian unstable main contrib" > /etc/apt/sources.list.d/debian-unstable.list
COPY aptpreferences.conf /etc/apt/preferences.d/debian-unstable
RUN apt-get update && apt-get install -y -t unstable dh-virtualenv
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

RUN paxctl -cm /usr/bin/python3.5 && mkdir -p /tmp/build
