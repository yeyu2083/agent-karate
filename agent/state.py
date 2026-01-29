from typing import TypedDict, List, Any, Optional
from pydantic import BaseModel, Field

class TestResult(BaseModel):
    feature: str
    scenario: str
    status: str
    duration: float
    error_message: Optional[str] = None
    steps: List[dict] = Field(default_factory=list)
    gherkin_steps: List[str] = Field(default_factory=list)
    background_steps: List[str] = Field(default_factory=list)
    expected_assertions: List[str] = Field(default_factory=list)
    examples: List[dict] = Field(default_factory=list)

class TestRailRunState(TypedDict):
    run_id: Optional[int]
    case_id_map: dict 
    results_submitted: int
    errors: List[str]

class AgentState(TypedDict):
    karate_results: List[TestResult]
    testrail_run: Optional[TestRailRunState]
    testrail_sync_status: str
    testrail_report: Optional[str]
    testrail_error: Optional[str]
    final_output: str
    current_step: str