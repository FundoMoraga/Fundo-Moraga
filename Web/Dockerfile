FROM nginx:alpine

# Copiar configuración de nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Copiar archivos del sitio
COPY . /usr/share/nginx/html/
RUN rm -f /usr/share/nginx/html/Dockerfile \
    /usr/share/nginx/html/nginx.conf \
    /usr/share/nginx/html/railway.json \
    /usr/share/nginx/html/MEJORAS-PREMIUM.md

# Exponer puerto 8080
EXPOSE 8080

# Iniciar nginx
CMD ["nginx", "-g", "daemon off;"]
