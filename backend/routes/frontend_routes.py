#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECPlacas 2.0 - Rutas de Frontend
Proyecto: Construcción de Software
Desarrollado por: Erick Costa

Rutas para servir archivos del frontend
"""

import os
from flask import Blueprint, send_from_directory, send_file, current_app
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Crear blueprint para rutas de frontend
frontend_bp = Blueprint('frontend', __name__)

# Obtener rutas del proyecto
PROJECT_ROOT = Path(__file__).parent.parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
PUBLIC_DIR = PROJECT_ROOT / "public"

@frontend_bp.route('/')
def index():
    """Página principal de ECPlacas 2.0"""
    try:
        index_path = FRONTEND_DIR / "index.html"
        if index_path.exists():
            return send_file(index_path)
        else:
            return """
            <html>
            <head><title>ECPlacas 2.0 - Error</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px; background: #000; color: #00ffff;">
                <h1>🚫 ECPlacas 2.0</h1>
                <h2>Archivo index.html no encontrado</h2>
                <p>Por favor verifique que el archivo frontend/index.html existe</p>
                <p><a href="/api/health" style="color: #00ffff;">Verificar API</a></p>
            </body>
            </html>
            """, 404
    except Exception as e:
        logger.error(f"Error sirviendo index.html: {e}")
        return f"Error cargando página principal: {e}", 500

@frontend_bp.route('/admin')
def admin():
    """Dashboard administrativo de ECPlacas 2.0"""
    try:
        admin_path = FRONTEND_DIR / "admin.html"
        if admin_path.exists():
            return send_file(admin_path)
        else:
            return """
            <html>
            <head><title>ECPlacas 2.0 Admin - Error</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px; background: #000; color: #00ffff;">
                <h1>🔧 ECPlacas 2.0 - Dashboard Admin</h1>
                <h2>Archivo admin.html no encontrado</h2>
                <p>Por favor verifique que el archivo frontend/admin.html existe</p>
                <p><a href="/" style="color: #00ffff;">Volver al Frontend</a></p>
            </body>
            </html>
            """, 404
    except Exception as e:
        logger.error(f"Error sirviendo admin.html: {e}")
        return f"Error cargando dashboard administrativo: {e}", 500

@frontend_bp.route('/static/<path:filename>')
def static_files(filename):
    """Servir archivos estáticos desde public/"""
    try:
        return send_from_directory(PUBLIC_DIR, filename)
    except Exception as e:
        logger.error(f"Error sirviendo archivo estático {filename}: {e}")
        return f"Archivo {filename} no encontrado", 404

@frontend_bp.route('/frontend/<path:filename>')
def frontend_files(filename):
    """Servir archivos del frontend"""
    try:
        return send_from_directory(FRONTEND_DIR, filename)
    except Exception as e:
        logger.error(f"Error sirviendo archivo frontend {filename}: {e}")
        return f"Archivo {filename} no encontrado", 404

@frontend_bp.route('/css/<path:filename>')
def css_files(filename):
    """Servir archivos CSS desde public/css/"""
    try:
        css_dir = PUBLIC_DIR / "css"
        return send_from_directory(css_dir, filename)
    except Exception as e:
        logger.error(f"Error sirviendo CSS {filename}: {e}")
        return f"Archivo CSS {filename} no encontrado", 404

@frontend_bp.route('/js/<path:filename>')
def js_files(filename):
    """Servir archivos JavaScript desde public/js/"""
    try:
        js_dir = PUBLIC_DIR / "js"
        return send_from_directory(js_dir, filename)
    except Exception as e:
        logger.error(f"Error sirviendo JS {filename}: {e}")
        return f"Archivo JS {filename} no encontrado", 404

@frontend_bp.route('/images/<path:filename>')
def image_files(filename):
    """Servir imágenes desde public/images/"""
    try:
        images_dir = PUBLIC_DIR / "images"
        return send_from_directory(images_dir, filename)
    except Exception as e:
        logger.error(f"Error sirviendo imagen {filename}: {e}")
        return f"Imagen {filename} no encontrada", 404

@frontend_bp.route('/fonts/<path:filename>')
def font_files(filename):
    """Servir fuentes desde public/fonts/"""
    try:
        fonts_dir = PUBLIC_DIR / "fonts"
        return send_from_directory(fonts_dir, filename)
    except Exception as e:
        logger.error(f"Error sirviendo fuente {filename}: {e}")
        return f"Fuente {filename} no encontrada", 404

@frontend_bp.route('/favicon.ico')
def favicon():
    """Favicon del sitio"""
    try:
        favicon_path = PUBLIC_DIR / "images" / "favicon.ico"
        if favicon_path.exists():
            return send_file(favicon_path)
        else:
            # Retornar un favicon por defecto si no existe
            return """
            <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
                <rect width="32" height="32" fill="#000"/>
                <text x="16" y="20" text-anchor="middle" fill="#00ffff" font-family="Arial" font-size="16" font-weight="bold">EC</text>
            </svg>
            """, 200, {'Content-Type': 'image/svg+xml'}
    except Exception as e:
        logger.error(f"Error sirviendo favicon: {e}")
        return "", 404

@frontend_bp.route('/manifest.json')
def manifest():
    """Manifest PWA"""
    manifest_data = {
        "name": "ECPlacas 2.0",
        "short_name": "ECPlacas",
        "description": "Sistema de Consulta Vehicular - Construcción de Software",
        "version": "2.0.0",
        "author": "Erick Costa",
        "start_url": "/",
        "display": "standalone",
        "theme_color": "#00ffff",
        "background_color": "#000000",
        "orientation": "portrait",
        "icons": [
            {
                "src": "/static/images/icon-192.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": "/static/images/icon-512.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    }
    
    return manifest_data, 200, {'Content-Type': 'application/json'}

@frontend_bp.route('/robots.txt')
def robots():
    """Archivo robots.txt"""
    robots_content = """User-agent: *
