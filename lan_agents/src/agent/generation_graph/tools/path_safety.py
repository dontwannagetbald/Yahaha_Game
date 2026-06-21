"""Path safety helpers for artifact workspace access."""

from __future__ import annotations

from pathlib import Path

from agent.providers import ProviderError


def ensure_workspace_root(workspace: str) -> Path:
    """Return a normalized workspace root, creating it if needed."""
    root = Path(workspace).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def resolve_workspace_path(workspace_root: Path, relative_path: str) -> Path:
    """Resolve a relative bundle path under the workspace root."""
    normalized = relative_path.strip().replace("\\", "/")
    if not normalized or normalized.startswith("/") or ".." in normalized.split("/"):
        raise ProviderError("artifact path must stay inside artifact_workspace")
    target = (workspace_root / normalized).resolve()
    if not str(target).startswith(str(workspace_root)):
        raise ProviderError("artifact path escaped artifact_workspace")
    target.parent.mkdir(parents=True, exist_ok=True)
    return target
