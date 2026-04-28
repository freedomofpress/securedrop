# debian:trixie 2025-08-25
FROM debian@sha256:6d87375016340817ac2391e670971725a9981cfc24e221c47734681ed0f6c0f5
ARG USER_NAME
ENV USER_NAME=${USER_NAME:-root}
ARG USER_ID
ENV USER_ID=${USER_ID:-0}

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# Install deps for building securedrop-admin package
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get -y update && \
    apt-get -y upgrade && \
    apt-get -y install \
    coreutils \
    debhelper \
    devscripts \
    dh-python \
    make \
    pkg-config \
    python3-all \
    python3-pip \
    python3-setuptools \
    python3-venv \
    rsync \
    sudo \
    tzdata \
    unzip \
    virtualenv \
    gnupg2 \
    git

# Add user if necessary
RUN if test $USER_NAME != root ; then \
        useradd --no-create-home --home-dir /tmp --uid $USER_ID $USER_NAME && \
        echo "$USER_NAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers ; \
    fi

WORKDIR /src
COPY . /src

# Build and install the securedrop-admin package
ENV PATH="/usr/share/securedrop-admin/venv/bin:$PATH"
RUN ln -s /src/builder/fixup-changelog.sh /fixup-changelog
RUN /src/builder/build-debs-admin.sh
RUN apt-get install -y /src/build/trixie/securedrop-admin_*+trixie_amd64.deb

# Install dev dependencies in a separate venv
RUN /usr/bin/python3 -m venv /opt/admin-dev/venv
RUN /opt/admin-dev/venv/bin/pip install --no-deps --require-hashes -r /src/admin/requirements-dev.txt

WORKDIR /src/admin

RUN chown -R $USER_NAME /src
