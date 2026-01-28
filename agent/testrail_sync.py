
# testrail_sync.py
"""
TestRail Synchronization
Sync Karate test cases to TestRail
"""

from typing import Optional, List
from .testrail_client import TestRailClient
from .state import TestResult


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
        Build a modern, visually appealing HTML description for TestRail
        """
        status_badge = self._get_status_badge(result.status)
        execution_time = f"{result.duration:.2f}s" if result.duration else "N/A"
        
        # Color scheme based on status
        color = "#4caf50" if result.status == 'passed' else "#f44336"
        light_color = "#e8f5e9" if result.status == 'passed' else "#ffebee"
        
        html = f"""
<div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 8px; color: white; margin-bottom: 15px;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h3 style="margin: 0 0 5px 0; font-size: 20px;">🧪 {result.feature}</h3>
            <p style="margin: 0; font-size: 14px; opacity: 0.9;">{result.scenario}</p>
        </div>
        <div style="text-align: right;">
            {status_badge}
            <p style="margin: 5px 0 0 0; font-size: 12px;">⏱️ {execution_time}</p>
        </div>
    </div>
</div>

<div style="margin: 15px 0; padding: 15px; background-color: #f5f5f5; border-radius: 8px; border-left: 4px solid {color};">
    <h4 style="margin: 0 0 10px 0; color: {color}; font-size: 16px;">📋 Precondiciones</h4>
    <div style="background-color: white; padding: 10px; border-radius: 5px; font-size: 13px;">
"""
        
        # Precondiciones
        if result.background_steps:
            for step in result.background_steps:
                html += f"        <div style=\"margin: 5px 0; padding-left: 15px; border-left: 2px solid #2196F3;\">{step}</div>\n"
        else:
            html += "        <div style=\"color: #999;\">Ninguna precondición especificada</div>\n"
        
        html += """    </div>
</div>

<div style="margin: 15px 0; padding: 15px; background-color: #f5f5f5; border-radius: 8px; border-left: 4px solid #FF9800;">
    <h4 style="margin: 0 0 10px 0; color: #FF9800; font-size: 16px;">🔧 Pasos</h4>
    <div style="background-color: white; padding: 10px; border-radius: 5px; font-size: 13px;">
"""
        
        # Steps del Gherkin
        if result.gherkin_steps:
            for step in result.gherkin_steps:
                # Diferenciar tipos de pasos por color
                if 'Given' in step:
                    icon = "🎯"
                    color_step = "#2196F3"
                elif 'When' in step:
                    icon = "⚡"
                    color_step = "#FF9800"
                elif 'Then' in step:
                    icon = "✔️"
                    color_step = "#4CAF50"
                else:
                    icon = "•"
                    color_step = "#757575"
                
                html += f"""        <div style="margin: 5px 0; padding: 8px; padding-left: 15px; border-left: 3px solid {color_step}; background-color: #fafafa;">
            <span style="color: {color_step}; font-weight: bold;">{icon}</span> {step}
        </div>
"""
        else:
            html += "        <div style=\"color: #999;\">Ningún paso especificado</div>\n"
        
        html += """    </div>
</div>

<div style="margin: 15px 0; padding: 15px; background-color: #f5f5f5; border-radius: 8px; border-left: 4px solid #9C27B0;">
    <h4 style="margin: 0 0 10px 0; color: #9C27B0; font-size: 16px;">🎯 Resultado Esperado</h4>
    <div style="background-color: white; padding: 10px; border-radius: 5px; font-size: 13px;">
"""
        
        # Expected Assertions
        if result.expected_assertions:
            for assertion in result.expected_assertions:
                html += f"""        <div style="margin: 5px 0; padding: 8px; padding-left: 15px; border-left: 3px solid #9C27B0; background-color: #fafafa;">
            ✓ {assertion}
        </div>
"""
        else:
            html += "        <div style=\"color: #999;\">Ninguna aserción especificada</div>\n"
        
        # Error details
        if result.status == 'failed' and result.error_message:
            html += f"""    </div>
</div>

<div style="margin: 15px 0; padding: 15px; background-color: #ffebee; border-radius: 8px; border-left: 4px solid #f44336;">
    <h4 style="margin: 0 0 10px 0; color: #f44336; font-size: 16px;">❌ Error</h4>
    <div style="background-color: white; padding: 10px; border-radius: 5px; font-size: 12px; color: #d32f2f; font-family: 'Courier New', monospace; word-break: break-word;">
        {result.error_message}
    </div>
"""
        
        html += """    </div>
</div>

<div style="margin: 15px 0; padding: 15px; background-color: #e3f2fd; border-radius: 8px; border-left: 4px solid #1976D2;">
    <h4 style="margin: 0 0 10px 0; color: #1976D2; font-size: 16px;">⚙️ Info de Automatización</h4>
    <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
        <tr>
            <td style="border: 1px solid #e0e0e0; padding: 8px; background-color: #f5f5f5; font-weight: bold; width: 40%;">Framework</td>
            <td style="border: 1px solid #e0e0e0; padding: 8px;">🐉 Karate DSL</td>
        </tr>
        <tr>
            <td style="border: 1px solid #e0e0e0; padding: 8px; background-color: #f5f5f5; font-weight: bold;">Tipo</td>
            <td style="border: 1px solid #e0e0e0; padding: 8px;">BDD/Gherkin (Behavioral)</td>
        </tr>
        <tr>
            <td style="border: 1px solid #e0e0e0; padding: 8px; background-color: #f5f5f5; font-weight: bold;">Automatizado</td>
            <td style="border: 1px solid #e0e0e0; padding: 8px;">✅ Sí</td>
        </tr>
    </table>
</div>
"""
        
        return html
    
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
