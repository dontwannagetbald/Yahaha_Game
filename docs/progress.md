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
- 执行器边界：已实现 fake runner、后台状态迁移、Agent 日志落库和 draft game 创建，后端创建任务后可自动推进到 `succeeded / failed`（Step 8）。
- Seed 游戏数据：已提供可重复执行的 published 可玩游戏写入，包含真实数据库记录、`published/*` 静态 bundle、public manifest/entry 地址，便于首页和游戏卡片联调（Step 10）。
- 独立 Agent 原型：已新增根目录 `agent/`，可在不接前后端的情况下本地运行 `conversation -> generation -> manifest` 全链路，并产出静态 bundle、校验结果和 provider 配置边界（Agent Prototype Step 1）。
- LangGraph 部署配置：已新增 `agent/langgraph.json`、`agent/my_agent/agent.py` 和 `agent/my_agent/requirements.txt`，可导出真实 `CompiledStateGraph` 并按 LangGraph 平台约定声明依赖与环境变量入口（Agent Prototype Step 1）。
- LangSmith tracing：已在独立 `agent/` 原型中接入 `LANGSMITH_TRACING / LANGSMITH_API_KEY / LANGSMITH_PROJECT / LANGSMITH_ENDPOINT` 配置、graph run metadata 和 runner tracing context（Agent Prototype Step 1）。
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
- 前端注册资料：邮箱注册已支持昵称输入、头像上传、密码规则校验；顶部导航已显示头像后的昵称，OAuth 用户优先展示 OAuth 头像与昵称（Frontend Step 3.4）。
- 前端首页筛选：Home 已支持 `最多游玩 / 最多点赞 / 最新发布` 排序、搜索框关键词过滤、类型筛选联动、固定精选推荐和放大镜图标样式，并补充首页校验脚本（Frontend Step 3.4）。
- 前端 Auth 弹窗优化：注册态字段校验已改为输入框右侧状态位与悬浮提示，邮箱注册默认使用系统头像，弹窗整体上移并改为更紧凑布局，避免错误提示把弹窗撑大（Frontend Step 3.4）。
- 前端 Play 布局：`/play` 已去掉顶部导航预留空白，页面默认禁用上下滚动，并把左侧信息区与游戏沙盒压到一屏内完整呈现，减少舞台底部留白（Frontend Step 3.4）。
- 前端 Play 交互：`/play` 已支持点亮小红心点赞，同类型游戏瀑布流展示与当前游戏相同标签的卡片，并可在 `Play` 内直接切换进入对应游戏（Frontend Step 3.4）。
- 前端 Play 加载态：游戏 sandbox 在内容显示前已接入封面占位图、半透明蒙版和卡通进度条，按游戏切换时会重置加载进度并完成过渡（Frontend Step 3.4）。
- 前端 Play 壳层修正：`/play` 已从全局 `app-shell` 顶部占位中拆出独立 `play-shell`，同时将游戏标签移动到简介下方，避免顶部残留导航留白（Frontend Step 3.4）。
- 前端 Create 重排：创建页已改为单一左侧 panel，顶部可折叠任务列表与下方对话输入区合并在同一栏中，右侧保留生成游戏显示面板（Frontend Step 3.4）。
- 前端 Create 输入区：附件按钮和发送按钮已叠放到文本框内部右下角，附件按钮可直接打开文件选择器并显示已选附件名（Frontend Step 3.4）。
- 前端 Create 附件交互：附件按钮已改为深色高对比可见态，支持多附件追加上传，且每个附件右上角都有白底黑字 `x` 可单独删除（Frontend Step 3.4）。
- 前端 Home 游戏流：已接入 `Games API / mock` 列表查询，支持只展示 published 游戏、真实卡片字段映射、固定精选推荐、排序、搜索、标签筛选和首页点赞（Frontend Step 4）。
- 前端 Play 点赞同步：`/play` 页点赞状态已改为跟随真实游戏数据和首页列表同步，不再使用本地 toggle 假计数（Frontend Step 4）。
- 前端 Games 前端层：已新增 `frontend/src/api/games.ts`、`frontend/src/lib/games.ts` 和 `frontend/scripts/check-home-api.mjs`，统一处理游戏字段映射、封面兜底、Games 请求和首页校验（Frontend Step 4）。
- 前端 Play 运行链路：已接入 `meta -> manifest -> sandboxed iframe` 的真实加载链路，支持超时、失败、重试与事件上报（Frontend Step 5）。
- 前端 Play mock 运行时：已为 mock 模式补齐内存 manifest 和 data URL iframe 入口，后端关闭时仍可跑通 Play 页面联调（Frontend Step 5）。

