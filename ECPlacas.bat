@echo off
chcp 65001 >nul
title ECPlacas 2.0 - Sistema de Consulta Vehicular

:: ==========================================
:: ECPlacas 2.0 - Lanzador Windows
:: Proyecto: Construcción de Software
:: Desarrollado por: Erick Costa
:: Temática: Futurista - Azul Neon
:: ==========================================

color 09
echo.
echo ╔══════════════════════════════════════════════════════════════════════╗
echo ║                         🚀 ECPlacas 2.0 🚀                         ║
echo ║                                                                      ║
echo ║  Sistema de Consulta Vehicular - Temática Futurista                ║
echo ║  Desarrollado por: Erick Costa                                      ║
echo ║  Proyecto: Construcción de Software                                 ║
echo ║                                                                      ║
echo ║  💻 Enfoque: Rendimiento ^| Sostenibilidad ^| Escalabilidad          ║
echo ╚══════════════════════════════════════════════════════════════════════╝
echo.

:: Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no encontrado. Instala Python 3.8+ desde python.org
    pause
    exit /b 1
)

:: Verificar si ECPlacas.py existe
if not exist "ECPlacas.py" (
    echo ❌ ECPlacas.py no encontrado en el directorio actual
    echo 💡 Asegúrate de ejecutar este archivo desde la carpeta del proyecto
    pause
    exit /b 1
)

:: Ejecutar ECPlacas.py
echo 🚀 Iniciando ECPlacas 2.0...
echo.
python ECPlacas.py %*

:: Mantener ventana abierta si hay error
if errorlevel 1 (
    echo.
    echo ❌ Error ejecutando ECPlacas 2.0
    echo 💡 Revisa los mensajes de error arriba
    pause
)