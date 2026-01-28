# graph.py
"""
LangGraph workflow for TestRail integration
Note: Graph structure kept for future extensibility with AI feedback
"""
from langgraph.graph import StateGraph, END
from .state import AgentState


def create_agent_graph():
    """Create workflow graph (currently linear, can be extended for AI analysis)"""
    workflow = StateGraph(AgentState)
    
    # Currently using direct main.py flow, but graph structure available for future AI nodes
    # Future enhancements:
    # - workflow.add_node("analyze_results_with_ai", analyze_ai_node)
    # - workflow.add_node("feedback_generation", feedback_node)
    
    workflow.set_entry_point("finalize")
    workflow.add_node("finalize", lambda x: x)
    workflow.add_edge("finalize", END)
    
    return workflow.compile()