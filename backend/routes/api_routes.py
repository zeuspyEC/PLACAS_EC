#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECPlacas 2.0 - Rutas de API
Proyecto: Construcción de Software
Desarrollado por: Erick Costa

Rutas principales de la API ECPlacas 2.0
"""

import asyncio
import time
import uuid
import threading
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
import logging

from ..models import UsuarioModel, VehiculoCompleto, ValidadorEcuatoriano
from ..scraper import vehicle_scraper
from ..db import db

logger = logging.getLogger(__name__)

# Crear blueprint para rutas de API
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Almacenamiento temporal para consultas en progreso
active_consultations = {}

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Verificación de salud del sistema"""
    try:
        start_time = time.time()
        
        # Verificar base de datos
        db_stats = db.get_system_stats()
        
        # Verificar scraper
        scraper_stats = vehicle_scraper.get_statistics()
        
        response_time = round((time.time() - start_time) * 1000, 2)
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'service': 'ECPlacas 2.0',
            'version': '2.0.0',
            'author': 'Erick Costa',
            'project': 'Construcción de Software',
            'theme': 'Futurista - Azul Neon',
            'timestamp': datetime.now().isoformat(),
            'response_time_ms': response_time,
            'database': {
                'status': 'online',
                'total_consultas': db_stats.get('total_consultas', 0),
                'total_usuarios': db_stats.get('total_usuarios', 0)
            },
            'scraper': {
                'status': 'online',
                'success_rate': scraper_stats.get('success_rate', {}).get('percentage', 0),
                'cache_entries': scraper_stats.get('cache_stats', {}).get('valid_entries', 0) if scraper_stats.get('cache_stats') else 0
            }
        })
        
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'service': 'ECPlacas 2.0',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@api_bp.route('/consultar-vehiculo', methods=['POST'])
def consultar_vehiculo():
    """Endpoint principal para consultar vehículo"""
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type debe ser application/json'
            }), 400
        
        data = request.get_json()
        
        # Validar datos de entrada
        placa = data.get('placa', '').strip().upper()
        usuario_data = data.get('usuario', {})
        
        if not placa:
            return jsonify({
                'success': False,
                'error': 'Número de placa es requerido'
            }), 400
        
        # Validar formato de placa
        es_valida, placa_normalizada, error_placa = ValidadorEcuatoriano.validar_placa(placa)
        if not es_valida:
            return jsonify({
                'success': False,
                'error': f'Formato de placa inválido: {error_placa}',
                'formato_esperado': 'ABC1234 o ABC123'
            }), 400
        
        # Crear y validar modelo de usuario
        try:
            usuario = UsuarioModel(
                nombre=usuario_data.get('nombre', '').strip().upper(),
                cedula=usuario_data.get('cedula', '').strip(),
                telefono=usuario_data.get('telefono', '').strip(),
                correo=usuario_data.get('correo', '').strip().lower(),
                country_code=usuario_data.get('country_code', '+593'),
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')
            )
            
            is_valid, errors = usuario.validar()
            if not is_valid:
                return jsonify({
                    'success': False,
                    'error': 'Datos de usuario inválidos',
                    'errores': errors
                }), 400
                
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error procesando datos de usuario: {str(e)}'
            }), 400
        
        # Generar session ID único
        session_id = f"ecplacas_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        
        logger.info(f"🚀 Nueva consulta ECPlacas 2.0 - Placa: {placa} → {placa_normalizada}, Session: {session_id}")
        
        # Función para ejecutar consulta en thread separado
        def run_consultation():
            try:
                # Actualizar progreso
                active_consultations[session_id]['progress'] = 10
                active_consultations[session_id]['message'] = '🔍 Validando placa...'
                
                # Ejecutar consulta asíncrona
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                active_consultations[session_id]['progress'] = 30
                active_consultations[session_id]['message'] = '📡 Consultando APIs externas...'
                
                vehicle_data = loop.run_until_complete(
                    vehicle_scraper.consultar_vehiculo(placa_normalizada)
                )
                
                active_consultations[session_id]['progress'] = 70
                active_consultations[session_id]['message'] = '💾 Procesando datos...'
                
                # Guardar usuario y consulta en base de datos
                user_id = db.save_user(usuario.to_dict())
                if user_id:
                    vehicle_dict = vehicle_data.to_dict()
                    vehicle_dict['ip_origen'] = request.remote_addr
                    vehicle_dict['user_agent'] = request.headers.get('User-Agent', '')
                    
                    consultation_id = db.save_vehicle_consultation(vehicle_dict, user_id)
                    
                    active_consultations[session_id]['progress'] = 100
                    active_consultations[session_id]['message'] = '✅ Consulta completada'
                    
                    # Guardar resultado final
                    active_consultations[session_id]['status'] = 'completado'
                    active_consultations[session_id]['result'] = vehicle_data.to_dict()
                    active_consultations[session_id]['consultation_id'] = consultation_id
                    active_consultations[session_id]['user_id'] = user_id
                else:
                    raise Exception("Error guardando usuario en base de datos")
                
                logger.info(f"✅ Consulta completada exitosamente: {session_id}")
                
            except Exception as e:
                logger.error(f"❌ Error en consulta {session_id}: {e}")
                active_consultations[session_id]['status'] = 'error'
                active_consultations[session_id]['error'] = str(e)
                active_consultations[session_id]['progress'] = 0
                active_consultations[session_id]['message'] = f'❌ Error: {str(e)}'
            finally:
                if 'loop' in locals():
                    loop.close()
        
        # Inicializar consulta en progreso
        active_consultations[session_id] = {
            'status': 'procesando',
            'progress': 0,
            'message': '🚀 Iniciando consulta ECPlacas 2.0...',
            'placa': placa_normalizada,
            'usuario': usuario.nombre,
            'timestamp': datetime.now().isoformat()
        }
        
        # Ejecutar en thread separado
        thread = threading.Thread(target=run_consultation, daemon=True)
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Consulta ECPlacas 2.0 iniciada exitosamente',
            'session_id': session_id,
            'placa_original': placa,
            'placa_normalizada': placa_normalizada,
            'status': 'procesando',
            'tiempo_estimado': '10-30 segundos',
            'usuario': usuario.nombre
        }), 202
        
    except Exception as e:
        logger.error(f"❌ Error en endpoint consultar-vehiculo: {e}")
        return jsonify({
            'success': False,
            'error': 'Error interno del servidor',
            'details': str(e) if current_app.debug else None
        }), 500

