from typing import Optional, List
from .testrail_client import TestRailClient
from .state import TestResult

class TestRailSync:
    def __init__(self, testrail_client: TestRailClient, project_id: int, suite_id: int):
        self.client = testrail_client
        self.project_id = project_id
        self.suite_id = suite_id

    def _build_preconditions(self, result: TestResult) -> str:
        """Formatea el Background como una lista clara"""
        steps = result.background_steps if result.background_steps else ["Given el entorno está configurado"]
        md = "### 📋 Precondiciones\n\n"
        for step in steps:
            md += f"* {step.strip()}\n"
        return md + "\n"

    def _build_steps(self, result: TestResult) -> str:
        """Formatea los pasos con sintaxis Gherkin para colores en TestRail"""
        steps = result.gherkin_steps if result.gherkin_steps else []
        md = "### ⚙️ Pasos de Karate\n\n"
        md += "```gherkin\n"
        if steps:
            for step in steps:
                md += f"{step.strip()}\n"
        else:
            md += "# No se capturaron pasos específicos.\n"
        md += "```\n\n"
        return md

    def _build_expected_result(self, result: TestResult) -> str:
        """Crea un reporte ejecutivo con el resultado final"""
        icon = "✅" if result.status.lower() == 'passed' else "❌"
        md = f"## {icon} STATUS: {result.status.upper()}\n"
        md += "---\n\n"
        
        if result.expected_assertions:
            md += "### 🔍 Validaciones Realizadas\n"
            md += "```gherkin\n"
            for assertion in result.expected_assertions:
                md += f"{assertion.strip()}\n"
            md += "```\n\n"
        
        if result.status.lower() != 'passed' and result.error_message:
            md += "### 🔴 Detalle del Error\n"
            md += "```text\n"
            md += f"{result.error_message.strip()}\n"
            md += "```\n\n"
            md += "> 💡 **Tip:** Revisar el log adjunto en la ejecución para más detalle.\n\n"

        md += "---\n"
        md += f"⏱️ **Duración:** `{result.duration:.2f}s` | 🤖 **Modo:** `Automatizado`"
        return md

    def _build_case_data(self, result: TestResult, automation_id: str, title: str) -> dict:
        """Genera el diccionario final para la API de TestRail"""
        return {
            'title': title,
            'custom_automation_id': automation_id,
            'description': f"**Feature:** {result.feature}\n**Escenario:** {result.scenario}",
            'custom_preconds': self._build_preconditions(result),
            'custom_steps': self._build_steps(result),
            'custom_expected': self._build_expected_result(result),
            'priority_id': 3,
            'custom_is_automated': 1
        }