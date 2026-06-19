# Frontend 实施计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 独立完成 React + Vite + Ant Design 前端的全局导航、Auth Modal、Home 游戏流、Create 工作台、Play sandbox runtime、Console 输出和错误反馈。

**架构：** 前端以 [api-contract.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/api-contract.md) 为唯一接口契约，可先使用 mock API 开发。页面行为以 [pages-design.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/pages-design.md) 为准，最终切换到真实后端时不改字段名。Play 和 Create 试玩都通过 manifest + sandboxed iframe 加载远端游戏产物，不实现本地 React 游戏组件。

**技术栈：** React、Vite、TypeScript、Ant Design、浏览器 DevTools Console、sandboxed iframe。

---

## 1. 必读上下文

前端开发者单独拿到本文档时，必须先阅读：

- [pages-design.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/pages-design.md)：页面数量、组件、布局、状态和交互。
- [design-document.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/design-document.md)：产品范围、权限、安全和运行时协议。
- [api-contract.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/api-contract.md)：接口字段、状态码、错误格式和 mock 约定。
- [design.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/design.md)：Yahaha 风格视觉系统。
- [architecture.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/architecture.md)：目录边界和文件职责。
- [progress.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/progress.md)：已完成步骤和当前缺口。

已有前端基线：

- React + Vite + Ant Design 基线已存在。
- 最小导航和 Auth Modal 基线已存在。
- 后端 Auth API 已有邮箱登录注册、退出登录、当前用户、Google OAuth 路径。

## 2. 前端独立运行原则

- 前端不能等待后端完成，必须能基于 [api-contract.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/api-contract.md) 使用 mock 数据开发。
- mock 数据字段名、状态码和错误格式必须与真实 API 契约一致。
- mock 只用于开发，不作为最终验收。
- 未登录用户可以访问 Home 和 Play，但点击点赞或 Create 时必须弹 Auth Modal。
- 页面内不新增调试面板；调试信息只输出到浏览器 DevTools Console。
- 不实现收藏、独立 Game Detail、My Games/Profile、Admin Console、发布后编辑、取消发布、GitHub OAuth 真实跑通、版本管理、Remix、内容审核、资源限额和成本统计。
- 每完成一个任务，更新 [architecture.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/architecture.md) 和 [progress.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/progress.md)。

## 3. 与其他端的接口边界

### 依赖后端

最终联调需要后端提供：

- Auth API：邮箱注册、邮箱登录、退出登录、`GET /api/auth/me`、Google OAuth、GitHub 未启用占位。
- Games API：`GET /api/games`、`GET /api/games/{game_id}`、点赞、发布。
- Uploads API：上传 presign、上传完成登记。
- Jobs API：创建任务、任务历史、任务详情、任务日志。
- Play Events API：Play 事件上报。

开发阶段可用 mock 替代，联调时只切 API base URL。

### 依赖 Agent

前端不直接调用 Agent。前端只通过 Jobs API 观察任务状态和日志。

前端需要展示：

- `pending / running / succeeded / failed`
- Agent 当前关键步骤
- Agent 可读日志摘要
- failed 原因
- succeeded draft game

## 4. Frontend Tasks

## Step 1：统一前端路由和全局 API 客户端

依赖其他端：不需要；依赖 [api-contract.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/api-contract.md)。

### Step 1.1：指令

- [ ] 建立 Home、Create、Play 三个路由。
### Step 1.2：指令

- [ ] 保留 Auth Modal 为全局弹窗，不做 Auth 独立页面。
### Step 1.3：指令

- [ ] API 客户端统一处理 base URL、cookie、错误格式、401 回调。
### Step 1.4：指令

- [ ] 401 默认触发 Auth Modal，除 `GET /api/auth/me` 外不弹 Error。
### Step 1.5：指令

- [ ] 增加 mock API 开关，mock 响应必须符合 [api-contract.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/api-contract.md)。
### Step 1.6：指令

- [ ] DevTools Console 输出使用结构化对象。
### Step 1.7：验证

