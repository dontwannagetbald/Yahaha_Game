import json
from pathlib import Path

from agent.generation_graph.orchestrator.build_parallel_contracts.node import (
    build_parallel_contracts,
)
from agent.generation_graph.orchestrator.planner import (
    OrchestratorPlanner,
    _messages_from_state,
    determine_game_archetype,
)
from agent.generation_graph.state import GenerationState
from agent.providers import LLMMessage, MockLLMProvider


BACKGROUND_PATH = "assets/background.png"
PLAYER_PATH = "assets/player.png"
COVER_PATH = "assets/cover.png"


def _load_generation_fixture() -> dict:
    fixture_path = (
        Path(__file__).parents[2]
        / "src"
        / "agent"
        / "generation_graph"
        / "fixtures"
        / "generation_confirmed_session.json"
    )
    return json.loads(fixture_path.read_text())


def _manifest_by_path(update: dict) -> dict[str, dict]:
    return {item["target_path"]: item for item in update["asset_manifest_plan"]}


def _base_development_brief(paths: list[str]) -> dict:
    return {
        "title": "星星小猫冒险",
        "gameplay_goal": "躲避障碍并收集星星",
        "core_loop": ["移动", "躲避", "收集"],
        "scene_layout": "1280x720 单屏森林场景",
        "entities": ["player", "hazard", "star"],
        "controls": "方向键或 WASD 移动",
        "win_condition": "倒计时结束分数达标",
        "lose_condition": "生命值归零",
        "ui_hud": ["score", "timer", "hp"],
        "allowed_asset_paths": paths,
        "technical_constraints": ["static-html5-only"],
    }


def _background_manifest(**overrides) -> dict:
    item = {
        "asset_id": "asset-background",
        "target_path": BACKGROUND_PATH,
        "kind": "image",
        "required": True,
        "source": "generated",
        "runtime_required": True,
        "display_only": False,
        "logical_width": 1280,
        "logical_height": 720,
        "alpha_required": False,
        "background": "scene",
        "fit": "cover",
        "derived_from": "",
        "title_source": "",
    }
    item.update(overrides)
    return item


def _player_manifest(**overrides) -> dict:
    item = {
        "asset_id": "asset-player",
        "target_path": PLAYER_PATH,
        "kind": "image",
        "required": True,
        "source": "uploaded",
        "runtime_required": True,
        "display_only": False,
        "logical_width": 256,
        "logical_height": 256,
        "alpha_required": True,
        "background": "transparent",
        "fit": "contain",
        "derived_from": "",
        "title_source": "",
    }
    item.update(overrides)
    return item


def _cover_manifest(**overrides) -> dict:
    item = {
        "asset_id": "asset-cover",
        "target_path": COVER_PATH,
        "kind": "image",
        "required": True,
        "source": "generated",
        "runtime_required": False,
        "display_only": True,
        "logical_width": 1280,
        "logical_height": 720,
        "alpha_required": False,
        "background": "scene",
        "fit": "cover",
        "derived_from": "",
        "title_source": "",
    }
    item.update(overrides)
    return item


def _three_asset_response() -> dict:
    paths = [BACKGROUND_PATH, PLAYER_PATH, COVER_PATH]
    return {
        "development_brief": _base_development_brief(paths),
        "asset_work_order": {
            "asset_decisions": [
                {
                    "target": "background",
                    "target_path": BACKGROUND_PATH,
                    "mode": "asset_agent_generate",
                    "source_asset_id": "",
                    "rationale": "森林场景需要稳定背景图。",
                },
                {
                    "target": "player",
                    "target_path": PLAYER_PATH,
                    "mode": "uploaded_reference",
                    "source_asset_id": "asset-cat-image",
                    "rationale": "用户上传图片适合作为小猫角色参考。",
                },
            ],
            "uploaded_asset_tasks": [
                {
                    "asset_id": "asset-cat-image",
                    "source_asset_id": "asset-cat-image",
                    "target_path": PLAYER_PATH,
                    "usage": "player character sprite",
                    "transform": "remove_background_and_resize_rgba",
                    "required": True,
                }
            ],
            "generated_asset_tasks": [
                {
                    "key": "background",
                    "target_path": BACKGROUND_PATH,
                    "usage": "main background image",
                    "generation_mode": "illustrate_scene",
                    "required": True,
                },
                {
                    "key": "asset-cover",
                    "target_path": COVER_PATH,
                    "usage": "independent display cover based on game content and style",
                    "generation_mode": "illustrate_independent_cover_art",
                    "required": True,
                },
            ],
        },
        "asset_manifest_plan": [
            _background_manifest(),
            _player_manifest(),
            _cover_manifest(),
        ],
        "game_spec": {"archetype": "top_down", "camera": "single-screen"},
    }


