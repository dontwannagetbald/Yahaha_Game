"""Generation subgraph assembly."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from langgraph.graph import END, START, StateGraph

from agent.generation_graph.asset_agent.run_asset_agent.node import run_asset_agent
from agent.generation_graph.coding_agent.debug_code_with_assets.node import (
    debug_code_with_assets,
)
from agent.generation_graph.coding_agent.draft_code.node import draft_code
from agent.generation_graph.orchestrator.build_parallel_contracts.node import (
    build_parallel_contracts,
)
from agent.generation_graph.state import GenerationState
from agent.generation_graph.tools.workspace import prepare_workspace, write_workspace_text
from agent.generation_graph.validator_agent.validate_final_delivery.node import (
    validate_final_delivery,
)
from agent.providers import MockLLMProvider, ProviderConfig, provider_from_config


def init_generation_context(state: GenerationState) -> dict[str, Any]:
    """Normalize the backend job input into a stage-B generation context."""
    workspace = state.artifact_workspace
    if not workspace:
        job_id = str(state.job_context.get("job_id") or "local-job")
        user_id = str(state.job_context.get("user_id") or "local-user")
        version = str(state.job_context.get("version") or "v1")
        workspace = str(Path("output") / "drafts" / user_id / job_id / version)
    prepare_workspace(workspace)
    return {
        "artifact_workspace": workspace,
        "asset_registry": _build_asset_registry(state.uploaded_assets),
        "generation_status": "planning",
        "agent_logs": [
            *state.agent_logs,
            {
                "step": "init_generation_context",
                "level": "info",
                "message": "Initialized generation context.",
            },
        ],
    }


def orchestrate_generation(state: GenerationState) -> dict[str, Any]:
    update = build_parallel_contracts(state)
    return {
        **update,
        "agent_logs": [
            *state.agent_logs,
            {
                "step": "build_parallel_contracts",
                "level": "info",
                "message": "Generated coding and asset contracts.",
            },
        ],
    }


def draft_game_code(state: GenerationState) -> dict[str, Any]:
    update = draft_code(state, provider=_coding_provider_from_env(state))
    if not state.asset_manifest_plan:
        update["processed_assets"] = []
        update["asset_analysis"] = []
    return {
        **update,
        "agent_logs": [
            *state.agent_logs,
            {
                "step": "draft_code",
                "level": "info",
                "message": "Drafted static HTML5 bundle files.",
            },
        ],
    }


def generate_requested_assets(state: GenerationState) -> dict[str, Any]:
    update = run_asset_agent(state)
    return {
        **update,
        "agent_logs": [
            *state.agent_logs,
            {
                "step": "run_asset_agent",
                "level": "info",
                "message": "Generated requested visual assets.",
            },
        ],
    }


def debug_game_code(state: GenerationState) -> dict[str, Any]:
    repairing_validation_failure = state.validation_report.get("valid") is False
    update = debug_code_with_assets(state, provider=_coding_provider_from_env(state))
    next_repair_count = (
        state.coding_repair_attempt_count + 1
        if repairing_validation_failure
        else state.coding_repair_attempt_count
    )
    step = (
        "coding_agent.repair_code"
        if repairing_validation_failure
        else "debug_code_with_assets"
    )
    message = (
        "Repaired bundle using validation_report feedback."
        if repairing_validation_failure
        else "Completed bundle debug checks."
    )
    return {
        **update,
        "coding_repair_attempt_count": next_repair_count,
        "agent_logs": [
            *state.agent_logs,
            {
                "step": step,
                "level": "info",
                "message": message,
            },
        ],
    }


def join_assets_and_code(state: GenerationState) -> dict[str, Any]:
    """Join code and assets into the context consumed by debug and validation."""
    context = {
        "code_artifacts": state.code_artifacts,
        "manifest_draft": state.manifest_draft,
        "processed_assets": state.processed_assets,
        "asset_manifest_plan": state.asset_manifest_plan,
        "artifact_workspace": state.artifact_workspace,
    }
    return {
        "integrated_bundle_context": context,
        "generation_status": "debugging",
        "agent_logs": [
            *state.agent_logs,
            {
                "step": "join_assets_and_code",
                "level": "info",
                "message": "Joined code artifacts and processed assets.",
            },
        ],
    }


def validate_delivery(state: GenerationState) -> dict[str, Any]:
    _write_final_manifest(state)
    return validate_final_delivery(state)


def finalize_success(state: GenerationState) -> dict[str, Any]:
    return {
        "status": "succeeded",
        "generation_status": "succeeded",
        "agent_logs": [
            *state.agent_logs,
            {
                "step": "finalize_success",
                "level": "info",
                "message": "Generation succeeded and draft metadata is ready.",
            },
        ],
    }


def finalize_failure(state: GenerationState) -> dict[str, Any]:
    message = state.error_message or "生成失败，请稍后重试。"
    return {
        "status": "failed",
        "generation_status": "failed",
        "failed_step": state.failed_step or "generation_graph",
        "error_message": message,
        "retry_hint": state.retry_hint or "请重新生成游戏，或调整素材后再试。",
        "agent_logs": [
            *state.agent_logs,
            {
                "step": "finalize_failure",
                "level": "error",
                "message": message,
            },
        ],
    }


def route_after_orchestrator(state: GenerationState) -> Literal["assets", "debug"]:
    if state.asset_manifest_plan:
        return "assets"
    return "debug"


def route_after_validation(state: GenerationState) -> Literal["success", "repair", "failure"]:
    if state.validation_report.get("valid") is True and state.generation_status == "succeeded":
        return "success"
    if state.coding_repair_attempt_count < 1:
        return "repair"
    return "failure"


def _coding_provider_from_env(state: GenerationState):
    config = ProviderConfig.from_env(
        model_env_name="CODING_AGENT_MODEL",
        fallback_model_env_name="OPENAI_COMPATIBLE_MODEL",
    )
    if config.provider.lower() == "mock":
        return MockLLMProvider(response=_mock_code_response(state))
    return provider_from_config(config)


def _mock_code_response(state: GenerationState) -> dict[str, Any]:
    asset_paths = {
        str(item.get("target_path") or "")
        for item in state.asset_manifest_plan
        if item.get("target_path")
    }
    uses_background = "assets/background.png" in asset_paths
    uses_player = "assets/player.png" in asset_paths
    background_setup = (
        "const bg=new Image();bg.src='assets/background.png';"
        if uses_background
        else ""
    )
    player_setup = (
        "const playerImg=new Image();playerImg.src='assets/player.png';"
        if uses_player
        else ""
    )
    background_draw = (
        "if(bg.complete){ctx.drawImage(bg,0,0,w,h);}else{drawBackground();}"
        if uses_background
        else "drawBackground();"
    )
    player_draw = (
        "if(playerImg.complete){ctx.drawImage(playerImg,player.x-32,player.y-32,64,64);}else{drawPlayer();}"
        if uses_player
        else "drawPlayer();"
    )
    title = str(state.game_plan.get("title") or "Generated Game").replace("'", "")
    return {
        "index_html": "<!doctype html><html><head><meta charset='utf-8'><link rel='stylesheet' href='style.css'></head><body><canvas id='game' width='960' height='540'></canvas><script src='game.js'></script></body></html>",
        "style_css": "html,body{margin:0;background:#101418;color:#fff}canvas{display:block;margin:0 auto;background:#182024}",
        "game_js": (
            "const canvas=document.getElementById('game');const ctx=canvas.getContext('2d');"
            "const w=canvas.width,h=canvas.height;"
            f"{background_setup}{player_setup}"
            "const player={x:w/2,y:h-90};"
            "window.addEventListener('keydown',(event)=>{if(event.key==='ArrowLeft'||event.key==='a'){player.x=Math.max(28,player.x-18);}if(event.key==='ArrowRight'||event.key==='d'){player.x=Math.min(w-28,player.x+18);}});"
            "function drawBackground(){const g=ctx.createLinearGradient(0,0,0,h);g.addColorStop(0,'#203a31');g.addColorStop(1,'#101418');ctx.fillStyle=g;ctx.fillRect(0,0,w,h);ctx.fillStyle='#ffc200';for(let i=0;i<16;i++){ctx.beginPath();ctx.arc(60+i*55,80+(i%4)*55,6,0,7);ctx.fill();}}"
            "function drawPlayer(){ctx.fillStyle='#f7c67a';ctx.beginPath();ctx.arc(player.x,player.y,28,0,7);ctx.fill();ctx.fillStyle='#fff';ctx.fillRect(player.x-10,player.y-8,7,7);ctx.fillRect(player.x+5,player.y-8,7,7);}"
            "function loop(){"
            f"{background_draw}{player_draw}"
            f"ctx.fillStyle='#fff';ctx.font='24px sans-serif';ctx.fillText('{title}',24,36);"
            "window.parent.postMessage({type:'game_ready'},'*');requestAnimationFrame(loop);}"
            "loop();"
        ),
        "coding_notes": [
            "Mock generation graph emitted a runnable static HTML5 bundle.",
            "Asset references are limited to Orchestrator-approved paths.",
        ],
    }


def _build_asset_registry(uploaded_assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    safe_keys = {
        "asset_id",
        "filename",
        "mime_type",
        "size_bytes",
        "object_key",
        "local_fixture_path",
        "user_hint",
    }
    return [
        {key: value for key, value in asset.items() if key in safe_keys}
        for asset in uploaded_assets
    ]


def _write_final_manifest(state: GenerationState) -> None:
    if not state.manifest_draft or not state.artifact_workspace:
        return
    workspace = prepare_workspace(state.artifact_workspace)
    manifest_path = write_workspace_text(
        workspace,
        "manifest.json",
        json.dumps(state.manifest_draft, ensure_ascii=False, indent=2),
    )
    code_artifacts = dict(state.code_artifacts or {})
    files = [
        item
        for item in code_artifacts.get("files", [])
        if item.get("relative_path") != "manifest.json"
    ]
    files.append(
        {
            "relative_path": "manifest.json",
            "absolute_path": str(manifest_path),
        }
    )
    code_artifacts["manifest_path"] = str(manifest_path)
    code_artifacts["files"] = files
    state.code_artifacts = code_artifacts


workflow = StateGraph(GenerationState)
workflow.add_node("init_generation_context", init_generation_context)
workflow.add_node("orchestrator", orchestrate_generation)
workflow.add_node("coding_agent", draft_game_code)
workflow.add_node("asset_agent", generate_requested_assets)
workflow.add_node("join_assets_and_code", join_assets_and_code)
workflow.add_node("debug_agent", debug_game_code)
workflow.add_node("validator_agent", validate_delivery)
workflow.add_node("finalize_success", finalize_success)
workflow.add_node("finalize_failure", finalize_failure)

workflow.add_edge(START, "init_generation_context")
workflow.add_edge("init_generation_context", "orchestrator")
workflow.add_edge("orchestrator", "coding_agent")
workflow.add_conditional_edges(
    "coding_agent",
    route_after_orchestrator,
    {
        "assets": "asset_agent",
        "debug": "join_assets_and_code",
    },
)
workflow.add_edge("asset_agent", "join_assets_and_code")
workflow.add_edge("join_assets_and_code", "debug_agent")
workflow.add_edge("debug_agent", "validator_agent")
workflow.add_conditional_edges(
    "validator_agent",
    route_after_validation,
    {
        "success": "finalize_success",
        "repair": "debug_agent",
        "failure": "finalize_failure",
    },
)
workflow.add_edge("finalize_success", END)
workflow.add_edge("finalize_failure", END)

generation_graph = workflow.compile(name="Generation Graph")
