#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECPlacas 2.0 - Utilidades del Sistema
Proyecto: Construcción de Software
Desarrollado por: Erick Costa

Funciones de utilidad para ECPlacas 2.0
"""

import re
import time
import json
import hashlib
import secrets
import string
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from functools import wraps
from pathlib import Path
import logging
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.base import MimeBase
from email import encoders
import qrcode
from io import BytesIO
import base64

logger = logging.getLogger(__name__)

class TextUtils:
    """Utilidades para procesamiento de texto"""
    
    @staticmethod
    def clean_string(text: str, allow_spaces: bool = True) -> str:
        """Limpiar string removiendo caracteres especiales"""
        if not text:
            return ""
        
        if allow_spaces:
            return re.sub(r'[^\w\s]', '', text).strip()
        else:
            return re.sub(r'[^\w]', '', text).strip()
    
    @staticmethod
    def normalize_name(name: str) -> str:
        """Normalizar nombre a formato estándar"""
        if not name:
            return ""
        
        # Remover caracteres especiales excepto letras, espacios y acentos
        clean_name = re.sub(r'[^a-zA-ZáéíóúñÁÉÍÓÚÑ\s]', '', name)
        
        # Convertir a título y normalizar espacios
        return ' '.join(clean_name.upper().split())
    
    @staticmethod
    def normalize_phone(phone: str, country_code: str = "+593") -> str:
        """Normalizar número telefónico"""
        if not phone:
            return ""
        
        # Remover todo excepto dígitos
        digits_only = re.sub(r'\D', '', phone)
        
        # Formatear según código de país
        if country_code == "+593":  # Ecuador
            if len(digits_only) == 9 and digits_only.startswith('9'):
                return f"0{digits_only}"
            elif len(digits_only) == 10 and digits_only.startswith('09'):
                return digits_only
            elif len(digits_only) == 8:
                return f"0{digits_only}"
        
        return digits_only
    
    @staticmethod
    def format_currency(amount: float, currency: str = "USD") -> str:
        """Formatear cantidad como moneda"""
        try:
            if currency == "USD":
                return f"${amount:,.2f}"
            else:
                return f"{amount:,.2f} {currency}"
        except:
            return str(amount)
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
        """Truncar texto a longitud máxima"""
        if not text:
            return ""
        
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix

class DateUtils:
    """Utilidades para manejo de fechas"""
    
    @staticmethod
    def parse_date(date_str: str, format_str: str = "%d-%m-%Y") -> Optional[datetime]:
        """Parsear string de fecha a datetime"""
        try:
            return datetime.strptime(date_str.split(' ')[0], format_str)
        except:
            return None
    
    @staticmethod
    def format_date(date_obj: datetime, format_str: str = "%d-%m-%Y") -> str:
        """Formatear datetime a string"""
        try:
            return date_obj.strftime(format_str)
        except:
            return ""
    
    @staticmethod
    def calculate_age(birth_date: datetime) -> int:
        """Calcular edad en años"""
        try:
            today = datetime.now()
            return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        except:
            return 0
    
    @staticmethod
    def days_between(date1: datetime, date2: datetime) -> int:
        """Calcular días entre dos fechas"""
        try:
            return abs((date2 - date1).days)
        except:
            return 0
    
    @staticmethod
    def format_relative_time(date_obj: datetime) -> str:
        """Formatear fecha en tiempo relativo"""
        try:
            now = datetime.now()
            diff = now - date_obj
            
            if diff.days > 365:
                years = diff.days // 365
                return f"hace {years} año{'s' if years > 1 else ''}"
            elif diff.days > 30:
                months = diff.days // 30
                return f"hace {months} mes{'es' if months > 1 else ''}"
            elif diff.days > 0:
                return f"hace {diff.days} día{'s' if diff.days > 1 else ''}"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"hace {hours} hora{'s' if hours > 1 else ''}"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"hace {minutes} minuto{'s' if minutes > 1 else ''}"
            else:
                return "hace un momento"
        except:
            return "fecha desconocida"

class SecurityUtils:
    """Utilidades de seguridad"""
    
    @staticmethod
    def generate_token(length: int = 32) -> str:
        """Generar token aleatorio seguro"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def hash_string(text: str, salt: str = "") -> str:
        """Crear hash SHA256 de un string"""
        return hashlib.sha256((text + salt).encode()).hexdigest()
    
    @staticmethod
    def generate_session_id() -> str:
        """Generar ID de sesión único"""
        timestamp = str(int(time.time() * 1000))
        random_part = secrets.token_hex(8)
        return f"ecplacas_{timestamp}_{random_part}"
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """Sanitizar entrada de usuario"""
        if not text:
            return ""
        
        # Remover caracteres peligrosos
        dangerous_chars = ['<', '>', '"', "'", '&', 'script', 'javascript:', 'vbscript:', 'onload', 'onerror']
        
        clean_text = text
        for char in dangerous_chars:
            clean_text = clean_text.replace(char, '')
        
        return clean_text.strip()
    
    @staticmethod
    def validate_ip(ip: str) -> bool:
        """Validar formato de dirección IP"""
        try:
            import ipaddress
            ipaddress.ip_address(ip)
            return True
        except:
            return False

