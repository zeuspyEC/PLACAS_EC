#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECPlacas 2.0 - Módulo Scraper Vehicular
Proyecto: Construcción de Software
Desarrollado por: Erick Costa

Módulo especializado para consultas a APIs externas de datos vehiculares
"""

import asyncio
import hashlib
import json
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

import aiohttp
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .models import ValidadorEcuatoriano, VehiculoCompleto

logger = logging.getLogger(__name__)


class VehicleScraperConfig:
    """Configuración del scraper vehicular"""

    # APIs principales
    APIS = {
        "ant_principal": {
            "base_url": "https://servicios.axiscloud.ec/CRV/paginas",
            "endpoint": "/datosVehiculo.jsp",
            "params": {"empresa": "02"},
            "timeout": 30,
            "retry_attempts": 3,
            "rate_limit": 1.0,  # segundos entre requests
            "active": True,
        },
        "ant_backup": {
            "base_url": "https://servicios.axiscloud.ec/CRV/paginas",
            "endpoint": "/datosVehiculo.jsp",
            "params": {"empresa": "01"},
            "timeout": 25,
            "retry_attempts": 2,
            "rate_limit": 1.5,
            "active": True,
        },
    }

    # Headers rotativos para evitar detección
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]

    # Configuración de cache
    CACHE_CONFIG = {
        "enabled": True,
        "ttl_hours": 24,  # Time to live en horas
        "max_entries": 1000,
    }


class VehicleCache:
    """Cache inteligente para consultas vehiculares"""

    def __init__(self, ttl_hours: int = 24, max_entries: int = 1000):
        self.cache = {}
        self.ttl_hours = ttl_hours
        self.max_entries = max_entries
        self.access_times = {}

    def _generate_key(self, placa: str, api_name: str) -> str:
        """Genera clave única para cache"""
        return hashlib.md5(f"{placa}_{api_name}".encode()).hexdigest()

    def get(self, placa: str, api_name: str) -> Optional[Dict]:
        """Obtiene datos del cache si están vigentes"""
        try:
            key = self._generate_key(placa, api_name)

            if key in self.cache:
                entry = self.cache[key]
                timestamp = entry["timestamp"]

                # Verificar si no ha expirado
                age_hours = (datetime.now() - timestamp).total_seconds() / 3600
                if age_hours < self.ttl_hours:
                    self.access_times[key] = datetime.now()
                    logger.info(f"🎯 Cache HIT para {placa} (edad: {age_hours:.1f}h)")
                    return entry["data"]
                else:
                    # Expired, remove
                    del self.cache[key]
                    if key in self.access_times:
                        del self.access_times[key]
                    logger.info(f"⏰ Cache EXPIRED para {placa}")

            return None

        except Exception as e:
            logger.error(f"❌ Error obteniendo del cache: {e}")
            return None

    def set(self, placa: str, api_name: str, data: Dict):
        """Almacena datos en cache"""
        try:
            key = self._generate_key(placa, api_name)

            # Limpiar cache si está lleno
            if len(self.cache) >= self.max_entries:
                self._cleanup_cache()

            self.cache[key] = {
                "data": data,
                "timestamp": datetime.now(),
                "placa": placa,
                "api": api_name,
            }
            self.access_times[key] = datetime.now()

            logger.info(f"💾 Cache SET para {placa}")

        except Exception as e:
            logger.error(f"❌ Error guardando en cache: {e}")

    def _cleanup_cache(self):
        """Limpia entradas antiguas del cache"""
        try:
            # Remover entradas expiradas
            current_time = datetime.now()
            expired_keys = []

            for key, entry in self.cache.items():
                age_hours = (current_time - entry["timestamp"]).total_seconds() / 3600
                if age_hours >= self.ttl_hours:
                    expired_keys.append(key)

            for key in expired_keys:
                del self.cache[key]
                if key in self.access_times:
                    del self.access_times[key]

            # Si aún está lleno, remover las menos accedidas
            if len(self.cache) >= self.max_entries:
                # Ordenar por último acceso
                sorted_keys = sorted(
                    self.access_times.keys(), key=lambda k: self.access_times[k]
                )

                # Remover el 20% más antiguo
                remove_count = max(1, len(sorted_keys) // 5)
                for key in sorted_keys[:remove_count]:
                    if key in self.cache:
                        del self.cache[key]
                    if key in self.access_times:
                        del self.access_times[key]

            logger.info(
                f"🧹 Cache limpiado: {len(expired_keys)} expiradas, {len(self.cache)} entradas restantes"
            )

        except Exception as e:
            logger.error(f"❌ Error limpiando cache: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del cache"""
        try:
            current_time = datetime.now()
            total_entries = len(self.cache)
            expired_count = 0
            age_distribution = {
                "0-1h": 0,
                "1-6h": 0,
                "6-12h": 0,
                "12-24h": 0,
                "+24h": 0,
            }

            for entry in self.cache.values():
                age_hours = (current_time - entry["timestamp"]).total_seconds() / 3600

                if age_hours >= self.ttl_hours:
                    expired_count += 1
                elif age_hours < 1:
                    age_distribution["0-1h"] += 1
                elif age_hours < 6:
                    age_distribution["1-6h"] += 1
                elif age_hours < 12:
                    age_distribution["6-12h"] += 1
                elif age_hours < 24:
                    age_distribution["12-24h"] += 1
                else:
                    age_distribution["+24h"] += 1

            return {
                "total_entries": total_entries,
                "expired_entries": expired_count,
                "valid_entries": total_entries - expired_count,
                "max_entries": self.max_entries,
                "usage_percent": (total_entries / self.max_entries) * 100,
                "ttl_hours": self.ttl_hours,
                "age_distribution": age_distribution,
            }

        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas de cache: {e}")
            return {}


