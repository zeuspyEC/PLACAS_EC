# -*- coding: utf-8 -*-
"""
==========================================
ECPlacas 2.0 - Backend Module
==========================================
Proyecto: Construcción de Software
Desarrollado por: Erick Costa
Temática: Futurista - Azul Neon
==========================================

Módulo principal del backend con optimizaciones de rendimiento,
sostenibilidad y escalabilidad.

Características:
- Lazy loading de componentes
- Cache inteligente
- Logs rotativos
- Pool de conexiones optimizado
- Gestión eficiente de memoria
"""

import os
import sys
from pathlib import Path

# Configuración del módulo backend
__version__ = "2.0.0"
__author__ = "Erick Costa"
__description__ = "ECPlacas 2.0 Backend - Sistema de Consulta Vehicular"

# Paths optimizados para rendimiento
BACKEND_ROOT = Path(__file__).parent
PROJECT_ROOT = BACKEND_ROOT.parent

# Configuración de logging para sostenibilidad
LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {"format": "%(levelname)s - %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "simple",
            "stream": sys.stdout,
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": str(BACKEND_ROOT / "logs" / "ecplacas.log"),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "ecplacas": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
            "propagate": False,
        }
    },
}

# Cache de configuración para rendimiento
_config_cache = {}


def get_config(key: str, default=None):
    """
    Obtener configuración con cache para optimizar rendimiento

    Args:
        key (str): Clave de configuración
        default: Valor por defecto

    Returns:
        Valor de configuración o default
    """
    if key in _config_cache:
        return _config_cache[key]

    # Cargar desde .env si existe
    env_file = BACKEND_ROOT / ".env"
    if env_file.exists() and key not in _config_cache:
        try:
            from dotenv import load_dotenv

            load_dotenv(env_file)
            _config_cache[key] = os.getenv(key, default)
        except ImportError:
            _config_cache[key] = default
    else:
        _config_cache[key] = default

    return _config_cache[key]


def clear_config_cache():
    """Limpiar cache de configuración (sostenibilidad)"""
    global _config_cache
    _config_cache.clear()


def get_version():
    """Obtener versión del backend"""
    return __version__


def get_paths():
    """Obtener paths principales del sistema"""
    return {
        "backend_root": BACKEND_ROOT,
        "project_root": PROJECT_ROOT,
        "database": BACKEND_ROOT / "database",
        "logs": BACKEND_ROOT / "logs",
        "static": BACKEND_ROOT / "static",
        "cache": BACKEND_ROOT / "cache",
    }


# Inicialización automática de directorios críticos
def _ensure_directories():
    """Asegurar que directorios críticos existan"""
    critical_dirs = [
        BACKEND_ROOT / "logs",
        BACKEND_ROOT / "database" / "backups",
        BACKEND_ROOT / "cache",
        BACKEND_ROOT / "static" / "css",
        BACKEND_ROOT / "static" / "js",
    ]

    for directory in critical_dirs:
        directory.mkdir(parents=True, exist_ok=True)


# Ejecutar inicialización
_ensure_directories()

# Exportar símbolos principales
__all__ = [
    "get_config",
    "clear_config_cache",
    "get_version",
    "get_paths",
    "BACKEND_ROOT",
    "PROJECT_ROOT",
    "LOG_CONFIG",
]
