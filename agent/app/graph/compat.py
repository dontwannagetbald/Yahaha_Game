from __future__ import annotations

from collections.abc import Callable
from typing import Any

START = "__start__"
END = "__end__"


class _CompiledGraph:
    def __init__(self, nodes: dict[str, Callable[[dict[str, Any]], dict[str, Any]]], order: list[str]) -> None:
        self._nodes = nodes
        self._order = order

    def invoke(self, state: dict[str, Any], config: dict[str, Any] | None = None, **_: Any) -> dict[str, Any]:
        current = dict(state)
        for name in self._order:
            current = self._nodes[name](current)
        return current


class StateGraph:
    def __init__(self, _state_type: type[Any] | None = None) -> None:
        self._nodes: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {}
        self._edges: dict[str, str] = {}

    def add_node(self, name: str, func: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
        self._nodes[name] = func

    def add_edge(self, left: str, right: str) -> None:
        self._edges[left] = right

    def compile(self) -> _CompiledGraph:
        order: list[str] = []
        cursor = self._edges.get(START)
        while cursor and cursor != END:
            order.append(cursor)
            cursor = self._edges.get(cursor)
        return _CompiledGraph(self._nodes, order)
