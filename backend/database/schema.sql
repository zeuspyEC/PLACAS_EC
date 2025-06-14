-- ==========================================
-- ECPlacas 2.0 - Esquema de Base de Datos
-- Proyecto: Construcción de Software
-- Desarrollado por: Erick Costa
-- Temática: Futurista - Azul Neon
-- ==========================================

-- Habilitar claves foráneas y configuraciones de performance
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 10000;
PRAGMA temp_store = memory;

-- ==========================================
-- TABLA DE USUARIOS
-- ==========================================
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    cedula TEXT UNIQUE NOT NULL,
    telefono TEXT,
    correo TEXT,
    country_code TEXT DEFAULT '+593',
    ip_address TEXT,
    user_agent TEXT,
    total_consultas INTEGER DEFAULT 0,
    ultimo_acceso TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Validaciones a nivel de base de datos
    CHECK (length(cedula) = 10),
    CHECK (total_consultas >= 0),
    CHECK (length(nombre) >= 2)
);

-- ==========================================
-- TABLA DE CONSULTAS VEHICULARES
-- ==========================================
CREATE TABLE IF NOT EXISTS consultas_vehiculares (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    usuario_id INTEGER,
    numero_placa TEXT NOT NULL,
    placa_original TEXT,
    placa_normalizada TEXT,
    consulta_exitosa BOOLEAN DEFAULT 0,
    tiempo_consulta REAL,
    mensaje_error TEXT,
    ip_origen TEXT,
    user_agent TEXT,
    api_utilizada TEXT DEFAULT 'ant_principal',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE SET NULL,
    
    -- Validaciones
    CHECK (tiempo_consulta >= 0),
    CHECK (length(numero_placa) >= 6)
);

-- ==========================================
-- TABLA DE DATOS VEHICULARES COMPLETOS
-- ==========================================
CREATE TABLE IF NOT EXISTS datos_vehiculares (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    consulta_id INTEGER NOT NULL,
    
    -- Datos de identificación
    vin_chasis TEXT,
    numero_motor TEXT,
    placa_anterior TEXT,
    
    -- Datos del modelo
    marca TEXT,
    modelo TEXT,
    anio_fabricacion INTEGER,
    pais_fabricacion TEXT,
    
    -- Características físicas
    clase_vehiculo TEXT,
    tipo_vehiculo TEXT,
    color_primario TEXT,
    color_secundario TEXT,
    peso_vehiculo TEXT,
    tipo_carroceria TEXT,
    
    -- Datos de matrícula y revisión
    matricula_desde TEXT,
    matricula_hasta TEXT,
    ano_ultima_revision TEXT,
    ultima_revision_desde TEXT,
    ultima_revision_hasta TEXT,
    servicio TEXT,
    ultima_actualizacion TEXT,
    
    -- Datos CRV (Centro de Retención Vehicular)
    indicador_crv TEXT,
    orden_crv TEXT,
    centro_retencion TEXT,
    tipo_retencion TEXT,
    motivo_retencion TEXT,
    fecha_inicio_retencion TEXT,
    dias_retencion TEXT,
    grua TEXT,
    area_ubicacion TEXT,
    columna TEXT,
    fila TEXT,
    
    -- Análisis ECPlacas 2.0
    estado_matricula TEXT,
    dias_hasta_vencimiento INTEGER,
    estimacion_valor REAL,
    categoria_riesgo TEXT DEFAULT 'BAJO',
    puntuacion_general INTEGER DEFAULT 0,
    recomendacion TEXT,
    
    -- Datos completos en JSON para backup
    datos_completos_json TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (consulta_id) REFERENCES consultas_vehiculares (id) ON DELETE CASCADE,
    
    -- Validaciones
    CHECK (anio_fabricacion >= 1950 OR anio_fabricacion IS NULL),
    CHECK (estimacion_valor >= 0 OR estimacion_valor IS NULL),
    CHECK (puntuacion_general >= 0 AND puntuacion_general <= 100),
    CHECK (estado_matricula IN ('VIGENTE', 'POR_VENCER', 'VENCIDA', 'INDETERMINADO') OR estado_matricula IS NULL)
);

