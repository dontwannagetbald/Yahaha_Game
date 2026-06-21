# Frontend 实施计划

> **面向 AI 开发者：** 本计划只写执行指令和验证要求，不包含代码。每一步都必须小而具体；每一步完成后必须执行验证；每个 Step x.x 验证通过后暂停，等待用户确认该 Step x.x 完成，再继续下一个 Step x.x。

**目标：** 基于当前静态预览 [yahaha-preview.html](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/yahaha-preview.html)，分阶段实现 Yahaha_Play 前端 MVP：先搭建写死界面，再接注册登录，最后接 Home、Play、Create、上传、生成任务和发布闭环。

**架构：** 第一阶段只做可交互静态 UI，不依赖后端；第二阶段接入 Auth API；后续阶段逐步把 mock 数据替换为真实 API。页面行为以 [pages-design.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/pages-design.md) 为准，视觉以 [design.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/design.md) 和当前 [yahaha-preview.html](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/yahaha-preview.html) 为准。

**技术栈：** React、Vite、TypeScript、Ant Design、CSS、浏览器 DevTools Console、sandboxed iframe。

---

## 0. 必读上下文与执行规则

### Step 0.1：读取产品与页面文档 ☑️ 已完成

- [ ] 指令：完整阅读 [design-document.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/design-document.md)、[pages-design.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/pages-design.md)、[design.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/design.md)、[api-contract.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/api-contract.md)、[architecture.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/architecture.md)、[progress.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/progress.md)。
- [ ] 验证：能用一句话说明 Home、Create、Play、Auth Modal 的职责；能列出 MVP 不做的能力；能说明页面内不新增调试面板，调试信息只输出 DevTools Console。

### Step 0.2：读取静态预览 ☑️ 已完成

- [ ] 指令：完整阅读 [yahaha-preview.html](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/yahaha-preview.html)，把它作为第一阶段 UI 的视觉参考。
- [ ] 验证：能指出预览中包含的 Home 未登录、Home 已登录、Auth Modal、Create、Play 交互；能说明当前导航、游戏卡片、筛选区、Play 左侧栏、Create 工作台的视觉要求。

### Step 0.3：确认前端当前状态 ☑️ 已完成

- [ ] 指令：检查 `frontend/` 目录当前文件、依赖、脚本和已有 React 入口。
- [ ] 验证：能启动或构建当前前端；能确认 `frontend/src/App.tsx` 和 `frontend/src/styles.css` 是当前主要界面入口；能确认不会删除用户已有改动。

## 1. 第一大步：搭建写死的前端界面

本阶段只做静态界面和页面内假交互，不接真实 API。所有数据写死在前端本地，目标是让用户先看到完整 MVP 页面形态。

### Step 1.1：建立页面壳和页面状态切换 ☑️ 已完成

- [ ] 指令：在 React 前端中建立 Home、Create、Play 三个主页面状态；先允许通过页面内导航切换，不要求真实路由完成。
- [ ] 指令：默认进入 Home 未登录状态。
- [ ] 指令：页面内不要出现“预览切换器”或开发用 tab。
- [ ] 验证：打开前端首页时只看到产品页面本身；点击顶部 `主页` 可回到 Home；点击游戏卡片可进入 Play；点击 Play 的 `返回主页` 可回到 Home。

### Step 1.2：实现固定顶部导航静态样式 ☑️ 已完成

- [ ] 指令：实现固定在顶部的导航栏，导航高度按当前预览较矮版本处理。
- [ ] 指令：Logo 在左侧，`主页` 和 `创建游戏` tab 放在头像左边，用户区域放最右侧。
- [ ] 指令：未登录显示默认头像和 `登录`；已登录静态状态显示头像、昵称和 hover 才出现的 `退出登录` 菜单。
- [ ] 验证：页面滚动时导航栏保持固定；导航高度不遮挡主体内容；hover 用户区域时才显示 `退出登录`；不 hover 时不显示 `退出登录`。

### Step 1.3：实现 Auth Modal 静态交互 ☑️ 已完成

