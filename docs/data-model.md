# AI Native 互动游戏平台 MVP 数据模型

## 1. 文档目标

本文档从 [design-document.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/design-document.md) 中摘出数据模型相关内容，单独整理核心业务模型、字段职责、关键约束和关系说明，便于交付时单独查阅。

产品级上下文仍以 [design-document.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/design-document.md) 为准；接口字段以 [api-contract.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/api-contract.md) 为准。

## 2. 核心模型列表

| 模型 | 作用 | 核心关系 |
| --- | --- | --- |
| `users` | 平台用户主表 | 被 `oauth_accounts`、`sessions`、`games`、`generation_jobs`、`create_sessions`、`uploaded_assets`、`play_events` 引用 |
| `oauth_accounts` | 第三方登录绑定表 | 关联 `users.user_id`，支持 Google / GitHub |
| `sessions` | 服务端登录态 | 关联 `users.user_id`，承载 httpOnly session |
| `games` | 游戏主表 | 关联创建者、发布状态、manifest 和统计信息 |
| `game_likes` | 游戏点赞记录 | 关联 `games.id` 与 `users.user_id` |
| `generation_jobs` | 生成任务表 | 关联 `users`、`games`、`create_sessions`，保存生成快照与状态 |
| `create_sessions` | Create 对话会话表 | 关联 `users`，承载确认前方案状态 |
| `create_session_messages` | Create 消息历史表 | 关联 `create_sessions.id`，恢复完整聊天气泡 |
| `uploaded_assets` | 上传素材表 | 关联 `users`，并可绑定 `create_sessions` 或 `generation_jobs` |
| `agent_logs` | Agent 执行日志表 | 关联 `generation_jobs.id` |
| `play_events` | 游玩埋点表 | 关联 `games.id`，可选关联 `users.user_id` |

## 3. 身份与会话模型

系统唯一身份以 `users.user_id` 为准，而不是 email。OAuth 登录时，首次登录会同时创建 `users` 和 `oauth_accounts`；再次登录通过 `(provider, provider_user_id)` 找回同一个 `user_id`。

### 3.1 users

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `user_id` | uuid | 系统唯一用户 ID，主键 |
| `email` | varchar nullable | 用户邮箱，不作为系统唯一身份 |
| `password_hash` | varchar nullable | 邮箱注册用户的密码哈希；OAuth-only 用户为空 |
| `display_name` | varchar nullable | 展示名，默认取邮箱前缀或第三方展示名 |
| `avatar_url` | text nullable | 头像 URL |
| `created_at` | timestamp | 创建时间 |
| `updated_at` | timestamp | 更新时间 |

约束：

- 系统身份唯一标识是 `user_id`，不是 email。
- `email` 不作为外键，也不作为系统主键。
- 邮箱注册场景中，本地密码账号不允许重复使用同一个 email。
- OAuth-only 用户允许 `password_hash = null`。

### 3.2 oauth_accounts

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `oauth_id` | uuid | OAuth 绑定 ID，主键 |
| `user_id` | uuid | 外键，关联 `users.user_id` |
| `provider` | varchar | `google / github` |
| `provider_user_id` | varchar | 第三方平台用户唯一 ID |
| `provider_email` | varchar | 第三方平台返回邮箱 |
| `provider_name` | varchar | 第三方平台展示名 |
| `avatar_url` | text | 第三方头像 URL |
| `access_token_encrypted` | text nullable | 加密后的访问令牌；MVP 可不长期保存 |
| `refresh_token_encrypted` | text nullable | 加密后的刷新令牌；MVP 可不长期保存 |
| `created_at` | timestamp | 绑定时间 |
| `updated_at` | timestamp | 更新时间 |

约束：

- `(provider, provider_user_id)` 唯一。
- 同一个用户可以绑定多个 provider。
- 第三方 token 不允许明文存储；如果 MVP 不需要调用第三方 API，登录后可以只保存 provider identity，不保存 access token。
- Google email 与已有邮箱注册账号相同且 `email_verified=true` 时，自动绑定到已有 `user_id`。
- Google email 相同但 Google `provider_user_id` 不同，不自动合并，避免误绑。
- OAuth-only 用户不能使用邮箱密码登录，除非后续实现设置密码。

### 3.3 sessions

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `session_id` | uuid | session ID，主键 |
| `user_id` | uuid | 外键，关联 `users.user_id` |
| `expires_at` | timestamp | 过期时间 |
| `last_seen_at` | timestamp nullable | 最近访问时间 |
| `user_agent` | text nullable | 登录设备 UA |
| `ip_address` | varchar nullable | 登录 IP |
| `created_at` | timestamp | 创建时间 |

## 4. 游戏与任务模型

### 4.1 games

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | uuid | 游戏 ID |
| `owner_id` | uuid | 创建者 |
| `title` | varchar | 游戏标题 |
| `description` | text | 简介 |
| `cover_url` | text | 封面 URL |
| `tags` | text[] | 标签 |
| `status` | varchar | `draft / published / deleted` |
| `manifest_url` | text | manifest public 或授权 URL |
| `artifact_base_url` | text | 产物基础 URL |
| `play_count` | integer | 游玩次数 |
| `like_count` | integer | 点赞次数 |
| `published_at` | timestamp | 发布时间 |
| `created_at` | timestamp | 创建时间 |
| `updated_at` | timestamp | 更新时间 |

### 4.2 game_likes

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | uuid | 点赞记录 ID |
| `game_id` | uuid | 游戏 ID |
| `user_id` | uuid | 点赞用户 ID，关联 `users.user_id` |
| `created_at` | timestamp | 点赞时间 |

约束：

