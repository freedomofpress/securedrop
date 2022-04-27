# sha256 as of 2022-04-27
FROM nginx:mainline-alpine@sha256:efc09388b15fb423c402f0b8b28ca70c7fd20fe31f8d7531ae1896bbb4944999
RUN apk --no-cache upgrade

COPY devops/demo/landing-page/nginx.conf /etc/nginx
RUN mkdir -p /opt/nginx/run /opt/nginx/webroot && chown -R nginx:nginx /opt/nginx
COPY --chown=nginx:nginx devops/demo/landing-page/webroot /opt/nginx/webroot

USER nginx
EXPOSE 8000
