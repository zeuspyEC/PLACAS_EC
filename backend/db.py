#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECPlacas 2.0 - Gestor de Base de Datos
Proyecto: Construcción de Software
Desarrollado por: Erick Costa

Gestor especializado de base de datos SQLite para ECPlacas 2.0
"""

import sqlite3
import logging
import json
import os
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager
import threading

# Configurar logging
logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Gestor de conexiones de base de datos thread-safe"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.local = threading.local()
    
    def get_connection(self) -> sqlite3.Connection:
        """Obtener conexión thread-local"""
        if not hasattr(self.local, 'connection'):
            self.local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            self.local.connection.row_factory = sqlite3.Row
            self.local.connection.execute("PRAGMA foreign_keys = ON")
            self.local.connection.execute("PRAGMA journal_mode = WAL")
            self.local.connection.execute("PRAGMA synchronous = NORMAL")
        
        return self.local.connection
    
    @contextmanager
    def get_cursor(self):
        """Context manager para obtener cursor"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Error en transacción de base de datos: {e}")
            raise
        finally:
            cursor.close()

class ECPlacasDatabase:
    """Gestor principal de base de datos ECPlacas 2.0"""
    
    def __init__(self, db_path: str = "database/ecplacas.sqlite"):
        self.db_path = db_path
        self.ensure_directory()
        self.connection_manager = DatabaseConnection(db_path)
        self.init_database()
    
    def ensure_directory(self):
        """Asegurar que el directorio de base de datos existe"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def init_database(self):
        """Inicializar base de datos con esquema completo"""
        try:
            with self.connection_manager.get_cursor() as cursor:
                # Leer y ejecutar esquema
                schema_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'schema.sql')
                if os.path.exists(schema_path):
                    with open(schema_path, 'r', encoding='utf-8') as f:
                        schema_sql = f.read()
                    cursor.executescript(schema_sql)
                else:
                    # Ejecutar esquema embebido si no existe archivo
                    self._create_schema(cursor)
                
                logger.info("✅ Base de datos ECPlacas 2.0 inicializada correctamente")
                
        except Exception as e:
            logger.error(f"❌ Error inicializando base de datos: {e}")
            raise
    
    def _create_schema(self, cursor: sqlite3.Cursor):
        """Crear esquema de base de datos embebido"""
        
        # Tabla de usuarios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                cedula TEXT UNIQUE NOT NULL,
                telefono TEXT,
                correo TEXT,
                country_code TEXT DEFAULT '+593',
                ip_address TEXT,
                user_agent TEXT,
                total_consultas INTEGER DEFAULT 0,
                ultimo_acceso TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de consultas vehiculares
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS consultas_vehiculares (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                usuario_id INTEGER,
                numero_placa TEXT NOT NULL,
                placa_original TEXT,
                placa_normalizada TEXT,
                consulta_exitosa BOOLEAN DEFAULT 0,
                tiempo_consulta REAL,
                mensaje_error TEXT,
                ip_origen TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        """)
        
        # Tabla de datos vehiculares completos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS datos_vehiculares (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                consulta_id INTEGER,
                vin_chasis TEXT,
                numero_motor TEXT,
                placa_anterior TEXT,
                marca TEXT,
                modelo TEXT,
                anio_fabricacion INTEGER,
                pais_fabricacion TEXT,
                clase_vehiculo TEXT,
                tipo_vehiculo TEXT,
                color_primario TEXT,
                color_secundario TEXT,
                peso_vehiculo TEXT,
                tipo_carroceria TEXT,
                matricula_desde TEXT,
                matricula_hasta TEXT,
                ano_ultima_revision TEXT,
                ultima_revision_desde TEXT,
                ultima_revision_hasta TEXT,
                servicio TEXT,
                ultima_actualizacion TEXT,
                indicador_crv TEXT,
                orden_crv TEXT,
                centro_retencion TEXT,
                tipo_retencion TEXT,
                motivo_retencion TEXT,
                fecha_inicio_retencion TEXT,
                dias_retencion TEXT,
                estado_matricula TEXT,
                dias_hasta_vencimiento INTEGER,
                estimacion_valor REAL,
                recomendacion TEXT,
                datos_completos_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (consulta_id) REFERENCES consultas_vehiculares (id)
            )
        """)
        
        # Tabla de estadísticas del sistema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS estadisticas_sistema (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha DATE UNIQUE,
                total_consultas INTEGER DEFAULT 0,
                consultas_exitosas INTEGER DEFAULT 0,
                usuarios_nuevos INTEGER DEFAULT 0,
                usuarios_activos INTEGER DEFAULT 0,
                tiempo_promedio_consulta REAL DEFAULT 0,
                placas_consultadas TEXT,
                marcas_populares TEXT,
                errores_comunes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de configuración del sistema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS configuracion_sistema (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clave TEXT UNIQUE NOT NULL,
                valor TEXT,
                descripcion TEXT,
                tipo_dato TEXT DEFAULT 'string',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de logs del sistema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs_sistema (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nivel TEXT NOT NULL,
                modulo TEXT,
                mensaje TEXT NOT NULL,
                detalles_json TEXT,
                ip_origen TEXT,
                usuario_id INTEGER,
                session_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        """)
        
        # Crear índices para optimización
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_usuarios_cedula ON usuarios(cedula)",
            "CREATE INDEX IF NOT EXISTS idx_usuarios_ultimo_acceso ON usuarios(ultimo_acceso)",
            "CREATE INDEX IF NOT EXISTS idx_consultas_placa ON consultas_vehiculares(numero_placa)",
            "CREATE INDEX IF NOT EXISTS idx_consultas_fecha ON consultas_vehiculares(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_consultas_exitosa ON consultas_vehiculares(consulta_exitosa)",
            "CREATE INDEX IF NOT EXISTS idx_vehiculos_marca ON datos_vehiculares(marca)",
            "CREATE INDEX IF NOT EXISTS idx_vehiculos_anio ON datos_vehiculares(anio_fabricacion)",
            "CREATE INDEX IF NOT EXISTS idx_estadisticas_fecha ON estadisticas_sistema(fecha)",
            "CREATE INDEX IF NOT EXISTS idx_logs_fecha ON logs_sistema(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_logs_nivel ON logs_sistema(nivel)"
        ]
        
        for indice in indices:
            cursor.execute(indice)
        
        # Insertar configuración inicial
        configuraciones_iniciales = [
            ('version_sistema', '2.0.0', 'Versión del sistema ECPlacas', 'string'),
            ('autor', 'Erick Costa', 'Desarrollador del sistema', 'string'),
            ('proyecto', 'Construcción de Software', 'Nombre del proyecto', 'string'),
            ('tema', 'Futurista - Azul Neon', 'Temática visual del sistema', 'string'),
            ('max_consultas_por_hora', '50', 'Límite de consultas por hora por IP', 'integer'),
            ('timeout_consulta', '30', 'Timeout en segundos para consultas', 'integer'),
            ('cache_habilitado', 'true', 'Cache de consultas habilitado', 'boolean'),
            ('notificaciones_email', 'false', 'Notificaciones por email habilitadas', 'boolean'),
            ('backup_automatico', 'true', 'Backup automático habilitado', 'boolean'),
            ('modo_debug', 'false', 'Modo debug del sistema', 'boolean')
        ]
        
        cursor.executemany("""
            INSERT OR IGNORE INTO configuracion_sistema (clave, valor, descripcion, tipo_dato)
            VALUES (?, ?, ?, ?)
        """, configuraciones_iniciales)
    
    # ==================== MÉTODOS DE USUARIOS ====================
    
    def save_user(self, user_data: Dict) -> int:
        """Guardar o actualizar usuario"""
        try:
            with self.connection_manager.get_cursor() as cursor:
                # Verificar si usuario existe
                cursor.execute("SELECT id, total_consultas FROM usuarios WHERE cedula = ?", (user_data['cedula'],))
                existing_user = cursor.fetchone()
                
                if existing_user:
                    # Actualizar usuario existente
                    cursor.execute("""
                        UPDATE usuarios SET 
                        nombre = ?, telefono = ?, correo = ?, 
                        country_code = ?, ip_address = ?, user_agent = ?,
                        total_consultas = total_consultas + 1,
                        ultimo_acceso = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                        WHERE cedula = ?
                    """, (
                        user_data['nombre'], user_data['telefono'], user_data['correo'],
                        user_data.get('country_code', '+593'), user_data.get('ip_address'),
                        user_data.get('user_agent'), user_data['cedula']
                    ))
                    user_id = existing_user['id']
                    logger.info(f"👤 Usuario actualizado: {user_data['cedula']} (ID: {user_id})")
                else:
                    # Crear nuevo usuario
                    cursor.execute("""
                        INSERT INTO usuarios (nombre, cedula, telefono, correo, 
                                            country_code, ip_address, user_agent, 
                                            total_consultas, ultimo_acceso)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
                    """, (
                        user_data['nombre'], user_data['cedula'], user_data['telefono'],
                        user_data['correo'], user_data.get('country_code', '+593'),
                        user_data.get('ip_address'), user_data.get('user_agent')
                    ))
                    user_id = cursor.lastrowid
                    logger.info(f"👤 Nuevo usuario creado: {user_data['cedula']} (ID: {user_id})")
                    
                    # Actualizar estadísticas
                    self._update_daily_stats(cursor, usuarios_nuevos=1)
                
                return user_id
                
        except Exception as e:
            logger.error(f"❌ Error guardando usuario: {e}")
            return 0
    
    def get_user(self, cedula: str) -> Optional[Dict]:
        """Obtener datos de usuario por cédula"""
        try:
            with self.connection_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM usuarios WHERE cedula = ?
                """, (cedula,))
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo usuario: {e}")
            return None
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Obtener estadísticas de usuario"""
        try:
            with self.connection_manager.get_cursor() as cursor:
                # Estadísticas generales
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_consultas,
                        COUNT(CASE WHEN consulta_exitosa = 1 THEN 1 END) as consultas_exitosas,
                        AVG(CASE WHEN consulta_exitosa = 1 THEN tiempo_consulta END) as tiempo_promedio,
                        MIN(created_at) as primera_consulta,
                        MAX(created_at) as ultima_consulta
                    FROM consultas_vehiculares 
                    WHERE usuario_id = ?
                """, (user_id,))
                
                stats = dict(cursor.fetchone())
                
                # Placas más consultadas
                cursor.execute("""
                    SELECT numero_placa, COUNT(*) as count
                    FROM consultas_vehiculares 
                    WHERE usuario_id = ? AND consulta_exitosa = 1
                    GROUP BY numero_placa
                    ORDER BY count DESC
                    LIMIT 5
                """, (user_id,))
                
                stats['placas_frecuentes'] = [dict(row) for row in cursor.fetchall()]
                
                return stats
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas de usuario: {e}")
            return {}
    
    # ==================== MÉTODOS DE CONSULTAS ====================
    
    def save_vehicle_consultation(self, vehicle_data: Dict, user_id: int) -> int:
        """Guardar consulta vehicular completa"""
        try:
            with self.connection_manager.get_cursor() as cursor:
                # Guardar consulta principal
                cursor.execute("""
                    INSERT INTO consultas_vehiculares 
                    (session_id, usuario_id, numero_placa, placa_original, 
                     placa_normalizada, consulta_exitosa, tiempo_consulta, 
                     mensaje_error, ip_origen, user_agent)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    vehicle_data['session_id'], user_id, vehicle_data['numero_placa'],
                    vehicle_data.get('placa_original'), vehicle_data.get('placa_normalizada'),
                    vehicle_data['consulta_exitosa'], vehicle_data.get('tiempo_consulta'),
                    vehicle_data.get('mensaje_error'), vehicle_data.get('ip_origen'),
                    vehicle_data.get('user_agent')
                ))
                
                consulta_id = cursor.lastrowid
                
                # Guardar datos vehiculares si la consulta fue exitosa
                if vehicle_data['consulta_exitosa']:
                    cursor.execute("""
                        INSERT INTO datos_vehiculares 
                        (consulta_id, vin_chasis, numero_motor, placa_anterior,
                         marca, modelo, anio_fabricacion, pais_fabricacion,
                         clase_vehiculo, tipo_vehiculo, color_primario, color_secundario,
                         peso_vehiculo, tipo_carroceria, matricula_desde, matricula_hasta,
                         ano_ultima_revision, ultima_revision_desde, ultima_revision_hasta,
                         servicio, ultima_actualizacion, indicador_crv, orden_crv,
                         centro_retencion, tipo_retencion, motivo_retencion,
                         fecha_inicio_retencion, dias_retencion, estado_matricula,
                         dias_hasta_vencimiento, estimacion_valor, recomendacion,
                         datos_completos_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        consulta_id, vehicle_data.get('vin_chasis'), vehicle_data.get('numero_motor'),
                        vehicle_data.get('placa_anterior'), vehicle_data.get('marca'), 
                        vehicle_data.get('modelo'), vehicle_data.get('anio_fabricacion'),
                        vehicle_data.get('pais_fabricacion'), vehicle_data.get('clase_vehiculo'),
                        vehicle_data.get('tipo_vehiculo'), vehicle_data.get('color_primario'),
                        vehicle_data.get('color_secundario'), vehicle_data.get('peso_vehiculo'),
                        vehicle_data.get('tipo_carroceria'), vehicle_data.get('matricula_desde'),
                        vehicle_data.get('matricula_hasta'), vehicle_data.get('ano_ultima_revision'),
                        vehicle_data.get('ultima_revision_desde'), vehicle_data.get('ultima_revision_hasta'),
                        vehicle_data.get('servicio'), vehicle_data.get('ultima_actualizacion'),
                        vehicle_data.get('indicador_crv'), vehicle_data.get('orden_crv'),
                        vehicle_data.get('centro_retencion'), vehicle_data.get('tipo_retencion'),
                        vehicle_data.get('motivo_retencion'), vehicle_data.get('fecha_inicio_retencion'),
                        vehicle_data.get('dias_retencion'), vehicle_data.get('estado_matricula'),
                        vehicle_data.get('dias_hasta_vencimiento'), vehicle_data.get('estimacion_valor'),
                        vehicle_data.get('recomendacion'), json.dumps(vehicle_data, ensure_ascii=False)
                    ))
                    
                    logger.info(f"🚗 Datos vehiculares guardados exitosamente (Consulta ID: {consulta_id})")
                
                # Actualizar estadísticas diarias
                self._update_daily_stats(
                    cursor, 
                    total_consultas=1, 
                    consultas_exitosas=1 if vehicle_data['consulta_exitosa'] else 0,
                    tiempo_consulta=vehicle_data.get('tiempo_consulta', 0)
                )
                
                return consulta_id
                
        except Exception as e:
            logger.error(f"❌ Error guardando consulta vehicular: {e}")
            return 0
    
    def get_consultation_result(self, session_id: str) -> Optional[Dict]:
        """Obtener resultado completo de consulta por session_id"""
        try:
            with self.connection_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT cv.*, dv.*
                    FROM consultas_vehiculares cv
                    LEFT JOIN datos_vehiculares dv ON cv.id = dv.consulta_id
                    WHERE cv.session_id = ?
                """, (session_id,))
                
                row = cursor.fetchone()
                if row:
                    result = dict(row)
                    # Parsear JSON si existe
                    if result.get('datos_completos_json'):
                        try:
                            result['datos_completos'] = json.loads(result['datos_completos_json'])
                        except:
                            pass
                    return result
                return None
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo resultado de consulta: {e}")
            return None
    
    def search_vehicle_history(self, placa: str, limit: int = 10) -> List[Dict]:
        """Buscar historial de consultas de una placa"""
        try:
            with self.connection_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT cv.*, u.nombre, u.cedula, dv.marca, dv.modelo, dv.anio_fabricacion
                    FROM consultas_vehiculares cv
                    LEFT JOIN usuarios u ON cv.usuario_id = u.id
                    LEFT JOIN datos_vehiculares dv ON cv.id = dv.consulta_id
                    WHERE cv.numero_placa = ? OR cv.placa_normalizada = ?
                    ORDER BY cv.created_at DESC
                    LIMIT ?
                """, (placa, placa, limit))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"❌ Error buscando historial de vehículo: {e}")
            return []
    
    # ==================== MÉTODOS DE ESTADÍSTICAS ====================
    
    def _update_daily_stats(self, cursor: sqlite3.Cursor, total_consultas: int = 0, 
                           consultas_exitosas: int = 0, usuarios_nuevos: int = 0,
                           tiempo_consulta: float = 0):
        """Actualizar estadísticas diarias"""
        try:
            today = date.today()
            
            # Insertar o actualizar estadísticas del día
            cursor.execute("""
                INSERT OR IGNORE INTO estadisticas_sistema 
                (fecha, total_consultas, consultas_exitosas, usuarios_nuevos, tiempo_promedio_consulta)
                VALUES (?, 0, 0, 0, 0)
            """, (today,))
            
            # Actualizar valores
            if total_consultas > 0 or consultas_exitosas > 0 or usuarios_nuevos > 0:
                cursor.execute("""
                    UPDATE estadisticas_sistema 
                    SET total_consultas = total_consultas + ?,
                        consultas_exitosas = consultas_exitosas + ?,
                        usuarios_nuevos = usuarios_nuevos + ?,
                        tiempo_promedio_consulta = CASE 
                            WHEN total_consultas > 0 THEN 
                                ((tiempo_promedio_consulta * (total_consultas - ?)) + ?) / total_consultas
                            ELSE ? 
                        END,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE fecha = ?
                """, (total_consultas, consultas_exitosas, usuarios_nuevos, 
                     total_consultas, tiempo_consulta, tiempo_consulta, today))
            
        except Exception as e:
            logger.error(f"❌ Error actualizando estadísticas diarias: {e}")
    
    def get_system_stats(self) -> Dict:
        """Obtener estadísticas completas del sistema"""
        try:
            with self.connection_manager.get_cursor() as cursor:
                stats = {}
                
                # Estadísticas generales
                cursor.execute("SELECT COUNT(*) FROM usuarios")
                stats['total_usuarios'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM consultas_vehiculares")
                stats['total_consultas'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM consultas_vehiculares WHERE consulta_exitosa = 1")
                stats['consultas_exitosas'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT AVG(tiempo_consulta) FROM consultas_vehiculares WHERE consulta_exitosa = 1")
                result = cursor.fetchone()[0]
                stats['tiempo_promedio'] = round(result, 2) if result else 0
                
                # Tasa de éxito
                if stats['total_consultas'] > 0:
                    stats['tasa_exito'] = round((stats['consultas_exitosas'] / stats['total_consultas']) * 100, 2)
                else:
                    stats['tasa_exito'] = 0
                
                # Estadísticas de hoy
                today = date.today()
                cursor.execute("""
                    SELECT COUNT(*) FROM consultas_vehiculares 
                    WHERE DATE(created_at) = ?
                """, (today,))
                stats['consultas_hoy'] = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT COUNT(DISTINCT usuario_id) FROM consultas_vehiculares 
                    WHERE DATE(created_at) = ?
                """, (today,))
                stats['usuarios_activos_hoy'] = cursor.fetchone()[0]
                
                # Marcas más consultadas
                cursor.execute("""
                    SELECT marca, COUNT(*) as count 
                    FROM datos_vehiculares 
                    WHERE marca IS NOT NULL AND marca != ''
                    GROUP BY marca 
                    ORDER BY count DESC 
                    LIMIT 5
                """)
                stats['marcas_populares'] = {row['marca']: row['count'] for row in cursor.fetchall()}
                
                # Años más consultados
                cursor.execute("""
                    SELECT anio_fabricacion, COUNT(*) as count 
                    FROM datos_vehiculares 
                    WHERE anio_fabricacion IS NOT NULL AND anio_fabricacion > 1980
                    GROUP BY anio_fabricacion 
                    ORDER BY count DESC 
                    LIMIT 5
                """)
                stats['anios_populares'] = {str(row['anio_fabricacion']): row['count'] for row in cursor.fetchall()}
                
                # Estadísticas de los últimos 7 días
                cursor.execute("""
                    SELECT 
                        fecha,
                        total_consultas,
                        consultas_exitosas,
                        usuarios_nuevos
                    FROM estadisticas_sistema 
                    WHERE fecha >= date('now', '-7 days')
                    ORDER BY fecha DESC
                """)
                stats['ultimos_7_dias'] = [dict(row) for row in cursor.fetchall()]
                
                # Estado del sistema
                cursor.execute("SELECT COUNT(*) FROM consultas_vehiculares WHERE created_at >= datetime('now', '-1 hour')")
                stats['consultas_ultima_hora'] = cursor.fetchone()[0]
                
                # Información del sistema
                stats['version'] = '2.0.0'
                stats['autor'] = 'Erick Costa'
                stats['proyecto'] = 'Construcción de Software'
                stats['tema'] = 'Futurista - Azul Neon'
                stats['ultima_actualizacion'] = datetime.now().isoformat()
                
                return stats
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas del sistema: {e}")
            return {}
    
    def get_dashboard_data(self) -> Dict:
        """Obtener datos completos para dashboard de administración"""
        try:
            stats = self.get_system_stats()
            
            with self.connection_manager.get_cursor() as cursor:
                # Consultas recientes
                cursor.execute("""
                    SELECT cv.*, u.nombre, u.cedula, dv.marca, dv.modelo
                    FROM consultas_vehiculares cv
                    LEFT JOIN usuarios u ON cv.usuario_id = u.id
                    LEFT JOIN datos_vehiculares dv ON cv.id = dv.consulta_id
                    ORDER BY cv.created_at DESC
                    LIMIT 10
                """)
                stats['consultas_recientes'] = [dict(row) for row in cursor.fetchall()]
                
                # Usuarios más activos
                cursor.execute("""
                    SELECT u.nombre, u.cedula, u.total_consultas, u.ultimo_acceso
                    FROM usuarios u
                    ORDER BY u.total_consultas DESC
                    LIMIT 5
                """)
                stats['usuarios_activos'] = [dict(row) for row in cursor.fetchall()]
                
                # Placas más consultadas
                cursor.execute("""
                    SELECT numero_placa, COUNT(*) as count, MAX(created_at) as ultima_consulta
                    FROM consultas_vehiculares
                    WHERE consulta_exitosa = 1
                    GROUP BY numero_placa
                    ORDER BY count DESC
                    LIMIT 10
                """)
                stats['placas_populares'] = [dict(row) for row in cursor.fetchall()]
                
                # Errores comunes
                cursor.execute("""
                    SELECT mensaje_error, COUNT(*) as count
                    FROM consultas_vehiculares
                    WHERE consulta_exitosa = 0 AND mensaje_error IS NOT NULL
                    GROUP BY mensaje_error
                    ORDER BY count DESC
                    LIMIT 5
                """)
                stats['errores_comunes'] = [dict(row) for row in cursor.fetchall()]
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo datos de dashboard: {e}")
            return {}
    
    # ==================== MÉTODOS DE CONFIGURACIÓN ====================
    
    def get_config(self, clave: str, default=None):
        """Obtener valor de configuración"""
        try:
            with self.connection_manager.get_cursor() as cursor:
                cursor.execute("SELECT valor, tipo_dato FROM configuracion_sistema WHERE clave = ?", (clave,))
                result = cursor.fetchone()
                
                if result:
                    valor, tipo_dato = result['valor'], result['tipo_dato']
                    
                    # Convertir según tipo de dato
                    if tipo_dato == 'integer':
                        return int(valor)
                    elif tipo_dato == 'float':
                        return float(valor)
                    elif tipo_dato == 'boolean':
                        return valor.lower() in ('true', '1', 'yes', 'on')
                    else:
                        return valor
                
                return default
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo configuración: {e}")
            return default
    
    def set_config(self, clave: str, valor: Any, descripcion: str = None, tipo_dato: str = 'string'):
        """Establecer valor de configuración"""
        try:
            with self.connection_manager.get_cursor() as cursor:
                cursor.execute("""
                    INSERT OR REPLACE INTO configuracion_sistema 
                    (clave, valor, descripcion, tipo_dato, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (clave, str(valor), descripcion, tipo_dato))
                
                logger.info(f"⚙️ Configuración actualizada: {clave} = {valor}")
                
        except Exception as e:
            logger.error(f"❌ Error estableciendo configuración: {e}")
    
    # ==================== MÉTODOS DE LOGS ====================
    
    def log_event(self, nivel: str, modulo: str, mensaje: str, detalles: Dict = None, 
                  ip_origen: str = None, usuario_id: int = None, session_id: str = None):
        """Registrar evento en logs del sistema"""
        try:
            with self.connection_manager.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO logs_sistema 
                    (nivel, modulo, mensaje, detalles_json, ip_origen, usuario_id, session_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    nivel, modulo, mensaje, 
                    json.dumps(detalles, ensure_ascii=False) if detalles else None,
                    ip_origen, usuario_id, session_id
                ))
                
        except Exception as e:
            logger.error(f"❌ Error registrando log: {e}")
    
    def get_logs(self, limite: int = 100, nivel: str = None, modulo: str = None) -> List[Dict]:
        """Obtener logs del sistema"""
        try:
            with self.connection_manager.get_cursor() as cursor:
                query = "SELECT * FROM logs_sistema"
                params = []
                conditions = []
                
                if nivel:
                    conditions.append("nivel = ?")
                    params.append(nivel)
                
                if modulo:
                    conditions.append("modulo = ?")
                    params.append(modulo)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                query += " ORDER BY created_at DESC LIMIT ?"
                params.append(limite)
                
                cursor.execute(query, params)
                
                logs = []
                for row in cursor.fetchall():
                    log = dict(row)
                    if log.get('detalles_json'):
                        try:
                            log['detalles'] = json.loads(log['detalles_json'])
                        except:
                            pass
                    logs.append(log)
                
                return logs
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo logs: {e}")
            return []
    
    # ==================== MÉTODOS DE MANTENIMIENTO ====================
    
    def cleanup_old_data(self, days_old: int = 90):
        """Limpiar datos antiguos del sistema"""
        try:
            with self.connection_manager.get_cursor() as cursor:
                cutoff_date = datetime.now() - timedelta(days=days_old)
                
                # Limpiar consultas antiguas sin éxito
                cursor.execute("""
                    DELETE FROM consultas_vehiculares 
                    WHERE consulta_exitosa = 0 AND created_at < ?
                """, (cutoff_date,))
                deleted_consultas = cursor.rowcount
                
                # Limpiar logs antiguos
                cursor.execute("""
                    DELETE FROM logs_sistema 
                    WHERE created_at < ?
                """, (cutoff_date,))
                deleted_logs = cursor.rowcount
                
                # Optimizar base de datos
                cursor.execute("VACUUM")
                
                logger.info(f"🧹 Limpieza completada: {deleted_consultas} consultas, {deleted_logs} logs eliminados")
                
                return {
                    'consultas_eliminadas': deleted_consultas,
                    'logs_eliminados': deleted_logs
                }
                
        except Exception as e:
            logger.error(f"❌ Error en limpieza de datos: {e}")
            return {}
    
    def backup_database(self, backup_path: str = None) -> str:
        """Crear backup de la base de datos"""
        try:
            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"backups/ecplacas_backup_{timestamp}.sqlite"
            
            # Asegurar directorio
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # Crear backup
            with sqlite3.connect(self.db_path) as source:
                with sqlite3.connect(backup_path) as backup:
                    source.backup(backup)
            
            logger.info(f"💾 Backup creado exitosamente: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"❌ Error creando backup: {e}")
            return ""
    
    def get_database_info(self) -> Dict:
        """Obtener información de la base de datos"""
        try:
            with self.connection_manager.get_cursor() as cursor:
                info = {}
                
                # Tamaño del archivo
                if os.path.exists(self.db_path):
                    info['tamaño_archivo'] = os.path.getsize(self.db_path)
                    info['tamaño_mb'] = round(info['tamaño_archivo'] / (1024 * 1024), 2)
                
                # Información de tablas
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """)
                tables = [row[0] for row in cursor.fetchall()]
                info['tablas'] = tables
                
                # Conteo de registros por tabla
                table_counts = {}
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    table_counts[table] = cursor.fetchone()[0]
                info['registros_por_tabla'] = table_counts
                
                # Versión SQLite
                cursor.execute("SELECT sqlite_version()")
                info['version_sqlite'] = cursor.fetchone()[0]
                
                # Configuración PRAGMA
                pragmas = ['journal_mode', 'synchronous', 'foreign_keys', 'auto_vacuum']
                pragma_info = {}
                for pragma in pragmas:
                    cursor.execute(f"PRAGMA {pragma}")
                    pragma_info[pragma] = cursor.fetchone()[0]
                info['configuracion'] = pragma_info
                
                return info
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo información de base de datos: {e}")
            return {}
    
    def close(self):
        """Cerrar conexiones de base de datos"""
        try:
            if hasattr(self.connection_manager.local, 'connection'):
                self.connection_manager.local.connection.close()
                delattr(self.connection_manager.local, 'connection')
            logger.info("🔒 Conexiones de base de datos cerradas")
        except Exception as e:
            logger.error(f"❌ Error cerrando base de datos: {e}")

# Instancia global de la base de datos
db = ECPlacasDatabase()

if __name__ == "__main__":
    # Pruebas básicas
    print("🧪 Probando ECPlacas Database...")
    
    # Obtener estadísticas
    stats = db.get_system_stats()
    print(f"📊 Estadísticas del sistema: {stats}")
    
    # Obtener información de la base de datos
    info = db.get_database_info()
    print(f"💾 Información de base de datos: {info}")
    
    print("✅ Pruebas completadas exitosamente")