-- ==========================================
-- TABLA DE ESTADÍSTICAS DEL SISTEMA
-- ==========================================
CREATE TABLE IF NOT EXISTS estadisticas_sistema (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha DATE UNIQUE NOT NULL,
    total_consultas INTEGER DEFAULT 0,
    consultas_exitosas INTEGER DEFAULT 0,
    usuarios_nuevos INTEGER DEFAULT 0,
    usuarios_activos INTEGER DEFAULT 0,
    tiempo_promedio_consulta REAL DEFAULT 0,
    placas_consultadas TEXT, -- JSON array de placas únicas del día
    marcas_populares TEXT,   -- JSON object con conteo de marcas
    errores_comunes TEXT,    -- JSON array de errores más frecuentes
    apis_utilizadas TEXT,    -- JSON object con uso por API
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CHECK (total_consultas >= consultas_exitosas),
    CHECK (usuarios_nuevos >= 0),
    CHECK (tiempo_promedio_consulta >= 0)
);

-- ==========================================
-- TABLA DE CONFIGURACIÓN DEL SISTEMA
-- ==========================================
CREATE TABLE IF NOT EXISTS configuracion_sistema (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clave TEXT UNIQUE NOT NULL,
    valor TEXT,
    descripcion TEXT,
    tipo_dato TEXT DEFAULT 'string', -- string, integer, float, boolean, json
    categoria TEXT DEFAULT 'general',
    editable BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CHECK (tipo_dato IN ('string', 'integer', 'float', 'boolean', 'json'))
);

-- ==========================================
-- TABLA DE LOGS DEL SISTEMA
-- ==========================================
CREATE TABLE IF NOT EXISTS logs_sistema (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nivel TEXT NOT NULL,
    modulo TEXT,
    mensaje TEXT NOT NULL,
    detalles_json TEXT,
    ip_origen TEXT,
    usuario_id INTEGER,
    session_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE SET NULL,
    
    CHECK (nivel IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'))
);

-- ==========================================
-- TABLA DE CACHE DE CONSULTAS
-- ==========================================
CREATE TABLE IF NOT EXISTS cache_consultas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    placa TEXT NOT NULL,
    api_source TEXT NOT NULL,
    response_data TEXT NOT NULL, -- JSON response completo
    hash_key TEXT UNIQUE NOT NULL,
    hits INTEGER DEFAULT 0,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CHECK (hits >= 0)
);

-- ==========================================
-- TABLA DE SESIONES ACTIVAS
-- ==========================================
CREATE TABLE IF NOT EXISTS sesiones_activas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    usuario_id INTEGER,
    ip_address TEXT,
    user_agent TEXT,
    estado TEXT DEFAULT 'activa', -- activa, completada, expirada, error
    progreso INTEGER DEFAULT 0, -- 0-100
    mensaje_estado TEXT,
    placa_consultada TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE SET NULL,
    
    CHECK (progreso >= 0 AND progreso <= 100),
    CHECK (estado IN ('activa', 'completada', 'expirada', 'error'))
);

-- ==========================================
-- TABLA DE NOTIFICACIONES
-- ==========================================
CREATE TABLE IF NOT EXISTS notificaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER,
    tipo TEXT NOT NULL, -- email, sms, whatsapp, push
    destinatario TEXT NOT NULL,
    asunto TEXT,
    mensaje TEXT NOT NULL,
    datos_adjuntos TEXT, -- JSON con datos adicionales
    estado TEXT DEFAULT 'pendiente', -- pendiente, enviado, fallido
    intentos INTEGER DEFAULT 0,
    enviado_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE SET NULL,
    
    CHECK (tipo IN ('email', 'sms', 'whatsapp', 'push')),
    CHECK (estado IN ('pendiente', 'enviado', 'fallido')),
    CHECK (intentos >= 0)
);

-- ==========================================
-- ÍNDICES PARA OPTIMIZACIÓN
-- ==========================================

-- Índices para usuarios
CREATE INDEX IF NOT EXISTS idx_usuarios_cedula ON usuarios(cedula);
CREATE INDEX IF NOT EXISTS idx_usuarios_ultimo_acceso ON usuarios(ultimo_acceso);
CREATE INDEX IF NOT EXISTS idx_usuarios_total_consultas ON usuarios(total_consultas DESC);

