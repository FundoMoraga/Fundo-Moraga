FROM nginx:alpine

# Copiar configuración de nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Copiar archivos del sitio
COPY index.html historia.html leyenda.html mapa.html /usr/share/nginx/html/
COPY styles.css script.js leyenda-styles.css leyenda-script.js mapa-styles.css mapa-script.js transitions.js /usr/share/nginx/html/
COPY assets /usr/share/nginx/html/assets/

# Exponer puerto 8080
EXPOSE 8080

# Iniciar nginx
CMD ["nginx", "-g", "daemon off;"]
