import json
from pathlib import Path


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def test_conversation_fixtures_cover_all_user_event_routes() -> None:
    expected = {
        "conversation_chat.json": "chat",
        "conversation_upload_assets.json": "upload_assets",
        "conversation_regenerate.json": "regenerate",
        "conversation_confirm.json": "confirm",
        "conversation_invalid.json": "unsupported",
    }

    for filename, event_type in expected.items():
        data = json.loads((FIXTURE_DIR / filename).read_text())
        assert data["user_event"]["type"] == event_type


def test_conversation_fixtures_do_not_contain_secrets_or_presigned_urls() -> None:
    unsafe_tokens = ["X-Amz-Signature", "presigned", "api_key", "token", "password", "secret"]

    for path in FIXTURE_DIR.glob("conversation_*.json"):
        text = path.read_text()
        assert not any(token in text for token in unsafe_tokens), path.name
