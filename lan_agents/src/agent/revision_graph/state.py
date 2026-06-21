"""State contract for the post-generation revision graph."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def default_revision_response() -> dict[str, Any]:
    """Return the empty response projected to the Create revision UI."""
    return {
        "message": "",
        "suggestions": [],
        "actions": [],
    }


@dataclass
class RevisionState:
    """Post-generation revision state shared by revision graph nodes."""

    parent_job: dict[str, Any] = field(default_factory=dict)
    base_game_plan: dict[str, Any] = field(default_factory=dict)
    base_material_usage: dict[str, Any] = field(default_factory=lambda: {"assets": []})
    generated_result: dict[str, Any] = field(default_factory=dict)
    user_message: str = ""
    revision_intent: str = ""
    game_plan_patch: dict[str, Any] = field(default_factory=dict)
    requires_regeneration: bool = False
    revision_job_payload: dict[str, Any] = field(default_factory=dict)
    assistant_response: dict[str, Any] = field(default_factory=default_revision_response)
    revision_status: str = "understanding"
    agent_logs: list[dict[str, Any]] = field(default_factory=list)
    error_message: str = ""
