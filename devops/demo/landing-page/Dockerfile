# sha256 as of 2022-02-16
FROM nginx:mainline-alpine@sha256:050385609d832fae11b007fbbfba77d0bba12bf72bc0dca0ac03e09b1998580f
RUN apk --no-cache upgrade

COPY nginx.conf /etc/nginx
RUN mkdir -p /opt/nginx/run /opt/nginx/webroot && chown -R nginx:nginx /opt/nginx
COPY --chown=nginx:nginx webroot /opt/nginx/webroot

USER nginx
EXPOSE 8000
