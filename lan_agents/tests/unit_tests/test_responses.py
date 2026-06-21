from agent.conversation_graph.nodes import build_error_response, build_user_response
from agent.state import ConversationState


def test_build_user_response_suggestions_are_plain_strings() -> None:
    state = ConversationState(
        game_plan={
            **ConversationState().game_plan,
            "title": "星星小猫",
        }
    )

    suggestions = build_user_response(state)["assistant_response"]["suggestions"]

    assert all(isinstance(suggestion, str) for suggestion in suggestions)


def test_build_user_response_uses_planner_followup_when_collecting() -> None:
    state = ConversationState(
        game_plan={
            **ConversationState().game_plan,
            "title": "云朵快跑",
        },
        assistant_response={
            "message": "这个方向不错。你希望它是什么视觉风格？",
            "suggestions": ["梦幻卡通", "像素天空"],
            "card": None,
            "actions": [],
        },
    )

    response = build_user_response(state)["assistant_response"]

    assert response["message"].startswith("🎨 ")
    assert "这个方向不错。你希望它是什么视觉风格？" in response["message"]
    assert response["suggestions"] == ["梦幻卡通", "像素天空"]


def test_build_user_response_does_not_fill_missing_planner_suggestions_locally() -> None:
    state = ConversationState(
        game_plan={
            **ConversationState().game_plan,
            "plan_id": "plan-cat",
            "tags": ["arcade", "casual"],
            "gameplay": "躲避滚石并收集星星",
            "characters": ["小猫"],
        },
        assistant_response={
            "message": "希望游戏是什么美术风格？",
            "suggestions": [],
            "card": None,
            "actions": [],
        },
    )

    response = build_user_response(state)["assistant_response"]

    assert response["message"].startswith("🎨 ")
    assert "希望游戏是什么美术风格？" in response["message"]
    assert response["suggestions"] == []


def test_build_user_response_keeps_model_character_gameplay_suggestions() -> None:
    state = ConversationState(
        game_plan={
            **ConversationState().game_plan,
            "plan_id": "plan-gacha",
            "title": "商店扭蛋机",
            "tags": ["casual", "simulation"],
            "style": "可爱明亮的商店风",
        },
        assistant_response={
            "message": "你这个可爱明亮的商店风很适合扭蛋机主题。接下来先确认一个关键设定：游戏里玩家要扮演谁、在商店里做什么？",
            "suggestions": [
                "扮演店员整理扭蛋机",
                "扮演顾客转扭蛋抽盲盒",
                "扮演玩具店老板经营商店",
                "扮演收藏家集齐整套潮玩",
            ],
            "card": None,
            "actions": [],
        },
    )

    response = build_user_response(state)["assistant_response"]

    assert response["suggestions"] == [
        "扮演店员整理扭蛋机",
        "扮演顾客转扭蛋抽盲盒",
        "扮演玩具店老板经营商店",
        "扮演收藏家集齐整套潮玩",
    ]


def test_build_user_response_does_not_reuse_stale_message_after_upload() -> None:
    state = ConversationState(
        user_event={
            "type": "upload_assets",
            "uploaded_assets": [
                {"asset_id": "asset-1", "filename": "screenshot.png", "mime_type": "image/png"}
            ],
        },
        assistant_response={
            "message": "您好呀，今天想要尝试做个什么样的游戏呢✨？",
            "suggestions": ["重新输入想法", "上传素材"],
            "card": None,
            "actions": [],
        },
    )

    response = build_user_response(state)

    assert response["conversation_status"] == "collecting"
    assert response["assistant_response"] == {
        "message": "",
        "suggestions": [],
        "card": None,
        "actions": [],
    }


def test_build_user_response_keeps_model_followup_even_if_it_looks_stale() -> None:
    state = ConversationState(
        game_plan={
            **ConversationState().game_plan,
            "plan_id": "plan-cat",
            "title": "星星小猫",
            "introduction": "帮助小猫收集星星并躲开滚石",
            "tags": ["arcade", "casual"],
            "gameplay": "躲避滚石并收集星星",
            "core_loop": ["躲避", "收集"],
            "style": "可爱卡通",
            "characters": ["小猫"],
        },
        assistant_response={
            "message": "希望游戏是什么美术风格？",
            "suggestions": ["柔和童话风", "手绘可爱风"],
            "card": None,
            "actions": [],
        },
    )

    response = build_user_response(state)["assistant_response"]

    assert response["message"].startswith("🎨 ")
    assert "希望游戏是什么美术风格？" in response["message"]
    assert response["suggestions"] == ["柔和童话风", "手绘可爱风"]


