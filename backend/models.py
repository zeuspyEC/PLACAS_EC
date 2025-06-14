#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECPlacas 2.0 - Modelos de Datos
Proyecto: Construcción de Software
Desarrollado por: Erick Costa

Modelos de datos y validadores para ECPlacas 2.0
"""

import re
import json
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# ==================== ENUMS ====================

class EstadoMatricula(Enum):
    """Estados posibles de matrícula vehicular"""
    VIGENTE = "VIGENTE"
    POR_VENCER = "POR VENCER"
    VENCIDA = "VENCIDA"
    INDETERMINADO = "INDETERMINADO"

class TipoVehiculo(Enum):
    """Tipos de vehículos"""
    AUTOMOVIL = "AUTOMÓVIL"
    CAMIONETA = "CAMIONETA"
    JEEP = "JEEP"
    MOTOCICLETA = "MOTOCICLETA"
    CAMION = "CAMIÓN"
    BUS = "BUS"
    TAXI = "TAXI"
    OTRO = "OTRO"

class TipoServicio(Enum):
    """Tipos de servicio vehicular"""
    PARTICULAR = "USO PARTICULAR"
    PUBLICO = "SERVICIO PÚBLICO"
    COMERCIAL = "COMERCIAL"
    OFICIAL = "OFICIAL"
    DIPLOMATICO = "DIPLOMÁTICO"
    OTRO = "OTRO"

class NivelLog(Enum):
    """Niveles de logging"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

# ==================== VALIDADORES ====================

class ValidadorEcuatoriano:
    """Validadores específicos para datos ecuatorianos"""
    
    # Códigos de provincia válidos en Ecuador
    PROVINCE_CODES = {
        '01': 'Azuay', '02': 'Bolívar', '03': 'Cañar', '04': 'Carchi',
        '05': 'Cotopaxi', '06': 'Chimborazo', '07': 'El Oro', '08': 'Esmeraldas',
        '09': 'Guayas', '10': 'Imbabura', '11': 'Loja', '12': 'Los Ríos',
        '13': 'Manabí', '14': 'Morona Santiago', '15': 'Napo', '16': 'Pastaza',
        '17': 'Pichincha', '18': 'Tungurahua', '19': 'Zamora Chinchipe',
        '20': 'Galápagos', '21': 'Sucumbíos', '22': 'Orellana',
        '23': 'Santo Domingo', '24': 'Santa Elena', '30': 'Exterior'
    }
    
    @staticmethod
    def validar_cedula(cedula: str) -> tuple[bool, str]:
        """
        Valida cédula ecuatoriana con algoritmo oficial
        Returns: (es_valida, mensaje_error)
        """
        try:
            if not cedula or not isinstance(cedula, str):
                return False, "Cédula requerida"
            
            # Limpiar y validar formato
            cedula_clean = re.sub(r'\D', '', cedula)
            if len(cedula_clean) != 10:
                return False, "Cédula debe tener exactamente 10 dígitos"
            
            # Verificar código de provincia
            province_code = cedula_clean[:2]
            if province_code not in ValidadorEcuatoriano.PROVINCE_CODES:
                return False, f"Código de provincia inválido: {province_code}"
            
            # Verificar tercer dígito (debe ser menor a 6 para personas naturales)
            if int(cedula_clean[2]) >= 6:
                return False, "Cédula corresponde a persona jurídica o extranjero"
            
            # Algoritmo de validación del dígito verificador
            digits = [int(d) for d in cedula_clean]
            coefficients = [2, 1, 2, 1, 2, 1, 2, 1, 2]
            total = 0
            
            for i in range(9):
                result = digits[i] * coefficients[i]
                if result > 9:
                    result -= 9
                total += result
            
            check_digit = (10 - (total % 10)) % 10
            
            if check_digit != digits[9]:
                return False, "Dígito verificador de cédula inválido"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validando cédula: {e}")
            return False, "Error en validación de cédula"
    
    @staticmethod
    def validar_placa(placa: str) -> tuple[bool, str, str]:
        """
        Valida y normaliza placa vehicular ecuatoriana
        Returns: (es_valida, placa_normalizada, mensaje_error)
        """
        try:
            if not placa or not isinstance(placa, str):
                return False, "", "Placa requerida"
            
            # Limpiar placa
            placa_clean = re.sub(r'[^A-Z0-9]', '', placa.upper())
            
            if len(placa_clean) < 6 or len(placa_clean) > 7:
                return False, "", "Placa debe tener entre 6 y 7 caracteres"
            
            # Patrones válidos para placas ecuatorianas
            patterns = [
                r'^[A-Z]{2,3}\d{3,4}$',  # ABC1234 o AB1234
                r'^[A-Z]{3}\d{3}$',      # ABC123 (se normaliza)
            ]
            
            is_valid = any(re.match(pattern, placa_clean) for pattern in patterns)
            
            if not is_valid:
                return False, "", "Formato de placa inválido (ej: ABC1234)"
            
            # Normalización automática para placas de 6 caracteres
            if len(placa_clean) == 6 and re.match(r'^[A-Z]{3}\d{3}$', placa_clean):
                letters = placa_clean[:3]
                numbers = placa_clean[3:]
                placa_normalizada = f"{letters}0{numbers}"
                logger.info(f"Placa normalizada: {placa_clean} → {placa_normalizada}")
                return True, placa_normalizada, ""
            
            return True, placa_clean, ""
            
        except Exception as e:
            logger.error(f"Error validando placa: {e}")
            return False, "", "Error en validación de placa"
    
    @staticmethod
    def validar_telefono(telefono: str, codigo_pais: str = "+593") -> tuple[bool, str]:
        """
        Valida número telefónico según país
        Returns: (es_valido, mensaje_error)
        """
        try:
            if not telefono:
                return False, "Teléfono requerido"
            
            # Limpiar número
            telefono_clean = re.sub(r'\D', '', telefono)
            
            # Validaciones según código de país
            if codigo_pais == "+593":  # Ecuador
                if len(telefono_clean) == 9 and telefono_clean.startswith('9'):
                    return True, ""  # Móvil
                elif len(telefono_clean) == 8 and telefono_clean[0] in '234567':
                    return True, ""  # Fijo
                else:
                    return False, "Formato inválido para Ecuador (9XXXXXXXX o 2XXXXXXX)"
            elif codigo_pais == "+57":  # Colombia
                if len(telefono_clean) == 10:
                    return True, ""
                else:
                    return False, "Teléfono colombiano debe tener 10 dígitos"
            elif codigo_pais == "+51":  # Perú
                if len(telefono_clean) == 9:
                    return True, ""
                else:
                    return False, "Teléfono peruano debe tener 9 dígitos"
            else:
                # Validación genérica
                if 7 <= len(telefono_clean) <= 15:
                    return True, ""
                else:
                    return False, "Teléfono debe tener entre 7 y 15 dígitos"
                    
        except Exception as e:
            logger.error(f"Error validando teléfono: {e}")
            return False, "Error en validación de teléfono"

