"""Best-effort runtime checks for drafted HTML5 bundles."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


CANVAS_PATTERN = re.compile(r"<canvas\b", re.IGNORECASE)
GAME_JS_SCRIPT_PATTERN = re.compile(
    r"""<script[^>]+src=['"]game\.js['"]""", re.IGNORECASE
)
GAME_READY_PATTERN = re.compile(r"game_ready")
RENDER_SIGNAL_PATTERN = re.compile(
    r"(getContext\s*\(|fillRect\s*\(|drawImage\s*\(|requestAnimationFrame\s*\()"
)


def run_headless_runtime_check(entry_path: str) -> dict[str, Any]:
    """Run a lightweight runtime check for the generated bundle.

    The current environment does not ship a browser runtime dependency, so this
    function uses Node syntax validation plus static runtime markers as a
    deterministic fallback boundary.
    """
    entry = Path(entry_path)
    game_js = entry.parent / "game.js"

    html_source = entry.read_text(encoding="utf-8") if entry.exists() else ""
    js_source = game_js.read_text(encoding="utf-8") if game_js.exists() else ""

    js_syntax_ok = False
    syntax_error = ""
    node_binary = shutil.which("node")
    if node_binary and game_js.exists():
        result = subprocess.run(
            [node_binary, "--check", str(game_js)],
            capture_output=True,
            text=True,
            check=False,
        )
        js_syntax_ok = result.returncode == 0
        syntax_error = (result.stderr or result.stdout).strip()
    elif not game_js.exists():
        syntax_error = "game.js is missing"
    else:
        syntax_error = "node is unavailable for JS syntax validation"

    html_has_canvas = bool(CANVAS_PATTERN.search(html_source))
    html_references_game_js = bool(GAME_JS_SCRIPT_PATTERN.search(html_source))
    game_ready_signal_found = bool(GAME_READY_PATTERN.search(js_source))
    render_signal_found = bool(RENDER_SIGNAL_PATTERN.search(js_source))

    return {
        "mode": "static-node-fallback",
        "entry_exists": entry.exists(),
        "game_js_exists": game_js.exists(),
        "html_has_canvas": html_has_canvas,
        "html_references_game_js": html_references_game_js,
        "node_available": bool(node_binary),
        "js_syntax_ok": js_syntax_ok,
        "syntax_error": syntax_error,
        "game_ready_signal_found": game_ready_signal_found,
        "render_signal_found": render_signal_found,
        "passed": bool(
            entry.exists()
            and game_js.exists()
            and html_has_canvas
            and html_references_game_js
            and js_syntax_ok
            and game_ready_signal_found
            and render_signal_found
        ),
    }
