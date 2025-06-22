@echo off
chcp 65001 >nul
title ECPlacas 2.0 - Automatización Completa EPN

:: ==========================================
:: ECPlacas 2.0 - Script de Automatización Completa
:: Proyecto: Construcción de Software - EPN
:: Desarrollado por: Erick Costa
:: Enfoque: Rendimiento | Sostenibilidad | Escalabilidad
:: ==========================================

setlocal EnableDelayedExpansion
color 0B

echo.
echo ╔══════════════════════════════════════════════════════════════════════╗
echo ║                    🚀 ECPlacas 2.0 - EPN 🚀                        ║
echo ║                                                                      ║
echo ║  Automatización Completa de Tareas del Examen                      ║
echo ║  Escuela Politécnica Nacional                                       ║
echo ║  Desarrollado por: Erick Costa                                      ║
echo ║  Construcción de Software - Junio 2025                            ║
echo ║                                                                      ║
echo ║  💻 Enfoque: Rendimiento ^| Sostenibilidad ^| Escalabilidad          ║
echo ║  🔥 Script de Automatización Python                                ║
echo ╚══════════════════════════════════════════════════════════════════════╝
echo.

:: Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no encontrado. Instala Python 3.8+ desde python.org
    pause
    exit /b 1
)

echo ✅ Python detectado

:: Verificar estructura del proyecto
if not exist "scripts\run_exam_tasks.py" (
    echo ❌ Script de automatización no encontrado
    echo 💡 Asegúrate de ejecutar desde el directorio del proyecto
    pause
    exit /b 1
)

echo ✅ Script de automatización encontrado

:menu
cls
echo.
echo ╔══════════════════════════════════════════════════════════════════════╗
echo ║               🎓 MENÚ DE AUTOMATIZACIÓN - EPN                      ║
echo ╚══════════════════════════════════════════════════════════════════════╝
echo.
echo 🔧 Tareas del Examen Disponibles:
echo.
echo    1. 🔨 Compilación del Proyecto
echo    2. 🔍 Análisis de Código (Linting)
echo    3. 🧪 Pruebas Unitarias e Integración
echo    4. 🐳 Build de Docker
echo    5. 🚀 TODAS LAS TAREAS AUTOMÁTICAS
echo    6. 🌟 TODO EXCEPTO DOCKER
echo.
echo 📊 Opciones Adicionales:
echo.
echo    7. ⚙️  Configurar Entorno de Desarrollo
echo    8. 📄 Ver Último Reporte
echo    9. 🧹 Limpiar Archivos Temporales
echo    0. ❌ Salir
echo.
set /p choice=💭 Selecciona una opción (0-9): 

if "%choice%"=="1" goto :compile
if "%choice%"=="2" goto :lint
if "%choice%"=="3" goto :test
if "%choice%"=="4" goto :docker
if "%choice%"=="5" goto :all_tasks
if "%choice%"=="6" goto :all_no_docker
if "%choice%"=="7" goto :setup_env
if "%choice%"=="8" goto :view_report
if "%choice%"=="9" goto :cleanup
if "%choice%"=="0" goto :exit
echo ⚠️ Opción inválida. Presiona cualquier tecla para continuar...
pause >nul
goto :menu

:compile
cls
echo.
echo ╔══════════════════════════════════════════════════════════════════════╗
echo ║                      🔨 COMPILACIÓN                                ║
echo ╚══════════════════════════════════════════════════════════════════════╝
echo.
echo 🔨 Ejecutando compilación del proyecto...
echo.
python scripts\run_exam_tasks.py --compile
echo.
echo ✅ Compilación completada. Presiona cualquier tecla para continuar...
pause >nul
goto :menu

:lint
cls
echo.
echo ╔══════════════════════════════════════════════════════════════════════╗
echo ║                    🔍 ANÁLISIS DE CÓDIGO                           ║
echo ╚══════════════════════════════════════════════════════════════════════╝
echo.
echo 🔍 Ejecutando análisis de código (linting)...
echo.
python scripts\run_exam_tasks.py --lint
echo.
echo ✅ Linting completado. Presiona cualquier tecla para continuar...
pause >nul
goto :menu

:test
cls
echo.
echo ╔══════════════════════════════════════════════════════════════════════╗
echo ║               🧪 PRUEBAS UNITARIAS E INTEGRACIÓN                   ║
echo ╚══════════════════════════════════════════════════════════════════════╝
echo.
echo 🧪 Ejecutando suite completa de pruebas...
echo.
python scripts\run_exam_tasks.py --test
echo.
echo ✅ Pruebas completadas. Presiona cualquier tecla para continuar...
pause >nul
goto :menu

:docker
cls
echo.
echo ╔══════════════════════════════════════════════════════════════════════╗
echo ║                       🐳 BUILD DOCKER                              ║
echo ╚══════════════════════════════════════════════════════════════════════╝
echo.
echo 🐳 Ejecutando build de imagen Docker...
echo.
python scripts\run_exam_tasks.py --docker
echo.
echo ✅ Docker build completado. Presiona cualquier tecla para continuar...
pause >nul
goto :menu

