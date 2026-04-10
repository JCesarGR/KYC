"""
Módulo de Scoring
=================
Cálculo de riesgo global basado en múltiples fuentes
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

def calculate_global_risk(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcula el score de riesgo global ponderado
    
    Ponderación:
    - 20% Email enrichment
    - 15% Phone enrichment
    - 40% Sanctions/Identity
    - 25% Network analysis
    
    Args:
        data: Dict con resultados de cada módulo
    
    Returns:
        Dict con score (0-100) y level (BAJO/MEDIO/ALTO/CRÍTICO)
    """
    
    scores = {}
    weights = {}
    
    # 1. Email Score (0-100)
    if data.get("enrichment") and data["enrichment"].get("email"):
        email_data = data["enrichment"]["email"]
        email_score = 0
        
        # Brechas de datos
        breach_count = email_data.get("breach_count", 0)
        if breach_count >= 5:
            email_score += 40
        elif breach_count >= 2:
            email_score += 20
        
        # Datos sensibles expuestos
        if email_data.get("sensitive_data_exposed"):
            email_score += 30
        
        # Email desechable
        if email_data.get("is_disposable"):
            email_score += 50
        
        # No entregable
        if email_data.get("deliverable") == False:
            email_score += 20
        
        scores["email"] = min(100, email_score)
        weights["email"] = 0.20
    
    # 2. Phone Score (0-100)
    if data.get("enrichment") and data["enrichment"].get("phone"):
        phone_data = data["enrichment"]["phone"]
        phone_score = 0
        
        # Reportado como spam
        if phone_data.get("is_spam_reported"):
            phone_score += 60
        
        # Número inválido
        if not phone_data.get("is_valid"):
            phone_score += 40
        
        # VoIP (más propenso a fraude)
        if phone_data.get("line_type") == "VOIP":
            phone_score += 20
        
        scores["phone"] = min(100, phone_score)
        weights["phone"] = 0.15
    
    # 3. Identity/Sanctions Score (0-100)
    identity_score = 0
    
    # RND - Detenciones
    if data.get("rnd"):
        detenciones = [r for r in data["rnd"] if not r.get("sin_resultados") and not r.get("error")]
        if detenciones:
            identity_score += 80  # CRÍTICO
    
    # Sanciones internacionales
    if data.get("sanctions"):
        if data["sanctions"].get("is_sanctioned"):
            identity_score = 100  # CRÍTICO AUTOMÁTICO
        elif data["sanctions"].get("is_pep"):
            identity_score += 50  # ALTO
    
    # CURP inválido
    if data.get("curp"):
        if not data["curp"].get("is_valid"):
            identity_score += 30
    
    if identity_score > 0:
        scores["identity"] = min(100, identity_score)
        weights["identity"] = 0.40
    
    # 4. Network Score (0-100)
    if data.get("network"):
        network_score = 0
        
        # Patrones sospechosos
        suspicious_patterns = data["network"].get("suspicious_patterns", [])
        network_score += min(50, len(suspicious_patterns) * 15)
        
        # Conexiones de alto riesgo
        high_risk_connections = data["network"].get("high_risk_connections", 0)
        network_score += min(50, high_risk_connections * 20)
        
        if network_score > 0:
            scores["network"] = min(100, network_score)
            weights["network"] = 0.25
    
    # Calcular score ponderado
    if not scores:
        return {
            "score": 0,
            "level": "BAJO",
            "components": {},
            "message": "No hay suficientes datos para calcular riesgo"
        }
    
    # Normalizar pesos si no están todos los componentes
    total_weight = sum(weights.values())
    if total_weight > 0:
        weights = {k: v / total_weight for k, v in weights.items()}
    
    # Calcular score global
    global_score = sum(scores[k] * weights.get(k, 0) for k in scores.keys())
    
    # Determinar nivel de riesgo
    if global_score >= 70:
        level = "CRÍTICO"
    elif global_score >= 50:
        level = "ALTO"
    elif global_score >= 30:
        level = "MEDIO"
    else:
        level = "BAJO"
    
    return {
        "score": round(global_score, 2),
        "level": level,
        "components": {
            k: {
                "score": scores[k],
                "weight": weights.get(k, 0) * 100
            }
            for k in scores.keys()
        }
    }


def calculate_email_risk(email_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calcula riesgo específico de email"""
    
    risk_score = 0
    indicators = []
    
    # Brechas
    breach_count = email_data.get("breach_count", 0)
    if breach_count > 0:
        risk_score += min(40, breach_count * 8)
        indicators.append(f"{breach_count} brecha(s) de datos")
    
    # Desechable
    if email_data.get("is_disposable"):
        risk_score += 50
        indicators.append("Email desechable")
    
    # No entregable
    if email_data.get("deliverable") == False:
        risk_score += 20
        indicators.append("Email no entregable")
    
    # Datos sensibles
    if email_data.get("sensitive_data_exposed"):
        risk_score += 30
        indicators.append("Datos sensibles expuestos")
    
    # Determinar nivel
    risk_score = min(100, risk_score)
    
    if risk_score >= 70:
        level = "CRÍTICO"
    elif risk_score >= 50:
        level = "ALTO"
    elif risk_score >= 30:
        level = "MEDIO"
    else:
        level = "BAJO"
    
    return {
        "score": risk_score,
        "level": level,
        "indicators": indicators
    }


def calculate_phone_risk(phone_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calcula riesgo específico de teléfono"""
    
    risk_score = 0
    indicators = []
    
    # Spam
    if phone_data.get("is_spam_reported"):
        risk_score += 60
        indicators.append("Reportado como spam")
    
    # Inválido
    if not phone_data.get("is_valid"):
        risk_score += 40
        indicators.append("Número inválido")
    
    # VoIP
    if phone_data.get("line_type") == "VOIP":
        risk_score += 20
        indicators.append("Línea VoIP")
    
    # Determinar nivel
    risk_score = min(100, risk_score)
    
    if risk_score >= 70:
        level = "CRÍTICO"
    elif risk_score >= 50:
        level = "ALTO"
    elif risk_score >= 30:
        level = "MEDIO"
    else:
        level = "BAJO"
    
    return {
        "score": risk_score,
        "level": level,
        "indicators": indicators
    }
