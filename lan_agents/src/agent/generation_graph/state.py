"""State contract for the second-stage generation graph."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GenerationState:
    """Confirmed generation job state shared by all stage-B agents."""

    job_context: dict[str, Any] = field(default_factory=dict)
    user_requirements: dict[str, Any] = field(default_factory=dict)
    game_plan: dict[str, Any] = field(default_factory=dict)
    material_usage: dict[str, Any] = field(default_factory=lambda: {"assets": []})
    uploaded_assets: list[dict[str, Any]] = field(default_factory=list)
    asset_registry: list[dict[str, Any]] = field(default_factory=list)
    artifact_workspace: str = ""
    development_brief: dict[str, Any] = field(default_factory=dict)
    asset_work_order: dict[str, Any] = field(default_factory=dict)
    asset_manifest_plan: list[dict[str, Any]] = field(default_factory=list)
    coding_agent_brief: dict[str, Any] = field(default_factory=dict)
    asset_agent_brief: dict[str, Any] = field(default_factory=dict)
    game_spec: dict[str, Any] = field(default_factory=dict)
    code_artifacts: dict[str, Any] = field(default_factory=dict)
    manifest_draft: dict[str, Any] = field(default_factory=dict)
    processed_assets: list[dict[str, Any]] = field(default_factory=list)
    asset_analysis: list[dict[str, Any]] = field(default_factory=list)
    integrated_bundle_context: dict[str, Any] = field(default_factory=dict)
    debug_report: dict[str, Any] = field(default_factory=dict)
    validation_report: dict[str, Any] = field(default_factory=dict)
    coding_repair_attempt_count: int = 0
    artifact_result: dict[str, Any] = field(default_factory=dict)
    draft_game_meta: dict[str, Any] = field(default_factory=dict)
    status: str = ""
    generation_status: str = "planning"
    agent_logs: list[dict[str, Any]] = field(default_factory=list)
    failed_step: str = ""
    error_message: str = ""
    retry_hint: str = ""
