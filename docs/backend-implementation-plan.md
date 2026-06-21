# Backend 实施计划

> **面向 AI 开发者：** 本计划只能作为执行指令使用。严禁在本文档中加入实现代码、伪代码或代码片段。每一步都必须小而具体，每一步完成前都必须运行对应验证测试。执行时优先使用 `test-driven-development`；完成声明前必须使用 `verification-before-completion`。

**目标：** 完成 FastAPI 后端的业务表、对象存储、上传、游戏列表、点赞、Create 对话会话、确认后任务、Agent 边界、发布、Play Events 和 seed 数据能力。

**架构：** 后端是认证、权限、PostgreSQL 状态、MinIO 对象路径、Create 对话会话、生成任务生命周期、revision 关系和 API 契约的事实来源。前端确认前通过 Create Sessions API 与 `conversation_graph` 交互，确认后通过 Jobs API 创建后台生成任务；生成后修改通过 revision job 创建新版本，不覆盖旧产物。业务产物先进入 `drafts/*`，发布后复制或转存到 `published/*`。

**技术栈：** FastAPI、SQLAlchemy async、Alembic、PostgreSQL、MinIO S3-compatible、FastAPI BackgroundTasks、pytest、Docker Compose。

---

## 0. 执行前约束

- 开始任何后端代码变更前，完整阅读 `docs/architecture.md`、`docs/design-document.md`、`docs/api-contract.md`、`docs/tech-stack.md` 和 `docs/progress.md`。
- 不修改前端页面、Agent 内部实现或设计系统，除非本计划明确要求。
- 不实现收藏、独立 Game Detail、My Games/Profile、Admin Console、发布后编辑、取消发布、GitHub OAuth 真实登录、完整版本管理 UI、Remix、内容审核、资源限额或成本统计。
- 每个 Step 完成后更新 `docs/architecture.md` 的文件职责和 `docs/progress.md` 的完成记录。
- 每个 Step 完成后运行该 Step 指定测试；阶段完成时运行 `backend/tests` 全量测试。
- 所有错误响应必须符合 `docs/api-contract.md` 的统一错误格式。
- 不在日志、响应、测试快照或 Console 输出中暴露 password、session id、OAuth code、access token、refresh token、API key 或完整 presigned URL 签名。
- Create 对话阶段只维护 `user_requirements`、`game_plan`、`material_usage` 三个业务主状态；游戏卡片只能从 `game_plan.plan_id/title/introduction/tags` 派生。
- `POST /api/jobs` 只接收已确认的 `session_id`，后端必须从 confirmed Create Session 读取快照创建任务，不信任前端重复提交的 `game_plan` 快照。
- `generation_jobs` 必须能反查 `create_session_id`；`GET /api/jobs` 和 `GET /api/jobs/{job_id}` 必须返回 `session_id`，用于前端恢复历史任务对话。
- 生成后修改不回写第一阶段 Create Session，不复用第一阶段需求收集事件；必须创建新的 revision job 并保留 `parent_job_id`。

## 1. 当前基线

以下能力已经存在，后续 Step 不要重复实现：

- FastAPI 应用入口、CORS、统一错误响应、`/health`、`/ready`。
- PostgreSQL async engine、session dependency、Alembic。
- `users`、`sessions`、`oauth_accounts` 表。
- 邮箱注册、邮箱登录、退出登录、`GET /api/auth/me`。
- Google OAuth start/callback 代码路径。
- GitHub OAuth 未启用占位。
- Docker Compose 中 PostgreSQL、MinIO、MinIO 初始化、backend、frontend。
- 后端启动配置校验。
- 当前已完成的 Jobs API 和 Agent Runner 仍停留在 Create Sessions 改造前的旧实现；后续 Step 7 和 Step 8 必须按 Create Sessions API、`session_id` 和会话快照重新对齐。

---

## Step 1：建立业务表迁移 ☑️ 已完成

**目标文件：**
- 修改：`backend/app/models.py`
- 新增：`backend/migrations/versions/<next_revision>_business_tables.py`
- 新增或修改测试：`backend/tests/test_migrations.py`
- 更新：`docs/architecture.md`、`docs/progress.md`

### Step 1.1：为游戏表编写迁移测试

**指令：**
- 新增迁移测试，验证数据库迁移后存在 `games` 表。
- 测试必须断言 `games` 包含 owner、标题、简介、封面、标签、状态、manifest URL、artifact base URL、play count、like count、发布时间、创建时间和更新时间字段。
- 测试必须断言 `games.status` 支持 `draft`、`published`、`deleted` 的业务值。

**验证：**
- 运行 `pytest backend/tests/test_migrations.py -k games -v`。
- 预期：测试先失败，失败原因指向 `games` 表或字段不存在。

### Step 1.2：实现游戏表迁移

**指令：**
- 在 SQLAlchemy model 和 Alembic migration 中新增 `games` 表。
- `owner_id` 必须关联 `users.user_id`。
- 为 `owner_id`、`status`、`published_at`、`created_at` 建立索引。
- 不添加发布后编辑、取消发布或收藏相关字段。

**验证：**
- 运行 `pytest backend/tests/test_migrations.py -k games -v`。
- 预期：所有 games 相关测试通过。

### Step 1.3：为点赞表编写迁移测试

**指令：**
- 新增迁移测试，验证存在 `game_likes` 表。
- 测试必须断言 `game_likes` 包含 `game_id`、`user_id`、`created_at`。
- 测试必须断言同一个用户对同一个游戏只能有一条点赞记录。

**验证：**
- 运行 `pytest backend/tests/test_migrations.py -k game_likes -v`。
- 预期：测试先失败，失败原因指向 `game_likes` 表或唯一约束不存在。

### Step 1.4：实现点赞表迁移

**指令：**
- 新增 `game_likes` 表。
- `game_id` 必须关联 `games.id`。
- `user_id` 必须关联 `users.user_id`。
- 建立 `(game_id, user_id)` 唯一约束。

**验证：**
- 运行 `pytest backend/tests/test_migrations.py -k game_likes -v`。
- 预期：点赞表结构和唯一约束测试通过。

### Step 1.5：为生成任务表编写迁移测试

**指令：**
- 新增迁移测试，验证存在 `generation_jobs` 表。
- 测试必须断言字段覆盖 user、prompt、status、game、artifact prefix、manifest URL、result summary、error message、created/started/finished 时间。
- 测试必须断言 status 支持 `pending`、`running`、`succeeded`、`failed`。

**验证：**
- 运行 `pytest backend/tests/test_migrations.py -k generation_jobs -v`。
- 预期：测试先失败，失败原因指向 `generation_jobs` 表或字段不存在。

### Step 1.6：实现生成任务表迁移

**指令：**
- 新增 `generation_jobs` 表和对应 model。
- `user_id` 必须关联 `users.user_id`。
- `game_id` 可为空，任务成功后关联 draft game。
- 为 `user_id`、`status`、`created_at` 建立索引。

**验证：**
- 运行 `pytest backend/tests/test_migrations.py -k generation_jobs -v`。
- 预期：生成任务表测试通过。

### Step 1.7：为上传素材表编写迁移测试

**指令：**
- 新增迁移测试，验证存在 `uploaded_assets` 表。
- 测试必须断言字段覆盖 user、job、filename、mime type、size bytes、object key、purpose、created_at。
- 测试必须验证 `job_id` 允许为空，以支持先上传再创建任务。

**验证：**
- 运行 `pytest backend/tests/test_migrations.py -k uploaded_assets -v`。
- 预期：测试先失败，失败原因指向 `uploaded_assets` 表、字段或 nullable 约束。

### Step 1.8：实现上传素材表迁移

