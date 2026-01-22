from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import analyze_results_node, map_to_xray_node, upload_to_jira_node


def create_agent_graph() -> StateGraph:
    graph = StateGraph(AgentState)
    
    graph.add_node("analyze", analyze_results_node)
    graph.add_node("map_to_xray", map_to_xray_node)
    graph.add_node("upload", upload_to_jira_node)
    
    graph.set_entry_point("analyze")
    graph.add_edge("analyze", "map_to_xray")
    graph.add_edge("map_to_xray", "upload")
    graph.add_edge("upload", END)
    
    return graph.compile()
