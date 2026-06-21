from agent.conversation_graph.routes import route_user_event
from agent.state import ConversationState


def test_route_user_event_supports_phase_one_event_types() -> None:
    for event_type in ("chat", "upload_assets", "regenerate", "confirm"):
        state = ConversationState(user_event={"type": event_type})

        assert route_user_event(state) == event_type


def test_route_user_event_returns_invalid_for_unknown_or_error_state() -> None:
    assert route_user_event(ConversationState(user_event={"type": "oops"})) == "invalid"
    assert (
        route_user_event(
            ConversationState(
                conversation_status="error",
                user_event={"type": "chat", "message": "hello"},
            )
        )
        == "invalid"
    )
