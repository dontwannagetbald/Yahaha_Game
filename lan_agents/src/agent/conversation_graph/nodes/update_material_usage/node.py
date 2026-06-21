"""Record uploaded assets as first-stage material usage skeletons."""

from __future__ import annotations

from typing import Any

from agent.conversation_graph.nodes._helpers import copy_dict, sanitize_asset
from agent.state import ConversationState


def update_material_usage(state: ConversationState) -> dict[str, Any]:
    """Record uploaded assets as first-stage material usage skeletons."""
    assets = [sanitize_asset(asset) for asset in state.user_event.get("uploaded_assets", [])]
    if bool(state.user_event.get("replace_existing_assets")):
        return {
            "material_usage": {"assets": assets},
        }
    existing_assets = copy_dict(state.material_usage).get("assets", [])
    merged_assets = {asset.get("asset_id"): asset for asset in existing_assets}
    for asset in assets:
        merged_assets[asset["asset_id"]] = {**merged_assets.get(asset["asset_id"], {}), **asset}
    return {
        "material_usage": {"assets": list(merged_assets.values())},
    }
