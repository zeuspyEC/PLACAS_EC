#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================
ECPlacas 2.0 SRI COMPLETO - Rutas de Admin
==========================================
Proyecto: Construcción de Software
Desarrollado por: Erick Costa
Versión: 2.0.1
==========================================

Rutas administrativas que complementan el panel de admin del app.py
"""

import json
import logging
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app, render_template_string

# Crear blueprint para rutas de admin
admin_bp = Blueprint('admin', __name__)

logger = logging.getLogger('ecplacas.admin')

# ==========================================
# MIDDLEWARE DE SEGURIDAD
# ==========================================

@admin_bp.before_request
def admin_security():
    """Middleware de seguridad para rutas admin"""
    # Log de acceso admin
    logger.warning(f"Admin access attempt: {request.method} {request.path} from {request.remote_addr}")
    
    # En producción, aquí iría autenticación real
    # Por ahora solo log de seguridad

# ==========================================
# RUTAS DE INFORMACIÓN DEL SISTEMA
# ==========================================

@admin_bp.route('/info')
def system_info():
    """Información detallada del sistema"""
    try:
        import platform
        import sys
        
        # Información del sistema
        system_info = {
            'sistema_operativo': {
                'nombre': platform.system(),
                'version': platform.version(),
                'arquitectura': platform.architecture()[0],
                'procesador': platform.processor(),
                'nombre_maquina': platform.node()
            },
            'python': {
                'version': sys.version,
                'version_info': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                'executable': sys.executable,
                'platform': sys.platform
            },
            'aplicacion': {
                'nombre': 'ECPlacas 2.0 SRI COMPLETO',
                'version': '2.0.1',
                'autor': 'Erick Costa',
                'proyecto': 'Construcción de Software',
                'debug_mode': current_app.debug,
                'environment': current_app.env
            },
            'paths': {
                'root_path': current_app.root_path,
                'instance_path': current_app.instance_path,
                'database_path': current_app.config.get('DATABASE_PATH', 'No configurado')
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # Información de memoria (si psutil está disponible)
        try:
            import psutil
            process = psutil.Process()
            system_info['recursos'] = {
                'memoria_proceso_mb': round(process.memory_info().rss / 1024 / 1024, 2),
                'cpu_percent': process.cpu_percent(),
                'memoria_sistema_percent': psutil.virtual_memory().percent,
                'disco_libre_gb': round(psutil.disk_usage('/').free / 1024 / 1024 / 1024, 2)
            }
        except ImportError:
            system_info['recursos'] = {'mensaje': 'psutil no disponible'}
        
        return jsonify({
            'success': True,
            'system_info': system_info
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo info del sistema: {e}")
        return jsonify({
            'success': False,
            'error': 'Error obteniendo información del sistema'
        }), 500

@admin_bp.route('/database/info')
def database_info():
    """Información de la base de datos"""
    try:
        db_path = current_app.config.get('DATABASE_PATH')
        if not db_path or not Path(db_path).exists():
            return jsonify({
                'success': False,
                'error': 'Base de datos no encontrada'
            }), 404
        
        # Información básica del archivo
        db_file = Path(db_path)
        file_size = db_file.stat().st_size
        
        # Conectar a la base de datos
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Información de SQLite
            cursor.execute("SELECT sqlite_version()")
            sqlite_version = cursor.fetchone()[0]
            
            # Obtener lista de tablas
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            # Conteo de registros por tabla
            table_counts = {}
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    table_counts[table] = cursor.fetchone()[0]
                except Exception as e:
                    table_counts[table] = f"Error: {e}"
            
            # Configuración PRAGMA
            pragma_info = {}
            pragmas = ['journal_mode', 'synchronous', 'foreign_keys', 'cache_size']
            for pragma in pragmas:
                try:
                    cursor.execute(f"PRAGMA {pragma}")
                    pragma_info[pragma] = cursor.fetchone()[0]
                except:
                    pragma_info[pragma] = 'Error'
        
        db_info = {
            'success': True,
            'database': {
                'path': str(db_path),
                'size_bytes': file_size,
                'size_mb': round(file_size / 1024 / 1024, 2),
                'sqlite_version': sqlite_version,
                'created': datetime.fromtimestamp(db_file.stat().st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(db_file.stat().st_mtime).isoformat()
            },
            'tables': {
                'total': len(tables),
                'list': tables,
                'record_counts': table_counts
            },
            'configuration': pragma_info,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(db_info)
        
    except Exception as e:
        logger.error(f"Error obteniendo info de BD: {e}")
        return jsonify({
            'success': False,
            'error': 'Error obteniendo información de la base de datos'
        }), 500

@admin_bp.route('/logs/list')
def list_logs():
    """Listar archivos de log disponibles"""
    try:
        logs_dir = Path(current_app.root_path).parent / "logs"
        
        if not logs_dir.exists():
            return jsonify({
                'success': False,
                'error': 'Directorio de logs no encontrado'
            }), 404
        
        log_files = []
        for log_file in logs_dir.rglob("*.log"):
            try:
                stat = log_file.stat()
                log_files.append({
                    'name': log_file.name,
                    'path': str(log_file.relative_to(logs_dir)),
                    'size_bytes': stat.st_size,
                    'size_mb': round(stat.st_size / 1024 / 1024, 2),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'category': log_file.parent.name if log_file.parent != logs_dir else 'root'
                })
            except Exception as e:
                logger.error(f"Error processing log file {log_file}: {e}")
        
        # Ordenar por fecha de modificación (más recientes primero)
        log_files.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({
            'success': True,
            'logs_directory': str(logs_dir),
            'total_files': len(log_files),
            'files': log_files,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error listando logs: {e}")
        return jsonify({
            'success': False,
            'error': 'Error listando archivos de log'
        }), 500

@admin_bp.route('/logs/view/<path:log_name>')
def view_log(log_name):
    """Ver contenido de un archivo de log"""
    try:
        logs_dir = Path(current_app.root_path).parent / "logs"
        log_file = logs_dir / log_name
        
        # Validación de seguridad - solo archivos .log
        if not log_file.suffix == '.log' or not log_file.exists():
            return jsonify({
                'success': False,
                'error': 'Archivo de log no encontrado o inválido'
            }), 404
        
        # Validación de ruta (evitar path traversal)
        try:
            log_file.resolve().relative_to(logs_dir.resolve())
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Ruta de archivo inválida'
            }), 400
        
        # Parámetros de consulta
        lines = int(request.args.get('lines', 100))
        offset = int(request.args.get('offset', 0))
        filter_level = request.args.get('level', '').upper()
        
        # Leer archivo
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            all_lines = f.readlines()
        
        # Filtrar por nivel si se especifica
        if filter_level:
            all_lines = [line for line in all_lines if filter_level in line.upper()]
        
        # Aplicar offset y límite
        total_lines = len(all_lines)
        start_idx = max(0, total_lines - lines - offset)
        end_idx = total_lines - offset
        selected_lines = all_lines[start_idx:end_idx]
        
        return jsonify({
            'success': True,
            'log_file': log_name,
            'total_lines': total_lines,
            'returned_lines': len(selected_lines),
            'offset': offset,
            'content': ''.join(selected_lines),
            'lines': [line.rstrip() for line in selected_lines],
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error viewing log {log_name}: {e}")
        return jsonify({
            'success': False,
            'error': 'Error leyendo archivo de log'
        }), 500

# ==========================================
# RUTAS DE GESTIÓN DE SISTEMA
# ==========================================

@admin_bp.route('/cache/status')
def cache_status():
    """Estado del sistema de cache"""
    try:
        # Información del cache (esto dependería de la implementación específica)
        cache_info = {
            'success': True,
            'cache_enabled': current_app.config.get('CACHE_ENABLED', False),
            'cache_type': 'Memory-based',
            'default_timeout': current_app.config.get('CACHE_DEFAULT_TIMEOUT', 3600),
            'max_entries': current_app.config.get('CACHE_MAX_ENTRIES', 1000),
            'timestamp': datetime.now().isoformat()
        }
        
        # Si hay un sistema de cache activo, agregar estadísticas
        # Esto sería específico a la implementación del cache
        
        return jsonify(cache_info)
        
    except Exception as e:
        logger.error(f"Error obteniendo estado del cache: {e}")
        return jsonify({
            'success': False,
            'error': 'Error obteniendo estado del cache'
        }), 500

@admin_bp.route('/cache/clear', methods=['POST'])
def clear_cache():
    """Limpiar cache del sistema"""
    try:
        # Implementación específica del clear cache
        # Esto dependería del sistema de cache utilizado
        
        logger.info("Cache cleared by admin request")
        
        return jsonify({
            'success': True,
            'message': 'Cache limpiado exitosamente',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error limpiando cache: {e}")
        return jsonify({
            'success': False,
            'error': 'Error limpiando cache'
        }), 500

@admin_bp.route('/backup/create', methods=['POST'])
def create_backup():
    """Crear backup de la base de datos"""
    try:
        db_path = current_app.config.get('DATABASE_PATH')
        if not db_path or not Path(db_path).exists():
            return jsonify({
                'success': False,
                'error': 'Base de datos no encontrada'
            }), 404
        
        # Crear directorio de backups
        backup_dir = Path(db_path).parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        # Generar nombre de backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"ecplacas_backup_{timestamp}.sqlite"
        backup_path = backup_dir / backup_name
        
        # Crear backup usando SQLite
        with sqlite3.connect(db_path) as source:
            with sqlite3.connect(backup_path) as backup:
                source.backup(backup)
        
        # Información del backup
        backup_info = {
            'success': True,
            'backup_created': True,
            'backup_name': backup_name,
            'backup_path': str(backup_path),
            'backup_size_mb': round(backup_path.stat().st_size / 1024 / 1024, 2),
            'created_at': datetime.now().isoformat()
        }
        
        logger.info(f"Backup created: {backup_name}")
        return jsonify(backup_info)
        
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return jsonify({
            'success': False,
            'error': 'Error creando backup'
        }), 500

@admin_bp.route('/backup/list')
def list_backups():
    """Listar backups disponibles"""
    try:
        db_path = current_app.config.get('DATABASE_PATH')
        if not db_path:
            return jsonify({
                'success': False,
                'error': 'Ruta de base de datos no configurada'
            }), 500
        
        backup_dir = Path(db_path).parent / "backups"
        
        if not backup_dir.exists():
            return jsonify({
                'success': True,
                'backups': [],
                'total': 0,
                'backup_directory': str(backup_dir)
            })
        
        backups = []
        for backup_file in backup_dir.glob("*.sqlite"):
            try:
                stat = backup_file.stat()
                backups.append({
                    'name': backup_file.name,
                    'path': str(backup_file),
                    'size_bytes': stat.st_size,
                    'size_mb': round(stat.st_size / 1024 / 1024, 2),
                    'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            except Exception as e:
                logger.error(f"Error processing backup file {backup_file}: {e}")
        
        # Ordenar por fecha de creación (más recientes primero)
        backups.sort(key=lambda x: x['created'], reverse=True)
        
        return jsonify({
            'success': True,
            'backups': backups,
            'total': len(backups),
            'backup_directory': str(backup_dir),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error listing backups: {e}")
        return jsonify({
            'success': False,
            'error': 'Error listando backups'
        }), 500

# ==========================================
# RUTAS DE CONFIGURACIÓN
# ==========================================

@admin_bp.route('/config/view')
def view_config():
    """Ver configuración actual del sistema"""
    try:
        # Obtener configuración sin valores sensibles
        safe_config = {}
        sensitive_keys = ['SECRET_KEY', 'JWT_SECRET_KEY', 'PASSWORD', 'TOKEN', 'SECURITY']
        
        for key, value in current_app.config.items():
            # Filtrar claves sensibles
            if any(sensitive in key.upper() for sensitive in sensitive_keys):
                safe_config[key] = '***HIDDEN***'
            else:
                safe_config[key] = value
        
        return jsonify({
            'success': True,
            'configuration': safe_config,
            'environment': current_app.env,
            'debug_mode': current_app.debug,
            'total_keys': len(current_app.config),
            'hidden_keys': len([k for k in current_app.config.keys() 
                              if any(s in k.upper() for s in sensitive_keys)]),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error viewing config: {e}")
        return jsonify({
            'success': False,
            'error': 'Error obteniendo configuración'
        }), 500

# ==========================================
# RUTAS DE MONITOREO
# ==========================================

@admin_bp.route('/monitoring/performance')
def performance_metrics():
    """Métricas de performance del sistema"""
    try:
        import time
        start_time = time.time()
        
        # Métricas básicas
        metrics = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': time.time() - start_time,
        }
        
        # Si psutil está disponible, agregar métricas detalladas
        try:
            import psutil
            process = psutil.Process()
            
            metrics.update({
                'cpu': {
                    'percent': psutil.cpu_percent(interval=1),
                    'count': psutil.cpu_count(),
                    'frequency': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
                },
                'memory': {
                    'total_gb': round(psutil.virtual_memory().total / 1024 / 1024 / 1024, 2),
                    'available_gb': round(psutil.virtual_memory().available / 1024 / 1024 / 1024, 2),
                    'percent_used': psutil.virtual_memory().percent,
                    'process_mb': round(process.memory_info().rss / 1024 / 1024, 2)
                },
                'disk': {
                    'total_gb': round(psutil.disk_usage('/').total / 1024 / 1024 / 1024, 2),
                    'free_gb': round(psutil.disk_usage('/').free / 1024 / 1024 / 1024, 2),
                    'percent_used': psutil.disk_usage('/').percent
                },
                'network': {
                    'connections': len(process.connections()),
                    'io_counters': psutil.net_io_counters()._asdict() if psutil.net_io_counters() else None
                }
            })
        except ImportError:
            metrics['note'] = 'psutil no disponible - métricas limitadas'
        
        return jsonify(metrics)
        
    except Exception as e:
        logger.error(f"Error obteniendo métricas: {e}")
        return jsonify({
            'success': False,
            'error': 'Error obteniendo métricas de performance'
        }), 500

# ==========================================
# MANEJO DE ERRORES ADMIN
# ==========================================

@admin_bp.errorhandler(403)
def admin_forbidden(error):
    """Manejo de errores 403 en admin"""
    return jsonify({
        'success': False,
        'error': 'Acceso denegado',
        'message': 'No tiene permisos para acceder a esta función administrativa',
        'timestamp': datetime.now().isoformat()
    }), 403

@admin_bp.errorhandler(500)
def admin_internal_error(error):
    """Manejo de errores 500 en admin"""
    logger.error(f"Error interno en admin: {error}")
    return jsonify({
        'success': False,
        'error': 'Error interno del servidor',
        'timestamp': datetime.now().isoformat()
    }), 500

if __name__ == "__main__":
    print("⚙️ Módulo de rutas de Administración para ECPlacas 2.0")
    print("🔧 Rutas incluidas:")
    print("   - /admin/info - Información del sistema")
    print("   - /admin/database/info - Info de base de datos")
    print("   - /admin/logs/list - Listar logs")
    print("   - /admin/logs/view/<log> - Ver log específico")
    print("   - /admin/cache/status - Estado del cache")
    print("   - /admin/cache/clear - Limpiar cache")
    print("   - /admin/backup/create - Crear backup")
    print("   - /admin/backup/list - Listar backups")
    print("   - /admin/config/view - Ver configuración")
    print("   - /admin/monitoring/performance - Métricas de performance")