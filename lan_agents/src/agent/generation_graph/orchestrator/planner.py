"""Orchestrator planner for stage-B parallel generation contracts."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from agent.generation_graph.state import GenerationState
from agent.providers import LLMMessage, LLMProvider, ProviderError, provider_from_env

ORCHESTRATOR_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": [
        "development_brief",
        "asset_work_order",
        "asset_manifest_plan",
        "coding_agent_brief",
        "asset_agent_brief",
        "game_spec",
    ],
    "properties": {
        "development_brief": {"type": "object"},
        "asset_work_order": {"type": "object"},
        "asset_manifest_plan": {"type": "array"},
        "coding_agent_brief": {"type": "object"},
        "asset_agent_brief": {"type": "object"},
        "game_spec": {"type": "object"},
    },
}

ALLOWED_MANIFEST_SOURCES = {"uploaded", "generated", "fallback"}
ALLOWED_ASSET_DECISION_MODES = {
    "code_generated",
    "uploaded_reference",
    "asset_agent_generate",
}
ALLOWED_MANIFEST_KINDS = {"image"}
ALLOWED_BACKGROUND_VALUES = {"scene", "transparent"}
ALLOWED_FIT_VALUES = {"cover", "contain"}
BACKGROUND_PATH = "assets/background.png"
PLAYER_PATH = "assets/player.png"
COVER_PATH = "assets/cover.png"
MVP_TARGET_PATHS = (BACKGROUND_PATH, PLAYER_PATH, COVER_PATH)
TARGET_PATH_ORDER = {
    BACKGROUND_PATH: 0,
    PLAYER_PATH: 1,
    COVER_PATH: 2,
}

ORCHESTRATOR_SYSTEM_PROMPT = """
You are the stage-B Orchestrator for Yahaha_Play.

Given one confirmed game session, produce one compact JSON object with exactly these keys:
- development_brief
- asset_work_order
- asset_manifest_plan
- coding_agent_brief
- asset_agent_brief
- game_spec

Goal:
- create aligned parallel contracts for Coding Agent and Asset Agent
- let both agents start from the same target paths and asset names
- keep output implementation-focused and concise

Rules:
- asset_manifest_plan is the source of truth for every asset target_path
- development_brief.allowed_asset_paths must match asset_manifest_plan target_path values
- every target_path used in asset_work_order tasks must already exist in asset_manifest_plan
- this week's MVP allows only these Asset Agent image paths:
  - assets/background.png
  - assets/player.png
  - assets/cover.png
- asset_manifest_plan must always include assets/cover.png as a display-only generated cover
- background/player may be omitted when Coding Agent should draw them procedurally
- use only relative asset paths under assets/
- decide whether each uploaded image/video is background reference or player reference from safe metadata, user hint, filename, material_usage, and game design needs
- visual upload file bytes are consumed by Asset Agent later; Orchestrator should not require image/video file upload support from the LLM provider
- pass readable non-visual reference files as model attachments when provider supports it, so you can improve design and code instructions
- if there is no useful uploaded image/video, prefer code_generated background/player unless the game clearly needs a generated image asset
- request Asset Agent output for every path included in asset_manifest_plan
- non-image/video uploads are reference attachments only; use them to improve development_brief, game_spec, code instructions, and material usage explanations
- ignore audio/file runtime outputs for this week's MVP; never add them to asset_manifest_plan or runtime asset paths
- background.png must target logical size 1280x720
- player.png must target logical size 256x256 and require transparent RGBA background
- cover.png must target logical size 1280x720, must be display_only, and must be generated independently from game content and visual style
- cover.png must not be derived from background.png and must not bake the title text into the image unless the user explicitly requested text in the artwork
- keep development_brief focused on gameplay, entities, controls, HUD, win/lose conditions, and technical constraints
- keep asset_work_order split into asset_decisions, uploaded_asset_tasks and generated_asset_tasks
- coding_agent_brief must tell Coding Agent exactly which asset paths it may reference and which targets should be drawn in code
- asset_agent_brief must tell Asset Agent exactly which image paths to produce and how to use upload references
- coding_agent_brief.asset_paths, asset_agent_brief.asset_paths, development_brief.allowed_asset_paths, and asset_manifest_plan target_path values must match exactly
- asset_decisions must explain background and player strategy for downstream Asset Agent and Coding Agent:
  - mode "code_generated" means no Asset Agent output is needed for that target
  - mode "uploaded_reference" means Asset Agent should use an uploaded image as reference for that target
  - mode "asset_agent_generate" means Asset Agent should generate that target from text/reference context
- do not include markdown, explanations, or extra keys

Required output shape:
- development_brief: title, gameplay_goal, core_loop, scene_layout, entities, controls, win_condition, lose_condition, ui_hud, allowed_asset_paths, technical_constraints
- asset_work_order.asset_decisions[*]: target, target_path, mode, source_asset_id, rationale
- asset_work_order.uploaded_asset_tasks[*]: asset_id, source_asset_id, target_path, usage, transform, required
- asset_work_order.generated_asset_tasks[*]: key, target_path, usage, generation_mode, required
- asset_manifest_plan[*]: asset_id, target_path, kind, required, source, runtime_required, display_only, logical_width, logical_height, alpha_required, background, fit, derived_from, title_source
- coding_agent_brief: goal, asset_paths, code_generated_targets, runtime_asset_paths, notes
- asset_agent_brief: asset_paths, background, player, uploaded_references, notes
- game_spec: archetype plus any compact runtime notes needed by downstream nodes
- asset_manifest_plan[*].background must be exactly "scene" or "transparent":
  - background.png uses "scene"
  - player.png uses "transparent"
  - cover.png uses "scene"
