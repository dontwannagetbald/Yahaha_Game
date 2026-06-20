from __future__ import annotations

from pathlib import Path

try:
    from langgraph.graph import END, START, StateGraph  # type: ignore
except ImportError:  # pragma: no cover
    from app.graph.compat import END, START, StateGraph

from app.agents.asset_agent import analyze_assets
from app.agents.developer_agent import generate_bundle
from app.agents.spec_builder import build_game_spec
from app.agents.validator_agent import validate_bundle


def _asset_node(state: dict[str, object]) -> dict[str, object]:
    state["asset_analysis"] = analyze_assets(list(state.get("uploaded_assets", [])))
    return state


def _spec_node(state: dict[str, object]) -> dict[str, object]:
    state["game_spec"] = build_game_spec(state, list(state.get("asset_analysis", [])))
    return state


def _developer_node(state: dict[str, object]) -> dict[str, object]:
    output_dir = Path(str(state["output_dir"]))
    state["artifact"] = generate_bundle(state["game_spec"], output_dir=output_dir)
    return state


def _validator_node(state: dict[str, object]) -> dict[str, object]:
    artifact = dict(state["artifact"])
    state["validation"] = validate_bundle(
        bundle_dir=Path(str(artifact["artifact_prefix"])),
        manifest_path=Path(str(artifact["manifest_path"])),
    )
    return state


def build_generation_graph():
    graph = StateGraph(dict)
    graph.add_node("analyze_assets", _asset_node)
    graph.add_node("build_game_spec", _spec_node)
    graph.add_node("generate_bundle", _developer_node)
    graph.add_node("validate_bundle", _validator_node)
    graph.add_edge(START, "analyze_assets")
    graph.add_edge("analyze_assets", "build_game_spec")
    graph.add_edge("build_game_spec", "generate_bundle")
    graph.add_edge("generate_bundle", "validate_bundle")
    graph.add_edge("validate_bundle", END)
    return graph.compile()


def run_generation(
    payload: dict[str, object],
    output_dir: Path,
    config: dict[str, object] | None = None,
) -> dict[str, object]:
    state = dict(payload)
    state["output_dir"] = str(output_dir)
    return build_generation_graph().invoke(state, config=config)
