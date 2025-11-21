import numpy as np
import random
from typing import List, Dict
import logging

class ResourceOptimizer:
    def __init__(self, population_size=100, generations=50):
        self.population_size = population_size
        self.generations = generations
        
    def optimize_team_assignment(self, candidates: List[Dict], 
                               requirements: Dict, max_team_size: int) -> List[Dict]:
        """Optimiza la asignación de equipo usando algoritmo genético simplificado"""
        
        if not candidates:
            return None
            
        # Si hay pocos candidatos, usar asignación directa
        if len(candidates) <= max_team_size:
            return self._direct_assignment(candidates, requirements)
            
        # Algoritmo genético simplificado
        best_team = self._genetic_algorithm(candidates, requirements, max_team_size)
        return best_team
    
    def _direct_assignment(self, candidates: List[Dict], requirements: Dict) -> List[Dict]:
        """Asignación directa cuando hay pocos candidatos"""
        team = []
        total_available = sum(emp['available_hours'] for emp in candidates)
        
        for emp in candidates:
            # Asignar horas proporcionalmente a la disponibilidad
            assigned_hours = (emp['available_hours'] / total_available) * 160  # 4 semanas
            weekly_hours = round(assigned_hours / 4, 2)
            
            team.append({
                'employee_id': emp['employee_id'],
                'name': emp['name'],
                'assigned_hours': weekly_hours,
                'skills': emp.get('skills', {}),
                'primary_skills': emp.get('matched_skills', [])
            })
        
        return team
    
    def _genetic_algorithm(self, candidates: List[Dict], requirements: Dict, max_team_size: int) -> List[Dict]:
        """Algoritmo genético simplificado para selección de equipo"""
        best_fitness = -float('inf')
        best_team_indices = []
        
        for _ in range(self.population_size):
            # Generar solución aleatoria
            team_size = random.randint(1, max_team_size)
            team_indices = random.sample(range(len(candidates)), team_size)
            
            # Evaluar fitness
            fitness = self._evaluate_fitness(team_indices, candidates, requirements)
            
            if fitness > best_fitness:
                best_fitness = fitness
                best_team_indices = team_indices
        
        return self._decode_solution(best_team_indices, candidates, requirements)
    
    def _evaluate_fitness(self, team_indices: List[int], candidates: List[Dict], requirements: Dict) -> float:
        """Evalúa la calidad de un equipo"""
        if not team_indices:
            return -1000
        
        skill_coverage = 0
        total_hours = 0
        skill_match_quality = 0
        
        for skill, req in requirements.items():
            skill_hours = 0
            max_skill_level = 0
            
            for idx in team_indices:
                candidate = candidates[idx]
                if skill in candidate.get('matched_skills', []):
                    skill_hours += min(candidate['available_hours'], 
                                     req['hours_needed'] / 10)  # Estimación semanal
                    skill_level = candidate.get('skills', {}).get(skill, 0)
                    max_skill_level = max(max_skill_level, skill_level)
            
            coverage_ratio = min(1.0, skill_hours / (req['hours_needed'] / 10)) if req['hours_needed'] > 0 else 1.0
            skill_coverage += coverage_ratio
            
            if max_skill_level >= req['min_level']:
                skill_match_quality += max_skill_level
        
        # Normalizar scores
        skill_coverage /= len(requirements)
        skill_match_quality /= len(requirements)
        
        # Penalizar sobre-asignación
        overload_penalty = 0
        for idx in team_indices:
            if candidates[idx]['available_hours'] > 40:
                overload_penalty += (candidates[idx]['available_hours'] - 40) * 10
        
        return skill_coverage * 100 - overload_penalty + skill_match_quality * 50
    
    def _decode_solution(self, team_indices: List[int], candidates: List[Dict], requirements: Dict) -> List[Dict]:
        """Decodifica la solución del algoritmo genético"""
        if not team_indices:
            return None
        
        team = []
        total_available = sum(candidates[i]['available_hours'] for i in team_indices)
        
        for idx in team_indices:
            candidate = candidates[idx]
            # Distribuir horas proporcionalmente a la disponibilidad y necesidades
            base_hours = (candidate['available_hours'] / total_available) * 160  # 4 semanas
            assigned_hours = min(base_hours, candidate['available_hours'] * 4)  # No exceder disponibilidad
            
            weekly_hours = round(assigned_hours / 4, 2)
            
            team.append({
                'employee_id': candidate['employee_id'],
                'name': candidate['name'],
                'assigned_hours': weekly_hours,
                'skills': candidate.get('skills', {}),
                'primary_skills': candidate.get('matched_skills', [])
            })
        
        return team