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
- 整体拆为两个阶段和一条生成后修改链路：
  - `阶段 A：对话设计阶段`
  - `阶段 B：后台生成阶段`
  - `阶段 C：生成后修改阶段`

推荐角色：

- `Orchestrator`：LangGraph 编排层，负责状态流转和任务派发。
- `Design Agent`：与用户对话，提出建议、补齐需求、沉淀确认卡片。
- `Asset Agent`：本周 MVP 负责背景/人物可选图和独立封面图合同：按需处理或生成 `background.png`、`player.png`，并始终独立生成 `cover.png`。
- `Coding Agent`：根据 Orchestrator 的开发文档生成静态游戏 bundle。
- `Validator Agent`：做最终交付验收、协议校验和安全检查，不负责调试和返修。

其中：

- `Orchestrator` 推荐实现为 LangGraph workflow controller，不建议做成一个很重的“大模型总指挥”。
- 第二阶段的 `game_spec` / 开发文档 / 素材清单由 `Orchestrator` 的规划节点产出，不另设独立 `Spec Builder Agent`。
- `Validator Agent` 必须独立保留，不建议让 `Orchestrator` 或 `Coding Agent` 兼任最终验收；否则创作、自调试和质量门禁会混在一起。

## 3. 为什么要分成两阶段

### 3.1 阶段 A：对话设计阶段
  
![相对路径示例](../images/conversation_graph.png)

目标：帮助用户把自然语言想法、后续补充要求和上传素材意图，收敛成一份可确认的游戏方案。

产出：

- `user_requirements`
- `game_plan`
- `material_usage`
  
这个阶段直接服务 Create 页，强调：

- AI 追问
- 每次追问都给出可选建议，降低用户表达成本
- 帮用户想玩法、风格、角色、胜负条件
- 明确素材怎么用
- 生成游戏卡片，包含标题和简介
- 支持用户点击 `换一换` 后，在原需求约束内重新生成方案和卡片
- 支持用户继续聊天后，基于新需求完善已有方案
- 不处理已生成 draft 的二次迭代；生成后修改属于阶段 C。

阶段 A 不建议默认使用 `create_react_agent`。推荐把 `Design Agent` 实现为普通 LangGraph node，由 `conversation_graph` 负责事件路由、状态维护和分支控制。原因是本阶段的输入、状态和输出都很明确，不需要让模型自主决定工具调用循环；后续如果需要搜索参考游戏、调用多模态理解工具或外部知识库，可再把对应节点升级为工具型 agent 或子图。

阶段 A 的用户动作：

| 动作 | 来源 | 含义 | Graph 处理 |
| --- | --- | --- | --- |
| `chat` | 用户发送消息 | 新增或修改需求 | 更新 `user_requirements`、`game_plan` 和 `material_usage` |
| `upload_assets` | 用户上传附件 | 新增或更新素材用途 | 只更新 `material_usage.assets`，必要时轻微更新 `game_plan` 展示文案 |
| `regenerate` | 用户点击换一换 | 保持既有需求，重新生成另一版方案 | 保留 `user_requirements` 和 `material_usage`，刷新 `game_plan` |
| `confirm` | 用户点击生成 | 用户接受当前方案并进入生成 | 锁定当前 `game_plan`，进入阶段 B |

阶段 A 的最小完成条件：

- `user_requirements` 能表达用户已经说清楚的需求和仍缺失的信息。
- `game_plan` 能覆盖标题、介绍、标签、玩法、风格、角色和胜负条件。
- `material_usage` 能表达每个上传素材在游戏里的用途。
- `assistant_response.card` 能从 `game_plan.title`、`game_plan.introduction` 和 `game_plan.tags` 直接派生，展示给用户。

### 3.2 阶段 B：后台生成阶段
  
![相对路径示例](../images/generation_graph.png)

目标：在用户确认后，生成可运行的游戏产物。

产出：

- `development_brief`
- `asset_work_order`
- `asset_manifest_plan`
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
- 支持 `Asset Agent` 和 `Coding Agent` 并发执行
- 支持 `Coding Agent` 在资源到齐后自调试
- 支持 `Validator Agent` 做最终交付验收

### 3.3 阶段 C：生成后修改阶段

目标：用户已经生成过 draft 后，在聊天区提出明确修改，系统基于已有方案和已生成结果生成补丁，并创建新版本任务。

输入：

- 上一版 `generation_job`
- 上一版确认快照：`user_requirements`、`game_plan`、`material_usage`
- 已生成 draft 的 `game_id`、manifest、artifact prefix 和日志摘要
- 用户新消息

输出：

- `revision_intent`
- `game_plan_patch`
- `requires_regeneration`
- `assistant_response`
- 新的 revision job 输入

规则：

- 阶段 C 不回到阶段 A 重新收集标题、玩法、风格、胜负条件等基础需求。
- 只有用户修改意图明确时才直接创建 revision job；过于模糊或冲突时先追问。
- revision job 不覆盖旧 job、旧 draft 或旧产物，而是生成一版新的 draft。
- 阶段 C 可实现为独立 `revision_graph`，也可以先以后端服务封装最小 revision mode；但不得混入 `conversation_graph` 的第一阶段状态机。

### 3.4 这样拆分的原因

- 前台聊天和后台生成的节奏不同，不应放进同一个循环。
- 用户确认前允许探索和发散；确认后应转入稳定、可审计的执行流。
- 对话状态适合面向产品语言；代码生成状态适合面向实现语言。
- 生成后修改是基于既有 draft 的迭代，不是从 0 到 1 的需求收集。
- revision job 保留历史版本，避免把已经生成好的 draft 丢失或覆盖。
- 这样最容易接回现有 `generation_job -> running -> succeeded/failed` 的后端模型。

## 4. 总体 Workflow

完整工作流如下：

1. 用户进入 Create，输入创意并上传素材。
2. `Design Agent` 基于聊天上下文持续维护 `user_requirements`、`game_plan` 和 `material_usage`。
3. 当关键信息足够时，`Design Agent` 从 `game_plan` 派生游戏卡片给用户确认。
4. 用户确认后，Create 创建 `generation_job`。
5. 后端调用 `Agent Runner`，进入后台生成流程。
6. `Orchestrator` 初始化生成状态，解析 `user_requirements`、`game_plan`、`material_usage` 和 `uploaded_assets`。
7. `Orchestrator` 生成互相对齐的 `development_brief`、`asset_work_order` 和 `asset_manifest_plan`。
8. LangGraph 并发调用 `Coding Agent` 和 `Asset Agent`。
9. `Coding Agent` 根据 `development_brief` 生成 `index.html`、`style.css`、`game.js` 和 `manifest_draft`。
10. `Asset Agent` 根据 `asset_work_order` 处理或生成 `background.png`、`player.png`，并始终独立生成 `cover.png`，产出 `processed_assets`。
11. `Coding Agent` 汇合代码和真实资源，自调试 bundle、修正资源引用和 manifest。
12. 如果校验通过，输出 `manifest.json`、`index.html`、`style.css`、`game.js` 和 `assets/*`。
13. `Validator Agent` 最终验收产物协议、安全边界和调试证据。
14. 如果验收失败，直接返回 `failed_step`、`error_message`、`retry_hint` 和日志。
15. 后端保存 draft game、artifact prefix、manifest 路径和 `agent_logs`。