:all_tasks
cls
echo.
echo ╔══════════════════════════════════════════════════════════════════════╗
echo ║              🚀 AUTOMATIZACIÓN COMPLETA - EPN                      ║
echo ╚══════════════════════════════════════════════════════════════════════╝
echo.
echo 🚀 Ejecutando TODAS las tareas del examen automáticamente...
echo.
echo 📋 Tareas a ejecutar:
echo    ✓ 1. Compilación
echo    ✓ 2. Linting
echo    ✓ 3. Pruebas
echo    ✓ 4. Docker Build
echo.
echo ⏱️ Esto puede tomar varios minutos...
echo.
python scripts\run_exam_tasks.py --all
echo.
echo 🎉 ¡Automatización completa finalizada!
echo 📊 Revisa el reporte generado para ver los resultados detallados.
echo.
pause
goto :menu

:all_no_docker
cls
echo.
echo ╔══════════════════════════════════════════════════════════════════════╗
echo ║            🌟 AUTOMATIZACIÓN SIN DOCKER - EPN                      ║
echo ╚══════════════════════════════════════════════════════════════════════╝
echo.
echo 🌟 Ejecutando todas las tareas EXCEPTO Docker...
echo.
echo 📋 Tareas a ejecutar:
echo    ✓ 1. Compilación
echo    ✓ 2. Linting
echo    ✓ 3. Pruebas
echo    ⏭️ 4. Docker Build (omitido)
echo.
python scripts\run_exam_tasks.py --no-docker
echo.
echo 🎉 ¡Automatización (sin Docker) finalizada!
echo.
pause
goto :menu

:setup_env
cls
echo.
echo ╔══════════════════════════════════════════════════════════════════════╗
echo ║               ⚙️ CONFIGURAR ENTORNO                                ║
echo ╚══════════════════════════════════════════════════════════════════════╝
echo.
echo ⚙️ Configurando entorno de desarrollo...
echo.
echo 📦 Instalando dependencias...
python -m pip install --upgrade pip
if exist "requirements.txt" (
    python -m pip install -r requirements.txt
)
echo.
echo 🔧 Instalando herramientas de desarrollo...
python -m pip install pytest pytest-cov flake8 black isort mypy bandit
echo.
echo ✅ Entorno configurado correctamente.
pause
goto :menu

:view_report
cls
echo.
echo ╔══════════════════════════════════════════════════════════════════════╗
echo ║                    📄 ÚLTIMO REPORTE                               ║
echo ╚══════════════════════════════════════════════════════════════════════╝
echo.
echo 📄 Buscando último reporte de automatización...
echo.

:: Buscar el archivo de reporte más reciente
set "latest_report="
for /f "delims=" %%i in ('dir "automation_report_*.json" /b /o-d 2^>nul') do (
    set "latest_report=%%i"
    goto :found_report
)

:found_report
if "%latest_report%"=="" (
    echo ⚠️ No se encontraron reportes de automatización.
    echo 💡 Ejecuta primero la automatización para generar un reporte.
) else (
    echo 📊 Último reporte encontrado: %latest_report%
    echo.
    echo 📈 Mostrando resumen del reporte...
    echo.
    type "%latest_report%" | findstr /i "overall_score compilation_success linting_score testing_success docker_success coverage_percentage"
    echo.
    echo 💡 Para ver el reporte completo, abre: %latest_report%
)
echo.
pause
goto :menu

:cleanup
cls
echo.
echo ╔══════════════════════════════════════════════════════════════════════╗
echo ║                    🧹 LIMPIAR ARCHIVOS                             ║
echo ╚══════════════════════════════════════════════════════════════════════╝
echo.
echo 🧹 Limpiando archivos temporales...
echo.

:: Limpiar cache de Python
if exist "__pycache__" (
    echo 🗑️ Eliminando cache de Python...
    rmdir /s /q __pycache__ 2>nul
)

:: Limpiar cache de pytest
if exist ".pytest_cache" (
    echo 🗑️ Eliminando cache de pytest...
    rmdir /s /q .pytest_cache 2>nul
)

:: Limpiar cache de mypy
if exist ".mypy_cache" (
    echo 🗑️ Eliminando cache de mypy...
    rmdir /s /q .mypy_cache 2>nul
)

:: Limpiar archivos de coverage antiguos
if exist "htmlcov" (
    echo 🗑️ Eliminando reportes de coverage antiguos...
    rmdir /s /q htmlcov 2>nul
)

if exist "coverage.xml" (
    del coverage.xml 2>nul
)

:: Limpiar reportes antiguos (mantener los 3 más recientes)
echo 🗑️ Limpiando reportes antiguos...
for /f "skip=3 delims=" %%i in ('dir "automation_report_*.json" /b /o-d 2^>nul') do (
    del "%%i" 2>nul
)

echo.
echo ✅ Limpieza completada.
pause
goto :menu

:exit
cls
echo.
echo ╔══════════════════════════════════════════════════════════════════════╗
echo ║                       👋 HASTA LUEGO                               ║
echo ╚══════════════════════════════════════════════════════════════════════╝
echo.
echo 🎓 ECPlacas 2.0 - Escuela Politécnica Nacional
echo 💻 Desarrollado por: Erick Costa
echo 📚 Construcción de Software - Junio 2025
echo.
echo 🚀 ¡Gracias por usar el sistema de automatización!
echo 📧 Para soporte: erick.costa@epn.edu.ec
echo.
echo ✨ ¡Éxito en tus estudios! ✨
echo.
timeout /t 3 /nobreak >nul
exit /b 0

:: ==========================================
:: ERROR HANDLERS
:: ==========================================
:error
echo.
echo ❌ Se produjo un error durante la ejecución.
echo 💡 Verifica los logs para más detalles.
echo.
pause
goto :menu