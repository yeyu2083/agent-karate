from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatZhipuAI
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from .state import AgentState
from .tools import JiraXrayClient, JiraXraySettings
import os


def get_llm(settings: JiraXraySettings):
    provider = settings.llm_provider.lower()
    
    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY not set")
        return ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.openai_model
        )
    
    elif provider == "azure":
        if not settings.azure_openai_api_key:
            raise ValueError("AZURE_OPENAI_API_KEY not set")
        return AzureChatOpenAI(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version=settings.azure_openai_api_version,
            deployment_name=settings.azure_openai_deployment_name
        )
    
    elif provider == "anthropic":
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        return ChatAnthropic(
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_model or "claude-3-opus-20240229"
        )

    elif provider == "google":
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY not set")
        return ChatGoogleGenerativeAI(
            api_key=settings.google_api_key,
            model=settings.google_model
        )

    elif provider in ["zhipu", "glm", "zai"]:
        if not settings.zai_api_key:
            raise ValueError("ZAI_API_KEY not set")
        return ChatZhipuAI(
            api_key=settings.zai_api_key,
            model=settings.zai_model
        )

    elif provider == "ollama":
        return Ollama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model
        )
    
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


def analyze_results_node(state: AgentState) -> AgentState:
    settings = JiraXraySettings()
    llm = get_llm(settings)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a QA analyst. Analyze these test results and provide a summary."),
        ("human", "{results}")
    ])
    
    results_text = "\n".join([
        f"- Feature: {r.feature}, Scenario: {r.scenario}, Status: {r.status}, Duration: {r.duration:.2f}s"
        for r in state.get('karate_results', [])
    ])
    
    if not results_text:
        results_text = "No test results available"
    
    try:
        chain = prompt | llm
        response = chain.invoke({"results": results_text})
        state["final_output"] = response.content
    except Exception as e:
        print(f"LLM error (using direct results): {e}")
        state["final_output"] = f"Test Results Summary:\n{results_text}"
    
    state["current_step"] = "analysis_complete"
    return state


def map_to_xray_node(state: AgentState) -> AgentState:
    settings = JiraXraySettings()
    client = JiraXrayClient(settings)
    
    # Get parent issue key from environment (dynamically extracted from branch)
    parent_issue_key = os.getenv("JIRA_PARENT_ISSUE", "").strip()
    
    # Crear Test Execution
    test_execution_key = client.create_test_execution(parent_issue_key)
    
    tests = []
    for result in state.get('karate_results', []):
        test_key = client.get_or_create_test_issue(result.feature, result.scenario, parent_issue_key)
        if test_key:
            tests.append({
                "testKey": test_key,
                "status": "PASS" if result.status == "passed" else "FAIL",
                "comment": result.error_message or "Test executed successfully",
                "start": str(int(result.duration * 1000))
            })
    
    payload = {
        "testExecutionKey": test_execution_key,
        "tests": tests
    }
    
    state["xray_import_payload"] = payload
    state["current_step"] = "mapped_to_xray"
    state["parent_issue"] = parent_issue_key or "None"
    state["test_execution"] = test_execution_key or "None"
    return state


def upload_to_jira_node(state: AgentState) -> AgentState:
    settings = JiraXraySettings()
    client = JiraXrayClient(settings)
    
    payload = state.get("xray_import_payload")
    if payload:
        response = client.import_execution_to_xray(payload)
        state["jira_response"] = response
        state["current_step"] = "uploaded_to_jira"
    
    return state
