# AI Native 互动游戏平台 MVP 实施计划

## 使用说明

本文档面向 AI 开发者，目标是基于 [design-document.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/design-document.md) 分阶段实现 MVP。

执行要求：

- 每一步都必须小而具体。
- 每一步完成后必须执行对应验证。
- 不要跳步实现。
- 不要在未验证前继续下一步。
- 不要擅自扩大范围。
- Create 页面具体布局尚未最终确认，实现前只搭建必要结构和可验证能力。

## Phase 0：项目基线

### Step 0.1：确认仓库现状 ☑️ 已完成

指令：

- 检查项目根目录现有文件。
- 确认 `docs/tech-stack.md`、`docs/design.md`、`docs/design-document.md` 均存在。
- 确认当前分支和工作区状态。
- 记录已有文件，不删除用户已有内容。

验证：

- 能列出上述 3 个文档。
- 能看到当前 git 状态。
- 工作区中没有因为本步骤产生的无关变更。

### Step 0.2：创建项目目录结构 ☑️ 已完成

指令：

- 创建前端、后端、部署和脚本相关目录。
- 前端目录用于 React + Vite + Ant Design。
- 后端目录用于 FastAPI。
- 保留 `docs/` 作为设计与交付文档目录。
- 不实现业务逻辑，只建立清晰目录边界。

验证：

- 项目目录能清楚区分 frontend、backend、deployment/scripts/docs。
- 空目录如需保留，应放置合适的占位说明文件。
- 运行文件列表命令能看到新结构。

### Step 0.3：建立环境变量样例 ☑️ 已完成

指令：

- 新增 `.env.example`。
- 列出前端、后端、PostgreSQL、MinIO、Session、OpenAI-compatible API、Mock provider 相关变量。
- 列出 Google OAuth 所需 client id、client secret、redirect URI。
- 列出 GitHub OAuth 预留变量，但标注 MVP 不真实跑通。
- 不写任何真实密钥。
- 每个变量需要有简短用途说明。

验证：

- `.env.example` 存在。
- 文件中没有真实 API key、密码或访问令牌。
- 覆盖数据库、对象存储、模型服务、session secret、前后端地址。
- 覆盖 Google OAuth 配置。
- GitHub OAuth 变量清楚标注为后续启用。

## Phase 1：Docker Compose 基础设施

### Step 1.1：定义 Docker Compose 服务 ☑️ 已完成

指令：

- 配置 Docker Compose。
- 服务至少包含 PostgreSQL、MinIO、backend、frontend。
- PostgreSQL 和 MinIO 使用持久化 volume。
- MinIO 需要暴露控制台端口和 S3 API 端口。
- backend 依赖 PostgreSQL 和 MinIO。
- frontend 依赖 backend。

验证：

- Docker Compose 配置语法检查通过。
- 启动后 PostgreSQL 容器健康。
- 启动后 MinIO 控制台可访问。
- backend 和 frontend 服务能启动或进入等待依赖状态。

### Step 1.2：初始化 MinIO bucket ☑️ 已完成

指令：

- 增加 MinIO 初始化流程。
- 创建用于游戏产物和上传素材的 bucket。
- 配置 `published/*` 可公开读取。
- 保持 `uploads/*` 和 `drafts/*` 私有。

验证：

- bucket 创建成功。
- 上传测试对象到 published 路径后，可以通过 public URL 读取。
- 上传测试对象到 uploads 路径后，不能直接 public 读取。
- 能生成 presigned URL 访问私有对象。

### Step 1.3：提供一条启动命令 ☑️ 已完成

指令：

- 在 README 或交付说明中写明本地启动命令。
- 启动命令应覆盖前端、后端、数据库和对象存储。
- 写明首次启动需要复制 `.env.example` 为本地 env 文件并填入必要变量。

验证：

- 新开发者按文档执行命令可以启动依赖服务。
- 端口冲突时文档说明如何调整。
- 服务启动后能访问 frontend、backend health check、MinIO console。

## Phase 2：后端基础

### Step 2.1：创建 FastAPI 应用骨架 ☑️ 已完成

指令：

- 创建 FastAPI 应用入口。
- 提供 health check API。
- 配置 CORS，使前端本地地址可访问后端。
- 配置统一错误响应格式。
- 暂不实现业务 API。