- 点赞必须登录。
- 同一用户对同一游戏最多点赞一次，使用 `(game_id, user_id)` 唯一约束。
- MVP 点赞只做新增点赞，不做取消点赞。

### 4.3 generation_jobs

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | uuid | 任务 ID |
| `user_id` | uuid | 创建者 |
| `prompt` | text | 用户创意 |
| `status` | varchar | `pending / running / succeeded / failed` |
| `create_session_id` | uuid nullable | 关联 Create 对话会话；新任务必须写入，历史任务可为空 |
| `parent_job_id` | uuid nullable | 生成后修改时指向上一版任务；初始生成为空 |
| `revision_intent` | text nullable | 生成后修改意图摘要；初始生成为空 |
| `user_requirements` | jsonb | 确认时用户需求快照 |
| `game_plan` | jsonb | 确认时游戏方案快照 |
| `material_usage` | jsonb | 确认时素材用途快照 |
| `game_id` | uuid | 成功后关联 draft game |
| `artifact_prefix` | text | 产物对象存储路径 |
| `error_message` | text | 失败原因 |
| `created_at` | timestamp | 创建时间 |
| `started_at` | timestamp | 开始时间 |
| `finished_at` | timestamp | 结束时间 |

约束：

- 新建生成任务必须由 confirmed `create_session` 创建，并写入 `create_session_id`。
- `GET /api/jobs` 和 `GET /api/jobs/{job_id}` 必须返回 `session_id` 或 `create_session_id`，用于前端恢复历史任务的聊天上下文。
- 生成后修改必须创建新的 revision job，不覆盖原 job、原 draft 或原始 `create_session` 快照。

## 5. Create 对话与素材模型

### 5.1 create_sessions

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | uuid | Create 对话会话 ID |
| `user_id` | uuid | 创建者 |
| `status` | varchar | `collecting / ready_to_confirm / confirmed / error` |
| `user_requirements` | jsonb | 用户需求摘要 |
| `game_plan` | jsonb | 当前完整游戏方案 |
| `material_usage` | jsonb | 素材用途计划，只维护 `assets` |
| `assistant_response` | jsonb | 最近一轮 AI 回复、建议答案和卡片 |
| `created_at` | timestamp | 创建时间 |
| `updated_at` | timestamp | 更新时间 |
| `confirmed_at` | timestamp nullable | 用户点击生成并确认当前方案的时间 |

约束：

- `POST /api/create-sessions` 创建新会话，不恢复旧会话。
- `GET /api/create-sessions/{session_id}` 读取已存在会话，用于刷新页面、点击历史任务和任务回看。
- `assistant_response` 只代表最近一轮 AI 回复；完整聊天气泡必须来自 `create_session_messages` 或等价消息历史字段。

### 5.2 create_session_messages

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | uuid | 消息 ID |
| `session_id` | uuid | 关联 Create 对话会话 |
| `role` | varchar | `user / assistant / system` |
| `content` | text | 消息正文 |
| `payload` | jsonb nullable | 建议答案、卡片快照、附件摘要、事件类型等展示补充 |
| `created_at` | timestamp | 消息创建时间 |

约束：

- 消息按 `created_at` 正序返回给前端，用于渲染聊天气泡。
- 用户消息和 AI 消息都必须归属同一个 `session_id`。
- 附件消息只保存安全元信息，不保存完整 presigned URL 签名。
- `confirm`、`regenerate`、`upload_assets` 等事件可以通过 `payload.event_type` 标注，方便历史回看。

### 5.3 uploaded_assets

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | uuid | 上传素材 ID |
| `user_id` | uuid | 上传者 |
| `session_id` | uuid nullable | 关联 Create 对话会话；文件可先上传，进入会话后再绑定 |
| `job_id` | uuid nullable | 关联生成任务；文件可先上传，创建任务后再绑定 |
| `filename` | varchar | 原始文件名 |
| `mime_type` | varchar | MIME type |
| `size_bytes` | bigint | 文件大小 |
| `object_key` | text | MinIO object key |
| `purpose` | text | 用户填写或系统推断的用途说明 |
| `created_at` | timestamp | 上传时间 |

## 6. 运行观测模型

### 6.1 agent_logs

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | uuid | 日志 ID |
| `job_id` | uuid | 任务 ID |
| `step` | varchar | 步骤名 |
| `level` | varchar | `info / warning / error` |
| `message` | text | 可读日志摘要 |
| `created_at` | timestamp | 记录时间 |

### 6.2 play_events

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | uuid | 事件 ID |
| `game_id` | uuid | 游戏 ID |
| `user_id` | uuid nullable | 登录用户可记录，游客为空 |
| `event_type` | varchar | `view / manifest_loaded / started / failed / timeout / exited` |
| `metadata` | jsonb | 阶段、耗时、错误原因、URL 类型等；不记录 secret |
| `created_at` | timestamp | 事件时间 |

## 7. 关键关系与约束

- `users.user_id` 是系统唯一身份，`email` 不是主键。
- `oauth_accounts` 用于第三方身份绑定，支持一个用户绑定多个 provider。
- `create_sessions` 与 `generation_jobs` 分别对应确认前对话阶段和确认后后台生成阶段。
- `generation_jobs.create_session_id` 必须能反查生成任务对应的历史会话。
- `uploaded_assets` 支持“先上传、后绑定会话/任务”的流程。
- `games` 保存最终对外展示与 Play 加载所需的发布元数据。
- `agent_logs` 和 `play_events` 承担任务执行和游玩可观测性记录。

## 8. 相关阅读

- 产品边界与业务状态： [design-document.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/design-document.md)
- 接口字段与响应契约： [api-contract.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/api-contract.md)
- Agent 编排与状态流： [agent-orchestration-design.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/agent-orchestration-design.md)
