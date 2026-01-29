from typing import Optional, List
from enum import Enum
from .testrail_client import TestRailClient
from .state import TestResult

class TestRailSync:
    def __init__(self, testrail_client: TestRailClient, project_id: int, suite_id: int):
        self.client = testrail_client
        self.project_id = project_id
        self.suite_id = suite_id
        self.sections_cache = None

    def _build_preconditions(self, result: TestResult) -> str:
        """Extrae Background steps de state.py y les da formato"""
        # Verificamos si hay pasos de background
        steps = result.background_steps if result.background_steps else ["Given the API is accessible"]
        
        md = "### 📋 Precondiciones (Background)\n\n"
        for step in steps:
            md += f"* {step.strip()}\n"
        md += "\n"
        return md

    def _build_steps(self, result: TestResult) -> str:
        """Formatea los gherkin_steps de state.py con sintaxis resaltada"""
        steps = result.gherkin_steps if result.gherkin_steps else []
        
        md = "### ⚙️ Pasos de Ejecución\n\n"
        md += "```gherkin\n"
        if steps:
            for step in steps:
                md += f"{step.strip()}\n"
        else:
            md += "# No se detectaron pasos Gherkin en este escenario.\n"
        md += "```\n\n"
        return md

    def _build_expected_result(self, result: TestResult) -> str:
        """Construye el bloque de resultado final basado en status y expected_assertions"""
        status_icon = "✅" if result.status.lower() == 'passed' else "❌"
        
        md = f"## {status_icon} RESULTADO: {result.status.upper()}\n"
        md += "---\n\n"
        
        # Validaciones del modelo (Match statements)
        if result.expected_assertions:
            md += "### 🔍 Validaciones Verificadas\n"
            md += "```gherkin\n"
            for assertion in result.expected_assertions:
                md += f"{assertion.strip()}\n"
            md += "```\n\n"
        
        # Manejo de errores
        if result.status.lower() != 'passed' and result.error_message:
            md += "### 🔴 Detalle del Error\n"
            md += "```text\n"
            md += f"{result.error_message.strip()}\n"
            md += "```\n\n"
            md += "> 💡 **Nota de Líder:** El log detallado ha sido adjuntado a este resultado para análisis técnico.\n\n"

        # Footer técnico con datos del modelo
        md += "---\n"
        dur = f"{result.duration:.2f}s" if result.duration else "0s"
        md += f"**Métricas:** ⏱️ Duración: `{dur}` | 🤖 Automatizado: `True` | 📂 Feature: `{result.feature}`"
        
        return md

    def _build_case_data(self, result: TestResult, automation_id: str, title: str) -> dict:
        """Une todas las piezas para el payload de TestRail"""
        return {
            'title': title,
            'custom_automation_id': automation_id,
            'description': f"**Escenario:** {result.scenario}\n\n{self._build_preconditions(result)}",
            'custom_preconds': self._build_preconditions(result),
            'custom_steps': self._build_steps(result),
            'custom_expected': self._build_expected_result(result),
            'priority_id': 3, # Medium por defecto
            'custom_is_automated': 1
        }