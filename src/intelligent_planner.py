import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import logging
import os

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class IntelligentTeamPlanner:
    def __init__(self):
        self.employees = []
        self.projects = []
        self.skills_matrix = {}
        self.assignments = {}
        
    def load_data(self, employees_file: str, projects_file: str):
        """Carga y procesa los datos de empleados y proyectos"""
        try:
            # Verificar que los archivos existan
            if not os.path.exists(employees_file):
                raise FileNotFoundError(f"Archivo no encontrado: {employees_file}")
            if not os.path.exists(projects_file):
                raise FileNotFoundError(f"Archivo no encontrado: {projects_file}")
                
            with open(employees_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.employees = data.get('employees', [])
                
            with open(projects_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.projects = data.get('projects', [])
                
            self._build_skills_matrix()
            logging.info(f"Datos cargados: {len(self.employees)} empleados, {len(self.projects)} proyectos")
            
        except Exception as e:
            logging.error(f"Error cargando datos: {e}")
            raise
            
    def _build_skills_matrix(self):
        """Construye matriz de habilidades para optimización"""
        self.skills_matrix = {}
        for emp in self.employees:
            self.skills_matrix[emp['id']] = emp.get('skills', {})
    
    def calculate_project_duration(self, project: Dict, total_weekly_hours: float) -> int:
        """Calcula la duración del proyecto en semanas"""
        if total_weekly_hours <= 0:
            return 0
            
        management_hours = project['estimated_hours'] * 0.10
        documentation_hours = project['estimated_hours'] * 0.10
        testing_hours = project['estimated_hours'] * 0.10
        
        productive_hours = project['estimated_hours'] * 0.70
        total_effective_hours = productive_hours + management_hours + documentation_hours + testing_hours
        
        return max(1, int(np.ceil(total_effective_hours / total_weekly_hours)))
    
    def find_optimal_assignments(self) -> Tuple[Dict, Dict]:
        """Ejecuta el algoritmo de optimización para asignaciones"""
        from .optimization_engine import ResourceOptimizer
        from .alert_system import AlertManager
        
        optimizer = ResourceOptimizer()
        alert_manager = AlertManager()
        
        assignments = {}
        skill_gaps = {}
        
        for project in self.projects:
            project_id = project['id']
            logging.info(f"Procesando proyecto: {project['name']}")
            
            # Encontrar candidatos para cada skill requerido
            candidate_assignments = self._find_candidates_for_project(project)
            
            if not candidate_assignments:
                logging.warning(f"No se encontraron candidatos para el proyecto {project_id}")
                continue
                
            # Optimizar asignaciones
            optimal_team = optimizer.optimize_team_assignment(
                candidate_assignments, 
                project['skill_requirements'],
                project['constraints']['max_team_size']
            )
            
            if optimal_team:
                assignments[project_id] = self._format_project_assignment(
                    project, optimal_team
                )
                
                # Verificar gaps de habilidades
                project_gaps = self._identify_skill_gaps(project, optimal_team)
                if project_gaps:
                    skill_gaps[project_id] = project_gaps
                    alert_manager.generate_alert(project_id, project_gaps)
            else:
                logging.warning(f"No se pudo formar equipo para el proyecto {project_id}")
            
        self.assignments = assignments
        
        # Mostrar resumen de alertas
        alert_summary = alert_manager.get_alerts_summary()
        logging.info(f"Resumen de alertas: {alert_summary}")
        
        return assignments, skill_gaps
    
    def _find_candidates_for_project(self, project: Dict) -> List[Dict]:
        """Encuentra empleados candidatos para el proyecto basado en habilidades"""
        candidates = []
        
        for emp in self.employees:
            if emp['available_hours'] <= 0:
                continue
                
            skill_match_score = 0
            matched_skills = []
            
            for skill, requirement in project['skill_requirements'].items():
                emp_skill_level = emp['skills'].get(skill, 0)
                if emp_skill_level >= requirement['min_level']:
                    skill_match_score += emp_skill_level
                    matched_skills.append(skill)
            
            if matched_skills:
                candidates.append({
                    'employee_id': emp['id'],
                    'name': emp['name'],
                    'available_hours': emp['available_hours'],
                    'skill_match_score': skill_match_score / len(matched_skills),
                    'matched_skills': matched_skills,
                    'skills': emp['skills'],
                    'current_commitment': emp.get('current_commitment', 0)
                })
        
        return sorted(candidates, key=lambda x: x['skill_match_score'], reverse=True)
    
    def _format_project_assignment(self, project: Dict, team: List) -> Dict:
        """Formatea la asignación del proyecto para output"""
        total_weekly_hours = sum(member['assigned_hours'] for member in team)
        duration_weeks = self.calculate_project_duration(project, total_weekly_hours)
        
        start_date = datetime.strptime(project['start_date'], '%Y-%m-%d')
        end_date = start_date + timedelta(weeks=duration_weeks)
        
        return {
            'project_name': project['name'],
            'start_date': project['start_date'],
            'estimated_end_date': end_date.strftime('%Y-%m-%d'),
            'duration_weeks': duration_weeks,
            'team_members': team,
            'total_weekly_hours': total_weekly_hours,
            'skill_coverage': self._calculate_skill_coverage(project, team)
        }
    
    def _identify_skill_gaps(self, project: Dict, team: List) -> List[Dict]:
        """Identifica gaps de habilidades en el equipo asignado"""
        gaps = []
        
        for skill, requirement in project['skill_requirements'].items():
            total_skill_hours = 0
            max_skill_level = 0
            
            for member in team:
                member_skills = member.get('skills', {})
                if skill in member_skills:
                    total_skill_hours += member['assigned_hours']
                    max_skill_level = max(max_skill_level, member_skills[skill])
            
            hours_gap = requirement['hours_needed'] - (total_skill_hours * 4)  # Convertir a horas totales
            level_gap = requirement['min_level'] - max_skill_level
            
            if hours_gap > 0 or level_gap > 0:
                gaps.append({
                    'skill': skill,
                    'hours_needed': requirement['hours_needed'],
                    'hours_covered': total_skill_hours * 4,
                    'level_required': requirement['min_level'],
                    'level_covered': max_skill_level,
                    'hours_gap': hours_gap,
                    'level_gap': level_gap
                })
        
        return gaps
    
    def _calculate_skill_coverage(self, project: Dict, team: List) -> float:
        """Calcula el porcentaje de cobertura de habilidades"""
        total_coverage = 0
        
        for skill, requirement in project['skill_requirements'].items():
            max_skill_level = 0
            for member in team:
                member_skills = member.get('skills', {})
                max_skill_level = max(max_skill_level, member_skills.get(skill, 0))
            
            if max_skill_level >= requirement['min_level']:
                total_coverage += 1
        
        return total_coverage / len(project['skill_requirements'])
    
    def generate_project_tables(self) -> Dict:
        """Genera tablas detalladas para cada proyecto"""
        project_tables = {}
        
        for project_id, assignment in self.assignments.items():
            table_data = []
            
            for member in assignment['team_members']:
                skill_levels = list(member.get('skills', {}).values())
                avg_skill_level = np.mean(skill_levels) if skill_levels else 0
                
                table_data.append({
                    'Employee_ID': member['employee_id'],
                    'Name': member['name'],
                    'Role': ', '.join(member.get('primary_skills', [])),
                    'Weekly_Hours': member['assigned_hours'],
                    'Skill_Level_Avg': f"{avg_skill_level:.2f}"
                })
            
            project_tables[project_id] = {
                'project_info': {
                    'name': assignment['project_name'],
                    'start_date': assignment['start_date'],
                    'duration_weeks': assignment['duration_weeks']
                },
                'team_table': pd.DataFrame(table_data),
                'summary': {
                    'total_team_size': len(assignment['team_members']),
                    'total_weekly_hours': assignment['total_weekly_hours'],
                    'skill_coverage_score': assignment['skill_coverage']
                }
            }
        
        return project_tables
    
    def export_assignments(self, output_file: str):
        """Exporta las asignaciones a archivo CSV"""
        try:
            all_assignments = []
            
            for project_id, assignment in self.assignments.items():
                for member in assignment['team_members']:
                    all_assignments.append({
                        'project_id': project_id,
                        'project_name': assignment['project_name'],
                        'employee_id': member['employee_id'],
                        'employee_name': member['name'],
                        'assigned_hours_weekly': member['assigned_hours'],
                        'start_date': assignment['start_date'],
                        'end_date': assignment['estimated_end_date']
                    })
            
            df = pd.DataFrame(all_assignments)
            
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            df.to_csv(output_file, index=False, encoding='utf-8')
            logging.info(f"Asignaciones exportadas a {output_file}")
            
        except Exception as e:
            logging.error(f"Error exportando asignaciones: {e}")

# Ejemplo de uso
if __name__ == "__main__":
    try:
        planner = IntelligentTeamPlanner()
        
        # Cargar datos
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        employees_file = os.path.join(data_dir, 'employees.json')
        projects_file = os.path.join(data_dir, 'projects.json')
        
        planner.load_data(employees_file, projects_file)
        
        # Generar asignaciones
        assignments, gaps = planner.find_optimal_assignments()
        
        # Generar tablas
        project_tables = planner.generate_project_tables()
        
        # Exportar resultados
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
        os.makedirs(output_dir, exist_ok=True)
        planner.export_assignments(os.path.join(output_dir, 'project_assignments.csv'))
        
        print(f"Proceso completado. {len(assignments)} proyectos asignados.")
        
    except Exception as e:
        logging.error(f"Error en ejecución: {e}")