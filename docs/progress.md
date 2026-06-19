# 项目进度记录

本文档记录已实现功能、对应实施计划 step，以及尚未落地或需要补齐的边界。项目 layer、目录边界和文件职责维护在 [architecture.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/architecture.md)。

## 已实现功能索引

- 仓库基线：保留原始需求、设计文档、技术栈、实施计划和架构记录；通过 `.gitignore` 排除本地依赖、构建产物、虚拟环境和缓存（Step 0.1）。
- 目录结构：建立 `frontend/`、`backend/`、`deployment/`、`scripts/`、`docs/` 的清晰边界，并通过 `.gitkeep` 保留暂未放置业务文件的目录（Step 0.2）。
- 环境变量样例：提供前端、后端、PostgreSQL、MinIO、Session、OpenAI-compatible API 和 Mock provider 变量样例，并使用占位值避免真实密钥（Step 0.3）。
- Docker Compose 基线：定义 PostgreSQL、MinIO、backend、frontend 服务，包含持久化 volume、健康检查、端口映射和服务依赖；frontend 已改为可选 profile，默认本地 Vite 开发（Step 1.1、Frontend Step 3.4）。
- MinIO 初始化：使用单 bucket 保存 `published/*`、`uploads/*`、`drafts/*`，并通过 prefix policy 仅公开 `published/*` 读取权限（Step 1.2）。
- 本地启动说明：README 提供复制 `.env.example`、一条 Compose 启动命令、端口说明和健康检查命令（Step 1.3）。
- 业务表迁移：已创建 `games`、`game_likes`、`generation_jobs`、`uploaded_assets`、`agent_logs`、`play_events`，并验证 Alembic 升级到 `0002_business_tables`（Step 1）。
- 对象存储服务：已封装单 bucket、三类 prefix、presigned read/upload URL、published public URL 和存储异常边界，并完成真实 MinIO 私有/公开访问验证（Step 2）。
- 后端接口文档：已显式开放 Swagger UI、ReDoc 和 OpenAPI JSON，便于查看认证、存储和后续业务接口（Step 2.5）。
- 上传接口：已实现 `POST /api/uploads/presign` 和 `POST /api/uploads/complete`，支持登录保护、20MB 限制、对象 key 签名和素材登记（Step 3）。
- 游戏接口：已实现 `GET /api/games` 和 `GET /api/games/{game_id}`，支持 published 列表、排序、搜索、标签筛选和 draft 预览权限（Step 4）。
- 点赞接口：已实现 `POST /api/games/{game_id}/like`，支持登录保护、首次点赞写入和重复点赞幂等（Step 5）。
- Play 事件接口：已实现 `POST /api/play-events`，支持游客/登录用户上报、`view` 计数规则和 metadata 脱敏（Step 6）。
- 任务接口：已实现 `POST /api/jobs`、`GET /api/jobs`、`GET /api/jobs/{job_id}`、`GET /api/jobs/{job_id}/logs`，支持素材归属校验、最多 5 个素材、任务排序和日志脱敏（Step 7）。
- 后端基础骨架：FastAPI 应用可创建，已配置本地前端 CORS，提供 `/health` 健康检查接口，并使用统一 HTTP 错误响应格式（Step 2.1）。
- 数据库连接基础：后端可读取 `DATABASE_URL`，创建 async SQLAlchemy engine，通过 `/ready` 执行 `SELECT 1` 检查数据库连接，并提供 Alembic 迁移（Step 2.2）。
- Phase 4 前数据表：当前只创建 `users`、`sessions`、`oauth_accounts`，对象存储和游戏相关表后续再建（Step 2.3 调整范围）。
- 基础配置校验：后端启动时校验必需数据库配置和模型 provider 配置；Mock provider 允许空模型密钥，OpenAI-compatible provider 缺少 API key 会失败（Step 2.4）。
- 邮箱认证：已实现邮箱注册、邮箱登录、退出登录、`/api/auth/me` 和 httpOnly session cookie（Step 3.1、3.2、3.3）。
- OAuth 认证：已实现 Google OAuth start/callback 代码路径和账号创建/绑定规则；backend 可从根目录 `.env` 和 Docker Compose 环境读取真实 Google 配置。GitHub OAuth 为后续版本占位（Step 3.5、3.6）。
- 前端 Auth 基线：React + Vite + Ant Design 已实现最小导航和 Auth Modal，包含邮箱登录注册、Google 入口和 GitHub 未启用入口（Step 8.1、8.2、8.3 部分完成）。
- 前端静态 MVP 界面：React 前端已实现写死 Home、Auth Modal、Create、Play 页面状态，包含固定导航、游戏卡片叠层、更多筛选、模拟登录/退出、Create 工作台和 Play 静态运行区（Frontend Step 1）。
- 前端静态界面验证：新增 `frontend/scripts/check-static-ui.mjs` 和 `npm run test:static-ui`，覆盖关键静态 UI 标记和页面内调试面板禁用约束（Frontend Step 1）。
- 前端 Auth API 客户端：新增统一请求入口和 Auth API 方法，支持 API base URL、cookie、统一 JSON 错误解析、网络异常和敏感字段约束检查（Frontend Step 2.1）。
- 前端当前用户恢复：应用启动时请求 `/api/auth/me`，无 session 保持游客 Home，已登录时恢复昵称和头像（Frontend Step 2.2）。
- 前端 Auth 交互：已接通邮箱注册、邮箱登录、退出登录、Google OAuth start、GitHub disabled 占位、页面级成功提示和错误提示（Frontend Step 2.3-2.8）。
- 前端基础设施：已新增 mock 开关、统一错误摘要和结构化 Console 输出，支持后端未完成时继续开发 Home/Create/Play（Frontend Step 3.1-3.3）。
- 前端路由拆分：已引入真实前端路由，拆分 `pages/` 与 `components/` 结构，`Play` 页面不显示导航，点击 `创建游戏` 登录成功后直达 `Create`（Frontend Step 3.4）。

