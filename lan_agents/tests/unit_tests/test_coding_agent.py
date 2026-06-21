import json
from pathlib import Path

import pytest

from agent.generation_graph.orchestrator.planner import deterministic_contracts
from agent.generation_graph.state import GenerationState
from agent.providers import MockLLMProvider, ProviderError


def _load_generation_fixture() -> dict:
    fixture_path = (
        Path(__file__).parents[2]
        / "src"
        / "agent"
        / "generation_graph"
        / "fixtures"
        / "generation_confirmed_session.json"
    )
    return json.loads(fixture_path.read_text())


def _build_coding_state(tmp_path: Path) -> GenerationState:
    fixture = _load_generation_fixture()
    state = GenerationState(**fixture)
    contracts = deterministic_contracts(state)
    state.development_brief = contracts["development_brief"]
    state.asset_manifest_plan = contracts["asset_manifest_plan"]
    state.game_spec = contracts["game_spec"]
    state.artifact_workspace = str(tmp_path / "artifact_workspace")
    return state


def test_draft_code_writes_bundle_files_inside_workspace(tmp_path: Path) -> None:
    from agent.generation_graph.coding_agent.draft_code.node import draft_code

    state = _build_coding_state(tmp_path)
    provider = MockLLMProvider(
        response={
            "index_html": "<!doctype html><html><head><link rel='stylesheet' href='style.css'></head><body><canvas id='game'></canvas><script src='game.js'></script></body></html>",
            "style_css": "body { margin: 0; background: #101418; }",
            "game_js": "const player = 'assets/player.png'; console.log(player);",
            "coding_notes": [
                "Use canvas rendering only.",
                "Do not depend on external libraries.",
            ],
        }
    )

    update = draft_code(state, provider=provider)

    code_artifacts = update["code_artifacts"]
    assert code_artifacts["referenced_asset_paths"] == ["assets/player.png"]
    assert [item["relative_path"] for item in code_artifacts["files"]] == [
        "index.html",
        "style.css",
        "game.js",
        "manifest_draft.json",
    ]
    assert Path(code_artifacts["index_html_path"]).exists()
    assert Path(code_artifacts["style_css_path"]).exists()
    assert Path(code_artifacts["game_js_path"]).exists()
    assert Path(code_artifacts["manifest_draft_path"]).exists()
    for key in (
        "index_html_path",
        "style_css_path",
        "game_js_path",
        "manifest_draft_path",
    ):
        assert str(Path(code_artifacts[key]).resolve()).startswith(
            str(Path(state.artifact_workspace).resolve())
        )
    assert update["manifest_draft"]["assets"] == ["assets/player.png"]
    assert update["manifest_draft"]["cover"] == "assets/cover.png"
    assert update["manifest_draft"]["title"] == "星星小猫冒险"
    assert update["manifest_draft"]["description"] == "帮助小猫在森林里收集星星，避开滚石和树桩，坚持到倒计时结束。"


def test_draft_code_rejects_external_cdn_reference(tmp_path: Path) -> None:
    from agent.generation_graph.coding_agent.draft_code.node import draft_code

    state = _build_coding_state(tmp_path)
    provider = MockLLMProvider(
        response={
            "index_html": "<html><head><script src='https://cdn.example.com/phaser.js'></script></head><body><script src='game.js'></script></body></html>",
            "style_css": "body { margin: 0; }",
            "game_js": "console.log('hello');",
            "coding_notes": [],
        }
    )

    with pytest.raises(ProviderError, match="external|CDN|remote"):
        draft_code(state, provider=provider)


def test_draft_code_allows_ui_text_fraction_that_starts_with_slash(
    tmp_path: Path,
) -> None:
    from agent.generation_graph.coding_agent.draft_code.node import draft_code

    state = _build_coding_state(tmp_path)
    state.asset_manifest_plan = []
    state.development_brief["allowed_asset_paths"] = []
    provider = MockLLMProvider(
        response={
            "index_html": "<!doctype html><html><head><link rel='stylesheet' href='style.css'></head><body><canvas id='game'></canvas><script src='game.js'></script></body></html>",
            "style_css": "body { margin: 0; }",
            "game_js": "let clues=0; progress.textContent='线索 '+clues+'/6';",
            "coding_notes": [],
        }
    )

    update = draft_code(state, provider=provider)

    assert update["manifest_draft"]["assets"] == []


