from __future__ import annotations


def log_event(step: str, agent: str, level: str, message: str) -> dict[str, str]:
    return {
        "step": step,
        "agent": agent,
        "level": level,
        "message": message,
    }

