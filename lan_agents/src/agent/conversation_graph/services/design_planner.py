"""Design planner service used by the generate_or_refine_plan node."""

from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from agent.conversation_graph.nodes._helpers import (
    _core_loop_from_gameplay,
    MVP_TAGS,
    copy_dict,
    extract_explicit_plan_fields,
    missing_confirmable_game_plan_fields,
    normalize_tags,
    string_suggestions,
    summarize_game_introduction,
)
from agent.conversation_graph.services.tone import friendly_design_message
from agent.providers import LLMMessage, LLMProvider, ProviderError, provider_from_env
from agent.state import ConversationState

DESIGN_PLANNER_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "game_plan_patch": {"type": "object"},
        "assistant_message": {"type": "string"},
        "suggestions": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["game_plan_patch", "assistant_message", "suggestions"],
}

ALLOWED_GAME_PLAN_FIELDS = {
    "plan_id",
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
    "suggestions",
    "confidence",
}

USER_ANSWERABLE_MISSING_FIELDS = {
    "title",
    "tags",
    "gameplay",
    "core_loop",
    "style",
    "characters",
    "win_condition",
    "lose_condition",
    "controls",
}

MAX_HISTORY_MESSAGES = 12
MAX_HISTORY_CONTENT_CHARS = 800
MAX_QUESTION_ROUNDS = 5

QUESTION_FIELD_MARKERS = {
    "style": ["风格", "画风", "美术"],
    "title": ["叫什么", "名字", "标题"],
    "characters": ["主角", "角色"],
    "win_condition": ["怎样才算赢", "怎么赢", "胜利", "获胜", "目标"],
    "lose_condition": ["失败", "输", "什么情况下算"],
    "controls": ["怎么控制", "操作方式", "控制", "操作"],
    "core_loop": ["核心循环", "重复做"],
    "gameplay": ["核心玩法", "玩法", "主要做什么", "扮演谁", "做什么"],
    "tags": ["类型标签", "游戏类型", "标签"],
}


class DesignPlanner:
    """Use an LLM provider to refine game_plan with deterministic fallback."""

    def __init__(self, provider: LLMProvider | None = None) -> None:
        self._provider = provider or provider_from_env()

    def plan(self, state: ConversationState) -> dict[str, Any]:
        """Return a `game_plan` update for the current conversation state."""
        fallback = deterministic_plan_update(state)
        if fallback.get("conversation_status") == "ready_to_confirm":
            return fallback
        force_complete = should_force_complete_plan(state)
        try:
            llm_result = self._provider.complete_json(
                messages=_messages_from_state(
                    state,
                    current_game_plan=fallback["game_plan"],
                ),
                response_schema=DESIGN_PLANNER_SCHEMA,
                temperature=0.3,
                max_tokens=1200,
            )
        except Exception as exc:
            reason = str(exc).strip()
            message = "LLM provider failed while generating design suggestions"
            if reason:
                message = f"{message}: {reason}"
            raise ProviderError(message) from exc

        game_plan = _merge_llm_patch(
            fallback["game_plan"],
            _allowed_llm_patch(state, fallback["game_plan"], llm_result.get("game_plan_patch", {})),
            llm_result.get("suggestions", []),
            state.user_requirements,
        )
        if force_complete and missing_confirmable_game_plan_fields(game_plan):
            game_plan = complete_missing_plan_fields(game_plan, state)
        status = (
            "ready_to_confirm"
            if not missing_confirmable_game_plan_fields(game_plan)
            else "collecting"
        )
        update: dict[str, Any] = {"game_plan": game_plan, "conversation_status": status}
        if status == "collecting":
            message = str(llm_result.get("assistant_message") or "").strip()
            suggestions = string_suggestions(llm_result.get("suggestions"), [])
            if not message and not suggestions:
                raise ProviderError("模型没有返回追问和可点击建议，请重试。")
            if message and not suggestions:
                raise ProviderError("模型没有返回可点击建议，请重试。")
            if message or suggestions:
                missing_fields = missing_confirmable_game_plan_fields(game_plan)
                update["assistant_response"] = {
                    "message": friendly_design_message(
                        message,
                        missing_fields=missing_fields,
                        game_plan=game_plan,
                    ),
                    "suggestions": suggestions,
                    "card": None,
                    "actions": [],
                }
        return update


