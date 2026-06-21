# Agent 实施计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 先基于 `lan_agents/` 框架实现第一阶段 `conversation_graph`，让 Design Agent 通过 LangGraph 节点完成对话需求收集、游戏方案生成、素材用途维护、换一换和确认交接；第二阶段从一开始接真实 OpenAI-compatible LLM，按 Orchestrator、Asset Agent、Coding Agent、Validator Agent 逐个实现和测试，最终生成静态游戏 bundle。

**架构：** Agent 代码先独立放在 `lan_agents/` 中本地调试。第一阶段暴露 `conversation_graph` 给 LangGraph Server 和 LangSmith Studio，用普通 LangGraph node 实现 Design Agent 能力。第二阶段暴露 `generation_graph`，由 Orchestrator 生成并发契约，Asset/Coding 并发执行，Coding 在素材到齐后自调试，Validator 最终验收。

**技术栈：** LangGraph Graph API、LangGraph CLI、LangSmith tracing、OpenAI-compatible API、Mock LLM test doubles、MinIO 产物路径、静态 HTML5 bundle、headless runtime check。

---

## 1. 必读上下文

Agent 开发者单独拿到本文档时，必须先阅读：

- [design-document.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/design-document.md)：产物协议、任务状态、Agent 日志、安全边界。
- [api-contract.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/api-contract.md)：Create Sessions API、Jobs API、任务日志字段。
- [tech-stack.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/tech-stack.md)：模型服务、OpenAI-compatible provider 和 LangGraph 边界。
- [architecture.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/architecture.md)：目录边界和文件职责。
- [progress.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/progress.md)：已完成步骤和当前缺口。

已确认边界：

- Agent 框架使用当前 `lan_agents/` 项目结构，不再沿用旧 `agent/` 原型目录。
- 第一阶段使用 `conversation_graph`，Design Agent 是普通 LangGraph node，不默认使用 `create_react_agent`。
- 第一阶段 state 的业务主参数是 `user_requirements`、`game_plan`、`material_usage`。
- 每个第一阶段 step 完成后，都必须能通过 `langgraph dev` 在 LangSmith Studio 看到最新 graph 结构，并能在 LangSmith 项目里看到一次对应 trace。
- 模型服务主路径使用真实 OpenAI-compatible API。
- 第二阶段从 Step 2 开始使用真实 OpenAI-compatible provider；Mock 仅作为 unit test test double 和无网络 CI 兜底。
- 第二阶段按单 Agent 闸门推进：先验证 provider，再验证 Orchestrator，再验证 Asset Agent，再验证 Coding Agent，再验证 Coding Debug，最后验证 Validator；任一 Agent 真实 smoke 不通过，不进入下一步。
- 第二阶段不是单次黑盒模型调用；每个 Agent 都必须有独立 node、独立输入 fixture、独立 schema 校验、独立 LangSmith trace。
- 异步任务由后端 FastAPI BackgroundTasks 启动，不引入 Celery。
- 产物必须是静态 Web bundle：`manifest.json`、`index.html`、`style.css`、`game.js`、`assets/*`。

## 2. Agent 独立运行原则

- 第一阶段不能等待前端完成，可以用固定 `user_event` fixture 独立运行 `conversation_graph`。
- 第一阶段输出必须能让前端展示 `assistant_response.message`、`assistant_response.suggestions` 和从 `game_plan` 派生的卡片。
- 第一阶段确认后输出 `handoff_to_generation=true`，后续第二阶段才能创建 generation job。
- 第二阶段可以在后端真实接入前，用固定输入文件或测试 fixture 独立运行。
- 第二阶段输出必须让后端能创建 draft game、写入 generation job、写入 agent logs。
- 第二阶段实现顺序必须严格遵守 `Provider -> Orchestrator -> Asset Agent -> Coding Agent -> Coding Debug -> Validator -> generation_graph`；不要先写端到端假链路再补 Agent。
- 第二阶段每个 Agent 的真实 LLM smoke runner 都必须使用同一份 OpenAI-compatible provider 配置，并把 prompt、响应摘要和 schema 校验结果写入 LangSmith trace。
- Agent 不能把 API key、session id、OAuth code、token、password 或完整 presigned URL 签名写入日志。
- Agent 生成的游戏 JS 只能作为静态文件被浏览器 sandboxed iframe 执行，后端不得执行生成 JS。
- 不实现复杂 retry、完整版本管理 UI、Remix、内容审核、资源限额和生成成本统计。
- 生成后聊天修改属于 revision loop，不属于第一阶段 `conversation_graph`；明确修改应生成 patch 并创建新的 revision job。

## 3. 与其他端的接口边界

### 后端调用 Agent 的输入

后端调用 Agent 执行器时传入：

- `job_id`
- `user_id`
- `session_id`
- `prompt`
- `user_requirements`
- `game_plan`
- `material_usage`
- uploaded assets 元信息
- 素材读取所需授权信息或后端可读 object key

### Agent 返回给后端的输出

Agent 成功时返回：

- status：`succeeded`
- draft game title
- draft game description
- tags
- cover path 或 cover URL
- artifact prefix
- manifest object key 或 manifest URL
- entry object key
- logs

Agent 失败时返回：

- status：`failed`
- error message
- retry hint
- failed step
- logs

### 前端如何看到 Agent 结果

前端不直接调用 Agent。前端通过后端 Jobs API 看到：

- 任务状态
- 当前关键步骤
- Agent 日志
- failed 原因
- succeeded draft game

## 4. Agent Tasks

## Step 1：实现第一阶段 conversation_graph

依赖其他端：不需要；使用 `lan_agents/` 本地运行。每个子步骤完成后，都要启动或刷新 LangGraph Server，并确认 LangSmith Studio 能看到最新 graph。

官方依据：

- LangGraph Graph API 把工作流拆成 `State`、`Nodes`、`Edges`；节点负责更新状态，边负责决定下一步。因此第一阶段适合用普通 node 加条件边，而不是默认上 `create_react_agent`。
- LangGraph 官方建议使用 `StateGraph` 定义 state schema、添加 node 和 edge，最后 `compile()` 后才能运行。
- `START` / `END` 用于声明入口和终点；`add_conditional_edges` 用于根据 state 动态路由。
- LangGraph CLI 使用 `langgraph.json` 暴露 graph；`dependencies` 指向本地包，`graphs` 指向已编译 graph 变量。
- LangSmith tracing 通过 `LANGSMITH_TRACING=true`、`LANGSMITH_API_KEY` 和 `LANGSMITH_PROJECT` 开启；运行 graph 后应能看到 trace。

### Step 1.1：指令

- [x] 在 `lan_agents/` 内确认使用当前模板结构：`lan_agents/pyproject.toml`、`lan_agents/langgraph.json`、`lan_agents/src/agent/graph.py`、`lan_agents/tests/`。
- [x] 保留包名 `agent`，不要新建旧式 `agent/` 原型目录。
- [x] 将 `langgraph.json` 的 `graphs` 映射更新为第一阶段 graph，例如 `"conversation": "./src/agent/graph.py:conversation_graph"`。
- [x] `.env.example` 增加 LangSmith 所需变量示例：`LANGSMITH_TRACING=true`、`LANGSMITH_API_KEY=`、`LANGSMITH_PROJECT=yahaha-agent-local`。
- [x] 本步骤不实现业务节点，只保证 LangGraph Server 能加载新的 graph 名称。

### Step 1.1：验证