**指令：**
- 新增 `uploaded_assets` 表和对应 model。
- `user_id` 必须关联 `users.user_id`。
- `job_id` 必须允许为空，并在绑定任务后可更新。
- 为 `user_id`、`job_id`、`created_at` 建立索引。

**验证：**
- 运行 `pytest backend/tests/test_migrations.py -k uploaded_assets -v`。
- 预期：上传素材表测试通过。

### Step 1.9：为 Agent 日志和 Play 事件表编写迁移测试

**指令：**
- 新增迁移测试，验证存在 `agent_logs` 和 `play_events` 表。
- `agent_logs` 必须覆盖 job、step、level、message、created_at。
- `play_events` 必须覆盖 game、user、event type、metadata、created_at。
- 测试必须断言 `play_events.user_id` 允许为空。
- 测试必须断言 event type 支持 `view`、`manifest_loaded`、`started`、`failed`、`timeout`、`exited`。

**验证：**
- 运行 `pytest backend/tests/test_migrations.py -k "agent_logs or play_events" -v`。
- 预期：测试先失败，失败原因指向表或字段不存在。

### Step 1.10：实现 Agent 日志和 Play 事件表迁移

**指令：**
- 新增 `agent_logs` 和 `play_events` 表及对应 model。
- `agent_logs.job_id` 必须关联 `generation_jobs.id`。
- `play_events.game_id` 必须关联 `games.id`。
- `play_events.user_id` 可为空，游客事件不需要登录。
- 为 `job_id`、`game_id`、`user_id`、`created_at` 建立必要索引。

**验证：**
- 运行 `pytest backend/tests/test_migrations.py -k "agent_logs or play_events" -v`。
- 预期：Agent 日志和 Play 事件表测试通过。

### Step 1.11：验证完整迁移链

**指令：**
- 从当前数据库执行 Alembic 到最新版本。
- 在干净数据库或一次性测试数据库中执行从零到最新版本迁移。
- 重复执行迁移，确认不会破坏已存在的 Auth 表。

**验证：**
- 运行 `pytest backend/tests/test_migrations.py -v`。
- 运行 `docker compose exec -T backend alembic upgrade head`。
- 运行 `docker compose exec -T backend alembic current`。
- 预期：迁移测试全部通过，当前 revision 为最新 head。

---

## Step 2：封装 MinIO 存储服务 ☑️ 已完成

**目标文件：**
- 新增：`backend/app/storage.py`
- 新增测试：`backend/tests/test_storage.py`
- 修改：`backend/app/config.py`
- 更新：`docs/architecture.md`、`docs/progress.md`

### Step 2.1：为对象 key 生成规则编写测试

**指令：**
- 新增测试，验证 uploads、drafts、published 三类路径均由存储服务统一生成。
- 测试必须覆盖 `uploads/{user_id}/{upload_id}/{filename}`。
- 测试必须覆盖 `drafts/{user_id}/{job_id}/{version}/...`。
- 测试必须覆盖 `published/{game_id}/{version}/...`。
- 测试必须断言业务层不需要手写 bucket 名。

**验证：**
- 运行 `pytest backend/tests/test_storage.py -k object_key -v`。
- 预期：测试先失败，失败原因指向存储服务不存在。

### Step 2.2：实现对象 key 生成服务

**指令：**
- 新增存储服务模块，集中管理 bucket 名、object key 和 public URL 生成。
- 文件名必须经过安全化处理，不能允许路径穿越。
- 不在业务 API 中拼接 bucket 或对象路径。

**验证：**
- 运行 `pytest backend/tests/test_storage.py -k object_key -v`。
- 预期：对象 key 生成测试通过。

### Step 2.3：为 presigned URL 编写测试

**指令：**
- 新增测试，验证 `uploads/*` 和 `drafts/*` 返回 presigned URL。
- 新增测试，验证 `published/*` 返回 public URL。
- 测试必须覆盖过期时间字段。
- 测试必须避免在断言输出中保存完整签名 URL。

**验证：**
- 运行 `pytest backend/tests/test_storage.py -k "presigned or public_url" -v`。
- 预期：测试先失败，失败原因指向 URL 能力不存在。

### Step 2.4：实现 URL 生成能力

**指令：**
- 封装 presigned upload URL、presigned read URL 和 public read URL。
- `uploads/*` 和 `drafts/*` 默认私有，只能通过 presigned URL 访问。
- `published/*` 使用 public-read URL。
- MinIO endpoint、public endpoint、bucket、region、SSL 配置必须从 settings 读取。

**验证：**
- 运行 `pytest backend/tests/test_storage.py -k "presigned or public_url" -v`。
- 预期：URL 生成测试通过。

### Step 2.5：为 MinIO 读写和错误格式编写集成测试

**指令：**
- 新增集成测试或 Compose 验证步骤，上传测试对象到 `uploads/*`。
- 验证 public URL 不能直接读取 `uploads/*`。
- 验证 presigned URL 可以读取 `uploads/*`。
- 验证 `published/*` public URL 可以读取。
- 验证 MinIO 不可用时，依赖存储的 API 返回统一错误格式。

**验证：**
- 运行 `pytest backend/tests/test_storage.py -m integration -v`，或运行文档中记录的 Compose 验证命令。
- 预期：私有路径、公有路径和依赖失败行为均符合设计。

---

## Step 3：实现 Uploads API ☑️ 已完成

**目标文件：**
- 新增：`backend/app/uploads.py`
- 修改：`backend/app/main.py`
- 新增测试：`backend/tests/test_uploads.py`
- 更新：`docs/architecture.md`、`docs/progress.md`

### Step 3.1：为 presign 登录权限编写测试

**指令：**
- 新增 API 测试，验证未登录调用 `POST /api/uploads/presign` 返回 401。
- 测试必须验证错误响应格式符合 API 契约。

**验证：**
- 运行 `pytest backend/tests/test_uploads.py -k presign_requires_login -v`。
- 预期：测试先失败，失败原因指向路由不存在或权限未实现。

### Step 3.2：实现 presign 登录保护

**指令：**
- 新增 Uploads router 并挂载到 FastAPI 应用。
- `POST /api/uploads/presign` 必须依赖当前用户。
- 未登录时返回统一 401 错误。

**验证：**
- 运行 `pytest backend/tests/test_uploads.py -k presign_requires_login -v`。
- 预期：未登录权限测试通过。

### Step 3.3：为 presign 成功响应编写测试

**指令：**
- 新增测试，使用已登录用户请求 presign。
- 请求字段包含 filename、mime_type、size_bytes。
- 测试必须断言响应包含 upload_id、object_key、upload_url、expires_in。
- 测试必须断言 object_key 位于当前用户的 `uploads/*` prefix。

**验证：**
- 运行 `pytest backend/tests/test_uploads.py -k presign_success -v`。
- 预期：测试先失败，失败原因指向成功响应尚未实现。

### Step 3.4：实现 presign 成功路径

**指令：**
- 校验 filename、mime_type、size_bytes。
- 支持任意 MIME type。
- 单文件最大 20MB。
- 创建上传占位记录或返回可登记的 upload_id。
- 使用存储服务生成 upload URL。

**验证：**
- 运行 `pytest backend/tests/test_uploads.py -k presign_success -v`。
- 预期：登录用户 presign 成功测试通过。

### Step 3.5：为文件大小限制编写测试

**指令：**
- 新增测试，验证超过 20MB 的 presign 请求返回 413。
- 测试必须断言错误消息明确提示文件过大。

**验证：**
- 运行 `pytest backend/tests/test_uploads.py -k file_too_large -v`。
- 预期：测试先失败，失败原因指向大小限制不存在。

### Step 3.6：实现文件大小限制

**指令：**
- 在 presign 请求校验中拒绝超过 20MB 的文件。
- 返回 API 契约定义的错误格式。

