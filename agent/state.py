from typing import TypedDict, List, Any, Optional
from pydantic import BaseModel, Field


class TestResult(BaseModel):
    feature: str
    scenario: str
    status: str
    duration: float
    error_message: Optional[str] = None


class AgentState(TypedDict):
    karate_results: List[TestResult]
    jira_ticket_id: Optional[str]
    xray_import_payload: Optional[dict]
    jira_response: Optional[dict]
    final_output: str
    current_step: str