验证：

- 后端服务能启动。
- health check 返回成功。
- 从前端开发服务器 origin 请求 health check 不被 CORS 拦截。
- 后端启动日志无错误。

### Step 2.2：连接 PostgreSQL ☑️ 已完成

指令：

- 配置后端读取数据库连接字符串。
- 建立数据库连接管理。
- 添加数据库迁移机制。
- 不创建业务表前先验证连接。

验证：

- 后端启动时可以连接 PostgreSQL。
- 数据库连接失败时有明确错误。
- 迁移命令可执行。
- 空迁移或初始化迁移执行成功。

### Step 2.3：创建 Phase 4 前核心数据表 ☑️ 已完成

指令：

- 创建 Phase 4 前必需的用户、session、OAuth 账号绑定表。
- 暂不创建游戏、生成任务、上传素材、Agent 日志、Play 事件相关表。
- 创建 OAuth 账号绑定表。
- 表字段以 `design-document.md` 的 Phase 4 前数据模型为准。
- 为 user_id、session_id 建立必要索引。
- 为 OAuth provider 和 provider_user_id 建立唯一约束。
- 将对象存储和游戏相关表放到 Phase 4 及后续阶段创建。

验证：

- 迁移执行成功。
- 数据库中能看到 `users`、`sessions`、`oauth_accounts`。
- 表字段和设计文档一致。
- `oauth_accounts` 表存在，且 `(provider, provider_user_id)` 唯一。
- 重复执行迁移不会破坏已有表。

### Step 2.4：实现基础配置校验 ☑️ 已完成

指令：

- 后端启动时校验必需环境变量。
- 区分必需变量和可选变量。
- OpenAI-compatible API key 在 Mock provider 模式下可以为空。
- 生产模式缺少密钥时必须报错。

验证：

- 缺少数据库配置时后端启动失败并给出明确错误。
- Mock provider 模式下无模型密钥仍可启动。
- OpenAI-compatible provider 模式下缺少模型密钥会失败。
- `.env.example` 与实际校验项一致。

## Phase 3：认证与会话

### Step 3.1：实现邮箱注册 ☑️ 已完成

指令：

- 实现注册 API。
- 校验邮箱格式和密码最小要求。
- 对密码做安全哈希。
- 邮箱唯一。
- 注册成功后返回用户基础信息。

验证：

- 使用有效邮箱和密码可以注册。
- 重复邮箱注册失败。
- 无效邮箱注册失败。
- 数据库中不保存明文密码。

### Step 3.2：实现邮箱登录 ☑️ 已完成

指令：

- 实现登录 API。
- 校验邮箱和密码。
- 登录成功后创建服务端 session。
- 通过 httpOnly cookie 写入 session id。

验证：

- 正确账号密码登录成功。
- 错误密码登录失败。
- 登录响应包含 Set-Cookie。
- Cookie 为 httpOnly。
- sessions 表中有对应 session 记录。

### Step 3.3：实现当前用户与退出登录 ☑️ 已完成

指令：

- 实现获取当前用户 API。
- 实现退出登录 API。
- 退出登录后服务端 session 失效。
- 未登录时返回明确未认证状态。

验证：

- 登录后请求当前用户返回用户信息。
- 未登录请求当前用户返回未认证。
- 退出登录后再次请求当前用户返回未认证。
- 退出登录后受保护 API 不可访问。

### Step 3.4：保护需要登录的后端 API

指令：

- 为 Create、上传、任务、发布和删除接口加登录校验。
- Home 和 published Play 相关接口保持公开。
- draft 资源只允许 owner 访问。

验证：

- 未登录可以访问 published 游戏列表。
- 未登录不能创建任务。
- 未登录不能上传素材。
- 非 owner 不能访问他人的 draft 游戏。
- owner 可以访问自己的 draft 游戏。

### Step 3.5：实现 Google OAuth 登录 ☑️ 已完成

指令：

- 实现 Google OAuth 授权开始接口。
- 实现 Google OAuth 回调接口。
- 使用 `state` 参数防止 CSRF。
- 回调中用授权码换取 token，并获取 Google 用户唯一 ID、邮箱、展示名和头像。
- 如果已有 Google 绑定记录，直接登录对应用户。
- 如果没有绑定记录，但邮箱已注册，则绑定到已有用户。
- 如果邮箱不存在，则创建新用户并绑定 Google 账号。
- 登录成功后创建服务端 session，并写入 httpOnly cookie。
- 回调完成后跳回前端原页面或默认页面。

