#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================
ECPlacas 2.0 SRI COMPLETO - Archivo Principal
==========================================
Proyecto: Construcción de Software
Desarrollado por: Erick Costa - ZeusPy
Versión: 2.0.1
==========================================

Punto de entrada principal del sistema ECPlacas 2.0 SRI COMPLETO
Maneja inicialización, configuración y ejecución del servidor.
"""

import sys
import os
import time
import json
import logging
import argparse
import subprocess
import webbrowser
from pathlib import Path
from datetime import datetime

# Agregar directorio del proyecto al path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

def print_banner():
    """Mostrar banner del sistema"""
    banner = f"""
╔══════════════════════════════════════════════════════════════════════╗
║                    🚀 ECPlacas 2.0 SRI COMPLETO 🚀                 ║
║                                                                      ║
║  Sistema Completo de Consulta Vehicular + Propietario              ║
║  Desarrollado por: Erick Costa - ZeusPy                            ║
║  Proyecto: Construcción de Software                                 ║
║  Versión: 2.0.1                                                     ║
║                                                                      ║
║  💻 Enfoque: Rendimiento | Sostenibilidad | Escalabilidad          ║
║  🔥 Características: SRI + Propietario | APIs Completas             ║
╚══════════════════════════════════════════════════════════════════════╝

🎯 Características Principales:
   🚗 Consultas vehiculares SRI completas
   👤 Propietario del vehículo (nombre y cédula)
   💰 Rubros de deuda detallados por beneficiario
   🔍 Componentes fiscales específicos
   📊 Historial completo de pagos SRI
   🌱 Plan excepcional IACV
   📈 Análisis consolidado con puntuación SRI
   ⚖️ Estados legales y recomendaciones
"""
    print(banner)

def setup_logging():
    """Configurar logging del sistema"""
    logs_dir = PROJECT_ROOT / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(logs_dir / "ecplacas_main.log", encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger('ecplacas.main')

def check_python_version():
    """Verificar versión de Python"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Error: Se requiere Python 3.8 o superior")
        print(f"Versión actual: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
    return True

def check_project_structure():
    """Verificar estructura del proyecto"""
    required_dirs = [
        "backend",
        "frontend", 
        "logs",
        "config"
    ]
    
    required_files = [
        "backend/app.py",
        "frontend/index.html",
        "requirements.txt"
    ]
    
    print("📁 Verificando estructura del proyecto...")
    
    # Crear directorios faltantes
    for dir_name in required_dirs:
        dir_path = PROJECT_ROOT / dir_name
        if not dir_path.exists():
            print(f"📁 Creando directorio: {dir_name}")
            dir_path.mkdir(parents=True, exist_ok=True)
    
    # Verificar archivos críticos
    missing_files = []
    for file_path in required_files:
        full_path = PROJECT_ROOT / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Archivos faltantes:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("✅ Estructura del proyecto válida")
    return True

def install_dependencies():
    """Instalar dependencias del proyecto"""
    requirements_file = PROJECT_ROOT / "requirements.txt"
    
    if not requirements_file.exists():
        print("❌ Error: requirements.txt no encontrado")
        return False
    
    print("📦 Verificando e instalando dependencias...")
    
    try:
        # Actualizar pip primero
        print("🔄 Actualizando pip...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "--upgrade", "pip"
        ], check=True, capture_output=True)
        
        # Instalar dependencias
        print("📋 Instalando dependencias desde requirements.txt...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], check=True, capture_output=True, text=True)
        
        print("✅ Dependencias instaladas correctamente")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando dependencias: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        return False

def check_dependencies():
    """Verificar que las dependencias están instaladas"""
    required_modules = [
        'flask',
        'requests', 
        'aiohttp'
    ]
    
    print("🔍 Verificando dependencias...")
    missing = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        print(f"❌ Módulos faltantes: {', '.join(missing)}")
        return False
    
    print("✅ Todas las dependencias están disponibles")
    return True

def setup_database():
    """Configurar base de datos inicial"""
    try:
        from backend.db import ECPlacasDatabase
        
        print("🗄️ Configurando base de datos...")
        db = ECPlacasDatabase()
        print("✅ Base de datos configurada correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error configurando base de datos: {e}")
        return False

def start_backend_server(host='0.0.0.0', port=5000, debug=False):
    """Iniciar servidor backend"""
    try:
        from backend.app import create_app
        
        print("🚀 Iniciando servidor backend...")
        app = create_app('production' if not debug else 'development')
        
        print(f"🌐 Servidor iniciado en: http://{host}:{port}")
        print(f"🔍 API Health: http://{host}:{port}/api/health")
        print(f"📊 Panel Admin: http://{host}:{port}/admin")
        
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True,
            use_reloader=False
        )
        
    except Exception as e:
        print(f"❌ Error iniciando servidor: {e}")
        return False

