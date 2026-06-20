from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Union
from uuid import UUID


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class UploadedAssetPayload:
    asset_id: UUID
    filename: str
    mime_type: str
    size_bytes: int
    object_key: str
    purpose: Optional[str] = None


@dataclass(frozen=True)
class AgentRunInput:
    job_id: UUID
    user_id: UUID
    prompt: str
    confirmation: Dict[str, Any]
    uploaded_assets: Sequence[UploadedAssetPayload] = field(default_factory=list)


@dataclass(frozen=True)
class AgentLogEvent:
    step: str
    level: str
    message: str
    created_at: datetime = field(default_factory=_now)


@dataclass(frozen=True)
class AgentRunSuccess:
    status: str = "succeeded"
    title: str = "Untitled Game"
    description: str = ""
    tags: List[str] = field(default_factory=list)
    cover_url: Optional[str] = None
    artifact_prefix: str = ""
    manifest_url: str = ""
    artifact_base_url: str = ""
    result_summary: Optional[str] = None
    logs: List[AgentLogEvent] = field(default_factory=list)


@dataclass(frozen=True)
class AgentRunFailure:
    status: str = "failed"
    error_message: str = "Generation failed"
    retry_hint: Optional[str] = None
    failed_step: Optional[str] = None
    logs: List[AgentLogEvent] = field(default_factory=list)


AgentRunResult = Union[AgentRunSuccess, AgentRunFailure]


class FakeAgentRunner:
    def __init__(self, result: Optional[AgentRunResult] = None) -> None:
        self._result = result or AgentRunSuccess(
            title="Mock Game",
            description="Mock generated game",
            tags=["mock"],
            artifact_prefix="drafts/mock-user/mock-job/v1",
            manifest_url="https://draft.local/drafts/mock-user/mock-job/v1/manifest.json",
            artifact_base_url="https://draft.local/drafts/mock-user/mock-job/v1/",
            result_summary="Mock generation completed",
            logs=[
                AgentLogEvent(step="start", level="info", message="Generation started"),
                AgentLogEvent(step="finish", level="info", message="Generation completed"),
            ],
        )

    async def run(self, payload: AgentRunInput) -> AgentRunResult:
        return self._result


_agent_runner: FakeAgentRunner = FakeAgentRunner()


def get_agent_runner() -> FakeAgentRunner:
    return _agent_runner


def set_agent_runner(runner: FakeAgentRunner) -> None:
    global _agent_runner
    _agent_runner = runner


def reset_agent_runner() -> None:
    global _agent_runner
    _agent_runner = FakeAgentRunner()
