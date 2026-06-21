# 前后端 API 契约

## 1. 契约目标

本文档定义 MVP 前后端并行开发的 HTTP API 契约。页面行为以 [pages-design.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/pages-design.md) 为准，产品边界以 [design-document.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/design-document.md) 为准。

通用约定：

- API base URL 由前端环境变量配置。
- 认证使用服务端 session 和 `httpOnly` cookie。
- 前端请求需要携带 cookie。
- 成功响应使用 JSON。
- 错误响应统一为 `{"error":{"code":"string","message":"string","retry_hint":"string|null"}}`。
- 不在任何响应、Console 或日志中暴露 password、session id、OAuth code、access token、refresh token、API key 或完整 presigned URL 签名。

## 2. 通用状态码

| 状态码 | 含义 | 前端处理 |
| --- | --- | --- |
| 200 | 请求成功 | 正常渲染或更新状态 |
| 201 | 创建成功 | 写入本地状态并输出 Console |
| 204 | 无响应体成功 | 用于退出登录等动作 |
| 400 | 请求参数错误 | Error 弹窗或表单错误 |
| 401 | 未登录 | 打开 Auth Modal |
| 403 | 无权限 | Error 弹窗，提示切换账号或返回 |
| 404 | 资源不存在 | Error 弹窗，提供返回 Home |
| 409 | 状态冲突 | Error 弹窗，提示刷新或重试 |
| 413 | 文件过大 | Error 弹窗，提示重新选择文件 |
| 422 | 字段校验失败 | 表单错误或 Error 弹窗 |
| 500 | 服务端异常 | Error 弹窗，提示稍后重试 |
| 503 | 依赖不可用 | Error 弹窗，提示稍后重试 |

## 3. Auth API

### POST `/api/auth/register`

权限：公开。

请求字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| email | string | 是 | 邮箱 |
| password | string | 是 | 密码 |

成功响应：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| user.user_id | string | 用户 ID |
| user.email | string nullable | 邮箱 |
| user.display_name | string nullable | 展示名 |
| user.avatar_url | string nullable | 头像 |

验证要点：

- 成功后写入 `httpOnly` session cookie。
- 重复邮箱返回 409 或 400，错误信息明确。

### POST `/api/auth/login`

权限：公开。

请求字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| email | string | 是 | 邮箱 |
| password | string | 是 | 密码 |

成功响应同注册。

验证要点：

- 密码错误返回 401。
- OAuth-only 用户使用邮箱密码登录时返回明确错误。
- 成功后写入 `httpOnly` session cookie。

### POST `/api/auth/logout`

权限：登录。

成功响应：204。

验证要点：

- 服务端 session 失效。
- 前端头像恢复默认头像，昵称区域恢复为 `登录`。

### GET `/api/auth/me`

权限：公开。

成功响应：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| authenticated | boolean | 是否已登录 |
| user | object nullable | 已登录时返回用户摘要 |

未登录时返回 `authenticated=false`，不弹 Error。

### GET `/api/auth/oauth/google/start`

权限：公开。

行为：

- 后端生成 OAuth state。
- 设置 state cookie。
- 返回 Google 授权跳转地址或直接 302 跳转。

前端处理：

- 点击 Google 登录后进入授权流程。
- 不在前端处理 Google client secret。

### GET `/api/auth/oauth/google/callback`

权限：公开回调。

行为：

- 校验 state。
- 换取 token。
- 获取 Google 用户信息。
- 创建或绑定 `users` 与 `oauth_accounts`。
- 写入 session。
- 重定向回前端。

验证要点：

- 首次 Google 登录创建 `users` 与 `oauth_accounts`。
- 再次 Google 登录复用同一 `user_id`。
- 回调失败展示 Error。

### GET `/api/auth/oauth/github/start`

权限：公开。

MVP 行为：返回未启用错误或 disabled 状态。GitHub 真实登录放后续版本。

## 4. Games API

### GET `/api/games`

权限：公开。

查询参数：

| 参数 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| sort | string | `latest` | `latest / play_count / like_count` |
| q | string | 空 | 搜索标题、简介或作者 |
| tag | string | 空 | 标签筛选 |

成功响应：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| games | array | 游戏卡片列表 |
| total | number | 返回数量 |

`games[]` 字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 游戏 ID |
| title | string | 标题 |
| description | string | 简介，Home 默认 hover 展示 |
| cover_url | string | 封面 URL |
| author.display_name | string | 作者展示名 |
| tags | string[] | 标签 |
| published_at | string | ISO 时间 |
| play_count | number | 游玩次数 |
| like_count | number | 点赞次数 |
| liked_by_me | boolean | 登录用户是否已点赞；未登录为 false |