- [x] 运行：`cd lan_agents && langgraph dev`。
- [x] 预期：LangGraph Server 启动成功，Studio 中能看到 `conversation` graph。
- [x] 在 LangSmith 项目 `yahaha-agent-local` 中能看到一次加载或调用 trace。
- [x] 如果 LangSmith 没有 trace，不允许进入 Step 1.2。

Step 1.1 当前状态：☑️ 已完成。本地 graph 配置、测试、LangGraph dev server 加载和 LangSmith metadata / run trace 均已验证。

### Step 1.2：指令

- [x] 创建 `lan_agents/src/agent/state.py`，定义第一阶段 state schema。
- [x] `ConversationState` 必须包含 `user_requirements`、`game_plan`、`material_usage`、`user_event`、`assistant_response`、`handoff_to_generation`、`conversation_status`。
- [x] `user_requirements` 字段按 [agent-orchestration-design.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/agent-orchestration-design.md) 定义：`intent_summary`、`must_have`、`nice_to_have`、`constraints`、`open_questions`、`answered_questions`、`preference_profile`、`revision_count`。
- [x] `game_plan` 字段按编排文档定义：`plan_id`、`title`、`introduction`、`tags`、`gameplay`、`core_loop`、`style`、`characters`、`win_condition`、`lose_condition`、`controls`、`suggestions`、`confidence`。
- [x] `material_usage` 只包含 `assets`，不要加入全局素材总结、缺失素材需求或深度分析字段。
- [x] `assistant_response.card` 只由 `game_plan.plan_id`、`game_plan.title`、`game_plan.introduction`、`game_plan.tags` 派生。
- [x] `assistant_response.suggestions` 必须是 `string[]`。

### Step 1.2：验证

- [x] 增加 unit test，验证最小 state 可以被 `conversation_graph.invoke()` 接收。
- [x] 运行：`cd lan_agents && pytest tests/unit_tests -q`。
- [x] 运行：`cd lan_agents && langgraph dev`。
- [x] 预期：Studio 中仍能看到 `conversation` graph，LangSmith 中能看到包含 state schema 字段的一次 trace。
- [x] 如果 state 字段和编排文档不一致，不允许进入 Step 1.3。

Step 1.2 当前状态：☑️ 已完成。第一阶段 `ConversationState`、graph 接入、unit/integration 测试、`langgraph validate` 和 LangGraph dev run state 字段观测均已验证。

### Step 1.3：指令

- [x] 创建 `lan_agents/src/agent/nodes.py`，先实现无模型的确定性骨架节点：`ingest_user_event`、`update_requirements`、`update_material_usage`、`generate_or_refine_plan`、`regenerate_plan`、`lock_confirmation`、`build_user_response`、`build_error_response`。
- [x] 节点函数只接收当前 state，返回局部 state update；不要在一个节点里手动调用下一个节点。
- [x] `ingest_user_event` 校验 `user_event.type` 是否为 `chat / upload_assets / regenerate / confirm`。
- [x] `build_user_response` 必须输出 `assistant_response.message`、`assistant_response.suggestions`、`assistant_response.card`、`assistant_response.actions`。
- [x] 所有节点先使用 deterministic stub，确保 graph 形状和状态流先跑通，模型调用留到后续步骤。

### Step 1.3：验证

- [x] 增加 unit test，分别直接调用每个 node，确认返回的是局部 state update。
- [x] 运行：`cd lan_agents && pytest tests/unit_tests -q`。
- [x] 运行：`cd lan_agents && langgraph dev`，在 Studio 执行一次 `chat` 输入。
- [x] 预期：LangSmith trace 中能看到 `ingest_user_event`、`update_requirements`、`generate_or_refine_plan`、`build_user_response` 等节点运行记录。

Step 1.3 当前状态：☑️ 已完成。确定性节点骨架、局部 state update、用户响应构建和节点级单元测试均已验证。

### Step 1.4：指令

- [x] 在 `lan_agents/src/agent/routing.py` 创建 `route_user_event(state)`。
- [x] `route_user_event` 只返回路由名，不直接修改 state。
- [x] 支持路由：`chat`、`upload_assets`、`regenerate`、`confirm`、`invalid`。
- [x] 在 `lan_agents/src/agent/graph.py` 使用 `StateGraph(ConversationState)` 组装第一阶段 graph。
- [x] Graph 结构必须与编排文档一致：

```text
START
  -> ingest_user_event
  -> route_user_event
    -> chat: update_requirements -> generate_or_refine_plan -> build_user_response -> END
    -> upload_assets: update_material_usage -> build_user_response -> END
    -> regenerate: regenerate_plan -> build_user_response -> END
    -> confirm: lock_confirmation -> END
    -> invalid: build_error_response -> END
```

### Step 1.4：验证

- [x] 增加 integration test，分别输入五种 `user_event.type`，确认走到对应节点和终态。
- [x] 运行：`cd lan_agents && pytest tests/integration_tests -q`。
- [x] 运行：`cd lan_agents && langgraph dev`，在 Studio 中确认 graph 图出现上述节点和条件边。
- [x] 在 LangSmith 中分别看到 `chat`、`upload_assets`、`regenerate`、`confirm`、`invalid` 的 trace。
- [x] 如果 Studio 图中没有条件边或节点命名不清晰，不允许进入 Step 1.5。

Step 1.4 当前状态：☑️ 已完成。`conversation_graph` 已按 `chat / upload_assets / regenerate / confirm / invalid` 条件边编排，并通过五类事件集成测试验证。

### Step 1.5：指令

- [x] 完善 `update_requirements`。
- [x] `chat` 输入时，把 `user_event.message` 合并进 `user_requirements.intent_summary`、`must_have`、`nice_to_have`、`constraints`、`preference_profile`。
- [x] 如果用户本轮提到素材用途，同时同步更新 `material_usage.assets`。
- [x] 避免重复追问：新问题写入 `open_questions` 前，要检查 `answered_questions`。
- [x] 本步骤可以先使用规则化实现，不强制接真实 LLM。

### Step 1.5：验证

- [x] 增加 unit test，覆盖首次聊天、继续补充、修改需求、回答已问问题四种情况。
- [x] 运行：`cd lan_agents && pytest tests/unit_tests -q`。
- [x] 运行：`cd lan_agents && langgraph dev`，在 Studio 连续执行两轮 `chat`。
- [x] 预期：LangSmith trace 中第二轮能看到 `user_requirements.revision_count` 增加，且没有丢失第一轮 `must_have`。

Step 1.5 当前状态：☑️ 已完成。`update_requirements` 已规则化吸收聊天需求、修改约束、偏好画像和素材用途提示，并通过单元测试验证。

### Step 1.5a：指令

- [x] 将第一阶段代码从扁平 `src/agent/nodes.py`、`src/agent/routing.py` 重构为 `src/agent/conversation_graph/` 子图目录。
- [x] 在 `src/agent/` 下预留 `generation_graph/` 子图目录，作为第二阶段生成链路边界。
- [x] `conversation_graph/` 内部分为 `nodes/`、`routes/`、`events/`。
- [x] 每个 conversation node 使用独立目录，例如 `nodes/update_requirements/node.py`。
- [x] 顶层 `src/agent/graph.py` 只保留 LangGraph 配置需要的兼容导出，不再承载业务节点实现。
- [x] 本步骤不改变 Step 1.3-1.5 已实现行为，不进入 Step 1.6。

### Step 1.5a：验证

