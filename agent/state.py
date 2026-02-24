from typing import TypedDict, List, Any, Optional
from pydantic import BaseModel, Field


class TestResult(BaseModel):
    feature: str
    scenario: str
    status: str
    duration: float
    error_message: Optional[str] = None
    steps: List[dict] = Field(default_factory=list)
    gherkin_steps: List[str] = Field(default_factory=list)  # Pasos del .feature (Given/When/Then)
    background_steps: List[str] = Field(default_factory=list)  # Pasos del Background
    prerequisites: List[str] = Field(default_factory=list)  # Precondiciones extraídas del Background
    expected_assertions: List[str] = Field(default_factory=list)  # Match statements (Then/And match)
    examples: List[dict] = Field(default_factory=list)  # Datos de Examples si es Scenario Outline
    tags: List[str] = Field(default_factory=list)  # Tags del scenario (@tag1, @tag2)
    example_index: int = -1  # Index del ejemplo si es Scenario Outline (-1 si no)


class TestRailRunState(TypedDict):
    """TestRail run execution state"""
    run_id: Optional[int]
    case_id_map: dict  # {automation_id: case_id}
    results_submitted: int
    errors: List[str]


class AgentState(TypedDict):
    # === Karate/Test Results ===
    karate_results: List[TestResult]
    
    # === TestRail Integration ===
    testrail_run: Optional[TestRailRunState]
    testrail_sync_status: str  # "PENDING", "IN_PROGRESS", "SUCCESS", "FAILED"
    testrail_report: Optional[str]
    testrail_error: Optional[str]
    
    # === Workflow State ===
    final_output: str
    current_step: str
