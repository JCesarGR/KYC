"""
KYC Platform - API Principal
============================
Plataforma unificada de Background Checks y KYC
Integra: SynkData + RND Scraper + Validación CURP
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import logging
from contextlib import asynccontextmanager

# Importar módulos propios
from modules.rnd_scraper import RNDScraper, ResultadoRND
from modules.enrichment import EnrichmentEngine
from modules.sanctions import SanctionsEngine
from modules.relationship import RelationshipEngine
from modules.curp_validator import CURPValidator
from database.db_manager import DatabaseManager
from utils.scoring import calculate_global_risk
from utils.reporting import generate_pdf_report

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Estado global de la aplicación
app_state = {
    "db": None,
    "rnd_scraper": None,
    "enrichment_engine": None,
    "sanctions_engine": None,
    "relationship_engine": None,
    "curp_validator": None,
    "stats": {
        "total_checks": 0,
        "checks_today": 0,
        "high_risk_detections": 0
    }
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manejo del ciclo de vida de la aplicación"""
    # Startup
    logger.info("🚀 Iniciando KYC Platform...")
    
    # Inicializar base de datos
    app_state["db"] = DatabaseManager()
    await app_state["db"].initialize()
    
    # Inicializar motores
    app_state["rnd_scraper"] = RNDScraper()
    app_state["enrichment_engine"] = EnrichmentEngine()
    app_state["sanctions_engine"] = SanctionsEngine()
    app_state["relationship_engine"] = RelationshipEngine()
    app_state["curp_validator"] = CURPValidator(app_state["db"])
    
    logger.info("✅ Todos los servicios iniciados correctamente")
    
    yield
    
    # Shutdown
    logger.info("🛑 Cerrando KYC Platform...")
    await app_state["db"].close()

# Inicializar FastAPI
app = FastAPI(
    title="KYC Platform API",
    description="Plataforma completa de Background Checks y KYC para México",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== MODELOS DE DATOS ====================

class BackgroundCheckRequest(BaseModel):
    """Solicitud de background check completo"""
    
    # Datos personales
    full_name: str = Field(..., description="Nombre completo")
    first_name: str = Field(..., description="Nombre(s)")
    paternal_surname: str = Field(..., description="Apellido paterno")
    maternal_surname: Optional[str] = Field(None, description="Apellido materno")
    birth_date: Optional[str] = Field(None, description="Fecha de nacimiento DD/MM/YYYY")
    
    # Identificación
    curp: Optional[str] = Field(None, description="CURP")
    rfc: Optional[str] = Field(None, description="RFC")
    
    # Contacto
    email: Optional[EmailStr] = Field(None, description="Email")
    phone: Optional[str] = Field(None, description="Teléfono con código de país")
    
    # Dirección
    address: Optional[str] = Field(None, description="Dirección completa")
    state: Optional[str] = Field("Nacional", description="Estado para búsqueda RND")
    
    # Cumplimiento
    consent_id: str = Field(..., description="ID de consentimiento del titular")
    requested_by: str = Field(..., description="Usuario que solicita el check")
    
    # Opciones
    include_rnd_check: bool = Field(True, description="Incluir búsqueda en RND")
    include_sanctions: bool = Field(True, description="Incluir búsqueda en listas negras")
    include_enrichment: bool = Field(True, description="Incluir enriquecimiento de datos")
    include_network_analysis: bool = Field(True, description="Incluir análisis de red")

class BackgroundCheckResponse(BaseModel):
    """Respuesta completa del background check"""
    
    # Identificadores
    check_id: str
    timestamp: str
    
    # Información de la persona
    subject: Dict[str, Any]
    
    # Resultados de scoring
    global_risk_score: float
    global_risk_level: str
    
    # Flags y alertas
    flags: List[str]
    critical_alerts: List[Dict[str, Any]]
    
    # Resultados por módulo
    rnd_results: Optional[List[Dict[str, Any]]] = None
    enrichment_results: Optional[Dict[str, Any]] = None
    sanctions_results: Optional[Dict[str, Any]] = None
    network_analysis: Optional[Dict[str, Any]] = None
    curp_validation: Optional[Dict[str, Any]] = None
    
    # Metadata
    sources_consulted: List[str]
    processing_time_ms: float
    consent_id: str
    requested_by: str

class CURPValidationRequest(BaseModel):
    """Solicitud de validación de CURP"""
    curp: str
    full_name: Optional[str] = None
    birth_date: Optional[str] = None

class StatsResponse(BaseModel):
    """Estadísticas del sistema"""
    total_checks: int
    checks_today: int
    checks_this_week: int
    checks_this_month: int
    high_risk_detections: int
    average_processing_time: float
    risk_distribution: Dict[str, int]
    top_risk_indicators: List[Dict[str, Any]]

# ==================== ENDPOINTS ====================

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "service": "KYC Platform API",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/api/docs"
    }