## 5. LangGraph 状态机建议

## 5.1 顶层 Graph

建议拆成三个子图：

- `conversation_graph`
- `generation_graph`
- `revision_graph`

顶层结构：

```text
START
  -> conversation_graph
  -> user_confirmed?
    -> no: return game card / continue chat
    -> yes: generation_graph
  -> END
```

在独立本地 `agent/` 目录里，可以先把 `conversation_graph`、`generation_graph` 和 `revision_graph` 的边界做清楚；接后端时，生成任务调用 `generation_graph`，生成后修改调用 `revision_graph` 或等价 revision mode。

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
    -> upload_assets: update_material_usage
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
| `upload_assets` | `user_event.type == "upload_assets"` | 用户上传或更新附件，Graph 只更新素材用途 |
| `regenerate` | `user_event.type == "regenerate"` | 用户点击 `换一换`，Graph 在原需求约束内重新生成方案 |
| `confirm` | `user_event.type == "confirm"` | 用户点击 `生成`，Graph 锁定当前方案并交给阶段 B |
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
| `handoff_to_generation` | boolean | 否 | 是否进入阶段 B，只有 `confirm` 成功后为 `true` |
| `conversation_status` | string | 否 | `collecting / ready_to_confirm / confirmed / error` |

实现时，`user_requirements`、`game_plan` 和 `material_usage` 是必须持久化和跨轮传入的核心状态；其他字段可以按请求临时生成，也可以写入 checkpoint 方便回放。

### 5.2.3 user_event 字段

`user_event` 表示 Create 页传入的当前用户动作。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `type` | string | `chat / upload_assets / regenerate / confirm` |
| `message` | string nullable | 用户本轮自然语言输入；`chat` 时必需 |
| `uploaded_assets` | object[] | 本轮可见素材列表，包含素材元信息 |
| `selected_plan_id` | string nullable | 用户点击生成或换一换时对应的方案 ID |
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

`game_plan` 是当前完整游戏方案。它是给用户展示、给阶段 B `Orchestrator` 生成开发文档和素材清单时使用的中间层。

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
| `suggestions` | string[] | 对本轮 AI 提问的简短建议答案，必须结合前文用户需求生成 |
| `confidence` | string | `low / medium / high`，表示方案完整度 |

`introduction` 是最终派生字段，不作为普通追问项向用户收集。Design Agent 必须先收集除 `introduction` 外的关键 `game_plan` 字段，再基于完整用户对话、游戏方案和素材用途总结出详细介绍，并由该介绍派生确认卡片。

`tags` 使用平台预定义集合，MVP集合如下：

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

`suggestions` 规则：

- 必须是字符串列表。
- 每条尽可能简短，建议 4 到 16 个中文字符。
- 每条都是对当前 AI 提问的可选回答，而不是泛泛的玩法说明。
- 必须结合前文用户需求生成，不能给与当前需求无关的模板化建议。
- 如果当前没有追问，`suggestions` 可以为空列表。

### 5.2.6 material_usage 字段

`material_usage` 记录用户上传素材和游戏设计之间的关系。阶段 A 只维护 `assets`，不做全局素材总结、缺失素材分析或深度多模态解析；这些属于阶段 B 的 `Asset Agent`。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `assets` | object[] | 每个素材的用途计划 |

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

### 5.2.7 游戏卡片字段

游戏卡片不是独立 state 参数，而是 `assistant_response.card`。它总是由 `game_plan` 派生，只包含卡片展示需要的字段。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `plan_id` | string | 对应 `game_plan.plan_id` |
| `title` | string | 游戏标题 |
| `introduction` | string | 游戏介绍 |
| `tags` | string[] | 展示标签 |

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

输出：不直接更新 state，只返回路由名：`chat / upload_assets / regenerate / confirm / invalid`。

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
| `material_usage` | 根据新消息和素材提示更新后的 `assets` |
| `conversation_status` | 通常为 `collecting` 或 `ready_to_confirm` |

#### update_material_usage

作用：处理用户上传或更新素材附件，只更新 `material_usage.assets`。

输入参数：

| 参数 | 含义 |
| --- | --- |
| `user_event.uploaded_assets` | 本轮上传或当前可见素材 |
| `material_usage` | 历史素材用途 |
| `user_requirements` | 历史需求摘要，用于让素材用途贴合前文 |
| `game_plan` | 当前方案，用于让素材用途贴合玩法和角色 |

输出更新：

| 字段 | 含义 |
| --- | --- |
| `material_usage.assets` | 更新后的素材用途列表 |
| `assistant_response.message` | 告诉用户素材已纳入方案 |
| `assistant_response.card` | 从当前 `game_plan` 派生的卡片 |

规则：

- 只更新 `material_usage.assets`。
- 如果用户给了素材用途提示，优先写入对应 `asset.user_hint` 和 `asset.intended_use`。
- 如果用户没有说明用途，应结合 `user_requirements` 和 `game_plan` 给出一个保守用途，如主角参考、背景参考、道具参考、音效参考。
- 该节点只在素材变化时运行；普通聊天里的素材提示可由 `update_requirements` 顺带同步。

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
| `user_event.selected_plan_id` | 被替换的方案 ID |

输出更新：

| 字段 | 含义 |
| --- | --- |
| `game_plan` | 同需求下的新方案 |
| `conversation_status` | `ready_to_confirm` |

规则：

- 必须保留 `user_requirements.must_have`、`constraints` 和 `material_usage.assets`。
- 可以改变标题、介绍、玩法表达、角色组合、风格细节和标签组合。
- 不能把用户已经否定的方向重新加回来。

#### lock_confirmation

作用：处理用户点击 `生成`，锁定当前方案，准备进入阶段 B。

输入参数：

| 参数 | 含义 |
| --- | --- |
| `game_plan` | 完整游戏方案 |
| `material_usage` | 素材用途 |

输出更新：

| 字段 | 含义 |
| --- | --- |
| `handoff_to_generation` | `true` |
| `conversation_status` | `confirmed` |

规则：

