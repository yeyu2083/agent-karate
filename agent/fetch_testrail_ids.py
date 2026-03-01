#!/usr/bin/env python3
"""
Fetch TestRail IDs automatically
Lee testrail-projects.yaml y obtiene automáticamente Project IDs y Suite IDs de TestRail
Uso: python -m agent.fetch_testrail_ids
"""

import os
import sys
import yaml
import requests
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TestRailIDFetcher:
    """Obtiene automáticamente IDs de TestRail"""
    
    def __init__(self):
        self.url = os.getenv('TESTRAIL_URL', '').strip()
        self.email = os.getenv('TESTRAIL_EMAIL', '').strip()
        self.api_key = os.getenv('TESTRAIL_API_KEY', '').strip()
        self.auth = (self.email, self.api_key)
        self.base_url = f"{self.url.rstrip('/')}/index.php?/api/v2"
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
    def validate_connection(self) -> bool:
        """Valida la conexión a TestRail"""
        try:
            response = requests.get(
                f"{self.base_url}/get_projects",
                auth=self.auth,
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                print("✅ Conexión a TestRail exitosa")
                return True
            else:
                print(f"❌ Error de conexión: Status {response.status_code}")
                print(f"   Respuesta: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error conectando a TestRail: {e}")
            return False
    
    def get_project_id(self, project_name: str) -> Optional[int]:
        """Obtiene Project ID por nombre"""
        try:
            response = requests.get(
                f"{self.base_url}/get_projects",
                auth=self.auth,
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            projects = data.get('projects', []) if isinstance(data, dict) else data
            
            for project in projects:
                if project.get('name', '').lower() == project_name.lower():
                    return project.get('id')
            
            print(f"❌ Proyecto '{project_name}' no encontrado")
            print(f"   Proyectos disponibles:")
            for p in projects:
                print(f"     - {p.get('name')} (ID: {p.get('id')})")
            return None
            
        except Exception as e:
            print(f"❌ Error obteniendo proyectos: {e}")
            return None
    
    def get_section_id(self, project_id: int, section_name: str) -> Optional[int]:
        """Obtiene Section ID por nombre dentro de un proyecto (Single Suite Mode)"""
        try:
            response = requests.get(
                f"{self.base_url}/get_sections/{project_id}",
                auth=self.auth,
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            sections = data.get('sections', []) if isinstance(data, dict) else data
            
            for section in sections:
                if section.get('name', '').lower() == section_name.lower():
                    return section.get('id')
            
            print(f"❌ Sección '{section_name}' no encontrada en proyecto {project_id}")
            print(f"   Secciones disponibles:")
            for s in sections:
                print(f"     - {s.get('name')} (ID: {s.get('id')})")
            return None
            
        except Exception as e:
            print(f"❌ Error obteniendo secciones: {e}")
            return None
    
    def fetch_all_ids(self, config_path: str) -> bool:
        """Lee testrail-projects.yaml y obtiene todos los IDs"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if not config or 'projects' not in config:
                print("❌ archivo testrail-projects.yaml no encontrado o mal formado")
                return False
            
            updated = False
            
            for project_key, project_config in config['projects'].items():
                print(f"\n📌 Procesando: {project_key}")
                print(f"   Buscando proyecto: {project_config.get('project_name')}")
                print(f"   Buscando sección: {project_config.get('section_name')}")
                
                # Obtener Project ID
                project_id = self.get_project_id(project_config['project_name'])
                if project_id:
                    project_config['project_id'] = project_id
                    print(f"   ✅ Project ID: {project_id}")
                    updated = True
                else:
                    print(f"   ✗ No se pudo obtener Project ID")
                    continue
                
                # Obtener Section ID
                section_id = self.get_section_id(project_id, project_config.get('section_name', 'Untitled'))
                if section_id:
                    project_config['section_id'] = section_id
                    print(f"   ✅ Section ID: {section_id}")
                    updated = True
                else:
                    print(f"   ✗ No se pudo obtener Section ID")
            
            # Guardar cambios
            if updated:
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
                print(f"\n✅ Archivo {config_path} actualizado correctamente")
                return True
            else:
                print(f"\n⚠️  No se pudo obtener los IDs")
                return False
                
        except Exception as e:
            print(f"❌ Error procesando archivo: {e}")
            return False


def main():
    """Main entry point"""
    print("=" * 60)
    print("TestRail ID Auto-Fetcher")
    print("=" * 60)
    
    # Validar variables de entorno
    if not os.getenv('TESTRAIL_URL'):
        print("❌ Error: TESTRAIL_URL no está configurado")
        return False
    if not os.getenv('TESTRAIL_EMAIL'):
        print("❌ Error: TESTRAIL_EMAIL no está configurado")
        return False
    if not os.getenv('TESTRAIL_API_KEY'):
        print("❌ Error: TESTRAIL_API_KEY no está configurado")
        return False
    
    fetcher = TestRailIDFetcher()
    
    # Validar conexión
    if not fetcher.validate_connection():
        return False
    
    # Encontrar el archivo de configuración
    # Ubicación principal: config/testrail-projects.yaml
    possible_paths = [
        Path(__file__).parent.parent / 'config' / 'testrail-projects.yaml',  # config/
        Path(__file__).parent.parent / 'testrail-projects.yaml',  # raíz (fallback)
        Path.cwd() / 'config' / 'testrail-projects.yaml',
        Path.cwd() / 'testrail-projects.yaml',
    ]
    
    config_path = None
    for path in possible_paths:
        if path.exists():
            config_path = str(path)
            path_display = str(path).replace("\\", "/")
            print(f"📁 Usando config: {path_display}")
            break
    
    if not config_path:
        print(f"❌ No se encontró testrail-projects.yaml")
        print(f"   Ubicación esperada: config/testrail-projects.yaml")
        print(f"   (o fallback en raíz del proyecto)")
        print(f"   Buscamos en:")
        for path in possible_paths:
            print(f"     - {path}")
        return False
    
    # Obtener los IDs
    success = fetcher.fetch_all_ids(config_path)
    print("\n" + "=" * 60)
    
    if success:
        print("✅ Proceso completado exitosamente")
        print(f"\n📋 Configuración guardada en:")
        config_display = config_path.replace("\\", "/")
        print(f"   {config_display}")
        print("\n📋 Resumen de proyectos configurados:")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        for project_key, project_config in config['projects'].items():
            if project_config.get('project_id'):
                print(f"\n{project_key}:")
                print(f"  • Project ID: {project_config['project_id']}")
                print(f"  • Section ID: {project_config['section_id']}")
                print(f"  • QA: {project_config['qa_name']} ({project_config['qa_email']})")
    
    return success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
