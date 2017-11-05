# ubuntu:14.04 as of 2017-11-05
FROM ubuntu@sha256:f6eed4def93a3b54da920737f0abf1a8cae2e480bb368280c898265fcaf910a3

RUN apt-get update # 2017-11-05
RUN apt-get install -y \
	python-pip libpython2.7-dev libssl-dev secure-delete gnupg2 ruby redis-server
# refs securedrop/issues/1594
RUN gem install sass -v 3.4.23

WORKDIR /app

COPY requirements requirements
RUN pip install -r requirements/securedrop-requirements.txt

#skip-if-test
COPY static static
#skip-if-test
COPY sass sass
#skip-if-test
RUN sass --force --stop-on-error --update sass:static/css --style compressed

#skip-if-test
COPY . /app

EXPOSE 8080 8081
CMD ["./manage.py", "run"]
