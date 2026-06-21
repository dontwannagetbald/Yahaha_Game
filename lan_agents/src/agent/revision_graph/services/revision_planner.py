"""LLM-backed planner for post-generation revision requests."""

from __future__ import annotations

import json
from typing import Any

from agent.providers import LLMMessage, LLMProvider, provider_from_env
from agent.revision_graph.nodes._helpers import (
    build_patch_from_message,
    is_unclear_revision,
    sanitize_text,
    summarize_intent,
)
from agent.revision_graph.state import RevisionState

REVISION_PLANNER_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "revision_intent": {"type": "string"},
        "game_plan_patch": {"type": "object"},
        "requires_regeneration": {"type": "boolean"},
        "assistant_message": {"type": "string"},
        "suggestions": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "revision_intent",
        "game_plan_patch",
        "requires_regeneration",
        "assistant_message",
        "suggestions",
    ],
}

ALLOWED_PATCH_FIELDS = {
    "title",
    "introduction",
    "tags",
    "gameplay",
    "core_loop",
    "style",
    "characters",
    "win_condition",
    "lose_condition",
    "controls",
}


class RevisionPlanner:
    """Ask the configured LLM to convert a user revision message into a safe patch."""

    def __init__(self, provider: LLMProvider | None = None) -> None:
        self._provider = provider or provider_from_env()

    def plan(self, state: RevisionState) -> dict[str, Any]:
        """Return revision intent and patch, falling back to deterministic parsing."""
        try:
            llm_result = self._provider.complete_json(
                messages=_messages_from_state(state),
                response_schema=REVISION_PLANNER_SCHEMA,
                temperature=0.2,
                max_tokens=900,
            )
            update = _normalize_llm_result(llm_result)
            if update:
                return update
        except Exception:
            pass
        return deterministic_revision_update(state)


def deterministic_revision_update(state: RevisionState) -> dict[str, Any]:
    """Return a deterministic revision update when the provider cannot help."""
    if is_unclear_revision(state.user_message):
        return {
            "revision_status": "needs_clarification",
            "requires_regeneration": False,
        }
    patch = build_patch_from_message(state.user_message)
    if not patch:
        return {
            "revision_status": "needs_clarification",
            "requires_regeneration": False,
        }
    return {
        "revision_status": "clear",
        "revision_intent": summarize_intent(state.user_message, patch),
        "game_plan_patch": patch,
        "requires_regeneration": True,
    }


def _messages_from_state(state: RevisionState) -> list[LLMMessage]:
    payload = {
        "parent_job": _safe_parent_job(state.parent_job),
        "base_game_plan": state.base_game_plan,
        "base_material_usage": state.base_material_usage,
        "generated_result": _safe_generated_result(state.generated_result),
        "user_message": sanitize_text(state.user_message),
    }
    return [
        LLMMessage(
            role="system",
            content=(
                "你是游戏 Revision Agent，负责生成后修改链路。"
                "只输出 JSON object，不要输出 Markdown。"
                "你的任务是理解用户对已生成 draft 的明确修改，输出 revision_intent、game_plan_patch、"
                "requires_regeneration、assistant_message 和 suggestions。"
                "明确修改应生成 patch 并 requires_regeneration=true；模糊修改应返回空 patch、"
                "requires_regeneration=false，并用 assistant_message 追问。"
                "只允许修改 game_plan 的 title/introduction/tags/gameplay/core_loop/style/characters/"
                "win_condition/lose_condition/controls。"
                "不要修改 parent_job、base_material_usage、generated_result、create_session 或旧产物路径；"
                "不覆盖旧产物，只创建新的 revision job。"
                "不要输出 secret、token、password、OAuth code 或完整 presigned URL。"
            ),
        ),
        LLMMessage(role="user", content=json.dumps(payload, ensure_ascii=False)),
    ]


def _normalize_llm_result(result: dict[str, Any]) -> dict[str, Any]:
    required_keys = {
        "revision_intent",
        "game_plan_patch",
        "requires_regeneration",
        "assistant_message",
        "suggestions",
    }
    if not required_keys.issubset(result.keys()):
        return {}
    patch = _allowed_patch(result.get("game_plan_patch") or {})
    requires_regeneration = bool(result.get("requires_regeneration"))
    assistant_message = sanitize_text(str(result.get("assistant_message") or "").strip())
    suggestions = _string_list(result.get("suggestions") or [])

    if not patch or not requires_regeneration:
        if not assistant_message:
            return {}
        return {
            "revision_status": "needs_clarification",
            "requires_regeneration": False,
            "game_plan_patch": {},
            "assistant_response": {
                "message": assistant_message,
                "suggestions": suggestions,
                "actions": [],
            },
        }

    revision_intent = sanitize_text(str(result.get("revision_intent") or "").strip())
    if not revision_intent:
        return {}
    return {
        "revision_status": "clear",
        "revision_intent": revision_intent,
        "game_plan_patch": patch,
        "requires_regeneration": True,
        "assistant_response": {
            "message": assistant_message or "我会按这个修改创建一个新版本。",
            "suggestions": suggestions,
            "actions": [],
        },
    }


def _allowed_patch(raw_patch: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw_patch, dict):
        return {}
    patch: dict[str, Any] = {}
    for key, value in raw_patch.items():
        if key not in ALLOWED_PATCH_FIELDS:
            continue
        if isinstance(value, str):
            cleaned = sanitize_text(value)
            if cleaned:
                patch[key] = cleaned
        elif isinstance(value, list):
            cleaned_items = [sanitize_text(str(item)) for item in value if str(item).strip()]
            if cleaned_items:
                patch[key] = cleaned_items
    return patch


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [sanitize_text(str(item)) for item in value if str(item).strip()][:4]


def _safe_parent_job(parent_job: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": parent_job.get("id"),
        "status": parent_job.get("status"),
        "create_session_id": parent_job.get("create_session_id"),
        "artifact_prefix": parent_job.get("artifact_prefix"),
    }


def _safe_generated_result(generated_result: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_prefix": generated_result.get("artifact_prefix"),
        "manifest_path": generated_result.get("manifest_path"),
        "entry_path": generated_result.get("entry_path"),
    }
