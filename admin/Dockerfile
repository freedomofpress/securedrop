# debian:bookworm 2024-01-12
FROM debian@sha256:b16cef8cbcb20935c0f052e37fc3d38dc92bfec0bcfb894c328547f81e932d67
ARG USER_NAME
ENV USER_NAME ${USER_NAME:-root}
ARG USER_ID
ENV USER_ID ${USER_ID:-0}

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

RUN apt-get update && \
    apt-get install -y python3 sudo gnupg2 git
RUN if test $USER_NAME != root ; then useradd --no-create-home --home-dir /tmp --uid $USER_ID $USER_NAME && echo "$USER_NAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers ; fi

WORKDIR /opt/admin
COPY . /opt
RUN rm -rf /opt/admin/.venv3
RUN cd /opt/admin && python3 bootstrap.py -v
ENV VIRTUAL_ENV /opt/admin/.venv3
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip3 install --no-deps --require-hashes -r /opt/admin/requirements-dev.txt

RUN chown -R $USER_NAME /opt
