# Agent 实施计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 独立完成生成任务执行器、Mock provider、OpenAI-compatible provider 适配、静态游戏产物协议、日志输出和失败原因边界，使后端可通过 BackgroundTasks 调用并生成 draft 游戏。

**架构：** Agent 不直接服务前端，只通过后端调用。后端传入 job、user、prompt、最终确认卡片和素材信息，Agent 返回标准化结果、日志事件、artifact prefix、manifest 路径和错误摘要。Agent 内部 LangGraph 节点、角色拆分和复杂 retry 策略后续再定，本计划只固定可接入的执行器边界。

**技术栈：** LangGraph、OpenAI-compatible API、Mock provider、MinIO 产物路径、静态 HTML5 bundle。

---

## 1. 必读上下文

Agent 开发者单独拿到本文档时，必须先阅读：

- [design-document.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/design-document.md)：产物协议、任务状态、Agent 日志、安全边界。
- [api-contract.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/api-contract.md)：Jobs API、confirmation 字段、任务日志字段。
- [tech-stack.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/tech-stack.md)：模型服务、Mock provider 和 LangGraph 边界。
- [architecture.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/architecture.md)：目录边界和文件职责。
- [progress.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/progress.md)：已完成步骤和当前缺口。

已确认边界：

- Agent 框架使用 LangGraph，但内部节点角色暂不在本计划定死。
- 模型服务主路径使用真实 OpenAI-compatible API。
- Mock provider 仅用于本地兜底和 CI。
- 异步任务由后端 FastAPI BackgroundTasks 启动，不引入 Celery。
- 产物必须是静态 Web bundle：`manifest.json`、`index.html`、`style.css`、`game.js`、`assets/*`。

## 2. Agent 独立运行原则

- Agent 不能等待前端完成，因为前端不直接调用 Agent。
- Agent 可以在后端真实接入前，用固定输入文件或测试 fixture 独立运行。
- Agent 输出必须让后端能创建 draft game、写入 generation job、写入 agent logs。
- Agent 不能把 API key、session id、OAuth code、token、password 或完整 presigned URL 签名写入日志。
- Agent 生成的游戏 JS 只能作为静态文件被浏览器 sandboxed iframe 执行，后端不得执行生成 JS。
- 不实现复杂 retry、版本管理、Remix、内容审核、资源限额和生成成本统计。

## 3. 与其他端的接口边界

### 后端调用 Agent 的输入

后端调用 Agent 执行器时传入：

- `job_id`
- `user_id`
- `prompt`
- `confirmation.title`
- `confirmation.short_description`
- `confirmation.game_type`
- `confirmation.core_gameplay`
- `confirmation.win_lose_condition`
- `confirmation.controls`
- `confirmation.assets_used`
- `confirmation.tags`
- `confirmation.cover_suggestion`
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

## Step 1：定义 Agent 执行器稳定边界

依赖其他端：不需要；Backend Step 8 最终会接入此边界。

### Step 1.1：指令

- [ ] 定义可被 FastAPI BackgroundTasks 调用的生成执行入口。
### Step 1.2：指令

- [ ] 输入包含 job id、user id、prompt、confirmation、uploaded assets 元信息和素材读取信息。
### Step 1.3：指令

- [ ] 输出包含任务状态、draft game 元信息、artifact prefix、manifest 路径、日志事件和错误摘要。
### Step 1.4：指令

- [ ] 不要在本步骤决定 LangGraph 内部节点角色。
### Step 1.5：指令

- [ ] 日志事件字段至少包含 step、level、message、created_at。
### Step 1.6：指令

- [ ] 不暴露模型密钥、session id 或完整 presigned URL 签名到日志。
### Step 1.7：验证

- [ ] 可以用固定输入调用执行入口。
### Step 1.8：验证

- [ ] 成功输出包含创建 draft game 所需字段。
### Step 1.9：验证

- [ ] 失败输出包含可展示给用户的错误摘要。
### Step 1.10：验证

- [ ] 日志事件格式能被后端 `agent_logs` 保存。

## Step 2：实现 Mock provider 生成链路

依赖其他端：不需要；后端可在 Backend Step 8 联调。

### Step 2.1：指令

- [ ] Mock provider 生成确定性的静态 HTML5 游戏 bundle。
### Step 2.2：指令

- [ ] 产物必须包含 `manifest.json`、`index.html`、`style.css`、`game.js`、`assets/*`。
### Step 2.3：指令

- [ ] 产物不依赖前端本地组件。
### Step 2.4：指令

- [ ] 产物目标路径为 `drafts/{user_id}/{job_id}/{version}/...`。
### Step 2.5：指令

- [ ] 生成过程输出可读 Agent 日志。
### Step 2.6：指令

- [ ] Mock provider 可以使用 confirmation 字段填充 title、description、tags、controls。
### Step 2.7：验证

- [ ] Mock provider 输入同一 prompt 和 confirmation 时产物结构稳定。
### Step 2.8：验证

- [ ] 产物目录出现完整 bundle。
### Step 2.9：验证

- [ ] manifest 字段满足产物协议。
### Step 2.10：验证

- [ ] index 入口可在 iframe 中运行。
### Step 2.11：验证

- [ ] 日志覆盖开始、读取素材、生成产物、校验产物、完成。

## Step 3：实现真实 OpenAI-compatible provider 适配

