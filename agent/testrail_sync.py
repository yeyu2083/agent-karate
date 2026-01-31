# testrail_sync.py
"""
TestRail Synchronization - ENHANCED VERSION v2
Sync Karate test cases to TestRail with premium visual formatting
"""

import os
import re
import json
import subprocess
from typing import Optional, List
from enum import Enum
from .testrail_client import TestRailClient
from .state import TestResult


class StepType(Enum):
    """Tipos de pasos Gherkin con iconos visuales"""
    GIVEN = ("Given", "🎯", "Setup")
    WHEN = ("When", "⚡", "Action")
    THEN = ("Then", "✅", "Validation")
    AND = ("And", "➕", "Additional")
    MATCH = ("match", "🔍", "Assertion")
    
    def __init__(self, keyword: str, icon: str, label: str):
        self.keyword = keyword
        self.icon = icon
        self.label = label


class MarkdownFormatter:
    """
    Utility class for creating clean, professional Markdown for TestRail
    Optimizado para el renderizado específico de TestRail
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
    def status_badge(status: str) -> str:
        """Create status-specific badge"""
        badges = {
            'passed': '✅ **PASSED**',
            'failed': '❌ **FAILED**',
            'skipped': '⏭️ **SKIPPED**',
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
        self.pr_id = self._extract_pr_id_from_branch()
        self.automated_type_id = self._get_automated_type_id()  # 🤖 Obtener ID del tipo "Automated"
    
    @staticmethod
    def _extract_pr_id_from_branch() -> Optional[str]:
        """Extraer PR ID desde GitHub Actions env vars o rama actual"""
        # 🎯 Primero: intentar obtener del contexto de GitHub Actions
        github_pr_id = os.getenv('GITHUB_HEAD_REF')  # Para pull_request events
        if github_pr_id:
            print(f"✓ PR ID desde GitHub context: {github_pr_id}")
            return github_pr_id
        
        # 🎯 Alternativa: usar GITHUB_REF si es un PR
        github_ref = os.getenv('GITHUB_REF', '')
        if 'pull' in github_ref:
            # Ej: refs/pull/123/merge -> extraer 123
            try:
                pr_match = re.search(r'/pull/(\d+)/', github_ref)
                if pr_match:
                    pr_id = pr_match.group(1)
                    print(f"✓ PR ID desde GITHUB_REF: {pr_id}")
                    return pr_id
            except Exception as e:
                print(f"⚠️ No se pudo extraer PR ID de GITHUB_REF: {e}")
        
        # Fallback: extraer del nombre de la rama
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                branch_name = result.stdout.strip()
                print(f"✓ Rama actual: {branch_name}")
                
                # Patrones comunes para PR IDs:
                # PR-123, PR123, issue-456, #789, SCRUM-4, etc
                patterns = [
                    r'PR[#-]?(\d+)',      # PR-123 o PR#123
                    r'issue[#-]?(\d+)',   # issue-456
                    r'#(\d+)',            # #789
                    r'([A-Z]+-\d+)',      # SCRUM-4, JIRA-123
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, branch_name, re.IGNORECASE)
                    if match:
                        pr_id = match.group(1)
                        print(f"✓ ID extraído de rama: {pr_id}")
                        return pr_id
                
                # Si no encuentra patrón, usar todo después del última /
                pr_id = branch_name.split('/')[-1]
                print(f"✓ ID (rama): {pr_id}")
                return pr_id
        
        except Exception as e:
            print(f"⚠️ No se pudo extraer ID de rama: {e}")
        
        return None
    
    def _get_automated_type_id(self) -> Optional[int]:
        """🤖 Obtener el ID del tipo de caso 'Automated'"""
        try:
            types = self.client.get_case_types()
            for case_type in types:
                if case_type.get('name', '').lower() == 'automated':
                    type_id = case_type.get('id')
                    print(f"✓ Tipo 'Automated' encontrado: ID={type_id}")
                    return type_id
            print(f"⚠️ Tipo 'Automated' no encontrado en TestRail")
        except Exception as e:
            print(f"⚠️ Error obteniendo tipos de casos: {e}")
        return None
    
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
                        case_id = created['id']
                        print(f"✓ Created case #{case_id}: {automation_id}")
                        
                        # 🔄 Actualizar campos que solo funcionan en update_case
                        update_data = {}
                        if self.automated_type_id:
                            update_data['type_id'] = self.automated_type_id
                        if case_data.get('is_automated'):
                            update_data['is_automated'] = 1  # ✅ Usar 1 en lugar de True
                        user_id = case_data.get('assigned_to_id')
                        if user_id:
                            update_data['assigned_to_id'] = user_id
                        
                        if update_data:
                            self.client.update_case(case_id, update_data)
                            print(f"  ✓ Updated fields: {list(update_data.keys())}")
                        
                        case_map[automation_id] = case_id
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
    
    def _get_assigned_user_id(self) -> Optional[int]:
        """👤 Obtener ID del usuario asignado (email desde config o env vars)"""
        email_to_find = None
        
        # 1️⃣ Intentar obtener del testrail.config.json (PRIORITARIO)
        try:
            # Ruta correcta: agent/__file__ → agent/ → parent (agent-karate/) → testrail.config.json
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'testrail.config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    email_to_find = config.get('qa', {}).get('assigned_email')
                    user_name = config.get('qa', {}).get('assigned_name', 'QA Lead')
                    if email_to_find and email_to_find != 'tu@email.com':
                        print(f"✓ Email de config.json: {email_to_find} ({user_name})")
            else:
                print(f"⚠️ Config file no encontrado en: {config_path}")
        except Exception as e:
            print(f"⚠️ No se pudo leer config.json: {e}")
        
        # 2️⃣ Fallback: env vars
        if not email_to_find:
            email_to_find = os.getenv('TESTRAIL_ASSIGNED_EMAIL') or \
                           os.getenv('GITHUB_EMAIL') or \
                           os.getenv('GITHUB_ACTOR_EMAIL')
            if email_to_find:
                print(f"✓ Email de env var: {email_to_find}")
        
        # 3️⃣ Buscar usuario en TestRail por email
        if email_to_find and email_to_find != 'tu@email.com':
            try:
                users = self.client.get_users()
                for user in users:
                    user_email = user.get('email', '').lower()
                    if user_email == email_to_find.lower():
                        user_id = user.get('id')
                        user_name = user.get('name', email_to_find)
                        print(f"✓ Usuario encontrado en TestRail: {user_name} ({email_to_find}) → ID: {user_id}")
                        return user_id
                print(f"⚠️ Usuario con email {email_to_find} no encontrado en TestRail")
            except Exception as e:
                print(f"⚠️ Error buscando usuario por email: {e}")
        else:
            print(f"ℹ️ No se especificó usuario - los casos no serán asignados")
            print(f"   Configura en testrail.config.json: 'qa.assigned_email'")
        
        # 4️⃣ Fallback: ID directo
        testrail_user_id = os.getenv('TESTRAIL_USER_ID')
        if testrail_user_id:
            try:
                user_id = int(testrail_user_id)
                print(f"✓ Usando usuario ID desde env: {user_id}")
                return user_id
            except ValueError:
                pass
        
        return None
    
    def _build_case_data(self, result: TestResult, automation_id: str, title: str) -> dict:
        """Build TestRail case payload with all formatted fields"""
        priority = self._infer_priority(result)
        description = self._build_description(result)
        preconditions = self._build_preconditions(result)
        steps = self._build_steps(result)
        expected_result = self._build_expected_result(result)
        assigned_user_id = self._get_assigned_user_id()
        
        case_data = {
            'title': title,
            'type_id': self.automated_type_id,  # 🤖 Tipo Automated
            'custom_automation_id': automation_id,
            'description': description,
            'custom_preconds': preconditions,
            'custom_steps': steps,
            'custom_expected': expected_result,
            'priority_id': priority,
            'custom_feature': result.feature,
            'custom_status_actual': result.status,
        }
        
        # 👤 Agregar usuario asignado si se encontró
        if assigned_user_id:
            case_data['assigned_to_id'] = assigned_user_id
        
        # 🏷️ Agregar solo tags a references (para filtrar en TestRail)
        if result.tags:
            case_data['refs'] = ', '.join([f"@{tag}" for tag in result.tags])
        
        # Debug: mostrar payload COMPLETO
        print(f"📋 Payload completo para caso: {automation_id}")
        print(f"   Fields enviados por API:")
        for key, value in case_data.items():
            if key.startswith('custom_preconds') or key.startswith('custom_steps'):
                print(f"   - {key}: {str(value)[:80]}...")
            else:
                print(f"   - {key}: {value}")
        
        print(f"   ⚠️ Completa manualmente en TestRail:")
        print(f"      • Is Automated: Sí")
        
        return case_data
    
    # ============================================================================
    # FORMATTING METHODS - ENHANCED VERSION
    # ============================================================================
    
    def _build_description(self, result: TestResult) -> str:
        """
        Build main description with enhanced visual hierarchy
        """
        md = ""
        
        # Header con emoji y feature
        md += self.md.header(f"🧪 {result.feature}", level=2)
        md += self.md.blockquote(f"**Scenario:** {result.scenario}")
        
        # ✅ Tags en descripción
        if result.tags:
            tags_str = " ".join([f"[{tag}]" for tag in result.tags])
            md += self.md.blockquote(f"🏷️ **Tags:** {tags_str}")
        
        md += "\n"
        
        # Stats table con más info y mejor formato
        md += self.md.header("📊 Test Metrics", level=3)
        
        headers = ["Metric", "Value"]
        md += self.md.table_header(*headers)
        
        # Status con emoji grande
        status_display = self.md.status_badge(result.status)
        md += self.md.table_row("Status", status_display)
        
        # Duration si existe
        if result.duration:
            duration_display = f"⏱️ **{result.duration:.3f}s**"
            md += self.md.table_row("Execution Time", duration_display)
        
        # Steps ejecutados
        if result.steps:
            md += self.md.table_row("Steps Executed", f"🔢 **{len(result.steps)}**")
        
        # Gherkin steps count
        if result.gherkin_steps:
            md += self.md.table_row("Gherkin Steps", f"📝 **{len(result.gherkin_steps)}**")
        
        # Assertions count
        if result.expected_assertions:
            md += self.md.table_row("Assertions", f"🔍 **{len(result.expected_assertions)}**")
        
        # Examples si hay Scenario Outline
        if result.examples:
            md += self.md.table_row("Test Scenarios", f"📋 **{len(result.examples)}**")
        
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
        Build preconditions - clean and professional
        """
        md = ""
        
        if result.background_steps:
            md += self.md.header("🔧 Prerequisites", level=4)
            for i, step in enumerate(result.background_steps, 1):
                # Mostrar exactamente como está en el código
                md += self.md.numbered_item(step, i)
        else:
            # IMPORTANTE: No usar fallback genérico - esto ayuda a identificar problemas
            md += self.md.header("🔧 Prerequisites", level=4)
            md += self.md.blockquote("ℹ️ Background/Prerequisites not extracted from feature file")
        
        return md
    
    def _build_steps(self, result: TestResult) -> str:
        """
        Build test steps with icons and better organization
        """
        md = ""
        
        if result.gherkin_steps:
            md += self.md.header("📋 Test Steps", level=4)
            
            for i, step in enumerate(result.gherkin_steps, 1):
                # Formatear con icono apropiado
                formatted = self._format_step_with_icon(step)
                md += self.md.numbered_item(formatted, i)
            
            # Si hay examples, mostrarlos en tabla mejorada
            if result.examples:
                md += "\n"
                md += self.md.horizontal_rule()
                md += self.md.header("📊 Test Data Matrix (Scenario Outline)", level=4)
                
                if result.examples:
                    first_example = result.examples[0]
                    headers = list(first_example.keys())
                    
                    # Headers con emojis
                    emoji_headers = [f"📌 {h.upper()}" for h in headers]
                    md += self.md.table_header(*emoji_headers)
                    
                    # Limitar a 10 rows para no saturar
                    for example in result.examples[:10]:
                        values = [f"`{example.get(h, '')}`" for h in headers]
                        md += self.md.table_row(*values)
                    
                    if len(result.examples) > 10:
                        md += f"\n> *...and {len(result.examples) - 10} more test scenarios*\n"
        else:
            # Fallback steps con mejor formato
            md += self.md.header("📋 Test Steps", level=4)
            md += self.md.numbered_item("🎯 **Setup** - Prepare test data and environment", 1)
            md += self.md.numbered_item("⚡ **Execute** - Send API request with test payload", 2)
            md += self.md.numbered_item("✅ **Verify** - Check HTTP response status code", 3)
            md += self.md.numbered_item("✅ **Validate** - Assert response body structure and values", 4)
        
        return md
    
    def _build_expected_result(self, result: TestResult) -> str:
        """
        Build expected results - SUPER visual y organizado
        """
        md = ""
        
        # Status banner con separadores y más énfasis
        md += "\n"
        md += "═══════════════════════════════════════════════════════\n\n"
        md += self.md.header(self.md.status_badge(result.status), level=2)
        md += "═══════════════════════════════════════════════════════\n\n"
        
        # Validations con formato mejorado - SIN TABLA, con formato lista estilizada
        if result.expected_assertions:
            md += self.md.header("🔍 Validations", level=3)
            md += "\n"
            
            for i, assertion in enumerate(result.expected_assertions, 1):
                clean_assertion = self._clean_assertion(assertion)
                
                # Status icon basado en el resultado general
                if result.status == "passed":
                    status_icon = "✅"
                    status_text = "PASS"
                else:
                    status_icon = "❌"
                    status_text = "FAIL"
                
                # Formato lista estilizada con números y boxes
                md += f"**`{i:02d}`** {status_icon} **{status_text}** │ {clean_assertion}\n\n"
            
            md += "\n"
        
        # Error details si falló - formato mejorado
        if result.error_message:
            md += "\n"
            md += "─────────────────────────────────────────────────────\n\n"
            md += self.md.header("🔴 Error Details", level=3)
            md += "\n"
            md += "⚠️ **The test failed with the following error:**\n\n"
            
            # Code block con el error
            md += self.md.code_block(result.error_message, "")
            md += "\n"
        
        # Metadata footer con mejor diseño - SIN tabla, con formato de bloques
        md += "\n"
        md += "─────────────────────────────────────────────────────\n\n"
        md += self.md.header("📌 Test Metadata", level=4)
        md += "\n"
        
        # Formato de bloques en lugar de tabla
        metadata_items = []
        
        metadata_items.append(f"🏷️ **Feature:** `{result.feature}`")
        metadata_items.append(f"📊 **Status:** {self.md.status_badge(result.status)}")
        
        if result.duration:
            metadata_items.append(f"⏱️ **Duration:** `{result.duration:.3f}s`")
        
        if result.steps:
            metadata_items.append(f"🔢 **Steps Executed:** `{len(result.steps)}`")
        
        if result.gherkin_steps:
            metadata_items.append(f"📝 **Gherkin Steps:** `{len(result.gherkin_steps)}`")
        
        if result.expected_assertions:
            passed = len(result.expected_assertions) if result.status == "passed" else 0
            total = len(result.expected_assertions)
            metadata_items.append(f"✅ **Assertions:** `{passed}/{total}` passed")
        
        # Mostrar en formato de bloques con bullets
        for item in metadata_items:
            md += f"- {item}\n"
        
        md += "\n"
        
        return md
    
    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    
    def _format_step_with_icon(self, step: str) -> str:
        """
        Format step with appropriate icon based on keyword
        """
        step = step.strip()
        step_lower = step.lower()
        
        # Detect keyword and add icon
        if step_lower.startswith('given'):
            icon = "🎯"
            clean = step[5:].strip()
            return f"{icon} **Given** {clean}"
        elif step_lower.startswith('when'):
            icon = "⚡"
            clean = step[4:].strip()
            return f"{icon} **When** {clean}"
        elif step_lower.startswith('then'):
            icon = "✅"
            clean = step[4:].strip()
            return f"{icon} **Then** {clean}"
        elif step_lower.startswith('and'):
            icon = "➕"
            clean = step[3:].strip()
            return f"{icon} **And** {clean}"
        elif 'match' in step_lower:
            icon = "🔍"
            return f"{icon} {step}"
        else:
            return f"▪️ {step}"
    
    def _format_step(self, step: str) -> str:
        """
        Format a Gherkin step - remove redundant keywords, clean up
        """
        step = step.strip()
        
        # Remove redundant Gherkin keywords pero mantener estructura
        for keyword in ['Given', 'When', 'Then', 'And', 'But']:
            if step.startswith(f"{keyword} "):
                step = step[len(keyword):].strip()
                break
        
        return step
    
    def _clean_assertion(self, assertion: str) -> str:
        """
        Clean up assertion text para mejor legibilidad
        Incluye formato visual mejorado
        """
        clean = assertion.strip()
        
        # Remove verbose keywords pero mantener info útil
        replacements = {
            'And match ': '',
            'match ': '',
            'Then status ': '**HTTP Status** → ',
            'And status ': '**HTTP Status** → ',
            'status ': '**HTTP Status** → ',
        }
        
        for old, new in replacements.items():
            if clean.startswith(old):
                clean = new + clean[len(old):].strip()
                break
        
        # Mejorar formato de comparaciones
        if '==' in clean:
            parts = clean.split('==')
            if len(parts) == 2:
                left = parts[0].strip()
                right = parts[1].strip()
                
                # Si es HTTP Status, formato especial
                if 'HTTP Status' in clean:
                    clean = f"**HTTP Status** → `{right}`"
                else:
                    # Formato mejorado con flecha
                    clean = f"`{left}` **must equal** `{right}`"
        
        # Highlight de tipos especiales
        clean = clean.replace("'#array'", "`#array` 📋")
        clean = clean.replace("'#object'", "`#object` 📦")
        clean = clean.replace("'#string'", "`#string` 📝")
        clean = clean.replace("'#number'", "`#number` 🔢")
        clean = clean.replace("'#boolean'", "`#boolean` ✓/✗")
        
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