验证：

- 点击 Google 登录可以跳转到 Google 授权页。
- 授权成功后能回到应用。
- 首次 Google 登录会创建用户和 `oauth_accounts` 绑定记录。
- 再次 Google 登录会复用同一个用户，不重复创建账号。
- 邮箱已通过邮箱注册时，Google 登录会绑定到已有用户。
- 登录成功后 `GET /api/auth/me` 返回当前用户。
- 登录成功后可以访问 Create 受保护页面。
- `state` 缺失或错误时回调失败。

### Step 3.6：保留 GitHub OAuth 设计占位 ☑️ 已完成

指令：

- 在后端保留 GitHub OAuth start 和 callback 路由设计。
- MVP 中 GitHub OAuth 可以返回未启用状态。
- 数据模型必须支持 `provider=github`。
- README 或完成度说明中标注 GitHub OAuth 后续版本真实跑通。

验证：

- GitHub OAuth 路由存在或有明确未启用响应。
- `oauth_accounts.provider` 支持 github。
- GitHub 未启用不会影响邮箱登录和 Google 登录。
- 文档明确说明 GitHub OAuth 后续实现。

## Phase 4：对象存储与产物协议

### Step 4.1：封装 MinIO 访问

指令：

- 后端封装 MinIO 客户端。
- 支持上传对象、生成 presigned URL、生成 public URL。
- 不在业务代码中散落 bucket 名和路径拼接逻辑。

验证：

- 可以上传测试对象。
- 可以生成 private object 的 presigned URL。
- 可以生成 published object 的 public URL。
- MinIO 不可用时后端返回明确错误。

### Step 4.2：实现上传 presign API

指令：

- 实现获取上传 presigned URL 的 API。
- 登录用户才能请求。
- 支持任意文件类型。
- 记录文件名、MIME type、大小和用途说明。
- 限制单文件最大 20MB。
- 限制单任务最多 5 个文件。

验证：

- 登录用户能获取 presigned URL。
- 未登录用户不能获取 presigned URL。
- 超过大小限制的文件请求被拒绝。
- 单任务超过 5 个文件被拒绝。
- 上传完成后数据库有 uploaded_assets 记录。

### Step 4.3：准备静态游戏产物样例

指令：

- 准备至少两个可运行的静态 HTML5 游戏样例 bundle。
- 每个 bundle 包含 `manifest.json`、`index.html`、`style.css`、`game.js`、`assets/*`。
- 上传到 MinIO published 路径。
- 在数据库中写入对应 published 游戏记录。

验证：

- 每个样例游戏的 manifest URL 可公开访问。
- 每个样例游戏的 index.html 可公开访问。
- 数据库中有至少 2 条 published 游戏记录。
- 通过浏览器直接打开样例 index.html 能看到可运行内容。

## Phase 5：游戏列表与 Play 后端

### Step 5.1：实现 published 游戏列表 API

指令：

- 实现 `GET /api/games`。
- 只返回 published 游戏。
- 支持按最新发布排序。
- 支持按游玩次数排序。
- 返回 Home 卡片所需字段。

验证：

- 接口只返回 published 游戏。
- draft 游戏不会出现在列表中。
- `sort=latest` 按发布时间倒序。
- `sort=play_count` 按游玩次数倒序。
- 返回字段包含封面、标题、作者、简介、标签、发布时间、游玩次数。

### Step 5.2：实现游戏详情 meta API

指令：

- 实现 `GET /api/games/{game_id}`。
- published 游戏公开可访问。
- draft 游戏只有 owner 可访问。
- 返回 Play 加载所需 meta 和 manifest URL。

验证：

- 游客可以获取 published 游戏 meta。
- 游客不能获取 draft 游戏 meta。
- owner 可以获取自己的 draft 游戏 meta。
- 返回的 manifest URL 可以被 Play 页面读取。

### Step 5.3：实现 Play 事件 API

指令：

- 实现 Play 事件记录 API。
- 支持记录 view、manifest_loaded、started、failed、exited。
- view 或 started 事件应更新 games.play_count。
- 游客事件 user_id 可为空。