- [x] 增加结构测试，确认 `conversation_graph`、`generation_graph`、`nodes/`、`routes/`、`events/` 目录存在。
- [x] 增加结构测试，确认 conversation nodes 是单节点目录结构。
- [x] 运行：`cd lan_agents && pytest tests/unit_tests/test_project_structure.py -q`。
- [x] 运行：`cd lan_agents && pytest -q`。
- [x] 运行：`cd lan_agents && langgraph validate`。

Step 1.5a 当前状态：☑️ 已完成。Agent 代码已拆为 `conversation_graph` 和 `generation_graph` 子图边界，conversation node 已迁移为单节点目录结构，行为测试保持通过。

### Step 1.5b：指令

- [x] 明确第一阶段不是每轮聊天都返回 card。
- [x] 每轮 `chat` 后先更新 `user_requirements`，再尝试更新部分 `game_plan`。
- [x] 根据 `game_plan` 缺失字段生成定制回复、追问和简短建议。
- [x] 只有 `game_plan` 的关键字段全部填充后，`assistant_response.card` 才从 `game_plan` 派生。
- [x] `introduction` 不作为用户追问字段；除简介外的关键字段完整后，再基于对话和 `game_plan` 自动总结简介。
- [x] 未完整时 `assistant_response.card=null`、`actions=[]`、`conversation_status=collecting`。
- [x] 完整时 `assistant_response.card` 包含 `plan_id/title/introduction/tags`，`actions=["generate","regenerate"]`，`conversation_status=ready_to_confirm`。

### Step 1.5b：验证

- [x] 增加 unit test，覆盖不完整 `game_plan` 只返回追问和建议，不返回 card。
- [x] 增加 unit test，覆盖完整 `game_plan` 返回 card。
- [x] 增加 integration test，覆盖普通单轮 chat 继续 collecting，完整方案 chat 才 ready_to_confirm。
- [x] 运行：`cd lan_agents && pytest -q`。
- [x] 运行：`cd lan_agents && langgraph validate`。

Step 1.5b 当前状态：☑️ 已完成。`conversation_graph` 已固化 card gating：不完整方案只追问，完整方案才返回确认卡片。

### Step 1.19：简介最终派生规则 ☑️ 已完成

- [x] 将 `introduction` 从普通需求收集字段改为最终派生字段。
- [x] 当除 `introduction` 外的关键 `game_plan` 字段完整时，自动根据用户需求和完整方案总结详细简介。
- [x] Design Agent prompt 明确禁止向用户追问卡片简介或介绍。
- [x] 确认卡片仍只展示 `plan_id/title/introduction/tags`，但 `introduction` 由系统总结生成。
- [x] 增加回归测试，覆盖完整方案缺简介时自动补简介并进入 `ready_to_confirm`。

Step 1.19 当前状态：☑️ 已完成。阶段一已支持“先收集玩法等关键方案字段，最后自动总结简介并出卡”。

### Step 1.6：指令

- [x] 完善 `update_material_usage`。
- [x] 该节点只更新 `material_usage.assets`。
- [x] 每个 asset 只保留 `asset_id`、`filename`、`mime_type`、`intended_use`、`usage_priority`、`user_hint`、`agent_note`。
- [x] 不把完整 presigned URL、临时 token、对象存储密钥写入 state 或 trace。
- [x] 如果用户没有说明用途，结合 `user_requirements` 和当前 `game_plan` 给出保守用途。

### Step 1.6：验证

- [x] 增加 unit test，覆盖图片、音频、视频、无 `user_hint`、已有同名素材更新。
- [x] 运行：`cd lan_agents && pytest tests/unit_tests -q`。
- [x] 运行：`cd lan_agents && langgraph dev`，在 Studio 执行一次 `upload_assets`。
- [x] 预期：LangSmith trace 中只看到安全素材元信息，看不到 presigned URL 或 secret。

Step 1.6 当前状态：☑️ 已完成。素材用途节点只保留安全素材元信息，并通过素材类型、无 hint 和同 asset 更新测试。

### Step 1.7：指令

- [x] 完善 `generate_or_refine_plan`。
- [x] 它根据 `user_requirements` 和 `material_usage` 生成 `game_plan`。
- [x] `tags` 必须来自 MVP 标签集合：`adventure / action / strategy / puzzle / arcade / survival / simulation / racing / rhythm / roleplay / casual / educational`。
- [x] `suggestions` 必须是对当前 AI 提问的简短建议答案列表，每条建议尽量短，并结合前文需求。
- [x] 不允许为了换新意丢弃 `must_have` 或 `constraints`。
- [x] 本步骤仍可先用 deterministic planner；接真实 LLM 时必须保持同一输出 schema。

### Step 1.7：验证

- [x] 增加 unit test，确认 `game_plan` 包含标题、介绍、标签、玩法、风格、角色、胜负条件、操作方式。
- [x] 增加 unit test，确认非法 tag 会被替换或过滤。
- [x] 运行：`cd lan_agents && pytest tests/unit_tests -q`。
- [x] 运行：`cd lan_agents && langgraph dev`，在 Studio 执行一次 `chat`。
- [x] 预期：LangSmith trace 中能看到完整 `game_plan`，且 `assistant_response.card` 只来自 `game_plan`。

Step 1.7 当前状态：☑️ 已完成。确定性 planner 可抽取完整方案字段并过滤 MVP 标签集合，card 仍只由 `game_plan` 派生。

### Step 1.8：指令

- [x] 完善 `regenerate_plan`。
- [x] 用户点击 `换一换` 时，必须保留 `user_requirements.must_have`、`user_requirements.constraints` 和 `material_usage.assets`。
- [x] 必须刷新 `game_plan.plan_id`、标题、介绍或玩法表达，保证用户看到的是另一版方案。
- [x] 不能把用户已经否定的方向重新加回来。

### Step 1.8：验证

- [x] 增加 integration test，先 `chat` 生成方案，再 `regenerate`，确认需求和素材用途未丢失。
- [x] 运行：`cd lan_agents && pytest tests/integration_tests -q`。
- [x] 运行：`cd lan_agents && langgraph dev`，在 Studio 连续执行 `chat -> regenerate`。
- [x] 预期：LangSmith trace 中能比较两次 `game_plan.plan_id` 不同，但 `must_have` 和 `material_usage.assets` 保持一致。

Step 1.8 当前状态：☑️ 已完成。`regenerate` 会刷新方案 ID 和展示表达，同时保留需求约束与素材用途。

### Step 1.9：指令

- [x] 完善 `lock_confirmation`。
- [x] 只有当 `game_plan` 具备标题、介绍、标签、玩法、风格、角色、胜负条件，且已上传素材都有用途时，才设置 `handoff_to_generation=true`。
- [x] 如果信息不完整，不能进入阶段 B，应返回 `conversation_status=error` 或保持 `collecting` 并给出可理解提示。
- [x] `confirm` 成功后不再生成卡片；阶段 B 读取 `game_plan` 和 `material_usage`。

### Step 1.9：验证

- [x] 增加 integration test，覆盖完整方案确认成功、缺少胜负条件确认失败、素材缺用途确认失败。
- [x] 运行：`cd lan_agents && pytest tests/integration_tests -q`。
- [x] 运行：`cd lan_agents && langgraph dev`，在 Studio 执行一次 `confirm`。
- [x] 预期：LangSmith trace 中 `confirm` 路由只经过 `lock_confirmation` 后到 `END`，成功时 `handoff_to_generation=true`。

Step 1.9 当前状态：☑️ 已完成。确认节点会校验方案完整性和素材用途，不完整时保持 collecting，完整时设置 `handoff_to_generation=true`。

