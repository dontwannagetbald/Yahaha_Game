from pathlib import Path
import threading
import time

from agent.generation_graph.asset_agent.prompt_builder import build_asset_prompts
from agent.generation_graph.asset_agent.run_asset_agent.node import run_asset_agent
from agent.generation_graph.asset_agent.tools.image_processing import (
    write_mock_background,
    write_mock_player_raw,
)
from agent.generation_graph.asset_agent.tools.png_codec import read_png_info, write_png_rgba
from agent.generation_graph.state import GenerationState
from agent.providers import ProviderError


BACKGROUND_PATH = "assets/background.png"
PLAYER_PATH = "assets/player.png"
COVER_PATH = "assets/cover.png"


class FakeImageClient:
    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.edit_calls: list[dict] = []

    def generate_png(self, *, prompt: str, size: str, output_path: Path) -> None:
        self.calls.append({"prompt": prompt, "size": size, "output_path": output_path})
        if output_path.name in {"background.png", "cover.png"}:
            write_mock_background(output_path)
            return
        write_mock_player_raw(output_path)

    def edit_png(
        self,
        *,
        prompt: str,
        size: str,
        input_path: Path,
        output_path: Path,
    ) -> None:
        self.edit_calls.append(
            {
                "prompt": prompt,
                "size": size,
                "input_path": input_path,
                "output_path": output_path,
            }
        )
        if output_path.name == "background.png":
            write_mock_background(output_path)
            return
        write_mock_player_raw(output_path)


class OverlapDetectingImageClient(FakeImageClient):
    def __init__(self, *, expected_calls: int) -> None:
        super().__init__()
        self.expected_calls = expected_calls
        self.started_calls = 0
        self.active_calls = 0
        self.max_active_calls = 0
        self._condition = threading.Condition()

    def generate_png(self, *, prompt: str, size: str, output_path: Path) -> None:
        with self._condition:
            self.started_calls += 1
            self.active_calls += 1
            self.max_active_calls = max(self.max_active_calls, self.active_calls)
            self._condition.notify_all()
            deadline = time.monotonic() + 0.2
            while (
                self.started_calls < self.expected_calls
                and time.monotonic() < deadline
            ):
                self._condition.wait(timeout=0.01)
        try:
            super().generate_png(prompt=prompt, size=size, output_path=output_path)
        finally:
            with self._condition:
                self.active_calls -= 1
                self._condition.notify_all()


def _build_state(tmp_path: Path) -> GenerationState:
    return GenerationState(
        job_context={"job_id": "job-asset-test", "user_id": "user-asset-test"},
        user_requirements={
            "intent_summary": "可爱卡通森林里的小猫收集星星小游戏",
            "must_have": ["小猫主角", "森林背景"],
        },
        game_plan={
            "title": "星星小猫冒险",
            "introduction": "帮助小猫在森林里收集星星并避开障碍。",
            "gameplay": "玩家控制小猫左右移动，收集星星得分并躲避障碍。",
            "core_loop": ["观察", "移动", "收集", "躲避"],
            "style": "可爱卡通森林",
            "characters": [{"role": "player", "description": "圆滚滚的小猫"}],
            "win_condition": "倒计时结束分数达标",
            "lose_condition": "生命值归零",
            "controls": "方向键或 WASD 移动",
            "tags": ["arcade", "casual"],
        },
        material_usage={"assets": []},
        uploaded_assets=[],
        asset_work_order={
            "asset_decisions": [
                {
                    "target": "background",
                    "target_path": BACKGROUND_PATH,
                    "mode": "asset_agent_generate",
                    "source_asset_id": "",
                    "rationale": "需要一张稳定场景背景。",
                },
                {
                    "target": "player",
                    "target_path": PLAYER_PATH,
                    "mode": "asset_agent_generate",
                    "source_asset_id": "",
                    "rationale": "需要一张透明人物图。",
                },
            ],
            "uploaded_asset_tasks": [],
            "generated_asset_tasks": [
                {
                    "key": "asset-cover",
                    "target_path": COVER_PATH,
                    "usage": "按游戏内容和画风生成独立封面图",
                    "generation_mode": "illustrate_independent_cover_art",
                    "required": True,
                },
        ],
        },
        asset_manifest_plan=[
            {
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
            },
            {
                "asset_id": "asset-player",
                "target_path": PLAYER_PATH,
                "kind": "image",
                "required": True,
                "source": "generated",
                "runtime_required": True,
                "display_only": False,
                "logical_width": 256,
                "logical_height": 256,
                "alpha_required": True,
                "background": "transparent",
                "fit": "contain",
                "derived_from": "",
                "title_source": "",
            },
            {
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
            },
        ],
        artifact_workspace=str(tmp_path / "artifact_workspace"),
    )