- 如果 `game_plan` 缺少标题、介绍、标签、玩法、风格、角色或胜负条件，不得进入阶段 B。
- 如果用户已上传素材但 `material_usage.assets` 没有记录用途，不得进入阶段 B。
- 成功后，阶段 B 直接读取 `game_plan`；前端卡片只是 `game_plan.title`、`game_plan.introduction` 和 `game_plan.tags` 的展示。

#### build_user_response

作用：把内部状态转成前端可展示响应。

输入参数：

| 参数 | 含义 |
| --- | --- |
| `user_requirements` | 用于说明还缺什么 |
| `game_plan` | 当前方案 |
| `material_usage` | 素材用途列表 |

输出更新：

| 字段 | 含义 |
| --- | --- |
| `assistant_response.message` | 给用户看的自然语言回复 |
| `assistant_response.suggestions` | 对当前 AI 提问的简短建议答案列表 |
| `assistant_response.card` | 从 `game_plan.title`、`game_plan.introduction`、`game_plan.tags` 派生的游戏卡片 |
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
| `route_user_event` | `update_material_usage` | 条件边 | `upload_assets` | 更新素材用途 |
| `update_material_usage` | `build_user_response` | 普通边 | 无 | 返回当前方案和素材反馈 |
| `route_user_event` | `regenerate_plan` | 条件边 | `regenerate` | 换一换 |
| `regenerate_plan` | `build_user_response` | 普通边 | 无 | 返回新方案 |
| `route_user_event` | `lock_confirmation` | 条件边 | `confirm` | 锁定方案 |
| `lock_confirmation` | `END` | 普通边 | `handoff_to_generation=true` | 结束第一阶段 |
| `route_user_event` | `build_error_response` | 条件边 | `invalid` | 构造错误响应 |
| `build_error_response` | `END` | 普通边 | 无 | 返回错误 |
| `build_user_response` | `END` | 普通边 | 无 | 返回对话结果 |

### 5.2.10 第一阶段输出契约

对前端返回：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `assistant_response.message` | string | AI 回复 |
| `assistant_response.suggestions` | string[] | 对当前 AI 提问的简短建议答案 |
| `assistant_response.card` | object nullable | 游戏卡片 |
| `assistant_response.actions` | string[] | 可用动作，通常是 `generate`、`regenerate` |
| `conversation_status` | string | 当前对话状态 |

交给阶段 B：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `user_requirements` | object | 用户需求摘要 |
| `game_plan` | object | 完整游戏方案 |
| `material_usage` | object | 素材用途计划 |
| `handoff_to_generation` | boolean | 是否允许创建生成任务 |

## 5.3 generation_graph

第二阶段使用 `generation_graph`。它是面向后端异步任务的 LangGraph 子图，只负责确认后的生成执行，不和用户继续对话。

### 5.3.1 Graph 结构

推荐结构：

```text
START
  -> init_generation_context
  -> build_parallel_contracts
  -> fan_out_generation
    -> coding: draft_code
    -> assets: run_asset_agent
  -> join_assets_and_code
  -> debug_code_with_assets
  -> validate_final_delivery
    -> valid: finalize_success
    -> invalid: finalize_failure
END
```

`fan_out_generation` 到 `draft_code` 和 `run_asset_agent` 是并发分支。两条分支必须读取同一个 `asset_manifest_plan`，这样 `Coding Agent` 可以先按目标路径生成代码草稿，`Asset Agent` 同时把真实资源处理到相同路径。

本阶段的调试职责属于 `Coding Agent`：它在 `join_assets_and_code` 后拿到真实 `processed_assets`，再执行 `debug_code_with_assets`，修复自己的代码、manifest 和资源引用。`Validator Agent` 不再负责调试和返修，只做最终交付验收。

MVP 不做自动返修循环。如果 `validate_final_delivery` 不通过，直接进入 `finalize_failure`，由后端记录错误，用户后续可以重新生成。

### 5.3.2 State 总览

第二阶段 state 维护确认后的生成上下文、并发契约、代码产物、素材产物、调试报告和最终验收结果。

| 字段 | 类型 | 是否必需 | 说明 |
| --- | --- | --- | --- |
| `job_context` | object | 是 | 后端生成任务上下文 |
| `user_requirements` | object | 是 | 第一阶段确认的用户需求 |
| `game_plan` | object | 是 | 第一阶段确认的游戏方案 |
| `material_usage` | object | 是 | 第一阶段确认的素材用途 |
| `uploaded_assets` | object[] | 是 | 后端可读的上传素材元信息 |
| `asset_registry` | object[] | 是 | 安全素材注册表 |
| `artifact_workspace` | string | 是 | 本次 bundle 工作目录 |
| `development_brief` | object | 是 | Coding Agent 开发文档 |
| `asset_work_order` | object | 是 | Asset Agent 素材任务单 |
| `asset_manifest_plan` | object[] | 是 | 代码和素材共享路径契约 |
| `code_artifacts` | object | 否 | Coding Agent 代码草稿和引用清单 |
| `manifest_draft` | object | 否 | Coding Agent 初版 manifest |
| `processed_assets` | object[] | 否 | Asset Agent 处理后的素材 |
| `asset_analysis` | object[] | 否 | Asset Agent 素材摘要和风险 |
| `integrated_bundle_context` | object | 否 | 代码和素材汇合后的上下文 |
| `debug_report` | object | 否 | Coding Agent 自调试报告 |
| `validation_report` | object | 否 | Validator 最终验收报告 |
| `artifact_result` | object | 否 | 成功后的产物路径结果 |
| `draft_game_meta` | object | 否 | 后端创建 draft game 所需 meta |
| `generation_status` | string | 否 | `planning / generating / debugging / validating / succeeded / failed` |
| `agent_logs` | object[] | 否 | 脱敏 Agent 日志 |

实现时，`development_brief`、`asset_work_order` 和 `asset_manifest_plan` 是 Orchestrator 的核心输出；`code_artifacts` 和 `processed_assets` 是并发分支输出；`debug_report` 是 Coding Agent 自调试证据；`validation_report` 是最终门禁证据。

### 5.3.3 节点定义

#### init_generation_context

作用：把后端 `generation_job` 输入转成第二阶段 state。

输入参数：

| 参数 | 含义 |
| --- | --- |
| `job_context` | `job_id`、`user_id`、`session_id`、创建时间和 prompt 摘要 |
| `user_requirements` | 第一阶段确认后的用户需求 |
| `game_plan` | 第一阶段确认后的完整游戏方案 |
| `material_usage` | 第一阶段确认后的素材用途 |
| `uploaded_assets` | 后端可读的上传素材元信息 |

输出更新：

| 字段 | 含义 |
| --- | --- |
| `generation_status` | `planning` |
| `artifact_workspace` | 本次任务的工作目录，如 `drafts/{user_id}/{job_id}/v1/` |
| `asset_registry` | 安全素材注册表，只包含元信息和 object key，不包含完整 presigned URL |
| `agent_logs` | 写入初始化日志 |