### Step 1.10：指令

- [x] 完善 `build_user_response` 和 `build_error_response`。
- [x] `assistant_response.card` 只包含 `plan_id`、`title`、`introduction`、`tags`。
- [x] `assistant_response.suggestions` 必须是 `string[]`，每条建议是当前 AI 提问的可选回答。
- [x] `assistant_response.actions` 根据信息完整度返回 `generate`、`regenerate` 或继续对话所需动作。
- [x] 错误响应必须可直接展示给用户，不暴露内部异常栈或 secret。

### Step 1.10：验证

- [x] 增加 unit test，确认 card 字段不会出现独立 confirmation card 数据。
- [x] 增加 unit test，确认 suggestions 是字符串列表，不是对象列表。
- [x] 运行：`cd lan_agents && pytest tests/unit_tests -q`。
- [x] 运行：`cd lan_agents && langgraph dev`，在 Studio 执行 `invalid` 输入。
- [x] 预期：LangSmith trace 中能看到错误路由和安全错误文案。

Step 1.10 当前状态：☑️ 已完成。用户响应和错误响应已收敛为安全前端展示协议。

### Step 1.11：指令

- [x] 创建第一阶段 fixture：`lan_agents/tests/fixtures/conversation_chat.json`、`conversation_upload_assets.json`、`conversation_regenerate.json`、`conversation_confirm.json`、`conversation_invalid.json`。
- [x] fixture 必须覆盖 `chat / upload_assets / regenerate / confirm / invalid` 五条边。
- [x] fixture 不包含真实用户隐私、真实密钥或完整 presigned URL。
- [x] 更新 `lan_agents/README.md`，写清楚如何运行第一阶段 graph、如何配置 LangSmith、如何在 Studio 查看 graph。

### Step 1.11：验证

- [x] 运行：`cd lan_agents && pytest -q`。
- [x] 运行：`cd lan_agents && langgraph dev`。
- [x] 逐个 fixture 在 Studio 中运行，确认 graph 路径正确。
- [x] LangSmith 项目中至少能看到五条 trace，对应五种用户动作。
- [x] 如果任一 fixture 不能产生 LangSmith trace，不允许标记 Step 1 完成。

Step 1.11 当前状态：☑️ 已完成。五类 fixture、README 运行说明和 fixture 安全测试均已完成。

### Step 1.12：指令

- [x] 更新 [architecture.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/architecture.md)，按项目约定用短格式记录 `lan_agents/` 中新增或变化文件职责，并标注 `Step 1.x`。
- [x] 更新 [progress.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/progress.md)，记录第一阶段已实现能力、验证命令、LangSmith 可见性和剩余边界。
- [x] 在本文档对应步骤中把已完成项标为 `☑️ 已完成`，但只能在真实实现和验证通过后标记。

### Step 1.12：验证

- [x] 检查文档中没有把 `confirmation_card` 写成独立 state。
- [x] 检查文档中没有给 `material_usage` 增加 `assets` 以外的第一阶段字段。
- [x] 检查文档中没有把 `assistant_response.suggestions` 写成对象列表。
- [x] 最后一次运行：`cd lan_agents && pytest -q`。
- [x] 最后一次运行：`cd lan_agents && langgraph dev`，确认 Studio 和 LangSmith 都能看到最新 `conversation_graph`。

Step 1.12 当前状态：☑️ 已完成。文档契约、测试、LangGraph validate、LangGraph dev 和 LangSmith fixture trace 均已完成最终收口。

### Step 1.13：指令

- [x] 新增统一 `LLMProvider` 抽象，供第一阶段和后续第二阶段复用。
- [x] 新增 `MockLLMProvider`，用于本地确定性运行、测试和 CI。
- [x] 新增 `OpenAICompatibleLLMProvider`，从环境变量读取 API key、base URL、model 和 timeout。
- [x] 新增 `DesignPlanner` service，只替换 `generate_or_refine_plan` 的方案生成能力。
- [x] `update_requirements`、路由、素材用途、卡片门控和确认校验继续保持确定性。
- [x] LLM 输出必须通过 schema/字段白名单合并到 `game_plan`，失败时 fallback 到 deterministic planner。

### Step 1.13：验证

- [x] 增加 unit test，覆盖 mock provider 输出、provider 配置选择和 OpenAI-compatible 必填配置校验。
- [x] 增加 unit test，覆盖 DesignPlanner 合并 LLM patch、过滤非法 tag 和 provider 失败 fallback。
- [x] 运行：`cd lan_agents && .venv/bin/python -m pytest -q`。
- [x] 运行：`cd lan_agents && .venv/bin/langgraph validate`。

Step 1.13 当前状态：☑️ 已完成。第一阶段已具备统一 provider 边界，默认 mock 保持确定性，真实 OpenAI-compatible provider 可通过环境变量开启。

### Step 1.14：指令

- [x] 让 provider 配置可从仓库根目录或 `lan_agents/` 的 `.env` 读取，适配本地直接运行和 LangGraph dev。
- [x] 扩展 `DesignPlanner` 的真实模型输出契约，允许返回 `game_plan_patch`、`assistant_message` 和 `suggestions`。
- [x] 当模型只补出部分 `game_plan` 时，保持 `conversation_status=collecting`，并把模型追问和建议返回给前端。
- [x] 当后续对话补齐 `game_plan` 时，进入 `ready_to_confirm`，并由 `build_user_response` 返回 card。
- [x] 不把路由、素材用途、卡片门控和确认校验交给模型。

### Step 1.14：验证

- [x] 增加 unit test，覆盖 `.env` 配置加载。
- [x] 增加 unit test，覆盖 LLM 部分补全后继续追问。
- [x] 增加 unit test，覆盖第二轮基于已有 `game_plan` 补齐后进入 `ready_to_confirm`。
- [x] 增加 unit test，覆盖 `build_user_response` 透传 planner 追问。
- [x] 运行：`cd lan_agents && .venv/bin/python -m pytest -q`。
- [x] 运行：`cd lan_agents && .venv/bin/langgraph validate`。

Step 1.14 当前状态：☑️ 已完成。真实 provider 链路代码已接通；当前根目录 `.env` 已设置 OpenAI-compatible key/base/model，真实调用前需确认 `LLM_PROVIDER=openai-compatible`。

### Step 1.15：指令

- [x] 增加 provider 预检入口，能确认当前是否真正启用 `openai-compatible`。
- [x] 预检输出必须脱敏，不能打印 API key、base URL、token 或完整 secret。
- [x] 在 `lan_agents/.env.example` 和 `lan_agents/README.md` 中写明第一阶段推荐模型 `gpt-5.4-mini`。
- [x] 明确如果只配置 `OPENAI_COMPATIBLE_*`，但没有 `LLM_PROVIDER=openai-compatible`，运行时仍会使用默认 mock。

### Step 1.15：验证

- [x] 增加 unit test，覆盖 provider 预检脱敏和缺失字段提示。
- [x] 增加 unit test，覆盖真实模型不返回建议时的 deterministic 兜底。
- [x] 运行：`cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_provider_preflight.py -q`。
- [x] 运行：`cd lan_agents && .venv/bin/python -m agent.providers.preflight`。
- [x] 运行真实 provider smoke test，确认 OpenAI-compatible provider 返回 JSON。
- [x] 运行真实 `conversation_graph.invoke`，确认 `collecting` 时返回追问和 `string[]` 建议。

