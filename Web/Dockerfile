FROM nginx:alpine

# Copiar configuración de nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Copiar archivos del sitio
COPY index.html historia.html leyenda.html /usr/share/nginx/html/
COPY styles.css script.js leyenda-styles.css leyenda-script.js /usr/share/nginx/html/
COPY assets /usr/share/nginx/html/assets/

# Exponer puerto 8080
EXPOSE 8080

# Iniciar nginx
CMD ["nginx", "-g", "daemon off;"]
