#!/usr/bin/env python3
"""
Script de demostración del nuevo sistema de múltiples proyectos
Ejecuta: python demo_multi_project.py
"""

from agent.project_config import ProjectConfigManager

def main():
    print("\n" + "="*70)
    print("DEMO: Sistema de Múltiples Proyectos TestRail")
    print("="*70)
    
    # Cargar configuración
    print("\n📁 Cargando testrail-projects.yaml...")
    try:
        manager = ProjectConfigManager()
        print("✅ Archivo cargado correctamente\n")
    except Exception as e:
        print(f"❌ Error al cargar: {e}")
        return
    
    # Mostrar resumen
    manager.print_summary()
    
    # Obtener proyecto. Si hay uno solo, se usa automáticamente
    print("\n" + "="*70)
    print("DEMO: Cómo funciona en el código (main.py)")
    print("="*70)
    
    projects = manager.list_projects()
    
    if not projects:
        print("\n⚠️  No hay proyectos configurados con IDs.")
        print("\nPasos para configurar:")
        print("  1. Editar config/testrail-projects.yaml")
        print("  2. Agregar: project_id y section_id")
        print("  3. O ejecutar: python -m agent.fetch_testrail_ids")
        return
    
    print(f"\n📌 Si hay {len(projects)} proyecto(s):")
    
    if len(projects) == 1:
        project = projects[0]
        print(f"\n   Ejecución automática:")
        print(f"   $ python -m agent.main")
        print(f"\n   ✓ Automáticamente usará:")
        print(f"     • Project ID: {project.project_id}")
        print(f"     • Section ID: {project.section_id}")
        print(f"     • QA: {project.qa_name} ({project.qa_email})")
    else:
        print(f"\n   Debes especificar qué proyecto:")
        for idx, project in enumerate(projects, 1):
            print(f"\n   {idx}. $ python -m agent.main --project {project.project_key}")
            print(f"      ✓ Usará: {project.qa_name} en {project.project_name}/{project.section_name}")
    
    # Mostrar flujo completo
    print("\n" + "="*70)
    print("FLUJO COMPLETO: Día a día")
    print("="*70)
    
    if len(projects) == 1:
        project = projects[0]
        print(f"""
DÍA 1 (Setup - Una sola vez):
  ✓ Editar testrail-projects.yaml
  ✓ Ejecutar: fetch_ids.bat (obtiene automáticamente los IDs)

DÍAS 2+ (Ejecución normal):
  $ mvn test                    # Ejecutar tests Karate
  $ python -m agent.main        # Sincronizar a TestRail automáticamente
  
  El sistema automáticamente:
  ✅ Lee el proyecto: {project.project_name}
  ✅ Usa la suite: {project.suite_name}
  ✅ Asigna a: {project.qa_email}
  ✅ Guarda histórico en MongoDB con QA: {project.qa_name}
  ✅ Notifica en Slack mencionando: {project.qa_name}
""")
    else:
        print(f"""
DÍA 1 (Setup - Una sola vez POR proyecto):
  ✓ Editar testrail-projects.yaml (cada QA agrega su proyecto)
  ✓ Ejecutar: fetch_ids.bat (obtiene automáticamente TODOS los IDs)

DÍAS 2+ (Ejecución normal - cada QA elige su proyecto):
  $ mvn test
  $ python -m agent.main --project <clave-del-proyecto>
  
Ejemplo:
""")
        for idx, project in enumerate(projects, 1):
            print(f"  Opción {idx}: python -m agent.main --project {project.project_key}")
            print(f"             → Usa {project.qa_name} en {project.project_name}")
    
    print("\n" + "="*70)
    print("✅ El sistema está listo para usar")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
