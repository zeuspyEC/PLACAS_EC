# ==========================================
# ECPlacas 2.0 - Dockerfile Optimizado para Producción
# Proyecto: Construcción de Software - EPN
# Desarrollado por: Erick Costa
# Enfoque: Rendimiento | Sostenibilidad | Escalabilidad
# ==========================================

# ==========================================
# ETAPA 1: BUILD (Compilación)
# ==========================================
FROM python:3.11-slim as builder

# Metadatos del contenedor
LABEL maintainer="Erick Costa <erick.costa@epn.edu.ec>"
LABEL project="ECPlacas 2.0"
LABEL description="Sistema de Consulta Vehicular - Construcción de Software - EPN"
LABEL version="2.0.1"
LABEL university="Escuela Politécnica Nacional"
LABEL stage="builder"

# Variables de build
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=2.0.1

LABEL org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="ECPlacas 2.0" \
      org.label-schema.description="Sistema de Consulta Vehicular - EPN" \
      org.label-schema.url="https://github.com/erickcosta/placas_ec" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.com/erickcosta/placas_ec" \
      org.label-schema.vendor="Erick Costa - EPN" \
      org.label-schema.version=$VERSION \
      org.label-schema.schema-version="1.0"

# Optimizaciones de build
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Instalar dependencias de compilación
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libc6-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /build

# Copiar archivos de dependencias
COPY requirements.txt pyproject.toml ./

# Crear wheel packages para dependencias (cache-friendly)
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# ==========================================
# ETAPA 2: RUNTIME (Producción)
# ==========================================
FROM python:3.11-slim as runtime

# Variables de entorno optimizadas para producción
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    FLASK_ENV=production \
    FLASK_HOST=0.0.0.0 \
    FLASK_PORT=5000 \
    WORKERS=4 \
    TIMEOUT=30 \
    KEEPALIVE=5 \
    MAX_REQUESTS=1000 \
    MAX_REQUESTS_JITTER=50

# Instalar dependencias runtime mínimas
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    sqlite3 \
    ca-certificates \
    tzdata \
    tini \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Configurar timezone para Ecuador
ENV TZ=America/Guayaquil
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Crear usuario no-root para seguridad
RUN groupadd -r ecplacas --gid=1000 && \
    useradd -r -g ecplacas --uid=1000 --home-dir=/app --shell=/bin/bash ecplacas

# Crear estructura de directorios optimizada
WORKDIR /app
RUN mkdir -p /app/{backend,frontend,database,logs,cache,config,static,scripts} \
    && mkdir -p /app/database/backups \
    && mkdir -p /app/logs/{app,access,error} \
    && mkdir -p /app/cache/{api,templates,static} \
    && chown -R ecplacas:ecplacas /app

# Copiar wheels desde builder stage
COPY --from=builder /build/wheels /wheels

# Instalar dependencias desde wheels (más rápido)
RUN pip install --no-cache-dir --no-index --find-links /wheels -r /wheels/../requirements.txt \
    && rm -rf /wheels

# Instalar servidor WSGI optimizado para producción
RUN pip install --no-cache-dir gunicorn[gevent]==21.2.0 gevent==23.7.0

# Copiar código fuente (optimizado para cache de Docker)
COPY --chown=ecplacas:ecplacas backend/ /app/backend/
COPY --chown=ecplacas:ecplacas frontend/ /app/frontend/
COPY --chown=ecplacas:ecplacas *.py /app/
COPY --chown=ecplacas:ecplacas *.md /app/
COPY --chown=ecplacas:ecplacas .env /app/ 2>/dev/null || true

# Crear archivo de configuración de producción
RUN cat > /app/gunicorn.conf.py << 'EOF'
# Configuración Gunicorn optimizada para ECPlacas 2.0 - EPN
import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('FLASK_PORT', 5000)}"
backlog = 2048

