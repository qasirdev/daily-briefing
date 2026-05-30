"""LangGraph builder for the briefing orchestration pipeline."""

from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from backend.graph.nodes import orchestrator_node
from backend.graph.state import BriefingGraphState


def build_briefing_graph() -> CompiledStateGraph[Any, Any, Any]:
    """Build and compile the minimal MVP1 briefing graph."""
    graph = StateGraph(BriefingGraphState)
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_edge(START, "orchestrator")
    graph.add_edge("orchestrator", END)
    return graph.compile()
