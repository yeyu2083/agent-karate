from typing import TypedDict, List, Any, Optional
from pydantic import BaseModel, Field


class TestResult(BaseModel):
    feature: str
    scenario: str
    status: str
    duration: float
    error_message: Optional[str] = None
    steps: List[dict] = Field(default_factory=list)


class TestRailRunState(TypedDict):
    """TestRail run execution state"""
    run_id: Optional[int]
    case_id_map: dict  # {automation_id: case_id}
    results_submitted: int
    errors: List[str]


class AgentState(TypedDict):
    # === Karate/Test Results ===
    karate_results: List[TestResult]
    
    # === Jira Integration (Legacy/Optional) ===
    jira_ticket_id: Optional[str]
    jira_response: Optional[dict]
    parent_issue: Optional[str]
    
    # === TestRail Integration (NEW) ===
    testrail_run: Optional[TestRailRunState]
    testrail_sync_status: str  # "PENDING", "IN_PROGRESS", "SUCCESS", "FAILED"
    testrail_report: Optional[str]
    testrail_error: Optional[str]
    
    # === Workflow State ===
    xray_import_payload: Optional[dict]  # Legacy
    final_output: str
    current_step: str
    test_plan: Optional[str]  # Legacy
    test_execution: Optional[str]  # Legacy
