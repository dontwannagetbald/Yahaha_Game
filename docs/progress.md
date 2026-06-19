# 项目进度记录

本文档记录已实现功能、对应实施计划 step，以及尚未落地或需要补齐的边界。项目 layer、目录边界和文件职责维护在 [architecture.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/architecture.md)。

## 已实现功能索引

- 仓库基线：保留原始需求、设计文档、技术栈、实施计划和架构记录；通过 `.gitignore` 排除本地依赖、构建产物、虚拟环境和缓存（Step 0.1）。
- 目录结构：建立 `frontend/`、`backend/`、`deployment/`、`scripts/`、`docs/` 的清晰边界，并通过 `.gitkeep` 保留暂未放置业务文件的目录（Step 0.2）。
- 环境变量样例：提供前端、后端、PostgreSQL、MinIO、Session、OpenAI-compatible API 和 Mock provider 变量样例，并使用占位值避免真实密钥（Step 0.3）。
- Docker Compose 基线：定义 PostgreSQL、MinIO、backend、frontend 服务，包含持久化 volume、健康检查、端口映射和服务依赖（Step 1.1）。
- MinIO 初始化：使用单 bucket 保存 `published/*`、`uploads/*`、`drafts/*`，并通过 prefix policy 仅公开 `published/*` 读取权限（Step 1.2）。
- 本地启动说明：README 提供复制 `.env.example`、一条 Compose 启动命令、端口说明和健康检查命令（Step 1.3）。
- 后端基础骨架：FastAPI 应用可创建，已配置本地前端 CORS，提供 `/health` 健康检查接口，并使用统一 HTTP 错误响应格式（Step 2.1）。
- 数据库连接基础：后端可读取 `DATABASE_URL`，创建 async SQLAlchemy engine，通过 `/ready` 执行 `SELECT 1` 检查数据库连接，并提供 Alembic 迁移（Step 2.2）。
- Phase 4 前数据表：当前只创建 `users`、`sessions`、`oauth_accounts`，对象存储和游戏相关表后续再建（Step 2.3 调整范围）。
- 基础配置校验：后端启动时校验必需数据库配置和模型 provider 配置；Mock provider 允许空模型密钥，OpenAI-compatible provider 缺少 API key 会失败（Step 2.4）。
- 邮箱认证：已实现邮箱注册、邮箱登录、退出登录、`/api/auth/me` 和 httpOnly session cookie（Step 3.1、3.2、3.3）。
- OAuth 认证：已实现 Google OAuth start/callback 代码路径和账号创建/绑定规则；backend 可从根目录 `.env` 和 Docker Compose 环境读取真实 Google 配置。GitHub OAuth 为后续版本占位（Step 3.5、3.6）。
- 前端 Auth 基线：React + Vite + Ant Design 已实现最小导航和 Auth Modal，包含邮箱登录注册、Google 入口和 GitHub 未启用入口（Step 8.1、8.2、8.3 部分完成）。
- 前端静态 MVP 界面：React 前端已实现写死 Home、Auth Modal、Create、Play 页面状态，包含固定导航、游戏卡片叠层、更多筛选、模拟登录/退出、Create 工作台和 Play 静态运行区（Frontend Step 1）。
- 前端静态界面验证：新增 `frontend/scripts/check-static-ui.mjs` 和 `npm run test:static-ui`，覆盖关键静态 UI 标记和页面内调试面板禁用约束（Frontend Step 1）。

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

## 尚未落地或需补齐的边界

- 后端尚未实现 Phase 4 及之后的对象存储、游戏、任务、Play 相关 API。
- 前端尚未实现正式路由、Home、Create 和 Play 页面；Create 页面以 [pages-design.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/pages-design.md) 中的左侧任务列表、聊天上传区、生成游戏显示面板为准。
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
