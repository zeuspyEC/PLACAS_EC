#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================
ECPlacas 2.0 SRI COMPLETO - Modelos de Datos
==========================================
Proyecto: Construcción de Software
Desarrollado por: Erick Costa - ZeusPy
Versión: 2.0.1
==========================================

Modelos de datos optimizados para sistema SRI COMPLETO + Propietario
Compatible con app.py y base de datos SQLite
"""

import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

# ==========================================
# ENUMS PARA CLASIFICACIÓN
# ==========================================


class TipoConsulta(Enum):
    SRI_COMPLETO = "sri_completo"
    SRI_BASICO = "sri_basico"
    PROPIETARIO_SOLO = "propietario_solo"
    COMPLETO_PROPIETARIO = "completo_propietario"


class EstadoConsulta(Enum):
    INICIANDO = "iniciando"
    CONSULTANDO_PROPIETARIO = "consultando_propietario"
    CONSULTANDO_BASE_SRI = "consultando_base_sri"
    CONSULTANDO_RUBROS = "consultando_rubros_sri"
    CONSULTANDO_COMPONENTES = "consultando_componentes_sri"
    CONSULTANDO_PAGOS = "consultando_pagos_sri"
    CONSULTANDO_IACV = "consultando_iacv"
    ANALIZANDO_COMPLETO = "analizando_completo"
    COMPLETADO = "completado"
    ERROR = "error"


class TipoComponente(Enum):
    IMPUESTO = "IMPUESTO"
    TASA = "TASA"
    INTERES = "INTERES"
    MULTA = "MULTA"
    PRESCRIPCION = "PRESCRIPCION"
    OTRO = "OTRO"


class EstadoLegalSRI(Enum):
    EXCELENTE = "EXCELENTE - SIN DEUDAS"
    BUENO = "BUENO - DEUDAS MENORES"
    REGULAR = "REGULAR - DEUDAS MODERADAS"
    MALO = "MALO - DEUDAS ALTAS"
    CRITICO = "CRÍTICO - MÚLTIPLES DEUDAS"


class RiesgoTributario(Enum):
    MUY_BAJO = "MUY BAJO"
    BAJO = "BAJO"
    MODERADO = "MODERADO"
    ALTO = "ALTO"
    CRITICO = "CRÍTICO"


# ==========================================
# MODELO DE USUARIO
# ==========================================


@dataclass
class UsuarioECPlacas:
    """Modelo de usuario del sistema ECPlacas 2.0"""

    nombre: str = ""
    cedula: str = ""
    telefono: str = ""
    correo: str = ""
    country_code: str = "+593"
    acepta_terminos: bool = False
    ip_address: str = ""
    user_agent: str = ""
    total_consultas: int = 0
    ultimo_acceso: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        data = asdict(self)
        if self.ultimo_acceso:
            data["ultimo_acceso"] = self.ultimo_acceso.isoformat()
        data["created_at"] = self.created_at.isoformat()
        return data

    def es_valido(self) -> bool:
        """Validar datos básicos del usuario"""
        return (
            len(self.nombre.strip()) >= 2
            and len(self.cedula) == 10
            and self.cedula.isdigit()
            and self.acepta_terminos
        )


# ==========================================
# MODELO DE PROPIETARIO VEHICULAR
# ==========================================


@dataclass
class PropietarioVehiculo:
    """Información del propietario del vehículo"""

    nombre: str = ""
    cedula: str = ""
    encontrado: bool = False
    fuente_api: str = ""  # primary, backup, manual
    timestamp_consulta: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            "nombre": self.nombre,
            "cedula": self.cedula,
            "encontrado": self.encontrado,
            "fuente_api": self.fuente_api,
            "timestamp_consulta": self.timestamp_consulta.isoformat(),
        }


# ==========================================
# MODELO DE RUBRO SRI
# ==========================================


@dataclass
class RubroSRI:
    """Rubro de deuda SRI detallado"""

    codigo_rubro: str = ""
    descripcion_rubro: str = ""
    nombre_corto_beneficiario: str = ""
    valor_rubro: float = 0.0
    anio_desde_pago: int = 0
    anio_hasta_pago: int = 0
    categoria: str = "OTRO"  # IMPUESTO, TASA, MULTA, OTRO
    prioridad: str = "MEDIA"  # ALTA, MEDIA, BAJA
    periodo_deuda: str = ""
    anos_deuda: int = 0

    def __post_init__(self):
        """Procesamiento post-inicialización"""
        if self.anio_desde_pago and self.anio_hasta_pago:
            self.anos_deuda = self.anio_hasta_pago - self.anio_desde_pago + 1
            self.periodo_deuda = f"{self.anio_desde_pago} - {self.anio_hasta_pago}"

        # Clasificar categoría automáticamente
        if not self.categoria or self.categoria == "OTRO":
            descripcion_upper = self.descripcion_rubro.upper()
            if "IMPUESTO" in descripcion_upper:
                self.categoria = "IMPUESTO"
            elif "TASA" in descripcion_upper:
                self.categoria = "TASA"
            elif "MULTA" in descripcion_upper:
                self.categoria = "MULTA"

        # Determinar prioridad por valor
        if not self.prioridad or self.prioridad == "MEDIA":
            if self.valor_rubro > 500:
                self.prioridad = "ALTA"
            elif self.valor_rubro > 100:
                self.prioridad = "MEDIA"
            else:
                self.prioridad = "BAJA"

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return asdict(self)


# ==========================================
# MODELO DE COMPONENTE SRI
# ==========================================


@dataclass
class ComponenteSRI:
    """Componente fiscal SRI detallado"""

    codigo_componente: str = ""
    descripcion_componente: str = ""
    valor_componente: float = 0.0
    tipo_componente: str = TipoComponente.OTRO.value
    rubro_padre: Optional[Dict] = None

    def __post_init__(self):
        """Clasificar tipo de componente automáticamente"""
        if self.tipo_componente == TipoComponente.OTRO.value:
            codigo_upper = self.codigo_componente.upper()
            descripcion_upper = self.descripcion_componente.upper()

            if "IMPUESTO" in codigo_upper or "IMPUESTO" in descripcion_upper:
                self.tipo_componente = TipoComponente.IMPUESTO.value
            elif "TASA" in codigo_upper or "TASA" in descripcion_upper:
                self.tipo_componente = TipoComponente.TASA.value
            elif "INTERES" in codigo_upper or "INTERES" in descripcion_upper:
                self.tipo_componente = TipoComponente.INTERES.value
            elif "MULTA" in codigo_upper or "MULTA" in descripcion_upper:
                self.tipo_componente = TipoComponente.MULTA.value
            elif "PRESCRIPCION" in codigo_upper or "PRESCRIPCION" in descripcion_upper:
                self.tipo_componente = TipoComponente.PRESCRIPCION.value

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return asdict(self)


# ==========================================
# MODELO DE PAGO SRI
# ==========================================


@dataclass
class PagoSRI:
    """Pago registrado en el SRI"""

    codigo_recaudacion: str = ""
    fecha_pago: str = ""
    fecha_pago_formateada: str = ""
    monto: float = 0.0
    descripcion_forma_pago: str = ""
    descripcion_estado: str = ""
    detalles_adicionales: Optional[List[Dict]] = None

    def __post_init__(self):
        """Formatear fecha si es necesario"""
        if self.fecha_pago and not self.fecha_pago_formateada:
            try:
                if len(self.fecha_pago) >= 10:
                    fecha_parte = self.fecha_pago.split(" ")[0]
                    if "-" in fecha_parte:
                        año, mes, dia = fecha_parte.split("-")
                        self.fecha_pago_formateada = f"{dia}/{mes}/{año}"
                    else:
                        self.fecha_pago_formateada = self.fecha_pago
            except:
                self.fecha_pago_formateada = self.fecha_pago

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return asdict(self)


# ==========================================
# MODELO DE CUOTA IACV
# ==========================================


@dataclass
class CuotaIACV:
    """Cuota del plan IACV (Impuesto Ambiental)"""

    numero_cuota: str = ""
    periodo_fiscal: str = ""
    total_cuota: float = 0.0
    estado_pago: str = "PENDIENTE"  # PAGADO, PENDIENTE, VENCIDO
    fecha_vencimiento_estimada: str = ""
    descripcion_cuota: str = ""

    def __post_init__(self):
        """Generar descripción y fecha de vencimiento"""
        if not self.descripcion_cuota and self.numero_cuota and self.periodo_fiscal:
            self.descripcion_cuota = (
                f"Cuota {self.numero_cuota} - {self.periodo_fiscal}"
            )

        if not self.fecha_vencimiento_estimada and self.periodo_fiscal:
            self.fecha_vencimiento_estimada = self._estimar_fecha_vencimiento()

    def _estimar_fecha_vencimiento(self) -> str:
        """Estimar fecha de vencimiento"""
        try:
            if "-" in self.periodo_fiscal:
                año_inicio = int(self.periodo_fiscal.split("-")[0])
            else:
                año_inicio = int(self.periodo_fiscal)

            cuota_num = 1
            if "Cuota" in self.numero_cuota:
                try:
                    cuota_num = int(self.numero_cuota.split("Cuota")[-1].strip())
                except:
                    cuota_num = 1

            mes_vencimiento = (cuota_num - 1) * 3 + 3
            if mes_vencimiento > 12:
                año_inicio += (mes_vencimiento - 1) // 12
                mes_vencimiento = ((mes_vencimiento - 1) % 12) + 1

            return f"31/{mes_vencimiento:02d}/{año_inicio}"
        except:
            return "Fecha no disponible"

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return asdict(self)


# ==========================================
# MODELO DE ANÁLISIS SRI
# ==========================================


@dataclass
class AnalisisSRI:
    """Análisis consolidado SRI"""

    estado_legal_sri: str = EstadoLegalSRI.EXCELENTE.value
    riesgo_tributario: str = RiesgoTributario.BAJO.value
    puntuacion_sri: int = 100
    puntuacion_general: int = 100
    recomendacion_tributaria: str = ""
    recomendacion_general: str = ""
    estimacion_valor: float = 0.0
    categoria_riesgo: str = "BAJO"

    def calcular_puntuacion(
        self,
        total_deudas: float,
        total_multas: float,
        total_intereses: float,
        cuotas_vencidas: float,
        total_pagos: float,
        prohibido_enajenar: str,
    ) -> int:
        """Calcular puntuación SRI basada en factores"""
        puntuacion = 100

        # Penalizaciones por deudas
        if total_deudas > 2000:
            puntuacion -= 50
        elif total_deudas > 1000:
            puntuacion -= 40
        elif total_deudas > 500:
            puntuacion -= 25
        elif total_deudas > 100:
            puntuacion -= 15
        elif total_deudas > 0:
            puntuacion -= 5

        # Penalizaciones específicas
        if total_multas > 100:
            puntuacion -= 20
        elif total_multas > 0:
            puntuacion -= 10

        if total_intereses > 50:
            puntuacion -= 15
        elif total_intereses > 0:
            puntuacion -= 5

        # IACV vencidas
        if cuotas_vencidas > 100:
            puntuacion -= 25
        elif cuotas_vencidas > 50:
            puntuacion -= 20
        elif cuotas_vencidas > 0:
            puntuacion -= 10

        # Bonificaciones por pagos
        if total_pagos > 2000:
            puntuacion += 10
        elif total_pagos > 1000:
            puntuacion += 5

        # Prohibición de enajenar
        if prohibido_enajenar and prohibido_enajenar.upper() in ["SI", "SÍ", "YES"]:
            puntuacion -= 30

        self.puntuacion_sri = max(0, min(100, puntuacion))
        return self.puntuacion_sri

    def determinar_estado_legal(self):
        """Determinar estado legal basado en puntuación"""
        if self.puntuacion_sri >= 95:
            self.estado_legal_sri = EstadoLegalSRI.EXCELENTE.value
            self.riesgo_tributario = RiesgoTributario.MUY_BAJO.value
            self.recomendacion_tributaria = (
                "Vehículo con situación tributaria óptima para transferencia"
            )
        elif self.puntuacion_sri >= 80:
            self.estado_legal_sri = EstadoLegalSRI.BUENO.value
            self.riesgo_tributario = RiesgoTributario.BAJO.value
            self.recomendacion_tributaria = (
                "Regularizar deudas menores antes de transferencia"
            )
        elif self.puntuacion_sri >= 60:
            self.estado_legal_sri = EstadoLegalSRI.REGULAR.value
            self.riesgo_tributario = RiesgoTributario.MODERADO.value
            self.recomendacion_tributaria = (
                "Negociar descuento por deudas pendientes en precio final"
            )
        elif self.puntuacion_sri >= 40:
            self.estado_legal_sri = EstadoLegalSRI.MALO.value
            self.riesgo_tributario = RiesgoTributario.ALTO.value
            self.recomendacion_tributaria = (
                "Verificar costos de regularización antes de compra"
            )
        else:
            self.estado_legal_sri = EstadoLegalSRI.CRITICO.value
            self.riesgo_tributario = RiesgoTributario.CRITICO.value
            self.recomendacion_tributaria = (
                "NO RECOMENDADO - Evaluar otras alternativas"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return asdict(self)


# ==========================================
# MODELO PRINCIPAL DE DATOS VEHICULARES SRI COMPLETO
# ==========================================


@dataclass
class DatosVehicularesCompletos:
    """Modelo principal de datos vehiculares SRI COMPLETO + Propietario"""

    # Identificación básica
    numero_placa: str = ""
    placa_original: str = ""
    placa_normalizada: str = ""
    codigo_vehiculo: int = 0
    numero_camv_cpn: str = ""
    session_id: str = ""

    # Propietario del vehículo
    propietario: PropietarioVehiculo = field(default_factory=PropietarioVehiculo)

    # Información básica del vehículo
    vin_chasis: str = ""
    numero_motor: str = ""
    descripcion_marca: str = ""
    descripcion_modelo: str = ""
    anio_auto: int = 0
    descripcion_pais: str = ""
    color_vehiculo1: str = ""
    color_vehiculo2: str = ""
    cilindraje: str = ""
    nombre_clase: str = ""

    # Información de matrícula
    fecha_ultima_matricula: str = ""
    fecha_caducidad_matricula: str = ""
    fecha_compra_registro: str = ""
    fecha_revision: str = ""
    descripcion_canton: str = ""
    descripcion_servicio: str = ""
    ultimo_anio_pagado: int = 0

    # Estados legales
    prohibido_enajenar: str = ""
    estado_exoneracion: str = ""
    observacion: str = ""
    aplica_cuota: bool = False
    mensaje_motivo_auto: str = ""

    # Datos SRI completos
    rubros_deuda: List[RubroSRI] = field(default_factory=list)
    componentes_deuda: List[ComponenteSRI] = field(default_factory=list)
    historial_pagos: List[PagoSRI] = field(default_factory=list)
    plan_iacv: List[CuotaIACV] = field(default_factory=list)

    # Análisis financiero
    total_deudas_sri: float = 0.0
    total_impuestos: float = 0.0
    total_tasas: float = 0.0
    total_intereses: float = 0.0
    total_multas: float = 0.0
    total_prescripciones: float = 0.0
    total_pagos_realizados: float = 0.0
    pagos_ultimo_ano: float = 0.0
    promedio_pago_anual: float = 0.0
    total_cuotas_vencidas: float = 0.0

    # Agrupaciones
    rubros_agrupados_por_beneficiario: Dict[str, Dict] = field(default_factory=dict)
    totales_por_beneficiario: Dict[str, float] = field(default_factory=dict)
    componentes_por_rubro: Dict[str, List] = field(default_factory=dict)
    cuotas_por_estado: Dict[str, int] = field(default_factory=dict)

    # Análisis consolidado
    analisis: AnalisisSRI = field(default_factory=AnalisisSRI)

    # Estados de matrícula
    estado_matricula: str = "INDETERMINADO"
    dias_hasta_vencimiento: int = 0

    # Metadatos
    timestamp_consulta: datetime = field(default_factory=datetime.now)
    tiempo_consulta: float = 0.0
    consulta_exitosa: bool = False
    mensaje_error: str = ""
    tipo_consulta: str = TipoConsulta.COMPLETO_PROPIETARIO.value

    def procesar_datos_completos(self):
        """Procesar y analizar todos los datos"""
        self._agrupar_rubros_por_beneficiario()
        self._analizar_componentes_por_tipo()
        self._analizar_plan_iacv()
        self._calcular_totales_pagos()
        self._realizar_analisis_consolidado()
        self._analizar_matricula()

    def _agrupar_rubros_por_beneficiario(self):
        """Agrupar rubros por beneficiario"""
        agrupados = {}
        totales = {}

        for rubro in self.rubros_deuda:
            beneficiario = rubro.nombre_corto_beneficiario or "DESCONOCIDO"
            valor = rubro.valor_rubro or 0

            if beneficiario not in agrupados:
                agrupados[beneficiario] = {
                    "rubros": [],
                    "total_valor": 0,
                    "cantidad_rubros": 0,
                    "tipos_deuda": set(),
                }

            agrupados[beneficiario]["rubros"].append(rubro.to_dict())
            agrupados[beneficiario]["total_valor"] += valor
            agrupados[beneficiario]["cantidad_rubros"] += 1
            agrupados[beneficiario]["tipos_deuda"].add(rubro.descripcion_rubro)

            totales[beneficiario] = agrupados[beneficiario]["total_valor"]

        # Convertir sets a listas para serialización
        for beneficiario in agrupados:
            agrupados[beneficiario]["tipos_deuda"] = list(
                agrupados[beneficiario]["tipos_deuda"]
            )

        self.rubros_agrupados_por_beneficiario = agrupados
        self.totales_por_beneficiario = totales

    def _analizar_componentes_por_tipo(self):
        """Analizar componentes por tipo"""
        totales = {
            "impuestos": 0.0,
            "tasas": 0.0,
            "intereses": 0.0,
            "multas": 0.0,
            "prescripciones": 0.0,
        }

        total_general = 0.0

        for componente in self.componentes_deuda:
            valor = componente.valor_componente or 0
            tipo = componente.tipo_componente

            if tipo == TipoComponente.IMPUESTO.value and valor > 0:
                totales["impuestos"] += valor
            elif tipo == TipoComponente.TASA.value and valor > 0:
                totales["tasas"] += valor
            elif tipo == TipoComponente.INTERES.value and valor > 0:
                totales["intereses"] += valor
            elif tipo == TipoComponente.MULTA.value and valor > 0:
                totales["multas"] += valor
            elif tipo == TipoComponente.PRESCRIPCION.value:
                totales["prescripciones"] += valor  # Puede ser negativo

            # Solo sumar valores positivos al total
            if valor > 0:
                total_general += valor

        self.total_impuestos = totales["impuestos"]
        self.total_tasas = totales["tasas"]
        self.total_intereses = totales["intereses"]
        self.total_multas = totales["multas"]
        self.total_prescripciones = totales["prescripciones"]
        self.total_deudas_sri = total_general

    def _analizar_plan_iacv(self):
        """Analizar plan IACV"""
        total_vencidas = 0.0
        estados_count = {}

        for cuota in self.plan_iacv:
            estado = cuota.estado_pago
            estados_count[estado] = estados_count.get(estado, 0) + 1

            if estado == "VENCIDO":
                total_vencidas += cuota.total_cuota or 0

        self.total_cuotas_vencidas = total_vencidas
        self.cuotas_por_estado = estados_count

    def _calcular_totales_pagos(self):
        """Calcular totales de pagos"""
        total_pagos = 0.0
        pagos_ultimo_ano = 0.0
        ano_actual = datetime.now().year

        for pago in self.historial_pagos:
            monto = pago.monto or 0
            total_pagos += monto

            # Pagos del último año
            if pago.fecha_pago and str(ano_actual) in pago.fecha_pago:
                pagos_ultimo_ano += monto

        self.total_pagos_realizados = total_pagos
        self.pagos_ultimo_ano = pagos_ultimo_ano

        # Calcular promedio anual
        if len(self.historial_pagos) > 0:
            anos_con_pagos = len(
                set(
                    p.fecha_pago[:4]
                    for p in self.historial_pagos
                    if p.fecha_pago and len(p.fecha_pago) >= 4
                )
            )
            if anos_con_pagos > 0:
                self.promedio_pago_anual = total_pagos / anos_con_pagos

    def _realizar_analisis_consolidado(self):
        """Realizar análisis consolidado SRI"""
        self.analisis.calcular_puntuacion(
            self.total_deudas_sri,
            self.total_multas,
            self.total_intereses,
            self.total_cuotas_vencidas,
            self.total_pagos_realizados,
            self.prohibido_enajenar,
        )

        self.analisis.determinar_estado_legal()

        # Estimación de valor
        if self.anio_auto > 0:
            ano_actual = datetime.now().year
            antiguedad = ano_actual - self.anio_auto

            valor_base = 15000
            factor_depreciacion = max(0.1, (1 - 0.08) ** antiguedad)
            valor_estimado = valor_base * factor_depreciacion

            if self.total_deudas_sri > 0:
                valor_estimado *= 0.9

            self.analisis.estimacion_valor = max(valor_estimado, 1000)

    def _analizar_matricula(self):
        """Analizar estado de matrícula"""
        if self.fecha_caducidad_matricula:
            try:
                fecha_vencimiento = datetime.strptime(
                    self.fecha_caducidad_matricula.split(" ")[0], "%d-%m-%Y"
                )
                today = datetime.now()
                dias_diferencia = (fecha_vencimiento - today).days

                self.dias_hasta_vencimiento = dias_diferencia

                if dias_diferencia > 30:
                    self.estado_matricula = "VIGENTE"
                elif dias_diferencia > 0:
                    self.estado_matricula = "POR VENCER"
                else:
                    self.estado_matricula = "VENCIDA"
            except:
                self.estado_matricula = "INDETERMINADO"

    def get_resumen_completo(self) -> Dict[str, Any]:
        """Obtener resumen completo optimizado para frontend"""
        return {
            "propietario": self.propietario.to_dict(),
            "vehiculo_basico": {
                "placa": self.numero_placa,
                "marca": self.descripcion_marca,
                "modelo": self.descripcion_modelo,
                "anio": self.anio_auto,
                "clase": self.nombre_clase,
                "color_primario": self.color_vehiculo1,
                "color_secundario": self.color_vehiculo2,
                "cilindraje": self.cilindraje,
                "pais": self.descripcion_pais,
            },
            "deudas_sri_completas": {
                "total_general": self.total_deudas_sri,
                "desglose": {
                    "impuestos": self.total_impuestos,
                    "tasas": self.total_tasas,
                    "multas": self.total_multas,
                    "intereses": self.total_intereses,
                    "prescripciones": self.total_prescripciones,
                },
                "rubros_count": len(self.rubros_deuda),
                "componentes_count": len(self.componentes_deuda),
                "beneficiarios": list(self.totales_por_beneficiario.keys()),
                "rubros_detallados": [r.to_dict() for r in self.rubros_deuda],
                "componentes_detallados": [c.to_dict() for c in self.componentes_deuda],
                "agrupado_beneficiarios": self.rubros_agrupados_por_beneficiario,
            },
            "pagos_sri_completos": {
                "total_pagado": self.total_pagos_realizados,
                "pagos_ultimo_ano": self.pagos_ultimo_ano,
                "promedio_anual": self.promedio_pago_anual,
                "historial_completo": [p.to_dict() for p in self.historial_pagos],
                "total_transacciones": len(self.historial_pagos),
            },
            "iacv_completo": {
                "cuotas_vencidas": self.total_cuotas_vencidas,
                "total_cuotas": len(self.plan_iacv),
                "estados_cuotas": self.cuotas_por_estado,
                "plan_detallado": [c.to_dict() for c in self.plan_iacv],
            },
            "estados_legales": {
                "matricula": {
                    "ultima": self.fecha_ultima_matricula,
                    "vencimiento": self.fecha_caducidad_matricula,
                    "estado": self.estado_matricula,
                    "dias_vencimiento": self.dias_hasta_vencimiento,
                    "ultimo_anio_pagado": self.ultimo_anio_pagado,
                },
                "prohibiciones": {
                    "enajenar": self.prohibido_enajenar,
                    "exoneracion": self.estado_exoneracion,
                    "observaciones": self.observacion,
                },
                "ubicacion": {
                    "canton": self.descripcion_canton,
                    "servicio": self.descripcion_servicio,
                },
            },
            "analisis_completo": self.analisis.to_dict(),
            "metadatos": {
                "session_id": self.session_id,
                "tiempo_consulta": self.tiempo_consulta,
                "timestamp": self.timestamp_consulta.isoformat(),
                "consulta_exitosa": self.consulta_exitosa,
                "tipo_consulta": self.tipo_consulta,
            },
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convertir todo el modelo a diccionario"""
        data = {
            # Datos básicos
            "numero_placa": self.numero_placa,
            "placa_original": self.placa_original,
            "placa_normalizada": self.placa_normalizada,
            "codigo_vehiculo": self.codigo_vehiculo,
            "numero_camv_cpn": self.numero_camv_cpn,
            "session_id": self.session_id,
            # Propietario
            "propietario_nombre": self.propietario.nombre,
            "propietario_cedula": self.propietario.cedula,
            "propietario_encontrado": self.propietario.encontrado,
            # Información del vehículo
            "vin_chasis": self.vin_chasis,
            "numero_motor": self.numero_motor,
            "descripcion_marca": self.descripcion_marca,
            "descripcion_modelo": self.descripcion_modelo,
            "anio_auto": self.anio_auto,
            "descripcion_pais": self.descripcion_pais,
            "color_vehiculo1": self.color_vehiculo1,
            "color_vehiculo2": self.color_vehiculo2,
            "cilindraje": self.cilindraje,
            "nombre_clase": self.nombre_clase,
            # Matrícula
            "fecha_ultima_matricula": self.fecha_ultima_matricula,
            "fecha_caducidad_matricula": self.fecha_caducidad_matricula,
            "descripcion_canton": self.descripcion_canton,
            "descripcion_servicio": self.descripcion_servicio,
            "ultimo_anio_pagado": self.ultimo_anio_pagado,
            "estado_matricula": self.estado_matricula,
            "dias_hasta_vencimiento": self.dias_hasta_vencimiento,
            # Estados legales
            "prohibido_enajenar": self.prohibido_enajenar,
            "estado_exoneracion": self.estado_exoneracion,
            "observacion": self.observacion,
            # Datos SRI
            "rubros_deuda": [r.to_dict() for r in self.rubros_deuda],
            "componentes_deuda": [c.to_dict() for c in self.componentes_deuda],
            "historial_pagos": [p.to_dict() for p in self.historial_pagos],
            "plan_excepcional_iacv": [c.to_dict() for c in self.plan_iacv],
            # Totales
            "total_deudas_sri": self.total_deudas_sri,
            "total_impuestos": self.total_impuestos,
            "total_tasas": self.total_tasas,
            "total_intereses": self.total_intereses,
            "total_multas": self.total_multas,
            "total_prescripciones": self.total_prescripciones,
            "total_pagos_realizados": self.total_pagos_realizados,
            "pagos_ultimo_ano": self.pagos_ultimo_ano,
            "promedio_pago_anual": self.promedio_pago_anual,
            "total_cuotas_vencidas": self.total_cuotas_vencidas,
            # Agrupaciones
            "rubros_agrupados_por_beneficiario": self.rubros_agrupados_por_beneficiario,
            "totales_por_beneficiario": self.totales_por_beneficiario,
            "cuotas_por_estado": self.cuotas_por_estado,
            # Análisis
            "estado_legal_sri": self.analisis.estado_legal_sri,
            "riesgo_tributario": self.analisis.riesgo_tributario,
            "puntuacion_sri": self.analisis.puntuacion_sri,
            "recomendacion_tributaria": self.analisis.recomendacion_tributaria,
            "estimacion_valor": self.analisis.estimacion_valor,
            # Metadatos
            "timestamp_consulta": self.timestamp_consulta.isoformat(),
            "tiempo_consulta": self.tiempo_consulta,
            "consulta_exitosa": self.consulta_exitosa,
            "mensaje_error": self.mensaje_error,
            "tipo_consulta": self.tipo_consulta,
        }

        return data


