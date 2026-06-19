# Backend 实施计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 独立完成 FastAPI 后端的业务数据模型、对象存储、Games / Uploads / Jobs / Play Events API、发布流程和 Agent 执行器接入边界。

**架构：** 后端是系统事实来源，负责 DB-backed session、权限校验、PostgreSQL 状态、MinIO 对象路径、任务生命周期和 API 契约。Agent 可先用 fake runner 解耦，前端可只依赖 [api-contract.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/api-contract.md) 并行开发。最终后端通过 BackgroundTasks 调用 Agent 执行器，产物进入 draft，再由 owner 发布到 published。

**技术栈：** FastAPI、PostgreSQL、SQLAlchemy、Alembic、MinIO S3-compatible、FastAPI BackgroundTasks、Docker Compose。

---

## 1. 必读上下文

后端开发者单独拿到本文档时，必须先阅读：

- [design-document.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/design-document.md)：产品边界、权限、数据模型、安全规则。
- [api-contract.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/api-contract.md)：前后端唯一接口契约。
- [tech-stack.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/tech-stack.md)：技术栈和存储策略。
- [architecture.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/architecture.md)：目录边界和文件职责。
- [progress.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/progress.md)：已完成步骤和当前缺口。

已有后端基线：

- FastAPI 应用骨架、CORS、统一错误响应、`/health`、`/ready` 已存在。
- PostgreSQL 连接和 Alembic 已存在。
- `users`、`sessions`、`oauth_accounts` 已存在。
- 邮箱注册、邮箱登录、退出登录、`GET /api/auth/me` 已存在。
- Google OAuth start/callback 代码路径已存在；GitHub OAuth 为未启用占位。
- Docker Compose、PostgreSQL、MinIO、MinIO bucket 初始化已存在。

## 2. 后端独立运行原则

- 后端不能等待前端完成。所有接口用 HTTP 测试、单元测试或 API client 验证。
- 后端不能等待 Agent 完成。Backend Step 8 前可使用 fake Agent runner 验证任务状态流。
- 所有响应字段、状态码和错误格式必须符合 [api-contract.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/api-contract.md)。
- 未登录用户可以访问 Home / published Play 相关接口，但不能点赞、创建任务、上传、发布或访问 draft。
- 不实现收藏、独立 Game Detail、My Games/Profile、Admin Console、发布后编辑、取消发布、GitHub OAuth 真实跑通、版本管理、Remix、内容审核、资源限额和成本统计。
- 每完成一个任务，更新 [architecture.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/architecture.md) 和 [progress.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/progress.md)。

## 3. 与其他端的接口边界

### 给前端的稳定边界

- 前端只依赖 [api-contract.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/api-contract.md)。
- 后端提供 Auth、Games、Uploads、Jobs、Play Events API。
- 401 代表未登录，前端会打开 Auth Modal。
- draft 资源仅 owner 可访问；published 资源公开。
- Play Events 公开可写，但 metadata 不能包含敏感信息。

### 给 Agent 的稳定边界

后端调用 Agent 执行器时传入：

- `job_id`
- `user_id`
- `prompt`
- `confirmation`
- `uploaded_assets` 元信息
- 授权读取素材的 URL 或后端可读 object key

Agent 返回：

- 任务成功或失败状态
- draft game 元信息
- artifact prefix
- manifest 路径
- 日志事件
- 错误摘要

Agent 内部节点设计后续再定，后端只依赖上述执行器边界。

## 4. Backend Tasks

## Step 1：补齐后端业务数据模型

依赖其他端：不需要。

### Step 1.1：指令

- [ ] 新增 `games`、`game_likes`、`generation_jobs`、`uploaded_assets`、`agent_logs`、`play_events` 数据模型和 Alembic 迁移。
### Step 1.2：指令

- [ ] `uploaded_assets.job_id` 允许为空，支持先上传文件再创建任务。
### Step 1.3：指令

- [ ] `game_likes.user_id` 必填，并对同一用户同一游戏建立唯一约束。
### Step 1.4：指令