验证：

- 发送 view 事件后数据库有 play_events 记录。
- 游客发送事件成功。
- 登录用户发送事件时记录 user_id。
- play_count 随有效事件增加。
- 无效 event_type 被拒绝。

## Phase 6：生成任务后端

### Step 6.1：创建生成任务 API

指令：

- 实现创建生成任务 API。
- 登录用户才能创建。
- 接收创意文本和已上传素材 ID 列表。
- 创建 generation_job，初始状态为 pending。
- 使用 FastAPI BackgroundTasks 启动后台执行。

验证：

- 登录用户可以创建任务。
- 未登录用户不能创建任务。
- 创建后数据库出现 pending 任务。
- 响应返回 job id。
- 后台任务启动后状态会进入 running。

### Step 6.2：实现 Mock provider 生成链路

指令：

- 在 Mock provider 模式下，后台任务生成一个固定但非前端硬编码的游戏 bundle。
- bundle 必须上传到 MinIO drafts 路径。
- 生成 `manifest.json`、`index.html`、`style.css`、`game.js`。
- 任务成功后创建 draft game 记录。

验证：

- Mock provider 模式下任务能从 pending 变为 running 再变为 succeeded。
- MinIO drafts 路径出现完整 bundle。
- 数据库中出现 draft game。
- draft game 关联 generation_job。
- draft manifest 可以通过 owner 授权方式访问。

### Step 6.3：接入 OpenAI-compatible provider

指令：

- 增加真实 OpenAI-compatible API provider。
- provider 只在后端运行。
- API key 从环境变量读取。
- 输出仍必须落到标准游戏产物协议。
- 如果模型调用失败，任务进入 failed 并记录错误摘要。

验证：

- provider 配置为 OpenAI-compatible 时会调用真实模型服务。
- 缺少 API key 时后端启动或任务执行明确失败。
- 模型调用失败时任务状态为 failed。
- failed 任务有 error_message。
- succeeded 任务产物协议与 Mock provider 一致。

### Step 6.4：记录任务日志

指令：

- 后台任务每个关键步骤写入 agent_logs。
- 日志需要可读，不暴露密钥。
- 日志至少覆盖任务开始、素材读取、生成产物、上传产物、创建 draft、任务完成或失败。

验证：

- 创建任务后能看到日志逐步增加。
- succeeded 任务有完整日志链路。
- failed 任务有错误日志。
- 日志不包含 API key、session id 或 presigned URL 全量敏感信息。

### Step 6.5：实现任务历史 API

指令：

- 实现获取当前用户任务历史 API。
- 只返回当前用户任务。
- 支持按创建时间倒序。
- 每条任务包含状态、创意摘要、创建时间、更新时间、关联 draft game、错误信息摘要。

验证：

- 用户只能看到自己的任务。
- 多个并发任务都能出现在任务历史中。
- 状态变化后历史接口能返回最新状态。
- 未登录请求失败。

### Step 6.6：实现任务日志 API

指令：

- 实现获取单个任务日志 API。
- 只有任务 owner 可访问。
- 日志按时间正序返回。

验证：

- owner 能获取自己的任务日志。
- 非 owner 不能获取。
- 未登录不能获取。
- 日志顺序正确。

## Phase 7：发布流程

### Step 7.1：实现发布 API

指令：

- 实现发布 draft 游戏 API。
- 只有 owner 可以发布。
- 发布时将游戏状态从 draft 改为 published。
- 将产物复制或转存到 published 路径。
- 更新 manifest_url 为 public-read URL。
- 写入 published_at。

验证：

- owner 可以发布自己的 draft 游戏。
- 非 owner 不能发布。
- 已发布游戏出现在 Home 列表。
- 发布后的 manifest URL 可公开访问。
- published_at 被正确写入。

### Step 7.2：限制发布后编辑

指令：

- MVP 不提供发布后编辑标题、简介、标签、封面能力。
- 确保没有暴露对应 API 或 UI。
- 在后续规划中保留该能力。

验证：

- API 列表中没有发布后编辑接口。
- 前端没有发布后编辑入口。
- 文档中明确说明该能力放后续版本。

### Step 7.3：实现删除限制

指令：

- 仅允许用户删除自己的 draft 或任务产物。
- 发布后的游戏删除或下架不进入 MVP。
- 删除采用逻辑删除。

