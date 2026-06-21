from agent.conversation_graph.nodes import update_material_usage
from agent.state import ConversationState


def test_update_material_usage_sanitizes_image_asset_and_drops_secrets() -> None:
    state = ConversationState(
        user_event={
            "type": "upload_assets",
            "uploaded_assets": [
                {
                    "asset_id": "img-1",
                    "filename": "cat.png",
                    "mime_type": "image/png",
                    "object_key": "uploads/user/cat.png",
                    "presigned_url": "http://example.test/cat.png?X-Amz-Signature=secret",
                    "token": "secret",
                    "user_hint": "主角",
                }
            ],
        }
    )

    update = update_material_usage(state)
    asset = update["material_usage"]["assets"][0]

    assert asset == {
        "asset_id": "img-1",
        "filename": "cat.png",
        "mime_type": "image/png",
        "intended_use": "character",
        "usage_priority": "primary",
        "user_hint": "主角",
        "agent_note": "已记录素材，后续会在生成阶段按用途使用。",
    }


def test_update_material_usage_infers_audio_video_and_unhinted_image() -> None:
    state = ConversationState(
        user_requirements={
            **ConversationState().user_requirements,
            "must_have": ["躲避障碍"],
        },
        game_plan={
            **ConversationState().game_plan,
            "style": "森林童话",
        },
        user_event={
            "type": "upload_assets",
            "uploaded_assets": [
                {"asset_id": "audio-1", "filename": "bgm.mp3", "mime_type": "audio/mpeg"},
                {"asset_id": "video-1", "filename": "run.mov", "mime_type": "video/quicktime"},
                {"asset_id": "img-2", "filename": "forest.png", "mime_type": "image/png"},
            ],
        },
    )

    update = update_material_usage(state)
    assets = update["material_usage"]["assets"]

    assert [asset["intended_use"] for asset in assets] == [
        "audio",
        "video_reference",
        "visual_reference",
    ]
    assert all(set(asset) == {"asset_id", "filename", "mime_type", "intended_use", "usage_priority", "user_hint", "agent_note"} for asset in assets)


def test_update_material_usage_updates_existing_same_asset() -> None:
    state = ConversationState(
        material_usage={
            "assets": [
                {
                    "asset_id": "asset-1",
                    "filename": "old.png",
                    "mime_type": "image/png",
                    "intended_use": "visual_reference",
                    "usage_priority": "supporting",
                    "user_hint": "",
                    "agent_note": "old",
                }
            ]
        },
        user_event={
            "type": "upload_assets",
            "uploaded_assets": [
                {
                    "asset_id": "asset-1",
                    "filename": "hero.png",
                    "mime_type": "image/png",
                    "user_hint": "主角",
                }
            ],
        },
    )

    update = update_material_usage(state)

    assert len(update["material_usage"]["assets"]) == 1
    assert update["material_usage"]["assets"][0]["filename"] == "hero.png"
    assert update["material_usage"]["assets"][0]["intended_use"] == "character"


def test_update_material_usage_can_replace_existing_assets() -> None:
    state = ConversationState(
        material_usage={
            "assets": [
                {
                    "asset_id": "asset-1",
                    "filename": "old.png",
                    "mime_type": "image/png",
                    "intended_use": "visual_reference",
                    "usage_priority": "supporting",
                    "user_hint": "",
                    "agent_note": "old",
                }
            ]
        },
        user_event={
            "type": "upload_assets",
            "replace_existing_assets": True,
            "uploaded_assets": [
                {
                    "asset_id": "asset-2",
                    "filename": "new.png",
                    "mime_type": "image/png",
                    "user_hint": "背景",
                }
            ],
        },
    )

    update = update_material_usage(state)

    assert update["material_usage"]["assets"] == [
        {
            "asset_id": "asset-2",
            "filename": "new.png",
            "mime_type": "image/png",
            "intended_use": "background",
            "usage_priority": "primary",
            "user_hint": "背景",
            "agent_note": "已记录素材，后续会在生成阶段按用途使用。",
        }
    ]