class RecordingAttachmentProvider(MockLLMProvider):
    def __init__(self, response: dict) -> None:
        super().__init__(response=response)
        self.attachment_calls: list[dict] = []

    def complete_json_with_attachments(
        self,
        *,
        messages: list[LLMMessage],
        response_schema: dict,
        attachments: list[dict],
        temperature: float = 1.0,
        max_completion_tokens: int = 1200,
    ) -> dict:
        self.attachment_calls.append(
            {
                "messages": messages,
                "response_schema": response_schema,
                "attachments": attachments,
                "temperature": temperature,
                "max_completion_tokens": max_completion_tokens,
            }
        )
        return super().complete_json(
            messages=messages,
            response_schema=response_schema,
            temperature=temperature,
            max_completion_tokens=max_completion_tokens,
        )


def test_orchestrator_generates_optional_background_player_contracts_for_mvp_bundle() -> None:
    provider = MockLLMProvider(response=_three_asset_response())
    state = GenerationState(**_load_generation_fixture())

    update = OrchestratorPlanner(provider=provider).plan(state)
    manifest = _manifest_by_path(update)

    assert update["development_brief"]["allowed_asset_paths"] == [
        BACKGROUND_PATH,
        PLAYER_PATH,
        COVER_PATH,
    ]
    assert set(manifest) == {BACKGROUND_PATH, PLAYER_PATH, COVER_PATH}
    assert manifest[BACKGROUND_PATH]["logical_width"] == 1280
    assert manifest[PLAYER_PATH]["alpha_required"] is True
    assert manifest[COVER_PATH]["runtime_required"] is False
    assert manifest[COVER_PATH]["display_only"] is True
    assert manifest[COVER_PATH]["derived_from"] == ""
    assert manifest[COVER_PATH]["title_source"] == ""


def test_orchestrator_outputs_child_agent_briefs_with_consistent_asset_paths() -> None:
    provider = MockLLMProvider(response=_three_asset_response())
    state = GenerationState(**_load_generation_fixture())

    update = OrchestratorPlanner(provider=provider).plan(state)
    manifest_paths = [item["target_path"] for item in update["asset_manifest_plan"]]

    assert update["coding_agent_brief"]["asset_paths"] == manifest_paths
    assert update["asset_agent_brief"]["asset_paths"] == manifest_paths
    assert update["development_brief"]["allowed_asset_paths"] == manifest_paths


def test_orchestrator_always_requests_independent_cover_when_no_visual_uploads_are_needed() -> None:
    fixture = _load_generation_fixture()
    fixture["uploaded_assets"] = []
    fixture["material_usage"] = {"assets": []}
    state = GenerationState(**fixture)

    update = OrchestratorPlanner(provider=MockLLMProvider(response={})).plan(state)
    manifest = _manifest_by_path(update)

    assert set(manifest) == {COVER_PATH}
    assert manifest[COVER_PATH]["source"] == "generated"
    assert manifest[COVER_PATH]["runtime_required"] is False
    assert manifest[COVER_PATH]["display_only"] is True
    assert manifest[COVER_PATH]["derived_from"] == ""
    assert manifest[COVER_PATH]["title_source"] == ""
    assert [item["mode"] for item in update["asset_work_order"]["asset_decisions"]] == [
        "code_generated",
        "code_generated",
    ]
    assert update["coding_agent_brief"]["asset_paths"] == [COVER_PATH]
    assert update["coding_agent_brief"]["runtime_asset_paths"] == []
    assert update["asset_agent_brief"]["asset_paths"] == [COVER_PATH]