- [ ] 指令：点击未登录导航中的 `登录` 打开 Auth Modal。
- [ ] 指令：Auth Modal 右上角使用 `取消` 按钮关闭弹窗。
- [ ] 指令：Auth Modal 登录态包含标题、邮箱、密码、登录按钮、Google 按钮、GitHub 占位按钮、注册切换文案。
- [ ] 指令：注册态包含标题、邮箱、密码、确认密码、注册按钮、返回登录入口。
- [ ] 验证：点击 `登录` 能打开弹窗；点击 `取消` 能关闭弹窗；登录态和注册态能互相切换；弹窗关闭后页面没有残留遮罩。

### Step 1.4：实现 Home 静态游戏流 ☑️ 已完成

- [ ] 指令：按照当前预览实现 Home 游戏流，至少展示 8 张静态游戏卡片。
- [ ] 指令：游戏卡片使用横向封面、圆角、封面底部统计叠层、封面左上角标签叠层。
- [ ] 指令：卡片下方展示标题、作者和发布时间。
- [ ] 指令：简介只在 hover 浮层展示，不常驻占用卡片高度。
- [ ] 验证：2560 × 1664 屏幕下游戏卡片布局不显得过高；标签在封面左上角；点赞数和游玩次数叠在封面底部；卡片下方不再显示标签和统计行。

### Step 1.5：实现 Home 筛选区静态样式 ☑️ 已完成

- [ ] 指令：筛选区顺序为 `最多游玩`、`最多点赞`、`最新发布`、搜索框、`更多筛选`。
- [ ] 指令：`更多筛选` 使用设计文档风格：深色透明背景、白字、弱白描边、胶囊圆角、右侧 down arrow。
- [ ] 指令：本阶段只做视觉和展开占位，不实现真实筛选结果。
- [ ] 验证：搜索框在 `更多筛选` 左边；`更多筛选` 在视觉上不是白底按钮；down arrow 清晰可见；点击筛选控件不会导致页面报错。

### Step 1.6：实现未登录与已登录静态状态切换 ☑️ 已完成

- [ ] 指令：在静态阶段，点击 Auth Modal 的登录按钮后模拟进入已登录 Home。
- [ ] 指令：点击 `退出登录` 后回到未登录 Home。
- [ ] 指令：未登录点击 `创建游戏` 只打开 Auth Modal，不进入 Create。
- [ ] 指令：已登录点击 `创建游戏` 进入 Create。
- [ ] 验证：未登录无法直接通过导航进入 Create；模拟登录后顶部显示昵称；退出登录后顶部恢复 `登录`；退出后再次点击 `创建游戏` 仍弹 Auth Modal。

### Step 1.7：实现 Create 静态工作台 ☑️ 已完成

- [ ] 指令：Create 使用左侧任务列表、聊天与上传区、生成游戏显示面板布局。
- [ ] 指令：左侧包含任务列表、任务状态、`+ 新建任务`、聊天输入框、附件入口、发送入口。
- [ ] 指令：中部或右侧包含 Agent 欢迎消息、用户消息、游戏卡片、生成游戏面板、进度条、Agent 步骤列表、Publish 和 Retry。
- [ ] 指令：本阶段不做真实上传、不做真实任务创建、不做真实发布。
- [ ] 验证：登录状态下能进入 Create；Create 页面不出现结构化游戏参数表单；任务状态 badge 可显示 `pending / running / succeeded / failed` 中至少两种；Publish 和 Retry 是可见但不调用 API 的静态按钮。

### Step 1.8：实现 Play 静态页面 ☑️ 已完成

- [ ] 指令：Play 左侧显示返回主页、游戏标题、作者、发布时间、游玩次数、点赞数、标签和简介。
- [ ] 指令：Play 主区域显示静态游戏运行区，不显示调试说明条。
- [ ] 指令：去掉 `可以在这里点赞` 之类的说明性标题。
- [ ] 指令：本阶段不加载真实 manifest，不创建 iframe。
- [ ] 验证：从 Home 点击卡片进入 Play；Play 左侧没有 `可以在这里点赞`；Play 页面底部没有调试说明条；点击返回主页回到 Home。

### Step 1.9：实现基础响应式与大屏适配 ☑️ 已完成