#### build_parallel_contracts

作用：由 `Orchestrator` 解析第一阶段传参，生成可并发执行的开发文档和素材清单。

输入参数：

| 参数 | 含义 |
| --- | --- |
| `user_requirements` | 用户需求摘要 |
| `game_plan` | 游戏方案 |
| `material_usage` | 素材用途 |
| `asset_registry` | 上传素材元信息 |
| `artifact_workspace` | 产物目标目录 |

输出更新：

| 字段 | 含义 |
| --- | --- |
| `development_brief` | 给 `Coding Agent` 的开发文档 |
| `asset_work_order` | 给 `Asset Agent` 的素材处理/生成清单 |
| `asset_manifest_plan` | 两个分支共享的资源路径契约 |
| `game_spec` | 面向实现的结构化规格，可由 `development_brief` 派生 |

规则：

- `development_brief` 和 `asset_work_order` 必须共享同一份 `asset_manifest_plan`。
- `asset_manifest_plan.target_path` 是代码引用和素材落盘的唯一约定路径。
- Orchestrator 不直接写代码、不直接处理素材、不做最终评估。
- 如果素材清单和开发文档无法对齐，应在本节点失败，不能进入并发分支。

#### fan_out_generation

作用：进入并发执行分支。

输出：不直接更新业务 state，只通过 LangGraph 边同时启动 `draft_code` 和 `run_asset_agent`。

#### draft_code

作用：Coding Agent 根据 `development_brief` 和 `asset_manifest_plan` 生成静态游戏代码草稿。

输入参数：

| 参数 | 含义 |
| --- | --- |
| `development_brief` | 玩法、场景、角色、UI、胜负条件、技术约束 |
| `asset_manifest_plan` | 代码允许引用的素材目标路径 |
| `artifact_workspace` | 文件写入目录 |

输出更新：

| 字段 | 含义 |
| --- | --- |
| `code_artifacts` | `index.html`、`style.css`、`game.js` 和代码引用清单 |
| `manifest_draft` | 初版 manifest |
| `coding_notes` | 实现说明和已知限制 |

规则：

- Coding Agent 可以引用 `asset_manifest_plan.target_path`，但不假设素材已经存在。
- Coding Agent 不生成最终素材文件；如需纯代码 fallback，可写在 `game.js` 中，但不得替代 Asset Agent 的素材职责。
- Coding Agent 必须保证游戏在无外网、sandboxed iframe 中运行。
- 本节点只生成代码草稿，不做真实资源到齐后的最终调试。

#### run_asset_agent

作用：根据 `asset_work_order` 处理用户上传素材，并补齐必要运行资源。

输入参数：

| 参数 | 含义 |
| --- | --- |
| `asset_work_order` | 素材处理/生成清单 |
| `asset_registry` | 用户上传素材元信息 |
| `asset_manifest_plan` | 素材目标路径契约 |
| `artifact_workspace` | 文件写入目录 |

输出更新：

| 字段 | 含义 |
| --- | --- |
| `processed_assets` | 已处理素材清单 |
| `asset_analysis` | 图片、视频、音频、文件的摘要和风险 |
| `asset_notes` | 素材处理说明 |

规则：

- 本周 MVP 的图像输出只包含三张候选图：`background.png`、`player.png`、`cover.png`；运行时代码只依赖 Orchestrator 选择的 `background.png` 和 `player.png`，`cover.png` 是展示素材。
- `background.png` 和 `player.png` 分开生成，各自使用独立 fixed prompt；fixed prompt 必须先声明生图模型是一位优秀的游戏 UI 设计师，再只放当前图片类型的定义。
- `background.png` fixed prompt 只包含背景图定义：`1280x720`、单屏游戏舞台、无 UI、无文字、留出玩法空间。
- `player.png` fixed prompt 只包含玩家图定义：模型生成画布可用 `1024x1024`，最终导出 `256x256`，单角色、完整轮廓、适合 2D sprite。
- `player.png` 生成时使用纯品红 `#FF00FF` 背景，并要求角色内部不要使用品红、粉色或紫色；Asset Agent 后处理负责把品红幕布抠成透明 alpha。
- `cover.png` fixed prompt 只包含独立封面图定义：`1280x720`、展示用 key art、按游戏内容和画风生成，不从 `background.png` 派生，不默认叠加标题文字。
- 图片：可直接复制、裁切、去底、缩放或转换为三图合同中的目标图片。
- 视频：本周只要求在需要时抽关键帧或提取静态背景参考，用来生成 `background.png`。
- 音频和通用文件：本周只作为规划参考输入，不要求直接进入运行时 `asset_manifest_plan`。
- 输出路径必须与 `asset_manifest_plan.target_path` 对齐。

#### join_assets_and_code

作用：等待代码分支和素材分支都完成，汇总给 Coding Agent 调试。

输出更新：

| 字段 | 含义 |
| --- | --- |
| `integrated_bundle_context` | 包含代码文件、资源文件、manifest 草稿和资源路径表 |
| `generation_status` | `debugging` |

规则：

- 如果 `draft_code` 或 `run_asset_agent` 任一分支失败，直接进入 `finalize_failure`，不进入调试。
- `integrated_bundle_context` 必须包含 `code_artifacts`、`manifest_draft`、`processed_assets` 和 `asset_manifest_plan`。

#### debug_code_with_assets

作用：Coding Agent 拿到真实资源后自调试代码，并修复代码、manifest 和资源引用问题。

输入参数：

| 参数 | 含义 |
| --- | --- |
| `integrated_bundle_context` | 汇合后的代码与资源上下文 |
| `development_brief` | 开发目标 |
| `asset_manifest_plan` | 路径契约 |
| `artifact_workspace` | 文件目录 |

输出更新：

| 字段 | 含义 |
| --- | --- |
| `code_artifacts` | 调试后代码文件清单 |
| `manifest_draft` | 调试后 manifest 草稿 |
| `debug_report` | 自调试结果 |
| `generation_status` | `validating` |

调试范围：

- 检查代码引用的 `assets/*` 是否已由 `processed_assets` 落盘。
- 修复 `manifest_draft.assets` 与真实资源不一致的问题。
- 用本地静态服务或 headless browser 打开入口，检查 JS error、非空画面和 `game_ready`。
- 如果是代码或 manifest 问题，Coding Agent 可以在本节点内自行修复。
- 如果是素材缺失或契约冲突，本节点不打回其他 Agent，只在 `debug_report` 中记录失败原因。

工具边界：

- 只能读写 `artifact_workspace`。
- 不能读写仓库源码、后端配置、前端源码或 `.env`。
- 不能把 API key、presigned URL 签名、token 写入代码、manifest 或日志。

