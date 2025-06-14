#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================
ECPlacas 2.0 - Sistema de Consulta Vehicular
==========================================
Proyecto: Construcción de Software
Desarrollado por: Erick Costa
Temática: Futurista - Azul Neon
Versión: 2.0.0
==========================================

ARCHIVO PRINCIPAL ÚNICO - PUNTO DE ENTRADA AL SISTEMA

Este archivo maneja:
- Verificación e instalación de dependencias
- Configuración automática del sistema
- Inicialización de la base de datos
- Lanzamiento del servidor Flask
- Gestión de logs y errores
- Optimización de rendimiento
- Escalabilidad del sistema
"""

import sys
import os
import subprocess
import argparse
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# ==========================================
# CONFIGURACIÓN GLOBAL DEL SISTEMA
# ==========================================

# Información del proyecto
PROJECT_INFO = {
    "name": "ECPlacas 2.0",
    "version": "2.0.0",
    "author": "Erick Costa",
    "description": "Sistema de Consulta Vehicular - Temática Futurista",
    "python_min_version": (3, 8),
    "encoding": "utf-8"
}

# Estructura de directorios requerida (optimizada para escalabilidad)
REQUIRED_STRUCTURE = {
    "backend": {
        "routes": {},
        "database": {
            "backups": {}
        },
        "logs": {
            "app": {},
            "access": {},
            "error": {}
        },
        "static": {
            "css": {},
            "js": {},
            "img": {}
        },
        "cache": {}
    },
    "frontend": {
        "css": {},
        "js": {},
        "assets": {}
    }
}

# Dependencias requeridas con versiones específicas para estabilidad
REQUIRED_PACKAGES = [
    "flask>=2.3.3",
    "flask-cors>=4.0.0",
    "requests>=2.31.0",
    "python-dotenv>=1.0.0",
    "beautifulsoup4>=4.12.2",
    "lxml>=4.9.3",
    "selenium>=4.15.0",
    "webdriver-manager>=4.0.1",
    "schedule>=1.2.0",
    "colorama>=0.4.6",
    "psutil>=5.9.6",
    "cryptography>=41.0.7"
]

# Archivos core del sistema (performance crítico)
CORE_FILES = [
    "backend/app.py",
    "backend/db.py", 
    "backend/models.py",
    "backend/scraper.py",
    "backend/utils.py",
    "backend/__init__.py",
    "backend/routes/__init__.py",
    "backend/routes/admin_routes.py",
    "backend/routes/api_routes.py", 
    "backend/routes/frontend_routes.py",
    "backend/database/schema.sql",
    "backend/.env",
    "frontend/index.html",
    "frontend/admin.html",
    "frontend/css/main.css"
]

# ==========================================
# CLASE PRINCIPAL DEL SISTEMA
# ==========================================

class ECPlacasManager:
    """
    Gestor principal del sistema ECPlacas 2.0
    
    Características de rendimiento y escalabilidad:
    - Inicialización lazy de componentes
    - Cache de configuración
    - Logs rotativos para sostenibilidad
    - Verificación de integridad en tiempo real
    - Gestión optimizada de memoria
    """
    
    def __init__(self):
        self.base_path = Path.cwd()
        self.backend_path = self.base_path / "backend"
        self.frontend_path = self.base_path / "frontend"
        self.config_cache = {}
        self.logger = self._setup_logging()
        self.start_time = time.time()
        
    def _setup_logging(self) -> logging.Logger:
        """Configurar sistema de logging optimizado"""
        logger = logging.getLogger('ECPlacas')
        logger.setLevel(logging.INFO)
        
        # Handler para consola con formato futurista
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '🚀 ECPlacas 2.0 | %(asctime)s | %(levelname)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def print_banner(self):
        """Banner futurista del sistema"""
        banner = f"""