def deterministic_plan_update(state: ConversationState) -> dict[str, Any]:
    """Create a deterministic plan update from accumulated requirements."""
    requirements = state.user_requirements
    message = str(state.user_event.get("message", "")).strip()
    game_plan = copy_dict(state.game_plan)
    game_plan["plan_id"] = game_plan.get("plan_id") or f"plan-{uuid4().hex[:8]}"
    if not game_plan.get("tags"):
        game_plan["tags"] = requirements.get("preference_profile", {}).get(
            "genre_candidates", []
        ) or ["arcade", "casual"]
    game_plan["tags"] = normalize_tags(game_plan.get("tags", []))

    explicit_fields = extract_explicit_plan_fields(message)
    for field, value in explicit_fields.items():
        game_plan[field] = value
    if not explicit_fields:
        _absorb_answer_to_previous_question(game_plan, state, message)

    if not game_plan.get("gameplay") and _message_has_gameplay_signal(message):
        game_plan["gameplay"] = requirements.get("intent_summary") or message
    if not game_plan.get("style"):
        game_plan["style"] = requirements.get("preference_profile", {}).get(
            "visual_style"
        )
    if not game_plan.get("characters") and ("小猫" in message or "猫" in message):
        game_plan["characters"] = ["小猫"]
    if not game_plan.get("core_loop") and game_plan.get("gameplay"):
        game_plan["core_loop"] = _core_loop_from_gameplay(str(game_plan["gameplay"]))

    game_plan["confidence"] = (
        "medium" if not missing_confirmable_game_plan_fields(game_plan) else "low"
    )
    if not missing_confirmable_game_plan_fields(game_plan) and not game_plan.get(
        "introduction"
    ):
        game_plan["introduction"] = summarize_game_introduction(game_plan, requirements)
    status = (
        "ready_to_confirm"
        if not missing_confirmable_game_plan_fields(game_plan)
        else "collecting"
    )
    return {"game_plan": game_plan, "conversation_status": status}


def should_force_complete_plan(state: ConversationState) -> bool:
    """Return true once the design chat has exceeded the question budget."""
    try:
        revision_count = int(state.user_requirements.get("revision_count", 0))
    except (TypeError, ValueError):
        revision_count = 0
    return revision_count > MAX_QUESTION_ROUNDS


def complete_missing_plan_fields(
    game_plan: dict[str, Any], state: ConversationState
) -> dict[str, Any]:
    """Complete required plan fields so the graph can stop asking questions."""
    completed = copy_dict(game_plan)
    requirements = state.user_requirements
    message = str(state.user_event.get("message") or "").strip()
    intent_summary = str(requirements.get("intent_summary") or "").strip()
    gameplay_source = str(completed.get("gameplay") or intent_summary or message).strip()

    completed["plan_id"] = completed.get("plan_id") or f"plan-{uuid4().hex[:8]}"
    completed["title"] = completed.get("title") or _fallback_title(
        gameplay_source or intent_summary
    )
    completed["tags"] = normalize_tags(
        completed.get("tags")
        or requirements.get("preference_profile", {}).get("genre_candidates", [])
        or ["casual"]
    )
    completed["gameplay"] = gameplay_source or "围绕已有创意完成轻量互动挑战"
    completed["core_loop"] = completed.get("core_loop") or _core_loop_from_gameplay(
        str(completed["gameplay"])
    )
    completed["style"] = (
        completed.get("style")
        or requirements.get("preference_profile", {}).get("visual_style")
        or "简洁明快"
    )
    completed["characters"] = completed.get("characters") or _fallback_characters(
        requirements, completed
    )
    completed["win_condition"] = (
        completed.get("win_condition")
        or _fallback_win_condition(str(completed["gameplay"]))
    )
    completed["lose_condition"] = completed.get("lose_condition") or "未完成主要目标"
    completed["controls"] = completed.get("controls") or "方向键或点击控制"
    completed["suggestions"] = []
    completed["confidence"] = "medium"
    if not completed.get("introduction"):
        completed["introduction"] = summarize_game_introduction(completed, requirements)
    return completed


def _fallback_title(source: str) -> str:
    text = source.strip().strip("。")
    for prefix in ["我想做一个", "我想做一款", "做一个", "做一款", "用户想做一个"]:
        if text.startswith(prefix):
            text = text[len(prefix) :]
            break
    return (text[:12] or "互动小游戏").strip("，,。 ")