**验证：**
- 运行 `pytest backend/tests/test_uploads.py -k file_too_large -v`。
- 预期：文件大小限制测试通过。

### Step 3.7：为 complete API 编写测试

**指令：**
- 新增测试，验证 `POST /api/uploads/complete` 需要登录。
- 新增测试，验证登录用户 complete 后数据库存在 `uploaded_assets` 记录。
- 测试必须断言记录包含 filename、mime_type、size_bytes、object_key、user_id。
- 测试必须断言 `job_id` 为空。

**验证：**
- 运行 `pytest backend/tests/test_uploads.py -k complete -v`。
- 预期：测试先失败，失败原因指向 complete 路由或数据库写入不存在。

### Step 3.8：实现 complete API

**指令：**
- 实现 `POST /api/uploads/complete`。
- 校验 object key 属于当前用户 uploads prefix。
- 写入或更新 `uploaded_assets`。
- 不读取、不执行上传文件内容。

**验证：**
- 运行 `pytest backend/tests/test_uploads.py -k complete -v`。
- 预期：complete API 测试通过。

---

## Step 4：实现 Games 列表和 Meta API ☑️ 已完成

**目标文件：**
- 新增：`backend/app/games.py`
- 修改：`backend/app/main.py`
- 新增测试：`backend/tests/test_games.py`
- 更新：`docs/architecture.md`、`docs/progress.md`

### Step 4.1：为 published 列表编写测试

**指令：**
- 新增测试数据，包含 published、draft、deleted 三种游戏。
- 测试游客调用 `GET /api/games`。
- 测试必须断言只返回 published 游戏。
- 测试必须断言响应包含 Home 卡片字段。

**验证：**
- 运行 `pytest backend/tests/test_games.py -k list_published -v`。
- 预期：测试先失败，失败原因指向路由不存在。

### Step 4.2：实现 published 游戏列表

**指令：**
- 新增 Games router 并挂载到 FastAPI 应用。
- 实现 `GET /api/games`。
- 默认只返回 published 游戏。
- 返回字段必须匹配 `docs/api-contract.md`。

**验证：**
- 运行 `pytest backend/tests/test_games.py -k list_published -v`。
- 预期：published 列表测试通过。

### Step 4.3：为排序编写测试

**指令：**
- 新增测试，分别验证 `sort=latest`、`sort=play_count`、`sort=like_count`。
- 测试数据必须能区分三种排序结果。
- 无效 sort 值必须返回 422 或 400。

**验证：**
- 运行 `pytest backend/tests/test_games.py -k sort -v`。
- 预期：测试先失败，失败原因指向排序未实现。

### Step 4.4：实现排序

**指令：**
- 实现 latest、play_count、like_count 三种排序。
- latest 按 published_at 倒序。
- play_count 和 like_count 均按计数倒序，并使用稳定次级排序。
- 拒绝 API 契约之外的 sort 值。

**验证：**
- 运行 `pytest backend/tests/test_games.py -k sort -v`。
- 预期：排序测试通过。

### Step 4.5：为搜索和标签筛选编写测试

**指令：**
- 新增测试，验证 `q` 可匹配标题、简介或作者展示名。
- 新增测试，验证 `tag` 只返回包含该标签的游戏。
- 新增测试，验证 `q` 和 `tag` 可组合使用。

**验证：**
- 运行 `pytest backend/tests/test_games.py -k "search or tag" -v`。
- 预期：测试先失败，失败原因指向搜索或标签筛选未实现。

### Step 4.6：实现搜索和标签筛选

**指令：**
- 实现标题、简介、作者展示名的搜索。
- 实现标签筛选。
- 保持只查询 published 游戏的约束。

**验证：**
- 运行 `pytest backend/tests/test_games.py -k "search or tag" -v`。
- 预期：搜索和标签筛选测试通过。

### Step 4.7：为游戏 meta 权限编写测试

**指令：**
- 新增测试，验证游客可以读取 published 游戏 meta。
- 新增测试，验证游客不能读取 draft 游戏 meta。
- 新增测试，验证 owner 可以读取自己的 draft 游戏 meta。
- 新增测试，验证非 owner 不能读取他人的 draft 游戏 meta。
- 测试必须断言响应包含 Play 左侧详情和 manifest URL 字段。

**验证：**
- 运行 `pytest backend/tests/test_games.py -k meta -v`。
- 预期：测试先失败，失败原因指向 meta 路由或权限未实现。

### Step 4.8：实现游戏 meta API

**指令：**
- 实现 `GET /api/games/{game_id}`。
- published 游戏公开可读。
- draft 游戏仅 owner 可读。
- deleted 游戏对普通用户不可读。
- 返回字段必须匹配 API 契约。

**验证：**
- 运行 `pytest backend/tests/test_games.py -k meta -v`。
- 预期：游戏 meta 权限测试通过。

---

## Step 5：实现点赞 API ☑️ 已完成

**目标文件：**
- 修改：`backend/app/games.py`
- 新增或修改测试：`backend/tests/test_likes.py`
- 更新：`docs/architecture.md`、`docs/progress.md`

### Step 5.1：为未登录点赞编写测试

**指令：**
- 新增测试，验证游客调用 `POST /api/games/{game_id}/like` 返回 401。
- 测试必须断言错误格式符合 API 契约。

**验证：**
- 运行 `pytest backend/tests/test_likes.py -k requires_login -v`。
- 预期：测试先失败，失败原因指向路由或权限不存在。

### Step 5.2：实现点赞登录保护

**指令：**
- 在 Games router 中新增点赞路由。
- 点赞 API 必须依赖当前用户。
- 未登录返回统一 401。

**验证：**
- 运行 `pytest backend/tests/test_likes.py -k requires_login -v`。
- 预期：未登录点赞测试通过。

### Step 5.3：为首次点赞编写测试

**指令：**
- 新增测试，验证登录用户首次点赞 published 游戏。
- 测试必须断言 `game_likes` 新增记录。
- 测试必须断言 `games.like_count` 增加。
- 测试必须断言响应包含 game_id、like_count、liked_by_me=true。

**验证：**
- 运行 `pytest backend/tests/test_likes.py -k first_like -v`。
- 预期：测试先失败，失败原因指向点赞逻辑未实现。

### Step 5.4：实现首次点赞

**指令：**
- 登录用户可对 published 游戏点赞。
- 点赞成功时写入 `game_likes` 并更新 `like_count`。
- 响应字段必须匹配 API 契约。

**验证：**
- 运行 `pytest backend/tests/test_likes.py -k first_like -v`。
- 预期：首次点赞测试通过。

### Step 5.5：为重复点赞和多用户点赞编写测试

**指令：**
- 新增测试，验证同一用户重复点赞不会增加计数。
- 新增测试，验证不同用户可以分别点赞同一个游戏。
- 新增测试，验证 draft 或 deleted 游戏不能被普通点赞。

**验证：**
- 运行 `pytest backend/tests/test_likes.py -k "duplicate or multiple_users or invalid_status" -v`。
- 预期：测试先失败，失败原因指向幂等或状态校验未实现。

### Step 5.6：实现点赞幂等和状态校验

**指令：**
- 同一用户重复点赞返回当前点赞状态，不新增记录，不增加计数。
- 只允许点赞 published 游戏。
- 不实现取消点赞。

**验证：**
- 运行 `pytest backend/tests/test_likes.py -v`。
- 预期：点赞 API 全部测试通过。

---

## Step 6：实现 Play Events API ☑️ 已完成

**目标文件：**
- 新增：`backend/app/play_events.py`
- 修改：`backend/app/main.py`
- 新增测试：`backend/tests/test_play_events.py`
- 更新：`docs/architecture.md`、`docs/progress.md`

### Step 6.1：为游客上报 view 编写测试

