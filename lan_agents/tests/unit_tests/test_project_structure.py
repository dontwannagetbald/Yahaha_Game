from pathlib import Path


def test_agent_graphs_are_split_into_subgraph_directories() -> None:
    src = Path(__file__).resolve().parents[2] / "src" / "agent"

    assert (src / "conversation_graph" / "graph.py").is_file()
    assert (src / "conversation_graph" / "routes" / "route_user_event" / "node.py").is_file()
    assert (src / "conversation_graph" / "events" / "user_event.py").is_file()
    assert (src / "generation_graph" / "graph.py").is_file()
    assert (src / "revision_graph" / "graph.py").is_file()
    assert (src / "revision_graph" / "routes" / "route_revision_intent" / "node.py").is_file()


def test_conversation_nodes_are_split_one_node_per_directory() -> None:
    nodes = Path(__file__).resolve().parents[2] / "src" / "agent" / "conversation_graph" / "nodes"
    expected_nodes = [
        "ingest_user_event",
        "update_requirements",
        "update_material_usage",
        "generate_or_refine_plan",
        "regenerate_plan",
        "lock_confirmation",
        "build_user_response",
        "build_error_response",
    ]

    for node_name in expected_nodes:
        assert (nodes / node_name / "node.py").is_file()


def test_revision_nodes_are_split_one_node_per_directory() -> None:
    nodes = Path(__file__).resolve().parents[2] / "src" / "agent" / "revision_graph" / "nodes"
    expected_nodes = [
        "load_revision_context",
        "understand_revision_intent",
        "ask_clarifying_question",
        "build_revision_patch",
        "create_revision_job_payload",
    ]

    for node_name in expected_nodes:
        assert (nodes / node_name / "node.py").is_file()
