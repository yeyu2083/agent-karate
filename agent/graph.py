# graph.py
from langchain.graph import StateGraph, END
from .state import AgentState
from .nodes import analyze_results_node, map_to_xray_node, upload_to_jira_node


def create_agent_graph():
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("analyze_results", analyze_results_node)
    workflow.add_node("map_to_xray", map_to_xray_node)
    workflow.add_node("upload_to_jira", upload_to_jira_node)
    
    # Define the flow
    workflow.set_entry_point("analyze_results")
    workflow.add_edge("analyze_results", "map_to_xray")
    workflow.add_edge("map_to_xray", "upload_to_jira")
    workflow.add_edge("upload_to_jira", END)
    
    return workflow.compile()