def _fallback_characters(
    requirements: dict[str, Any], game_plan: dict[str, Any]
) -> list[str]:
    candidates = [
        str(item).replace("主角", "").strip()
        for item in requirements.get("must_have", [])
        if isinstance(item, str) and ("主角" in item or "角色" in item)
    ]
    if candidates:
        return [candidates[0]]
    gameplay = str(game_plan.get("gameplay") or "")
    if "玩家" in gameplay:
        return ["玩家"]
    return ["主角"]


def _fallback_win_condition(gameplay: str) -> str:
    if "收集" in gameplay:
        return "收集目标物并达到分数要求"
    if "追逐" in gameplay or "抓" in gameplay:
        return "在限定时间内完成追逐目标"
    if "躲避" in gameplay:
        return "坚持到倒计时结束"
    return "完成关卡目标"


def _absorb_answer_to_previous_question(
    game_plan: dict[str, Any], state: ConversationState, message: str
) -> None:
    """Use the previous assistant question to place short user answers."""
    fields = _fields_from_previous_question(state)
    if not fields:
        return
    if len(fields) > 1:
        _absorb_multi_field_answer(game_plan, fields, message)
        return
    field = fields[0]
    if field not in missing_confirmable_game_plan_fields(game_plan):
        return
    answer = _first_answer_clause(message)
    if not answer:
        return
    _set_answer_for_field(game_plan, field, answer)


def _absorb_multi_field_answer(
    game_plan: dict[str, Any], fields: list[str], message: str
) -> None:
    clauses = _answer_clauses(message)
    if not clauses:
        return
    missing_fields = missing_confirmable_game_plan_fields(game_plan)
    for field, answer in zip(fields, clauses):
        if field not in missing_fields:
            continue
        _set_answer_for_field(game_plan, field, answer)


def _set_answer_for_field(game_plan: dict[str, Any], field: str, answer: str) -> None:
    if field in {"title", "gameplay", "style", "win_condition", "lose_condition", "controls"}:
        game_plan[field] = answer
    elif field == "characters":
        game_plan[field] = [answer]
    elif field == "core_loop":
        game_plan[field] = _core_loop_from_gameplay(answer)
    elif field == "tags":
        game_plan[field] = normalize_tags([answer])


def _field_from_previous_question(state: ConversationState) -> str | None:
    fields = _fields_from_previous_question(state)
    return fields[0] if fields else None


def _fields_from_previous_question(state: ConversationState) -> list[str]:
    candidates = [str(state.assistant_response.get("message") or "")]
    for item in reversed(state.conversation_history):
        if isinstance(item, dict) and item.get("role") == "assistant":
            candidates.append(str(item.get("content") or ""))
            break
    for message in candidates:
        fields = _fields_from_question(message)
        if fields:
            return fields
    return []


def _field_from_question(message: str) -> str | None:
    fields = _fields_from_question(message)
    return fields[0] if fields else None


def _fields_from_question(message: str) -> list[str]:
    field_positions: list[tuple[int, str]] = []
    for field, markers in QUESTION_FIELD_MARKERS.items():
        positions = [message.find(marker) for marker in markers if marker in message]
        if positions:
            field_positions.append((min(positions), field))
    return [field for _, field in sorted(field_positions)]


def _first_answer_clause(message: str) -> str:
    clauses = _answer_clauses(message)
    return clauses[0] if clauses else ""


def _answer_clauses(message: str) -> list[str]:
    answer = " ".join(str(message or "").split()).strip()
    if not answer:
        return []
    clauses = [answer]
    for separator in ["，", "。", ",", ".", "；", ";", "\n"]:
        next_clauses = []
        for clause in clauses:
            next_clauses.extend(clause.split(separator))
        clauses = next_clauses
    return [clause.strip() for clause in clauses if clause.strip()]


def _message_has_gameplay_signal(message: str) -> bool:
    return any(keyword in message for keyword in ["玩法", "躲避", "收集", "闯关", "到达"])