class RateLimiter:
    """Limitador de velocidad para APIs"""
    
    def __init__(self, max_requests: int = 50, time_window: int = 3600):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = {}
    
    def is_allowed(self, identifier: str) -> Tuple[bool, int]:
        """Verificar si se permite la request"""
        current_time = time.time()
        
        # Limpiar requests antiguos
        self._cleanup_old_requests(current_time)
        
        # Obtener requests del identificador
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        user_requests = self.requests[identifier]
        
        # Verificar límite
        if len(user_requests) >= self.max_requests:
            return False, self.max_requests - len(user_requests)
        
        # Agregar nueva request
        user_requests.append(current_time)
        return True, self.max_requests - len(user_requests)
    
    def _cleanup_old_requests(self, current_time: float):
        """Limpiar requests antiguas"""
        cutoff_time = current_time - self.time_window
        
        for identifier in list(self.requests.keys()):
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if req_time > cutoff_time
            ]
            
            # Remover identificadores sin requests
            if not self.requests[identifier]:
                del self.requests[identifier]

class FileUtils:
    """Utilidades para manejo de archivos"""
    
    @staticmethod
    def ensure_directory(path: Union[str, Path]) -> bool:
        """Asegurar que existe un directorio"""
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Error creando directorio {path}: {e}")
            return False
    
    @staticmethod
    def get_file_size(path: Union[str, Path]) -> int:
        """Obtener tamaño de archivo en bytes"""
        try:
            return Path(path).stat().st_size
        except:
            return 0
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Formatear tamaño de archivo"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    @staticmethod
    def safe_filename(filename: str) -> str:
        """Crear nombre de archivo seguro"""
        # Remover caracteres peligrosos
        safe_chars = re.sub(r'[^\w\-_\.]', '_', filename)
        
        # Limitar longitud
        if len(safe_chars) > 100:
            name, ext = safe_chars.rsplit('.', 1) if '.' in safe_chars else (safe_chars, '')
            safe_chars = name[:90] + ('.' + ext if ext else '')
        
        return safe_chars

class QRCodeGenerator:
    """Generador de códigos QR"""
    
    @staticmethod
    def generate_qr(data: str, size: int = 10, border: int = 4) -> str:
        """Generar código QR y retornar como base64"""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=size,
                border=border,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
        except Exception as e:
            logger.error(f"Error generando QR: {e}")
            return ""
    
    @staticmethod
    def generate_verification_qr(session_id: str, placa: str) -> str:
        """Generar QR de verificación para consulta"""
        verification_data = {
            'session_id': session_id,
            'placa': placa,
            'timestamp': datetime.now().isoformat(),
            'service': 'ECPlacas 2.0',
            'version': '2.0.0'
        }
        
        return QRCodeGenerator.generate_qr(json.dumps(verification_data))

class EmailService:
    """Servicio de envío de emails"""
    
    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str, use_tls: bool = True):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls
    
    def send_email(self, to_email: str, subject: str, body: str, is_html: bool = False, 
                   attachments: List[Dict] = None) -> bool:
        """Enviar email"""
        try:
            msg = MimeMultipart()
            msg['From'] = self.username
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Agregar cuerpo
            mime_type = 'html' if is_html else 'plain'
            msg.attach(MimeText(body, mime_type, 'utf-8'))
            
            # Agregar adjuntos
            if attachments:
                for attachment in attachments:
                    self._add_attachment(msg, attachment)
            
            # Enviar email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"✅ Email enviado exitosamente a {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error enviando email: {e}")
            return False
    
    def _add_attachment(self, msg: MimeMultipart, attachment: Dict):
        """Agregar adjunto al email"""
        try:
            with open(attachment['path'], 'rb') as file:
                part = MimeBase('application', 'octet-stream')
                part.set_payload(file.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {attachment["filename"]}'
                )
                msg.attach(part)
        except Exception as e:
            logger.error(f"Error agregando adjunto: {e}")

