# Agent 编排设计文档

## 1. 文档目标

本文档定义本项目生成链路的 Agent 编排方案，用于后续在独立于 `frontend/` 和 `backend/` 的本地 `agent/` 目录中，先行实现和调试一套基于 LangGraph 的多 Agent 工作流。

本文档回答以下问题：

- Create 页中的“对话澄清”和“后台生成”如何拆阶段。
- 多 Agent 是否合理，以及应该如何分工。
- 每个 Agent 的输入、输出、技能、工具和状态字段是什么。
- LangGraph 工作流如何从用户对话一路推进到 `manifest.json` 产物。
- 未来如何把本地 `agent/` 目录接回现有后端 `generation_job` 链路。

本文档不直接替代 [agent-implementation-plan.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/agent-implementation-plan.md)，而是作为它的详细编排补充。

## 2. 设计结论

结论：`这种多 Agent 设计是合理的，但必须采用“双阶段、外单内多”的实现方式。`

推荐架构：

- 对外只有一个 `Agent Runner` 入口，供后端 `generation_job` 调用。
- 对内采用多 Agent 协作，但不把每个 Agent 都暴露给前端或后端。
- 整体拆为两个阶段：
  - `阶段 A：对话设计阶段`
  - `阶段 B：后台生成阶段`

推荐角色：

- `Orchestrator`：LangGraph 编排层，负责状态流转和任务派发。
- `Design Agent`：与用户对话，提出建议、补齐需求、沉淀确认卡片。
- `Asset Agent`：理解上传素材，并生成素材用途计划。
- `Spec Builder`：把确认卡片和素材分析转成开发可执行的 `game spec`。
- `Developer Agent`：生成静态游戏 bundle。
- `Validator Agent`：校验产物协议、运行约束和错误原因。

其中：

- `Orchestrator` 推荐实现为 LangGraph workflow controller，不建议做成一个很重的“大模型总指挥”。
- `Spec Builder` 推荐实现为独立节点，可单独调用模型，也可后续并入 `Design Agent` 或 `Developer Agent` 前置节点。

## 3. 为什么要分成两阶段

### 3.1 阶段 A：对话设计阶段

目标：帮助用户把自然语言想法、后续补充要求和上传素材意图，收敛成一份可确认的游戏方案。

产出：

- `user_requirements`
- `game_plan`
- `material_usage`
- `confirmation_card`

这个阶段直接服务 Create 页，强调：

- AI 追问
- 每次追问都给出可选建议，降低用户表达成本
- 帮用户想玩法、风格、角色、胜负条件
- 明确素材怎么用
- 生成游戏卡片，包含标题和简介
- 支持用户点击 `换一换` 后，在原需求约束内重新生成方案和卡片
- 支持用户继续聊天后，基于新需求完善已有方案

阶段 A 不建议默认使用 `create_react_agent`。推荐把 `Design Agent` 实现为普通 LangGraph node，由 `conversation_graph` 负责事件路由、状态维护和分支控制。原因是本阶段的输入、状态和输出都很明确，不需要让模型自主决定工具调用循环；后续如果需要搜索参考游戏、调用多模态理解工具或外部知识库，可再把对应节点升级为工具型 agent 或子图。

阶段 A 的用户动作：

| 动作 | 来源 | 含义 | Graph 处理 |
| --- | --- | --- | --- |
| `chat` | 用户发送消息 | 新增或修改需求 | 更新 `user_requirements`、`game_plan` 和 `material_usage` |
| `regenerate` | 用户点击换一换 | 保持既有需求，重新生成另一版方案 | 保留 `user_requirements` 和 `material_usage`，刷新 `game_plan` 和 `confirmation_card` |
| `confirm` | 用户点击生成 | 用户接受当前方案并进入生成 | 锁定 `confirmation_card`，进入阶段 B |

阶段 A 的最小完成条件：

- `user_requirements` 能表达用户已经说清楚的需求和仍缺失的信息。
- `game_plan` 能覆盖标题、介绍、标签、玩法、风格、角色和胜负条件。
- `material_usage` 能表达每个上传素材在游戏里的用途。
- `confirmation_card` 能直接展示给用户，并能作为阶段 B 的输入。

### 3.2 阶段 B：后台生成阶段

目标：在用户确认后，生成可运行的游戏产物。

产出：

- `game_spec`
- `artifact bundle`
- `manifest.json`
- `agent logs`
- `validation report`

这个阶段不再和用户持续对话，强调：

- 可重复执行
- 可记录日志
- 可失败归因
- 可被后端异步任务调用

### 3.3 这样拆分的原因

- 前台聊天和后台生成的节奏不同，不应放进同一个循环。
- 用户确认前允许探索和发散；确认后应转入稳定、可审计的执行流。
- 对话状态适合面向产品语言；代码生成状态适合面向实现语言。
- 这样最容易接回现有 `generation_job -> running -> succeeded/failed` 的后端模型。