╔══════════════════════════════════════════════════════════════════════╗
║                         🚀 ECPlacas 2.0 🚀                         ║
║                                                                      ║
║  Sistema de Consulta Vehicular - Temática Futurista                ║
║  Desarrollado por: Erick Costa                                      ║
║  Proyecto: Construcción de Software                                 ║
║  Versión: {PROJECT_INFO['version']}                                           ║
║                                                                      ║
║  💻 Enfoque: Rendimiento | Sostenibilidad | Escalabilidad          ║
╚══════════════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def check_python_version(self) -> bool:
        """Verificar versión de Python (crítico para rendimiento)"""
        current_version = sys.version_info[:2]
        min_version = PROJECT_INFO["python_min_version"]
        
        if current_version < min_version:
            self.logger.error(f"❌ Python {min_version[0]}.{min_version[1]}+ requerido. Actual: {current_version[0]}.{current_version[1]}")
            return False
        
        self.logger.info(f"✅ Python {current_version[0]}.{current_version[1]} - Compatible")
        return True
    
    def create_directory_structure(self) -> bool:
        """Crear estructura de directorios optimizada para escalabilidad"""
        try:
            self.logger.info("📁 Creando estructura de directorios...")
            
            def create_recursive(base_path: Path, structure: dict):
                for name, subdirs in structure.items():
                    dir_path = base_path / name
                    dir_path.mkdir(exist_ok=True)
                    
                    if isinstance(subdirs, dict):
                        create_recursive(dir_path, subdirs)
            
            create_recursive(self.base_path, REQUIRED_STRUCTURE)
            
            # Crear archivos __init__.py para módulos Python
            init_files = [
                self.backend_path / "__init__.py",
                self.backend_path / "routes" / "__init__.py"
            ]
            
            for init_file in init_files:
                if not init_file.exists():
                    init_file.write_text('# ECPlacas 2.0 - Python Module\n')
            
            self.logger.info("✅ Estructura de directorios creada exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error creando estructura: {e}")
            return False
    
    def install_dependencies(self) -> bool:
        """Instalar dependencias con optimización de rendimiento"""
        try:
            self.logger.info("📦 Verificando e instalando dependencias...")
            
            # Verificar pip actualizado
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                         check=True, capture_output=True)
            
            # Instalar dependencias en lote para mejor rendimiento
            cmd = [sys.executable, "-m", "pip", "install"] + REQUIRED_PACKAGES
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info("✅ Dependencias instaladas correctamente")
                return True
            else:
                self.logger.error(f"❌ Error instalando dependencias: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error en instalación: {e}")
            return False
    
    def verify_system_integrity(self) -> Tuple[bool, List[str]]:
        """Verificar integridad del sistema (sostenibilidad)"""
        self.logger.info("🔍 Verificando integridad del sistema...")
        
        missing_files = []
        
        for file_path in CORE_FILES:
            full_path = self.base_path / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            self.logger.warning(f"⚠️  Archivos faltantes: {len(missing_files)}")
            for file in missing_files:
                self.logger.warning(f"   - {file}")
            return False, missing_files
        
        self.logger.info("✅ Integridad del sistema verificada")
        return True, []
    
    def create_environment_file(self) -> bool:
        """Crear archivo .env con configuración optimizada"""
        env_path = self.backend_path / ".env"
        
        if env_path.exists():
            self.logger.info("✅ Archivo .env ya existe")
            return True
        
        try:
            env_content = f"""# ECPlacas 2.0 - Configuración del Sistema
# Generado automáticamente el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# Configuración de Flask (optimizada para rendimiento)
FLASK_APP=app.py
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=ecplacas_2024_secret_key_futuristic_theme_{int(time.time())}

# Configuración de Base de Datos (SQLite optimizada)
DATABASE_URL=sqlite:///database/ecplacas.sqlite
DATABASE_POOL_SIZE=20
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600

# Configuración de APIs (escalabilidad)
API_TIMEOUT=30
API_MAX_RETRIES=3
API_RATE_LIMIT=100
API_CACHE_TTL=3600

# Configuración de Logs (sostenibilidad)
LOG_LEVEL=INFO
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=5
LOG_ROTATION_ENABLED=True

# Configuración de Cache (rendimiento)
CACHE_TYPE=simple
CACHE_DEFAULT_TIMEOUT=3600
CACHE_MAX_ENTRIES=1000

# Configuración de Seguridad
CORS_ORIGINS=*
RATE_LIMITING_ENABLED=True
MAX_REQUESTS_PER_HOUR=1000

# Información del Proyecto
PROJECT_NAME=ECPlacas 2.0
PROJECT_VERSION=2.0.0
PROJECT_AUTHOR=Erick Costa
PROJECT_THEME=Futurista - Azul Neon

# Configuración de Performance
THREADING_ENABLED=True
PROCESS_POOL_SIZE=4
ASYNC_ENABLED=True
COMPRESSION_ENABLED=True
"""
            
            env_path.write_text(env_content, encoding='utf-8')
            self.logger.info("✅ Archivo .env creado exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error creando .env: {e}")
            return False
    
    def start_server(self) -> bool:
        """Iniciar servidor Flask con configuración optimizada"""
        try:
            self.logger.info("🚀 Iniciando servidor ECPlacas 2.0...")
            
            # Cambiar al directorio backend
            os.chdir(self.backend_path)
            
            # Configurar variables de entorno
            os.environ['FLASK_APP'] = 'app.py'
            os.environ['FLASK_ENV'] = 'production'
            
            # Importar la aplicación Flask
            sys.path.insert(0, str(self.backend_path))
            
            from app import create_app
            app = create_app()
            
            # Configuración de servidor optimizada para rendimiento
            server_config = {
                'host': '0.0.0.0',
                'port': 5000,
                'debug': False,
                'threaded': True,
                'use_reloader': False,
                'processes': 1
            }
            
            self.logger.info("🌐 Servidor iniciado en http://localhost:5000")
            self.logger.info("🎯 Panel Admin: http://localhost:5000/admin")
            self.logger.info("⚡ API Health: http://localhost:5000/api/health")
            
            # Iniciar servidor
            app.run(**server_config)
            
            return True
            
        except ImportError as e:
            self.logger.error(f"❌ Error importando app: {e}")
            self.logger.error("💡 Ejecuta primero: python ECPlacas.py --setup")
            return False
        except Exception as e:
            self.logger.error(f"❌ Error iniciando servidor: {e}")
            return False
    
    def show_status(self):
        """Mostrar estado del sistema"""
        self.logger.info("📊 Estado del Sistema ECPlacas 2.0")
        self.logger.info("="*50)
        
        # Verificar estructura
        structure_ok = all((self.base_path / path).exists() for path in ["backend", "frontend"])
        self.logger.info(f"📁 Estructura: {'✅ OK' if structure_ok else '❌ ERROR'}")
        
        # Verificar archivos core
        integrity_ok, missing = self.verify_system_integrity()
        self.logger.info(f"🔍 Integridad: {'✅ OK' if integrity_ok else f'❌ {len(missing)} archivos faltantes'}")
        
        # Verificar .env
        env_exists = (self.backend_path / ".env").exists()
        self.logger.info(f"⚙️  Configuración: {'✅ OK' if env_exists else '❌ .env faltante'}")
        
        # Verificar base de datos
        db_exists = (self.backend_path / "database" / "ecplacas.sqlite").exists()
        self.logger.info(f"🗄️  Base de Datos: {'✅ OK' if db_exists else '❌ DB faltante'}")
        
        # Tiempo de ejecución
        runtime = time.time() - self.start_time
        self.logger.info(f"⏱️  Tiempo de verificación: {runtime:.2f}s")
    
    def interactive_menu(self):
        """Menú interactivo del sistema"""
        while True:
            print("\n" + "="*60)
            print("🎯 ECPlacas 2.0 - Menú Principal")
            print("="*60)
            print("1. 🚀 Iniciar Servidor")
            print("2. 🔧 Configurar Sistema")
            print("3. 🔍 Verificar Estado")
            print("4. 📦 Instalar Dependencias")
            print("5. 🗄️  Configurar Base de Datos")
            print("6. 📊 Ver Logs")
            print("7. 🧹 Limpiar Cache")
            print("8. ❌ Salir")
            print("="*60)
            
            try:
                choice = input("Selecciona una opción (1-8): ").strip()
                
                if choice == "1":
                    self.start_server()
                elif choice == "2":
                    self.setup_system()
                elif choice == "3":
                    self.show_status()
                elif choice == "4":
                    self.install_dependencies()
                elif choice == "5":
                    self.setup_database()
                elif choice == "6":
                    self.show_logs()
                elif choice == "7":
                    self.clean_cache()
                elif choice == "8":
                    self.logger.info("👋 Saliendo de ECPlacas 2.0...")
                    break
                else:
                    print("❌ Opción inválida. Intenta de nuevo.")
                    
            except KeyboardInterrupt:
                self.logger.info("\n👋 Saliendo de ECPlacas 2.0...")
                break
            except Exception as e:
                self.logger.error(f"❌ Error en menú: {e}")
    
    def setup_system(self) -> bool:
        """Configuración completa del sistema"""
        self.logger.info("🔧 Iniciando configuración completa del sistema...")
        
        steps = [
            ("Verificar Python", self.check_python_version),
            ("Crear estructura", self.create_directory_structure),
            ("Instalar dependencias", self.install_dependencies),
            ("Crear configuración", self.create_environment_file),
            ("Configurar base de datos", self.setup_database)
        ]
        
        for step_name, step_func in steps:
            self.logger.info(f"⚙️  {step_name}...")
            if not step_func():
                self.logger.error(f"❌ Error en: {step_name}")
                return False
            time.sleep(0.5)  # Breve pausa para UX
        
        self.logger.info("✅ Sistema configurado exitosamente")
        return True
    
    def setup_database(self) -> bool:
        """Configurar base de datos con optimizaciones"""
        try:
            self.logger.info("🗄️  Configurando base de datos...")
            
            db_path = self.backend_path / "database" / "ecplacas.sqlite"
            schema_path = self.backend_path / "database" / "schema.sql"
            
            # Si la base de datos ya existe, hacer backup
            if db_path.exists():
                backup_path = self.backend_path / "database" / "backups" / f"ecplacas_backup_{int(time.time())}.sqlite"
                backup_path.parent.mkdir(exist_ok=True)
                import shutil
                shutil.copy2(db_path, backup_path)
                self.logger.info(f"📦 Backup creado: {backup_path.name}")
            
            # Crear base de datos si el schema existe
            if schema_path.exists():
                import sqlite3
                
                conn = sqlite3.connect(db_path)
                with open(schema_path, 'r', encoding='utf-8') as f:
                    conn.executescript(f.read())
                conn.close()
                
                self.logger.info("✅ Base de datos configurada correctamente")
                return True
            else:
                self.logger.warning("⚠️  Schema SQL no encontrado")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error configurando DB: {e}")
            return False
    
    def show_logs(self):
        """Mostrar logs del sistema"""
        log_path = self.backend_path / "logs" / "ecplacas.log"
        
        if log_path.exists():
            print("\n" + "="*60)
            print("📋 Últimas 20 líneas del log:")
            print("="*60)
            
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines[-20:]:
                        print(line.strip())
            except Exception as e:
                self.logger.error(f"❌ Error leyendo logs: {e}")
        else:
            self.logger.info("📋 No hay logs disponibles")
    
    def clean_cache(self):
        """Limpiar cache del sistema"""
        cache_path = self.backend_path / "cache"
        
        if cache_path.exists():
            import shutil
            shutil.rmtree(cache_path)
            cache_path.mkdir()
            self.logger.info("🧹 Cache limpiado exitosamente")
        else:
            self.logger.info("🧹 No hay cache para limpiar")