def test_orchestrator_uses_uploaded_image_and_video_only_for_background_player_assets() -> None:
    state = GenerationState(**_load_generation_fixture())

    update = OrchestratorPlanner(provider=MockLLMProvider(response={})).plan(state)
    manifest_paths = {item["target_path"] for item in update["asset_manifest_plan"]}
    decisions_by_target = {
        item["target"]: item for item in update["asset_work_order"]["asset_decisions"]
    }

    assert manifest_paths == {BACKGROUND_PATH, PLAYER_PATH, COVER_PATH}
    assert decisions_by_target["background"]["source_asset_id"] == "asset-forest-video"
    assert decisions_by_target["background"]["mode"] == "uploaded_reference"
    assert decisions_by_target["player"]["source_asset_id"] == "asset-cat-image"
    assert decisions_by_target["player"]["mode"] == "uploaded_reference"


def test_orchestrator_preserves_uploaded_background_when_llm_only_requests_player_revision() -> None:
    response = _three_asset_response()
    response["asset_manifest_plan"] = [
        _player_manifest(source="generated"),
        _cover_manifest(),
    ]
    response["development_brief"] = _base_development_brief([PLAYER_PATH, COVER_PATH])
    response["asset_work_order"] = {
        "asset_decisions": [
            {
                "target": "background",
                "target_path": BACKGROUND_PATH,
                "mode": "code_generated",
                "source_asset_id": "",
                "rationale": "Only the character is being revised.",
            },
            {
                "target": "player",
                "target_path": PLAYER_PATH,
                "mode": "asset_agent_generate",
                "source_asset_id": "",
                "rationale": "Generate a new player sprite for the revision.",
            },
        ],
        "uploaded_asset_tasks": [],
        "generated_asset_tasks": [
            {
                "key": "asset-player",
                "target_path": PLAYER_PATH,
                "usage": "player character sprite",
                "generation_mode": "illustrate_character_transparent_background",
                "required": True,
            },
            {
                "key": "asset-cover",
                "target_path": COVER_PATH,
                "usage": "independent display cover based on game content and style",
                "generation_mode": "illustrate_independent_cover_art",
                "required": True,
            },
        ],
    }
    fixture = _load_generation_fixture()
    fixture["uploaded_assets"] = [
        {
            "asset_id": "asset-flower-background",
            "filename": "background.jpg",
            "mime_type": "image/jpeg",
            "local_path": "fixtures/uploads/background.jpg",
            "user_hint": "",
        }
    ]
    fixture["material_usage"] = {
        "assets": [
            {
                "asset_id": "asset-flower-background",
                "filename": "background.jpg",
                "mime_type": "image/jpeg",
                "intended_use": "background",
                "usage_priority": "supporting",
                "agent_note": "用户要求用这个做背景图片。",
            }
        ]
    }
    state = GenerationState(**fixture)

    update = OrchestratorPlanner(provider=MockLLMProvider(response=response)).plan(state)
    manifest = _manifest_by_path(update)
    uploaded_tasks = {
        item["target_path"]: item
        for item in update["asset_work_order"]["uploaded_asset_tasks"]
    }
    decisions_by_target = {
        item["target"]: item for item in update["asset_work_order"]["asset_decisions"]
    }

    assert set(manifest) == {BACKGROUND_PATH, PLAYER_PATH, COVER_PATH}
    assert manifest[BACKGROUND_PATH]["source"] == "uploaded"
    assert uploaded_tasks[BACKGROUND_PATH]["source_asset_id"] == "asset-flower-background"
    assert decisions_by_target["background"]["mode"] == "uploaded_reference"
    assert update["coding_agent_brief"]["runtime_asset_paths"] == [
        BACKGROUND_PATH,
        PLAYER_PATH,
    ]


