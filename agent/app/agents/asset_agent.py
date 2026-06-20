from __future__ import annotations

from app.tools.asset_tools import summarize_asset


def analyze_assets(uploaded_assets: list[dict[str, object]]) -> list[dict[str, object]]:
    analyses: list[dict[str, object]] = []
    for asset in uploaded_assets:
        summary = summarize_asset(asset)
        media_type = str(summary["media_type"])
        analyses.append(
            {
                "asset_id": asset["asset_id"],
                "media_type": media_type,
                "summary": summary["summary"],
                "suggested_uses": [f"Use {asset['filename']} as player or prop inspiration"],
                "risks": [],
            }
        )
    return analyses