**指令：**
- 新增测试，验证游客可以调用 `POST /api/play-events` 上报 `view`。
- 测试必须断言数据库写入 `play_events`。
- 测试必须断言 `user_id` 为空。

**验证：**
- 运行 `pytest backend/tests/test_play_events.py -k guest_view -v`。
- 预期：测试先失败，失败原因指向路由不存在。

### Step 6.2：实现游客上报

**指令：**
- 新增 Play Events router 并挂载到 FastAPI 应用。
- 允许游客写入 play event。
- event 必须关联存在的 published 游戏。

**验证：**
- 运行 `pytest backend/tests/test_play_events.py -k guest_view -v`。
- 预期：游客 view 上报测试通过。

### Step 6.3：为登录用户上报编写测试

**指令：**
- 新增测试，验证登录用户上报时记录 `user_id`。
- 测试必须覆盖 `manifest_loaded`、`started`、`failed`、`timeout`、`exited` 中至少两个非 view 事件。

**验证：**
- 运行 `pytest backend/tests/test_play_events.py -k authenticated_user -v`。
- 预期：测试先失败，失败原因指向用户识别或事件类型未实现。

### Step 6.4：实现登录用户识别和事件类型校验

**指令：**
- 如果请求带有效 session，记录 `user_id`。
- 如果请求无 session，按游客处理。
- 只接受 API 契约定义的 event type。
- 无效 event type 返回 422 或 400。

**验证：**
- 运行 `pytest backend/tests/test_play_events.py -k authenticated_user -v`。
- 预期：登录用户事件测试通过。

### Step 6.5：为 play_count 计数规则编写测试

**指令：**
- 新增测试，明确只用 `view` 或只用 `started` 作为 play_count 增量触发点。
- 测试必须验证同一次实现不会让 `view` 和 `started` 都增加计数。
- 新增测试，验证 `failed`、`timeout`、`exited` 不增加 play_count。

**验证：**
- 运行 `pytest backend/tests/test_play_events.py -k play_count -v`。
- 预期：测试先失败，失败原因指向计数规则未实现。

### Step 6.6：实现 play_count 计数规则

**指令：**
- 选择一种计数触发事件，并在代码和 progress 中记录选择。
- 其他事件只记录日志，不增加 play_count。
- 保证并发请求不会产生明显负计数或覆盖计数。

**验证：**
- 运行 `pytest backend/tests/test_play_events.py -k play_count -v`。
- 预期：play_count 计数测试通过。

### Step 6.7：为 metadata 脱敏编写测试

**指令：**
- 新增测试，提交 metadata 中包含敏感字段名或完整签名 URL。
- 测试必须断言保存后的 metadata 不包含 secret、token、password、OAuth code 或完整 presigned URL 签名。

**验证：**
- 运行 `pytest backend/tests/test_play_events.py -k metadata_sanitized -v`。
- 预期：测试先失败，失败原因指向 metadata 未脱敏。

### Step 6.8：实现 metadata 脱敏

**指令：**
- 保存 metadata 前移除敏感字段。
- 对 URL 字段只保留非敏感摘要或 URL 类型。
- 不影响 stage、duration_ms、error_code、url_type 等允许字段。

**验证：**
- 运行 `pytest backend/tests/test_play_events.py -v`。
- 预期：Play Events API 全部测试通过。

---

## Step 7：实现 Create Sessions API

**目标文件：**
- 新增：`backend/app/create_sessions.py`
- 修改：`backend/app/main.py`
- 修改：`backend/app/models.py`
- 新增或修改测试：`backend/tests/test_create_sessions.py`
- 更新：`docs/architecture.md`、`docs/progress.md`

### Step 7.1：为 Create Sessions 表编写迁移测试 ☑️ 已完成

**指令：**
- 新增迁移测试，验证存在 `create_sessions` 表。
- 测试必须断言字段覆盖 user、status、user requirements、game plan、material usage、assistant response、created/updated/confirmed 时间。
- 测试必须断言 status 支持 `collecting`、`ready_to_confirm`、`confirmed`、`error`。
- 测试必须断言 `user_id` 关联 `users.user_id`。
- 测试必须断言 `confirmed_at` 允许为空。

**验证：**
- 运行 `pytest backend/tests/test_migrations.py -k create_sessions -v`。
- 预期：测试先失败，失败原因指向 `create_sessions` 表或字段不存在。

### Step 7.2：实现 Create Sessions 表迁移 ☑️ 已完成

**指令：**
- 新增 `create_sessions` 表和对应 model。
- `user_id` 必须关联 `users.user_id`。
- `user_requirements`、`game_plan`、`material_usage`、`assistant_response` 必须使用 JSON 字段。
- 为 `user_id`、`status`、`created_at`、`updated_at` 建立索引。
- 不在该表保存完整 presigned URL、API key、token 或 secret。

**验证：**
- 运行 `pytest backend/tests/test_migrations.py -k create_sessions -v`。
- 预期：Create Sessions 表结构测试通过。

### Step 7.3：为 uploaded_assets 会话绑定编写迁移测试 ☑️ 已完成

**指令：**
- 新增迁移测试，验证 `uploaded_assets` 存在 nullable `session_id` 字段。
- 测试必须断言 `session_id` 可为空，以支持文件先上传、进入 Create 会话后再绑定。
- 测试必须断言 `session_id` 可以关联 `create_sessions.id`。
- 测试必须断言 `session_id` 有索引或可用于 owner 会话素材查询。

**验证：**
- 运行 `pytest backend/tests/test_migrations.py -k uploaded_assets_session -v`。
- 预期：测试先失败，失败原因指向 `uploaded_assets.session_id` 不存在。

### Step 7.4：实现 uploaded_assets 会话绑定迁移 ☑️ 已完成

**指令：**
- 为 `uploaded_assets` 增加 nullable `session_id` 字段。
- `session_id` 必须允许为空，并在用户把素材加入 Create 会话后可更新。
- 为 `session_id` 建立索引。
- 保持现有 `job_id` 绑定生成任务的能力不变。

**验证：**
- 运行 `pytest backend/tests/test_migrations.py -k uploaded_assets_session -v`。
- 预期：uploaded_assets 会话绑定迁移测试通过。

### Step 7.5：为创建会话登录权限编写测试 ☑️ 已完成

**指令：**
- 新增测试，验证未登录调用 `POST /api/create-sessions` 返回 401。
- 测试必须断言错误格式符合 API 契约。

**验证：**
- 运行 `pytest backend/tests/test_create_sessions.py -k create_requires_login -v`。
- 预期：测试先失败，失败原因指向 Create Sessions 路由不存在。

### Step 7.6：实现创建会话登录保护 ☑️ 已完成

**指令：**
- 新增 Create Sessions router 并挂载到 FastAPI 应用。
- 创建会话必须依赖当前用户。
- 初始状态必须是 `collecting`，并初始化 `user_requirements`、`game_plan`、`material_usage`、`assistant_response`。

**验证：**
- 运行 `pytest backend/tests/test_create_sessions.py -k create_requires_login -v`。
- 预期：未登录创建会话测试通过。

### Step 7.7：为初始消息和素材绑定编写测试 ☑️ 已完成

**指令：**
- 新增测试，验证登录用户提交 `initial_message` 后会创建 Create Session。
- 新增测试，验证 `asset_ids` 必须属于当前用户。
- 新增测试，验证会话创建时可把当前用户素材绑定到 `uploaded_assets.session_id`。
- 测试必须断言绑定素材时不写入 `job_id`。

**验证：**
- 运行 `pytest backend/tests/test_create_sessions.py -k "initial_message or asset_binding" -v`。
- 预期：测试先失败，失败原因指向初始消息处理或素材绑定未实现。

### Step 7.8：实现初始消息和素材绑定 ☑️ 已完成

