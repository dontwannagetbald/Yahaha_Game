"""Top-level graph exports for LangGraph configuration."""

from agent.conversation_graph.graph import conversation_graph
from agent.generation_graph.graph import generation_graph
from agent.revision_graph.graph import revision_graph

# Backward-compatible alias for template tests and imports during migration.
graph = conversation_graph
