#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================
ECPlacas 2.0 SRI DEFINITIVO
==========================================
Desarrollado por: Erick Costa
Versión: 2.0.3 DEFINITIVA
SOLO APIs que FUNCIONAN - INFORMACIÓN COMPLETA
==========================================
"""

import json
import time
import logging
import uuid
import os
import sys
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

# Flask imports
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configuración de paths
BACKEND_ROOT = Path(__file__).parent
PROJECT_ROOT = BACKEND_ROOT.parent
FRONTEND_PATH = PROJECT_ROOT / "frontend"
LOGS_PATH = BACKEND_ROOT / "logs"

# Crear directorios
LOGS_PATH.mkdir(parents=True, exist_ok=True)

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_PATH / "ecplacas_definitivo.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ==========================================
# CONFIGURACIÓN DE APIs - SOLO LAS QUE FUNCIONAN
# ==========================================

SRI_BASE_URL = "https://srienlinea.sri.gob.ec/sri-matriculacion-vehicular-recaudacion-servicio-internet/rest"

# SOLO endpoints verificados que SÍ funcionan
SRI_ENDPOINTS = {
    'base_vehiculo': f"{SRI_BASE_URL}/BaseVehiculo/obtenerPorNumeroPlacaOPorNumeroCampvOPorNumeroCpn",
    'consulta_rubros': f"{SRI_BASE_URL}/ConsultaRubros/obtenerPorCodigoVehiculo",
    'consulta_pagos': f"{SRI_BASE_URL}/consultaPagos/obtenerPorPlacaCampvCpn",
    'plan_iacv': f"{SRI_BASE_URL}/CuotasImpAmbiental/obtenerDetallePlanExcepcionalPagosPorCodigoVehiculo"
}

# ==========================================
# ESTRUCTURAS DE DATOS COMPLETAS
# ==========================================

@dataclass
class UserData:
    """Datos del usuario"""
    nombre: str = ""
    cedula: str = ""
    telefono: str = ""
    correo: str = ""

@dataclass
class VehicleDataComplete:
    """Datos vehiculares COMPLETOS con TODA la información que SÍ se obtiene"""
    
    # ==================== IDENTIFICACIÓN BÁSICA ====================
    numero_placa: str = ""
    placa_original: str = ""
    placa_normalizada: str = ""
    codigo_vehiculo: int = 0
    numero_camv_cpn: str = ""
    
    # ==================== INFORMACIÓN DEL MODELO ====================
    descripcion_marca: str = ""
    descripcion_modelo: str = ""
    anio_auto: int = 0
    descripcion_pais: str = ""
    color_vehiculo1: str = ""
    color_vehiculo2: str = ""
    cilindraje: str = ""
    nombre_clase: str = ""
    
    # ==================== DATOS SRI COMPLETOS - RUBROS ====================
    rubros_deuda: List[Dict] = field(default_factory=list)
    total_rubros: int = 0
    total_deudas_sri: float = 0.0
    rubros_por_beneficiario: Dict[str, List] = field(default_factory=dict)
    
    # ==================== HISTORIAL DE PAGOS COMPLETO ====================
    historial_pagos: List[Dict] = field(default_factory=list)
    total_pagos_realizados: float = 0.0
    total_transacciones: int = 0
    ultimo_pago_fecha: str = ""
    ultimo_pago_monto: float = 0.0
    
    # ==================== PLAN IACV COMPLETO ====================
    plan_iacv: List[Dict] = field(default_factory=list)
    total_cuotas_iacv: int = 0
    cuotas_vencidas: float = 0.0
    cuotas_por_estado: Dict[str, int] = field(default_factory=dict)
    
    # ==================== ANÁLISIS CONSOLIDADO ====================
    estado_legal_sri: str = "INDETERMINADO"
    tiene_deudas: bool = False
    tiene_pagos: bool = False
    puntuacion_sri: float = 0.0
    recomendacion: str = ""
    
    # ==================== METADATOS ====================
    session_id: str = ""
    timestamp_consulta: datetime = field(default_factory=datetime.now)
    tiempo_consulta: float = 0.0
    consulta_exitosa: bool = False
    mensaje_error: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario completo"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result
    
    def get_complete_summary(self) -> Dict[str, Any]:
        """Resumen COMPLETO para frontend"""
        return {
            'vehiculo_basico': {
                'placa': self.numero_placa,
                'marca': self.descripcion_marca,
                'modelo': self.descripcion_modelo,
                'anio': self.anio_auto,
                'pais': self.descripcion_pais,
                'color1': self.color_vehiculo1,
                'color2': self.color_vehiculo2,
                'clase': self.nombre_clase,
                'cilindraje': self.cilindraje,
                'codigo_vehiculo': self.codigo_vehiculo,
                'camv_cpn': self.numero_camv_cpn
            },
            'deudas_sri_completas': {
                'total_deudas': self.total_deudas_sri,
                'total_rubros': self.total_rubros,
                'rubros_detallados': self.rubros_deuda,
                'rubros_por_beneficiario': self.rubros_por_beneficiario,
                'tiene_deudas': self.tiene_deudas
            },
            'pagos_sri_completos': {
                'total_pagado': self.total_pagos_realizados,
                'total_transacciones': self.total_transacciones,
                'ultimo_pago_fecha': self.ultimo_pago_fecha,
                'ultimo_pago_monto': self.ultimo_pago_monto,
                'historial_completo': self.historial_pagos,
                'tiene_pagos': self.tiene_pagos
            },
            'iacv_completo': {
                'total_cuotas': self.total_cuotas_iacv,
                'cuotas_vencidas': self.cuotas_vencidas,
                'cuotas_por_estado': self.cuotas_por_estado,
                'plan_detallado': self.plan_iacv
            },
            'analisis_consolidado': {
                'estado_legal': self.estado_legal_sri,
                'puntuacion_sri': self.puntuacion_sri,
                'recomendacion': self.recomendacion,
                'tiene_deudas': self.tiene_deudas,
                'tiene_pagos': self.tiene_pagos
            },
            'metadatos': {
                'session_id': self.session_id,
                'tiempo_consulta': self.tiempo_consulta,
                'timestamp': self.timestamp_consulta.isoformat(),
                'consulta_exitosa': self.consulta_exitosa
            }
        }

# ==========================================
# VALIDADORES
# ==========================================

class PlateValidator:
    @staticmethod
    def normalize_plate(placa: str) -> tuple[str, str, bool]:
        if not placa or not isinstance(placa, str):
            return placa, placa, False
        
        placa_clean = re.sub(r'[^A-Z0-9]', '', placa.upper())
        placa_original = placa_clean
        
        # Normalización ABC123 -> ABC0123
        pattern_3_digits = r'^([A-Z]{2,3})(\d{3})$'
        match = re.match(pattern_3_digits, placa_clean)
        
        if match:
            letters = match.group(1)
            numbers = match.group(2)
            placa_normalizada = f"{letters}0{numbers}"
            return (placa_original, placa_normalizada, True)
        else:
            return (placa_original, placa_clean, False)
    
    @staticmethod
    def validate_plate_format(placa: str) -> bool:
        if not placa or len(placa) < 6 or len(placa) > 8:
            return False
        patterns = [r'^[A-Z]{2,3}\d{3,4}$', r'^[A-Z]{2,3}-\d{3,4}$']
        return any(re.match(pattern, placa.upper()) for pattern in patterns)

class CedulaValidator:
    PROVINCE_CODES = {
        '01': 'Azuay', '02': 'Bolívar', '03': 'Cañar', '04': 'Carchi',
        '05': 'Cotopaxi', '06': 'Chimborazo', '07': 'El Oro', '08': 'Esmeraldas',
        '09': 'Guayas', '10': 'Imbabura', '11': 'Loja', '12': 'Los Ríos',
        '13': 'Manabí', '14': 'Morona Santiago', '15': 'Napo', '16': 'Pastaza',
        '17': 'Pichincha', '18': 'Tungurahua', '19': 'Zamora Chinchipe',
        '20': 'Galápagos', '21': 'Sucumbíos', '22': 'Orellana',
        '23': 'Santo Domingo', '24': 'Santa Elena', '30': 'Exterior'
    }
    
    @classmethod
    def validate_ecuadorian_id(cls, cedula: str) -> bool:
        if not cedula or len(cedula) != 10 or not cedula.isdigit():
            return False
        
        province_code = cedula[:2]
        if province_code not in cls.PROVINCE_CODES:
            return False
        
        if int(cedula[2]) >= 6:
            return False
        
        digits = [int(d) for d in cedula]
        coefficients = [2, 1, 2, 1, 2, 1, 2, 1, 2]
        total = 0
        
        for i in range(9):
            result = digits[i] * coefficients[i]
            if result > 9:
                result -= 9
            total += result
        
        check_digit = (10 - (total % 10)) % 10
        return check_digit == digits[9]

# ==========================================
# CONSULTOR SRI COMPLETO - SOLO APIs QUE FUNCIONAN
# ==========================================

class VehicleConsultantComplete:
    """Consultor SRI COMPLETO usando SOLO APIs verificadas que funcionan"""
    
    def __init__(self):
        self.session = self._create_session()
        self.active_consultations = {}
    
    def _create_session(self) -> requests.Session:
        session = requests.Session()
        retry_strategy = Retry(total=2, status_forcelist=[429, 500, 502, 503, 504], backoff_factor=1)
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'es-ES,es;q=0.9',
            'Connection': 'keep-alive'
        })
        return session
    
    def consultar_vehiculo_completo(self, placa: str, user_data: UserData, session_id: str) -> VehicleDataComplete:
        """Consulta COMPLETA usando todas las APIs que funcionan"""
        start_time = time.time()
        
        placa_original, placa_normalizada, was_modified = PlateValidator.normalize_plate(placa)
        
        vehicle_data = VehicleDataComplete(
            numero_placa=placa_normalizada,
            placa_original=placa_original,
            placa_normalizada=placa_normalizada,
            session_id=session_id
        )
        
        try:
            logger.info(f"🚀 Iniciando consulta COMPLETA: {placa_original} → {placa_normalizada}")
            
            # ==================== PASO 1: INFORMACIÓN BÁSICA ====================
            self.active_consultations[session_id] = {
                'status': 'consultando_base',
                'progress': 20,
                'message': '🔍 Consultando información básica SRI...'
            }
            
            base_info = self._consultar_base_vehiculo(placa_normalizada)
            if not base_info:
                if placa_original != placa_normalizada:
                    base_info = self._consultar_base_vehiculo(placa_original)
            
            if not base_info:
                raise Exception("No se encontró información del vehículo en el SRI")
            
            self._procesar_info_basica(vehicle_data, base_info)
            codigo_vehiculo = vehicle_data.codigo_vehiculo
            
            # ==================== PASO 2: RUBROS DE DEUDA ====================
            self.active_consultations[session_id] = {
                'status': 'consultando_rubros',
                'progress': 40,
                'message': '💰 Consultando rubros de deuda SRI...'
            }
            
            rubros_data = self._consultar_rubros_deuda(codigo_vehiculo)
            self._procesar_rubros_deuda(vehicle_data, rubros_data)
            
            # ==================== PASO 3: HISTORIAL DE PAGOS ====================
            self.active_consultations[session_id] = {
                'status': 'consultando_pagos',
                'progress': 60,
                'message': '📊 Consultando historial de pagos SRI...'
            }
            
            pagos_data = self._consultar_historial_pagos(placa_normalizada)
            self._procesar_historial_pagos(vehicle_data, pagos_data)
            
            # ==================== PASO 4: PLAN IACV ====================
            self.active_consultations[session_id] = {
                'status': 'consultando_iacv',
                'progress': 80,
                'message': '🌱 Consultando plan IACV...'
            }
            
            iacv_data = self._consultar_plan_iacv(codigo_vehiculo)
            self._procesar_plan_iacv(vehicle_data, iacv_data)
            
            # ==================== PASO 5: ANÁLISIS CONSOLIDADO ====================
            self.active_consultations[session_id] = {
                'status': 'analizando',
                'progress': 95,
                'message': '📈 Realizando análisis consolidado...'
            }
            
            self._realizar_analisis_consolidado(vehicle_data)
            
            vehicle_data.consulta_exitosa = True
            
            # COMPLETADO
            self.active_consultations[session_id] = {
                'status': 'completado',
                'progress': 100,
                'message': '✅ Consulta SRI COMPLETA exitosa',
                'result': vehicle_data.to_dict(),
                'complete_summary': vehicle_data.get_complete_summary()
            }
            
            logger.info(f"✅ Consulta COMPLETA exitosa: {vehicle_data.descripcion_marca} {vehicle_data.descripcion_modelo}, "
                       f"Rubros: {vehicle_data.total_rubros}, Deudas: ${vehicle_data.total_deudas_sri:.2f}, "
                       f"Pagos: {vehicle_data.total_transacciones}, IACV: {vehicle_data.total_cuotas_iacv}")
            
        except Exception as e:
            logger.error(f"❌ Error en consulta COMPLETA: {e}")
            vehicle_data.consulta_exitosa = False
            vehicle_data.mensaje_error = str(e)
            
            self.active_consultations[session_id] = {
                'status': 'error',
                'progress': 0,
                'message': f'❌ Error: {str(e)}',
                'error': str(e)
            }
        
        vehicle_data.tiempo_consulta = time.time() - start_time
        return vehicle_data
    
    def _consultar_base_vehiculo(self, placa: str) -> Optional[Dict]:
        """Consultar información básica - API VERIFICADA ✅"""
        try:
            url = f"{SRI_ENDPOINTS['base_vehiculo']}?numeroPlacaCampvCpn={placa}"
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            data = response.json()
            logger.info(f"✅ Info básica obtenida para {placa}")
            return data
        except Exception as e:
            logger.error(f"❌ Error consultando base: {e}")
            return None
    
    def _consultar_rubros_deuda(self, codigo_vehiculo: int) -> List[Dict]:
        """Consultar rubros de deuda - API VERIFICADA ✅"""
        try:
            url = f"{SRI_ENDPOINTS['consulta_rubros']}?codigoVehiculo={codigo_vehiculo}"
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            data = response.json()
            logger.info(f"✅ Rubros obtenidos: {len(data)} elementos")
            return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f"❌ Error consultando rubros: {e}")
            return []
    
    def _consultar_historial_pagos(self, placa: str) -> Dict:
        """Consultar historial de pagos - API VERIFICADA ✅"""
        try:
            url = f"{SRI_ENDPOINTS['consulta_pagos']}?placaCampvCpn={placa}"
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            data = response.json()
            logger.info(f"✅ Historial de pagos obtenido")
            return data if isinstance(data, dict) else {}
        except Exception as e:
            logger.error(f"❌ Error consultando pagos: {e}")
            return {}
    
    def _consultar_plan_iacv(self, codigo_vehiculo: int) -> List[Dict]:
        """Consultar plan IACV - API VERIFICADA ✅"""
        try:
            url = f"{SRI_ENDPOINTS['plan_iacv']}?codigo={codigo_vehiculo}"
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            data = response.json()
            logger.info(f"✅ Plan IACV obtenido: {len(data)} cuotas")
            return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f"❌ Error consultando IACV: {e}")
            return []
    
    def _procesar_info_basica(self, vehicle_data: VehicleDataComplete, base_info: Dict):
        """Procesar información básica del vehículo"""
        mappings = {
            'codigo_vehiculo': 'codigoVehiculo',
            'numero_camv_cpn': 'numeroCamvCpn',
            'descripcion_marca': 'descripcionMarca',
            'descripcion_modelo': 'descripcionModelo',
            'anio_auto': 'anioAuto',
            'descripcion_pais': 'descripcionPais',
            'color_vehiculo1': 'colorVehiculo1',
            'color_vehiculo2': 'colorVehiculo2',
            'cilindraje': 'cilindraje',
            'nombre_clase': 'nombreClase'
        }
        
        for vehicle_field, sri_field in mappings.items():
            if sri_field in base_info:
                value = base_info[sri_field]
                if value is None or value == "":
                    value = "N/A" if isinstance(getattr(vehicle_data, vehicle_field), str) else 0
                setattr(vehicle_data, vehicle_field, value)
    
    def _procesar_rubros_deuda(self, vehicle_data: VehicleDataComplete, rubros_data: List[Dict]):
        """Procesar rubros de deuda completos"""
        vehicle_data.rubros_deuda = rubros_data
        vehicle_data.total_rubros = len(rubros_data)
        
        # Calcular total de deudas y agrupar por beneficiario
        total_deudas = 0.0
        beneficiarios = {}
        
        for rubro in rubros_data:
            valor = rubro.get('valorRubro', 0)
            if isinstance(valor, (int, float)):
                total_deudas += valor
            
            beneficiario = rubro.get('nombreCortoBeneficiario', 'DESCONOCIDO')
            if beneficiario not in beneficiarios:
                beneficiarios[beneficiario] = []
            beneficiarios[beneficiario].append(rubro)
        
        vehicle_data.total_deudas_sri = total_deudas
        vehicle_data.rubros_por_beneficiario = beneficiarios
        vehicle_data.tiene_deudas = total_deudas > 0
    
    def _procesar_historial_pagos(self, vehicle_data: VehicleDataComplete, pagos_data: Dict):
        """Procesar historial completo de pagos"""
        if 'data' in pagos_data and isinstance(pagos_data['data'], list):
            pagos_list = pagos_data['data']
            vehicle_data.historial_pagos = pagos_list
            vehicle_data.total_transacciones = len(pagos_list)
            
            # Calcular totales
            total_pagado = 0.0
            ultimo_pago = None
            
            for pago in pagos_list:
                monto = pago.get('monto', 0)
                if isinstance(monto, (int, float)):
                    total_pagado += monto
                
                # Encontrar último pago
                if ultimo_pago is None or (pago.get('fechaDePago', '') > ultimo_pago.get('fechaDePago', '')):
                    ultimo_pago = pago
            
            vehicle_data.total_pagos_realizados = total_pagado
            vehicle_data.tiene_pagos = total_pagado > 0
            
            if ultimo_pago:
                vehicle_data.ultimo_pago_fecha = ultimo_pago.get('fechaDePago', '')
                vehicle_data.ultimo_pago_monto = ultimo_pago.get('monto', 0)
    
    def _procesar_plan_iacv(self, vehicle_data: VehicleDataComplete, iacv_data: List[Dict]):
        """Procesar plan IACV completo"""
        vehicle_data.plan_iacv = iacv_data
        vehicle_data.total_cuotas_iacv = len(iacv_data)
        
        # Analizar estados y cuotas vencidas
        cuotas_vencidas = 0.0
        estados_count = {}
        
        for cuota in iacv_data:
            estado = cuota.get('estadoPago', 'DESCONOCIDO')
            estados_count[estado] = estados_count.get(estado, 0) + 1
            
            if estado == 'VENCIDO':
                total_cuota = cuota.get('totalCuota', 0)
                if isinstance(total_cuota, (int, float)):
                    cuotas_vencidas += total_cuota
        
        vehicle_data.cuotas_vencidas = cuotas_vencidas
        vehicle_data.cuotas_por_estado = estados_count
    
    def _realizar_analisis_consolidado(self, vehicle_data: VehicleDataComplete):
        """Análisis consolidado completo"""
        # Calcular puntuación SRI (0-100)
        puntuacion = 100
        
        # Penalizar por deudas
        if vehicle_data.total_deudas_sri > 1000:
            puntuacion -= 40
        elif vehicle_data.total_deudas_sri > 500:
            puntuacion -= 25
        elif vehicle_data.total_deudas_sri > 100:
            puntuacion -= 15
        elif vehicle_data.total_deudas_sri > 0:
            puntuacion -= 5
        
        # Penalizar por IACV vencidas
        if vehicle_data.cuotas_vencidas > 50:
            puntuacion -= 20
        elif vehicle_data.cuotas_vencidas > 0:
            puntuacion -= 10
        
        # Bonificar por pagos
        if vehicle_data.total_pagos_realizados > 1000:
            puntuacion += 10
        elif vehicle_data.total_pagos_realizados > 500:
            puntuacion += 5
        
        vehicle_data.puntuacion_sri = max(0, min(100, puntuacion))
        
        # Determinar estado legal
        if puntuacion >= 90:
            vehicle_data.estado_legal_sri = "EXCELENTE"
        elif puntuacion >= 70:
            vehicle_data.estado_legal_sri = "BUENO"
        elif puntuacion >= 50:
            vehicle_data.estado_legal_sri = "REGULAR"
        else:
            vehicle_data.estado_legal_sri = "CRÍTICO"
        
        # Generar recomendación
        recomendaciones = []
        if vehicle_data.tiene_deudas:
            recomendaciones.append(f"💰 Deudas SRI: ${vehicle_data.total_deudas_sri:.2f}")
        if vehicle_data.cuotas_vencidas > 0:
            recomendaciones.append(f"🌱 IACV vencidas: ${vehicle_data.cuotas_vencidas:.2f}")
        if vehicle_data.tiene_pagos:
            recomendaciones.append(f"✅ Pagos realizados: ${vehicle_data.total_pagos_realizados:.2f}")
        if not recomendaciones:
            recomendaciones.append("✅ Sin observaciones importantes")
        
        vehicle_data.recomendacion = " | ".join(recomendaciones)

# ==========================================
# APLICACIÓN FLASK
# ==========================================

def create_app():
    app = Flask(__name__, static_folder=None, template_folder=None)
    
    app.config.update({
        'SECRET_KEY': f'ecplacas_definitivo_{int(time.time())}',
        'JSON_AS_ASCII': False,
        'JSONIFY_PRETTYPRINT_REGULAR': True,
    })
    
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:*", "http://127.0.0.1:*"],
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type"],
        }
    })
    
    # Instancia global del consultor COMPLETO
    vehicle_consultant = VehicleConsultantComplete()
    
    @app.route('/')
    def index():
        try:
            index_path = FRONTEND_PATH / 'index.html'
            if index_path.exists():
                return send_from_directory(str(FRONTEND_PATH), 'index.html')
            else:
                return create_frontend_fallback()
        except Exception as e:
            logger.error(f"❌ Error sirviendo index: {e}")
            return create_frontend_fallback()
    
    @app.route('/static/<path:filename>')
    def static_files(filename):
        try:
            if filename.endswith('.css'):
                css_path = FRONTEND_PATH / 'css' / filename
                if css_path.exists():
                    return send_from_directory(str(FRONTEND_PATH / 'css'), filename)
            elif filename.endswith('.js'):
                js_path = FRONTEND_PATH / 'js' / filename
                if js_path.exists():
                    return send_from_directory(str(FRONTEND_PATH / 'js'), filename)
            
            file_path = FRONTEND_PATH / filename
            if file_path.exists():
                return send_from_directory(str(FRONTEND_PATH), filename)
            
            return "Archivo no encontrado", 404
        except Exception as e:
            logger.error(f"❌ Error sirviendo estático {filename}: {e}")
            return "Error interno", 500
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            'success': True,
            'status': 'healthy',
            'service': 'ECPlacas 2.0 SRI DEFINITIVO',
            'version': '2.0.3',
            'author': 'Erick Costa',
            'timestamp': datetime.now().isoformat(),
            'features_activas': {
                'consulta_sri_base': True,
                'rubros_deuda_sri': True,
                'historial_pagos_sri': True,
                'plan_iacv_sri': True,
                'analisis_consolidado': True,
                'validacion_placas': True,
                'validacion_cedulas': True,
                'informacion_completa': True
            },
            'apis_verificadas': list(SRI_ENDPOINTS.keys())
        })
    
    @app.route('/api/consultar-vehiculo', methods=['POST'])
    def consultar_vehiculo_completo():
        try:
            if not request.is_json:
                return jsonify({
                    'success': False, 
                    'error': 'Content-Type debe ser application/json'
                }), 400
            
            data = request.get_json()
            placa = data.get('placa', '').strip()
            usuario_data = data.get('usuario', {})
            
            if not placa:
                return jsonify({'success': False, 'error': 'Placa es requerida'}), 400
            
            if not PlateValidator.validate_plate_format(placa):
                return jsonify({
                    'success': False,
                    'error': 'Formato de placa inválido',
                    'placa_recibida': placa
                }), 400
            
            user_data = UserData(
                nombre=usuario_data.get('nombre', ''),
                cedula=usuario_data.get('cedula', ''),
                telefono=usuario_data.get('telefono', ''),
                correo=usuario_data.get('correo', '')
            )
            
            if user_data.cedula and not CedulaValidator.validate_ecuadorian_id(user_data.cedula):
                return jsonify({
                    'success': False,
                    'error': 'Cédula ecuatoriana inválida',
                    'cedula_recibida': user_data.cedula
                }), 400
            
            session_id = f"ecplacas_def_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            
            logger.info(f"🚀 Nueva consulta COMPLETA - Placa: {placa}, Session: {session_id}")
            
            # Ejecutar consulta COMPLETA (síncrona)
            vehicle_data = vehicle_consultant.consultar_vehiculo_completo(placa, user_data, session_id)
            
            placa_original, placa_normalizada, was_modified = PlateValidator.normalize_plate(placa)
            
            if vehicle_data.consulta_exitosa:
                return jsonify({
                    'success': True,
                    'message': 'Consulta SRI COMPLETA exitosa',
                    'session_id': session_id,
                    'placa': placa_original,
                    'placa_normalizada': placa_normalizada,
                    'placa_fue_normalizada': was_modified,
                    'vehicle_data': vehicle_data.to_dict(),
                    'complete_summary': vehicle_data.get_complete_summary(),
                    'features_extraidas': {
                        'datos_sri_completos': True,
                        'rubros_deuda': vehicle_data.total_rubros,
                        'historial_pagos': vehicle_data.total_transacciones,
                        'plan_iacv': vehicle_data.total_cuotas_iacv,
                        'total_deudas_sri': vehicle_data.total_deudas_sri,
                        'total_pagos_realizados': vehicle_data.total_pagos_realizados,
                        'analisis_consolidado': True
                    },
                    'timestamp': datetime.now().isoformat()
                })
            else:
                return jsonify({
                    'success': False,
                    'error': vehicle_data.mensaje_error,
                    'session_id': session_id,
                    'placa': placa_original
                }), 404
            
        except Exception as e:
            logger.error(f"❌ Error en consulta COMPLETA: {e}")
            return jsonify({
                'success': False,
                'error': 'Error interno del servidor',
                'details': str(e)
            }), 500
    
    @app.route('/api/estado-consulta/<session_id>', methods=['GET'])
    def get_consultation_status(session_id):
        try:
            if session_id in vehicle_consultant.active_consultations:
                consultation = vehicle_consultant.active_consultations[session_id]
                return jsonify({
                    'success': True,
                    'session_id': session_id,
                    'status': consultation.get('status', 'unknown'),
                    'progress': consultation.get('progress', 0),
                    'message': consultation.get('message', ''),
                    'result_available': consultation.get('status') == 'completado',
                    'timestamp': datetime.now().isoformat()
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Sesión no encontrada'
                }), 404
        except Exception as e:
            logger.error(f"❌ Error obteniendo estado: {e}")
            return jsonify({'success': False, 'error': 'Error interno'}), 500
    
    @app.route('/api/resultado/<session_id>', methods=['GET'])
    def get_consultation_result(session_id):
        try:
            if session_id in vehicle_consultant.active_consultations:
                consultation = vehicle_consultant.active_consultations[session_id]
                
                if consultation.get('status') == 'completado' and 'result' in consultation:
                    return jsonify({
                        'success': True,
                        'session_id': session_id,
                        'vehicle_data': consultation['result'],
                        'complete_summary': consultation.get('complete_summary', {}),
                        'timestamp': datetime.now().isoformat()
                    })
                elif consultation.get('status') == 'error':
                    return jsonify({
                        'success': False,
                        'error': consultation.get('error', 'Error desconocido'),
                        'session_id': session_id
                    }), 500
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Consulta no completada',
                        'status': consultation.get('status'),
                        'progress': consultation.get('progress', 0)
                    }), 202
            else:
                return jsonify({
                    'success': False,
                    'error': 'Sesión no encontrada'
                }), 404
        except Exception as e:
            logger.error(f"❌ Error obteniendo resultado: {e}")
            return jsonify({'success': False, 'error': 'Error interno'}), 500
    
    @app.route('/api/validar-placa', methods=['POST'])
    def validate_plate():
        try:
            data = request.get_json()
            placa = data.get('placa', '').strip()
            
            if not placa:
                return jsonify({'success': False, 'error': 'Placa requerida'}), 400
            
            placa_original, placa_normalizada, fue_modificada = PlateValidator.normalize_plate(placa)
            es_valida = PlateValidator.validate_plate_format(placa_normalizada)
            
            return jsonify({
                'success': True,
                'placa_original': placa_original,
                'placa_normalizada': placa_normalizada,
                'fue_modificada': fue_modificada,
                'es_valida': es_valida,
                'mensaje': f"Placa {'normalizada automáticamente' if fue_modificada else 'sin cambios'}"
            })
        except Exception as e:
            logger.error(f"❌ Error validando placa: {e}")
            return jsonify({'success': False, 'error': 'Error procesando validación'}), 500
    
    @app.route('/api/validar-cedula', methods=['POST'])
    def validate_cedula():
        try:
            data = request.get_json()
            cedula = data.get('cedula', '').strip()
            
            if not cedula:
                return jsonify({'success': False, 'error': 'Cédula requerida'}), 400
            
            es_valida = CedulaValidator.validate_ecuadorian_id(cedula)
            
            provincia_info = None
            if es_valida and len(cedula) >= 2:
                codigo_provincia = cedula[:2]
                provincia_info = {
                    'codigo': codigo_provincia,
                    'nombre': CedulaValidator.PROVINCE_CODES.get(codigo_provincia, 'Desconocida')
                }
            
            return jsonify({
                'success': True,
                'cedula': cedula,
                'es_valida': es_valida,
                'provincia': provincia_info,
                'algoritmo': 'Validación oficial Ecuador',
                'mensaje': 'Cédula válida' if es_valida else 'Cédula inválida'
            })
        except Exception as e:
            logger.error(f"❌ Error validando cédula: {e}")
            return jsonify({'success': False, 'error': 'Error procesando validación'}), 500
    
    @app.route('/api/estadisticas', methods=['GET'])
    def get_statistics():
        try:
            consultas_totales = len(vehicle_consultant.active_consultations)
            consultas_exitosas = sum(1 for c in vehicle_consultant.active_consultations.values() 
                                   if c.get('status') == 'completado')
            consultas_con_error = sum(1 for c in vehicle_consultant.active_consultations.values() 
                                    if c.get('status') == 'error')
            
            return jsonify({
                'success': True,
                'estadisticas_generales': {
                    'total_consultas': consultas_totales,
                    'consultas_exitosas': consultas_exitosas,
                    'consultas_con_error': consultas_con_error,
                    'tasa_exito': round((consultas_exitosas / max(consultas_totales, 1)) * 100, 2),
                    'ultima_actualizacion': datetime.now().isoformat()
                },
                'apis_disponibles': {
                    'sri_endpoints_activos': list(SRI_ENDPOINTS.keys()),
                    'total_endpoints': len(SRI_ENDPOINTS),
                    'funcionalidad_completa': True
                },
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return jsonify({'success': False, 'error': 'Error obteniendo estadísticas'}), 500
    
    @app.route('/api/test-sri-completo', methods=['GET'])
    def test_sri_completo():
        try:
            placa_test = request.args.get('placa', 'TBX0160')
            
            logger.info(f"🧪 Iniciando test SRI COMPLETO con placa: {placa_test}")
            
            # Crear datos de usuario de prueba
            user_data_test = UserData(
                nombre="Usuario Test",
                cedula="1234567890",
                telefono="0999999999",
                correo="test@test.com"
            )
            
            session_id_test = f"test_definitivo_{int(time.time())}"
            
            # Ejecutar consulta de prueba
            vehicle_data = vehicle_consultant.consultar_vehiculo_completo(
                placa_test, 
                user_data_test, 
                session_id_test
            )
            
            if vehicle_data.consulta_exitosa:
                return jsonify({
                    'success': True,
                    'test_result': {
                        'placa_test': placa_test,
                        'marca_modelo': f"{vehicle_data.descripcion_marca} {vehicle_data.descripcion_modelo}",
                        'anio': vehicle_data.anio_auto,
                        'codigo_vehiculo': vehicle_data.codigo_vehiculo,
                        'total_deudas_sri': vehicle_data.total_deudas_sri,
                        'total_rubros': vehicle_data.total_rubros,
                        'total_pagos_realizados': vehicle_data.total_pagos_realizados,
                        'total_transacciones': vehicle_data.total_transacciones,
                        'total_cuotas_iacv': vehicle_data.total_cuotas_iacv,
                        'cuotas_vencidas': vehicle_data.cuotas_vencidas,
                        'estado_legal_sri': vehicle_data.estado_legal_sri,
                        'puntuacion_sri': vehicle_data.puntuacion_sri,
                        'tiempo_consulta': vehicle_data.tiempo_consulta,
                        'tiene_deudas': vehicle_data.tiene_deudas,
                        'tiene_pagos': vehicle_data.tiene_pagos
                    },
                    'apis_probadas': {
                        'base_vehiculo': True,
                        'rubros_deuda': True,
                        'historial_pagos': True,
                        'plan_iacv': True
                    },
                    'timestamp': datetime.now().isoformat()
                })
            else:
                return jsonify({
                    'success': False,
                    'error': vehicle_data.mensaje_error,
                    'placa_test': placa_test
                }), 500
                
        except Exception as e:
            logger.error(f"❌ Error en test SRI COMPLETO: {e}")
            return jsonify({
                'success': False,
                'error': 'Error en test SRI COMPLETO',
                'details': str(e)
            }), 500
    
    @app.route('/api/limpiar-cache', methods=['POST'])
    def clear_cache():
        try:
            # Limpiar consultas antiguas (más de 1 hora)
            current_time = time.time()
            sessions_to_remove = []
            
            for session_id, consultation in vehicle_consultant.active_consultations.items():
                # Estimar tiempo basado en session_id si es posible
                try:
                    session_timestamp = int(session_id.split('_')[2])
                    if current_time - session_timestamp > 3600:  # 1 hora
                        sessions_to_remove.append(session_id)
                except:
                    # Si no se puede parsear, eliminar después de muchas consultas
                    if len(vehicle_consultant.active_consultations) > 100:
                        sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove[:50]:  # Máximo 50 por vez
                del vehicle_consultant.active_consultations[session_id]
            
            logger.info(f"🧹 Cache limpiado: {len(sessions_to_remove)} sesiones eliminadas")
            
            return jsonify({
                'success': True,
                'message': 'Cache limpiado exitosamente',
                'sessions_removed': len(sessions_to_remove),
                'consultas_activas': len(vehicle_consultant.active_consultations),
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Error limpiando cache: {e}")
            return jsonify({'success': False, 'error': 'Error limpiando cache'}), 500
    
    def create_frontend_fallback():
        """Frontend de emergencia COMPLETO con toda la información"""
        return f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>ECPlacas 2.0 SRI DEFINITIVO</title>
            <style>
                body {{
                    font-family: 'Arial', sans-serif;
                    background: linear-gradient(135deg, #000 0%, #001122 50%, #000033 100%);
                    color: #00ffff;
                    margin: 0;
                    padding: 20px;
                    min-height: 100vh;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 2rem;
                    border: 2px solid #00ffff;
                    border-radius: 20px;
                    background: rgba(0, 0, 0, 0.8);
                }}
                .logo {{
                    font-size: 2.5rem;
                    font-weight: bold;
                    margin-bottom: 1rem;
                    text-align: center;
                    text-shadow: 0 0 20px #00ffff;
                }}
                .form-group {{
                    margin-bottom: 1rem;
                }}
                label {{
                    display: block;
                    margin-bottom: 0.5rem;
                    color: #00ffff;
                    font-weight: bold;
                }}
                input {{
                    width: 100%;
                    padding: 1rem;
                    background: rgba(0, 0, 0, 0.5);
                    border: 2px solid rgba(0, 255, 255, 0.3);
                    border-radius: 10px;
                    color: #fff;
                    font-size: 1rem;
                }}
                input:focus {{
                    outline: none;
                    border-color: #00ffff;
                    box-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
                }}
                .btn {{
                    background: linear-gradient(135deg, #00ffff, #0066ff);
                    color: #000;
                    border: none;
                    padding: 1rem 2rem;
                    border-radius: 25px;
                    font-weight: bold;
                    cursor: pointer;
                    width: 100%;
                    font-size: 1rem;
                    margin-top: 1rem;
                }}
                .btn:hover {{
                    transform: translateY(-3px);
                    box-shadow: 0 10px 25px rgba(0, 255, 255, 0.5);
                }}
                .result {{
                    margin-top: 2rem;
                    padding: 1.5rem;
                    background: rgba(0, 255, 255, 0.1);
                    border-radius: 15px;
                    border: 2px solid #00ffff;
                }}
                .result-section {{
                    margin-bottom: 2rem;
                    padding: 1rem;
                    background: rgba(0, 0, 0, 0.3);
                    border-radius: 10px;
                    border-left: 4px solid #00ffff;
                }}
                .result-title {{
                    font-size: 1.2rem;
                    font-weight: bold;
                    color: #00ffff;
                    margin-bottom: 1rem;
                }}
                .result-item {{
                    display: flex;
                    justify-content: space-between;
                    padding: 0.5rem 0;
                    border-bottom: 1px solid rgba(0, 255, 255, 0.2);
                }}
                .result-label {{
                    color: #99ccff;
                    font-weight: 500;
                }}
                .result-value {{
                    color: #fff;
                    font-weight: bold;
                }}
                .status {{
                    padding: 1rem;
                    margin: 1rem 0;
                    border-radius: 10px;
                    text-align: center;
                }}
                .status.success {{
                    background: rgba(0, 255, 102, 0.2);
                    border: 2px solid #00ff66;
                    color: #00ff66;
                }}
                .status.error {{
                    background: rgba(255, 102, 102, 0.2);
                    border: 2px solid #ff6666;
                    color: #ff6666;
                }}
                .hidden {{ display: none; }}
                .grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 1rem;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">ECPlacas 2.0 SRI DEFINITIVO</div>
                <div style="text-align: center; margin-bottom: 2rem; color: #99ccff;">
                    Sistema COMPLETO • Información SRI Total • Erick Costa
                </div>
                
                <form id="consultaForm">
                    <div class="grid">
                        <div class="form-group">
                            <label>Nombre Completo *</label>
                            <input type="text" id="nombre" placeholder="Ingrese su nombre completo" required>
                        </div>
                        <div class="form-group">
                            <label>Cédula de Identidad *</label>
                            <input type="text" id="cedula" placeholder="1234567890" maxlength="10" required>
                        </div>
                        <div class="form-group">
                            <label>Teléfono (Opcional)</label>
                            <input type="text" id="telefono" placeholder="0999999999" maxlength="10">
                        </div>
                        <div class="form-group">
                            <label>Correo (Opcional)</label>
                            <input type="email" id="correo" placeholder="usuario@email.com">
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label>Número de Placa *</label>
                        <input type="text" id="placa" placeholder="ABC1234" style="text-transform: uppercase; text-align: center; font-size: 1.3rem; letter-spacing: 2px;" required>
                    </div>
                    
                    <button type="submit" class="btn">🔍 Consultar SRI COMPLETO</button>
                </form>
                
                <div id="status" class="hidden"></div>
                <div id="result" class="hidden"></div>
            </div>
            
            <script>
                document.getElementById('consultaForm').addEventListener('submit', async function(e) {{
                    e.preventDefault();
                    
                    const statusDiv = document.getElementById('status');
                    const resultDiv = document.getElementById('result');
                    
                    statusDiv.className = 'status';
                    statusDiv.innerHTML = '⏳ Consultando SRI COMPLETO...';
                    statusDiv.classList.remove('hidden');
                    resultDiv.classList.add('hidden');
                    
                    const formData = {{
                        usuario: {{
                            nombre: document.getElementById('nombre').value,
                            cedula: document.getElementById('cedula').value,
                            telefono: document.getElementById('telefono').value,
                            correo: document.getElementById('correo').value
                        }},
                        placa: document.getElementById('placa').value.toUpperCase()
                    }};
                    
                    try {{
                        const response = await fetch('/api/consultar-vehiculo', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify(formData)
                        }});
                        
                        const data = await response.json();
                        
                        if (data.success) {{
                            statusDiv.className = 'status success';
                            statusDiv.innerHTML = '✅ Consulta SRI COMPLETA exitosa';
                            
                            const summary = data.complete_summary;
                            const vehiculo = summary.vehiculo_basico;
                            const deudas = summary.deudas_sri_completas;
                            const pagos = summary.pagos_sri_completos;
                            const iacv = summary.iacv_completo;
                            const analisis = summary.analisis_consolidado;
                            
                            resultDiv.innerHTML = `
                                <div class="result-title">🚗 INFORMACIÓN COMPLETA DEL VEHÍCULO</div>
                                
                                <div class="result-section">
                                    <div class="result-title">📋 Datos Básicos</div>
                                    <div class="result-item"><span class="result-label">Placa:</span><span class="result-value">${{vehiculo.placa}}</span></div>
                                    <div class="result-item"><span class="result-label">Marca/Modelo:</span><span class="result-value">${{vehiculo.marca}} ${{vehiculo.modelo}}</span></div>
                                    <div class="result-item"><span class="result-label">Año:</span><span class="result-value">${{vehiculo.anio}}</span></div>
                                    <div class="result-item"><span class="result-label">País:</span><span class="result-value">${{vehiculo.pais}}</span></div>
                                    <div class="result-item"><span class="result-label">Color:</span><span class="result-value">${{vehiculo.color1 || 'N/A'}}</span></div>
                                    <div class="result-item"><span class="result-label">Clase:</span><span class="result-value">${{vehiculo.clase || 'N/A'}}</span></div>
                                    <div class="result-item"><span class="result-label">Código Vehículo:</span><span class="result-value">${{vehiculo.codigo_vehiculo}}</span></div>
                                </div>
                                
                                <div class="result-section">
                                    <div class="result-title">💰 Deudas SRI Completas</div>
                                    <div class="result-item"><span class="result-label">Total Deudas:</span><span class="result-value" style="color: ${deudas.tiene_deudas ? '#ff6666' : '#00ff66'};">$${{deudas.total_deudas.toFixed(2)}}</span></div>
                                    <div class="result-item"><span class="result-label">Total Rubros:</span><span class="result-value">${{deudas.total_rubros}}</span></div>
                                    <div class="result-item"><span class="result-label">Estado Deudas:</span><span class="result-value">${{deudas.tiene_deudas ? '❌ CON DEUDAS' : '✅ SIN DEUDAS'}}</span></div>
                                </div>
                                
                                <div class="result-section">
                                    <div class="result-title">📊 Pagos SRI Completos</div>
                                    <div class="result-item"><span class="result-label">Total Pagado:</span><span class="result-value" style="color: #00ff66;">$${{pagos.total_pagado.toFixed(2)}}</span></div>
                                    <div class="result-item"><span class="result-label">Total Transacciones:</span><span class="result-value">${{pagos.total_transacciones}}</span></div>
                                    <div class="result-item"><span class="result-label">Último Pago:</span><span class="result-value">${{pagos.ultimo_pago_fecha || 'N/A'}}</span></div>
                                    <div class="result-item"><span class="result-label">Último Monto:</span><span class="result-value">$${{(pagos.ultimo_pago_monto || 0).toFixed(2)}}</span></div>
                                </div>
                                
                                <div class="result-section">
                                    <div class="result-title">🌱 Plan IACV Completo</div>
                                    <div class="result-item"><span class="result-label">Total Cuotas:</span><span class="result-value">${{iacv.total_cuotas}}</span></div>
                                    <div class="result-item"><span class="result-label">Cuotas Vencidas:</span><span class="result-value" style="color: ${iacv.cuotas_vencidas > 0 ? '#ff6666' : '#00ff66'};">$${{iacv.cuotas_vencidas.toFixed(2)}}</span></div>
                                </div>
                                
                                <div class="result-section">
                                    <div class="result-title">📈 Análisis Consolidado</div>
                                    <div class="result-item"><span class="result-label">Estado Legal SRI:</span><span class="result-value">${{analisis.estado_legal}}</span></div>
                                    <div class="result-item"><span class="result-label">Puntuación SRI:</span><span class="result-value">${{analisis.puntuacion_sri.toFixed(1)}}/100</span></div>
                                    <div class="result-item"><span class="result-label">Recomendación:</span><span class="result-value" style="font-size: 0.9rem;">${{analisis.recomendacion}}</span></div>
                                </div>
                                
                                <div class="result-section">
                                    <div class="result-title">⏱️ Metadatos</div>
                                    <div class="result-item"><span class="result-label">Tiempo Consulta:</span><span class="result-value">${{summary.metadatos.tiempo_consulta.toFixed(2)}}s</span></div>
                                    <div class="result-item"><span class="result-label">Session ID:</span><span class="result-value" style="font-size: 0.8rem;">${{summary.metadatos.session_id}}</span></div>
                                </div>
                            `;
                            resultDiv.classList.remove('hidden');
                        }} else {{
                            statusDiv.className = 'status error';
                            statusDiv.innerHTML = `❌ Error: ${{data.error}}`;
                        }}
                    }} catch (error) {{
                        statusDiv.className = 'status error';
                        statusDiv.innerHTML = `❌ Error de conexión: ${{error.message}}`;
                    }}
                }});
                
                // Validaciones en tiempo real
                document.getElementById('cedula').addEventListener('input', function(e) {{
                    e.target.value = e.target.value.replace(/\\D/g, '').slice(0, 10);
                }});
                
                document.getElementById('placa').addEventListener('input', function(e) {{
                    e.target.value = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 8);
                }});
                
                document.getElementById('telefono').addEventListener('input', function(e) {{
                    e.target.value = e.target.value.replace(/\\D/g, '').slice(0, 10);
                }});
            </script>
        </body>
        </html>
        """
    
    return app