- [ ] `/` 能进入 Home。
### Step 1.8：验证

- [ ] `/create` 未登录时弹 Auth Modal。
### Step 1.9：验证

- [ ] `/play/:gameId` 可以直接刷新访问。
### Step 1.10：验证

- [ ] API 错误统一进入 Error 弹窗或表单错误。
### Step 1.11：验证

- [ ] Console 不打印 secret、token、password 或 OAuth code。

## Step 2：完善全局导航和登录态展示

依赖其他端：可先 mock；最终联调依赖后端 Auth。

### Step 2.1：指令

- [ ] 未登录显示默认头像和 `登录`。
### Step 2.2：指令

- [ ] 已登录显示头像和昵称。
### Step 2.3：指令

- [ ] 已登录展开菜单提供 `退出登录`。
### Step 2.4：指令

- [ ] 点击 `创建游戏` 时，未登录弹 Auth Modal，不跳转。
### Step 2.5：指令

- [ ] 退出登录后头像恢复默认头像，昵称区域恢复为 `登录`。
### Step 2.6：验证

- [ ] 未登录可以浏览 Home。
### Step 2.7：验证

- [ ] 点击登录打开 Auth Modal。
### Step 2.8：验证

- [ ] 登录成功后头像和昵称更新。
### Step 2.9：验证

- [ ] 退出登录后恢复未登录展示。
### Step 2.10：验证

- [ ] 未登录点击 Create 不改变页面路由，只弹 Auth Modal。

## Step 3：完善 Auth Modal

依赖其他端：可先 mock；最终联调依赖后端 Auth 和 Google OAuth。

### Step 3.1：指令

- [ ] 登录和注册在同一个弹窗内切换。
### Step 3.2：指令

- [ ] 注册入口文案是 `注册`。
### Step 3.3：指令

- [ ] 邮箱登录、邮箱注册、退出登录走 API 客户端。
### Step 3.4：指令

- [ ] Google 登录按钮进入 Google OAuth start 流程。
### Step 3.5：指令

- [ ] GitHub 入口显示未启用或 disabled。
### Step 3.6：指令

- [ ] 登录成功后关闭弹窗，显示成功提示，并刷新当前用户。
### Step 3.7：指令

- [ ] 登录、注册、OAuth 失败时显示明确错误。
### Step 3.8：验证

- [ ] mock 新邮箱注册成功并创建 session 状态。
### Step 3.9：验证

- [ ] mock 重复邮箱注册显示明确错误。
### Step 3.10：验证

- [ ] mock 正确账号密码登录成功。
### Step 3.11：验证

- [ ] mock 错误密码登录失败并显示错误。
### Step 3.12：验证

- [ ] 真实 Google OAuth 成功后返回应用并显示 OAuth 头像和昵称。
### Step 3.13：验证

- [ ] GitHub 入口不会误导用户为已可用。

## Step 4：实现 Home 游戏流

依赖其他端：可先 mock；最终联调依赖后端 Games API 和 seed 数据。

### Step 4.1：指令

- [ ] 从 `GET /api/games` 获取 published 游戏。
### Step 4.2：指令

- [ ] 展示封面、标题、作者、发布时间、标签、点赞数、游玩次数。
### Step 4.3：指令

- [ ] 简介只在 hover 浮层显示。
### Step 4.4：指令

- [ ] 支持最新发布、最多游玩、最多点赞排序。
### Step 4.5：指令

- [ ] 支持搜索和标签筛选。
### Step 4.6：指令

- [ ] 点击卡片主体进入 Play。
### Step 4.7：指令

- [ ] 标签不是 Play 入口。
### Step 4.8：验证

- [ ] Home 未登录可访问。
### Step 4.9：验证

- [ ] 页面加载时调用游戏列表 API 或 mock API。
### Step 4.10：验证

- [ ] 至少展示 3 个游戏，其中最终验收至少 1 个来自 Create 发布。
### Step 4.11：验证