- [ ] 指令：按 2560 × 1664 优先优化桌面布局，同时保留普通桌面和移动端可用性。
- [ ] 指令：导航固定，主体内容不被导航遮挡。
- [ ] 指令：Home 大屏卡片不超过合理高度，Create 和 Play 主体尽量横向利用宽屏。
- [ ] 验证：在 2560 × 1664 下首屏没有异常大空白；在普通桌面宽度下卡片不会过窄；在移动宽度下文字不溢出按钮或卡片。

### Step 1.10：第一大步交付验证 ☑️ 已完成

- [ ] 指令：运行前端构建或类型检查。
- [ ] 指令：手动走通 Home 未登录、Auth Modal、模拟登录、Home 已登录、Create、Play、退出登录。
- [ ] 验证：构建或类型检查通过；浏览器控制台无渲染错误；所有静态页面均可通过页面内交互到达；页面内没有调试面板。

## 2. 第二大步：实现注册登录功能

本阶段只接 Auth，不接游戏列表、任务、发布等业务 API。

### Step 2.1：建立 Auth API 客户端 ☑️ 已完成

- [ ] 指令：建立统一请求入口，处理 API base URL、cookie、JSON 错误格式和网络异常。
- [ ] 指令：Auth 请求必须携带 cookie。
- [ ] 指令：不要在 Console 中输出 password、session id、OAuth code、token 或 secret。
- [ ] 验证：调用 `GET /api/auth/me` 能区分已登录和未登录；网络失败时显示明确错误；Console 中没有敏感字段。

### Step 2.2：接入当前用户检查 ☑️ 已完成

- [ ] 指令：应用启动时请求当前用户。
- [ ] 指令：未登录时保持 Home 游客状态，不弹错误框。
- [ ] 指令：已登录时展示头像和昵称。
- [ ] 验证：无 session 打开页面不会弹错误；有 session 打开页面能恢复已登录导航；刷新页面后登录态仍正确。

### Step 2.3：接入邮箱注册 ☑️ 已完成

- [ ] 指令：注册态提交邮箱、密码和确认密码。
- [ ] 指令：前端校验邮箱格式、密码最小长度、两次密码一致。
- [ ] 指令：注册成功后关闭弹窗、刷新当前用户、显示成功提示。
- [ ] 验证：新邮箱注册成功后导航变为已登录；重复邮箱显示明确错误；密码不一致不发送注册请求；注册失败错误保留在弹窗内或错误提示中。

### Step 2.4：接入邮箱登录 ☑️ 已完成

- [ ] 指令：登录态提交邮箱和密码。
- [ ] 指令：登录成功后关闭弹窗、刷新当前用户、显示成功提示。
- [ ] 指令：登录失败时不关闭弹窗。
- [ ] 验证：正确账号密码登录成功；错误密码显示明确错误；登录成功后未登录受保护入口可以进入 Create；登录失败后页面仍停留在 Auth Modal。

### Step 2.5：接入退出登录 ☑️ 已完成

- [ ] 指令：点击 hover 菜单中的 `退出登录` 调用退出 API。
- [ ] 指令：退出成功后清除前端用户状态并回到未登录 Home。
- [ ] 指令：退出失败时显示错误，不提前清除用户状态。
- [ ] 验证：退出成功后导航恢复默认头像和 `登录`；退出后点击 `创建游戏` 弹 Auth Modal；退出失败时用户态不被错误清空。

### Step 2.6：接入 Google OAuth 入口 ☑️ 已完成

- [ ] 指令：点击 Google 按钮调用 Google OAuth start 接口。
- [ ] 指令：拿到授权地址后跳转到 Google 授权页。
- [ ] 指令：OAuth 回到前端后刷新当前用户。
- [ ] 验证：点击 Google 登录能进入授权流程；授权成功后回到应用并显示 OAuth 昵称和头像；OAuth 失败时显示明确错误；Console 只输出 provider、user_id、nickname、session 检查摘要，不输出敏感信息。

### Step 2.7：保留 GitHub 占位 ☑️ 已完成

- [ ] 指令：GitHub 按钮展示为 disabled 或明确未启用状态。
- [ ] 指令：不要触发真实 GitHub OAuth。
- [ ] 验证：用户不会误以为 GitHub 已可用；点击或悬停时能看到未启用反馈；GitHub 占位不影响邮箱登录和 Google 登录。

