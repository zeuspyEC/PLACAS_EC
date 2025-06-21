#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================
ECPlacas 2.0 SRI COMPLETO - Configuración
==========================================
Proyecto: Construcción de Software
Desarrollado por: Erick Costa
Versión: 2.0.1
==========================================

Configuración centralizada del sistema ECPlacas 2.0
"""

import os
import sys
from pathlib import Path
from datetime import timedelta

# Paths del proyecto
PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_ROOT = PROJECT_ROOT / "backend"
FRONTEND_ROOT = PROJECT_ROOT / "frontend"
DATABASE_ROOT = BACKEND_ROOT / "database"
LOGS_ROOT = PROJECT_ROOT / "logs"

# Asegurar que existan los directorios críticos
for directory in [DATABASE_ROOT, LOGS_ROOT, LOGS_ROOT / "app", LOGS_ROOT / "error", LOGS_ROOT / "access"]:
    directory.mkdir(parents=True, exist_ok=True)

class BaseConfig:
    """Configuración base del sistema"""
    
    # ==========================================
    # INFORMACIÓN DEL SISTEMA
    # ==========================================
    APP_NAME = "ECPlacas 2.0 SRI COMPLETO"
    APP_VERSION = "2.0.1"
    APP_AUTHOR = "Erick Costa"
    APP_PROJECT = "Construcción de Software"
    APP_THEME = "Futurista - Azul Neon"
    
    # ==========================================
    # CONFIGURACIÓN DE FLASK
    # ==========================================
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'ecplacas_2024_sri_completo_secret_key'
    WTF_CSRF_ENABLED = False
    JSON_AS_ASCII = False
    JSONIFY_PRETTYPRINT_REGULAR = True
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # ==========================================
    # BASE DE DATOS
    # ==========================================
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DATABASE_PATH = str(DATABASE_ROOT / "ecplacas.sqlite")
    DATABASE_BACKUP_PATH = str(DATABASE_ROOT / "backups")
    
    # Pool de conexiones optimizado
    DATABASE_POOL_SIZE = 5
    DATABASE_POOL_TIMEOUT = 30
    DATABASE_POOL_RECYCLE = 3600
    
    # ==========================================
    # APIs SRI Y PROPIETARIO
    # ==========================================
    SRI_BASE_URL = "https://srienlinea.sri.gob.ec/sri-matriculacion-vehicular-recaudacion-servicio-internet/rest"
    
    SRI_ENDPOINTS = {
        'base_vehiculo': f"{SRI_BASE_URL}/BaseVehiculo/obtenerPorNumeroPlacaOPorNumeroCampvOPorNumeroCpn",
        'consulta_rubros': f"{SRI_BASE_URL}/ConsultaRubros/obtenerPorCodigoVehiculo",
        'consulta_componente': f"{SRI_BASE_URL}/ConsultaComponente/obtenerListaComponentesPorCodigoConsultaRubro",
        'consulta_pagos': f"{SRI_BASE_URL}/consultaPagos/obtenerPorPlacaCampvCpn",
        'detalle_pagos': f"{SRI_BASE_URL}/consultaPagos/obtenerDetallesPago",
        'plan_excepcional': f"{SRI_BASE_URL}/CuotasImpAmbiental/obtenerDetallePlanExcepcionalPagosPorCodigoVehiculo"
    }
    
    OWNER_APIS = {
        'primary': 'https://app3902.privynote.net/api/v1/transit/vehicle-owner',
        'backup': 'https://consultasecuador.com/api/vehiculo/propietario'
    }
    
    # Timeouts y reintentos
    API_TIMEOUT = 30
    API_MAX_RETRIES = 3
    API_RATE_LIMIT = 1.0  # segundos entre requests
    
    # ==========================================
    # CÓDIGOS DE PROVINCIA ECUADOR
    # ==========================================
    PROVINCE_CODES = {
        '01': 'Azuay', '02': 'Bolívar', '03': 'Cañar', '04': 'Carchi',
        '05': 'Cotopaxi', '06': 'Chimborazo', '07': 'El Oro', '08': 'Esmeraldas',
        '09': 'Guayas', '10': 'Imbabura', '11': 'Loja', '12': 'Los Ríos',
        '13': 'Manabí', '14': 'Morona Santiago', '15': 'Napo', '16': 'Pastaza',
        '17': 'Pichincha', '18': 'Tungurahua', '19': 'Zamora Chinchipe',
        '20': 'Galápagos', '21': 'Sucumbíos', '22': 'Orellana',
        '23': 'Santo Domingo', '24': 'Santa Elena', '30': 'Exterior'
    }
    
    # ==========================================
    # CACHE Y PERFORMANCE
    # ==========================================
    CACHE_ENABLED = True
    CACHE_DEFAULT_TIMEOUT = 24 * 3600  # 24 horas
    CACHE_MAX_ENTRIES = 1000
    
    # ==========================================
    # RATE LIMITING
    # ==========================================
    RATELIMIT_ENABLED = True
    RATELIMIT_DEFAULT = "50 per hour"
    RATELIMIT_STORAGE_URL = "memory://"
    
    # ==========================================
    # LOGGING
    # ==========================================
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = str(LOGS_ROOT / "app" / "ecplacas.log")
    LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # ==========================================
    # SEGURIDAD
    # ==========================================
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT') or 'ecplacas_salt_2024'
    SECURITY_REGISTERABLE = False
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_TRACKABLE = True
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # ==========================================
    # CORS
    # ==========================================
    CORS_ORIGINS = ["http://localhost:*", "http://127.0.0.1:*"]
    CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS = ["Content-Type", "Authorization", "X-Requested-With"]
    
    # ==========================================
    # SESIONES
    # ==========================================
    SESSION_TIMEOUT = 7200  # 2 horas
    SESSION_CLEANUP_INTERVAL = 3600  # 1 hora
    
    # ==========================================
    # MÉTRICAS Y MONITOREO
    # ==========================================
    METRICS_ENABLED = True
    PERFORMANCE_MONITORING = True
    ERROR_TRACKING = True

class DevelopmentConfig(BaseConfig):
    """Configuración para desarrollo"""
    
    DEBUG = True
    ENV = 'development'
    TESTING = False
    
    # APIs mock para testing
    USE_MOCK_APIS = False
    
    # Logging más detallado
    LOG_LEVEL = 'DEBUG'
    
    # Rate limiting más permisivo
    RATELIMIT_DEFAULT = "100 per hour"
    
    # Cache deshabilitado para desarrollo
    CACHE_ENABLED = False

class TestingConfig(BaseConfig):
    """Configuración para testing"""
    
    DEBUG = True
    TESTING = True
    ENV = 'testing'
    
    # Base de datos en memoria para tests
    DATABASE_PATH = ":memory:"
    
    # APIs mock habilitadas
    USE_MOCK_APIS = True
    
    # Sin rate limiting en tests
    RATELIMIT_ENABLED = False
    
    # Cache deshabilitado
    CACHE_ENABLED = False
    
    # WTF-Forms sin CSRF para tests
    WTF_CSRF_ENABLED = False

class ProductionConfig(BaseConfig):
    """Configuración para producción"""
    
    DEBUG = False
    ENV = 'production'
    TESTING = False
    
    # Logging optimizado para producción
    LOG_LEVEL = 'INFO'
    
    # Seguridad reforzada
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Rate limiting estricto
    RATELIMIT_DEFAULT = "30 per hour"
    
    # CORS específico para producción
    CORS_ORIGINS = ["https://ecplacas.com", "https://www.ecplacas.com"]
    
    # Timeouts más largos para producción
    API_TIMEOUT = 45

class DockerConfig(ProductionConfig):
    """Configuración para Docker"""
    
    # Paths ajustados para Docker
    DATABASE_PATH = "/app/data/ecplacas.sqlite"
    DATABASE_BACKUP_PATH = "/app/data/backups"
    LOG_FILE = "/app/logs/ecplacas.log"
    
    # Variables de entorno para Docker
    SECRET_KEY = os.environ.get('SECRET_KEY', 'docker_secret_key_change_in_production')

# ==========================================
# CONFIGURACIÓN POR DEFECTO
# ==========================================

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'docker': DockerConfig,
    'default': DevelopmentConfig
}

def get_config(config_name=None):
    """Obtener configuración según el entorno"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    return config.get(config_name, config['default'])

