@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ==========================================
REM ECPlacas 2.0 - Script de Automatización Windows
REM Proyecto: Construcción de Software - EPN
REM Desarrollado por: Erick Costa
REM Enfoque: Rendimiento | Sostenibilidad | Escalabilidad
REM ==========================================

title ECPlacas 2.0 - Automatización EPN

echo ========================================
echo ECPlacas 2.0 - Sistema de Automatización
echo Escuela Politécnica Nacional
echo Desarrollado por: Erick Costa
echo Fecha: %date% %time%
echo ========================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no está instalado o no está en PATH
    echo Por favor instala Python 3.8+ desde https://python.org
    pause
    exit /b 1
)

REM Verificar si estamos en el directorio correcto
if not exist "ECPlacas.py" (
    echo [ERROR] No se encuentra ECPlacas.py
    echo Por favor ejecuta este script desde el directorio raíz del proyecto
    pause
    exit /b 1
)

:MENU
cls
echo ========================================
echo ECPlacas 2.0 - Menu Principal
echo ========================================
echo.
echo 1. Ejecutar TODAS las tareas del examen
echo 2. Solo Compilación
echo 3. Solo Linting
echo 4. Solo Pruebas
echo 5. Solo Docker
echo 6. Configurar entorno
echo 7. Ver reportes
echo 8. Limpiar proyecto
echo 9. Salir
echo.
set /p choice="Selecciona una opción (1-9): "

if "%choice%"=="1" goto ALL_TASKS
if "%choice%"=="2" goto COMPILE_ONLY
if "%choice%"=="3" goto LINT_ONLY
if "%choice%"=="4" goto TEST_ONLY
if "%choice%"=="5" goto DOCKER_ONLY
if "%choice%"=="6" goto SETUP_ENV
if "%choice%"=="7" goto VIEW_REPORTS
if "%choice%"=="8" goto CLEAN_PROJECT
if "%choice%"=="9" goto EXIT

echo [ERROR] Opción inválida. Por favor selecciona 1-9.
pause
goto MENU

:ALL_TASKS
echo.
echo [INFO] Ejecutando TODAS las tareas del examen...
python scripts/run_exam_tasks.py --all
goto SHOW_RESULTS

:COMPILE_ONLY
echo.
echo [INFO] Ejecutando solo compilación...
python scripts/run_exam_tasks.py --compile
goto SHOW_RESULTS

:LINT_ONLY
echo.
echo [INFO] Ejecutando solo linting...
python scripts/run_exam_tasks.py --lint
goto SHOW_RESULTS

:TEST_ONLY
echo.
echo [INFO] Ejecutando solo pruebas...
python scripts/run_exam_tasks.py --test
goto SHOW_RESULTS

:DOCKER_ONLY
echo.
echo [INFO] Ejecutando solo Docker...
python scripts/run_exam_tasks.py --docker
goto SHOW_RESULTS

:SETUP_ENV
echo.
echo [INFO] Configurando entorno de desarrollo...
echo [INFO] Verificando entorno virtual...

if not exist "venv\" (
    echo [INFO] Creando entorno virtual...
    python -m venv venv
)

echo [INFO] Activando entorno virtual...
call venv\Scripts\activate.bat

echo [INFO] Actualizando pip...
python -m pip install --upgrade pip

echo [INFO] Instalando dependencias...
pip install -r requirements.txt

echo [SUCCESS] Entorno configurado correctamente
pause
goto MENU

:VIEW_REPORTS
echo.
echo [INFO] Abriendo reportes...

if exist "htmlcov\index.html" (
    echo [INFO] Abriendo reporte de cobertura...
    start htmlcov\index.html
)

for %%f in (automation_report_*.json) do (
    echo [INFO] Reporte encontrado: %%f
)

if exist "flake8-report.txt" (
    echo [INFO] Mostrando reporte de linting...
    type flake8-report.txt
)

pause
goto MENU

:CLEAN_PROJECT
echo.
echo [WARNING] Esto eliminará archivos temporales y cache
set /p confirm="¿Estás seguro? (S/N): "

if /i "%confirm%"=="S" (
    echo [INFO] Limpiando proyecto...
    
    if exist "__pycache__" rmdir /s /q __pycache__
    if exist ".pytest_cache" rmdir /s /q .pytest_cache
    if exist "htmlcov" rmdir /s /q htmlcov
    if exist ".coverage" del .coverage
    if exist "coverage.xml" del coverage.xml
    if exist "flake8-report.txt" del flake8-report.txt
    del automation_report_*.json 2>nul
    
    echo [SUCCESS] Proyecto limpiado
) else (
    echo [INFO] Operación cancelada
)

pause
goto MENU

:SHOW_RESULTS
echo.
echo ========================================
echo Ejecución completada
echo ========================================
echo.
echo [INFO] Revisa los logs arriba para ver los resultados
echo [INFO] Los reportes se han guardado en el directorio del proyecto
echo.

REM Buscar el reporte más reciente
for /f "delims=" %%f in ('dir /b /od automation_report_*.json 2^>nul') do set latest_report=%%f

if defined latest_report (
    echo [INFO] Reporte más reciente: %latest_report%
)

echo.
set /p view_report="¿Quieres ver el reporte de cobertura? (S/N): "
if /i "%view_report%"=="S" (
    if exist "htmlcov\index.html" (
        start htmlcov\index.html
    ) else (
        echo [WARNING] Reporte de cobertura no encontrado
    )
)

echo.
set /p return_menu="¿Volver al menú principal? (S/N): "
if /i "%return_menu%"=="S" goto MENU

:EXIT
echo.
echo ========================================
echo Gracias por usar ECPlacas 2.0
echo Desarrollado por: Erick Costa
echo Escuela Politécnica Nacional
echo ========================================
echo.
pause
exit /b 0