### Step 2.8：第二大步交付验证 ☑️ 已完成

- [ ] 指令：完整验证注册、登录、当前用户恢复、退出登录、Google OAuth 入口、GitHub 占位。
- [ ] 指令：运行前端构建或类型检查。
- [ ] 验证：Auth 全链路通过；未登录 Home 和 Play 仍可访问；未登录 Create 仍弹 Auth Modal；构建或类型检查通过。

## 3. 第三大步：实现 API mock 层与错误反馈

### Step 3.1：建立 mock 开关 ☑️ 已完成

- [ ] 指令：增加前端 mock 开关，用于在后端未完成时跑通 Home、Create、Play 的开发数据。
- [ ] 指令：mock 字段必须与 [api-contract.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/api-contract.md) 一致。
- [ ] 验证：关闭后端时 mock 模式仍能展示 Home、Create、Play；切换到真实 API 模式时请求路径和字段名不需要修改。

### Step 3.2：统一错误弹窗 ☑️ 已完成

- [ ] 指令：为登录失败、注册失败、文件上传失败、任务失败、发布失败、Play 加载失败建立统一错误展示方式。
- [ ] 指令：错误内容包含标题、失败原因和下一步重试建议。
- [ ] 验证：模拟每类错误都能看到用户可理解的错误；错误弹窗不会展示 secret、token、password、OAuth code 或完整 presigned URL。

### Step 3.3：统一 DevTools Console 输出 ☑️ 已完成

- [ ] 指令：建立结构化 Console 输出约定，输出请求摘要、状态、耗时、业务 ID 和错误摘要。
- [ ] 指令：页面内不新增调试面板。
- [ ] 验证：Home、Auth、Create、Play 的关键动作都能在 DevTools Console 看到结构化摘要；页面里看不到 Printer 或调试面板。

## 4. 第四大步：接入 Home 游戏流

### Step 4.1：接入 published 游戏列表 ☑️ 已完成

- [ ] 指令：Home 从 `GET /api/games` 或 mock 获取 published 游戏列表。
- [ ] 指令：只展示 published 游戏。
- [ ] 验证：页面加载时会请求游戏列表；draft 游戏不会出现在 Home；至少能展示 3 个游戏。

### Step 4.2：接入 Home 卡片真实字段 ☑️ 已完成

- [ ] 指令：卡片展示封面、标题、作者、发布时间、标签、简介、点赞数和游玩次数。
- [ ] 指令：标签叠在封面左上角；点赞数和游玩次数叠在封面底部；简介只在 hover 显示。
- [ ] 验证：接口返回字段能完整映射到卡片；缺少封面时有合理兜底；hover 时出现简介；标签点击不会进入 Play。

### Step 4.3：接入排序 ☑️ 已完成

- [ ] 指令：支持 `最多游玩`、`最多点赞`、`最新发布` 三种排序。
- [ ] 指令：切换排序时更新请求参数或 mock 查询条件。
- [ ] 验证：三种排序切换后列表顺序正确；当前选中排序有明确视觉状态；Console 输出当前排序和返回条数。

### Step 4.4：接入搜索与更多筛选 ☑️ 已完成

- [ ] 指令：搜索框支持按关键词筛选游戏。
- [ ] 指令：`更多筛选` 展开标签筛选下拉区域。
- [ ] 指令：标签筛选只改变列表结果，不作为 Play 入口。
- [ ] 验证：输入关键词后列表变化；选择标签后列表变化；清空筛选后恢复列表；搜索框和更多筛选在视觉顺序上保持为搜索框在左、更多筛选在右。

### Step 4.5：接入点赞 ☑️ 已完成

- [ ] 指令：点赞图标和卡片主体点击区域分离。
- [ ] 指令：未登录点击点赞弹 Auth Modal，不调用点赞 API。
- [ ] 指令：登录用户点击点赞调用点赞 API，成功后更新点赞数。
- [ ] 验证：未登录点赞只弹 Auth Modal 且不进入 Play；登录点赞后点赞数更新；重复点击不会重复增加；Console 输出点赞结果或未登录原因。

