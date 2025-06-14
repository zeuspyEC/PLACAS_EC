#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECPlacas 2.0 - Rutas Administrativas
Proyecto: Construcción de Software
Desarrollado por: Erick Costa

Rutas para funciones administrativas del sistema
"""

import os
import json
import time
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, send_file
from pathlib import Path
import logging

from ..db import db
from ..scraper import vehicle_scraper

logger = logging.getLogger(__name__)

# Crear blueprint para rutas administrativas
admin_bp = Blueprint('admin', __name__, url_prefix='/admin/api')

PROJECT_ROOT = Path(__file__).parent.parent.parent

@admin_bp.route('/dashboard-data', methods=['GET'])
def get_dashboard_data():
    """Obtener datos completos para el dashboard administrativo"""
    try:
        # Obtener datos de dashboard desde la base de datos
        dashboard_data = db.get_dashboard_data()
        
        # Obtener estadísticas del scraper
        scraper_stats = vehicle_scraper.get_statistics()
        
        # Agregar información del sistema
        system_info = {
            'version': '2.0.0',
            'author': 'Erick Costa',
            'project': 'Construcción de Software',
            'theme': 'Futurista - Azul Neon',
            'uptime': get_system_uptime(),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'dashboard': dashboard_data,
            'scraper': scraper_stats,
            'system': system_info
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo datos de dashboard: {e}")
        return jsonify({
            'success': False,
            'error': 'Error obteniendo datos del dashboard'
        }), 500

@admin_bp.route('/usuarios', methods=['GET'])
def get_usuarios():
    """Obtener lista de usuarios del sistema"""
    try:
        # Parámetros de paginación
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        
        # TODO: Implementar paginación en db.py
        # Por ahora retornar datos mock estructurados
        usuarios_mock = [
            {
                'id': 1,
                'nombre': 'JUAN PÉREZ GARCÍA',
                'cedula': '1234567890',
                'correo': 'juan@email.com',
                'telefono': '0987654321',
                'total_consultas': 15,
                'ultimo_acceso': '2024-12-15 14:30:22',
                'created_at': '2024-12-10 10:15:33'
            },
            {
                'id': 2,
                'nombre': 'MARÍA GARCÍA LÓPEZ',
                'cedula': '0987654321',
                'correo': 'maria@email.com',
                'telefono': '0998765432',
                'total_consultas': 8,
                'ultimo_acceso': '2024-12-15 13:45:11',
                'created_at': '2024-12-12 16:22:45'
            }
        ]
        
        return jsonify({
            'success': True,
            'usuarios': usuarios_mock,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': len(usuarios_mock),
                'pages': 1
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo usuarios: {e}")
        return jsonify({
            'success': False,
            'error': 'Error obteniendo lista de usuarios'
        }), 500

@admin_bp.route('/consultas-recientes', methods=['GET'])
def get_consultas_recientes():
    """Obtener consultas recientes del sistema"""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        # TODO: Implementar en db.py
        # Por ahora retornar datos mock
        consultas_mock = [
            {
                'id': 1,
                'timestamp': '2024-12-15 14:30:22',
                'placa': 'ABC1234',
                'usuario': 'Juan Pérez',
                'estado': 'Exitosa',
                'tiempo': 1.2,
                'ip_origen': '192.168.1.100'
            },
            {
                'id': 2,
                'timestamp': '2024-12-15 14:28:15',
                'placa': 'XYZ9876',
                'usuario': 'María García',
                'estado': 'Exitosa',
                'tiempo': 0.8,
                'ip_origen': '192.168.1.105'
            },
            {
                'id': 3,
                'timestamp': '2024-12-15 14:25:33',
                'placa': 'DEF5555',
                'usuario': 'Carlos López',
                'estado': 'Error',
                'tiempo': 2.1,
                'ip_origen': '192.168.1.102'
            }
        ]
        
        return jsonify({
            'success': True,
            'consultas': consultas_mock[:limit]
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo consultas recientes: {e}")
        return jsonify({
            'success': False,
            'error': 'Error obteniendo consultas recientes'
        }), 500

@admin_bp.route('/logs', methods=['GET'])
def get_logs():
    """Obtener logs del sistema"""
    try:
        # Parámetros
        limit = request.args.get('limit', 100, type=int)
        level = request.args.get('level', None)
        module = request.args.get('module', None)
        
        # Obtener logs desde la base de datos
        logs = db.get_logs(limite=limit, nivel=level, modulo=module)
        
        return jsonify({
            'success': True,
            'logs': logs,
            'count': len(logs)
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo logs: {e}")
        return jsonify({
            'success': False,
            'error': 'Error obteniendo logs del sistema'
        }), 500

@admin_bp.route('/system-info', methods=['GET'])
def get_system_info():
    """Obtener información detallada del sistema"""
    try:
        import platform
        import psutil
        import sys
        
        # Información del sistema
        system_info = {
            'platform': {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            },
            'resources': {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory': {
                    'total': psutil.virtual_memory().total,
                    'available': psutil.virtual_memory().available,
                    'percent': psutil.virtual_memory().percent,
                    'used': psutil.virtual_memory().used
                },
                'disk': {
                    'total': psutil.disk_usage('/').total,
                    'used': psutil.disk_usage('/').used,
                    'free': psutil.disk_usage('/').free,
                    'percent': psutil.disk_usage('/').percent
                }
            },
            'database': db.get_database_info(),
            'uptime': get_system_uptime()
        }
        
        return jsonify({
            'success': True,
            'system_info': system_info
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo información del sistema: {e}")
        return jsonify({
            'success': False,
            'error': 'Error obteniendo información del sistema'
        }), 500

@admin_bp.route('/backup-database', methods=['POST'])
def backup_database():
    """Crear backup de la base de datos"""
    try:
        # Crear backup
        backup_path = db.backup_database()
        
        if backup_path:
            return jsonify({
                'success': True,
                'message': 'Backup creado exitosamente',
                'backup_path': backup_path,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Error creando backup'
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Error creando backup: {e}")
        return jsonify({
            'success': False,
            'error': 'Error creando backup de la base de datos'
        }), 500

@admin_bp.route('/clear-cache', methods=['POST'])
def clear_cache():
    """Limpiar cache del sistema"""
    try:
        # Limpiar cache del scraper
        vehicle_scraper.clear_cache()
        
        return jsonify({
            'success': True,
            'message': 'Cache limpiado exitosamente',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Error limpiando cache: {e}")
        return jsonify({
            'success': False,
            'error': 'Error limpiando cache del sistema'
        }), 500

@admin_bp.route('/cleanup-old-data', methods=['POST'])
def cleanup_old_data():
    """Limpiar datos antiguos del sistema"""
    try:
        days_old = request.json.get('days_old', 90) if request.is_json else 90
        
        # Ejecutar limpieza
        cleanup_result = db.cleanup_old_data(days_old)
        
        return jsonify({
            'success': True,
            'message': 'Limpieza completada exitosamente',
            'result': cleanup_result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Error en limpieza de datos: {e}")
        return jsonify({
            'success': False,
            'error': 'Error en limpieza de datos antiguos'
        }), 500

@admin_bp.route('/test-apis', methods=['POST'])
def test_apis():
    """Probar conectividad con APIs externas"""
    try:
        # Probar APIs del scraper
        test_results = vehicle_scraper.test_apis()
        
        return jsonify({
            'success': True,
            'api_tests': test_results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Error probando APIs: {e}")
        return jsonify({
            'success': False,
            'error': 'Error probando conectividad de APIs'
        }), 500

@admin_bp.route('/configuration', methods=['GET'])
def get_configuration():
    """Obtener configuración del sistema"""
    try:
        # Obtener configuración desde base de datos
        # TODO: Implementar get_system_configuration en db.py
        
        config_mock = {
            'version_sistema': '2.0.0',
            'autor': 'Erick Costa',
            'proyecto': 'Construcción de Software',
            'tema': 'Futurista - Azul Neon',
            'cache_habilitado': True,
            'rate_limit_per_hour': 50,
            'backup_automatico': True,
            'log_level': 'INFO'
        }
        
        return jsonify({
            'success': True,
            'configuration': config_mock
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo configuración: {e}")
        return jsonify({
            'success': False,
            'error': 'Error obteniendo configuración del sistema'
        }), 500

@admin_bp.route('/configuration', methods=['POST'])
def update_configuration():
    """Actualizar configuración del sistema"""
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type debe ser application/json'
            }), 400
        
        config_data = request.get_json()
        
        # TODO: Implementar update_system_configuration en db.py
        # Por ahora simular actualización exitosa
        
        return jsonify({
            'success': True,
            'message': 'Configuración actualizada exitosamente',
            'updated_keys': list(config_data.keys()),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Error actualizando configuración: {e}")
        return jsonify({
            'success': False,
            'error': 'Error actualizando configuración del sistema'
        }), 500

@admin_bp.route('/export-data', methods=['POST'])
def export_data():
    """Exportar datos del sistema"""
    try:
        export_type = request.json.get('type', 'all') if request.is_json else 'all'
        format_type = request.json.get('format', 'json') if request.is_json else 'json'
        
        # TODO: Implementar exportación real
        export_result = {
            'export_id': f"export_{int(time.time())}",
            'type': export_type,
            'format': format_type,
            'status': 'completed',
            'file_size': '1.2MB',
            'records_count': 150
        }
        
        return jsonify({
            'success': True,
            'message': 'Exportación completada',
            'export': export_result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Error exportando datos: {e}")
        return jsonify({
            'success': False,
            'error': 'Error exportando datos del sistema'
        }), 500

@admin_bp.route('/restart-system', methods=['POST'])
def restart_system():
    """Reiniciar sistema (simulado)"""
    try:
        # En un entorno real, esto requeriría permisos especiales
        # Por ahora solo simular el reinicio
        
        return jsonify({
            'success': True,
            'message': 'Comando de reinicio enviado',
            'note': 'El sistema se reiniciará en 10 segundos',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Error en comando de reinicio: {e}")
        return jsonify({
            'success': False,
            'error': 'Error ejecutando comando de reinicio'
        }), 500

def get_system_uptime():
    """Obtener tiempo de funcionamiento del sistema"""
    try:
        import psutil
        boot_time = psutil.boot_time()
        current_time = time.time()
        uptime_seconds = current_time - boot_time
        
        # Convertir a formato legible
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        
        return f"{days}d {hours}h {minutes}m"
    except:
        return "Unknown"

# Manejadores de errores para el blueprint administrativo
@admin_bp.errorhandler(403)
def admin_forbidden(error):
    return jsonify({
        'success': False,
        'error': 'Acceso prohibido',
        'message': 'Se requieren permisos de administrador'
    }), 403

@admin_bp.errorhandler(404)
def admin_not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint administrativo no encontrado',
        'available_endpoints': [
            '/admin/api/dashboard-data',
            '/admin/api/usuarios',
            '/admin/api/consultas-recientes',
            '/admin/api/logs',
            '/admin/api/system-info',
            '/admin/api/backup-database',
            '/admin/api/clear-cache'
        ]
    }), 404

@admin_bp.errorhandler(500)
def admin_internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Error interno del servidor administrativo'
    }), 500
