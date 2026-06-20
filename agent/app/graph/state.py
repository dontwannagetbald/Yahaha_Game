from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

@dataclass
class UploadedAsset:
    asset_id: str
    filename: str
    mime_type: str
    size_bytes: int
    object_key: str


@dataclass
class ConfirmationCard:
    title: str
    short_description: str
    game_type: str
    core_gameplay: str
    win_lose_condition: str
    controls: str
    assets_used: str
    cover_suggestion: str
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StructuredDesignState:
    intent_summary: str
    visual_style: str
    win_condition: str
    lose_condition: str
    player_role: str
    core_loop: list[str] = field(default_factory=list)
    controls_detail: list[str] = field(default_factory=list)
    asset_intent: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AgentLog:
    step: str
    agent: str
    level: str
    message: str


@dataclass
class GenerationArtifact:
    artifact_prefix: str
    manifest_path: str
    entry_path: str
    files: list[str]


@dataclass
class ValidationReport:
    valid: bool
    failed_step: str | None = None
    issues: list[dict[str, Any]] = field(default_factory=list)
    error_message: str | None = None
    retry_hint: str | None = None