## 4. 总体 Workflow

完整工作流如下：

1. 用户进入 Create，输入创意并上传素材。
2. `Design Agent` 基于聊天上下文持续维护 `user_requirements`、`game_plan` 和 `material_usage`。
3. 当关键信息足够时，`Design Agent` 生成 `confirmation_card` 给用户确认。
4. 用户确认后，Create 创建 `generation_job`。
5. 后端调用 `Agent Runner`，进入后台生成流程。
6. `Orchestrator` 初始化生成状态，并调用 `Asset Agent` 分析素材。
7. `Spec Builder` 结合 `prompt + user_requirements + game_plan + material_usage + confirmation_card + asset_analysis` 生成 `game_spec`。
8. `Developer Agent` 根据 `game_spec` 和素材计划生成静态 bundle。
9. `Validator Agent` 校验 bundle、manifest、资源引用和运行约束。
10. 如果校验通过，输出 `manifest.json`、`index.html`、`style.css`、`game.js` 和 `assets/*`。
11. 如果校验失败，返回 `failed_step`、`error_message`、`retry_hint` 和日志。
12. 后端保存 draft game、artifact prefix、manifest 路径和 `agent_logs`。

## 5. LangGraph 状态机建议

## 5.1 顶层 Graph

建议拆成两个子图：

- `conversation_graph`
- `generation_graph`

顶层结构：

```text
START
  -> conversation_graph
  -> user_confirmed?
    -> no: return confirmation card / continue chat
    -> yes: generation_graph
  -> END
```

在独立本地 `agent/` 目录里，可以先把两个子图都做通；接后端时，只把 `generation_graph` 暴露给后端 runner。

## 5.2 conversation_graph

第一阶段使用 `conversation_graph`。它是一个面向 Create 页对话体验的 LangGraph 子图，只负责需求收集和方案确认，不生成游戏代码和静态 bundle。

### 5.2.1 Graph 结构

推荐结构：

```text
START
  -> ingest_user_event
  -> route_user_event
    -> chat: update_requirements
      -> generate_or_refine_plan
      -> build_user_response
      -> END
    -> regenerate: regenerate_plan
      -> build_user_response
      -> END
    -> confirm: lock_confirmation
      -> END
    -> invalid: build_error_response
      -> END
```

路由规则：

| 路由 | 条件 | 说明 |
| --- | --- | --- |
| `chat` | `user_event.type == "chat"` | 用户发送新消息，Graph 需要吸收新需求并完善方案 |
| `regenerate` | `user_event.type == "regenerate"` | 用户点击 `换一换`，Graph 在原需求约束内重新生成方案 |
| `confirm` | `user_event.type == "confirm"` | 用户点击 `生成`，Graph 锁定当前卡片并交给阶段 B |
| `invalid` | 缺少必要事件字段或事件类型不支持 | 返回可展示错误，不进入生成 |

### 5.2.2 State 总览

第一阶段 state 只维护三个业务主参数，并允许额外响应字段存在。

| 字段 | 类型 | 是否必需 | 说明 |
| --- | --- | --- | --- |
| `user_requirements` | object | 是 | 用户需求的累积摘要，不等同于原始聊天记录 |
| `game_plan` | object | 是 | 当前可展示、可确认的游戏方案 |
| `material_usage` | object | 是 | 上传素材在游戏中的用途计划 |
| `user_event` | object | 是 | 当前轮用户动作，来自聊天输入或按钮 |
| `assistant_response` | object | 否 | 本轮返回给前端展示的消息、建议和卡片 |
| `confirmation_card` | object | 否 | 用户可确认的卡片对象，来自 `game_plan` 的展示子集 |
| `handoff_to_generation` | boolean | 否 | 是否进入阶段 B，只有 `confirm` 成功后为 `true` |
| `conversation_status` | string | 否 | `collecting / ready_to_confirm / confirmed / error` |

实现时，`user_requirements`、`game_plan` 和 `material_usage` 是必须持久化和跨轮传入的核心状态；其他字段可以按请求临时生成，也可以写入 checkpoint 方便回放。

### 5.2.3 user_event 字段

`user_event` 表示 Create 页传入的当前用户动作。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `type` | string | `chat / regenerate / confirm` |
| `message` | string nullable | 用户本轮自然语言输入；`chat` 时必需 |
| `uploaded_assets` | object[] | 本轮可见素材列表，包含素材元信息 |
| `selected_card_id` | string nullable | 用户点击生成或换一换时对应的卡片 ID |
| `timestamp` | string | 前端或后端生成的事件时间 |