## Step 完成记录

### Step 0.1：确认仓库现状 ☑️ 已完成

- 已确认根目录 `prd.md` 作为原始需求输入；按用户确认，不再要求 `docs/prd.md`。
- 已确认 `docs/tech-stack.md`、`docs/design.md`、`docs/design-document.md` 和 `docs/implementation-plan.md` 存在。
- 已确认当前分支为 `main`，并通过 `.gitignore` 排除本地依赖、构建产物、虚拟环境和缓存文件。
- 已更新 `docs/implementation-plan.md`，将 Step 0.1 标注为 ☑️ 已完成。

### Step 0.2：创建项目目录结构 ☑️ 已完成

- 已建立 `frontend/`、`backend/`、`deployment/`、`scripts/`、`docs/` 目录边界。
- 已用 `deployment/.gitkeep` 和 `scripts/.gitkeep` 保留空目录。
- 已更新 `docs/architecture.md`，用 layer/layout 形式维护每个目录和文件作用。
- 已更新 `docs/implementation-plan.md`，将 Step 0.2 标注为 ☑️ 已完成。

### Step 0.3：建立环境变量样例 ☑️ 已完成

- 已扩展 `.env.example`，覆盖前端、后端、PostgreSQL、MinIO、Session、OpenAI-compatible API 和 Mock provider 变量。
- 已为每组变量添加简短用途说明。
- 已使用 `change-me-local`、空 API key 和示例 URL 作为占位值，避免提交真实密钥。
- 已更新 `docs/architecture.md` 和 `docs/implementation-plan.md`，记录 Step 0.3 完成状态。

### Step 1.1：定义 Docker Compose 服务 ☑️ 已完成

- 已在 `docker-compose.yml` 中定义 PostgreSQL、MinIO、backend、frontend 服务。
- 已为 PostgreSQL 和 MinIO 配置 `postgres-data`、`minio-data` 持久化 volume。
- 已暴露 MinIO S3 API 端口 `9000` 和控制台端口 `9001`。
- 已配置 backend 同时依赖 PostgreSQL 和 MinIO 健康状态，frontend 依赖 backend。
- 已更新 `docs/architecture.md` 和 `docs/implementation-plan.md`，记录 Step 1.1 完成状态。

### Step 1.2：初始化 MinIO bucket ☑️ 已完成

