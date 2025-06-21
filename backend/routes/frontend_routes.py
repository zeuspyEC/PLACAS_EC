#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================
ECPlacas 2.0 SRI COMPLETO - Rutas de Frontend
==========================================
Proyecto: Construcción de Software
Desarrollado por: Erick Costa
Versión: 2.0.1
==========================================

Rutas que complementan las del app.py para servir archivos estáticos
y manejar el frontend de manera optimizada
"""

import os
import mimetypes
import logging
from pathlib import Path
from flask import Blueprint, send_from_directory, send_file, request, current_app, abort
from werkzeug.exceptions import NotFound

# Crear blueprint para rutas de frontend
frontend_bp = Blueprint('frontend', __name__)

logger = logging.getLogger('ecplacas.frontend')

# ==========================================
# CONFIGURACIÓN DE PATHS
# ==========================================

def get_frontend_path():
    """Obtener path del directorio frontend"""
    # Buscar en varios lugares posibles
    possible_paths = [
        Path(current_app.root_path).parent / "frontend",  # ../frontend desde backend
        Path(current_app.root_path) / "frontend",         # ./frontend desde raíz
        Path(current_app.root_path) / "static",           # ./static como fallback
        Path(current_app.root_path) / ".." / ".." / "frontend"  # ../../frontend
    ]
    
    for path in possible_paths:
        if path.exists() and (path / "index.html").exists():
            return path
    
    # Si no encuentra, usar el primero como default
    return possible_paths[0]

def get_static_path():
    """Obtener path del directorio de archivos estáticos"""
    frontend_path = get_frontend_path()
    static_paths = [
        frontend_path / "assets",
        frontend_path / "static", 
        frontend_path,
        Path(current_app.root_path) / "static"
    ]
    
    for path in static_paths:
        if path.exists():
            return path
    
    return static_paths[0]

# ==========================================
# MIDDLEWARE
# ==========================================

@frontend_bp.before_request
def before_frontend_request():
    """Middleware para requests de frontend"""
    # Log solo para requests importantes
    if not request.path.startswith(('/css/', '/js/', '/img/', '/assets/')):
        logger.info(f"Frontend: {request.method} {request.path} from {request.remote_addr}")

@frontend_bp.after_request
def after_frontend_request(response):
    """Middleware de respuesta para frontend"""
    # Headers de cache optimizados según tipo de archivo
    if request.path.endswith(('.css', '.js')):
        response.headers['Cache-Control'] = 'public, max-age=86400'  # 24 horas
    elif request.path.endswith(('.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg')):
        response.headers['Cache-Control'] = 'public, max-age=604800'  # 7 días
    elif request.path.endswith('.html'):
        response.headers['Cache-Control'] = 'public, max-age=300'  # 5 minutos
    
    # Headers de seguridad
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    return response

# ==========================================
# RUTAS DE ARCHIVOS ESTÁTICOS
# ==========================================

@frontend_bp.route('/css/<path:filename>')
def serve_css(filename):
    """Servir archivos CSS optimizados"""
    try:
        frontend_path = get_frontend_path()
        css_paths = [
            frontend_path / "css",
            frontend_path / "assets" / "css",
            frontend_path
        ]
        
        for css_path in css_paths:
            file_path = css_path / filename
            if file_path.exists():
                response = send_file(file_path, mimetype='text/css')
                response.headers['Cache-Control'] = 'public, max-age=86400'
                return response
        
        logger.warning(f"CSS file not found: {filename}")
        abort(404)
        
    except Exception as e:
        logger.error(f"Error serving CSS {filename}: {e}")
        abort(500)

@frontend_bp.route('/js/<path:filename>')
def serve_js(filename):
    """Servir archivos JavaScript optimizados"""
    try:
        frontend_path = get_frontend_path()
        js_paths = [
            frontend_path / "js",
            frontend_path / "assets" / "js",
            frontend_path
        ]
        
        for js_path in js_paths:
            file_path = js_path / filename
            if file_path.exists():
                response = send_file(file_path, mimetype='application/javascript')
                response.headers['Cache-Control'] = 'public, max-age=86400'
                return response
        
        logger.warning(f"JS file not found: {filename}")
        abort(404)
        
    except Exception as e:
        logger.error(f"Error serving JS {filename}: {e}")
        abort(500)

@frontend_bp.route('/img/<path:filename>')
@frontend_bp.route('/images/<path:filename>')
@frontend_bp.route('/assets/img/<path:filename>')
def serve_images(filename):
    """Servir archivos de imagen optimizados"""
    try:
        frontend_path = get_frontend_path()
        img_paths = [
            frontend_path / "img",
            frontend_path / "images", 
            frontend_path / "assets" / "img",
            frontend_path / "assets" / "images",
            frontend_path
        ]
        
        for img_path in img_paths:
            file_path = img_path / filename
            if file_path.exists():
                # Detectar MIME type automáticamente
                mimetype, _ = mimetypes.guess_type(str(file_path))
                response = send_file(file_path, mimetype=mimetype)
                response.headers['Cache-Control'] = 'public, max-age=604800'  # 7 días
                return response
        
        logger.warning(f"Image file not found: {filename}")
        abort(404)
        
    except Exception as e:
        logger.error(f"Error serving image {filename}: {e}")
        abort(500)

@frontend_bp.route('/assets/<path:filename>')
def serve_assets(filename):
    """Servir archivos de assets generales"""
    try:
        frontend_path = get_frontend_path()
        assets_paths = [
            frontend_path / "assets",
            frontend_path
        ]
        
        for assets_path in assets_paths:
            file_path = assets_path / filename
            if file_path.exists():
                # Detectar MIME type
                mimetype, _ = mimetypes.guess_type(str(file_path))
                if not mimetype:
                    mimetype = 'application/octet-stream'
                
                response = send_file(file_path, mimetype=mimetype)
                
                # Cache según extensión
                if filename.endswith(('.css', '.js')):
                    response.headers['Cache-Control'] = 'public, max-age=86400'
                elif filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg')):
                    response.headers['Cache-Control'] = 'public, max-age=604800'
                else:
                    response.headers['Cache-Control'] = 'public, max-age=3600'
                
                return response
        
        logger.warning(f"Asset file not found: {filename}")
        abort(404)
        
    except Exception as e:
        logger.error(f"Error serving asset {filename}: {e}")
        abort(500)

# ==========================================
# RUTAS DE FAVICON Y ROBOTS
# ==========================================

@frontend_bp.route('/favicon.ico')
def favicon():
    """Servir favicon"""
    try:
        frontend_path = get_frontend_path()
        favicon_paths = [
            frontend_path / "favicon.ico",
            frontend_path / "img" / "favicon.ico",
            frontend_path / "assets" / "img" / "favicon.ico"
        ]
        
        for favicon_path in favicon_paths:
            if favicon_path.exists():
                response = send_file(favicon_path, mimetype='image/x-icon')
                response.headers['Cache-Control'] = 'public, max-age=604800'
                return response
        
        # Generar favicon básico si no existe
        return generate_basic_favicon()
        
    except Exception as e:
        logger.error(f"Error serving favicon: {e}")
        abort(404)

@frontend_bp.route('/robots.txt')
def robots_txt():
    """Servir robots.txt"""
    try:
        frontend_path = get_frontend_path()
        robots_path = frontend_path / "robots.txt"
        
        if robots_path.exists():
            return send_file(robots_path, mimetype='text/plain')
        else:
            # Generar robots.txt básico
            robots_content = """User-agent: *