### Frontend Step 5：接入 Play 页面 ☑️ 已完成

- 已在 `frontend/src/api/play.ts` 建立 manifest 加载、iframe 入口解析和 `/api/play-events` 上报客户端；真实模式读取 `game.manifest_url`，mock 模式读取内存 manifest（Frontend Step 5.2、Step 5.3、Step 5.5）。
- 已在 `frontend/src/App.tsx` 的 `PlayRoute` 中按 `gameId` 真实请求 meta，并补齐无效 game id 的可见错误态与刷新 URL 进入同一游戏的加载路径（Frontend Step 5.1）。
- 已在 `frontend/src/pages/PlayPage.tsx` 把静态舞台改为真实运行状态机，按 `loading_meta / loading_manifest / loading_iframe / ready / error / timeout` 分阶段推进，并提供 `重新加载` 入口（Frontend Step 5.2、Step 5.3、Step 5.4）。
- 已在 `frontend/src/pages/PlayPage.tsx` 使用 `sandbox="allow-scripts"` 的真实 iframe 承载游戏入口，不再用本地 React 组件伪装游戏，同时在 iframe `onLoad` / `onError` 上接 started / failed 状态（Frontend Step 5.3、Step 5.4）。
- 已接入 `view`、`manifest_loaded`、`started`、`failed`、`timeout`、`exited` 事件上报，并在 DevTools Console 输出 manifest URL、runtime、entry 和阶段摘要（Frontend Step 5.5）。
- 已新增 `frontend/scripts/check-play-runtime.mjs`，并验证 `cd frontend && npm run test:play-runtime`、`npm run test:play-page`、`npm run build` 全部通过（Frontend Step 5）。

### Frontend Step 4：接入 Home 游戏流 ☑️ 已完成

- 已在 `frontend/src/api/games.ts` 建立 `GET /api/games`、`GET /api/games/{game_id}`、`POST /api/games/{game_id}/like` 对应客户端，并在 `frontend/src/lib/games.ts` 中统一做字段映射、数字格式化和封面兜底（Frontend Step 4.1、Step 4.2、Step 4.5）。
- 已在 `frontend/src/App.tsx` 接入首页列表请求、固定精选推荐源数据、首页错误弹窗与点赞更新逻辑；mock 模式下也支持同样的排序、搜索、筛选和点赞行为（Frontend Step 4.1、Step 4.3、Step 4.4、Step 4.5）。
- 已在 `frontend/src/pages/HomePage.tsx` 保留你确认过的首页样式，只把数据流改为真实查询参数请求；搜索仍然是输入完成后触发，tab 仍有下划线，更多筛选仍在搜索框右侧（Frontend Step 4.2、Step 4.3、Step 4.4）。
- 已把首页卡片点赞按钮从 Play 入口点击区域中分离；未登录点击点赞会直接弹登录框，已登录点赞后会更新首页与 Play 的点赞状态（Frontend Step 4.5）。
- 已更新 `frontend/scripts/check-home-api.mjs`、`frontend/scripts/check-home-filters.mjs`、`frontend/scripts/check-play-page.mjs`，并验证 `cd frontend && npm run test:home-api`、`npm run test:home-filters`、`npm run test:play-page`、`npm run build` 全部通过（Frontend Step 4）。

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

### Step 8：接入 Agent Runner 边界 ☑️ 已完成

- 已新增 `backend/app/agent_runner.py`，定义后端可调用的执行器输入、成功/失败输出、日志事件结构和可替换 fake runner。
- 已在 `backend/app/jobs.py` 中为创建任务接入 `BackgroundTasks`，任务创建后会在后台推进状态流，不再停留在纯 `pending`。
- 已实现任务状态迁移：执行开始更新为 `running`，fake success 更新为 `succeeded`，fake failure 更新为 `failed` 并保存 `error_message`。
- 已将 runner 输出的日志写入 `agent_logs`，并保持 Step 7 的日志查询接口可继续按时间正序读取。
- 已在 fake success 路径创建 draft game，保存 `game_id`、`artifact_prefix`、`manifest_url`、`artifact_base_url` 和基础游戏 meta。
- 已新增 `backend/tests/test_agent_runner.py`，覆盖 runner 输入边界、后台状态流、错误落库和 draft game 关联。
- 已验证 `pytest backend/tests/test_agent_runner.py -q` 通过。