**指令：**
- 创建会话时保存 owner、状态和初始 JSON 状态。
- 如果存在 `initial_message`，通过后端 conversation runner 调用 `lan_agents.conversation_graph`，生成第一轮 `assistant_response` 和基础 `user_requirements`。
- 校验所有 `asset_ids` 属于当前用户。
- 将素材绑定到当前 `session_id`，保持 `job_id` 为空。
- 响应字段必须匹配 `docs/api-contract.md` 的 Create Sessions API。

**验证：**
- 运行 `pytest backend/tests/test_create_sessions.py -k "initial_message or asset_binding" -v`。
- 预期：初始消息和素材绑定测试通过。

### Step 7.9：为事件权限和类型校验编写测试 ☑️ 已完成

**指令：**
- 新增测试，验证非 owner 不能访问 `POST /api/create-sessions/{session_id}/events`。
- 新增测试，验证不支持的事件类型返回统一 400 错误。
- 新增测试，验证 `chat` 事件缺少 `message` 时返回统一 422 或 400 错误。
- 新增测试，验证响应不包含完整 presigned URL、API key、token 或 secret。

**验证：**
- 运行 `pytest backend/tests/test_create_sessions.py -k "event_permissions or invalid_event" -v`。
- 预期：测试先失败，失败原因指向事件路由或校验未实现。

### Step 7.10：实现事件权限和类型校验 ☑️ 已完成

**指令：**
- 实现 `POST /api/create-sessions/{session_id}/events`。
- 只允许 owner 发送事件。
- 支持 `chat`、`upload_assets`、`regenerate`、`confirm` 四类事件。
- 对未知事件、缺少必填字段、跨用户素材访问返回统一错误格式。
- 所有响应和日志都必须脱敏。

**验证：**
- 运行 `pytest backend/tests/test_create_sessions.py -k "event_permissions or invalid_event" -v`。
- 预期：事件权限和类型校验测试通过。

### Step 7.11：为 chat 事件编写测试 ☑️ 已完成

**指令：**
- 新增测试，验证 `chat` 事件会更新 `user_requirements`、`game_plan`、`material_usage`。
- 测试必须断言 `assistant_response.suggestions` 是字符串列表。
- 测试必须断言建议答案每条简短，并结合已有用户需求。
- 测试必须断言 `assistant_response.card` 只包含 `plan_id`、`title`、`introduction`、`tags`。

**验证：**
- 运行 `pytest backend/tests/test_create_sessions.py -k chat_event -v`。
- 预期：测试先失败，失败原因指向 conversation 事件处理未实现。

### Step 7.12：实现 chat 事件 conversation runner ☑️ 已完成

**指令：**
- 在后端封装一个可替换的 conversation runner 边界，并通过该边界调用 `lan_agents.conversation_graph`。
- runner 必须接收当前 `user_requirements`、`game_plan`、`material_usage` 和 `chat` 事件。
- runner 必须返回更新后的三个业务主状态和 `assistant_response`。
- `assistant_response.card` 必须从 `game_plan` 派生，不作为独立持久化来源。

**验证：**
- 运行 `pytest backend/tests/test_create_sessions.py -k chat_event -v`。
- 预期：chat 事件测试通过。

### Step 7.13：为 upload_assets 事件编写测试 ☑️ 已完成

**指令：**
- 新增测试，验证 `upload_assets` 事件只更新 `material_usage.assets`。
- 测试必须断言不会创建 `generation_job`。
- 测试必须断言上传素材用途结合已有 `user_requirements` 或 `game_plan` 给出保守用途。
- 测试必须断言素材仍归当前 owner 所有。

**验证：**
- 运行 `pytest backend/tests/test_create_sessions.py -k upload_assets_event -v`。
- 预期：测试先失败，失败原因指向素材事件处理未实现。

### Step 7.14：实现 upload_assets 事件 ☑️ 已完成

**指令：**
- 处理 `upload_assets` 事件时校验素材归属。
- 只更新 `material_usage.assets` 和对应 `uploaded_assets.session_id`。
- 不做深度多模态分析，不写全局素材总结，不创建任务。
- 响应中继续返回由当前 `game_plan` 派生的卡片。

**验证：**
- 运行 `pytest backend/tests/test_create_sessions.py -k upload_assets_event -v`。
- 预期：upload_assets 事件测试通过。

### Step 7.15：为 regenerate 事件编写测试 ☑️ 已完成

**指令：**
- 新增测试，验证 `regenerate` 会生成新的 `game_plan.plan_id`。
- 测试必须断言保留 `user_requirements.must_have`、`constraints` 和 `material_usage.assets`。
- 测试必须断言返回新的 `assistant_response.card`。

**验证：**
- 运行 `pytest backend/tests/test_create_sessions.py -k regenerate_event -v`。
- 预期：测试先失败，失败原因指向换一换逻辑未实现。

### Step 7.16：实现 regenerate 事件 ☑️ 已完成

**指令：**
- 处理 `regenerate` 时保留用户需求和素材用途。
- 只刷新当前 `game_plan` 和由它派生的卡片。
- 不丢失已上传素材，不创建 `generation_job`。

**验证：**
- 运行 `pytest backend/tests/test_create_sessions.py -k regenerate_event -v`。
- 预期：regenerate 事件测试通过。

### Step 7.17：为 confirm 事件编写测试 ☑️ 已完成

**指令：**
- 新增测试，验证 `confirm` 只有在 `game_plan` 覆盖标题、介绍、标签、玩法、风格、角色、胜负条件时成功。
- 新增测试，验证已上传素材必须存在 `material_usage.assets` 用途记录。
- 测试必须断言成功后状态为 `confirmed`，写入 `confirmed_at`，并返回 `handoff_to_generation=true`。
- 测试必须断言 `confirm` 不创建 `generation_job`。

**验证：**
- 运行 `pytest backend/tests/test_create_sessions.py -k confirm_event -v`。
- 预期：测试先失败，失败原因指向确认逻辑未实现。

### Step 7.18：实现 confirm 事件 ☑️ 已完成

**指令：**
- 校验当前 `game_plan` 和 `material_usage` 完整性。
- 成功后将 Create Session 状态更新为 `confirmed` 并写入 `confirmed_at`。
- 返回 `handoff_to_generation=true`。
- 不在本接口创建后台生成任务。

**验证：**
- 运行 `pytest backend/tests/test_create_sessions.py -k confirm_event -v`。
- 预期：confirm 事件测试通过。

### Step 7.19：为会话读取编写测试 ☑️ 已完成

**指令：**
- 新增测试，验证 owner 可以调用 `GET /api/create-sessions/{session_id}` 恢复当前状态。
- 新增测试，验证非 owner 读取返回 404 或 403。
- 测试必须断言返回 `user_requirements`、`game_plan`、`material_usage`、最近 `assistant_response`。

**验证：**
- 运行 `pytest backend/tests/test_create_sessions.py -k get_session -v`。
- 预期：测试先失败，失败原因指向读取接口未实现。

### Step 7.20：实现会话读取并完成 Create Sessions API 验证 ☑️ 已完成

**指令：**
- 实现 `GET /api/create-sessions/{session_id}`。
- 只允许 owner 读取。
- 响应必须匹配 `docs/api-contract.md`。
- 更新 `docs/architecture.md` 和 `docs/progress.md`。

**验证：**
- 运行 `pytest backend/tests/test_create_sessions.py -v`。
- 运行 `pytest backend/tests -q`。
- 预期：Create Sessions API 测试和后端全量测试通过。

### Step 7.21：为 Create Session 消息历史编写迁移测试 ☑️ 已完成

**指令：**
- 新增迁移测试，验证存在 `create_session_messages` 表。
- 测试必须断言字段覆盖 `session_id`、`role`、`content`、`payload`、`created_at`。
- 测试必须断言 `session_id` 关联 `create_sessions.id`。
- 测试必须断言 `role` 支持 `user / assistant / system`。
- 测试必须断言可按 `session_id, created_at` 查询消息历史。

