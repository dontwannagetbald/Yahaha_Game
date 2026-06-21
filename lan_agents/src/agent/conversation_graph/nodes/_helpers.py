"""Shared deterministic helpers for conversation nodes."""

from __future__ import annotations

import copy
from dataclasses import asdict
from typing import Any
from uuid import uuid4

from agent.state import ConversationState

MVP_TAGS = {
    "adventure",
    "action",
    "strategy",
    "puzzle",
    "arcade",
    "survival",
    "simulation",
    "racing",
    "rhythm",
    "roleplay",
    "casual",
    "educational",
}


def state_defaults_update(state: ConversationState) -> dict[str, Any]:
    current = asdict(state)
    return {
        "user_requirements": current["user_requirements"],
        "game_plan": current["game_plan"],
        "material_usage": current["material_usage"],
        "assistant_response": current["assistant_response"],
        "handoff_to_generation": current["handoff_to_generation"],
    }


def copy_dict(value: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(value)


def append_unique(existing: list[str], additions: list[str]) -> list[str]:
    result = list(existing)
    for item in additions:
        if item and item not in result:
            result.append(item)
    return result


def merge_summary(existing: str, message: str) -> str:
    if not existing:
        return message
    if message in existing:
        return existing
    return f"{existing}；{message}"


def extract_must_haves(message: str) -> list[str]:
    mapping = {
        "躲避": "躲避障碍",
        "障碍": "躲避障碍",
        "收集星星": "收集星星",
        "星星": "收集星星",
        "小猫": "小猫主角",
        "猫": "小猫主角",
    }
    return [value for keyword, value in mapping.items() if keyword in message]


def extract_nice_to_haves(message: str) -> list[str]:
    mapping = {
        "可爱": "可爱风格",
        "卡通": "卡通表现",
        "森林": "森林场景",
    }
    return [value for keyword, value in mapping.items() if keyword in message]


def extract_constraints(message: str) -> list[str]:
    constraints = []
    if "不要" in message or "改成" in message or "换成" in message:
        constraints.append(message)
    if "简单" in message or "轻松" in message:
        constraints.append("难度简单")
    if "儿童" in message or "小朋友" in message:
        constraints.append("儿童友好")
    return constraints


def merge_preference_profile(profile: dict[str, Any], message: str) -> dict[str, Any]:
    merged = copy_dict(profile)
    genres = list(merged.get("genre_candidates", []))
    if ("躲避" in message or "障碍" in message) and "arcade" not in genres:
        genres.append("arcade")
    if ("收集" in message or "星星" in message) and "casual" not in genres:
        genres.append("casual")
    merged["genre_candidates"] = genres
    if "可爱" in message:
        merged["visual_style"] = "可爱"
    elif "像素" in message:
        merged["visual_style"] = "像素"
    if "轻松" in message or "可爱" in message:
        merged["tone"] = "轻松"
    if "简单" in message:
        merged["difficulty"] = "easy"
    elif "困难" in message or "难一点" in message:
        merged["difficulty"] = "hard"
    return merged


def next_open_questions(requirements: dict[str, Any]) -> list[str]:
    answered = {
        item.get("question")
        for item in requirements.get("answered_questions", [])
        if isinstance(item, dict)
    }
    questions = list(requirements.get("open_questions", []))
    style_question = "希望游戏是什么美术风格？"
    profile = requirements.get("preference_profile", {})
    if not profile.get("visual_style") and style_question not in answered:
        questions = append_unique(questions, [style_question])
    return [question for question in questions if question not in answered]


def sync_material_usage_from_message(
    material_usage: dict[str, Any], message: str
) -> dict[str, Any] | None:
    if "背景" not in message and "主角" not in message:
        return None
    usage = "background" if "背景" in message else "character"
    updated = copy_dict(material_usage)
    assets = updated.get("assets", [])
    if not assets:
        return None
    assets[0]["intended_use"] = usage
    updated["assets"] = assets
    return updated


def sanitize_asset(asset: dict[str, Any]) -> dict[str, Any]:
    user_hint = asset.get("user_hint") or ""
    return {
        "asset_id": str(asset.get("asset_id") or uuid4().hex),
        "filename": str(asset.get("filename") or "asset"),
        "mime_type": str(asset.get("mime_type") or "application/octet-stream"),
        "intended_use": intended_use_from_hint(
            str(user_hint), str(asset.get("mime_type", ""))
        ),
        "usage_priority": "primary" if user_hint else "supporting",
        "user_hint": user_hint,
        "agent_note": "已记录素材，后续会在生成阶段按用途使用。",
    }


def intended_use_from_hint(user_hint: str, mime_type: str) -> str:
    if "背景" in user_hint:
        return "background"
    if "主角" in user_hint or "角色" in user_hint:
        return "character"
    if mime_type.startswith("audio/"):
        return "audio"
    if mime_type.startswith("video/"):
        return "video_reference"
    if mime_type.startswith("image/"):
        return "visual_reference"
    return "reference"


def card_from_game_plan(game_plan: dict[str, Any]) -> dict[str, Any] | None:
    if missing_confirmable_game_plan_fields(game_plan):
        return None
    title = game_plan.get("title")
    introduction = game_plan.get("introduction")
    tags = game_plan.get("tags")
    if not title or not introduction or not tags:
        return None
    return {
        "plan_id": game_plan.get("plan_id"),
        "title": title,
        "introduction": introduction,
        "tags": tags,
    }


def normalize_tags(tags: list[Any]) -> list[str]:
    normalized = []
    for tag in tags:
        text = str(tag).strip().lower()
        if text in MVP_TAGS and text not in normalized:
            normalized.append(text)
    return normalized or ["casual"]


def missing_game_plan_fields(game_plan: dict[str, Any]) -> list[str]:
    required_fields = [
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
    ]
    return [field for field in required_fields if not game_plan.get(field)]


def missing_confirmable_game_plan_fields(game_plan: dict[str, Any]) -> list[str]:
    """Return fields that must be collected from users before final summary."""
    required_fields = [
        "plan_id",
        "title",
        "tags",
        "gameplay",
        "core_loop",
        "style",
        "characters",
        "win_condition",
        "lose_condition",
        "controls",
    ]
    return [field for field in required_fields if not game_plan.get(field)]


def summarize_game_introduction(
    game_plan: dict[str, Any], requirements: dict[str, Any] | None = None
) -> str:
    """Create the final card introduction from the complete design context."""
    requirements = requirements or {}
    title = str(game_plan.get("title") or "").strip()
    gameplay = str(game_plan.get("gameplay") or "").strip()
    style = str(game_plan.get("style") or "").strip()
    characters = ", ".join(str(item) for item in game_plan.get("characters", []) if item)
    win_condition = str(game_plan.get("win_condition") or "").strip()
    lose_condition = str(game_plan.get("lose_condition") or "").strip()
    controls = str(game_plan.get("controls") or "").strip()
    intent_summary = str(requirements.get("intent_summary") or "").strip()

    genre_text = _localized_tag_summary(game_plan.get("tags") or [])
    subject = f"玩家将控制{characters}" if characters else "玩家将操作主角"
    action_text = _clean_intro_sentence(gameplay or intent_summary)
    opening_bits = []
    if title:
        opening_bits.append(f"《{title}》是一款")
    if style:
        opening_bits.append(f"{style}风格的")
    if genre_text:
        opening_bits.append(f"{genre_text}小游戏")
    else:
        opening_bits.append("轻量互动小游戏")

    sentences = ["".join(opening_bits)]
    if action_text:
        sentences.append(f"{subject}，{action_text}")
    if win_condition:
        sentences.append(f"目标是{win_condition.rstrip('。')}")
    if lose_condition:
        sentences[-1] = f"{sentences[-1]}，同时避免{lose_condition.rstrip('。')}"
    if controls:
        sentences.append(f"操作方式为{controls.rstrip('。')}")
    introduction = "。".join(sentence for sentence in sentences if sentence).strip()
    if not introduction:
        return "一款根据你的创意整理出的轻量互动小游戏。"
    if not introduction.endswith("。"):
        introduction = f"{introduction}。"
    return introduction


def _clean_intro_sentence(text: str) -> str:
    sentence = text.strip().rstrip("。")
    for prefix in ["我想做一个", "我想做一款", "做一个", "做一款"]:
        if sentence.startswith(prefix):
            sentence = sentence[len(prefix) :]
            break
    for suffix in ["的轻松小游戏", "的小游戏", "轻松小游戏", "小游戏"]:
        if sentence.endswith(suffix):
            sentence = sentence[: -len(suffix)]
            break
    return sentence


def _localized_tag_summary(tags: list[Any]) -> str:
    labels = {
        "action": "动作",
        "adventure": "冒险",
        "arcade": "街机",
        "casual": "休闲",
        "educational": "教育",
        "puzzle": "解谜",
        "racing": "竞速",
        "rhythm": "音游",
        "roleplay": "角色扮演",
        "simulation": "模拟",
        "strategy": "策略",
        "survival": "生存",
    }
    localized = [labels.get(str(tag), str(tag)) for tag in tags]
    return "、".join(tag for tag in localized if tag)


def assets_missing_usage(material_usage: dict[str, Any]) -> list[str]:
    missing = []
    for asset in material_usage.get("assets", []):
        if not asset.get("intended_use"):
            missing.append(str(asset.get("asset_id") or asset.get("filename") or "asset"))
    return missing


def followup_for_missing_fields(missing_fields: list[str]) -> dict[str, Any]:
    first_missing = missing_fields[0] if missing_fields else ""
    followups = {
        "title": "我已经理解大方向了。你希望这个游戏叫什么名字？",
        "gameplay": "我还需要确认核心玩法：玩家主要做什么？",
        "style": "玩法方向清楚了。你希望游戏是什么视觉风格？",
        "characters": "风格也清楚了。主角或主要角色是谁？",
        "win_condition": "角色确定了。玩家怎样才算赢？",
        "lose_condition": "胜利条件有了。什么情况下算失败？",
        "controls": "最后确认操作方式：玩家怎么控制？",
        "core_loop": "我还需要把核心循环说清楚。玩家每轮重复做哪些动作？",
        "tags": "我还需要确认游戏类型标签。",
        "plan_id": "我正在整理方案，还需要再确认一个关键设定。",
    }
    message = followups.get(
        first_missing,
        "我还需要补齐一些设定，才能给你确认卡片。",
    )
    return {"message": message, "suggestions": []}


def safe_text(value: Any, fallback: str) -> str:
    text = str(value or "").strip()
    unsafe_markers = ["Traceback", "token=", "X-Amz-Signature", "secret", "password", "api_key"]
    if not text or any(marker.lower() in text.lower() for marker in unsafe_markers):
        return fallback
    return text


def string_suggestions(value: Any, fallback: list[str]) -> list[str]:
    if not isinstance(value, list):
        return fallback
    suggestions = [item for item in value if isinstance(item, str) and item.strip()]
    return suggestions or fallback


def extract_explicit_plan_fields(message: str) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    extractors = {
        "title": ["标题叫", "名字叫"],
        "gameplay": ["玩法是"],
        "style": ["风格是"],
        "win_condition": ["胜利条件是"],
        "lose_condition": ["失败条件是"],
        "controls": ["操作方式是", "操作是"],
    }
    for field, markers in extractors.items():
        value = _extract_after_markers(message, markers)
        if value:
            fields[field] = value
    character = _extract_after_markers(message, ["角色是", "主角是"])
    if character:
        fields["characters"] = [character]
    if fields.get("gameplay"):
        fields["core_loop"] = _core_loop_from_gameplay(fields["gameplay"])
    return fields


def _extract_after_markers(message: str, markers: list[str]) -> str:
    for marker in markers:
        if marker not in message:
            continue
        tail = message.split(marker, 1)[1]
        for separator in ["，", "。", ",", "."]:
            tail = tail.split(separator, 1)[0]
        return tail.strip()
    return ""


def _core_loop_from_gameplay(gameplay: str) -> list[str]:
    loop = []
    if "躲避" in gameplay:
        loop.append("躲避")
    if "收集" in gameplay:
        loop.append("收集")
    if "到达" in gameplay:
        loop.append("到达")
    return loop or ["行动", "反馈", "推进"]