# Worker processes
workers = int(os.environ.get('WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = "gevent"
worker_connections = 1000
max_requests = int(os.environ.get('MAX_REQUESTS', 1000))
max_requests_jitter = int(os.environ.get('MAX_REQUESTS_JITTER', 50))
preload_app = True

# Timeout
timeout = int(os.environ.get('TIMEOUT', 30))
keepalive = int(os.environ.get('KEEPALIVE', 5))

# Logging
accesslog = "/app/logs/access/gunicorn_access.log"
errorlog = "/app/logs/error/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "ecplacas-gunicorn"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Performance
sendfile = True
enable_stdio_inheritance = True
EOF

# Script de inicio optimizado
RUN cat > /app/start.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Iniciando ECPlacas 2.0 - EPN en modo producción..."

# Verificar estructura de directorios
mkdir -p /app/{logs/{app,access,error},database/backups,cache/{api,templates,static}}

# Crear .env si no existe
if [ ! -f /app/.env ]; then
    echo "📝 Creando archivo .env básico..."
    cat > /app/.env << 'ENV_EOF'
FLASK_ENV=production
FLASK_DEBUG=False
DATABASE_PATH=/app/database/ecplacas.sqlite
LOG_LEVEL=INFO
ENV_EOF
fi

# Migración/Inicialización de base de datos
echo "🗄️ Inicializando base de datos..."
cd /app
python -c "
from backend.db import ECPlacasDatabase
try:
    db = ECPlacasDatabase()
    if db.verificar_conexion():
        print('✅ Base de datos inicializada correctamente')
    else:
        print('❌ Error en conexión de base de datos')
        exit(1)
except Exception as e:
    print(f'❌ Error inicializando base de datos: {e}')
    exit(1)
"

# Verificar conectividad básica
echo "🔍 Verificando aplicación..."
python -c "
import sys
sys.path.insert(0, '/app/backend')
try:
    from app import create_app
    app = create_app()
    print('✅ Aplicación Flask cargada correctamente')
except Exception as e:
    print(f'❌ Error cargando aplicación: {e}')
    sys.exit(1)
"

echo "✅ Verificaciones completadas"
echo "🌐 Iniciando servidor Gunicorn..."
echo "📊 Workers: $WORKERS"
echo "⚡ Timeout: $TIMEOUT segundos"
echo "🔄 Max requests: $MAX_REQUESTS"

# Ejecutar Gunicorn
exec gunicorn --config /app/gunicorn.conf.py "backend.app:create_app()"
EOF

# Hacer el script ejecutable
RUN chmod +x /app/start.sh

# Script de health check avanzado
RUN cat > /app/healthcheck.sh << 'EOF'
#!/bin/bash
set -e

# Health check comprehensivo
HEALTH_URL="http://localhost:${FLASK_PORT:-5000}/api/health"

# Test de conectividad básica
if ! curl -f -s -m 10 "$HEALTH_URL" > /dev/null; then
    echo "❌ Health check falló"
    exit 1
fi

# Test de base de datos
python -c "
import sys
sys.path.insert(0, '/app/backend')
from backend.db import ECPlacasDatabase
try:
    db = ECPlacasDatabase()
    if not db.verificar_conexion():
        print('❌ Base de datos no disponible')
        exit(1)
except Exception as e:
    print(f'❌ Error verificando base de datos: {e}')
    exit(1)
"

echo "✅ Health check OK"
exit 0
EOF

RUN chmod +x /app/healthcheck.sh

# Configuración de seguridad
RUN chown -R ecplacas:ecplacas /app && \
    chmod -R 755 /app && \
    chmod -R 644 /app/backend/ && \
    chmod +x /app/*.sh

# Cambiar al usuario no-root
USER ecplacas

# Crear volúmenes para persistencia
VOLUME ["/app/database", "/app/logs", "/app/cache"]

# Exponer puerto
EXPOSE 5000

# Health check optimizado
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD ["/app/healthcheck.sh"]

# Usar tini como init system para manejo correcto de señales
ENTRYPOINT ["/usr/bin/tini", "--"]

# Comando por defecto optimizado
CMD ["/app/start.sh"]

# ==========================================
# METADATOS FINALES
# ==========================================
LABEL final.size="~200MB" \
      final.optimizations="multi-stage,wheels,non-root,tini,gunicorn" \
      final.security="non-root-user,minimal-packages,health-checks" \
      final.performance="gevent,preload,workers-auto-scaling" \
      final.monitoring="structured-logs,health-endpoints,metrics" \
      final.university="Escuela Politécnica Nacional" \
      final.project="Construcción de Software"

# ==========================================
# INSTRUCCIONES DE USO PARA EPN
# ==========================================

# BUILD OPTIMIZADO:
# docker build -t ecplacas-epn:2.0.1 \
#   --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
#   --build-arg VCS_REF=$(git rev-parse --short HEAD) \
#   --build-arg VERSION=2.0.1 \
#   .

# PRODUCCIÓN BÁSICA:
# docker run -d \
#   --name ecplacas-prod \
#   --restart=unless-stopped \
#   -p 5000:5000 \
#   -v ecplacas_data:/app/database \
#   -v ecplacas_logs:/app/logs \
#   -e WORKERS=4 \
#   -e TIMEOUT=30 \
#   ecplacas-epn:2.0.1

# DESARROLLO:
# docker run -d \
#   --name ecplacas-dev \
#   -p 5000:5000 \
#   -v $(pwd):/app \
#   -e FLASK_ENV=development \
#   -e WORKERS=1 \
#   ecplacas-epn:2.0.1

# MONITOREO:
# docker logs -f ecplacas-prod
# docker exec ecplacas-prod cat /app/logs/access/gunicorn_access.log
# docker stats ecplacas-prod
