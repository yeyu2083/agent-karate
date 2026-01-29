# testrail_sync.py
"""
TestRail Synchronization - IMPROVED VERSION
Sync Karate test cases to TestRail with enhanced Markdown formatting
"""

from typing import Optional, List
from enum import Enum
from .testrail_client import TestRailClient
from .state import TestResult


class StepType(Enum):
    """Tipos de pasos Gherkin con mejor visualización"""
    GIVEN = ("Given", "🎯", "Precondition")
    WHEN = ("When", "⚡", "Action")
    THEN = ("Then", "✅", "Validation")
    AND = ("And", "➕", "Additional")
    
    def __init__(self, keyword: str, icon: str, label: str):
        self.keyword = keyword
        self.icon = icon
        self.label = label


class MarkdownFormatter:
    """
    Utility class for creating clean, professional Markdown for TestRail
    TestRail soporta Markdown pero es limitado - esta clase optimiza para eso.
    """
    
    @staticmethod
    def header(text: str, level: int = 2) -> str:
        """Create header with proper spacing"""
        return f"\n{'#' * level} {text}\n\n"
    
    @staticmethod
    def bold(text: str) -> str:
        """Bold text"""
        return f"**{text}**"
    
    @staticmethod
    def code_inline(text: str) -> str:
        """Inline code"""
        return f"`{text}`"
    
    @staticmethod
    def code_block(text: str, language: str = "") -> str:
        """Code block with optional language"""
        return f"\n```{language}\n{text}\n```\n"
    
    @staticmethod
    def list_item(text: str, indent: int = 0) -> str:
        """List item with optional indentation"""
        return f"{'  ' * indent}- {text}\n"
    
    @staticmethod
    def numbered_item(text: str, number: int) -> str:
        """Numbered list item"""
        return f"{number}. {text}\n"
    
    @staticmethod
    def horizontal_rule() -> str:
        """Horizontal divider"""
        return "\n---\n\n"
    
    @staticmethod
    def blockquote(text: str) -> str:
        """Blockquote for emphasis"""
        return f"> {text}\n"
    
    @staticmethod
    def table_row(*cells: str) -> str:
        """Create table row"""
        return "| " + " | ".join(cells) + " |\n"
    
    @staticmethod
    def table_header(*headers: str) -> str:
        """Create table header with separator"""
        header = MarkdownFormatter.table_row(*headers)
        separator = MarkdownFormatter.table_row(*["---"] * len(headers))
        return header + separator
    
    @staticmethod
    def badge(text: str, emoji: str = "") -> str:
        """Create visual badge with emoji"""
        if emoji:
            return f"{emoji} **{text}**"
        return f"**{text}**"
    
    @staticmethod
    def status_badge(status: str) -> str:
        """Create status-specific badge"""
        badges = {
            'passed': '✅ **PASSED**',
            'failed': '❌ **FAILED**',
            'skipped': '⏭️ **SKIPPED**',
            'pending': '⏳ **PENDING**'
        }
        return badges.get(status.lower(), f'❓ **{status.upper()}**')