-- Índices para consultas vehiculares
CREATE INDEX IF NOT EXISTS idx_consultas_placa ON consultas_vehiculares(numero_placa);
CREATE INDEX IF NOT EXISTS idx_consultas_placa_normalizada ON consultas_vehiculares(placa_normalizada);
CREATE INDEX IF NOT EXISTS idx_consultas_fecha ON consultas_vehiculares(created_at);
CREATE INDEX IF NOT EXISTS idx_consultas_exitosa ON consultas_vehiculares(consulta_exitosa);
CREATE INDEX IF NOT EXISTS idx_consultas_usuario ON consultas_vehiculares(usuario_id);
CREATE INDEX IF NOT EXISTS idx_consultas_session ON consultas_vehiculares(session_id);
CREATE INDEX IF NOT EXISTS idx_consultas_ip ON consultas_vehiculares(ip_origen);

-- Índices para datos vehiculares
CREATE INDEX IF NOT EXISTS idx_vehiculos_marca ON datos_vehiculares(marca);
CREATE INDEX IF NOT EXISTS idx_vehiculos_anio ON datos_vehiculares(anio_fabricacion);
CREATE INDEX IF NOT EXISTS idx_vehiculos_tipo ON datos_vehiculares(tipo_vehiculo);
CREATE INDEX IF NOT EXISTS idx_vehiculos_estado_matricula ON datos_vehiculares(estado_matricula);
CREATE INDEX IF NOT EXISTS idx_vehiculos_estimacion_valor ON datos_vehiculares(estimacion_valor);
CREATE INDEX IF NOT EXISTS idx_vehiculos_consulta_id ON datos_vehiculares(consulta_id);

-- Índices para estadísticas
CREATE INDEX IF NOT EXISTS idx_estadisticas_fecha ON estadisticas_sistema(fecha);

-- Índices para logs
CREATE INDEX IF NOT EXISTS idx_logs_fecha ON logs_sistema(created_at);
CREATE INDEX IF NOT EXISTS idx_logs_nivel ON logs_sistema(nivel);
CREATE INDEX IF NOT EXISTS idx_logs_modulo ON logs_sistema(modulo);
CREATE INDEX IF NOT EXISTS idx_logs_usuario ON logs_sistema(usuario_id);

-- Índices para cache
CREATE INDEX IF NOT EXISTS idx_cache_placa ON cache_consultas(placa);
CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache_consultas(expires_at);
CREATE INDEX IF NOT EXISTS idx_cache_hash ON cache_consultas(hash_key);

-- Índices para sesiones
CREATE INDEX IF NOT EXISTS idx_sesiones_session_id ON sesiones_activas(session_id);
CREATE INDEX IF NOT EXISTS idx_sesiones_usuario ON sesiones_activas(usuario_id);
CREATE INDEX IF NOT EXISTS idx_sesiones_estado ON sesiones_activas(estado);
CREATE INDEX IF NOT EXISTS idx_sesiones_actividad ON sesiones_activas(last_activity);

-- Índices para notificaciones
CREATE INDEX IF NOT EXISTS idx_notificaciones_usuario ON notificaciones(usuario_id);
CREATE INDEX IF NOT EXISTS idx_notificaciones_estado ON notificaciones(estado);
CREATE INDEX IF NOT EXISTS idx_notificaciones_tipo ON notificaciones(tipo);

-- ==========================================
-- TRIGGERS PARA MANTENIMIENTO AUTOMÁTICO
-- ==========================================

-- Trigger para actualizar timestamp en usuarios
CREATE TRIGGER IF NOT EXISTS tr_usuarios_updated_at
    AFTER UPDATE ON usuarios
    FOR EACH ROW
BEGIN
    UPDATE usuarios SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger para actualizar estadísticas cuando se inserta una consulta
CREATE TRIGGER IF NOT EXISTS tr_actualizar_estadisticas_consulta
    AFTER INSERT ON consultas_vehiculares
    FOR EACH ROW
