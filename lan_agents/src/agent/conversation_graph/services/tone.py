"""Tone helpers for the Design Agent's user-facing replies."""

from __future__ import annotations

from typing import Any

ICON_BY_FIELD = {
    "gameplay": "🎮",
    "core_loop": "🧩",
    "style": "🎨",
    "characters": "🐾",
    "win_condition": "🏁",
    "lose_condition": "🧩",
    "controls": "🎮",
    "title": "✨",
    "introduction": "✨",
    "tags": "🧩",
}

GENERATED_OPENINGS = [
    "先把核心玩法定下来，",
    "最后确认一下，",
    "继续补齐几个关键设定，",
    "我们先把关键设定搭起来：",
]


def friendly_design_message(
    message: str,
    *,
    missing_fields: list[str] | None = None,
    game_plan: dict[str, Any] | None = None,
) -> str:
    """Make a Design Agent message warmer while keeping it concise."""
    fields = missing_fields or []
    plan = game_plan or {}
    clean_message = _normalize_progress_claims(
        _collapse_repeated_generated_openings(
            _strip_known_icons(str(message or "").strip())
        ),
        missing_count=len(fields),
    )
    if not clean_message:
        clean_message = "我还需要再确认一个关键设定。"
    icon = _icon_for(fields, clean_message)
    if _has_generated_opening(clean_message):
        return f"{icon} {clean_message}"
    if _has_friendly_opening(clean_message) and not _has_bad_progress_claim(
        clean_message, len(fields)
    ):
        return f"{icon} {clean_message}"
    opening = _opening_for_progress(fields, plan, clean_message)
    return f"{icon} {opening}{clean_message}"


def friendly_ready_message() -> str:
    """Return the friendly message shown when a card is ready."""
    return "✨ 我整理好一版完整方案啦，你可以直接生成，也可以点换一换看看另一个方向。"


def _icon_for(missing_fields: list[str], message: str) -> str:
    if "风格" in message:
        return "🎨"
    if "玩法" in message or "控制" in message or "操作" in message:
        return "🎮"
    if "赢" in message or "胜利" in message:
        return "🏁"
    if "角色" in message or "主角" in message:
        return "🐾"
    for field in missing_fields:
        if field in ICON_BY_FIELD:
            return ICON_BY_FIELD[field]
    return "✨"


def _subject_hint(game_plan: dict[str, Any]) -> str:
    title = str(game_plan.get("title") or "").strip()
    if title:
        return f"关于{title}，"
    characters = game_plan.get("characters") or []
    if characters:
        return f"关于{characters[0]}，"
    return ""


def _opening_for_progress(
    missing_fields: list[str], game_plan: dict[str, Any], message: str
) -> str:
    missing_count = len(missing_fields)
    subject = _subject_hint(game_plan)
    if "玩法" in message or "核心玩法" in message:
        return f"先把核心玩法定下来，{subject}"
    if missing_count <= 1:
        return f"最后确认一下，{subject}"
    if subject:
        return f"继续补齐几个关键设定，{subject}"
    return "我们先把关键设定搭起来："


def _has_generated_opening(message: str) -> bool:
    return any(message.startswith(opening) for opening in GENERATED_OPENINGS)


def _collapse_repeated_generated_openings(message: str) -> str:
    cleaned = message.strip()
    changed = True
    while changed:
        changed = False
        for opening in GENERATED_OPENINGS:
            duplicate = f"{opening}{opening}"
            if duplicate in cleaned:
                cleaned = cleaned.replace(duplicate, opening)
                changed = True
    return cleaned


def _strip_known_icons(message: str) -> str:
    for icon in ["✨", "🎮", "🎨", "🧩", "🏁", "🐾"]:
        message = message.replace(icon, "")
    return message.strip()


def _has_friendly_opening(message: str) -> bool:
    openings = ["我已经", "我整理", "这个方向", "太好了", "很棒"]
    return any(message.startswith(opening) for opening in openings)


def _has_bad_progress_claim(message: str, missing_count: int) -> bool:
    return missing_count > 1 and any(
        marker in message
        for marker in ["只差", "最后一步", "最后一个", "最后确认", "就差"]
    )


def _normalize_progress_claims(message: str, *, missing_count: int) -> str:
    replacements = {
        "现在我只差一个最大关键的问题：": "",
        "现在我只差一个最大关键的问题，": "",
        "现在我只差一个最大关键的问题": "",
        "我只差一个最大关键的问题：": "",
        "我只差一个最大关键的问题，": "",
        "我只差一个最大关键的问题": "",
        "现在我只差一个关键设定：": "",
        "现在我只差一个关键设定，": "",
        "现在我只差一个关键设定": "",
        "我只差一个关键设定：": "",
        "我只差一个关键设定，": "",
        "我只差一个关键设定": "",
        "只差一个关键设定：": "",
        "只差一个关键设定，": "",
        "只差一个关键设定": "",
        "最大关键的问题：": "",
        "最大关键的问题，": "",
        "最大关键的问题": "",
        "现在只差一个关键点：": "",
        "现在只差一个关键点，": "",
        "现在只差一个关键点": "",
        "只差一个关键点：": "",
        "只差一个关键点，": "",
        "只差一个关键点": "",
    }
    if missing_count > 1:
        replacements.update(
            {
                "最后一步：": "",
                "最后一步，": "",
                "最后一步": "",
                "最后一个问题：": "",
                "最后一个问题，": "",
                "最后一个问题": "",
                "最后确认一下：": "",
                "最后确认一下，": "",
                "最后确认一下": "",
                "最后确认": "确认",
            }
        )
    cleaned = message
    for source, target in replacements.items():
        cleaned = cleaned.replace(source, target)
    return cleaned.strip(" ，。")