依赖其他端：不需要；依赖后端环境变量约定。

### Step 3.1：指令

- [ ] 真实 provider 只在后端或 Agent 执行环境中调用。
### Step 3.2：指令

- [ ] API key、base URL、model name 从环境变量读取。
### Step 3.3：指令

- [ ] provider 输出必须落到同一静态产物协议。
### Step 3.4：指令

- [ ] 模型调用失败时返回失败状态和错误摘要。
### Step 3.5：指令

- [ ] Mock provider 仅用于本地兜底和 CI。
### Step 3.6：指令

- [ ] 真实 provider 不得要求前端提供任何模型密钥。
### Step 3.7：验证

- [ ] provider 为 OpenAI-compatible 且密钥存在时会走真实模型服务。
### Step 3.8：验证

- [ ] provider 为 OpenAI-compatible 但密钥缺失时任务失败或服务启动失败，错误明确。
### Step 3.9：验证

- [ ] provider 为 mock 时不需要模型密钥。
### Step 3.10：验证

- [ ] 真实 provider 产物协议与 Mock provider 一致。
### Step 3.11：验证

- [ ] 错误日志不包含 API key。

## Step 4：实现生成结果校验和打包

依赖其他端：不需要；上传到 MinIO 的动作可由 Backend Step 2 / Step 8 负责。

### Step 4.1：指令

- [ ] 校验产物包含 `manifest.json`、`index.html`、`style.css`、`game.js`。
### Step 4.2：指令

- [ ] 校验 manifest 包含 entry、title、description、cover、runtime、generatedAt。
### Step 4.3：指令

- [ ] 校验 entry 指向存在的文件。
### Step 4.4：指令

- [ ] 校验 scripts 和 styles 路径在 bundle 中存在。
### Step 4.5：指令

- [ ] 校验 assets 中列出的文件存在。
### Step 4.6：指令

- [ ] 打包前确保不包含后端密钥、本地绝对路径或临时日志。
### Step 4.7：验证

- [ ] 缺少 manifest 时任务失败。
### Step 4.8：验证

- [ ] entry 不存在时任务失败。
### Step 4.9：验证

- [ ] scripts 或 styles 缺失时任务失败。
### Step 4.10：验证

- [ ] 完整 bundle 校验通过。
### Step 4.11：验证

- [ ] 校验失败会输出 Agent error 日志。
### Step 4.12：验证

- [ ] 打包后的 artifact prefix 可被后端保存。

## Step 5：输出 Agent 日志和失败原因

依赖其他端：不需要；Backend Step 7 / Step 8 最终会持久化日志。

### Step 5.1：指令

- [ ] 每个关键步骤输出日志事件。
### Step 5.2：指令

- [ ] 日志 level 支持 `info / warning / error`。
### Step 5.3：指令

- [ ] failed 任务必须返回用户可理解的失败原因。
### Step 5.4：指令

- [ ] 错误摘要需要告诉用户如何重试。
### Step 5.5：指令

- [ ] 不实现复杂 retry 策略；Agent 失败后是否允许用户点击 retry 留待后续确认。
### Step 5.6：指令

- [ ] 日志不得包含 secret、token、password、OAuth code、完整 presigned URL。
### Step 5.7：验证

- [ ] succeeded 任务有完整日志链路。
### Step 5.8：验证

- [ ] failed 任务有 error 日志和 `error_message`。
### Step 5.9：验证

- [ ] 日志能被后端按时间正序展示。
### Step 5.10：验证

- [ ] 日志不包含敏感信息。

## Step 6：提供后端联调 fixture

依赖其他端：不需要。

### Step 6.1：指令

- [ ] 准备一个成功 fixture，包含 prompt、confirmation、uploaded assets 元信息。
### Step 6.2：指令

- [ ] 准备一个失败 fixture，用于模拟模型调用失败或产物校验失败。
### Step 6.3：指令

- [ ] fixture 的输入输出字段与 Agent Step 1 执行器边界一致。
### Step 6.4：指令

- [ ] fixture 不包含真实密钥或真实用户隐私数据。
### Step 6.5：验证

- [ ] Backend Step 8 可以用成功 fixture 创建 succeeded 任务和 draft game。
### Step 6.6：验证

- [ ] Backend Step 8 可以用失败 fixture 创建 failed 任务和错误日志。

## 5. Agent 交付前自检

- [ ] Mock provider 可独立运行并生成完整 bundle。
- [ ] OpenAI-compatible provider 可在有密钥时运行。
- [ ] 缺少模型密钥时错误明确。
- [ ] 产物协议与 [design-document.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/design-document.md) 一致。
- [ ] 执行器输入输出与本文档第 3 节一致。
- [ ] 日志不包含敏感信息。
- [ ] 后端可用 fixture 接入。
- [ ] 更新 [architecture.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/architecture.md) 和 [progress.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/progress.md)。

## 6. 最终接入条件

Agent 完成后，应能支持：

- Backend Step 8 用真实 Agent 执行器替换 fake runner。
- 后端创建任务后，任务可从 `pending` 到 `running` 到 `succeeded / failed`。
- succeeded 任务生成 draft game 和完整静态 bundle。
- failed 任务返回可展示错误原因和日志。
- 前端通过 Jobs API 展示任务状态、Agent 日志和 draft 试玩入口。
