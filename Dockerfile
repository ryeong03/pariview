FROM nginx:stable-alpine
ENV PORT=8080
ENV NGINX_ENVSUBST_FILTER=PORT
COPY deploy/default.conf.template /etc/nginx/templates/default.conf.template
COPY web/dist/ /usr/share/nginx/html/
EXPOSE 8080
