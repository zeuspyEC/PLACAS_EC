"""
Configuración de fixtures globales para pytest
ECPlacas 2.0 - Construcción de Software - EPN
"""

import pytest
import os
import tempfile
import sqlite3
from pathlib import Path


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Configurar entorno de pruebas global."""
    # Configurar variables de entorno para tests
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['TESTING'] = 'True'
    os.environ['WTF_CSRF_ENABLED'] = 'False'
    
    yield
    
    # Cleanup después de todas las pruebas
    test_env_vars = ['FLASK_ENV', 'TESTING', 'WTF_CSRF_ENABLED', 'DATABASE_PATH']
    for var in test_env_vars:
        os.environ.pop(var, None)


@pytest.fixture(scope="session")
def test_data_dir():
    """Directorio temporal para datos de prueba."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_consulta_data():
    """Datos de ejemplo para pruebas de consultas."""
    return {
        'placa': 'ABC-1234',
        'tipo_consulta': 'vehiculo',
        'ip_cliente': '127.0.0.1',
        'user_agent': 'pytest-test-agent/1.0',
        'resultado': '{"success": true, "test": true}'
    }


@pytest.fixture
def mock_api_response():
    """Mock de respuesta de API externa."""
    return {
        'success': True,
        'data': {
            'placa': 'ABC-1234',
            'marca': 'TOYOTA',
            'modelo': 'COROLLA',
            'año': '2020',
            'color': 'BLANCO'
        },
        'timestamp': '2024-06-21T10:30:00',
        'source': 'test_mock'
    }


# Configuración de pytest-asyncio
pytest_plugins = ['pytest_asyncio']