# ==========================================
# FUNCIÓN PRINCIPAL
# ==========================================

def main():
    """Función principal con parseo de argumentos optimizado"""
    parser = argparse.ArgumentParser(
        description=f"{PROJECT_INFO['name']} v{PROJECT_INFO['version']} - {PROJECT_INFO['description']}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Ejemplos de uso:
  python ECPlacas.py                    # Inicio rápido
  python ECPlacas.py --setup           # Configuración completa
  python ECPlacas.py --check           # Verificar sistema
  python ECPlacas.py --menu            # Menú interactivo

Desarrollado por: {PROJECT_INFO['author']}
        """
    )
    
    parser.add_argument('--setup', action='store_true', 
                       help='Configurar sistema completo')
    parser.add_argument('--start', action='store_true',
                       help='Iniciar servidor directamente')
    parser.add_argument('--check', action='store_true',
                       help='Verificar estado del sistema')
    parser.add_argument('--menu', action='store_true',
                       help='Mostrar menú interactivo')
    parser.add_argument('--version', action='version',
                       version=f"{PROJECT_INFO['name']} v{PROJECT_INFO['version']}")
    
    args = parser.parse_args()
    
    # Crear instancia del manager
    manager = ECPlacasManager()
    manager.print_banner()
    
    try:
        # Ejecutar acción según argumentos
        if args.setup:
            success = manager.setup_system()
            if success:
                print("\n🎉 Sistema configurado. Ejecuta 'python ECPlacas.py --start' para iniciar")
            return 0 if success else 1
            
        elif args.start:
            return 0 if manager.start_server() else 1
            
        elif args.check:
            manager.show_status()
            return 0
            
        elif args.menu:
            manager.interactive_menu()
            return 0
            
        else:
            # Comportamiento por defecto: inicio inteligente
            manager.logger.info("🤖 Modo automático: Verificando sistema...")
            
            # Verificar si necesita configuración
            integrity_ok, missing = manager.verify_system_integrity()
            
            if not integrity_ok:
                manager.logger.info("🔧 Primera vez o archivos faltantes. Configurando...")
                if manager.setup_system():
                    manager.logger.info("🚀 Iniciando servidor...")
                    return 0 if manager.start_server() else 1
                else:
                    return 1
            else:
                manager.logger.info("✅ Sistema verificado. Iniciando servidor...")
                return 0 if manager.start_server() else 1
                
    except KeyboardInterrupt:
        manager.logger.info("\n👋 Saliendo de ECPlacas 2.0...")
        return 0
    except Exception as e:
        manager.logger.error(f"❌ Error crítico: {e}")
        return 1

if __name__ == "__main__":
    # Configurar encoding para Windows
    if sys.platform.startswith('win'):
        try:
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)
        except:
            pass
    
    # Ejecutar función principal
    sys.exit(main())