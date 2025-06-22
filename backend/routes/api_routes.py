#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================
ECPlacas 2.0 SRI COMPLETO - Rutas de API
==========================================
Proyecto: Construcción de Software
Desarrollado por: Erick Costa
Versión: 2.0.1
==========================================

Rutas adicionales de API que complementan app.py
Estas rutas se integran con las principales del sistema
"""

import json
import logging
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request
from werkzeug.exceptions import BadRequest, NotFound

# Crear blueprint para rutas de API adicionales
api_bp = Blueprint("api_additional", __name__)

logger = logging.getLogger("ecplacas.api")

# ==========================================
# MIDDLEWARE Y DECORADORES
# ==========================================


@api_bp.before_request
def before_api_request():
    """Middleware para todas las rutas de API"""
    # Log de todas las requests API
    logger.info(
        f"API Request: {request.method} {request.path} from {request.remote_addr}"
    )

    # Verificar Content-Type para requests POST/PUT
    if request.method in ["POST", "PUT"] and request.content_type:
        if not request.content_type.startswith("application/json"):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Content-Type debe ser application/json",
                    }
                ),
                400,
            )


@api_bp.after_request
def after_api_request(response):
    """Middleware de respuesta para APIs"""
    # Agregar headers CORS adicionales
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"

    # Headers de cache
    if request.method == "GET":
        response.headers["Cache-Control"] = "public, max-age=300"  # 5 minutos

    return response


# ==========================================
# RUTAS DE INFORMACIÓN DEL SISTEMA
# ==========================================


@api_bp.route("/version", methods=["GET"])
def get_version():
    """Obtener información de versión del sistema"""
    try:
        version_info = {
            "success": True,
            "version": "2.0.1",
            "name": "ECPlacas 2.0 SRI COMPLETO",
            "author": "Erick Costa",
            "project": "Construcción de Software",
            "theme": "Futurista - Azul Neon",
            "release_date": "2024-12-15",
            "python_version": f"{current_app.config.get('PYTHON_VERSION', 'Unknown')}",
            "flask_version": f"{current_app.config.get('FLASK_VERSION', 'Unknown')}",
            "features": {
                "sri_completo": True,
                "propietario_vehiculo": True,
                "rubros_detallados": True,
                "componentes_fiscales": True,
                "historial_pagos": True,
                "plan_iacv": True,
                "analisis_consolidado": True,
                "cache_inteligente": True,
                "rate_limiting": True,
                "logs_rotativos": True,
            },
            "apis_disponibles": {
                "consulta_completa": "/api/consultar-vehiculo",
                "estado_consulta": "/api/estado-consulta/<session_id>",
                "resultado_completo": "/api/resultado/<session_id>",
                "estadisticas": "/api/estadisticas",
                "validar_placa": "/api/validar-placa",
                "validar_cedula": "/api/validar-cedula",
                "test_sri": "/api/test-sri-completo",
            },
            "timestamp": datetime.now().isoformat(),
        }

        return jsonify(version_info)

    except Exception as e:
        logger.error(f"Error obteniendo versión: {e}")
        return jsonify({"success": False, "error": "Error interno del servidor"}), 500


@api_bp.route("/features", methods=["GET"])
def get_features():
    """Obtener lista completa de características"""
    try:
        features = {
            "success": True,
            "sistema": "ECPlacas 2.0 SRI COMPLETO + PROPIETARIO",
            "caracteristicas_principales": [
                {
                    "categoria": "Consultas SRI",
                    "descripcion": "Consultas completas al Sistema de Rentas Internas",
                    "funcionalidades": [
                        "Información básica del vehículo",
                        "Rubros de deuda detallados",
                        "Componentes fiscales específicos",
                        "Historial completo de pagos",
                        "Plan IACV (Impuesto Ambiental)",
                        "Estados legales y prohibiciones",
                    ],
                },
                {
                    "categoria": "Propietario del Vehículo",
                    "descripcion": "Información del propietario actual",
                    "funcionalidades": [
                        "Nombre completo del propietario",
                        "Cédula de identidad",
                        "Múltiples fuentes de datos",
                        "Validación cruzada",
                    ],
                },
                {
                    "categoria": "Análisis Consolidado",
                    "descripcion": "Análisis inteligente de toda la información",
                    "funcionalidades": [
                        "Puntuación SRI (0-100)",
                        "Riesgo tributario",
                        "Estado legal consolidado",
                        "Recomendaciones tributarias",
                        "Estimación de valor",
                    ],
                },
                {
                    "categoria": "Performance",
                    "descripcion": "Optimizaciones para máximo rendimiento",
                    "funcionalidades": [
                        "Cache inteligente",
                        "Rate limiting",
                        "Pool de conexiones",
                        "Logs rotativos",
                        "Consultas asíncronas",
                    ],
                },
            ],
            "tecnologias": {
                "backend": "Flask + Python 3.8+",
                "frontend": "HTML5 + CSS3 + JavaScript ES6+",
                "base_datos": "SQLite con WAL mode",
                "apis_externas": "SRI Ecuador + Propietarios",
                "cache": "Memory-based con TTL",
                "logs": "Rotating file handlers",
            },
            "timestamp": datetime.now().isoformat(),
        }

        return jsonify(features)

    except Exception as e:
        logger.error(f"Error obteniendo características: {e}")
        return jsonify({"success": False, "error": "Error interno del servidor"}), 500


# ==========================================
# RUTAS DE UTILIDADES
# ==========================================


@api_bp.route("/ping", methods=["GET"])
def ping():
    """Endpoint simple de ping/pong"""
    return jsonify(
        {
            "success": True,
            "message": "pong",
            "timestamp": datetime.now().isoformat(),
            "server": "ECPlacas 2.0 SRI COMPLETO",
        }
    )


@api_bp.route("/time", methods=["GET"])
def get_server_time():
    """Obtener hora del servidor"""
    now = datetime.now()
    return jsonify(
        {
            "success": True,
            "server_time": now.isoformat(),
            "unix_timestamp": int(now.timestamp()),
            "timezone": str(now.astimezone().tzinfo),
            "formatted": now.strftime("%Y-%m-%d %H:%M:%S"),
        }
    )


@api_bp.route("/endpoints", methods=["GET"])
def list_endpoints():
    """Listar todos los endpoints disponibles"""
    try:
        from flask import current_app

        endpoints = []
        for rule in current_app.url_map.iter_rules():
            if rule.endpoint != "static":
                endpoints.append(
                    {
                        "endpoint": rule.endpoint,
                        "methods": sorted(rule.methods - {"HEAD", "OPTIONS"}),
                        "path": str(rule),
                        "description": getattr(
                            current_app.view_functions.get(rule.endpoint),
                            "__doc__",
                            "Sin descripción",
                        ),
                    }
                )

        # Agrupar por prefijo
        grouped = {
            "api": [e for e in endpoints if e["path"].startswith("/api/")],
            "admin": [e for e in endpoints if e["path"].startswith("/admin/")],
            "frontend": [
                e for e in endpoints if not e["path"].startswith(("/api/", "/admin/"))
            ],
        }

        return jsonify(
            {
                "success": True,
                "total_endpoints": len(endpoints),
                "endpoints_por_categoria": {k: len(v) for k, v in grouped.items()},
                "endpoints": grouped,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error listando endpoints: {e}")
        return jsonify({"success": False, "error": "Error interno del servidor"}), 500


# ==========================================
# RUTAS DE VALIDACIÓN AVANZADA
# ==========================================


@api_bp.route("/validate/batch", methods=["POST"])
def validate_batch():
    """Validar múltiples placas y cédulas en lote"""
    try:
        if not request.is_json:
            return (
                jsonify({"success": False, "error": "Contenido debe ser JSON válido"}),
                400,
            )

        data = request.get_json()
        placas = data.get("placas", [])
        cedulas = data.get("cedulas", [])

        if not placas and not cedulas:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Debe proporcionar al menos una placa o cédula",
                    }
                ),
                400,
            )

        # Importar validadores (asumiendo que están en app.py)
        from backend.app import CedulaValidator, PlateValidator

        resultados = {"placas": {}, "cedulas": {}}

        # Validar placas
        for placa in placas[:50]:  # Límite de 50 por seguridad
            try:
                original, normalizada, modificada = PlateValidator.normalize_plate(
                    placa
                )
                es_valida = PlateValidator.validate_plate_format(normalizada)

                resultados["placas"][placa] = {
                    "original": original,
                    "normalizada": normalizada,
                    "fue_modificada": modificada,
                    "es_valida": es_valida,
                    "formato": (
                        "Ecuatoriana estándar" if es_valida else "Formato inválido"
                    ),
                }
            except Exception as e:
                resultados["placas"][placa] = {"error": str(e), "es_valida": False}

        # Validar cédulas
        for cedula in cedulas[:50]:  # Límite de 50 por seguridad
            try:
                es_valida = CedulaValidator.validate_ecuadorian_id(cedula)
                provincia_info = None

                if es_valida and len(cedula) >= 2:
                    from backend.app import PROVINCE_CODES

                    codigo_provincia = cedula[:2]
                    provincia_info = {
                        "codigo": codigo_provincia,
                        "nombre": PROVINCE_CODES.get(codigo_provincia, "Desconocida"),
                    }

                resultados["cedulas"][cedula] = {
                    "es_valida": es_valida,
                    "provincia": provincia_info,
                    "algoritmo": "Validación oficial Ecuador",
                }
            except Exception as e:
                resultados["cedulas"][cedula] = {"error": str(e), "es_valida": False}

        return jsonify(
            {
                "success": True,
                "resultados": resultados,
                "resumen": {
                    "placas_procesadas": len(resultados["placas"]),
                    "cedulas_procesadas": len(resultados["cedulas"]),
                    "placas_validas": sum(
                        1 for r in resultados["placas"].values() if r.get("es_valida")
                    ),
                    "cedulas_validas": sum(
                        1 for r in resultados["cedulas"].values() if r.get("es_valida")
                    ),
                },
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error en validación por lotes: {e}")
        return jsonify({"success": False, "error": "Error interno del servidor"}), 500


# ==========================================
# RUTAS DE DESARROLLO Y DEBUG
# ==========================================


@api_bp.route("/debug/config", methods=["GET"])
def debug_config():
    """Obtener configuración del sistema (solo desarrollo)"""
    try:
        if not current_app.debug:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Endpoint solo disponible en modo debug",
                    }
                ),
                403,
            )

        config_info = {
            "success": True,
            "debug_mode": current_app.debug,
            "environment": current_app.env,
            "config_keys": sorted(
                [k for k in current_app.config.keys() if not k.startswith("SECRET")]
            ),
            "database_path": current_app.config.get("DATABASE_PATH"),
            "cache_enabled": current_app.config.get("CACHE_ENABLED"),
            "rate_limit_enabled": current_app.config.get("RATELIMIT_ENABLED"),
            "timestamp": datetime.now().isoformat(),
        }

        return jsonify(config_info)

    except Exception as e:
        logger.error(f"Error obteniendo config debug: {e}")
        return jsonify({"success": False, "error": "Error interno del servidor"}), 500


# ==========================================
# MANEJO DE ERRORES
# ==========================================


@api_bp.errorhandler(400)
def bad_request(error):
    """Manejo de errores 400"""
    return (
        jsonify(
            {
                "success": False,
                "error": "Solicitud inválida",
                "message": (
                    str(error.description)
                    if hasattr(error, "description")
                    else "Bad Request"
                ),
                "timestamp": datetime.now().isoformat(),
            }
        ),
        400,
    )


@api_bp.errorhandler(404)
def not_found(error):
    """Manejo de errores 404"""
    return (
        jsonify(
            {
                "success": False,
                "error": "Endpoint no encontrado",
                "path": request.path,
                "method": request.method,
                "available_endpoints": "/api/endpoints",
                "timestamp": datetime.now().isoformat(),
            }
        ),
        404,
    )


@api_bp.errorhandler(405)
def method_not_allowed(error):
    """Manejo de errores 405"""
    return (
        jsonify(
            {
                "success": False,
                "error": "Método no permitido",
                "method": request.method,
                "path": request.path,
                "allowed_methods": (
                    error.valid_methods if hasattr(error, "valid_methods") else []
                ),
                "timestamp": datetime.now().isoformat(),
            }
        ),
        405,
    )


@api_bp.errorhandler(500)
def internal_error(error):
    """Manejo de errores 500"""
    logger.error(f"Error interno en API: {error}")
    return (
        jsonify(
            {
                "success": False,
                "error": "Error interno del servidor",
                "timestamp": datetime.now().isoformat(),
                "support": "Contacte al desarrollador: Erick Costa",
            }
        ),
        500,
    )


# ==========================================
# RUTAS DE MONITOREO
# ==========================================


@api_bp.route("/monitoring/status", methods=["GET"])
def monitoring_status():
    """Estado del sistema para monitoreo"""
    try:
        import os

        import psutil

        # Información básica del sistema
        status = {
            "success": True,
            "status": "healthy",
            "uptime": time.time() - psutil.boot_time(),
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent,
            },
            "cpu_percent": psutil.cpu_percent(interval=1),
            "disk": {
                "total": psutil.disk_usage("/").total,
                "free": psutil.disk_usage("/").free,
                "percent": psutil.disk_usage("/").percent,
            },
            "process": {
                "pid": os.getpid(),
                "memory_mb": psutil.Process().memory_info().rss / 1024 / 1024,
                "cpu_percent": psutil.Process().cpu_percent(),
            },
            "timestamp": datetime.now().isoformat(),
        }

        return jsonify(status)

    except ImportError:
        # Si psutil no está disponible, retornar información básica
        return jsonify(
            {
                "success": True,
                "status": "healthy",
                "message": "Monitoreo básico (psutil no disponible)",
                "timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Error en monitoreo: {e}")
        return (
            jsonify({"success": False, "error": "Error obteniendo estado del sistema"}),
            500,
        )


if __name__ == "__main__":
    print("🔧 Módulo de rutas API adicionales para ECPlacas 2.0")
    print("📡 Rutas incluidas:")
    print("   - /api/version - Información de versión")
    print("   - /api/features - Características del sistema")
    print("   - /api/ping - Test de conectividad")
    print("   - /api/time - Hora del servidor")
    print("   - /api/endpoints - Lista de endpoints")
    print("   - /api/validate/batch - Validación por lotes")
    print("   - /api/debug/config - Configuración (debug)")
    print("   - /api/monitoring/status - Estado del sistema")
