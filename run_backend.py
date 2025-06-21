#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================
ECPlacas 2.0 - Ejecutor de Backend
==========================================
Proyecto: Construcción de Software
Desarrollado por: Erick Costa
Temática: Futurista - Azul Neon
==========================================

EJECUTOR ESPECÍFICO DEL BACKEND
Este archivo ejecuta únicamente el servidor Flask backend
"""

import sys
import os
import time
import logging
from pathlib import Path

# Configurar encoding para Windows
if sys.platform.startswith('win'):
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)
    except:
        pass

def print_backend_banner():
    """Banner del backend"""
    banner = f"""
╔══════════════════════════════════════════════════════════════════════╗
║                    🔧 ECPlacas 2.0 - BACKEND 🔧                    ║
║                                                                      ║
║  Servidor Flask con APIs SRI Completas + Propietario              ║
║  Desarrollado por: Erick Costa                                      ║
║  Proyecto: Construcción de Software                                 ║
║  Versión: 2.0.1                                                     ║
║                                                                      ║
║  🔥 Solo Backend - Optimizado para Rendimiento                     ║
╚══════════════════════════════════════════════════════════════════════╝
    """
    print(banner)

def main():
    """Función principal para ejecutar solo el backend"""
    print_backend_banner()
    
    try:
        # Obtener directorio actual
        current_dir = Path.cwd()
        backend_dir = current_dir / "backend"
        
        # Verificar que existe el directorio backend
        if not backend_dir.exists():
            print("❌ Error: Directorio 'backend' no encontrado")
            print("💡 Estructura esperada:")
            print("   proyecto/")
            print("   ├── run_backend.py  (este archivo)")
            print("   └── backend/")
            print("       └── app.py")
            return 1
        
        # Verificar que existe app.py
        app_file = backend_dir / "app.py"
        if not app_file.exists():
            print("❌ Error: backend/app.py no encontrado")
            print("💡 Verifica que el archivo backend/app.py existe")
            return 1
        
        print("🚀 Iniciando servidor backend...")
        print("📁 Proyecto:", current_dir)
        print("📁 Backend:", backend_dir)
        print("🐍 Python:", sys.version.split()[0])
        print("="*70)
        
        # Agregar directorio backend al path de Python
        sys.path.insert(0, str(backend_dir))
        
        # Cambiar al directorio backend
        original_cwd = os.getcwd()
        os.chdir(backend_dir)
        
        try:
            # Importar la aplicación Flask
            from app import create_app
            
            app = create_app('production')
            
            # Configuración del servidor optimizada para backend
            server_config = {
                'host': '0.0.0.0',
                'port': 5000,
                'debug': False,
                'threaded': True,
                'use_reloader': False,
                'processes': 1
            }
            
            print("🌐 Backend disponible en: http://localhost:5000")
            print("🔍 API Health: http://localhost:5000/api/health")
            print("📊 Estadísticas: http://localhost:5000/api/estadisticas")
            print("⚙️  Admin Panel: http://localhost:5000/admin")
            print("🧪 Test SRI: http://localhost:5000/api/test-sri-completo")
            print("="*70)
            print("🎯 SOLO BACKEND - Frontend debe ejecutarse por separado")
            print("💡 Para frontend: python run_frontend.py")
            print("💡 Para sistema completo: python ECPlacas.py")
            print("="*70)
            print("🛑 Presiona Ctrl+C para detener el servidor")
            print("="*70)
            
            # Ejecutar servidor Flask
            app.run(**server_config)
            
        except ImportError as e:
            print(f"❌ Error importando aplicación: {e}")
            print("💡 Posibles soluciones:")
            print("   1. Verificar que backend/app.py existe y es válido")
            print("   2. Instalar dependencias: pip install -r requirements.txt")
            print("   3. Ejecutar configuración: python ECPlacas.py --setup")
            return 1
        
        except Exception as e:
            print(f"❌ Error ejecutando backend: {e}")
            return 1
            
        finally:
            # Restaurar directorio original
            os.chdir(original_cwd)
            
    except KeyboardInterrupt:
        print("\n🛑 Backend detenido por el usuario")
        return 0
    except Exception as e:
        print(f"❌ Error general: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())