`uploaded_assets` 的元素建议包含：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `asset_id` | string | 后端素材 ID |
| `filename` | string | 原始文件名 |
| `mime_type` | string | MIME 类型 |
| `size_bytes` | number | 文件大小 |
| `object_key` | string | 对象存储 key，不向模型暴露完整 presigned URL |
| `user_hint` | string nullable | 用户对素材用途的说明 |

### 5.2.4 user_requirements 字段

`user_requirements` 是第一阶段最重要的记忆对象。它负责把多轮聊天压缩成稳定需求。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `intent_summary` | string | 用户想做什么游戏的摘要 |
| `must_have` | string[] | 用户明确要求必须保留的内容 |
| `nice_to_have` | string[] | 用户提到但可调整的偏好 |
| `constraints` | string[] | 不能违背的限制，如儿童友好、单键操作、必须使用某素材 |
| `open_questions` | string[] | 仍需澄清的问题 |
| `answered_questions` | object[] | 已经问过并得到回答的问题，避免重复追问 |
| `preference_profile` | object | 风格、节奏、难度、目标玩家等偏好 |
| `revision_count` | number | 用户继续聊天修改方案的次数 |

`preference_profile` 建议字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `genre_candidates` | string[] | 可能的游戏类型 |
| `visual_style` | string nullable | 美术风格，如像素、赛博、童话 |
| `tone` | string nullable | 氛围，如轻松、紧张、搞笑 |
| `target_session_length` | string nullable | 单局时长预估，如 1 分钟、3 分钟 |
| `difficulty` | string nullable | `easy / medium / hard` |

### 5.2.5 game_plan 字段

`game_plan` 是当前完整游戏方案。它是给用户展示、给后续 `Spec Builder` 使用的中间层。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `plan_id` | string | 当前方案 ID，换一换时生成新 ID |
| `title` | string | 游戏标题 |
| `introduction` | string | 游戏介绍，展示在卡片和确认区 |
| `tags` | string[] | 归一化标签 |
| `gameplay` | string | 核心玩法说明 |
| `core_loop` | string[] | 玩家反复执行的主循环 |
| `style` | string | 视觉与听觉风格 |
| `characters` | object[] | 玩家角色、敌人、NPC、交互物 |
| `win_condition` | string | 胜利条件 |
| `lose_condition` | string | 失败条件 |
| `controls` | string | 操作方式 |
| `suggestions` | object[] | 本轮给用户的建议，每个追问后至少带一个建议 |
| `confidence` | string | `low / medium / high`，表示方案完整度 |

`tags` 使用平台预定义集合，MVP 建议集合如下：

| 标签值 | 中文名 | 说明 |
| --- | --- | --- |
| `adventure` | 冒险 | 探索、闯关、发现 |
| `action` | 动作 | 反应、躲避、攻击 |
| `strategy` | 策略 | 规划、资源、决策 |
| `puzzle` | 解谜 | 机关、逻辑、推理 |
| `arcade` | 街机 | 高反馈、短局、分数 |
| `survival` | 生存 | 资源压力、坚持时间 |
| `simulation` | 模拟 | 经营、养成、系统反馈 |
| `racing` | 竞速 | 速度、路线、时间挑战 |
| `rhythm` | 音乐节奏 | 节拍、点击、连击 |
| `roleplay` | 角色扮演 | 角色成长、剧情扮演 |
| `casual` | 休闲 | 低门槛、轻松体验 |
| `educational` | 教育 | 学习、训练、知识反馈 |

`suggestions` 的元素建议包含：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `question` | string | AI 想问用户的问题 |
| `suggested_answer` | string | AI 推荐的默认答案 |
| `alternatives` | string[] | 其他可选方向 |
| `reason` | string | 为什么这个问题会影响游戏方案 |

### 5.2.6 material_usage 字段

`material_usage` 记录用户上传素材和游戏设计之间的关系。阶段 A 不做深度多模态解析，只做用途规划；深度理解留给阶段 B 的 `Asset Agent`。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `assets` | object[] | 每个素材的用途计划 |
| `global_usage_summary` | string | 全部素材如何服务游戏体验 |
| `missing_asset_needs` | string[] | 当前方案还缺哪些素材，可由生成阶段补足 |

`assets` 的元素建议包含：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `asset_id` | string | 后端素材 ID |
| `filename` | string | 原始文件名 |
| `mime_type` | string | MIME 类型 |
| `intended_use` | string | 计划用途，如主角参考、背景参考、音效参考 |
| `usage_priority` | string | `must_use / optional / reference_only` |
| `user_hint` | string nullable | 用户声明的用途 |
| `agent_note` | string | Design Agent 对该素材用途的解释 |

### 5.2.7 confirmation_card 字段