- 已新增 `deployment/minio-init.sh`，用于等待 MinIO、创建单个 bucket，并写入 prefix policy。
- 已新增 `minio-init` Compose 服务，依赖 MinIO 健康状态后执行初始化。
- 已配置 `published/*` public-read，未给 `uploads/*` 和 `drafts/*` 配置公开读取权限。
- 已配置 backend 等待 `minio-init` 成功完成后启动，确保对象存储初始化先于业务服务。
- 已更新 `docs/architecture.md` 和 `docs/implementation-plan.md`，记录 Step 1.2 完成状态。

### Step 1.3：提供一条启动命令 ☑️ 已完成

- 已在 `README.md` 中记录复制 `.env.example` 到 `.env` 的首次启动前置步骤。
- 已提供 `docker compose up --build` 作为本地完整栈启动命令，覆盖 frontend、backend、PostgreSQL 和 MinIO。
- 已记录 frontend、backend health、backend readiness、MinIO S3 API、MinIO Console 和 PostgreSQL 端口。
- 已补充端口冲突时修改 `docker-compose.yml` host-side port 的说明。

### Step 1：建立业务表迁移 ☑️ 已完成

- 已在 `backend/app/models.py` 中补齐 `games`、`game_likes`、`generation_jobs`、`uploaded_assets`、`agent_logs`、`play_events` 模型。
- 已新增 `backend/migrations/versions/0002_business_tables.py`，为业务表建立外键、唯一约束和必要索引。
- 已新增 `backend/tests/test_migrations.py`，覆盖业务表字段、索引、唯一约束和 Alembic SQL 输出。
- 已将 `games.tags` 调整为跨 SQLite/PostgreSQL 均可运行的 JSON 列，避免破坏现有后端测试。
- 已验证 `pytest backend/tests/test_migrations.py -v`、`pytest backend/tests -q`、`docker compose exec -T backend alembic upgrade head` 和 `docker compose exec -T backend alembic current` 均通过，当前 revision 为 `0002_business_tables`。

### Step 2：封装 MinIO 存储服务 ☑️ 已完成

- 已在 `backend/app/config.py` 中补齐 MinIO endpoint、public endpoint、bucket、region、SSL 和访问凭证配置项。
- 已新增 `backend/app/storage.py`，统一生成 `uploads/*`、`drafts/*`、`published/*` 对象路径，并集中处理 presigned upload URL、presigned read URL、public read URL。
- 已对文件名和相对路径做安全化处理，移除路径穿越片段，避免业务层手写 bucket 名和对象路径。
- 已新增 `backend/tests/test_storage.py`，覆盖对象 key 规则、public/presigned URL 规则和底层 S3 客户端异常包装。
- 已新增 `boto3` 依赖，并验证 `pytest backend/tests/test_storage.py -v`、`pytest backend/tests -q` 均通过。
- 已通过真实 Compose/MinIO 验证：`published/*` 无认证访问返回 200，`uploads/*` 无认证访问返回 403，`uploads/*` presigned URL 在容器内访问返回 200。
- 已在 `backend/app/main.py` 中显式配置 `/docs`、`/redoc`、`/openapi.json`，并补齐 OpenAPI 标题、版本和说明。
- 已在 `README.md` 中补充 Swagger UI、ReDoc 和 OpenAPI JSON 访问地址，方便本地查看后端接口。

### Step 2.1：创建 FastAPI 应用骨架 ☑️ 已完成

- 已创建 FastAPI 应用入口 `backend/app/main.py`。
- 已提供 `/health` 健康检查接口。
- 已配置本地前端 origin `http://localhost:5173` 可访问后端。
- 已添加统一 HTTP 错误响应格式：`{"error": {"code": "...", "message": "..."}}`。
- 已用测试覆盖 health、CORS preflight 和 HTTP 404 错误格式。

### Step 2.2：连接 PostgreSQL ☑️ 已完成

- 已通过 `backend/app/config.py` 读取 `DATABASE_URL`。
- 已通过 `backend/app/db.py` 建立 async SQLAlchemy engine 和 session dependency。
- 已通过 `/ready` 执行 `SELECT 1` 验证数据库连接。
- 已在数据库异常时返回明确的 `503 service_unavailable` 错误。
- 已添加 Alembic 迁移机制。
- 已让后端 Docker 镜像启动时先执行 `alembic upgrade head` 再启动 API。