BEGIN
    INSERT OR IGNORE INTO estadisticas_sistema (fecha, total_consultas, consultas_exitosas)
    VALUES (DATE(NEW.created_at), 0, 0);
    
    UPDATE estadisticas_sistema 
    SET total_consultas = total_consultas + 1,
        consultas_exitosas = consultas_exitosas + CASE WHEN NEW.consulta_exitosa = 1 THEN 1 ELSE 0 END,
        updated_at = CURRENT_TIMESTAMP
    WHERE fecha = DATE(NEW.created_at);
END;

-- Trigger para limpiar sesiones expiradas
CREATE TRIGGER IF NOT EXISTS tr_limpiar_sesiones_expiradas
    AFTER INSERT ON sesiones_activas
    FOR EACH ROW
BEGIN
    UPDATE sesiones_activas 
    SET estado = 'expirada' 
    WHERE estado = 'activa' 
    AND last_activity < datetime('now', '-2 hours');
END;

-- Trigger para limpiar cache expirado
CREATE TRIGGER IF NOT EXISTS tr_limpiar_cache_expirado
    AFTER INSERT ON cache_consultas
    FOR EACH ROW
BEGIN
    DELETE FROM cache_consultas 
    WHERE expires_at < datetime('now');
END;

-- ==========================================
-- VISTAS ÚTILES PARA CONSULTAS
-- ==========================================

-- Vista para consultas completas con datos de usuario y vehículo
CREATE VIEW IF NOT EXISTS vista_consultas_completas AS
SELECT 
    cv.id as consulta_id,
    cv.session_id,
    cv.numero_placa,
    cv.placa_normalizada,
    cv.consulta_exitosa,
    cv.tiempo_consulta,
    cv.created_at as fecha_consulta,
    u.nombre as usuario_nombre,
    u.cedula as usuario_cedula,
    u.correo as usuario_correo,
    dv.marca,
    dv.modelo,
    dv.anio_fabricacion,
    dv.tipo_vehiculo,
    dv.estado_matricula,
    dv.estimacion_valor,
    dv.puntuacion_general
FROM consultas_vehiculares cv
LEFT JOIN usuarios u ON cv.usuario_id = u.id
LEFT JOIN datos_vehiculares dv ON cv.id = dv.consulta_id;

-- Vista para estadísticas rápidas del día actual
CREATE VIEW IF NOT EXISTS vista_estadisticas_hoy AS
SELECT 
    DATE('now') as fecha,
    COUNT(*) as total_consultas,
    COUNT(CASE WHEN consulta_exitosa = 1 THEN 1 END) as consultas_exitosas,
    COUNT(DISTINCT usuario_id) as usuarios_activos,
    AVG(CASE WHEN consulta_exitosa = 1 THEN tiempo_consulta END) as tiempo_promedio,
    COUNT(DISTINCT numero_placa) as placas_unicas
FROM consultas_vehiculares 
WHERE DATE(created_at) = DATE('now');

-- Vista para top marcas más consultadas
CREATE VIEW IF NOT EXISTS vista_top_marcas AS
SELECT 
    marca,
    COUNT(*) as total_consultas,
    AVG(estimacion_valor) as valor_promedio,
    COUNT(DISTINCT anio_fabricacion) as anios_diferentes,
    MAX(created_at) as ultima_consulta
FROM datos_vehiculares 
WHERE marca IS NOT NULL AND marca != ''
GROUP BY marca
ORDER BY total_consultas DESC;

-- ==========================================
-- DATOS INICIALES DE CONFIGURACIÓN
-- ==========================================

-- Configuraciones del sistema ECPlacas 2.0
INSERT OR IGNORE INTO configuracion_sistema (clave, valor, descripcion, tipo_dato, categoria) VALUES
-- Información del sistema
('version_sistema', '2.0.0', 'Versión del sistema ECPlacas', 'string', 'sistema'),
('autor', 'Erick Costa', 'Desarrollador del sistema', 'string', 'sistema'),
('proyecto', 'Construcción de Software', 'Nombre del proyecto académico', 'string', 'sistema'),
('tema', 'Futurista - Azul Neon', 'Temática visual del sistema', 'string', 'sistema'),
('fecha_lanzamiento', '2024-12-15', 'Fecha de lanzamiento del sistema', 'string', 'sistema'),

