
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
            automation_id = f"{result.feature}.{result.scenario}"
            
            # Check if case already exists
            existing_case = self._find_case_by_automation_id(automation_id)
            
            case_data = self._build_case_data(result, automation_id)
            
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
    
    def _build_case_data(self, result: TestResult, automation_id: str) -> dict:
        """Build TestRail case payload from TestResult with formatted description"""
        priority = self._infer_priority(result)
        description = self._build_formatted_description(result)
        
        return {
            'title': result.scenario,
            'custom_automation_id': automation_id,
            'description': description,
            'priority_id': priority,
            'custom_feature': result.feature,
            'custom_is_automated': 1,  # Marcar como automatizado
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
<p style="margin: 5px 0;"><strong>Automation Status:</strong> {status_badge} | {execution_time}</p>
</div>

<h4>📝 Test Steps:</h4>
<ul style="font-family: monospace; background-color: #f5f5f5; padding: 10px; border-radius: 5px; margin: 10px 0;">
"""
        
        # Add steps
        if result.steps:
            for i, step in enumerate(result.steps, 1):
                step_text = step.get('text', 'N/A') if isinstance(step, dict) else str(step)
                step_keyword = step.get('keyword', '•') if isinstance(step, dict) else '•'
                description_html += f'<li><strong>{step_keyword}</strong> {step_text}</li>\n'
        else:
            description_html += '<li>• No steps recorded</li>\n'
        
        description_html += """</ul>

<h4>📊 Expected Result:</h4>
<p style="background-color: #e8f5e9; padding: 10px; border-left: 4px solid #4caf50; border-radius: 3px; margin: 10px 0;">
Test should pass without errors. Response status and assertions must match expected values.
</p>
"""
        
        # Add error if failed
        if result.status == 'failed' and result.error_message:
            description_html += f"""
<h4>❌ Failure Details:</h4>
<p style="background-color: #ffebee; padding: 10px; border-left: 4px solid #f44336; border-radius: 3px; margin: 10px 0;">
<code>{result.error_message}</code>
</p>
"""
        
        description_html += """
<h4>⚙️ Automation Info:</h4>
<p style="margin: 10px 0;">
<code>type: karate</code> | <code>framework: karate-dsl</code> | <code>automated: yes</code>
</p>
"""
        
        return description_html
    
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