def test_build_user_response_keeps_model_win_question_when_message_mentions_character() -> None:
    state = ConversationState(
        game_plan={
            **ConversationState().game_plan,
            "plan_id": "plan-witch",
            "tags": ["adventure"],
            "gameplay": "魔女学徒在暗黑学院探索法术冒险",
            "core_loop": ["探索", "施法", "收集"],
            "style": "暗黑奇幻",
            "characters": ["魔女学徒"],
        },
        assistant_response={
            "message": "很好，魔女学徒这个角色很适合暗黑奇幻的法术冒险。接下来我先确认一个关键设定：你希望玩家通过什么方式获得胜利？",
            "suggestions": [
                "完成主线仪式并成为正式魔女",
                "击败守护禁书的最终魔物",
                "收集全部咒印碎片并解开诅咒",
                "救回被黑暗吞噬的同伴",
            ],
            "card": None,
            "actions": [],
        },
    )

    response = build_user_response(state)["assistant_response"]

    assert "通过什么方式获得胜利" in response["message"]
    assert response["suggestions"] == [
        "完成主线仪式并成为正式魔女",
        "击败守护禁书的最终魔物",
        "收集全部咒印碎片并解开诅咒",
        "救回被黑暗吞噬的同伴",
    ]


def test_build_user_response_keeps_model_suggestions_without_keyword_filtering() -> None:
    state = ConversationState(
        game_plan={
            **ConversationState().game_plan,
            "plan_id": "plan-cat",
            "tags": ["arcade", "casual"],
            "gameplay": "躲避滚石并收集星星",
            "core_loop": ["躲避", "收集"],
            "characters": ["小猫"],
        },
        assistant_response={
            "message": "你希望它是什么美术风格？",
            "suggestions": ["星星小猫", "森林快跑", "滚石大冒险"],
            "card": None,
            "actions": [],
        },
    )

    response = build_user_response(state)["assistant_response"]

    assert "美术风格" in response["message"]
    assert response["suggestions"] == ["星星小猫", "森林快跑", "滚石大冒险"]


def test_build_user_response_keeps_model_suggestions_for_gameplay_direction_question() -> None:
    state = ConversationState(
        game_plan={
            **ConversationState().game_plan,
            "plan_id": "plan-eagle",
            "tags": ["arcade", "adventure"],
            "style": "像素风",
            "characters": ["老鹰", "老鼠"],
        },
        assistant_response={
            "message": "像素风很适合“老鹰抓老鼠”这个题材。你希望这款游戏更偏追逐躲避，还是带关卡/任务的冒险？",
            "suggestions": ["星星小猫", "森林快跑", "滚石大冒险"],
            "card": None,
            "actions": [],
        },
    )

    response = build_user_response(state)["assistant_response"]

    assert "追逐躲避" in response["message"]
    assert response["suggestions"] == ["星星小猫", "森林快跑", "滚石大冒险"]


def test_build_user_response_keeps_model_optional_followup_without_local_replacement() -> None:
    state = ConversationState(
        game_plan={
            **ConversationState().game_plan,
            "plan_id": "plan-eagle",
            "tags": ["arcade", "adventure"],
            "gameplay": "关卡冒险中追逐躲避",
            "core_loop": ["追逐", "躲避", "闯关"],
            "style": "像素风",
            "characters": ["老鹰", "老鼠"],
        },
        assistant_response={
            "message": "老鼠除了跑和跳，还想要哪种特别能力？",
            "suggestions": ["隐身", "冲刺", "放陷阱"],
            "card": None,
            "actions": [],
        },
    )

    response = build_user_response(state)["assistant_response"]

    assert "特别能力" in response["message"]
    assert response["suggestions"] == ["隐身", "冲刺", "放陷阱"]


def test_build_user_response_does_not_ask_user_for_introduction() -> None:
    state = ConversationState(
        game_plan={
            **ConversationState().game_plan,
            "plan_id": "plan-cat",
            "title": "星星小猫",
            "tags": ["arcade", "casual"],
            "gameplay": "躲避滚石并收集星星",
            "core_loop": ["躲避", "收集"],
            "style": "可爱卡通",
            "characters": ["小猫"],
            "win_condition": "收集10颗星星",
            "lose_condition": "撞到滚石",
            "controls": "方向键移动",
        },
    )

    response = build_user_response(state)

    assert response["conversation_status"] == "ready_to_confirm"
    assert response["assistant_response"]["card"] is None
    assert "简介" not in response["assistant_response"]["message"]
    assert "介绍" not in response["assistant_response"]["message"]


def test_build_error_response_is_safe_for_user_display() -> None:
    state = ConversationState(
        assistant_response={
            "message": "Traceback token=secret X-Amz-Signature=abc",
            "suggestions": [{"label": "bad"}],
            "card": {"title": "bad"},
            "actions": ["generate"],
        }
    )

    response = build_error_response(state)["assistant_response"]

    assert "Traceback" not in response["message"]
    assert "secret" not in response["message"]
    assert "X-Amz-Signature" not in response["message"]
    assert all(isinstance(suggestion, str) for suggestion in response["suggestions"])
    assert response["card"] is None
    assert response["actions"] == []
