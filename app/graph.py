"""Assemble the repair StateGraph and its conditional Router edge."""

from langgraph.graph import END, START, StateGraph

from app.config import settings
from app.nodes.diagnoser import diagnoser
from app.nodes.patch_generator import patch_generator
from app.nodes.test_runner import test_runner
from app.state import AgentState


def route(state: AgentState) -> str:
    """Conditional edge: end on success or when the loop cap is hit, else re-diagnose."""
    if state["is_success"] or state["loop_count"] >= settings.max_loops:
        return END
    return "diagnoser"


def build_graph():
    """Build and compile the Diagnoser → Patch Generator → Test Runner loop."""
    graph = StateGraph(AgentState)
    graph.add_node("diagnoser", diagnoser)
    graph.add_node("patch_generator", patch_generator)
    graph.add_node("test_runner", test_runner)

    graph.add_edge(START, "diagnoser")
    graph.add_edge("diagnoser", "patch_generator")
    graph.add_edge("patch_generator", "test_runner")
    graph.add_conditional_edges("test_runner", route, {"diagnoser": "diagnoser", END: END})

    return graph.compile()
