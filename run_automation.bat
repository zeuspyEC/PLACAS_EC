@echo off
chcp 65001 >nul
title ECPlacas 2.0 - Automatización Completa - EPN

:: ==========================================
:: ECPlacas 2.0 - Script de Automatización Windows
:: Proyecto: Construcción de Software - EPN
:: Desarrollado por: Erick Costa
:: ==========================================

setlocal EnableDelayedExpansion
color 09

echo.
echo ╔══════════════════════════════════════════════════════════════════════╗
echo ║                    🚀 ECPlacas 2.0 - EPN 🚀                        ║
echo ║                                                                      ║
echo ║  Automatización Completa - Construcción de Software                ║
echo ║  Escuela Politécnica Nacional                                       ║
echo ║  Desarrollado por: Erick Costa                                      ║
echo ║                                                                      ║
echo ║  💻 Tareas del Examen: Compilar | Lint | Tests | Docker            ║
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
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo 🐍 Versión: %PYTHON_VERSION%

:: Verificar que estamos en el directorio correcto
if not exist "backend\app.py" (
    echo ❌ No se encontró backend\app.py
    echo 💡 Ejecuta este script desde el directorio raíz del proyecto ECPlacas
    pause
    exit /b 1
)

echo ✅ Estructura del proyecto verificada

:: Mostrar menú de opciones
:menu
cls
echo.
echo 📋 SELECCIONA LAS TAREAS A EJECUTAR:
echo.
echo 1. 🔥 EJECUTAR TODO (Examen Completo)
echo 2. 🔨 Solo Compilación
echo 3. 🔍 Solo Linting
echo 4. 🧪 Solo Pruebas
echo 5. 🐳 Solo Docker Build
echo 6. ⚡ Todo excepto Docker
echo 7. 📊 Ver último reporte
echo 8. 🧹 Limpiar archivos temporales
echo 9. ❓ Ayuda
echo 0. 🚪 Salir
echo.

set /p choice="Selecciona una opción (0-9): "

if "%choice%"=="1" goto :run_all
if "%choice%"=="2" goto :run_compile
if "%choice%"=="3" goto :run_lint
if "%choice%"=="4" goto :run_test
if "%choice%"=="5" goto :run_docker
if "%choice%"=="6" goto :run_no_docker
if "%choice%"=="7" goto :show_report
if "%choice%"=="8" goto :cleanup
if "%choice%"=="9" goto :help
if "%choice%"=="0" goto :exit

echo ❌ Opción inválida
timeout /t 2 >nul
goto :menu

:: ==========================================
:: EJECUCIONES
:: ==========================================

:run_all
echo.
echo 🔥 EJECUTANDO TODAS LAS TAREAS DEL EXAMEN...
echo ════════════════════════════════════════════
echo.
python scripts/run_exam_tasks.py --all
if errorlevel 1 (
    echo.
    echo ❌ Error en la ejecución completa
    pause
) else (
    echo.
    echo 🎉 Todas las tareas completadas exitosamente
    pause
)
goto :menu

:run_compile
echo.
echo 🔨 EJECUTANDO SOLO COMPILACIÓN...
echo ═══════════════════════════════════
echo.
python scripts/run_exam_tasks.py --compile
pause
goto :menu

:run_lint
echo.
echo 🔍 EJECUTANDO SOLO LINTING...
echo ════════════════════════════════
echo.
python scripts/run_exam_tasks.py --lint
pause
goto :menu

:run_test
echo.
echo 🧪 EJECUTANDO SOLO PRUEBAS...
echo ═══════════════════════════════
echo.
python scripts/run_exam_tasks.py --test
pause
goto :menu

:run_docker
echo.
echo 🐳 EJECUTANDO SOLO DOCKER BUILD...
echo ═════════════════════════════════════
echo.
python scripts/run_exam_tasks.py --docker
pause
goto :menu

:run_no_docker
echo.
echo ⚡ EJECUTANDO TODO EXCEPTO DOCKER...
echo ══════════════════════════════════════
echo.
python scripts/run_exam_tasks.py --no-docker
pause
goto :menu

:show_report
echo.
echo 📊 ÚLTIMO REPORTE DE EJECUCIÓN:
echo ═══════════════════════════════════
echo.

:: Buscar el último reporte JSON
for /f "delims=" %%i in ('dir /b /o-d automation_report_*.json 2^>nul') do (
    set "latest_report=%%i"
    goto :found_report
)

