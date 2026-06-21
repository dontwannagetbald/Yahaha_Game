from __future__ import annotations

import inspect
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional, Protocol, Sequence, Union
from uuid import UUID

from app.config import settings


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class UploadedAssetPayload:
    asset_id: UUID
    filename: str
    mime_type: str
    size_bytes: int
    object_key: str
    local_path: str = ""
    purpose: Optional[str] = None


@dataclass(frozen=True)
class AgentRunInput:
    job_id: UUID
    user_id: UUID
    session_id: Optional[UUID]
    prompt: str
    confirmation: Dict[str, Any]
    user_requirements: Dict[str, Any] = field(default_factory=dict)
    game_plan: Dict[str, Any] = field(default_factory=dict)
    material_usage: Dict[str, Any] = field(default_factory=dict)
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
    validation_report: Optional[Dict[str, Any]] = None
    logs: List[AgentLogEvent] = field(default_factory=list)


AgentRunResult = Union[AgentRunSuccess, AgentRunFailure]
AgentLogEmitter = Callable[[AgentLogEvent], Optional[Awaitable[None]]]


class AgentRunner(Protocol):
    async def run(
        self,
        payload: AgentRunInput,
        emit_log: Optional[AgentLogEmitter] = None,
    ) -> AgentRunResult:
        ...


class GenerationGraph(Protocol):
    def astream_events(self, state: dict[str, Any], version: str):
        ...


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

    async def run(
        self,
        payload: AgentRunInput,
        emit_log: Optional[AgentLogEmitter] = None,
    ) -> AgentRunResult:
        return self._result


class LangGraphGenerationRunner:
    """Run the real stage-B LangGraph graph and stream node lifecycle logs."""

    def __init__(self, graph: Optional[GenerationGraph] = None) -> None:
        self._graph = graph

    async def run(
        self,
        payload: AgentRunInput,
        emit_log: Optional[AgentLogEmitter] = None,
    ) -> AgentRunResult:
        graph = self._graph or get_generation_graph()
        graph_state = _state_from_payload(payload)
        final_state: Optional[dict[str, Any]] = None
        active_nodes: list[str] = []
        errored_nodes: set[str] = set()

        try:
            async for event in graph.astream_events(graph_state, version="v2"):
                node_name = _node_name_from_event(event)
                event_name = str(event.get("event") or "")
                if not node_name:
                    if event_name == "on_chain_end":
                        output = (event.get("data") or {}).get("output")
                        if isinstance(output, dict):
                            final_state = output
                    continue

                if event_name == "on_chain_start":
                    active_nodes.append(node_name)
                    await _emit(
                        emit_log,
                        AgentLogEvent(
                            step=node_name,
                            level="info",
                            message=f"{node_name} started",
                        ),
                    )
                elif event_name == "on_chain_end":
                    _discard_last(active_nodes, node_name)
                    output = (event.get("data") or {}).get("output")
                    if isinstance(output, dict):
                        final_state = {**(final_state or {}), **output}
                    await _emit(
                        emit_log,
                        AgentLogEvent(
                            step=node_name,
                            level="info",
                            message=f"{node_name} completed",
                        ),
                    )
                elif event_name == "on_chain_error":
                    _discard_last(active_nodes, node_name)
                    errored_nodes.add(node_name)
                    await _emit(
                        emit_log,
                        AgentLogEvent(
                            step=node_name,
                            level="error",
                            message=f"{node_name} failed: {_event_error_message(event)}",
                        ),
                    )
        except Exception as exc:
            failed_node = active_nodes[-1] if active_nodes else "generation_graph"
            if failed_node not in errored_nodes:
                await _emit(
                    emit_log,
                    AgentLogEvent(
                        step=failed_node,
                        level="error",
                        message=f"{failed_node} failed: {exc}",
                    ),
                )
            raise

        return _result_from_generation_state(final_state or graph_state, payload)


_agent_runner: Optional[AgentRunner] = None


def get_agent_runner() -> AgentRunner:
    global _agent_runner
    if _agent_runner is None:
        _agent_runner = _build_default_agent_runner()
    return _agent_runner


def set_agent_runner(runner: AgentRunner) -> None:
    global _agent_runner
    _agent_runner = runner


def reset_agent_runner() -> None:
    global _agent_runner
    _agent_runner = None


def get_generation_graph() -> GenerationGraph:
    _ensure_lan_agents_on_path()
    from agent.graph import generation_graph

    return generation_graph


def _build_default_agent_runner() -> AgentRunner:
    if settings.agent_runner.lower() == "langgraph":
        return LangGraphGenerationRunner()
    return FakeAgentRunner()


def _ensure_lan_agents_on_path() -> None:
    src_path = Path(settings.lan_agents_src_path)
    if src_path.exists() and str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))