#### validate_final_delivery

作用：Validator Agent 做最终交付验收，不做调试，不做返修。

输入参数：

| 参数 | 含义 |
| --- | --- |
| `integrated_bundle_context` | 汇合后的代码与资源上下文 |
| `debug_report` | Coding Agent 自调试报告 |
| `asset_manifest_plan` | 路径契约 |
| `artifact_workspace` | 文件目录 |

输出更新：

| 字段 | 含义 |
| --- | --- |
| `validation_report` | 最终验收报告 |
| `generation_status` | `succeeded` 或 `failed` |

验收范围：

- 产物协议：`manifest.json`、`index.html`、`style.css`、`game.js` 是否存在。
- manifest 合法：`entry`、`styles`、`scripts`、`assets`、`runtime` 字段是否可用。
- 资源完整：`manifest.assets` 和 `asset_manifest_plan.target_path` 中运行必需资源是否存在。
- 路径安全：所有输出路径都在 `artifact_workspace` 内，且 bundle 内引用路径不越界。
- 安全脱敏：不包含完整 presigned URL、API key、OAuth code、session id、token、password。
- 外部依赖：不依赖外网 CDN 或父页面能力。
- 调试证据：`debug_report` 必须存在，且没有未解决的 JS 启动错误。
- 后端可保存：能产出 `artifact_result` 和 `draft_game_meta` 所需字段。

规则：

- Validator 只判断 `valid / invalid`。
- Validator 不打回 Coding Agent、Asset Agent 或 Orchestrator。
- 验收失败直接进入 `finalize_failure`。

#### finalize_success

作用：生成最终 `artifact_result` 和后端可保存结果。

输出更新：

| 字段 | 含义 |
| --- | --- |
| `status` | `succeeded` |
| `artifact_result` | 产物路径、manifest 路径、入口路径和文件清单 |
| `draft_game_meta` | title、description、tags、cover path |
| `agent_logs` | 完成日志 |

#### finalize_failure

作用：输出结构化失败结果。

输出更新：

| 字段 | 含义 |
| --- | --- |
| `status` | `failed` |
| `failed_step` | 失败步骤 |
| `error_message` | 给用户的失败摘要 |
| `retry_hint` | 重试建议 |
| `validation_report` | 最终验收失败报告 |
| `debug_report` | Coding Agent 自调试报告 |
| `agent_logs` | 脱敏日志 |

### 5.3.4 边定义

| 起点 | 终点 | 类型 | 条件 | 作用 |
| --- | --- | --- | --- | --- |
| `START` | `init_generation_context` | 普通边 | 无 | 初始化生成任务上下文 |
| `init_generation_context` | `build_parallel_contracts` | 普通边 | 无 | 生成并发契约 |
| `build_parallel_contracts` | `fan_out_generation` | 普通边 | 契约有效 | 进入并发分支 |
| `fan_out_generation` | `draft_code` | 并发边 | coding | 生成代码草稿 |
| `fan_out_generation` | `run_asset_agent` | 并发边 | assets | 处理或生成三张图合同 |
| `draft_code` | `join_assets_and_code` | 汇合边 | 代码分支完成 | 等待素材分支 |
| `run_asset_agent` | `join_assets_and_code` | 汇合边 | 素材分支完成 | 等待代码分支 |
| `join_assets_and_code` | `debug_code_with_assets` | 普通边 | 两分支成功 | Coding Agent 自调试 |
| `debug_code_with_assets` | `validate_final_delivery` | 普通边 | 调试完成 | Validator 最终验收 |
| `validate_final_delivery` | `finalize_success` | 条件边 | `valid` | 保存成功结果 |
| `validate_final_delivery` | `finalize_failure` | 条件边 | `invalid` | 保存失败结果 |
| `finalize_success` | `END` | 普通边 | 无 | 结束生成 |
| `finalize_failure` | `END` | 普通边 | 无 | 结束失败 |

### 5.3.5 第二阶段输出契约

成功返回给后端：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `status` | string | `succeeded` |
| `artifact_result.artifact_prefix` | string | 产物目录前缀 |
| `artifact_result.manifest_path` | string | manifest 路径 |
| `artifact_result.entry_path` | string | index.html 路径 |
| `draft_game_meta` | object | draft game 标题、简介、标签、封面 |
| `agent_logs` | object[] | 脱敏日志 |

失败返回给后端：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `status` | string | `failed` |
| `failed_step` | string | 失败步骤 |
| `error_message` | string | 给用户展示的失败摘要 |
| `retry_hint` | string nullable | 重试建议 |
| `validation_report` | object nullable | Validator 最终验收报告 |
| `debug_report` | object nullable | Coding Agent 自调试报告 |
| `agent_logs` | object[] | 脱敏日志 |

## 5.4 revision_graph

`revision_graph` 是生成后聊天修改链路。它只在已有 `generation_job` 进入 `succeeded / failed` 后使用。

推荐结构：

```text
START
  -> load_revision_context
  -> understand_revision_intent
    -> unclear: ask_clarifying_question -> END
    -> clear: build_revision_patch
  -> create_revision_job_payload
  -> END
```

### 5.4.1 State 总览

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `parent_job` | object | 上一版任务摘要 |
| `base_game_plan` | object | 上一版确认的游戏方案 |
| `base_material_usage` | object | 上一版素材用途 |
| `generated_result` | object | 上一版 draft、manifest、artifact 摘要 |
| `user_message` | string | 用户本轮修改消息 |
| `revision_intent` | string | 修改意图摘要 |
| `game_plan_patch` | object | 对 `game_plan` 的补丁 |
| `requires_regeneration` | boolean | 是否需要重新生成 draft |
| `assistant_response` | object | 给前端展示的反馈或澄清问题 |

### 5.4.2 输出示例

```json
{
  "revision_intent": "降低难度",
  "game_plan_patch": {
    "lose_condition": "碰到障碍后扣血，血量归零才失败",
    "style": "保持可爱卡通"
  },
  "requires_regeneration": true,
  "assistant_response": {
    "message": "我会把失败条件调宽松一点，现在开始更新。",
    "suggestions": []
  }
}
```

### 5.4.3 边界

- 明确修改如“把小猫换成兔子”“难度降低一点”“背景改成雪地”应直接生成 patch 并创建 revision job。
- 模糊修改如“改得更好玩一点”“换成我之前说的那个风格”应先追问，不创建任务。
- 不直接热改当前 iframe 里的代码；更稳的做法是创建新的 revision job，重新生成一版 draft。

## 6. Agent 角色定义

## 6.1 Orchestrator

### 角色定位

工作流控制器和第二阶段契约生成者。它负责把第一阶段确认结果翻译成并发可执行的开发文档和素材清单，但不直接写代码、不直接处理素材、不做最终质量评估。