### Step 10：准备 Seed 游戏数据 ☑️ 已完成

- 已新增 `backend/app/seed.py`，提供固定 seed 作者、固定 game id 的 published 可玩游戏定义，以及 `manifest.json`、`index.html`、`style.css`、`game.js`、`assets/cover.svg` bundle 组装逻辑。
- 已将 seed bundle 升级为两个真实可玩的 canvas 小游戏：`Sky Runner` 横版跑酷收集玩法，`Pixel Raid` 俯视角生存战斗玩法。
- 已新增 `scripts/seed_backend.py`，可在本地或容器环境直接执行 seed，把示例游戏写入真实数据库和对象存储。
- 已让 seed 过程把 bundle 上传到 `published/{game_id}/v1/*`，并把 `cover_url`、`manifest_url`、`artifact_base_url` 回填为 public-read URL。
- 已保证 seed 幂等：重复执行会复用固定作者和固定游戏记录，不会重复创建同一批 mock 游戏。
- 已新增 `backend/tests/test_seed.py`，覆盖 published 游戏写入、幂等行为、manifest 契约和静态 bundle 结构。
- 已验证 `cd backend && ../.venv/bin/pytest tests/test_seed.py -q`、`cd backend && ../.venv/bin/pytest tests -q`、带本机 PostgreSQL/MinIO 覆盖变量执行 `scripts/seed_backend.py`、数据库 published 记录检查，以及 MinIO public manifest / entry 读取。

### Agent Prototype Step 1：完成独立 Agent 原型 ☑️ 已完成

- 已新增 [agent-orchestration-design.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/agent-orchestration-design.md)，明确双阶段工作流、Orchestrator / Design / Asset / Spec Builder / Developer / Validator 分工、状态字段和本地目录结构。
- 已新增 [2026-06-20-agent-prototype.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/superpowers/plans/2026-06-20-agent-prototype.md)，把独立 `agent/` 原型拆成可执行的小步计划。
- 已新增根目录 `agent/` 原型工程，包含 `conversation_graph`、`generation_graph`、agent 节点、provider 骨架、bundle tools、CLI runner 和 fixture。
- 已实现 `python3 -m app.runner conversation --input fixtures/sample_request.json`，可从 prompt 产出 `confirmation_card` 和 `structured_design_state`。
- 已实现 `python3 -m app.runner generate --input fixtures/sample_request.json --output-dir output/demo`，可从对话输入继续生成 `manifest.json`、`index.html`、`style.css`、`game.js`。
- 已实现 bundle 校验失败路径，缺少关键文件时会返回 `failed_step=validate_bundle`、用户可读错误和重试提示。
- 已补 provider 骨架：`mock` 默认可运行，`openai-compatible` 缺少 `OPENAI_COMPATIBLE_API_KEY / BASE_URL / MODEL` 时会返回明确错误。
- 已验证 `python3 -m pytest agent/tests -q`、`cd agent && python3 -m app.runner conversation --input fixtures/sample_request.json`、`cd agent && python3 -m app.runner generate --input fixtures/sample_request.json --output-dir output/demo` 均通过。
- 已新增 `agent/langgraph.json`、`agent/my_agent/agent.py`、`agent/my_agent/requirements.txt` 和 `agent/tests/test_langgraph_deploy_config.py`，并验证 `cd agent && ../.venv/bin/python3 -m pytest tests/test_langgraph_deploy_config.py -q` 通过；`conversation_graph` 与 `generation_graph` 已可导出为真实 `CompiledStateGraph`。
- 已新增 `agent/app/tracing.py` 和 `agent/tests/test_langsmith_tracing.py`，支持 LangSmith 配置解析、缺少 API key 的明确报错、conversation/generation 的 `run_name / tags / metadata` 注入，以及惰性加载 `langsmith` SDK。
- 已验证 `cd agent && ../.venv/bin/python3 -m pytest tests/test_langsmith_tracing.py -q`、`cd agent && ../.venv/bin/python3 -m pytest tests/test_runner_cli.py -q`、`cd agent && ../.venv/bin/python3 -m pytest tests -q` 全部通过。