## 5. 第五大步：接入 Play 页面

### Step 5.1：根据游戏 ID 加载 meta ☑️ 已完成

- [ ] 指令：点击 Home 卡片进入 Play，并携带对应 game id。
- [ ] 指令：Play 根据 game id 请求游戏 meta。
- [ ] 验证：有效 game id 展示对应游戏详情；无效 game id 显示错误；刷新 Play URL 后仍能加载同一个游戏。

### Step 5.2：加载 manifest ☑️ 已完成

- [ ] 指令：从 game meta 读取 manifest URL 并加载 manifest。
- [ ] 指令：manifest 加载失败时显示错误态和重试入口。
- [ ] 验证：manifest 成功时 Console 输出 manifest URL 和 JSON 摘要；manifest 404 或网络失败时进入错误态；错误态不会白屏。

### Step 5.3：创建 sandboxed iframe ☑️ 已完成

- [ ] 指令：根据 manifest entry 构建 iframe URL。
- [ ] 指令：iframe 使用 sandbox 限制，只允许脚本运行，不允许访问父页面 DOM。
- [ ] 验证：iframe src 是远端对象存储或 S3-compatible URL；sandbox 属性符合安全要求；页面不使用本地 React 组件伪装游戏。

### Step 5.4：处理 Play loading、timeout 和重试 ☑️ 已完成

- [ ] 指令：meta、manifest、iframe ready 分阶段显示 loading。
- [ ] 指令：任一阶段超时进入 timeout 状态。
- [ ] 指令：点击重试时重新执行完整加载链路。
- [ ] 验证：模拟 meta 超时、manifest 超时、iframe 超时都能进入 timeout；重试后重新请求；Console 输出总耗时和阶段耗时。

### Step 5.5：上报 Play 事件 ☑️ 已完成

- [ ] 指令：上报 view、manifest_loaded、started、failed、timeout、exited。
- [ ] 指令：游客事件允许 user_id 为空。
- [ ] 验证：进入 Play 时上报 view；manifest 成功时上报 manifest_loaded；失败和超时时上报对应事件；Console 输出事件摘要。

## 6. 第六大步：接入 Create 工作台

### Step 6.1：接入任务历史

- [ ] 指令：Create 登录后请求当前用户任务历史。
- [ ] 指令：左侧任务列表显示任务名、状态、创建时间和结果摘要。
- [ ] 指令：任务历史必须读取并保存每个任务的 `session_id`，用于点击历史任务时恢复对应对话。
- [ ] 指令：只展示当前用户任务。
- [ ] 验证：未登录访问 Create 弹 Auth Modal；登录后能看到任务历史；刷新 Create 后任务历史仍存在；任务项包含 `job_id` 与 `session_id`；多个任务状态互不影响。

### Step 6.2：拆分 Create 页任务状态与会话状态 ☑️ 已完成

- [ ] 指令：Create 页必须至少维护 `selectedTaskId`、`selectedCreateSessionId`、`currentJobStatus` 和 `isConversationLocked` 四类状态。
- [ ] 指令：不要把 task id 和 create session id 混成一个当前 ID。
- [ ] 指令：`+ 新建任务` 创建新的空 `create_session`，聊天区清空并可编辑，右侧生成面板回到 idle。
- [ ] 指令：点击历史任务时，从任务的 `session_id` 调用 `GET /api/create-sessions/{session_id}`，恢复该任务当时的对话上下文。
- [ ] 指令：点击历史任务时禁止调用 `POST /api/create-sessions`；该接口只用于新建空白对话。
- [ ] 指令：Create 页确认前状态必须来自 `Create Sessions API`，不再用本地临时对象替代 `user_requirements`、`game_plan`、`material_usage`、`assistant_response`。
- [ ] 指令：聊天气泡必须优先来自 `create_session.messages`；`assistant_response` 只能作为最近一轮状态和当前动作来源。
- [ ] 指令：刷新页面后，任务列表从 `GET /api/jobs` 恢复；如果当前选中任务有 `session_id`，聊天区恢复该 session；如果没有任务或用户点击新建任务，再创建空会话。
- [ ] 指令：如果恢复失败或会话不可读，允许用户重新创建新会话，并显示明确错误。
- [ ] 验证：首次进入 Create 可创建空会话；点击历史任务能按 `session_id` 恢复对应对话且不会创建新 session；刷新后任务列表和选中任务上下文一致；存在 `messages` 时聊天气泡完整恢复；Console 输出 `job_id`、`session_id`、恢复命中状态和请求摘要，不输出敏感字段。