验证：

- owner 可以删除自己的 draft。
- 非 owner 不能删除。
- 删除后 draft 不再可预览。
- published 游戏没有普通用户删除入口。

## Phase 8：前端基础

### Step 8.1：创建 React + Vite + Ant Design 项目

指令：

- 创建前端应用。
- 接入 Ant Design。
- 配置路由。
- 配置 API 请求基础地址。
- 配置全局深色主题和 Yahaha 风格主色。

验证：

- 前端开发服务可以启动。
- 浏览器能打开首页。
- Ant Design 组件样式正常。
- API 基础地址来自环境变量。

### Step 8.2：实现全局布局和导航

指令：

- 实现全局导航。
- 未登录显示 Sign In。
- 已登录显示用户邮箱和 Logout。
- Home 和 Play 允许游客访问。
- Create 入口未登录时触发 Auth Modal。

验证：

- 未登录状态下可以看到 Home。
- 点击 Sign In 打开 Auth Modal。
- 登录后导航显示用户信息。
- 点击 Logout 后恢复未登录状态。
- 未登录点击 Create 会弹出 Auth Modal。

### Step 8.3：实现 Auth Modal

指令：

- 实现登录/注册模式切换。
- 表单使用邮箱和密码。
- 注册态显示确认密码。
- 增加 Google 登录按钮，并连接真实 Google OAuth 授权开始接口。
- 增加 GitHub 登录按钮或占位入口，但明确展示暂未启用。
- 登录成功后刷新当前用户状态。
- 错误信息在弹窗内展示。

验证：

- 可以注册新用户。
- 可以登录已注册用户。
- 错误密码有明确提示。
- 注册重复邮箱有明确提示。
- 点击 Google 登录能进入 Google OAuth 授权流程。
- Google OAuth 成功回调后弹窗关闭或页面恢复登录态。
- GitHub 登录入口不会误导为已可用能力。
- 登录成功后弹窗关闭并显示用户状态。

## Phase 9：Home 前端

### Step 9.1：实现游戏列表展示

指令：

- 从后端获取 published 游戏列表。
- 使用卡片展示封面、标题、作者、简介、标签、发布时间和游玩次数。
- 不使用前端硬编码数组作为唯一数据源。

验证：

- 页面加载后调用后端 games API。
- 至少显示 2 个 seed 游戏。
- 卡片字段完整。
- 删除或修改数据库数据后 Home 展示会随接口变化。

### Step 9.2：实现排序切换

指令：

- 提供最新发布和最多游玩两个排序选项。
- 切换排序时重新请求后端或更新列表。
- 当前排序状态在 UI 中清晰可见。

验证：

- 默认排序为最新发布。
- 切换到最多游玩后顺序变化符合 play_count。
- 切回最新发布后顺序符合 published_at。
- 排序选项不会影响未登录访问。

### Step 9.3：实现进入 Play

指令：

- 点击游戏卡片进入 Play 页面。
- 使用游戏 ID 构建路由。
- 不做 Game Detail 页面。

验证：

- 点击任意卡片能进入对应 Play URL。
- URL 中包含 game id。
- 浏览器刷新 Play URL 后仍可加载。

## Phase 10：Play 前端

### Step 10.1：加载游戏 meta

指令：

- Play 页面根据路由 game id 请求后端 meta。
- 展示 loading、failed 和 ready 状态。
- failed 状态提供重试和返回 Home。

验证：

- 有效 published game id 能加载 meta。
- 无效 game id 显示错误态。
- 网络失败显示错误态，不白屏。
- 返回 Home 按钮可用。

### Step 10.2：加载 manifest

指令：

- 从 meta 中读取 manifest URL。
- 前端请求 manifest。
- 校验 manifest 中 entry 字段存在。
- manifest 加载失败时显示错误态。

验证：

- 有效 manifest 能加载。
- manifest URL 不可访问时显示错误态。
- 缺少 entry 字段时显示错误态。
- 加载成功后记录 manifest_loaded 事件。

### Step 10.3：运行 sandboxed iframe

指令：

- 根据 manifest entry 构建 iframe URL。
- 使用 sandboxed iframe 运行游戏。
- 页面展示标题、作者、简介、标签、游玩次数、返回、重新开始。
- 不将游戏实现为本地 React 组件。