Allow: /
Disallow: /api/
Disallow: /admin/
Sitemap: /sitemap.xml
"""
            from flask import Response
            return Response(robots_content, mimetype='text/plain')
        
    except Exception as e:
        logger.error(f"Error serving robots.txt: {e}")
        abort(500)

@frontend_bp.route('/manifest.json')
def manifest():
    """Servir manifest.json para PWA"""
    try:
        frontend_path = get_frontend_path()
        manifest_path = frontend_path / "manifest.json"
        
        if manifest_path.exists():
            return send_file(manifest_path, mimetype='application/json')
        else:
            # Generar manifest básico
            manifest_data = {
                "name": "ECPlacas 2.0 SRI COMPLETO",
                "short_name": "ECPlacas 2.0",
                "description": "Sistema de Consulta Vehicular SRI + Propietario",
                "start_url": "/",
                "display": "standalone",
                "background_color": "#000033",
                "theme_color": "#00ffff",
                "icons": [
                    {
                        "src": "/img/icon-192.png",
                        "sizes": "192x192",
                        "type": "image/png"
                    },
                    {
                        "src": "/img/icon-512.png", 
                        "sizes": "512x512",
                        "type": "image/png"
                    }
                ]
            }
            
            from flask import jsonify
            response = jsonify(manifest_data)
            response.headers['Cache-Control'] = 'public, max-age=86400'
            return response
        
    except Exception as e:
        logger.error(f"Error serving manifest.json: {e}")
        abort(500)

# ==========================================
# FUNCIONES AUXILIARES
# ==========================================

def generate_basic_favicon():
    """Generar favicon básico si no existe"""
    try:
        # Crear un favicon básico de 16x16 en formato ICO
        # Esto es un placeholder - en producción usar un favicon real
        from flask import Response
        
        # ICO file header para 16x16 favicon básico (azul)
        ico_data = b'\x00\x00\x01\x00\x01\x00\x10\x10\x00\x00\x01\x00\x20\x00\x68\x04\x00\x00\x16\x00\x00\x00'
        
        response = Response(ico_data, mimetype='image/x-icon')
        response.headers['Cache-Control'] = 'public, max-age=86400'
        return response
        
    except Exception as e:
        logger.error(f"Error generating basic favicon: {e}")
        abort(404)

# ==========================================
# MANEJO DE ERRORES ESPECÍFICO PARA FRONTEND
# ==========================================

@frontend_bp.errorhandler(404)
def frontend_not_found(error):
    """Manejo de 404 para archivos estáticos"""
    # Para archivos estáticos, retornar 404 normal
    if request.path.startswith(('/css/', '/js/', '/img/', '/assets/')):
        logger.warning(f"Static file not found: {request.path}")
        abort(404)
    
    # Para otras rutas, podría redirigir al index.html (SPA)
    try:
        frontend_path = get_frontend_path()
        index_path = frontend_path / "index.html"
        
        if index_path.exists():
            logger.info(f"SPA fallback: {request.path} -> index.html")
            return send_file(index_path, mimetype='text/html')
        else:
            abort(404)
            
    except Exception as e:
        logger.error(f"Error in frontend 404 handler: {e}")
        abort(404)

# ==========================================
# RUTAS DE UTILIDADES DE FRONTEND
# ==========================================

@frontend_bp.route('/healthcheck')
def frontend_healthcheck():
    """Healthcheck específico para frontend"""
    try:
        frontend_path = get_frontend_path()
        index_exists = (frontend_path / "index.html").exists()
        
        return {
            'success': True,
            'frontend_available': index_exists,
            'frontend_path': str(frontend_path),
            'static_files': {
                'css': len(list((frontend_path / "css").glob("*.css"))) if (frontend_path / "css").exists() else 0,
                'js': len(list((frontend_path / "js").glob("*.js"))) if (frontend_path / "js").exists() else 0,
                'images': len(list((frontend_path / "img").glob("*"))) if (frontend_path / "img").exists() else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error in frontend healthcheck: {e}")
        return {'success': False, 'error': str(e)}, 500

if __name__ == "__main__":
    print("🎨 Módulo de rutas de Frontend para ECPlacas 2.0")
    print("📁 Rutas incluidas:")
    print("   - /css/<filename> - Archivos CSS")
    print("   - /js/<filename> - Archivos JavaScript")
    print("   - /img/<filename> - Archivos de imagen")
    print("   - /assets/<filename> - Assets generales")
    print("   - /favicon.ico - Favicon")
    print("   - /robots.txt - Robots.txt")
    print("   - /manifest.json - PWA Manifest")
    print("   - /healthcheck - Estado del frontend")