### 2026-06-20：调整 Home 精选推荐选取规则

- 已将 `frontend/src/pages/HomePage.tsx` 中的精选推荐改为固定选择全量游戏里“点赞数 + 游玩数”总和最高的卡片，不再跟随当前列表首项变化（Frontend Step 3.4）。
- 已更新 `frontend/scripts/check-home-filters.mjs`，补充对精选推荐选取逻辑的源码校验，确保后续修改不会退回为取第一张卡（Frontend Step 3.4）。
- 已校正 `frontend/src/pages/home.css` 中搜索放大镜字号为 `20px`，避免图标异常放大影响首页排版。
- 已验证 `npm run test:home-filters` 和 `npm run build` 均通过。

### 2026-06-20：补齐 Play 页 sandbox 加载占位层

- 已在 `frontend/src/pages/PlayPage.tsx` 新增加载态状态机，进入游戏或切换猜你喜欢卡片时会先显示封面占位层，再按进度推进到游戏舞台（Frontend Step 3.4）。
- 已在 `frontend/src/pages/play.css` 增加封面图、半透明蒙版和卡通进度条样式，保持现有 Yahaha 深色风格下的加载过渡（Frontend Step 3.4）。
- 已更新 `frontend/scripts/check-play-page.mjs`，补充对加载占位层结构与样式 token 的校验，避免后续回退（Frontend Step 3.4）。
- 已验证 `cd frontend && npm run test:play-page` 和 `cd frontend && npm run build` 均通过（Frontend Step 3.4）。

### 2026-06-20：修正 Play 页顶部留白与标签顺序

- 已在 `frontend/src/App.tsx` 将 `/play` 路由壳层改为纯 `play-shell`，不再叠加 `app-shell` 的 `padding-top: 56px`，从根因上移除顶部导航留白（Frontend Step 3.4）。
- 已在 `frontend/src/pages/PlayPage.tsx` 将游戏标签移动到简介下方，使左侧信息顺序更贴近你当前想要的版式（Frontend Step 3.4）。
- 已在 `frontend/src/pages/play.css` 为独立 `play-shell` 补齐背景，避免脱离全局壳层后出现背景断层（Frontend Step 3.4）。
- 已更新 `frontend/scripts/check-routing-structure.mjs` 和 `frontend/scripts/check-play-page.mjs`，锁定 `/play` 独立壳层和标签顺序，避免后续回退（Frontend Step 3.4）。
- 已验证 `cd frontend && npm run test:routing-structure`、`cd frontend && npm run test:play-page`、`cd frontend && npm run build` 均通过（Frontend Step 3.4）。

### 2026-06-20：重排 Create 页为单侧栏结构

- 已在 `frontend/src/pages/CreatePage.tsx` 将旧的“任务列表”和“对话记录”拆分结构改为单一左侧 `create-side-panel`，其中上方为可折叠任务列表，下方为对话流与输入栏（Frontend Step 3.4）。
- 已在 `frontend/src/pages/create.css` 按 `Play` 页同类布局重写创建页分栏，保留左侧 `430px` 宽度，右侧让生成游戏显示面板占用剩余空间（Frontend Step 3.4）。
- 已新增 `frontend/scripts/check-create-layout.mjs` 与 `npm run test:create-layout`，锁定单侧栏、折叠任务区和右侧独立生成面板结构，避免后续回退（Frontend Step 3.4）。
- 已验证 `cd frontend && npm run test:create-layout` 与 `cd frontend && npm run build` 均通过（Frontend Step 3.4）。

### 2026-06-20：实现 Create 输入框内浮动操作区

- 已在 `frontend/src/pages/CreatePage.tsx` 为输入区增加隐藏文件输入、附件按钮点击触发和已选附件列表展示，附件按钮现在可以直接打开系统文件选择器（Frontend Step 3.4）。
- 已在 `frontend/src/pages/create.css` 将发送按钮与附件按钮改为叠放在文本框右下角，并为文本框底部预留按钮空间，避免遮挡输入内容（Frontend Step 3.4）。
- 已更新 `frontend/scripts/check-create-layout.mjs`，补充对 `composer-input-wrap`、浮动按钮区和附件选择入口的校验，避免后续回退（Frontend Step 3.4）。
- 已验证 `cd frontend && npm run test:create-layout` 与 `cd frontend && npm run build` 均通过（Frontend Step 3.4）。

