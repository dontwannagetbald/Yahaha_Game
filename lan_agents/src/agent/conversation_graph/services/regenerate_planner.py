"""LLM-backed planner for first-phase card regeneration."""

from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from agent.conversation_graph.nodes._helpers import (
    MVP_TAGS,
    copy_dict,
    normalize_tags,
    summarize_game_introduction,
)
from agent.providers import LLMMessage, LLMProvider, ProviderError, provider_from_env
from agent.state import ConversationState

REGENERATE_PLANNER_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "introduction": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["title", "introduction", "tags"],
}

FALLBACK_VARIANTS = (
    {
        "title_suffix": "Remix",
        "lead_sentence": "这版我保留核心玩法，但把整体节奏调整得更轻快。",
    },
    {
        "title_suffix": "Sprint",
        "lead_sentence": "这版我保留目标结构，但把推进节奏改得更有冲刺感。",
    },
    {
        "title_suffix": "Twist",
        "lead_sentence": "这版我保留原始创意，但把整体表达改得更灵动直接。",
    },
)


class RegeneratePlanner:
    """Ask the configured LLM for a new confirmation-card variant."""

    def __init__(self, provider: LLMProvider | None = None) -> None:
        self._provider = provider or provider_from_env()

    def regenerate(self, state: ConversationState) -> dict[str, Any]:
        """Return a refreshed game_plan while preserving core design fields."""
        base_plan = copy_dict(state.game_plan)
        try:
            llm_result = self._provider.complete_json(
                messages=_messages_from_state(state),
                response_schema=REGENERATE_PLANNER_SCHEMA,
                temperature=0.7,
                max_tokens=900,
            )
        except Exception as exc:
            reason = str(exc).strip()
            message = "LLM provider failed while regenerating design card"
            if reason:
                message = f"{message}: {reason}"
            raise ProviderError(message) from exc

        game_plan = _merge_card_variant(base_plan, llm_result, state)
        return {"game_plan": game_plan, "conversation_status": "ready_to_confirm"}


def _messages_from_state(state: ConversationState) -> list[LLMMessage]:
    game_plan = state.game_plan
    current_card = {
        "title": game_plan.get("title", ""),
        "introduction": game_plan.get("introduction", ""),
        "tags": game_plan.get("tags", []),
    }
    payload = {
        "user_requirements": state.user_requirements,
        "game_plan": game_plan,
        "material_usage": state.material_usage,
        "current_card": current_card,
        "conversation_history": state.conversation_history[-12:],
        "user_event": state.user_event,
    }
    tags = ", ".join(sorted(MVP_TAGS))
    return [
        LLMMessage(
            role="system",
            content=(
                "你是游戏 Design Agent，正在处理用户点击“换一换/重新生成方案卡片”。"
                "只输出 JSON object，不要输出 Markdown。"
                "你的任务是重新生成一版确认卡片，只允许输出 title、introduction、tags。"
                "新卡片必须和当前 user_requirements、game_plan、material_usage 保持一致，"
                "但 title 和 introduction 要明显不同于 current_card，给用户一种新表达/新包装。"
                "不要修改玩法、角色、胜负条件、操作方式或素材用途；这些只能作为生成简介的事实依据。"
                "introduction 要是 1 到 2 句中文，具体总结玩法、角色、胜负条件和操作方式，不要空泛。"
                f"tags 只能来自 MVP 标签集合：{tags}。"
            ),
        ),
        LLMMessage(role="user", content=json.dumps(payload, ensure_ascii=False)),
    ]


def _merge_card_variant(
    base_plan: dict[str, Any], llm_result: dict[str, Any], state: ConversationState
) -> dict[str, Any]:
    game_plan = copy_dict(base_plan)
    plan_token = uuid4().hex[:8]
    game_plan["plan_id"] = f"plan-{plan_token}"

    title = str(llm_result.get("title") or "").strip()
    introduction = str(llm_result.get("introduction") or "").strip()
    tags = normalize_tags(llm_result.get("tags") or game_plan.get("tags") or [])

    if title:
        game_plan["title"] = title
    else:
        variant = FALLBACK_VARIANTS[int(plan_token[-1], 16) % len(FALLBACK_VARIANTS)]
        base_title = str(game_plan.get("title") or "新方案").strip()
        game_plan["title"] = f"{base_title} {variant['title_suffix']}".strip()
    if introduction:
        game_plan["introduction"] = introduction
    else:
        variant = FALLBACK_VARIANTS[int(plan_token[-1], 16) % len(FALLBACK_VARIANTS)]
        summary = summarize_game_introduction(game_plan, state.user_requirements)
        game_plan["introduction"] = f"{variant['lead_sentence']}{summary}"
    game_plan["tags"] = tags
    game_plan["confidence"] = game_plan.get("confidence") or "medium"
    return game_plan