`confirmation_card` 是给用户点击 `生成` 前确认的展示对象。它来自 `game_plan`，但只保留前端卡片和确认区需要的信息。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `card_id` | string | 卡片 ID，通常与 `game_plan.plan_id` 对齐 |
| `title` | string | 游戏标题 |
| `introduction` | string | 游戏介绍 |
| `tags` | string[] | 展示标签 |
| `gameplay_summary` | string | 玩法摘要 |
| `style_summary` | string | 风格摘要 |
| `character_summary` | string | 角色摘要 |
| `win_lose_summary` | string | 胜负条件摘要 |
| `material_usage_summary` | string | 素材用途摘要 |
| `is_ready_to_generate` | boolean | 是否足够进入阶段 B |

### 5.2.8 节点定义

#### ingest_user_event

作用：校验并规范化本轮用户动作。

输入参数：

| 参数 | 来源 | 含义 |
| --- | --- | --- |
| `user_event` | 前端或后端 | 用户本轮动作 |
| `user_requirements` | checkpoint 或请求 | 历史需求摘要 |
| `game_plan` | checkpoint 或请求 | 当前方案 |
| `material_usage` | checkpoint 或请求 | 当前素材用途 |

输出更新：

| 字段 | 含义 |
| --- | --- |
| `user_event` | 规范化后的事件 |
| `conversation_status` | 校验失败时为 `error` |
| `assistant_response` | 校验失败时给前端的错误信息 |

#### route_user_event

作用：根据 `user_event.type` 决定下一条边。

输入参数：

| 参数 | 含义 |
| --- | --- |
| `user_event.type` | 当前事件类型 |
| `conversation_status` | 前序校验状态 |

输出：不直接更新 state，只返回路由名：`chat / regenerate / confirm / invalid`。

#### update_requirements

作用：把用户新消息合并进 `user_requirements`，并同步素材用途初稿。

输入参数：

| 参数 | 含义 |
| --- | --- |
| `user_event.message` | 用户本轮补充内容 |
| `user_event.uploaded_assets` | 当前可见素材 |
| `user_requirements` | 历史需求摘要 |
| `material_usage` | 历史素材用途 |

输出更新：

| 字段 | 含义 |
| --- | --- |
| `user_requirements` | 合并新消息后的需求状态 |
| `material_usage` | 根据新消息和素材提示更新后的用途计划 |
| `conversation_status` | 通常为 `collecting` 或 `ready_to_confirm` |

#### generate_or_refine_plan

作用：根据最新 `user_requirements` 生成或完善 `game_plan`。

输入参数：

| 参数 | 含义 |
| --- | --- |
| `user_requirements` | 最新用户需求 |
| `material_usage` | 最新素材用途 |
| `game_plan` | 旧方案，用户继续聊天时用于保持连续性 |

输出更新：

| 字段 | 含义 |
| --- | --- |
| `game_plan` | 新方案或完善后的方案 |
| `confirmation_card` | 从方案提取出的卡片 |
| `conversation_status` | 信息充分时为 `ready_to_confirm`，否则为 `collecting` |

规则：

- 如果 `user_requirements.open_questions` 非空，`game_plan.suggestions` 必须包含追问和建议答案。
- 如果用户已有明确要求，节点不得为了生成新意而丢弃 `must_have`。
- 如果用户修改需求，节点应优先解释变更后的方案，而不是重新开始。

#### regenerate_plan

作用：处理用户点击 `换一换`。它只刷新方案表达，不清空需求。

输入参数：

| 参数 | 含义 |
| --- | --- |
| `user_requirements` | 需要保持一致的需求约束 |
| `material_usage` | 需要保持一致的素材用途 |
| `game_plan` | 当前用户想替换的方案 |
| `user_event.selected_card_id` | 被替换的卡片 ID |

输出更新：

| 字段 | 含义 |
| --- | --- |
| `game_plan` | 同需求下的新方案 |
| `confirmation_card` | 新卡片 |
| `conversation_status` | `ready_to_confirm` |

规则：

- 必须保留 `user_requirements.must_have`、`constraints` 和 `material_usage.assets`。
- 可以改变标题、介绍、玩法表达、角色组合、风格细节和标签组合。
- 不能把用户已经否定的方向重新加回来。

#### lock_confirmation

作用：处理用户点击 `生成`，锁定当前卡片，准备进入阶段 B。

输入参数：

| 参数 | 含义 |
| --- | --- |
| `confirmation_card` | 用户确认的卡片 |
| `game_plan` | 完整游戏方案 |
| `material_usage` | 素材用途 |

输出更新：

| 字段 | 含义 |
| --- | --- |
| `handoff_to_generation` | `true` |
| `conversation_status` | `confirmed` |

规则：

- 如果 `confirmation_card.is_ready_to_generate` 为 `false`，不得进入阶段 B。
- 如果缺少标题、介绍、玩法、胜负条件或素材用途摘要，应返回 `invalid` 或 `collecting`。

#### build_user_response

作用：把内部状态转成前端可展示响应。

输入参数：

