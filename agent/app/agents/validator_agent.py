from __future__ import annotations

import json
from pathlib import Path


def validate_bundle(bundle_dir: Path, manifest_path: Path) -> dict[str, object]:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {
            "valid": False,
            "failed_step": "validate_bundle",
            "issues": [{"field": "manifest", "message": "manifest.json is missing"}],
            "error_message": "生成结果缺少 manifest.json，无法预览游戏。",
            "retry_hint": "请重新生成任务。",
        }

    required_files = ["index.html", "style.css", "game.js"]
    missing = [name for name in required_files if not (bundle_dir / name).exists()]
    if missing:
        return {
            "valid": False,
            "failed_step": "validate_bundle",
            "issues": [{"field": "bundle", "message": f"Missing files: {', '.join(missing)}"}],
            "error_message": f"生成结果缺少关键文件：{', '.join(missing)}。",
            "retry_hint": "请重新生成任务。",
        }

    entry = manifest.get("entry")
    if entry != "index.html":
        return {
            "valid": False,
            "failed_step": "validate_bundle",
            "issues": [{"field": "entry", "message": "entry must be index.html"}],
            "error_message": "生成结果入口文件不正确，无法在 Play 中加载。",
            "retry_hint": "请重新生成任务。",
        }

    return {
        "valid": True,
        "failed_step": None,
        "issues": [],
        "error_message": None,
        "retry_hint": None,
    }

