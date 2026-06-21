"""Prompt builders for the stage-B Asset Agent."""

from __future__ import annotations

import json
import re
from typing import Any

from agent.generation_graph.state import GenerationState

BACKGROUND_FIXED_PROMPT = """
You are an excellent game UI designer and 2D game environment artist.
Your task is to generate the main background image for a playable HTML5 game.

Asset type: game background.
Target asset path: assets/background.png.
Required output size: 1280x720.
Definition: a single-screen game stage background, suitable for gameplay.
The image must not contain UI panels, HUD, buttons, text, logos, watermarks, speech bubbles, title text, or menu elements.
The image should leave clear playable space for the player character, hazards, collectibles, and code-generated effects.
Use a coherent game-art style that matches the game description.
""".strip()

PLAYER_FIXED_PROMPT = """
You are an excellent game UI designer and 2D game character artist.
Your task is to generate the player character image for a playable HTML5 game.

Asset type: player character sprite.
Target asset path: assets/player.png.
Model generation canvas: 1024x1024.
Final required export size: 256x256.
Definition: a single complete player character, centered, fully visible, readable at small size, suitable as a 2D game sprite.
Generate the character on a perfectly flat solid magenta background (#FF00FF).
Do not use magenta, pink, or purple anywhere in the character.
No shadow, no floor, no scenery, no gradient, no texture in the background.
The background must be a uniform chroma-key color for later removal.
The intended final asset is a transparent-background RGBA PNG after post-processing.
""".strip()

COVER_FIXED_PROMPT = """
You are an excellent game key art designer and 2D game cover artist.
Your task is to generate an independent display cover image for a Yahaha_Play game.

Asset type: game cover art.
Target asset path: assets/cover.png.
Required output size: 1280x720.
Definition: a polished promotional cover image that communicates the game's theme, mood, genre, main character fantasy, and core action at a glance.
This cover is display-only and is not used as the runtime background.
Do not derive this image from background.png.
Do not simply add title text over a background.
Do not include UI panels, HUD, buttons, menus, watermarks, logos, or fake app chrome.
Avoid readable text unless the user explicitly requested text as part of the artwork.
Use the confirmed game content and visual style to create a clear, attractive hero composition.
""".strip()

SENSITIVE_PATTERN = re.compile(
    r"(X-Amz-Signature=|Authorization:|Bearer\s+[A-Za-z0-9._-]+|sk-[A-Za-z0-9]+)",
    re.IGNORECASE,
)


def build_asset_prompts(state: GenerationState) -> dict[str, dict[str, Any]]:
    """Build separate generation prompts for background, player, and cover assets."""
    game_prompt = _game_description_prompt(state)
    return {
        "background": {
            "target_path": "assets/background.png",
            "model_size": "1280x720",
            "fixed_prompt": BACKGROUND_FIXED_PROMPT,
            "game_prompt": game_prompt,
            "reference_prompt": _reference_prompt(state, "assets/background.png"),
            "prompt": _join_prompt(
                BACKGROUND_FIXED_PROMPT,
                game_prompt,
                _reference_prompt(state, "assets/background.png"),
            ),
        },
        "player": {
            "target_path": "assets/player.png",
            "model_size": "1024x1024",
            "fixed_prompt": PLAYER_FIXED_PROMPT,
            "game_prompt": game_prompt,
            "reference_prompt": _reference_prompt(state, "assets/player.png"),
            "prompt": _join_prompt(
                PLAYER_FIXED_PROMPT,
                game_prompt,
                _reference_prompt(state, "assets/player.png"),
            ),
        },
        "cover": {
            "target_path": "assets/cover.png",
            "model_size": "1280x720",
            "fixed_prompt": COVER_FIXED_PROMPT,
            "game_prompt": game_prompt,
            "reference_prompt": _reference_prompt(state, "assets/cover.png"),
            "prompt": _join_prompt(
                COVER_FIXED_PROMPT,
                game_prompt,
                _reference_prompt(state, "assets/cover.png"),
            ),
        },
    }


def _game_description_prompt(state: GenerationState) -> str:
    payload = {
        "title": state.game_plan.get("title"),
        "introduction": state.game_plan.get("introduction"),
        "gameplay": state.game_plan.get("gameplay"),
        "core_loop": state.game_plan.get("core_loop"),
        "style": state.game_plan.get("style"),
        "characters": state.game_plan.get("characters"),
        "win_condition": state.game_plan.get("win_condition"),
        "lose_condition": state.game_plan.get("lose_condition"),
        "controls": state.game_plan.get("controls"),
        "requirements": {
            "intent_summary": state.user_requirements.get("intent_summary"),
            "must_have": state.user_requirements.get("must_have"),
            "constraints": state.user_requirements.get("constraints"),
        },
    }
    return "Game description prompt:\n" + _sanitize(json.dumps(payload, ensure_ascii=False))


def _reference_prompt(state: GenerationState, target_path: str) -> str:
    task = _task_for_target(state, target_path)
    if not task:
        return "Reference prompt: no user reference image is available; generate from the game description."
    source_asset_id = str(task.get("source_asset_id") or "")
    uploaded = _uploaded_asset_by_id(state, source_asset_id)
    if not uploaded:
        return "Reference prompt: no readable reference image is available; generate from the game description."
    mime_type = str(uploaded.get("mime_type") or "")
    reference_kind = "video keyframe" if mime_type.startswith("video/") else "image"
    usage = _sanitize(str(task.get("usage") or "visual reference"))
    filename = _sanitize(str(uploaded.get("filename") or "uploaded asset"))
    if target_path == "assets/background.png":
        purpose = "background atmosphere, composition, and visual style"
    elif target_path == "assets/player.png":
        purpose = "player character shape, identity, and readable sprite silhouette"
    else:
        purpose = "overall cover mood, key art composition, and visual style"
    return (
        "Reference prompt: use the provided "
        f"{reference_kind} from {filename} only as reference for {purpose}. "
        f"Reference usage from Orchestrator: {usage}. "
        "Do not copy UI, text, signatures, or irrelevant objects from the reference."
    )


def _task_for_target(state: GenerationState, target_path: str) -> dict[str, Any] | None:
    for task in state.asset_work_order.get("uploaded_asset_tasks", []):
        if isinstance(task, dict) and task.get("target_path") == target_path:
            return task
    return None


def _uploaded_asset_by_id(state: GenerationState, asset_id: str) -> dict[str, Any] | None:
    for asset in state.uploaded_assets:
        if str(asset.get("asset_id") or "") == asset_id:
            return asset
    return None


def _join_prompt(*parts: str) -> str:
    return "\n\n".join(part.strip() for part in parts if part.strip())


def _sanitize(value: str) -> str:
    return SENSITIVE_PATTERN.sub("[redacted]", value)
