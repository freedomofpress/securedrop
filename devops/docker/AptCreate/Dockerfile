FROM debian:jessie

# User provided User ID #
ARG UID

# reprepro args
ENV REP_CODENAME=trusty
ARG REP_COMPONENTS=main
ARG REP_ARCH="i386 amd64"

ENV REPO_DIR=/var/repos
ENV REPREPRO_CONFIG_DIR=$REPO_DIR/conf
ENV REPREPRO_BASE_DIR=$REPO_DIR/base

RUN apt-get update &&\
    apt-get install reprepro python -y &&\
    rm -rf /var/lib/apt/lists/*

RUN getent passwd $USER_ID || \
        adduser --disabled-password --quiet --gecos "docker_user," -uid $UID apt_user && \
    mkdir -p ${REPREPRO_CONFIG_DIR} ${REPREPRO_BASE_DIR} && \
    chown ${UID} -R ${REPO_DIR}

COPY apt-test.priv /tmp
COPY entry.sh /usr/local/bin
WORKDIR /var/repos/base

USER $UID

CMD bash /usr/local/bin/entry.sh
