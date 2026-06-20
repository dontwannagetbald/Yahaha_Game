from __future__ import annotations

from app.graph.state import ConfirmationCard, StructuredDesignState


def build_design_output(prompt: str, uploaded_assets: list[dict[str, object]]) -> tuple[dict[str, object], dict[str, object]]:
    asset_names = ", ".join(str(asset["filename"]) for asset in uploaded_assets) or "无素材"
    confirmation = ConfirmationCard(
        title="霓虹生存者",
        short_description="在霓虹竞技场中躲避障碍并收集能量。",
        game_type="arcade survival",
        core_gameplay="躲避障碍、收集能量并坚持到倒计时结束",
        win_lose_condition="倒计时结束前生命值保持大于 0 即获胜",
        controls="方向键或 WASD 移动",
        assets_used=f"优先参考素材：{asset_names}",
        tags=["survival", "neon"],
        cover_suggestion="霓虹竞技场中的机器人主角",
    )
    design_state = StructuredDesignState(
        intent_summary=prompt,
        visual_style="neon sci-fi",
        core_loop=["move", "avoid", "collect", "survive"],
        win_condition="survive until timer ends",
        lose_condition="hp reaches zero",
        controls_detail=["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"],
        player_role="robot scout",
        asset_intent=[
            {
                "asset_id": asset.get("asset_id", ""),
                "suggested_use": f"Use {asset.get('filename', 'asset')} as robot reference",
            }
            for asset in uploaded_assets
        ],
    )
    return confirmation.to_dict(), design_state.to_dict()
