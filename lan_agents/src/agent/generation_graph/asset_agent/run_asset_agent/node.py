"""Asset Agent node for generating MVP image assets."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable

from agent.generation_graph.asset_agent.prompt_builder import build_asset_prompts
from agent.generation_graph.asset_agent.tools.image_model import (
    ImageGenerationClient,
    ImageGenerationConfig,
    image_client_from_env,
)
from agent.generation_graph.asset_agent.tools.image_processing import (
    write_background_from_uploaded_image,
    write_chroma_keyed_player,
    write_chroma_keyed_player_from_source,
    write_mock_background,
    write_mock_cover,
    write_mock_player_raw,
    write_player_from_uploaded_image,
)
from agent.generation_graph.state import GenerationState
from agent.generation_graph.tools.path_safety import resolve_workspace_path
from agent.generation_graph.tools.workspace import prepare_workspace
from agent.providers import ProviderError

BACKGROUND_PATH = "assets/background.png"
PLAYER_PATH = "assets/player.png"
COVER_PATH = "assets/cover.png"
PLAYER_RAW_PATH = "assets/player_raw.png"


def run_asset_agent(
    state: GenerationState,
    *,
    image_client: ImageGenerationClient | None = None,
) -> dict[str, Any]:
    """Generate requested image assets inside artifact_workspace."""
    _validate_inputs(state)
    workspace_root = prepare_workspace(state.artifact_workspace)
    prompts = build_asset_prompts(state)
    manifest_paths = {item.get("target_path") for item in state.asset_manifest_plan}
    active_image_client = image_client if image_client is not None else image_client_from_env()
    image_config = ImageGenerationConfig.from_env()

    asset_jobs: list[
        tuple[str, Callable[[], tuple[dict[str, Any], dict[str, Any]]]]
    ] = []

    def generate_background_asset() -> tuple[dict[str, Any], dict[str, Any]]:
        background_path = resolve_workspace_path(workspace_root, BACKGROUND_PATH)
        background_reference = _uploaded_reference_for_target(state, BACKGROUND_PATH)
        if background_reference and active_image_client:
            active_image_client.edit_png(
                prompt=prompts["background"]["prompt"],
                size=image_config.background_size,
                input_path=Path(str(background_reference["local_path"])),
                output_path=background_path,
            )
            background_source = "image_model_refined"
            background_source_asset_id = str(background_reference.get("asset_id") or "")
        elif background_reference:
            write_background_from_uploaded_image(
                Path(str(background_reference["local_path"])),
                background_path,
            )
            background_source = "uploaded_reference"
            background_source_asset_id = str(background_reference.get("asset_id") or "")
        elif active_image_client:
            active_image_client.generate_png(
                prompt=prompts["background"]["prompt"],
                size=image_config.background_size,
                output_path=background_path,
            )
            background_source = "image_model"
            background_source_asset_id = ""
        else:
            write_mock_background(background_path)
            background_source = "mock"
            background_source_asset_id = ""
        return (
            _processed_asset(
                target_path=BACKGROUND_PATH,
                absolute_path=background_path,
                prompt=prompts["background"]["prompt"],
                width=1280,
                height=720,
                runtime_required=True,
                alpha_required=False,
                transparent_background=False,
                source=background_source,
                source_asset_id=background_source_asset_id,
            ),
            {
                "asset_id": "background",
                "target_path": BACKGROUND_PATH,
                "summary": (
                    "Created 1280x720 gameplay background from uploaded reference."
                    if background_source == "uploaded_reference"
                    else "Generated 1280x720 gameplay background from Asset Agent prompts."
                ),
                "blocking": False,
            },
        )

    def generate_player_asset() -> tuple[dict[str, Any], dict[str, Any]]:
        player_raw_path = resolve_workspace_path(workspace_root, PLAYER_RAW_PATH)
        player_path = resolve_workspace_path(workspace_root, PLAYER_PATH)
        player_reference = _uploaded_reference_for_target(state, PLAYER_PATH)
        if player_reference and active_image_client:
            active_image_client.edit_png(
                prompt=prompts["player"]["prompt"],
                size=image_config.player_source_size,
                input_path=Path(str(player_reference["local_path"])),
                output_path=player_raw_path,
            )
            write_chroma_keyed_player_from_source(player_raw_path, player_path)
            player_source = "image_model_refined"
            player_source_asset_id = str(player_reference.get("asset_id") or "")
        elif player_reference:
            write_player_from_uploaded_image(
                Path(str(player_reference["local_path"])),
                player_path,
            )
            player_source = "uploaded_reference"
            player_source_asset_id = str(player_reference.get("asset_id") or "")
        elif active_image_client:
            active_image_client.generate_png(
                prompt=prompts["player"]["prompt"],
                size=image_config.player_source_size,
                output_path=player_raw_path,
            )
            write_chroma_keyed_player_from_source(player_raw_path, player_path)
            player_source = "image_model"
            player_source_asset_id = ""
        else:
            write_mock_player_raw(player_raw_path)
            write_chroma_keyed_player(player_path)
            player_source = "mock"
            player_source_asset_id = ""
        return (
            _processed_asset(
                target_path=PLAYER_PATH,
                absolute_path=player_path,
                prompt=prompts["player"]["prompt"],
                width=256,
                height=256,
                runtime_required=True,
                alpha_required=True,
                transparent_background=True,
                source=player_source,
                source_asset_id=player_source_asset_id,
            ),
            {
                "asset_id": "player",
                "target_path": PLAYER_PATH,
                "summary": (
                    "Created 256x256 RGBA player sprite from uploaded reference."
                    if player_source == "uploaded_reference"
                    else "Generated 1024x1024 magenta-matte source and exported 256x256 RGBA player sprite."
                ),
                "blocking": False,
            },
        )

    def generate_cover_asset() -> tuple[dict[str, Any], dict[str, Any]]:
        cover_path = resolve_workspace_path(workspace_root, COVER_PATH)
        if active_image_client:
            active_image_client.generate_png(
                prompt=prompts["cover"]["prompt"],
                size=image_config.background_size,
                output_path=cover_path,
            )
            cover_source = "image_model"
        else:
            write_mock_cover(cover_path)
            cover_source = "mock"
        return (
            _processed_asset(
                target_path=COVER_PATH,
                absolute_path=cover_path,
                prompt=prompts["cover"]["prompt"],
                width=1280,
                height=720,
                runtime_required=False,
                alpha_required=False,
                transparent_background=False,
                source=cover_source,
                source_asset_id="",
            ),
            {
                "asset_id": "cover",
                "target_path": COVER_PATH,
                "summary": "Generated independent 1280x720 display cover art from game content and style.",
                "blocking": False,
            },
        )

    if BACKGROUND_PATH in manifest_paths:
        asset_jobs.append(("background", generate_background_asset))
    if PLAYER_PATH in manifest_paths:
        asset_jobs.append(("player", generate_player_asset))
    if COVER_PATH in manifest_paths:
        asset_jobs.append(("cover", generate_cover_asset))

    processed_by_name: dict[str, dict[str, Any]] = {}
    analysis_by_name: dict[str, dict[str, Any]] = {}
    if len(asset_jobs) <= 1:
        for name, job in asset_jobs:
            processed_asset, analysis = job()
            processed_by_name[name] = processed_asset
            analysis_by_name[name] = analysis
    else:
        with ThreadPoolExecutor(max_workers=min(3, len(asset_jobs))) as executor:
            futures = {executor.submit(job): name for name, job in asset_jobs}
            for future, name in futures.items():
                processed_asset, analysis = future.result()
                processed_by_name[name] = processed_asset
                analysis_by_name[name] = analysis

    ordered_names = [name for name, _job in asset_jobs]
    processed_assets = [processed_by_name[name] for name in ordered_names]
    asset_analysis = [analysis_by_name[name] for name in ordered_names]

    return {
        "processed_assets": processed_assets,
        "asset_analysis": asset_analysis,
        "asset_decisions": state.asset_work_order.get("asset_decisions", []),
        "asset_notes": [
            "MVP image generator uses the configured image model when ASSET_IMAGE_PROVIDER is openai-compatible; otherwise it stays deterministic locally.",
            "Uploaded background/player images are converted into runtime PNG assets before model generation fallback.",
            "Player transparency is produced by post-processing the magenta matte, not by trusting the image model.",
            "Asset Agent always generates cover.png independently as display-only key art when requested by Orchestrator.",
        ],
        "generation_status": "assets_generated",
    }


def _validate_inputs(state: GenerationState) -> None:
    if not state.artifact_workspace:
        raise ProviderError("Asset Agent requires artifact_workspace")
    manifest_paths = {item.get("target_path") for item in state.asset_manifest_plan}
    invalid = manifest_paths - {BACKGROUND_PATH, PLAYER_PATH, COVER_PATH}
    if invalid:
        raise ProviderError(
            f"Asset Agent received invalid manifest paths: {', '.join(sorted(invalid))}"
        )


def _uploaded_reference_for_target(
    state: GenerationState,
    target_path: str,
) -> dict[str, Any] | None:
    task = _uploaded_task_for_target(state, target_path)
    if not task:
        return None
    source_asset_id = str(task.get("source_asset_id") or task.get("asset_id") or "")
    uploaded = _uploaded_asset_by_id(state, source_asset_id)
    if not uploaded:
        if task.get("required"):
            raise ProviderError(
                f"Required uploaded image asset is missing for {target_path}: {source_asset_id}"
            )
        return None
    mime_type = str(uploaded.get("mime_type") or "")
    if not mime_type.startswith("image/"):
        return None
    has_explicit_local_path = bool(str(uploaded.get("local_path") or "").strip())
    local_path = str(
        uploaded.get("local_path") or uploaded.get("local_fixture_path") or ""
    ).strip()
    if not local_path:
        raise ProviderError(f"Uploaded image asset for {target_path} has no local path")
    resolved_local_path = _resolve_uploaded_local_path(local_path)
    if not resolved_local_path.is_file():
        if not has_explicit_local_path:
            return None
        raise ProviderError(f"Uploaded image asset not found: {local_path}")
    return {**uploaded, "local_path": str(resolved_local_path)}


def _uploaded_task_for_target(
    state: GenerationState,
    target_path: str,
) -> dict[str, Any] | None:
    for task in state.asset_work_order.get("uploaded_asset_tasks", []):
        if isinstance(task, dict) and task.get("target_path") == target_path:
            return task
    for decision in state.asset_work_order.get("asset_decisions", []):
        if (
            isinstance(decision, dict)
            and decision.get("target_path") == target_path
            and decision.get("mode") == "uploaded_reference"
        ):
            return {
                "source_asset_id": decision.get("source_asset_id"),
                "target_path": target_path,
                "required": True,
            }
    return None


def _uploaded_asset_by_id(
    state: GenerationState,
    asset_id: str,
) -> dict[str, Any] | None:
    for asset in state.uploaded_assets:
        if str(asset.get("asset_id") or "") == asset_id:
            return asset
    return None


def _resolve_uploaded_local_path(local_path: str) -> Path:
    path = Path(local_path)
    if path.is_absolute():
        return path
    cwd_path = Path.cwd() / path
    if cwd_path.is_file():
        return cwd_path
    module_root_path = Path(__file__).resolve().parents[6] / path
    if module_root_path.is_file():
        return module_root_path
    return cwd_path


def _processed_asset(
    *,
    target_path: str,
    absolute_path: Path,
    prompt: str,
    width: int,
    height: int,
    runtime_required: bool,
    alpha_required: bool,
    transparent_background: bool,
    source: str,
    source_asset_id: str,
) -> dict[str, Any]:
    return {
        "target_path": target_path,
        "path": str(absolute_path),
        "width": width,
        "height": height,
        "kind": "image",
        "runtime_required": runtime_required,
        "alpha_required": alpha_required,
        "transparent_background": transparent_background,
        "source": source,
        "source_asset_id": source_asset_id,
        "prompt_preview": prompt[:500],
    }