### Step 2.3：创建 Phase 4 前核心数据表 ☑️ 已完成

- 按用户确认，Phase 4 前只创建 Auth/OAuth/session 必需表，不创建对象存储和游戏相关表。
- 已创建 `users` 表，以 `user_id` 作为系统唯一身份。
- 已创建 `oauth_accounts` 表，以 `user_id` 外键关联 `users.user_id`，并为 `(provider, provider_user_id)` 建立唯一约束。
- 已创建 `sessions` 表，以 `session_id` 保存服务端 session，并通过 `user_id` 关联用户。
- 已验证 Alembic SQL 输出和真实 PostgreSQL 迁移。

### Step 2.4：实现基础配置校验 ☑️ 已完成

- 已新增后端配置校验入口，启动加载配置时执行必需项检查。
- 已将 `DATABASE_URL` 改为必需配置，缺少时抛出明确的配置错误。
- 已区分 `MODEL_PROVIDER=mock` 与 `MODEL_PROVIDER=openai-compatible`。
- 已允许 Mock provider 模式下 `OPENAI_COMPATIBLE_API_KEY` 为空。
- 已要求 OpenAI-compatible provider 模式下必须提供 `OPENAI_COMPATIBLE_API_KEY`、base URL 和模型名。
- 已补齐 Docker Compose backend 服务对模型 provider 相关环境变量的透传。
- 已用测试覆盖缺少数据库配置、Mock provider 空 key、OpenAI-compatible provider 缺 key，以及 `.env.example` 覆盖校验项。

### Step 3.1-3.3：邮箱注册、登录、当前用户和退出登录 ☑️ 已完成

- 已实现 `/api/auth/register`、`/api/auth/login`、`/api/auth/logout`、`/api/auth/me`。
- 邮箱注册用户写入 `password_hash`，不会保存明文密码。
- OAuth-only 用户 `password_hash` 允许为空。
- session cookie 使用 httpOnly。
- 已用单元测试和本地 PostgreSQL API 请求验证。

### Step 3.5-3.6：Google OAuth 与 GitHub 占位 ☑️ 已完成代码路径

- 已实现 `/api/auth/oauth/google/start` 和 `/api/auth/oauth/google/callback`。
- 已实现 Google 首次登录创建 `users` + `oauth_accounts`，再次登录复用同一 `user_id`，verified email 命中本地密码账号时自动绑定。
- 已固定配置读取路径，后端从项目根目录 `.env` 读取 Google client id/secret/redirect URI，避免从 `backend/` 启动时读不到配置。
- 已在 Docker Compose backend 服务中透传 Google OAuth、GitHub OAuth 和 session 相关环境变量。
- 已用本地 `.env` 验证 Google 必需变量存在且非空。
- 已用真实 Compose backend 验证 `/api/auth/oauth/google/start` 返回 Google 授权地址并设置 OAuth state cookie。
- 缺少 Google client id/secret 时，start endpoint 仍返回 `503 service_unavailable`。
- Google callback 成功后会设置 httpOnly session cookie 并重定向回前端 `FRONTEND_ORIGIN`。
- 已实现 `/api/auth/oauth/github/start` 和 `/api/auth/oauth/github/callback` 占位，返回后续版本提示。
- 完整 Google 授权页账号选择/同意步骤需要用户在浏览器中完成。

### Step 3：实现 Uploads API ☑️ 已完成

- 已新增 `backend/app/uploads.py`，实现 `POST /api/uploads/presign` 和 `POST /api/uploads/complete`。
- 已对 Uploads API 接入登录保护；未登录调用 presign 或 complete 时，返回统一 `401 unauthorized` 错误格式。
- 已为 presign 请求增加 `filename`、`mime_type`、`size_bytes` 校验，并限制单文件最大 20MB；超限时返回 `413 file_too_large`。
- 已复用存储服务生成当前用户 `uploads/*` prefix 下的 object key 和 presigned upload URL。
- 已在 complete 路径校验 object key 必须属于当前用户 uploads prefix，并将素材登记到 `uploaded_assets`，`job_id` 保持为空。
- 已新增 `backend/tests/test_uploads.py`，覆盖 presign 登录保护、presign 成功响应、20MB 限制、complete 登录保护和 complete 落库。
- 已验证 `pytest backend/tests/test_uploads.py -v`、`pytest backend/tests -q` 通过。