- [ ] `play_events.event_type` 支持 `view`、`manifest_loaded`、`started`、`failed`、`timeout`、`exited`。
### Step 1.5：指令

- [ ] 不要创建收藏、发布后编辑、取消发布、平台维护者后台相关表。
### Step 1.6：验证

- [ ] 从空数据库执行迁移成功。
### Step 1.7：验证

- [ ] 表字段与 [design-document.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/design-document.md) 数据模型一致。
### Step 1.8：验证

- [ ] 重复点赞唯一约束生效。
### Step 1.9：验证

- [ ] `uploaded_assets` 可以创建未绑定 job 的记录。
### Step 1.10：验证

- [ ] 重复执行迁移不会破坏已存在的 Auth 表。

## Step 2：实现 MinIO 存储服务边界

依赖其他端：不需要。

### Step 2.1：指令

- [ ] 封装对象存储访问，统一处理 bucket、object key、public URL、presigned URL。
### Step 2.2：指令

- [ ] 保持 `uploads/*` 和 `drafts/*` 私有。
### Step 2.3：指令

- [ ] 保持 `published/*` public-read。
### Step 2.4：指令

- [ ] 业务代码不得散落 bucket 名和路径拼接逻辑。
### Step 2.5：验证

- [ ] 可以上传测试对象到 `uploads/*`。
### Step 2.6：验证

- [ ] `uploads/*` 不能 public 读取，但 presigned URL 可读取。
### Step 2.7：验证

- [ ] `published/*` 对象可以 public 读取。
### Step 2.8：验证

- [ ] MinIO 不可用时 API 返回统一错误格式。

## Step 3：实现上传 API

依赖其他端：不需要；前端可用 mock 并行。

### Step 3.1：指令

- [ ] 实现 `POST /api/uploads/presign`。
### Step 3.2：指令

- [ ] 实现 `POST /api/uploads/complete`。
### Step 3.3：指令

- [ ] 只允许登录用户调用。
### Step 3.4：指令

- [ ] 支持任意文件类型。
### Step 3.5：指令

- [ ] 单文件最大 `20MB`。
### Step 3.6：指令

- [ ] 单任务最多 `5` 个文件的限制在创建任务时校验。
### Step 3.7：指令

- [ ] 上传完成后记录文件名、MIME type、大小、object key。
### Step 3.8：验证

- [ ] 未登录请求 presign 返回 401。
### Step 3.9：验证

- [ ] 登录用户请求 presign 返回 `upload_id`、`object_key`、`upload_url`、过期时间。
### Step 3.10：验证

- [ ] 超过 `20MB` 的文件请求被拒绝。
### Step 3.11：验证

- [ ] 上传完成登记后数据库有 `uploaded_assets` 记录。
### Step 3.12：验证

- [ ] 响应和错误格式符合 [api-contract.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/api-contract.md)。

## Step 4：实现 Games 列表和 meta API

依赖其他端：不需要；前端可用 mock 并行。

### Step 4.1：指令

- [ ] 实现 `GET /api/games`。
### Step 4.2：指令

- [ ] 只返回 `published` 游戏。
### Step 4.3：指令

- [ ] 支持 `sort=latest`、`sort=play_count`、`sort=like_count`。
### Step 4.4：指令

- [ ] 支持搜索和标签筛选。
### Step 4.5：指令

- [ ] 实现 `GET /api/games/{game_id}`。
### Step 4.6：指令

- [ ] `published` 游戏公开可读，`draft` 仅 owner 可读。
### Step 4.7：指令

- [ ] 返回 Home 卡片和 Play 左侧详情需要的全部字段。
### Step 4.8：验证

- [ ] 游客可以获取 published 游戏列表。
### Step 4.9：验证

- [ ] draft 不出现在 Home 列表中。
### Step 4.10：验证

- [ ] 最新发布、最多游玩、最多点赞排序正确。
### Step 4.11：验证

- [ ] 搜索关键词能筛出匹配游戏。
### Step 4.12：验证

- [ ] 标签筛选只返回包含该标签的游戏。
### Step 4.13：验证

- [ ] 游客不能读取 draft meta，owner 可以读取自己的 draft meta。

