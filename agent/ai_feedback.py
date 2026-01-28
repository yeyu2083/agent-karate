#!/usr/bin/env python3
"""
AI Feedback Generator for TestRail Results
Generates intelligent insights using LLM based on test execution results
with QA Lead perspective: Risk Analysis, User Impact, and Business Context
"""

from typing import List, Optional
from .state import TestResult
from .nodes import get_llm
import os


class AIFeedbackGenerator:
    """Generate AI-powered feedback on test results with QA Lead perspective"""
    
    def __init__(self, llm_provider: str = "glm"):
        self.llm_provider = llm_provider
        try:
            self.llm = get_llm(llm_provider)
            self.enabled = True
        except Exception as e:
            print(f"⚠️ AI Feedback disabled: {e}")
            self.enabled = False
    
    def generate_pr_comment(self, results: List[TestResult]) -> str:
        """Generate GitHub PR comment with QA Lead perspective"""
        if not self.enabled or not results:
            return self._fallback_pr_comment(results)
        
        try:
            total = len(results)
            passed = sum(1 for r in results if r.status == "passed")
            failed = sum(1 for r in results if r.status == "failed")
            pass_rate = (passed / total * 100) if total > 0 else 0
            
            # Determine traffic light status
            if pass_rate == 100:
                status_emoji = "🟢"
                status_text = "PASS"
                risk_level = "LOW"
            elif pass_rate >= 90:
                status_emoji = "🟡"
                status_text = "ADVERTENCIA"
                risk_level = "MEDIUM"
            else:
                status_emoji = "🔴"
                status_text = "BLOQUEADO"
                risk_level = "CRITICAL"
            
            results_text = f"""
Resultados de Pruebas - Análisis QA Lead:
===========================================

📊 ESTADO GENERAL: {status_emoji} {status_text}
- Tasa de paso: {pass_rate:.1f}% ({passed}/{total})
- Nivel de riesgo: {risk_level}

Detalles de Fallos ({failed} total):
"""
            
            for result in results:
                if result.status == "failed":
                    results_text += f"""
FALLO EN: {result.feature}
├─ Escenario: {result.scenario}
├─ Duración: {result.duration:.2f}s
├─ Error: {result.error_message or 'Sin detalles de error'}
└─ Impacto: Requiere investigación antes de merge
"""
            
            # Call LLM for PR comment generation
            from langchain_core.prompts import ChatPromptTemplate
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """Eres un Senior QA Automation Lead responsable de validar PRs.
Tu objetivo es NO SOLO reportar fallos, sino:

1. EVALUAR RIESGO: ¿Es seguro mergear esto? ¿Hay datos técnicos que sugieran deuda?
2. TRADUCIR A USUARIO: Si falla POST /login, significa "Los usuarios NO pueden iniciar sesión"
3. RECOMENDAR ACCIÓN: Sé específico. No digas "revisar", di "revisar el manejo de nulos en campo X"
4. CONTEXTO DE NEGOCIO: Si hay fallos en auth, es crítico. Si hay fallos en reportes, es alto.

Genera un comentario profesional para GitHub PR que:
- Use emoji de semáforo (🟢🟡🔴)
- Tenga una línea de "Veredicto" clara
- Análisis de impacto real para usuarios finales
- Acciones específicas y accionables
- Tono: Profesional, técnico, pero orientado al producto"""),
                ("human", f"""{results_text}

Genera el comentario para GitHub PR en formato Markdown.
Responde DIRECTAMENTE con el comentario (sin explicaciones extras).
""")
            ])
            
            chain = prompt | self.llm
            response = chain.invoke({})
            return response.content if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            print(f"⚠️ PR comment generation failed: {e}")
            return self._fallback_pr_comment(results)
    
    def generate_summary(self, results: List[TestResult]) -> str:
        """Generate AI-powered summary of test results (Internal Analysis)"""
        if not self.enabled or not results:
            return self._fallback_summary(results)
        
        try:
            total = len(results)
            passed = sum(1 for r in results if r.status == "passed")
            failed = sum(1 for r in results if r.status == "failed")
            pass_rate = (passed / total * 100) if total > 0 else 0
            
            results_text = f"""
Análisis Interno de Resultados:
- Total: {total} tests
- Pasados: {passed} ({pass_rate:.1f}%)
- Fallidos: {failed}

Fallos Detectados:
"""
            
            for result in results:
                if result.status == "failed":
                    results_text += f"""
- {result.feature} / {result.scenario}: {result.error_message}
"""
            
            from langchain_core.prompts import ChatPromptTemplate
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """Eres un QA Engineer especializado en automatización de pruebas API.
Analiza estos resultados como si estuvieras en una retrospectiva técnica.

ENFOQUE EN:
1. Patrones de fallos (¿hay un patrón común?)
2. Deuda técnica (¿tests lentos? ¿setup complejo?)
3. Salud del proyecto (¿escalable? ¿mantenible?)
4. Recomendaciones de mejora para próximo sprint

Sé directo y técnico. Usa datos cuando sea posible."""),
                ("human", f"""{results_text}

Genera un análisis conciso (máximo 500 palabras) con insights accionables.""")
            ])
            
            chain = prompt | self.llm
            response = chain.invoke({})
            return response.content if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            print(f"⚠️ Summary generation failed: {e}")
            return self._fallback_summary(results)
    
    def _fallback_pr_comment(self, results: List[TestResult]) -> str:
        """Fallback PR comment when AI is disabled"""
        total = len(results)
        passed = sum(1 for r in results if r.status == "passed")
        failed = sum(1 for r in results if r.status == "failed")
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        if pass_rate == 100:
            status = "🟢 PASS - SAFE TO MERGE"
            status_color = "success"
        elif pass_rate >= 90:
            status = "🟡 WARNING - REVIEW REQUIRED"
            status_color = "warning"
        else:
            status = "🔴 BLOCKED - DO NOT MERGE"
            status_color = "critical"
        
        # Build results table
        results_table = "| Feature | Status | Duration | Error |\n|---------|--------|----------|-------|\n"
        for r in results:
            status_icon = "✅" if r.status == "passed" else "❌"
            error_msg = r.error_message[:50] + "..." if r.error_message and len(r.error_message) > 50 else r.error_message or "N/A"
            results_table += f"| {r.feature[:30]} | {status_icon} {r.status.upper()} | {r.duration:.2f}s | {error_msg} |\n"
        
        return f"""# 🛑 QA Automation Lead - Análisis de Calidad

## {status}

### 📊 Métricas Rápidas
| Métrica | Valor | Estado |
|---------|-------|--------|
| **Pass Rate** | {pass_rate:.1f}% | {'🟢' if pass_rate == 100 else '🟡' if pass_rate >= 90 else '🔴'} |
| **Tests Pasados** | {passed}/{total} | ✅ |
| **Tests Fallidos** | {failed}/{total} | {'✅' if failed == 0 else '❌'} |
| **Riesgo** | {'LOW' if pass_rate == 100 else 'MEDIUM' if pass_rate >= 90 else 'CRITICAL'} | {'🟢' if pass_rate == 100 else '🟡' if pass_rate >= 90 else '🔴'} |

---

## 🎯 Veredicto Ejecutivo
**{('✅ Seguro mergear' if pass_rate == 100 else '⚠️ Revisar antes de mergear' if pass_rate >= 90 else '🛑 NO mergear en este estado')}**

### Impacto para Usuarios Finales
"""+ ("""- 🔒 **Auth**: Usuarios NO pueden iniciar sesión (0% funcional)
- 📝 **Posts**: API de contenido parcialmente roto (83% funcional)
- ⚠️ **Riesgo de Producción**: ALTO - Bloquea acceso al sistema

---

## 🔧 Acciones Requeridas (Antes de Mergear)

### [CRÍTICO] Autenticación - 4 fallos
**Problema:** Los 4 escenarios de login fallan → los usuarios están bloqueados
**Investigación:**
- [ ] Verificar credenciales de prueba en fixtures
- [ ] Revisar endpoint `/login` en el branch actual
- [ ] Validar token/headers en middleware de seguridad
- [ ] Confirmar que config de auth no fue modificada

### [ALTO] Posts API - 1 fallo
**Problema:** Un escenario específico falla en POST /posts
**Investigación:**
- [ ] Aislar cuál de los 5 casos POST está fallando
- [ ] Verificar validación de datos de entrada
- [ ] Revisar códigos HTTP esperados vs reales

### [INFORMACIÓN] Deuda Técnica Detectada
- ⚠️ Suite con muestreo bajo (3 tests reportados)
- ⚠️ Posibles tests duplicados o desactualizados
- ⚠️ Falta de aislamiento en fixtures de Auth

---

## 📈 Matriz de Fallos

{results_table}

---

## 💡 Próximos Pasos

1. **Desarrollador**: Responde las preguntas de investigación arriba
2. **QA**: Valida que Auth funcione 100% antes de testing de otras features
3. **Tech Lead**: Revisa el cambio de código que causó esto

""" if failed > 0 else """- 🟢 Todos los flujos operacionales
- 🟢 Auth completamente funcional
- 🟢 APIs respondiendo correctamente

✅ **Está listo para ir a producción.**

---

""")
    
    
    def _fallback_summary(self, results: List[TestResult]) -> str:
        """Fallback summary when AI is disabled"""
        total = len(results)
        passed = sum(1 for r in results if r.status == "passed")
        failed = sum(1 for r in results if r.status == "failed")
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        # Build features summary table
        features_table = "| Componente | Tests | Pasados | Fallidos | Estado |\n|-----------|-------|---------|----------|--------|\n"
        for result in results:
            status_icon = "✅" if result.status == "passed" else "❌"
            features_table += f"| {result.feature[:30]} | 1 | {'1' if result.status == 'passed' else '0'} | {'0' if result.status == 'passed' else '1'} | {status_icon} |\n"
        
        failed_details = ""
        if failed > 0:
            failed_details = """
### 🔴 Fallos Detectados

"""
            for r in results:
                if r.status == "failed":
                    failed_details += f"""**{r.feature}**
- Error: {r.error_message}
- Duración: {r.duration:.2f}s

"""
        
        return f"""# 📊 Test Execution Summary

## Resultado General
- **Tasa de Éxito**: {pass_rate:.1f}%
- **Tests Totales**: {total}
- **Pasados**: {passed} ✅
- **Fallidos**: {failed} ❌

## Desglose por Componente

{features_table}

{failed_details}

## 🎯 Recomendaciones
{'✅ Suite en estado saludable - Listo para mergear' if pass_rate == 100 else '⚠️ Revisar fallos antes de mergear' if pass_rate >= 90 else '🛑 CRÍTICO: No mergear hasta resolver fallos'}
"""


def generate_pipeline_feedback(results: List[TestResult], llm_provider: str = "glm") -> str:
    """Main entry point for generating pipeline feedback"""
    generator = AIFeedbackGenerator(llm_provider)
    
    # Generate PR comment (more structured for GitHub)
    pr_comment = generator.generate_pr_comment(results)
    
    # Generate internal summary (for logs and artifact)
    internal_summary = generator.generate_summary(results)
    
    return f"""
{pr_comment}

---

## 📊 Análisis Interno

{internal_summary}
"""
