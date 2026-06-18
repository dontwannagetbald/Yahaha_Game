# AI Native 互动游戏平台 MVP 产品设计文档

## 1. 文档目标

本文档定义 AI Native 互动游戏平台 MVP 的产品范围、核心用户旅程、页面能力、业务状态、数据模型、接口边界、运行时协议、安全边界和已知取舍。

当前版本先不展开 Agent 内部设计，只定义用户可见的生成任务、任务日志、产物地址、发布状态和 Play 运行协议。Create 页面具体界面布局尚未最终确定，正式实现 Create UI 前需要再次确认交互细节。

## 2. 产品目标

MVP 需要在 2 天交付周期内打通完整闭环：

1. 用户可以通过邮箱注册/登录。
2. 未登录用户可以浏览首页游戏流并游玩已发布游戏。
3. 登录用户可以提交创意和文件素材，创建互动游戏生成任务。
4. 系统异步生成游戏产物，并展示任务状态、产物地址和执行日志。
5. 用户可以预览生成结果，确认后发布。
6. 发布后的游戏出现在 Home，并可被所有用户点击游玩。

核心验收目标是证明「登录/注册 -> 创意生成 -> 游戏发布 -> 浏览游玩」链路真实可运行，并且 Play 页面动态加载对象存储中的远端游戏文件，而不是硬编码本地组件。

## 3. 技术栈

| 模块 | 技术选型 |
| --- | --- |
| 前端 | React + Vite + Ant Design |
| 后端 | FastAPI |
| 数据库 | PostgreSQL |
| 对象存储 | MinIO |
| Agent 框架 | LangGraph |
| 异步任务 | FastAPI BackgroundTasks |
| 模型服务 | OpenAI-compatible API；Mock provider 仅用于本地兜底和 CI |
| 部署方式 | Docker Compose |

详细技术栈说明见 [tech-stack.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/tech-stack.md)。

## 4. 设计风格

界面风格参考 Yahaha 官网，采用深色游戏化视觉、沉浸式封面图、白色文字和黄色主 CTA。

关键视觉规则：

- 页面基础色使用 `#0F1112`。
- 主文字使用白色。
- 主按钮使用 `#FFC200` 背景、深色文字、`99px` 胶囊圆角。
- Home 和 Play 以游戏封面、预览画面、运行 iframe 为视觉主体。
- Create 属于工作流页面，需要继承品牌色，但信息密度可以高于官网首页。

详细设计系统见 [design.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/design.md)。

## 5. 用户角色与权限

### 未登录游客

- 可以访问 Home。
- 可以查看所有 published 游戏。
- 可以进入 Play 并游玩游戏。
- 点击 Create、Publish、删除等受保护操作时，弹出登录/注册弹窗。

### 登录用户

- 可以创建生成任务。
- 可以上传任意文件作为素材。
- 可以查看自己的任务历史。
- 可以预览自己的生成结果。
- 可以发布自己生成成功的 draft 游戏。
- 只能发布、编辑、删除自己的游戏或任务。

### 平台维护者

MVP 暂不实现平台维护者后台。平台维护者能力只在设计上保留扩展空间，包括内容审核、异常包处理、对象存储管理、任务稳定性监控和违规内容下架。

## 6. 核心用户旅程

### 未登录游客旅程

1. 进入 Home。
2. 浏览所有用户发布的游戏。
3. 选择排序：最新发布或最多游玩。
4. 点击游戏卡片。
5. 进入 Play。
6. Play 从后端获取游戏 meta。
7. Play 加载 MinIO 中的 `manifest.json` 和游戏 bundle。
8. 游戏在 sandboxed iframe 中运行。
9. 系统记录游玩次数和基础 play 事件。

### 登录用户旅程

1. 用户进入 Create。
2. 如果未登录，弹出登录/注册弹窗。
3. 登录后输入创意文本并上传任意文件素材。
4. 提交生成任务。
5. 后端创建 `generation_job`，状态为 `pending`。
6. 后台任务执行，状态更新为 `running`。
7. Create 页面任务历史实时展示任务状态和 Agent 执行日志。
8. 任务成功后状态为 `succeeded`，生成结果默认是 `draft`。
9. 用户预览 draft 游戏。
10. 用户点击 `Publish`。
11. 后端将游戏状态更新为 `published`。
12. 游戏进入 Home 游戏流，可被所有用户游玩。

## 7. MVP 页面范围

| 页面 / 组件 | MVP 范围 | 说明 |
| --- | --- | --- |
| Home | 必做 | 展示所有 published 游戏，支持最新发布 / 最多游玩排序。 |
| Auth Modal | 必做 | 登录注册不做独立页面，统一用弹窗承载。 |
| Create | 必做 | 支持创意输入、任意文件上传、生成任务提交、任务历史、状态和日志展示、预览、发布。具体 UI 布局待二次确认。 |
| Play | 必做 | 动态加载远端 manifest 和 bundle，在 sandboxed iframe 中运行游戏。 |
| Game Detail | 不做 | Home 卡片直接进入 Play，详情页放后续版本。 |
| My Games / Profile | 不做 | MVP 没有单独展示用户已发布游戏的地方。 |
| Admin Console | 不做 | 平台维护者后台放后续版本。 |

## 8. 页面设计

### 8.1 全局导航

导航包含：

- Logo / 产品名。
- Home 入口。
- Create 入口。
- 登录状态区域。

未登录时显示 `Sign In` 黄色胶囊按钮，点击打开 Auth Modal。已登录时显示用户邮箱和 `Logout`。

导航在 Home 和 Play 中可以采用透明或深色叠层；在 Create 中采用深色固定导航，优先保证工作流可读性。

### 8.2 Auth Modal

Auth 不做独立页面，使用一个弹窗承载登录、注册和退出后的重新登录。

能力：

- 邮箱注册。
- 邮箱登录。
- 退出登录。
- 错误提示。
- 登录成功后刷新当前用户 session 状态。

弹窗字段：

- Email。
- Password。
- Confirm Password，仅注册态显示。

交互：

- 用户访问 Home / Play 不强制登录。
- 用户访问 Create 或点击 Publish 时，如果未登录，弹出 Auth Modal。
- 登录成功后继续原动作或停留在当前页面。

第三方登录：

- MVP 不真实接入。
- 设计文档保留 Google / GitHub OAuth 的账号绑定模型和扩展接口。

### 8.3 Home

Home 展示所有用户发布的 `published` 游戏列表，不区分官方示例和用户生成。

卡片字段：

- 封面。
- 标题。
- 作者。
- 简介。
- 标签。
- 发布时间。
- 游玩次数。

排序：

- 最新发布。
- 最多游玩。

MVP 不做：

- 搜索。
- 标签筛选。
- 点赞。
- 收藏。
- 游戏详情页。

空状态：

- 如果没有 published 游戏，展示引导文案和 Create CTA。
- 测试数据至少 seed 3 个示例游戏，其中至少 1 个需要来自 Create 发布闭环。

### 8.4 Create

Create 是创作者工作台，但具体界面布局尚未最终确定。实现 Create 界面前需要再次确认具体交互。

已确认产品能力：

- 需要登录。
- 支持自然语言创意输入。
- 支持任意文件上传。
- 用户可以并发提交多个生成任务。
- 用户提交任务后可以离开页面，回来继续查看任务状态。
- 页面展示任务历史。
- 每条任务实时显示状态：`pending / running / succeeded / failed`。
- 每条任务展示 Agent 执行日志摘要或步骤流。
- 任务成功后生成结果默认是 `draft`。
- 用户可以预览 draft。
- 用户点击 `Publish` 后，游戏进入 Home。

暂不实现：

- 发布后编辑标题、简介、标签、封面。
- 用户已发布游戏管理页。
- 取消发布。
- 生成中 Cancel。
- Remix 派生。
- 版本管理 UI。

建议实现形态：

- 顶部：创意输入框和文件上传区。
- 中部：提交按钮和当前上传素材列表。
- 下方：任务历史列表。
- 任务详情：状态、关键步骤、日志、产物地址、预览按钮、发布按钮。

### 8.5 Play

Play 页面负责动态加载并运行远端游戏。

页面状态：

| 状态 | 行为 |
| --- | --- |
| loading | 展示正在加载游戏 meta、manifest 或 bundle。 |
| ready | 在 sandboxed iframe 中展示游戏。 |
| failed | 展示错误原因、重试按钮和返回首页入口。 |
| exited | 提供返回首页和重新开始入口。 |

展示信息：

- 游戏标题。
- 作者。
- 简介。
- 标签。
- 游玩次数。
- 返回 Home。
- 重新开始。

运行机制：

- 前端请求 `GET /api/games/{id}` 获取 meta。
- 前端从 meta 中读取 `manifest_url`。
- 前端加载 MinIO public-read `manifest.json`。
- 前端将 `index.html` 作为 iframe 入口。
- iframe 使用 sandbox 限制能力。

Play 必须能证明游戏文件来自 MinIO 或 S3-compatible URL，而不是本地硬编码组件。

## 9. 业务状态

### 游戏状态

| 状态 | 含义 |
| --- | --- |
| draft | 生成成功但未发布，仅创建者可预览。 |
| published | 已发布，进入 Home，所有用户可游玩。 |
| deleted | 用户删除自己的 draft 或任务产物后进入逻辑删除状态。 |

MVP 不做 `unpublished`。取消发布放后续版本。

### 生成任务状态

| 状态 | 含义 |
| --- | --- |
| pending | 任务已创建，等待后台任务执行。 |
| running | 任务正在生成。 |
| succeeded | 任务完成，生成 draft 游戏产物。 |
| failed | 任务失败，可查看错误信息和日志。 |

任务历史需要支持多个任务并发存在。前端可以通过轮询或 SSE 获取任务最新状态；MVP 优先使用轮询，降低实现复杂度。

## 10. 远端游戏产物协议

每个生成游戏版本是一个静态 bundle：

```text
manifest.json
index.html
style.css
game.js
assets/*
```

`manifest.json` 示例字段：

```json
{
  "schemaVersion": "1.0",
  "title": "Space Runner",
  "description": "A small arcade game generated from user prompt.",
  "entry": "index.html",
  "styles": ["style.css"],
  "scripts": ["game.js"],
  "assets": ["assets/cover.png"],
  "cover": "assets/cover.png",
  "controls": ["Arrow keys to move", "Space to jump"],
  "runtime": "html5-iframe",
  "generatedAt": "2026-06-19T00:00:00Z"
}
```

存储路径建议：

```text
uploads/{user_id}/{upload_id}/{filename}
drafts/{user_id}/{job_id}/{version}/manifest.json
drafts/{user_id}/{job_id}/{version}/index.html
published/{game_id}/{version}/manifest.json
published/{game_id}/{version}/index.html
published/{game_id}/{version}/assets/*
```

访问策略：

- `uploads/*` 私有，通过 presigned URL 访问。
- `drafts/*` 私有，仅创建者通过后端授权预览。
- `published/*` public-read，Play 可以直接加载。

## 11. 数据模型

### users

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | uuid | 用户 ID |
| email | varchar | 邮箱，唯一 |
| password_hash | varchar | 密码哈希 |
| display_name | varchar | 展示名，默认取邮箱前缀 |
| created_at | timestamp | 创建时间 |

### sessions

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | uuid | session ID |
| user_id | uuid | 用户 ID |
| expires_at | timestamp | 过期时间 |
| created_at | timestamp | 创建时间 |

### games

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | uuid | 游戏 ID |
| owner_id | uuid | 创建者 |
| title | varchar | 游戏标题 |
| description | text | 简介 |
| cover_url | text | 封面 URL |
| tags | text[] | 标签 |
| status | varchar | `draft / published / deleted` |
| manifest_url | text | manifest public 或授权 URL |
| artifact_base_url | text | 产物基础 URL |
| play_count | integer | 游玩次数 |
| published_at | timestamp | 发布时间 |
| created_at | timestamp | 创建时间 |
| updated_at | timestamp | 更新时间 |

### generation_jobs

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | uuid | 任务 ID |
| user_id | uuid | 创建者 |
| prompt | text | 用户创意 |
| status | varchar | `pending / running / succeeded / failed` |
| game_id | uuid | 成功后关联 draft game |
| artifact_prefix | text | 产物对象存储路径 |
| error_message | text | 失败原因 |
| created_at | timestamp | 创建时间 |
| started_at | timestamp | 开始时间 |
| finished_at | timestamp | 结束时间 |

### uploaded_assets

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | uuid | 上传素材 ID |
| user_id | uuid | 上传者 |
| job_id | uuid | 关联生成任务 |
| filename | varchar | 原始文件名 |
| mime_type | varchar | MIME type |
| size_bytes | bigint | 文件大小 |
| object_key | text | MinIO object key |
| purpose | text | 用户填写或系统推断的用途说明 |
| created_at | timestamp | 上传时间 |

### agent_logs

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | uuid | 日志 ID |
| job_id | uuid | 任务 ID |
| step | varchar | 步骤名 |
| level | varchar | `info / warning / error` |
| message | text | 可读日志摘要 |
| created_at | timestamp | 记录时间 |

### play_events

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | uuid | 事件 ID |
| game_id | uuid | 游戏 ID |
| user_id | uuid nullable | 登录用户可记录，游客为空 |
| event_type | varchar | `view / manifest_loaded / started / failed / exited` |
| metadata | jsonb | 错误原因、耗时等 |
| created_at | timestamp | 事件时间 |

## 12. API 设计

