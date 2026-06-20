from __future__ import annotations


def summarize_asset(asset: dict[str, object]) -> dict[str, object]:
    media_type = str(asset.get("mime_type", "application/octet-stream")).split("/")[0]
    return {
        "asset_id": asset.get("asset_id", ""),
        "media_type": media_type,
        "summary": f"{asset.get('filename', 'asset')} is available as a {media_type} asset.",
    }

