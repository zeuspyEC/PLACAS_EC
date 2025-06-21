#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================
ECPlacas 2.0 - Ejecutor de Frontend
==========================================
Proyecto: Construcción de Software
Desarrollado por: Erick Costa
Temática: Futurista - Azul Neon
==========================================

EJECUTOR ESPECÍFICO DEL FRONTEND
Este archivo sirve únicamente los archivos estáticos del frontend
"""

import sys
import os
import time
import webbrowser
import threading
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver

def print_frontend_banner():
    """Banner del frontend"""
    banner = f"""
╔══════════════════════════════════════════════════════════════════════╗
║                    🎨 ECPlacas 2.0 - FRONTEND 🎨                   ║
║                                                                      ║
║  Servidor Estático para Frontend HTML/CSS/JS                       ║
║  Desarrollado por: Erick Costa                                      ║
║  Proyecto: Construcción de Software                                 ║
║  Versión: 2.0.1                                                     ║
║                                                                      ║
║  🎯 Solo Frontend - Servidor de Archivos Estáticos                 ║
╚══════════════════════════════════════════════════════════════════════╝
    """
    print(banner)

class ECPlacasFrontendHandler(SimpleHTTPRequestHandler):
    """Handler personalizado para el frontend de ECPlacas"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path.cwd() / "frontend"), **kwargs)
    
    def end_headers(self):
        # Agregar headers de seguridad
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY') 
        self.send_header('X-XSS-Protection', '1; mode=block')
        self.send_header('Cache-Control', 'public, max-age=86400')  # 24 horas
        super().end_headers()
    
    def do_GET(self):
        """Manejo de requests GET con fallbacks inteligentes"""
        
        # Si piden la raíz, servir index.html
        if self.path == '/':
            self.path = '/index.html'
        
        # Si piden admin sin extensión, servir admin.html
        elif self.path == '/admin':
            self.path = '/admin.html'
        
        # Agregar extensión .html si no tiene extensión
        elif '.' not in self.path.split('/')[-1] and not self.path.endswith('/'):
            self.path += '.html'
        
        try:
            return super().do_GET()
        except FileNotFoundError:
            # Si no encuentra el archivo, servir index.html (SPA fallback)
            self.path = '/index.html'
            return super().do_GET()
    
    def log_message(self, format, *args):
        """Log personalizado para requests"""
        print(f"🌐 {self.address_string()} - {format % args}")

def open_browser(url, delay=2):
    """Abrir navegador automáticamente con delay"""
    def delayed_open():
        time.sleep(delay)
        try:
            webbrowser.open(url)
            print(f"🌐 Navegador abierto: {url}")
        except Exception as e:
            print(f"⚠️ No se pudo abrir el navegador automáticamente: {e}")
            print(f"💡 Abra manualmente: {url}")
    
    threading.Thread(target=delayed_open, daemon=True).start()