**验证：**
- 运行 `pytest backend/tests/test_migrations.py -k create_session_messages -v`。
- 预期：测试先失败，失败原因指向消息历史表不存在。

### Step 7.22：实现 Create Session 消息历史表 ☑️ 已完成

**指令：**
- 新增 `create_session_messages` 表和对应 model。
- `POST /api/create-sessions` 只创建新会话，不承担历史恢复职责。
- `GET /api/create-sessions/{session_id}` 只读取已有会话，不创建新会话。
- 消息 `payload` 可保存建议答案、卡片快照、附件摘要和事件类型；不得保存完整 presigned URL 签名、token、API key 或 secret。
- 为 `session_id` 和 `created_at` 建立查询索引。

**验证：**
- 运行 `pytest backend/tests/test_migrations.py -k create_session_messages -v`。
- 预期：消息历史表结构测试通过。

### Step 7.23：为 Create Session 消息写入编写测试 ☑️ 已完成

**指令：**
- 新增测试，验证 `POST /api/create-sessions` 带 `initial_message` 时写入用户消息和 AI 消息。
- 新增测试，验证 `chat` 事件追加一条用户消息和一条 AI 消息。
- 新增测试，验证 `upload_assets / regenerate / confirm` 事件追加可回看的事件消息或带 `payload.event_type` 的消息。
- 测试必须断言消息按创建时间正序返回。

**验证：**
- 运行 `pytest backend/tests/test_create_sessions.py -k session_messages -v`。
- 预期：测试先失败，失败原因指向消息历史未写入或未返回。

### Step 7.24：实现 Create Session 消息写入和返回 ☑️ 已完成

**指令：**
- 在创建会话、聊天、上传素材、换一换和确认事件处理后写入 `create_session_messages`。
- `GET /api/create-sessions/{session_id}`、`POST /api/create-sessions` 和 `POST /api/create-sessions/{session_id}/events` 响应都返回 `messages`。
- `assistant_response` 继续表示最近一轮 AI 回复；聊天气泡以 `messages` 为准。
- 不把消息历史作为 Agent 状态事实来源；Agent 状态事实来源仍是 `user_requirements`、`game_plan` 和 `material_usage`。

**验证：**
- 运行 `pytest backend/tests/test_create_sessions.py -k session_messages -v`。
- 运行 `pytest backend/tests/test_create_sessions.py -v`。
- 预期：消息历史写入、读取和既有 Create Sessions API 测试通过。

---

## Step 8：改造 Jobs API 与 Agent Runner 输入边界

**目标文件：**
- 修改：`backend/app/jobs.py`
- 修改：`backend/app/agent_runner.py`
- 修改：`backend/app/models.py`
- 修改测试：`backend/tests/test_jobs.py`
- 修改测试：`backend/tests/test_agent_runner.py`
- 更新：`docs/architecture.md`、`docs/progress.md`

### Step 8.1：为 generation_jobs 会话快照和 revision 字段编写迁移测试 ☑️ 已完成

**指令：**
- 新增迁移测试，验证 `generation_jobs` 存在 nullable `create_session_id` 字段。
- 新增迁移测试，验证 `generation_jobs` 存在 nullable `parent_job_id` 和 `revision_intent` 字段。
- 新增迁移测试，验证 `generation_jobs` 存在 `user_requirements`、`game_plan`、`material_usage` JSON 字段。
- 测试必须断言旧 `confirmation` 字段不再作为新的 Jobs API 入参来源；如果保留该字段，只能作为兼容或待废弃快照。
- 测试必须断言 `create_session_id` 可为空，以兼容历史任务。
- 测试必须断言 `parent_job_id` 可为空，以区分初始生成任务和 revision job。

**验证：**
- 运行 `pytest backend/tests/test_migrations.py -k generation_jobs_session_snapshot -v`。
- 预期：测试先失败，失败原因指向 generation_jobs 会话快照字段不存在。

### Step 8.2：实现 generation_jobs 会话快照和 revision 字段迁移 ☑️ 已完成

**指令：**
- 为 `generation_jobs` 增加 nullable `create_session_id` 字段。
- 为 `generation_jobs` 增加 nullable `parent_job_id` 和 `revision_intent` 字段。
- 为 `generation_jobs` 增加 `user_requirements`、`game_plan`、`material_usage` JSON 字段，用于保存用户确认时的快照。
- `create_session_id` 必须允许为空以兼容历史任务，但新 Jobs API 创建的任务必须写入。
- 为 `create_session_id` 建立索引。
- 为 `parent_job_id` 建立索引，并关联 `generation_jobs.id`。

**验证：**
- 运行 `pytest backend/tests/test_migrations.py -k generation_jobs_session_snapshot -v`。
- 预期：generation_jobs 会话快照字段迁移测试通过。

### Step 8.3：为 Jobs API 新入参编写测试 ☑️ 已完成

**指令：**
- 新增或修改测试，验证未登录调用 `POST /api/jobs` 返回 401。
- 新增测试，验证 `POST /api/jobs` 只需要 `session_id`。
- 新增测试，验证前端提交的 `user_requirements`、`game_plan`、`material_usage` 不会被信任或覆盖后端快照。

**验证：**
- 运行 `pytest backend/tests/test_jobs.py -k "create_requires_login or session_id_only" -v`。
- 预期：测试先失败，失败原因指向 Jobs API 仍使用旧 `confirmation` 入参。

### Step 8.4：实现 Jobs API 新入参 ☑️ 已完成

**指令：**
- 将创建任务请求改为只接收 `session_id` 和可选 `prompt`。
- 根据 `session_id` 读取 owner 的 Create Session。
- 只有状态为 `confirmed` 的 Create Session 可以创建任务。
- 从 Create Session 读取 `user_requirements`、`game_plan`、`material_usage` 快照写入 `generation_jobs`。
- 新任务必须写入 `create_session_id`，响应字段同时返回 `session_id`。
- 不再从请求体读取旧 `confirmation` 字段。

**验证：**
- 运行 `pytest backend/tests/test_jobs.py -k "create_requires_login or session_id_only" -v`。
- 预期：Jobs API 新入参测试通过。

### Step 8.5：为会话权限和重复创建编写测试 ☑️ 已完成

**指令：**
- 新增测试，验证非 owner 不能用别人的 `session_id` 创建任务。
- 新增测试，验证未 confirmed 会话不能创建任务。
- 新增测试，验证同一个 confirmed 会话只能创建一个初始生成任务；后续修改必须走 revision job。

**验证：**
- 运行 `pytest backend/tests/test_jobs.py -k "session_ownership or session_status or duplicate_session" -v`。
- 预期：测试先失败，失败原因指向会话权限或重复创建规则未实现。

### Step 8.6：实现会话权限和重复创建规则 ☑️ 已完成

**指令：**
- 只允许 owner 使用自己的 confirmed Create Session 创建任务。
- MVP 同一个 confirmed 会话只允许创建一个初始生成任务；重新生成和生成后修改通过后续 revision job 承接。
- 每个任务都保存创建时的会话快照。
- 响应必须匹配 `docs/api-contract.md`。

**验证：**
- 运行 `pytest backend/tests/test_jobs.py -k "session_ownership or session_status or duplicate_session" -v`。
- 预期：会话权限和重复创建规则测试通过。

### Step 8.7：为素材绑定到任务编写测试 ☑️ 已完成

**指令：**
- 新增测试，验证任务创建时只绑定当前 session 的素材。
- 新增测试，验证单任务最多绑定 5 个素材。
- 新增测试，验证素材绑定到 `job_id` 后仍保留 `session_id`。
- 新增测试，验证响应和日志不暴露完整 presigned URL 签名。

