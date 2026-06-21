"""Deterministic helpers for the generated iframe runtime protocol."""

from __future__ import annotations

from agent.generation_graph.tools.runtime_check import GAME_READY_PATTERN


GAME_READY_SNIPPET = "window.parent.postMessage({ type: 'game_ready' }, '*');"


def ensure_game_ready_signal(js_source: str) -> str:
    """Ensure generated game.js notifies the parent iframe when it is ready."""
    if GAME_READY_PATTERN.search(js_source):
        return js_source
    return f"{js_source.rstrip()}\n{GAME_READY_SNIPPET}\n"