### Step 6.3：接入聊天输入与 AI 建议答案 ☑️ 已完成

- [ ] 指令：用户通过聊天输入描述游戏创意或补充要求，发送时调用 `POST /api/create-sessions/{session_id}/events` 的 `chat` 事件。
- [ ] 指令：只有 `isConversationLocked=false` 且当前处于第一阶段 `collecting / ready_to_confirm` 时，才允许发送第一阶段 `chat` 事件。
- [ ] 指令：不新增玩法、风格、角色、胜负条件等结构化表单。
- [ ] 指令：空输入不能提交；发送中需要禁用重复提交。
- [ ] 指令：AI 每轮回复后展示 `assistant_response.message`，并将 `assistant_response.suggestions` 作为可点击的竖向短按钮展示在回复下方。
- [ ] 指令：事件成功后用响应中的 `messages` 更新聊天气泡；如果后端暂未提供 `messages`，只能临时追加本轮用户消息和 `assistant_response.message`，并在后续恢复时以服务端 `messages` 为准。
- [ ] 指令：用户点击发送或按 Enter 后，聊天区先立刻追加用户气泡；如果请求超过 `2s` 仍未返回，再追加一条 AI `思考中...` 占位气泡；接口成功后再用服务端 `messages` 替换，占位不落库。
- [ ] 指令：当用户气泡或延迟出现的 AI `思考中...` 占位追加到消息流后，聊天区需要自动滚到底部，不能让占位气泡落到可视区外。
- [ ] 指令：点击建议按钮后，只将该建议回填到输入框，不自动发送；用户需要再点击发送按钮才提交 `chat` 事件。
- [ ] 指令：只有当返回的 `conversation_status` 为 `ready_to_confirm` 时，才显示可生成的游戏卡片和后续动作按钮。
- [ ] 验证：输入有效创意会触发 `chat` 事件；发送后立即看到用户气泡；若请求超过 `2s` 才出现 AI `思考中...` 占位；锁定状态下不能发送第一阶段 `chat`；空输入显示错误；建议答案以竖向按钮展示；点击建议只回填输入框且不触发请求；页面没有结构化表单字段；Console 输出事件类型、响应状态和 suggestions 数量摘要。

### Step 6.4：接入文件上传与素材绑定事件 ☑️ 已完成

- [ ] 指令：附件入口支持选择任意文件。
- [ ] 指令：上传前请求 presigned URL，上传完成后登记文件信息。
- [ ] 指令：上传完成后必须继续向当前 `create_session` 发送 `upload_assets` 事件，把素材绑定到会话并更新 `material_usage.assets`。
- [ ] 指令：单文件超过 20MB 时阻止上传并显示错误。
- [ ] 指令：聊天框下方展示当前会话已选择或已绑定的素材列表，并允许删除尚未提交的本地选择。
- [ ] 指令：`upload_assets` system 消息只作为历史事件保留，不渲染为 AI 聊天气泡；用户只在附件列表看到已绑定素材。
- [ ] 验证：小文件上传成功后显示在聊天框下方，并触发 `upload_assets`；聊天流不出现“上传素材”AI 气泡；大文件显示错误；上传失败时可重试；刷新页面后已绑定素材仍可恢复；Console 输出文件名、大小、MIME type、object key 摘要和素材绑定结果。

### Step 6.5：接入游戏卡片、换一换与确认动作