## Step 5：实现登录后点赞 API

依赖其他端：不需要；前端可用 mock 并行。

### Step 5.1：指令

- [ ] 实现 `POST /api/games/{game_id}/like`。
### Step 5.2：指令

- [ ] 只允许登录用户调用。
### Step 5.3：指令

- [ ] 未登录返回 401。
### Step 5.4：指令

- [ ] MVP 只做新增点赞，不做取消点赞。
### Step 5.5：指令

- [ ] 同一用户重复点赞不增加计数。
### Step 5.6：指令

- [ ] 返回更新后的 `like_count` 和 `liked_by_me=true`。
### Step 5.7：验证

- [ ] 未登录点赞返回 401。
### Step 5.8：验证

- [ ] 登录用户首次点赞后 `game_likes` 新增记录，`games.like_count` 增加。
### Step 5.9：验证

- [ ] 同一用户重复点赞不重复增加 `like_count`。
### Step 5.10：验证

- [ ] 不同用户可以分别点赞同一游戏。
### Step 5.11：验证

- [ ] 前端所需响应字段符合 [api-contract.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/api-contract.md)。

## Step 6：实现 Play Events API

依赖其他端：不需要；前端可用 mock 并行。

### Step 6.1：指令

- [ ] 实现 `POST /api/play-events`。
### Step 6.2：指令

- [ ] 允许游客上报。
### Step 6.3：指令

- [ ] 登录用户上报时记录 `user_id`。
### Step 6.4：指令

- [ ] 支持 `view`、`manifest_loaded`、`started`、`failed`、`timeout`、`exited`。
### Step 6.5：指令

- [ ] 只选择 `view` 或 `started` 之一更新 `play_count`，避免同一次 Play 重复计数。
### Step 6.6：指令

- [ ] metadata 不保存 secret、token、password、OAuth code 或完整 presigned URL 签名。
### Step 6.7：验证

- [ ] 游客可以上报 `view`。
### Step 6.8：验证

- [ ] 登录用户上报时记录 `user_id`。
### Step 6.9：验证

- [ ] 无效事件类型被拒绝。
### Step 6.10：验证

- [ ] 有效计数事件会增加 `play_count`。
### Step 6.11：验证

- [ ] failed 和 timeout 事件可记录错误阶段、耗时和错误码。

## Step 7：实现 Jobs API

依赖其他端：不需要；Agent 和前端均可 mock 并行。

### Step 7.1：指令

- [ ] 实现 `POST /api/jobs`。
### Step 7.2：指令

- [ ] 创建时接收自然语言创意、素材 ID 列表和最终确认卡片内容。
### Step 7.3：指令

- [ ] 校验登录态。
### Step 7.4：指令

- [ ] 校验素材属于当前用户。
### Step 7.5：指令

- [ ] 单任务最多绑定 `5` 个素材。
### Step 7.6：指令

- [ ] 创建后写入 `pending` 任务，并启动 FastAPI BackgroundTasks。
### Step 7.7：指令

- [ ] 实现 `GET /api/jobs`、`GET /api/jobs/{job_id}`、`GET /api/jobs/{job_id}/logs`。
### Step 7.8：指令

- [ ] 只允许 owner 访问自己的任务和日志。
### Step 7.9：验证

- [ ] 未登录创建任务返回 401。
### Step 7.10：验证

- [ ] 登录用户创建任务后返回 `job_id` 和 `pending`。
### Step 7.11：验证

- [ ] 同一用户可并发创建多个任务。
### Step 7.12：验证

- [ ] 用户只能看到自己的任务历史。
### Step 7.13：验证

- [ ] 非 owner 不能读取任务详情和日志。
### Step 7.14：验证

- [ ] 素材不属于当前用户时创建任务失败。

## Step 8：接入 Agent 执行器边界

依赖其他端：最终依赖 Agent Step 1；后端可先用 fake Agent runner 独立验证。

### Step 8.1：指令

- [ ] 为 BackgroundTasks 增加 Agent runner 调用边界。
### Step 8.2：指令