验证要点：

- 只返回 `published` 游戏。
- 支持最新发布、最多游玩、最多点赞排序。
- 支持搜索和标签筛选。

### GET `/api/games/{game_id}`

权限：published 公开；draft 仅 owner。

成功响应字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 游戏 ID |
| status | string | `draft / published` |
| title | string | 标题 |
| description | string | 简介 |
| cover_url | string | 封面 URL |
| author.display_name | string | 作者展示名 |
| tags | string[] | 标签 |
| published_at | string nullable | 发布时间 |
| play_count | number | 游玩次数 |
| like_count | number | 点赞次数 |
| liked_by_me | boolean | 登录用户是否已点赞 |
| manifest_url | string | manifest URL |
| artifact_base_url | string | 产物基础 URL |

验证要点：

- 游客可读取 published。
- 游客不可读取 draft。
- owner 可读取自己的 draft 预览。

### POST `/api/games/{game_id}/like`

权限：登录。

请求体：空。

成功响应：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| game_id | string | 游戏 ID |
| like_count | number | 更新后的点赞数 |
| liked_by_me | boolean | 固定为 true |

验证要点：

- 未登录返回 401，前端弹 Auth Modal。
- 同一用户重复点赞不增加计数，可返回 200 和当前状态。
- MVP 不做取消点赞。

### POST `/api/games/{game_id}/publish`

权限：owner。

请求体：空。

成功响应：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| game_id | string | 游戏 ID |
| status | string | `published` |
| manifest_url | string | public-read manifest URL |
| published_at | string | 发布时间 |

验证要点：

- 只能发布自己的 draft。
- 成功后 Home 列表能查询到该游戏。
- Publish 过程中前端按钮显示 loading。

### DELETE `/api/games/{game_id}`

权限：owner。

MVP 范围：只允许删除自己的 draft 或任务产物，采用逻辑删除；published 删除或下架放后续。

## 5. Uploads API

### POST `/api/uploads/presign`

权限：登录。

请求字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| filename | string | 是 | 原始文件名 |
| mime_type | string | 是 | MIME type |
| size_bytes | number | 是 | 文件大小 |

成功响应：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| upload_id | string | 上传记录 ID |
| object_key | string | MinIO object key |
| upload_url | string | presigned URL |
| expires_in | number | 秒 |

验证要点：

- 支持任意文件类型。
- 单文件最大 `20MB`。
- 未登录返回 401。

### POST `/api/uploads/complete`

权限：登录。

请求字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| upload_id | string | 是 | 上传记录 ID |
| object_key | string | 是 | MinIO object key |
| filename | string | 是 | 原始文件名 |
| mime_type | string | 是 | MIME type |
| size_bytes | number | 是 | 文件大小 |

成功响应：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| asset_id | string | 素材 ID |
| filename | string | 文件名 |
| mime_type | string | MIME type |
| size_bytes | number | 文件大小 |

验证要点：

- 文件可以先上传，创建任务时再绑定到 `generation_job`。
- 前端在聊天框下方展示文件列表。

## 6. Create Sessions API

Create Session 是确认前对话会话，负责承载 `conversation_graph` 的 `chat / upload_assets / regenerate / confirm` 事件。它不等同于 `generation_job`；只有用户点击 `生成` 且会话进入 `confirmed` 后，前端才调用 Jobs API 创建后台生成任务。Confirmed 会话仍必须可读，用于历史任务回看和恢复当时的对话上下文。

`POST /api/create-sessions` 只创建新会话；恢复历史任务对话必须通过任务返回的 `session_id` 调用 `GET /api/create-sessions/{session_id}`。如果要恢复完整聊天气泡，响应必须包含消息历史；只返回最近一轮 `assistant_response` 不足以渲染完整对话流。

### POST `/api/create-sessions`

权限：登录。

请求字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| initial_message | string | 否 | 用户进入 Create 后的首条创意文本 |
| asset_ids | string[] | 否 | 已上传但尚未绑定任务的素材 ID |

成功响应：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| session_id | string | Create 对话会话 ID |
| conversation_status | string | `collecting / ready_to_confirm / confirmed / error` |
| user_requirements | object | 用户需求摘要 |
| game_plan | object nullable | 当前完整游戏方案 |
| material_usage | object | 素材用途计划，只包含 `assets` |
| assistant_response | object | AI 回复、建议答案和卡片 |
| messages | array | 当前会话消息历史，按时间正序 |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |

验证要点：

