"""
Generador de Reportes PDF
=========================
Genera reportes en PDF de background checks
"""

import os
from datetime import datetime
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

async def generate_pdf_report(check_id: str, data: Dict[str, Any]):
    """
    Genera reporte PDF de un background check
    
    Args:
        check_id: ID del check
        data: Datos completos del check
    """
    
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.platypus import Image as RLImage
        
        # Crear directorio de reportes si no existe
        reports_dir = "/app/reports"
        os.makedirs(reports_dir, exist_ok=True)
        
        # Nombre del archivo
        filename = f"{reports_dir}/check_{check_id}.pdf"
        
        # Crear documento
        doc = SimpleDocTemplate(filename, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=30
        )
        
        story.append(Paragraph("KYC Background Check Report", title_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Información del sujeto
        subject_data = [
            ["Campo", "Valor"],
            ["Nombre Completo", data["subject"]["full_name"]],
            ["CURP", data["subject"].get("curp", "N/A")],
            ["Email", data["subject"].get("email", "N/A")],
            ["Teléfono", data["subject"].get("phone", "N/A")],
        ]
        
        subject_table = Table(subject_data, colWidths=[2*inch, 4*inch])
        subject_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(Paragraph("Información del Sujeto", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        story.append(subject_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Score de Riesgo
        risk_color = colors.green
        if data["global_risk_level"] == "MEDIO":
            risk_color = colors.yellow
        elif data["global_risk_level"] == "ALTO":
            risk_color = colors.orange
        elif data["global_risk_level"] == "CRÍTICO":
            risk_color = colors.red
        
        risk_data = [
            ["Score Global", f"{data['global_risk_score']:.1f}/100"],
            ["Nivel de Riesgo", data["global_risk_level"]]
        ]
        
        risk_table = Table(risk_data, colWidths=[2*inch, 4*inch])
        risk_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), risk_color),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('PADDING', (0, 0), (-1, -1), 12),
        ]))
        
        story.append(Paragraph("Evaluación de Riesgo", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        story.append(risk_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Flags
        if data.get("flags"):
            story.append(Paragraph("Indicadores", styles['Heading2']))
            story.append(Spacer(1, 0.1*inch))
            
            for flag in data["flags"]:
                story.append(Paragraph(f"• {flag}", styles['Normal']))
            
            story.append(Spacer(1, 0.3*inch))
        
        # Alertas Críticas
        if data.get("critical_alerts"):
            story.append(Paragraph("⚠️ Alertas Críticas", styles['Heading2']))
            story.append(Spacer(1, 0.1*inch))
            
            for alert in data["critical_alerts"]:
                alert_text = f"<b>{alert['type']}</b> ({alert['severity']}): {alert['message']}"
                story.append(Paragraph(alert_text, styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
        
        # Metadata
        story.append(PageBreak())
        story.append(Paragraph("Metadata del Check", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        meta_data = [
            ["Check ID", check_id],
            ["Fecha", datetime.fromisoformat(data["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")],
            ["Solicitado por", data["requested_by"]],
            ["ID de Consentimiento", data["consent_id"]],
            ["Tiempo de Procesamiento", f"{data['processing_time_ms']:.0f} ms"],
            ["Fuentes Consultadas", str(len(data["sources_consulted"]))],
        ]
        
        meta_table = Table(meta_data, colWidths=[2*inch, 4*inch])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(meta_table)
        
        # Construir PDF
        doc.build(story)
        
        logger.info(f"✅ Reporte PDF generado: {filename}")
        return filename
        
    except Exception as e:
        logger.error(f"❌ Error generando reporte PDF: {e}")
        return None