class VehicleScraper:
    """Scraper principal para consultas vehiculares ECPlacas 2.0"""

    def __init__(self, use_cache: bool = True):
        self.config = VehicleScraperConfig()
        self.cache = VehicleCache() if use_cache else None
        self.session = self._create_session()
        self.last_request_time = {}
        self.request_count = {"today": 0, "total": 0}
        self.success_rate = {"successful": 0, "total": 0}

    def _create_session(self) -> requests.Session:
        """Crea sesión HTTP optimizada"""
        session = requests.Session()

        # Configurar retry strategy
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1,
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Headers por defecto
        session.headers.update(
            {
                "Accept": "application/json, text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8",
                "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "Upgrade-Insecure-Requests": "1",
            }
        )

        return session

    def _get_random_headers(self) -> Dict[str, str]:
        """Obtiene headers aleatorios para evitar detección"""
        return {
            "User-Agent": random.choice(self.config.USER_AGENTS),
            "X-Forwarded-For": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
            "X-Real-IP": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
        }

    def _apply_rate_limit(self, api_name: str):
        """Aplica rate limiting por API"""
        try:
            api_config = self.config.APIS.get(api_name, {})
            rate_limit = api_config.get("rate_limit", 1.0)

            if api_name in self.last_request_time:
                elapsed = time.time() - self.last_request_time[api_name]
                if elapsed < rate_limit:
                    sleep_time = rate_limit - elapsed
                    logger.info(
                        f"⏱️ Rate limiting: esperando {sleep_time:.2f}s para {api_name}"
                    )
                    time.sleep(sleep_time)

            self.last_request_time[api_name] = time.time()

        except Exception as e:
            logger.error(f"❌ Error aplicando rate limit: {e}")

    async def consultar_vehiculo(self, placa: str) -> VehiculoCompleto:
        """
        Consulta principal de datos vehiculares
        Intenta múltiples APIs en orden de prioridad
        """
        start_time = time.time()
        vehiculo = VehiculoCompleto()
        vehiculo.numero_placa = placa
        vehiculo.timestamp_consulta = datetime.now()

        # Validar y normalizar placa
        es_valida, placa_normalizada, error_placa = ValidadorEcuatoriano.validar_placa(
            placa
        )
        if not es_valida:
            vehiculo.consulta_exitosa = False
            vehiculo.mensaje_error = f"Placa inválida: {error_placa}"
            vehiculo.tiempo_consulta = time.time() - start_time
            return vehiculo

        vehiculo.placa_original = placa
        vehiculo.placa_normalizada = placa_normalizada
        vehiculo.numero_placa = placa_normalizada

        logger.info(
            f"🚀 Iniciando consulta ECPlacas 2.0 para: {placa} → {placa_normalizada}"
        )

        # Intentar APIs en orden de prioridad
        apis_ordenadas = [
            (name, config)
            for name, config in self.config.APIS.items()
            if config.get("active", True)
        ]

        for api_name, api_config in apis_ordenadas:
            try:
                logger.info(f"🔍 Intentando API: {api_name}")

                # Verificar cache primero
                if self.cache:
                    cached_data = self.cache.get(placa_normalizada, api_name)
                    if cached_data:
                        vehiculo.procesar_datos_api(cached_data)
                        vehiculo.consulta_exitosa = True
                        vehiculo.tiempo_consulta = time.time() - start_time
                        logger.info(
                            f"✅ Consulta exitosa desde CACHE para {placa_normalizada}"
                        )
                        return vehiculo

                # Aplicar rate limiting
                self._apply_rate_limit(api_name)

                # Realizar consulta
                api_response = await self._consultar_api(
                    api_name, api_config, placa_normalizada
                )

                if api_response and self._validar_respuesta(api_response):
                    # Procesar datos exitosos
                    vehiculo.procesar_datos_api(api_response)
                    vehiculo.consulta_exitosa = True

                    # Guardar en cache
                    if self.cache:
                        self.cache.set(placa_normalizada, api_name, api_response)

                    # Actualizar estadísticas
                    self.success_rate["successful"] += 1

                    vehiculo.tiempo_consulta = time.time() - start_time
                    logger.info(
                        f"✅ Consulta exitosa desde {api_name} para {placa_normalizada} ({vehiculo.tiempo_consulta:.2f}s)"
                    )
                    return vehiculo
                else:
                    logger.warning(
                        f"⚠️ API {api_name} retornó datos inválidos para {placa_normalizada}"
                    )
                    continue

            except Exception as e:
                logger.error(f"❌ Error en API {api_name}: {e}")
                continue

            finally:
                self.success_rate["total"] += 1
                self.request_count["total"] += 1

        # Si llegamos aquí, todas las APIs fallaron
        vehiculo.consulta_exitosa = False
        vehiculo.mensaje_error = "No se pudo obtener datos de ninguna API disponible"
        vehiculo.tiempo_consulta = time.time() - start_time

        logger.error(f"❌ Todas las APIs fallaron para {placa_normalizada}")
        return vehiculo

    async def _consultar_api(
        self, api_name: str, api_config: Dict, placa: str
    ) -> Optional[Dict]:
        """Consulta una API específica"""
        try:
            # Construir URL
            base_url = api_config["base_url"]
            endpoint = api_config["endpoint"]
            url = f"{base_url}{endpoint}"

            # Parámetros
            params = api_config.get("params", {}).copy()
            params["identidad"] = placa

            # Headers aleatorios
            headers = self._get_random_headers()

            # Timeout
            timeout = api_config.get("timeout", 30)

            logger.info(f"📡 Consultando {url} con placa {placa}")

            # Realizar request
            response = self.session.get(
                url, params=params, headers=headers, timeout=timeout, verify=True
            )

            response.raise_for_status()

            # Parsear respuesta
            if response.headers.get("content-type", "").startswith("application/json"):
                data = response.json()
            else:
                # Intentar parsear como JSON de todas formas
                try:
                    data = response.json()
                except:
                    logger.error(f"❌ Respuesta no es JSON válido desde {api_name}")
                    return None

            logger.info(
                f"✅ Respuesta exitosa desde {api_name} ({len(json.dumps(data))} chars)"
            )
            return data

        except requests.exceptions.Timeout:
            logger.error(f"⏱️ Timeout en API {api_name} después de {timeout}s")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"🔌 Error de conexión en API {api_name}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"🌐 Error HTTP en API {api_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error inesperado en API {api_name}: {e}")
            return None

    def _validar_respuesta(self, data: Dict) -> bool:
        """Valida que la respuesta de la API sea válida"""
        try:
            if not isinstance(data, dict):
                return False

            # Verificar estructura básica
            if "codError" not in data:
                return False

            # Verificar código de error
            cod_error = data.get("codError")
            if cod_error != "0":
                mensaje_error = data.get("mensajeError", "Error desconocido")
                logger.warning(f"⚠️ API retornó error: {cod_error} - {mensaje_error}")
                return False

            # Verificar que tenga campos de datos
            campos = data.get("campos", {})
            if not campos:
                logger.warning("⚠️ Respuesta sin campos de datos")
                return False

            # Verificar al menos un conjunto de datos importante
            datos_importantes = [
                "lsDatosIdentificacion",
                "lsDatosModelo",
                "lsOtrasCaracteristicas",
                "lsRevision",
            ]

            tiene_datos = any(campos.get(campo) for campo in datos_importantes)
            if not tiene_datos:
                logger.warning("⚠️ Respuesta sin datos vehiculares importantes")
                return False

            return True

        except Exception as e:
            logger.error(f"❌ Error validando respuesta: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas del scraper"""
        try:
            stats = {
                "request_count": self.request_count.copy(),
                "success_rate": {
                    "percentage": (
                        (
                            self.success_rate["successful"]
                            / self.success_rate["total"]
                            * 100
                        )
                        if self.success_rate["total"] > 0
                        else 0
                    ),
                    "successful": self.success_rate["successful"],
                    "total": self.success_rate["total"],
                },
                "apis_status": {},
                "cache_stats": self.cache.get_stats() if self.cache else None,
            }

            # Estado de APIs
            for api_name, api_config in self.config.APIS.items():
                stats["apis_status"][api_name] = {
                    "active": api_config.get("active", False),
                    "base_url": api_config.get("base_url", ""),
                    "timeout": api_config.get("timeout", 0),
                    "rate_limit": api_config.get("rate_limit", 0),
                    "last_request": self.last_request_time.get(api_name, 0),
                }

            return stats

        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {}

    def clear_cache(self):
        """Limpia completamente el cache"""
        if self.cache:
            self.cache.cache.clear()
            self.cache.access_times.clear()
            logger.info("🧹 Cache limpiado completamente")

    def test_apis(self, placa_test: str = "TBX0160") -> Dict[str, Any]:
        """Prueba todas las APIs con una placa de testing"""
        results = {}

        for api_name, api_config in self.config.APIS.items():
            if not api_config.get("active", True):
                results[api_name] = {"status": "inactive"}
                continue

            try:
                start_time = time.time()

                # Aplicar rate limiting
                self._apply_rate_limit(api_name)

                # Realizar consulta de prueba
                response = asyncio.run(
                    self._consultar_api(api_name, api_config, placa_test)
                )

                elapsed_time = time.time() - start_time

                if response and self._validar_respuesta(response):
                    results[api_name] = {
                        "status": "success",
                        "response_time": round(elapsed_time, 2),
                        "data_fields": list(response.get("campos", {}).keys()),
                        "message": "API funcionando correctamente",
                    }
                else:
                    results[api_name] = {
                        "status": "error",
                        "response_time": round(elapsed_time, 2),
                        "message": "Respuesta inválida o vacía",
                    }

            except Exception as e:
                results[api_name] = {"status": "error", "message": str(e)}

        return results

    def close(self):
        """Cierra recursos del scraper"""
        try:
            if self.session:
                self.session.close()
            logger.info("🔒 Scraper cerrado correctamente")
        except Exception as e:
            logger.error(f"❌ Error cerrando scraper: {e}")


# Instancia global del scraper
vehicle_scraper = VehicleScraper()


# Función de conveniencia para uso directo
async def consultar_placa(placa: str) -> VehiculoCompleto:
    """
    Función de conveniencia para consultar una placa
    """
    return await vehicle_scraper.consultar_vehiculo(placa)


if __name__ == "__main__":
    # Pruebas del scraper
    async def test_scraper():
        print("🧪 Probando ECPlacas Scraper...")

        # Prueba de APIs
        print("\n📡 Probando APIs...")
        api_results = vehicle_scraper.test_apis()
        for api_name, result in api_results.items():
            status = result["status"]
            emoji = "✅" if status == "success" else "❌" if status == "error" else "⏸️"
            print(f"{emoji} {api_name}: {result.get('message', status)}")

        # Prueba de consulta real
        print("\n🚗 Probando consulta real...")
        vehiculo = await vehicle_scraper.consultar_vehiculo("TBX0160")

        if vehiculo.consulta_exitosa:
            print(f"✅ Consulta exitosa:")
            print(f"   Placa: {vehiculo.numero_placa}")
            print(f"   Marca: {vehiculo.modelo.marca}")
            print(f"   Modelo: {vehiculo.modelo.modelo}")
            print(f"   Año: {vehiculo.modelo.anio_fabricacion}")
            print(f"   Estado: {vehiculo.analisis.estado_matricula.value}")
            print(f"   Tiempo: {vehiculo.tiempo_consulta:.2f}s")
        else:
            print(f"❌ Consulta fallida: {vehiculo.mensaje_error}")

        # Estadísticas
        print("\n📊 Estadísticas:")
        stats = vehicle_scraper.get_statistics()
        print(f"   Requests totales: {stats['request_count']['total']}")
        print(f"   Tasa de éxito: {stats['success_rate']['percentage']:.1f}%")
        if stats["cache_stats"]:
            print(f"   Cache entries: {stats['cache_stats']['valid_entries']}")

        vehicle_scraper.close()
        print("\n✅ Pruebas completadas")

    # Ejecutar pruebas
    asyncio.run(test_scraper())
