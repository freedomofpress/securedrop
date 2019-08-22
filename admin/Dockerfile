# debian:stretch 2019-01-22
FROM debian@sha256:21ac5961a3038a839f6fa92ec4583c90f9eb6ca8f580598cde19d35d0f4d8fa6
ARG USER_NAME
ENV USER_NAME ${USER_NAME:-root}
ARG USER_ID
ENV USER_ID ${USER_ID:-0}

RUN apt-get update && \
    apt-get install -y python sudo lsb-release gnupg2 git
RUN if test $USER_NAME != root ; then useradd --no-create-home --home-dir /tmp --uid $USER_ID $USER_NAME && echo "$USER_NAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers ; fi

WORKDIR /opt
COPY bootstrap.py .
COPY requirements.txt .
RUN python bootstrap.py -v
ENV VIRTUAL_ENV /opt/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
COPY requirements-dev.txt .
RUN pip install --require-hashes -r requirements-dev.txt
# Now also pin pip due to https://github.com/jazzband/pip-tools/issues/853
RUN pip install pip==19.1

RUN chown -R $USER_NAME /opt
