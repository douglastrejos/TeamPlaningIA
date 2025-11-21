import pandas as pd
import json
import os
from datetime import datetime
from typing import Dict, List
import logging
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

class ReportGenerator:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Configurar estilo para gráficos
        plt.style.use('default')
        sns.set_palette("husl")
        
    def generate_comprehensive_report(self, assignments: Dict, skill_gaps: Dict, project_tables: Dict):
        """Genera un reporte completo con todos los análisis"""
        logging.info("Generando reporte completo...")
        
        # 1. Reporte ejecutivo
        self._generate_executive_report(assignments, skill_gaps)
        
        # 2. Reporte detallado por proyecto
        self._generate_project_detail_reports(assignments, project_tables)
        
        # 3. Reporte de recursos
        self._generate_resource_utilization_report(assignments)
        
        # 4. Reporte de gaps de habilidades
        self._generate_skill_gap_report(skill_gaps)
        
        # 5. Gráficos y visualizaciones
        self._generate_visualizations(assignments, skill_gaps)
        
        logging.info("Reporte completo generado exitosamente")
    
    def _generate_executive_report(self, assignments: Dict, skill_gaps: Dict):
        """Genera reporte ejecutivo resumido"""
        executive_data = {
            'timestamp': datetime.now().isoformat(),
            'total_projects': len(assignments),
            'total_assignments': sum(len(proj['team_members']) for proj in assignments.values()),
            'projects_with_gaps': len(skill_gaps),
            'total_skill_gaps': sum(len(gaps) for gaps in skill_gaps.values()),
            'resource_utilization': self._calculate_resource_utilization(assignments),
            'critical_gaps': self._count_critical_gaps(skill_gaps)
        }
        
        report_content = f"""
# REPORTE EJECUTIVO - PLANIFICACIÓN DE EQUIPOS
## Contoso Consulting
### Fecha de generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## RESUMEN EJECUTIVO

### 📊 Métricas Principales
- **Proyectos planificados**: {executive_data['total_projects']}
- **Asignaciones totales**: {executive_data['total_assignments']}
- **Tasa de utilización de recursos**: {executive_data['resource_utilization']:.1%}
- **Proyectos con gaps**: {executive_data['projects_with_gaps']}
- **Gaps críticos identificados**: {executive_data['critical_gaps']}

### 🚨 Alertas Principales
"""
        
        # Agregar información de gaps críticos
        critical_projects = []
        for project_id, gaps in skill_gaps.items():
            critical_gaps = [gap for gap in gaps if gap.get('hours_gap', 0) > 100 or gap.get('level_gap', 0) > 0.3]
            if critical_gaps:
                critical_projects.append((project_id, critical_gaps))
        
        if critical_projects:
            for project_id, gaps in critical_projects[:5]:  # Mostrar solo los 5 más críticos
                report_content += f"- **{project_id}**: {len(gaps)} gaps críticos\n"
        else:
            report_content += "- No se identificaron gaps críticos\n"
        
        report_content += f"""

### 📈 Recomendaciones

1. **Asignación de Recursos**: {self._get_resource_recommendation(executive_data['resource_utilization'])}
2. **Gestión de Gaps**: {self._get_gap_management_recommendation(executive_data['critical_gaps'])}
3. **Planificación**: {self._get_planning_recommendation(executive_data['total_projects'])}

---

## DETALLE POR PROYECTO

"""
        
        # Agregar resumen por proyecto
        for project_id, assignment in assignments.items():
            project_gaps = skill_gaps.get(project_id, [])
            report_content += f"""
### 🎯 {assignment['project_name']} ({project_id})
- **Fecha inicio**: {assignment['start_date']}
- **Duración estimada**: {assignment['duration_weeks']} semanas
- **Tamaño del equipo**: {len(assignment['team_members'])} personas
- **Horas semanales totales**: {assignment['total_weekly_hours']}
- **Cobertura de habilidades**: {assignment['skill_coverage']:.1%}
- **Gaps identificados**: {len(project_gaps)}

"""
        
        # Guardar reporte ejecutivo
        report_path = os.path.join(self.output_dir, 'executive_report.md')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logging.info(f"Reporte ejecutivo guardado en: {report_path}")
    
    def _generate_project_detail_reports(self, assignments: Dict, project_tables: Dict):
        """Genera reportes detallados por proyecto"""
        for project_id, assignment in assignments.items():
            project_table = project_tables.get(project_id, {})
            
            report_content = f"""
# REPORTE DETALLADO - {assignment['project_name']}
## Proyecto: {project_id}

## INFORMACIÓN GENERAL
- **Nombre**: {assignment['project_name']}
- **Fecha de inicio**: {assignment['start_date']}
- **Fecha estimada de fin**: {assignment['estimated_end_date']}
- **Duración**: {assignment['duration_weeks']} semanas
- **Horas semanales totales**: {assignment['total_weekly_hours']}
- **Cobertura de habilidades**: {assignment['skill_coverage']:.1%}

## EQUIPO ASIGNADO

"""
            
            # Tabla de equipo
            if 'team_table' in project_table and not project_table['team_table'].empty:
                df = project_table['team_table']
                report_content += df.to_markdown(index=False)
            else:
                report_content += "No hay datos de equipo disponibles.\n"
            
            report_content += f"""

## DISTRIBUCIÓN DE HORAS

"""
            
            # Distribución de horas
            if assignment['team_members']:
                hours_data = []
                for member in assignment['team_members']:
                    hours_data.append({
                        'Empleado': member['name'],
                        'Horas/Semana': member['assigned_hours'],
                        'Roles': ', '.join(member.get('primary_skills', []))
                    })
                
                hours_df = pd.DataFrame(hours_data)
                report_content += hours_df.to_markdown(index=False)
            
            # Guardar reporte del proyecto
            safe_project_name = "".join(c for c in assignment['project_name'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            report_path = os.path.join(self.output_dir, f'project_{project_id}_{safe_project_name}.md')
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
        
        logging.info(f"Reportes detallados generados para {len(assignments)} proyectos")
    
    def _generate_resource_utilization_report(self, assignments: Dict):
        """Genera reporte de utilización de recursos"""
        resource_data = []
        
        # Recopilar datos de utilización
        employee_hours = {}
        
        for project_id, assignment in assignments.items():
            for member in assignment['team_members']:
                emp_id = member['employee_id']
                if emp_id not in employee_hours:
                    employee_hours[emp_id] = {
                        'name': member['name'],
                        'total_hours': 0,
                        'projects': []
                    }
                
                employee_hours[emp_id]['total_hours'] += member['assigned_hours']
                employee_hours[emp_id]['projects'].append(project_id)
        
        # Convertir a DataFrame
        utilization_data = []
        for emp_id, data in employee_hours.items():
            utilization_data.append({
                'Employee_ID': emp_id,
                'Name': data['name'],
                'Total_Weekly_Hours': data['total_hours'],
                'Number_of_Projects': len(data['projects']),
                'Projects': ', '.join(data['projects'])
            })
        
        df = pd.DataFrame(utilization_data)
        
        # Análisis de utilización
        total_employees = len(utilization_data)
        over_utilized = len(df[df['Total_Weekly_Hours'] > 40])
        under_utilized = len(df[df['Total_Weekly_Hours'] < 20])
        well_utilized = len(df[(df['Total_Weekly_Hours'] >= 20) & (df['Total_Weekly_Hours'] <= 40)])
        
        report_content = f"""
# REPORTE DE UTILIZACIÓN DE RECURSOS

## RESUMEN DE UTILIZACIÓN
- **Total de empleados asignados**: {total_employees}
- **Bien utilizados (20-40h/semana)**: {well_utilized}
- **Sobre-utilizados (>40h/semana)**: {over_utilized}
- **Sub-utilizados (<20h/semana)**: {under_utilized}

## DETALLE POR EMPLEADO

"""
        
        report_content += df.to_markdown(index=False)
        
        # Guardar reporte
        report_path = os.path.join(self.output_dir, 'resource_utilization_report.md')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        # Exportar a CSV
        csv_path = os.path.join(self.output_dir, 'resource_utilization.csv')
        df.to_csv(csv_path, index=False, encoding='utf-8')
        
        logging.info(f"Reporte de utilización guardado en: {report_path}")
    
    def _generate_skill_gap_report(self, skill_gaps: Dict):
        """Genera reporte de gaps de habilidades"""
        if not skill_gaps:
            report_content = """
# REPORTE DE GAPS DE HABILIDADES

## RESUMEN
No se identificaron gaps de habilidades en los proyectos.
"""
        else:
            gap_data = []
            for project_id, gaps in skill_gaps.items():
                for gap in gaps:
                    gap_data.append({
                        'Project_ID': project_id,
                        'Skill': gap['skill'],
                        'Hours_Needed': gap['hours_needed'],
                        'Hours_Covered': gap['hours_covered'],
                        'Hours_Gap': gap.get('hours_gap', 0),
                        'Level_Required': gap['level_required'],
                        'Level_Covered': gap['level_covered'],
                        'Level_Gap': gap.get('level_gap', 0),
                        'Severity': 'CRITICAL' if gap.get('hours_gap', 0) > 100 or gap.get('level_gap', 0) > 0.3 else 'HIGH'
                    })
            
            df = pd.DataFrame(gap_data)
            
            report_content = f"""
# REPORTE DE GAPS DE HABILIDADES

## RESUMEN
- **Total de gaps identificados**: {len(gap_data)}
- **Proyectos con gaps**: {len(skill_gaps)}
- **Gaps críticos**: {len(df[df['Severity'] == 'CRITICAL'])}
- **Gaps altos**: {len(df[df['Severity'] == 'HIGH'])}

## DETALLE DE GAPS

"""
            
            report_content += df.to_markdown(index=False)
            
            # Análisis por skill
            skill_analysis = df.groupby('Skill').agg({
                'Hours_Gap': 'sum',
                'Level_Gap': 'mean',
                'Project_ID': 'count'
            }).rename(columns={'Project_ID': 'Project_Count'})
            
            report_content += """

## ANÁLISIS POR HABILIDAD

"""
            
            report_content += skill_analysis.to_markdown()
        
        # Guardar reporte
        report_path = os.path.join(self.output_dir, 'skill_gap_report.md')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logging.info(f"Reporte de gaps guardado en: {report_path}")
    
    def _generate_visualizations(self, assignments: Dict, skill_gaps: Dict):
        """Genera visualizaciones y gráficos"""
        try:
            # 1. Gráfico de utilización de recursos
            self._create_utilization_chart(assignments)
            
            # 2. Gráfico de distribución de gaps
            self._create_gap_analysis_chart(skill_gaps)
            
            # 3. Gráfico de timeline de proyectos
            self._create_project_timeline_chart(assignments)
            
            logging.info("Visualizaciones generadas exitosamente")
            
        except Exception as e:
            logging.warning(f"No se pudieron generar visualizaciones: {e}")
    
    def _create_utilization_chart(self, assignments: Dict):
        """Crea gráfico de utilización de recursos"""
        employee_hours = {}
        
        for assignment in assignments.values():
            for member in assignment['team_members']:
                emp_id = member['employee_id']
                if emp_id not in employee_hours:
                    employee_hours[emp_id] = {
                        'name': member['name'],
                        'hours': 0
                    }
                employee_hours[emp_id]['hours'] += member['assigned_hours']
        
        # Preparar datos para el gráfico
        names = [data['name'] for data in employee_hours.values()]
        hours = [data['hours'] for data in employee_hours.values()]
        
        plt.figure(figsize=(12, 8))
        bars = plt.barh(names, hours, color='skyblue')
        plt.axvline(x=40, color='red', linestyle='--', label='Límite 40h/semana')
        plt.axvline(x=20, color='green', linestyle='--', label='Mínimo recomendado 20h/semana')
        
        plt.xlabel('Horas Semanales')
        plt.ylabel('Empleados')
        plt.title('Utilización de Recursos por Empleado')
        plt.legend()
        plt.tight_layout()
        
        # Guardar gráfico
        chart_path = os.path.join(self.output_dir, 'resource_utilization.png')
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_gap_analysis_chart(self, skill_gaps: Dict):
        """Crea gráfico de análisis de gaps"""
        if not skill_gaps:
            return
            
        gap_data = []
        for gaps in skill_gaps.values():
            for gap in gaps:
                gap_data.append(gap)
        
        df = pd.DataFrame(gap_data)
        
        # Gráfico de gaps por skill
        skill_gaps_sum = df.groupby('skill')['hours_gap'].sum().sort_values(ascending=False)
        
        plt.figure(figsize=(10, 6))
        skill_gaps_sum.plot(kind='bar', color='coral')
        plt.title('Gaps de Horas por Habilidad')
        plt.xlabel('Habilidad')
        plt.ylabel('Horas de Gap Total')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        chart_path = os.path.join(self.output_dir, 'skill_gaps.png')
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_project_timeline_chart(self, assignments: Dict):
        """Crea gráfico de timeline de proyectos"""
        project_data = []
        
        for project_id, assignment in assignments.items():
            start_date = datetime.strptime(assignment['start_date'], '%Y-%m-%d')
            end_date = datetime.strptime(assignment['estimated_end_date'], '%Y-%m-%d')
            
            project_data.append({
                'Project': assignment['project_name'],
                'Start': start_date,
                'End': end_date,
                'Duration': assignment['duration_weeks'],
                'Team_Size': len(assignment['team_members'])
            })
        
        df = pd.DataFrame(project_data)
        
        plt.figure(figsize=(14, 8))
        
        for i, project in enumerate(project_data):
            plt.barh(project['Project'], project['Duration'], 
                    left=(project['Start'] - df['Start'].min()).days,
                    alpha=0.7,
                    label=project['Project'])
        
        plt.xlabel('Timeline (días)')
        plt.ylabel('Proyectos')
        plt.title('Timeline de Proyectos')
        plt.tight_layout()
        
        chart_path = os.path.join(self.output_dir, 'project_timeline.png')
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def _calculate_resource_utilization(self, assignments: Dict) -> float:
        """Calcula la tasa de utilización de recursos"""
        total_assigned_hours = sum(
            sum(member['assigned_hours'] for member in assignment['team_members'])
            for assignment in assignments.values()
        )
        
        # Asumiendo 40 empleados full-time (40h) y 10 part-time (20h)
        total_available_hours = (40 * 40) + (10 * 20)
        
        return total_assigned_hours / total_available_hours if total_available_hours > 0 else 0
    
    def _count_critical_gaps(self, skill_gaps: Dict) -> int:
        """Cuenta gaps críticos"""
        critical_count = 0
        for gaps in skill_gaps.values():
            for gap in gaps:
                if gap.get('hours_gap', 0) > 100 or gap.get('level_gap', 0) > 0.3:
                    critical_count += 1
        return critical_count
    
    def _get_resource_recommendation(self, utilization: float) -> str:
        """Genera recomendación basada en utilización"""
        if utilization > 0.9:
            return "Alta utilización - considerar contratar recursos adicionales"
        elif utilization < 0.6:
            return "Baja utilización - buscar más proyectos o redistribuir"
        else:
            return "Utilización óptima - mantener nivel actual"
    
    def _get_gap_management_recommendation(self, critical_gaps: int) -> str:
        """Genera recomendación para gestión de gaps"""
        if critical_gaps > 5:
            return "Múltiples gaps críticos - priorizar capacitación y contratación"
        elif critical_gaps > 0:
            return "Algunos gaps críticos - desarrollar planes de mitigación"
        else:
            return "Sin gaps críticos - mantener monitoreo"
    
    def _get_planning_recommendation(self, total_projects: int) -> str:
        """Genera recomendación de planificación"""
        if total_projects > 25:
            return "Alta carga de proyectos - revisar prioridades y recursos"
        elif total_projects > 15:
            return "Carga moderada - planificación adecuada"
        else:
            return "Carga manejable - oportunidad para nuevos proyectos"

# Función de uso simplificado
def generate_all_reports(planner, output_dir: str = "output"):
    """Función conveniente para generar todos los reportes"""
    # Obtener datos del planner
    assignments, skill_gaps = planner.find_optimal_assignments()
    project_tables = planner.generate_project_tables()
    
    # Generar reportes
    reporter = ReportGenerator(output_dir)
    reporter.generate_comprehensive_report(assignments, skill_gaps, project_tables)
    
    return assignments, skill_gaps

if __name__ == "__main__":
    # Ejemplo de uso independiente
    from .intelligent_planner import IntelligentTeamPlanner
    
    planner = IntelligentTeamPlanner()
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    planner.load_data(
        os.path.join(data_dir, 'employees.json'),
        os.path.join(data_dir, 'projects.json')
    )
    
    generate_all_reports(planner)