| 参数 | 含义 |
| --- | --- |
| `user_requirements` | 用于说明还缺什么 |
| `game_plan` | 当前方案 |
| `confirmation_card` | 游戏卡片 |
| `material_usage` | 素材用途摘要 |

输出更新：

| 字段 | 含义 |
| --- | --- |
| `assistant_response.message` | 给用户看的自然语言回复 |
| `assistant_response.suggestions` | 追问后的建议选项 |
| `assistant_response.card` | 游戏卡片 |
| `assistant_response.actions` | 前端按钮，如 `generate`、`regenerate` |

#### build_error_response

作用：为不支持事件或缺字段构造错误响应。

输入参数：

| 参数 | 含义 |
| --- | --- |
| `user_event` | 原始事件 |
| `conversation_status` | 错误状态 |

输出更新：

| 字段 | 含义 |
| --- | --- |
| `assistant_response.message` | 可展示错误 |
| `conversation_status` | `error` |

### 5.2.9 边定义

| 起点 | 终点 | 类型 | 条件 | 作用 |
| --- | --- | --- | --- | --- |
| `START` | `ingest_user_event` | 普通边 | 无 | 进入第一阶段 |
| `ingest_user_event` | `route_user_event` | 普通边 | 校验完成 | 统一进入路由 |
| `route_user_event` | `update_requirements` | 条件边 | `chat` | 吸收新消息 |
| `update_requirements` | `generate_or_refine_plan` | 普通边 | 无 | 生成或完善方案 |
| `generate_or_refine_plan` | `build_user_response` | 普通边 | 无 | 组装前端响应 |
| `route_user_event` | `regenerate_plan` | 条件边 | `regenerate` | 换一换 |
| `regenerate_plan` | `build_user_response` | 普通边 | 无 | 返回新方案 |
| `route_user_event` | `lock_confirmation` | 条件边 | `confirm` | 锁定卡片 |
| `lock_confirmation` | `END` | 普通边 | `handoff_to_generation=true` | 结束第一阶段 |
| `route_user_event` | `build_error_response` | 条件边 | `invalid` | 构造错误响应 |
| `build_error_response` | `END` | 普通边 | 无 | 返回错误 |
| `build_user_response` | `END` | 普通边 | 无 | 返回对话结果 |

### 5.2.10 第一阶段输出契约

对前端返回：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `assistant_response.message` | string | AI 回复 |
| `assistant_response.suggestions` | object[] | 追问和建议 |
| `assistant_response.card` | object nullable | 游戏卡片 |
| `assistant_response.actions` | string[] | 可用动作，通常是 `generate`、`regenerate` |
| `conversation_status` | string | 当前对话状态 |

交给阶段 B：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `user_requirements` | object | 用户需求摘要 |
| `game_plan` | object | 完整游戏方案 |
| `material_usage` | object | 素材用途计划 |
| `confirmation_card` | object | 用户确认卡片 |
| `handoff_to_generation` | boolean | 是否允许创建生成任务 |

## 5.3 generation_graph

节点建议：

- `init_generation_context`
- `analyze_assets`
- `build_game_spec`
- `generate_game_bundle`
- `validate_bundle`
- `finalize_success`
- `finalize_failure`

推荐边：

```text
START
  -> init_generation_context
  -> analyze_assets
  -> build_game_spec
  -> generate_game_bundle
  -> validate_bundle
    -> valid: finalize_success
    -> invalid: finalize_failure
END
```

MVP 不建议在 Graph 内做复杂自动重试。失败后直接返回结构化错误即可。

## 6. Agent 角色定义

## 6.1 Orchestrator

### 角色定位

工作流控制器，不直接承担主要内容创作。

### 核心职责

- 初始化和维护全局 state。
- 决定当前应该调用哪个 Agent。
- 记录阶段日志和失败点。
- 汇总最终输出。

### 不负责

- 不直接产出玩法方案。
- 不直接编写游戏代码。
- 不替代 Validator 做产物校验。

### 输入

- `job_context`
- `conversation_context`
- `uploaded_assets`
- `confirmation_card`

### 输出

- `graph_state`
- `job_status`
- `agent_logs`
- `final_result`

### Skills

- 工作流编排
- 状态路由
- 错误收敛
- 结果聚合

### Tools

- `state_store`
- `log_writer`
- `route_decider`
- `result_aggregator`

## 6.2 Design Agent

### 角色定位

面向用户的需求设计顾问。

### 核心职责

- 和用户对话。
- 提出建议和候选玩法。
- 补齐缺失的需求字段。
- 维护 `user_requirements`、`game_plan` 和 `material_usage`。
- 生成 `confirmation_card`。

### 输入

- `user_event`
- `user_requirements`
- `game_plan`
- `material_usage`

### 输出

- `assistant_response`
- `user_requirements`
- `game_plan`
- `material_usage`
- `confirmation_card`

