FROM nginx:alpine
# Copiar configuración de nginx
COPY nginx.conf /etc/nginx/nginx.conf

COPY docker-entrypoint.d/10-seed-assets.sh /docker-entrypoint.d/10-seed-assets.sh

COPY . /usr/share/nginx/html/
RUN chmod +x /docker-entrypoint.d/10-seed-assets.sh \
    && mkdir -p /seed \
    && if [ -d /usr/share/nginx/html/assets ]; then mv /usr/share/nginx/html/assets /seed/assets; fi \
    && rm -f /usr/share/nginx/html/Dockerfile \
    /usr/share/nginx/html/nginx.conf \
    /usr/share/nginx/html/railway.json \
    /usr/share/nginx/html/MEJORAS-PREMIUM.md \
    && rm -rf /usr/share/nginx/html/docker-entrypoint.d

# Exponer puerto 8080
EXPOSE 8080

# Iniciar nginx
CMD ["nginx", "-g", "daemon off;"]
