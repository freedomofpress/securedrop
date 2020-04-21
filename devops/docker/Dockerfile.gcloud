FROM centos:7 as gcloud-downloader
ARG GCLOUD_VERSION
LABEL org="Freedom of the Press"
LABEL image_name="gcloud-sdk-centos7"

COPY devops/docker/google-cloud-sdk.repo /etc/yum.repos.d/google-cloud-sdk.repo
COPY devops/docker/gce-rpm-key.gpg /etc/pki/rpm-gpg/
COPY devops/docker/gce-yum-key.gpg /etc/pki/rpm-gpg/

RUN rpm --import /etc/pki/rpm-gpg/gce-rpm-key.gpg && \
    rpm --import /etc/pki/rpm-gpg/gce-yum-key.gpg

RUN rpm --import /etc/pki/rpm-gpg/gce* && \
    yum install google-cloud-sdk-${GCLOUD_VERSION}.el7.noarch -y && \
    yum clean all && rm -rf /var/cache/yum

COPY devops/docker/gcloud-wrapper.sh /usr/bin/gcloud-wrapper
RUN useradd gcloud && \
    chmod +x /usr/bin/gcloud-wrapper
USER gcloud
ENTRYPOINT ["/usr/bin/gcloud-wrapper"]
