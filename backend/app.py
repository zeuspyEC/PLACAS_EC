#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================
ECPlacas 2.0 - Sistema de Consulta Vehicular
==========================================
Proyecto: Construcción de Software
Desarrollado por: Erick Costa
Temática: Futurista con paleta azul neon, cyan y negro
==========================================

Backend principal con Flask para consultas vehiculares integrales
Optimizado para máximo rendimiento, sostenibilidad y escalabilidad
"""

import asyncio
import aiohttp
import json
import time
import logging
import threading
import uuid
import os
import sys
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path
import sqlite3
from contextlib import asynccontextmanager

# Flask imports
from flask import Flask, request, jsonify, Response, send_from_directory, g
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configuración de paths para el proyecto
BACKEND_ROOT = Path(__file__).parent
PROJECT_ROOT = BACKEND_ROOT.parent
FRONTEND_PATH = PROJECT_ROOT / "frontend"
DATABASE_PATH = BACKEND_ROOT / "database"
LOGS_PATH = BACKEND_ROOT / "logs"

# Asegurar que directorios existen
for path in [DATABASE_PATH, LOGS_PATH, LOGS_PATH / "app", LOGS_PATH / "access", LOGS_PATH / "error"]:
    path.mkdir(parents=True, exist_ok=True)

# Configuración de logging profesional y rotativo
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Configurar sistema de logging profesional y sostenible"""
    logger = logging.getLogger('ecplacas')
    logger.setLevel(logging.INFO)
    
    # Formatter detallado para archivos
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Formatter simple para consola
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Handler de archivo rotativo (sostenibilidad)
    file_handler = RotatingFileHandler(
        LOGS_PATH / "ecplacas.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(detailed_formatter)
    file_handler.setLevel(logging.INFO)
    
    # Handler de consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)
    
    # Configurar logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return logger

# Inicializar logging
logger = setup_logging()

# Configuración de la API principal optimizada
API_CONFIG = {
    'base_url': 'https://servicios.axiscloud.ec/CRV/paginas',
    'endpoint': '/datosVehiculo.jsp',
    'default_empresa': '02',
    'timeout': 30,
    'max_retries': 3,
    'rate_limit': 1.0,  # segundos entre requests
    'connection_pool_size': 10
}

# Códigos de provincia para validación de cédulas ecuatorianas
PROVINCE_CODES = {
    '01': 'Azuay', '02': 'Bolívar', '03': 'Cañar', '04': 'Carchi',
    '05': 'Cotopaxi', '06': 'Chimborazo', '07': 'El Oro', '08': 'Esmeraldas',
    '09': 'Guayas', '10': 'Imbabura', '11': 'Loja', '12': 'Los Ríos',
    '13': 'Manabí', '14': 'Morona Santiago', '15': 'Napo', '16': 'Pastaza',
    '17': 'Pichincha', '18': 'Tungurahua', '19': 'Zamora Chinchipe',
    '20': 'Galápagos', '21': 'Sucumbíos', '22': 'Orellana',
    '23': 'Santo Domingo', '24': 'Santa Elena', '30': 'Exterior'
}

@dataclass
class UserData:
    """Estructura de datos del usuario optimizada"""
    nombre: str = ""
    cedula: str = ""
    telefono: str = ""
    correo: str = ""
    country_code: str = "+593"
    acepta_terminos: bool = False
    ip_address: str = ""
    user_agent: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class VehicleData:
    """Estructura completa de datos vehiculares ECPlacas 2.0"""
    # Identificación principal
    numero_placa: str = ""
    placa_original: str = ""
    placa_normalizada: str = ""
    
    # Datos de identificación vehicular
    vin_chasis: str = ""
    numero_motor: str = ""
    placa_anterior: str = ""
    
    # Información del modelo
    marca: str = ""
    modelo: str = ""
    anio_fabricacion: int = 0
    pais_fabricacion: str = ""
    
    # Características físicas
    clase_vehiculo: str = ""
    tipo_vehiculo: str = ""
    color_primario: str = ""
    color_secundario: str = ""
    peso_vehiculo: str = ""
    tipo_carroceria: str = ""
    
    # Datos de matrícula y revisión
    matricula_desde: str = ""
    matricula_hasta: str = ""
    ano_ultima_revision: str = ""
    ultima_revision_desde: str = ""
    ultima_revision_hasta: str = ""
    servicio: str = ""
    ultima_actualizacion: str = ""
    
    # Estado CRV (Centro de Retención Vehicular)
    indicador_crv: str = ""
    orden_crv: str = ""
    centro_retencion: str = ""
    tipo_retencion: str = ""
    motivo_retencion: str = ""
    fecha_inicio_retencion: str = ""
    dias_retencion: str = ""
    grua: str = ""
    area_ubicacion: str = ""
    columna: str = ""
    fila: str = ""
    
    # Análisis ECPlacas 2.0
    estado_matricula: str = ""
    dias_hasta_vencimiento: int = 0
    estimacion_valor: float = 0.0
    categoria_riesgo: str = "BAJO"
    puntuacion_general: int = 0
    recomendacion: str = ""
    
    # Metadatos
    session_id: str = ""
    timestamp_consulta: datetime = field(default_factory=datetime.now)
    tiempo_consulta: float = 0.0
    consulta_exitosa: bool = False
    mensaje_error: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para API"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result

class PlateValidator:
    """Validador avanzado de placas ecuatorianas con optimizaciones"""
    
    # Cache de validaciones para rendimiento
    _validation_cache = {}
    
    @classmethod
    def normalize_plate(cls, placa: str) -> tuple[str, str, bool]:
        """Normaliza placas ecuatorianas con detección inteligente y cache"""
        if not placa or not isinstance(placa, str):
            return placa, placa, False
        
        # Verificar cache primero (rendimiento)
        cache_key = placa.upper().strip()
        if cache_key in cls._validation_cache:
            return cls._validation_cache[cache_key]
        
        # Limpiar entrada
        placa_clean = re.sub(r'[^A-Z0-9]', '', placa.upper())
        placa_original = placa_clean
        
        # Patrón para normalización automática
        pattern_3_digits = r'^([A-Z]{2,3})(\d{3})$'
        match = re.match(pattern_3_digits, placa_clean)
        
        if match:
            letters = match.group(1)
            numbers = match.group(2)
            placa_normalizada = f"{letters}0{numbers}"
            
            result = (placa_original, placa_normalizada, True)
            logger.info(f"🔧 Placa normalizada: {placa_original} → {placa_normalizada}")
        else:
            result = (placa_original, placa_clean, False)
        
        # Almacenar en cache (sostenibilidad)
        cls._validation_cache[cache_key] = result
        
        # Limpiar cache si crece mucho (gestión de memoria)
        if len(cls._validation_cache) > 1000:
            cls._validation_cache.clear()
        
        return result
    
    @staticmethod
    def validate_plate_format(placa: str) -> bool:
        """Valida formato de placa ecuatoriana optimizado"""
        if not placa or len(placa) < 6 or len(placa) > 8:
            return False
        
        patterns = [
            r'^[A-Z]{2,3}\d{3,4}$',
            r'^[A-Z]{2,3}-\d{3,4}$'
        ]
        
        return any(re.match(pattern, placa.upper()) for pattern in patterns)

class CedulaValidator:
    """Validador de cédulas ecuatorianas con cache"""
    
    _validation_cache = {}
    
    @classmethod
    def validate_ecuadorian_id(cls, cedula: str) -> bool:
        """Valida cédula ecuatoriana con algoritmo oficial y cache"""
        if not cedula or len(cedula) != 10 or not cedula.isdigit():
            return False
        
        # Verificar cache
        if cedula in cls._validation_cache:
            return cls._validation_cache[cedula]
        
        # Verificar código de provincia
        province_code = cedula[:2]
        if province_code not in PROVINCE_CODES:
            cls._validation_cache[cedula] = False
            return False
        
        # Verificar tercer dígito (debe ser menor a 6 para personas naturales)
        if int(cedula[2]) >= 6:
            cls._validation_cache[cedula] = False
            return False
        
        # Algoritmo de validación
        digits = [int(d) for d in cedula]
        coefficients = [2, 1, 2, 1, 2, 1, 2, 1, 2]
        total = 0
        
        for i in range(9):
            result = digits[i] * coefficients[i]
            if result > 9:
                result -= 9
            total += result
        
        check_digit = (10 - (total % 10)) % 10
        is_valid = check_digit == digits[9]
        
        # Almacenar en cache
        cls._validation_cache[cedula] = is_valid
        
        # Limpiar cache si crece mucho
        if len(cls._validation_cache) > 10000:
            cls._validation_cache.clear()
        
        return is_valid

class DatabaseManager:
    """Gestor de base de datos SQLite optimizado para ECPlacas 2.0"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(DATABASE_PATH / "ecplacas.sqlite")
        self.connection_pool = []
        self.pool_size = 5
        self.init_database()
    
    def get_connection(self):
        """Obtener conexión del pool (rendimiento)"""
        if self.connection_pool:
            return self.connection_pool.pop()
        else:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")  # Optimización
            conn.execute("PRAGMA synchronous = NORMAL")  # Balance rendimiento/seguridad
            return conn
    
    def return_connection(self, conn):
        """Devolver conexión al pool (sostenibilidad)"""
        if len(self.connection_pool) < self.pool_size:
            self.connection_pool.append(conn)
        else:
            conn.close()
    
    def init_database(self):
        """Inicializar base de datos con esquema completo optimizado"""
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Configuraciones de optimización
            cursor.execute("PRAGMA journal_mode = WAL")
            cursor.execute("PRAGMA synchronous = NORMAL")
            cursor.execute("PRAGMA cache_size = 10000")
            cursor.execute("PRAGMA temp_store = MEMORY")
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Tabla de usuarios optimizada
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
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    -- Validaciones a nivel de base de datos
                    CHECK (length(cedula) = 10),
                    CHECK (total_consultas >= 0),
                    CHECK (length(nombre) >= 2)
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
                    api_utilizada TEXT DEFAULT 'ant_principal',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE SET NULL,
                    
                    -- Validaciones
                    CHECK (tiempo_consulta >= 0),
                    CHECK (length(numero_placa) >= 6)
                )
            """)
            
            # Tabla de datos vehiculares completos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS datos_vehiculares (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    consulta_id INTEGER NOT NULL,
                    
                    -- Datos de identificación
                    vin_chasis TEXT,
                    numero_motor TEXT,
                    placa_anterior TEXT,
                    
                    -- Datos del modelo
                    marca TEXT,
                    modelo TEXT,
                    anio_fabricacion INTEGER,
                    pais_fabricacion TEXT,
                    
                    -- Características físicas
                    clase_vehiculo TEXT,
                    tipo_vehiculo TEXT,
                    color_primario TEXT,
                    color_secundario TEXT,
                    peso_vehiculo TEXT,
                    tipo_carroceria TEXT,
                    
                    -- Datos de matrícula y revisión
                    matricula_desde TEXT,
                    matricula_hasta TEXT,
                    ano_ultima_revision TEXT,
                    ultima_revision_desde TEXT,
                    ultima_revision_hasta TEXT,
                    servicio TEXT,
                    ultima_actualizacion TEXT,
                    
                    -- Datos CRV (Centro de Retención Vehicular)
                    indicador_crv TEXT,
                    orden_crv TEXT,
                    centro_retencion TEXT,
                    tipo_retencion TEXT,
                    motivo_retencion TEXT,
                    fecha_inicio_retencion TEXT,
                    dias_retencion TEXT,
                    grua TEXT,
                    area_ubicacion TEXT,
                    columna TEXT,
                    fila TEXT,
                    
                    -- Análisis ECPlacas 2.0
                    estado_matricula TEXT,
                    dias_hasta_vencimiento INTEGER,
                    estimacion_valor REAL,
                    categoria_riesgo TEXT DEFAULT 'BAJO',
                    puntuacion_general INTEGER DEFAULT 0,
                    recomendacion TEXT,
                    
                    -- Datos completos en JSON para backup
                    datos_completos_json TEXT,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (consulta_id) REFERENCES consultas_vehiculares (id) ON DELETE CASCADE,
                    
                    -- Validaciones
                    CHECK (anio_fabricacion >= 1950 OR anio_fabricacion IS NULL),
                    CHECK (estimacion_valor >= 0 OR estimacion_valor IS NULL),
                    CHECK (puntuacion_general >= 0 AND puntuacion_general <= 100),
                    CHECK (estado_matricula IN ('VIGENTE', 'POR_VENCER', 'VENCIDA', 'INDETERMINADO') OR estado_matricula IS NULL)
                )
            """)
            
            # Tabla de estadísticas del sistema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS estadisticas_sistema (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha DATE UNIQUE NOT NULL,
                    total_consultas INTEGER DEFAULT 0,
                    consultas_exitosas INTEGER DEFAULT 0,
                    usuarios_nuevos INTEGER DEFAULT 0,
                    usuarios_activos INTEGER DEFAULT 0,
                    tiempo_promedio_consulta REAL DEFAULT 0,
                    placas_consultadas TEXT, -- JSON array de placas únicas del día
                    marcas_populares TEXT,   -- JSON object con conteo de marcas
                    errores_comunes TEXT,    -- JSON array de errores más frecuentes
                    apis_utilizadas TEXT,    -- JSON object con uso por API
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    CHECK (total_consultas >= consultas_exitosas),
                    CHECK (usuarios_nuevos >= 0),
                    CHECK (tiempo_promedio_consulta >= 0)
                )
            """)
            
            # Tabla de configuración del sistema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS configuracion_sistema (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    clave TEXT UNIQUE NOT NULL,
                    valor TEXT,
                    descripcion TEXT,
                    tipo_dato TEXT DEFAULT 'string', -- string, integer, float, boolean, json
                    categoria TEXT DEFAULT 'general',
                    editable BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    CHECK (tipo_dato IN ('string', 'integer', 'float', 'boolean', 'json'))
                )
            """)
            
            # Crear índices para optimización de rendimiento
            indices = [
                "CREATE INDEX IF NOT EXISTS idx_usuarios_cedula ON usuarios(cedula)",
                "CREATE INDEX IF NOT EXISTS idx_usuarios_ultimo_acceso ON usuarios(ultimo_acceso)",
                "CREATE INDEX IF NOT EXISTS idx_usuarios_total_consultas ON usuarios(total_consultas DESC)",
                
                "CREATE INDEX IF NOT EXISTS idx_consultas_placa ON consultas_vehiculares(numero_placa)",
                "CREATE INDEX IF NOT EXISTS idx_consultas_placa_normalizada ON consultas_vehiculares(placa_normalizada)",
                "CREATE INDEX IF NOT EXISTS idx_consultas_fecha ON consultas_vehiculares(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_consultas_exitosa ON consultas_vehiculares(consulta_exitosa)",
                "CREATE INDEX IF NOT EXISTS idx_consultas_usuario ON consultas_vehiculares(usuario_id)",
                "CREATE INDEX IF NOT EXISTS idx_consultas_session ON consultas_vehiculares(session_id)",
                "CREATE INDEX IF NOT EXISTS idx_consultas_ip ON consultas_vehiculares(ip_origen)",
                
                "CREATE INDEX IF NOT EXISTS idx_vehiculos_marca ON datos_vehiculares(marca)",
                "CREATE INDEX IF NOT EXISTS idx_vehiculos_anio ON datos_vehiculares(anio_fabricacion)",
                "CREATE INDEX IF NOT EXISTS idx_vehiculos_tipo ON datos_vehiculares(tipo_vehiculo)",
                "CREATE INDEX IF NOT EXISTS idx_vehiculos_estado_matricula ON datos_vehiculares(estado_matricula)",
                "CREATE INDEX IF NOT EXISTS idx_vehiculos_estimacion_valor ON datos_vehiculares(estimacion_valor)",
                "CREATE INDEX IF NOT EXISTS idx_vehiculos_consulta_id ON datos_vehiculares(consulta_id)",
                
                "CREATE INDEX IF NOT EXISTS idx_estadisticas_fecha ON estadisticas_sistema(fecha)"
            ]
            
            for indice in indices:
                cursor.execute(indice)
            
            # Trigger para actualizar timestamp de usuarios
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS tr_usuarios_updated_at
                AFTER UPDATE ON usuarios
                FOR EACH ROW
                BEGIN
                    UPDATE usuarios SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END
            """)
            
            # Trigger para actualizar estadísticas automáticamente
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS tr_actualizar_estadisticas_consulta
                AFTER INSERT ON consultas_vehiculares
                FOR EACH ROW
                BEGIN
                    INSERT OR IGNORE INTO estadisticas_sistema (fecha, total_consultas, consultas_exitosas)
                    VALUES (DATE(NEW.created_at), 0, 0);
                    
                    UPDATE estadisticas_sistema 
                    SET total_consultas = total_consultas + 1,
                        consultas_exitosas = consultas_exitosas + CASE WHEN NEW.consulta_exitosa = 1 THEN 1 ELSE 0 END,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE fecha = DATE(NEW.created_at);
                END
            """)
            
            conn.commit()
            self.return_connection(conn)
            logger.info("✅ Base de datos ECPlacas 2.0 inicializada correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando base de datos: {e}")
            raise
    
    def save_user(self, user_data: UserData) -> int:
        """Guardar o actualizar usuario con optimizaciones"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Verificar si usuario existe
            cursor.execute("SELECT id FROM usuarios WHERE cedula = ?", (user_data.cedula,))
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
                    user_data.nombre, user_data.telefono, user_data.correo,
                    user_data.country_code, user_data.ip_address, 
                    user_data.user_agent, user_data.cedula
                ))
                user_id = existing_user[0]
            else:
                # Crear nuevo usuario
                cursor.execute("""
                    INSERT INTO usuarios (nombre, cedula, telefono, correo, 
                                        country_code, ip_address, user_agent, 
                                        total_consultas, ultimo_acceso)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
                """, (
                    user_data.nombre, user_data.cedula, user_data.telefono, 
                    user_data.correo, user_data.country_code, 
                    user_data.ip_address, user_data.user_agent
                ))
                user_id = cursor.lastrowid
            
            conn.commit()
            self.return_connection(conn)
            return user_id
            
        except Exception as e:
            logger.error(f"❌ Error guardando usuario: {e}")
            if 'conn' in locals():
                self.return_connection(conn)
            return 0
    
    def save_vehicle_consultation(self, vehicle_data: VehicleData, user_id: int) -> int:
        """Guardar consulta vehicular completa con optimizaciones"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Guardar consulta
            cursor.execute("""
                INSERT INTO consultas_vehiculares 
                (session_id, usuario_id, numero_placa, placa_original, 
                 placa_normalizada, consulta_exitosa, tiempo_consulta, mensaje_error,
                 ip_origen, user_agent, api_utilizada)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                vehicle_data.session_id, user_id, vehicle_data.numero_placa,
                vehicle_data.placa_original, vehicle_data.placa_normalizada,
                vehicle_data.consulta_exitosa, vehicle_data.tiempo_consulta,
                vehicle_data.mensaje_error, '', '', 'ant_principal'
            ))
            
            consulta_id = cursor.lastrowid
            
            # Guardar datos vehiculares si la consulta fue exitosa
            if vehicle_data.consulta_exitosa:
                cursor.execute("""
                    INSERT INTO datos_vehiculares 
                    (consulta_id, vin_chasis, numero_motor, placa_anterior,
                     marca, modelo, anio_fabricacion, pais_fabricacion,
                     clase_vehiculo, tipo_vehiculo, color_primario, color_secundario,
                     peso_vehiculo, tipo_carroceria, matricula_desde, matricula_hasta,
                     ano_ultima_revision, ultima_revision_desde, ultima_revision_hasta,
                     servicio, ultima_actualizacion, indicador_crv, orden_crv,
                     centro_retencion, tipo_retencion, motivo_retencion,
                     fecha_inicio_retencion, dias_retencion, grua, area_ubicacion,
                     columna, fila, estado_matricula, dias_hasta_vencimiento,
                     estimacion_valor, categoria_riesgo, puntuacion_general,
                     recomendacion, datos_completos_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    consulta_id, vehicle_data.vin_chasis, vehicle_data.numero_motor,
                    vehicle_data.placa_anterior, vehicle_data.marca, vehicle_data.modelo,
                    vehicle_data.anio_fabricacion, vehicle_data.pais_fabricacion,
                    vehicle_data.clase_vehiculo, vehicle_data.tipo_vehiculo,
                    vehicle_data.color_primario, vehicle_data.color_secundario,
                    vehicle_data.peso_vehiculo, vehicle_data.tipo_carroceria,
                    vehicle_data.matricula_desde, vehicle_data.matricula_hasta,
                    vehicle_data.ano_ultima_revision, vehicle_data.ultima_revision_desde,
                    vehicle_data.ultima_revision_hasta, vehicle_data.servicio,
                    vehicle_data.ultima_actualizacion, vehicle_data.indicador_crv,
                    vehicle_data.orden_crv, vehicle_data.centro_retencion,
                    vehicle_data.tipo_retencion, vehicle_data.motivo_retencion,
                    vehicle_data.fecha_inicio_retencion, vehicle_data.dias_retencion,
                    vehicle_data.grua, vehicle_data.area_ubicacion, vehicle_data.columna,
                    vehicle_data.fila, vehicle_data.estado_matricula,
                    vehicle_data.dias_hasta_vencimiento, vehicle_data.estimacion_valor,
                    vehicle_data.categoria_riesgo, vehicle_data.puntuacion_general,
                    vehicle_data.recomendacion, json.dumps(vehicle_data.to_dict())
                ))
            
            conn.commit()
            self.return_connection(conn)
            return consulta_id
            
        except Exception as e:
            logger.error(f"❌ Error guardando consulta vehicular: {e}")
            if 'conn' in locals():
                self.return_connection(conn)
            return 0
    
    def get_system_stats(self) -> Dict:
        """Obtener estadísticas del sistema optimizadas"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Estadísticas generales
            cursor.execute("SELECT COUNT(*) FROM usuarios")
            total_usuarios = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM consultas_vehiculares")
            total_consultas = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM consultas_vehiculares WHERE consulta_exitosa = 1")
            consultas_exitosas = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(tiempo_consulta) FROM consultas_vehiculares WHERE consulta_exitosa = 1")
            tiempo_promedio = cursor.fetchone()[0] or 0
            
            # Consultas de hoy
            today = datetime.now().date()
            cursor.execute("""
                SELECT COUNT(*) FROM consultas_vehiculares 
                WHERE DATE(created_at) = ?
            """, (today,))
            consultas_hoy = cursor.fetchone()[0]
            
            # Marcas más consultadas (últimos 30 días)
            cursor.execute("""
                SELECT marca, COUNT(*) as count 
                FROM datos_vehiculares dv
                JOIN consultas_vehiculares cv ON dv.consulta_id = cv.id
                WHERE marca IS NOT NULL AND marca != ''
                AND cv.created_at >= date('now', '-30 days')
                GROUP BY marca 
                ORDER BY count DESC 
                LIMIT 5
            """)
            marcas_populares = dict(cursor.fetchall())
            
            self.return_connection(conn)
            
            return {
                'total_usuarios': total_usuarios,
                'total_consultas': total_consultas,
                'consultas_exitosas': consultas_exitosas,
                'tasa_exito': round((consultas_exitosas / total_consultas * 100) if total_consultas > 0 else 0, 2),
                'tiempo_promedio_consulta': round(tiempo_promedio, 2),
                'consultas_hoy': consultas_hoy,
                'marcas_populares': marcas_populares
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            if 'conn' in locals():
                self.return_connection(conn)
            return {}
    
    def backup_database(self) -> Optional[str]:
        """Crear backup de la base de datos"""
        try:
            backup_dir = DATABASE_PATH / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"ecplacas_backup_{timestamp}.sqlite"
            
            # Usar SQLite backup API
            source = sqlite3.connect(self.db_path)
            backup = sqlite3.connect(str(backup_path))
            
            source.backup(backup)
            
            source.close()
            backup.close()
            
            logger.info(f"✅ Backup creado: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"❌ Error creando backup: {e}")
            return None
    
    def cleanup_old_data(self, days_old: int = 90) -> Dict:
        """Limpiar datos antiguos del sistema"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            # Limpiar consultas antiguas (cascada eliminará datos vehiculares)
            cursor.execute("""
                DELETE FROM consultas_vehiculares 
                WHERE created_at < ? AND consulta_exitosa = 0
            """, (cutoff_date,))
            
            deleted_consultas = cursor.rowcount
            
            # Limpiar estadísticas muy antiguas
            cursor.execute("""
                DELETE FROM estadisticas_sistema 
                WHERE created_at < ?
            """, (cutoff_date,))
            
            deleted_stats = cursor.rowcount
            
            conn.commit()
            self.return_connection(conn)
            
            result = {
                'consultas_eliminadas': deleted_consultas,
                'estadisticas_eliminadas': deleted_stats,
                'fecha_corte': cutoff_date.isoformat()
            }
            
            logger.info(f"✅ Limpieza completada: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error en limpieza: {e}")
            if 'conn' in locals():
                self.return_connection(conn)
            return {}

class VehicleConsultant:
    """Consultor principal de datos vehiculares optimizado"""
    
    def __init__(self):
        self.session = self._create_optimized_session()
        self.db = DatabaseManager()
        self.active_consultations = {}
        self.request_times = []  # Para rate limiting
        self._last_request_time = 0
    
    def _create_optimized_session(self) -> requests.Session:
        """Crear sesión HTTP optimizada para rendimiento"""
        session = requests.Session()
        
        # Estrategia de reintentos optimizada
        retry_strategy = Retry(
            total=API_CONFIG['max_retries'],
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=API_CONFIG['connection_pool_size'],
            pool_maxsize=API_CONFIG['connection_pool_size']
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Headers optimizados
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/html, */*',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'DNT': '1',
            'Upgrade-Insecure-Requests': '1'
        })
        
        return session
    
    def _apply_rate_limiting(self):
        """Aplicar rate limiting para sostenibilidad"""
        current_time = time.time()
        
        # Verificar si necesitamos esperar
        if self._last_request_time > 0:
            time_since_last = current_time - self._last_request_time
            if time_since_last < API_CONFIG['rate_limit']:
                sleep_time = API_CONFIG['rate_limit'] - time_since_last
                time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    async def consultar_vehiculo_completo(self, placa: str, user_data: UserData, session_id: str) -> VehicleData:
        """Consulta completa de datos vehiculares con optimizaciones"""
        start_time = time.time()
        
        # Normalizar placa
        placa_original, placa_normalizada, was_modified = PlateValidator.normalize_plate(placa)
        
        vehicle_data = VehicleData(
            numero_placa=placa_normalizada,
            placa_original=placa_original,
            placa_normalizada=placa_normalizada,
            session_id=session_id
        )
        
        try:
            logger.info(f"🚀 Iniciando consulta ECPlacas 2.0 para: {placa_original} → {placa_normalizada}")
            
            # Aplicar rate limiting
            self._apply_rate_limiting()
            
            # Actualizar estado de consulta
            self.active_consultations[session_id] = {
                'status': 'consultando_api',
                'progress': 25,
                'message': '🔍 Consultando datos vehiculares ANT...'
            }
            
            # Consultar datos desde la API
            api_data = await self._consultar_api_externa(placa_normalizada)
            
            if api_data and api_data.get('codError') == '0':
                # Actualizar progreso
                self.active_consultations[session_id] = {
                    'status': 'procesando_datos',
                    'progress': 60,
                    'message': '⚙️ Procesando información vehicular...'
                }
                
                # Procesar datos exitosos
                self._procesar_datos_vehiculares(vehicle_data, api_data.get('campos', {}))
                
                # Actualizar progreso
                self.active_consultations[session_id] = {
                    'status': 'analizando',
                    'progress': 80,
                    'message': '🔬 Realizando análisis inteligente...'
                }
                
                # Realizar análisis adicional
                self._analizar_estado_vehiculo(vehicle_data)
                
                vehicle_data.consulta_exitosa = True
                logger.info(f"✅ Consulta exitosa para {placa_normalizada}")
                
            else:
                vehicle_data.consulta_exitosa = False
                vehicle_data.mensaje_error = api_data.get('mensajeError', 'Error desconocido') if api_data else 'No se pudo conectar con el servicio'
                logger.warning(f"⚠️ Consulta fallida para {placa_normalizada}: {vehicle_data.mensaje_error}")
            
            vehicle_data.tiempo_consulta = time.time() - start_time
            
            # Actualizar progreso final
            self.active_consultations[session_id] = {
                'status': 'guardando',
                'progress': 90,
                'message': '💾 Guardando resultados...'
            }
            
            # Guardar en base de datos
            user_id = self.db.save_user(user_data)
            if user_id:
                consultation_id = self.db.save_vehicle_consultation(vehicle_data, user_id)
                logger.info(f"💾 Datos guardados - Usuario: {user_id}, Consulta: {consultation_id}")
            
            return vehicle_data
            
        except Exception as e:
            vehicle_data.tiempo_consulta = time.time() - start_time
            vehicle_data.consulta_exitosa = False
            vehicle_data.mensaje_error = str(e)
            logger.error(f"❌ Error en consulta: {e}")
            return vehicle_data
    
    async def _consultar_api_externa(self, placa: str) -> Optional[Dict]:
        """Consultar API externa de datos vehiculares con manejo de errores"""
        try:
            url = f"{API_CONFIG['base_url']}{API_CONFIG['endpoint']}"
            params = {
                'empresa': API_CONFIG['default_empresa'],
                'identidad': placa
            }
            
            response = self.session.get(url, params=params, timeout=API_CONFIG['timeout'])
            response.raise_for_status()
            
            # Verificar si la respuesta es JSON válida
            try:
                data = response.json()
            except json.JSONDecodeError:
                logger.error(f"❌ Respuesta no es JSON válida para {placa}")
                return None
            
            logger.info(f"✅ Respuesta recibida de API externa para {placa}")
            return data
            
        except requests.exceptions.Timeout:
            logger.error(f"⏰ Timeout consultando API externa para {placa}")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"🔌 Error de conexión con API externa para {placa}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"🌐 Error HTTP {e.response.status_code} para {placa}")
            return None
        except Exception as e:
            logger.error(f"❌ Error inesperado consultando API externa: {e}")
            return None
    
    def _procesar_datos_vehiculares(self, vehicle_data: VehicleData, campos: Dict):
        """Procesar datos vehiculares desde la respuesta de la API optimizado"""
        try:
            # Mapeo de campos optimizado
            field_mappings = {
                'lsDatosIdentificacion': {
                    'vin': 'vin_chasis',
                    'motor': 'numero_motor',
                    'placa anterior': 'placa_anterior'
                },
                'lsDatosModelo': {
                    'marca': 'marca',
                    'modelo': 'modelo',
                    'año fabricación': ('anio_fabricacion', int),
                    'país fabricación': 'pais_fabricacion'
                },
                'lsOtrasCaracteristicas': {
                    'clase': 'clase_vehiculo',
                    'tipo': 'tipo_vehiculo',
                    'color 1': 'color_primario',
                    'color 2': 'color_secundario',
                    'peso': 'peso_vehiculo',
                    'carrocería': 'tipo_carroceria'
                },
                'lsRevision': {
                    'matrícula desde': 'matricula_desde',
                    'matrícula hasta': 'matricula_hasta',
                    'año última revisión': 'ano_ultima_revision',
                    'última revisión desde': 'ultima_revision_desde',
                    'última revisión hasta': 'ultima_revision_hasta'
                },
                'lsCrv': {
                    'indicador crv': 'indicador_crv',
                    'orden crv': 'orden_crv',
                    'centro retención': 'centro_retencion',
                    'tipo retención': 'tipo_retencion',
                    'motivo retención': 'motivo_retencion',
                    'fecha inicio retención': 'fecha_inicio_retencion',
                    'días retención': 'dias_retencion',
                    'grúa': 'grua',
                    'área ubicación': 'area_ubicacion',
                    'columna': 'columna',
                    'fila': 'fila'
                }
            }
            
            # Procesar cada sección
            for section_key, field_map in field_mappings.items():
                section_data = campos.get(section_key, [])
                if isinstance(section_data, list):
                    for item in section_data:
                        etiqueta = item.get('etiqueta', '').lower()
                        valor = item.get('valor', '')
                        
                        for search_key, target_field in field_map.items():
                            if search_key in etiqueta:
                                if isinstance(target_field, tuple):
                                    field_name, field_type = target_field
                                    try:
                                        setattr(vehicle_data, field_name, field_type(valor) if valor else (0 if field_type == int else ''))
                                    except ValueError:
                                        setattr(vehicle_data, field_name, 0 if field_type == int else '')
                                else:
                                    setattr(vehicle_data, target_field, valor)
                                break
            
            # Datos adicionales
            vehicle_data.servicio = campos.get('lsServicio', '')
            vehicle_data.ultima_actualizacion = campos.get('lsUltimaActualizacion', '')
            
            logger.info(f"✅ Datos vehiculares procesados correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error procesando datos vehiculares: {e}")
    
    def _analizar_estado_vehiculo(self, vehicle_data: VehicleData):
        """Realizar análisis inteligente del estado del vehículo"""
        try:
            # Analizar estado de matrícula
            if vehicle_data.matricula_hasta:
                try:
                    fecha_vencimiento = datetime.strptime(vehicle_data.matricula_hasta.split(' ')[0], '%d-%m-%Y')
                    today = datetime.now()
                    dias_diferencia = (fecha_vencimiento - today).days
                    
                    vehicle_data.dias_hasta_vencimiento = dias_diferencia
                    
                    if dias_diferencia > 30:
                        vehicle_data.estado_matricula = "VIGENTE"
                        vehicle_data.categoria_riesgo = "BAJO"
                        vehicle_data.puntuacion_general = 85
                    elif dias_diferencia > 0:
                        vehicle_data.estado_matricula = "POR VENCER"
                        vehicle_data.categoria_riesgo = "MEDIO"
                        vehicle_data.puntuacion_general = 60
                    else:
                        vehicle_data.estado_matricula = "VENCIDA"
                        vehicle_data.categoria_riesgo = "ALTO"
                        vehicle_data.puntuacion_general = 25
                except:
                    vehicle_data.estado_matricula = "INDETERMINADO"
                    vehicle_data.categoria_riesgo = "MEDIO"
                    vehicle_data.puntuacion_general = 50
            
            # Estimación inteligente de valor
            if vehicle_data.anio_fabricacion > 0:
                anio_actual = datetime.now().year
                antiguedad = anio_actual - vehicle_data.anio_fabricacion
                
                # Valor base según marca (machine learning simplificado)
                brand_multipliers = {
                    'TOYOTA': 1.3, 'HONDA': 1.25, 'NISSAN': 1.2, 'MAZDA': 1.15,
                    'CHEVROLET': 1.0, 'HYUNDAI': 1.0, 'KIA': 0.95, 'FORD': 0.9,
                    'CHERY': 0.7, 'GREAT WALL': 0.7, 'JAC': 0.65, 'DONGFENG': 0.6
                }
                
                valor_base = 12000  # USD base
                multiplier = brand_multipliers.get(vehicle_data.marca.upper(), 0.8)
                valor_base *= multiplier
                
                # Ajuste por tipo de vehículo
                if 'SUV' in vehicle_data.tipo_vehiculo.upper() or 'JEEP' in vehicle_data.tipo_vehiculo.upper():
                    valor_base *= 1.2
                elif 'SEDAN' in vehicle_data.tipo_vehiculo.upper():
                    valor_base *= 1.1
                elif 'HATCHBACK' in vehicle_data.tipo_vehiculo.upper():
                    valor_base *= 0.9
                
                # Depreciación por año (curva realista)
                if antiguedad <= 5:
                    depreciacion = 0.12 * antiguedad  # 12% anual primeros 5 años
                elif antiguedad <= 10:
                    depreciacion = 0.6 + 0.08 * (antiguedad - 5)  # 8% anual siguientes 5 años
                else:
                    depreciacion = 1.0 + 0.04 * (antiguedad - 10)  # 4% anual después de 10 años
                
                valor_depreciado = valor_base * (1 - min(depreciacion, 0.85))  # Mínimo 15% del valor base
                
                # Ajustes por estado
                if vehicle_data.indicador_crv == 'S':
                    valor_depreciado *= 0.7  # 30% menos si está retenido
                
                if vehicle_data.estado_matricula == "VENCIDA":
                    valor_depreciado *= 0.85  # 15% menos si matrícula vencida
                
                vehicle_data.estimacion_valor = max(valor_depreciado, 800)  # Valor mínimo
            
            # Generar recomendaciones inteligentes
            recomendaciones = []
            
            # Análisis de retención
            if vehicle_data.indicador_crv == 'S':
                recomendaciones.append("🚨 VEHÍCULO RETENIDO - Gestionar liberación urgente")
                vehicle_data.puntuacion_general = max(vehicle_data.puntuacion_general - 40, 0)
            
            # Análisis de matrícula
            if vehicle_data.estado_matricula == "VENCIDA":
                recomendaciones.append("🔴 Matrícula vencida - Renovar INMEDIATAMENTE")
            elif vehicle_data.estado_matricula == "POR VENCER":
                dias = vehicle_data.dias_hasta_vencimiento
                recomendaciones.append(f"🟡 Matrícula vence en {dias} días - Planificar renovación")
            else:
                recomendaciones.append("✅ Matrícula vigente")
            
            # Análisis por antigüedad
            if vehicle_data.anio_fabricacion > 0:
                antiguedad = datetime.now().year - vehicle_data.anio_fabricacion
                if antiguedad > 25:
                    recomendaciones.append("🔧 Vehículo muy antiguo - Inspección mecánica recomendada")
                elif antiguedad > 15:
                    recomendaciones.append("🔧 Vehículo antiguo - Mantenimiento preventivo")
                elif antiguedad < 3:
                    recomendaciones.append("⭐ Vehículo casi nuevo - Excelente estado")
                elif antiguedad < 8:
                    recomendaciones.append("✨ Vehículo en buen rango de edad")
            
            # Análisis de valor
            if vehicle_data.estimacion_valor > 15000:
                recomendaciones.append("💎 Vehículo de alto valor comercial")
            elif vehicle_data.estimacion_valor > 8000:
                recomendaciones.append("💰 Buen valor comercial")
            elif vehicle_data.estimacion_valor > 3000:
                recomendaciones.append("💵 Valor comercial moderado")
            else:
                recomendaciones.append("📉 Valor comercial bajo")
            
            vehicle_data.recomendacion = " | ".join(recomendaciones)
            
            logger.info(f"✅ Análisis inteligente completado - Puntuación: {vehicle_data.puntuacion_general}")
            
        except Exception as e:
            logger.error(f"❌ Error en análisis de vehículo: {e}")
    
    def clear_cache(self):
        """Limpiar cache del consultor (sostenibilidad)"""
        PlateValidator._validation_cache.clear()
        CedulaValidator._validation_cache.clear()
        logger.info("✅ Cache del consultor limpiado")
    
    def test_apis(self) -> Dict:
        """Probar conectividad con APIs externas"""
        try:
            test_placa = "PBA123"  # Placa de prueba
            start_time = time.time()
            
            response = self.session.get(
                f"{API_CONFIG['base_url']}{API_CONFIG['endpoint']}",
                params={'empresa': API_CONFIG['default_empresa'], 'identidad': test_placa},
                timeout=10
            )
            
            response_time = time.time() - start_time
            
            return {
                'api_ant': {
                    'status': 'online' if response.status_code == 200 else 'offline',
                    'response_time': round(response_time, 3),
                    'status_code': response.status_code
                }
            }
            
        except Exception as e:
            return {
                'api_ant': {
                    'status': 'offline',
                    'error': str(e),
                    'response_time': None
                }
            }

# Instancia global del consultor optimizada
vehicle_consultant = VehicleConsultant()

# ==========================================
# FACTORY FUNCTION PRINCIPAL
# ==========================================

def create_app(config_name: str = 'production') -> Flask:
    """
    Factory function para crear aplicación Flask ECPlacas 2.0
    Compatible con el sistema principal ECPlacas.py
    
    Args:
        config_name: Configuración ('development', 'production', 'testing')
        
    Returns:
        Flask: Aplicación Flask configurada y optimizada
    """
    
    # Crear instancia de Flask
    app = Flask(__name__, 
                static_folder=None,
                template_folder=None)
    
    # ==========================================
    # CONFIGURACIÓN DE LA APLICACIÓN
    # ==========================================
    
    # Configuración básica optimizada
    app.config.update({
        'SECRET_KEY': os.getenv('SECRET_KEY', f'ecplacas_2024_secret_key_futuristic_{int(time.time())}'),
        'WTF_CSRF_ENABLED': False,
        'JSON_AS_ASCII': False,
        'JSONIFY_PRETTYPRINT_REGULAR': True,
        'SEND_FILE_MAX_AGE_DEFAULT': timedelta(hours=1),
        'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB
        
        # Configuración de performance
        'PREFERRED_URL_SCHEME': 'https' if config_name == 'production' else 'http',
        'SESSION_COOKIE_SECURE': config_name == 'production',
        'SESSION_COOKIE_HTTPONLY': True,
        'SESSION_COOKIE_SAMESITE': 'Lax',
    })
    
    # Configuración específica por entorno
    if config_name == 'development':
        app.config.update({
            'DEBUG': True,
            'TESTING': False,
            'ENV': 'development'
        })
    elif config_name == 'testing':
        app.config.update({
            'DEBUG': False,
            'TESTING': True,
            'ENV': 'testing'
        })
    else:  # production
        app.config.update({
            'DEBUG': False,
            'TESTING': False,
            'ENV': 'production'
        })
    
    # ==========================================
    # CONFIGURAR EXTENSIONES
    # ==========================================
    
    # CORS optimizado para desarrollo y producción
    cors_origins = ["http://localhost:*", "http://127.0.0.1:*"]
    if config_name == 'production':
        cors_origins.extend([
            "https://ecplacas.com",
            "https://www.ecplacas.com"
        ])
    
    CORS(app, resources={
        r"/api/*": {
            "origins": cors_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
            "supports_credentials": True
        }
    })
    
    # Proxy fix para deployment
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    
    # ==========================================
    # HOOKS DE APLICACIÓN
    # ==========================================
    
    @app.before_request
    def before_request():
        """Hook optimizado antes de cada request"""
        g.start_time = time.time()
        g.request_id = f"{int(time.time())}{hash(request.remote_addr or 'unknown') % 1000:03d}"
        
        # Rate limiting básico por IP
        if not hasattr(g, 'rate_limited'):
            # Implementar rate limiting simple aquí si es necesario
            pass
    
    @app.after_request
    def after_request(response):
        """Hook optimizado después de cada request"""
        
        # Headers de rendimiento y seguridad
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            response.headers['X-Response-Time'] = f'{duration:.3f}s'
        
        # Headers de seguridad
        response.headers.update({
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'X-Powered-By': 'ECPlacas-2.0-Futuristic-Engine',
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        })
        
        # Logging de requests importantes
        if hasattr(g, 'request_id') and (response.status_code >= 400 or app.config['DEBUG']):
            logger.info(f"Request {g.request_id}: {request.method} {request.path} -> {response.status_code} "
                       f"({response.headers.get('X-Response-Time', 'N/A')})")
        
        return response
    
    # ==========================================
    # ROUTES PRINCIPALES
    # ==========================================
    
    @app.route('/')
    def index():
        """Página principal - servir frontend"""
        try:
            index_path = FRONTEND_PATH / 'index.html'
            if index_path.exists():
                return send_from_directory(str(FRONTEND_PATH), 'index.html')
            else:
                return create_emergency_frontend(), 200
        except Exception as e:
            logger.error(f"❌ Error sirviendo index: {e}")
            return create_emergency_frontend(), 200
    
    @app.route('/admin')
    def admin():
        """Dashboard administrativo"""
        try:
            admin_path = FRONTEND_PATH / 'admin.html'
            if admin_path.exists():
                return send_from_directory(str(FRONTEND_PATH), 'admin.html')
            else:
                return create_emergency_admin(), 200
        except Exception as e:
            logger.error(f"❌ Error sirviendo admin: {e}")
            return create_emergency_admin(), 200
    
    @app.route('/static/<path:filename>')
    def static_files(filename):
        """Servir archivos estáticos optimizado"""
        try:
            # Intentar servir desde frontend/css primero
            if filename.endswith('.css'):
                css_path = FRONTEND_PATH / 'css' / filename
                if css_path.exists():
                    return send_from_directory(str(FRONTEND_PATH / 'css'), filename)
            
            # Fallback a public si existe
            public_path = PROJECT_ROOT / 'public'
            if public_path.exists():
                return send_from_directory(str(public_path), filename)
            
            return "Archivo no encontrado", 404
            
        except Exception as e:
            logger.error(f"❌ Error sirviendo estático {filename}: {e}")
            return "Error interno", 500
    
    # ==========================================
    # API ENDPOINTS
    # ==========================================
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check optimizado del sistema"""
        try:
            stats = vehicle_consultant.db.get_system_stats()
            
            return jsonify({
                'success': True,
                'status': 'healthy',
                'service': 'ECPlacas 2.0',
                'version': '2.0.0',
                'author': 'Erick Costa',
                'project': 'Construcción de Software',
                'theme': 'Futurista - Azul Neon',
                'timestamp': datetime.now().isoformat(),
                'environment': config_name,
                'estadisticas': stats,
                'features': {
                    'consultas_vehiculares': True,
                    'validacion_cedulas': True,
                    'normalizacion_placas': True,
                    'analisis_inteligente': True,
                    'base_datos_optimizada': True,
                    'cache_inteligente': True,
                    'logs_rotativos': True
                }
            })
            
        except Exception as e:
            logger.error(f"❌ Error en health check: {e}")
            return jsonify({
                'success': False,
                'status': 'unhealthy',
                'error': 'Error interno del sistema',
                'timestamp': datetime.now().isoformat()
            }), 500
    
    @app.route('/api/consultar-vehiculo', methods=['POST'])
    def consultar_vehiculo():
        """Endpoint optimizado para consultar vehículo"""
        try:
            if not request.is_json:
                return jsonify({
                    'success': False, 
                    'error': 'Content-Type debe ser application/json'
                }), 400
            
            data = request.get_json()
            placa = data.get('placa', '').strip()
            usuario_data = data.get('usuario', {})
            
            # Validaciones de entrada
            if not placa:
                return jsonify({
                    'success': False, 
                    'error': 'Placa es requerida'
                }), 400
            
            if not PlateValidator.validate_plate_format(placa):
                return jsonify({
                    'success': False,
                    'error': 'Formato de placa inválido',
                    'formato_esperado': 'ABC1234 o ABC123',
                    'placa_recibida': placa
                }), 400
            
            # Crear datos de usuario
            user_data = UserData(
                nombre=usuario_data.get('nombre', ''),
                cedula=usuario_data.get('cedula', ''),
                telefono=usuario_data.get('telefono', ''),
                correo=usuario_data.get('correo', ''),
                country_code=usuario_data.get('country_code', '+593'),
                acepta_terminos=usuario_data.get('acepta_terminos', False),
                ip_address=request.remote_addr or 'unknown',
                user_agent=request.headers.get('User-Agent', '')
            )
            
            # Validar cédula
            if not CedulaValidator.validate_ecuadorian_id(user_data.cedula):
                return jsonify({
                    'success': False,
                    'error': 'Cédula ecuatoriana inválida',
                    'cedula_recibida': user_data.cedula
                }), 400
            
            # Generar session ID único
            session_id = f"ecplacas_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
            
            logger.info(f"🚀 Nueva consulta ECPlacas 2.0 - Placa: {placa}, Session: {session_id}, Usuario: {user_data.nombre}")
            
            # Función para ejecutar consulta en thread
            def run_consultation():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # Marcar como iniciando
                    vehicle_consultant.active_consultations[session_id] = {
                        'status': 'iniciando',
                        'progress': 10,
                        'message': '🚀 Iniciando consulta ECPlacas 2.0...',
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # Ejecutar consulta
                    vehicle_data = loop.run_until_complete(
                        vehicle_consultant.consultar_vehiculo_completo(placa, user_data, session_id)
                    )
                    
                    # Marcar como completado
                    vehicle_consultant.active_consultations[session_id] = {
                        'status': 'completado',
                        'progress': 100,
                        'message': '✅ Consulta completada exitosamente',
                        'result': vehicle_data.to_dict(),
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    logger.info(f"✅ Consulta completada: {session_id} - Éxito: {vehicle_data.consulta_exitosa}")
                    
                except Exception as e:
                    logger.error(f"❌ Error en thread de consulta {session_id}: {e}")
                    vehicle_consultant.active_consultations[session_id] = {
                        'status': 'error',
                        'progress': 0,
                        'message': f'Error en consulta: {str(e)}',
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    }
                finally:
                    loop.close()
            
            # Ejecutar en thread separado para no bloquear la respuesta
            thread = threading.Thread(target=run_consultation, daemon=True)
            thread.start()
            
            return jsonify({
                'success': True,
                'message': 'Consulta ECPlacas 2.0 iniciada exitosamente',
                'session_id': session_id,
                'placa': placa,
                'placa_normalizada': PlateValidator.normalize_plate(placa)[1],
                'status': 'procesando',
                'tiempo_estimado_segundos': 15,
                'urls': {
                    'estado': f'/api/estado-consulta/{session_id}',
                    'resultado': f'/api/resultado/{session_id}'
                }
            }), 202
            
        except Exception as e:
            logger.error(f"❌ Error en endpoint consultar-vehiculo: {e}")
            return jsonify({
                'success': False, 
                'error': 'Error interno del servidor',
                'timestamp': datetime.now().isoformat()
            }), 500
    
    @app.route('/api/estado-consulta/<session_id>', methods=['GET'])
    def estado_consulta(session_id):
        """Obtener estado de consulta en tiempo real"""
        try:
            if session_id not in vehicle_consultant.active_consultations:
                return jsonify({
                    'success': False, 
                    'error': 'Session ID no encontrada'
                }), 404
            
            consultation = vehicle_consultant.active_consultations[session_id]
            
            return jsonify({
                'success': True,
                'session_id': session_id,
                'status': consultation.get('status'),
                'progress': consultation.get('progress', 0),
                'message': consultation.get('message', ''),
                'timestamp': consultation.get('timestamp'),
                'error': consultation.get('error')
            })
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estado {session_id}: {e}")
            return jsonify({
                'success': False, 
                'error': 'Error interno del servidor'
            }), 500
    
    @app.route('/api/resultado/<session_id>', methods=['GET'])
    def obtener_resultado(session_id):
        """Obtener resultado completo de consulta"""
        try:
            if session_id not in vehicle_consultant.active_consultations:
                return jsonify({
                    'success': False, 
                    'error': 'Session ID no encontrada'
                }), 404
            
            consultation = vehicle_consultant.active_consultations[session_id]
            
            if consultation.get('status') != 'completado':
                return jsonify({
                    'success': False,
                    'error': 'Consulta no completada',
                    'status': consultation.get('status'),
                    'progress': consultation.get('progress', 0),
                    'message': consultation.get('message', '')
                }), 400
            
            # Limpiar sesión después de obtener resultado (sostenibilidad)
            result = consultation.get('result')
            
            # Programar limpieza de sesión en 5 minutos
            def cleanup_session():
                time.sleep(300)  # 5 minutos
                if session_id in vehicle_consultant.active_consultations:
                    del vehicle_consultant.active_consultations[session_id]
            
            cleanup_thread = threading.Thread(target=cleanup_session, daemon=True)
            cleanup_thread.start()
            
            return jsonify({
                'success': True,
                'session_id': session_id,
                'data': result,
                'timestamp': consultation.get('timestamp'),
                'version': '2.0.0',
                'system': 'ECPlacas 2.0 - Futuristic Engine'
            })
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo resultado {session_id}: {e}")
            return jsonify({
                'success': False, 
                'error': 'Error interno del servidor'
            }), 500
    
    @app.route('/api/estadisticas', methods=['GET'])
    def obtener_estadisticas():
        """Obtener estadísticas detalladas del sistema"""
        try:
            stats = vehicle_consultant.db.get_system_stats()
            
            # Estadísticas adicionales del sistema
            system_stats = {
                'consultas_activas': len(vehicle_consultant.active_consultations),
                'cache_size': {
                    'placas': len(PlateValidator._validation_cache),
                    'cedulas': len(CedulaValidator._validation_cache)
                },
                'uptime': time.time() - app.start_time if hasattr(app, 'start_time') else 0
            }
            
            return jsonify({
                'success': True,
                'estadisticas': stats,
                'sistema': system_stats,
                'timestamp': datetime.now().isoformat(),
                'version': '2.0.0'
            })
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return jsonify({
                'success': False, 
                'error': 'Error obteniendo estadísticas del sistema'
            }), 500
    
    # ==========================================
    # ADMIN ENDPOINTS
    # ==========================================
    
    @app.route('/api/admin/system-status', methods=['GET'])
    def admin_system_status():
        """Estado detallado para administradores"""
        try:
            import psutil
            
            system_info = {
                'database': {
                    'path': vehicle_consultant.db.db_path,
                    'size_mb': os.path.getsize(vehicle_consultant.db.db_path) / (1024*1024) if os.path.exists(vehicle_consultant.db.db_path) else 0
                },
                'performance': {
                    'cpu_percent': psutil.cpu_percent(interval=1),
                    'memory_percent': psutil.virtual_memory().percent,
                    'active_consultations': len(vehicle_consultant.active_consultations)
                },
                'cache': {
                    'placas_cached': len(PlateValidator._validation_cache),
                    'cedulas_cached': len(CedulaValidator._validation_cache)
                }
            }
            
            return jsonify({
                'success': True,
                'system_info': system_info,
                'estadisticas': vehicle_consultant.db.get_system_stats()
            })
            
        except Exception as e:
            logger.error(f"❌ Error en admin status: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/admin/clear-cache', methods=['POST'])
    def admin_clear_cache():
        """Limpiar cache del sistema"""
        try:
            vehicle_consultant.clear_cache()
            return jsonify({
                'success': True,
                'message': 'Cache limpiado exitosamente'
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/admin/backup-database', methods=['POST'])
    def admin_backup_database():
        """Crear backup de base de datos"""
        try:
            backup_path = vehicle_consultant.db.backup_database()
            if backup_path:
                return jsonify({
                    'success': True,
                    'message': 'Backup creado exitosamente',
                    'backup_path': backup_path
                })
            else:
                return jsonify({'success': False, 'error': 'Error creando backup'}), 500
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # ==========================================
    # ERROR HANDLERS
    # ==========================================
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Manejo de errores 404 personalizado"""
        return jsonify({
            'success': False,
            'error': 'Endpoint no encontrado',
            'path': request.path,
            'method': request.method,
            'service': 'ECPlacas 2.0',
            'timestamp': datetime.now().isoformat()
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Manejo de errores 500 personalizado"""
        logger.error(f"❌ Error interno del servidor: {error}")
        
        return jsonify({
            'success': False,
            'error': 'Error interno del servidor',
            'service': 'ECPlacas 2.0',
            'timestamp': datetime.now().isoformat()
        }), 500
    
    @app.errorhandler(429)
    def rate_limit_error(error):
        """Manejo de rate limiting"""
        return jsonify({
            'success': False,
            'error': 'Demasiadas solicitudes',
            'message': 'Por favor espere antes de realizar otra consulta',
            'service': 'ECPlacas 2.0'
        }), 429
    
    # ==========================================
    # INICIALIZACIÓN FINAL
    # ==========================================
    
    # Marcar tiempo de inicio para uptime
    app.start_time = time.time()
    
    # Log de inicialización
    logger.info("🚀 ECPlacas 2.0 - Aplicación Flask inicializada exitosamente")
    logger.info(f"📁 Backend: {BACKEND_ROOT}")
    logger.info(f"🎨 Frontend: {FRONTEND_PATH}")
    logger.info(f"🗄️ Database: {DATABASE_PATH}")
    logger.info(f"⚙️ Configuración: {config_name}")
    logger.info(f"🐍 Python: {sys.version.split()[0]}")
    
    return app

# ==========================================
# FUNCIÓN DE COMPATIBILIDAD LEGACY
# ==========================================

def create_ecplacas_api():
    """Función de compatibilidad con código legacy"""
    return create_app('production')

# ==========================================
# FUNCIONES DE EMERGENCIA
# ==========================================

def create_emergency_frontend():
    """Frontend de emergencia si no se encuentra index.html"""
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ECPlacas 2.0 - Sistema Activo</title>
        <style>
            body { 
                font-family: 'Arial', sans-serif; 
                background: linear-gradient(135deg, #000 0%, #001133 100%);
                color: #00ffff; 
                text-align: center; 
                padding: 50px; 
                margin: 0;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                justify-content: center;
            }
            .container {
                background: rgba(0, 51, 102, 0.3);
                border: 2px solid #00ffff;
                border-radius: 20px;
                padding: 2rem;
                backdrop-filter: blur(10px);
                max-width: 600px;
                margin: 0 auto;
            }
            h1 { 
                font-size: 3rem; 
                text-shadow: 0 0 20px #00ffff;
                margin-bottom: 1rem;
            }
            .status { color: #00ff66; font-size: 1.5rem; margin: 1rem 0; }
            .info { margin: 1rem 0; font-size: 1.1rem; }
            a { color: #00ffff; text-decoration: none; font-weight: bold; }
            a:hover { text-shadow: 0 0 10px #00ffff; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 ECPlacas 2.0</h1>
            <div class="status">✅ Sistema Funcionando Correctamente</div>
            <div class="info">
                <p><strong>Estado:</strong> Backend operativo</p>
                <p><strong>Versión:</strong> 2.0.0</p>
                <p><strong>Desarrollado por:</strong> Erick Costa</p>
                <p><strong>Tema:</strong> Futurista - Azul Neon</p>
            </div>
            <hr style="border-color: #00ffff; margin: 2rem 0;">
            <div class="info">
                <p>🔗 <a href="/api/health">Health Check API</a></p>
                <p>🎛️ <a href="/admin">Panel de Administración</a></p>
                <p>⚠️ Fronted completo en configuración</p>
            </div>
        </div>
    </body>
    </html>
    """

def create_emergency_admin():
    """Admin de emergencia si no se encuentra admin.html"""
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>ECPlacas 2.0 - Admin Básico</title>
        <style>
            body { font-family: Arial; background: #000; color: #00ffff; padding: 2rem; }
            .container { max-width: 800px; margin: 0 auto; }
            h1 { text-align: center; text-shadow: 0 0 20px #00ffff; }
            .section { background: rgba(0,51,102,0.3); padding: 1rem; margin: 1rem 0; border-radius: 10px; }
            button { background: linear-gradient(135deg, #0066ff, #00ffff); border: none; padding: 0.5rem 1rem; 
                     border-radius: 5px; color: #000; font-weight: bold; cursor: pointer; }
            #status { margin: 1rem 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛠️ ECPlacas 2.0 - Panel Básico</h1>
            <div class="section">
                <h3>Estado del Sistema</h3>
                <div id="status">Cargando...</div>
                <button onclick="checkHealth()">Verificar Estado</button>
            </div>
            <div class="section">
                <h3>Acciones Rápidas</h3>
                <button onclick="clearCache()">Limpiar Cache</button>
                <button onclick="viewStats()">Ver Estadísticas</button>
                <a href="/api/health" style="color: #00ffff;">API Health</a>
            </div>
        </div>
        
        <script>
            async function checkHealth() {
                try {
                    const response = await fetch('/api/health');
                    const data = await response.json();
                    document.getElementById('status').innerHTML = 
                        data.success ? '✅ Sistema Saludable' : '❌ Sistema con Problemas';
                } catch (e) {
                    document.getElementById('status').innerHTML = '❌ Error de Conexión';
                }
            }
            
            async function clearCache() {
                try {
                    const response = await fetch('/api/admin/clear-cache', {method: 'POST'});
                    const data = await response.json();
                    alert(data.success ? 'Cache limpiado' : 'Error limpiando cache');
                } catch (e) {
                    alert('Error de conexión');
                }
            }
            
            async function viewStats() {
                try {
                    const response = await fetch('/api/estadisticas');
                    const data = await response.json();
                    alert(JSON.stringify(data.estadisticas, null, 2));
                } catch (e) {
                    alert('Error obteniendo estadísticas');
                }
            }
            
            checkHealth();
        </script>
    </body>
    </html>
    """

# ==========================================
# APLICACIÓN PRINCIPAL PARA USO DIRECTO
# ==========================================

def main():
    """Función principal para ejecución directa del archivo"""
    
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║    ███████╗ ██████╗██████╗ ██╗      █████╗  ██████╗ █████╗ ███████╗        ║
║    ██╔════╝██╔════╝██╔══██╗██║     ██╔══██╗██╔════╝██╔══██╗██╔════╝        ║
║    █████╗  ██║     ██████╔╝██║     ███████║██║     ███████║███████╗        ║
║    ██╔══╝  ██║     ██╔═══╝ ██║     ██╔══██║██║     ██╔══██║╚════██║        ║
║    ███████╗╚██████╗██║     ███████╗██║  ██║╚██████╗██║  ██║███████║        ║
║    ╚══════╝ ╚═════╝╚═╝     ╚══════╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝        ║
║                                                                              ║
║                                  2.0                                        ║
║                    Sistema de Consulta Vehicular                            ║
║                                                                              ║
║                        Desarrollado por: Erick Costa                        ║
║                     Proyecto: Construcción de Software                      ║
║                       Temática: Futurista - Azul Neon                       ║
║                                                                              ║
║            🚀 OPTIMIZADO PARA RENDIMIENTO Y ESCALABILIDAD 🚀               ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    logger.info("🚀 Iniciando ECPlacas 2.0 - Sistema Completo de Consulta Vehicular")
    logger.info("✨ Características Avanzadas:")
    logger.info("   • 🔍 Consultas vehiculares ANT completas y optimizadas")
    logger.info("   • 🗄️ Base de datos SQLite con índices y pool de conexiones")
    logger.info("   • 🎨 Interfaz futurista con paleta azul neon")
    logger.info("   • ✅ Validación avanzada de placas y cédulas con cache")
    logger.info("   • 📊 Dashboard de administración en tiempo real")
    logger.info("   • 🧠 Análisis inteligente de vehículos con ML básico")
    logger.info("   • 🔄 Logs rotativos para sostenibilidad")
    logger.info("   • ⚡ Rate limiting y optimizaciones de rendimiento")
    logger.info("   • 🛡️ Headers de seguridad y CORS configurado")
    logger.info("   • 🧩 Arquitectura modular y escalable")
    
    # Crear aplicación
    app = create_app('development' if os.getenv('FLASK_ENV') == 'development' else 'production')
    
    # Configuración del servidor
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'production') == 'development'
    
    logger.info(f"🌐 Servidor iniciando en http://{host}:{port}")
    logger.info(f"🎯 Modo: {'Desarrollo' if debug else 'Producción'}")
    logger.info(f"📊 Debug: {'Habilitado' if debug else 'Deshabilitado'}")
    logger.info(f"🔗 URLs principales:")
    logger.info(f"   • Frontend: http://localhost:{port}")
    logger.info(f"   • Admin: http://localhost:{port}/admin")
    logger.info(f"   • API Health: http://localhost:{port}/api/health")
    logger.info(f"   • API Consultas: http://localhost:{port}/api/consultar-vehiculo")
    
    print("\n🎯 ECPlacas 2.0 listo para recibir conexiones...")
    print("ℹ️ Presione Ctrl+C para detener el servidor")
    print("-" * 80)
    
    try:
        # Iniciar servidor Flask optimizado
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True,
            use_reloader=False,  # Evitar doble inicio
            processes=1  # Single process para desarrollo
        )
        
    except KeyboardInterrupt:
        logger.info("\n👋 ECPlacas 2.0 detenido por el usuario")
        print("\n🛑 Servidor detenido correctamente")
    except Exception as e:
        logger.error(f"❌ Error crítico iniciando servidor: {e}")
        print(f"❌ Error: {e}")
        return 1
    
    return 0

# ==========================================
# INSTANCIA GLOBAL PARA COMPATIBILIDAD
# ==========================================

# Crear instancia global para compatibilidad con imports
app = create_app()

if __name__ == '__main__':
    sys.exit(main())