@api_bp.route('/estado-consulta/<session_id>', methods=['GET'])
def estado_consulta(session_id):
    """Obtener estado de consulta en progreso"""
    try:
        if session_id not in active_consultations:
            return jsonify({
                'success': False,
                'error': 'Session ID no encontrado',
                'session_id': session_id
            }), 404
        
        consultation = active_consultations[session_id]
        
        response_data = {
            'success': True,
            'session_id': session_id,
            'status': consultation.get('status'),
            'progress': consultation.get('progress', 0),
            'message': consultation.get('message', ''),
            'placa': consultation.get('placa'),
            'usuario': consultation.get('usuario'),
            'timestamp': consultation.get('timestamp')
        }
        
        # Agregar error si existe
        if 'error' in consultation:
            response_data['error'] = consultation['error']
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estado de consulta: {e}")
        return jsonify({
            'success': False,
            'error': 'Error obteniendo estado de consulta',
            'session_id': session_id
        }), 500

@api_bp.route('/resultado/<session_id>', methods=['GET'])
def obtener_resultado(session_id):
    """Obtener resultado completo de consulta"""
    try:
        if session_id not in active_consultations:
            return jsonify({
                'success': False,
                'error': 'Session ID no encontrado',
                'session_id': session_id
            }), 404
        
        consultation = active_consultations[session_id]
        
        if consultation.get('status') != 'completado':
            return jsonify({
                'success': False,
                'error': 'Consulta no completada',
                'status': consultation.get('status'),
                'progress': consultation.get('progress', 0),
                'message': consultation.get('message', ''),
                'session_id': session_id
            }), 400
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'data': consultation.get('result'),
            'consultation_id': consultation.get('consultation_id'),
            'user_id': consultation.get('user_id'),
            'timestamp': consultation.get('timestamp'),
            'version': '2.0.0',
            'service': 'ECPlacas 2.0'
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo resultado: {e}")
        return jsonify({
            'success': False,
            'error': 'Error obteniendo resultado de consulta',
            'session_id': session_id
        }), 500