- [ ] 排序切换后请求参数和展示顺序正确。
### Step 4.12：验证

- [ ] 搜索和标签筛选能改变列表结果。
### Step 4.13：验证

- [ ] 点击卡片进入对应 Play URL。

## Step 5：实现 Home 点赞交互

依赖其他端：可先 mock；最终联调依赖后端点赞 API。

### Step 5.1：指令

- [ ] 点赞图标和卡片点击区域分离。
### Step 5.2：指令

- [ ] 登录用户点击点赞图标调用点赞 API。
### Step 5.3：指令

- [ ] 未登录用户点击点赞图标弹 Auth Modal，不调用点赞 API。
### Step 5.4：指令

- [ ] 点赞成功后更新卡片点赞数。
### Step 5.5：指令

- [ ] MVP 不提供取消点赞。
### Step 5.6：验证

- [ ] 未登录点击点赞只弹 Auth Modal。
### Step 5.7：验证

- [ ] 未登录点赞不会进入 Play。
### Step 5.8：验证

- [ ] 登录用户点击点赞后点赞数更新。
### Step 5.9：验证

- [ ] 重复点击不会重复增加点赞数。
### Step 5.10：验证

- [ ] Console 输出登录点赞结果或未登录触发 Auth Modal 的原因。

## Step 6：实现 Create 页面布局

依赖其他端：不需要。

### Step 6.1：指令

- [ ] 使用左侧任务列表、聊天与上传区、生成游戏显示面板三块布局。
### Step 6.2：指令

- [ ] 页面以自然语言对话为主，不做结构化输入表单。
### Step 6.3：指令

- [ ] 左侧任务列表显示任务名、状态、创建时间、结果摘要和 `+ 新建任务`。
### Step 6.4：指令

- [ ] 聊天区显示 Agent 欢迎消息、AI 追问、用户消息、最终确认卡片、输入框、附件 icon、发送 icon、文件列表。
### Step 6.5：指令

- [ ] 生成游戏显示面板支持 idle、pending、running、succeeded、failed、timeout 状态。
### Step 6.6：验证

- [ ] 未登录访问 Create 弹 Auth Modal。
### Step 6.7：验证

- [ ] 登录后能看到三块布局。
### Step 6.8：验证

- [ ] 任务状态 badge 支持 `pending / running / succeeded / failed`。
### Step 6.9：验证

- [ ] 页面没有结构化表单入口。
### Step 6.10：验证

- [ ] 页面没有发布后编辑入口。

## Step 7：实现最终确认卡片

依赖其他端：可先 mock；最终通过 Jobs API 提交。

### Step 7.1：指令

- [ ] AI 追问结束后展示最终确认卡片。
### Step 7.2：指令

- [ ] 卡片字段包括游戏标题、一句话简介、游戏类型、核心玩法、胜负条件、操作方式、使用到的素材、标签、封面建议。
### Step 7.3：指令

- [ ] 用户可以直接在卡片里修改这些字段。
### Step 7.4：指令

- [ ] 创建任务时把卡片内容作为 `confirmation` 传给后端。
### Step 7.5：验证

- [ ] 卡片展示全部字段。
### Step 7.6：验证

- [ ] 用户修改字段后，本地状态同步更新。
### Step 7.7：验证

- [ ] 创建任务请求包含修改后的卡片内容。
### Step 7.8：验证

- [ ] 空标题或空创意时不能提交。

## Step 8：实现 Create 文件上传

依赖其他端：可先 mock；最终联调依赖后端 Uploads API。

### Step 8.1：指令

- [ ] 附件 icon 点击后选择文件。
### Step 8.2：指令

- [ ] 支持任意文件类型。
### Step 8.3：指令

- [ ] 单文件超过 `20MB` 时阻止或展示错误。
### Step 8.4：指令

- [ ] 上传前请求 presigned URL。
### Step 8.5：指令

- [ ] 上传成功后调用 complete API。
### Step 8.6：指令

- [ ] 上传成功后的文件列表显示在用户聊天框下方。
### Step 8.7：指令

