# Yahaha Agent Prototype

独立于前后端的本地 Agent 原型目录。

## 当前能力

- `conversation`：根据 prompt 生成 `confirmation_card` 和 `structured_design_state`
- `generate`：根据设计状态生成静态 bundle 和 `manifest.json`
- `langgraph.json`：提供 LangGraph 平台 / 自托管部署入口
- `my_agent/requirements.txt`：提供 LangGraph 部署依赖定义
- `LangSmith tracing`：支持通过环境变量开启 conversation / generation 的运行追踪

## 运行

```bash
cd agent
../.venv/bin/python3 -m pytest tests -v
../.venv/bin/python3 -m app.runner conversation --input fixtures/sample_request.json
../.venv/bin/python3 -m app.runner generate --input fixtures/sample_request.json --output-dir output/demo
```

## LangSmith

在 `agent/.env` 中配置以下变量即可开启 tracing：

```bash
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_pt_xxx
LANGSMITH_PROJECT=yahaha-agent
LANGSMITH_ENDPOINT=
```

说明：

- `LANGSMITH_TRACING=true` 时，runner 会为 `conversation` 和 `generate` 打 trace。
- `run_name` 分别为 `yahaha-agent-conversation` 和 `yahaha-agent-generate`。
- tags 默认包含 `yahaha-agent`、命令名，以及可选的 provider 名。
- metadata 默认包含 `asset_count`、`provider`、`has_confirmation_card`、`output_dir` 等摘要字段。
- 如果开启 tracing 但没有配置 `LANGSMITH_API_KEY`，runner 会明确报错。

## LangGraph 部署配置

- 图导出入口：`my_agent/agent.py`
- 部署配置：`langgraph.json`
- 依赖清单：`my_agent/requirements.txt`
- 环境变量模板：`.env.example`

如果要按 LangGraph 平台约定运行，请先复制环境变量模板：

```bash
cd agent
cp .env.example .env
```

## 说明

- 当前环境若缺少 `langgraph`，会退回到本地兼容层，保持 graph 结构和调用方式一致。
- 待依赖安装恢复后，可切换到真实 `langgraph` 包运行。
- 当前项目请优先使用仓库根目录的 `.venv/bin/python3`，避免系统 `/usr/bin/python3` 与已安装依赖所在解释器不一致。
- 当前 `.venv` 已可导出真实 `CompiledStateGraph`，`my_agent/agent.py` 中的 `conversation_graph` 和 `generation_graph` 可被 `langgraph.json` 直接引用。
- LangSmith 采用懒加载，只有在 `LANGSMITH_TRACING=true` 时才会创建 `langsmith.Client` 并进入 tracing context。