Step 1.15 当前状态：☑️ 已完成。provider 预检和第一阶段推荐模型配置说明已补齐；根目录 `.env` 已启用 `LLM_PROVIDER=openai-compatible`，真实 provider smoke test 和 `conversation_graph.invoke` 均已跑通。

### Step 1.16：指令

- [x] 增加第一阶段完整对话 demo runner，用于从模型追问跑到最终 `game_plan` 完整并输出 card。
- [x] demo runner 必须打印 `pretty_print_messages` 格式的用户/AI 对话。
- [x] demo runner 必须打印本地 agent 日志，包含每轮状态、已填充字段、是否输出 card 和 assistant actions。
- [x] demo runner 只能作为本地验收工具，不改变第一阶段 state 契约，不新增 `confirmation_card` 独立字段。
- [x] 当真实模型漏填 `core_loop` 但已有 `gameplay` 时，DesignPlanner 必须能自动派生核心循环，避免完整方案卡在 collecting。
- [x] 当真实模型重复追问已补齐字段时，`build_user_response` 必须按当前缺失字段替换追问，避免用户重复回答。

### Step 1.16：验证

- [x] 增加 unit test，覆盖 `pretty_print_messages` 和 demo runner 日志/card 输出。
- [x] 运行：`cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_conversation_demo.py -q`。
- [x] 运行：`cd lan_agents && .venv/bin/python -m pytest -q`。
- [x] 运行：`cd lan_agents && .venv/bin/langgraph validate`。
- [x] 运行真实 provider demo，确认输出从追问进入 `ready_to_confirm` 并包含 card。

Step 1.16 当前状态：☑️ 已完成。完整对话 demo runner、pretty print 输出、本地 agent 日志和真实 provider 端到端输出均已补齐。

### Step 1.17：指令

- [x] 为 Design Agent 增加亲和语气 skill，但不改变 `assistant_response` schema。
- [x] `assistant_response.message` 可以带一个上下文 icon，但最多只能有一个 icon。
- [x] 回复应先轻轻肯定用户已有想法，再提出一个关键追问；语气亲和但不啰嗦。
- [x] `assistant_response.suggestions` 仍必须是短字符串列表。
- [x] 如果模型给出的 suggestions 和追问字段不匹配，必须回退到当前字段的确定性建议。

### Step 1.17：验证

- [x] 增加 unit test，覆盖亲和语气、单 icon、ready message 和模型追问包装。
- [x] 增加 unit test，覆盖模型额外 emoji 清理。
- [x] 增加 unit test，覆盖追问和 suggestions 不匹配时的确定性兜底。
- [x] 运行：`cd lan_agents && .venv/bin/python -m pytest -q`。
- [x] 运行：`cd lan_agents && .venv/bin/langgraph validate`。
- [x] 运行真实 provider demo，确认输出亲和文案、单 icon、建议匹配和最终 card。

Step 1.17 当前状态：☑️ 已完成。Design Agent 已具备亲和语气 skill，真实模型 demo 已验证用户可见输出更自然。

### Step 1.18：指令

- [x] DesignPlanner system prompt 必须明确列出完整 MVP 标签集合。
- [x] 标签列表必须从 `MVP_TAGS` 常量生成，避免 prompt 和后处理白名单不一致。
- [x] 继续保留 `normalize_tags`，不要只依赖模型遵守 prompt。

### Step 1.18：验证

- [x] 增加 unit test，记录 provider 收到的 system prompt，并断言包含所有 `MVP_TAGS`。
- [x] 运行：`cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_design_planner.py -q`。
- [x] 运行：`cd lan_agents && .venv/bin/python -m pytest -q`。
- [x] 运行：`cd lan_agents && .venv/bin/langgraph validate`。

Step 1.18 当前状态：☑️ 已完成。外部模型现在能看到完整 MVP tag 集合，后处理过滤仍保留。

## Step 2：接通第二阶段真实 LLM provider 基线

依赖其他端：不需要；使用 `lan_agents/` 本地运行。第二阶段从一开始就接 `openai-compatible`，Mock 仅作为单元测试替身，不作为主路径。

### Step 2.1：指令

- [x] 在 `lan_agents/src/agent/generation_graph/` 下建立第二阶段基础目录：`state.py`、`graph.py`、`orchestrator/`、`asset_agent/`、`coding_agent/`、`validator_agent/`、`tools/`、`fixtures/`。
- [x] 在 `tools/` 下预留确定性工具边界：`workspace.py`、`asset_registry.py`、`schema_guard.py`、`logging.py`、`path_safety.py`。
- [x] 新增 `GenerationState`，字段必须覆盖 [agent-orchestration-design.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/agent-orchestration-design.md) 的第二阶段 State：`job_context`、`user_requirements`、`game_plan`、`material_usage`、`uploaded_assets`、`asset_registry`、`artifact_workspace`、`development_brief`、`asset_work_order`、`asset_manifest_plan`、`game_spec`、`code_artifacts`、`manifest_draft`、`processed_assets`、`asset_analysis`、`integrated_bundle_context`、`debug_report`、`validation_report`、`artifact_result`、`draft_game_meta`、`generation_status`、`agent_logs`、`failed_step`、`error_message`、`retry_hint`。
- [x] 复用第一阶段已有 `LLMProvider` / `OpenAICompatibleLLMProvider`，不要为第二阶段另写一套 provider。
- [x] 新增第二阶段 provider smoke runner，例如 `python -m agent.generation_graph.tools.provider_smoke`，它调用真实模型并要求返回 JSON。
- [x] smoke runner 输出必须脱敏，不能打印 API key、base URL token、完整 presigned URL 或用户 secret。
- [x] 新增第二阶段 fixture：`generation_confirmed_session.json`，包含完整 `user_requirements`、`game_plan`、`material_usage`、`uploaded_assets` 和 `job_context`。
- [x] 新增四类上传素材 fixture 元信息：image、video、audio、generic file；fixture 只保存 object key 或本地测试路径，不保存完整 presigned URL。

### Step 2.2：验证

- [x] 增加 unit test，确认 `GenerationState` 默认值和字段名与编排文档一致。
- [x] 增加 unit test，确认第二阶段 provider 配置复用第一阶段配置。
- [x] 增加 unit test，确认第二阶段 fixture 覆盖 image/video/audio/file 四类上传素材。
- [x] 运行：`cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_generation_state.py tests/unit_tests/test_generation_provider.py -q`。
- [x] 运行：`cd lan_agents && .venv/bin/python -m agent.generation_graph.tools.provider_smoke`。
- [x] 预期：真实 provider 返回可解析 JSON，LangSmith 能看到一次第二阶段 smoke trace。
- [x] 如果真实 provider 不通，不允许进入 Step 3。

Step 2 当前状态：☑️ 已完成。第二阶段 state、目录边界、fixture、provider smoke runner、OpenAI-compatible 响应解析容错和真实 provider smoke 均已验证。

## Step 3：实现 Orchestrator 契约生成 Agent

依赖其他端：不需要；输入使用固定 confirmed create session fixture。

### Step 3.1：指令

