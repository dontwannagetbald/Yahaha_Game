from dataclasses import asdict
import json
from pathlib import Path

from agent.generation_graph.state import GenerationState


EXPECTED_GENERATION_STATE_FIELDS = {
    "job_context",
    "user_requirements",
    "game_plan",
    "material_usage",
    "uploaded_assets",
    "asset_registry",
    "artifact_workspace",
    "development_brief",
    "asset_work_order",
    "asset_manifest_plan",
    "coding_agent_brief",
    "asset_agent_brief",
    "game_spec",
    "code_artifacts",
    "manifest_draft",
    "processed_assets",
    "asset_analysis",
    "integrated_bundle_context",
    "debug_report",
    "validation_report",
    "coding_repair_attempt_count",
    "artifact_result",
    "draft_game_meta",
    "status",
    "generation_status",
    "agent_logs",
    "failed_step",
    "error_message",
    "retry_hint",
}


def test_generation_state_defaults_match_generation_contract() -> None:
    state = GenerationState()

    payload = asdict(state)

    assert set(payload) == EXPECTED_GENERATION_STATE_FIELDS
    assert payload["generation_status"] == "planning"
    assert payload["status"] == ""
    assert payload["uploaded_assets"] == []
    assert payload["asset_registry"] == []
    assert payload["agent_logs"] == []
    assert payload["artifact_workspace"] == ""
    assert payload["coding_repair_attempt_count"] == 0


def test_generation_state_uses_independent_mutable_defaults() -> None:
    first = GenerationState()
    second = GenerationState()

    first.uploaded_assets.append({"asset_id": "asset-image"})
    first.agent_logs.append({"step": "init_generation_context"})

    assert second.uploaded_assets == []
    assert second.agent_logs == []


def test_generation_confirmed_session_fixture_covers_required_upload_types() -> None:
    fixture_path = (
        Path(__file__).parents[2]
        / "src"
        / "agent"
        / "generation_graph"
        / "fixtures"
        / "generation_confirmed_session.json"
    )

    fixture = json.loads(fixture_path.read_text())
    mime_types = {asset["mime_type"] for asset in fixture["uploaded_assets"]}

    assert any(mime_type.startswith("image/") for mime_type in mime_types)
    assert any(mime_type.startswith("video/") for mime_type in mime_types)
    assert any(mime_type.startswith("audio/") for mime_type in mime_types)
    assert any(mime_type == "application/pdf" for mime_type in mime_types)
    assert all("presigned" not in json.dumps(asset) for asset in fixture["uploaded_assets"])