### 2026-06-20：完善 Create 附件按钮可见性与删除交互

- 已在 `frontend/src/pages/CreatePage.tsx` 将附件选择改为多附件追加模式，重复点附件按钮可继续补选文件；每个已选附件都支持点击右上角 `x` 单独移除（Frontend Step 3.4）。
- 已在 `frontend/src/pages/create.css` 提升附件按钮在白色输入框上的对比度，并为附件 chip 增加白色圆底黑字的删除按钮样式（Frontend Step 3.4）。
- 已更新 `frontend/scripts/check-create-layout.mjs`，补充对删除逻辑和删除按钮样式 token 的校验，避免后续回退（Frontend Step 3.4）。
- 已验证 `cd frontend && npm run test:create-layout` 与 `cd frontend && npm run build` 均通过（Frontend Step 3.4）。

## 尚未落地或需补齐的边界

- 后端尚未实现真实生成产物落盘、Publish API 和端到端生成闭环。
- 前端已完成页面与路由骨架，但尚未全面接通 Home、Create、Play 与后端真实业务数据链路；Create 页面仍需继续对齐 [pages-design.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/pages-design.md) 的任务工作台交互。
- `frontend/vite.config.ts`、`frontend/vite.config.js` 和 `frontend/vite.config.d.ts` 当前存在职责重叠，后续推进 Step 8.1 时应统一配置来源。
- 后续实施计划需按前端、后端、Agent 三端拆分，并以接口契约保证并行开发一致性。
- 独立 `agent/` 原型当前优先使用本地 Graph 兼容层；真实 `langgraph` 包安装仍受当前会话网络/审批环境限制，后续拿到依赖后可切换到真实包验证。
- 独立 `agent/` 原型尚未接回 `backend/app/agent_runner.py`，目前只作为本地调试和工作流验证入口。

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

### 2026-06-19：补齐 Home 排序与搜索交互

- 已在 `frontend/src/pages/HomePage.tsx` 接入首页真实前端筛选逻辑，支持 `最多游玩 / 最多点赞 / 最新发布` 三个 tab 排序，并与类型筛选共同生效（Frontend Step 3.4）。
- 已为搜索框接入标题、作者、简介、标签关键词过滤；无结果时展示首页空状态提示，避免界面空白（Frontend Step 3.4）。
- 已在 `frontend/src/pages/home.css` 放大搜索框放大镜 icon，并补充搜索空态样式，保持首页现有视觉方向不变（Frontend Step 3.4）。
- 已新增 `frontend/scripts/check-home-filters.mjs` 与 `npm run test:home-filters`，先红灯验证首页缺少排序搜索逻辑，再绿灯验证新逻辑和 icon 样式已存在（Frontend Step 3.4）。
- 已验证 `npm run test:home-filters` 和 `npm run build` 均通过。

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
- 已为 `frontend/vite.config.ts` 增加 `envDir: ".."` 和 `/api -> http://localhost:8000` 本地代理，修复本地 Vite 开发时 Google 登录等 Auth 请求误打到 5173 返回 HTML 的问题；并通过 `npm run test:auth-client`、`npm run build` 验证（Frontend Step 3.4）。
- 已为邮箱注册增加昵称和头像上传链路：新增后端 `/api/auth/avatar/presign`、`/api/auth/avatar/complete`，允许注册前上传头像并在注册时写入 `avatar_url`；MinIO 匿名读取策略已扩展到 `avatars/*`（Frontend Step 3.4）。
- 已在前端 Auth Modal 中增加昵称输入、头像文件选择和密码规则提示；注册时执行“头像预签名 -> 直传 -> 完成上传 -> 提交注册”的真实链路（Frontend Step 3.4）。
- 已在顶部导航中显示头像后的昵称，并修复 Home 页筛选 tab 选中态下划线显示问题（Frontend Step 3.4）。
- 已验证 `./.venv/bin/pytest backend/tests/test_auth.py -q`、`cd frontend && npm run test:auth-ui`、`cd frontend && npm run test:auth-client`、`cd frontend && npm run build` 全部通过（Frontend Step 3.4）。

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