def test_orchestrator_passes_only_non_visual_files_as_model_references(
    tmp_path: Path,
) -> None:
    provider = RecordingAttachmentProvider(response=_three_asset_response())
    cat_file = tmp_path / "cat.png"
    cat_file.write_bytes(b"png")
    audio_file = tmp_path / "pop.wav"
    audio_file.write_bytes(b"wav")
    rules_file = tmp_path / "rules.pdf"
    rules_file.write_bytes(b"%PDF-1.4")
    state = GenerationState(**_load_generation_fixture())
    for asset in state.uploaded_assets:
        if asset["asset_id"] == "asset-cat-image":
            asset["local_path"] = str(cat_file)
        if asset["asset_id"] == "asset-pop-audio":
            asset["local_path"] = str(audio_file)
        if asset["asset_id"] == "asset-rules-file":
            asset["local_path"] = str(rules_file)

    update = OrchestratorPlanner(provider=provider).plan(state)

    attachment_ids = {
        attachment["asset_id"]
        for attachment in provider.attachment_calls[0]["attachments"]
    }
    assert attachment_ids == {
        "asset-pop-audio",
        "asset-rules-file",
    }
    assert "asset-cat-image" not in attachment_ids
    assert "asset-forest-video" not in attachment_ids
    assert "asset-cat-image" in provider.attachment_calls[0]["messages"][-1].content
    assert COVER_PATH in str(update["asset_manifest_plan"])


def test_orchestrator_normalizes_cover_path_from_llm_as_independent_generated_asset() -> None:
    response = _three_asset_response()
    response["asset_manifest_plan"] = [
        _background_manifest(),
        _player_manifest(),
        _cover_manifest(
            source="uploaded",
            runtime_required=True,
            display_only=False,
            alpha_required=True,
            background="transparent",
            fit="contain",
            derived_from=PLAYER_PATH,
            title_source="custom_title",
        ),
    ]
    provider = MockLLMProvider(response=response)
    state = GenerationState(**_load_generation_fixture())

    update = OrchestratorPlanner(provider=provider).plan(state)
    manifest = _manifest_by_path(update)

    assert set(manifest) == {BACKGROUND_PATH, PLAYER_PATH, COVER_PATH}
    assert manifest[COVER_PATH]["source"] == "generated"
    assert manifest[COVER_PATH]["runtime_required"] is False
    assert manifest[COVER_PATH]["display_only"] is True
    assert manifest[COVER_PATH]["alpha_required"] is False
    assert manifest[COVER_PATH]["background"] == "scene"
    assert manifest[COVER_PATH]["fit"] == "cover"
    assert manifest[COVER_PATH]["derived_from"] == ""
    assert manifest[COVER_PATH]["title_source"] == ""


def test_orchestrator_moves_llm_uploaded_cover_task_to_generated_task() -> None:
    response = _three_asset_response()
    response["asset_work_order"]["uploaded_asset_tasks"].append(
        {
            "asset_id": "asset-cover",
            "source_asset_id": "asset-cat-image",
            "target_path": COVER_PATH,
            "usage": "cover reference",
            "transform": "resize_to_cover",
            "required": True,
        }
    )
    response["asset_work_order"]["generated_asset_tasks"] = [
        task
        for task in response["asset_work_order"]["generated_asset_tasks"]
        if task["target_path"] != COVER_PATH
    ]
    provider = MockLLMProvider(response=response)
    state = GenerationState(**_load_generation_fixture())

    update = OrchestratorPlanner(provider=provider).plan(state)

    assert all(
        task["target_path"] != COVER_PATH
        for task in update["asset_work_order"]["uploaded_asset_tasks"]
    )
    assert any(
        task["target_path"] == COVER_PATH
        and task["generation_mode"] == "illustrate_independent_cover_art"
        for task in update["asset_work_order"]["generated_asset_tasks"]
    )


