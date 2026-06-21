"""Deterministic local LLM provider used by tests and CI."""

from __future__ import annotations

import copy
from typing import Any

from agent.providers.base import LLMMessage

DEFAULT_MOCK_RESPONSE: dict[str, Any] = {
    "game_plan_patch": {},
    "assistant_message": "我已经理解大方向了。你希望先补充哪个关键设定？",
    "suggestions": ["先定游戏名字", "先定玩法目标", "先定操作方式"],
}


class MockLLMProvider:
    """Return a configured JSON response without any network call."""

    def __init__(
        self,
        response: dict[str, Any] | None = None,
        raises: Exception | None = None,
    ) -> None:
        self._response = response if response is not None else DEFAULT_MOCK_RESPONSE
        self._raises = raises
        self.calls: list[dict[str, Any]] = []

    def complete_json(
        self,
        *,
        messages: list[LLMMessage],
        response_schema: dict[str, Any],
        temperature: float = 1.0,
        max_completion_tokens: int = 1200,
    ) -> dict[str, Any]:
        """Return the configured response and record the call."""
        self.calls.append(
            {
                "messages": messages,
                "response_schema": response_schema,
                "temperature": temperature,
                "max_completion_tokens": max_completion_tokens,
            }
        )
        if self._raises:
            raise self._raises
        return copy.deepcopy(self._response)

    def complete_json_with_attachments(
        self,
        *,
        messages: list[LLMMessage],
        response_schema: dict[str, Any],
        attachments: list[dict[str, Any]],
        temperature: float = 1.0,
        max_completion_tokens: int = 1200,
    ) -> dict[str, Any]:
        """Record reference attachments and return the configured response."""
        self.calls.append(
            {
                "messages": messages,
                "response_schema": response_schema,
                "attachments": attachments,
                "temperature": temperature,
                "max_completion_tokens": max_completion_tokens,
            }
        )
        if self._raises:
            raise self._raises
        return copy.deepcopy(self._response)
