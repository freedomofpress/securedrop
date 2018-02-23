# ubuntu:14.04 as of 2017-12-15
FROM ubuntu@sha256:084989eb923bd86dbf7e706d464cf3587274a826b484f75b69468c19f8ae354c

RUN apt-get -y update && apt-get install -y python rsync sudo bash \
            devscripts git aptitude ipython libssl-dev ntp \
            python-dev python-pip python-ipdb ruby tmux vim paxctl && \
            aptitude -y dist-upgrade && \
            apt-get clean
