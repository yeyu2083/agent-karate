
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
        Build a styled Markdown description for TestRail
        """
        md = ""
        
        # Header
        md += f"## 🧪 {result.feature}\n"
        md += f"**Scenario**: {result.scenario}\n\n"
        
        # Preconditions (Background)
        if result.background_steps:
            md += "### 📋 Background\n"
            for step in result.background_steps:
                md += f"- {step}\n"
            md += "\n"
        
        # Steps
        md += "### ⚙️ Steps\n"
        if result.gherkin_steps:
            for i, step in enumerate(result.gherkin_steps, 1):
                md += f"{i}. {step}\n"
        md += "\n"
        
        # Expected Results (Assertions)
        if result.expected_assertions:
            md += "### ✔️ Verified Assertions\n"
            for assertion in result.expected_assertions:
                clean = assertion.strip()
                # Clean up verbose keywords
                if clean.startswith("And match"):
                    clean = clean[9:].strip()
                elif clean.startswith("match"):
                    clean = clean[5:].strip()
                elif clean.startswith("Then status"):
                    clean = f"Status {clean[11:].strip()}"
                    
                md += f"- {clean}\n"
            md += "\n"
        
        # Status and Details
        md += "### 📊 Result\n"
        if result.status == 'passed':
            md += "✅ **PASSED**\n"
        else:
            md += "❌ **FAILED**\n"
            if result.error_message:
                md += f"\n**Error:**  \n{result.error_message}\n"

        if result.duration:
            md += f"\n⏱️ **Duration**: {result.duration:.2f}s"
            
        return md
    
    def _build_preconditions(self, result: TestResult) -> str:
        """Build preconditions from Background steps with visual styling"""
        steps = []
        if result.background_steps and len(result.background_steps) > 0:
            steps = result.background_steps
        else:
            steps = ["Given the API is accessible", "And the test environment is configured"]
        
        md = "📋 **Precondiciones:**\n"
        md += "```gherkin\n"
        for step in steps:
            if step.strip().lower().startswith('given'):
                md += f"🎯 {step}\n"
            elif step.strip().lower().startswith('when'):
                md += f"⚡ {step}\n"
            elif step.strip().lower().startswith('then'):
                md += f"✔️ {step}\n"
            elif step.strip().lower().startswith('and'):
                md += f"• {step}\n"
            else:
                md += f"{step}\n"
        md += "```\n"
        return md
    
    def _build_steps(self, result: TestResult) -> str:
        """Build test steps from Gherkin definition with visual formatting"""
        steps = []
        if result.gherkin_steps and len(result.gherkin_steps) > 0:
            steps = result.gherkin_steps
        else:
            steps = [
                "Given Prepare test data",
                "When Send API request",
                "Then Verify HTTP response status",
                "And Validate response body"
            ]
        
        md = "⚙️ **Pasos de Karate:**\n"
        md += "```gherkin\n"
        for i, step in enumerate(steps, 1):
            step_lower = step.strip().lower()
            if step_lower.startswith('given'):
                md += f"🎯 {step}\n"
            elif step_lower.startswith('when'):
                md += f"⚡ {step}\n"
            elif step_lower.startswith('then'):
                md += f"✔️ {step}\n"
            elif step_lower.startswith('and'):
                md += f"• {step}\n"
            else:
                md += f"{step}\n"
        md += "```\n"
        return md
    
    def _build_expected_result(self, result: TestResult) -> str:
        """Build expected result from assertions and test status with full visual detail"""
        md = ""
        
        md += "---\n"
        if result.status == 'passed':
            md += "✅ **RESULTADO: PASSED** 🎉\n"
        else:
            md += "❌ **RESULTADO: FAILED** ⚠️\n"
        md += "---\n\n"
        
        if result.expected_assertions and len(result.expected_assertions) > 0:
            md += "🔍 **Validaciones Esperadas:**\n\n"
            md += "```gherkin\n"
            for i, assertion in enumerate(result.expected_assertions, 1):
                clean = assertion.strip()
                if not clean.startswith("match") and not clean.startswith("status"):
                    md += f"{i}. And match {clean}\n"
                else:
                    md += f"{i}. {clean}\n"
            md += "```\n\n"
        
        if result.error_message:
            md += "🔴 **Detalles del Error:**\n"
            md += f"```\n{result.error_message}\n```\n"
        
        md += f"\n📊 **Estado**: {result.status.upper()}"
        if result.duration:
            md += f" | ⏱️ **Duración**: {result.duration:.2f}s"
        md += "\n"
        
        return md
    
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