@app.get("/api/health")
async def health_check():
    """Health check del servicio"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": app_state["db"] is not None,
            "rnd_scraper": app_state["rnd_scraper"] is not None,
            "enrichment": app_state["enrichment_engine"] is not None,
            "sanctions": app_state["sanctions_engine"] is not None,
            "relationships": app_state["relationship_engine"] is not None
        }
    }

@app.post("/api/v1/background-check", response_model=BackgroundCheckResponse)
async def background_check(
    request: BackgroundCheckRequest,
    background_tasks: BackgroundTasks
):
    """
    Ejecuta un background check completo
    
    Incluye:
    - Validación de CURP
    - Búsqueda en RND (Registro Nacional de Detenciones)
    - Enriquecimiento de email y teléfono
    - Búsqueda en listas de sanciones (OFAC, ONU, SAT 69-B, etc.)
    - Análisis de red y relaciones
    """
    start_time = datetime.utcnow()
    check_id = str(uuid.uuid4())
    
    logger.info(f"[{check_id}] Iniciando background check para: {request.full_name}")
    
    # Inicializar respuesta
    results = {
        "check_id": check_id,
        "timestamp": start_time.isoformat(),
        "subject": {
            "full_name": request.full_name,
            "curp": request.curp,
            "email": request.email,
            "phone": request.phone
        },
        "flags": [],
        "critical_alerts": [],
        "sources_consulted": [],
    }
    
    try:
        # 1. VALIDACIÓN DE CURP
        if request.curp:
            logger.info(f"[{check_id}] Validando CURP...")
            curp_validation = await app_state["curp_validator"].validate(
                curp=request.curp,
                full_name=request.full_name,
                birth_date=request.birth_date
            )
            results["curp_validation"] = curp_validation
            results["sources_consulted"].append("CURP Database")
            
            if not curp_validation["is_valid"]:
                results["flags"].append("⚠️ CURP inválido o no coincide con datos proporcionados")
                results["critical_alerts"].append({
                    "type": "INVALID_CURP",
                    "severity": "HIGH",
                    "message": curp_validation["message"]
                })
        
        # 2. BÚSQUEDA EN RND (Registro Nacional de Detenciones)
        if request.include_rnd_check:
            logger.info(f"[{check_id}] Buscando en RND...")
            rnd_results = app_state["rnd_scraper"].buscar(
                nombre=request.first_name,
                paterno=request.paternal_surname,
                materno=request.maternal_surname or "",
                fecha_nac=request.birth_date or "",
                estado=request.state
            )
            
            # Convertir resultados a dict
            rnd_data = []
            for resultado in rnd_results:
                rnd_dict = {
                    "nombre_buscado": resultado.nombre_buscado,
                    "estado": resultado.estado,
                    "nombre": resultado.nombre,
                    "lugar_detencion": resultado.lugar_detencion,
                    "direccion": resultado.direccion,
                    "fecha_hora": resultado.fecha_hora,
                    "autoridad_detiene": resultado.autoridad_detiene,
                    "autoridad_resguarda": resultado.autoridad_resguarda,
                    "sin_resultados": resultado.sin_resultados,
                    "error": resultado.error
                }
                rnd_data.append(rnd_dict)
            
            results["rnd_results"] = rnd_data
            results["sources_consulted"].append("RND (SSPC)")
            
            # Verificar si hay detenciones
            detenciones_encontradas = [r for r in rnd_data if not r["sin_resultados"] and not r["error"]]
            if detenciones_encontradas:
                results["flags"].append("🚨 ALERTA: Se encontraron registros de detención")
                results["critical_alerts"].append({
                    "type": "RND_DETENTION_FOUND",
                    "severity": "CRITICAL",
                    "message": f"Se encontraron {len(detenciones_encontradas)} registro(s) de detención",
                    "details": detenciones_encontradas
                })
        
        # 3. ENRIQUECIMIENTO DE DATOS
        if request.include_enrichment:
            logger.info(f"[{check_id}] Enriqueciendo datos...")
            enrichment_results = {}
            
            if request.email:
                email_data = await app_state["enrichment_engine"].enrich_email(request.email)
                enrichment_results["email"] = email_data
                results["sources_consulted"].extend([
                    "HaveIBeenPwned",
                    "Hunter.io",
                    "Gravatar"
                ])
                
                if email_data["risk_level"] in ["ALTO", "CRÍTICO"]:
                    results["flags"].append(f"⚠️ Email de riesgo {email_data['risk_level']}")
            
            if request.phone:
                phone_data = await app_state["enrichment_engine"].enrich_phone(request.phone)
                enrichment_results["phone"] = phone_data
                results["sources_consulted"].extend([
                    "NumVerify",
                    "ShouldIAnswer"
                ])
                
                if phone_data.get("is_spam_reported"):
                    results["flags"].append("⚠️ Teléfono reportado como spam")
            
            results["enrichment_results"] = enrichment_results
        
        # 4. BÚSQUEDA EN LISTAS DE SANCIONES
        if request.include_sanctions:
            logger.info(f"[{check_id}] Buscando en listas de sanciones...")
            sanctions_results = await app_state["sanctions_engine"].search(request.full_name)
            results["sanctions_results"] = sanctions_results
            results["sources_consulted"].extend([
                "OFAC SDN",
                "ONU Consolidated List",
                "OpenSanctions",
                "SAT Lista 69-B",
                "DOF",
                "SCJN"
            ])
            
            if sanctions_results.get("is_sanctioned"):
                results["flags"].append("🚨 ALERTA CRÍTICA: Persona en lista de sanciones")
                results["critical_alerts"].append({
                    "type": "SANCTIONS_MATCH",
                    "severity": "CRITICAL",
                    "message": "Coincidencia en listas de sanciones internacionales",
                    "details": sanctions_results["matches"]
                })
            
            if sanctions_results.get("is_pep"):
                results["flags"].append("⚠️ Persona Expuesta Políticamente (PEP)")
        
        # 5. ANÁLISIS DE RED Y RELACIONES
        if request.include_network_analysis:
            logger.info(f"[{check_id}] Analizando red de relaciones...")
            
            # Calcular score de riesgo preliminar
            preliminary_score = calculate_global_risk({
                "rnd": results.get("rnd_results"),
                "enrichment": results.get("enrichment_results"),
                "sanctions": results.get("sanctions_results")
            })
            
            # Ingresar persona en el grafo
            person_node = await app_state["relationship_engine"].ingest_person(
                name=request.full_name,
                email=request.email,
                phone=request.phone,
                curp=request.curp,
                rfc=request.rfc,
                address=request.address,
                risk_score=preliminary_score["score"],
                risk_level=preliminary_score["level"]
            )
            
            # Analizar red
            network_analysis = await app_state["relationship_engine"].analyze_network(
                person_id=person_node["id"],
                depth=2
            )
            results["network_analysis"] = network_analysis
            results["sources_consulted"].append("Relationship Graph")
            
            if network_analysis.get("suspicious_patterns"):
                results["flags"].append("⚠️ Patrones sospechosos en red de relaciones")
                for pattern in network_analysis["suspicious_patterns"]:
                    results["critical_alerts"].append({
                        "type": "NETWORK_PATTERN",
                        "severity": "MEDIUM",
                        "message": pattern["description"]
                    })
        
        # 6. CALCULAR SCORE GLOBAL DE RIESGO
        risk_calculation = calculate_global_risk({
            "rnd": results.get("rnd_results"),
            "enrichment": results.get("enrichment_results"),
            "sanctions": results.get("sanctions_results"),
            "network": results.get("network_analysis"),
            "curp": results.get("curp_validation")
        })
        
        results["global_risk_score"] = risk_calculation["score"]
        results["global_risk_level"] = risk_calculation["level"]
        
        # 7. GUARDAR EN BASE DE DATOS
        await app_state["db"].save_background_check({
            **results,
            "consent_id": request.consent_id,
            "requested_by": request.requested_by
        })
        
        # 8. ACTUALIZAR ESTADÍSTICAS
        app_state["stats"]["total_checks"] += 1
        app_state["stats"]["checks_today"] += 1
        if results["global_risk_level"] in ["ALTO", "CRÍTICO"]:
            app_state["stats"]["high_risk_detections"] += 1
        
        # 9. CALCULAR TIEMPO DE PROCESAMIENTO
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds() * 1000
        results["processing_time_ms"] = processing_time
        results["consent_id"] = request.consent_id
        results["requested_by"] = request.requested_by
        
        # 10. PROGRAMAR GENERACIÓN DE REPORTE PDF (tarea asíncrona)
        background_tasks.add_task(
            generate_pdf_report,
            check_id=check_id,
            data=results
        )
        
        logger.info(
            f"[{check_id}] Check completado - "
            f"Riesgo: {results['global_risk_level']} "
            f"({results['global_risk_score']:.1f}/100) - "
            f"Tiempo: {processing_time:.0f}ms"
        )
        
        return BackgroundCheckResponse(**results)
        
    except Exception as e:
        logger.error(f"[{check_id}] Error en background check: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando background check: {str(e)}"
        )

@app.post("/api/v1/validate-curp")
async def validate_curp(request: CURPValidationRequest):
    """Valida una CURP contra la base de datos oficial"""
    try:
        result = await app_state["curp_validator"].validate(
            curp=request.curp,
            full_name=request.full_name,
            birth_date=request.birth_date
        )
        return result
    except Exception as e:
        logger.error(f"Error validando CURP: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/stats", response_model=StatsResponse)
async def get_stats():
    """Obtiene estadísticas del sistema"""
    try:
        db_stats = await app_state["db"].get_statistics()
        
        return StatsResponse(
            total_checks=db_stats["total_checks"],
            checks_today=db_stats["checks_today"],
            checks_this_week=db_stats["checks_this_week"],
            checks_this_month=db_stats["checks_this_month"],
            high_risk_detections=db_stats["high_risk_detections"],
            average_processing_time=db_stats["average_processing_time"],
            risk_distribution=db_stats["risk_distribution"],
            top_risk_indicators=db_stats["top_risk_indicators"]
        )
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/check/{check_id}")
async def get_check_results(check_id: str):
    """Obtiene los resultados de un background check previo"""
    try:
        results = await app_state["db"].get_background_check(check_id)
        if not results:
            raise HTTPException(status_code=404, detail="Check no encontrado")
        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo check {check_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/network/visualize/{person_id}")
async def visualize_network(person_id: str, depth: int = 2):
    """Obtiene datos de visualización del grafo de relaciones"""
    try:
        network_data = await app_state["relationship_engine"].export_visualization(
            person_id=person_id,
            depth=depth
        )
        return network_data
    except Exception as e:
        logger.error(f"Error generando visualización: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
