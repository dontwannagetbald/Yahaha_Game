"""Small deterministic helpers for the MVP revision graph."""

from __future__ import annotations

import copy
import re
from typing import Any


SECRET_PATTERNS = (
    re.compile(r"password", re.IGNORECASE),
    re.compile(r"secret", re.IGNORECASE),
    re.compile(r"token", re.IGNORECASE),
    re.compile(r"oauth", re.IGNORECASE),
    re.compile(r"X-Amz-", re.IGNORECASE),
    re.compile(r"Signature=", re.IGNORECASE),
)


def sanitize_text(value: str) -> str:
    """Remove obvious sensitive fragments before echoing user text into outputs."""
    cleaned = value.strip()
    for pattern in SECRET_PATTERNS:
        cleaned = pattern.sub("[redacted]", cleaned)
    return cleaned


def append_log(state: Any, step: str, message: str, level: str = "info") -> list[dict[str, Any]]:
    logs = list(getattr(state, "agent_logs", []) or [])
    logs.append({"step": step, "level": level, "message": message})
    return logs


def merged_game_plan(base_game_plan: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    plan = copy.deepcopy(base_game_plan)
    for key, value in patch.items():
        plan[key] = copy.deepcopy(value)
    return plan


def is_unclear_revision(message: str) -> bool:
    normalized = message.strip()
    if not normalized:
        return True
    unclear_markers = ("更好玩", "优化一下", "随便", "之前说的", "好一点", "升级一下")
    concrete_markers = (
        "失败",
        "难度",
        "血量",
        "背景",
        "雪",
        "角色",
        "主角",
        "换成",
        "操作",
        "标题",
        "简介",
        "标签",
        "胜利",
        "收集",
    )
    return any(marker in normalized for marker in unclear_markers) and not any(
        marker in normalized for marker in concrete_markers
    )


def build_patch_from_message(message: str) -> dict[str, Any]:
    text = sanitize_text(message)
    patch: dict[str, Any] = {}

    if "血量归零" in text:
        patch["lose_condition"] = "碰到障碍后扣血，血量归零才失败"
    elif "失败" in text and ("宽松" in text or "降低" in text or "简单" in text):
        patch["lose_condition"] = "失败条件调宽松，允许玩家犯错后继续游戏"

    if "雪" in text or "雪地" in text:
        patch["style"] = "雪地场景"
    elif "背景" in text:
        patch["style"] = text.rstrip("。.")

    if "兔子" in text and ("主角" in text or "角色" in text or "换成" in text):
        patch["characters"] = ["兔子"]
    elif "小猫" in text and ("主角" in text or "角色" in text or "换成" in text):
        patch["characters"] = ["小猫"]

    if "标题" in text:
        title_match = re.search(r"标题(?:改成|叫|为)?[：: ]?([^，。,.]+)", text)
        if title_match:
            patch["title"] = title_match.group(1).strip()

    return patch


def summarize_intent(message: str, patch: dict[str, Any]) -> str:
    if "lose_condition" in patch:
        return "调整失败条件"
    if "characters" in patch:
        return "调整角色设定"
    if "style" in patch:
        return "调整视觉风格"
    if "title" in patch:
        return "调整标题"
    return sanitize_text(message)[:80] or "生成后修改请求"