- 本接口只用于创建新会话。
- 点击历史任务或刷新历史任务时不得调用本接口创建新会话。

### POST `/api/create-sessions/{session_id}/events`

权限：owner。

请求字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| type | string | 是 | `chat / upload_assets / regenerate / confirm` |
| message | string | 条件必填 | 用户本轮自然语言输入；`chat` 时必填 |
| uploaded_assets | object[] | 否 | 本轮可见素材元信息；`upload_assets` 时通常传入 |
| selected_plan_id | string | 否 | 点击 `生成` 或 `换一换` 时对应的方案 ID |

`uploaded_assets[]` 字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| asset_id | string | 素材 ID |
| filename | string | 原始文件名 |
| mime_type | string | MIME type |
| size_bytes | number | 文件大小 |
| object_key | string | 对象存储 key；不向模型或日志暴露完整 presigned URL |
| user_hint | string nullable | 用户对素材用途的说明 |

成功响应：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| session_id | string | Create 对话会话 ID |
| conversation_status | string | 当前对话状态 |
| user_requirements | object | 用户需求摘要 |
| game_plan | object nullable | 当前完整游戏方案 |
| material_usage | object | 素材用途计划，只包含 `assets` |
| assistant_response.message | string | AI 回复 |
| assistant_response.suggestions | string[] | 对当前 AI 提问的简短建议答案 |
| assistant_response.card | object nullable | 游戏卡片，由 `game_plan` 派生 |
| assistant_response.actions | string[] | 可用动作，如 `generate / regenerate` |
| messages | array | 更新后的会话消息历史，按时间正序 |
| handoff_to_generation | boolean | `confirm` 成功后为 `true` |
| updated_at | string | 更新时间 |

`assistant_response.card` 字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| plan_id | string | 对应 `game_plan.plan_id` |
| title | string | 游戏标题 |
| introduction | string | 游戏介绍 |
| tags | string[] | 标签 |

验证要点：

- 每个 `chat` 事件至少追加一条用户消息和一条 AI 消息。
- `upload_assets / regenerate / confirm` 事件需要追加可回看的事件消息或在最近消息 `payload.event_type` 中记录。
- `assistant_response.suggestions` 必须是字符串列表，不是对象列表。
- `assistant_response.card` 只包含 `plan_id / title / introduction / tags`。
- `regenerate` 必须保持已有 `user_requirements.must_have`、`constraints` 和 `material_usage.assets`。
- `confirm` 成功后返回 `handoff_to_generation=true`，但本接口不创建 `generation_job`。
- 不在响应中返回完整 presigned URL、session id、API key、token 或 secret。

### GET `/api/create-sessions/{session_id}`

权限：owner。

成功响应：与 `POST /api/create-sessions/{session_id}/events` 成功响应一致，但不触发新的 Agent 事件。

`messages[]` 字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 消息 ID |
| role | string | `user / assistant / system` |
| content | string | 消息正文 |
| payload | object nullable | 建议答案、卡片快照、附件摘要、事件类型等展示补充 |
| created_at | string | ISO 时间 |

验证要点：

- 只允许 owner 获取。
- 刷新 Create 页面或点击历史任务后，前端通过该接口恢复当前 `user_requirements`、`game_plan`、`material_usage`、最近一轮 `assistant_response` 和完整 `messages`。
- 本接口只能读取旧会话，不创建新会话。

## 7. Jobs API

### POST `/api/jobs`

权限：登录。

请求字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| session_id | string | 是 | 已确认的 Create 对话会话 ID |
| prompt | string | 否 | 原始自然语言创意摘要；可由 `user_requirements.intent_summary` 派生 |

成功响应：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| job_id | string | 任务 ID |
| session_id | string | 关联的 Create 对话会话 ID |
| status | string | `pending` |
| created_at | string | 创建时间 |

验证要点：

- 只有 `session_id` 对应会话为 `confirmed` 时才能创建任务。
- 后端从 confirmed `create_session` 读取 `user_requirements`、`game_plan`、`material_usage` 快照，不信任前端重复提交这些字段。
- 新创建任务必须保存 `session_id`，供任务历史反查对应 `create_session`。
- 支持并发创建多个任务。
- 单任务最多绑定 `5` 个文件。
- 创建后可离开页面，回来通过任务历史继续查看。

### GET `/api/jobs`

权限：登录。

成功响应：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| jobs | array | 当前用户任务列表 |

`jobs[]` 字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| job_id | string | 任务 ID |
| session_id | string nullable | 关联 Create 对话会话 ID；历史任务可为空 |
| parent_job_id | string nullable | revision job 的上一版任务 ID；初始任务为空 |
| title | string | 任务名，可取确认卡片标题 |
| status | string | `pending / running / succeeded / failed` |
| created_at | string | 创建时间 |
| started_at | string nullable | 开始时间 |
| finished_at | string nullable | 结束时间 |
| game_id | string nullable | 成功后关联 draft game |
| result_summary | string nullable | 结果摘要 |
| error_message | string nullable | 失败原因 |

验证要点：

- 只返回当前用户任务。
- 按创建时间倒序。
- 多个并发任务状态互不覆盖。
- 前端点击历史任务时，必须优先使用 `session_id` 拉取 `GET /api/create-sessions/{session_id}` 恢复聊天上下文。

### GET `/api/jobs/{job_id}`

权限：owner。

成功响应字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| job_id | string | 任务 ID |
| session_id | string nullable | 关联 Create 对话会话 ID；历史任务可为空 |
| parent_job_id | string nullable | revision job 的上一版任务 ID；初始任务为空 |
| status | string | `pending / running / succeeded / failed` |
| title | string | 任务名 |
| game_id | string nullable | 成功后关联 draft game |
| artifact_prefix | string nullable | 产物对象存储路径 |
| manifest_url | string nullable | draft manifest 授权 URL 或 published URL |
| artifact_base_url | string nullable | 产物基础 URL |
| result_summary | string nullable | 结果摘要 |
| error_message | string nullable | 失败原因 |
| revision_intent | string nullable | 生成后修改意图摘要 |
| created_at | string | 创建时间 |
| started_at | string nullable | 开始时间 |
| finished_at | string nullable | 结束时间 |

验证要点：

- owner 可读取自己任务的关联 `session_id` 和产物信息。
- 如果任务是 revision job，必须返回 `parent_job_id`。
- 不返回完整 presigned URL 签名或敏感字段。

### POST `/api/jobs/{job_id}/revisions`

权限：owner。

状态：后续版本契约；生成后聊天修改使用该接口或等价 revision job 创建接口，不复用第一阶段 `chat` 事件。

请求字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| message | string | 是 | 用户本轮明确修改诉求 |
| base_session_id | string | 否 | 原任务关联的 Create Session；未传时由 `job_id` 反查 |

成功响应：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| job_id | string | 新 revision job ID |
| parent_job_id | string | 被修改的上一版 job ID |
| session_id | string | 关联的原 Create Session ID |
| status | string | `pending` |
| revision_intent | string | 修改意图摘要 |
| assistant_response.message | string | 给用户的简短反馈 |

验证要点：

- 只有 `succeeded / failed` 的任务允许进入 revision loop；`pending / running` 返回 409。
- 后端基于原任务快照、已生成结果和新消息生成 patch，再创建新的 revision job。
- revision job 不覆盖旧任务、旧 draft 或原始 `create_session` 快照。
- 用户消息过于模糊或冲突时，可以返回需要澄清的错误或 `requires_clarification` 响应，而不是创建任务。

### GET `/api/jobs/{job_id}/logs`

权限：owner。

成功响应：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| logs | array | 日志列表 |

`logs[]` 字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| step | string | 步骤名 |
| level | string | `info / warning / error` |
| message | string | 可读日志摘要 |
| created_at | string | 记录时间 |

验证要点：

- 按时间正序。
- 不暴露密钥或完整签名 URL。

## 8. Play Events API

### POST `/api/play-events`

权限：公开。

请求字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| game_id | string | 是 | 游戏 ID |
| event_type | string | 是 | `view / manifest_loaded / started / failed / timeout / exited` |
| metadata | object | 否 | 阶段、耗时、错误原因、URL 类型等 |

`metadata` 建议字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| stage | string | `meta / manifest / bundle / iframe` |
| duration_ms | number | 耗时 |
| error_code | string | 错误码 |
| url_type | string | `meta / manifest / entry / asset` |

验证要点：

- 游客可上报。
- 登录用户上报时记录 `user_id`。
- `view` 或 `started` 更新 `play_count`，具体实现只能选择一种计数触发，避免重复计数。
- 无效 `event_type` 被拒绝。

## 9. 前端 Mock 契约

前端可在后端未完成时使用本契约构造 mock 数据，但字段名必须与本文档一致。

Mock 限制：

- 不能把 mock 数据作为最终验收依据。
- Play iframe 最终必须加载 MinIO 或 S3-compatible URL。
- Console 输出结构应与真实 API 响应一致。
- 未登录点赞必须模拟 401，并触发 Auth Modal。