### Skills

- 创意收敛
- 游戏玩法建议
- 风格与角色设定
- 胜负条件整理
- 素材用途初步映射

### Tools

- `conversation_memory`
- `suggestion_templates`
- `requirements_updater`
- `game_plan_builder`
- `material_usage_planner`
- `confirmation_card_builder`

## 6.3 Asset Agent

### 角色定位

素材理解与素材计划节点。

### 核心职责

- 分析图片、视频、音频和通用文件的可用性。
- 识别素材类型、内容摘要和潜在用途。
- 输出素材使用建议，而不是盲目生成新素材。
- 可选地产出轻量补充素材建议，如封面占位图、icon 占位图、背景图占位图。

### 输入

- `asset_registry`
- `asset_access_info`
- `user_requirements`
- `game_plan`
- `material_usage`
- `confirmation_card`

### 输出

- `asset_analysis`
- `asset_usage_plan`
- `asset_risks`

### Skills

- 多模态素材理解
- 素材分类
- 用途映射
- 风险识别

### Tools

- `image_describer`
- `video_keyframe_sampler`
- `audio_transcriber`
- `file_metadata_reader`
- `asset_usage_planner`

### 说明

MVP 推荐先实现“理解和规划”，而不是强做完整媒体再生成。

## 6.4 Spec Builder

### 角色定位

把用户确认结果翻译成开发可执行规格。

### 核心职责

- 读取 `user_requirements`、`game_plan`、`material_usage`、`confirmation_card` 和 `asset_analysis`。
- 生成更严格、更工程化的 `game_spec`。
- 明确玩法循环、场景结构、交互对象、素材分配和技术约束。

### 输入

- `prompt`
- `user_requirements`
- `game_plan`
- `material_usage`
- `confirmation_card`
- `asset_analysis`

### 输出

- `game_spec`

### Skills

- 规格抽象
- 实现约束归一化
- 游戏 loop 结构化
- 素材使用计划固化

### Tools

- `spec_schema_builder`
- `constraint_normalizer`
- `asset_plan_merger`

## 6.5 Developer Agent

### 角色定位

游戏实现节点，负责静态 Web bundle 生成。

### 核心职责

- 根据 `game_spec` 生成 `index.html`、`style.css`、`game.js`。
- 生成 `manifest.json`。
- 合理引用素材或生成占位资源。
- 保证产物是纯静态文件，不依赖本地 React 组件。

### 输入

- `game_spec`
- `asset_usage_plan`
- `artifact_workspace`

### 输出

- `artifact_files`
- `manifest_draft`
- `dev_notes`

### Skills

- HTML5 小游戏生成
- HUD 与交互逻辑实现
- 资源引用组织
- manifest 生成

### Tools

- `bundle_writer`
- `template_selector`
- `html_generator`
- `css_generator`
- `js_generator`
- `manifest_builder`

## 6.6 Validator Agent

### 角色定位

生成产物的质量门禁。

### 核心职责

- 校验产物协议是否完整。
- 校验入口文件、脚本、样式和资源引用是否存在。
- 校验 manifest 字段。
- 给出用户可理解的失败原因和重试提示。

### 输入

- `artifact_files`
- `manifest_draft`
- `game_spec`

### 输出

- `validation_report`
- `sanitized_error_summary`
- `retry_hint`

### Skills

- 产物协议校验
- 路径一致性校验
- 错误摘要生成
- 风险脱敏

### Tools

- `bundle_linter`
- `manifest_validator`
- `path_checker`
- `error_sanitizer`

## 7. 对话阶段字段设计

