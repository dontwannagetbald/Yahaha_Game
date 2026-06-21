# Yahaha LangGraph Agents

This package contains the local LangGraph implementation for Yahaha game creation agents.

Current exported graph:

- `conversation`: first-stage Create conversation graph.

The graph is configured in `langgraph.json`:

```json
{
  "graphs": {
    "conversation": "./src/agent/graph.py:conversation_graph"
  }
}
```

## Setup

Use the project virtualenv:

```bash
cd lan_agents
.venv/bin/python -m pip install -e .
```

Create local environment variables if needed:

```bash
cp .env.example .env
```

LangSmith tracing uses:

```text
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=yahaha-agent-local
```

By default, the conversation graph uses `LLM_PROVIDER=mock`, so model API keys are not required for local tests or CI.

To try an OpenAI-compatible provider for `generate_or_refine_plan`, configure:

```text
LLM_PROVIDER=openai-compatible
OPENAI_COMPATIBLE_API_KEY=...
OPENAI_COMPATIBLE_BASE_URL=https://api.openai.com/v1
OPENAI_COMPATIBLE_MODEL=gpt-5.4-mini
LLM_TIMEOUT_SECONDS=30
```

The recommended first-stage conversation model is `gpt-5.4-mini`: it is enough for requirement collection, concise suggestions, and structured `game_plan` patches. Keep stronger code-generation models for the later `generation_graph`.

Only `generate_or_refine_plan` calls the DesignPlanner provider in the current phase. Routing, requirement updates, material usage, card gating, and confirmation checks remain deterministic.

`ProviderConfig` reads environment variables from the process first, then from the nearest `.env` in the current directory or its parents. This means both of these work:

- Run from the repository root with `.env`.
- Run from `lan_agents/` with either `lan_agents/.env` or the repository root `.env`.

Check the active provider config without printing secrets:

```bash
cd lan_agents
.venv/bin/python -m agent.providers.preflight
```

Expected live-provider output should show `"provider": "openai-compatible"` and `"api_key": "SET"`. If it shows `"provider": "mock"`, add `LLM_PROVIDER=openai-compatible` to the repository root `.env` or `lan_agents/.env`.

For a live multi-turn check, keep passing the returned state into the next run. The first turn may return `conversation_status=collecting` with a follow-up question and short suggestions; once all required `game_plan` fields are filled, the response becomes `ready_to_confirm` and includes a card.

## Run Locally

Validate graph config:

```bash
.venv/bin/langgraph validate
```

Start LangGraph Server and Studio:

```bash
.venv/bin/langgraph dev
```

Open the Studio URL printed by the command. Select the `conversation` graph.

## Fixture Inputs

Fixture files live in `tests/fixtures/` and can be pasted into Studio as graph input:

- `conversation_chat.json`
- `conversation_upload_assets.json`
- `conversation_regenerate.json`
- `conversation_confirm.json`
- `conversation_invalid.json`

Example API call:

```bash
curl -s -X POST http://127.0.0.1:2024/runs/wait \
  -H 'Content-Type: application/json' \
  -d '{"assistant_id":"conversation","input":{"user_event":{"type":"chat","message":"做一个躲避障碍小游戏"}}}'
```

If port `2024` is busy, use the port printed by `langgraph dev`.

## Tests

Run all local tests:

```bash
.venv/bin/python -m pytest -q
```

The test suite covers state schema, node behavior, routing, fixture safety, provider boundaries, DesignPlanner fallback, and conversation graph branches.