def _state_from_payload(payload: AgentRunInput) -> dict[str, Any]:
    version = "v1"
    return {
        "job_context": {
            "job_id": str(payload.job_id),
            "user_id": str(payload.user_id),
            "session_id": str(payload.session_id) if payload.session_id else None,
            "prompt_summary": payload.prompt,
            "version": version,
        },
        "user_requirements": dict(payload.user_requirements or {}),
        "game_plan": dict(payload.game_plan or payload.confirmation or {}),
        "material_usage": dict(payload.material_usage or {"assets": []}),
        "uploaded_assets": [_asset_to_graph_dict(asset) for asset in payload.uploaded_assets],
        "artifact_workspace": str(
            Path("output") / "drafts" / str(payload.user_id) / str(payload.job_id) / version
        ),
    }


def _asset_to_graph_dict(asset: UploadedAssetPayload) -> dict[str, Any]:
    return {
        "asset_id": str(asset.asset_id),
        "filename": asset.filename,
        "mime_type": asset.mime_type,
        "size_bytes": asset.size_bytes,
        "object_key": asset.object_key,
        "local_path": asset.local_path,
        "purpose": asset.purpose,
    }


def _result_from_generation_state(
    state: dict[str, Any],
    payload: AgentRunInput,
) -> AgentRunResult:
    if state.get("status") == "failed" or state.get("generation_status") == "failed":
        return AgentRunFailure(
            error_message=str(state.get("error_message") or "Generation failed"),
            retry_hint=state.get("retry_hint"),
            failed_step=state.get("failed_step"),
            validation_report=_dict_field(state, "validation_report") or None,
            logs=_logs_from_generation_state(state),
        )

    meta = _dict_field(state, "draft_game_meta")
    artifact = _dict_field(state, "artifact_result")
    game_plan = _dict_field(state, "game_plan") or payload.game_plan
    workspace = str(artifact.get("workspace") or state.get("artifact_workspace") or "")
    manifest_path = str(
        artifact.get("manifest_path")
        or meta.get("manifest_path")
        or "manifest.json"
    )
    cover_path = str(artifact.get("cover_path") or meta.get("cover_path") or "")

    return AgentRunSuccess(
        title=str(meta.get("title") or game_plan.get("title") or "Untitled Game"),
        description=str(
            meta.get("description") or game_plan.get("introduction") or ""
        ),
        tags=[
            str(tag)
            for tag in (meta.get("tags") or game_plan.get("tags") or [])
            if isinstance(tag, str)
        ],
        cover_url=_join_artifact_url(workspace, cover_path) if cover_path else None,
        artifact_prefix=workspace,
        manifest_url=_join_artifact_url(workspace, manifest_path),
        artifact_base_url=_artifact_base_url(workspace),
        result_summary=str(
            state.get("result_summary")
            or state.get("generation_status")
            or "Generation completed"
        ),
        logs=_logs_from_generation_state(state),
    )


def _dict_field(state: dict[str, Any], key: str) -> dict[str, Any]:
    value = state.get(key)
    return value if isinstance(value, dict) else {}


def _logs_from_generation_state(state: dict[str, Any]) -> List[AgentLogEvent]:
    raw_logs = state.get("agent_logs")
    if not isinstance(raw_logs, list):
        return []
    logs: List[AgentLogEvent] = []
    for raw_log in raw_logs:
        if not isinstance(raw_log, dict):
            continue
        step = str(raw_log.get("step") or "").strip()
        message = str(raw_log.get("message") or "").strip()
        if not step or not message:
            continue
        level = str(raw_log.get("level") or "info").strip().lower()
        if level not in {"info", "warning", "error"}:
            level = "info"
        logs.append(AgentLogEvent(step=step, level=level, message=message))
    return logs


def _join_artifact_url(workspace: str, path: str) -> str:
    if not path:
        return workspace
    if path.startswith("http://") or path.startswith("https://"):
        return path
    if workspace and path.startswith(workspace):
        return path
    return "/".join([part.strip("/") for part in [workspace, path] if part])


def _artifact_base_url(workspace: str) -> str:
    return f"{workspace.rstrip('/')}/" if workspace else ""


def _node_name_from_event(event: dict[str, Any]) -> str:
    metadata = event.get("metadata") or {}
    node_name = metadata.get("langgraph_node")
    node_name = str(node_name or "").strip()
    event_name = str(event.get("name") or "").strip()
    if node_name and event_name == node_name:
        return node_name
    return ""


def _event_error_message(event: dict[str, Any]) -> str:
    data = event.get("data") or {}
    error = data.get("error") or data.get("exception") or "unknown error"
    return str(error)


def _discard_last(active_nodes: list[str], node_name: str) -> None:
    for index in range(len(active_nodes) - 1, -1, -1):
        if active_nodes[index] == node_name:
            del active_nodes[index]
            return


async def _emit(
    emit_log: Optional[AgentLogEmitter],
    log: AgentLogEvent,
) -> None:
    if emit_log is None:
        return
    result = emit_log(log)
    if inspect.isawaitable(result):
        await result
