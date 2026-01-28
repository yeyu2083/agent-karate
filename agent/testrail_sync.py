
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
        Build an HTML-formatted description for TestRail
        Includes feature, steps, execution status and automation info
        """
        
        # Status badge
        status_badge = self._get_status_badge(result.status)
        execution_time = f"⏱️ {result.duration:.2f}s" if result.duration else "⏱️ N/A"
        
        description_html = f"""
<div style="background-color: #f9f9f9; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
<h3>📋 Feature: <strong>{result.feature}</strong></h3>
<p style="margin: 5px 0;"><strong>Status:</strong> {status_badge} | {execution_time}</p>
"""
        
        # Add error details if present
        if result.error_message:
            description_html += f'<p style="margin: 5px 0;"><strong>Summary:</strong> {result.error_message}</p>\n'
        
        description_html += """</div>

<h4>📝 Test Scenarios:</h4>
<ul style="background-color: #f5f5f5; padding: 10px; border-radius: 5px; margin: 10px 0;">
"""
        
        # If we have individual steps, show them
        if result.steps:
            for i, step in enumerate(result.steps, 1):
                step_text = step.get('text', 'N/A') if isinstance(step, dict) else str(step)
                step_status = step.get('status', 'unknown') if isinstance(step, dict) else 'unknown'
                status_emoji = '✅' if step_status == 'passed' else '❌' if step_status == 'failed' else '⚠️'
                step_keyword = step.get('keyword', '•').strip() if isinstance(step, dict) else '•'
                duration_ms = step.get('duration_ms', 0) if isinstance(step, dict) else 0
                
                duration_str = f" ({duration_ms:.0f}ms)" if duration_ms > 0 else ""
                description_html += f'<li>{status_emoji} <strong>{step_keyword}</strong> {step_text}{duration_str}</li>\n'
        else:
            # Fallback mode: show feature summary
            description_html += f'<li>📊 {result.scenario}</li>\n'
        
        description_html += """</ul>

<h4>📊 Expected Result:</h4>
<p style="background-color: #e8f5e9; padding: 10px; border-left: 4px solid #4caf50; border-radius: 3px; margin: 10px 0;">
Test should pass without errors. All API responses must match expected schemas and status codes.
</p>
"""
        
        # Add error if failed
        if result.status == 'failed' and result.error_message:
            description_html += f"""
<h4>❌ Failure Details:</h4>
<p style="background-color: #ffebee; padding: 10px; border-left: 4px solid #f44336; border-radius: 3px; margin: 10px 0;">
<strong>Error:</strong> {result.error_message}
</p>
"""
        
        description_html += """
<h4>⚙️ Automation Info</h4>
<table style="width: 100%; border-collapse: collapse; margin: 10px 0;">
<tr>
  <td style="border: 1px solid #ddd; padding: 5px;"><strong>Framework</strong></td>
  <td style="border: 1px solid #ddd; padding: 5px;">Karate DSL (API Testing)</td>
</tr>
<tr>
  <td style="border: 1px solid #ddd; padding: 5px;"><strong>Automation Type</strong></td>
  <td style="border: 1px solid #ddd; padding: 5px;">Behavioral (BDD/Gherkin)</td>
</tr>
<tr>
  <td style="border: 1px solid #ddd; padding: 5px;"><strong>Automated</strong></td>
  <td style="border: 1px solid #ddd; padding: 5px;">✅ Yes</td>
</tr>
</table>
"""
        
        return description_html
    
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