### Step 4：实现 Games 列表和 Meta API ☑️ 已完成

- 已新增 `backend/app/games.py`，实现 `GET /api/games` 和 `GET /api/games/{game_id}`。
- 已对列表接口接入 `latest`、`play_count`、`like_count` 排序，并支持 `q` 搜索标题、简介、作者展示名和 `tag` 标签筛选。
- 已将列表结果限制为 `published` 游戏，并按当前登录态返回 `liked_by_me`。
- 已实现游戏 meta 权限：`published` 公开可读，`draft` 仅 owner 可读，`deleted` 返回 `404`。
- 已新增 `backend/tests/test_games.py`，覆盖 published 列表、排序、筛选和 draft meta 权限。
- 已验证 `pytest backend/tests/test_games.py -q` 与 `pytest backend/tests -q` 通过。

### Step 5：实现点赞 API ☑️ 已完成

- 已在 `backend/app/games.py` 中新增 `POST /api/games/{game_id}/like`。
- 已对点赞接口接入登录保护，未登录时返回统一 `401 unauthorized` 错误格式。
- 已实现首次点赞写入 `game_likes` 并递增 `games.like_count`。
- 已实现重复点赞幂等返回，不重复写入记录，不重复累加计数。
- 已限制仅 `published` 游戏可被点赞，`draft` 和 `deleted` 游戏返回 `404`。
- 已新增 `backend/tests/test_likes.py`，覆盖登录保护、首次点赞、重复点赞、多用户点赞和无效状态。
- 已验证 `pytest backend/tests/test_likes.py -q` 与 `pytest backend/tests -q` 通过。

### Step 6：实现 Play Events API ☑️ 已完成

- 已新增 `backend/app/play_events.py`，实现 `POST /api/play-events`。
- 已允许游客和登录用户上报事件；登录态存在时会记录 `user_id`，否则按游客写入。
- 已限制 event type 为 `view`、`manifest_loaded`、`started`、`failed`、`timeout`、`exited`。
- 已选择 `view` 作为 `play_count` 增量触发事件，其他事件只记录不计数。
- 已在保存 metadata 前移除 `secret`、`token`、`password`、`code` 等敏感字段，并去除 presigned URL 签名参数。
- 已新增 `backend/tests/test_play_events.py`，覆盖游客上报、登录用户事件、计数规则和 metadata 脱敏。
- 已验证 `pytest backend/tests/test_play_events.py -q` 与 `pytest backend/tests -q` 通过。

### Step 7：实现 Jobs API 基础 ☑️ 已完成

- 已新增 `backend/app/jobs.py`，实现 `POST /api/jobs`、`GET /api/jobs`、`GET /api/jobs/{job_id}` 和 `GET /api/jobs/{job_id}/logs`。
- 已对创建任务接入登录保护，保存 `prompt`、`confirmation` 并创建 `pending` 状态任务。
- 已限制单任务最多绑定 5 个素材，并校验所有 `asset_id` 必须属于当前用户；创建成功后会把素材绑定到任务。
- 已将任务列表限制为当前用户，并按 `created_at` 倒序返回；详情和日志仅 owner 可读。
- 已对任务日志按时间正序返回，并在响应前脱敏敏感文本与 presigned URL 签名。
- 已新增 `backend/tests/test_jobs.py`，覆盖登录保护、创建成功、素材归属、数量限制、列表详情权限和日志脱敏。
- 已验证 `pytest backend/tests/test_jobs.py -q` 与 `pytest backend/tests -q` 通过。

## 尚未落地或需补齐的边界