def test_build_asset_prompts_keeps_background_and_player_definitions_separate(
    tmp_path: Path,
) -> None:
    state = _build_state(tmp_path)

    prompts = build_asset_prompts(state)

    background_prompt = prompts["background"]["prompt"]
    player_prompt = prompts["player"]["prompt"]
    assert "Asset type: game background" in background_prompt
    assert "Required output size: 1280x720" in background_prompt
    assert "transparent-background RGBA" not in background_prompt
    cover_prompt = prompts["cover"]["prompt"]
    assert "Asset type: game cover art" in cover_prompt
    assert "Target asset path: assets/cover.png" in cover_prompt
    assert "Do not derive this image from background.png" in cover_prompt
    assert "Asset type: player character sprite" in player_prompt
    assert "Final required export size: 256x256" in player_prompt
    assert "#FF00FF" in player_prompt
    assert "Do not use magenta" in player_prompt
    assert "single-screen game stage background" not in player_prompt


def test_run_asset_agent_writes_requested_background_and_player_assets(
    tmp_path: Path,
) -> None:
    state = _build_state(tmp_path)

    update = run_asset_agent(state)

    workspace = Path(state.artifact_workspace)
    background_path = workspace / "assets" / "background.png"
    player_path = workspace / "assets" / "player.png"
    cover_path = workspace / "assets" / "cover.png"
    assert background_path.exists()
    assert player_path.exists()
    assert cover_path.exists()
    assert read_png_info(background_path) == {
        "width": 1280,
        "height": 720,
        "color_type": 6,
    }
    assert read_png_info(player_path) == {
        "width": 256,
        "height": 256,
        "color_type": 6,
    }
    assert read_png_info(cover_path) == {
        "width": 1280,
        "height": 720,
        "color_type": 6,
    }
    processed_paths = {item["target_path"] for item in update["processed_assets"]}
    assert processed_paths == {BACKGROUND_PATH, PLAYER_PATH, COVER_PATH}
    player_asset = next(
        item for item in update["processed_assets"] if item["target_path"] == PLAYER_PATH
    )
    assert player_asset["alpha_required"] is True
    assert player_asset["transparent_background"] is True
    assert update["asset_decisions"] == state.asset_work_order["asset_decisions"]


def test_run_asset_agent_calls_image_model_with_fixed_sizes(tmp_path: Path) -> None:
    state = _build_state(tmp_path)
    image_client = FakeImageClient()

    run_asset_agent(state, image_client=image_client)

    calls_by_name = {call["output_path"].name: call for call in image_client.calls}
    assert set(calls_by_name) == {"background.png", "player_raw.png", "cover.png"}
    assert calls_by_name["background.png"]["size"] == "1280x720"
    assert calls_by_name["player_raw.png"]["size"] == "1024x1024"
    assert calls_by_name["cover.png"]["size"] == "1280x720"
    assert "Asset type: game background" in calls_by_name["background.png"]["prompt"]
    assert "Asset type: player character sprite" in calls_by_name["player_raw.png"]["prompt"]
    assert "Asset type: game cover art" in calls_by_name["cover.png"]["prompt"]
    assert (Path(state.artifact_workspace) / "assets" / "cover.png").exists()


def test_run_asset_agent_generates_independent_images_concurrently(
    tmp_path: Path,
) -> None:
    state = _build_state(tmp_path)
    image_client = OverlapDetectingImageClient(expected_calls=3)

    run_asset_agent(state, image_client=image_client)

    assert image_client.started_calls == 3
    assert image_client.max_active_calls >= 2


def test_run_asset_agent_generates_independent_cover_even_without_runtime_assets(
    tmp_path: Path,
) -> None:
    state = _build_state(tmp_path)
    state.asset_manifest_plan = [
        item for item in state.asset_manifest_plan if item["target_path"] == COVER_PATH
    ]
    state.asset_work_order = {
        "asset_decisions": [
            {
                "target": "background",
                "target_path": BACKGROUND_PATH,
                "mode": "code_generated",
                "source_asset_id": "",
                "rationale": "代码直接绘制背景。",
            },
            {
                "target": "player",
                "target_path": PLAYER_PATH,
                "mode": "code_generated",
                "source_asset_id": "",
                "rationale": "代码直接绘制角色。",
            },
        ],
        "uploaded_asset_tasks": [],
        "generated_asset_tasks": [
            {
                "key": "asset-cover",
                "target_path": COVER_PATH,
                "usage": "按游戏内容和画风生成独立封面图",
                "generation_mode": "illustrate_independent_cover_art",
                "required": True,
            }
        ],
    }
    image_client = FakeImageClient()

    update = run_asset_agent(state, image_client=image_client)

    assert [call["output_path"].name for call in image_client.calls] == ["cover.png"]
    assert update["processed_assets"][0]["target_path"] == COVER_PATH
    assert update["processed_assets"][0]["runtime_required"] is False
    assert update["processed_assets"][0]["source"] == "image_model"
    assert (Path(state.artifact_workspace) / COVER_PATH).exists()