验证：

- iframe 加载的是 MinIO public URL。
- iframe 中能看到游戏内容。
- 浏览器检查 iframe src 不是本地前端路由。
- 重新开始会刷新 iframe。
- started 或 view 事件成功上报。

### Step 10.4：验证 Play 计数

指令：

- Play 页面进入时上报 view 或 started。
- 后端更新 play_count。
- Home 列表展示更新后的游玩次数。

验证：

- 进入 Play 后 play_count 增加。
- 返回 Home 后对应卡片游玩次数更新。
- 游玩次数排序会受更新影响。

## Phase 11：Create 前端

### Step 11.1：实现 Create 访问保护

指令：

- Create 页面需要登录。
- 未登录进入 Create 时弹出 Auth Modal。
- 登录成功后停留在 Create。

验证：

- 未登录访问 Create 会弹出登录弹窗。
- 登录成功后可以看到 Create 基础页面。
- 退出登录后再次访问 Create 会被拦截。

### Step 11.2：搭建 Create 基础结构

指令：

- 只实现必要结构，不做最终复杂布局。
- 包含创意输入、文件上传、提交按钮、任务历史区域。
- 标注 Create 详细布局后续需要确认。

验证：

- 页面上能看到创意输入入口。
- 页面上能看到文件上传入口。
- 页面上能看到任务历史区域。
- 没有实现未确认的复杂聊天式 UI。

### Step 11.3：实现文件上传

指令：

- 支持选择任意文件。
- 上传前请求 presigned URL。
- 上传成功后调用 complete API。
- 展示上传中、成功、失败状态。
- 限制单文件 20MB，单任务最多 5 个文件。

验证：

- 小于 20MB 的文件可以上传。
- 大于 20MB 的文件被前端或后端拒绝。
- 上传成功后 UI 显示文件名。
- 数据库中有 uploaded_assets 记录。
- 超过 5 个文件不能继续添加。

### Step 11.4：实现创建任务

指令：

- 用户输入创意并选择已上传素材后，可以提交任务。
- 调用创建任务 API。
- 提交成功后任务出现在任务历史中。
- 支持连续提交多个任务。

验证：

- 空创意不能提交。
- 有效创意可以提交。
- 提交后出现 pending 任务。
- 连续提交多个任务后历史中出现多条任务。
- 每条任务都有独立 job id。

### Step 11.5：实现任务历史轮询

指令：

- Create 页面定时刷新当前用户任务历史。
- 展示每条任务的状态。
- 支持 pending、running、succeeded、failed。
- 不阻塞用户提交新任务。

验证：

- pending 任务会自动更新为 running。
- succeeded 任务会自动显示成功状态。
- failed 任务会自动显示失败状态和错误摘要。
- 多个并发任务状态互不覆盖。

### Step 11.6：展示任务日志

指令：

- 每条任务提供查看日志入口。
- 日志按时间正序展示。
- 默认可以折叠，避免任务列表过长。

验证：

- succeeded 任务能看到完整日志。
- failed 任务能看到错误日志。
- 日志顺序正确。
- 非当前用户不能通过接口查看日志。

### Step 11.7：实现 draft 预览

指令：

- succeeded 任务显示预览入口。
- 预览使用 Play 运行机制加载 draft game。
- draft 只允许 owner 预览。

验证：

- owner 可以预览自己的 succeeded 任务。
- 游客不能预览 draft。
- 非 owner 不能预览 draft。
- 预览 iframe 仍加载 MinIO 中的 manifest 和 bundle。

### Step 11.8：实现发布按钮

指令：

- succeeded 任务显示 Publish 按钮。
- 点击后调用发布 API。
- 发布成功后任务关联游戏进入 Home。
- 发布后不显示编辑标题、简介、标签、封面入口。

验证：

- owner 可以发布 draft。
- 发布后 Home 能看到新游戏。
- 游客可以进入新游戏 Play。
- 发布后的游戏没有 meta 编辑入口。
- 非 owner 不能发布。

## Phase 12：端到端验收

### Step 12.1：验证游客浏览游玩链路

指令：

- 使用全新浏览器会话或清除登录态。
- 访问 Home。
- 切换排序。
- 点击一个 seed 游戏进入 Play。
- 完成一次 iframe 加载。

验证：

- 未登录可以浏览 Home。
- 未登录可以进入 Play。
- iframe 加载远端 MinIO URL。
- play_count 增加。
- 页面无白屏。

### Step 12.2：验证注册登录链路

指令：

- 打开 Auth Modal。
- 注册一个新账号。
- 退出登录。
- 使用同一账号重新登录。
- 刷新页面验证 session。
- 使用 Google OAuth 注册或登录一个账号。
- 查看 OAuth 登录后的 session 状态和受保护页面访问控制。

验证：

- 注册成功。
- 退出后当前用户状态清空。
- 重新登录成功。
- 刷新后仍保持登录态。
- httpOnly cookie 存在。
- Google OAuth 授权回调成功。
- Google OAuth 登录后 `oauth_accounts` 有绑定记录。
- Google OAuth 登录后 `GET /api/auth/me` 返回用户。
- Google OAuth 登录后可以访问 Create。
- GitHub OAuth 标注为后续实现，不作为 MVP 真实验收项。

### Step 12.3：验证 Create 到 Publish 链路

指令：

- 登录用户进入 Create。
- 上传至少一个文件。
- 输入创意。
- 创建生成任务。
- 等待任务 succeeded。
- 查看任务日志。
- 预览 draft。
- 点击 Publish。
- 回到 Home 查找新游戏。
- 进入 Play 游玩新游戏。

验证：

- uploaded_assets 有记录。
- generation_jobs 有记录。
- agent_logs 有记录。
- games 中先出现 draft，再变为 published。
- MinIO 中有 draft 和 published 产物。
- Home 出现新发布游戏。
- Play iframe 加载新游戏的 published manifest。

### Step 12.4：验证并发任务

指令：

- 同一用户连续提交至少 2 个生成任务。
- 不等待第一个完成就提交第二个。
- 观察任务历史。

验证：

- 两个任务都有独立 job id。
- 两个任务状态分别更新。
- 一个任务失败不会影响另一个任务。
- 两个任务日志互不混淆。

### Step 12.5：验证权限隔离

指令：

- 创建用户 A 和用户 B。
- 用户 A 创建 draft。
- 用户 B 尝试访问用户 A 的 draft meta、日志和发布接口。
- 游客尝试访问 draft。

验证：

- 用户 B 不能访问用户 A 的 draft。
- 用户 B 不能查看用户 A 的任务日志。
- 用户 B 不能发布用户 A 的游戏。
- 游客不能访问 draft。
- published 游戏仍对所有人可访问。

## Phase 13：交付文档与收尾

### Step 13.1：完善 README

指令：

- 写清项目目标。
- 写清技术栈。
- 写清启动命令。
- 写清环境变量配置。
- 写清测试账号或 seed 数据。
- 写清核心链路演示步骤。

验证：

- 新开发者只看 README 可以启动项目。
- README 中没有真实密钥。
- README 覆盖 Home、Auth、Create、Publish、Play 演示步骤。

### Step 13.2：补充完成度说明

指令：

- 在 docs 中补充完成度说明。
- 明确已完成、未完成、Mock 的部分。
- 明确如果再给 1 周的迭代计划。

验证：

- 文档明确列出 MVP 范围。
- 文档明确列出后续能力：Game Detail、搜索、标签筛选、点赞、收藏、发布后编辑、取消发布、平台维护者后台。
- Mock provider 的用途说明清楚。

### Step 13.3：执行最终自动化检查

指令：

- 执行前端 lint 或 build。
- 执行后端测试或基础 API 测试。
- 执行数据库迁移验证。
- 执行 Docker Compose 启动验证。

验证：

- 前端构建通过。
- 后端测试通过。
- 数据库迁移可从空库执行。
- Docker Compose 可完整启动。
- 核心端到端手工验收通过。

### Step 13.4：提交前检查

指令：

- 检查 git diff。
- 确认没有提交真实密钥、临时日志、大文件或本地 MinIO 数据。
- 确认文档、前端、后端、部署文件均在正确位置。
- 确认提交记录不少于 3 次，或准备拆分为清晰提交。

验证：

- git diff 内容符合预期。
- 没有 `.env` 真实文件被提交。
- 没有对象存储数据目录被提交。
- 交付物满足 PRD 的必选项。