def test_draft_code_rejects_absolute_local_path(tmp_path: Path) -> None:
    from agent.generation_graph.coding_agent.draft_code.node import draft_code

    state = _build_coding_state(tmp_path)
    provider = MockLLMProvider(
        response={
            "index_html": "<!doctype html><html><head><link rel='stylesheet' href='style.css'></head><body><canvas id='game'></canvas><script src='game.js'></script></body></html>",
            "style_css": "body { margin: 0; }",
            "game_js": "const bad='/Users/root1/workspace/Yahaha_Game/assets/player.png';",
            "coding_notes": [],
        }
    )

    with pytest.raises(ProviderError, match="absolute local path"):
        draft_code(state, provider=provider)


def test_draft_code_rejects_asset_reference_outside_manifest_plan(tmp_path: Path) -> None:
    from agent.generation_graph.coding_agent.draft_code.node import draft_code

    state = _build_coding_state(tmp_path)
    provider = MockLLMProvider(
        response={
            "index_html": "<html><head><link rel='stylesheet' href='style.css'></head><body><img src='assets/not-planned.png'><script src='game.js'></script></body></html>",
            "style_css": "body { margin: 0; }",
            "game_js": "console.log('hello');",
            "coding_notes": [],
        }
    )

    with pytest.raises(ProviderError, match="asset_manifest_plan|planned asset"):
        draft_code(state, provider=provider)


def test_draft_code_allows_empty_manifest_for_procedural_assets(tmp_path: Path) -> None:
    from agent.generation_graph.coding_agent.draft_code.node import draft_code

    state = _build_coding_state(tmp_path)
    state.asset_manifest_plan = []
    state.development_brief["allowed_asset_paths"] = []
    provider = MockLLMProvider(
        response={
            "index_html": "<!doctype html><html><head><link rel='stylesheet' href='style.css'></head><body><canvas id='game'></canvas><script src='game.js'></script></body></html>",
            "style_css": "body { margin: 0; background: #101418; }",
            "game_js": "const canvas = document.getElementById('game'); console.log(canvas);",
            "coding_notes": ["draw background and player procedurally"],
        }
    )

    update = draft_code(state, provider=provider)

    assert update["code_artifacts"]["referenced_asset_paths"] == []
    assert update["manifest_draft"]["assets"] == []
    assert update["manifest_draft"]["cover"] == ""


def test_draft_code_requests_large_token_budget_for_real_bundle_output(
    tmp_path: Path,
) -> None:
    from agent.generation_graph.coding_agent.draft_code.node import draft_code

    state = _build_coding_state(tmp_path)
    provider = MockLLMProvider(
        response={
            "index_html": "<!doctype html><html><head><link rel='stylesheet' href='style.css'></head><body><canvas id='game'></canvas><script src='game.js'></script></body></html>",
            "style_css": "body { margin: 0; background: #101418; }",
            "game_js": "const player = 'assets/player.png'; console.log(player);",
            "coding_notes": ["bundle output must not be truncated"],
        }
    )

    draft_code(state, provider=provider)

    assert provider.calls[0]["max_completion_tokens"] >= 12000


def test_draft_code_prompt_enforces_compact_json_safe_bundle_output(
    tmp_path: Path,
) -> None:
    from agent.generation_graph.coding_agent.draft_code.node import draft_code

    state = _build_coding_state(tmp_path)
    provider = MockLLMProvider(
        response={
            "index_html": "<!doctype html><html><head><link rel='stylesheet' href='style.css'></head><body><canvas id='game'></canvas><script src='game.js'></script></body></html>",
            "style_css": "body { margin: 0; background: #101418; }",
            "game_js": "const player = 'assets/player.png'; console.log(player);",
            "coding_notes": ["keep output compact and json-safe"],
        }
    )

    draft_code(state, provider=provider)

    system_prompt = provider.calls[0]["messages"][0].content
    assert "compact" in system_prompt.lower()
    assert "single quotes" in system_prompt.lower()
    assert "valid json strings" in system_prompt.lower()
    assert "game_ready" in system_prompt


