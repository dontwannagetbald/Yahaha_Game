from __future__ import annotations

from datetime import datetime, timezone


def build_manifest(title: str, description: str) -> dict[str, object]:
    return {
        "schemaVersion": "1.0",
        "title": title,
        "description": description,
        "entry": "index.html",
        "styles": ["style.css"],
        "scripts": ["game.js"],
        "assets": [],
        "cover": None,
        "controls": ["Arrow keys or WASD to move"],
        "runtime": "html5-iframe",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }

