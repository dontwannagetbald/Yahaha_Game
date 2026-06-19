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

## 6. Jobs API

### POST `/api/jobs`

权限：登录。

请求字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| prompt | string | 是 | 自然语言创意 |
| asset_ids | string[] | 否 | 已上传素材 ID |
| confirmation | object | 是 | 最终确认卡片内容 |

`confirmation` 字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| title | string | 游戏标题 |
| short_description | string | 一句话简介 |
| game_type | string | 游戏类型 |
| core_gameplay | string | 核心玩法 |
| win_lose_condition | string | 胜负条件 |
| controls | string | 操作方式 |
| assets_used | string | 使用到的素材 |
| tags | string[] | 标签 |
| cover_suggestion | string | 封面建议 |

成功响应：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| job_id | string | 任务 ID |
| status | string | `pending` |
| created_at | string | 创建时间 |

验证要点：

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

### GET `/api/jobs/{job_id}`

权限：owner。

成功响应：返回单个任务详情，并包含 `artifact_prefix`、`manifest_url`、`game_id`、`error_message` 等字段。

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

## 7. Play Events API

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

## 8. 前端 Mock 契约

前端可在后端未完成时使用本契约构造 mock 数据，但字段名必须与本文档一致。

Mock 限制：

- 不能把 mock 数据作为最终验收依据。
- Play iframe 最终必须加载 MinIO 或 S3-compatible URL。
- Console 输出结构应与真实 API 响应一致。
- 未登录点赞必须模拟 401，并触发 Auth Modal。