class ValidadorFormatos:
    """Validadores de formatos generales"""
    
    @staticmethod
    def validar_email(email: str) -> tuple[bool, str]:
        """Valida formato de correo electrónico"""
        if not email:
            return False, "Correo requerido"
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(pattern, email.lower()):
            return True, ""
        else:
            return False, "Formato de correo inválido"
    
    @staticmethod
    def validar_nombre(nombre: str) -> tuple[bool, str]:
        """Valida formato de nombre completo"""
        if not nombre:
            return False, "Nombre requerido"
        
        if len(nombre.strip()) < 2:
            return False, "Nombre muy corto"
        
        # Solo letras, espacios y acentos
        pattern = r'^[a-zA-ZáéíóúñÁÉÍÓÚÑ\s]+$'
        if re.match(pattern, nombre):
            return True, ""
        else:
            return False, "Nombre solo puede contener letras y espacios"

# ==================== MODELOS DE DATOS ====================

@dataclass
class UsuarioModel:
    """Modelo de datos de usuario"""
    id: Optional[int] = None
    nombre: str = ""
    cedula: str = ""
    telefono: str = ""
    correo: str = ""
    country_code: str = "+593"
    ip_address: str = ""
    user_agent: str = ""
    total_consultas: int = 0
    ultimo_acceso: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def validar(self) -> tuple[bool, List[str]]:
        """Valida todos los campos del usuario"""
        errores = []
        
        # Validar nombre
        valid_nombre, error_nombre = ValidadorFormatos.validar_nombre(self.nombre)
        if not valid_nombre:
            errores.append(f"Nombre: {error_nombre}")
        
        # Validar cédula
        valid_cedula, error_cedula = ValidadorEcuatoriano.validar_cedula(self.cedula)
        if not valid_cedula:
            errores.append(f"Cédula: {error_cedula}")
        
        # Validar teléfono
        valid_telefono, error_telefono = ValidadorEcuatoriano.validar_telefono(self.telefono, self.country_code)
        if not valid_telefono:
            errores.append(f"Teléfono: {error_telefono}")
        
        # Validar correo
        valid_correo, error_correo = ValidadorFormatos.validar_email(self.correo)
        if not valid_correo:
            errores.append(f"Correo: {error_correo}")
        
        return len(errores) == 0, errores
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para API"""
        data = asdict(self)
        # Convertir datetime a string
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UsuarioModel':
        """Crea instancia desde diccionario"""
        # Filtrar campos válidos
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        
        # Convertir strings de fecha a datetime
        for field in ['ultimo_acceso', 'created_at', 'updated_at']:
            if field in filtered_data and isinstance(filtered_data[field], str):
                try:
                    filtered_data[field] = datetime.fromisoformat(filtered_data[field])
                except:
                    filtered_data[field] = None
        
        return cls(**filtered_data)

@dataclass
class DatosIdentificacionVehicular:
    """Datos de identificación del vehículo"""
    vin_chasis: str = ""
    numero_motor: str = ""
    placa_actual: str = ""
    placa_anterior: str = ""
    
    def es_completo(self) -> bool:
        """Verifica si los datos de identificación están completos"""
        return bool(self.vin_chasis and self.numero_motor and self.placa_actual)

@dataclass
class DatosModeloVehicular:
    """Datos del modelo del vehículo"""
    marca: str = ""
    modelo: str = ""
    anio_fabricacion: int = 0
    pais_fabricacion: str = ""
    
    def es_completo(self) -> bool:
        """Verifica si los datos del modelo están completos"""
        return bool(self.marca and self.modelo and self.anio_fabricacion > 1950)
    
    def get_antiguedad(self) -> int:
        """Calcula la antigüedad del vehículo"""
        if self.anio_fabricacion > 0:
            return datetime.now().year - self.anio_fabricacion
        return 0

@dataclass
class CaracteristicasVehiculares:
    """Características físicas del vehículo"""
    clase_vehiculo: str = ""
    tipo_vehiculo: str = ""
    color_primario: str = ""
    color_secundario: str = ""
    peso_vehiculo: str = ""
    tipo_carroceria: str = ""
    
    def es_completo(self) -> bool:
        """Verifica si las características están completas"""
        return bool(self.clase_vehiculo and self.tipo_vehiculo and self.color_primario)

@dataclass
class DatosMatricula:
    """Datos de matrícula y revisión técnica"""
    matricula_desde: str = ""
    matricula_hasta: str = ""
    ano_ultima_revision: str = ""
    ultima_revision_desde: str = ""
    ultima_revision_hasta: str = ""
    servicio: str = ""
    ultima_actualizacion: str = ""
    
    def get_estado_matricula(self) -> tuple[EstadoMatricula, int]:
        """
        Calcula el estado de la matrícula
        Returns: (estado, dias_hasta_vencimiento)
        """
        try:
            if not self.matricula_hasta:
                return EstadoMatricula.INDETERMINADO, 0
            
            # Parsear fecha de vencimiento
            fecha_vencimiento = datetime.strptime(self.matricula_hasta.split(' ')[0], '%d-%m-%Y')
            today = datetime.now()
            dias_diferencia = (fecha_vencimiento - today).days
            
            if dias_diferencia > 30:
                return EstadoMatricula.VIGENTE, dias_diferencia
            elif dias_diferencia > 0:
                return EstadoMatricula.POR_VENCER, dias_diferencia
            else:
                return EstadoMatricula.VENCIDA, dias_diferencia
                
        except Exception as e:
            logger.error(f"Error calculando estado de matrícula: {e}")
            return EstadoMatricula.INDETERMINADO, 0
    
    def es_completo(self) -> bool:
        """Verifica si los datos de matrícula están completos"""
        return bool(self.matricula_desde and self.matricula_hasta)

@dataclass
class DatosCRV:
    """Datos del Centro de Retención Vehicular"""
    indicador_crv: str = ""
    orden_crv: str = ""
    centro_retencion: str = ""
    tipo_retencion: str = ""
    motivo_retencion: str = ""
    fecha_inicio_retencion: str = ""
    dias_retencion: str = ""
    grua: str = ""
    area_ubicacion: str = ""
    columna: str = ""
    fila: str = ""
    
    def esta_retenido(self) -> bool:
        """Verifica si el vehículo está retenido"""
        return self.indicador_crv.upper() == 'S'
    
    def get_info_retencion(self) -> Dict[str, str]:
        """Obtiene información completa de retención"""
        if not self.esta_retenido():
            return {}
        
        return {
            'centro': self.centro_retencion,
            'tipo': self.tipo_retencion,
            'motivo': self.motivo_retencion,
            'fecha_inicio': self.fecha_inicio_retencion,
            'dias': self.dias_retencion,
            'ubicacion': f"{self.area_ubicacion} - Columna {self.columna}, Fila {self.fila}"
        }

@dataclass
class AnalisisVehicular:
    """Análisis inteligente del vehículo"""
    estado_matricula: EstadoMatricula = EstadoMatricula.INDETERMINADO
    dias_hasta_vencimiento: int = 0
    estimacion_valor: float = 0.0
    categoria_riesgo: str = "BAJO"
    recomendaciones: List[str] = field(default_factory=list)
    puntuacion_general: int = 0  # 0-100
    
    def agregar_recomendacion(self, recomendacion: str):
        """Agrega una recomendación al análisis"""
        if recomendacion and recomendacion not in self.recomendaciones:
            self.recomendaciones.append(recomendacion)
    
    def get_recomendacion_texto(self) -> str:
        """Obtiene todas las recomendaciones como texto"""
        return " | ".join(self.recomendaciones) if self.recomendaciones else "Sin recomendaciones específicas"

@dataclass
class VehiculoCompleto:
    """Modelo completo de datos vehiculares ECPlacas 2.0"""
    
    # Metadatos de consulta
    session_id: str = ""
    numero_placa: str = ""
    placa_original: str = ""
    placa_normalizada: str = ""
    consulta_exitosa: bool = False
    tiempo_consulta: float = 0.0
    mensaje_error: str = ""
    timestamp_consulta: datetime = field(default_factory=datetime.now)
    
    # Datos estructurados del vehículo
    identificacion: DatosIdentificacionVehicular = field(default_factory=DatosIdentificacionVehicular)
    modelo: DatosModeloVehicular = field(default_factory=DatosModeloVehicular)
    caracteristicas: CaracteristicasVehiculares = field(default_factory=CaracteristicasVehiculares)
    matricula: DatosMatricula = field(default_factory=DatosMatricula)
    crv: DatosCRV = field(default_factory=DatosCRV)
    analisis: AnalisisVehicular = field(default_factory=AnalisisVehicular)
    
    def procesar_datos_api(self, api_response: Dict[str, Any]):
        """Procesa respuesta de API y llena los datos estructurados"""
        try:
            campos = api_response.get('campos', {})
            
            # Procesar datos de identificación
            identificacion_data = campos.get('lsDatosIdentificacion', [])
            for item in identificacion_data:
                etiqueta = item.get('etiqueta', '').lower()
                valor = item.get('valor', '')
                
                if 'vin' in etiqueta:
                    self.identificacion.vin_chasis = valor
                elif 'motor' in etiqueta:
                    self.identificacion.numero_motor = valor
                elif 'placa anterior' in etiqueta:
                    self.identificacion.placa_anterior = valor
            
            self.identificacion.placa_actual = self.numero_placa
            
            # Procesar datos del modelo
            modelo_data = campos.get('lsDatosModelo', [])
            for item in modelo_data:
                etiqueta = item.get('etiqueta', '').lower()
                valor = item.get('valor', '')
                
                if 'marca' in etiqueta:
                    self.modelo.marca = valor
                elif 'modelo' in etiqueta:
                    self.modelo.modelo = valor
                elif 'año fabricación' in etiqueta:
                    try:
                        self.modelo.anio_fabricacion = int(valor) if valor else 0
                    except:
                        self.modelo.anio_fabricacion = 0
                elif 'país fabricación' in etiqueta:
                    self.modelo.pais_fabricacion = valor
            
            # Procesar características
            caracteristicas_data = campos.get('lsOtrasCaracteristicas', [])
            for item in caracteristicas_data:
                etiqueta = item.get('etiqueta', '').lower()
                valor = item.get('valor', '')
                
                if 'clase' in etiqueta:
                    self.caracteristicas.clase_vehiculo = valor
                elif 'tipo' in etiqueta:
                    self.caracteristicas.tipo_vehiculo = valor
                elif 'color 1' in etiqueta:
                    self.caracteristicas.color_primario = valor
                elif 'color 2' in etiqueta:
                    self.caracteristicas.color_secundario = valor
                elif 'peso' in etiqueta:
                    self.caracteristicas.peso_vehiculo = valor
                elif 'carrocería' in etiqueta:
                    self.caracteristicas.tipo_carroceria = valor
            
            # Procesar datos de matrícula
            revision_data = campos.get('lsRevision', [])
            for item in revision_data:
                etiqueta = item.get('etiqueta', '').lower()
                valor = item.get('valor', '')
                
                if 'matrícula desde' in etiqueta:
                    self.matricula.matricula_desde = valor
                elif 'matrícula hasta' in etiqueta:
                    self.matricula.matricula_hasta = valor
                elif 'año última revisión' in etiqueta:
                    self.matricula.ano_ultima_revision = valor
                elif 'última revisión desde' in etiqueta:
                    self.matricula.ultima_revision_desde = valor
                elif 'última revisión hasta' in etiqueta:
                    self.matricula.ultima_revision_hasta = valor
            
            # Procesar datos CRV
            crv_data = campos.get('lsCrv', [])
            for item in crv_data:
                etiqueta = item.get('etiqueta', '').lower()
                valor = item.get('valor', '')
                
                if 'indicador crv' in etiqueta:
                    self.crv.indicador_crv = valor
                elif 'orden crv' in etiqueta:
                    self.crv.orden_crv = valor
                elif 'centro retención' in etiqueta:
                    self.crv.centro_retencion = valor
                elif 'tipo retención' in etiqueta:
                    self.crv.tipo_retencion = valor
                elif 'motivo retención' in etiqueta:
                    self.crv.motivo_retencion = valor
                elif 'fecha inicio retención' in etiqueta:
                    self.crv.fecha_inicio_retencion = valor
                elif 'días retención' in etiqueta:
                    self.crv.dias_retencion = valor
                elif 'grúa' in etiqueta:
                    self.crv.grua = valor
                elif 'área ubicación' in etiqueta:
                    self.crv.area_ubicacion = valor
                elif 'columna' in etiqueta:
                    self.crv.columna = valor
                elif 'fila' in etiqueta:
                    self.crv.fila = valor
            
            # Datos adicionales
            self.matricula.servicio = campos.get('lsServicio', '')
            self.matricula.ultima_actualizacion = campos.get('lsUltimaActualizacion', '')
            
            # Realizar análisis
            self.realizar_analisis()
            
            logger.info(f"✅ Datos vehiculares procesados exitosamente para {self.numero_placa}")
            
        except Exception as e:
            logger.error(f"❌ Error procesando datos vehiculares: {e}")
            raise
    
    def realizar_analisis(self):
        """Realiza análisis inteligente del vehículo"""
        try:
            # Analizar estado de matrícula
            estado_matricula, dias_hasta_vencimiento = self.matricula.get_estado_matricula()
            self.analisis.estado_matricula = estado_matricula
            self.analisis.dias_hasta_vencimiento = dias_hasta_vencimiento
            
            # Generar recomendaciones
            self._generar_recomendaciones()
            
            # Calcular estimación de valor
            self._calcular_estimacion_valor()
            
            # Calcular puntuación general
            self._calcular_puntuacion_general()
            
            logger.info(f"✅ Análisis vehicular completado para {self.numero_placa}")
            
        except Exception as e:
            logger.error(f"❌ Error en análisis vehicular: {e}")
    
    def _generar_recomendaciones(self):
        """Genera recomendaciones basadas en el estado del vehículo"""
        # Recomendaciones por estado CRV
        if self.crv.esta_retenido():
            self.analisis.agregar_recomendacion("⚠️ VEHÍCULO RETENIDO - Verificar estado legal urgente")
            self.analisis.categoria_riesgo = "ALTO"
        
        # Recomendaciones por matrícula
        if self.analisis.estado_matricula == EstadoMatricula.VENCIDA:
            self.analisis.agregar_recomendacion("🔴 Matrícula vencida - Renovar URGENTE")
            if self.analisis.categoria_riesgo == "BAJO":
                self.analisis.categoria_riesgo = "ALTO"
        elif self.analisis.estado_matricula == EstadoMatricula.POR_VENCER:
            if self.analisis.dias_hasta_vencimiento <= 7:
                self.analisis.agregar_recomendacion("🟠 Matrícula vence en menos de 7 días - Renovar PRONTO")
            else:
                self.analisis.agregar_recomendacion("🟡 Matrícula por vencer - Planificar renovación")
        elif self.analisis.estado_matricula == EstadoMatricula.VIGENTE:
            self.analisis.agregar_recomendacion("✅ Matrícula vigente - Documento en regla")
        
        # Recomendaciones por antigüedad
        antiguedad = self.modelo.get_antiguedad()
        if antiguedad > 25:
            self.analisis.agregar_recomendacion("🔧 Vehículo muy antiguo - Revisar estado mecánico y emisiones")
        elif antiguedad > 15:
            self.analisis.agregar_recomendacion("🔧 Vehículo antiguo - Mantenimiento preventivo recomendado")
        elif antiguedad < 3:
            self.analisis.agregar_recomendacion("⭐ Vehículo relativamente nuevo - Mantener historial de mantenimiento")
        
        # Recomendaciones por marca
        marca_upper = self.modelo.marca.upper()
        if marca_upper in ['TOYOTA', 'HONDA', 'NISSAN', 'MAZDA']:
            self.analisis.agregar_recomendacion("🏆 Marca reconocida por confiabilidad y repuestos disponibles")
        elif marca_upper in ['CHEVROLET', 'HYUNDAI', 'KIA', 'FORD']:
            self.analisis.agregar_recomendacion("👍 Marca con buen soporte local y repuestos accesibles")
        
        # Si no hay recomendaciones específicas
        if not self.analisis.recomendaciones:
            self.analisis.agregar_recomendacion("📋 Vehículo sin observaciones especiales")
    
    def _calcular_estimacion_valor(self):
        """Calcula estimación básica de valor de mercado"""
        try:
            if self.modelo.anio_fabricacion <= 0:
                self.analisis.estimacion_valor = 0
                return
            
            # Valor base según tipo de vehículo
            tipo_vehiculo = self.caracteristicas.tipo_vehiculo.upper()
            if tipo_vehiculo in ['JEEP', 'CAMIONETA']:
                valor_base = 18000
            elif tipo_vehiculo in ['AUTOMÓVIL', 'AUTOMOVIL']:
                valor_base = 15000
            elif tipo_vehiculo == 'MOTOCICLETA':
                valor_base = 5000
            elif tipo_vehiculo in ['CAMIÓN', 'CAMION', 'BUS']:
                valor_base = 25000
            else:
                valor_base = 12000
            
            # Factor por marca
            marca_upper = self.modelo.marca.upper()
            factor_marca = 1.0
            
            if marca_upper in ['TOYOTA', 'HONDA', 'NISSAN', 'LEXUS', 'BMW', 'MERCEDES']:
                factor_marca = 1.3
            elif marca_upper in ['CHEVROLET', 'HYUNDAI', 'KIA', 'MAZDA', 'FORD']:
                factor_marca = 1.1
            elif marca_upper in ['CHERY', 'GREAT WALL', 'BYD', 'JAC']:
                factor_marca = 0.8
            
            # Depreciación por año
            antiguedad = self.modelo.get_antiguedad()
            depreciacion_anual = 0.08  # 8% anual
            factor_depreciacion = max(0.1, (1 - depreciacion_anual) ** antiguedad)
            
            # Factor por estado de matrícula
            factor_matricula = 1.0
            if self.analisis.estado_matricula == EstadoMatricula.VENCIDA:
                factor_matricula = 0.85
            elif self.crv.esta_retenido():
                factor_matricula = 0.75
            
            # Cálculo final
            self.analisis.estimacion_valor = max(
                valor_base * factor_marca * factor_depreciacion * factor_matricula,
                1000  # Valor mínimo
            )
            
            logger.info(f"💰 Estimación de valor calculada: ${self.analisis.estimacion_valor:,.2f}")
            
        except Exception as e:
            logger.error(f"❌ Error calculando estimación de valor: {e}")
            self.analisis.estimacion_valor = 0
    
    def _calcular_puntuacion_general(self):
        """Calcula puntuación general del vehículo (0-100)"""
        try:
            puntuacion = 100
            
            # Penalizaciones por problemas
            if self.crv.esta_retenido():
                puntuacion -= 40
            
            if self.analisis.estado_matricula == EstadoMatricula.VENCIDA:
                puntuacion -= 25
            elif self.analisis.estado_matricula == EstadoMatricula.POR_VENCER:
                if self.analisis.dias_hasta_vencimiento <= 7:
                    puntuacion -= 15
                else:
                    puntuacion -= 5
            
            # Penalización por antigüedad
            antiguedad = self.modelo.get_antiguedad()
            if antiguedad > 25:
                puntuacion -= 20
            elif antiguedad > 15:
                puntuacion -= 10
            elif antiguedad > 10:
                puntuacion -= 5
            
            # Bonificaciones por marca reconocida
            marca_upper = self.modelo.marca.upper()
            if marca_upper in ['TOYOTA', 'HONDA', 'NISSAN']:
                puntuacion += 5
            
            # Asegurar rango válido
            self.analisis.puntuacion_general = max(0, min(100, puntuacion))
            
        except Exception as e:
            logger.error(f"❌ Error calculando puntuación general: {e}")
            self.analisis.puntuacion_general = 50
    
    def es_datos_completos(self) -> bool:
        """Verifica si todos los datos importantes están completos"""
        return (
            self.identificacion.es_completo() and
            self.modelo.es_completo() and
            self.caracteristicas.es_completo() and
            self.matricula.es_completo()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte todo el modelo a diccionario para API"""
        try:
            data = {
                # Metadatos
                'session_id': self.session_id,
                'numero_placa': self.numero_placa,
                'placa_original': self.placa_original,
                'placa_normalizada': self.placa_normalizada,
                'consulta_exitosa': self.consulta_exitosa,
                'tiempo_consulta': self.tiempo_consulta,
                'mensaje_error': self.mensaje_error,
                'timestamp_consulta': self.timestamp_consulta.isoformat(),
                
                # Datos del vehículo (para compatibilidad)
                'vin_chasis': self.identificacion.vin_chasis,
                'numero_motor': self.identificacion.numero_motor,
                'placa_anterior': self.identificacion.placa_anterior,
                'marca': self.modelo.marca,
                'modelo': self.modelo.modelo,
                'anio_fabricacion': self.modelo.anio_fabricacion,
                'pais_fabricacion': self.modelo.pais_fabricacion,
                'clase_vehiculo': self.caracteristicas.clase_vehiculo,
                'tipo_vehiculo': self.caracteristicas.tipo_vehiculo,
                'color_primario': self.caracteristicas.color_primario,
                'color_secundario': self.caracteristicas.color_secundario,
                'peso_vehiculo': self.caracteristicas.peso_vehiculo,
                'tipo_carroceria': self.caracteristicas.tipo_carroceria,
                'matricula_desde': self.matricula.matricula_desde,
                'matricula_hasta': self.matricula.matricula_hasta,
                'ano_ultima_revision': self.matricula.ano_ultima_revision,
                'servicio': self.matricula.servicio,
                'ultima_actualizacion': self.matricula.ultima_actualizacion,
                'indicador_crv': self.crv.indicador_crv,
                
                # Análisis
                'estado_matricula': self.analisis.estado_matricula.value,
                'dias_hasta_vencimiento': self.analisis.dias_hasta_vencimiento,
                'estimacion_valor': self.analisis.estimacion_valor,
                'categoria_riesgo': self.analisis.categoria_riesgo,
                'recomendacion': self.analisis.get_recomendacion_texto(),
                'puntuacion_general': self.analisis.puntuacion_general,
                
                # Datos estructurados completos
                'datos_estructurados': {
                    'identificacion': asdict(self.identificacion),
                    'modelo': asdict(self.modelo),
                    'caracteristicas': asdict(self.caracteristicas),
                    'matricula': asdict(self.matricula),
                    'crv': asdict(self.crv),
                    'analisis': asdict(self.analisis)
                }
            }
            
            return data
            
        except Exception as e:
            logger.error(f"❌ Error convirtiendo a diccionario: {e}")
            return {}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VehiculoCompleto':
        """Crea instancia desde diccionario"""
        try:
            instance = cls()
            
            # Cargar metadatos básicos
            instance.session_id = data.get('session_id', '')
            instance.numero_placa = data.get('numero_placa', '')
            instance.placa_original = data.get('placa_original', '')
            instance.placa_normalizada = data.get('placa_normalizada', '')
            instance.consulta_exitosa = data.get('consulta_exitosa', False)
            instance.tiempo_consulta = data.get('tiempo_consulta', 0.0)
            instance.mensaje_error = data.get('mensaje_error', '')
            
            # Timestamp
            timestamp_str = data.get('timestamp_consulta')
            if timestamp_str:
                try:
                    instance.timestamp_consulta = datetime.fromisoformat(timestamp_str)
                except:
                    instance.timestamp_consulta = datetime.now()
            
            # Si hay datos estructurados, cargarlos
            datos_estructurados = data.get('datos_estructurados', {})
            if datos_estructurados:
                if 'identificacion' in datos_estructurados:
                    instance.identificacion = DatosIdentificacionVehicular(**datos_estructurados['identificacion'])
                if 'modelo' in datos_estructurados:
                    instance.modelo = DatosModeloVehicular(**datos_estructurados['modelo'])
                if 'caracteristicas' in datos_estructurados:
                    instance.caracteristicas = CaracteristicasVehiculares(**datos_estructurados['caracteristicas'])
                if 'matricula' in datos_estructurados:
                    instance.matricula = DatosMatricula(**datos_estructurados['matricula'])
                if 'crv' in datos_estructurados:
                    instance.crv = DatosCRV(**datos_estructurados['crv'])
                if 'analisis' in datos_estructurados:
                    analisis_data = datos_estructurados['analisis']
                    # Convertir enum
                    if 'estado_matricula' in analisis_data:
                        try:
                            analisis_data['estado_matricula'] = EstadoMatricula(analisis_data['estado_matricula'])
                        except:
                            analisis_data['estado_matricula'] = EstadoMatricula.INDETERMINADO
                    instance.analisis = AnalisisVehicular(**analisis_data)
            else:
                # Cargar desde formato plano (compatibilidad)
                instance._cargar_desde_formato_plano(data)
            
            return instance
            
        except Exception as e:
            logger.error(f"❌ Error creando instancia desde diccionario: {e}")
            return cls()
    
    def _cargar_desde_formato_plano(self, data: Dict[str, Any]):
        """Carga datos desde formato plano para compatibilidad"""
        # Identificación
        self.identificacion.vin_chasis = data.get('vin_chasis', '')
        self.identificacion.numero_motor = data.get('numero_motor', '')
        self.identificacion.placa_anterior = data.get('placa_anterior', '')
        self.identificacion.placa_actual = self.numero_placa
        
        # Modelo
        self.modelo.marca = data.get('marca', '')
        self.modelo.modelo = data.get('modelo', '')
        self.modelo.anio_fabricacion = data.get('anio_fabricacion', 0)
        self.modelo.pais_fabricacion = data.get('pais_fabricacion', '')
        
        # Características
        self.caracteristicas.clase_vehiculo = data.get('clase_vehiculo', '')
        self.caracteristicas.tipo_vehiculo = data.get('tipo_vehiculo', '')
        self.caracteristicas.color_primario = data.get('color_primario', '')
        self.caracteristicas.color_secundario = data.get('color_secundario', '')
        self.caracteristicas.peso_vehiculo = data.get('peso_vehiculo', '')
        self.caracteristicas.tipo_carroceria = data.get('tipo_carroceria', '')
        
        # Matrícula
        self.matricula.matricula_desde = data.get('matricula_desde', '')
        self.matricula.matricula_hasta = data.get('matricula_hasta', '')
        self.matricula.ano_ultima_revision = data.get('ano_ultima_revision', '')
        self.matricula.servicio = data.get('servicio', '')
        self.matricula.ultima_actualizacion = data.get('ultima_actualizacion', '')
        
        # CRV
        self.crv.indicador_crv = data.get('indicador_crv', '')
        
        # Análisis básico
        estado_str = data.get('estado_matricula', 'INDETERMINADO')
        try:
            self.analisis.estado_matricula = EstadoMatricula(estado_str)
        except:
            self.analisis.estado_matricula = EstadoMatricula.INDETERMINADO
        
        self.analisis.dias_hasta_vencimiento = data.get('dias_hasta_vencimiento', 0)
        self.analisis.estimacion_valor = data.get('estimacion_valor', 0.0)
        self.analisis.categoria_riesgo = data.get('categoria_riesgo', 'BAJO')

# Crear instancia de validador para uso global
validador = ValidadorEcuatoriano()

if __name__ == "__main__":
    # Pruebas básicas
    print("🧪 Probando modelos ECPlacas 2.0...")
    
    # Probar validación de cédula
    cedula_test = "1234567890"
    valida, error = ValidadorEcuatoriano.validar_cedula(cedula_test)
    print(f"Cédula {cedula_test}: {'✅ Válida' if valida else f'❌ {error}'}")
    
    # Probar validación de placa
    placa_test = "ABC123"
    valida, normalizada, error = ValidadorEcuatoriano.validar_placa(placa_test)
    print(f"Placa {placa_test}: {'✅ Válida' if valida else f'❌ {error}'}")
    if valida:
        print(f"Normalizada: {normalizada}")
    
    # Probar modelo de vehículo
    vehiculo = VehiculoCompleto()
    vehiculo.numero_placa = "TBX0160"
    vehiculo.session_id = "test_123"
    
    print(f"Vehículo creado: {vehiculo.numero_placa}")
    print(f"Datos completos: {vehiculo.es_datos_completos()}")
    
    print("✅ Pruebas de modelos completadas exitosamente")
