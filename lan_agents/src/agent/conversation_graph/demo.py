"""Local demo runner for the first-stage conversation graph."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from typing import Any, Protocol

from agent.conversation_graph import conversation_graph

DEFAULT_DEMO_USER_MESSAGES = [
    "我想做一个动物追逐躲避类的轻松小游戏。",
    "名字叫森林追逐，风格是像素街机。",
    "主角是逃跑的小动物，胜利条件是到达终点，失败条件是被追上，操作方式是方向键移动。",
]


class ConversationGraphLike(Protocol):
    """Small protocol for the compiled graph used by tests and CLI."""

    def invoke(self, state: dict[str, Any]) -> dict[str, Any]:
        """Invoke the conversation graph with a state dictionary."""


def run_conversation_demo(
    *,
    graph: ConversationGraphLike = conversation_graph,
    user_messages: list[str] | None = None,
    max_turns: int | None = None,
) -> dict[str, Any]:
    """Run a multi-turn conversation until the graph returns a confirmation card."""
    messages_to_send = list(user_messages or DEFAULT_DEMO_USER_MESSAGES)
    if max_turns is not None:
        messages_to_send = messages_to_send[:max_turns]

    state: dict[str, Any] = {}
    transcript: list[dict[str, Any]] = []
    agent_logs: list[dict[str, Any]] = []

    for index, user_message in enumerate(messages_to_send, start=1):
        transcript.append({"role": "user", "content": user_message})
        next_input = {**state, "user_event": {"type": "chat", "message": user_message}}
        state = graph.invoke(next_input)

        assistant_response = state.get("assistant_response", {})
        transcript.append(
            {
                "role": "assistant",
                "content": assistant_response.get("message", ""),
                "suggestions": assistant_response.get("suggestions", []),
            }
        )
        if assistant_response.get("card"):
            transcript.append({"role": "card", "content": assistant_response["card"]})

        agent_logs.append(_agent_log(index, state))
        if state.get("conversation_status") == "ready_to_confirm":
            break

    output = _format_demo_output(transcript, agent_logs, state)
    return {
        "messages": transcript,
        "agent_logs": agent_logs,
        "final_state": state,
        "final_card": state.get("assistant_response", {}).get("card"),
        "output": output,
    }


def pretty_print_messages(messages: list[dict[str, Any]]) -> str:
    """Format conversation messages for terminal inspection."""
    lines: list[str] = ["[Conversation]"]
    for message in messages:
        role = message.get("role")
        content = message.get("content")
        if role == "user":
            lines.append(f"[User] {content}")
        elif role == "assistant":
            lines.append(f"[Assistant] {content}")
            suggestions = message.get("suggestions") or []
            if suggestions:
                lines.append(f"建议：{', '.join(str(item) for item in suggestions)}")
        elif role == "card" and isinstance(content, dict):
            lines.append(f"[Card] {content.get('title', '')}")
            lines.append(f"介绍：{content.get('introduction', '')}")
            lines.append(f"标签：{', '.join(content.get('tags', []))}")
    return "\n".join(lines)


def _agent_log(turn: int, state: dict[str, Any]) -> dict[str, Any]:
    game_plan = state.get("game_plan", {})
    assistant_response = state.get("assistant_response", {})
    return {
        "step": f"conversation_turn_{turn}",
        "level": "info",
        "status": state.get("conversation_status"),
        "message": _log_message(state),
        "filled_game_plan_fields": [
            key for key, value in game_plan.items() if value and key != "suggestions"
        ],
        "assistant_actions": assistant_response.get("actions", []),
        "has_card": bool(assistant_response.get("card")),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def _log_message(state: dict[str, Any]) -> str:
    status = state.get("conversation_status")
    card = state.get("assistant_response", {}).get("card")
    if status == "ready_to_confirm" and card:
        return "Design Agent 已补齐 game_plan 并输出确认卡片。"
    return "Design Agent 正在追问缺失信息并更新 game_plan。"


def _format_demo_output(
    transcript: list[dict[str, Any]],
    agent_logs: list[dict[str, Any]],
    final_state: dict[str, Any],
) -> str:
    sections = [
        pretty_print_messages(transcript),
        "[Agent Logs]",
        json.dumps(agent_logs, ensure_ascii=False, indent=2),
        "[Final Game Plan]",
        json.dumps(final_state.get("game_plan", {}), ensure_ascii=False, indent=2),
        "[Final Card]",
        json.dumps(
            final_state.get("assistant_response", {}).get("card"),
            ensure_ascii=False,
            indent=2,
        ),
    ]
    return "\n\n".join(sections)


def main() -> None:
    """Run the demo and print the complete output."""
    parser = argparse.ArgumentParser(description="Run a full conversation graph demo.")
    parser.add_argument("--max-turns", type=int, default=None)
    args = parser.parse_args()
    result = run_conversation_demo(max_turns=args.max_turns)
    print(result["output"])


if __name__ == "__main__":
    main()