Disallow: /api/
Disallow: /admin/
Disallow: /static/
Allow: /

# ECPlacas 2.0 - Sistema de Consulta Vehicular
# Desarrollado por: Erick Costa
# Proyecto: Construcción de Software
"""
    
    return robots_content, 200, {'Content-Type': 'text/plain'}

@frontend_bp.route('/sitemap.xml')
def sitemap():
    """Sitemap XML básico"""
    sitemap_content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>http://localhost:5000/</loc>
        <lastmod>2024-12-15</lastmod>
        <changefreq>weekly</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>http://localhost:5000/admin</loc>
        <lastmod>2024-12-15</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
</urlset>"""
    
    return sitemap_content, 200, {'Content-Type': 'application/xml'}

@frontend_bp.route('/service-worker.js')
def service_worker():
    """Service Worker básico para PWA"""
    sw_content = """
// ECPlacas 2.0 - Service Worker
// Versión: 2.0.0
// Autor: Erick Costa

const CACHE_NAME = 'ecplacas-v2.0.0';
const urlsToCache = [
    '/',
    '/static/css/main.css',
    '/static/js/main.js',
    '/api/health'
];

// Instalación del Service Worker
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('ECPlacas 2.0: Cache abierto');
                return cache.addAll(urlsToCache);
            })
    );
});

// Interceptar requests
self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                // Retornar desde cache si existe
                if (response) {
                    return response;
                }
                return fetch(event.request);
            }
        )
    );
});

// Actualización del Service Worker
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('ECPlacas 2.0: Eliminando cache antiguo', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});
"""
    
    return sw_content, 200, {'Content-Type': 'application/javascript'}

# Manejador de errores 404 para el frontend
@frontend_bp.errorhandler(404)
def frontend_not_found(error):
    """Página 404 personalizada"""
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ECPlacas 2.0 - Página No Encontrada</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
            
            body {
                font-family: 'Orbitron', monospace;
                background: linear-gradient(135deg, #000 0%, #001122 50%, #000033 100%);
                color: #00ffff;
                margin: 0;
                padding: 0;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                text-align: center;
            }
            
            .container {
                background: rgba(0, 0, 0, 0.8);
                border: 2px solid #00ffff;
                border-radius: 20px;
                padding: 3rem;
                box-shadow: 0 0 30px rgba(0, 255, 255, 0.5);
            }
            
            h1 {
                font-size: 4rem;
                margin-bottom: 1rem;
                text-shadow: 0 0 20px #00ffff;
            }
            
            h2 {
                font-size: 2rem;
                margin-bottom: 2rem;
                color: #99ccff;
            }
            
            p {
                font-size: 1.2rem;
                margin-bottom: 2rem;
                color: #cccccc;
            }
            
            a {
                display: inline-block;
                background: linear-gradient(135deg, #0066ff, #00ffff);
                color: #000;
                padding: 1rem 2rem;
                text-decoration: none;
                border-radius: 25px;
                font-weight: bold;
                transition: all 0.3s ease;
                margin: 0 1rem;
            }
            
            a:hover {
                transform: translateY(-3px);
                box-shadow: 0 10px 25px rgba(0, 255, 255, 0.5);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>404</h1>
            <h2>Página No Encontrada</h2>
            <p>La página que busca no existe en ECPlacas 2.0</p>
            <div>
                <a href="/">🏠 Inicio</a>
                <a href="/admin">🔧 Admin</a>
                <a href="/api/health">🔍 API</a>
            </div>
        </div>
    </body>
    </html>
    """, 404