- [ ] 上传失败弹 Error，并提示重新上传。
### Step 8.8：验证

- [ ] 小于 `20MB` 的文件可以上传。
### Step 8.9：验证

- [ ] 大于 `20MB` 的文件显示错误。
### Step 8.10：验证

- [ ] 上传成功后文件名显示在聊天框下方。
### Step 8.11：验证

- [ ] 上传失败时出现 Error 弹窗和重试提示。
### Step 8.12：验证

- [ ] Console 输出文件名、大小、MIME type、object key 摘要。

## Step 9：实现任务创建和历史轮询

依赖其他端：可先 mock；最终联调依赖后端 Jobs API 和 Agent 执行结果。

### Step 9.1：指令

- [ ] 提交自然语言创意、素材 ID 列表和最终确认卡片。
### Step 9.2：指令

- [ ] 创建任务成功后任务进入左侧任务列表。
### Step 9.3：指令

- [ ] 定时刷新当前用户任务历史。
### Step 9.4：指令

- [ ] 用户离开 Create 再回来仍能看到任务历史。
### Step 9.5：指令

- [ ] 支持多个并发任务。
### Step 9.6：验证

- [ ] 有效创意可以创建任务。
### Step 9.7：验证

- [ ] 空创意不能创建任务。
### Step 9.8：验证

- [ ] 创建后显示 `pending` 状态。
### Step 9.9：验证

- [ ] 任务状态能更新为 `running / succeeded / failed`。
### Step 9.10：验证

- [ ] 连续提交多个任务时，每个任务状态独立。
### Step 9.11：验证

- [ ] 刷新页面后任务历史仍存在。

## Step 10：展示 Agent 日志和生成面板状态

依赖其他端：可先 mock；最终联调依赖后端 Jobs Logs API。

### Step 10.1：指令

- [ ] 生成游戏显示面板展示 Agent 当前关键步骤。
### Step 10.2：指令

- [ ] 展示关键步骤列表、每步状态和可读日志摘要。
### Step 10.3：指令

- [ ] failed 时显示失败步骤和失败原因。
### Step 10.4：指令

- [ ] running 时显示进度条或当前步骤。
### Step 10.5：指令

- [ ] timeout 时显示 Error 弹窗和重试入口。
### Step 10.6：验证

- [ ] running 任务显示当前步骤。
### Step 10.7：验证

- [ ] succeeded 任务显示完整日志摘要。
### Step 10.8：验证

- [ ] failed 任务显示失败原因。
### Step 10.9：验证

- [ ] 日志顺序与接口返回一致。
### Step 10.10：验证

- [ ] Console 输出任务 ID、状态、当前步骤、错误日志。

## Step 11：实现 Create 内试玩和发布

依赖其他端：可先 mock；最终联调依赖后端 Games meta、Jobs、Publish API 和 Agent 产物。

### Step 11.1：指令

- [ ] succeeded 任务在生成游戏面板中直接显示可试玩游戏。
### Step 11.2：指令

- [ ] 试玩即 Preview，不新增 Preview 按钮。
### Step 11.3：指令

- [ ] 试玩使用与 Play 相同的 manifest 加载和 iframe 机制。
### Step 11.4：指令

- [ ] Publish 按钮放在游戏旁边。
### Step 11.5：指令

- [ ] 点击 Publish 后按钮显示上传中。
### Step 11.6：指令

- [ ] 发布成功后跳转 Home。
### Step 11.7：指令

- [ ] Home 新增用户刚发布的游戏。
### Step 11.8：验证

- [ ] succeeded 任务显示可试玩游戏。
### Step 11.9：验证

- [ ] draft 试玩 iframe 加载远端或授权 URL，不是本地 React 组件。
### Step 11.10：验证

- [ ] Publish loading 状态可见。
### Step 11.11：验证

- [ ] 发布成功后自动跳转 Home。
### Step 11.12：验证

- [ ] Home 能看到刚发布游戏。
### Step 11.13：验证

