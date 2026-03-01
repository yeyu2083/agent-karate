"""
Project Configuration Manager
Lee testrail-projects.yaml y proporciona configuración de TestRail
para cada proyecto con info del QA asignado
"""

import os
import yaml
from typing import Optional, Dict, List, Any
from pathlib import Path
from dataclasses import dataclass


@dataclass
class ProjectConfig:
    """Configuración de un proyecto TestRail específico"""
    project_key: str            # Clave única (ej: "agent-testing-comments")
    project_name: str           # Nombre en TestRail (ej: "agent-testing")
    section_name: str           # Nombre de la sección en TestRail
    project_id: int             # ID del proyecto (obtenido automáticamente)
    section_id: int             # ID de la sección (obtenido automáticamente)
    qa_email: str               # Email del QA asignado
    qa_name: str                # Nombre del QA asignado
    
    def __repr__(self) -> str:
        return f"ProjectConfig({self.project_key}: {self.qa_name} <{self.qa_email}>)"


class ProjectConfigManager:
    """Maneja la configuración de múltiples proyectos desde YAML"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializa el manager
        
        Args:
            config_path: Ruta al archivo testrail-projects.yaml
                        Si no se proporciona, busca en varias ubicaciones
        """
        self.config_path = config_path or self._find_config_file()
        self.config_data = None
        self.projects: Dict[str, ProjectConfig] = {}
        
        if self.config_path and os.path.exists(self.config_path):
            self._load_config()
        else:
            raise FileNotFoundError(
                f"No se encontró testrail-projects.yaml. "
                f"Buscaremos en: {self._get_search_paths()}"
            )
    
    @staticmethod
    def _get_search_paths() -> List[str]:
        """Rutas donde buscamos el archivo YAML dentro de config/"""
        project_root = Path(__file__).parent.parent
        return [
            str(project_root / 'config' / 'testrail-projects.yaml'),
            str(project_root / 'testrail-projects.yaml'),  # fallback a raíz (legacy)
            str(Path.cwd() / 'config' / 'testrail-projects.yaml'),
            str(Path.cwd() / 'testrail-projects.yaml'),
            './config/testrail-projects.yaml',
            './testrail-projects.yaml',
        ]
    
    @staticmethod
    def _find_config_file() -> Optional[str]:
        """Busca el archivo testrail-projects.yaml"""
        for path in ProjectConfigManager._get_search_paths():
            if os.path.exists(path):
                return path
        return None
    
    def _load_config(self):
        """Carga el archivo YAML y crea objetos ProjectConfig"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config_data = yaml.safe_load(f)
            
            if not self.config_data or 'projects' not in self.config_data:
                raise ValueError("El archivo YAML no tiene la sección 'projects'")
            
            for project_key, project_data in self.config_data['projects'].items():
                # Validar que todos los campos obligatorios estén presentes
                required_fields = [
                    'project_name', 'section_name', 'qa_email', 'qa_name',
                    'project_id', 'section_id'
                ]
                
                missing_fields = [f for f in required_fields if f not in project_data]
                if missing_fields:
                    raise ValueError(
                        f"Proyecto '{project_key}' faltan campos: {missing_fields}"
                    )
                
                # Verificar que los IDs están configurados
                if not project_data.get('project_id') or not project_data.get('section_id'):
                    print(
                        f"⚠️  Proyecto '{project_key}': IDs no configurados. "
                        f"Ejecuta: python -m agent.fetch_testrail_ids"
                    )
                    continue
                
                # Crear objeto ProjectConfig
                config = ProjectConfig(
                    project_key=project_key,
                    project_name=project_data['project_name'],
                    section_name=project_data['section_name'],
                    project_id=int(project_data['project_id']),
                    section_id=int(project_data['section_id']),
                    qa_email=project_data['qa_email'],
                    qa_name=project_data['qa_name'],
                )
                
                self.projects[project_key] = config
            
            config_location = self.config_path.replace("\\", "/")
            print(f"✓ Cargados {len(self.projects)} proyectos desde {config_location}")
            
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML: {e}")
        except Exception as e:
            raise Exception(f"Error loading config: {e}")
    
    def get_project(self, project_key: Optional[str] = None) -> ProjectConfig:
        """
        Obtiene la configuración de un proyecto
        
        Args:
            project_key: Clave del proyecto. Si no se proporciona:
                        - Si hay un solo proyecto, usa ese
                        - Si hay múltiples, lanza error pidiendo especificar
        
        Returns:
            ProjectConfig del proyecto solicitado
        
        Raises:
            ValueError si no encuentra el proyecto o no especifica cuál usar
        """
        if not self.projects:
            raise ValueError(
                "No hay proyectos configurados. "
                "Verifica que testrail-projects.yaml tenga proyectos con IDs configurados."
            )
        
        # Si no se especifica, usar el único o lanzar error
        if not project_key:
            if len(self.projects) == 1:
                project_key = list(self.projects.keys())[0]
                print(f"✓ Usando proyecto único: {project_key}")
            else:
                projects_list = "\n".join(f"  • {k}" for k in self.projects.keys())
                raise ValueError(
                    f"Múltiples proyectos configurados. Especifica cuál usar:\n"
                    f"{projects_list}\n\n"
                    f"Uso: python -m agent.main --project <clave>"
                )
        
        if project_key not in self.projects:
            projects_list = "\n".join(f"  • {k}" for k in self.projects.keys())
            raise ValueError(
                f"Proyecto '{project_key}' no encontrado.\n"
                f"Proyectos disponibles:\n{projects_list}"
            )
        
        return self.projects[project_key]
    
    def list_projects(self) -> List[ProjectConfig]:
        """Retorna lista de todos los proyectos configurados"""
        return list(self.projects.values())
    
    def print_summary(self):
        """Imprime un resumen de los proyectos configurados"""
        print("\n" + "="*60)
        print("📋 PROYECTOS TESTRAIL CONFIGURADOS")
        print("="*60)
        
        if not self.projects:
            print("⚠️  No hay proyectos configurados")
            return
        
        for idx, (key, config) in enumerate(self.projects.items(), 1):
            print(f"\n{idx}. {key}")
            print(f"   Proyecto TestRail: {config.project_name} (ID: {config.project_id})")
            print(f"   Sección: {config.section_name} (ID: {config.section_id})")
            print(f"   QA Asignado: {config.qa_name}")
            print(f"   Email: {config.qa_email}")
