from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_langgraph_json_points_to_exported_graphs():
    config_path = ROOT / "langgraph.json"
    assert config_path.exists()

    config = json.loads(config_path.read_text(encoding="utf-8"))
    assert config["dependencies"] == ["./my_agent"]
    assert config["env"] == ".env"
    assert config["graphs"]["conversation"].endswith(":conversation_graph")
    assert config["graphs"]["generation"].endswith(":generation_graph")


def test_requirements_txt_contains_langgraph_runtime_dependencies():
    requirements_path = ROOT / "my_agent" / "requirements.txt"
    assert requirements_path.exists()

    requirements = requirements_path.read_text(encoding="utf-8")
    assert "langgraph" in requirements
    assert "langchain-core" in requirements


def test_my_agent_exports_compiled_graphs():
    from my_agent.agent import conversation_graph, generation_graph

    assert hasattr(conversation_graph, "invoke")
    assert hasattr(generation_graph, "invoke")
