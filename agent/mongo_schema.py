#!/usr/bin/env python3
"""
MongoDB Schema & Models for Test Execution History
Almacena histórico de ejecuciones, resultados, feedback de IA y tendencias
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class StatusEnum(str, Enum):
    """Estados posibles de un test"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class RiskLevelEnum(str, Enum):
    """Niveles de riesgo determinados por IA"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    CRITICAL = "CRITICAL"


class TestExecutionStep(BaseModel):
    """Paso individual dentro de un test"""
    step_type: str  # "Given", "When", "Then", "And"
    text: str
    status: StatusEnum
    duration_ms: Optional[float] = None
    assertion: Optional[str] = None


class TestResultDocument(BaseModel):
    """📊 Documento principal: Resultado de un test individual"""
    
    # === Identificadores ===
    test_id: str = Field(..., description="Ej: API de Posts - Pruebas de Publicaciones.Obtener posts por ID")
    execution_id: str = Field(..., description="UUID única de esta ejecución")
    
    # === Metadata de Ejecución ===
    run_date: datetime = Field(default_factory=datetime.utcnow)
    branch: str = Field(..., description="Ej: feature/validaciones")
    pr_number: Optional[int] = None
    commit_sha: str
    github_actor: Optional[str] = None
    
    # === Test Básico ===
    feature: str = Field(..., description="Feature del Karate")
    scenario: str = Field(..., description="Nombre del Scenario")
    tags: List[str] = Field(default_factory=list, description="[@smoke, @regression, @critical]")
    
    # === Resultado ===
    status: StatusEnum
    duration_ms: float
    pass_rate: float = Field(..., ge=0, le=100, description="Porcentaje de assertions que pasaron")
    
    # === Error Details ===
    error_message: Optional[str] = None
    error_type: Optional[str] = None  # "AssertionError", "TimeoutError", etc
    stack_trace: Optional[str] = None
    
    # === Steps Detallados ===
    gherkin_steps: List[str] = Field(default_factory=list, description="Pasos del .feature")
    background_steps: List[str] = Field(default_factory=list, description="Pasos del Background")
    prerequisites: List[str] = Field(default_factory=list)
    expected_assertions: List[str] = Field(default_factory=list, description="Match statements")
    test_steps_detail: List[TestExecutionStep] = Field(default_factory=list, description="Desglose de cada paso")
    
    # === Metrics ===
    assertions_total: int
    assertions_passed: int
    assertions_failed: int
    
    # === Examples (Scenario Outline) ===
    is_scenario_outline: bool = False
    example_data: Optional[Dict[str, Any]] = None
    example_index: Optional[int] = None
    
    # === TestRail Integration ===
    testrail_case_id: Optional[int] = None
    testrail_case_title: Optional[str] = None
    
    # === IA Feedback (Generado después) ===
    ai_risk_level: Optional[RiskLevelEnum] = None
    ai_root_cause: Optional[str] = Field(None, description="Diagnóstico de IA sobre qué falló")
    ai_user_impact: Optional[str] = Field(None, description="Qué significa esto para el usuario final")
    ai_recommended_action: Optional[str] = Field(None, description="Qué hacer al respecto")
    
    class Config:
        json_schema_extra = {
            "example": {
                "test_id": "API Posts.Get by ID",
                "execution_id": "exec-2026-01-30-001",
                "run_date": "2026-01-30T15:30:00Z",
                "branch": "feature/posts-api",
                "pr_number": 60,
                "commit_sha": "abc123def456",
                "feature": "API de Posts",
                "scenario": "Obtener posts por ID",
                "tags": ["@smoke", "@critical"],
                "status": "passed",
                "duration_ms": 245.5,
                "pass_rate": 100.0,
                "assertions_total": 5,
                "assertions_passed": 5,
                "assertions_failed": 0,
                "testrail_case_id": 362
            }
        }


class ExecutionSummaryDocument(BaseModel):
    """📈 Documento agregado: Resumen de una ejecución completa (todos los tests)"""
    
    # === Identificadores ===
    execution_batch_id: str = Field(..., description="UUID para agrupar múltiples tests")
    
    # === Metadata ===
    run_date: datetime = Field(default_factory=datetime.utcnow)
    branch: str
    pr_number: Optional[int] = None
    commit_sha: str
    github_actor: Optional[str] = None
    
    # === Agregados Globales ===
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    overall_pass_rate: float = Field(..., ge=0, le=100)
    total_duration_ms: float
    
    # === Riesgos Detectados ===
    overall_risk_level: RiskLevelEnum
    failed_features: List[str] = Field(default_factory=list, description="Features con fallos")
    flaky_tests: List[str] = Field(default_factory=list, description="Tests que fallan ocasionalmente")
    
    # === Análisis Agregado de IA ===
    ai_pr_comment: Optional[str] = Field(None, description="Comentario generado para el PR en GitHub")
    ai_technical_summary: Optional[str] = Field(None, description="Análisis técnico interno")
    ai_blockers: List[str] = Field(default_factory=list, description="Problemas críticos bloqueantes")
    ai_recommendations: List[str] = Field(default_factory=list, description="Acciones recomendadas")
    
    # === TestRail Integration ===
    testrail_run_id: Optional[int] = None
    testrail_cases_synced: int = 0
    
    # === Referencia a Resultados Individuales ===
    test_result_ids: List[str] = Field(default_factory=list, description="IDs de TestResultDocument relacionados")
    
    class Config:
        json_schema_extra = {
            "example": {
                "execution_batch_id": "batch-2026-01-30-60",
                "run_date": "2026-01-30T15:45:00Z",
                "branch": "feature/posts-api",
                "pr_number": 60,
                "total_tests": 12,
                "passed_tests": 11,
                "failed_tests": 1,
                "overall_pass_rate": 91.67,
                "overall_risk_level": "MEDIUM",
                "testrail_run_id": 42
            }
        }


class TestTrendDocument(BaseModel):
    """📊 Documento para tendencias: Seguimiento de salud a lo largo del tiempo"""
    
    # === Periodo ===
    feature: str
    scenario: str
    date_start: datetime
    date_end: datetime
    
    # === Tendencias ===
    executions_count: int
    pass_rate_avg: float
    pass_rate_min: float
    pass_rate_max: float
    pass_rate_trend: str = Field(..., description="'UP', 'DOWN', 'STABLE'")
    
    # === Flakiness ===
    flakiness_score: float = Field(..., ge=0, le=1, description="0 = siempre pasa, 1 = siempre falla")
    failure_count: int
    
    # === Tags más frecuentes ===
    common_tags: Dict[str, int]
    
    # === Error Pattern ===
    most_common_error: Optional[str] = None
    error_frequency: Optional[int] = None


class AIFeedbackDocument(BaseModel):
    """🤖 Documento especializado: Feedback de IA reutilizable"""
    
    # === Identificadores ===
    feedback_id: str
    execution_batch_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # === Contexto ===
    feature: str
    failed_tests: List[str]
    
    # === Análisis ===
    root_causes: List[str] = Field(description="Causas raíz identificadas por IA")
    affected_systems: List[str] = Field(description="Sistemas afectados")
    user_impact_description: str
    
    # === Acciones ===
    recommended_priority: str = Field(..., description="'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'")
    recommended_actions: List[Dict[str, str]] = Field(description="[{'action': '...', 'owner': '...', 'priority': '...'}]")
    
    # === Contexto de Negocio ===
    business_impact: Optional[str] = None
    

# ============================================================================
# ÍNDICES RECOMENDADOS PARA MONGODB
# ============================================================================
"""
db.test_results.createIndex({ "execution_id": 1 })
db.test_results.createIndex({ "branch": 1, "run_date": -1 })
db.test_results.createIndex({ "feature": 1, "scenario": 1 })
db.test_results.createIndex({ "tags": 1 })
db.test_results.createIndex({ "status": 1 })
db.test_results.createIndex({ "ai_risk_level": 1 })

db.execution_summaries.createIndex({ "pr_number": 1 })
db.execution_summaries.createIndex({ "branch": 1, "run_date": -1 })
db.execution_summaries.createIndex({ "overall_risk_level": 1 })

db.test_trends.createIndex({ "feature": 1, "scenario": 1 })
db.test_trends.createIndex({ "flakiness_score": 1 })

db.ai_feedback.createIndex({ "execution_batch_id": 1 })
db.ai_feedback.createIndex({ "created_at": -1 })
"""


# ============================================================================
# COLECCIONES RECOMENDADAS
# ============================================================================
COLLECTIONS = {
    "test_results": "Resultados individuales de cada test",
    "execution_summaries": "Resúmenes de ejecuciones completas",
    "test_trends": "Tendencias y análisis histórico",
    "ai_feedback": "Feedback de IA reutilizable",
    "flaky_tests_registry": "Registro de tests inestables para tracking",
}