- [ ] 发布失败时 Error 弹窗提示可重试。

## Step 12：实现 Play 页面加载链路

依赖其他端：可先 mock；最终联调依赖后端 Games meta、Play Events 和 seed 数据。

### Step 12.1：指令

- [ ] 根据路由 game id 请求 game meta。
### Step 12.2：指令

- [ ] 加载 manifest。
### Step 12.3：指令

- [ ] 根据 manifest entry 构建 iframe URL。
### Step 12.4：指令

- [ ] iframe 使用 `sandbox="allow-scripts"`。
### Step 12.5：指令

- [ ] 不启用 `allow-same-origin`、`allow-forms`、`allow-popups`、`allow-top-navigation`。
### Step 12.6：指令

- [ ] 页面左侧展示标题、作者、发布时间、简介、标签、点赞数、游玩次数和返回 Home。
### Step 12.7：指令

- [ ] 未 load 完成时显示转圈 loading。
### Step 12.8：验证

- [ ] 有效 game id 能加载并进入 ready。
### Step 12.9：验证

- [ ] 无效 game id 显示错误态。
### Step 12.10：验证

- [ ] manifest 不可访问时显示错误态。
### Step 12.11：验证

- [ ] iframe src 是 MinIO 或 S3-compatible URL。
### Step 12.12：验证

- [ ] iframe sandbox 属性符合设计。
### Step 12.13：验证

- [ ] Play 左侧详情字段完整。

## Step 13：实现 Play 超时、事件和 Console 输出

依赖其他端：可先 mock；最终联调依赖后端 Play Events API。

### Step 13.1：指令

- [ ] meta 加载超过 `10s` 进入 timeout。
### Step 13.2：指令

- [ ] manifest 加载超过 `10s` 进入 timeout。
### Step 13.3：指令

- [ ] bundle / iframe ready 超过 `20s` 进入 timeout。
### Step 13.4：指令

- [ ] 点击重新开始时重新加载整个 Play 链路。
### Step 13.5：指令

- [ ] 上报 Play view、manifest_loaded、started、failed、timeout、exited。
### Step 13.6：指令

- [ ] DevTools Console 输出 meta JSON 摘要、manifest URL、manifest JSON、bundle base URL、iframe entry URL、load 总时长、各阶段耗时、错误日志。
### Step 13.7：指令

- [ ] 页面内不新增调试面板。
### Step 13.8：验证

- [ ] 每个阶段 loading 时显示转圈。
### Step 13.9：验证

- [ ] 模拟 meta 超时进入 timeout。
### Step 13.10：验证

- [ ] 模拟 manifest 超时进入 timeout。
### Step 13.11：验证

- [ ] 模拟 iframe ready 超时进入 timeout。
### Step 13.12：验证

- [ ] 重新开始会重新请求 meta、manifest 并重建 iframe。
### Step 13.13：验证

- [ ] Console 输出包含总耗时和阶段耗时。
### Step 13.14：验证

- [ ] 页面内没有调试面板。

## 5. 前端交付前自检

- [ ] 执行前端 lint 或 build。
- [ ] 关闭真实后端时，mock 模式能展示 Home、Create、Play 全流程状态。
- [ ] 连接真实后端时，Auth、Games、Uploads、Jobs、Play Events 字段不需要修改。
- [ ] 验证未登录点赞弹 Auth Modal。
- [ ] 验证 Play iframe sandbox 属性。
- [ ] 验证页面内没有调试面板，调试信息只输出 DevTools Console。
- [ ] 验证响应式布局下文字不溢出。
- [ ] 更新 [architecture.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/architecture.md) 和 [progress.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/progress.md)。

## 6. 最终接入条件

前端完成后，应能支持：

- 将 mock API 切换到真实 Backend API。
- 展示 Agent 任务状态和日志，但不直接依赖 Agent 内部实现。
- Integration Plan 中游客 Home 到 Play、登录点赞、Create 到 Publish、并发任务和权限隔离验收可执行。