def test_draft_code_uses_default_temperature_for_real_provider(
    tmp_path: Path,
) -> None:
    from agent.generation_graph.coding_agent.draft_code.node import draft_code

    state = _build_coding_state(tmp_path)
    provider = MockLLMProvider(
        response={
            "index_html": "<!doctype html><html><head><link rel='stylesheet' href='style.css'></head><body><canvas id='game'></canvas><script src='game.js'></script></body></html>",
            "style_css": "body { margin: 0; background: #101418; }",
            "game_js": "const player = 'assets/player.png'; console.log(player);",
            "coding_notes": ["default temperature matches gpt-5.5 constraints"],
        }
    )

    draft_code(state, provider=provider)

    assert provider.calls[0]["temperature"] == 1.0


def test_draft_code_accepts_single_string_coding_note(tmp_path: Path) -> None:
    from agent.generation_graph.coding_agent.draft_code.node import draft_code

    state = _build_coding_state(tmp_path)
    provider = MockLLMProvider(
        response={
            "index_html": "<!doctype html><html><head><link rel='stylesheet' href='style.css'></head><body><canvas id='game'></canvas><script src='game.js'></script></body></html>",
            "style_css": "body { margin: 0; background: #101418; }",
            "game_js": "const player = 'assets/player.png'; console.log(player);",
            "coding_notes": "keep runtime simple",
        }
    )

    update = draft_code(state, provider=provider)

    assert update["coding_notes"] == ["keep runtime simple"]


def test_draft_code_adds_required_game_ready_signal_when_provider_omits_it(
    tmp_path: Path,
) -> None:
    from agent.generation_graph.coding_agent.draft_code.node import draft_code

    state = _build_coding_state(tmp_path)
    state.asset_manifest_plan = []
    state.development_brief["allowed_asset_paths"] = []
    provider = MockLLMProvider(
        response={
            "index_html": "<!doctype html><html><head><link rel='stylesheet' href='style.css'></head><body><canvas id='game'></canvas><script src='game.js'></script></body></html>",
            "style_css": "body { margin: 0; background: #101418; }",
            "game_js": (
                "const canvas=document.getElementById('game');"
                "const ctx=canvas.getContext('2d');"
                "window.addEventListener('keydown',()=>{});"
                "ctx.fillRect(0,0,canvas.width,canvas.height);"
            ),
            "coding_notes": ["provider omitted ready signal"],
        }
    )

    update = draft_code(state, provider=provider)
    game_js = Path(update["code_artifacts"]["game_js_path"]).read_text(encoding="utf-8")

    assert "window.parent.postMessage({ type: 'game_ready' }, '*');" in game_js


def test_draft_code_retries_once_when_provider_returns_invalid_json(
    tmp_path: Path,
) -> None:
    from agent.generation_graph.coding_agent.draft_code.node import draft_code

    class FlakyProvider:
        def __init__(self) -> None:
            self.calls = []
            self._attempt = 0

        def complete_json(self, **kwargs):  # type: ignore[no-untyped-def]
            self.calls.append(kwargs)
            self._attempt += 1
            if self._attempt == 1:
                raise ProviderError("LLM provider returned invalid JSON")
            return {
                "index_html": "<!doctype html><html><head><link rel='stylesheet' href='style.css'></head><body><canvas id='game'></canvas><script src='game.js'></script></body></html>",
                "style_css": "body { margin: 0; background: #101418; }",
                "game_js": "const player = 'assets/player.png'; console.log(player);",
                "coding_notes": ["retry succeeded"],
            }

    state = _build_coding_state(tmp_path)
    provider = FlakyProvider()

    update = draft_code(state, provider=provider)

    assert update["coding_notes"] == ["retry succeeded"]
    assert len(provider.calls) == 2