**验证：**
- 运行 `pytest backend/tests/test_jobs.py -k "asset_binding or asset_limit" -v`。
- 预期：测试先失败，失败原因指向素材绑定仍按旧 `asset_ids` 请求体处理。

### Step 8.8：实现素材绑定到任务 ☑️ 已完成

**指令：**
- 创建任务时从 `material_usage.assets` 或当前 session 绑定素材中解析素材 ID。
- 校验素材属于当前用户且 `session_id` 匹配。
- 单任务最多绑定 5 个素材。
- 创建成功后把对应 `uploaded_assets.job_id` 写为当前任务 ID。

**验证：**
- 运行 `pytest backend/tests/test_jobs.py -k "asset_binding or asset_limit" -v`。
- 预期：素材绑定到任务测试通过。

### Step 8.9：为 Agent Runner 输入边界编写测试 ☑️ 已完成

**指令：**
- 修改 runner 输入测试，验证后端调用 runner 时传入 job_id、user_id、session_id、prompt、user_requirements、game_plan、material_usage、uploaded_assets。
- 测试必须验证 runner 输入包含 `session_id` 和会话快照；旧 `confirmation` 仅作为从 `game_plan` 派生的兼容快照。
- 测试必须验证 uploaded_assets 不包含完整 presigned URL 签名。

**验证：**
- 运行 `pytest backend/tests/test_agent_runner.py -k runner_input -v`。
- 预期：测试先失败，失败原因指向 runner 输入仍使用旧 confirmation 模型。

### Step 8.10：实现 Agent Runner 新输入边界 ☑️ 已完成

**指令：**
- 更新 `AgentRunInput`，加入 `session_id`、`user_requirements`、`game_plan`、`material_usage`。
- `confirmation` 仅保留为从 `game_plan` 派生的兼容快照，不再来自 Jobs 请求体。
- 保留 fake runner，可被测试配置为 success 或 failure。
- 不在本 Step 接真实 `lan_agents` generation graph。

**验证：**
- 运行 `pytest backend/tests/test_agent_runner.py -k runner_input -v`。
- 预期：runner 新输入边界测试通过。

### Step 8.11：为任务状态流编写测试 ☑️ 已完成

**指令：**
- 新增或修改测试，验证创建任务后 BackgroundTasks 会使状态从 pending 进入 running。
- 新增或修改测试，验证 fake success 后任务变为 succeeded。
- 新增或修改测试，验证 fake failure 后任务变为 failed 并保存 error_message。
- 测试必须断言状态流使用新 runner 输入快照。

**验证：**
- 运行 `pytest backend/tests/test_agent_runner.py -k status_flow -v`。
- 预期：测试先失败，失败原因指向后台执行流仍依赖旧模型。

### Step 8.12：实现任务状态流 ☑️ 已完成

**指令：**
- 创建任务后注册后台执行任务。
- 执行开始时更新为 running。
- fake success 后更新为 succeeded。
- fake failure 后更新为 failed 并写入 error_message。
- 每次状态变化都写入 Agent 日志。

**验证：**
- 运行 `pytest backend/tests/test_agent_runner.py -k status_flow -v`。
- 预期：任务状态流测试通过。

### Step 8.13：为 draft game 创建编写测试 ☑️ 已完成

**指令：**
- 新增或修改测试，验证 fake success 会创建 draft game。
- 测试必须断言 draft game 的标题、简介、标签优先来自 runner 成功结果。
- 测试必须断言 runner 未返回标题、简介或标签时，可回退到 `generation_jobs.game_plan`。
- 测试必须断言 job 关联 game_id、artifact_prefix、manifest_url 和 artifact_base_url。

**验证：**
- 运行 `pytest backend/tests/test_agent_runner.py -k draft_game -v`。
- 预期：测试先失败，失败原因指向 draft game 新快照回退逻辑未实现。

### Step 8.14：实现 draft game 创建 ☑️ 已完成

**指令：**
- fake success 结果必须转成 draft game 记录。
- draft game owner 必须是任务创建者。
- 保存 manifest_url、artifact_base_url、标题、简介、标签、封面等 meta。
- 当 runner 成功结果缺少可展示 meta 时，使用任务保存的 `game_plan` 快照兜底。

**验证：**
- 运行 `pytest backend/tests/test_agent_runner.py -v`。
- 运行 `pytest backend/tests/test_jobs.py -v`。
- 运行 `pytest backend/tests -q`。
- 预期：Agent Runner 和 Jobs API 测试全部通过。

### Step 8.15：为 Jobs 查询返回 session_id 编写测试 ☑️ 已完成

**指令：**
- 新增或修改测试，验证 `GET /api/jobs` 的每个任务项返回 `session_id`。
- 新增或修改测试，验证 `GET /api/jobs/{job_id}` 返回 `session_id`、`parent_job_id` 和任务关联信息。
- 测试必须覆盖历史任务 `create_session_id=null` 时返回 `session_id=null`。

**验证：**
- 运行 `pytest backend/tests/test_jobs.py -k "list_returns_session or detail_returns_session" -v`。
- 预期：测试先失败，失败原因指向 Jobs 查询响应缺少会话关联字段。

### Step 8.16：实现 Jobs 查询返回 session_id ☑️ 已完成

**指令：**
- `GET /api/jobs` 每个任务项必须返回 `session_id`，值来自 `generation_jobs.create_session_id`。
- `GET /api/jobs/{job_id}` 必须返回 `session_id`、`parent_job_id`、任务状态、draft game 信息和产物地址。
- 不返回完整 presigned URL 签名或敏感字段。

**验证：**
- 运行 `pytest backend/tests/test_jobs.py -k "list_returns_session or detail_returns_session" -v`。
- 预期：Jobs 查询会话关联字段测试通过。

### Step 8.17：为 revision job 契约编写测试 ☑️ 已完成

**指令：**
- 新增测试，验证 `pending / running` 任务不能创建 revision job，返回 409。
- 新增测试，验证 `succeeded / failed` 任务可基于用户修改消息创建新的 revision job。
- 测试必须断言新 job 的 `parent_job_id` 指向上一版任务。
- 测试必须断言新 job 保留原任务的 `create_session_id`，但保存新的 `revision_intent`。
- 测试必须断言旧 job、旧 draft 和旧快照不被覆盖。

**验证：**
- 运行 `pytest backend/tests/test_jobs.py -k revision_job -v`。
- 预期：测试先失败，失败原因指向 revision job 接口或模型尚未实现。

### Step 8.18：实现 revision job 最小契约 ☑️ 已完成

**指令：**
- 新增 `POST /api/jobs/{job_id}/revisions` 或等价内部服务，作为生成后聊天修改入口。
- 只允许 owner 对自己的 `succeeded / failed` 任务创建 revision job。
- 基于原任务的 `user_requirements`、`game_plan`、`material_usage`、已生成 draft 信息和新消息生成 revision patch 或 `revision_intent`。
- MVP 可先保存 patch 意图并复用现有 fake runner 重新生成 draft；不得覆盖旧任务和旧产物。
- 新 revision job 创建后进入 `pending`，后台状态流与普通 job 一致。

**验证：**
- 运行 `pytest backend/tests/test_jobs.py -k revision_job -v`。
- 运行 `pytest backend/tests/test_agent_runner.py -v`。
- 预期：revision job 契约和任务状态流测试通过。

---

## Step 9：实现 Publish API

**目标文件：**
- 修改：`backend/app/games.py`
- 新增或修改测试：`backend/tests/test_publish.py`
- 更新：`docs/architecture.md`、`docs/progress.md`

### Step 9.1：为发布权限编写测试 ☑️ 已完成

