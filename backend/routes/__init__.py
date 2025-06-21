#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================
ECPlacas 2.0 SRI COMPLETO - Módulo de Rutas
==========================================
Proyecto: Construcción de Software
Desarrollado por: Erick Costa
Versión: 2.0.1
==========================================

Módulo de rutas centralizadas para ECPlacas 2.0
Organiza las rutas por funcionalidad para mejor mantenimiento
"""

from flask import Blueprint

# Importar blueprints de rutas específicas
from .api_routes import api_bp
from .frontend_routes import frontend_bp
from .admin_routes import admin_bp

def register_routes(app):
    """
    Registrar todas las rutas en la aplicación Flask
    
    Args:
        app: Instancia de Flask
    """
    try:
        # Registrar blueprint de API
        app.register_blueprint(api_bp, url_prefix='/api')
        
        # Registrar blueprint de frontend
        app.register_blueprint(frontend_bp)
        
        # Registrar blueprint de admin
        app.register_blueprint(admin_bp, url_prefix='/admin')
        
        print("✅ Rutas registradas correctamente:")
        print("   📡 API: /api/*")
        print("   🎨 Frontend: /*")
        print("  ⚙️ Admin: /admin/*")
        
    except Exception as e:
        print(f"❌ Error registrando rutas: {e}")
        raise

__all__ = ['register_routes', 'api_bp', 'frontend_bp', 'admin_bp']