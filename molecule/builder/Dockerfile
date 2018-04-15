ARG IMAGE
FROM $IMAGE

# additional meta-data makes it easier to clean up, find
ARG NAME
LABEL org="Freedom of the Press"
LABEL image_name="$NAME"

# Build dependencies must not be added here, they are listed
# in install_files/ansible-base/group_vars/all/securedrop
RUN apt-get -y update && apt-get install -y python rsync sudo bash aptitude && \
            aptitude -y dist-upgrade && \
            apt-get clean
