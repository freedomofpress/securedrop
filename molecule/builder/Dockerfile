ARG IMAGE
FROM $IMAGE

# additional meta-data makes it easier to clean up, find
ARG NAME
LABEL org="Freedom of the Press"
LABEL image_name="$NAME"

RUN apt-get -y update && apt-get install -y python rsync sudo bash \
            devscripts git aptitude ipython libssl-dev ntp \
            python-dev python-pip python-ipdb ruby tmux vim paxctl && \
            aptitude -y dist-upgrade && \
            apt-get clean