def test_build_parallel_contracts_keeps_parallelizable_contract_boundary() -> None:
    provider = MockLLMProvider(response=_three_asset_response())
    state = GenerationState(**_load_generation_fixture())

    update = build_parallel_contracts(state, provider=provider)

    manifest_paths = {item["target_path"] for item in update["asset_manifest_plan"]}
    assert manifest_paths == {BACKGROUND_PATH, PLAYER_PATH, COVER_PATH}
    assert set(update["development_brief"]["allowed_asset_paths"]) == manifest_paths
    assert update["asset_work_order"]["uploaded_asset_tasks"][0]["source_asset_id"] == (
        "asset-cat-image"
    )
    assert any(
        task["target_path"] == COVER_PATH
        and task["generation_mode"] == "illustrate_independent_cover_art"
        for task in update["asset_work_order"]["generated_asset_tasks"]
    )


def test_determine_game_archetype_prefers_confirmed_tags_and_gameplay() -> None:
    fixture = _load_generation_fixture()
    archetype = determine_game_archetype(
        fixture["user_requirements"], fixture["game_plan"]
    )
    assert archetype == "top_down"


def test_orchestrator_fallback_uses_uploaded_video_and_image_references() -> None:
    provider = MockLLMProvider(
        response={
            "development_brief": {},
            "asset_work_order": {},
            "asset_manifest_plan": [],
            "game_spec": {},
        }
    )
    state = GenerationState(**_load_generation_fixture())

    update = OrchestratorPlanner(provider=provider).plan(state)
    manifest = _manifest_by_path(update)

    assert set(manifest) == {BACKGROUND_PATH, PLAYER_PATH, COVER_PATH}
    assert manifest[BACKGROUND_PATH]["source"] == "uploaded"
    assert manifest[PLAYER_PATH]["source"] == "uploaded"
    assert manifest[COVER_PATH]["source"] == "generated"
    uploaded_tasks = {
        item["target_path"]: item
        for item in update["asset_work_order"]["uploaded_asset_tasks"]
    }
    assert uploaded_tasks[BACKGROUND_PATH]["source_asset_id"] == "asset-forest-video"
    assert uploaded_tasks[BACKGROUND_PATH]["usage"] == "background_reference"
    assert uploaded_tasks[BACKGROUND_PATH]["transform"] == "extract_keyframe_resize_cover"
    assert uploaded_tasks[PLAYER_PATH]["source_asset_id"] == "asset-cat-image"
    assert uploaded_tasks[PLAYER_PATH]["usage"] == "character_reference"
    assert uploaded_tasks[PLAYER_PATH]["transform"] == "remove_background_and_resize_rgba"
    assert uploaded_tasks[PLAYER_PATH]["required"] is True
    assert [task["target_path"] for task in update["asset_work_order"]["generated_asset_tasks"]] == [
        COVER_PATH
    ]
    assert update["asset_work_order"]["asset_decisions"][0]["mode"] == "uploaded_reference"
    assert update["asset_work_order"]["asset_decisions"][1]["mode"] == "uploaded_reference"


def test_orchestrator_fallback_prefers_code_generation_when_no_uploads() -> None:
    provider = MockLLMProvider(
        response={
            "development_brief": {},
            "asset_work_order": {},
            "asset_manifest_plan": [],
            "game_spec": {},
        }
    )
    fixture = _load_generation_fixture()
    fixture["uploaded_assets"] = []
    fixture["material_usage"] = {"assets": []}
    state = GenerationState(**fixture)

    update = OrchestratorPlanner(provider=provider).plan(state)
    manifest = _manifest_by_path(update)

    assert set(manifest) == {COVER_PATH}
    assert update["development_brief"]["allowed_asset_paths"] == [COVER_PATH]
    assert update["asset_work_order"]["uploaded_asset_tasks"] == []
    assert [task["target_path"] for task in update["asset_work_order"]["generated_asset_tasks"]] == [
        COVER_PATH
    ]
    assert update["asset_work_order"]["asset_decisions"][0]["mode"] == "code_generated"
    assert update["asset_work_order"]["asset_decisions"][1]["mode"] == "code_generated"