echo ⚠️ No se encontraron reportes previos
pause
goto :menu

:found_report
echo 📄 Archivo: %latest_report%
echo.
python -c "import json; data=json.load(open('%latest_report%')); print('🎯 Score General:', f\"{data['summary']['overall_score']:.1f}%%\"); print('🔨 Compilación:', '✅ PASS' if data['summary']['compilation_success'] else '❌ FAIL'); print('🔍 Linting:', f\"{data['summary']['linting_score']:.1f}%%\"); print('🧪 Pruebas:', '✅ PASS' if data['summary']['testing_success'] else '❌ FAIL'); print('🐳 Docker:', '✅ PASS' if data['summary']['docker_success'] else '❌ FAIL')"
echo.
pause
goto :menu

:cleanup
echo.
echo 🧹 LIMPIANDO ARCHIVOS TEMPORALES...
echo ══════════════════════════════════════
echo.

:: Limpiar cache Python
if exist "__pycache__" (
    rmdir /s /q __pycache__
    echo ✅ Removido __pycache__
)

if exist "backend\__pycache__" (
    rmdir /s /q backend\__pycache__
    echo ✅ Removido backend\__pycache__
)

if exist "tests\__pycache__" (
    rmdir /s /q tests\__pycache__
    echo ✅ Removido tests\__pycache__
)

:: Limpiar archivos de cobertura
if exist "htmlcov" (
    rmdir /s /q htmlcov
    echo ✅ Removido htmlcov
)

if exist "coverage.xml" (
    del coverage.xml
    echo ✅ Removido coverage.xml
)

if exist ".coverage" (
    del .coverage
    echo ✅ Removido .coverage
)

:: Limpiar archivos de linting
if exist "flake8-report.txt" (
    del flake8-report.txt
    echo ✅ Removido flake8-report.txt
)

:: Limpiar reportes antiguos (mantener últimos 5)
echo 🗂️ Limpiando reportes antiguos...
for /f "skip=5 delims=" %%i in ('dir /b /o-d automation_report_*.json 2^>nul') do (
    del "%%i"
    echo ✅ Removido %%i
)

echo.
echo ✅ Limpieza completada
pause
goto :menu

:help
echo.
echo ❓ AYUDA - ECPlacas 2.0 Automatización
echo ════════════════════════════════════════
echo.
echo Este script automatiza todas las tareas del examen:
echo.
echo 🔨 COMPILACIÓN:
echo    - Verifica sintaxis Python
echo    - Compila módulos principales
echo    - Verifica imports
echo.
echo 🔍 LINTING:
echo    - Análisis con Flake8
echo    - Verificación de formato con Black
echo    - Organización de imports con isort
echo.
echo 🧪 PRUEBAS:
echo    - Pruebas unitarias con pytest
echo    - Pruebas de integración
echo    - Cobertura de código
echo    - Pruebas de rendimiento
echo.
echo 🐳 DOCKER:
echo    - Build de imagen optimizada
echo    - Test básico de la imagen
echo    - Verificación de health check
echo.
echo 📊 REPORTES:
echo    - Genera reportes JSON detallados
echo    - Métricas de rendimiento
echo    - Scores de calidad
echo.
echo 💡 CONSEJOS:
echo    - Ejecuta "Todo" para el examen completo
echo    - Revisa los reportes para métricas detalladas
echo    - Usa la limpieza periódicamente
echo.
pause
goto :menu

:exit
echo.
echo 👋 Gracias por usar ECPlacas 2.0 Automatización
echo 🎓 Escuela Politécnica Nacional
echo 👨‍💻 Desarrollado por: Erick Costa
echo.
pause
exit /b 0

:: ==========================================
:: FUNCIONES AUXILIARES
:: ==========================================

:check_dependencies
echo 🔍 Verificando dependencias...

:: Verificar pip
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip no encontrado
    exit /b 1
)

:: Verificar pytest
python -c "import pytest" >nul 2>&1
if errorlevel 1 (
    echo ⚠️ pytest no encontrado, instalando...
    python -m pip install pytest pytest-cov
)

:: Verificar flake8
python -c "import flake8" >nul 2>&1
if errorlevel 1 (
    echo ⚠️ flake8 no encontrado, instalando...
    python -m pip install flake8
)

echo ✅ Dependencias verificadas
exit /b 0