- asset_manifest_plan[*].source must be exactly "uploaded", "generated", or "fallback"
- asset_manifest_plan[*].kind must be exactly "image"
""".strip()

LIST_SPLIT_PATTERN = re.compile(r"\s*(?:,|，|、|;|；|\n+|->|=>|→)\s*")


class OrchestratorPlanner:
    """Build aligned development and asset contracts from confirmed inputs."""

    def __init__(self, provider: LLMProvider | None = None) -> None:
        self._provider = provider or provider_from_env()

    def plan(self, state: GenerationState) -> dict[str, Any]:
        fallback = deterministic_contracts(state)
        try:
            messages = _messages_from_state(state)
            attachments = _reference_attachments_from_state(state, require_readable=True)
            if attachments and hasattr(self._provider, "complete_json_with_attachments"):
                llm_result = self._provider.complete_json_with_attachments(
                    messages=messages,
                    response_schema=ORCHESTRATOR_SCHEMA,
                    attachments=attachments,
                    temperature=1.0,
                    max_completion_tokens=2200,
                )
            else:
                llm_result = self._provider.complete_json(
                    messages=messages,
                    response_schema=ORCHESTRATOR_SCHEMA,
                    temperature=1.0,
                    max_completion_tokens=2200,
                )
        except Exception as exc:
            reason = str(exc).strip()
            message = "Orchestrator failed while building parallel contracts"
            if reason:
                message = f"{message}: {reason}"
            raise ProviderError(message) from exc

        llm_manifest = llm_result.get("asset_manifest_plan")
        manifest_source = (
            llm_manifest
            if isinstance(llm_manifest, list)
            and (llm_manifest or not fallback["asset_manifest_plan"])
            else fallback["asset_manifest_plan"]
        )
        manifest_plan = _normalize_manifest_plan(manifest_source)
        manifest_paths = [item["target_path"] for item in manifest_plan]
        allowed_paths = set(manifest_paths)
        asset_work_order = _normalize_asset_work_order(
            llm_result.get("asset_work_order") or fallback["asset_work_order"],
            allowed_paths,
        )
        asset_work_order = _complete_asset_work_order(
            asset_work_order,
            fallback["asset_work_order"],
        )
        manifest_plan = _align_manifest_sources_with_work_order(
            manifest_plan, asset_work_order
        )
        development_brief = _normalize_development_brief(
            llm_result.get("development_brief") or fallback["development_brief"],
            manifest_paths,
        )
        game_spec = (
            llm_result.get("game_spec")
            if isinstance(llm_result.get("game_spec"), dict) and llm_result.get("game_spec")
            else fallback["game_spec"]
        )
        coding_agent_brief = _build_coding_agent_brief(
            development_brief, asset_work_order, manifest_paths, game_spec
        )
        asset_agent_brief = _build_asset_agent_brief(
            asset_work_order, manifest_plan, state
        )
        _validate_agent_asset_consistency(
            development_brief=development_brief,
            coding_agent_brief=coding_agent_brief,
            asset_agent_brief=asset_agent_brief,
            manifest_paths=manifest_paths,
        )

        return {
            "development_brief": development_brief,
            "asset_work_order": asset_work_order,
            "asset_manifest_plan": manifest_plan,
            "coding_agent_brief": coding_agent_brief,
            "asset_agent_brief": asset_agent_brief,
            "game_spec": game_spec,
            "generation_status": "planning",
        }


def _build_coding_agent_brief(
    development_brief: dict[str, Any],
    asset_work_order: dict[str, Any],
    asset_paths: list[str],
    game_spec: dict[str, Any],
) -> dict[str, Any]:
    code_generated_targets = [
        item["target"]
        for item in asset_work_order.get("asset_decisions", [])
        if item.get("mode") == "code_generated"
    ]
    return {
        "goal": "Generate the playable static HTML5 game bundle.",
        "asset_paths": asset_paths,
        "runtime_asset_paths": [
            path
            for path in asset_paths
            if path in {BACKGROUND_PATH, PLAYER_PATH}
        ],
        "code_generated_targets": code_generated_targets,
        "gameplay_goal": development_brief.get("gameplay_goal", ""),
        "archetype": game_spec.get("archetype", ""),
        "notes": [
            "Only reference paths listed in asset_paths.",
            "Draw code_generated_targets procedurally in game.js.",
            "Do not wait for Asset Agent when asset_paths is empty.",
        ],
    }


def _build_asset_agent_brief(
    asset_work_order: dict[str, Any],
    manifest_plan: list[dict[str, Any]],
    state: GenerationState,
) -> dict[str, Any]:
    asset_paths = [item["target_path"] for item in manifest_plan]
    decisions = {
        item.get("target"): item
        for item in asset_work_order.get("asset_decisions", [])
        if isinstance(item, dict)
    }
    uploaded_references = []
    for task in asset_work_order.get("uploaded_asset_tasks", []):
        source_asset_id = str(task.get("source_asset_id") or "")
        uploaded = _asset_by_id(state.uploaded_assets, source_asset_id)
        uploaded_references.append(
            {
                "source_asset_id": source_asset_id,
                "filename": str((uploaded or {}).get("filename") or ""),
                "mime_type": str((uploaded or {}).get("mime_type") or ""),
                "target_path": task.get("target_path"),
                "usage": task.get("usage", ""),
                "transform": task.get("transform", ""),
            }
        )
    return {
        "asset_paths": asset_paths,
        "background": _asset_target_brief("background", decisions, asset_paths),
        "player": _asset_target_brief("player", decisions, asset_paths),
        "cover": {
            "target": "cover",
            "target_path": COVER_PATH,
            "required": COVER_PATH in asset_paths,
            "mode": "asset_agent_generate",
            "source_asset_id": "",
            "rationale": "Always generate independent display cover art from game content and style.",
        },
        "uploaded_references": uploaded_references,
        "notes": [
            "Generate only asset_paths listed here.",
            "Always create cover.png as independent display art; do not derive it from background.png or bake title text into it.",
            "Never create audio, video, or PDF runtime assets in this MVP.",
        ],
    }


def _asset_target_brief(
    target: str, decisions: dict[str, dict[str, Any]], asset_paths: list[str]
) -> dict[str, Any]:
    target_path = BACKGROUND_PATH if target == "background" else PLAYER_PATH
    decision = decisions.get(target, {})
    return {
        "target": target,
        "target_path": target_path,
        "required": target_path in asset_paths,
        "mode": decision.get("mode", "code_generated"),
        "source_asset_id": decision.get("source_asset_id", ""),
        "rationale": decision.get("rationale", ""),
    }


def _validate_agent_asset_consistency(
    *,
    development_brief: dict[str, Any],
    coding_agent_brief: dict[str, Any],
    asset_agent_brief: dict[str, Any],
    manifest_paths: list[str],
) -> None:
    expected = list(manifest_paths)
    if list(development_brief.get("allowed_asset_paths", [])) != expected:
        raise ProviderError("development_brief asset paths differ from asset_manifest_plan")
    if list(coding_agent_brief.get("asset_paths", [])) != expected:
        raise ProviderError("coding_agent_brief asset paths differ from asset_manifest_plan")
    if list(asset_agent_brief.get("asset_paths", [])) != expected:
        raise ProviderError("asset_agent_brief asset paths differ from asset_manifest_plan")


def _asset_by_id(assets: list[dict[str, Any]], asset_id: str) -> dict[str, Any] | None:
    for asset in assets:
        if str(asset.get("asset_id") or "") == asset_id:
            return asset
    return None


def determine_game_archetype(
    user_requirements: dict[str, Any], game_plan: dict[str, Any]
) -> str:
    """Infer a stage-B archetype from confirmed tags and gameplay signals."""
    tags = {str(tag).lower() for tag in game_plan.get("tags", [])}
    gameplay = json.dumps(
        {
            "intent_summary": user_requirements.get("intent_summary", ""),
            "gameplay": game_plan.get("gameplay", ""),
            "core_loop": game_plan.get("core_loop", []),
        },
        ensure_ascii=False,
    ).lower()
    if "strategy" in tags:
        return "tower_defense"
    if "puzzle" in tags:
        return "grid_logic"
    if any(tag in tags for tag in {"roleplay", "simulation", "educational", "rhythm"}):
        return "ui_heavy"
    if any(keyword in gameplay for keyword in ["top-down", "俯视", "arena", "四向", "八向"]):
        return "top_down"
    if any(tag in tags for tag in {"action", "arcade", "survival", "casual"}):
        return "top_down"
    return "platformer"


def deterministic_contracts(state: GenerationState) -> dict[str, Any]:
    """Build a minimal aligned contract set from confirmed inputs."""
    archetype = determine_game_archetype(state.user_requirements, state.game_plan)
    manifest_plan = _fallback_manifest_plan(state)
    allowed_paths = [item["target_path"] for item in manifest_plan]
    development_brief = {
        "title": str(state.game_plan.get("title") or "Generated Game").strip(),
        "gameplay_goal": str(
            state.game_plan.get("gameplay") or state.user_requirements.get("intent_summary") or ""
        ).strip(),
        "core_loop": _fallback_core_loop(state.game_plan),
        "scene_layout": f"1280x720 {str(state.game_plan.get('style') or 'single-screen scene').strip()}",
        "entities": _fallback_entities(state.game_plan),
        "controls": str(state.game_plan.get("controls") or "keyboard input").strip(),
        "win_condition": str(state.game_plan.get("win_condition") or "reach the score goal").strip(),
        "lose_condition": str(state.game_plan.get("lose_condition") or "lose all health").strip(),
        "ui_hud": ["score", "timer", "status"],
        "allowed_asset_paths": allowed_paths,
        "technical_constraints": [
            "static-html5-only",
            "iframe-sandbox-allow-scripts",
            "logic-resolution-1280x720",
        ],
    }
    asset_work_order = _fallback_asset_work_order(state, manifest_plan)
    coding_agent_brief = _build_coding_agent_brief(
        development_brief, asset_work_order, allowed_paths, {"archetype": archetype}
    )
    asset_agent_brief = _build_asset_agent_brief(asset_work_order, manifest_plan, state)
    return {
        "development_brief": development_brief,
        "asset_work_order": asset_work_order,
        "asset_manifest_plan": manifest_plan,
        "coding_agent_brief": coding_agent_brief,
        "asset_agent_brief": asset_agent_brief,
        "game_spec": {
            "archetype": archetype,
            "runtime": "html5-iframe",
            "title": development_brief["title"],
        },
    }


def _messages_from_state(state: GenerationState) -> list[LLMMessage]:
    archetype = determine_game_archetype(state.user_requirements, state.game_plan)
    reference_attachments = _reference_attachments_from_state(state)
    payload = {
        "user_requirements": state.user_requirements,
        "game_plan": state.game_plan,
        "material_usage": state.material_usage,
        "uploaded_assets": state.uploaded_assets,
        "reference_attachments": [
            {
                "asset_id": item["asset_id"],
                "filename": item["filename"],
                "mime_type": item["mime_type"],
                "user_hint": item.get("user_hint", ""),
            }
            for item in reference_attachments
        ],
        "asset_registry": state.asset_registry,
        "artifact_workspace": state.artifact_workspace,
        "archetype": archetype,
    }
    return [
        LLMMessage(
            role="system",
            content=ORCHESTRATOR_SYSTEM_PROMPT,
        ),
        LLMMessage(role="user", content=json.dumps(payload, ensure_ascii=False)),
    ]


def _reference_attachments_from_state(
    state: GenerationState, *, require_readable: bool = False
) -> list[dict[str, Any]]:
    """Select user uploads that should be passed as temporary model references."""
    result = []
    for asset in state.uploaded_assets:
        if not isinstance(asset, dict):
            continue
        mime_type = str(asset.get("mime_type") or "").strip().lower()
        if mime_type.startswith(("image/", "video/")):
            continue
        asset_id = str(asset.get("asset_id") or "").strip()
        filename = str(asset.get("filename") or asset_id or "reference-file").strip()
        if not asset_id:
            continue
        local_path = str(
            asset.get("local_path")
            or asset.get("local_fixture_path")
            or asset.get("file_path")
            or ""
        ).strip()
        if require_readable and (not local_path or not Path(local_path).is_file()):
            continue
        result.append(
            {
                "asset_id": asset_id,
                "filename": filename,
                "mime_type": mime_type or "application/octet-stream",
                "local_path": local_path,
                "object_key": str(asset.get("object_key") or "").strip(),
                "user_hint": str(asset.get("user_hint") or "").strip(),
            }
        )
    return result


def _normalize_manifest_plan(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ProviderError("asset_manifest_plan must be a list")
    result: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    for item in value:
        if not isinstance(item, dict):
            raise ProviderError("asset_manifest_plan items must be objects")
        target_path = _require_target_path(item.get("target_path"))
        if target_path in seen_paths:
            raise ProviderError("asset_manifest_plan contains duplicate target_path")
        source = _normalize_source_value(item.get("source"), target_path)
        kind = _normalize_kind_value(item.get("kind"))
        if source not in ALLOWED_MANIFEST_SOURCES:
            raise ProviderError("asset_manifest_plan source is invalid")
        if kind not in ALLOWED_MANIFEST_KINDS:
            raise ProviderError("asset_manifest_plan kind is invalid")
        seen_paths.add(target_path)
        normalized_item = {
            "asset_id": str(item.get("asset_id") or target_path).strip() or target_path,
            "target_path": target_path,
            "kind": kind,
            "required": bool(item.get("required", False)),
            "source": source,
            "runtime_required": bool(item.get("runtime_required", False)),
            "display_only": bool(item.get("display_only", False)),
            "logical_width": _require_positive_int(
                item.get("logical_width"), "asset_manifest_plan logical_width"
            ),
            "logical_height": _require_positive_int(
                item.get("logical_height"), "asset_manifest_plan logical_height"
            ),
            "alpha_required": bool(item.get("alpha_required", False)),
            "background": _normalize_background_value(
                item.get("background"), target_path
            ),
            "fit": str(item.get("fit") or "").strip(),
            "derived_from": str(item.get("derived_from") or "").strip(),
            "title_source": str(item.get("title_source") or "").strip(),
        }
        _normalize_mvp_manifest_contract(normalized_item)
        _validate_mvp_manifest_item(normalized_item)
        result.append(normalized_item)
    if COVER_PATH not in seen_paths:
        result.append(_cover_manifest_item())
        seen_paths.add(COVER_PATH)
    return sorted(result, key=lambda item: TARGET_PATH_ORDER[item["target_path"]])


def _merge_missing_mvp_manifest_items(
    manifest_plan: list[dict[str, Any]], fallback_plan: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    by_path = {item["target_path"]: item for item in manifest_plan}
    for fallback_item in fallback_plan:
        by_path.setdefault(fallback_item["target_path"], fallback_item)
    missing_paths = set(MVP_TARGET_PATHS) - set(by_path)
    if missing_paths:
        raise ProviderError("asset_manifest_plan is missing required MVP target paths")
    return sorted(by_path.values(), key=lambda item: TARGET_PATH_ORDER[item["target_path"]])


def _fallback_manifest_plan(state: GenerationState) -> list[dict[str, Any]]:
    background_asset = _select_background_source_asset(state)
    player_asset = _select_player_source_asset(state)
    result: list[dict[str, Any]] = []
    if background_asset:
        result.append(
            _build_manifest_item(
                asset_id=str(background_asset.get("asset_id") or "asset-background"),
                target_path=BACKGROUND_PATH,
                source="uploaded",
                runtime_required=True,
                display_only=False,
                logical_width=1280,
                logical_height=720,
                alpha_required=False,
                background="scene",
                fit="cover",
            )
        )
    if player_asset:
        result.append(
            _build_manifest_item(
                asset_id=str(player_asset.get("asset_id") or "asset-player"),
                target_path=PLAYER_PATH,
                source="uploaded",
                runtime_required=True,
                display_only=False,
                logical_width=256,
                logical_height=256,
                alpha_required=True,
                background="transparent",
                fit="contain",
            )
        )
    result.append(_cover_manifest_item())
    return result


def _cover_manifest_item() -> dict[str, Any]:
    return _build_manifest_item(
        asset_id="asset-cover",
        target_path=COVER_PATH,
        source="generated",
        runtime_required=False,
        display_only=True,
        logical_width=1280,
        logical_height=720,
        alpha_required=False,
        background="scene",
        fit="cover",
        derived_from="",
        title_source="",
    )


def _normalize_development_brief(
    value: Any, manifest_paths: list[str]
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProviderError("development_brief must be an object")
    required_fields = {
        "title",
        "gameplay_goal",
        "core_loop",
        "scene_layout",
        "entities",
        "controls",
        "win_condition",
        "lose_condition",
        "ui_hud",
        "allowed_asset_paths",
        "technical_constraints",
    }
    missing = [field for field in required_fields if field not in value]
    if missing:
        raise ProviderError(
            f"development_brief missing required fields: {', '.join(sorted(missing))}"
        )
    raw_paths = value.get("allowed_asset_paths", [])
    if raw_paths and not isinstance(raw_paths, list):
        raise ProviderError("development_brief.allowed_asset_paths must be a list")
    return {
        "title": str(value["title"]).strip(),
        "gameplay_goal": str(value["gameplay_goal"]).strip(),
        "core_loop": _string_list(value["core_loop"], "development_brief.core_loop"),
        "scene_layout": str(value["scene_layout"]).strip(),
        "entities": _string_list(value["entities"], "development_brief.entities"),
        "controls": str(value["controls"]).strip(),
        "win_condition": str(value["win_condition"]).strip(),
        "lose_condition": str(value["lose_condition"]).strip(),
        "ui_hud": _string_list(value["ui_hud"], "development_brief.ui_hud"),
        "allowed_asset_paths": manifest_paths,
        "technical_constraints": _string_list(
            value["technical_constraints"], "development_brief.technical_constraints"
        ),
    }


def _fallback_core_loop(game_plan: dict[str, Any]) -> list[str]:
    core_loop = game_plan.get("core_loop")
    if isinstance(core_loop, list) and core_loop:
        return [str(item).strip() for item in core_loop if str(item).strip()]
    gameplay = str(game_plan.get("gameplay") or "").strip()
    if gameplay:
        return [gameplay]
    return ["observe", "act", "progress"]


def _fallback_entities(game_plan: dict[str, Any]) -> list[str]:
    characters = game_plan.get("characters")
    if isinstance(characters, list) and characters:
        normalized = []
        for item in characters:
            if isinstance(item, dict):
                normalized.append(str(item.get("role") or item.get("description") or "entity").strip())
            else:
                normalized.append(str(item).strip())
        normalized = [item for item in normalized if item]
        if normalized:
            return normalized
    return ["player", "goal", "hazard"]


def _normalize_asset_work_order(
    value: Any, allowed_paths: set[str]
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProviderError("asset_work_order must be an object")
    asset_decisions = _normalize_asset_decisions(value.get("asset_decisions", []))
    uploaded_tasks = _normalize_uploaded_tasks(
        value.get("uploaded_asset_tasks", []), allowed_paths
    )
    generated_tasks = _normalize_generated_tasks(
        value.get("generated_asset_tasks", []), allowed_paths
    )
    return {
        "asset_decisions": asset_decisions,
        "uploaded_asset_tasks": uploaded_tasks,
        "generated_asset_tasks": generated_tasks,
    }


def _complete_asset_work_order(
    value: dict[str, Any], fallback: dict[str, Any]
) -> dict[str, Any]:
    uploaded_paths = {
        item["target_path"]
        for item in value.get("uploaded_asset_tasks", [])
        if isinstance(item, dict) and item.get("target_path")
    }
    generated_paths = {
        item["target_path"]
        for item in value.get("generated_asset_tasks", [])
        if isinstance(item, dict) and item.get("target_path")
    }
    covered_paths = uploaded_paths | generated_paths
    uploaded_tasks = list(value.get("uploaded_asset_tasks", []))
    for task in fallback.get("uploaded_asset_tasks", []):
        target_path = task.get("target_path")
        if target_path and target_path not in covered_paths:
            uploaded_tasks.append(task)
            covered_paths.add(target_path)
    generated_tasks = list(value.get("generated_asset_tasks", []))
    for task in fallback.get("generated_asset_tasks", []):
        target_path = task.get("target_path")
        if target_path and target_path not in covered_paths:
            generated_tasks.append(task)
            covered_paths.add(target_path)
    return {
        "asset_decisions": value.get("asset_decisions", []),
        "uploaded_asset_tasks": uploaded_tasks,
        "generated_asset_tasks": generated_tasks,
    }


def _normalize_asset_decisions(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ProviderError("asset_decisions must be a list")
    by_target: dict[str, dict[str, Any]] = {}
    for item in value:
        if not isinstance(item, dict):
            raise ProviderError("asset_decisions items must be objects")
        target_path = _require_target_path(item.get("target_path"))
        if target_path not in {BACKGROUND_PATH, PLAYER_PATH}:
            continue
        target = "background" if target_path == BACKGROUND_PATH else "player"
        mode = str(item.get("mode") or "").strip()
        if mode not in ALLOWED_ASSET_DECISION_MODES:
            raise ProviderError("asset_decisions mode is invalid")
        by_target[target] = {
            "target": target,
            "target_path": target_path,
            "mode": mode,
            "source_asset_id": str(item.get("source_asset_id") or "").strip(),
            "rationale": str(item.get("rationale") or "").strip(),
        }
    result = []
    for target, path in (("background", BACKGROUND_PATH), ("player", PLAYER_PATH)):
        result.append(
            by_target.get(
                target,
                {
                    "target": target,
                    "target_path": path,
                    "mode": "code_generated",
                    "source_asset_id": "",
                    "rationale": "Coding Agent can draw this target directly.",
                },
            )
        )
    return result


def _align_manifest_sources_with_work_order(
    manifest_plan: list[dict[str, Any]], asset_work_order: dict[str, Any]
) -> list[dict[str, Any]]:
    uploaded_paths = {
        item["target_path"]
        for item in asset_work_order.get("uploaded_asset_tasks", [])
        if isinstance(item, dict) and item.get("target_path")
    }
    generated_paths = {
        item["target_path"]
        for item in asset_work_order.get("generated_asset_tasks", [])
        if isinstance(item, dict) and item.get("target_path")
    }
    aligned = []
    for item in manifest_plan:
        next_item = dict(item)
        target_path = next_item["target_path"]
        if target_path in uploaded_paths:
            next_item["source"] = "uploaded"
        elif target_path in generated_paths:
            next_item["source"] = "generated"
        elif target_path == COVER_PATH:
            next_item["source"] = "generated"
        aligned.append(next_item)
    return aligned


def _fallback_asset_work_order(
    state: GenerationState, manifest_plan: list[dict[str, Any]]
) -> dict[str, Any]:
    uploaded_tasks = []
    generated_tasks = []
    background_asset = _select_background_source_asset(state)
    player_asset = _select_player_source_asset(state)
    for item in manifest_plan:
        if item["target_path"] == BACKGROUND_PATH and background_asset:
            uploaded_tasks.append(
                {
                    "asset_id": item["asset_id"],
                    "source_asset_id": str(background_asset.get("asset_id") or item["asset_id"]),
                    "target_path": item["target_path"],
                    "usage": _usage_for_uploaded_asset(
                        str(background_asset.get("asset_id") or item["asset_id"]),
                        state.material_usage,
                    ),
                    "transform": _transform_for_uploaded_target(background_asset, item["target_path"]),
                    "required": False,
                }
            )
            continue
        if item["target_path"] == PLAYER_PATH and player_asset:
            uploaded_tasks.append(
                {
                    "asset_id": item["asset_id"],
                    "source_asset_id": str(player_asset.get("asset_id") or item["asset_id"]),
                    "target_path": item["target_path"],
                    "usage": _usage_for_uploaded_asset(
                        str(player_asset.get("asset_id") or item["asset_id"]),
                        state.material_usage,
                    ),
                    "transform": _transform_for_uploaded_target(player_asset, item["target_path"]),
                    "required": item["required"],
                }
            )
            continue
        if item["source"] in {"generated", "fallback"}:
            generated_tasks.append(
                {
                    "key": item["asset_id"],
                    "target_path": item["target_path"],
                    "usage": _generated_usage_for_target(item["target_path"]),
                    "generation_mode": _generation_mode_for_target(item["target_path"]),
                    "required": item["required"],
                }
            )
    return {
        "asset_decisions": _fallback_asset_decisions(
            background_asset=background_asset,
            player_asset=player_asset,
            manifest_plan=manifest_plan,
        ),
        "uploaded_asset_tasks": uploaded_tasks,
        "generated_asset_tasks": generated_tasks,
    }


def _fallback_asset_decisions(
    *,
    background_asset: dict[str, Any] | None,
    player_asset: dict[str, Any] | None,
    manifest_plan: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    manifest_paths = {item["target_path"] for item in manifest_plan}
    decisions = []
    for target, path, source_asset in (
        ("background", BACKGROUND_PATH, background_asset),
        ("player", PLAYER_PATH, player_asset),
    ):
        if source_asset and path in manifest_paths:
            decisions.append(
                {
                    "target": target,
                    "target_path": path,
                    "mode": "uploaded_reference",
                    "source_asset_id": str(source_asset.get("asset_id") or ""),
                    "rationale": "User uploaded image is useful as visual reference.",
                }
            )
            continue
        if path in manifest_paths:
            decisions.append(
                {
                    "target": target,
                    "target_path": path,
                    "mode": "asset_agent_generate",
                    "source_asset_id": "",
                    "rationale": "Asset Agent should generate this image from the game plan.",
                }
            )
            continue
        decisions.append(
            {
                "target": target,
                "target_path": path,
                "mode": "code_generated",
                "source_asset_id": "",
                "rationale": "Prefer Coding Agent to draw this target directly.",
            }
        )
    return decisions


def _normalize_uploaded_tasks(
    value: Any, allowed_paths: set[str]
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ProviderError("uploaded_asset_tasks must be a list")
    result: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ProviderError("uploaded_asset_tasks items must be objects")
        if str(item.get("target_path") or "").strip() == COVER_PATH:
            continue
        result.append(
            {
                "asset_id": str(item.get("asset_id") or ""),
                "source_asset_id": str(item.get("source_asset_id") or item.get("asset_id") or ""),
                "target_path": _require_allowed_manifest_path(
                    item.get("target_path"), allowed_paths
                ),
                "usage": str(item.get("usage") or "").strip(),
                "transform": str(item.get("transform") or "none").strip(),
                "required": bool(item.get("required", False)),
            }
        )
    return result


def _normalize_generated_tasks(
    value: Any, allowed_paths: set[str]
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ProviderError("generated_asset_tasks must be a list")
    result: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ProviderError("generated_asset_tasks items must be objects")
        result.append(
            {
                "key": str(item.get("key") or ""),
                "target_path": _require_allowed_manifest_path(
                    item.get("target_path"), allowed_paths
                ),
                "usage": str(item.get("usage") or "").strip(),
                "generation_mode": str(item.get("generation_mode") or "placeholder").strip(),
                "required": bool(item.get("required", False)),
            }
        )
    return result


def _fallback_target_path_for_uploaded_asset(asset: dict[str, Any]) -> str:
    mime_type = str(asset.get("mime_type") or "")
    asset_id = str(asset.get("asset_id") or "asset").lower()
    hint = str(asset.get("user_hint") or "").lower()
    if mime_type.startswith("image/") and any(
        keyword in f"{asset_id} {hint}" for keyword in ("cat", "player", "hero", "主角", "小猫")
    ):
        return PLAYER_PATH
    if mime_type.startswith("image/"):
        return BACKGROUND_PATH
    return ""


def _manifest_kind_from_mime_type(mime_type: str) -> str:
    return "image"


def _is_required_uploaded_asset(
    asset: dict[str, Any], material_usage: dict[str, Any]
) -> bool:
    asset_id = str(asset.get("asset_id") or "")
    for item in material_usage.get("assets", []):
        if str(item.get("asset_id") or "") != asset_id:
            continue
        return str(item.get("usage_priority") or "").strip() == "must_use"
    return False


def _usage_for_uploaded_asset(asset_id: str, material_usage: dict[str, Any]) -> str:
    for item in material_usage.get("assets", []):
        if str(item.get("asset_id") or "") != asset_id:
            continue
        return str(item.get("intended_use") or item.get("agent_note") or "uploaded asset").strip()
    return "uploaded asset"


def _default_transform_for_kind(kind: str) -> str:
    if kind == "image":
        return "resize"
    return "none"


def _require_target_path(value: Any) -> str:
    path = str(value or "").strip()
    if not path:
        raise ProviderError("asset_manifest_plan target_path is required")
    if not path.startswith("assets/") or ".." in path or path.startswith("/"):
        raise ProviderError("asset_manifest_plan target_path is invalid")
    if path not in MVP_TARGET_PATHS:
        raise ProviderError("asset_manifest_plan target_path is outside MVP asset contract")
    return path


def _require_allowed_manifest_path(value: Any, allowed_paths: set[str]) -> str:
    path = _require_target_path(value)
    if path not in allowed_paths:
        raise ProviderError("contract path is outside asset_manifest_plan")
    return path


def _string_list(value: Any, field_name: str) -> list[str]:
    items: list[Any]
    if isinstance(value, list):
        items = value
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            raise ProviderError(f"{field_name} must not be empty")
        items = [part for part in LIST_SPLIT_PATTERN.split(text) if part.strip()]
        if not items:
            items = [text]
    else:
        raise ProviderError(f"{field_name} must be a list")
    result = [str(item).strip() for item in items if str(item).strip()]
    if not result:
        raise ProviderError(f"{field_name} must not be empty")
    return result


def _require_positive_int(value: Any, field_name: str) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ProviderError(f"{field_name} must be an integer") from exc
    if number <= 0:
        raise ProviderError(f"{field_name} must be positive")
    return number


def _normalize_background_value(value: Any, target_path: str) -> str:
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if text in {"transparent", "transparent_rgba", "alpha", "rgba", "none", "cutout"}:
        return "transparent"
    if text in {
        "scene",
        "scene_background",
        "background",
        "opaque",
        "solid",
        "full_scene",
        "full_background",
    }:
        return "scene"
    if target_path == PLAYER_PATH:
        return "transparent"
    if target_path == BACKGROUND_PATH:
        return "scene"
    return text


def _normalize_source_value(value: Any, target_path: str) -> str:
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if text in {
        "uploaded",
        "upload",
        "uploaded_asset",
        "user_uploaded",
        "provided",
        "provided_by_user",
        "source_asset",
    }:
        return "uploaded"
    if text in {
        "generated",
        "ai_generated",
        "generated_asset",
        "derived",
        "derived_generated",
        "created",
        "synthesized",
    }:
        return "generated"
    if text in {"fallback", "placeholder", "default"}:
        return "fallback"
    return text


def _normalize_kind_value(value: Any) -> str:
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if text in {
        "image",
        "png",
        "jpg",
        "jpeg",
        "webp",
        "sprite",
        "sprite_png",
        "background_image",
        "character_image",
    }:
        return "image"
    return text


def _normalize_mvp_manifest_contract(item: dict[str, Any]) -> None:
    target_path = item["target_path"]
    if target_path == BACKGROUND_PATH:
        item["runtime_required"] = True
        item["display_only"] = False
        item["logical_width"] = 1280
        item["logical_height"] = 720
        item["alpha_required"] = False
        item["background"] = "scene"
        item["fit"] = "cover"
        item["derived_from"] = ""
        item["title_source"] = ""
    elif target_path == PLAYER_PATH:
        item["runtime_required"] = True
        item["display_only"] = False
        item["logical_width"] = 256
        item["logical_height"] = 256
        item["alpha_required"] = True
        item["background"] = "transparent"
        item["fit"] = "contain"
        item["derived_from"] = ""
        item["title_source"] = ""
    elif target_path == COVER_PATH:
        item["runtime_required"] = False
        item["display_only"] = True
        item["logical_width"] = 1280
        item["logical_height"] = 720
        item["alpha_required"] = False
        item["background"] = "scene"
        item["fit"] = "cover"
        item["source"] = "generated"
        item["derived_from"] = ""
        item["title_source"] = ""


def _build_manifest_item(
    *,
    asset_id: str,
    target_path: str,
    source: str,
    runtime_required: bool,
    display_only: bool,
    logical_width: int,
    logical_height: int,
    alpha_required: bool,
    background: str,
    fit: str,
    derived_from: str = "",
    title_source: str = "",
) -> dict[str, Any]:
    item = {
        "asset_id": asset_id,
        "target_path": target_path,
        "kind": "image",
        "required": True,
        "source": source,
        "runtime_required": runtime_required,
        "display_only": display_only,
        "logical_width": logical_width,
        "logical_height": logical_height,
        "alpha_required": alpha_required,
        "background": background,
        "fit": fit,
        "derived_from": derived_from,
        "title_source": title_source,
    }
    _validate_mvp_manifest_item(item)
    return item


def _validate_mvp_manifest_item(item: dict[str, Any]) -> None:
    if item["background"] not in ALLOWED_BACKGROUND_VALUES:
        raise ProviderError("asset_manifest_plan background is invalid")
    if item["fit"] not in ALLOWED_FIT_VALUES:
        raise ProviderError("asset_manifest_plan fit is invalid")
    if item["target_path"] == BACKGROUND_PATH:
        if item["logical_width"] != 1280 or item["logical_height"] != 720:
            raise ProviderError("background.png must use 1280x720 logical size")
        if not item["runtime_required"] or item["display_only"]:
            raise ProviderError("background.png contract flags are invalid")
        if item["alpha_required"] or item["background"] != "scene" or item["fit"] != "cover":
            raise ProviderError("background.png display contract is invalid")
        if item["derived_from"] or item["title_source"]:
            raise ProviderError("background.png must not be derived")
        return
    if item["target_path"] == PLAYER_PATH:
        if item["logical_width"] != 256 or item["logical_height"] != 256:
            raise ProviderError("player.png must use 256x256 logical size")
        if not item["runtime_required"] or item["display_only"]:
            raise ProviderError("player.png contract flags are invalid")
        if not item["alpha_required"] or item["background"] != "transparent":
            raise ProviderError("player.png must require transparent background")
        if item["fit"] != "contain" or item["derived_from"] or item["title_source"]:
            raise ProviderError("player.png manifest contract is invalid")
        return
    if item["target_path"] == COVER_PATH:
        if item["logical_width"] != 1280 or item["logical_height"] != 720:
            raise ProviderError("cover.png must use 1280x720 logical size")
        if item["runtime_required"] or not item["display_only"]:
            raise ProviderError("cover.png contract flags are invalid")
        if item["alpha_required"] or item["background"] != "scene" or item["fit"] != "cover":
            raise ProviderError("cover.png display contract is invalid")
        if item["source"] != "generated":
            raise ProviderError("cover.png must be generated independently")
        if item["derived_from"] or item["title_source"]:
            raise ProviderError("cover.png must not be derived from background or title")
        return


def _material_usage_map(state: GenerationState) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("asset_id") or ""): item
        for item in state.material_usage.get("assets", [])
        if isinstance(item, dict)
    }


def _asset_context_text(asset: dict[str, Any], usage: dict[str, Any] | None) -> str:
    values = [
        asset.get("asset_id"),
        asset.get("filename"),
        asset.get("user_hint"),
        (usage or {}).get("intended_use"),
        (usage or {}).get("usage_priority"),
        (usage or {}).get("user_hint"),
        (usage or {}).get("agent_note"),
    ]
    return " ".join(str(value or "") for value in values).lower()


def _select_player_source_asset(state: GenerationState) -> dict[str, Any] | None:
    usage_map = _material_usage_map(state)
    best_asset: dict[str, Any] | None = None
    best_score = -1
    for asset in state.uploaded_assets:
        mime_type = str(asset.get("mime_type") or "")
        if not mime_type.startswith(("image/", "video/")):
            continue
        usage = usage_map.get(str(asset.get("asset_id") or ""))
        text = _asset_context_text(asset, usage)
        score = 10
        if "must_use" in text:
            score += 50
        if any(keyword in text for keyword in ("character", "player", "hero", "主角", "小猫", "cat")):
            score += 100
        if score > best_score:
            best_score = score
            best_asset = asset
    return best_asset


def _select_background_source_asset(state: GenerationState) -> dict[str, Any] | None:
    usage_map = _material_usage_map(state)
    player_asset_id = str((_select_player_source_asset(state) or {}).get("asset_id") or "")
    best_asset: dict[str, Any] | None = None
    best_score = -1
    for asset in state.uploaded_assets:
        mime_type = str(asset.get("mime_type") or "")
        if not mime_type.startswith(("image/", "video/")):
            continue
        asset_id = str(asset.get("asset_id") or "")
        if asset_id and asset_id == player_asset_id:
            continue
        usage = usage_map.get(asset_id)
        text = _asset_context_text(asset, usage)
        score = 10
        if mime_type.startswith("video/"):
            score += 30
        if any(
            keyword in text
            for keyword in ("background", "scene", "forest", "landscape", "背景", "森林", "氛围")
        ):
            score += 100
        if score > best_score:
            best_score = score
            best_asset = asset
    return best_asset


def _transform_for_uploaded_target(asset: dict[str, Any], target_path: str) -> str:
    mime_type = str(asset.get("mime_type") or "")
    if target_path == BACKGROUND_PATH:
        if mime_type.startswith("video/"):
            return "extract_keyframe_resize_cover"
        return "resize_to_background_cover"
    if target_path == PLAYER_PATH:
        return "remove_background_and_resize_rgba"
    return "none"


def _generated_usage_for_target(target_path: str) -> str:
    if target_path == BACKGROUND_PATH:
        return "main background image"
    if target_path == PLAYER_PATH:
        return "player character sprite"
    if target_path == COVER_PATH:
        return "independent display cover art based on game content and style"
    return "generated image"


def _generation_mode_for_target(target_path: str) -> str:
    if target_path == BACKGROUND_PATH:
        return "illustrate_scene"
    if target_path == PLAYER_PATH:
        return "illustrate_character_transparent_background"
    if target_path == COVER_PATH:
        return "illustrate_independent_cover_art"
    return "illustrate_image"
