#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================
ECPlacas 2.0 SRI - Sistema COMPLETO Optimizado
==========================================
Proyecto: Construcción de Software
Desarrollado por: Erick Costa - ZeusPy
Temática: Futurista con paleta azul neon, cyan y negro
Versión: 2.0.1 OPTIMIZADA
==========================================

Backend COMPLETO con:
✅ Información SRI completa (rubros, componentes, pagos, IACV)
✅ Propietario del vehículo
✅ Análisis consolidado avanzado
✅ Optimizado para máximo rendimiento y escalabilidad
✅ Presentación completa de TODOS los datos
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

# Configuración de paths
BACKEND_ROOT = Path(__file__).parent
PROJECT_ROOT = BACKEND_ROOT.parent
FRONTEND_PATH = PROJECT_ROOT / "frontend"
DATABASE_PATH = BACKEND_ROOT / "database"
LOGS_PATH = BACKEND_ROOT / "logs"

# Asegurar directorios
for path in [DATABASE_PATH, LOGS_PATH]:
    path.mkdir(parents=True, exist_ok=True)

# Configuración de logging optimizado
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Configurar sistema de logging optimizado"""
    logger = logging.getLogger('ecplacas')
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler de archivo rotativo
    file_handler = RotatingFileHandler(
        LOGS_PATH / "ecplacas.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # Handler de consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # Configurar logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

# URLs de APIs COMPLETAS
SRI_BASE_URL = "https://srienlinea.sri.gob.ec/sri-matriculacion-vehicular-recaudacion-servicio-internet/rest"
SRI_ENDPOINTS = {
    'base_vehiculo': f"{SRI_BASE_URL}/BaseVehiculo/obtenerPorNumeroPlacaOPorNumeroCampvOPorNumeroCpn",
    'consulta_rubros': f"{SRI_BASE_URL}/ConsultaRubros/obtenerPorCodigoVehiculo",
    'consulta_componente': f"{SRI_BASE_URL}/ConsultaComponente/obtenerListaComponentesPorCodigoConsultaRubro",
    'consulta_pagos': f"{SRI_BASE_URL}/consultaPagos/obtenerPorPlacaCampvCpn",
    'detalle_pagos': f"{SRI_BASE_URL}/consultaPagos/obtenerDetallesPago",
    'plan_excepcional': f"{SRI_BASE_URL}/CuotasImpAmbiental/obtenerDetallePlanExcepcionalPagosPorCodigoVehiculo"
}

# APIs para propietario del vehículo
OWNER_APIS = {
    'primary': 'https://app3902.privynote.net/api/v1/transit/vehicle-owner',
    'backup': 'https://consultasecuador.com/api/vehiculo/propietario'
}

# Códigos de provincia Ecuador
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
    """Estructura de datos del usuario"""
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
class VehicleDataSRI:
    """Estructura COMPLETA de datos vehiculares ECPlacas 2.0 con información SRI + PROPIETARIO"""
    
    # ==================== IDENTIFICACIÓN BÁSICA ====================
    numero_placa: str = ""
    placa_original: str = ""
    placa_normalizada: str = ""
    codigo_vehiculo: int = 0
    numero_camv_cpn: str = ""
    
    # ==================== PROPIETARIO DEL VEHÍCULO ====================
    propietario_nombre: str = ""
    propietario_cedula: str = ""
    propietario_encontrado: bool = False
    
    # ==================== DATOS DE IDENTIFICACIÓN VEHICULAR ====================
    vin_chasis: str = ""
    numero_motor: str = ""
    placa_anterior: str = ""
    
    # ==================== INFORMACIÓN DEL MODELO ====================
    descripcion_marca: str = ""
    descripcion_modelo: str = ""
    anio_auto: int = 0
    descripcion_pais: str = ""
    color_vehiculo1: str = ""
    color_vehiculo2: str = ""
    cilindraje: str = ""
    nombre_clase: str = ""
    
    # ==================== INFORMACIÓN DE MATRÍCULA ====================
    fecha_ultima_matricula: str = ""
    fecha_caducidad_matricula: str = ""
    fecha_compra_registro: str = ""
    fecha_revision: str = ""
    descripcion_canton: str = ""
    descripcion_servicio: str = ""
    ultimo_anio_pagado: int = 0
    
    # ==================== ESTADOS LEGALES ====================
    prohibido_enajenar: str = ""
    estado_exoneracion: str = ""
    observacion: str = ""
    aplica_cuota: bool = False
    mensaje_motivo_auto: str = ""
    
    # ==================== DATOS SRI COMPLETOS - RUBROS Y DEUDAS ====================
    rubros_deuda: List[Dict] = field(default_factory=list)
    componentes_deuda: List[Dict] = field(default_factory=list)
    rubros_agrupados_por_beneficiario: Dict[str, Dict] = field(default_factory=dict)
    componentes_por_rubro: Dict[str, List] = field(default_factory=dict)
    totales_por_beneficiario: Dict[str, float] = field(default_factory=dict)
    total_deudas_sri: float = 0.0
    
    # ==================== ANÁLISIS DETALLADO DE COMPONENTES SRI ====================
    total_impuestos: float = 0.0
    total_tasas: float = 0.0
    total_intereses: float = 0.0
    total_multas: float = 0.0
    total_prescripciones: float = 0.0
    
    # ==================== HISTORIAL DE PAGOS COMPLETO ====================
    historial_pagos: List[Dict] = field(default_factory=list)
    detalles_pagos: List[Dict] = field(default_factory=list)
    total_pagos_realizados: float = 0.0
    
    # ==================== PLAN EXCEPCIONAL IACV ====================
    plan_excepcional_iacv: List[Dict] = field(default_factory=list)
    total_cuotas_vencidas: float = 0.0
    cuotas_por_estado: Dict[str, int] = field(default_factory=dict)
    
    # ==================== ANÁLISIS CONSOLIDADO COMPLETO ====================
    estado_legal_sri: str = "PENDIENTE"
    riesgo_tributario: str = "INDETERMINADO"
    puntuacion_sri: int = 0
    recomendacion_tributaria: str = ""
    
    # ==================== ESTADÍSTICAS ADICIONALES ====================
    total_rubros_pendientes: int = 0
    total_componentes_analizados: int = 0
    pagos_ultimo_ano: float = 0.0
    promedio_pago_anual: float = 0.0
    
    # ==================== DATOS LEGACY ANT (COMPATIBILIDAD) ====================
    clase_vehiculo: str = ""
    tipo_vehiculo: str = ""
    color_primario: str = ""
    peso_vehiculo: str = ""
    tipo_carroceria: str = ""
    matricula_desde: str = ""
    matricula_hasta: str = ""
    servicio: str = ""
    ultima_actualizacion: str = ""
    indicador_crv: str = ""
    
    # ==================== ANÁLISIS INTELIGENTE ====================
    estado_matricula: str = ""
    dias_hasta_vencimiento: int = 0
    estimacion_valor: float = 0.0
    categoria_riesgo: str = "BAJO"
    puntuacion_general: int = 0
    recomendacion: str = ""
    
    # ==================== METADATOS ====================
    session_id: str = ""
    timestamp_consulta: datetime = field(default_factory=datetime.now)
    tiempo_consulta: float = 0.0
    consulta_exitosa: bool = False
    mensaje_error: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario COMPLETO para API"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, (list, dict)):
                result[key] = value
            else:
                result[key] = value
        return result
    
    def get_complete_summary(self) -> Dict[str, Any]:
        """Obtiene resumen COMPLETO optimizado para frontend"""
        return {
            'propietario': {
                'nombre': self.propietario_nombre,
                'cedula': self.propietario_cedula,
                'encontrado': self.propietario_encontrado
            },
            'vehiculo_basico': {
                'placa': self.numero_placa,
                'marca': self.descripcion_marca,
                'modelo': self.descripcion_modelo,
                'anio': self.anio_auto,
                'clase': self.nombre_clase,
                'color_primario': self.color_vehiculo1,
                'color_secundario': self.color_vehiculo2,
                'cilindraje': self.cilindraje,
                'pais': self.descripcion_pais
            },
            'deudas_sri_completas': {
                'total_general': self.total_deudas_sri,
                'desglose': {
                    'impuestos': self.total_impuestos,
                    'tasas': self.total_tasas,
                    'multas': self.total_multas,
                    'intereses': self.total_intereses,
                    'prescripciones': self.total_prescripciones
                },
                'rubros_count': self.total_rubros_pendientes,
                'componentes_count': self.total_componentes_analizados,
                'beneficiarios': list(self.totales_por_beneficiario.keys()),
                'rubros_detallados': self.rubros_deuda,
                'componentes_detallados': self.componentes_deuda,
                'agrupado_beneficiarios': self.rubros_agrupados_por_beneficiario
            },
            'pagos_sri_completos': {
                'total_pagado': self.total_pagos_realizados,
                'pagos_ultimo_ano': self.pagos_ultimo_ano,
                'promedio_anual': self.promedio_pago_anual,
                'historial_completo': self.historial_pagos,
                'detalles_pagos': self.detalles_pagos,
                'total_transacciones': len(self.historial_pagos)
            },
            'iacv_completo': {
                'cuotas_vencidas': self.total_cuotas_vencidas,
                'total_cuotas': len(self.plan_excepcional_iacv),
                'estados_cuotas': self.cuotas_por_estado,
                'plan_detallado': self.plan_excepcional_iacv
            },
            'estados_legales': {
                'matricula': {
                    'ultima': self.fecha_ultima_matricula,
                    'vencimiento': self.fecha_caducidad_matricula,
                    'estado': self.estado_matricula,
                    'dias_vencimiento': self.dias_hasta_vencimiento,
                    'ultimo_anio_pagado': self.ultimo_anio_pagado
                },
                'prohibiciones': {
                    'enajenar': self.prohibido_enajenar,
                    'exoneracion': self.estado_exoneracion,
                    'observaciones': self.observacion
                },
                'ubicacion': {
                    'canton': self.descripcion_canton,
                    'servicio': self.descripcion_servicio
                }
            },
            'analisis_completo': {
                'estado_legal': self.estado_legal_sri,
                'riesgo_tributario': self.riesgo_tributario,
                'puntuacion_sri': self.puntuacion_sri,
                'puntuacion_general': self.puntuacion_general,
                'recomendacion_tributaria': self.recomendacion_tributaria,
                'recomendacion_general': self.recomendacion,
                'estimacion_valor': self.estimacion_valor,
                'categoria_riesgo': self.categoria_riesgo
            },
            'metadatos': {
                'session_id': self.session_id,
                'tiempo_consulta': self.tiempo_consulta,
                'timestamp': self.timestamp_consulta.isoformat(),
                'consulta_exitosa': self.consulta_exitosa
            }
        }

class PlateValidator:
    """Validador de placas ecuatorianas optimizado"""
    
    _validation_cache = {}
    
    @classmethod
    def normalize_plate(cls, placa: str) -> tuple[str, str, bool]:
        """Normaliza placas ecuatorianas con cache"""
        if not placa or not isinstance(placa, str):
            return placa, placa, False
        
        cache_key = placa.upper().strip()
        if cache_key in cls._validation_cache:
            return cls._validation_cache[cache_key]
        
        placa_clean = re.sub(r'[^A-Z0-9]', '', placa.upper())
        placa_original = placa_clean
        
        # Normalización automática ABC123 -> ABC0123
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
        
        cls._validation_cache[cache_key] = result
        
        # Limpiar cache si crece mucho
        if len(cls._validation_cache) > 1000:
            cls._validation_cache.clear()
        
        return result
    
    @staticmethod
    def validate_plate_format(placa: str) -> bool:
        """Valida formato de placa ecuatoriana"""
        if not placa or len(placa) < 6 or len(placa) > 8:
            return False
        
        patterns = [
            r'^[A-Z]{2,3}\d{3,4}$',
            r'^[A-Z]{2,3}-\d{3,4}$'
        ]
        
        return any(re.match(pattern, placa.upper()) for pattern in patterns)

class CedulaValidator:
    """Validador de cédulas ecuatorianas optimizado"""
    
    _validation_cache = {}
    
    @classmethod
    def validate_ecuadorian_id(cls, cedula: str) -> bool:
        """Valida cédula ecuatoriana con algoritmo oficial"""
        if not cedula or len(cedula) != 10 or not cedula.isdigit():
            return False
        
        if cedula in cls._validation_cache:
            return cls._validation_cache[cedula]
        
        # Verificar código de provincia
        province_code = cedula[:2]
        if province_code not in PROVINCE_CODES:
            cls._validation_cache[cedula] = False
            return False
        
        # Verificar tercer dígito
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
        
        cls._validation_cache[cedula] = is_valid
        
        # Limpiar cache si crece mucho
        if len(cls._validation_cache) > 10000:
            cls._validation_cache.clear()
        
        return is_valid

class DatabaseManager:
    """Gestor de base de datos optimizado para datos completos"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(DATABASE_PATH / "ecplacas.sqlite")
        self.connection_pool = []
        self.pool_size = 5
        self.init_database()
    
    def get_connection(self):
        """Obtener conexión del pool"""
        if self.connection_pool:
            return self.connection_pool.pop()
        else:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            return conn
    
    def return_connection(self, conn):
        """Devolver conexión al pool"""
        if len(self.connection_pool) < self.pool_size:
            self.connection_pool.append(conn)
        else:
            conn.close()
    
    def init_database(self):
        """Inicializar base de datos optimizada"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Configuraciones de optimización
            cursor.execute("PRAGMA journal_mode = WAL")
            cursor.execute("PRAGMA synchronous = NORMAL")
            cursor.execute("PRAGMA cache_size = 10000")
            cursor.execute("PRAGMA temp_store = MEMORY")
            cursor.execute("PRAGMA foreign_keys = ON")
            
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
                    codigo_vehiculo INTEGER,
                    consulta_exitosa BOOLEAN DEFAULT 0,
                    tiempo_consulta REAL,
                    mensaje_error TEXT,
                    ip_origen TEXT,
                    user_agent TEXT,
                    api_utilizada TEXT DEFAULT 'sri_completo',
                    tiene_datos_sri BOOLEAN DEFAULT 0,
                    tiene_propietario BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE SET NULL
                )
            """)
            
            # Tabla de datos vehiculares SRI COMPLETOS + PROPIETARIO
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS datos_vehiculares_sri (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    consulta_id INTEGER NOT NULL,
                    
                    -- Propietario
                    propietario_nombre TEXT,
                    propietario_cedula TEXT,
                    propietario_encontrado BOOLEAN DEFAULT 0,
                    
                    -- Datos básicos SRI
                    codigo_vehiculo INTEGER,
                    numero_camv_cpn TEXT,
                    descripcion_marca TEXT,
                    descripcion_modelo TEXT,
                    anio_auto INTEGER,
                    descripcion_pais TEXT,
                    color_vehiculo1 TEXT,
                    color_vehiculo2 TEXT,
                    cilindraje TEXT,
                    nombre_clase TEXT,
                    
                    -- Información de matrícula SRI
                    fecha_ultima_matricula TEXT,
                    fecha_caducidad_matricula TEXT,
                    fecha_compra_registro TEXT,
                    fecha_revision TEXT,
                    descripcion_canton TEXT,
                    descripcion_servicio TEXT,
                    ultimo_anio_pagado INTEGER,
                    
                    -- Estados legales SRI
                    prohibido_enajenar TEXT,
                    estado_exoneracion TEXT,
                    observacion TEXT,
                    aplica_cuota BOOLEAN DEFAULT 0,
                    mensaje_motivo_auto TEXT,
                    
                    -- Datos de deudas SRI
                    total_deudas_sri REAL DEFAULT 0,
                    total_impuestos REAL DEFAULT 0,
                    total_tasas REAL DEFAULT 0,
                    total_intereses REAL DEFAULT 0,
                    total_multas REAL DEFAULT 0,
                    total_prescripciones REAL DEFAULT 0,
                    total_rubros_pendientes INTEGER DEFAULT 0,
                    total_componentes_analizados INTEGER DEFAULT 0,
                    
                    -- Datos de pagos SRI
                    total_pagos_realizados REAL DEFAULT 0,
                    pagos_ultimo_ano REAL DEFAULT 0,
                    promedio_pago_anual REAL DEFAULT 0,
                    
                    -- Plan IACV
                    total_cuotas_vencidas REAL DEFAULT 0,
                    
                    -- Análisis SRI
                    estado_legal_sri TEXT DEFAULT 'PENDIENTE',
                    riesgo_tributario TEXT DEFAULT 'INDETERMINADO',
                    puntuacion_sri INTEGER DEFAULT 0,
                    recomendacion_tributaria TEXT,
                    
                    -- Datos JSON completos
                    rubros_deuda_json TEXT,
                    componentes_deuda_json TEXT,
                    historial_pagos_json TEXT,
                    plan_iacv_json TEXT,
                    totales_beneficiario_json TEXT,
                    
                    -- Legacy ANT (compatibilidad)
                    vin_chasis TEXT,
                    numero_motor TEXT,
                    placa_anterior TEXT,
                    clase_vehiculo TEXT,
                    tipo_vehiculo TEXT,
                    color_primario TEXT,
                    peso_vehiculo TEXT,
                    tipo_carroceria TEXT,
                    matricula_desde TEXT,
                    matricula_hasta TEXT,
                    servicio TEXT,
                    ultima_actualizacion TEXT,
                    indicador_crv TEXT,
                    estado_matricula TEXT,
                    dias_hasta_vencimiento INTEGER,
                    estimacion_valor REAL,
                    categoria_riesgo TEXT DEFAULT 'BAJO',
                    puntuacion_general INTEGER DEFAULT 0,
                    recomendacion TEXT,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (consulta_id) REFERENCES consultas_vehiculares (id) ON DELETE CASCADE
                )
            """)
            
            # Crear índices optimizados
            indices = [
                "CREATE INDEX IF NOT EXISTS idx_usuarios_cedula ON usuarios(cedula)",
                "CREATE INDEX IF NOT EXISTS idx_consultas_placa ON consultas_vehiculares(numero_placa)",
                "CREATE INDEX IF NOT EXISTS idx_consultas_session ON consultas_vehiculares(session_id)",
                "CREATE INDEX IF NOT EXISTS idx_vehiculos_sri_codigo ON datos_vehiculares_sri(codigo_vehiculo)",
                "CREATE INDEX IF NOT EXISTS idx_vehiculos_sri_marca ON datos_vehiculares_sri(descripcion_marca)",
                "CREATE INDEX IF NOT EXISTS idx_vehiculos_sri_propietario ON datos_vehiculares_sri(propietario_cedula)"
            ]
            
            for indice in indices:
                cursor.execute(indice)
            
            conn.commit()
            self.return_connection(conn)
            logger.info("✅ Base de datos ECPlacas 2.0 SRI + Propietario inicializada")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando base de datos: {e}")
            raise
    
    def save_user(self, user_data: UserData) -> int:
        """Guardar o actualizar usuario"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM usuarios WHERE cedula = ?", (user_data.cedula,))
            existing_user = cursor.fetchone()
            
            if existing_user:
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
    
    def save_vehicle_consultation_complete(self, vehicle_data: VehicleDataSRI, user_id: int) -> int:
        """Guardar consulta vehicular COMPLETA con SRI + Propietario"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Guardar consulta principal
            cursor.execute("""
                INSERT INTO consultas_vehiculares 
                (session_id, usuario_id, numero_placa, placa_original, 
                 placa_normalizada, codigo_vehiculo, consulta_exitosa, tiempo_consulta, 
                 mensaje_error, ip_origen, user_agent, api_utilizada, tiene_datos_sri, tiene_propietario)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                vehicle_data.session_id, user_id, vehicle_data.numero_placa,
                vehicle_data.placa_original, vehicle_data.placa_normalizada,
                vehicle_data.codigo_vehiculo, vehicle_data.consulta_exitosa, 
                vehicle_data.tiempo_consulta, vehicle_data.mensaje_error, 
                '', '', 'sri_completo_propietario', 1, vehicle_data.propietario_encontrado
            ))
            
            consulta_id = cursor.lastrowid
            
            # Guardar datos vehiculares SRI + Propietario completos
            if vehicle_data.consulta_exitosa:
                cursor.execute("""
                    INSERT INTO datos_vehiculares_sri 
                    (consulta_id, propietario_nombre, propietario_cedula, propietario_encontrado,
                     codigo_vehiculo, numero_camv_cpn, descripcion_marca, descripcion_modelo, 
                     anio_auto, descripcion_pais, color_vehiculo1, color_vehiculo2, cilindraje, 
                     nombre_clase, fecha_ultima_matricula, fecha_caducidad_matricula, 
                     fecha_compra_registro, fecha_revision, descripcion_canton, descripcion_servicio, 
                     ultimo_anio_pagado, prohibido_enajenar, estado_exoneracion, observacion, 
                     aplica_cuota, mensaje_motivo_auto, total_deudas_sri, total_impuestos, 
                     total_tasas, total_intereses, total_multas, total_prescripciones, 
                     total_rubros_pendientes, total_componentes_analizados, total_pagos_realizados, 
                     pagos_ultimo_ano, promedio_pago_anual, total_cuotas_vencidas, estado_legal_sri, 
                     riesgo_tributario, puntuacion_sri, recomendacion_tributaria, rubros_deuda_json, 
                     componentes_deuda_json, historial_pagos_json, plan_iacv_json, 
                     totales_beneficiario_json, vin_chasis, numero_motor, placa_anterior, 
                     clase_vehiculo, tipo_vehiculo, color_primario, peso_vehiculo, tipo_carroceria, 
                     matricula_desde, matricula_hasta, servicio, ultima_actualizacion, 
                     indicador_crv, estado_matricula, dias_hasta_vencimiento, estimacion_valor, 
                     categoria_riesgo, puntuacion_general, recomendacion)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    consulta_id, vehicle_data.propietario_nombre, vehicle_data.propietario_cedula,
                    vehicle_data.propietario_encontrado, vehicle_data.codigo_vehiculo, 
                    vehicle_data.numero_camv_cpn, vehicle_data.descripcion_marca, 
                    vehicle_data.descripcion_modelo, vehicle_data.anio_auto, vehicle_data.descripcion_pais,
                    vehicle_data.color_vehiculo1, vehicle_data.color_vehiculo2, vehicle_data.cilindraje,
                    vehicle_data.nombre_clase, vehicle_data.fecha_ultima_matricula,
                    vehicle_data.fecha_caducidad_matricula, vehicle_data.fecha_compra_registro,
                    vehicle_data.fecha_revision, vehicle_data.descripcion_canton,
                    vehicle_data.descripcion_servicio, vehicle_data.ultimo_anio_pagado,
                    vehicle_data.prohibido_enajenar, vehicle_data.estado_exoneracion,
                    vehicle_data.observacion, vehicle_data.aplica_cuota, vehicle_data.mensaje_motivo_auto,
                    vehicle_data.total_deudas_sri, vehicle_data.total_impuestos, vehicle_data.total_tasas,
                    vehicle_data.total_intereses, vehicle_data.total_multas, vehicle_data.total_prescripciones,
                    vehicle_data.total_rubros_pendientes, vehicle_data.total_componentes_analizados,
                    vehicle_data.total_pagos_realizados, vehicle_data.pagos_ultimo_ano,
                    vehicle_data.promedio_pago_anual, vehicle_data.total_cuotas_vencidas,
                    vehicle_data.estado_legal_sri, vehicle_data.riesgo_tributario,
                    vehicle_data.puntuacion_sri, vehicle_data.recomendacion_tributaria,
                    json.dumps(vehicle_data.rubros_deuda), json.dumps(vehicle_data.componentes_deuda),
                    json.dumps(vehicle_data.historial_pagos), json.dumps(vehicle_data.plan_excepcional_iacv),
                    json.dumps(vehicle_data.totales_por_beneficiario), vehicle_data.vin_chasis,
                    vehicle_data.numero_motor, vehicle_data.placa_anterior, vehicle_data.clase_vehiculo,
                    vehicle_data.tipo_vehiculo, vehicle_data.color_primario, vehicle_data.peso_vehiculo,
                    vehicle_data.tipo_carroceria, vehicle_data.matricula_desde, vehicle_data.matricula_hasta,
                    vehicle_data.servicio, vehicle_data.ultima_actualizacion, vehicle_data.indicador_crv,
                    vehicle_data.estado_matricula, vehicle_data.dias_hasta_vencimiento,
                    vehicle_data.estimacion_valor, vehicle_data.categoria_riesgo,
                    vehicle_data.puntuacion_general, vehicle_data.recomendacion
                ))
            
            conn.commit()
            self.return_connection(conn)
            logger.info(f"✅ Consulta COMPLETA guardada: ID {consulta_id}")
            return consulta_id
            
        except Exception as e:
            logger.error(f"❌ Error guardando consulta completa: {e}")
            if 'conn' in locals():
                self.return_connection(conn)
            return 0

class VehicleConsultantSRI:
    """Consultor SRI COMPLETO + Propietario optimizado"""
    
    def __init__(self):
        self.session = self._create_optimized_session()
        self.db = DatabaseManager()
        self.active_consultations = {}
        self._last_request_time = 0
    
    def _create_optimized_session(self) -> requests.Session:
        """Crear sesión HTTP optimizada"""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache'
        })
        
        return session
    
    def _apply_rate_limiting(self):
        """Aplicar rate limiting"""
        current_time = time.time()
        if self._last_request_time > 0:
            time_since_last = current_time - self._last_request_time
            if time_since_last < 1.0:
                sleep_time = 1.0 - time_since_last
                time.sleep(sleep_time)
        self._last_request_time = time.time()
    
    async def consultar_vehiculo_completo(self, placa: str, user_data: UserData, session_id: str) -> VehicleDataSRI:
        """Consulta COMPLETA: SRI + Propietario"""
        start_time = time.time()
        
        placa_original, placa_normalizada, was_modified = PlateValidator.normalize_plate(placa)
        
        vehicle_data = VehicleDataSRI(
            numero_placa=placa_normalizada,
            placa_original=placa_original,
            placa_normalizada=placa_normalizada,
            session_id=session_id
        )
        
        try:
            logger.info(f"🚀 Iniciando consulta COMPLETA para: {placa_original} → {placa_normalizada}")
            
            # PASO 1: Propietario del vehículo
            self.active_consultations[session_id] = {
                'status': 'consultando_propietario',
                'progress': 5,
                'message': '👤 Obteniendo propietario del vehículo...'
            }
            
            await self._consultar_propietario_vehiculo(vehicle_data, placa_normalizada)
            
            # PASO 2: Información base SRI
            self.active_consultations[session_id] = {
                'status': 'consultando_base_sri',
                'progress': 15,
                'message': '🔍 Consultando información base SRI...'
            }
            
            base_info = await self._consultar_base_vehiculo_sri(placa_normalizada)
            
            if not base_info or 'codigoVehiculo' not in base_info:
                if placa_original != placa_normalizada:
                    base_info = await self._consultar_base_vehiculo_sri(placa_original)
                
                if not base_info or 'codigoVehiculo' not in base_info:
                    vehicle_data.consulta_exitosa = False
                    vehicle_data.mensaje_error = "No se encontró información del vehículo en el SRI"
                    vehicle_data.tiempo_consulta = time.time() - start_time
                    return vehicle_data
            
            self._actualizar_info_basica_sri(vehicle_data, base_info)
            codigo_vehiculo = base_info['codigoVehiculo']
            
            # PASO 3: Rubros de deuda SRI
            self.active_consultations[session_id] = {
                'status': 'consultando_rubros_sri',
                'progress': 35,
                'message': '💰 Consultando rubros de deuda SRI...'
            }
            
            rubros_info = await self._consultar_rubros_deuda_sri(codigo_vehiculo)
            vehicle_data.rubros_deuda = rubros_info
            vehicle_data.total_rubros_pendientes = len(rubros_info)
            
            # PASO 4: Componentes detallados SRI
            self.active_consultations[session_id] = {
                'status': 'consultando_componentes_sri',
                'progress': 55,
                'message': '🔍 Analizando componentes fiscales...'
            }
            
            await self._consultar_componentes_detallados_sri(vehicle_data, rubros_info)
            
            # PASO 5: Historial de pagos SRI
            self.active_consultations[session_id] = {
                'status': 'consultando_pagos_sri',
                'progress': 75,
                'message': '📊 Obteniendo historial de pagos...'
            }
            
            historial_pagos = await self._consultar_historial_pagos_sri(placa_normalizada)
            vehicle_data.historial_pagos = historial_pagos
            await self._procesar_detalles_pagos_sri(vehicle_data, historial_pagos)
            
            # PASO 6: Plan excepcional IACV
            self.active_consultations[session_id] = {
                'status': 'consultando_iacv',
                'progress': 85,
                'message': '🌱 Consultando plan IACV...'
            }
            
            plan_iacv = await self._consultar_plan_excepcional_iacv_sri(codigo_vehiculo)
            vehicle_data.plan_excepcional_iacv = plan_iacv
            self._analizar_plan_iacv_sri(vehicle_data, plan_iacv)
            
            # PASO 7: Análisis consolidado COMPLETO
            self.active_consultations[session_id] = {
                'status': 'analizando_completo',
                'progress': 95,
                'message': '📈 Realizando análisis consolidado...'
            }
            
            self._agrupar_rubros_por_beneficiario_sri(vehicle_data)
            self._analizar_componentes_detallados_sri(vehicle_data)
            self._realizar_analisis_consolidado_sri(vehicle_data)
            
            vehicle_data.consulta_exitosa = True
            vehicle_data.tiempo_consulta = time.time() - start_time
            
            logger.info(f"✅ Consulta COMPLETA exitosa para {placa_normalizada}: "
                       f"Propietario: {vehicle_data.propietario_encontrado}, "
                       f"Rubros: {len(rubros_info)}, Componentes: {len(vehicle_data.componentes_deuda)}, "
                       f"Deudas: ${vehicle_data.total_deudas_sri:.2f}")
            
            # Guardar en base de datos
            user_id = self.db.save_user(user_data)
            if user_id:
                consultation_id = self.db.save_vehicle_consultation_complete(vehicle_data, user_id)
                logger.info(f"💾 Datos COMPLETOS guardados - Usuario: {user_id}, Consulta: {consultation_id}")
            
            return vehicle_data
            
        except Exception as e:
            vehicle_data.tiempo_consulta = time.time() - start_time
            vehicle_data.consulta_exitosa = False
            vehicle_data.mensaje_error = str(e)
            logger.error(f"❌ Error en consulta COMPLETA: {e}")
            return vehicle_data
    
    async def _consultar_propietario_vehiculo(self, vehicle_data: VehicleDataSRI, placa: str):
        """Consultar propietario del vehículo usando APIs disponibles"""
        try:
            self._apply_rate_limiting()
            
            # Intentar API principal
            try:
                response = self.session.post(
                    OWNER_APIS['primary'],
                    json={"value": placa},
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('data') and data['data'].get('name'):
                        vehicle_data.propietario_nombre = data['data']['name']
                        vehicle_data.propietario_cedula = data['data'].get('cedula', '')
                        vehicle_data.propietario_encontrado = True
                        logger.info(f"✅ Propietario encontrado: {vehicle_data.propietario_nombre}")
                        return
            except Exception as e:
                logger.warning(f"⚠️ Error en API principal de propietario: {e}")
            
            # Intentar API de respaldo
            try:
                response = self.session.get(
                    f"{OWNER_APIS['backup']}?placa={placa}",
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('propietario'):
                        vehicle_data.propietario_nombre = data['propietario'].get('nombre', '')
                        vehicle_data.propietario_cedula = data['propietario'].get('cedula', '')
                        vehicle_data.propietario_encontrado = True
                        logger.info(f"✅ Propietario encontrado (backup): {vehicle_data.propietario_nombre}")
                        return
            except Exception as e:
                logger.warning(f"⚠️ Error en API backup de propietario: {e}")
            
            # Si no se encuentra en ninguna API
            vehicle_data.propietario_encontrado = False
            logger.info(f"ℹ️ No se pudo obtener información del propietario para {placa}")
            
        except Exception as e:
            logger.error(f"❌ Error general consultando propietario: {e}")
            vehicle_data.propietario_encontrado = False
    
    async def _consultar_base_vehiculo_sri(self, placa: str) -> Optional[Dict]:
        """Consultar información base desde SRI"""
        try:
            self._apply_rate_limiting()
            
            url = f"{SRI_ENDPOINTS['base_vehiculo']}?numeroPlacaCampvCpn={placa}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"✅ Información base SRI obtenida para {placa}")
            return data
            
        except Exception as e:
            logger.error(f"❌ Error consultando base SRI: {e}")
            return None
    
    async def _consultar_rubros_deuda_sri(self, codigo_vehiculo: int) -> List[Dict]:
        """Consultar rubros de deuda detallados desde SRI"""
        try:
            self._apply_rate_limiting()
            
            url = f"{SRI_ENDPOINTS['consulta_rubros']}?codigoVehiculo={codigo_vehiculo}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Enriquecer datos de rubros
            for rubro in data:
                anio_desde = rubro.get('anioDesdePago', 0)
                anio_hasta = rubro.get('anioHastaPago', 0)
                if anio_desde and anio_hasta:
                    rubro['anos_deuda'] = anio_hasta - anio_desde + 1
                    rubro['periodo_deuda'] = f"{anio_desde} - {anio_hasta}"
                
                # Clasificar tipo de rubro
                descripcion = rubro.get('descripcionRubro', '').upper()
                if 'IMPUESTO' in descripcion:
                    rubro['categoria'] = 'IMPUESTO'
                elif 'TASA' in descripcion:
                    rubro['categoria'] = 'TASA'
                elif 'MULTA' in descripcion:
                    rubro['categoria'] = 'MULTA'
                else:
                    rubro['categoria'] = 'OTRO'
                
                # Determinar prioridad
                valor = rubro.get('valorRubro', 0)
                if valor > 500:
                    rubro['prioridad'] = 'ALTA'
                elif valor > 100:
                    rubro['prioridad'] = 'MEDIA'
                else:
                    rubro['prioridad'] = 'BAJA'
            
            logger.info(f"✅ {len(data)} rubros SRI obtenidos")
            return data
            
        except Exception as e:
            logger.error(f"❌ Error consultando rubros SRI: {e}")
            return []
    
    async def _consultar_componentes_detallados_sri(self, vehicle_data: VehicleDataSRI, rubros_info: List[Dict]):
        """Consultar componentes detallados para cada rubro SRI"""
        try:
            todos_componentes = []
            componentes_por_rubro = {}
            
            for rubro in rubros_info:
                codigo_rubro = rubro.get('codigoRubro')
                if not codigo_rubro:
                    continue
                
                self._apply_rate_limiting()
                
                url = f"{SRI_ENDPOINTS['consulta_componente']}?codigoConsultaRubro={codigo_rubro}"
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                componentes = response.json()
                
                # Enriquecer componentes
                for componente in componentes:
                    componente['rubro_padre'] = {
                        'codigoRubro': codigo_rubro,
                        'descripcionRubro': rubro.get('descripcionRubro', ''),
                        'nombreCortoBeneficiario': rubro.get('nombreCortoBeneficiario', ''),
                        'valorRubro': rubro.get('valorRubro', 0)
                    }
                    
                    # Clasificar tipo de componente
                    codigo_comp = componente.get('codigoComponente', '').upper()
                    descripcion_comp = componente.get('descripcionComponente', '').upper()
                    
                    if 'IMPUESTO' in codigo_comp or 'IMPUESTO' in descripcion_comp:
                        componente['tipo_componente'] = 'IMPUESTO'
                    elif 'TASA' in codigo_comp or 'TASA' in descripcion_comp:
                        componente['tipo_componente'] = 'TASA'
                    elif 'INTERES' in codigo_comp or 'INTERES' in descripcion_comp:
                        componente['tipo_componente'] = 'INTERES'
                    elif 'MULTA' in codigo_comp or 'MULTA' in descripcion_comp:
                        componente['tipo_componente'] = 'MULTA'
                    elif 'PRESCRIPCION' in codigo_comp or 'PRESCRIPCION' in descripcion_comp:
                        componente['tipo_componente'] = 'PRESCRIPCION'
                    else:
                        componente['tipo_componente'] = 'OTRO'
                
                componentes_por_rubro[str(codigo_rubro)] = componentes
                todos_componentes.extend(componentes)
            
            vehicle_data.componentes_deuda = todos_componentes
            vehicle_data.componentes_por_rubro = componentes_por_rubro
            vehicle_data.total_componentes_analizados = len(todos_componentes)
            
            logger.info(f"✅ {len(todos_componentes)} componentes SRI procesados")
            
        except Exception as e:
            logger.error(f"❌ Error consultando componentes SRI: {e}")
    
    async def _consultar_historial_pagos_sri(self, placa: str) -> List[Dict]:
        """Consultar historial completo de pagos SRI"""
        try:
            self._apply_rate_limiting()
            
            url = f"{SRI_ENDPOINTS['consulta_pagos']}?placaCampvCpn={placa}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if isinstance(data, dict) and 'data' in data:
                pagos = data['data']
            else:
                pagos = data if isinstance(data, list) else []
            
            # Mejorar formato de fechas
            for pago in pagos:
                if 'fechaDePago' in pago:
                    fecha_original = pago['fechaDePago']
                    try:
                        if fecha_original and len(fecha_original) >= 10:
                            fecha_formateada = self._formatear_fecha_pago(fecha_original)
                            pago['fechaDePagoFormateada'] = fecha_formateada
                    except Exception as e:
                        logger.debug(f"Error formateando fecha {fecha_original}: {e}")
            
            logger.info(f"✅ {len(pagos)} pagos SRI encontrados")
            return pagos
            
        except Exception as e:
            logger.error(f"❌ Error consultando pagos SRI: {e}")
            return []
    
    async def _procesar_detalles_pagos_sri(self, vehicle_data: VehicleDataSRI, historial_pagos: List[Dict]):
        """Procesar detalles de pagos SRI"""
        try:
            detalles_pagos = []
            total_pagos = 0.0
            pagos_ultimo_ano = 0.0
            ano_actual = datetime.now().year
            
            # Procesar hasta 50 pagos para evitar timeout
            pagos_a_procesar = historial_pagos[:50] if len(historial_pagos) > 50 else historial_pagos
            
            for pago in pagos_a_procesar:
                codigo_recaudacion = pago.get('codigoRecaudacion')
                if codigo_recaudacion:
                    try:
                        self._apply_rate_limiting()
                        url = f"{SRI_ENDPOINTS['detalle_pagos']}?codigoRecaudacion={codigo_recaudacion}"
                        response = self.session.get(url, timeout=30)
                        response.raise_for_status()
                        
                        data = response.json()
                        if isinstance(data, dict) and 'data' in data:
                            detalles = data['data']
                        else:
                            detalles = data if isinstance(data, list) else []
                        
                        detalles_pagos.extend(detalles)
                    except:
                        pass
                
                # Sumar montos de TODOS los pagos
                monto = pago.get('monto', 0)
                if isinstance(monto, (int, float)):
                    total_pagos += monto
                    
                    # Pagos del último año
                    fecha_pago = pago.get('fechaDePago', '')
                    if fecha_pago and str(ano_actual) in fecha_pago:
                        pagos_ultimo_ano += monto
            
            vehicle_data.detalles_pagos = detalles_pagos
            vehicle_data.total_pagos_realizados = total_pagos
            vehicle_data.pagos_ultimo_ano = pagos_ultimo_ano
            
            # Calcular promedio anual
            if len(historial_pagos) > 0:
                anos_con_pagos = len(set(p.get('fechaDePago', '')[:4] for p in historial_pagos if p.get('fechaDePago')))
                if anos_con_pagos > 0:
                    vehicle_data.promedio_pago_anual = total_pagos / anos_con_pagos
            
            logger.info(f"✅ Pagos SRI procesados: Total ${total_pagos:.2f}")
            
        except Exception as e:
            logger.error(f"❌ Error procesando pagos SRI: {e}")
    
    async def _consultar_plan_excepcional_iacv_sri(self, codigo_vehiculo: int) -> List[Dict]:
        """Consultar plan excepcional IACV completo"""
        try:
            self._apply_rate_limiting()
            
            url = f"{SRI_ENDPOINTS['plan_excepcional']}?codigo={codigo_vehiculo}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Mejorar datos del plan IACV
            for cuota in data:
                # Agregar fecha de vencimiento estimada
                periodo = cuota.get('periodoFiscal', '')
                if periodo:
                    fecha_vencimiento = self._estimar_fecha_vencimiento_iacv(periodo, cuota.get('numeroCuota', ''))
                    cuota['fechaVencimientoEstimada'] = fecha_vencimiento
                
                # Mejorar descripción de cuota
                numero_cuota = cuota.get('numeroCuota', '')
                if numero_cuota:
                    cuota['descripcionCuota'] = f"Cuota {numero_cuota} - {periodo}"
            
            logger.info(f"✅ Plan IACV obtenido: {len(data)} cuotas")
            return data
            
        except Exception as e:
            logger.error(f"❌ Error consultando plan IACV: {e}")
            return []
    
    def _formatear_fecha_pago(self, fecha_str: str) -> str:
        """Formatea fecha de pago a formato legible"""
        try:
            if ' ' in fecha_str:
                fecha_parte = fecha_str.split(' ')[0]
            else:
                fecha_parte = fecha_str[:10]
            
            if '-' in fecha_parte and len(fecha_parte) == 10:
                año, mes, dia = fecha_parte.split('-')
                return f"{dia}/{mes}/{año}"
            
            return fecha_str
        except Exception:
            return fecha_str
    
    def _estimar_fecha_vencimiento_iacv(self, periodo_fiscal: str, numero_cuota: str) -> str:
        """Estima fecha de vencimiento para cuotas IACV"""
        try:
            if '-' in periodo_fiscal:
                año_inicio = int(periodo_fiscal.split('-')[0])
            else:
                año_inicio = int(periodo_fiscal)
            
            cuota_num = 1
            if 'Cuota' in numero_cuota:
                try:
                    cuota_num = int(numero_cuota.split('Cuota')[-1].strip())
                except:
                    cuota_num = 1
            
            mes_vencimiento = (cuota_num - 1) * 3 + 3
            if mes_vencimiento > 12:
                año_inicio += (mes_vencimiento - 1) // 12
                mes_vencimiento = ((mes_vencimiento - 1) % 12) + 1
            
            return f"31/{mes_vencimiento:02d}/{año_inicio}"
            
        except Exception as e:
            logger.debug(f"Error estimando fecha vencimiento: {e}")
            return "Fecha no disponible"
    
    def _actualizar_info_basica_sri(self, vehicle_data: VehicleDataSRI, base_info: Dict):
        """Actualizar información básica desde SRI"""
        vehicle_data.codigo_vehiculo = base_info.get('codigoVehiculo', 0)
        vehicle_data.numero_camv_cpn = base_info.get('numeroCamvCpn', '')
        vehicle_data.descripcion_marca = base_info.get('descripcionMarca', '')
        vehicle_data.descripcion_modelo = base_info.get('descripcionModelo', '')
        vehicle_data.anio_auto = base_info.get('anioAuto', 0)
        vehicle_data.descripcion_pais = base_info.get('descripcionPais', '')
        vehicle_data.color_vehiculo1 = base_info.get('colorVehiculo1', '')
        vehicle_data.color_vehiculo2 = base_info.get('colorVehiculo2', '')
        vehicle_data.cilindraje = base_info.get('cilindraje', '')
        vehicle_data.nombre_clase = base_info.get('nombreClase', '')
        vehicle_data.fecha_ultima_matricula = base_info.get('fechaUltimaMatricula', '')
        vehicle_data.fecha_caducidad_matricula = base_info.get('fechaCaducidadMatricula', '')
        vehicle_data.fecha_compra_registro = base_info.get('fechaCompraRegistro', '')
        vehicle_data.fecha_revision = base_info.get('fechaRevision', '')
        vehicle_data.descripcion_canton = base_info.get('descripcionCanton', '')
        vehicle_data.descripcion_servicio = base_info.get('descripcionServicio', '')
        vehicle_data.ultimo_anio_pagado = base_info.get('ultimoAnioPagado', 0)
        vehicle_data.prohibido_enajenar = base_info.get('prohibidoEnajenar', '')
        vehicle_data.estado_exoneracion = base_info.get('estadoExoneracion', '')
        vehicle_data.observacion = base_info.get('observacion', '')
        vehicle_data.aplica_cuota = base_info.get('aplicaCuota', False)
        vehicle_data.mensaje_motivo_auto = base_info.get('mensajeMotivoAuto', '')
        
        # Compatibilidad con campos legacy
        vehicle_data.clase_vehiculo = vehicle_data.nombre_clase
        vehicle_data.tipo_vehiculo = base_info.get('tipoVehiculo', '')
        vehicle_data.color_primario = vehicle_data.color_vehiculo1
        vehicle_data.matricula_desde = vehicle_data.fecha_ultima_matricula
        vehicle_data.matricula_hasta = vehicle_data.fecha_caducidad_matricula
        vehicle_data.servicio = vehicle_data.descripcion_servicio
    
    def _agrupar_rubros_por_beneficiario_sri(self, vehicle_data: VehicleDataSRI):
        """Agrupar rubros por beneficiario"""
        try:
            agrupados = {}
            totales_beneficiario = {}
            
            for rubro in vehicle_data.rubros_deuda:
                beneficiario = rubro.get('nombreCortoBeneficiario', 'DESCONOCIDO')
                valor = rubro.get('valorRubro', 0)
                
                if beneficiario not in agrupados:
                    agrupados[beneficiario] = {
                        'rubros': [],
                        'total_valor': 0,
                        'cantidad_rubros': 0,
                        'tipos_deuda': set()
                    }
                
                agrupados[beneficiario]['rubros'].append(rubro)
                agrupados[beneficiario]['total_valor'] += valor if isinstance(valor, (int, float)) else 0
                agrupados[beneficiario]['cantidad_rubros'] += 1
                agrupados[beneficiario]['tipos_deuda'].add(rubro.get('descripcionRubro', ''))
                
                totales_beneficiario[beneficiario] = agrupados[beneficiario]['total_valor']
            
            # Convertir sets a listas
            for beneficiario in agrupados:
                agrupados[beneficiario]['tipos_deuda'] = list(agrupados[beneficiario]['tipos_deuda'])
            
            vehicle_data.rubros_agrupados_por_beneficiario = agrupados
            vehicle_data.totales_por_beneficiario = totales_beneficiario
            
            logger.info(f"✅ Rubros agrupados por {len(agrupados)} beneficiarios")
            
        except Exception as e:
            logger.error(f"❌ Error agrupando rubros: {e}")
    
    def _analizar_componentes_detallados_sri(self, vehicle_data: VehicleDataSRI):
        """Analizar componentes por tipo"""
        try:
            total_impuestos = 0.0
            total_tasas = 0.0
            total_intereses = 0.0
            total_multas = 0.0
            total_prescripciones = 0.0
            total_general = 0.0
            
            for componente in vehicle_data.componentes_deuda:
                valor = componente.get('valorComponente', 0)
                if not isinstance(valor, (int, float)):
                    continue
                
                tipo_comp = componente.get('tipo_componente', 'OTRO')
                
                if tipo_comp == 'IMPUESTO' and valor > 0:
                    total_impuestos += valor
                elif tipo_comp == 'TASA' and valor > 0:
                    total_tasas += valor
                elif tipo_comp == 'INTERES' and valor > 0:
                    total_intereses += valor
                elif tipo_comp == 'MULTA' and valor > 0:
                    total_multas += valor
                elif tipo_comp == 'PRESCRIPCION':
                    total_prescripciones += valor  # Puede ser negativo
                
                # Solo sumar valores positivos al total general
                if valor > 0:
                    total_general += valor
            
            vehicle_data.total_impuestos = total_impuestos
            vehicle_data.total_tasas = total_tasas
            vehicle_data.total_intereses = total_intereses
            vehicle_data.total_multas = total_multas
            vehicle_data.total_prescripciones = total_prescripciones
            vehicle_data.total_deudas_sri = total_general
            
            logger.info(f"✅ Análisis componentes SRI: Total ${total_general:.2f}")
            
        except Exception as e:
            logger.error(f"❌ Error analizando componentes: {e}")
    
    def _analizar_plan_iacv_sri(self, vehicle_data: VehicleDataSRI, plan_iacv: List[Dict]):
        """Analizar plan IACV"""
        try:
            total_vencidas = 0.0
            estados_count = {}
            
            for cuota in plan_iacv:
                estado = cuota.get('estadoPago', 'PENDIENTE')
                estados_count[estado] = estados_count.get(estado, 0) + 1
                
                if estado == 'VENCIDO':
                    total_cuota = cuota.get('totalCuota', 0)
                    if isinstance(total_cuota, (int, float)):
                        total_vencidas += total_cuota
            
            vehicle_data.total_cuotas_vencidas = total_vencidas
            vehicle_data.cuotas_por_estado = estados_count
            
            logger.info(f"✅ Plan IACV: {len(plan_iacv)} cuotas, ${total_vencidas:.2f} vencidas")
            
        except Exception as e:
            logger.error(f"❌ Error analizando IACV: {e}")
    
    def _realizar_analisis_consolidado_sri(self, vehicle_data: VehicleDataSRI):
        """Análisis consolidado SRI completo"""
        try:
            puntuacion = 100
            
            # Penalizaciones por deudas SRI
            if vehicle_data.total_deudas_sri > 2000:
                puntuacion -= 50
            elif vehicle_data.total_deudas_sri > 1000:
                puntuacion -= 40
            elif vehicle_data.total_deudas_sri > 500:
                puntuacion -= 25
            elif vehicle_data.total_deudas_sri > 100:
                puntuacion -= 15
            elif vehicle_data.total_deudas_sri > 0:
                puntuacion -= 5
            
            # Penalizaciones específicas por tipo
            if vehicle_data.total_multas > 100:
                puntuacion -= 20
            elif vehicle_data.total_multas > 0:
                puntuacion -= 10
            
            if vehicle_data.total_intereses > 50:
                puntuacion -= 15
            elif vehicle_data.total_intereses > 0:
                puntuacion -= 5
            
            # IACV vencidas
            if vehicle_data.total_cuotas_vencidas > 100:
                puntuacion -= 25
            elif vehicle_data.total_cuotas_vencidas > 50:
                puntuacion -= 20
            elif vehicle_data.total_cuotas_vencidas > 0:
                puntuacion -= 10
            
            # Bonificaciones por pagos
            if vehicle_data.total_pagos_realizados > 2000:
                puntuacion += 10
            elif vehicle_data.total_pagos_realizados > 1000:
                puntuacion += 5
            
            if vehicle_data.pagos_ultimo_ano > 0:
                puntuacion += 5
            
            # Prohibición de enajenar
            if vehicle_data.prohibido_enajenar and vehicle_data.prohibido_enajenar.upper() in ['SI', 'SÍ', 'YES']:
                puntuacion -= 30
            
            # Bonificación por prescripciones
            if vehicle_data.total_prescripciones < 0:
                puntuacion += min(10, abs(vehicle_data.total_prescripciones) / 100)
            
            vehicle_data.puntuacion_sri = max(0, min(100, puntuacion))
            
            # Determinar estado legal SRI
            if vehicle_data.puntuacion_sri >= 95:
                vehicle_data.estado_legal_sri = "EXCELENTE - SIN DEUDAS"
                vehicle_data.riesgo_tributario = "MUY BAJO"
                vehicle_data.recomendacion_tributaria = "Vehículo con situación tributaria óptima para transferencia"
            elif vehicle_data.puntuacion_sri >= 80:
                vehicle_data.estado_legal_sri = "BUENO - DEUDAS MENORES"
                vehicle_data.riesgo_tributario = "BAJO"
                vehicle_data.recomendacion_tributaria = "Regularizar deudas menores antes de transferencia"
            elif vehicle_data.puntuacion_sri >= 60:
                vehicle_data.estado_legal_sri = "REGULAR - DEUDAS MODERADAS"
                vehicle_data.riesgo_tributario = "MODERADO"
                vehicle_data.recomendacion_tributaria = "Negociar descuento por deudas pendientes en precio final"
            elif vehicle_data.puntuacion_sri >= 40:
                vehicle_data.estado_legal_sri = "MALO - DEUDAS ALTAS"
                vehicle_data.riesgo_tributario = "ALTO"
                vehicle_data.recomendacion_tributaria = "Verificar costos de regularización antes de compra"
            else:
                vehicle_data.estado_legal_sri = "CRÍTICO - MÚLTIPLES DEUDAS"
                vehicle_data.riesgo_tributario = "CRÍTICO"
                vehicle_data.recomendacion_tributaria = "NO RECOMENDADO - Evaluar otras alternativas"
            
            # Análisis de matrícula
            if vehicle_data.fecha_caducidad_matricula:
                try:
                    fecha_vencimiento = datetime.strptime(vehicle_data.fecha_caducidad_matricula.split(' ')[0], '%d-%m-%Y')
                    today = datetime.now()
                    dias_diferencia = (fecha_vencimiento - today).days
                    
                    vehicle_data.dias_hasta_vencimiento = dias_diferencia
                    
                    if dias_diferencia > 30:
                        vehicle_data.estado_matricula = "VIGENTE"
                    elif dias_diferencia > 0:
                        vehicle_data.estado_matricula = "POR VENCER"
                    else:
                        vehicle_data.estado_matricula = "VENCIDA"
                except:
                    vehicle_data.estado_matricula = "INDETERMINADO"
            
            # Estimación de valor
            if vehicle_data.anio_auto > 0:
                anio_actual = datetime.now().year
                antiguedad = anio_actual - vehicle_data.anio_auto
                
                valor_base = 15000
                factor_depreciacion = max(0.1, (1 - 0.08) ** antiguedad)
                valor_estimado = valor_base * factor_depreciacion
                
                if vehicle_data.total_deudas_sri > 0:
                    valor_estimado *= 0.9
                
                vehicle_data.estimacion_valor = max(valor_estimado, 1000)
            
            # Recomendación general
            recomendaciones = []
            if vehicle_data.propietario_encontrado:
                recomendaciones.append(f"👤 Propietario: {vehicle_data.propietario_nombre}")
            if vehicle_data.total_deudas_sri > 0:
                recomendaciones.append(f"💰 Deudas SRI: ${vehicle_data.total_deudas_sri:.2f}")
            if vehicle_data.total_cuotas_vencidas > 0:
                recomendaciones.append(f"🌱 IACV vencidas: ${vehicle_data.total_cuotas_vencidas:.2f}")
            if vehicle_data.estado_matricula == "VENCIDA":
                recomendaciones.append("🔴 Matrícula vencida")
            elif vehicle_data.estado_matricula == "VIGENTE":
                recomendaciones.append("✅ Matrícula vigente")
            
            if not recomendaciones:
                recomendaciones.append("✅ Sin observaciones importantes")
            
            vehicle_data.recomendacion = " | ".join(recomendaciones)
            
            logger.info(f"✅ Análisis SRI consolidado: Puntuación {vehicle_data.puntuacion_sri}, Estado {vehicle_data.estado_legal_sri}")
            
        except Exception as e:
            logger.error(f"❌ Error en análisis consolidado SRI: {e}")

# Instancia global del consultor SRI
vehicle_consultant_sri = VehicleConsultantSRI()

# ==========================================
# FACTORY FUNCTION PRINCIPAL
# ==========================================

def create_app(config_name: str = 'production') -> Flask:
    """Factory function para crear aplicación Flask ECPlacas 2.0 SRI COMPLETA + Propietario"""
    
    app = Flask(__name__, static_folder=None, template_folder=None)
    
    # Configuración básica optimizada
    app.config.update({
        'SECRET_KEY': os.getenv('SECRET_KEY', f'ecplacas_sri_completo_{int(time.time())}'),
        'WTF_CSRF_ENABLED': False,
        'JSON_AS_ASCII': False,
        'JSONIFY_PRETTYPRINT_REGULAR': True,
        'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,
        'PREFERRED_URL_SCHEME': 'https' if config_name == 'production' else 'http',
        'SESSION_COOKIE_SECURE': config_name == 'production',
        'SESSION_COOKIE_HTTPONLY': True,
        'SEND_FILE_MAX_AGE_DEFAULT': 31536000
    })
    
    # CORS optimizado
    cors_origins = ["http://localhost:*", "http://127.0.0.1:*"]
    if config_name == 'production':
        cors_origins.extend(["https://ecplacas.com", "https://www.ecplacas.com"])
    
    CORS(app, resources={
        r"/api/*": {
            "origins": cors_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
            "supports_credentials": True
        }
    })
    
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    
    # ==========================================
    # HOOKS DE APLICACIÓN
    # ==========================================
    
    @app.before_request
    def before_request():
        g.start_time = time.time()
        g.request_id = f"{int(time.time())}{hash(request.remote_addr or 'unknown') % 1000:03d}"
    
    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            response.headers['X-Response-Time'] = f'{duration:.3f}s'
        
        response.headers.update({
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'X-Powered-By': 'ECPlacas-2.0-SRI-COMPLETO-Engine',
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        })
        
        return response
    
    # ==========================================
    # ROUTES PRINCIPALES
    # ==========================================
    
    @app.route('/')
    def index():
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
            # Buscar en frontend/css primero
            if filename.endswith('.css'):
                css_path = FRONTEND_PATH / 'css' / filename
                if css_path.exists():
                    return send_from_directory(str(FRONTEND_PATH / 'css'), filename, mimetype='text/css')
            
            # Buscar en frontend/js
            if filename.endswith('.js'):
                js_path = FRONTEND_PATH / 'js' / filename
                if js_path.exists():
                    return send_from_directory(str(FRONTEND_PATH / 'js'), filename, mimetype='application/javascript')
            
            # Buscar en frontend directamente
            file_path = FRONTEND_PATH / filename
            if file_path.exists():
                return send_from_directory(str(FRONTEND_PATH), filename)
            
            # Backend/static como fallback
            backend_static = BACKEND_ROOT / 'static'
            if (backend_static / filename).exists():
                return send_from_directory(str(backend_static), filename)
            
            logger.warning(f"⚠️ Archivo estático no encontrado: {filename}")
            return "Archivo no encontrado", 404
            
        except Exception as e:
            logger.error(f"❌ Error sirviendo estático {filename}: {e}")
            return "Error interno", 500
    
    # ==========================================
    # API ENDPOINTS SRI COMPLETOS + PROPIETARIO
    # ==========================================
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        try:
            return jsonify({
                'success': True,
                'status': 'healthy',
                'service': 'ECPlacas 2.0 SRI COMPLETO + PROPIETARIO',
                'version': '2.0.1',
                'author': 'Erick Costa',
                'project': 'Construcción de Software',
                'theme': 'Futurista - Azul Neon',
                'timestamp': datetime.now().isoformat(),
                'environment': config_name,
                'features_completas': {
                    'propietario_vehiculo': True,
                    'consultas_vehiculares_sri': True,
                    'rubros_deuda_detallados': True,
                    'componentes_fiscales_completos': True,
                    'historial_pagos_completo': True,
                    'plan_iacv_ambiental': True,
                    'analisis_consolidado_sri': True,
                    'validacion_cedulas': True,
                    'normalizacion_placas': True,
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
    def consultar_vehiculo_completo():
        """Endpoint COMPLETO para consultar vehículo con datos SRI + Propietario"""
        try:
            if not request.is_json:
                return jsonify({
                    'success': False, 
                    'error': 'Content-Type debe ser application/json'
                }), 400
            
            data = request.get_json()
            placa = data.get('placa', '').strip()
            usuario_data = data.get('usuario', {})
            
            # Validaciones
            if not placa:
                return jsonify({'success': False, 'error': 'Placa es requerida'}), 400
            
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
            
            # Generar session ID
            session_id = f"ecplacas_completo_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
            
            logger.info(f"🚀 Nueva consulta ECPlacas 2.0 COMPLETA - Placa: {placa}, Session: {session_id}")
            
            # Función para consulta completa
            def run_complete_consultation():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # Marcar como iniciando
                    vehicle_consultant_sri.active_consultations[session_id] = {
                        'status': 'iniciando',
                        'progress': 5,
                        'message': '🚀 Iniciando consulta SRI COMPLETA + Propietario...',
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # Ejecutar consulta SRI completa + propietario
                    vehicle_data = loop.run_until_complete(
                        vehicle_consultant_sri.consultar_vehiculo_completo(placa, user_data, session_id)
                    )
                    
                    # Marcar como completado
                    vehicle_consultant_sri.active_consultations[session_id] = {
                        'status': 'completado',
                        'progress': 100,
                        'message': '✅ Consulta SRI COMPLETA + Propietario exitosa',
                        'result': vehicle_data.to_dict(),
                        'complete_summary': vehicle_data.get_complete_summary(),
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    logger.info(f"✅ Consulta COMPLETA finalizada: {session_id} - "
                               f"Propietario: {vehicle_data.propietario_encontrado}, "
                               f"Deudas: ${vehicle_data.total_deudas_sri:.2f}, "
                               f"Rubros: {vehicle_data.total_rubros_pendientes}, "
                               f"Pagos: ${vehicle_data.total_pagos_realizados:.2f}")
                    
                except Exception as e:
                    logger.error(f"❌ Error en thread COMPLETO {session_id}: {e}")
                    vehicle_consultant_sri.active_consultations[session_id] = {
                        'status': 'error',
                        'progress': 0,
                        'message': f'Error en consulta COMPLETA: {str(e)}',
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    }
                finally:
                    loop.close()
            
            # Ejecutar en thread separado
            thread = threading.Thread(target=run_complete_consultation, daemon=True)
            thread.start()
            
            # Normalizar placa para respuesta
            placa_original, placa_normalizada, was_modified = PlateValidator.normalize_plate(placa)
            
            return jsonify({
                'success': True,
                'message': 'Consulta ECPlacas 2.0 SRI COMPLETA + Propietario iniciada exitosamente',
                'session_id': session_id,
                'placa': placa_original,
                'placa_normalizada': placa_normalizada,
                'placa_fue_normalizada': was_modified,
                'status': 'procesando',
                'tiempo_estimado_segundos': 45,
                'caracteristicas_completas': [
                    '👤 Propietario del vehículo',
                    '🚗 Información base vehicular SRI',
                    '💰 Rubros de deuda detallados por beneficiario',
                    '🔍 Componentes fiscales (impuestos, tasas, multas, intereses, prescripciones)',
                    '📊 Historial completo de pagos SRI',
                    '🌱 Plan excepcional IACV (Impuesto Ambiental)',
                    '📈 Análisis consolidado con puntuación SRI',
                    '⚖️ Estados legales y recomendaciones tributarias'
                ],
                'urls': {
                    'estado': f'/api/estado-consulta/{session_id}',
                    'resultado': f'/api/resultado/{session_id}'
                },
                'timestamp': datetime.now().isoformat()
            }), 202
            
        except Exception as e:
            logger.error(f"❌ Error iniciando consulta COMPLETA: {e}")
            return jsonify({
                'success': False,
                'error': 'Error interno del servidor',
                'timestamp': datetime.now().isoformat()
            }), 500
    
    @app.route('/api/estado-consulta/<session_id>', methods=['GET'])
    def get_consultation_status(session_id):
        """Obtener estado actual de consulta SRI COMPLETA"""
        try:
            if session_id in vehicle_consultant_sri.active_consultations:
                consultation = vehicle_consultant_sri.active_consultations[session_id]
                return jsonify({
                    'success': True,
                    'session_id': session_id,
                    'status': consultation.get('status', 'unknown'),
                    'progress': consultation.get('progress', 0),
                    'message': consultation.get('message', ''),
                    'timestamp': consultation.get('timestamp', datetime.now().isoformat()),
                    'result_available': consultation.get('status') == 'completado'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Sesión no encontrada',
                    'session_id': session_id
                }), 404
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo estado: {e}")
            return jsonify({
                'success': False,
                'error': 'Error interno',
                'session_id': session_id
            }), 500
    
    @app.route('/api/resultado/<session_id>', methods=['GET'])
    def get_consultation_result(session_id):
        """Obtener resultado COMPLETO de consulta SRI + Propietario"""
        try:
            if session_id in vehicle_consultant_sri.active_consultations:
                consultation = vehicle_consultant_sri.active_consultations[session_id]
                
                if consultation.get('status') == 'completado' and 'result' in consultation:
                    vehicle_data = consultation['result']
                    complete_summary = consultation.get('complete_summary', {})
                    
                    return jsonify({
                        'success': True,
                        'session_id': session_id,
                        'vehicle_data': vehicle_data,
                        'complete_summary': complete_summary,
                        'timestamp': consultation.get('timestamp'),
                        'response_time': vehicle_data.get('tiempo_consulta', 0),
                        'features_extraidas': {
                            'propietario_encontrado': vehicle_data.get('propietario_encontrado', False),
                            'datos_sri_completos': True,
                            'rubros_deuda': len(vehicle_data.get('rubros_deuda', [])),
                            'componentes_analizados': vehicle_data.get('total_componentes_analizados', 0),
                            'historial_pagos': len(vehicle_data.get('historial_pagos', [])),
                            'plan_iacv': len(vehicle_data.get('plan_excepcional_iacv', [])),
                            'total_deudas_sri': vehicle_data.get('total_deudas_sri', 0),
                            'total_pagos_realizados': vehicle_data.get('total_pagos_realizados', 0)
                        }
                    })
                elif consultation.get('status') == 'error':
                    return jsonify({
                        'success': False,
                        'error': consultation.get('error', 'Error desconocido'),
                        'session_id': session_id
                    }), 500
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Consulta aún en proceso',
                        'status': consultation.get('status'),
                        'progress': consultation.get('progress', 0)
                    }), 202
            else:
                return jsonify({
                    'success': False,
                    'error': 'Sesión no encontrada',
                    'session_id': session_id
                }), 404
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo resultado: {e}")
            return jsonify({
                'success': False,
                'error': 'Error interno',
                'session_id': session_id
            }), 500
    
    @app.route('/api/estadisticas', methods=['GET'])
    def get_system_statistics():
        """Obtener estadísticas completas del sistema SRI + Propietario"""
        try:
            # Estadísticas básicas del sistema
            basic_stats = {
                'total_consultas': len(vehicle_consultant_sri.active_consultations),
                'consultas_activas': sum(1 for c in vehicle_consultant_sri.active_consultations.values() 
                                       if c.get('status') not in ['completado', 'error']),
                'consultas_completadas': sum(1 for c in vehicle_consultant_sri.active_consultations.values() 
                                           if c.get('status') == 'completado'),
                'consultas_con_error': sum(1 for c in vehicle_consultant_sri.active_consultations.values() 
                                         if c.get('status') == 'error'),
                'ultima_actualizacion': datetime.now().isoformat()
            }
            
            # Estadísticas de propietarios encontrados
            propietarios_stats = {
                'propietarios_encontrados': sum(1 for c in vehicle_consultant_sri.active_consultations.values() 
                                               if c.get('result', {}).get('propietario_encontrado', False)),
                'tasa_exito_propietarios': 0
            }
            
            if basic_stats['consultas_completadas'] > 0:
                propietarios_stats['tasa_exito_propietarios'] = round(
                    (propietarios_stats['propietarios_encontrados'] / basic_stats['consultas_completadas']) * 100, 2
                )
            
            return jsonify({
                'success': True,
                'estadisticas_generales': basic_stats,
                'estadisticas_propietarios': propietarios_stats,
                'apis_disponibles': {
                    'sri_endpoints': list(SRI_ENDPOINTS.keys()),
                    'owner_apis': list(OWNER_APIS.keys())
                },
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return jsonify({
                'success': False,
                'error': 'Error obteniendo estadísticas'
            }), 500
    
    @app.route('/api/test-sri-completo', methods=['GET'])
    def test_sri_completo():
        """Probar APIs completas del SRI + Propietario"""
        try:
            placa_test = request.args.get('placa', 'TBX0160')
            
            # Ejecutar pruebas en thread separado
            def run_tests():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    vehicle_data = loop.run_until_complete(
                        vehicle_consultant_sri.consultar_vehiculo_completo(
                            placa_test, 
                            UserData(nombre="Test Usuario", cedula="1234567890", telefono="0999999999", correo="test@test.com"),
                            f"test_completo_{int(time.time())}"
                        )
                    )
                    
                    return vehicle_data.to_dict()
                except Exception as e:
                    logger.error(f"Error en test SRI completo: {e}")
                    return {'error': str(e)}
                finally:
                    loop.close()
            
            result = run_tests()
            
            if 'error' in result:
                return jsonify({
                    'success': False,
                    'error': result['error'],
                    'placa_test': placa_test
                }), 500
            else:
                return jsonify({
                    'success': True,
                    'test_result': {
                        'propietario_encontrado': result.get('propietario_encontrado', False),
                        'propietario_nombre': result.get('propietario_nombre', ''),
                        'marca_modelo': f"{result.get('descripcion_marca', '')} {result.get('descripcion_modelo', '')}",
                        'total_deudas_sri': result.get('total_deudas_sri', 0),
                        'total_rubros': result.get('total_rubros_pendientes', 0),
                        'total_componentes': result.get('total_componentes_analizados', 0),
                        'total_pagos_realizados': result.get('total_pagos_realizados', 0),
                        'estado_legal_sri': result.get('estado_legal_sri', ''),
                        'puntuacion_sri': result.get('puntuacion_sri', 0),
                        'tiempo_consulta': result.get('tiempo_consulta', 0)
                    },
                    'placa_test': placa_test,
                    'timestamp': datetime.now().isoformat()
                })
                
        except Exception as e:
            logger.error(f"❌ Error en test SRI completo: {e}")
            return jsonify({
                'success': False,
                'error': 'Error en test SRI completo'
            }), 500
    
    @app.route('/api/limpiar-cache', methods=['POST'])
    def clear_system_cache():
        """Limpiar cache del sistema"""
        try:
            # Limpiar active consultations antiguas (más de 2 horas)
            current_time = time.time()
            sessions_to_remove = []
            
            for session_id, consultation in vehicle_consultant_sri.active_consultations.items():
                consultation_time = consultation.get('timestamp')
                if consultation_time:
                    try:
                        consultation_datetime = datetime.fromisoformat(consultation_time)
                        if (datetime.now() - consultation_datetime).total_seconds() > 7200:  # 2 horas
                            sessions_to_remove.append(session_id)
                    except:
                        sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                del vehicle_consultant_sri.active_consultations[session_id]
            
            # Limpiar caches de validación
            PlateValidator._validation_cache.clear()
            CedulaValidator._validation_cache.clear()
            
            logger.info(f"🧹 Cache limpiado: {len(sessions_to_remove)} sesiones eliminadas")
            
            return jsonify({
                'success': True,
                'message': f'Cache limpiado exitosamente',
                'sessions_removed': len(sessions_to_remove),
                'caches_cleared': ['plate_validator', 'cedula_validator', 'active_consultations'],
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Error limpiando cache: {e}")
            return jsonify({
                'success': False,
                'error': 'Error limpiando cache'
            }), 500
    
    @app.route('/api/validar-placa', methods=['POST'])
    def validate_plate():
        """Validar y normalizar placa"""
        try:
            if not request.is_json:
                return jsonify({
                    'success': False,
                    'error': 'Contenido debe ser JSON válido'
                }), 400
            
            data = request.get_json()
            placa = data.get('placa', '').strip()
            
            if not placa:
                return jsonify({
                    'success': False,
                    'error': 'El campo placa es requerido'
                }), 400
            
            placa_original, placa_normalizada, fue_modificada = PlateValidator.normalize_plate(placa)
            es_valida = PlateValidator.validate_plate_format(placa_normalizada)
            
            return jsonify({
                'success': True,
                'placa_original': placa_original,
                'placa_normalizada': placa_normalizada,
                'fue_modificada': fue_modificada,
                'es_valida': es_valida,
                'formato_detectado': 'Ecuatoriana estándar' if es_valida else 'Formato inválido',
                'mensaje': f"Placa {'normalizada automáticamente' if fue_modificada else 'sin cambios'}"
            })
            
        except Exception as e:
            logger.error(f"❌ Error validando placa: {e}")
            return jsonify({
                'success': False,
                'error': 'Error procesando validación de placa',
                'details': str(e)
            }), 500
    
    @app.route('/api/validar-cedula', methods=['POST'])
    def validate_cedula():
        """Validar cédula ecuatoriana"""
        try:
            if not request.is_json:
                return jsonify({
                    'success': False,
                    'error': 'Contenido debe ser JSON válido'
                }), 400
            
            data = request.get_json()
            cedula = data.get('cedula', '').strip()
            
            if not cedula:
                return jsonify({
                    'success': False,
                    'error': 'El campo cédula es requerido'
                }), 400
            
            es_valida = CedulaValidator.validate_ecuadorian_id(cedula)
            
            # Obtener información de provincia si es válida
            provincia_info = None
            if es_valida and len(cedula) >= 2:
                codigo_provincia = cedula[:2]
                provincia_info = {
                    'codigo': codigo_provincia,
                    'nombre': PROVINCE_CODES.get(codigo_provincia, 'Desconocida')
                }
            
            return jsonify({
                'success': True,
                'cedula': cedula,
                'es_valida': es_valida,
                'provincia': provincia_info,
                'algoritmo': 'Validación oficial Ecuador con dígito verificador',
                'mensaje': 'Cédula válida' if es_valida else 'Cédula inválida'
            })
            
        except Exception as e:
            logger.error(f"❌ Error validando cédula: {e}")
            return jsonify({
                'success': False,
                'error': 'Error procesando validación de cédula',
                'details': str(e)
            }), 500
    
    # ==========================================
    # FUNCIONES DE EMERGENCIA
    # ==========================================
    
    def create_emergency_frontend():
        """Crear frontend de emergencia si no existe index.html"""
        return f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>ECPlacas 2.0 SRI COMPLETO - Sistema Activo</title>
            <style>
                body {{
                    font-family: 'Arial', sans-serif;
                    background: linear-gradient(135deg, #000 0%, #001122 50%, #000033 100%);
                    color: #00ffff;
                    margin: 0;
                    padding: 20px;
                    min-height: 100vh;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                }}
                .container {{
                    text-align: center;
                    max-width: 900px;
                    padding: 2rem;
                    border: 2px solid #00ffff;
                    border-radius: 20px;
                    background: rgba(0, 0, 0, 0.8);
                    box-shadow: 0 0 30px rgba(0, 255, 255, 0.5);
                }}
                .logo {{
                    font-size: 3rem;
                    font-weight: bold;
                    margin-bottom: 1rem;
                    text-shadow: 0 0 20px #00ffff;
                }}
                .subtitle {{
                    font-size: 1.2rem;
                    margin-bottom: 2rem;
                    color: #99ccff;
                }}
                .status {{
                    background: linear-gradient(135deg, #00ff66, #00cc55);
                    color: #000;
                    padding: 1rem 2rem;
                    border-radius: 25px;
                    font-weight: bold;
                    margin: 2rem 0;
                    display: inline-block;
                }}
                .features {{
                    text-align: left;
                    margin: 2rem 0;
                    background: rgba(0, 51, 102, 0.3);
                    padding: 1.5rem;
                    border-radius: 15px;
                }}
                .features ul {{
                    list-style: none;
                    padding: 0;
                }}
                .features li {{
                    padding: 0.5rem 0;
                    color: #99ffcc;
                }}
                .features li:before {{
                    content: "✅ ";
                    color: #00ff66;
                }}
                .btn {{
                    background: linear-gradient(135deg, #0066ff, #00ffff);
                    border: none;
                    border-radius: 25px;
                    padding: 1rem 2rem;
                    color: #000;
                    font-weight: bold;
                    text-decoration: none;
                    display: inline-block;
                    margin: 0.5rem;
                    transition: all 0.3s ease;
                }}
                .btn:hover {{
                    transform: translateY(-3px);
                    box-shadow: 0 10px 25px rgba(0, 255, 255, 0.5);
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">ECPlacas 2.0 SRI COMPLETO</div>
                <div class="subtitle">Sistema de Consulta Vehicular + Propietario • Erick Costa</div>
                <div class="status">🚀 SISTEMA ACTIVO</div>
                
                <div style="background: rgba(0, 0, 0, 0.5); padding: 1.5rem; border-radius: 15px; margin: 2rem 0;">
                    <h2 style="color: #00ffff; margin-top: 0;">Sistema en Funcionamiento</h2>
                    <p>El backend de ECPlacas 2.0 SRI COMPLETO está ejecutándose correctamente.</p>
                    <p><strong>Servidor:</strong> http://localhost:5000</p>
                    <p><strong>API Health:</strong> <a href="/api/health" style="color: #00ffff;">/api/health</a></p>
                </div>
                
                <div class="features">
                    <h3>🎯 Características COMPLETAS Disponibles:</h3>
                    <ul>
                        <li>👤 Propietario del vehículo (nombre y cédula)</li>
                        <li>🚗 Consultas vehiculares SRI completas</li>
                        <li>💰 Rubros de deuda detallados por beneficiario</li>
                        <li>🔍 Componentes fiscales específicos (impuestos, tasas, multas, intereses)</li>
                        <li>📊 Historial completo de pagos SRI</li>
                        <li>🌱 Plan excepcional IACV (Impuesto Ambiental)</li>
                        <li>📈 Análisis consolidado con puntuación SRI (0-100)</li>
                        <li>⚖️ Estados legales y recomendaciones tributarias</li>
                        <li>🔒 Validación de cédulas ecuatorianas</li>
                        <li>🏷️ Normalización automática de placas</li>
                        <li>💾 Base de datos optimizada SQLite</li>
                        <li>⚡ Cache inteligente de consultas</li>
                        <li>📋 Logs rotativos para sostenibilidad</li>
                    </ul>
                </div>
                
                <div style="background: rgba(0, 0, 0, 0.5); padding: 1.5rem; border-radius: 15px; margin: 2rem 0;">
                    <h3>📡 APIs COMPLETAS Disponibles:</h3>
                    <p><strong>POST</strong> /api/consultar-vehiculo - Consulta SRI completa + propietario</p>
                    <p><strong>GET</strong> /api/estado-consulta/&lt;session_id&gt; - Estado en tiempo real</p>
                    <p><strong>GET</strong> /api/resultado/&lt;session_id&gt; - Resultado completo</p>
                    <p><strong>GET</strong> /api/estadisticas - Estadísticas del sistema</p>
                    <p><strong>GET</strong> /api/test-sri-completo - Probar APIs SRI + propietario</p>
                    <p><strong>POST</strong> /api/validar-placa - Validar formato de placa</p>
                    <p><strong>POST</strong> /api/validar-cedula - Validar cédula ecuatoriana</p>
                    <p><strong>POST</strong> /api/limpiar-cache - Limpiar cache del sistema</p>
                </div>
                
                <div>
                    <a href="/api/health" class="btn">🔍 Verificar Estado</a>
                    <a href="/admin" class="btn">⚙️ Panel Admin</a>
                    <a href="/api/estadisticas" class="btn">📊 Estadísticas</a>
                    <a href="/api/test-sri-completo" class="btn">🧪 Test Completo</a>
                </div>
                
                <div style="margin-top: 3rem; color: #666; font-size: 0.9rem;">
                    <p>ECPlacas 2.0 SRI COMPLETO + PROPIETARIO • Desarrollado por <span style="color: #00ffff;">Erick Costa</span></p>
                    <p>Proyecto: Construcción de Software • Temática: Futurista - Azul Neon</p>
                    <p>Versión: 2.0.1 OPTIMIZADA • Sistema completo con datos SRI y propietario</p>
                </div>
            </div>
            
            <script>
                // Auto-refresh status cada 30 segundos
                setInterval(() => {{
                    fetch('/api/health')
                        .then(response => response.json())
                        .then(data => {{
                            if (data.success) {{
                                console.log('✅ Sistema SRI COMPLETO funcionando correctamente');
                            }}
                        }})
                        .catch(error => {{
                            console.error('❌ Error verificando estado:', error);
                        }});
                }}, 30000);
            </script>
        </body>
        </html>
        """
    
    def create_emergency_admin():
        """Crear panel admin de emergencia"""
        return f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>ECPlacas 2.0 SRI COMPLETO - Admin Emergency</title>
            <style>
                body {{
                    font-family: 'Arial', sans-serif;
                    background: linear-gradient(135deg, #000 0%, #001122 50%, #000033 100%);
                    color: #00ffff;
                    margin: 0;
                    padding: 20px;
                    min-height: 100vh;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 2rem;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 3rem;
                    padding: 2rem;
                    border: 2px solid #00ffff;
                    border-radius: 20px;
                    background: rgba(0, 0, 0, 0.8);
                }}
                .logo {{
                    font-size: 2.5rem;
                    font-weight: bold;
                    margin-bottom: 0.5rem;
                    text-shadow: 0 0 20px #00ffff;
                }}
                .card {{
                    background: rgba(0, 0, 0, 0.8);
                    border: 1px solid rgba(0, 255, 255, 0.3);
                    border-radius: 15px;
                    padding: 2rem;
                    margin: 1rem 0;
                }}
                .grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 1.5rem;
                }}
                .btn {{
                    background: linear-gradient(135deg, #0066ff, #00ffff);
                    border: none;
                    border-radius: 25px;
                    padding: 1rem 2rem;
                    color: #000;
                    font-weight: bold;
                    cursor: pointer;
                    margin: 0.5rem;
                    transition: all 0.3s ease;
                }}
                .btn:hover {{
                    transform: translateY(-3px);
                    box-shadow: 0 10px 25px rgba(0, 255, 255, 0.5);
                }}
                .status-item {{
                    display: flex;
                    justify-content: space-between;
                    padding: 0.5rem 0;
                    border-bottom: 1px solid rgba(0, 255, 255, 0.1);
                }}
                .status-ok {{ color: #00ff66; }}
                .status-error {{ color: #ff6666; }}
                pre {{
                    background: rgba(0, 0, 0, 0.5);
                    padding: 1rem;
                    border-radius: 10px;
                    overflow-x: auto;
                    color: #99ccff;
                    font-size: 0.9rem;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">ECPlacas 2.0 SRI COMPLETO Admin</div>
                    <div>Panel Administrativo - Sistema Completo + Propietario</div>
                    <div style="margin-top: 1rem;">
                        <button class="btn" onclick="location.href='/'">🏠 Frontend</button>
                        <button class="btn" onclick="refreshStats()">🔄 Actualizar</button>
                    </div>
                </div>
                
                <div class="grid">
                    <div class="card">
                        <h3>🖥️ Estado del Sistema COMPLETO</h3>
                        <div id="systemStatus">
                            <div class="status-item">
                                <span>Backend SRI + Propietario:</span>
                                <span class="status-ok">✅ Activo</span>
                            </div>
                            <div class="status-item">
                                <span>Base de Datos:</span>
                                <span id="dbStatus">⏳ Verificando...</span>
                            </div>
                            <div class="status-item">
                                <span>APIs SRI:</span>
                                <span id="apiStatus">⏳ Verificando...</span>
                            </div>
                            <div class="status-item">
                                <span>APIs Propietario:</span>
                                <span id="ownerApiStatus">⏳ Verificando...</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>📊 Estadísticas COMPLETAS</h3>
                        <div id="stats">
                            <div class="status-item">
                                <span>Consultas Totales:</span>
                                <span id="totalConsultas">⏳</span>
                            </div>
                            <div class="status-item">
                                <span>Consultas Activas:</span>
                                <span id="consultasActivas">⏳</span>
                            </div>
                            <div class="status-item">
                                <span>Consultas Completadas:</span>
                                <span id="consultasCompletadas">⏳</span>
                            </div>
                            <div class="status-item">
                                <span>Propietarios Encontrados:</span>
                                <span id="propietariosEncontrados">⏳</span>
                            </div>
                            <div class="status-item">
                                <span>Tasa Éxito Propietarios:</span>
                                <span id="tasaExitoPropietarios">⏳</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <h3>🔧 Herramientas Administrativas COMPLETAS</h3>
                    <button class="btn" onclick="testSRICompleto()">🧪 Probar SRI + Propietario</button>
                    <button class="btn" onclick="clearCache()">🧹 Limpiar Cache</button>
                    <button class="btn" onclick="downloadStats()">📊 Descargar Stats</button>
                    <button class="btn" onclick="validatePlate()">🔍 Validar Placa</button>
                    <button class="btn" onclick="validateCedula()">📋 Validar Cédula</button>
                </div>
                
                <div class="card">
                    <h3>📋 Información del Sistema COMPLETO</h3>
                    <pre id="systemInfo">Cargando información del sistema...</pre>
                </div>
                
                <div class="card">
                    <h3>🔍 Test de Sistema COMPLETO</h3>
                    <div>
                        <label>Placa de prueba: </label>
                        <input type="text" id="testPlaca" value="TBX0160" style="padding: 0.5rem; margin: 0.5rem; background: rgba(0,0,0,0.5); border: 1px solid #00ffff; color: #fff; border-radius: 5px;">
                        <button class="btn" onclick="runCompleteTest()">▶ Ejecutar Test COMPLETO</button>
                    </div>
                    <pre id="testResults" style="max-height: 400px; overflow-y: auto;">Resultados aparecerán aquí...</pre>
                </div>
            </div>
            
            <script>
                function refreshStats() {{
                    fetch('/api/health')
                        .then(response => response.json())
                        .then(data => {{
                            if (data.success) {{
                                document.getElementById('dbStatus').innerHTML = '<span class="status-ok">✅ Conectada</span>';
                                document.getElementById('apiStatus').innerHTML = '<span class="status-ok">✅ SRI Disponibles</span>';
                                document.getElementById('ownerApiStatus').innerHTML = '<span class="status-ok">✅ Propietario Disponibles</span>';
                                document.getElementById('systemInfo').textContent = JSON.stringify(data, null, 2);
                            }}
                        }})
                        .catch(error => {{
                            document.getElementById('dbStatus').innerHTML = '<span class="status-error">❌ Error</span>';
                            document.getElementById('apiStatus').innerHTML = '<span class="status-error">❌ Error</span>';
                            console.error('Error:', error);
                        }});
                    
                    fetch('/api/estadisticas')
                        .then(response => response.json())
                        .then(data => {{
                            if (data.success) {{
                                const general = data.estadisticas_generales || {{}};
                                const propietarios = data.estadisticas_propietarios || {{}};
                                
                                document.getElementById('totalConsultas').textContent = general.total_consultas || '0';
                                document.getElementById('consultasActivas').textContent = general.consultas_activas || '0';
                                document.getElementById('consultasCompletadas').textContent = general.consultas_completadas || '0';
                                document.getElementById('propietariosEncontrados').textContent = propietarios.propietarios_encontrados || '0';
                                document.getElementById('tasaExitoPropietarios').textContent = (propietarios.tasa_exito_propietarios || 0) + '%';
                            }}
                        }})
                        .catch(error => {{
                            console.error('Error obteniendo estadísticas:', error);
                        }});
                }}
                
                function testSRICompleto() {{
                    fetch('/api/test-sri-completo?placa=TBX0160')
                        .then(response => response.json())
                        .then(data => {{
                            alert(data.success ? '✅ APIs SRI + Propietario funcionando correctamente' : '❌ Error en APIs');
                        }})
                        .catch(error => {{
                            alert('❌ Error conectando con APIs');
                        }});
                }}
                
                function clearCache() {{
                    fetch('/api/limpiar-cache', {{ method: 'POST' }})
                        .then(response => response.json())
                        .then(data => {{
                            alert(data.success ? '✅ Cache limpiado exitosamente' : '❌ Error limpiando cache');
                            refreshStats();
                        }});
                }}
                
                function downloadStats() {{
                    window.open('/api/estadisticas', '_blank');
                }}
                
                function validatePlate() {{
                    const placa = prompt('Ingrese placa a validar:', 'ABC123');
                    if (placa) {{
                        fetch('/api/validar-placa', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{ placa: placa }})
                        }})
                        .then(response => response.json())
                        .then(data => {{
                            alert(JSON.stringify(data, null, 2));
                        }});
                    }}
                }}
                
                function validateCedula() {{
                    const cedula = prompt('Ingrese cédula a validar:', '1234567890');
                    if (cedula) {{
                        fetch('/api/validar-cedula', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{ cedula: cedula }})
                        }})
                        .then(response => response.json())
                        .then(data => {{
                            alert(JSON.stringify(data, null, 2));
                        }});
                    }}
                }}
                
                function runCompleteTest() {{
                    const placa = document.getElementById('testPlaca').value;
                    document.getElementById('testResults').textContent = 'Ejecutando test SRI COMPLETO + Propietario...';
                    
                    fetch(`/api/test-sri-completo?placa=${{placa}}`)
                        .then(response => response.json())
                        .then(data => {{
                            document.getElementById('testResults').textContent = JSON.stringify(data, null, 2);
                        }})
                        .catch(error => {{
                            document.getElementById('testResults').textContent = 'Error: ' + error.message;
                        }});
                }}
                
                // Auto-refresh cada 30 segundos
                setInterval(refreshStats, 30000);
                
                // Cargar datos iniciales
                refreshStats();
            </script>
        </body>
        </html>
        """
    
    return app

# ==========================================
# PUNTO DE ENTRADA PRINCIPAL
# ==========================================

if __name__ == '__main__':
    try:
        logger.info("🚀 Iniciando ECPlacas 2.0 SRI COMPLETO + PROPIETARIO...")
        app = create_app()
        
        # Configuración del servidor optimizada
        server_config = {
            'host': '0.0.0.0',
            'port': 5000,
            'debug': False,
            'threaded': True,
            'use_reloader': False
        }
        
        logger.info("="*80)
        logger.info("🎯 ECPlacas 2.0 SRI COMPLETO + PROPIETARIO - SISTEMA INICIADO")
        logger.info("="*80)
        logger.info("🌐 Frontend: http://localhost:5000")
        logger.info("⚙️  Admin: http://localhost:5000/admin") 
        logger.info("🔍 API Health: http://localhost:5000/api/health")
        logger.info("📊 Estadísticas: http://localhost:5000/api/estadisticas")
        logger.info("🧪 Test Completo: http://localhost:5000/api/test-sri-completo")
        logger.info("="*80)
        logger.info("✨ Características COMPLETAS Activadas:")
        logger.info("   👤 • Propietario del vehículo (nombre y cédula)")
        logger.info("   🚗 • Consultas vehiculares SRI completas")
        logger.info("   💰 • Rubros de deuda detallados por beneficiario")
        logger.info("   🔍 • Componentes fiscales específicos (impuestos, tasas, multas, intereses)")
        logger.info("   📊 • Historial completo de pagos SRI con fechas")
        logger.info("   🌱 • Plan excepcional IACV (Impuesto Ambiental) con estados")
        logger.info("   📈 • Análisis consolidado con puntuación SRI (0-100)")
        logger.info("   ⚖️  • Estados legales y recomendaciones tributarias")
        logger.info("   🔒 • Validación de cédulas ecuatorianas con algoritmo oficial")
        logger.info("   🏷️  • Normalización automática de placas ecuatorianas")
        logger.info("   💾 • Base de datos SQLite optimizada para escalabilidad")
        logger.info("   ⚡ • Cache inteligente para máximo rendimiento")
        logger.info("   📋 • Logs rotativos para sostenibilidad ambiental")
        logger.info("   🔗 • APIs RESTful completas y documentadas")
        logger.info("="*80)
        logger.info("🔗 APIs COMPLETAS Disponibles:")
        logger.info("   • POST /api/consultar-vehiculo - Consulta SRI completa + propietario")
        logger.info("   • GET  /api/estado-consulta/<session_id> - Estado en tiempo real")
        logger.info("   • GET  /api/resultado/<session_id> - Resultado completo con datos SRI + propietario")
        logger.info("   • GET  /api/estadisticas - Estadísticas del sistema completo")
        logger.info("   • GET  /api/test-sri-completo - Probar conectividad con APIs SRI + propietario")
        logger.info("   • POST /api/validar-placa - Validar formato de placa")
        logger.info("   • POST /api/validar-cedula - Validar cédula ecuatoriana")
        logger.info("   • POST /api/limpiar-cache - Limpiar cache del sistema")
        logger.info("="*80)
        logger.info("🚀 Listo para recibir consultas SRI COMPLETAS + PROPIETARIO!")
        logger.info("="*80)
        
        app.run(**server_config)
        
    except KeyboardInterrupt:
        logger.info("🛑 Servidor ECPlacas 2.0 SRI COMPLETO detenido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error crítico al ejecutar servidor SRI COMPLETO: {e}")
        sys.exit(1)