第一阶段字段以 [5.2 conversation_graph](#52-conversation_graph) 为准。对话阶段只维护三个业务主状态：`user_requirements`、`game_plan`、`material_usage`，并按需派生 `confirmation_card` 和 `assistant_response`。

## 7.1 user_requirements

这是用户需求的累积摘要，用于跨轮保持一致性。

核心字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| intent_summary | string | 用户想做什么游戏 |
| must_have | string[] | 必须保留的要求 |
| nice_to_have | string[] | 可调整偏好 |
| constraints | string[] | 设计限制 |
| open_questions | string[] | 仍需澄清的问题 |
| answered_questions | object[] | 已回答问题 |
| preference_profile | object | 类型、风格、难度、节奏等偏好 |

## 7.2 game_plan

这是完整游戏方案，用于展示和后续生成。

核心字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| plan_id | string | 方案 ID |
| title | string | 游戏标题 |
| introduction | string | 游戏介绍 |
| tags | string[] | 归一化标签 |
| gameplay | string | 核心玩法 |
| style | string | 风格 |
| characters | object[] | 角色和交互对象 |
| win_condition | string | 胜利条件 |
| lose_condition | string | 失败条件 |
| controls | string | 操作方式 |
| suggestions | object[] | 追问和建议 |

## 7.3 material_usage

这是素材用途计划，用于说明上传素材如何进入游戏设计。

核心字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| assets | object[] | 每个素材的用途计划 |
| global_usage_summary | string | 素材整体用途摘要 |
| missing_asset_needs | string[] | 仍缺少的素材需求 |

## 7.4 confirmation_card

这是给用户看的确认对象。

建议字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| title | string | 游戏标题 |
| introduction | string | 游戏介绍 |
| tags | string[] | 标签 |
| gameplay_summary | string | 核心玩法摘要 |
| style_summary | string | 风格摘要 |
| character_summary | string | 角色摘要 |
| win_lose_summary | string | 胜负条件摘要 |
| controls | string | 操作方式 |
| material_usage_summary | string | 素材用途摘要 |
| is_ready_to_generate | boolean | 是否允许进入生成 |
| asset_intent | object[] | 每个素材希望扮演的角色 |
| open_questions | string[] | 尚未澄清的问题 |
| confidence | string | low / medium / high |

## 8. 后台生成字段设计

## 8.1 job_context

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| job_id | string | 任务 ID |
| user_id | string | 用户 ID |
| created_at | string | 任务创建时间 |
| prompt | string | 原始创意 |

## 8.2 asset_registry

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| asset_id | string | 素材 ID |
| filename | string | 原始文件名 |
| mime_type | string | MIME type |
| size_bytes | number | 文件大小 |
| object_key | string | 存储路径 |
| access_mode | string | object_key / signed_url |
| purpose_hint | string nullable | 用户填写或系统推断用途 |

## 8.3 asset_analysis

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| asset_id | string | 素材 ID |
| media_type | string | image / video / audio / file |
| summary | string | 内容摘要 |
| extracted_elements | string[] | 提取到的主体、场景、动作、音效等 |
| suggested_uses | string[] | 推荐用途 |
| risks | string[] | 风险或不确定性 |

## 8.4 game_spec

`game_spec` 是开发 Agent 的主输入。

建议字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| spec_version | string | 规格版本 |
| title | string | 标题 |
| description | string | 简介 |
| genre | string | 游戏类型 |
| platform | string | 建议固定为 `html5-iframe` |
| gameplay_loop | string[] | 主循环 |
| objective | string | 目标 |
| fail_states | string[] | 失败状态 |
| controls | object[] | 输入映射 |
| scenes | object[] | 场景或关卡 |
| entities | object[] | 玩家、敌人、道具、障碍 |
| ui_hud | string[] | UI 元素 |
| art_direction | string | 视觉风格 |
| audio_direction | string | 音效方向 |
| asset_bindings | object[] | 素材到实体或场景的绑定 |
| implementation_notes | string[] | 实现建议 |
| technical_constraints | string[] | 例如单页、无外网、iframe sandbox |
| output_contract | object | 产物协议要求 |

## 8.5 artifact_result

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| artifact_prefix | string | 产物目录前缀 |
| manifest_path | string | manifest 路径 |
| entry_path | string | index.html 路径 |
| files | string[] | 产物文件清单 |
| cover_path | string nullable | 封面路径 |

## 8.6 validation_report

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| valid | boolean | 是否通过 |
| failed_step | string nullable | 失败步骤 |
| issues | object[] | 详细问题 |
| error_message | string nullable | 给用户的失败摘要 |
| retry_hint | string nullable | 重试提示 |

## 9. Agent 日志格式

所有 Agent 共用统一日志 schema：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| step | string | 步骤名 |
| agent | string | 产生日志的 Agent |
| level | string | info / warning / error |
| message | string | 可读摘要 |
| created_at | string | ISO 时间 |
| metadata | object | 非敏感附加信息 |

日志要求：

- 不包含 API key、password、session id、OAuth code。
- 不输出完整 presigned URL 签名。
- 文件路径可输出 object key 或去签名后的摘要 URL。

## 10. Tool 层设计建议

本地 `agent/` 目录建议把 Tools 做成普通 Python service，不先依赖后端框架。

推荐 Tool 列表：

- `read_asset_metadata(asset)`：读取文件名、类型、大小。
- `describe_image(path_or_bytes)`：图片摘要。
- `sample_video_frames(path_or_bytes)`：视频抽帧。
- `transcribe_audio(path_or_bytes)`：音频转写。
- `build_confirmation_card(design_state)`：生成确认卡片。
- `build_game_spec(inputs)`：生成规格。
- `write_artifact_file(path, content)`：写文件。
- `copy_or_bind_asset(asset, target_path)`：复制或绑定素材。
- `build_manifest(bundle_context)`：生成 manifest。
- `validate_bundle(bundle_dir)`：校验 bundle。
- `sanitize_error(error)`：脱敏错误。

MVP 里建议优先确保这些 Tool 稳定，而不是优先增加更多 Agent。

## 11. Skill 层设计建议

这里的 `skill` 指 Agent 的能力模块，不是 Codex skill。

推荐 skill 划分：

- `requirement_elicitation`
- `gameplay_suggestion`
- `design_state_normalization`
- `multimodal_asset_understanding`
- `asset_usage_mapping`
- `game_spec_authoring`
- `html5_bundle_generation`
- `manifest_authoring`
- `bundle_validation`
- `error_summarization`

建议关系：

- `Design Agent` 持有前 3 个 skill。
- `Asset Agent` 持有中间 2 个 skill。
- `Spec Builder` 持有 `game_spec_authoring`。
- `Developer Agent` 持有 `html5_bundle_generation` 和 `manifest_authoring`。
- `Validator Agent` 持有最后 2 个 skill。

## 12. 本地独立 agent 目录建议

推荐新建独立目录：

```text
agent/
├── README.md
├── pyproject.toml
├── .env.example
├── app/
│   ├── graph/
│   │   ├── conversation_graph.py
│   │   ├── generation_graph.py
│   │   └── state.py
│   ├── agents/
│   │   ├── design_agent.py
│   │   ├── asset_agent.py
│   │   ├── spec_builder.py
│   │   ├── developer_agent.py
│   │   └── validator_agent.py
│   ├── tools/
│   │   ├── asset_tools.py
│   │   ├── manifest_tools.py
│   │   ├── bundle_tools.py
│   │   └── logging_tools.py
│   ├── providers/
│   │   ├── openai_compatible.py
│   │   └── mock_provider.py
│   ├── schemas/
│   │   ├── confirmation.py
│   │   ├── requirements.py
│   │   ├── game_plan.py
│   │   ├── material_usage.py
│   │   ├── game_spec.py
│   │   └── validation.py
│   └── runner.py
├── fixtures/
│   ├── sample_prompt.json
│   ├── success_case/
│   └── failure_case/
├── output/
└── tests/
```

## 13. 本地调试路径建议

建议按以下顺序打通：

1. 先打通 `Design Agent -> user_requirements + game_plan + material_usage -> confirmation_card`。
2. 再打通 `Asset Agent -> asset_analysis`。
3. 再打通 `Spec Builder -> game_spec`。
4. 再打通 `Developer Agent -> bundle + manifest`。
5. 最后打通 `Validator Agent -> validation_report`。

本地最小验收标准：

- 输入一段 prompt 和 1 个素材。
- 经过对话阶段得到确认卡片。
- 用户确认后能生成一套完整 bundle。
- 产物包含 `manifest.json`、`index.html`、`style.css`、`game.js`。
- Validator 返回 `valid=true`。

## 14. 与现有后端对接方式

后端最终只需要关心一个统一 runner：

- 输入：
  - `job_id`
  - `user_id`
  - `prompt`
  - `user_requirements`
  - `game_plan`
  - `material_usage`
  - `confirmation_card`
  - `uploaded_assets`
- 输出：
  - `status`
  - `artifact_prefix`
  - `manifest_path`
  - `entry_path`
  - `draft_game_meta`
  - `logs`
  - `error_message`
  - `retry_hint`

接回现有系统时：

- 前端仍然只与 `Jobs API` 和 `Uploads API` 交互。
- 后端仍然只维护 `generation_jobs`、`agent_logs`、`games`。
- Agent 目录只作为独立执行器，不直接侵入前后端代码。

## 15. MVP 范围与非目标

## 15.1 本期建议纳入

- Design Agent 对话收敛
- Asset Agent 素材理解
- Spec Builder 规格生成
- Developer Agent 生成静态小游戏
- Validator Agent 校验产物
- LangGraph 编排
- Mock provider 和 OpenAI-compatible provider

## 15.2 本期不建议强做

- 多轮自动 retry
- 复杂子任务并行调度
- 大规模音视频再生成
- 内容审核 Agent
- 成本优化 Agent
- 资源配额 Agent
- 自动版本管理和 Remix

## 16. 推荐实施顺序

建议顺序：

1. 先在独立 `agent/` 目录实现 `conversation_graph`。
2. 再实现 `generation_graph` 的 mock provider 版本。
3. 再补 OpenAI-compatible provider。
4. 最后再接回后端 `Agent Runner`。

## 17. 最终判断

本方案判断如下：

- `Design Agent + Asset Agent + Developer Agent + Validator Agent + Orchestrator` 的方向是合理的。
- 为了避免需求和实现之间出现语义断层，必须增加一个 `Spec Builder` 节点，或者把它明确为 Orchestrator 内部的 planner 子节点。
- 如果按本文档实施，可以先在独立 `agent/` 目录把“从对话到 manifest”的全流程打通，再决定如何接回现有系统。