def _messages_from_state(
    state: ConversationState,
    *,
    current_game_plan: dict[str, Any] | None = None,
) -> list[LLMMessage]:
    mvp_tags = ", ".join(sorted(MVP_TAGS))
    design_chat_round = _safe_revision_count(state.user_requirements)
    force_complete = should_force_complete_plan(state)
    prompt_game_plan = current_game_plan or state.game_plan
    missing_fields = [
        field
        for field in missing_confirmable_game_plan_fields(prompt_game_plan)
        if field in USER_ANSWERABLE_MISSING_FIELDS
    ]
    conversation_history = _compact_conversation_history(state.conversation_history)
    payload = {
        "user_requirements": state.user_requirements,
        "game_plan": prompt_game_plan,
        "material_usage": state.material_usage,
        "user_event": state.user_event,
        "conversation_history": conversation_history,
        "missing_game_plan_fields": missing_fields,
        "missing_field_count": len(missing_fields),
        "asked_game_plan_fields": _asked_game_plan_fields(
            conversation_history,
            str(state.assistant_response.get("message") or ""),
        ),
        "design_chat_round": design_chat_round,
        "max_question_rounds": MAX_QUESTION_ROUNDS,
        "should_force_complete_plan": force_complete,
        "previous_assistant_message": str(
            state.assistant_response.get("message") or ""
        ).strip(),
    }
    return [
        LLMMessage(
            role="system",
            content=(
                "你是游戏 Design Agent。只输出 JSON object，不要输出 Markdown。"
                "根据用户需求完善 game_plan，字段必须保持简短、可执行。"
                "你同时具备一个沟通风格 skill：像温暖、鼓励型的游戏设计伙伴。"
                "assistant_message 要先轻轻肯定用户已有想法，再提出一个最关键追问；语气亲和但不啰嗦。"
                "assistant_message 可以使用且最多使用一个合适 icon：✨灵感、🎮玩法、🎨风格、🧩规则、🏁胜负条件、🐾角色。"
                "不要连续使用多个 emoji，不要过度卖萌。"
                "不要复用 previous_assistant_message 中已经出现过的完整句子、开场白或追问；"
                "尤其不要重复“我们先把关键设定搭起来”“我已经抓到一些方向啦”等固定开场。"
                "conversation_history 是此前可见对话的最近历史，必须结合它理解用户已经回答过什么、"
                "不要重复追问已在历史中明确回答的内容。"
                "如果用户刚回答了上一轮追问，assistant_message 必须承接用户新答案，再换一种说法提出下一个关键追问。"
                "你必须根据 missing_game_plan_fields 和 missing_field_count 判断进度；"
                "asked_game_plan_fields 是此前 assistant 已经追问过的字段。"
                "不要追问与 asked_game_plan_fields 语义相同或高度相似的问题；"
                "如果用户刚回答过这些字段，必须先把答案写入 game_plan_patch，再选择新的缺失字段追问。"
                "你的提问目标是在最短时间内补齐 game_plan；每次只能问一个问题时，"
                "优先选择一次能补齐最多缺失字段的问题，避免把可合并确认的信息拆成多轮。"
                "例如可把角色目标、胜负条件、操作方式合并成一个简短问题，但不要变成冗长表单。"
                "如果 title 在 missing_game_plan_fields 中，并且 gameplay、characters、win_condition、controls 中至少两个已明确，"
                "下一轮应优先询问标题，或让 suggestions 直接给出 2 到 4 个符合当前题材的标题选项。"
                "suggestions 也要尽量覆盖多个缺失字段的组合答案，让用户点一次就能补齐更多方案信息。"
                "只有 missing_field_count 等于 1 时，才可以使用“最后一个问题”“只差一个”“最后确认”等收尾表达。"
                "如果 missing_field_count 大于 1，禁止说“最后”“只差一个”“最大关键的问题”“只差一个关键设定”，"
                "要改说“下一个关键设定”或“先确认其中一项”。"
                "assistant_message 只能追问缺失的必填 game_plan 字段：title、tags、gameplay、core_loop、style、characters、win_condition、lose_condition、controls。"
                "不要追问特别能力、皮肤、道具细节、关卡数量等可选扩展；这些可以放进已有字段，但不能阻塞确认卡片。"
                "提问环节最多五轮。payload 中 should_force_complete_plan 为 true 时，禁止继续追问，"
                "必须由你基于已有 user_requirements、conversation_history、material_usage 和 game_plan 自行补全所有缺失必填字段，"
                "assistant_message 必须为空字符串，suggestions 必须为空数组。"
                f"tags 只能来自 MVP 标签集合：{mvp_tags}。"
                "不要向用户追问卡片简介或介绍；introduction 是最终派生字段，"
                "必须在 title、tags、gameplay、core_loop、style、characters、win_condition、lose_condition、controls 都齐全后，"
                "基于完整对话和 game_plan 总结生成。"
                "若方案信息仍缺失，assistant_message 必须提出一个最关键追问，"
                "suggestions 必须由你根据当前用户题材、game_plan 和 assistant_message 生成 2 到 4 条简短可点击回答，"
                "不要使用固定模板、测试样例或与当前题材无关的建议。若方案完整，assistant_message 可为空。"
            ),
        ),
        LLMMessage(role="user", content=json.dumps(payload, ensure_ascii=False)),
    ]