def test_run_asset_agent_uses_uploaded_background_and_player_images(
    tmp_path: Path,
) -> None:
    state = _build_state(tmp_path)
    background_reference = tmp_path / "reference-background.png"
    player_reference = tmp_path / "reference-player.png"
    _write_solid_png(background_reference, (9, 18, 27, 255))
    _write_solid_png(player_reference, (220, 80, 40, 255))
    state.uploaded_assets = [
        {
            "asset_id": "manual-background",
            "filename": "background.png",
            "mime_type": "image/png",
            "local_path": str(background_reference),
            "user_hint": "游戏背景",
        },
        {
            "asset_id": "manual-role",
            "filename": "role.png",
            "mime_type": "image/png",
            "local_path": str(player_reference),
            "user_hint": "游戏角色",
        },
    ]
    state.asset_work_order["asset_decisions"] = [
        {
            "target": "background",
            "target_path": BACKGROUND_PATH,
            "mode": "uploaded_reference",
            "source_asset_id": "manual-background",
            "rationale": "用户明确说明该文件对应游戏背景。",
        },
        {
            "target": "player",
            "target_path": PLAYER_PATH,
            "mode": "uploaded_reference",
            "source_asset_id": "manual-role",
            "rationale": "用户明确说明该文件对应游戏角色。",
        },
    ]
    state.asset_work_order["uploaded_asset_tasks"] = [
        {
            "asset_id": "manual-background",
            "source_asset_id": "manual-background",
            "target_path": BACKGROUND_PATH,
            "usage": "作为游戏背景参考",
            "transform": "转换为 1280x720 背景 PNG",
            "required": True,
        },
        {
            "asset_id": "manual-role",
            "source_asset_id": "manual-role",
            "target_path": PLAYER_PATH,
            "usage": "作为玩家角色参考",
            "transform": "转换为 256x256 透明角色 PNG",
            "required": True,
        },
    ]
    state.asset_manifest_plan[0]["source"] = "uploaded"
    state.asset_manifest_plan[0]["derived_from"] = "manual-background"
    state.asset_manifest_plan[1]["source"] = "uploaded"
    state.asset_manifest_plan[1]["derived_from"] = "manual-role"

    update = run_asset_agent(state)

    workspace = Path(state.artifact_workspace)
    background_path = workspace / BACKGROUND_PATH
    player_path = workspace / PLAYER_PATH
    assert background_path.exists()
    assert player_path.exists()
    assert background_path.read_bytes() != _mock_background_bytes(tmp_path)
    assert read_png_info(background_path) == {
        "width": 1280,
        "height": 720,
        "color_type": 6,
    }
    assert read_png_info(player_path) == {
        "width": 256,
        "height": 256,
        "color_type": 6,
    }
    processed_by_path = {item["target_path"]: item for item in update["processed_assets"]}
    assert processed_by_path[BACKGROUND_PATH]["source_asset_id"] == "manual-background"
    assert processed_by_path[BACKGROUND_PATH]["source"] == "uploaded_reference"
    assert processed_by_path[PLAYER_PATH]["source_asset_id"] == "manual-role"
    assert processed_by_path[PLAYER_PATH]["source"] == "uploaded_reference"
    assert processed_by_path[PLAYER_PATH]["transparent_background"] is True