- 后端尚未实现 Agent runner、任务异步执行、生成产物落盘、发布接口、seed 数据和端到端生成闭环。
- 前端已完成页面与路由骨架，但尚未全面接通 Home、Create、Play 与后端真实业务数据链路；Create 页面仍需继续对齐 [pages-design.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/pages-design.md) 的任务工作台交互。
- `frontend/vite.config.ts`、`frontend/vite.config.js` 和 `frontend/vite.config.d.ts` 当前存在职责重叠，后续推进 Step 8.1 时应统一配置来源。
- 后续实施计划需按前端、后端、Agent 三端拆分，并以接口契约保证并行开发一致性。

## 文档一致性更新记录

### 2026-06-19：同步页面设计、接口契约和分端计划

- 已将 `docs/tech-stack.md` 中的 Agent 说明收敛为「LangGraph 框架已定，内部节点设计后续确认」，避免提前写死 planner、asset analyzer、code generator 等角色。
- 已将 `docs/design.md` 中官网 `Sign In` 参考样式改为本项目 `登录` / `Publish` 可复用的按钮样式说明。
- 已修正 `docs/design-document.md` 的上传素材模型，允许文件先上传、创建任务后再绑定到 `generation_job`。
- 已新增 `docs/api-contract.md`，作为前后端并行开发的唯一接口契约，覆盖 Auth、Games、Uploads、Jobs、Play Events 和统一错误格式。
- 已重写 `docs/implementation-plan.md`，拆分为 Backend Plan、Frontend Plan、Agent Plan 和 Integration Plan，并在每一步标明跨端依赖和验证测试。
- 已更新 `docs/yahaha-preview.html`，移除页面内调试面板口径，改为 DevTools Console 输出说明。

### 2026-06-19：拆分三端独立实施计划

- 已新增 `docs/backend-implementation-plan.md`，后端开发者可独立实现数据模型、存储、API、发布流程和 Agent runner 接入。
- 已新增 `docs/frontend-implementation-plan.md`，前端开发者可基于 `api-contract.md` 使用 mock 独立实现 Home、Create、Play 和 Auth Modal。
- 已新增 `docs/agent-implementation-plan.md`，Agent 开发者可独立实现执行器边界、Mock provider、OpenAI-compatible provider、产物协议和日志。
- 已将 `docs/implementation-plan.md` 改为总索引和最终集成验收清单，避免三端计划与总计划重复维护。
- 已统一三端实施计划编号为 `Step X` / `Step X.X` 格式，并清理总索引和跨端依赖中的旧端侧字母编号引用。

### 2026-06-19：完成 Frontend Step 0-1 静态界面

- 已按 `docs/frontend-implementation-plan.md` 完成第二大步前的前端工作：Step 0.1-0.3 和 Step 1.1-1.10 均已验证通过。
- 已将 `frontend/src/App.tsx` 从 Auth 基线替换为静态 MVP 页面壳，支持 Home、Create、Play、Auth Modal、模拟登录、模拟退出和页面内切换（Frontend Step 1）。
- 已将 `frontend/src/styles.css` 更新为 Yahaha 深色视觉、固定顶部导航、大屏游戏卡片网格、封面标签叠层、封面统计叠层、Create 工作台和 Play 静态运行区样式（Frontend Step 1）。
- 已新增 `frontend/scripts/check-static-ui.mjs`，并在 `frontend/package.json` 中新增 `test:static-ui` 脚本；红灯验证确认旧界面缺少目标标记，绿灯验证确认新界面通过（Frontend Step 1）。
- 已运行 `npm run test:static-ui` 和 `npm run build`，二者均通过。
- 已按静态界面反馈调整导航登录状态：未登录时不显示默认头像，只显示 `登录`；模拟登录后 `登录` 替换为头像按钮，hover/focus 头像显示用户菜单和 `退出登录`；同时为 `html`、`body`、`#root` 和页面根容器补齐深色背景与横向溢出约束，避免页面底部出现浅色条（Frontend Step 1）。
- 已补齐 Home 静态筛选 tab 的本地切换状态，`最多游玩 / 最多点赞 / 最新发布` 可以切换 active；已将第一张游戏卡片从占位字段替换为完整模拟数据，并统一点赞 icon 为心形展示（Frontend Step 1）。
- 已按静态界面反馈将顶部导航调整为玻璃磨砂质感，保留固定顶部布局并增加半透明叠层、背景模糊、弱白描边和内高光（Frontend Step 1）。
- 已补齐 Home「更多筛选」下拉清单交互，点击可展开类型列表、选择类型后更新按钮文案并收起菜单（Frontend Step 1）。
- 已将顶部导航改为视口固定定位，页面滚动时导航栏保持不动，并为页面内容补齐顶部占位避免被遮挡（Frontend Step 1）。