- [ ] fake Agent runner 能返回成功、失败两种结果，用于后端独立测试。
### Step 8.3：指令

- [ ] 真实 Agent Step 1 完成后，用真实执行器替换 fake runner。
### Step 8.4：指令

- [ ] 任务启动后状态从 `pending` 变为 `running`。
### Step 8.5：指令

- [ ] Agent 成功后创建或更新 draft game。
### Step 8.6：指令

- [ ] Agent 失败后任务状态变为 `failed`，写入 `error_message`。
### Step 8.7：指令

- [ ] 后端负责写入任务状态变化和 Agent 日志。
### Step 8.8：验证

- [ ] 使用 fake runner 创建任务后状态会从 `pending` 进入 `running`。
### Step 8.9：验证

- [ ] fake success 返回后任务变为 `succeeded`，并关联 draft game。
### Step 8.10：验证

- [ ] fake failure 返回后任务变为 `failed`，并保留失败原因。
### Step 8.11：验证

- [ ] 真实 Agent Step 1 接入后，调用输入输出与本文档边界一致。
### Step 8.12：验证

- [ ] 任务日志能按时间正序查询。

## Step 9：实现发布 API

依赖其他端：不需要前端；需要 Backend Step 2、Backend Step 4、Backend Step 8。Agent 可先用 fake runner 产物。

### Step 9.1：指令

- [ ] 实现 `POST /api/games/{game_id}/publish`。
### Step 9.2：指令

- [ ] 只允许 owner 发布自己的 draft。
### Step 9.3：指令

- [ ] 发布时将 draft 产物复制或转存到 `published/*`。
### Step 9.4：指令

- [ ] 更新 `manifest_url` 为 public-read URL。
### Step 9.5：指令

- [ ] 更新状态为 `published`，写入 `published_at`。
### Step 9.6：指令

- [ ] 不提供发布后编辑标题、简介、标签、封面接口。
### Step 9.7：验证

- [ ] owner 可以发布自己的 draft。
### Step 9.8：验证

- [ ] 非 owner 不能发布。
### Step 9.9：验证

- [ ] 游客不能发布。
### Step 9.10：验证

- [ ] 发布后游戏出现在 `GET /api/games`。
### Step 9.11：验证

- [ ] 发布后的 manifest URL 可 public 读取。
### Step 9.12：验证

- [ ] 发布后没有 meta 编辑接口。

## Step 10：准备示例游戏和 seed 数据

依赖其他端：不需要。

### Step 10.1：指令

- [ ] 准备至少 2 个 seed published 静态游戏。
### Step 10.2：指令

- [ ] 每个游戏包含 `manifest.json`、`index.html`、`style.css`、`game.js`、`assets/*`。
### Step 10.3：指令

- [ ] 写入数据库 published 游戏记录。
### Step 10.4：指令

- [ ] 设置封面、标题、作者、简介、标签、发布时间、点赞数和游玩次数。
### Step 10.5：验证

- [ ] Home API 至少返回 2 个 seed 游戏。
### Step 10.6：验证

- [ ] 每个 seed 游戏 manifest URL 可访问。
### Step 10.7：验证

- [ ] 每个 seed 游戏 entry URL 可在浏览器中运行。
### Step 10.8：验证

- [ ] Play meta 字段满足前端契约。

## 5. 后端交付前自检

- [ ] 执行后端测试。
- [ ] 从空数据库执行迁移。
- [ ] 用 HTTP 请求验证 Auth、Games、Uploads、Jobs、Play Events API。
- [ ] 验证未登录、非 owner、owner 三类权限。
- [ ] 验证 published public-read，uploads/drafts private。
- [ ] 验证响应字段与 [api-contract.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/api-contract.md) 一致。
- [ ] 更新 [architecture.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/architecture.md) 和 [progress.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/progress.md)。

## 6. 最终接入条件

后端完成后，应能支持：

- 前端不改字段名即可从 mock 切换到真实 API。
- Agent Step 1 执行器可替换 fake runner。
- Integration Plan 中游客 Home 到 Play、登录点赞、Create 到 Publish、并发任务和权限隔离验收可执行。