class TestRailSync:
    """Synchronize Karate scenarios to TestRail cases with enhanced formatting"""
    
    def __init__(self, testrail_client: TestRailClient, project_id: int, suite_id: int):
        self.client = testrail_client
        self.project_id = project_id
        self.suite_id = suite_id
        self.sections_cache = None
        self.md = MarkdownFormatter()
    
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
            section_id = sections[0]['id']
            print(f"✓ Using section: {sections[0]['name']} (ID: {section_id})")
        
        for result in test_results:
            # Clean scenario name
            if result.feature == result.scenario:
                automation_id = result.feature
                title = result.feature
            else:
                scenario_clean = result.scenario.split('.')[0] if '.' in result.scenario else result.scenario
                automation_id = f"{result.feature}.{scenario_clean}"
                title = scenario_clean
            
            existing_case = self._find_case_by_automation_id(automation_id)
            case_data = self._build_case_data(result, automation_id, title)
            
            if existing_case:
                updated = self.client.update_case(existing_case['id'], case_data)
                if updated:
                    print(f"✓ Updated case #{existing_case['id']}: {automation_id}")
                    case_map[automation_id] = existing_case['id']
            else:
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
                if case.get('custom_automation_id') == automation_id:
                    return case
            return None
        except Exception as e:
            print(f"⚠️ Error searching for case {automation_id}: {e}")
            return None
    
    def _build_case_data(self, result: TestResult, automation_id: str, title: str) -> dict:
        """Build TestRail case payload with all formatted fields"""
        priority = self._infer_priority(result)
        description = self._build_description(result)
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
            'custom_is_automated': 1,
            'custom_status_actual': result.status,
            'estimate': self._estimate_duration(result.duration) if result.duration else None,
        }
    
    # ============================================================================
    # FORMATTING METHODS - Aquí está la magia ✨
    # ============================================================================
    
    def _build_description(self, result: TestResult) -> str:
        """
        Build main description with clean, scannable layout
        """
        md = ""
        
        # Header with feature info
        md += self.md.header(f"🧪 {result.feature}", level=2)
        md += self.md.blockquote(f"**Scenario:** {result.scenario}")
        md += "\n"
        
        # Quick stats table - muy visual
        if result.duration or result.status:
            md += self.md.header("📊 Quick Stats", level=3)
            
            # Table format
            headers = ["Metric", "Value"]
            md += self.md.table_header(*headers)
            
            if result.status:
                md += self.md.table_row("Status", self.md.status_badge(result.status))
            
            if result.duration:
                duration_str = f"⏱️ {result.duration:.2f}s"
                md += self.md.table_row("Duration", duration_str)
            
            if result.examples:
                md += self.md.table_row("Examples", f"📋 {len(result.examples)} scenarios")
            
            md += "\n"
        
        # Background steps si existen
        if result.background_steps:
            md += self.md.header("🎬 Background Setup", level=3)
            for step in result.background_steps:
                md += self.md.list_item(self._format_step(step))
            md += "\n"
        
        return md
    
    def _build_preconditions(self, result: TestResult) -> str:
        """
        Build preconditions - limpio y claro
        """
        md = ""
        
        if result.background_steps:
            md += self.md.header("Prerequisites", level=4)
            for i, step in enumerate(result.background_steps, 1):
                md += self.md.numbered_item(self._format_step(step), i)
        else:
            # Default preconditions
            md += self.md.header("Prerequisites", level=4)
            md += self.md.list_item("API endpoint is accessible")
            md += self.md.list_item("Test environment is configured")
            md += self.md.list_item("Required test data is available")
        
        return md
    
    def _build_steps(self, result: TestResult) -> str:
        """
        Build test steps with clear structure and icons
        """
        md = ""
        
        if result.gherkin_steps:
            md += self.md.header("Test Steps", level=4)
            
            for i, step in enumerate(result.gherkin_steps, 1):
                # Detectar tipo de paso y añadir icono
                step_type = self._detect_step_type(step)
                icon = step_type.icon if step_type else "▪️"
                
                formatted_step = self._format_step(step)
                md += self.md.numbered_item(f"{icon} {formatted_step}", i)
            
            # Si hay examples, mostrarlos en tabla
            if result.examples:
                md += "\n"
                md += self.md.header("📋 Test Data (Examples)", level=5)
                
                if result.examples:
                    # Usar las keys del primer example como headers
                    first_example = result.examples[0]
                    headers = list(first_example.keys())
                    
                    md += self.md.table_header(*headers)
                    
                    for example in result.examples[:5]:  # Limitar a 5 para no saturar
                        values = [str(example.get(h, '')) for h in headers]
                        md += self.md.table_row(*values)
                    
                    if len(result.examples) > 5:
                        md += f"\n*...and {len(result.examples) - 5} more examples*\n"
        else:
            # Fallback steps
            md += self.md.header("Test Steps", level=4)
            md += self.md.numbered_item("🎯 Prepare test data", 1)
            md += self.md.numbered_item("⚡ Execute API request", 2)
            md += self.md.numbered_item("✅ Verify response status", 3)
            md += self.md.numbered_item("✅ Validate response body", 4)
        
        return md
    
    def _build_expected_result(self, result: TestResult) -> str:
        """
        Build expected results - MUY visual y fácil de leer
        """
        md = ""
        
        # Status banner grande
        md += self.md.horizontal_rule()
        md += self.md.header(self.md.status_badge(result.status), level=3)
        md += self.md.horizontal_rule()
        
        # Assertions/Validations
        if result.expected_assertions:
            md += self.md.header("🔍 Validations", level=4)
            
            for i, assertion in enumerate(result.expected_assertions, 1):
                clean_assertion = self._clean_assertion(assertion)
                
                # Diferentes iconos para variedad visual
                icons = ['✓', '✔️', '☑️', '✅']
                icon = icons[i % len(icons)]
                
                md += self.md.list_item(f"{icon} {clean_assertion}")
            
            md += "\n"
        
        # Error details si falló
        if result.error_message:
            md += self.md.header("🔴 Error Details", level=4)
            md += self.md.blockquote("The test failed with the following error:")
            md += self.md.code_block(result.error_message, "")
            md += "\n"
        
        # Footer con metadata
        md += self._build_metadata_footer(result)
        
        return md
    
    def _build_metadata_footer(self, result: TestResult) -> str:
        """
        Build metadata footer con info relevante
        """
        md = ""
        md += self.md.horizontal_rule()
        md += self.md.header("📌 Test Metadata", level=5)
        
        metadata = []
        metadata.append(f"**Feature:** {self.md.code_inline(result.feature)}")
        metadata.append(f"**Status:** {self.md.status_badge(result.status)}")
        
        if result.duration:
            metadata.append(f"**Duration:** ⏱️ {result.duration:.2f}s")
        
        if result.steps:
            metadata.append(f"**Steps Executed:** {len(result.steps)}")
        
        md += " | ".join(metadata)
        md += "\n"
        
        return md
    
    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    
    def _detect_step_type(self, step: str) -> Optional[StepType]:
        """Detect Gherkin step type from text"""
        step_lower = step.lower().strip()
        
        for step_type in StepType:
            if step_lower.startswith(step_type.keyword.lower()):
                return step_type
        
        return None
    
    def _format_step(self, step: str) -> str:
        """
        Format a Gherkin step - remove redundant keywords, clean up
        """
        step = step.strip()
        
        # Remove redundant Gherkin keywords
        for keyword in ['Given', 'When', 'Then', 'And', 'But']:
            if step.startswith(f"{keyword} "):
                step = step[len(keyword):].strip()
                break
        
        return step
    
    def _clean_assertion(self, assertion: str) -> str:
        """
        Clean up assertion text para mejor legibilidad
        """
        clean = assertion.strip()
        
        # Remove verbose keywords
        replacements = {
            'And match ': '',
            'match ': '',
            'Then status ': 'HTTP Status: ',
            'And status ': 'HTTP Status: ',
            'status ': 'HTTP Status: ',
        }
        
        for old, new in replacements.items():
            if clean.startswith(old):
                clean = new + clean[len(old):].strip()
                break
        
        return clean
    
    def _infer_priority(self, result: TestResult) -> int:
        """
        Infer priority from scenario characteristics
        1=Don't Test, 2=Low, 3=Medium, 4=High, 5=Critical
        """
        scenario_lower = result.scenario.lower()
        feature_lower = result.feature.lower()
        
        # Critical indicators
        if any(x in scenario_lower + feature_lower for x in 
               ['critical', 'smoke', 'p0', 'blocker', 'security']):
            return 5  # Critical
        
        # High priority
        if any(x in scenario_lower + feature_lower for x in 
               ['important', 'main', 'core', 'p1', 'auth']):
            return 4  # High
        
        # Low priority
        if any(x in scenario_lower + feature_lower for x in 
               ['edge', 'negative', 'error', 'p3', 'optional']):
            return 2  # Low
        
        # Default: Medium
        return 3
    
    def _estimate_duration(self, duration: float) -> str:
        """
        Convert duration to TestRail estimate format (e.g., "30s", "2m")
        """
        if duration < 60:
            return f"{int(duration)}s"
        elif duration < 3600:
            minutes = int(duration / 60)
            return f"{minutes}m"
        else:
            hours = int(duration / 3600)
            return f"{hours}h"