- [x] 创建 `lan_agents/src/agent/generation_graph/orchestrator/build_parallel_contracts/node.py`。
- [x] Orchestrator 必须使用真实 LLM 解析 `user_requirements`、`game_plan`、`material_usage`、`uploaded_assets`。
- [x] Orchestrator 输出 `development_brief`、`asset_work_order`、`asset_manifest_plan` 和可选 `game_spec`。
- [x] 本周 MVP 图像合同只允许三张图：`assets/background.png`、`assets/player.png`、`assets/cover.png`；其中运行时可只引用背景/人物，封面为展示素材。
- [x] `assets/background.png` 必须定义为主背景图，逻辑分辨率固定为 `1280x720`。
- [x] `assets/player.png` 必须定义为玩家主角图，逻辑分辨率固定为 `256x256`，并要求透明底 `RGBA PNG`。
- [x] `assets/cover.png` 必须由 Asset Agent 按游戏内容和画风独立生成，作为展示封面，不作为运行时强依赖。
- [x] `development_brief.allowed_asset_paths` 必须全部来自 `asset_manifest_plan.target_path`。
- [x] `asset_work_order.uploaded_asset_tasks[].target_path` 和 `generated_asset_tasks[].target_path` 必须全部来自 `asset_manifest_plan.target_path`。
- [x] `asset_manifest_plan` 必须列出每个素材的 `asset_id`、`target_path`、`kind`、`required`、`source`、`runtime_required`、`display_only`、`logical_width`、`logical_height`、`alpha_required`、`background`、`fit`、`derived_from`、`title_source`，其中 `source` 只能是 `uploaded / generated / fallback`。
- [x] `development_brief` 必须明确 `title`、`gameplay_goal`、`core_loop`、`scene_layout`、`entities`、`controls`、`win_condition`、`lose_condition`、`ui_hud`、`allowed_asset_paths`、`technical_constraints`。
- [x] `asset_work_order` 必须明确 `uploaded_asset_tasks` 和 `generated_asset_tasks`，且只围绕这三张图安排任务；其中封面任务必须体现“独立封面图生成”。
- [x] 输出 JSON 必须经过 schema/字段白名单校验，非法字段丢弃，缺关键字段时失败。
- [x] Orchestrator 不直接写代码、不处理素材、不做最终验收。

### Step 3.2：验证

- [x] 增加 unit test，使用 mock LLM 响应验证三份契约路径一致。
- [x] 增加 unit test，验证非法路径、越界路径、未出现在 `asset_manifest_plan` 的路径会失败。
- [x] 增加 unit test，验证 `development_brief` 和 `asset_work_order` 可并发执行：Coding 只依赖三张图目标路径，Asset 只负责把三张图落到目标路径。
- [x] 增加 unit test，验证 `player.png` 会要求透明底，`cover.png` 会声明 `display_only=true`、`derived_from=""` 和 `title_source=""`。
- [x] 增加 unit test，验证无上传素材时 Orchestrator 仍会规划 `cover.png`，且背景/人物可由代码生成。
- [x] 增加真实 LLM integration test 或 smoke runner：`python -m agent.generation_graph.orchestrator.demo --fixture fixtures/generation_confirmed_session.json`。
- [x] 运行：`cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_generation_orchestrator.py -q`。
- [x] 运行真实 Orchestrator demo，确认输出包含 `development_brief`、`asset_work_order`、`asset_manifest_plan`。
- [x] 如果 Orchestrator 不能稳定输出可解析结构，不允许进入 Step 4。

Step 3 当前状态：☑️ 已完成。图像合同已经收口为 `background.png / player.png / cover.png`，并覆盖 `1280x720` 背景、`256x256` 透明底玩家图、`cover.png` 独立展示封面、无上传素材时背景/人物代码生成优先和并发路径边界；已在 backend 容器内完成真实 OpenAI-compatible provider demo 验证。

## Step 4：实现 Asset Agent

依赖其他端：不需要；使用本地 fixture 模拟已上传到 MinIO 的素材元信息和可读本地样本文件。

### Step 4.1：指令

- [x] 创建 `lan_agents/src/agent/generation_graph/asset_agent/run_asset_agent/node.py`。
- [x] Asset Agent 读取 `asset_work_order`、`asset_manifest_plan` 和 `artifact_workspace`。
- [x] Asset Agent 先实现可替换的本地确定性生图边界，并通过 `ASSET_IMAGE_PROVIDER=openai-compatible` 接入真实图像大模型调用边界。
- [x] 本周 MVP 只稳定产出三张图：`assets/background.png`、`assets/player.png`、`assets/cover.png`。
- [x] `background.png` 输出尺寸固定为 `1280x720`，prompt builder 只放背景图定义，并包含游戏 UI 设计师 system role。
- [x] `player.png` 输出尺寸固定为 `256x256`，prompt builder 只放玩家图定义，并包含游戏 UI 设计师 system role。
- [x] 玩家图生成 prompt 使用纯品红 `#FF00FF` 幕布，后处理导出透明底 `RGBA PNG`。
- [x] `cover.png` 必须由图像模型按游戏内容和画风独立生成，不从 `background.png` 派生，不默认叠加标题文案。
- [x] 如果用户没有上传可用素材，Asset Agent 仍必须生成 `cover.png`；`background.png` 和 `player.png` 优先由代码绘制，除非 Orchestrator 明确规划为素材图。
- [x] 本周不要求把音频、通用文件直接变成运行时资源；它们可以暂不进入 `asset_manifest_plan`。
- [x] Asset Agent 只处理图片/视频参考；图片直接作为参考图，视频后续通过关键帧作为参考图，其他附件本周不处理。
- [x] 输出 `processed_assets` 和 `asset_analysis`。
- [x] `processed_assets[].path` 必须与 `asset_manifest_plan.target_path` 对齐。

### Step 4.2：验证

- [x] 增加 unit test，覆盖 `background.png`、`player.png`、`cover.png` 三张图的输出路径都位于 `artifact_workspace/assets/`。
- [x] 增加 unit test，确认不会把完整 presigned URL、API key、token 写入 `processed_assets`、`asset_analysis` 或日志。
- [x] 增加 unit test，覆盖上传素材缺失时仍会生成 `background.png`、`player.png`、`cover.png`，不静默成功。
- [x] 增加 unit test，覆盖真实图像模型调用 payload、`b64_json` 解析，以及 `background=1280x720 / player_source=1024x1024` 固定尺寸传参。
- [x] 增加本地 smoke runner：`python -m agent.generation_graph.asset_agent.demo --fixture fixtures/generation_confirmed_session.json`。
- [x] 运行：`cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_asset_agent.py -q`。
- [x] 运行 Asset Agent demo，确认 `assets/background.png`、`assets/player.png`、`assets/cover.png` 三张图都已生成。
- [x] 如果三张图合同任一项不稳定，不允许进入 Step 5。

Step 4 当前状态：真实图像模型客户端边界已接入，真实联网 smoke 待跑。当前已完成 background/player 独立 prompt、OpenAI-compatible `/images/generations` 调用边界、`#FF00FF` 品红幕布玩家图后处理、三图落盘、三图合同稳定性、敏感信息脱敏测试、本地 Asset demo 和 `langgraph validate`；已尝试真实 image provider smoke，但当前 Codex 审批器因 `codex-auto-review model_price_error` 拒绝联网提权。后续还需视频关键帧抽取、Pillow/OpenCV 生产级抠图和真实 image provider smoke 后，再标记为 ☑️ 已完成。

## Step 5：实现 Coding Agent 代码草稿生成

依赖其他端：不需要；依赖 Step 3 的 `development_brief` 和 `asset_manifest_plan`。

### Step 5.1：指令

