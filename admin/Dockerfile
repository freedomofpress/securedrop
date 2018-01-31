# debian:stretch Thu Jan 25 08:58:24 CET 2018
FROM debian@sha256:0a5fcee6f52d5170f557ee2447d7a10a5bdcf715dd7f0250be0b678c556a501b
ARG USER_NAME
ENV USER_NAME ${USER_NAME:-root}
ARG USER_ID
ENV USER_ID ${USER_ID:-0}

RUN apt-get update
RUN apt-get install -y python sudo lsb-release gnupg2
RUN if test $USER_NAME != root ; then useradd --no-create-home --home-dir /tmp --uid $USER_ID $USER_NAME && echo "$USER_NAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers ; fi

WORKDIR /opt
COPY bootstrap.py .
COPY requirements.txt .
RUN python bootstrap.py -v
COPY requirements-dev.txt .
RUN .venv/bin/pip install -r requirements-dev.txt
COPY . .