def test_run_asset_agent_refines_uploaded_images_with_image_model(
    tmp_path: Path,
) -> None:
    state = _build_state(tmp_path)
    background_reference = tmp_path / "reference-background.png"
    player_reference = tmp_path / "reference-player.png"
    _write_solid_png(background_reference, (9, 18, 27, 255))
    _write_solid_png(player_reference, (220, 80, 40, 255))
    state.uploaded_assets = [
        {
            "asset_id": "manual-background",
            "filename": "background.png",
            "mime_type": "image/png",
            "local_path": str(background_reference),
            "user_hint": "游戏背景",
        },
        {
            "asset_id": "manual-role",
            "filename": "role.png",
            "mime_type": "image/png",
            "local_path": str(player_reference),
            "user_hint": "游戏角色",
        },
    ]
    state.asset_work_order["asset_decisions"] = [
        {
            "target": "background",
            "target_path": BACKGROUND_PATH,
            "mode": "uploaded_reference",
            "source_asset_id": "manual-background",
            "rationale": "用户明确说明该文件对应游戏背景。",
        },
        {
            "target": "player",
            "target_path": PLAYER_PATH,
            "mode": "uploaded_reference",
            "source_asset_id": "manual-role",
            "rationale": "用户明确说明该文件对应游戏角色。",
        },
    ]
    state.asset_work_order["uploaded_asset_tasks"] = [
        {
            "asset_id": "manual-background",
            "source_asset_id": "manual-background",
            "target_path": BACKGROUND_PATH,
            "usage": "作为游戏背景参考",
            "transform": "refine_to_game_background",
            "required": True,
        },
        {
            "asset_id": "manual-role",
            "source_asset_id": "manual-role",
            "target_path": PLAYER_PATH,
            "usage": "作为玩家角色参考",
            "transform": "refine_remove_background_resize_rgba",
            "required": True,
        },
    ]
    state.asset_manifest_plan[0]["source"] = "uploaded"
    state.asset_manifest_plan[0]["derived_from"] = "manual-background"
    state.asset_manifest_plan[1]["source"] = "uploaded"
    state.asset_manifest_plan[1]["derived_from"] = "manual-role"
    image_client = FakeImageClient()

    update = run_asset_agent(state, image_client=image_client)

    calls_by_name = {call["output_path"].name: call for call in image_client.edit_calls}
    assert set(calls_by_name) == {"background.png", "player_raw.png"}
    assert calls_by_name["background.png"]["input_path"] == background_reference
    assert calls_by_name["background.png"]["size"] == "1280x720"
    assert calls_by_name["player_raw.png"]["input_path"] == player_reference
    assert calls_by_name["player_raw.png"]["size"] == "1024x1024"
    processed_by_path = {item["target_path"]: item for item in update["processed_assets"]}
    assert processed_by_path[BACKGROUND_PATH]["source"] == "image_model_refined"
    assert processed_by_path[PLAYER_PATH]["source"] == "image_model_refined"
    assert (Path(state.artifact_workspace) / PLAYER_PATH).exists()


def test_run_asset_agent_skips_generation_when_manifest_is_empty(
    tmp_path: Path,
) -> None:
    state = _build_state(tmp_path)
    state.asset_manifest_plan = []
    state.asset_work_order = {
        "asset_decisions": [
            {
                "target": "background",
                "target_path": BACKGROUND_PATH,
                "mode": "code_generated",
                "source_asset_id": "",
                "rationale": "代码可直接绘制背景。",
            },
            {
                "target": "player",
                "target_path": PLAYER_PATH,
                "mode": "code_generated",
                "source_asset_id": "",
                "rationale": "代码可直接绘制玩家。",
            },
        ],
        "uploaded_asset_tasks": [],
        "generated_asset_tasks": [],
    }

    update = run_asset_agent(state)

    workspace = Path(state.artifact_workspace)
    assert update["processed_assets"] == []
    assert update["asset_analysis"] == []
    assert update["asset_decisions"] == state.asset_work_order["asset_decisions"]
    assert not (workspace / "assets" / "background.png").exists()
    assert not (workspace / "assets" / "player.png").exists()
    assert not (workspace / "assets" / "cover.png").exists()


def test_run_asset_agent_sanitizes_asset_outputs(tmp_path: Path) -> None:
    state = _build_state(tmp_path)
    state.uploaded_assets = [
        {
            "asset_id": "secret-image",
            "filename": "secret.png",
            "mime_type": "image/png",
            "object_key": "uploads/user/secret.png?X-Amz-Signature=hidden",
            "user_hint": "Authorization: Bearer hidden",
        }
    ]

    update = run_asset_agent(state)

    output_text = str(update)
    assert "X-Amz-Signature" not in output_text
    assert "Authorization" not in output_text
    assert "Bearer" not in output_text


def _write_solid_png(path: Path, color: tuple[int, int, int, int]) -> None:
    write_png_rgba(path, 32, 32, lambda _x, _y: color)


def _mock_background_bytes(tmp_path: Path) -> bytes:
    mock_path = tmp_path / "mock-background.png"
    write_mock_background(mock_path)
    return mock_path.read_bytes()
