"""
Middleware de compresión y headers de seguridad para Flask
Optimiza performance y mejora seguridad
"""
from flask import Flask, request, make_response
from functools import wraps
import gzip
import io

def add_security_headers(app: Flask):
    """Añade headers de seguridad HTTP a todas las respuestas"""
    
    @app.after_request
    def set_security_headers(response):
        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy (CSP)
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://www.googletagmanager.com https://www.google-analytics.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https: blob:; "
            "connect-src 'self' https://www.google-analytics.com https://*.blob.core.windows.net; "
            "frame-src 'self' https://www.youtube.com; "
            "media-src 'self' https://*.blob.core.windows.net;"
        )
        response.headers['Content-Security-Policy'] = csp
        
        # HTTPS enforcement (solo en producción)
        if not request.url.startswith('http://localhost'):
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Performance hints
        response.headers['X-DNS-Prefetch-Control'] = 'on'
        
        return response
    
    print("✅ Security headers configurados")


def add_compression(app: Flask):
    """Añade compresión gzip a respuestas grandes"""
    
    @app.after_request
    def compress_response(response):
        # Solo comprimir si el cliente acepta gzip
        accept_encoding = request.headers.get('Accept-Encoding', '')
        
        if 'gzip' not in accept_encoding.lower():
            return response
        
        # Solo comprimir ciertos content types
        compressible_types = [
            'text/html',
            'text/css',
            'text/javascript',
            'application/javascript',
            'application/json',
            'application/xml',
            'text/xml'
        ]
        
        content_type = response.headers.get('Content-Type', '')
        if not any(ct in content_type for ct in compressible_types):
            return response
        
        # Solo comprimir respuestas grandes (> 1KB)
        if response.content_length and response.content_length < 1024:
            return response
        
        # Comprimir
        try:
            gzip_buffer = io.BytesIO()
            with gzip.GzipFile(mode='wb', fileobj=gzip_buffer) as gzip_file:
                gzip_file.write(response.get_data())
            
            compressed_data = gzip_buffer.getvalue()
            
            # Solo usar compresión si reduce tamaño significativamente
            original_size = len(response.get_data())
            compressed_size = len(compressed_data)
            
            if compressed_size < original_size * 0.9:  # Al menos 10% de reducción
                response.set_data(compressed_data)
                response.headers['Content-Encoding'] = 'gzip'
                response.headers['Content-Length'] = len(compressed_data)
                response.headers['Vary'] = 'Accept-Encoding'
        
        except Exception as e:
            print(f"⚠️  Error comprimiendo respuesta: {e}")
        
        return response
    
    print("✅ Compresión gzip configurada")


def add_cache_headers(app: Flask):
    """Añade headers de caching para assets estáticos"""
    
    @app.after_request
    def set_cache_headers(response):
        # Cache agresivo para assets versionados
        path = request.path
        
        # Assets con versión en nombre (cache 1 año)
        if any(ext in path for ext in ['.20260126-1.', '.v1.', '.min.']):
            response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
        
        # CSS/JS generales (cache 1 día)
        elif path.endswith(('.css', '.js')) and '/css/' in path:
            response.headers['Cache-Control'] = 'public, max-age=86400'
        
        # Imágenes (cache 1 semana)
        elif path.endswith(('.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.ico')):
            response.headers['Cache-Control'] = 'public, max-age=604800'
        
        # Fuentes (cache 1 mes)
        elif path.endswith(('.woff', '.woff2', '.ttf', '.eot')):
            response.headers['Cache-Control'] = 'public, max-age=2592000'
        
        # HTML del blog (cache 1 hora con revalidación)
        elif '/blog/' in path and path.endswith('.html'):
            response.headers['Cache-Control'] = 'public, max-age=3600, must-revalidate'
        
        # HTML principal (no cache - siempre fresco)
        elif path.endswith('.html') or path == '/':
            response.headers['Cache-Control'] = 'no-cache, must-revalidate'
        
        # APIs (no cache)
        elif '/api/' in path:
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
        
        return response
    
    print("✅ Cache headers configurados")


def setup_middleware(app: Flask):
    """Configura todos los middlewares de optimización"""
    print("\n🔧 Configurando middleware de optimización...")
    
    add_security_headers(app)
    add_compression(app)
    add_cache_headers(app)
    
    print("✅ Middleware configurado completamente\n")
