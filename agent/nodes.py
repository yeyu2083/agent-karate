# nodes.py
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
    
    try:
        llm = get_llm(settings)
        
        # Preparar los resultados de las pruebas para el LLM
        total_tests = len(state.get('karate_results', []))
        passed_tests = sum(1 for result in state.get('karate_results', []) if result.status == "passed")
        failed_tests = total_tests - passed_tests
        
        # Crear un resumen de los resultados
        results_summary = f"""
        Total de pruebas: {total_tests}
        Pruebas exitosas: {passed_tests}
        Pruebas fallidas: {failed_tests}
        
        Detalles de las pruebas fallidas:
        """
        
        # Agregar detalles de las pruebas fallidas
        for result in state.get('karate_results', []):
            if result.status == "failed":
                results_summary += f"""
                - Feature: {result.feature}
                - Scenario: {result.scenario}
                - Error: {result.error_message or 'No error message provided'}
                """
        
        # Prompt mejorado para el LLM
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un analista de QA especializado en pruebas de automatización con Karate.
            Analiza los siguientes resultados de pruebas y proporciona un resumen detallado que incluya:
            1. Un resumen ejecutivo de los resultados
            2. Las principales causas de los fallos (si hay alguna)
            3. Recomendaciones para mejorar los resultados
            4. Una evaluación de la calidad general del código de pruebas
            
            Usa un tono profesional y estructurado suitable para un informe técnico."""),
            ("human", "{results}")
        ])
        
        chain = prompt | llm
        response = chain.invoke({"results": results_summary})
        state["final_output"] = response.content
    except Exception as e:
        print(f"LLM error (using direct results): {e}")
        # Fallback a un resumen simple si el LLM falla
        total_tests = len(state.get('karate_results', []))
        passed_tests = sum(1 for result in state.get('karate_results', []) if result.status == "passed")
        failed_tests = total_tests - passed_tests
        
        state["final_output"] = f"""
        Test Results Summary:
        - Total tests: {total_tests}
        - Passed: {passed_tests}
        - Failed: {failed_tests}
        
        Note: Detailed analysis unavailable due to LLM error: {str(e)}
        """
    
    state["current_step"] = "analysis_complete"
    return state


def map_to_xray_node(state: AgentState) -> AgentState:
    settings = JiraXraySettings()
    client = JiraXrayClient(settings)
    
    # Get parent issue key from environment (extracted from branch name)
    parent_issue_key = os.getenv("JIRA_PARENT_ISSUE", "").strip()
    
    try:
        print(f"\n🏗️ Building X-Ray Test Hierarchy")
        if parent_issue_key:
            print(f"   Parent US: {parent_issue_key}")
        
        # STEP 1: Create Test Plan (if we have a parent)
        test_plan_key = None
        if parent_issue_key:
            test_plan_key = client.create_test_plan(f"Test Plan for {parent_issue_key}")
            if test_plan_key:
                print(f"   ✅ Created Test Plan: {test_plan_key}")
                # Link Test Plan to parent US
                client.link_test_plan_to_parent(test_plan_key, parent_issue_key)
        
        # STEP 2: Create individual test issues
        print(f"\n📋 Creating Test Issues")
        tests = []
        test_keys = []
        
        for result in state.get('karate_results', []):
            test_key = client.get_or_create_test_issue(
                result.feature, 
                result.scenario, 
                None,
                steps=result.steps
            )
            
            if test_key:
                test_keys.append(test_key)
                tests.append({
                    "testKey": test_key,
                    "status": "PASS" if result.status == "passed" else "FAIL",
                    "comment": result.error_message or "Test executed successfully",
                    "start": str(int(result.duration * 1000))
                })
        
        print(f"   ✅ Created {len(test_keys)} test issues: {', '.join(test_keys)}")
        
        # STEP 3: Create Test Execution container
        test_execution_key = None
        if parent_issue_key or test_plan_key:
            test_execution_key = client.create_test_execution(parent_issue_key, test_plan_key)
            if test_execution_key:
                print(f"   ✅ Created Test Execution: {test_execution_key}")
                
                # Link all tests to the test execution container
                for test_key in test_keys:
                    client.link_test_to_execution(test_execution_key, test_key)
                
                # STEP 4: Link Test Execution to parent issue (US)
                if parent_issue_key:
                    client.link_test_execution_to_parent(test_execution_key, parent_issue_key)
                
                # STEP 5: Link Test Execution to Test Plan
                if test_plan_key:
                    client.link_execution_to_test_plan(test_execution_key, test_plan_key)
        
        # Prepare payload
        payload = {
            "tests": tests,
            "parent_issue": parent_issue_key or "None",
            "test_plan": test_plan_key or "None",
            "test_execution": test_execution_key or "None"
        }
        
        state["xray_import_payload"] = payload
        state["current_step"] = "mapped_to_xray"
        state["parent_issue"] = parent_issue_key or "None"
        state["test_execution"] = test_execution_key or "None"
        
        # Print hierarchy
        print(f"\n✅ Test Hierarchy Structure:")
        if parent_issue_key:
            print(f"   {parent_issue_key} (US/Historia)")
            if test_plan_key:
                print(f"   ├─ is tested by: {test_plan_key} (Test Plan)")
            if test_execution_key:
                print(f"   ├─ is tested by: {test_execution_key} (Test Execution)")
                for test_key in test_keys:
                    print(f"   │  ├─ {test_key} (Test)")
                if test_plan_key:
                    print(f"   └─ {test_plan_key} (Test Plan)")
                    print(f"      ├─ contains: {test_execution_key} (Test Execution)")
                    for test_key in test_keys:
                        print(f"      │  ├─ {test_key} (Test)")
        else:
            if test_execution_key:
                print(f"   {test_execution_key} (Test Execution)")
                for test_key in test_keys:
                    print(f"   ├─ {test_key} (Test)")
        
        # STEP 6: Transition Historia de Usuario if all tests pass
        if parent_issue_key:
            all_passed = all(r.status == "passed" for r in state.get('karate_results', []))
            if all_passed:
                print(f"\n🌟 All tests passed! Transitioning {parent_issue_key} to Done...")
                if not client.transition_issue(parent_issue_key, "Done"):
                    if not client.transition_issue(parent_issue_key, "Finalizado"):
                        client.transition_issue(parent_issue_key, "Tested")
            else:
                failed_count = sum(1 for r in state.get('karate_results', []) if r.status != "passed")
                print(f"⚠️ {failed_count} test(s) failed. Not transitioning {parent_issue_key}.")

    except Exception as e:
        print(f"❌ Error creating tests: {e}")
        state["current_step"] = "test_creation_error"
        state["error_message"] = str(e)
    
    return state


def upload_to_jira_node(state: AgentState) -> AgentState:
    """Note: Tests are already created and linked in map_to_xray_node. This is a no-op."""
    state["current_step"] = "completed"
    state["jira_response"] = {"status": "success", "message": "Tests already linked in map_to_xray_node"}
    return state