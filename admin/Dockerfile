# debian:buster 2020-08-04
FROM debian@sha256:1e74c92df240634a39d050a5e23fb18f45df30846bb222f543414da180b47a5d
ARG USER_NAME
ENV USER_NAME ${USER_NAME:-root}
ARG USER_ID
ENV USER_ID ${USER_ID:-0}

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

RUN apt-get update && \
    apt-get install -y python3 sudo lsb-release gnupg2 git
RUN if test $USER_NAME != root ; then useradd --no-create-home --home-dir /tmp --uid $USER_ID $USER_NAME && echo "$USER_NAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers ; fi

WORKDIR /opt/admin
COPY . /opt
RUN rm -rf /opt/admin/.venv3
RUN cd /opt/admin && python3 bootstrap.py -v
ENV VIRTUAL_ENV /opt/admin/.venv3
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip3 install --no-deps --require-hashes -r /opt/admin/requirements-dev.txt

RUN chown -R $USER_NAME /opt
