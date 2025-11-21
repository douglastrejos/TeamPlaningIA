import os
import sys
from src.intelligent_planner import IntelligentTeamPlanner
from src.report_generator import generate_all_reports

def main():
    print("🚀 Iniciando Planificador de Equipos con IA")
    print("=" * 50)
    
    try:
        # 1. Inicializar el planificador
        planner = IntelligentTeamPlanner()
        
        # 2. Cargar datos
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        employees_file = os.path.join(data_dir, 'employees.json')
        projects_file = os.path.join(data_dir, 'projects.json')
        
        print("📂 Cargando datos...")
        planner.load_data(employees_file, projects_file)
        print("✅ Datos cargados exitosamente")
        
        # 3. Generar asignaciones y reportes
        print("🧠 Generando asignaciones óptimas...")
        assignments, skill_gaps = generate_all_reports(planner, "output")
        
        # 4. Mostrar resumen
        print("\n" + "=" * 50)
        print("📊 RESUMEN FINAL")
        print("=" * 50)
        print(f"✅ Proyectos asignados: {len(assignments)}")
        print(f"⚠️  Proyectos con gaps: {len(skill_gaps)}")
        print(f"📁 Reportes guardados en: /output/")
        
        # 5. Mostrar alertas críticas
        critical_gaps = sum(len([g for g in gaps if g.get('hours_gap', 0) > 100]) 
                          for gaps in skill_gaps.values())
        if critical_gaps > 0:
            print(f"🚨 Gaps críticos identificados: {critical_gaps}")
        
        print("\n🎯 ¡Proceso completado! Revisa los archivos en la carpeta /output/")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()