class TemplateEngine:
    """Motor de plantillas simple"""
    
    @staticmethod
    def render_template(template: str, context: Dict[str, Any]) -> str:
        """Renderizar plantilla con contexto"""
        try:
            result = template
            for key, value in context.items():
                placeholder = f"{{{{{key}}}}}"
                result = result.replace(placeholder, str(value))
            return result
        except Exception as e:
            logger.error(f"Error renderizando plantilla: {e}")
            return template
    
    @staticmethod
    def get_email_template(template_name: str = "consultation_result") -> str:
        """Obtener plantilla de email"""
        templates = {
            "consultation_result": """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>ECPlacas 2.0 - Resultado de Consulta</title>
                <style>
                    body { font-family: Arial, sans-serif; background: #f0f0f0; margin: 0; padding: 20px; }
                    .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
                    .header { background: linear-gradient(135deg, #000033, #0066ff); color: white; padding: 20px; text-align: center; border-radius: 10px; margin-bottom: 20px; }
                    .logo { font-size: 24px; font-weight: bold; color: #00ffff; }
                    .subtitle { color: #99ccff; margin-top: 5px; }
                    .content { color: #333; line-height: 1.6; }
                    .vehicle-info { background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0; }
                    .footer { text-align: center; color: #666; font-size: 12px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 15px; }
                    .qr-code { text-align: center; margin: 20px 0; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="logo">ECPlacas 2.0</div>
                        <div class="subtitle">Sistema de Consulta Vehicular</div>
                    </div>
                    
                    <div class="content">
                        <h2>Resultado de Consulta Vehicular</h2>
                        <p>Estimado/a <strong>{{usuario_nombre}}</strong>,</p>
                        <p>Su consulta para la placa <strong>{{numero_placa}}</strong> ha sido procesada exitosamente.</p>
                        
                        <div class="vehicle-info">
                            <h3>Información del Vehículo</h3>
                            <p><strong>Placa:</strong> {{numero_placa}}</p>
                            <p><strong>Marca:</strong> {{marca}}</p>
                            <p><strong>Modelo:</strong> {{modelo}}</p>
                            <p><strong>Año:</strong> {{anio_fabricacion}}</p>
                            <p><strong>Estado de Matrícula:</strong> {{estado_matricula}}</p>
                        </div>
                        
                        <div class="qr-code">
                            <p><strong>Código de Verificación:</strong></p>
                            <img src="{{qr_code}}" alt="Código QR de Verificación" style="max-width: 200px;">
                        </div>
                        
                        <p>Este resultado fue generado el {{fecha_consulta}} y es válido para fines informativos.</p>
                    </div>
                    
                    <div class="footer">
                        <p>ECPlacas 2.0 - Desarrollado por Erick Costa</p>
                        <p>Proyecto: Construcción de Software • Temática: Futurista - Azul Neon</p>
                    </div>
                </div>
            </body>
            </html>
            """,
            
            "notification": """
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #00ffff;">{{title}}</h2>
                <p>{{message}}</p>
                <div style="text-align: center; margin: 20px 0;">
                    <p style="color: #666; font-size: 12px;">ECPlacas 2.0 - {{timestamp}}</p>
                </div>
            </div>
            """
        }
        
        return templates.get(template_name, "")

# Decoradores útiles
def rate_limit(max_requests: int = 50, time_window: int = 3600):
    """Decorador para rate limiting"""
    limiter = RateLimiter(max_requests, time_window)
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from flask import request, jsonify
            
            # Obtener identificador (IP del cliente)
            identifier = request.remote_addr
            
            # Verificar límite
            allowed, remaining = limiter.is_allowed(identifier)
            
            if not allowed:
                return jsonify({
                    'success': False,
                    'error': 'Rate limit exceeded',
                    'remaining': remaining,
                    'reset_time': time_window
                }), 429
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def log_request(func):
    """Decorador para logging de requests"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        from flask import request
        
        start_time = time.time()
        logger.info(f"🌐 Request: {request.method} {request.path} from {request.remote_addr}")
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"✅ Response: {request.path} completed in {duration:.3f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ Error in {request.path}: {e} (duration: {duration:.3f}s)")
            raise
    
    return wrapper

# Instancias globales de utilidades
text_utils = TextUtils()
date_utils = DateUtils()
security_utils = SecurityUtils()
file_utils = FileUtils()
qr_generator = QRCodeGenerator()
template_engine = TemplateEngine()

if __name__ == "__main__":
    # Pruebas de utilidades
    print("🧪 Probando utilidades ECPlacas 2.0...")
    
    # Probar limpieza de texto
    test_name = "   juan pérez@garcía!!! "
    clean_name = text_utils.normalize_name(test_name)
    print(f"Nombre limpio: '{test_name}' → '{clean_name}'")
    
    # Probar formateo de fecha
    test_date = datetime.now()
    relative_time = date_utils.format_relative_time(test_date)
    print(f"Tiempo relativo: {relative_time}")
    
    # Probar generación de token
    token = security_utils.generate_token(16)
    print(f"Token generado: {token}")
    
    # Probar QR
    qr_data = qr_generator.generate_verification_qr("test_123", "ABC1234")
    print(f"QR generado: {len(qr_data)} caracteres")
    
    print("✅ Pruebas de utilidades completadas")