### 核心职责

- 初始化和维护全局 state。
- 决定当前应该调用哪个 Agent。
- 解析 `user_requirements`、`game_plan`、`material_usage` 和 `uploaded_assets`。
- 产出 `development_brief`，明确游戏应该做什么。
- 产出 `asset_work_order`，明确素材应该怎么处理。
- 产出 `asset_manifest_plan`，统一代码引用路径和素材落盘路径。
- 记录阶段日志和失败点。
- 汇总最终输出。

### 不负责

- 不重新发明第一阶段已经确认的玩法方案。
- 不直接编写游戏代码。
- 不直接转码、裁切、生成或复制素材。
- 不替代 Validator 做产物校验。

### 输入

- `job_context`
- `user_requirements`
- `game_plan`
- `material_usage`
- `uploaded_assets`

### 输出

- `development_brief`
- `asset_work_order`
- `asset_manifest_plan`
- `game_spec`
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
- `contract_builder`
- `asset_manifest_planner`
- `result_aggregator`

## 6.2 Design Agent

### 角色定位

面向用户的需求设计顾问。

### 核心职责

- 和用户对话。
- 提出建议和候选玩法。
- 补齐缺失的需求字段。
- 维护 `user_requirements`、`game_plan` 和 `material_usage`。
- 派生 `assistant_response.card`，供用户查看标题、介绍和标签。

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
- `game_card_projector`

## 6.3 Asset Agent

### 角色定位

素材处理与素材生成节点。本周 MVP 只围绕三张图工作：`assets/background.png`、`assets/player.png`、`assets/cover.png`。它按 `asset_work_order` 把这三张图写入 `asset_manifest_plan.target_path`。

### 核心职责

- 处理用户上传素材，使其进入游戏 bundle 的三张图合同。
- 产出主背景图 `assets/background.png`，逻辑分辨率固定为 `1280x720`。
- 产出玩家主角图 `assets/player.png`，逻辑分辨率固定为 `256x256`，并导出为透明底 `RGBA PNG`。
- 产出展示封面图 `assets/cover.png`，逻辑分辨率固定为 `1280x720`，并基于游戏内容和画风独立生成。
- 为 `background.png`、`player.png` 和 `cover.png` 分别生成图片处理 prompt；prompt 由 fixed prompt、game prompt 和 reference prompt 组成。
- fixed prompt 内先声明 system role：生图模型是一位优秀的游戏 UI 设计师，再放当前生图类型的定义。
- `player.png` 使用品红 `#FF00FF` 幕布生成，Asset Agent 后处理负责抠图、居中、缩放和透明通道验收。
- `cover.png` 不从 `assets/background.png` 派生，也不默认叠加 `game_plan.title` 标题文案。
- 当上传素材不足时，优先让 Coding Agent 用代码绘制运行时背景/人物；Asset Agent 仍必须生成独立 `cover.png`。
- 对玩家图执行去底或后处理，并把透明底要求作为可验收合同字段保留给 Validator。
- 输出素材处理结果和风险，不直接修改游戏代码。

### 输入

- `asset_registry`
- `asset_work_order`
- `asset_manifest_plan`
- `artifact_workspace`

### 输出

- `asset_analysis`
- `processed_assets`
- `asset_notes`

### Skills

- 背景图生成或抽帧
- 玩家图裁切与透明底处理
- 独立封面图生成
- 风险识别
- 素材路径对齐

### Tools

- `image_describer`
- `image_transformer`
- `video_keyframe_sampler`
- `background_remover`
- `asset_writer`
- `asset_path_checker`

### 说明

本周 MVP 的图像素材只围绕这三张图。用户上传的视频、音频和通用文件仍可作为规划参考输入，但它们本周不要求直接进入运行时资源。运行时真正依赖的只有 Orchestrator 选择进入 `runtime_asset_paths` 的 `background.png` 和 `player.png`；`cover.png` 是展示素材，由 Asset Agent 独立生成。

## 6.4 Coding Agent

### 角色定位

游戏实现节点，负责静态 Web bundle 生成。

### 核心职责

- 根据 `development_brief` 生成 `index.html`、`style.css`、`game.js`。
- 根据 `asset_manifest_plan` 引用资源目标路径。
- 生成 `manifest_draft`。
- 保证产物是纯静态文件，不依赖本地 React 组件。
- 在真实资源到齐后自调试代码、manifest 和资源引用。

### 输入

- `development_brief`
- `asset_manifest_plan`
- `artifact_workspace`
- `processed_assets`
- `integrated_bundle_context`

### 输出

- `code_artifacts`
- `manifest_draft`
- `debug_report`
- `coding_notes`

### Skills

- HTML5 小游戏生成
- HUD 与交互逻辑实现
- 资源引用组织
- manifest 生成
- 资源到齐后的自调试

### Tools

- `bundle_writer`
- `template_selector`
- `html_generator`
- `css_generator`
- `js_generator`
- `manifest_builder`
- `headless_runtime_checker`
- `asset_reference_checker`

### 说明

Coding Agent 可以先引用 `asset_manifest_plan.target_path` 生成代码草稿；等 Asset Agent 返回真实资源后，再由 Coding Agent 自己执行本地调试并修正代码、manifest 和资源引用。Coding Agent 不负责生成最终素材文件。

## 6.5 Validator Agent

### 角色定位

生成产物的最终质量门禁。

### 核心职责

- 读取 Coding Agent 的 `debug_report`。
- 校验产物协议是否完整。
- 校验入口文件、脚本、样式和资源引用是否存在。
- 校验 manifest 字段。
- 校验路径、安全脱敏、外网依赖和 iframe sandbox 边界。
- 判断最终交付是否可以给后端创建 draft game。
- 给出用户可理解的失败原因和重试提示。
- 不调试代码，不打回其他 Agent 返修。

### 输入

- `integrated_bundle_context`
- `debug_report`
- `asset_manifest_plan`
- `artifact_workspace`

### 输出

- `validation_report`
- `sanitized_error_summary`
- `retry_hint`

### Skills

- 产物协议校验
- 路径一致性校验
- 安全边界检查
- 调试证据检查
- 风险脱敏

### Tools

- `bundle_linter`
- `manifest_validator`
- `path_checker`
- `secret_scanner`
- `external_dependency_checker`
- `error_sanitizer`

## 7. 对话阶段字段设计

