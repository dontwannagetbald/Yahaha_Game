from __future__ import annotations

import os


class OpenAICompatibleProvider:
    name = "openai-compatible"

    def ensure_configured(self) -> None:
        if not os.getenv("OPENAI_COMPATIBLE_API_KEY"):
            raise RuntimeError(
                "OPENAI_COMPATIBLE_API_KEY is required when provider=openai-compatible"
            )
        if not os.getenv("OPENAI_COMPATIBLE_BASE_URL"):
            raise RuntimeError(
                "OPENAI_COMPATIBLE_BASE_URL is required when provider=openai-compatible"
            )
        if not os.getenv("OPENAI_COMPATIBLE_MODEL"):
            raise RuntimeError(
                "OPENAI_COMPATIBLE_MODEL is required when provider=openai-compatible"
            )