**指令：**
- 新增测试，验证游客不能发布 draft。
- 新增测试，验证非 owner 不能发布别人的 draft。
- 新增测试，验证 owner 可以发布自己的 draft。

**验证：**
- 运行 `pytest backend/tests/test_publish.py -k publish_permissions -v`。
- 预期：测试先失败，失败原因指向发布路由不存在。

### Step 9.2：实现发布权限 ☑️ 已完成

**指令：**
- 实现 `POST /api/games/{game_id}/publish`。
- 只允许 owner 发布自己的 draft。
- 非 draft 状态不能重复发布。

**验证：**
- 运行 `pytest backend/tests/test_publish.py -k publish_permissions -v`。
- 预期：发布权限测试通过。

### Step 9.3：为发布产物转存编写测试 ☑️ 已完成

**指令：**
- 新增测试，验证发布时将 draft 产物复制或转存到 `published/*`。
- 测试必须断言发布后 manifest_url 是 public-read URL。
- 测试必须断言 artifact_base_url 指向 published prefix。

**验证：**
- 运行 `pytest backend/tests/test_publish.py -k artifact_publish -v`。
- 预期：测试先失败，失败原因指向产物转存未实现。

### Step 9.4：实现产物转存 ☑️ 已完成

**指令：**
- 发布时把 draft bundle 复制或转存到 published prefix。
- 更新 manifest_url 和 artifact_base_url。
- 不把 uploads 原始素材公开。

**验证：**
- 运行 `pytest backend/tests/test_publish.py -k artifact_publish -v`。
- 预期：产物转存测试通过。

### Step 9.5：为发布后列表可见编写测试 ☑️ 已完成

**指令：**
- 新增测试，验证发布成功后 status 为 published。
- 测试必须断言 published_at 被写入。
- 测试必须断言发布后游戏出现在 `GET /api/games`。
- 测试必须断言没有发布后 meta 编辑接口。

**验证：**
- 运行 `pytest backend/tests/test_publish.py -k published_visible -v`。
- 预期：测试先失败，失败原因指向发布状态更新不完整。

### Step 9.6：实现发布状态更新 ☑️ 已完成

**指令：**
- 发布成功后更新 status、published_at、manifest_url、artifact_base_url。
- 保持标题、简介、标签、封面来自 draft meta。
- 不新增发布后编辑接口。

**验证：**
- 运行 `pytest backend/tests/test_publish.py -v`。
- 预期：Publish API 测试全部通过。

---

## Step 10：准备 Seed 游戏数据 ☑️ 已完成

**目标文件：**
- 新增：`backend/app/seed.py`
- 新增：`backend/tests/test_seed.py`
- 新增或修改：`scripts/seed_backend.py`
- 更新：`docs/architecture.md`、`docs/progress.md`

### Step 10.1：为 seed 数据编写测试

**指令：**
- 新增测试，验证 seed 过程会创建至少 2 个 published 游戏。
- 每个 seed 游戏必须包含 cover、title、author、description、tags、published_at、manifest_url、artifact_base_url、play_count、like_count。
- seed 过程重复执行不能重复创建相同游戏。

**验证：**
- 运行 `pytest backend/tests/test_seed.py -k seed_games -v`。
- 预期：测试先失败，失败原因指向 seed 能力不存在。

### Step 10.2：实现 seed 数据写入

**指令：**
- 新增后端 seed 入口。
- 创建至少 2 个 published 示例游戏。
- 示例游戏产物必须符合 manifest、index、style、game、assets 的静态 bundle 结构。
- 不依赖前端页面实现。

**验证：**
- 运行 `pytest backend/tests/test_seed.py -k seed_games -v`。
- 预期：seed 数据测试通过。

### Step 10.3：为 seed 产物可访问性编写测试

**指令：**
- 新增测试或 Compose 验证，确认每个 seed 游戏 manifest URL 可 public 读取。
- 新增测试或 Compose 验证，确认 entry URL 可被浏览器或 HTTP client 读取。
- 新增测试，确认 Play meta 字段满足 API 契约。

**验证：**
- 运行 `pytest backend/tests/test_seed.py -k seed_artifacts -v`，或运行记录在 README/progress 中的 Compose 验证命令。
- 预期：seed 游戏 manifest、entry 和 meta 均可访问。

### Step 10.4：实现 seed 产物上传

**指令：**
- seed 过程必须把静态 bundle 上传到 `published/*`。
- 数据库中的 manifest_url 和 artifact_base_url 必须指向 public-read 地址。
- seed 不写入真实用户密钥或 OAuth 信息。

**验证：**
- 运行 `pytest backend/tests/test_seed.py -v`。
- 预期：seed 测试全部通过。

---

## Step 11：后端端到端验收

**目标文件：**
- 新增或修改：`backend/tests/test_backend_e2e.py`
- 更新：`README.md` 或 `docs/progress.md` 中的后端验收命令

### Step 11.1：编写端到端测试清单

**指令：**
- 新增后端端到端测试，覆盖注册、登录、上传 presign、上传 complete、创建 Create Session、发送 `chat`、`upload_assets`、`regenerate`、`confirm` 事件、基于 confirmed `session_id` 创建任务、任务查询返回 `session_id`、fake success、生成后 revision job、读取 draft、发布、列表出现、Play Events 上报。
- 测试必须断言 Jobs API 不接收或不信任前端提交的 `game_plan`、`material_usage` 快照。
- 测试必须断言生成任务使用 Create Session 中已确认的 `user_requirements`、`game_plan`、`material_usage`。
- 测试必须覆盖游客、owner、非 owner 三类权限。
- 测试必须覆盖统一错误格式。

**验证：**
- 运行 `pytest backend/tests/test_backend_e2e.py -v`。
- 预期：测试先失败，失败原因指向尚未串联完整流程。

### Step 11.2：补齐端到端缺口

**指令：**
- 根据端到端测试失败点，只补齐本计划已定义能力中的遗漏。
- 不新增本计划范围外功能。
- 修复后记录发现的接口或权限边界。

**验证：**
- 运行 `pytest backend/tests/test_backend_e2e.py -v`。
- 预期：端到端测试通过。

### Step 11.3：执行后端全量验证

**指令：**
- 运行后端全部测试。
- 运行 Alembic 当前版本检查。
- 运行 Docker Compose 配置检查。
- 验证 backend `/health` 和 `/ready`。
- 验证 MinIO published public-read、uploads/drafts private。

**验证：**
- 运行 `pytest backend/tests -v`。
- 运行 `docker compose config --quiet`。
- 运行 `docker compose exec -T backend alembic current`。
- 运行 `curl -i http://127.0.0.1:8000/health`。
- 运行 `curl -i http://127.0.0.1:8000/ready`。
- 预期：全部命令成功，HTTP health 和 ready 返回 200。

---

## 12. 完成判定

后端完成时必须同时满足：

- 所有 backend tests 通过。
- 从空数据库执行迁移成功。
- Auth、Uploads、Games、Likes、Jobs、Play Events、Publish API 均可通过 HTTP 测试验证。
- Create Sessions API 可通过 HTTP 测试验证，且 `chat / upload_assets / regenerate / confirm` 四类事件行为符合 `docs/api-contract.md`。
- Jobs API 只从 confirmed Create Session 创建任务，不以旧 `confirmation` 作为新任务输入。
- published 产物 public-read，uploads 和 drafts 不可 public-read。
- draft 资源只允许 owner 读取。
- 游客可以读取 Home 列表和 published Play meta。
- 游客不能点赞、上传、创建任务、发布或读取 draft。
- 同一用户重复点赞不增加 like_count。
- Play Events 不保存敏感 metadata。
- Seed 至少提供 2 个 published 静态游戏。
- `docs/architecture.md` 和 `docs/progress.md` 已更新。
- `docs/api-contract.md` 未出现与实现不一致的字段名、状态码或错误格式。