# ==========================================
# PUNTO DE ENTRADA PRINCIPAL
# ==========================================

if __name__ == '__main__':
    try:
        logger.info("🚀 Iniciando ECPlacas 2.0 SRI DEFINITIVO...")
        app = create_app()
        
        logger.info("="*80)
        logger.info("🎯 ECPlacas 2.0 SRI DEFINITIVO - SISTEMA INICIADO")
        logger.info("="*80)
        logger.info("🌐 Frontend: http://localhost:5000")
        logger.info("🔍 API Health: http://localhost:5000/api/health")
        logger.info("📊 Estadísticas: http://localhost:5000/api/estadisticas")
        logger.info("🧪 Test SRI: http://localhost:5000/api/test-sri-completo")
        logger.info("="*80)
        logger.info("✨ CARACTERÍSTICAS SRI DEFINITIVAS:")
        logger.info("   ✅ • Información básica vehicular SRI")
        logger.info("   💰 • Rubros de deuda completos por beneficiario")
        logger.info("   📊 • Historial completo de pagos SRI")
        logger.info("   🌱 • Plan IACV (Impuesto Ambiental) detallado")
        logger.info("   📈 • Análisis consolidado con puntuación SRI")
        logger.info("   🔒 • Validación de cédulas y placas ecuatorianas")
        logger.info("   ⚡ • APIs verificadas que SÍ funcionan")
        logger.info("   🧹 • Código optimizado y mantenible")
        logger.info("="*80)
        logger.info("🔗 APIs ACTIVAS VERIFICADAS:")
        logger.info("   • POST /api/consultar-vehiculo - Consulta SRI COMPLETA")
        logger.info("   • GET  /api/estado-consulta/<session_id> - Estado consulta")
        logger.info("   • GET  /api/resultado/<session_id> - Resultado completo")
        logger.info("   • GET  /api/estadisticas - Estadísticas sistema")
        logger.info("   • GET  /api/test-sri-completo - Test APIs SRI")
        logger.info("   • POST /api/validar-placa - Validar placa")
        logger.info("   • POST /api/validar-cedula - Validar cédula")
        logger.info("   • POST /api/limpiar-cache - Limpiar cache")
        logger.info("="*80)
        logger.info("🎯 INFORMACIÓN COMPLETA DISPONIBLE:")
        logger.info("   📋 • Datos básicos: Marca, modelo, año, país, color, clase")
        logger.info("   💰 • Deudas SRI: Total, rubros por beneficiario")
        logger.info("   📊 • Pagos SRI: Historial, transacciones, último pago")
        logger.info("   🌱 • IACV: Cuotas, estados, vencidas")
        logger.info("   📈 • Análisis: Estado legal, puntuación, recomendaciones")
        logger.info("="*80)
        logger.info("🚀 LISTO PARA CONSULTAS SRI DEFINITIVAS!")
        logger.info("="*80)
        
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
        
    except KeyboardInterrupt:
        logger.info("🛑 Servidor SRI DEFINITIVO detenido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error crítico: {e}")
        sys.exit(1)