# ==========================================
# VALIDACIONES DE CONFIGURACIÓN
# ==========================================

def validate_config(config_obj):
    """Validar configuración del sistema"""
    errors = []
    
    # Verificar paths críticos
    critical_paths = [
        ('DATABASE_PATH', Path(config_obj.DATABASE_PATH).parent),
        ('LOG_FILE', Path(config_obj.LOG_FILE).parent)
    ]
    
    for name, path in critical_paths:
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"No se puede crear directorio para {name}: {e}")
    
    # Verificar variables de entorno críticas en producción
    if config_obj.ENV == 'production':
        required_env_vars = ['SECRET_KEY']
        for var in required_env_vars:
            if not os.environ.get(var):
                errors.append(f"Variable de entorno requerida en producción: {var}")
    
    return errors

# ==========================================
# CONFIGURACIÓN DE LOGGING DETALLADA
# ==========================================

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '%(asctime)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'json': {
            'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'simple',
            'stream': sys.stdout
        },
        'app_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'filename': str(LOGS_ROOT / 'app' / 'ecplacas.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'encoding': 'utf-8'
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'detailed',
            'filename': str(LOGS_ROOT / 'error' / 'errors.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 3,
            'encoding': 'utf-8'
        },
        'performance_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'json',
            'filename': str(LOGS_ROOT / 'app' / 'performance.log'),
            'maxBytes': 5242880,  # 5MB
            'backupCount': 2,
            'encoding': 'utf-8'
        }
    },
    'loggers': {
        'ecplacas': {
            'level': 'DEBUG',
            'handlers': ['console', 'app_file', 'error_file'],
            'propagate': False
        },
        'ecplacas.performance': {
            'level': 'INFO',
            'handlers': ['performance_file'],
            'propagate': False
        },
        'werkzeug': {
            'level': 'WARNING',
            'handlers': ['console'],
            'propagate': False
        }
    }
}

# ==========================================
# CONFIGURACIÓN DE DESARROLLO LOCAL
# ==========================================

if __name__ == "__main__":
    # Script para verificar configuración
    import json
    
    print("🔧 Verificando configuración ECPlacas 2.0...")
    
    for env_name, config_class in config.items():
        print(f"\n📋 Configuración: {env_name}")
        cfg = config_class()
        
        errors = validate_config(cfg)
        if errors:
            print(f"❌ Errores encontrados:")
            for error in errors:
                print(f"   - {error}")
        else:
            print("✅ Configuración válida")
        
        # Mostrar algunas configuraciones importantes
        print(f"   Database: {cfg.DATABASE_PATH}")
        print(f"   Debug: {cfg.DEBUG}")
        print(f"   Log Level: {cfg.LOG_LEVEL}")
    
    print("\n✅ Verificación de configuración completada")