def _safe_revision_count(requirements: dict[str, Any]) -> int:
    try:
        return int(requirements.get("revision_count", 0))
    except (TypeError, ValueError):
        return 0


def _compact_conversation_history(history: Any) -> list[dict[str, str]]:
    """Keep recent safe user-visible history for prompt context."""
    if not isinstance(history, list):
        return []
    compact: list[dict[str, str]] = []
    for item in history[-MAX_HISTORY_MESSAGES:]:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").strip()
        if role not in {"user", "assistant", "system"}:
            continue
        content = " ".join(str(item.get("content") or "").split())
        if not content:
            continue
        compact.append(
            {
                "role": role,
                "content": content[:MAX_HISTORY_CONTENT_CHARS],
            }
        )
    return compact


def _asked_game_plan_fields(
    conversation_history: list[dict[str, str]], previous_assistant_message: str
) -> list[str]:
    asked_fields: list[str] = []
    messages = [previous_assistant_message]
    messages.extend(
        item["content"]
        for item in conversation_history
        if item.get("role") == "assistant"
    )
    for message in messages:
        for field in _fields_from_question(message):
            if field not in asked_fields:
                asked_fields.append(field)
    return asked_fields


def _merge_llm_patch(
    base_game_plan: dict[str, Any],
    patch: Any,
    suggestions: Any,
    requirements: dict[str, Any] | None = None,
) -> dict[str, Any]:
    game_plan = copy_dict(base_game_plan)
    if isinstance(patch, dict):
        for field, value in patch.items():
            if field not in ALLOWED_GAME_PLAN_FIELDS:
                continue
            if field == "introduction":
                continue
            if field == "tags":
                game_plan["tags"] = normalize_tags(value if isinstance(value, list) else [])
            elif field in {"core_loop", "characters"}:
                if isinstance(value, list):
                    game_plan[field] = [str(item) for item in value if str(item).strip()]
            elif field == "suggestions":
                game_plan["suggestions"] = string_suggestions(value, [])
            elif isinstance(value, str):
                game_plan[field] = value.strip()
            elif field in {"plan_id", "confidence"} and value is not None:
                game_plan[field] = str(value)
    if not game_plan.get("plan_id"):
        game_plan["plan_id"] = f"plan-{uuid4().hex[:8]}"
    if suggestions:
        game_plan["suggestions"] = string_suggestions(suggestions, [])
    if not game_plan.get("core_loop") and game_plan.get("gameplay"):
        game_plan["core_loop"] = _core_loop_from_gameplay(str(game_plan["gameplay"]))
    game_plan["tags"] = normalize_tags(game_plan.get("tags", []))
    if not missing_confirmable_game_plan_fields(game_plan) and not game_plan.get(
        "introduction"
    ):
        game_plan["introduction"] = summarize_game_introduction(game_plan, requirements)
    game_plan["confidence"] = (
        "medium" if not missing_confirmable_game_plan_fields(game_plan) else "low"
    )
    return game_plan


def _allowed_llm_patch(
    state: ConversationState,
    fallback_game_plan: dict[str, Any],
    patch: Any,
) -> Any:
    """Prevent the model from silently deciding unanswered required fields."""
    if should_force_complete_plan(state) or not isinstance(patch, dict):
        return patch

    allowed_fields = {
        "plan_id",
        "tags",
        "gameplay",
        "core_loop",
        "suggestions",
        "confidence",
    }
    allowed_fields.update(
        field
        for field, value in fallback_game_plan.items()
        if value and field in ALLOWED_GAME_PLAN_FIELDS
    )
    allowed_fields.update(extract_explicit_plan_fields(str(state.user_event.get("message") or "")).keys())
    allowed_fields.update(_fields_from_previous_question(state))
    return {
        field: value
        for field, value in patch.items()
        if field in allowed_fields
    }
