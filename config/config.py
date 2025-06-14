#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECPlacas 2.0 - Configuración del Sistema
Proyecto: Construcción de Software
Desarrollado por: Erick Costa

Configuración centralizada para ECPlacas 2.0
"""

import os
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

@dataclass
class DatabaseConfig:
    """Configuración de base de datos"""
    path: str = "database/ecplacas.sqlite"
    backup_path: str = "database/backups/"
    journal_mode: str = "WAL"
    synchronous: str = "NORMAL"
    cache_size: int = 10000
    timeout: float = 30.0
    
    @property
    def absolute_path(self) -> Path:
        """Ruta absoluta de la base de datos"""
        return Path(__file__).parent / self.path
    
    @property
    def backup_absolute_path(self) -> Path:
        """Ruta absoluta de backups"""
        return Path(__file__).parent / self.backup_path

@dataclass
class ServerConfig:
    """Configuración del servidor Flask"""
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False
    threaded: bool = True
    use_reloader: bool = False
    secret_key: str = "ecplacas_2024_change_in_production"
    
    @classmethod
    def from_env(cls) -> 'ServerConfig':
        """Crear configuración desde variables de entorno"""
        return cls(
            host=os.getenv('FLASK_HOST', '0.0.0.0'),
            port=int(os.getenv('FLASK_PORT', 5000)),
            debug=os.getenv('FLASK_ENV', 'production') == 'development',
            secret_key=os.getenv('SECRET_KEY', 'ecplacas_2024_change_in_production')
        )

@dataclass
class APIConfig:
    """Configuración de APIs externas"""
    ant_base_url: str = "https://servicios.axiscloud.ec/CRV/paginas"
    ant_endpoint: str = "/datosVehiculo.jsp"
    ant_empresa: str = "02"
    timeout: int = 30
    max_retries: int = 3
    rate_limit: float = 1.0
    
    @classmethod
    def from_env(cls) -> 'APIConfig':
        """Crear configuración desde variables de entorno"""
        return cls(
            ant_base_url=os.getenv('ANT_API_BASE_URL', cls.ant_base_url),
            ant_empresa=os.getenv('ANT_API_EMPRESA', cls.ant_empresa),
            timeout=int(os.getenv('ANT_API_TIMEOUT', cls.timeout)),
            max_retries=int(os.getenv('ANT_API_MAX_RETRIES', cls.max_retries)),
            rate_limit=float(os.getenv('ANT_API_RATE_LIMIT', cls.rate_limit))
        )

@dataclass
class CacheConfig:
    """Configuración de cache"""
    enabled: bool = True
    ttl_hours: int = 24
    max_entries: int = 1000
    cleanup_interval: int = 3600  # segundos
    
    @classmethod
    def from_env(cls) -> 'CacheConfig':
        """Crear configuración desde variables de entorno"""
        return cls(
            enabled=os.getenv('CACHE_ENABLED', 'true').lower() == 'true',
            ttl_hours=int(os.getenv('CACHE_TTL_HOURS', cls.ttl_hours)),
            max_entries=int(os.getenv('CACHE_MAX_ENTRIES', cls.max_entries))
        )

@dataclass
class LoggingConfig:
    """Configuración de logging"""
    level: str = "INFO"
    file_path: str = "logs/ecplacas.log"
    max_size: str = "10MB"
    backup_count: int = 5
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @classmethod
    def from_env(cls) -> 'LoggingConfig':
        """Crear configuración desde variables de entorno"""
        return cls(
            level=os.getenv('LOG_LEVEL', cls.level),
            file_path=os.getenv('LOG_FILE', cls.file_path),
            max_size=os.getenv('LOG_MAX_SIZE', cls.max_size),
            backup_count=int(os.getenv('LOG_BACKUP_COUNT', cls.backup_count))
        )
    
    @property
    def level_int(self) -> int:
        """Nivel de logging como entero"""
        return getattr(logging, self.level.upper(), logging.INFO)

@dataclass
class SecurityConfig:
    """Configuración de seguridad"""
    jwt_secret_key: str = "jwt_secret_change_in_production"
    rate_limit_enabled: bool = True
    rate_limit_per_hour: int = 50
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30
    
    @classmethod
    def from_env(cls) -> 'SecurityConfig':
        """Crear configuración desde variables de entorno"""
        return cls(
            jwt_secret_key=os.getenv('JWT_SECRET_KEY', cls.jwt_secret_key),
            rate_limit_enabled=os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true',
            rate_limit_per_hour=int(os.getenv('RATE_LIMIT_PER_HOUR', cls.rate_limit_per_hour)),
            max_login_attempts=int(os.getenv('MAX_LOGIN_ATTEMPTS', cls.max_login_attempts)),
            lockout_duration_minutes=int(os.getenv('LOCKOUT_DURATION_MINUTES', cls.lockout_duration_minutes))
        )

@dataclass
class NotificationConfig:
    """Configuración de notificaciones"""
    email_enabled: bool = False
    email_smtp_server: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_use_tls: bool = True
    
    sms_enabled: bool = False
    sms_api_key: str = ""
    sms_api_secret: str = ""
    
    whatsapp_enabled: bool = False
    whatsapp_api_token: str = ""
    
    @classmethod
    def from_env(cls) -> 'NotificationConfig':
        """Crear configuración desde variables de entorno"""
        return cls(
            email_enabled=os.getenv('EMAIL_ENABLED', 'false').lower() == 'true',
            email_smtp_server=os.getenv('EMAIL_SMTP_SERVER', cls.email_smtp_server),
            email_smtp_port=int(os.getenv('EMAIL_SMTP_PORT', cls.email_smtp_port)),
            email_username=os.getenv('EMAIL_USERNAME', ''),
            email_password=os.getenv('EMAIL_PASSWORD', ''),
            email_use_tls=os.getenv('EMAIL_USE_TLS', 'true').lower() == 'true',
            
            sms_enabled=os.getenv('SMS_ENABLED', 'false').lower() == 'true',
            sms_api_key=os.getenv('SMS_API_KEY', ''),
            sms_api_secret=os.getenv('SMS_API_SECRET', ''),
            
            whatsapp_enabled=os.getenv('WHATSAPP_ENABLED', 'false').lower() == 'true',
            whatsapp_api_token=os.getenv('WHATSAPP_API_TOKEN', '')
        )

@dataclass
class MaintenanceConfig:
    """Configuración de mantenimiento"""
    backup_enabled: bool = True
    backup_frequency_hours: int = 24
    cleanup_logs_days: int = 30
    cleanup_cache_days: int = 7
    cleanup_sessions_hours: int = 2
    
    @classmethod
    def from_env(cls) -> 'MaintenanceConfig':
        """Crear configuración desde variables de entorno"""
        return cls(
            backup_enabled=os.getenv('BACKUP_ENABLED', 'true').lower() == 'true',
            backup_frequency_hours=int(os.getenv('BACKUP_FREQUENCY_HOURS', cls.backup_frequency_hours)),
            cleanup_logs_days=int(os.getenv('CLEANUP_LOGS_DAYS', cls.cleanup_logs_days)),
            cleanup_cache_days=int(os.getenv('CLEANUP_CACHE_DAYS', cls.cleanup_cache_days)),
            cleanup_sessions_hours=int(os.getenv('CLEANUP_SESSIONS_HOURS', cls.cleanup_sessions_hours))
        )

@dataclass
class DevelopmentConfig:
    """Configuración de desarrollo"""
    debug_mode: bool = False
    metrics_enabled: bool = True
    profiling_enabled: bool = False
    mock_api_responses: bool = False
    
    @classmethod
    def from_env(cls) -> 'DevelopmentConfig':
        """Crear configuración desde variables de entorno"""
        return cls(
            debug_mode=os.getenv('DEBUG_MODE', 'false').lower() == 'true',
            metrics_enabled=os.getenv('METRICS_ENABLED', 'true').lower() == 'true',
            profiling_enabled=os.getenv('PROFILING_ENABLED', 'false').lower() == 'true',
            mock_api_responses=os.getenv('MOCK_API_RESPONSES', 'false').lower() == 'true'
        )

class ECPlacasConfig:
    """Configuración principal de ECPlacas 2.0"""
    
    def __init__(self):
        """Inicializar configuración completa"""
        
        # Información del proyecto
        self.PROJECT_NAME = "ECPlacas 2.0"
        self.VERSION = "2.0.0"
        self.AUTHOR = "Erick Costa"
        self.PROJECT_TYPE = "Construcción de Software"
        self.THEME = "Futurista - Azul Neon"
        
        # Rutas del proyecto
        self.PROJECT_ROOT = Path(__file__).parent
        self.BACKEND_DIR = self.PROJECT_ROOT / "backend"
        self.FRONTEND_DIR = self.PROJECT_ROOT / "frontend"
        self.DATABASE_DIR = self.PROJECT_ROOT / "database"
        self.LOGS_DIR = self.PROJECT_ROOT / "logs"
        self.CONFIG_DIR = self.PROJECT_ROOT / "config"
        
        # Cargar configuraciones
        self.server = ServerConfig.from_env()
        self.database = DatabaseConfig()
        self.api = APIConfig.from_env()
        self.cache = CacheConfig.from_env()
        self.logging = LoggingConfig.from_env()
        self.security = SecurityConfig.from_env()
        self.notifications = NotificationConfig.from_env()
        self.maintenance = MaintenanceConfig.from_env()
        self.development = DevelopmentConfig.from_env()
        
        # Crear directorios necesarios
        self._ensure_directories()
        
        # Configurar logging
        self._setup_logging()
    
    def _ensure_directories(self):
        """Asegurar que existen los directorios necesarios"""
        directories = [
            self.LOGS_DIR,
            self.CONFIG_DIR,
            self.DATABASE_DIR / "backups",
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _setup_logging(self):
        """Configurar sistema de logging"""
        import logging.handlers
        
        # Crear logger principal
        logger = logging.getLogger()
        logger.setLevel(self.logging.level_int)
        
        # Limpiar handlers existentes
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Formatter
        formatter = logging.Formatter(self.logging.format)
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.logging.level_int)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Handler para archivo con rotación
        file_handler = logging.handlers.RotatingFileHandler(
            self.LOGS_DIR / "ecplacas.log",
            maxBytes=self._parse_size(self.logging.max_size),
            backupCount=self.logging.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(self.logging.level_int)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    def _parse_size(self, size_str: str) -> int:
        """Convertir string de tamaño a bytes"""
        size_str = size_str.upper()
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)
    
    def get_flask_config(self) -> Dict[str, Any]:
        """Obtener configuración para Flask"""
        return {
            'SECRET_KEY': self.server.secret_key,
            'DEBUG': self.server.debug,
            'TESTING': False,
            'JSON_SORT_KEYS': False,
            'JSONIFY_PRETTYPRINT_REGULAR': True,
            'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB
        }
    
    def get_database_url(self) -> str:
        """Obtener URL de conexión a la base de datos"""
        return f"sqlite:///{self.database.absolute_path}"
    
    def is_production(self) -> bool:
        """Verificar si está en modo producción"""
        return not self.server.debug and not self.development.debug_mode
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Obtener información del entorno"""
        import platform
        import sys
        
        return {
            'project': {
                'name': self.PROJECT_NAME,
                'version': self.VERSION,
                'author': self.AUTHOR,
                'theme': self.THEME
            },
            'system': {
                'platform': platform.system(),
                'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                'architecture': platform.machine()
            },
            'server': {
                'host': self.server.host,
                'port': self.server.port,
                'debug': self.server.debug,
                'environment': 'development' if self.server.debug else 'production'
            },
            'features': {
                'cache_enabled': self.cache.enabled,
                'rate_limiting': self.security.rate_limit_enabled,
                'notifications': {
                    'email': self.notifications.email_enabled,
                    'sms': self.notifications.sms_enabled,
                    'whatsapp': self.notifications.whatsapp_enabled
                },
                'maintenance': {
                    'backup': self.maintenance.backup_enabled,
                    'metrics': self.development.metrics_enabled
                }
            }
        }
    
    def validate_configuration(self) -> tuple[bool, list[str]]:
        """Validar configuración completa"""
        errors = []
        warnings = []
        
        # Validar configuración del servidor
        if not (1 <= self.server.port <= 65535):
            errors.append(f"Puerto inválido: {self.server.port}")
        
        # Validar configuración de base de datos
        if not self.database.absolute_path.parent.exists():
            try:
                self.database.absolute_path.parent.mkdir(parents=True)
            except Exception as e:
                errors.append(f"No se puede crear directorio de base de datos: {e}")
        
        # Validar configuración de API
        if not self.api.ant_base_url.startswith(('http://', 'https://')):
            errors.append("URL de API ANT debe comenzar con http:// o https://")
        
        if self.api.timeout <= 0:
            errors.append("Timeout de API debe ser mayor a 0")
        
        # Validar configuración de cache
        if self.cache.ttl_hours <= 0:
            errors.append("TTL de cache debe ser mayor a 0")
        
        # Validar configuración de seguridad
        if self.is_production():
            if self.server.secret_key == "ecplacas_2024_change_in_production":
                errors.append("SECRET_KEY debe cambiarse en producción")
            
            if self.security.jwt_secret_key == "jwt_secret_change_in_production":
                errors.append("JWT_SECRET_KEY debe cambiarse en producción")
        
        # Validar notificaciones
        if self.notifications.email_enabled:
            if not self.notifications.email_username or not self.notifications.email_password:
                warnings.append("Email habilitado pero credenciales incompletas")
        
        return len(errors) == 0, errors + warnings
    
    def __str__(self) -> str:
        """Representación string de la configuración"""
        env_info = self.get_environment_info()
        return f"""
ECPlacas 2.0 Configuration
=========================
Project: {env_info['project']['name']} v{env_info['project']['version']}
Author: {env_info['project']['author']}
Theme: {env_info['project']['theme']}

Server: {env_info['server']['host']}:{env_info['server']['port']}
Environment: {env_info['server']['environment']}
Database: {self.database.path}

Features:
  • Cache: {'✅' if self.cache.enabled else '❌'}
  • Rate Limiting: {'✅' if self.security.rate_limit_enabled else '❌'}
  • Email Notifications: {'✅' if self.notifications.email_enabled else '❌'}
  • Automatic Backup: {'✅' if self.maintenance.backup_enabled else '❌'}
        """

# Instancia global de configuración
config = ECPlacasConfig()

# Funciones de conveniencia
def get_config() -> ECPlacasConfig:
    """Obtener instancia de configuración"""
    return config

def is_development() -> bool:
    """Verificar si está en modo desarrollo"""
    return config.server.debug or config.development.debug_mode

def is_production() -> bool:
    """Verificar si está en modo producción"""
    return config.is_production()

if __name__ == "__main__":
    # Script de prueba de configuración
    print("🧪 Probando configuración de ECPlacas 2.0...")
    
    # Mostrar configuración
    print(config)
    
    # Validar configuración
    is_valid, issues = config.validate_configuration()
    
    if is_valid:
        print("✅ Configuración válida")
    else:
        print("❌ Problemas en configuración:")
        for issue in issues:
            print(f"   • {issue}")
    
    # Mostrar información del entorno
    import json
    env_info = config.get_environment_info()
    print("\n📋 Información del entorno:")
    print(json.dumps(env_info, indent=2, ensure_ascii=False))
