
# testrail_sync.py
"""
TestRail Synchronization
Sync Karate test cases to TestRail
"""

from typing import Optional, List
from enum import Enum
from .testrail_client import TestRailClient
from .state import TestResult


class StepType(Enum):
    """Tipos de pasos Gherkin"""
    GIVEN = ("Given", "🎯", "#2196F3", "Configuración")
    WHEN = ("When", "⚡", "#FF9800", "Acción")
    THEN = ("Then", "✔️", "#4CAF50", "Validación")
    AND = ("And", "•", "#757575", "Adicional")
    
    def __init__(self, keyword: str, icon: str, color: str, label: str):
        self.keyword = keyword
        self.icon = icon
        self.color = color
        self.label = label


class TestDescriptionBuilder:
    """
    Constructor moderno y elegante para descripciones HTML de TestRail
    Implementa patrón Builder para código limpio y mantenible
    """
    
    # Paleta de colores moderna
    COLORS = {
        'primary_start': '#667eea',
        'primary_end': '#764ba2',
        'secondary': '#FF9800',
        'success': '#4CAF50',
        'error': '#f44336',
        'info': '#2196F3',
        'warning': '#FFC107',
        'background': '#f5f5f5',
        'white': '#ffffff',
    }
    
    FONTS = {
        'primary': "'Segoe UI', 'Tahoma', 'Geneva', 'Verdana', sans-serif",
        'mono': "'Courier New', 'Courier', monospace",
    }
    
    def __init__(self, feature_name: str, scenario_name: str = None):
        self.feature = feature_name
        self.scenario = scenario_name or feature_name
        self.sections = []
        self.status = None
        self.duration = None
        self.error_msg = None
    
    def set_status(self, status: str, duration: float = None, error: str = None) -> 'TestDescriptionBuilder':
        """Establecer estado del test (passed/failed)"""
        self.status = status
        self.duration = duration
        self.error_msg = error
        return self
    
    def add_preconditions(self, steps: List[str]) -> 'TestDescriptionBuilder':
        """Agregar sección de Precondiciones"""
        if steps and len(steps) > 0:
            self.sections.append({
                'type': 'preconditions',
                'icon': '📋',
                'title': 'Precondiciones',
                'color': self.COLORS['info'],
                'items': steps
            })
        return self
    
    def add_steps(self, steps: List[str]) -> 'TestDescriptionBuilder':
        """Agregar sección de Pasos con diferenciación de tipos"""
        if steps and len(steps) > 0:
            self.sections.append({
                'type': 'steps',
                'icon': '🔧',
                'title': 'Pasos',
                'color': self.COLORS['secondary'],
                'items': steps
            })
        return self
    
    def add_expected(self, assertions: List[str]) -> 'TestDescriptionBuilder':
        """Agregar sección de Resultados Esperados"""
        if assertions and len(assertions) > 0:
            self.sections.append({
                'type': 'expected',
                'icon': '🎯',
                'title': 'Resultados Esperados',
                'color': '#9C27B0',
                'items': assertions
            })
        return self
    
    def build(self) -> str:
        """Construir HTML final estilizado"""
        html_parts = []
        
        # Header elegante con gradiente
        html_parts.append(self._build_header())
        
        # Secciones
        for section in self.sections:
            html_parts.append(self._build_section(section))
        
        # Error details si aplica
        if self.status == 'failed' and self.error_msg:
            html_parts.append(self._build_error_section())
        
        # Footer con info de automatización
        html_parts.append(self._build_automation_info())
        
        return '\n'.join(html_parts)
    
    def _build_header(self) -> str:
        """Construir header con gradiente y status"""
        status_badge = self._get_status_badge()
        exec_time = f"⏱️ {self.duration:.2f}s" if self.duration else "⏱️ N/A"
        
        return f"""
<div style="font-family: {self.FONTS['primary']}; background: linear-gradient(135deg, {self.COLORS['primary_start']} 0%, {self.COLORS['primary_end']} 100%); 
            padding: 24px; border-radius: 12px; color: white; margin-bottom: 20px; 
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
        <div style="flex: 1;">
            <h2 style="margin: 0 0 8px 0; font-size: 24px; font-weight: 600;">
                🧪 {self.feature}
            </h2>
            <p style="margin: 0; font-size: 14px; opacity: 0.9; font-weight: 500;">
                {self.scenario}
            </p>
        </div>
        <div style="text-align: right;">
            {status_badge}
            <p style="margin: 8px 0 0 0; font-size: 13px; opacity: 0.9;">
                {exec_time}
            </p>
        </div>
    </div>
</div>
"""
    
    def _build_section(self, section: dict) -> str:
        """Construir sección individual con estilo"""
        color = section['color']
        icon = section['icon']
        title = section['title']
        
        items_html = []
        for item in section['items']:
            if section['type'] == 'steps':
                items_html.append(self._style_step(item))
            else:
                items_html.append(self._style_item(item))
        
        items_content = '\n'.join(items_html)
        
        return f"""
<div style="margin: 16px 0; border-radius: 12px; overflow: hidden; 
            box-shadow: 0 2px 8px rgba(0,0,0,0.08); background: white;">
    <div style="background: linear-gradient(90deg, {color} 0%, {self._lighten_color(color, 30)} 100%);
                color: white; padding: 16px 20px; font-weight: 600; font-size: 15px;">
        <span style="font-size: 18px; margin-right: 8px;">{icon}</span>
        {title}
    </div>
    <div style="padding: 16px 20px; background-color: {self._lighten_color(color, 95)};">
        {items_content}
    </div>
</div>
"""
    
    def _style_item(self, item: str) -> str:
        """Estilizar item genérico"""
        return f"""
        <div style="margin: 8px 0; padding: 10px; padding-left: 16px; 
                    background-color: white; border-left: 3px solid {self.COLORS['info']};
                    border-radius: 4px; font-size: 13px; color: #333;">
            ✓ {item}
        </div>
"""
    
    def _style_step(self, step: str) -> str:
        """Estilizar pasos con diferenciación de tipos"""
        # Detectar tipo de paso
        step_type = None
        for stype in StepType:
            if step.startswith(stype.keyword):
                step_type = stype
                break
        
        if not step_type:
            step_type = StepType.AND
        
        return f"""
        <div style="margin: 8px 0; padding: 12px; padding-left: 16px;
                    background-color: white; border-left: 4px solid {step_type.color};
                    border-radius: 4px; font-size: 13px; color: #333;
                    transition: all 0.2s ease;">
            <span style="color: {step_type.color}; font-weight: bold; margin-right: 8px;">
                {step_type.icon}
            </span>
            <span style="background-color: {self._lighten_color(step_type.color, 85)}; 
                        color: {step_type.color}; padding: 2px 6px; border-radius: 3px;
                        font-weight: 600; font-size: 11px; margin-right: 8px;">
                {step_type.label}
            </span>
            {step}
        </div>
"""
    
    def _get_status_badge(self) -> str:
        """Generar badge de estado"""
        if self.status == 'passed':
            return f"""
            <div style="display: inline-block; background-color: {self.COLORS['success']};
                       color: white; padding: 6px 14px; border-radius: 20px;
                       font-weight: 600; font-size: 12px;">
                ✓ PASSED
            </div>
"""
        elif self.status == 'failed':
            return f"""
            <div style="display: inline-block; background-color: {self.COLORS['error']};
                       color: white; padding: 6px 14px; border-radius: 20px;
                       font-weight: 600; font-size: 12px;">
                ✗ FAILED
            </div>
"""
        else:
            return f"""
            <div style="display: inline-block; background-color: {self.COLORS['warning']};
                       color: white; padding: 6px 14px; border-radius: 20px;
                       font-weight: 600; font-size: 12px;">
                ⏳ UNKNOWN
            </div>
"""
    
    def _build_error_section(self) -> str:
        """Construir sección de error"""
        return f"""
<div style="margin: 16px 0; border-radius: 12px; overflow: hidden;
            box-shadow: 0 2px 8px rgba(244,67,54,0.15);">
    <div style="background: linear-gradient(90deg, {self.COLORS['error']} 0%, #e53935 100%);
                color: white; padding: 16px 20px; font-weight: 600; font-size: 15px;">
        <span style="font-size: 18px; margin-right: 8px;">❌</span>
        Detalles del Error
    </div>
    <div style="padding: 16px 20px; background-color: #ffebee;">
        <div style="background-color: white; padding: 12px; border-radius: 6px;
                    font-family: {self.FONTS['mono']}; font-size: 12px;
                    color: #d32f2f; word-break: break-word; line-height: 1.6;
                    border-left: 4px solid {self.COLORS['error']};">
            {self.error_msg}
        </div>
    </div>
</div>
"""
    
    def _build_automation_info(self) -> str:
        """Construir sección de info de automatización"""
        return f"""
<div style="margin: 16px 0; border-radius: 12px; overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
    <div style="background: linear-gradient(90deg, {self.COLORS['info']} 0%, #1565c0 100%);
                color: white; padding: 16px 20px; font-weight: 600; font-size: 15px;">
        <span style="font-size: 18px; margin-right: 8px;">⚙️</span>
        Información de Automatización
    </div>
    <div style="padding: 16px 20px; background-color: #e3f2fd;">
        <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
            <tr>
                <td style="border: 1px solid #bbdefb; padding: 10px; background-color: white; 
                          font-weight: 600; width: 35%; color: {self.COLORS['info']};">
                    🐉 Framework
                </td>
                <td style="border: 1px solid #bbdefb; padding: 10px; background-color: #f5f5f5;">
                    Karate DSL
                </td>
            </tr>
            <tr>
                <td style="border: 1px solid #bbdefb; padding: 10px; background-color: white;
                          font-weight: 600; color: {self.COLORS['info']};">
                    📝 Tipo
                </td>
                <td style="border: 1px solid #bbdefb; padding: 10px; background-color: #f5f5f5;">
                    BDD/Gherkin (Behavioral Testing)
                </td>
            </tr>
            <tr>
                <td style="border: 1px solid #bbdefb; padding: 10px; background-color: white;
                          font-weight: 600; color: {self.COLORS['info']};">
                    ✅ Automatizado
                </td>
                <td style="border: 1px solid #bbdefb; padding: 10px; background-color: #f5f5f5;">
                    Sí • Sincronizado con TestRail
                </td>
            </tr>
        </table>
    </div>
</div>
"""
    
    @staticmethod
    def _lighten_color(hex_color: str, percent: int) -> str:
        """Aclarar un color HEX en porcentaje"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        rgb = tuple(min(255, int(c + (255 - c) * percent / 100)) for c in rgb)
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


class TestRailSync:
    """Synchronize Karate scenarios to TestRail cases"""
    
    def __init__(self, testrail_client: TestRailClient, project_id: int, suite_id: int):
        self.client = testrail_client
        self.project_id = project_id
        self.suite_id = suite_id
        self.sections_cache = None
    
    def sync_cases_from_karate(self, test_results: List[TestResult]) -> dict[str, int]:
        """
        For each Karate result:
        1. Check if TestRail case exists (by automation_id)
        2. Create or update case
        
        Returns: {automation_id: case_id}
        """
        case_map = {}
        sections = self._get_sections()
        
        if not sections:
            print("⚠️ No sections found. Creating cases in suite root.")
            section_id = None
        else:
            # Use first section
            section_id = sections[0]['id']
            print(f"✓ Using section: {sections[0]['name']} (ID: {section_id})")
        
        for result in test_results:
            # Clean scenario name - if feature and scenario are the same (fallback mode), use just feature
            if result.feature == result.scenario:
                # Fallback mode: feature summary only
                automation_id = result.feature
                title = result.feature
            else:
                # Individual scenario mode
                scenario_clean = result.scenario.split('.')[0] if '.' in result.scenario else result.scenario
                automation_id = f"{result.feature}.{scenario_clean}"
                title = scenario_clean
            
            # Check if case already exists
            existing_case = self._find_case_by_automation_id(automation_id)
            
            case_data = self._build_case_data(result, automation_id, title)
            
            if existing_case:
                # Update existing case
                updated = self.client.update_case(existing_case['id'], case_data)
                if updated:
                    print(f"✓ Updated case #{existing_case['id']}: {automation_id}")
                    case_map[automation_id] = existing_case['id']
            else:
                # Create new case
                if section_id:
                    created = self.client.add_case(section_id, case_data)
                    if created:
                        print(f"✓ Created case #{created['id']}: {automation_id}")
                        case_map[automation_id] = created['id']
                else:
                    print(f"⚠️ Cannot create case without section_id: {automation_id}")
        
        return case_map
    
    def _get_sections(self) -> List[dict]:
        """Get cached sections or fetch from API"""
        if self.sections_cache is None:
            self.sections_cache = self.client.get_sections(self.project_id, self.suite_id)
        return self.sections_cache
    
    def _find_case_by_automation_id(self, automation_id: str) -> Optional[dict]:
        """Query TestRail for case with matching automation_id"""
        try:
            cases = self.client.get_cases(self.project_id, self.suite_id)
            
            for case in cases:
                # Check custom_automation_id field
                if case.get('custom_automation_id') == automation_id:
                    return case
            
            return None
        except Exception as e:
            print(f"⚠️ Error searching for case {automation_id}: {e}")
            return None
    
    def _build_case_data(self, result: TestResult, automation_id: str, title: str) -> dict:
        """Build TestRail case payload from TestResult with formatted description"""
        priority = self._infer_priority(result)
        description = self._build_formatted_description(result)
        preconditions = self._build_preconditions(result)
        steps = self._build_steps(result)
        expected_result = self._build_expected_result(result)
        
        return {
            'title': title,
            'custom_automation_id': automation_id,
            'description': description,
            'custom_preconds': preconditions,
            'custom_steps': steps,
            'custom_expected': expected_result,
            'priority_id': priority,
            'custom_feature': result.feature,
            'custom_is_automated': 1,  # Marcar como automatizado
            'custom_status_actual': result.status,  # Status real (passed/failed)
            'estimate': None,  # Se calcula automáticamente
        }
    
    def _build_formatted_description(self, result: TestResult) -> str:
        """
        Construir descripción HTML moderna y elegante usando TestDescriptionBuilder
        """
        builder = (TestDescriptionBuilder(result.feature, result.scenario)
            .set_status(result.status, result.duration, result.error_message)
            .add_preconditions(result.background_steps)
            .add_steps(result.gherkin_steps)
            .add_expected(result.expected_assertions))
        
        return builder.build()
    
    def _build_preconditions(self, result: TestResult) -> str:
        """Build preconditions from Background steps"""
        preconditions = []
        
        # Usar Background steps si existen
        if result.background_steps and len(result.background_steps) > 0:
            preconditions = result.background_steps
        else:
            # Fallback genérico
            preconditions = [
                "Given the API is accessible",
                "And the test environment is configured"
            ]
        
        return "\n".join([f"{i+1}. {p}" for i, p in enumerate(preconditions)])
    
    def _build_steps(self, result: TestResult) -> str:
        """Build test steps from Gherkin definition"""
        if result.gherkin_steps and len(result.gherkin_steps) > 0:
            # Usar pasos reales del .feature
            return "\n".join([f"{i}. {step}" for i, step in enumerate(result.gherkin_steps, 1)])
        
        # Fallback a pasos genéricos
        steps = [
            "1. Prepare test data",
            "2. Send API request",
            "3. Verify HTTP response status",
            "4. Validate response body",
            "5. Assert all conditions pass"
        ]
        return "\n".join(steps)
    
    def _build_expected_result(self, result: TestResult) -> str:
        """Build expected result from assertions and test status"""
        lines = []
        
        # Status del test
        if result.status == 'passed':
            lines.append("✅ Test execution successful")
        else:
            lines.append("❌ Test failed")
        
        # Aserciones esperadas (match statements)
        if result.expected_assertions and len(result.expected_assertions) > 0:
            lines.append("\nExpected Assertions:")
            for assertion in result.expected_assertions:
                lines.append(f"  • {assertion}")
        
        # Error si existe
        if result.error_message:
            lines.append(f"\nError Details: {result.error_message}")
        
        return "\n".join(lines)
    
    def _get_status_badge(self, status: str) -> str:
        """Generate HTML badge for status"""
        if status == 'passed':
            return '<span style="background-color: #4caf50; color: white; padding: 2px 8px; border-radius: 3px;">✅ PASSED</span>'
        elif status == 'failed':
            return '<span style="background-color: #f44336; color: white; padding: 2px 8px; border-radius: 3px;">❌ FAILED</span>'
        else:
            return '<span style="background-color: #ff9800; color: white; padding: 2px 8px; border-radius: 3px;">⚠️ UNKNOWN</span>'
    
    def _infer_priority(self, result: TestResult) -> int:
        """
        Infer priority from scenario name
        1=Don't Test, 2=Low, 3=Medium, 4=High, 5=Critical
        """
        scenario_lower = result.scenario.lower()
        
        if any(x in scenario_lower for x in ['critical', 'smoke', 'main']):
            return 5  # Critical
        elif any(x in scenario_lower for x in ['error', 'negative']):
            return 2  # Low
        else:
            return 3  # Medium (default)