def test_draft_code_retries_once_when_provider_request_fails(
    tmp_path: Path,
) -> None:
    from agent.generation_graph.coding_agent.draft_code.node import draft_code

    class FlakyRequestProvider:
        def __init__(self) -> None:
            self.calls = []

        def complete_json(self, **kwargs):  # type: ignore[no-untyped-def]
            self.calls.append(kwargs)
            if len(self.calls) == 1:
                raise ProviderError("LLM provider request failed: TimeoutError: timed out")
            return {
                "index_html": "<!doctype html><html><head><link rel='stylesheet' href='style.css'></head><body><canvas id='game'></canvas><script src='game.js'></script></body></html>",
                "style_css": "body { margin: 0; background: #101418; }",
                "game_js": "const player = 'assets/player.png'; console.log(player);",
                "coding_notes": ["request retry succeeded"],
            }

    state = _build_coding_state(tmp_path)
    provider = FlakyRequestProvider()

    update = draft_code(state, provider=provider)

    assert update["coding_notes"] == ["request retry succeeded"]
    assert len(provider.calls) == 2


def test_draft_code_retries_once_when_provider_exhausts_completion_budget(
    tmp_path: Path,
) -> None:
    from agent.generation_graph.coding_agent.draft_code.node import draft_code

    class TruncatedProvider:
        def __init__(self) -> None:
            self.calls = []

        def complete_json(self, **kwargs):  # type: ignore[no-untyped-def]
            self.calls.append(kwargs)
            if len(self.calls) == 1:
                raise ProviderError(
                    "LLM provider stopped because max_completion_tokens was exhausted "
                    "(finish_reason=length, completion_tokens=5200, reasoning_tokens=5200)"
                )
            return {
                "index_html": "<!doctype html><html><head><link rel='stylesheet' href='style.css'></head><body><canvas id='game'></canvas><script src='game.js'></script></body></html>",
                "style_css": "body { margin: 0; background: #101418; }",
                "game_js": "const player = 'assets/player.png'; console.log(player);",
                "coding_notes": ["length retry succeeded"],
            }

    state = _build_coding_state(tmp_path)
    provider = TruncatedProvider()

    update = draft_code(state, provider=provider)

    assert update["coding_notes"] == ["length retry succeeded"]
    assert len(provider.calls) == 2


def test_draft_code_retries_once_with_safety_feedback(
    tmp_path: Path,
) -> None:
    from agent.generation_graph.coding_agent.draft_code.node import draft_code

    class SafetyRetryProvider:
        def __init__(self) -> None:
            self.calls = []

        def complete_json(self, **kwargs):  # type: ignore[no-untyped-def]
            self.calls.append(kwargs)
            if len(self.calls) == 1:
                return {
                    "index_html": "<!doctype html><html><head><script src='https://cdn.example.com/phaser.js'></script></head><body><script src='game.js'></script></body></html>",
                    "style_css": "body { margin: 0; }",
                    "game_js": "console.log('unsafe first draft');",
                    "coding_notes": ["first draft used a CDN"],
                }
            return {
                "index_html": "<!doctype html><html><head><link rel='stylesheet' href='style.css'></head><body><canvas id='game'></canvas><script src='game.js'></script></body></html>",
                "style_css": "body { margin: 0; }",
                "game_js": "const canvas = document.getElementById('game'); console.log(canvas);",
                "coding_notes": ["fixed unsafe reference after feedback"],
            }

    state = _build_coding_state(tmp_path)
    state.asset_manifest_plan = []
    provider = SafetyRetryProvider()

    update = draft_code(state, provider=provider)

    assert update["coding_notes"] == ["fixed unsafe reference after feedback"]
    assert len(provider.calls) == 2
    retry_payload = provider.calls[1]["messages"][1].content
    assert "previous_attempt_error" in retry_payload
    assert "remote or CDN reference" in retry_payload
