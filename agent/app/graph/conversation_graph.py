from __future__ import annotations

try:
    from langgraph.graph import END, START, StateGraph  # type: ignore
except ImportError:  # pragma: no cover
    from app.graph.compat import END, START, StateGraph

from app.agents.design_agent import build_design_output


def _build_design_state_node(state: dict[str, object]) -> dict[str, object]:
    confirmation, design_state = build_design_output(
        prompt=str(state["prompt"]),
        uploaded_assets=list(state.get("uploaded_assets", [])),
    )
    state["confirmation_card"] = confirmation
    state["structured_design_state"] = design_state
    return state


def build_conversation_graph():
    graph = StateGraph(dict)
    graph.add_node("build_design_state", _build_design_state_node)
    graph.add_edge(START, "build_design_state")
    graph.add_edge("build_design_state", END)
    return graph.compile()


def run_conversation(payload: dict[str, object], config: dict[str, object] | None = None) -> dict[str, object]:
    return build_conversation_graph().invoke(payload, config=config)