- [ ] 指令：当会话进入 `ready_to_confirm` 时，展示由 `assistant_response.card` 派生的游戏卡片。
- [ ] 指令：游戏卡片只展示 `plan_id`、标题、介绍和标签，不展示完整 `game_plan` 字段，不支持卡片内联编辑。
- [ ] 指令：用户想修改方案时，只能继续发送聊天消息，由 AI 更新 `game_plan` 和派生卡片。
- [ ] 指令：`换一换` 只在 `ready_to_confirm` 状态显示，点击后发送 `regenerate` 事件，并带上当前 `selected_plan_id`。
- [ ] 指令：`生成` 只在 `ready_to_confirm` 状态可用，点击后发送 `confirm` 事件；`confirm` 成功前不调用 Jobs API。
- [ ] 指令：`regenerate` 成功后要替换为新的卡片和 `plan_id`，同时保留已有聊天上下文与素材列表。
- [ ] 验证：`ready_to_confirm` 时卡片常驻显示；`换一换` 只在可确认阶段出现；点击 `换一换` 后卡片内容或 `plan_id` 变化；点击 `生成` 前不会创建任务；`confirm` 成功后拿到 `handoff_to_generation=true`；Console 输出 `selected_plan_id`、事件类型和会话状态变化摘要。

### Step 6.6：基于 confirmed session 创建生成任务 ☑️ 已完成

- [x] 指令：只有当前 `create_session` 成功 `confirm` 后，前端才调用 `POST /api/jobs`。
- [x] 指令：创建任务请求只提交 `session_id` 和可选 `prompt`，不重复提交 `user_requirements`、`game_plan`、`material_usage` 或确认卡片内容。
- [x] 指令：创建成功后新任务进入左侧列表，初始状态为 `pending`，并切换右侧生成面板关注该任务。
- [x] 指令：创建成功后写入 `selectedTaskId=job_id`、`selectedCreateSessionId=session_id`、`currentJobStatus=pending`，并设置 `isConversationLocked=true`。
- [x] 指令：如果创建任务失败，保留当前 confirmed 会话和游戏卡片，允许用户重试创建任务。
- [x] 验证：有效请求返回 `job_id` 和 `session_id`；新任务出现在任务列表；聊天区变为只读；创建失败显示错误；创建任务请求摘要中只有 `session_id` 和可选 `prompt`；Console 输出 `job_id`、`session_id` 和请求结果摘要。

### Step 6.7：轮询任务状态与日志

- [ ] 指令：定时刷新当前任务状态和 Agent 日志。
- [ ] 指令：生成面板显示 `pending`、`running`、`succeeded`、`failed`、`timeout` 状态。
- [ ] 指令：`failed` 时显示失败步骤和原因。
- [ ] 指令：当用户从任务列表切换任务时，右侧面板和日志区域同步切换到当前选中任务。
- [ ] 指令：`pending / running` 时 `isConversationLocked=true`，禁用输入、建议答案、上传、生成、换一换和重新生成。
- [ ] 指令：`succeeded / failed` 时允许进入生成后修改入口，但不能继续调用第一阶段 `chat / regenerate / confirm` 来改已生成游戏。
- [ ] 验证：`pending` 能更新到 `running`；`running` 显示当前步骤且聊天区锁定；`succeeded` 显示完整日志摘要并展示生成后修改入口；`failed` 显示失败原因并可进入修改或 retry 入口；日志顺序与接口一致；切换任务时右侧显示和聊天上下文同步更新。

### Step 6.8：接入生成后修改入口

- [ ] 指令：当当前任务为 `succeeded / failed`，用户在聊天框输入明确修改时，进入 revision mode。
- [ ] 指令：revision mode 使用当前任务的 `job_id`、关联 `session_id`、已有 `game_plan` 和用户新消息创建新的 revision job；不调用第一阶段 `POST /api/create-sessions/{session_id}/events` 的 `chat`。
- [ ] 指令：MVP 可先调用后续契约 `POST /api/jobs/{job_id}/revisions` 或使用 mock 占位，但 UI 状态必须表现为创建新任务、重新生成一版 draft。
- [ ] 指令：新 revision job 创建成功后，左侧新增任务项，`parent_job_id` 指向上一版任务，并切换生成面板到新任务。
- [ ] 指令：旧任务、旧 draft、旧 session 对话上下文必须保留，可点击回看。
- [ ] 验证：succeeded/failed 任务下输入明确修改不会触发第一阶段 `chat`；会创建或 mock 创建新 revision job；任务列表出现新版本任务；旧任务仍可点击回看；Console 输出 `parent_job_id`、新 `job_id`、`session_id` 和 revision intent 摘要。