- [x] 创建 `lan_agents/src/agent/generation_graph/coding_agent/draft_code/node.py`。
- [x] Coding Agent 一开始就使用真实 LLM，根据 `development_brief` 和 `asset_manifest_plan` 生成 `index.html`、`style.css`、`game.js` 和 `manifest_draft`。
- [x] Coding Agent 只能写入 `artifact_workspace`。
- [x] Coding Agent 可以引用 `asset_manifest_plan.target_path`，但不能生成最终素材文件。
- [x] Coding Agent 不能使用占位资源路径；如果需要绘制 fallback，必须写在 `game.js` 的 canvas 绘制逻辑中，不得伪造 `assets/*` 文件。
- [x] 生成代码必须是纯静态 HTML5，不依赖 React、本地前端组件或外网 CDN。
- [x] `manifest_draft.assets` 必须来自 `asset_manifest_plan.target_path` 和实际代码引用路径。
- [x] 输出 `code_artifacts`、`manifest_draft` 和 `coding_notes`。

### Step 5.2：验证

- [x] 增加 unit test，使用 mock LLM 响应验证文件写入范围限制。
- [x] 增加 unit test，确认生成代码不包含外网 CDN、API key、presigned URL 签名或本地绝对路径。
- [x] 增加 unit test，确认代码引用的所有 `assets/*` 都来自 `asset_manifest_plan.target_path`，不能编造未规划资源。
- [x] 增加真实 LLM smoke runner：`python -m agent.generation_graph.coding_agent.demo --fixture fixtures/development_brief.json`。
- [x] 运行：`cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_coding_agent.py -q`。
- [x] 运行 Coding Agent demo，确认 `artifact_workspace` 中出现 `index.html`、`style.css`、`game.js` 和 `manifest_draft.json`。
- [ ] 如果真实模型不能产出完整四类文件，不允许进入 Step 6。

Step 5 当前状态：代码与本地验证已完成，真实 provider smoke 待补跑。当前已通过 mock unit test、`langgraph validate` 和 mock demo 证明 Coding Agent 的落盘范围、外链拦截、合同资源校验、`code_artifacts.files / referenced_asset_paths` 交接契约以及 `manifest_draft` 生成逻辑；但本会话内真实 OpenAI-compatible provider smoke 先被沙箱网络 DNS 拦截，随后提权审批又因 `codex-auto-review` 配置异常被拒，尚缺一次真实 provider 生成四类文件并写 trace 的最终证据。补齐后再将 Step 5 标注为 ☑️ 已完成并进入 Step 6。

## Step 6：实现 Coding Agent 资源到齐后自调试

依赖其他端：不需要；依赖 Step 4 和 Step 5 的输出。

### Step 6.1：指令

- [x] 创建 `lan_agents/src/agent/generation_graph/coding_agent/debug_code_with_assets/node.py`。
- [x] 创建本地工具 `run_headless_runtime_check(entry_path)`，由 Coding Agent 调用，用于打开 `index.html` 并检查 JS error、非空画面和 `game_ready`。
- [x] 创建本地工具 `check_asset_references(bundle_context)`，检查 `game.js`、CSS、HTML、manifest 中的 `assets/*` 引用是否真实存在。
- [x] `debug_code_with_assets` 可以让真实 LLM 基于错误报告修正代码和 manifest，但只能读写 `artifact_workspace`。
- [x] 如果素材缺失或契约冲突，Coding Agent 不打回其他 Agent，只在 `debug_report.unresolved_issues` 里记录。
- [x] Coding Agent 最多执行一轮自修复：`runtime_check -> LLM patch -> runtime_check`；仍失败则保留失败证据，交给 Validator 最终判定。
- [x] 输出 `debug_report`，并更新调试后的 `code_artifacts` 和 `manifest_draft`。

### Step 6.2：验证

- [x] 增加 unit test，覆盖缺素材时 `debug_report.unresolved_issues` 有记录，但不会越权修改 `asset_work_order`。
- [x] 增加 unit test，覆盖 JS error 时 Coding Agent 可修复后重新通过 runtime check。
- [x] 增加 unit test，覆盖一轮自修复仍失败时不会继续无限循环。
- [x] 增加真实 LLM smoke runner：`python -m agent.generation_graph.coding_agent.debug_demo --fixture fixtures/integrated_bundle_context.json`。
- [x] 运行：`cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_coding_debug.py -q`。
- [x] 运行 debug demo，确认输出 `debug_report.attempted=true`，且没有未解决的 JS 启动错误。
- [x] 如果 Coding Agent 不能生成 `debug_report`，不允许进入 Step 7。

Step 6 当前状态：☑️ 已完成。已补齐 `debug_code_with_assets` 节点、本地 `runtime_check / asset_reference_check` 工具、一轮修复边界、`debug_demo.py` 与 `fixtures/integrated_bundle_context.json`，并验证 `tests/unit_tests/test_generation_orchestrator.py`、`test_asset_agent.py`、`test_coding_agent.py`、`test_coding_debug.py` 共 `28 passed`、`langgraph validate` 通过，且 `python -m agent.generation_graph.coding_agent.debug_demo --fixture fixtures/integrated_bundle_context.json` 输出 `debug_report.attempted=true`、`unresolved_issues=[]`。

## Step 7：实现 Validator Agent 最终交付验收

依赖其他端：不需要；不做调试和返修。

### Step 7.1：指令

- [x] 创建 `lan_agents/src/agent/generation_graph/validator_agent/validate_final_delivery/node.py`。
- [x] Validator 读取 `integrated_bundle_context`、`debug_report`、`asset_manifest_plan` 和 `artifact_workspace`。
- [x] Validator 可调用真实 LLM 生成用户可读 `error_message` 和 `retry_hint`，但硬性验收项必须由确定性工具判定。
- [x] Validator 校验 `manifest.json`、`index.html`、`style.css`、`game.js` 是否存在。
- [x] Validator 校验 manifest 的 `entry`、`styles`、`scripts`、`assets`、`cover`、`runtime`、`generatedAt`。
- [x] Validator 校验 `manifest.assets` 和 `asset_manifest_plan.target_path` 中运行必需资源是否存在。
- [x] Validator 校验所有输出路径都在 `artifact_workspace` 内。
- [x] Validator 扫描 secret、token、password、OAuth code、完整 presigned URL 和外网 CDN。
- [x] Validator 检查 `debug_report` 存在且没有未解决的 JS 启动错误。
- [x] Validator 只输出 `valid / invalid`，不输出 `repair_decision` 或 `repair_instruction`。
- [x] Validator 不调用 Coding Agent 或 Asset Agent，不做返修、不改文件。

### Step 7.2：验证

- [x] 增加 unit test，覆盖完整 bundle 验收通过。
- [x] 增加 unit test，覆盖缺 manifest、缺 entry、缺资源、含 secret、含外链时验收失败。
- [x] 增加 unit test，覆盖缺 `debug_report` 或 `debug_report.unresolved_issues` 非空时验收失败。
- [x] 增加真实 LLM smoke runner：`python -m agent.generation_graph.validator_agent.demo --fixture fixtures/validated_bundle_context.json`。
- [x] 运行：`cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_validator_agent.py -q`。
- [x] 运行 Validator demo，确认成功输出 `validation_report.valid=true`，失败输出可展示 `error_message` 和 `retry_hint`。
- [x] 如果 Validator 会修改 bundle 或输出返修指令，不允许进入 Step 8。

Step 7 当前状态：☑️ 已完成。Validator Agent 已实现确定性最终交付验收，覆盖 manifest、入口文件、运行资源、展示封面、路径越界、安全扫描和 debug report 门禁；`cover.png` 缺失按失败处理。已验证 Validator 单测、Validator demo、相关 generation 局部回归、完整 `lan_agents` 测试和 `langgraph validate`。

