FROM nginx:alpine

# Render debe desplegar la página web estática, no el backend Python.
COPY Web/nginx.conf /etc/nginx/nginx.conf
COPY Web/docker-entrypoint.d/10-seed-assets.sh /docker-entrypoint.d/10-seed-assets.sh
COPY Web/ /usr/share/nginx/html/

RUN chmod +x /docker-entrypoint.d/10-seed-assets.sh \
    && mkdir -p /seed \
    && if [ -d /usr/share/nginx/html/assets ]; then mv /usr/share/nginx/html/assets /seed/assets; fi \
    && rm -f /usr/share/nginx/html/Dockerfile \
    /usr/share/nginx/html/nginx.conf \
    /usr/share/nginx/html/railway.json \
    /usr/share/nginx/html/MEJORAS-PREMIUM.md \
    && rm -rf /usr/share/nginx/html/docker-entrypoint.d

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
