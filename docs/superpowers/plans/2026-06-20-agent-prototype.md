# Agent Prototype 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 在独立 `agent/` 目录中实现一个可本地调试的 LangGraph 原型，打通从对话收敛到产出 `manifest.json` 的完整流程。

**架构：** 原型拆成 `conversation_graph` 和 `generation_graph` 两个子图，前者负责 `confirmation_card + structured_design_state`，后者负责 `asset_analysis + game_spec + bundle + validation`。通过 `runner.py` 和 fixture 驱动本地执行，先用 mock provider 跑通，再预留 OpenAI-compatible provider。

**技术栈：** Python 3.13、LangGraph、Pydantic、pytest、静态 HTML5 bundle。

---

## 文件结构

- 创建：`agent/README.md`
- 创建：`agent/pyproject.toml`
- 创建：`agent/.env.example`
- 创建：`agent/app/graph/state.py`
- 创建：`agent/app/graph/conversation_graph.py`
- 创建：`agent/app/graph/generation_graph.py`
- 创建：`agent/app/agents/design_agent.py`
- 创建：`agent/app/agents/asset_agent.py`
- 创建：`agent/app/agents/spec_builder.py`
- 创建：`agent/app/agents/developer_agent.py`
- 创建：`agent/app/agents/validator_agent.py`
- 创建：`agent/app/providers/mock_provider.py`
- 创建：`agent/app/providers/openai_compatible.py`
- 创建：`agent/app/tools/asset_tools.py`
- 创建：`agent/app/tools/bundle_tools.py`
- 创建：`agent/app/tools/manifest_tools.py`
- 创建：`agent/app/tools/logging_tools.py`
- 创建：`agent/app/runner.py`
- 创建：`agent/fixtures/sample_request.json`
- 创建：`agent/tests/test_conversation_graph.py`
- 创建：`agent/tests/test_generation_graph.py`
- 创建：`agent/tests/test_runner_cli.py`

## 任务 1：搭建项目骨架和依赖入口

**文件：**
- 创建：`agent/pyproject.toml`
- 创建：`agent/README.md`
- 创建：`agent/.env.example`

- [ ] **步骤 1：创建失败的测试入口约束**

在 `agent/tests/test_runner_cli.py` 里先断言 `python -m app.runner --help` 可以返回 0，并暴露 `conversation` 和 `generate` 两个子命令。

- [ ] **步骤 2：运行测试验证失败**

运行：`cd agent && python3 -m pytest tests/test_runner_cli.py -v`
预期：FAIL，提示 `app.runner` 不存在。

- [ ] **步骤 3：实现最小项目骨架**

创建 `pyproject.toml`、`README.md`、`app/__init__.py` 和最小 `runner.py`，保证 CLI 可启动并显示帮助。

- [ ] **步骤 4：运行测试验证通过**

运行：`cd agent && python3 -m pytest tests/test_runner_cli.py -v`
预期：PASS

## 任务 2：实现对话状态和 conversation graph

**文件：**
- 创建：`agent/app/graph/state.py`
- 创建：`agent/app/graph/conversation_graph.py`
- 创建：`agent/app/agents/design_agent.py`
- 创建：`agent/tests/test_conversation_graph.py`

- [ ] **步骤 1：编写失败的 conversation graph 测试**

断言输入一段 prompt 和一条用户消息后，graph 输出：
- `structured_design_state.core_loop`
- `structured_design_state.win_condition`
- `confirmation_card.title`
- `confirmation_card.core_gameplay`

- [ ] **步骤 2：运行测试验证失败**

运行：`cd agent && python3 -m pytest tests/test_conversation_graph.py -v`
预期：FAIL，提示 state 或 graph 不存在。

- [ ] **步骤 3：实现最小状态模型和 Design Agent**

用 Pydantic 定义对话状态、确认卡片和设计状态；Design Agent 先使用 deterministic mock 逻辑把 fixture prompt 映射为结构化字段。

- [ ] **步骤 4：实现 conversation graph**

使用 LangGraph `StateGraph`，至少包含：
- `ingest_user_input`
- `update_design_state`
- `build_confirmation_card`

- [ ] **步骤 5：运行测试验证通过**

运行：`cd agent && python3 -m pytest tests/test_conversation_graph.py -v`
预期：PASS

## 任务 3：实现 generation graph 和产物生成

**文件：**
- 创建：`agent/app/graph/generation_graph.py`
- 创建：`agent/app/agents/asset_agent.py`
- 创建：`agent/app/agents/spec_builder.py`
- 创建：`agent/app/agents/developer_agent.py`
- 创建：`agent/app/tools/asset_tools.py`
- 创建：`agent/app/tools/bundle_tools.py`
- 创建：`agent/app/tools/manifest_tools.py`
- 创建：`agent/tests/test_generation_graph.py`