### Auth

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/auth/register` | 邮箱注册 |
| POST | `/api/auth/login` | 邮箱登录，写入 httpOnly session cookie |
| POST | `/api/auth/logout` | 退出登录 |
| GET | `/api/auth/me` | 获取当前 session 用户 |

### Games

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | `/api/games` | 公开 | 获取 published 游戏列表，支持 `sort=latest/play_count` |
| GET | `/api/games/{game_id}` | 公开或 owner | 获取游戏 meta；draft 仅 owner 可访问 |
| POST | `/api/games/{game_id}/publish` | owner | 发布 draft 游戏 |
| DELETE | `/api/games/{game_id}` | owner | 删除自己的 draft 或未发布产物 |

MVP 暂不提供发布后编辑接口。发布后编辑标题、简介、标签、封面放后续版本。

### Create Jobs

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| POST | `/api/jobs` | 登录 | 创建生成任务 |
| GET | `/api/jobs` | 登录 | 获取自己的任务历史 |
| GET | `/api/jobs/{job_id}` | owner | 获取任务详情、状态、产物地址 |
| GET | `/api/jobs/{job_id}/logs` | owner | 获取任务日志 |

### Uploads

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| POST | `/api/uploads/presign` | 登录 | 获取上传 presigned URL |
| POST | `/api/uploads/complete` | 登录 | 上传完成后登记文件元信息 |

上传限制：

- 支持任意文件类型。
- 建议单文件最大 `20MB`。
- 建议单任务最多 `5` 个文件。
- 后端记录 MIME type、文件大小、object key 和用途说明。
- 上传文件只存储，不在后端直接执行。

### Play Events

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| POST | `/api/play-events` | 公开 | 记录 view、加载成功、加载失败、退出等事件 |

## 13. 权限规则

- Home published 列表公开。
- Play published 游戏公开。
- Create 页面必须登录。
- 生成任务只对创建者可见。
- draft 游戏只对 owner 可见。
- Publish 只能由 owner 执行。
- Delete 只能由 owner 执行。
- 发布后的游戏进入公开列表。
- 发布后编辑游戏信息不在 MVP 范围内。

## 14. 安全设计

### 会话安全

- 使用服务端 session。
- Session ID 通过 `httpOnly` cookie 存储。
- Cookie 设置 `SameSite=Lax`。
- 生产环境启用 `Secure`。
- 密码使用强哈希算法存储，不能明文保存。

### 上传安全

- 任意文件上传只进入私有 MinIO 路径。
- 后端校验文件大小和基础 MIME 信息。
- 上传文件不在后端执行。
- Agent 只能通过授权 URL 读取素材。
- 公开产物和原始上传素材分开存储。

### Play 隔离

- 生成游戏在 sandboxed iframe 中运行。
- iframe 禁止访问父页面 DOM。
- 后端不执行生成游戏中的 JS。
- published bundle 只作为静态文件加载。
- Play 加载失败时展示错误态，不白屏。

### 密钥安全

- `.env.example` 只列变量名和用途，不提交真实密钥。
- OpenAI-compatible API key 只存在后端环境变量中。
- 前端不能直接接触模型服务密钥。

## 15. 埋点与可观测性

MVP 至少记录：

- 游戏列表曝光或请求。
- Play view。
- manifest 加载成功 / 失败。
- iframe 启动成功 / 失败。
- 生成任务创建。
- 生成任务状态变化。
- Publish 成功 / 失败。

任务可观测性：

- 每个任务展示 Agent 执行日志摘要。
- 每个任务保留错误原因。
- 每个任务保留产物路径或 manifest URL。

## 16. 测试数据

MVP 需要准备至少 3 个示例游戏：

- 至少 2 个可通过 seed 脚本初始化为 `published`。
- 至少 1 个必须通过 Create 流程生成 draft，再由用户点击 Publish 进入 Home。
- 示例游戏不区分官方示例和用户生成。

每个示例游戏需要包含：

- 封面。
- 标题。
- 作者。
- 简介。
- 标签。
- 发布时间。
- manifest URL。
- 可运行 bundle。

## 17. 已知取舍

- Auth 不做独立页面，统一使用弹窗。
- 未登录用户可以浏览和游玩，但不能创建和发布。
- Game Detail 不进入 MVP。
- 搜索、标签筛选、点赞、收藏不进入 MVP。
- 发布后编辑标题、简介、标签、封面不进入 MVP。
- 取消发布不进入 MVP。
- 用户已发布游戏管理页不进入 MVP。
- 平台维护者后台不进入 MVP。
- Create 具体页面布局待二次确认。
- Agent 内部编排不在本文档展开。
- 异步任务使用 FastAPI BackgroundTasks，不引入 Celery。

## 18. 后续版本规划

如果再给 1 周，建议优先迭代：

1. 用户作品管理页：展示自己的 draft、published 和 deleted 游戏。
2. 发布后编辑游戏 meta：标题、简介、标签、封面。
3. 取消发布和重新发布。
4. 搜索和标签筛选。
5. 点赞、收藏和分享。
6. 任务 Retry、Cancel 和版本管理。
7. 平台维护者后台：内容审核、任务监控、产物下架。
8. 更完整的 OAuth 登录：Google / GitHub 账号绑定。
9. Play 性能统计：manifest 加载耗时、iframe ready 耗时、运行错误率。

## 19. 待实现前再次确认

Create 页面具体界面还未最终确定。正式开始实现 Create UI 前，需要再次确认：

- 创意输入是单轮提交还是聊天式多轮对话。
- 文件上传区的位置、素材用途说明是否必填。
- 任务历史列表的信息密度和展开方式。
- 日志是默认展开还是折叠。
- 预览和发布按钮在任务卡片内还是单独结果区。
- 并发任务多时的排序和筛选。