# ==========================================
# MODELO DE SESIÓN DE CONSULTA
# ==========================================


@dataclass
class SesionConsulta:
    """Sesión de consulta activa"""

    session_id: str = ""
    usuario: Optional[UsuarioECPlacas] = None
    placa_consultada: str = ""
    estado: str = EstadoConsulta.INICIANDO.value
    progreso: int = 0
    mensaje_estado: str = ""
    datos_vehiculares: Optional[DatosVehicularesCompletos] = None
    started_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    def actualizar_estado(
        self, nuevo_estado: EstadoConsulta, progreso: int, mensaje: str
    ):
        """Actualizar estado de la sesión"""
        self.estado = nuevo_estado.value
        self.progreso = progreso
        self.mensaje_estado = mensaje
        self.last_activity = datetime.now()

        if nuevo_estado in [EstadoConsulta.COMPLETADO, EstadoConsulta.ERROR]:
            self.completed_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para API"""
        return {
            "session_id": self.session_id,
            "placa_consultada": self.placa_consultada,
            "estado": self.estado,
            "progreso": self.progreso,
            "mensaje_estado": self.mensaje_estado,
            "started_at": self.started_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "usuario": self.usuario.to_dict() if self.usuario else None,
            "datos_disponibles": self.datos_vehiculares is not None,
        }


# ==========================================
# FUNCIONES DE UTILIDAD
# ==========================================


def crear_vehiculo_desde_dict(data: Dict[str, Any]) -> DatosVehicularesCompletos:
    """Crear modelo de vehículo desde diccionario"""
    vehiculo = DatosVehicularesCompletos()

    # Mapear campos básicos
    for field_name, field_value in data.items():
        if hasattr(vehiculo, field_name):
            setattr(vehiculo, field_name, field_value)

    # Crear propietario si existe
    if "propietario_nombre" in data or "propietario_cedula" in data:
        vehiculo.propietario = PropietarioVehiculo(
            nombre=data.get("propietario_nombre", ""),
            cedula=data.get("propietario_cedula", ""),
            encontrado=data.get("propietario_encontrado", False),
        )

    # Procesar rubros
    if "rubros_deuda" in data and isinstance(data["rubros_deuda"], list):
        vehiculo.rubros_deuda = [
            RubroSRI(**rubro) if isinstance(rubro, dict) else rubro
            for rubro in data["rubros_deuda"]
        ]

    # Procesar componentes
    if "componentes_deuda" in data and isinstance(data["componentes_deuda"], list):
        vehiculo.componentes_deuda = [
            ComponenteSRI(**comp) if isinstance(comp, dict) else comp
            for comp in data["componentes_deuda"]
        ]

    # Procesar pagos
    if "historial_pagos" in data and isinstance(data["historial_pagos"], list):
        vehiculo.historial_pagos = [
            PagoSRI(**pago) if isinstance(pago, dict) else pago
            for pago in data["historial_pagos"]
        ]

    # Procesar IACV
    if "plan_excepcional_iacv" in data and isinstance(
        data["plan_excepcional_iacv"], list
    ):
        vehiculo.plan_iacv = [
            CuotaIACV(**cuota) if isinstance(cuota, dict) else cuota
            for cuota in data["plan_excepcional_iacv"]
        ]

    return vehiculo


# Exportar modelos principales
__all__ = [
    "UsuarioECPlacas",
    "PropietarioVehiculo",
    "RubroSRI",
    "ComponenteSRI",
    "PagoSRI",
    "CuotaIACV",
    "AnalisisSRI",
    "DatosVehicularesCompletos",
    "SesionConsulta",
    "TipoConsulta",
    "EstadoConsulta",
    "TipoComponente",
    "EstadoLegalSRI",
    "RiesgoTributario",
    "crear_vehiculo_desde_dict",
]