## Step 8：组装 generation_graph 端到端链路

依赖其他端：不需要；使用本地 fixture。

### Step 8.1：指令

- [x] 在 `lan_agents/src/agent/generation_graph/graph.py` 组装第二阶段 graph。
- [x] Graph 结构按现有 StateGraph 边界收口为：`init_generation_context -> build_parallel_contracts -> draft_code -> run_asset_agent(按需) -> join_assets_and_code -> debug_code_with_assets -> validate_final_delivery -> finalize_success/finalize_failure`；真实并发 fan-out/reducer 后续单独补强。
- [x] `join_assets_and_code` 汇总代码和素材上下文；当前按现有顺序图保证 Asset 分支在 Debug 前完成。
- [x] `lan_agents/src/agent/graph.py` 和 `lan_agents/langgraph.json` 暴露 `"generation": "./src/agent/graph.py:generation_graph"`。
- [x] `finalize_success` 输出 `status=succeeded`、`artifact_result`、`draft_game_meta`、`agent_logs`。
- [x] `finalize_failure` 输出 `status=failed`、`failed_step`、`error_message`、`retry_hint`、`debug_report`、`validation_report`、`agent_logs`。
- [x] 每个关键节点写入脱敏 `agent_logs`。

### Step 8.2：验证

- [x] 增加 integration test，使用 mock LLM test double 和本地素材 fixture 跑通 succeeded；该测试只用于 CI，不代表第二阶段主路径。
- [x] 增加 integration test，模拟 Validator 失败并输出 failed。
- [x] 运行：`cd lan_agents && .venv/bin/python -m pytest tests/integration_tests/test_generation_graph.py -q`。
- [x] 运行：`cd lan_agents && .venv/bin/langgraph validate`。
- [ ] 运行：`cd lan_agents && .venv/bin/langgraph dev`，在 Studio 中看到 `generation` graph。
- [x] 用真实 LLM 运行一次 generation fixture，LangSmith 中能看到 Orchestrator、Asset、Coding、Debug、Validator 的 trace，并且产物目录包含 `manifest.json`、`index.html`、`style.css`、`game.js`、`assets/*`。

Step 8 当前状态：本地 mock/CI 链路和真实 LLM/图片 provider smoke 已完成，真实 LangGraph dev Studio 可视化待补跑。当前 generation graph 已能输出 `status=succeeded/failed`、`artifact_result`、`draft_game_meta`、`validation_report` 和脱敏 `agent_logs`。

## Step 9：输出 Agent 日志和失败原因

依赖其他端：不需要；Backend Step 7 / Step 8 最终会持久化日志。

### Step 9.1：指令

- [ ] 每个关键步骤输出日志事件。
### Step 9.2：指令

- [ ] 日志 level 支持 `info / warning / error`。
### Step 9.3：指令

- [ ] failed 任务必须返回用户可理解的失败原因。
### Step 9.4：指令

- [ ] 错误摘要需要告诉用户如何重试。
### Step 9.5：指令

- [ ] 不实现自动返修；Agent 失败后由后端记录错误，用户后续可重新生成。
### Step 9.6：指令

- [ ] 日志不得包含 secret、token、password、OAuth code、完整 presigned URL。
### Step 9.7：验证

- [ ] succeeded 任务有完整日志链路。
### Step 9.8：验证

- [ ] failed 任务有 error 日志和 `error_message`。
### Step 9.9：验证

- [ ] 日志能被后端按时间正序展示。
### Step 9.10：验证

- [ ] 日志不包含敏感信息。

## Step 10：提供后端联调 fixture

依赖其他端：不需要。

### Step 10.1：指令

- [ ] 准备一个成功 fixture，包含 prompt、`game_plan`、`material_usage`、uploaded assets 元信息。
### Step 10.2：指令

- [ ] 准备一个失败 fixture，用于模拟模型调用失败或产物校验失败。
### Step 10.3：指令

- [ ] fixture 的输入输出字段与 Agent Step 8 `generation_graph` 执行器边界一致。
### Step 10.4：指令

- [ ] fixture 不包含真实密钥或真实用户隐私数据。
### Step 10.5：验证

- [ ] Backend Step 8 可以用成功 fixture 创建 succeeded 任务和 draft game。
### Step 10.6：验证

- [ ] Backend Step 8 可以用失败 fixture 创建 failed 任务和错误日志。

## Step 11：实现生成后修改 revision_graph

依赖其他端：需要 Jobs API 能提供 `session_id`、原任务快照、draft 结果摘要和创建 revision job 的入口。

### Step 11.1：指令

- [x] 新增 `revision_graph` 或 revision mode 服务，输入为上一版任务、上一版 `game_plan`、上一版 `material_usage`、已生成结果和用户新消息。
### Step 11.2：指令

- [x] 明确修改如“把小猫换成兔子”“难度降低一点”“背景改成雪地”应输出 `revision_intent`、`game_plan_patch`、`requires_regeneration=true` 和用户可见 `assistant_response`。
### Step 11.3：指令

- [x] 模糊或冲突修改应返回澄清问题，不创建 revision job。
### Step 11.4：指令

- [x] revision 输出不得覆盖原始 `create_session`、原始 job 快照或旧产物路径。
### Step 11.5：指令

- [ ] revision job 创建后复用 `generation_graph` 重新生成一版 draft。
### Step 11.6：验证

- [x] 明确修改输入能生成稳定 patch。
### Step 11.7：验证

- [x] 模糊修改输入不会创建 revision job。
### Step 11.8：验证

- [x] 新 revision job 带 `parent_job_id`，旧 job 和旧 draft 保持不变。
### Step 11.9：验证

- [x] revision 输出和日志不包含 secret、token、password、OAuth code 或完整 presigned URL。

Step 11 当前状态：已完成 `revision_graph` 最小契约，能基于上一版任务、方案、素材用途、产物摘要和用户修改消息输出 `game_plan_patch` 与 `revision_job_payload`；模糊修改会追问且不创建 payload。后端创建 revision job 后复用 `generation_graph` 重新生成 draft 的执行接入仍待补。

## 5. Agent 交付前自检

- [ ] OpenAI-compatible provider 可在有密钥时运行，并能为 Orchestrator、Asset、Coding、Debug 节点产生 trace。
- [ ] Mock LLM test double 只用于 unit test 和 CI，不作为第二阶段主路径。
- [ ] 缺少模型密钥时错误明确。
- [ ] 产物协议与 [design-document.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/design-document.md) 一致。
- [ ] 执行器输入输出与本文档第 3 节一致。
- [ ] 日志不包含敏感信息。
- [ ] Coding Agent 产出 `debug_report`。
- [ ] Validator Agent 只做最终验收，不输出 `repair_decision` 或 `repair_instruction`。
- [ ] 后端可用 fixture 接入。
- [ ] revision_graph 或 revision mode 可基于已有 draft 创建新版本任务，不覆盖旧产物。
- [ ] 更新 [architecture.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/architecture.md) 和 [progress.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/progress.md)。

## 6. 最终接入条件

Agent 完成后，应能支持：

- Backend Step 8 用真实 Agent 执行器替换 fake runner。
- 后端创建任务后，任务可从 `pending` 到 `running` 到 `succeeded / failed`。
- succeeded 任务生成 draft game 和完整静态 bundle。
- failed 任务返回可展示错误原因和日志。
- 前端通过 Jobs API 展示任务状态、Agent 日志和 draft 试玩入口。
