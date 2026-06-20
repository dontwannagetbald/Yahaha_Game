from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.graph.conversation_graph import run_conversation
from app.graph.generation_graph import run_generation
from app.providers.mock_provider import MockProvider
from app.providers.openai_compatible import OpenAICompatibleProvider
from app.tracing import open_langsmith_tracing


def _resolve_provider(name: str):
    if name == "mock":
        return MockProvider()
    if name == "openai-compatible":
        return OpenAICompatibleProvider()
    raise RuntimeError(f"Unsupported provider: {name}")


def _read_input(path: str) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _conversation_command(args: argparse.Namespace) -> int:
    payload = _read_input(args.input)
    with open_langsmith_tracing(command="conversation", payload=payload) as run_config:
        result = run_conversation(payload, config=run_config)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _generate_command(args: argparse.Namespace) -> int:
    provider = _resolve_provider(args.provider)
    provider.ensure_configured()
    payload = _read_input(args.input)
    with open_langsmith_tracing(
        command="generate",
        payload=payload,
        provider=args.provider,
        output_dir=args.output_dir,
    ) as run_config:
        if "confirmation_card" not in payload or "structured_design_state" not in payload:
            payload = run_conversation(payload, config=run_config)
        result = run_generation(payload, output_dir=Path(args.output_dir), config=run_config)
    print(result["artifact"]["manifest_path"])
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Standalone agent prototype runner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    conversation = subparsers.add_parser("conversation", help="Run conversation graph")
    conversation.add_argument("--input", required=True)
    conversation.set_defaults(handler=_conversation_command)

    generate = subparsers.add_parser("generate", help="Run generation graph")
    generate.add_argument("--input", required=True)
    generate.add_argument("--output-dir", required=True)
    generate.add_argument(
        "--provider",
        default="mock",
        choices=["mock", "openai-compatible"],
    )
    generate.set_defaults(handler=_generate_command)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