### 2026-06-19：完成 Frontend Step 2.1 Auth API 客户端

- 已新增 `frontend/src/api/client.ts`，统一处理 `VITE_API_BASE_URL`、`credentials: "include"`、JSON 错误格式、204 空响应和网络异常（Frontend Step 2.1）。
- 已新增 `frontend/src/api/auth.ts`，封装当前用户、邮箱登录、邮箱注册、退出登录和 Google OAuth start 方法（Frontend Step 2.1）。
- 已新增 `frontend/scripts/check-auth-client.mjs` 和 `npm run test:auth-client`，验证 Auth 客户端关键约束，并检查源码中不出现 session id、token、client secret 等敏感字段输出（Frontend Step 2.1）。
- 已运行 `npm run test:auth-client` 和 `npm run build`，二者均通过。

### 2026-06-19：完成 Frontend Step 2.2 当前用户检查

- 已在 `frontend/src/App.tsx` 接入启动时的 `getCurrentUser()` 检查，应用首次加载会恢复当前用户；无 session 时静默保持游客 Home，不弹错误框（Frontend Step 2.2）。
- 已将顶部登录态从写死文案切换为真实用户字段，优先展示 `display_name`，回退 `email`，并在存在 `avatar_url` 时展示真实头像（Frontend Step 2.2）。
- 已保留静态阶段模拟登录能力，但改为同步写入本地 mock 用户，避免与当前用户恢复状态冲突（Frontend Step 2.2）。
- 已新增 `frontend/scripts/check-current-user.mjs` 和 `npm run test:current-user`，先验证缺失恢复逻辑时红灯，再验证接入后的关键约束为绿灯（Frontend Step 2.2）。
- 已运行 `npm run test:current-user`、`npm run test:auth-client` 和 `npm run build`，三者均通过。

### 2026-06-19：完成 Frontend Step 2.3-2.8 Auth 全链路

- 已将 `frontend/src/App.tsx` 的 Auth Modal 改为受控表单，接入邮箱格式、密码最小长度、确认密码一致性校验，并在注册/登录成功后刷新前端用户态、关闭弹窗、展示成功提示（Frontend Step 2.3、2.4）。
- 已接入真实退出登录请求；仅在接口成功后清空当前用户和登录态，失败时保留用户态并展示错误提示（Frontend Step 2.5）。
- 已接入 Google OAuth start，请求授权地址后通过浏览器跳转进入授权流程；回到前端后复用启动时的当前用户检查恢复登录态，并输出不含敏感信息的 Console 摘要（Frontend Step 2.6）。
- 已保留 GitHub 按钮 disabled 占位，并提供“GitHub 登录暂未启用”的明确反馈，不触发真实 GitHub OAuth（Frontend Step 2.7）。
- 已新增 `frontend/scripts/check-auth-ui.mjs` 和 `npm run test:auth-ui`，覆盖 Auth 表单、退出登录、Google 跳转、GitHub 占位和敏感信息约束（Frontend Step 2.8）。
- 已运行 `npm run test:auth-ui`、`npm run test:current-user`、`npm run test:auth-client` 和 `npm run build`，四者均通过（Frontend Step 2.8）。

### 2026-06-19：完成 Frontend Step 3.1-3.3 API mock、错误反馈与 Console 输出

