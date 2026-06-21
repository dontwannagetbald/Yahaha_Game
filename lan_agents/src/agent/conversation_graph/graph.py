"""Conversation subgraph assembly."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from agent.conversation_graph.nodes import (
    build_error_response,
    build_user_response,
    generate_or_refine_plan,
    ingest_user_event,
    lock_confirmation,
    regenerate_plan,
    update_material_usage,
    update_requirements,
)
from agent.conversation_graph.routes import route_user_event
from agent.state import ConversationState


class Context(TypedDict):
    """Context parameters for the agent."""

    my_configurable_param: str


workflow = StateGraph(ConversationState, context_schema=Context)
workflow.add_node("ingest_user_event", ingest_user_event)
workflow.add_node("update_requirements", update_requirements)
workflow.add_node("update_material_usage", update_material_usage)
workflow.add_node("generate_or_refine_plan", generate_or_refine_plan)
workflow.add_node("regenerate_plan", regenerate_plan)
workflow.add_node("lock_confirmation", lock_confirmation)
workflow.add_node("build_user_response", build_user_response)
workflow.add_node("build_error_response", build_error_response)

workflow.add_edge(START, "ingest_user_event")
workflow.add_conditional_edges(
    "ingest_user_event",
    route_user_event,
    {
        "chat": "update_requirements",
        "upload_assets": "update_material_usage",
        "regenerate": "regenerate_plan",
        "confirm": "lock_confirmation",
        "invalid": "build_error_response",
    },
)
workflow.add_edge("update_requirements", "generate_or_refine_plan")
workflow.add_edge("generate_or_refine_plan", "build_user_response")
workflow.add_edge("update_material_usage", "build_user_response")
workflow.add_edge("regenerate_plan", "build_user_response")
workflow.add_edge("build_user_response", END)
workflow.add_edge("lock_confirmation", END)
workflow.add_edge("build_error_response", END)

conversation_graph = workflow.compile(name="Conversation Graph")
