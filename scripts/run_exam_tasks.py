#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================
ECPlacas 2.0 - Script de Automatización Completa
==========================================
Proyecto: Construcción de Software - EPN
Desarrollado por: Erick Costa
Enfoque: Rendimiento | Sostenibilidad | Escalabilidad
==========================================

Script que automatiza todas las tareas del examen:
- Compilación
- Linting
- Pruebas unitarias e integración
- Build de Docker
- Documentación
"""

import os
import sys
import subprocess
import time
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Colores para output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'

def print_banner():
    """Mostrar banner del proyecto."""
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════════════╗
║                    🚀 ECPlacas 2.0 - EPN 🚀                        ║
║                                                                      ║
║  Sistema de Consulta Vehicular - Construcción de Software          ║
║  Escuela Politécnica Nacional                                       ║
║  Desarrollado por: Erick Costa                                      ║
║  Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}                           ║
║                                                                      ║
║  💻 Enfoque: Rendimiento | Sostenibilidad | Escalabilidad          ║
║  🔥 Script de Automatización Completa                              ║
╚══════════════════════════════════════════════════════════════════════╝
{Colors.RESET}
    """
    print(banner)

def log_step(step: str, status: str = "INFO"):
    """Log de pasos con colores."""
    timestamp = datetime.now().strftime('%H:%M:%S')
    colors = {
        "INFO": Colors.BLUE,
        "SUCCESS": Colors.GREEN,
        "WARNING": Colors.YELLOW,
        "ERROR": Colors.RED,
        "RUNNING": Colors.CYAN
    }
    color = colors.get(status, Colors.WHITE)
    print(f"{color}[{timestamp}] {status}: {step}{Colors.RESET}")

def run_command(command: List[str], description: str, cwd: Optional[Path] = None) -> Dict[str, Any]:
    """Ejecutar comando con logging detallado."""
    log_step(f"Ejecutando: {description}", "RUNNING")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False  # No lanzar excepción automáticamente
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode == 0:
            log_step(f"✅ {description} completado en {duration:.2f}s", "SUCCESS")
            return {
                "success": True,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration": duration
            }
        else:
            log_step(f"❌ {description} falló (código: {result.returncode})", "ERROR")
            if result.stderr:
                print(f"{Colors.RED}Error output:{Colors.RESET}")
                print(result.stderr)
            return {
                "success": False,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration": duration
            }
            
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        log_step(f"❌ Error ejecutando {description}: {e}", "ERROR")
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
            "duration": duration
        }

