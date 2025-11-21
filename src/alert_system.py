import logging
from typing import Dict, List
import smtplib
from email.mime.text import MIMEText

class AlertManager:
    def __init__(self, config_file: str = None):
        self.alerts = []
        self.config = self._load_config(config_file)
    
    def generate_alert(self, project_id: str, skill_gaps: List[Dict]):
        """Genera alertas para gaps de habilidades"""
        
        for gap in skill_gaps:
            alert_message = (
                f"🚨 ALERTA: Proyecto {project_id} - Gap en habilidad {gap['skill']}\n"
                f"   • Horas requeridas: {gap['hours_needed']}\n"
                f"   • Horas cubiertas: {gap['hours_covered']}\n"
                f"   • Nivel requerido: {gap['level_required']}\n"
                f"   • Nivel cubierto: {gap['level_covered']}\n"
            )
            
            self.alerts.append({
                'project_id': project_id,
                'skill': gap['skill'],
                'message': alert_message,
                'severity': self._calculate_severity(gap),
                'timestamp': self._get_timestamp()
            })
            
            logging.warning(alert_message)
    
    def _calculate_severity(self, gap: Dict) -> str:
        """Calcula la severidad del gap"""
        coverage_ratio = gap['hours_covered'] / gap['hours_needed'] if gap['hours_needed'] > 0 else 0
        level_ratio = gap['level_covered'] / gap['level_required'] if gap['level_required'] > 0 else 0
        
        if coverage_ratio < 0.5 or level_ratio < 0.7:
            return "CRITICAL"
        elif coverage_ratio < 0.8 or level_ratio < 0.9:
            return "HIGH"
        else:
            return "MEDIUM"
    
    def send_email_alerts(self, recipients: List[str]):
        """Envía alertas por email"""
        if not self.alerts:
            return
            
        critical_alerts = [a for a in self.alerts if a['severity'] == 'CRITICAL']
        
        if critical_alerts:
            subject = f"🚨 Alertas Críticas de Asignación - {len(critical_alerts)} proyectos afectados"
            body = self._format_email_body(critical_alerts)
            self._send_email(recipients, subject, body)
    
    def _format_email_body(self, alerts: List[Dict]) -> str:
        """Formatea el cuerpo del email"""
        body = "Resumen de Alertas Críticas:\n\n"
        
        for alert in alerts:
            body += f"Proyecto: {alert['project_id']}\n"
            body += f"Habilidad: {alert['skill']}\n"
            body += f"Severidad: {alert['severity']}\n"
            body += f"Mensaje: {alert['message']}\n"
            body += "-" * 50 + "\n"
            
        return body
    
    def _send_email(self, recipients: List[str], subject: str, body: str):
        """Envía email (implementación básica)"""
        try:
            # Configurar envío de email según necesidades
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = self.config.get('email_from', 'noreply@company.com')
            msg['To'] = ', '.join(recipients)
            
            # Aquí iría la lógica real de envío de email
            logging.info(f"Email preparado para: {recipients}")
            logging.info(f"Asunto: {subject}")
            logging.info(f"Cuerpo:\n{body}")
            
        except Exception as e:
            logging.error(f"Error enviando email: {e}")
    
    def _load_config(self, config_file: str) -> Dict:
        """Carga configuración desde archivo"""
        # Configuración básica - puedes extender esto para cargar desde archivo
        return {
            'email_from': 'team-planner@contoso.com',
            'smtp_server': 'smtp.office365.com',
            'smtp_port': 587
        }
    
    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_alerts_summary(self) -> Dict:
        """Retorna un resumen de todas las alertas"""
        summary = {
            'total_alerts': len(self.alerts),
            'critical_alerts': len([a for a in self.alerts if a['severity'] == 'CRITICAL']),
            'high_alerts': len([a for a in self.alerts if a['severity'] == 'HIGH']),
            'medium_alerts': len([a for a in self.alerts if a['severity'] == 'MEDIUM']),
            'projects_affected': len(set(a['project_id'] for a in self.alerts))
        }
        return summary
    
    def clear_alerts(self):
        """Limpia todas las alertas"""
        self.alerts.clear()
        logging.info("Todas las alertas han sido limpiadas")