## 7. 第七大步：接入 Create 试玩与发布

### Step 7.1：显示 succeeded 任务试玩

- [ ] 指令：任务 succeeded 后在生成游戏面板中直接显示试玩区域。
- [ ] 指令：试玩即 Preview，不新增独立 Preview 按钮。
- [ ] 指令：试玩使用与 Play 相同的 manifest 加载和 sandboxed iframe 机制。
- [ ] 验证：succeeded 任务显示 iframe；iframe src 来自 draft manifest 或授权 URL；sandbox 属性符合 Play 的安全要求。

### Step 7.2：接入 Publish

- [ ] 指令：Publish 按钮放在游戏旁边。
- [ ] 指令：点击 Publish 后按钮进入 loading 状态。
- [ ] 指令：发布成功后跳转 Home。
- [ ] 验证：Publish 请求只允许 owner 执行；发布中 loading 可见；发布失败显示可重试错误；发布成功后自动回到 Home。

### Step 7.3：验证发布后进入 Home

- [ ] 指令：发布成功后刷新 Home 游戏列表。
- [ ] 指令：Home 新增刚发布游戏。
- [ ] 验证：刚发布游戏出现在 Home；点击该游戏能进入 Play；Play 加载的是 published manifest URL。

## 8. 第八大步：最终联调与交付自检

### Step 8.1：前端构建与基础质量检查

- [ ] 指令：运行前端构建、类型检查或 lint。
- [ ] 验证：命令通过；没有 TypeScript 错误；没有明显 lint error；浏览器控制台无运行时渲染错误。

### Step 8.2：游客链路验收

- [ ] 指令：以未登录状态访问 Home，搜索、筛选、排序、进入 Play。
- [ ] 验证：游客可浏览 Home；游客可进入 Play；游客点击点赞弹 Auth Modal；游客点击 Create 弹 Auth Modal。

### Step 8.3：登录链路验收

- [ ] 指令：完成注册、登录、刷新恢复用户、退出登录。
- [ ] 验证：注册成功创建用户态；登录成功显示用户信息；刷新后用户态保留；退出后恢复游客态。

### Step 8.4：Create 到 Publish 闭环验收

- [ ] 指令：登录用户创建空 `create_session`、发送聊天消息、点击建议答案、上传文件并绑定素材、在 `ready_to_confirm` 状态下点击 `换一换` 或 `生成`、基于 confirmed `session_id` 创建任务、等待 succeeded、试玩、可选进入 revision mode、Publish。
- [ ] 验证：Create Session 与任务链路完整打通；建议答案可点击；游戏卡片只展示标题、介绍、标签；任务状态完整变化；任务可通过 `session_id` 恢复历史对话；Agent 日志可见；试玩 iframe 可运行；生成后修改不会混入第一阶段对话 loop；发布成功后 Home 出现新游戏。

### Step 8.5：Play 远端加载验收

- [ ] 指令：从 Home 进入刚发布游戏的 Play 页面。
- [ ] 验证：Play meta、manifest、iframe entry 都来自后端或对象存储 URL；iframe sandbox 属性正确；失败和超时状态可重试。

### Step 8.6：文档更新

- [ ] 指令：每完成一个被用户确认的 Step x.x 后，按项目规则更新 [architecture.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/architecture.md) 和 [progress.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/progress.md)。
- [ ] 验证：`architecture.md` 只记录 layer、目录边界和文件职责；`progress.md` 记录已实现功能、完成度、待补齐边界和验证结果；对应 Step x.x 标注为已完成。

## 9. 禁止范围

- [ ] 不做独立 Game Detail 页面。
- [ ] 不做 My Games / Profile。
- [ ] 不做 Admin Console。
- [ ] 不做收藏。
- [ ] 不做发布后编辑标题、简介、标签、封面。
- [ ] 不做取消发布。
- [ ] 不做完整版本管理 UI。
- [ ] 不做 Remix。
- [ ] 不做 GitHub OAuth 真实跑通。
- [ ] 不在页面内新增 Printer 或调试面板。
