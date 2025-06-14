#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECPlacas 2.0 - Paquete de Rutas
Proyecto: Construcción de Software
Desarrollado por: Erick Costa

Inicialización del paquete de rutas
"""

from .api_routes import api_bp
from .frontend_routes import frontend_bp
from .admin_routes import admin_bp

__all__ = ['api_bp', 'frontend_bp', 'admin_bp']