def open_browser(url, delay=2):
    """Abrir navegador automáticamente"""
    def delayed_open():
        time.sleep(delay)
        try:
            webbrowser.open(url)
            print(f"🌐 Navegador abierto: {url}")
        except Exception as e:
            print(f"⚠️ No se pudo abrir el navegador automáticamente: {e}")
            print(f"💡 Abra manualmente: {url}")
    
    import threading
    threading.Thread(target=delayed_open, daemon=True).start()

def create_config_file():
    """Crear archivo de configuración si no existe"""
    config_dir = PROJECT_ROOT / "config"
    config_file = config_dir / "config.py"
    
    if not config_file.exists():
        print("⚙️ Creando archivo de configuración...")
        
        config_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECPlacas 2.0 - Configuración del Sistema
"""

import os
from pathlib import Path

# Paths del proyecto
PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_ROOT = PROJECT_ROOT / "backend"
FRONTEND_ROOT = PROJECT_ROOT / "frontend"

class Config:
    """Configuración base"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'ecplacas_2024_secret_key'
    DATABASE_PATH = str(PROJECT_ROOT / "backend" / "database" / "ecplacas.sqlite")
    
class DevelopmentConfig(Config):
    """Configuración de desarrollo"""
    DEBUG = True
    ENV = 'development'
    
class ProductionConfig(Config):
    """Configuración de producción"""
    DEBUG = False
    ENV = 'production'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
'''
        
        config_dir.mkdir(exist_ok=True)
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        print("✅ Archivo de configuración creado")

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='ECPlacas 2.0 SRI COMPLETO')
    parser.add_argument('--setup', action='store_true', help='Configurar sistema inicial')
    parser.add_argument('--install-deps', action='store_true', help='Instalar dependencias')
    parser.add_argument('--host', default='0.0.0.0', help='Host del servidor')
    parser.add_argument('--port', type=int, default=5000, help='Puerto del servidor')
    parser.add_argument('--debug', action='store_true', help='Modo debug')
    parser.add_argument('--no-browser', action='store_true', help='No abrir navegador automáticamente')
    
    args = parser.parse_args()
    
    # Configurar logging
    logger = setup_logging()
    
    # Mostrar banner
    print_banner()
    
    # Verificaciones iniciales
    if not check_python_version():
        sys.exit(1)
    
    if args.setup or args.install_deps:
        if not check_project_structure():
            sys.exit(1)
        
        if args.install_deps or args.setup:
            if not install_dependencies():
                sys.exit(1)
        
        if args.setup:
            create_config_file()
            if not setup_database():
                sys.exit(1)
            
            print("\n✅ Sistema configurado correctamente")
            print("💡 Ahora puede ejecutar: python ECPlacas.py")
            sys.exit(0)
    
    # Verificar dependencias
    if not check_dependencies():
        print("\n💡 Ejecute: python ECPlacas.py --install-deps")
        sys.exit(1)
    
    # Verificar estructura
    if not check_project_structure():
        print("\n💡 Ejecute: python ECPlacas.py --setup")
        sys.exit(1)
    
    # Crear archivo de configuración si no existe
    create_config_file()
    
    # Configurar base de datos
    if not setup_database():
        print("⚠️ Advertencia: Problemas con la base de datos")
    
    # Abrir navegador automáticamente (si no se deshabilitó)
    if not args.no_browser:
        url = f"http://localhost:{args.port}"
        open_browser(url)
    
    # Información final
    print("="*70)
    print("🎯 ECPlacas 2.0 SRI COMPLETO - SISTEMA INICIADO")
    print("="*70)
    print(f"🌐 Frontend: http://localhost:{args.port}")
    print(f"⚙️ Admin: http://localhost:{args.port}/admin")
    print(f"🔍 API Health: http://localhost:{args.port}/api/health")
    print(f"📊 API Stats: http://localhost:{args.port}/api/estadisticas")
    print("="*70)
    print("🛑 Presiona Ctrl+C para detener el servidor")
    print("="*70)
    
    # Iniciar servidor
    try:
        start_backend_server(
            host=args.host,
            port=args.port,
            debug=args.debug
        )
    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido por el usuario")
        logger.info("Sistema ECPlacas 2.0 detenido por el usuario")
    except Exception as e:
        print(f"\n❌ Error ejecutando el sistema: {e}")
        logger.error(f"Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()