def check_frontend_files():
    """Verificar que existan los archivos del frontend"""
    frontend_dir = Path.cwd() / "frontend"
    required_files = [
        "index.html"
    ]
    
    if not frontend_dir.exists():
        print("❌ Error: Directorio 'frontend' no encontrado")
        print("💡 Estructura esperada:")
        print("   proyecto/")
        print("   ├── run_frontend.py  (este archivo)")
        print("   └── frontend/")
        print("       ├── index.html")
        print("       ├── admin.html")
        print("       └── css/")
        return False
    
    missing_files = []
    for file in required_files:
        if not (frontend_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("❌ Archivos faltantes en frontend:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("✅ Archivos del frontend verificados")
    return True

def main():
    """Función principal para servir solo el frontend"""
    print_frontend_banner()
    
    # Verificar archivos del frontend
    if not check_frontend_files():
        return 1
    
    # Configuración del servidor
    HOST = '0.0.0.0'
    PORT = 8080
    
    try:
        # Cambiar al directorio del proyecto
        project_dir = Path.cwd()
        print(f"📁 Directorio del proyecto: {project_dir}")
        print(f"📁 Sirviendo desde: {project_dir / 'frontend'}")
        
        # Crear servidor HTTP
        with socketserver.TCPServer((HOST, PORT), ECPlacasFrontendHandler) as httpd:
            print("🚀 Iniciando servidor de frontend...")
            print("="*70)
            print("🎨 ECPlacas 2.0 FRONTEND - SERVIDOR INICIADO")
            print("="*70)
            print(f"🌐 Frontend disponible en: http://localhost:{PORT}")
            print(f"📱 Admin Panel: http://localhost:{PORT}/admin")
            print(f"📋 Archivos CSS: http://localhost:{PORT}/css/")
            print(f"📜 Archivos JS: http://localhost:{PORT}/js/")
            print("="*70)
            print("⚠️  NOTA: Este servidor SOLO sirve archivos estáticos")
            print("💡 Para funcionalidad completa, ejecute también el backend:")
            print("   python run_backend.py")
            print("   O use: python ECPlacas.py")
            print("="*70)
            print("🛑 Presione Ctrl+C para detener el servidor")
            print("="*70)
            
            # Abrir navegador automáticamente
            url = f"http://localhost:{PORT}"
            open_browser(url)
            
            # Iniciar servidor
            print("🎯 Servidor de frontend listo para recibir conexiones...")
            httpd.serve_forever()
            
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Error: Puerto {PORT} ya está en uso")
            print("💡 Posibles soluciones:")
            print(f"   1. Usar otro puerto: python run_frontend.py --port 8081")
            print(f"   2. Detener el proceso que usa el puerto {PORT}")
            print(f"   3. Esperar unos minutos y volver a intentar")
        else:
            print(f"❌ Error de red: {e}")
        return 1
    
    except KeyboardInterrupt:
        print("\n🛑 Servidor de frontend detenido por el usuario")
        return 0
    
    except Exception as e:
        print(f"❌ Error general: {e}")
        return 1

if __name__ == "__main__":
    import argparse
    
    # Argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='ECPlacas 2.0 Frontend Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host del servidor')
    parser.add_argument('--port', type=int, default=8080, help='Puerto del servidor')
    parser.add_argument('--no-browser', action='store_true', help='No abrir navegador automáticamente')
    
    args = parser.parse_args()
    
    # Usar argumentos personalizados si se proporcionan
    if len(sys.argv) > 1:
        try:
            # Modificar función main para usar argumentos
            def main_with_args():
                print_frontend_banner()
                
                if not check_frontend_files():
                    return 1
                
                HOST = args.host
                PORT = args.port
                
                try:
                    project_dir = Path.cwd()
                    print(f"📁 Directorio del proyecto: {project_dir}")
                    print(f"📁 Sirviendo desde: {project_dir / 'frontend'}")
                    
                    with socketserver.TCPServer((HOST, PORT), ECPlacasFrontendHandler) as httpd:
                        print("🚀 Iniciando servidor de frontend...")
                        print("="*70)
                        print("🎨 ECPlacas 2.0 FRONTEND - SERVIDOR INICIADO")
                        print("="*70)
                        print(f"🌐 Frontend disponible en: http://{HOST}:{PORT}")
                        print(f"📱 Admin Panel: http://{HOST}:{PORT}/admin")
                        print("="*70)
                        print("🛑 Presione Ctrl+C para detener el servidor")
                        print("="*70)
                        
                        if not args.no_browser:
                            url = f"http://localhost:{PORT}"
                            open_browser(url)
                        
                        print("🎯 Servidor de frontend listo para recibir conexiones...")
                        httpd.serve_forever()
                        
                except KeyboardInterrupt:
                    print("\n🛑 Servidor de frontend detenido por el usuario")
                    return 0
                except Exception as e:
                    print(f"❌ Error: {e}")
                    return 1
            
            sys.exit(main_with_args())
            
        except Exception as e:
            print(f"❌ Error procesando argumentos: {e}")
            sys.exit(1)
    else:
        sys.exit(main())