@api_bp.route('/estadisticas', methods=['GET'])
def obtener_estadisticas():
    """Obtener estadísticas del sistema"""
    try:
        # Obtener estadísticas de base de datos
        db_stats = db.get_system_stats()
        
        # Obtener estadísticas del scraper
        scraper_stats = vehicle_scraper.get_statistics()
        
        # Estadísticas de consultas activas
        active_stats = {
            'consultas_activas': len([c for c in active_consultations.values() if c.get('status') == 'procesando']),
            'consultas_completadas_sesion': len([c for c in active_consultations.values() if c.get('status') == 'completado']),
            'consultas_error_sesion': len([c for c in active_consultations.values() if c.get('status') == 'error']),
            'total_consultas_sesion': len(active_consultations)
        }
        
        return jsonify({
            'success': True,
            'estadisticas': {
                **db_stats,
                'scraper': scraper_stats,
                'sesion_actual': active_stats,
                'sistema': {
                    'version': '2.0.0',
                    'autor': 'Erick Costa',
                    'proyecto': 'Construcción de Software',
                    'tema': 'Futurista - Azul Neon'
                }
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas: {e}")
        return jsonify({
            'success': False,
            'error': 'Error obteniendo estadísticas del sistema'
        }), 500

@api_bp.route('/limpiar-consultas', methods=['POST'])
def limpiar_consultas():
    """Limpiar consultas completadas o con error (endpoint administrativo)"""
    try:
        # Solo limpiar consultas completadas o con error de más de 1 hora
        current_time = datetime.now()
        cleaned_count = 0
        
        sessions_to_remove = []
        for session_id, consultation in active_consultations.items():
            if consultation.get('status') in ['completado', 'error']:
                try:
                    timestamp = datetime.fromisoformat(consultation.get('timestamp', ''))
                    if (current_time - timestamp).total_seconds() > 3600:  # 1 hora
                        sessions_to_remove.append(session_id)
                except:
                    sessions_to_remove.append(session_id)  # Remover si no tiene timestamp válido
        
        for session_id in sessions_to_remove:
            del active_consultations[session_id]
            cleaned_count += 1
        
        logger.info(f"🧹 Limpieza de consultas: {cleaned_count} sesiones eliminadas")
        
        return jsonify({
            'success': True,
            'message': f'Limpieza completada: {cleaned_count} consultas eliminadas',
            'consultas_activas': len(active_consultations)
        })
        
    except Exception as e:
        logger.error(f"❌ Error en limpieza de consultas: {e}")
        return jsonify({
            'success': False,
            'error': 'Error en limpieza de consultas'
        }), 500

# Manejadores de errores para el blueprint
@api_bp.errorhandler(404)
def api_not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint de API no encontrado',
        'service': 'ECPlacas 2.0',
        'available_endpoints': [
            '/api/health',
            '/api/consultar-vehiculo',
            '/api/estado-consulta/<session_id>',
            '/api/resultado/<session_id>',
            '/api/estadisticas'
        ]
    }), 404

@api_bp.errorhandler(405)
def api_method_not_allowed(error):
    return jsonify({
        'success': False,
        'error': 'Método HTTP no permitido',
        'service': 'ECPlacas 2.0'
    }), 405

@api_bp.errorhandler(500)
def api_internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Error interno del servidor',
        'service': 'ECPlacas 2.0'
    }), 500

# Función para limpiar consultas periódicamente
def cleanup_old_consultations():
    """Limpia consultas antiguas periódicamente"""
    import threading
    import time
    
    def cleanup_worker():
        while True:
            try:
                current_time = datetime.now()
                sessions_to_remove = []
                
                for session_id, consultation in active_consultations.items():
                    try:
                        timestamp = datetime.fromisoformat(consultation.get('timestamp', ''))
                        # Remover consultas de más de 24 horas
                        if (current_time - timestamp).total_seconds() > 86400:
                            sessions_to_remove.append(session_id)
                    except:
                        sessions_to_remove.append(session_id)
                
                for session_id in sessions_to_remove:
                    del active_consultations[session_id]
                
                if sessions_to_remove:
                    logger.info(f"🧹 Limpieza automática: {len(sessions_to_remove)} consultas eliminadas")
                
            except Exception as e:
                logger.error(f"Error en limpieza automática: {e}")
            
            # Ejecutar cada 6 horas
            time.sleep(21600)
    
    cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
    cleanup_thread.start()

# Inicializar limpieza automática al importar el módulo
cleanup_old_consultations()