- [ ] **步骤 1：编写失败的 generation graph 测试**

断言给定 fixture 输入后，graph 会在临时输出目录生成：
- `manifest.json`
- `index.html`
- `style.css`
- `game.js`

并返回：
- `artifact_prefix`
- `manifest_path`
- `entry_path`

- [ ] **步骤 2：运行测试验证失败**

运行：`cd agent && python3 -m pytest tests/test_generation_graph.py -v`
预期：FAIL，提示 generation graph 或 agent 节点不存在。

- [ ] **步骤 3：实现 Asset Agent 和 Spec Builder**

Asset Agent 先输出素材摘要和用途建议；Spec Builder 生成 `game_spec`，至少包含 `title`、`description`、`gameplay_loop`、`controls` 和 `asset_bindings`。

- [ ] **步骤 4：实现 Developer Agent**

用最小静态模板生成 bundle 文件，并通过 manifest tool 生成 `manifest.json`。

- [ ] **步骤 5：运行测试验证通过**

运行：`cd agent && python3 -m pytest tests/test_generation_graph.py -v`
预期：PASS

## 任务 4：实现 Validator Agent 和错误路径

**文件：**
- 创建：`agent/app/agents/validator_agent.py`
- 创建：`agent/app/tools/logging_tools.py`
- 修改：`agent/tests/test_generation_graph.py`

- [ ] **步骤 1：编写失败的校验测试**

增加一个测试：删除 `game.js` 后运行 Validator，预期返回：
- `valid = false`
- `failed_step = "validate_bundle"`
- `error_message` 非空

- [ ] **步骤 2：运行测试验证失败**

运行：`cd agent && python3 -m pytest tests/test_generation_graph.py -k validate -v`
预期：FAIL，提示 validator 缺失或未正确报错。

- [ ] **步骤 3：实现 Validator Agent**

校验 manifest、entry、scripts、styles、assets 路径存在；生成脱敏错误摘要和 retry hint。

- [ ] **步骤 4：运行测试验证通过**

运行：`cd agent && python3 -m pytest tests/test_generation_graph.py -v`
预期：PASS

## 任务 5：补全 runner 和 fixture 驱动闭环

**文件：**
- 创建：`agent/fixtures/sample_request.json`
- 修改：`agent/app/runner.py`
- 修改：`agent/tests/test_runner_cli.py`

- [ ] **步骤 1：编写失败的 CLI 闭环测试**

断言通过 `generate` 子命令读取 fixture 后，CLI 会在输出目录生成 bundle，并打印 `manifest_path`。

- [ ] **步骤 2：运行测试验证失败**

运行：`cd agent && python3 -m pytest tests/test_runner_cli.py -k generate -v`
预期：FAIL，提示 CLI 未接 generation graph。

- [ ] **步骤 3：实现 CLI 闭环**

让 `runner.py` 支持：
- `conversation --input <json>`
- `generate --input <json> --output-dir <path>`

- [ ] **步骤 4：运行测试验证通过**

运行：`cd agent && python3 -m pytest tests/test_runner_cli.py -v`
预期：PASS

## 任务 6：补 OpenAI-compatible provider 骨架

**文件：**
- 创建：`agent/app/providers/mock_provider.py`
- 创建：`agent/app/providers/openai_compatible.py`
- 修改：`agent/app/runner.py`

- [ ] **步骤 1：编写失败的 provider 选择测试**

断言当 provider 为 `mock` 时不需要 API key；当 provider 为 `openai-compatible` 且未设置 key 时抛出明确错误。

- [ ] **步骤 2：运行测试验证失败**

运行：`cd agent && python3 -m pytest tests/test_runner_cli.py -k provider -v`
预期：FAIL，提示 provider 层不存在。

- [ ] **步骤 3：实现 provider 抽象**

保留 mock provider 为默认可运行路径；OpenAI-compatible provider 先实现配置校验和接口骨架。

- [ ] **步骤 4：运行测试验证通过**

运行：`cd agent && python3 -m pytest tests/test_runner_cli.py -v`
预期：PASS

## 最终验证

- [ ] 运行：`cd agent && python3 -m pytest tests -v`
预期：全部通过

- [ ] 运行：`cd agent && python3 -m app.runner conversation --input fixtures/sample_request.json`
预期：输出 confirmation card 和 design state 摘要

- [ ] 运行：`cd agent && python3 -m app.runner generate --input fixtures/sample_request.json --output-dir output/demo`
预期：生成完整 bundle，并输出 manifest 路径

计划已完成并保存到 `docs/superpowers/plans/2026-06-20-agent-prototype.md`。两种执行方式：

**1. 子代理驱动（推荐）** - 每个任务调度一个新的子代理，任务间进行审查，快速迭代

**2. 内联执行** - 在当前会话中使用 executing-plans 执行任务，批量执行并设有检查点
