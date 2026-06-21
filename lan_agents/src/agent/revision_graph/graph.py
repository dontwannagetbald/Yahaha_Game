"""Post-generation revision subgraph assembly."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from agent.revision_graph.nodes import (
    ask_clarifying_question,
    build_revision_patch,
    create_revision_job_payload,
    load_revision_context,
    understand_revision_intent,
)
from agent.revision_graph.routes import route_revision_intent
from agent.revision_graph.state import RevisionState


workflow = StateGraph(RevisionState)
workflow.add_node("load_revision_context", load_revision_context)
workflow.add_node("understand_revision_intent", understand_revision_intent)
workflow.add_node("ask_clarifying_question", ask_clarifying_question)
workflow.add_node("build_revision_patch", build_revision_patch)
workflow.add_node("create_revision_job_payload", create_revision_job_payload)

workflow.add_edge(START, "load_revision_context")
workflow.add_edge("load_revision_context", "understand_revision_intent")
workflow.add_conditional_edges(
    "understand_revision_intent",
    route_revision_intent,
    {
        "unclear": "ask_clarifying_question",
        "clear": "build_revision_patch",
    },
)
workflow.add_edge("ask_clarifying_question", END)
workflow.add_edge("build_revision_patch", "create_revision_job_payload")
workflow.add_edge("create_revision_job_payload", END)

revision_graph = workflow.compile(name="Revision Graph")
