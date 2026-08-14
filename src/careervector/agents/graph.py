from functools import lru_cache

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from careervector.agents.nodes.gap_analyst_node import gap_analyst_node
from careervector.agents.nodes.parser_node import parser_node
from careervector.agents.nodes.roadmap_synthesizer_node import roadmap_synthesizer_node
from careervector.agents.state import CopilotState


def build_copilot_graph() -> CompiledStateGraph[CopilotState, None, CopilotState, CopilotState]:
    graph: StateGraph[CopilotState, None, CopilotState, CopilotState] = StateGraph(CopilotState)
    graph.add_node("parser", parser_node)
    graph.add_node("gap_analyst", gap_analyst_node)
    graph.add_node("roadmap_synthesizer", roadmap_synthesizer_node)
    graph.set_entry_point("parser")
    graph.add_edge("parser", "gap_analyst")
    graph.add_edge("gap_analyst", "roadmap_synthesizer")
    graph.add_edge("roadmap_synthesizer", END)
    return graph.compile()


@lru_cache
def get_copilot_graph() -> CompiledStateGraph[CopilotState, None, CopilotState, CopilotState]:
    return build_copilot_graph()