class ECPlacasAutomation:
    """Clase principal de automatización."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results = {}
        self.start_time = datetime.now()
        
        # Verificar que estamos en el directorio correcto
        if not (project_root / "backend" / "app.py").exists():
            raise FileNotFoundError("No se encontró la estructura del proyecto ECPlacas")
    
    def setup_environment(self) -> bool:
        """Configurar entorno de desarrollo."""
        log_step("Configurando entorno de desarrollo", "INFO")
        
        # Verificar Python
        python_check = run_command(
            [sys.executable, "--version"],
            "Verificar versión de Python"
        )
        
        if not python_check["success"]:
            return False
        
        # Instalar/actualizar dependencias
        deps_install = run_command(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            "Instalar dependencias",
            self.project_root
        )
        
        # Instalar dependencias de desarrollo
        dev_deps_install = run_command(
            [sys.executable, "-m", "pip", "install", 
             "pytest", "pytest-cov", "flake8", "black", "isort", "mypy"],
            "Instalar dependencias de desarrollo",
            self.project_root
        )
        
        self.results["environment_setup"] = {
            "python_check": python_check,
            "dependencies": deps_install,
            "dev_dependencies": dev_deps_install
        }
        
        return all([
            python_check["success"],
            deps_install["success"],
            dev_deps_install["success"]
        ])
    
    def compile_project(self) -> bool:
        """Compilar el proyecto (verificar sintaxis Python)."""
        log_step("🔨 Iniciando compilación del proyecto", "INFO")
        
        # Compilar backend
        backend_compile = run_command(
            [sys.executable, "-m", "py_compile", "backend/app.py"],
            "Compilar backend/app.py",
            self.project_root
        )
        
        # Compilar otros módulos importantes
        modules_to_compile = [
            "backend/db.py",
            "backend/utils.py",
            "ECPlacas.py"
        ]
        
        compile_results = [backend_compile]
        
        for module in modules_to_compile:
            if (self.project_root / module).exists():
                result = run_command(
                    [sys.executable, "-m", "py_compile", module],
                    f"Compilar {module}",
                    self.project_root
                )
                compile_results.append(result)
        
        # Verificar imports
        import_check = run_command(
            [sys.executable, "-c", 
             "import sys; sys.path.insert(0, 'backend'); import app; print('✅ Imports OK')"],
            "Verificar imports del proyecto",
            self.project_root
        )
        compile_results.append(import_check)
        
        all_success = all(result["success"] for result in compile_results)
        
        self.results["compilation"] = {
            "backend_compile": backend_compile,
            "modules_compiled": compile_results[1:-1],
            "import_check": import_check,
            "overall_success": all_success
        }
        
        if all_success:
            log_step("✅ Compilación completada exitosamente", "SUCCESS")
        else:
            log_step("❌ Errores en la compilación", "ERROR")
        
        return all_success
    
    def run_linting(self) -> bool:
        """Ejecutar análisis de código (linting)."""
        log_step("🔍 Iniciando análisis de código (linting)", "INFO")
        
        # Flake8
        flake8_result = run_command(
            [sys.executable, "-m", "flake8", "backend/", "--config=.flake8"],
            "Análisis con Flake8",
            self.project_root
        )
        
        # Black (formateo)
        black_result = run_command(
            [sys.executable, "-m", "black", "--check", "--diff", "backend/"],
            "Verificar formateo con Black",
            self.project_root
        )
        
        # isort (imports)
        isort_result = run_command(
            [sys.executable, "-m", "isort", "--check-only", "--diff", "backend/"],
            "Verificar imports con isort",
            self.project_root
        )
        
        # Crear reporte de linting
        linting_score = 0
        total_checks = 3
        
        if flake8_result["success"]:
            linting_score += 1
        if black_result["success"]:
            linting_score += 1
        if isort_result["success"]:
            linting_score += 1
        
        linting_percentage = (linting_score / total_checks) * 100
        
        self.results["linting"] = {
            "flake8": flake8_result,
            "black": black_result,
            "isort": isort_result,
            "score": linting_score,
            "total": total_checks,
            "percentage": linting_percentage
        }
        
        if linting_score == total_checks:
            log_step(f"✅ Linting completado: {linting_percentage:.1f}% ({linting_score}/{total_checks})", "SUCCESS")
            return True
        else:
            log_step(f"⚠️ Linting con advertencias: {linting_percentage:.1f}% ({linting_score}/{total_checks})", "WARNING")
            return False
    
    def run_tests(self) -> bool:
        """Ejecutar pruebas unitarias e integración."""
        log_step("🧪 Iniciando suite de pruebas", "INFO")
        
        # Pruebas unitarias
        unit_tests = run_command(
            [sys.executable, "-m", "pytest", "tests/", "-v", 
             "--tb=short", "--cov=backend", "--cov-report=term-missing", 
             "--cov-report=html:htmlcov", "--cov-report=xml",
             "-m", "not slow"],
            "Ejecutar pruebas unitarias",
            self.project_root
        )
        
        # Pruebas de integración (si existen)
        integration_tests = run_command(
            [sys.executable, "-m", "pytest", "tests/", "-v",
             "-m", "integration", "--tb=short"],
            "Ejecutar pruebas de integración",
            self.project_root
        )
        
        # Pruebas de rendimiento (limitadas)
        performance_tests = run_command(
            [sys.executable, "-m", "pytest", "tests/", "-v",
             "-k", "performance", "--tb=short", "-x"],
            "Ejecutar pruebas de rendimiento",
            self.project_root
        )
        
        # Calcular coverage si está disponible
        coverage_percentage = 0
        if unit_tests["success"] and "coverage.xml" in os.listdir(self.project_root):
            try:
                # Intentar extraer coverage del output
                if "%" in unit_tests["stdout"]:
                    for line in unit_tests["stdout"].split("\\n"):
                        if "TOTAL" in line and "%" in line:
                            coverage_percentage = float(line.split("%")[0].split()[-1])
                            break
            except:
                coverage_percentage = 0
        
        tests_passed = unit_tests["success"]
        
        self.results["testing"] = {
            "unit_tests": unit_tests,
            "integration_tests": integration_tests,
            "performance_tests": performance_tests,
            "coverage_percentage": coverage_percentage,
            "overall_success": tests_passed
        }
        
        if tests_passed:
            log_step(f"✅ Pruebas completadas - Coverage: {coverage_percentage:.1f}%", "SUCCESS")
        else:
            log_step("❌ Algunas pruebas fallaron", "ERROR")
        
        return tests_passed
    
    def build_docker(self) -> bool:
        """Construir imagen Docker."""
        log_step("🐳 Iniciando build de Docker", "INFO")
        
        # Verificar que Docker está disponible
        docker_check = run_command(
            ["docker", "--version"],
            "Verificar Docker"
        )
        
        if not docker_check["success"]:
            log_step("⚠️ Docker no disponible, saltando build", "WARNING")
            self.results["docker"] = {
                "docker_available": False,
                "reason": "Docker no encontrado"
            }
            return False
        
        # Build de la imagen
        build_args = [
            "--build-arg", f"BUILD_DATE={datetime.now().isoformat()}",
            "--build-arg", f"VERSION=2.0.1",
            "--build-arg", f"VCS_REF=local-build"
        ]
        
        docker_build = run_command(
            ["docker", "build"] + build_args + ["-t", "ecplacas-epn:2.0.1", "."],
            "Build imagen Docker",
            self.project_root
        )
        
        # Test básico de la imagen
        docker_test = {"success": False}
        if docker_build["success"]:
            docker_test = run_command(
                ["docker", "run", "--rm", "ecplacas-epn:2.0.1", "/app/healthcheck.sh"],
                "Test básico imagen Docker"
            )
        
        self.results["docker"] = {
            "docker_available": True,
            "build": docker_build,
            "test": docker_test,
            "overall_success": docker_build["success"]
        }
        
        if docker_build["success"]:
            log_step("✅ Imagen Docker construida exitosamente", "SUCCESS")
        else:
            log_step("❌ Error construyendo imagen Docker", "ERROR")
        
        return docker_build["success"]
    
    def generate_report(self) -> Dict[str, Any]:
        """Generar reporte completo de ejecución."""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        # Calcular score general
        scores = []
        if "compilation" in self.results:
            scores.append(1 if self.results["compilation"]["overall_success"] else 0)
        if "linting" in self.results:
            scores.append(self.results["linting"]["percentage"] / 100)
        if "testing" in self.results:
            scores.append(1 if self.results["testing"]["overall_success"] else 0)
        if "docker" in self.results:
            scores.append(1 if self.results["docker"]["overall_success"] else 0)
        
        overall_score = (sum(scores) / len(scores)) * 100 if scores else 0
        
        report = {
            "project": "ECPlacas 2.0",
            "university": "Escuela Politécnica Nacional",
            "student": "Erick Costa",
            "execution": {
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": total_duration
            },
            "results": self.results,
            "summary": {
                "overall_score": overall_score,
                "compilation_success": self.results.get("compilation", {}).get("overall_success", False),
                "linting_score": self.results.get("linting", {}).get("percentage", 0),
                "testing_success": self.results.get("testing", {}).get("overall_success", False),
                "docker_success": self.results.get("docker", {}).get("overall_success", False),
                "coverage_percentage": self.results.get("testing", {}).get("coverage_percentage", 0)
            }
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any]) -> None:
        """Guardar reporte en archivo JSON."""
        report_file = self.project_root / f"automation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        log_step(f"📄 Reporte guardado en: {report_file}", "SUCCESS")
    
    def print_summary(self, report: Dict[str, Any]) -> None:
        """Imprimir resumen final."""
        summary = report["summary"]
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}📊 RESUMEN DE EJECUCIÓN{Colors.RESET}")
        print("=" * 70)
        
        # Score general
        score_color = Colors.GREEN if summary["overall_score"] >= 80 else Colors.YELLOW if summary["overall_score"] >= 60 else Colors.RED
        print(f"🎯 Score General: {score_color}{summary['overall_score']:.1f}%{Colors.RESET}")
        
        # Resultados individuales
        results = [
            ("🔨 Compilación", summary["compilation_success"]),
            ("🔍 Linting", f"{summary['linting_score']:.1f}%"),
            ("🧪 Pruebas", summary["testing_success"]),
            ("🐳 Docker", summary["docker_success"]),
        ]
        
        for name, result in results:
            if isinstance(result, bool):
                color = Colors.GREEN if result else Colors.RED
                status = "✅ PASS" if result else "❌ FAIL"
            else:
                try:
                    percentage = float(str(result).replace('%', ''))
                    color = Colors.GREEN if percentage >= 80 else Colors.YELLOW if percentage >= 60 else Colors.RED
                    status = result
                except:
                    color = Colors.YELLOW
                    status = result
            
            print(f"{name}: {color}{status}{Colors.RESET}")
        
        # Métricas adicionales
        if summary["coverage_percentage"] > 0:
            cov_color = Colors.GREEN if summary["coverage_percentage"] >= 80 else Colors.YELLOW
            print(f"📈 Cobertura de Código: {cov_color}{summary['coverage_percentage']:.1f}%{Colors.RESET}")
        
        print(f"⏱️ Tiempo Total: {Colors.CYAN}{report['execution']['duration_seconds']:.2f} segundos{Colors.RESET}")
        print("=" * 70)


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Script de automatización completa para ECPlacas 2.0 - EPN"
    )
    parser.add_argument("--all", action="store_true", help="Ejecutar todas las tareas")
    parser.add_argument("--compile", action="store_true", help="Solo compilación")
    parser.add_argument("--lint", action="store_true", help="Solo linting")
    parser.add_argument("--test", action="store_true", help="Solo pruebas")
    parser.add_argument("--docker", action="store_true", help="Solo Docker build")
    parser.add_argument("--no-docker", action="store_true", help="Ejecutar todo excepto Docker")
    
    args = parser.parse_args()
    
    # Si no se especifica nada, ejecutar todo
    if not any([args.compile, args.lint, args.test, args.docker, args.no_docker]):
        args.all = True
    
    print_banner()
    
    # Detectar directorio del proyecto
    current_dir = Path.cwd()
    project_root = current_dir
    
    # Buscar el directorio raíz del proyecto
    while project_root.parent != project_root:
        if (project_root / "backend" / "app.py").exists():
            break
        project_root = project_root.parent
    else:
        log_step("❌ No se encontró el directorio del proyecto ECPlacas", "ERROR")
        sys.exit(1)
    
    log_step(f"📁 Directorio del proyecto: {project_root}", "INFO")
    
    try:
        automation = ECPlacasAutomation(project_root)
        
        # Configurar entorno
        if not automation.setup_environment():
            log_step("❌ Error configurando entorno", "ERROR")
            sys.exit(1)
        
        # Ejecutar tareas seleccionadas
        success = True
        
        if args.all or args.compile:
            success &= automation.compile_project()
        
        if args.all or args.lint:
            success &= automation.run_linting()
        
        if args.all or args.test:
            success &= automation.run_tests()
        
        if (args.all or args.docker) and not args.no_docker:
            success &= automation.build_docker()
        
        # Generar y mostrar reporte
        report = automation.generate_report()
        automation.save_report(report)
        automation.print_summary(report)
        
        if success:
            log_step("🎉 Todas las tareas completadas exitosamente", "SUCCESS")
            sys.exit(0)
        else:
            log_step("⚠️ Algunas tareas completadas con errores", "WARNING")
            sys.exit(1)
    
    except Exception as e:
        log_step(f"❌ Error inesperado: {e}", "ERROR")
        sys.exit(1)


if __name__ == "__main__":
    main()
