"""
Database Manager
================
Gestión de base de datos PostgreSQL para la plataforma KYC
"""

import asyncpg
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import logging
import os

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gestor de base de datos PostgreSQL"""
    
    def __init__(self):
        self.pool = None
        self.database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://kyc_user:kyc_password@localhost:5432/kyc_db"
        )
    
    async def initialize(self):
        """Inicializa el pool de conexiones"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            
            # Crear tablas si no existen
            await self._create_tables()
            
            logger.info("✅ Base de datos inicializada correctamente")
        except Exception as e:
            logger.error(f"❌ Error inicializando base de datos: {e}")
            raise
    
    async def close(self):
        """Cierra el pool de conexiones"""
        if self.pool:
            await self.pool.close()
            logger.info("Base de datos cerrada")
    
    async def _create_tables(self):
        """Crea las tablas necesarias"""
        
        async with self.pool.acquire() as conn:
            # Tabla de personas verificadas
            await conn.execute("""
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
                )
            """)
            
            # Tabla de background checks
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS background_checks (
                    id SERIAL PRIMARY KEY,
                    check_id UUID UNIQUE NOT NULL,
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
                    created_at TIMESTAMP DEFAULT NOW(),
                    INDEX idx_check_id (check_id),
                    INDEX idx_curp (curp),
                    INDEX idx_risk_level (global_risk_level),
                    INDEX idx_created_at (created_at)
                )
            """)
            
            # Tabla de validación de CURP (cache)
            await conn.execute("""
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
                    INDEX idx_curp_val (curp)
                )
            """)
            
            # Tabla de auditoría
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id SERIAL PRIMARY KEY,
                    event_type VARCHAR(50) NOT NULL,
                    user_id VARCHAR(100),
                    check_id UUID,
                    description TEXT,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    INDEX idx_event_type (event_type),
                    INDEX idx_user_id (user_id),
                    INDEX idx_created_at (created_at)
                )
            """)
            
            logger.info("Tablas creadas/verificadas correctamente")
    
    async def save_background_check(self, check_data: Dict[str, Any]) -> int:
        """Guarda un background check completo"""
        
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # 1. Guardar o actualizar persona
                person_id = await conn.fetchval("""
                    INSERT INTO persons (full_name, curp, rfc, email, phone, birth_date)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (curp) 
                    DO UPDATE SET 
                        full_name = EXCLUDED.full_name,
                        email = EXCLUDED.email,
                        phone = EXCLUDED.phone,
                        updated_at = NOW()
                    RETURNING id
                """,
                    check_data["subject"]["full_name"],
                    check_data["subject"].get("curp"),
                    check_data["subject"].get("rfc"),
                    check_data["subject"].get("email"),
                    check_data["subject"].get("phone"),
                    None  # birth_date se puede parsear si está disponible
                )
                
                # 2. Guardar background check
                check_id = await conn.fetchval("""
                    INSERT INTO background_checks (
                        check_id, person_id, full_name, curp, email, phone,
                        global_risk_score, global_risk_level, flags, critical_alerts,
                        rnd_results, enrichment_results, sanctions_results,
                        network_analysis, curp_validation, sources_consulted,
                        processing_time_ms, consent_id, requested_by
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                        $11, $12, $13, $14, $15, $16, $17, $18, $19
                    )
                    RETURNING id
                """,
                    check_data["check_id"],
                    person_id,
                    check_data["subject"]["full_name"],
                    check_data["subject"].get("curp"),
                    check_data["subject"].get("email"),
                    check_data["subject"].get("phone"),
                    check_data["global_risk_score"],
                    check_data["global_risk_level"],
                    json.dumps(check_data.get("flags", [])),
                    json.dumps(check_data.get("critical_alerts", [])),
                    json.dumps(check_data.get("rnd_results")),
                    json.dumps(check_data.get("enrichment_results")),
                    json.dumps(check_data.get("sanctions_results")),
                    json.dumps(check_data.get("network_analysis")),
                    json.dumps(check_data.get("curp_validation")),
                    json.dumps(check_data.get("sources_consulted", [])),
                    check_data.get("processing_time_ms"),
                    check_data["consent_id"],
                    check_data["requested_by"]
                )
                
                # 3. Registrar en auditoría
                await conn.execute("""
                    INSERT INTO audit_log (event_type, user_id, check_id, description, metadata)
                    VALUES ($1, $2, $3, $4, $5)
                """,
                    "BACKGROUND_CHECK_COMPLETED",
                    check_data["requested_by"],
                    check_data["check_id"],
                    f"Background check completado para {check_data['subject']['full_name']}",
                    json.dumps({
                        "risk_level": check_data["global_risk_level"],
                        "risk_score": check_data["global_risk_score"]
                    })
                )
                
                logger.info(f"Background check guardado: {check_data['check_id']}")
                return check_id
    
    async def get_background_check(self, check_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene un background check por su ID"""
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT 
                    check_id, full_name, curp, email, phone,
                    global_risk_score, global_risk_level, flags, critical_alerts,
                    rnd_results, enrichment_results, sanctions_results,
                    network_analysis, curp_validation, sources_consulted,
                    processing_time_ms, consent_id, requested_by, created_at
                FROM background_checks
                WHERE check_id = $1
            """, check_id)
            
            if not row:
                return None
            
            return {
                "check_id": str(row["check_id"]),
                "timestamp": row["created_at"].isoformat(),
                "subject": {
                    "full_name": row["full_name"],
                    "curp": row["curp"],
                    "email": row["email"],
                    "phone": row["phone"]
                },
                "global_risk_score": row["global_risk_score"],
                "global_risk_level": row["global_risk_level"],
                "flags": json.loads(row["flags"]) if row["flags"] else [],
                "critical_alerts": json.loads(row["critical_alerts"]) if row["critical_alerts"] else [],
                "rnd_results": json.loads(row["rnd_results"]) if row["rnd_results"] else None,
                "enrichment_results": json.loads(row["enrichment_results"]) if row["enrichment_results"] else None,
                "sanctions_results": json.loads(row["sanctions_results"]) if row["sanctions_results"] else None,
                "network_analysis": json.loads(row["network_analysis"]) if row["network_analysis"] else None,
                "curp_validation": json.loads(row["curp_validation"]) if row["curp_validation"] else None,
                "sources_consulted": json.loads(row["sources_consulted"]) if row["sources_consulted"] else [],
                "processing_time_ms": row["processing_time_ms"],
                "consent_id": row["consent_id"],
                "requested_by": row["requested_by"]
            }
    
    async def check_curp(self, curp: str) -> Dict[str, Any]:
        """Verifica si un CURP existe en la base de datos"""
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT curp, nombre_completo, fecha_nacimiento, sexo, estado, is_valid
                FROM curp_validations
                WHERE curp = $1
            """, curp)
            
            if row:
                return {
                    "exists": True,
                    "data": {
                        "nombre_completo": row["nombre_completo"],
                        "fecha_nacimiento": row["fecha_nacimiento"].isoformat() if row["fecha_nacimiento"] else None,
                        "sexo": row["sexo"],
                        "estado": row["estado"],
                        "is_valid": row["is_valid"]
                    }
                }
            
            return {"exists": False, "data": None}
    
    async def save_curp_validation(self, curp_data: Dict[str, Any]):
        """Guarda o actualiza una validación de CURP"""
        
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO curp_validations (
                    curp, nombre_completo, fecha_nacimiento, sexo, estado, is_valid, source
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (curp) 
                DO UPDATE SET 
                    nombre_completo = EXCLUDED.nombre_completo,
                    validation_date = NOW()
            """,
                curp_data["curp"],
                curp_data.get("nombre_completo"),
                curp_data.get("fecha_nacimiento"),
                curp_data.get("sexo"),
                curp_data.get("estado"),
                curp_data.get("is_valid", True),
                curp_data.get("source", "manual")
            )
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema"""
        
        async with self.pool.acquire() as conn:
            # Total de checks
            total_checks = await conn.fetchval(
                "SELECT COUNT(*) FROM background_checks"
            )
            
            # Checks hoy
            checks_today = await conn.fetchval("""
                SELECT COUNT(*) FROM background_checks
                WHERE created_at >= CURRENT_DATE
            """)
            
            # Checks esta semana
            checks_this_week = await conn.fetchval("""
                SELECT COUNT(*) FROM background_checks
                WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
            """)
            
            # Checks este mes
            checks_this_month = await conn.fetchval("""
                SELECT COUNT(*) FROM background_checks
                WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE)
            """)
            
            # Detecciones de alto riesgo
            high_risk = await conn.fetchval("""
                SELECT COUNT(*) FROM background_checks
                WHERE global_risk_level IN ('ALTO', 'CRÍTICO')
            """)
            
            # Tiempo promedio de procesamiento
            avg_time = await conn.fetchval("""
                SELECT AVG(processing_time_ms) FROM background_checks
                WHERE processing_time_ms IS NOT NULL
            """) or 0
            
            # Distribución de riesgo
            risk_dist = await conn.fetch("""
                SELECT global_risk_level, COUNT(*) as count
                FROM background_checks
                GROUP BY global_risk_level
                ORDER BY global_risk_level
            """)
            
            risk_distribution = {row["global_risk_level"]: row["count"] for row in risk_dist}
            
            # Top indicadores de riesgo (flags más comunes)
            # Simulación - en producción esto vendría de análisis de flags
            top_indicators = [
                {"name": "Registros en RND", "count": high_risk},
                {"name": "Email comprometido", "count": int(total_checks * 0.15)},
                {"name": "Listas de sanciones", "count": int(total_checks * 0.05)},
                {"name": "CURP inválido", "count": int(total_checks * 0.08)},
                {"name": "Teléfono spam", "count": int(total_checks * 0.12)}
            ]
            
            return {
                "total_checks": total_checks,
                "checks_today": checks_today,
                "checks_this_week": checks_this_week,
                "checks_this_month": checks_this_month,
                "high_risk_detections": high_risk,
                "average_processing_time": float(avg_time),
                "risk_distribution": risk_distribution,
                "top_risk_indicators": top_indicators
            }