- 已新增 `frontend/src/mock/runtime.ts`，提供 `VITE_ENABLE_MOCK_API` 开关、mock Auth store，以及 Home/Create/Play 当前阶段可用的静态开发数据；关闭后端时仍可继续展示主要页面（Frontend Step 3.1）。
- 已新增 `frontend/src/lib/errors.ts`，统一生成面向用户的错误标题、失败原因、`retryHint` 和下一步建议；`App.tsx` 中的登录、注册、退出登录和 Google 登录失败已复用这一层（Frontend Step 3.2）。
- 已新增 `frontend/src/lib/console.ts`，统一输出时间戳、请求路径、状态码、业务状态和摘要字段，并对 password、token、secret、OAuth code 等敏感信息做脱敏（Frontend Step 3.3）。
- 已在 `frontend/src/App.tsx` 接入页面级错误弹窗和结构化 Console 输出；当前 Home、Create、Play、Auth 的关键动作都会输出到 DevTools Console，页面内没有新增调试面板（Frontend Step 3.2、3.3）。
- 已新增 `frontend/scripts/check-app-infra.mjs` 和 `npm run test:app-infra`，覆盖 mock 开关、错误摘要和 Console 工具接入约束（Frontend Step 3.3）。
- 已运行 `npm run test:app-infra`、`npm run test:auth-ui`、`npm run test:current-user`、`npm run test:auth-client` 和 `npm run build`，五者均通过（Frontend Step 3.3）。

### 2026-06-19：收敛 Frontend Step 3.4 首页版式与导航比例

- 已重排 `frontend/src/pages/HomePage.tsx`，将首页改为更规范的三段式结构：轻量 Hero、精选游戏 Spotlight、独立浏览面板和更整齐的卡片列表（Frontend Step 3.4）。
- 已重写 `frontend/src/pages/home.css`，整体下调标题、按钮、筛选器和卡片字号，减少首屏拥挤感，并让搜索与筛选从背景图中独立出来（Frontend Step 3.4）。
- 已调整 `frontend/src/styles.css` 顶部导航比例，收窄导航高度、站名字号、导航间距、头像尺寸和登录按钮尺寸，使其更接近 Yahaha 官网导航风格（Frontend Step 3.4）。
- 已运行 `npm run build` 和 `npm run test:routing-structure`，确认视觉重排后前端构建与页面拆分结构仍然通过（Frontend Step 3.4）。
- 已将 `docker-compose.yml` 中 frontend 服务切换为 `docker-frontend` 可选 profile，并在 `README.md` 中明确推荐「backend 走 Docker、frontend 本地 `npm run dev`」的开发方式，避免旧前端容器缓存页面（Frontend Step 3.4）。

### 2026-06-19：完成 Frontend Step 3.4 路由与页面结构拆分

- 已安装 `react-router-dom`，并在 `frontend/src/main.tsx` 中挂载 `BrowserRouter`；`frontend/src/App.tsx` 现只保留路由、导航显隐、Auth 全局状态和错误弹窗编排（Frontend Step 3.4）。
- 已将 `Home / Create / Play` 拆分到 `frontend/src/pages/`，并各自拥有独立 CSS 文件；同时将 `AuthModal` 和 `TopNav` 抽到 `frontend/src/components/`（Frontend Step 3.4）。
- 已将 `Play` 页面改为独立路由 `/play/:gameId`，并明确不显示顶部导航；`Home` 与 `Create` 继续复用导航壳层（Frontend Step 3.4）。
- 已修正受保护入口行为：未登录点击 `创建游戏` 后，登录成功直接 `navigate("/create")`，不再回到主页（Frontend Step 3.4）。
- 已新增 `frontend/src/types/ui.ts` 收敛页面与展示类型，并新增 `frontend/scripts/check-routing-structure.mjs` 校验页面拆分、真实路由和 `Play` 无导航约束（Frontend Step 3.4）。
- 已运行 `npm run test:routing-structure`、`npm run test:auth-ui`、`npm run test:app-infra` 和 `npm run build`，四者均通过（Frontend Step 3.4）。

### 2026-06-19：补齐 Auth 成功/失败弹窗反馈

- 已将登录/注册成功从右上角提示改为统一成功弹窗，分别展示“登录成功”或“注册成功”，并提示即将跳转的页面（Frontend Step 3.4 调整）。
- 已将登录/注册失败和前端校验失败统一接入错误弹窗，弹窗内展示失败标题、具体失败原因和下一步建议（Frontend Step 3.4 调整）。
- 已运行 `npm run test:auth-ui`、`npm run test:routing-structure`、`npm run test:app-infra` 和 `npm run build`，四者均通过（Frontend Step 3.4 调整）。
