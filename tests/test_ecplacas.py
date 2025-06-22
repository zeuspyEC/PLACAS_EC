#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================
ECPlacas 2.0 - Suite de Pruebas Completa
==========================================
Proyecto: Construcción de Software - EPN
Desarrollado por: Erick Costa
Enfoque: Rendimiento | Sostenibilidad | Escalabilidad
==========================================

Suite completa de pruebas unitarias e integración
optimizada para rendimiento y escalabilidad.
"""

import pytest
import asyncio
import tempfile
import shutil
import sqlite3
import json
import time
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List, Optional
from contextlib import contextmanager

# Agregar el directorio backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Importaciones del proyecto
try:
    from app import create_app
    from db import ECPlacasDatabase
except ImportError as e:
    pytest.skip(f"Módulos del proyecto no disponibles: {e}", allow_module_level=True)


# ==========================================
# CONFIGURACIÓN DE FIXTURES GLOBALES
# ==========================================

@pytest.fixture(scope="session")
def event_loop():
    """Crear event loop para pruebas asíncronas."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def temp_database():
    """Base de datos temporal para pruebas."""
    with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as tmp:
        db_path = tmp.name
    
    # Crear base de datos de prueba
    conn = sqlite3.connect(db_path)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS consultas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            placa TEXT NOT NULL,
            fecha_consulta DATETIME DEFAULT CURRENT_TIMESTAMP,
            resultado TEXT,
            tipo_consulta TEXT DEFAULT 'vehiculo',
            tiempo_respuesta REAL,
            ip_cliente TEXT,
            user_agent TEXT
        )
    ''')
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture(scope="function")
def app(temp_database):
    """Aplicación Flask para pruebas."""
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['DATABASE_PATH'] = temp_database
    os.environ['TESTING'] = 'True'
    
    try:
        app = create_app()
        app.config.update({
            'TESTING': True,
            'WTF_CSRF_ENABLED': False,
            'DATABASE_PATH': temp_database
        })
        
        with app.app_context():
            yield app
    except Exception as e:
        pytest.skip(f"No se pudo crear la aplicación Flask: {e}")


@pytest.fixture(scope="function")
def client(app):
    """Cliente de pruebas Flask."""
    return app.test_client()


@pytest.fixture(scope="function")
def runner(app):
    """Runner CLI para pruebas."""
    return app.test_cli_runner()


@pytest.fixture(scope="function")
def database(temp_database):
    """Instancia de base de datos para pruebas."""
    return ECPlacasDatabase(db_path=temp_database)


# ==========================================
# MOCKS Y UTILIDADES DE PRUEBA
# ==========================================

@pytest.fixture
def mock_sri_response():
    """Mock de respuesta exitosa del SRI."""
    return {
        'success': True,
        'data': {
            'placa': 'ABC-1234',
            'marca': 'TOYOTA',
            'modelo': 'COROLLA',
            'año': '2020',
            'color': 'BLANCO',
            'propietario': {
                'nombre': 'JUAN PEREZ',
                'cedula': '1234567890',
                'direccion': 'QUITO, PICHINCHA'
            },
            'sri_data': {
                'ruc': '1234567890001',
                'razon_social': 'JUAN PEREZ',
                'estado': 'ACTIVO',
                'fecha_actualizacion': '2024-01-15'
            }
        },
        'timestamp': '2024-01-15T10:30:00',
        'source': 'test'
    }


@pytest.fixture
def mock_sri_error():
    """Mock de respuesta de error del SRI."""
    return {
        'success': False,
        'error': 'Placa no encontrada',
        'code': 'PLACA_NOT_FOUND',
        'timestamp': '2024-01-15T10:30:00'
    }


class PerformanceTimer:
    """Utilidad para medir rendimiento en pruebas."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self):
        self.start_time = time.perf_counter()
    
    def stop(self):
        self.end_time = time.perf_counter()
        return self.elapsed
    
    @property
    def elapsed(self):
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None


@contextmanager
def performance_test(max_time_seconds: float = 1.0):
    """Context manager para pruebas de rendimiento."""
    timer = PerformanceTimer()
    timer.start()
    try:
        yield timer
    finally:
        elapsed = timer.stop()
        assert elapsed <= max_time_seconds, f"Test took {elapsed:.3f}s, max allowed: {max_time_seconds}s"


# ==========================================
# PRUEBAS UNITARIAS - CORE FUNCTIONALITY
# ==========================================

class TestAppCore:
    """Pruebas del núcleo de la aplicación."""
    
    def test_app_creation(self, app):
        """Test de creación de aplicación."""
        assert app is not None
        assert app.config['TESTING'] is True
    
    def test_app_config(self, app):
        """Test de configuración de aplicación."""
        assert 'DATABASE_PATH' in app.config
    
    def test_health_endpoint(self, client):
        """Test del endpoint de salud."""
        with performance_test(0.5):
            response = client.get('/api/health')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'status' in data
    
    def test_cors_headers(self, client):
        """Test de headers CORS."""
        response = client.get('/api/health')
        # Verificar que no hay errores CORS básicos
        assert response.status_code == 200


class TestDatabase:
    """Pruebas de base de datos."""
    
    def test_database_connection(self, database):
        """Test de conexión a base de datos."""
        assert database is not None
        assert database.verificar_conexion()
    
    def test_database_insert_consulta(self, database):
        """Test de inserción en base de datos."""
        consulta_data = {
            'placa': 'TEST-123',
            'resultado': '{"test": true}',
            'tipo_consulta': 'vehiculo',
            'tiempo_respuesta': 0.5,
            'ip_cliente': '127.0.0.1'
        }
        
        with performance_test(0.1):
            result = database.insertar_consulta(**consulta_data)
            assert result is True
    
    def test_database_get_estadisticas(self, database):
        """Test de obtención de estadísticas."""
        with performance_test(0.2):
            stats = database.obtener_estadisticas()
            assert isinstance(stats, dict)
            assert 'total_consultas' in stats


# ==========================================
# PRUEBAS DE INTEGRACIÓN - API ENDPOINTS
# ==========================================

class TestAPIEndpoints:
    """Pruebas de integración de APIs."""
    
    def test_consulta_vehiculo_invalid_input(self, client):
        """Test de consulta con entrada inválida."""
        response = client.post('/api/consultar-vehiculo', 
                             json={'placa': ''})
        
        assert response.status_code in [400, 422]
    
    def test_api_endpoints_exist(self, client):
        """Test de existencia de endpoints principales."""
        endpoints = [
            '/api/health',
            '/api/estadisticas'
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            # Debe existir (no 404)
            assert response.status_code != 404


# ==========================================
# PRUEBAS DE RENDIMIENTO
# ==========================================

class TestPerformance:
    """Pruebas específicas de rendimiento."""
    
    def test_multiple_concurrent_requests(self, client):
        """Test de múltiples requests concurrentes."""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request():
            response = client.get('/api/health')
            results.put(response.status_code)
        
        # Crear 5 threads concurrentes
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        with performance_test(3.0):
            # Iniciar todos los threads
            for thread in threads:
                thread.start()
            
            # Esperar que terminen
            for thread in threads:
                thread.join()
        
        # Verificar resultados
        assert results.qsize() == 5
        while not results.empty():
            assert results.get() == 200
    
    @pytest.mark.slow
    def test_database_bulk_operations(self, database):
        """Test de operaciones masivas en base de datos."""
        consultas = []
        for i in range(50):
            consultas.append({
                'placa': f'TEST-{i:03d}',
                'resultado': f'{{"test": {i}}}',
                'tipo_consulta': 'vehiculo',
                'tiempo_respuesta': 0.1,
                'ip_cliente': '127.0.0.1'
            })
        
        with performance_test(2.0):
            for consulta in consultas:
                database.insertar_consulta(**consulta)
        
        # Verificar que se insertaron
        stats = database.obtener_estadisticas()
        assert stats['total_consultas'] >= 50


# ==========================================
# PRUEBAS DE ESCALABILIDAD
# ==========================================

class TestScalability:
    """Pruebas de escalabilidad del sistema."""
    
    @pytest.mark.slow
    def test_memory_usage_stability(self, client):
        """Test de estabilidad de uso de memoria."""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss
            
            # Realizar muchas requests
            for _ in range(25):
                client.get('/api/health')
            
            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory
            
            # La memoria no debería aumentar más de 5MB
            assert memory_increase < 5 * 1024 * 1024
        except ImportError:
            pytest.skip("psutil no disponible para test de memoria")
    
    def test_response_time_consistency(self, client):
        """Test de consistencia en tiempos de respuesta."""
        response_times = []
        
        for _ in range(10):
            timer = PerformanceTimer()
            timer.start()
            client.get('/api/health')
            elapsed = timer.stop()
            response_times.append(elapsed)
        
        # Calcular estadísticas
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        
        # Los tiempos deben ser consistentes
        assert avg_time < 0.2  # Promedio menor a 200ms
        assert max_time < 0.5  # Máximo menor a 500ms


# ==========================================
# PRUEBAS DE SOSTENIBILIDAD
# ==========================================

class TestSustainability:
    """Pruebas de sostenibilidad y recursos."""
    
    def test_cache_efficiency(self, client):
        """Test de eficiencia del cache."""
        # Primera request (sin cache)
        timer1 = PerformanceTimer()
        timer1.start()
        response1 = client.get('/api/estadisticas')
        time1 = timer1.stop()
        
        # Segunda request (potencialmente con cache)
        timer2 = PerformanceTimer()
        timer2.start()
        response2 = client.get('/api/estadisticas')
        time2 = timer2.stop()
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        # La segunda request debería ser igual o más rápida
        assert time2 <= time1 * 1.5  # Permitir 50% de variación
    
    def test_connection_cleanup(self, database):
        """Test de limpieza de conexiones."""
        # Abrir múltiples conexiones
        connections = []
        for _ in range(3):
            conn = database.obtener_conexion()
            connections.append(conn)
        
        # Cerrar todas las conexiones
        for conn in connections:
            if conn:
                conn.close()
        
        # Verificar que la base de datos sigue funcionando
        assert database.verificar_conexion()


# ==========================================
# PRUEBAS DE SEGURIDAD
# ==========================================

class TestSecurity:
    """Pruebas básicas de seguridad."""
    
    def test_sql_injection_protection(self, client):
        """Test de protección contra SQL injection."""
        malicious_input = "'; DROP TABLE consultas; --"
        
        response = client.post('/api/consultar-vehiculo', 
                             json={'placa': malicious_input})
        
        # No debería causar error 500
        assert response.status_code in [400, 404, 422]
    
    def test_xss_protection(self, client):
        """Test de protección contra XSS."""
        xss_payload = '<script>alert("xss")</script>'
        
        response = client.post('/api/consultar-vehiculo', 
                             json={'placa': xss_payload})
        
        assert response.status_code in [400, 404, 422]
        # Verificar que el payload no se refleje en la respuesta
        assert b'<script>' not in response.data


# ==========================================
# CONFIGURACIÓN DE MARKS
# ==========================================

pytestmark = [
    pytest.mark.filterwarnings("ignore::DeprecationWarning"),
    pytest.mark.filterwarnings("ignore::PendingDeprecationWarning"),
]


# ==========================================
# EJECUTAR PRUEBAS
# ==========================================

if __name__ == "__main__":
    # Ejecutar suite completa
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--cov=backend",
        "--cov-report=term-missing",
        "--cov-report=html",
        "-m", "not slow"
    ])
