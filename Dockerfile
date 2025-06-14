# ==========================================
# ECPlacas 2.0 - Dockerfile
# Proyecto: Construcción de Software
# Desarrollado por: Erick Costa
# ==========================================

# Usar imagen base oficial de Python
FROM python:3.11-slim

# Información del contenedor
LABEL maintainer="Erick Costa"
LABEL project="ECPlacas 2.0"
LABEL description="Sistema de Consulta Vehicular - Construcción de Software"
LABEL version="2.0.0"
LABEL theme="Futurista - Azul Neon"

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_ENV=production
ENV FLASK_HOST=0.0.0.0
ENV FLASK_PORT=5000

# Crear usuario no-root para seguridad
RUN groupadd -r ecplacas && useradd -r -g ecplacas -s /bin/bash -d /app ecplacas

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Crear estructura de directorios
WORKDIR /app
RUN mkdir -p /app/{backend,frontend,database,logs,config,public,scripts,docs} \
    && mkdir -p /app/database/backups \
    && chown -R ecplacas:ecplacas /app

# Copiar requirements primero para aprovechar cache de Docker
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY --chown=ecplacas:ecplacas . /app/

# Crear archivo .env si no existe
RUN if [ ! -f /app/.env ]; then \
        cp /app/.env.example /app/.env; \
    fi

# Asegurar permisos correctos
RUN chown -R ecplacas:ecplacas /app \
    && chmod +x /app/scripts/*.py

# Cambiar al usuario no-root
USER ecplacas

# Exponer puerto
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Comando por defecto
CMD ["python", "backend/app.py"]

# ==========================================
# INSTRUCCIONES DE USO
# ==========================================

# Construir imagen:
# docker build -t ecplacas-2.0 .

# Ejecutar contenedor:
# docker run -d \
#   --name ecplacas-container \
#   -p 5000:5000 \
#   -v $(pwd)/database:/app/database \
#   -v $(pwd)/logs:/app/logs \
#   ecplacas-2.0

# Para desarrollo con bind mount:
# docker run -d \
#   --name ecplacas-dev \
#   -p 5000:5000 \
#   -v $(pwd):/app \
#   -e FLASK_ENV=development \
#   ecplacas-2.0

# Ver logs:
# docker logs ecplacas-container

# Acceder al contenedor:
# docker exec -it ecplacas-container bash

# Detener contenedor:
# docker stop ecplacas-container

# Eliminar contenedor:
# docker rm ecplacas-container

# ==========================================
# NOTAS DE PRODUCCIÓN
# ==========================================

# 1. Para producción, usar un reverse proxy como Nginx
# 2. Configurar SSL/TLS apropiadamente
# 3. Usar volúmenes para persistir datos
# 4. Configurar variables de entorno sensibles como secrets
# 5. Implementar logging centralizado
# 6. Monitorear recursos del contenedor