-- Configuraciones de API
('max_consultas_por_hora', '50', 'Límite de consultas por hora por IP', 'integer', 'api'),
('timeout_consulta', '30', 'Timeout en segundos para consultas', 'integer', 'api'),
('max_reintentos', '3', 'Número máximo de reintentos por consulta', 'integer', 'api'),
('rate_limit_enabled', 'true', 'Habilitar rate limiting', 'boolean', 'api'),

-- Configuraciones de cache
('cache_habilitado', 'true', 'Cache de consultas habilitado', 'boolean', 'cache'),
('cache_ttl_hours', '24', 'Tiempo de vida del cache en horas', 'integer', 'cache'),
('cache_max_entries', '1000', 'Máximo número de entradas en cache', 'integer', 'cache'),

-- Configuraciones de notificaciones
('notificaciones_email', 'false', 'Notificaciones por email habilitadas', 'boolean', 'notificaciones'),
('notificaciones_sms', 'false', 'Notificaciones por SMS habilitadas', 'boolean', 'notificaciones'),
('notificaciones_whatsapp', 'false', 'Notificaciones por WhatsApp habilitadas', 'boolean', 'notificaciones'),

-- Configuraciones de mantenimiento
('backup_automatico', 'true', 'Backup automático habilitado', 'boolean', 'mantenimiento'),
('backup_frecuencia_horas', '24', 'Frecuencia de backup en horas', 'integer', 'mantenimiento'),
('limpieza_logs_dias', '30', 'Días para mantener logs del sistema', 'integer', 'mantenimiento'),
('limpieza_cache_dias', '7', 'Días para mantener cache expirado', 'integer', 'mantenimiento'),

-- Configuraciones de seguridad
('max_intentos_login', '5', 'Máximo intentos de login por IP', 'integer', 'seguridad'),
('bloqueo_ip_minutos', '30', 'Minutos de bloqueo por exceder intentos', 'integer', 'seguridad'),
('jwt_secret_key', 'ecplacas_2024_secret_key', 'Clave secreta para JWT', 'string', 'seguridad'),

-- Configuraciones de desarrollo
('modo_debug', 'false', 'Modo debug del sistema', 'boolean', 'desarrollo'),
('log_level', 'INFO', 'Nivel de logging', 'string', 'desarrollo'),
('metrics_enabled', 'true', 'Métricas de performance habilitadas', 'boolean', 'desarrollo');

-- ==========================================
-- PROCEDIMIENTOS ALMACENADOS (SIMULADOS CON TRIGGERS)
-- ==========================================

-- Log inicial del sistema
INSERT INTO logs_sistema (nivel, modulo, mensaje, detalles_json) VALUES
('INFO', 'database', 'Base de datos ECPlacas 2.0 inicializada correctamente', 
 '{"version": "2.0.0", "autor": "Erick Costa", "proyecto": "Construcción de Software"}');

-- ==========================================
-- COMENTARIOS FINALES
-- ==========================================

/*
Este esquema de base de datos para ECPlacas 2.0 incluye:

✅ CARACTERÍSTICAS PRINCIPALES:
- Estructura completa para gestión de usuarios y consultas vehiculares
- Cache inteligente para optimizar performance
- Sistema de logs completo para auditoría
- Notificaciones multi-canal
- Estadísticas detalladas del sistema
- Configuración flexible
- Triggers automáticos para mantenimiento
- Vistas optimizadas para consultas frecuentes
- Índices para máximo rendimiento

✅ OPTIMIZACIONES:
- WAL mode para mejor concurrencia
- Índices estratégicos en todas las consultas frecuentes
- Triggers para mantenimiento automático
- Vistas para consultas complejas
- Validaciones a nivel de base de datos

✅ SEGURIDAD:
- Validaciones de integridad
- Claves foráneas con CASCADE apropiado
- Campos obligatorios bien definidos
- Logs de auditoría completos

✅ ESCALABILIDAD:
- Estructura preparada para crecimiento
- Particionado por fecha en estadísticas
- Cache con expiración automática
- Limpieza automática de datos antiguos

Desarrollado específicamente para el proyecto de Construcción de Software
con temática futurista y paleta azul neon.

Autor: Erick Costa
Fecha: Diciembre 2024
Versión: 2.0.0
*/