def test_orchestrator_accepts_string_list_fields_from_llm() -> None:
    response = _three_asset_response()
    response["development_brief"]["core_loop"] = "移动，躲避，收集"
    response["development_brief"]["entities"] = "player, hazard, star"
    response["development_brief"]["ui_hud"] = "score, timer, hp"
    response["development_brief"]["technical_constraints"] = (
        "static-html5-only, iframe-sandbox-allow-scripts"
    )
    provider = MockLLMProvider(response=response)
    state = GenerationState(**_load_generation_fixture())

    update = OrchestratorPlanner(provider=provider).plan(state)

    assert update["development_brief"]["core_loop"] == ["移动", "躲避", "收集"]
    assert update["development_brief"]["entities"] == ["player", "hazard", "star"]
    assert update["development_brief"]["ui_hud"] == ["score", "timer", "hp"]
    assert update["development_brief"]["technical_constraints"] == [
        "static-html5-only",
        "iframe-sandbox-allow-scripts",
    ]


def test_orchestrator_normalizes_llm_manifest_aliases() -> None:
    response = _three_asset_response()
    response["asset_manifest_plan"] = [
        _background_manifest(
            source="ai_generated",
            kind="background_image",
            background="opaque",
            derived_from="uploaded/video.mp4",
            title_source="game_plan.title",
        ),
        _player_manifest(
            source="user_uploaded",
            kind="sprite_png",
            background="transparent_rgba",
            derived_from=BACKGROUND_PATH,
            title_source="game_plan.title",
        ),
        _cover_manifest(
            source="placeholder",
            kind="background_image",
            background="opaque",
            derived_from="uploaded/video.mp4",
            title_source="custom",
        ),
    ]
    provider = MockLLMProvider(response=response)
    state = GenerationState(**_load_generation_fixture())

    update = OrchestratorPlanner(provider=provider).plan(state)
    manifest = _manifest_by_path(update)

    assert manifest[BACKGROUND_PATH]["source"] == "generated"
    assert manifest[BACKGROUND_PATH]["kind"] == "image"
    assert manifest[BACKGROUND_PATH]["background"] == "scene"
    assert manifest[BACKGROUND_PATH]["derived_from"] == ""
    assert manifest[BACKGROUND_PATH]["title_source"] == ""
    assert manifest[PLAYER_PATH]["source"] == "uploaded"
    assert manifest[PLAYER_PATH]["kind"] == "image"
    assert manifest[PLAYER_PATH]["background"] == "transparent"
    assert manifest[PLAYER_PATH]["derived_from"] == ""
    assert manifest[PLAYER_PATH]["title_source"] == ""
    assert manifest[COVER_PATH]["source"] == "generated"
    assert manifest[COVER_PATH]["derived_from"] == ""
    assert manifest[COVER_PATH]["title_source"] == ""


def test_orchestrator_aligns_manifest_sources_with_asset_work_order() -> None:
    response = _three_asset_response()
    response["asset_manifest_plan"] = [
        _background_manifest(source="uploaded"),
        _player_manifest(source="generated"),
    ]
    provider = MockLLMProvider(response=response)
    state = GenerationState(**_load_generation_fixture())

    update = OrchestratorPlanner(provider=provider).plan(state)
    manifest = _manifest_by_path(update)

    assert manifest[BACKGROUND_PATH]["source"] == "generated"
    assert manifest[PLAYER_PATH]["source"] == "uploaded"
    assert manifest[COVER_PATH]["source"] == "generated"


def test_orchestrator_prompt_stays_compact_and_contract_focused() -> None:
    state = GenerationState(**_load_generation_fixture())

    messages = _messages_from_state(state)

    assert len(messages) == 2
    system_prompt = messages[0].content
    assert BACKGROUND_PATH in system_prompt
    assert PLAYER_PATH in system_prompt
    assert COVER_PATH in system_prompt
    assert "1280x720" in system_prompt
    assert "transparent" in system_prompt
    assert "image/*" not in system_prompt
    assert "video/*" not in system_prompt
    assert len(system_prompt) < 5000