第一阶段字段以 [5.2 conversation_graph](#52-conversation_graph) 为准。对话阶段只维护三个业务主状态：`user_requirements`、`game_plan`、`material_usage`，并按需派生 `assistant_response`。游戏卡片不是独立状态，只是 `game_plan.title`、`game_plan.introduction` 和 `game_plan.tags` 的展示投影。

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
| suggestions | string[] | 对当前 AI 提问的简短建议答案 |

`introduction` 由 Design Agent 在其他关键字段完整后总结生成，不要求用户单独撰写简介。

## 7.3 material_usage

这是素材用途计划，用于说明上传素材如何进入游戏设计。

核心字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| assets | object[] | 每个素材的用途计划 |

## 7.4 assistant_response.card

这是给用户看的游戏卡片，由 `game_plan` 直接派生。

建议字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| plan_id | string | 对应 `game_plan.plan_id` |
| title | string | 游戏标题 |
| introduction | string | 游戏介绍 |
| tags | string[] | 标签 |

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

## 8.4 development_brief

`development_brief` 是 Coding Agent 的主输入，由 Orchestrator 生成。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| title | string | 游戏标题 |
| gameplay_goal | string | 玩家目标 |
| core_loop | string[] | 主循环 |
| win_condition | string | 胜利条件 |
| lose_condition | string | 失败条件 |
| controls | string | 输入说明 |
| scene_layout | string | 场景布局，需体现 `1280x720` 逻辑分辨率 |
| entities | string[] | 玩家、障碍、目标等实体 |
| ui_hud | string[] | UI 元素 |
| allowed_asset_paths | string[] | 允许引用的 `assets/*` 路径 |
| technical_constraints | string[] | 单页、无外网、iframe sandbox 等约束 |

本周 MVP 约束：

- `allowed_asset_paths` 只包含 `assets/background.png`、`assets/player.png`、`assets/cover.png` 中由 Orchestrator 规划的路径，其中 `assets/cover.png` 必须始终存在。
- `scene_layout` 必须体现逻辑分辨率按当前游戏面板收口为 `1280x720`。
- `technical_constraints` 至少包含静态 HTML5、iframe sandbox 和等比缩放约束。

## 8.5 asset_work_order

`asset_work_order` 是 Asset Agent 的主输入，由 Orchestrator 生成。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| uploaded_asset_tasks | object[] | 用户上传素材的处理任务 |
| generated_asset_tasks | object[] | 缺失资源或生成资源任务 |

`uploaded_asset_tasks[]` 建议字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| asset_id | string | 运行时资源 ID |
| source_asset_id | string | 上传素材 ID |
| target_path | string | 输出路径，必须来自 `asset_manifest_plan` |
| usage | string | 在游戏中的用途 |
| transform | string | 处理方式，例如去底、抽帧、裁切、缩放 |
| required | boolean | 是否为运行必须资源 |

`generated_asset_tasks[]` 建议字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| key | string | 任务键 |
| target_path | string | 输出路径，必须来自 `asset_manifest_plan` |
| usage | string | 用途 |
| generation_mode | string | 生成方式 |
| required | boolean | 是否必须产出 |

本周 MVP 规则：

- 任务只围绕三张图。
- `background.png` 和 `player.png` 可来自上传素材或直接生成。
- `cover.png` 必须是独立生成任务，来源是游戏内容、画风和可用参考素材，不从 `background.png` 派生，不默认叠加标题。
- 如果用户没有上传素材，也必须规划 `cover.png`；`background.png` 和 `player.png` 可按游戏需要改由代码绘制。

## 8.6 asset_manifest_plan

`asset_manifest_plan` 是 Coding Agent 和 Asset Agent 的共享契约。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| asset_id | string | 稳定资源键 |
| target_path | string | bundle 内目标路径，如 `assets/player.png` |
| kind | string | 本周固定为 `image` |
| required | boolean | 是否必须产出 |
| source | string | uploaded / generated / fallback |
| runtime_required | boolean | 缺失时游戏是否不可运行 |
| display_only | boolean | 是否只用于展示，不是运行时强依赖 |
| logical_width | number | 逻辑宽度 |
| logical_height | number | 逻辑高度 |
| alpha_required | boolean | 是否要求透明背景 |
| background | string | `scene / transparent` 等背景要求 |
| fit | string | `cover / contain` 等适配方式 |
| derived_from | string | 派生来源；独立生成的封面为空 |
| title_source | string | 标题来源；独立生成的封面为空 |

规则：

- `development_brief.allowed_asset_paths` 必须来自 `asset_manifest_plan.target_path`。
- `asset_work_order.*.target_path` 必须来自 `asset_manifest_plan.target_path`。
- Validator 以 `asset_manifest_plan` 判断代码引用和真实资源是否对齐。

本周 MVP 目标清单：

| target_path | runtime_required | display_only | logical size | alpha_required | 说明 |
| --- | --- | --- | --- | --- | --- |
| `assets/background.png` | `true` | `false` | `1280x720` | `false` | 游戏主背景图 |
| `assets/player.png` | `true` | `false` | `256x256` | `true` | 玩家主角图，必须透明底 |
| `assets/cover.png` | `false` | `true` | `1280x720` | `false` | 独立展示封面，按游戏内容和画风生成 |

## 8.7 game_spec

`game_spec` 是 Orchestrator 从 `development_brief` 派生的结构化实现规格。它可以作为内部辅助字段存在，但第二阶段的并发契约以 `development_brief`、`asset_work_order` 和 `asset_manifest_plan` 为准。

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

## 8.8 code_artifacts

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| files | object[] | 代码文件清单 |
| referenced_asset_paths | string[] | 代码实际引用的素材路径 |
| manifest_draft | object | 初版 manifest |
| coding_notes | string[] | 实现说明和限制 |

## 8.9 processed_assets

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| asset_key | string | 对应 `asset_manifest_plan.asset_key` |
| source_asset_id | string nullable | 来源上传素材 ID |
| target_path | string | 实际落盘路径 |
| media_type | string | image / video / audio / file |
| operation | string | copy / transform / keyframe / transcribe / summarize / convert / generate / reference |
| status | string | succeeded / failed / reference_only |
| notes | string[] | 处理说明 |

## 8.10 artifact_result

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| artifact_prefix | string | 产物目录前缀 |
| manifest_path | string | manifest 路径 |
| entry_path | string | index.html 路径 |
| files | string[] | 产物文件清单 |
| cover_path | string nullable | 封面路径 |

## 8.11 validation_report

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| valid | boolean | 是否通过 |
| failed_step | string nullable | 失败步骤 |
| issues | object[] | 详细问题 |
| protocol_check | object | 文件协议和 manifest 检查 |
| asset_check | object | 资源路径和 `asset_manifest_plan` 对齐检查 |
| security_check | object | secret、外链、路径越界和 sandbox 边界检查 |
| debug_evidence_check | object | Coding Agent `debug_report` 证据检查 |
| error_message | string nullable | 给用户的失败摘要 |
| retry_hint | string nullable | 重试提示 |

## 8.12 debug_report

`debug_report` 由 Coding Agent 产出，用于说明它在真实资源到齐后如何调试代码。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| attempted | boolean | 是否执行过自调试 |
| runtime_check | object | 本地运行检查结果，如 JS error、画面非空、game_ready |
| asset_reference_check | object | 代码和 manifest 资源引用检查 |
| fixed_issues | object[] | Coding Agent 已修复的问题 |
| unresolved_issues | object[] | 仍未解决的问题 |
| notes | string[] | 调试说明 |

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
- `transform_image(path_or_bytes, target_spec)`：图片裁切、压缩或格式转换。
- `sample_video_frames(path_or_bytes)`：视频抽帧。
- `read_video_metadata(path_or_bytes)`：读取视频时长、尺寸、编码等信息。
- `transcribe_audio(path_or_bytes)`：音频转写。
- `read_audio_metadata(path_or_bytes)`：读取音频时长、格式、声道等信息。
- `convert_audio(path_or_bytes, target_spec)`：音频格式转换或短音效替代。
- `summarize_file(path_or_bytes)`：通用文件摘要；不可读文件只输出元信息。
- `project_game_card(game_plan)`：从 `game_plan` 派生展示卡片。
- `build_parallel_contracts(inputs)`：生成 `development_brief`、`asset_work_order` 和 `asset_manifest_plan`。
- `write_artifact_file(path, content)`：写文件。
- `copy_or_bind_asset(asset, target_path)`：复制或绑定素材。
- `build_manifest(bundle_context)`：生成 manifest。
- `validate_bundle(bundle_dir)`：校验 bundle。
- `run_headless_runtime_check(entry_path)`：Coding Agent 打开入口并检查 JS error、非空画面和 `game_ready`。
- `check_asset_references(bundle_context)`：Coding Agent 检查代码、manifest 和真实资源引用。
- `scan_bundle_secrets(bundle_dir)`：Validator 检查输出是否包含敏感信息。
- `check_external_dependencies(bundle_dir)`：Validator 检查是否依赖外网资源。
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
- `parallel_contract_authoring`
- `html5_bundle_generation`
- `manifest_authoring`
- `bundle_validation`
- `runtime_debugging`
- `delivery_validation`
- `error_summarization`

建议关系：

- `Design Agent` 持有前 3 个 skill。
- `Orchestrator` 持有 `parallel_contract_authoring`。
- `Asset Agent` 持有 `multimodal_asset_understanding`、`asset_usage_mapping` 和轻量资源生成能力。
- `Coding Agent` 持有 `html5_bundle_generation`、`manifest_authoring` 和 `runtime_debugging`。
- `Validator Agent` 持有 `bundle_validation`、`delivery_validation` 和 `error_summarization`。

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

1. 先打通 `Design Agent -> user_requirements + game_plan + material_usage -> assistant_response.card`。
2. 再打通 `Orchestrator -> development_brief + asset_work_order + asset_manifest_plan`。
3. 再打通 `Asset Agent -> processed_assets + asset_analysis`，稳定产出 `background.png`、`player.png`、`cover.png`。
4. 再打通 `Coding Agent -> code_artifacts + manifest_draft`。
5. 再打通 `join_assets_and_code -> debug_code_with_assets`，让 Coding Agent 拿到真实素材后自调试。
6. 最后打通 `validate_final_delivery -> validation_report`，让 Validator Agent 做最终验收。

本地最小验收标准：

- 输入一段 prompt；如需验证多模态上传，可额外带图片、视频、音频、通用文件样本，但本周运行时只验三张图输出。
- 经过对话阶段得到完整游戏方案和游戏卡片。
- 用户确认后能生成一套完整 bundle。
- 产物包含 `manifest.json`、`index.html`、`style.css`、`game.js`。
- `assets/*` 中包含 `asset_manifest_plan` 要求的运行资源。
- Coding Agent 产出 `debug_report`，并证明资源引用、JS 启动和 `game_ready` 已检查。
- Validator 只做最终交付验收，并返回 `valid=true`。

## 14. 与现有后端对接方式

后端最终只需要关心一个统一 runner：

- 输入：
  - `job_id`
  - `user_id`
  - `prompt`
  - `user_requirements`
  - `game_plan`
  - `material_usage`
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

- 前端确认前与 `Create Sessions API` 和 `Uploads API` 交互，确认后通过 `Jobs API` 创建后台生成任务。
- 后端需要维护确认前 `create_sessions`，以及确认后的 `generation_jobs`、`agent_logs`、`games`。
- `generation_jobs` 必须保存 `create_session_id`，Jobs 查询必须返回 `session_id`，用于前端点击历史任务时恢复对应对话。
- 生成后修改通过 revision job 接入，后端保存 `parent_job_id` 和 `revision_intent`，不覆盖旧产物。
- Agent 目录只作为独立执行器，不直接侵入前后端代码。

## 15. MVP 范围与非目标

## 15.1 本期建议纳入

- Design Agent 对话收敛
- Orchestrator 并发契约生成
- Asset Agent 稳定处理三张图合同
- Coding Agent 生成静态小游戏并在素材到齐后自调试
- Validator Agent 做最终交付验收
- revision_graph 或 revision mode 最小契约
- LangGraph 编排
- Mock provider 和 OpenAI-compatible provider

## 15.2 本期不建议强做

- 多轮自动 retry
- 超过 Coding/Asset 并发分支以外的复杂子任务调度
- 大规模音视频再生成
- 内容审核 Agent
- 成本优化 Agent
- 资源配额 Agent
- 完整版本管理 UI 和 Remix

## 16. 推荐实施顺序

建议顺序：

1. 先在独立 `agent/` 目录实现 `conversation_graph`。
2. 再实现 `generation_graph` 的 Orchestrator 契约节点。
3. 再实现 Asset/Coding 并发分支的 mock provider 版本。
4. 再实现 Coding Agent 资源到齐后的自调试。
5. 再实现 Validator 最终交付验收。
6. 再补 `revision_graph` 或 revision mode 最小契约。
7. 再补 OpenAI-compatible provider。
8. 最后再接回后端 `Agent Runner`。

## 17. 最终判断

本方案判断如下：

- `Design Agent + Asset Agent + Coding Agent + Validator Agent + Orchestrator` 的方向是合理的。
- 为了避免需求和实现之间出现语义断层，第二阶段必须由 Orchestrator 先生成 `development_brief`、`asset_work_order` 和 `asset_manifest_plan`，不再另设独立 `Spec Builder Agent`。
- 为了保留并发能力又不牺牲调试能力，Coding Agent 和 Asset Agent 并发执行；资源到齐后由 Coding Agent 自调试，Validator Agent 只做最终交付验收。
- 如果按本文档实施，可以先在独立 `agent/` 目录把“从对话到 manifest”的全流程打通，再决定如何接回现有系统。
