# nodes.py - REFACTORED FOR TESTRAIL
"""
Agent workflow nodes for TestRail integration
"""

from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatZhipuAI
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from .state import AgentState
from .testrail_client import TestRailClient, TestRailSettings
from .testrail_sync import TestRailSync
from .testrail_runner import TestRailRunner
import os


def get_llm(llm_provider: str = "glm"):
    """Get LLM based on provider"""
    provider = llm_provider.lower()
    
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")
        return ChatOpenAI(api_key=api_key, model="gpt-4o")
    
    elif provider == "azure":
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        if not api_key:
            raise ValueError("AZURE_OPENAI_API_KEY not set")
        return AzureChatOpenAI(
            api_key=api_key,
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        )
    
    elif provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        return ChatAnthropic(api_key=api_key, model="claude-3-opus-20240229")

    elif provider == "google":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not set")
        return ChatGoogleGenerativeAI(api_key=api_key, model="gemini-1.5-pro")

    elif provider in ["zhipu", "glm", "zai"]:
        api_key = os.getenv("ZAI_API_KEY")
        if not api_key:
            raise ValueError("ZAI_API_KEY not set")
        return ChatZhipuAI(api_key=api_key, model="GLM-4.7-flash")

    elif provider == "ollama":
        return Ollama(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            model=os.getenv("OLLAMA_MODEL", "llama3")
        )
    
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


def analyze_results_node(state: AgentState) -> AgentState:
    """Analyze test results with LLM (fallback to summary if LLM fails)"""
    llm_provider = os.getenv("LLM_PROVIDER", "glm")
    
    try:
        llm = get_llm(llm_provider)
        
        # Prepare results summary
        total_tests = len(state.get('karate_results', []))
        passed_tests = sum(1 for result in state.get('karate_results', []) if result.status == "passed")
        failed_tests = total_tests - passed_tests
        
        results_summary = f"""
        Total de pruebas: {total_tests}
        Pruebas exitosas: {passed_tests}
        Pruebas fallidas: {failed_tests}
        
        Detalles de las pruebas fallidas:
        """
        
        for result in state.get('karate_results', []):
            if result.status == "failed":
                results_summary += f"""
                - Feature: {result.feature}
                - Scenario: {result.scenario}
                - Error: {result.error_message or 'No error message provided'}
                """
        
        # Call LLM
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un analista de QA especializado en pruebas de automatización con Karate.
            Analiza los siguientes resultados de pruebas y proporciona un resumen detallado."""),
            ("human", "{results}")
        ])
        
        chain = prompt | llm
        response = chain.invoke({"results": results_summary})
        state["final_output"] = response.content
    
    except Exception as e:
        print(f"⚠️ LLM analysis failed: {e}")
        # Fallback to simple summary
        total_tests = len(state.get('karate_results', []))
        passed_tests = sum(1 for result in state.get('karate_results', []) if result.status == "passed")
        failed_tests = total_tests - passed_tests
        
        state["final_output"] = f"""
        Test Results Summary:
        - Total tests: {total_tests}
        - Passed: {passed_tests}
        - Failed: {failed_tests}
        """
    
    state["current_step"] = "analysis_complete"
    return state


def map_to_testrail_node(state: AgentState) -> AgentState:
    """Map test results to TestRail and submit"""
    
    try:
        print(f"\n🏗️ Building TestRail Test Execution")
        
        # Initialize TestRail
        testrail_settings = TestRailSettings()
        testrail_client = TestRailClient(testrail_settings)
        
        # Verify connection
        if not testrail_client.check_connection():
            raise Exception("Cannot connect to TestRail")
        
        # Get metadata from environment
        build_number = os.getenv("BUILD_NUMBER", "unknown")
        branch_name = os.getenv("BRANCH_NAME", "unknown")
        commit_sha = os.getenv("COMMIT_SHA", "")[:7]
        commit_message = os.getenv("COMMIT_MESSAGE", "")
        jira_issue = os.getenv("JIRA_PARENT_ISSUE", "").strip() or None
        
        build_data = {
            'build_number': build_number,
            'branch': branch_name,
            'commit_sha': commit_sha,
            'commit_message': commit_message,
            'jira_issue': jira_issue,
            'environment': 'dev'
        }
        
        test_results = state.get('karate_results', [])
        
        if not test_results:
            print("⚠️ No test results to submit")
            state["current_step"] = "no_results"
            return state
        
        # ===== STEP 1: Sync test cases to TestRail =====
        print(f"\n📋 Syncing test cases to TestRail")
        sync = TestRailSync(
            testrail_client,
            testrail_settings.testrail_project_id,
            testrail_settings.testrail_suite_id
        )
        
        case_id_map = sync.sync_cases_from_karate(test_results)
        
        if not case_id_map:
            raise Exception("Failed to sync test cases")
        
        print(f"✓ Synced {len(case_id_map)} test cases")
        
        # ===== STEP 2: Create TestRail run =====
        print(f"\n🚀 Creating TestRail run")
        runner = TestRailRunner(testrail_client)
        
        case_ids = list(case_id_map.values())
        run_id = runner.create_run_from_build(
            testrail_settings.testrail_project_id,
            testrail_settings.testrail_suite_id,
            build_data,
            case_ids
        )
        
        if not run_id:
            raise Exception("Failed to create TestRail run")
        
        # ===== STEP 3: Submit test results =====
        print(f"\n📊 Submitting test results")
        success = runner.submit_results(run_id, test_results, case_id_map)
        
        if not success:
            raise Exception("Failed to submit results")
        
        # ===== STEP 4: Attach artifact =====
        print(f"\n📎 Attaching artifact")
        karate_json_path = os.getenv("KARATE_JSON_PATH", "karate.json")
        if os.path.exists(karate_json_path):
            runner.attach_artifact(run_id, karate_json_path)
        
        # ===== STEP 5: Generate report =====
        print(f"\n📝 Generating report")
        report = runner.generate_run_report(run_id)
        
        # Print hierarchy
        print(f"\n✅ TestRail Execution Complete:")
        print(f"   Project: API Automation")
        print(f"   Suite: Authentication")
        print(f"   Run: #{run_id}")
        print(f"   Build: #{build_number} - {branch_name}")
        
        if jira_issue:
            print(f"   Jira: {jira_issue}")
        
        # Update state
        state["testrail_run"] = {
            "run_id": run_id,
            "case_id_map": case_id_map,
            "results_submitted": len(case_id_map),
            "errors": []
        }
        state["testrail_sync_status"] = "SUCCESS"
        state["testrail_report"] = report
        state["current_step"] = "mapped_to_testrail"
    
    except Exception as e:
        print(f"❌ Error in TestRail execution: {e}")
        state["testrail_sync_status"] = "FAILED"
        state["testrail_error"] = str(e)
        state["current_step"] = "testrail_error"
    
    return state


def upload_to_jira_node(state: AgentState) -> AgentState:
    """Optional: Link TestRail run to Jira Historia (future enhancement)"""
    state["current_step"] = "completed"
    return state