from __future__ import annotations


def build_game_spec(request: dict[str, object], asset_analysis: list[dict[str, object]]) -> dict[str, object]:
    confirmation = dict(request["confirmation_card"])
    design_state = dict(request["structured_design_state"])
    return {
        "spec_version": "1.0",
        "title": confirmation["title"],
        "description": confirmation["short_description"],
        "genre": confirmation["game_type"],
        "platform": "html5-iframe",
        "gameplay_loop": design_state["core_loop"],
        "objective": confirmation["win_lose_condition"],
        "fail_states": [design_state["lose_condition"]],
        "controls": design_state["controls_detail"],
        "entities": [
            {"name": "player", "role": design_state["player_role"]},
            {"name": "energy_orb", "role": "collectible"},
            {"name": "hazard", "role": "obstacle"},
        ],
        "ui_hud": ["timer", "score", "hp"],
        "art_direction": design_state["visual_style"],
        "asset_bindings": asset_analysis,
    }

