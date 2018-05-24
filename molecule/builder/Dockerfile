# ubuntu:xenial-20180417
FROM ubuntu@sha256:1dfb94f13f5c181756b2ed7f174825029aca902c78d0490590b1aaa203abc052

# additional meta-data makes it easier to clean up, find
LABEL org="Freedom of the Press"
LABEL image_name="sd-builder-app"

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
        # ossec_urls.py
        python-requests \
        python-virtualenv \
        rsync \
        ruby \
        secure-delete \
        sudo \
        sqlite \
        unzip \
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/*

RUN paxctl -cm /usr/bin/python2.7 && mkdir -p /tmp/build
