-- =====================================================
-- KYC Platform - Database Initialization
-- =====================================================

-- Extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- Para búsquedas fuzzy

-- =====================================================
-- TABLA: persons
-- =====================================================
CREATE TABLE IF NOT EXISTS persons (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    curp VARCHAR(18) UNIQUE,
    rfc VARCHAR(13),
    email VARCHAR(255),
    phone VARCHAR(20),
    birth_date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_persons_curp ON persons(curp);
CREATE INDEX idx_persons_email ON persons(email);
CREATE INDEX idx_persons_phone ON persons(phone);
CREATE INDEX idx_persons_full_name_trgm ON persons USING gin (full_name gin_trgm_ops);

-- =====================================================
-- TABLA: background_checks
-- =====================================================
CREATE TABLE IF NOT EXISTS background_checks (
    id SERIAL PRIMARY KEY,
    check_id UUID UNIQUE NOT NULL DEFAULT uuid_generate_v4(),
    person_id INTEGER REFERENCES persons(id),
    full_name VARCHAR(255) NOT NULL,
    curp VARCHAR(18),
    email VARCHAR(255),
    phone VARCHAR(20),
    global_risk_score FLOAT NOT NULL,
    global_risk_level VARCHAR(20) NOT NULL,
    flags JSONB,
    critical_alerts JSONB,
    rnd_results JSONB,
    enrichment_results JSONB,
    sanctions_results JSONB,
    network_analysis JSONB,
    curp_validation JSONB,
    sources_consulted JSONB,
    processing_time_ms FLOAT,
    consent_id VARCHAR(100) NOT NULL,
    requested_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_checks_check_id ON background_checks(check_id);
CREATE INDEX idx_checks_curp ON background_checks(curp);
CREATE INDEX idx_checks_person_id ON background_checks(person_id);
CREATE INDEX idx_checks_risk_level ON background_checks(global_risk_level);
CREATE INDEX idx_checks_created_at ON background_checks(created_at);
CREATE INDEX idx_checks_requested_by ON background_checks(requested_by);

-- =====================================================
-- TABLA: curp_validations
-- =====================================================
CREATE TABLE IF NOT EXISTS curp_validations (
    id SERIAL PRIMARY KEY,
    curp VARCHAR(18) UNIQUE NOT NULL,
    nombre_completo VARCHAR(255),
    fecha_nacimiento DATE,
    sexo CHAR(1),
    estado VARCHAR(50),
    is_valid BOOLEAN DEFAULT TRUE,
    validation_date TIMESTAMP DEFAULT NOW(),
    source VARCHAR(50),
    metadata JSONB
);

CREATE INDEX idx_curp_val_curp ON curp_validations(curp);
CREATE INDEX idx_curp_val_nombre_trgm ON curp_validations USING gin (nombre_completo gin_trgm_ops);

-- =====================================================
-- TABLA: audit_log
-- =====================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    user_id VARCHAR(100),
    check_id UUID,
    person_id INTEGER REFERENCES persons(id),
    description TEXT,
    metadata JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_event_type ON audit_log(event_type);
CREATE INDEX idx_audit_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_check_id ON audit_log(check_id);
CREATE INDEX idx_audit_created_at ON audit_log(created_at);

-- =====================================================
-- TABLA: api_keys
-- =====================================================
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    permissions JSONB,
    rate_limit_per_hour INTEGER DEFAULT 1000,
    is_active BOOLEAN DEFAULT TRUE,
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);

-- =====================================================
-- TABLA: rate_limits
-- =====================================================
CREATE TABLE IF NOT EXISTS rate_limits (
    id SERIAL PRIMARY KEY,
    identifier VARCHAR(255) NOT NULL, -- IP, user_id, api_key
    endpoint VARCHAR(255) NOT NULL,
    request_count INTEGER DEFAULT 0,
    window_start TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_rate_limits_identifier ON rate_limits(identifier);
CREATE INDEX idx_rate_limits_endpoint ON rate_limits(endpoint);
CREATE UNIQUE INDEX idx_rate_limits_identifier_endpoint ON rate_limits(identifier, endpoint);

-- =====================================================
-- TABLA: sanctions_cache
-- =====================================================
CREATE TABLE IF NOT EXISTS sanctions_cache (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    normalized_name VARCHAR(255) NOT NULL,
    source VARCHAR(100) NOT NULL, -- OFAC, ONU, SAT, etc.
    data JSONB,
    last_updated TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sanctions_name_trgm ON sanctions_cache USING gin (normalized_name gin_trgm_ops);
CREATE INDEX idx_sanctions_source ON sanctions_cache(source);

-- =====================================================
-- FUNCIONES ÚTILES
-- =====================================================

-- Función para limpiar rate limits antiguos
CREATE OR REPLACE FUNCTION cleanup_old_rate_limits()
RETURNS void AS $$
BEGIN
    DELETE FROM rate_limits 
    WHERE window_start < NOW() - INTERVAL '1 hour';
END;
$$ LANGUAGE plpgsql;

-- Función para normalizar nombres (para búsqueda fuzzy)
CREATE OR REPLACE FUNCTION normalize_name(name TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN UPPER(
        REGEXP_REPLACE(
            TRANSLATE(name, 'ÁÉÍÓÚÑÜ', 'AEIOUÑU'),
            '\s+', ' ', 'g'
        )
    );
END;
$$ LANGUAGE plpgsql;

-- Trigger para actualizar updated_at en persons
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_persons_updated_at
    BEFORE UPDATE ON persons
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- VISTAS ÚTILES
-- =====================================================

-- Vista de estadísticas diarias
CREATE OR REPLACE VIEW daily_stats AS
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_checks,
    AVG(global_risk_score) as avg_risk_score,
    COUNT(CASE WHEN global_risk_level = 'BAJO' THEN 1 END) as low_risk,
    COUNT(CASE WHEN global_risk_level = 'MEDIO' THEN 1 END) as medium_risk,
    COUNT(CASE WHEN global_risk_level = 'ALTO' THEN 1 END) as high_risk,
    COUNT(CASE WHEN global_risk_level = 'CRÍTICO' THEN 1 END) as critical_risk,
    AVG(processing_time_ms) as avg_processing_time
FROM background_checks
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Vista de top usuarios
CREATE OR REPLACE VIEW top_users AS
SELECT 
    requested_by,
    COUNT(*) as total_checks,
    AVG(global_risk_score) as avg_risk_score,
    COUNT(CASE WHEN global_risk_level IN ('ALTO', 'CRÍTICO') THEN 1 END) as high_risk_checks,
    MIN(created_at) as first_check,
    MAX(created_at) as last_check
FROM background_checks
GROUP BY requested_by
ORDER BY total_checks DESC;

-- =====================================================
-- DATOS DE EJEMPLO (OPCIONAL - Solo para desarrollo)
-- =====================================================

-- Insertar algunos CURPs de ejemplo para testing
INSERT INTO curp_validations (curp, nombre_completo, fecha_nacimiento, sexo, estado, source)
VALUES 
    ('GALJ850615HDFRPN01', 'JUAN GARCIA LOPEZ', '1985-06-15', 'H', 'DISTRITO FEDERAL', 'manual'),
    ('ROMC900312MDFNRL03', 'MARIA DEL CARMEN RODRIGUEZ', '1990-03-12', 'M', 'DISTRITO FEDERAL', 'manual'),
    ('SAHP750820HGRNNL09', 'PEDRO SANCHEZ HERNANDEZ', '1975-08-20', 'H', 'GUERRERO', 'manual')
ON CONFLICT (curp) DO NOTHING;

-- =====================================================
-- PERMISOS (Ajustar según tu configuración)
-- =====================================================

-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO kyc_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO kyc_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO kyc_user;

-- =====================================================
-- INFORMACIÓN
-- =====================================================

-- Mostrar resumen de tablas creadas
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Fin del script
SELECT 'KYC Platform Database initialized successfully!' as status;
