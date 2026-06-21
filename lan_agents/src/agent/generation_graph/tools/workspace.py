"""Workspace helpers for generated game artifacts."""

from __future__ import annotations

from pathlib import Path

from agent.generation_graph.tools.path_safety import (
    ensure_workspace_root,
    resolve_workspace_path,
)


def prepare_workspace(workspace: str) -> Path:
    """Create and return the artifact workspace root."""
    return ensure_workspace_root(workspace)


def write_workspace_text(workspace_root: Path, relative_path: str, content: str) -> Path:
    """Write a text file inside the artifact workspace."""
    target = resolve_workspace_path(workspace_root, relative_path)
    target.write_text(content, encoding="utf-8")
    return target
