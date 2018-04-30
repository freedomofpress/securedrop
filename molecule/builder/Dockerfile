ARG IMAGE
FROM $IMAGE

# additional meta-data makes it easier to clean up, find
ARG NAME
LABEL org="Freedom of the Press"
LABEL image_name="$NAME"

# Non-version specific tooling required
# Followed by pegged dependencies
RUN apt-get -y update && apt-get install -y make unzip python python-pip rsync sudo bash aptitude paxctl \
        devscripts=2.14.1 \
        git=1:1.9.1-1 \
        gdb=7.7.1-0ubuntu5~14.04.3 \
        gnupg2=2.0.22-3ubuntu1.3 \
        haveged=1.7c-1 \
        libffi-dev=3.1~rc1+r3.0.13-12ubuntu0.2 \
        libssl-dev=1.0.1f-1ubuntu2.25 \
        ntp=1:4.2.6.p5+dfsg-3ubuntu2.14.04.12 \
        inotify-tools=3.14-1ubuntu1 \
        python-dev=2.7.5-5ubuntu3 \
        ruby=1:1.9.3.4 \
        secure-delete=3.1-6 \
        sqlite=2.8.17-10ubuntu2 \
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/*

RUN paxctl -cm /usr/bin/python2.7
RUN mkdir -p /tmp/build
