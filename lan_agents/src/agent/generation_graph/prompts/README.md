# Generation Graph Prompt Pack

This directory contains the Yahaha_Play generation prompt pack inspired by OpenGame's disciplined pipeline, adapted for this project's LangGraph and static bundle architecture.

The prompts are contracts for future `generation_graph` nodes. They do not execute by themselves yet.

## Files

- `classify_game_type.md`: classifies a confirmed game idea by mechanics, physics, perspective, and runtime structure.
- `generate_technical_gdd.md`: turns confirmed first-stage state into a six-section technical GDD.
- `generate_asset_work_order.md`: converts the GDD asset registry and uploaded asset metadata into a safe static-bundle asset plan.
- `generate_static_bundle.md`: instructs the coding node to produce `manifest.json`, `index.html`, `style.css`, `game.js`, and `assets/*`.
- `validate_bundle.md`: defines final validator checks for file completeness, manifest integrity, iframe safety, runtime boot, gameplay completeness, asset integrity, and storage readiness.

## Pipeline

```text
confirmed create_session
  -> classify_game_type
  -> generate_technical_gdd
  -> generate_asset_work_order
  -> generate_static_bundle
  -> validate_bundle
  -> backend upload / draft game creation
```

## Project Constraints

Generated games must remain static HTML5 iframe bundles:

```text
manifest.json
index.html
style.css
game.js
assets/*
```

They must not require npm packages, a dev server, private runtime URLs, backend execution, or parent-page privileges.
