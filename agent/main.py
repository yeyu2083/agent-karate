import os
import sys
from dotenv import load_dotenv
from .state import AgentState, TestResult
from .karate_parser import KarateParser
from .graph import create_agent_graph
from .tools import JiraXraySettings, JiraXrayClient

load_dotenv()


# agent.py
import os
import sys
from dotenv import load_dotenv
from .state import AgentState, TestResult
from .karate_parser import KarateParser
from .graph import create_agent_graph
from .tools import JiraXraySettings, JiraXrayClient

load_dotenv()


def run_agent(karate_json_path: str = "target/karate-reports/karate-summary.json") -> AgentState:
    initial_state: AgentState = {
        "karate_results": [],
        "jira_ticket_id": None,
        "xray_import_payload": None,
        "jira_response": None,
        "final_output": "",
        "current_step": "initialized"
    }

    print("\n🔍 Verifying Jira Connection...")
    try:
        settings = JiraXraySettings()
        client = JiraXrayClient(settings)
        if not client.check_connection():
            print("⚠️ Skipping agent execution due to Jira connection failure.")
            initial_state["current_step"] = "connection_failed"
            return initial_state
    except Exception as e:
        print(f"❌ Configuration Error: {e}")
        initial_state["current_step"] = "configuration_error"
        return initial_state
    
    if not os.path.exists(karate_json_path):
        print(f"Error: Karate results file not found at {karate_json_path}")
        initial_state["current_step"] = "file_not_found"
        return initial_state
    
    parser = KarateParser()
    results = parser.parse_karate_json(karate_json_path)
    
    if not results:
        print("No test results found in Karate JSON file")
        initial_state["current_step"] = "no_results"
        return initial_state
    
    print(f"Loaded {len(results)} test results from Karate")
    
    initial_state["karate_results"] = results
    
    try:
        graph = create_agent_graph()
        final_state = graph.invoke(initial_state)
        
        print("\n=== Agent Execution Complete ===")
        print(f"Final Output: {final_state.get('final_output', 'No output')}")
        print(f"Jira Response: {final_state.get('jira_response', {})}")
        
        return final_state
    except Exception as e:
        print(f"Error executing agent graph: {e}")
        import traceback
        traceback.print_exc()
        initial_state["final_output"] = f"Error: {str(e)}"
        initial_state["current_step"] = "error"
        return initial_state


if __name__ == "__main__":
    json_path = sys.argv[1] if len(sys.argv) > 1 else "target/karate-reports/karate-summary.json"
    run_agent(json_path)