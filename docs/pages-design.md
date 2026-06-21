# Yahaha Play 页面设计文档

## 1. 文档目标

本文档定义 MVP 的页面数量、页面功能组件、交互规则、状态展示和布局方式。页面设计基于 [prd.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/prd.md)、[design-document.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/design-document.md) 以及当前线框讨论结果。

页面使用的 API 字段、错误格式和跨端 mock 约定以 [api-contract.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/api-contract.md) 为准。

MVP 页面范围：

| 页面 / 组件 | 类型 | MVP 是否实现 |
| --- | --- | --- |
| Home | 路由页面 | 是 |
| Create | 路由页面 | 是 |
| Play | 路由页面 | 是 |
| Auth Modal | 全局弹窗 | 是 |
| Game Detail 独立页 | 路由页面 | 否，后续版本 |
| My Games / Profile | 路由页面 | 否，后续版本 |
| Admin Console | 路由页面 | 否，后续版本 |

## 2. 全局布局与导航

### 2.1 顶部导航

所有页面共享顶部导航。

导航组件：

- 产品名：`Yahaha_Play`。
- 主导航：`主页`、`创建游戏`。
- 登录区域：
  - 未登录：默认头像 + `登录`。
  - 已登录：OAuth 或本地账号头像 + 昵称。
  - 已登录展开菜单：`退出登录`。

交互规则：

- 点击 `主页` 进入 Home。
- 点击 `创建游戏` 时：
  - 已登录：进入 Create。
  - 未登录：弹出 Auth Modal，不跳转。
- 退出登录成功后：
  - 清除 session。
  - 头像切换为默认头像。
  - 昵称区域恢复为 `登录`。
  - 如果用户之后再次点击 `创建游戏`，按未登录逻辑弹 Auth Modal。

### 2.2 全局错误反馈

所有失败状态都需要统一显示 Error 弹窗或明确错误提示。

必须覆盖：

- 登录失败。
- 注册失败。
- Google OAuth 回调失败。
- 文件上传失败。
- 生成任务创建失败。
- Agent 生成失败。
- 产物上传失败。
- Publish 失败。
- Play meta 加载失败。
- manifest 加载失败。
- iframe 初始化失败。
- 请求超时。

错误弹窗内容：

- 错误标题。
- 失败原因。
- 用户下一步应该怎么重试。
- 可选技术信息输出到调试 Console。

## 3. Auth Modal

Auth 不做独立页面，只作为全局弹窗出现。

### 3.1 触发入口

- 点击顶部导航 `登录`。
- 未登录时点击 `创建游戏`。
- 未登录时触发任何受保护动作。

### 3.2 登录态

登录表单组件：

- 标题：`登录`。
- 邮箱输入框。
- 密码输入框。
- 登录按钮。
- Google 登录按钮。
- GitHub 入口：后续版本，占位或 disabled。
- 文案：`尚无账号？注册`，其中 `注册` 是切换入口。

登录成功：

- 关闭 Auth Modal。
- 顶部头像和昵称更新。
- 昵称优先使用 OAuth 返回昵称；本地邮箱账号可使用邮箱前缀。
- 显示成功弹窗或成功提示。
- 调试 Console 打印 session 检查结果，例如 `GET /api/auth/me` 返回的用户摘要。

登录失败：

- 弹 Error 弹窗或表单内错误提示。
- 提示用户检查邮箱、密码或重试。
- 调试 Console 打印错误 code、message、请求时间。

### 3.3 注册态

注册通过登录弹窗中的 `注册` 入口切换，不单独做页面。

注册表单组件：

- 标题：`注册`。
- 邮箱输入框。
- 密码输入框。
- 确认密码输入框。
- 注册按钮。
- 返回登录入口。

注册成功：

- 创建 session。
- 关闭 Auth Modal。
- 顶部头像和昵称更新。
- 显示成功提示。

注册失败：

- 邮箱已注册、密码不符合要求、网络异常等都显示明确错误。
- 调试 Console 打印错误摘要。

### 3.4 Google OAuth

Google OAuth 需要真实跑通。

交互规则：

- 点击 Google 登录后跳转 Google 授权页。
- 授权回调成功后回到应用。
- 回到应用后显示登录成功提示。
- 顶部显示 OAuth 账号头像和昵称。
- 账号绑定结果不做独立页面展示，表现与普通登录一致。
- 调试 Console 打印 OAuth 登录结果摘要，包括 provider、user_id、nickname、是否拿到 session，不打印 secret。

GitHub OAuth 放后续版本，本 MVP 只保留后续实现入口或说明。

## 4. Home 页面

Home 是公开游戏流页面，未登录也可以访问。

### 4.1 页面功能

必须实现：

- 展示所有 `published` 游戏。
- 游戏卡片数据来自后端或数据库。
- 至少展示 3 个示例游戏。
- 至少 1 个游戏来自 Create 流程生成并发布。
- 点击游戏卡片进入 Play。
- 支持排序：
  - 最多游玩。
  - 最多点赞。
  - 最新发布。
- 支持搜索框。
- 支持标签筛选。

后续版本：

- 收藏。
- 独立 Game Detail 页面。
- 用户作品管理页。

### 4.2 游戏卡片

卡片展示：

- 封面。
- 游戏标题。
- 作者。
- 发布时间。
- 标签，例如 `冒险`。
- 点赞图标和点赞数。
- 游玩次数图标和游玩次数。

简介展示规则：

- 简介只在 hover 时展示。
- hover 浮层显示游戏简介，不要求常驻展示。

点击规则：

- 点击卡片任意主体区域进入 Play。
- 标签 `冒险` 不是 Play 入口，只作为标签展示。
- 登录用户点击点赞图标后触发点赞动作。
- 未登录用户点击点赞图标时弹出 Auth Modal，不执行点赞请求。
- 点赞动作与进入 Play 的点击区域需要避免冲突。

### 4.3 排版

桌面端：

- 顶部为全局导航。
- 导航下方为筛选与搜索区。
- 筛选区从左到右排列：最多游玩、最多点赞、最新发布、标签筛选、搜索框。
- 游戏列表使用网格布局。
- 卡片以封面为主体，下方展示标题、作者、发布时间、标签和统计信息。

移动端：

- 导航压缩为产品名 + 登录区域 + 简化菜单。
- 排序和筛选可换行或使用横向滚动。
- 卡片改为单列或双列。

### 4.4 Home Console 输出

Home 页面不显示调试面板；开发/验收时通过浏览器 DevTools Console 查看输出。

Console 输出：

- 当前排序。
- 当前筛选标签。
- 当前搜索关键词。
- 游戏列表 API 返回条数。
- 用户刚发布的游戏是否出现在 Home。
- 登录用户点赞接口返回结果。
- 未登录用户点击点赞时输出 Auth Modal 触发原因。

## 5. Create 页面

Create 是创作者工作台。页面以自然语言对话为主，不做结构化表单输入。

### 5.1 页面功能

必须实现：

- 需要登录。
- 未登录点击 `创建游戏` 时弹 Auth Modal。
- 用户可以输入自然语言创意。
- 用户可以点击附件 icon 上传任意文件。
- 上传成功后的文件列表显示在用户聊天框下方。
- 支持并发创建多个生成任务。
- 用户离开页面后回来仍能看到任务历史。
- 任务列表显示任务名、状态、创建时间、结果。
- 任务状态包括 `pending / running / succeeded / failed`。
- 任务列表中的每个任务必须带有关联 `session_id`，用于恢复该任务对应的对话上下文。
- Agent 执行步骤和当前关键步骤显示在生成游戏的 Agent 记录区域。
- 生成成功后直接显示可试玩游戏，试玩即 Preview。
- 生成成功后游戏默认为 draft。
- Publish 按钮放在游戏旁边。
- 点击 Publish 后显示上传中状态。
- 发布成功后跳转 Home。
- 跳转 Home 后，Home 新增用户刚发布的游戏。

不做结构化输入表单：

- 不单独提供玩法、风格、角色、胜负条件等固定字段。
- 这些结构化信息通过 AI 追问和 `create_session` 内的 `user_requirements`、`game_plan`、`material_usage` 沉淀。
- 前端展示的游戏卡片只显示 `plan_id`、标题、介绍和标签；它由 `game_plan` 派生，不作为独立业务状态保存。
- 用户不直接编辑卡片字段；如果想修改玩法、风格、角色、胜负条件或素材用途，继续通过聊天让 AI 更新方案。
- Create 页状态必须拆分为 `selectedTaskId`、`selectedCreateSessionId`、`currentJobStatus` 和 `isConversationLocked`，不能把任务 ID 和会话 ID 混成一个当前 ID。
- 生成后继续聊天修改游戏时，进入 revision loop，不再复用第一阶段 Design Agent 的需求收集 loop。

后续版本：

- 发布后编辑标题、简介、标签、封面。
- 用户发布游戏管理页。
- 取消发布。
- 生成中 Cancel。
- 完整版本管理 UI。
- Remix 派生。
- 安全沙箱可视化配置。
- 内容审核面板。
- 资源限额展示。
- 生成成本统计。

### 5.2 左侧任务列表

组件：

- 标题：`任务列表`。
- 任务项：任务名 + 状态。
- `+ 新建任务`。
- 折叠/展开控制。

任务项显示：

- 任务名。
- 状态 badge：`pending / running / succeeded / failed`。
- 创建时间。
- 结果摘要：
  - succeeded：显示 draft game id 或标题。
  - failed：显示失败原因摘要。

交互：

- 点击任务后，通过任务返回的 `session_id` 读取对应 `create_session`，切换聊天区到该任务当时的对话上下文，同时切换生成游戏面板到该任务。
- 点击历史任务时不能调用 `POST /api/create-sessions`；必须调用 `GET /api/create-sessions/{session_id}` 读取旧会话。
- 点击 `+ 新建任务` 才调用 `POST /api/create-sessions` 创建新的空白聊天和生成游戏面板。
- 多个任务可以并发存在。
- `pending / running` 任务的聊天区只读，输入、建议答案、上传、生成、换一换和重新生成入口均禁用。
- `succeeded / failed` 任务允许进入生成后修改，但修改会创建新的 revision job，不覆盖原任务。

### 5.3 聊天与上传区

组件：

- Agent 欢迎消息。
- AI 追问消息。
- 用户消息。
- 建议答案按钮列表。
- 游戏卡片。
- 输入框。
- 附件 icon。
- 发送 icon。
- 文件列表。

消息恢复规则：

- 聊天区气泡来自 `create_session.messages`，按时间正序渲染。
- `assistant_response` 只代表最近一轮 AI 回复和当前动作，不作为完整聊天历史。
- 如果后端暂未返回 `messages`，前端只能恢复当前方案状态，不能声称已恢复完整聊天气泡。

文件上传规则：

- 点击附件 icon 选择文件。
- 上传完成后，前端除了登记文件信息，还需要向当前 `create_session` 发送 `upload_assets` 事件，把素材绑定到会话。
- 已绑定素材在刷新后仍应能从当前会话恢复。
- 支持任意文件。
- 上传中显示进度。
- 上传成功后，文件列表显示在用户聊天框下方。
- 上传失败时弹 Error 弹窗，提示重新上传。
- 调试 Console 打印上传文件名、大小、mime type、object key 或 presigned URL 摘要。

自然语言输入规则：

- 用户可以直接描述想做的游戏。
- AI 可以追问缺失信息。
- AI 最后输出确认卡片，供用户确认后开始生成。
- 用户不能直接在确认卡片里编辑标题、简介、玩法、胜负条件、操作方式、素材用途、标签或封面建议；这些修改都通过继续聊天更新 `game_plan`。
- 不强制用户填写结构化表单。

### 5.4 生成游戏显示面板

面板状态：

| 状态 | 页面表现 |
| --- | --- |
| idle | 显示引导文案，让用户从左侧聊天开始描述游戏。 |
| pending | 显示任务已创建，等待执行。 |
| running | 显示进度条和 Agent 当前步骤。 |
| succeeded | 显示可试玩游戏、Publish 按钮和产物信息。 |
| failed | 显示失败原因、Error 弹窗和重试入口。 |
| timeout | 显示超时提示、Error 弹窗和重试入口。 |

Agent 记录区域：

- 显示关键步骤。
- 显示每步状态。
- 显示可读日志摘要。
- 失败时显示失败步骤和原因。

生成成功后：

- 游戏直接显示在生成游戏面板中。
- 用户可以在该面板试玩，这就是 Preview。
- Publish 按钮放在游戏旁边。
- 用户仍可继续在聊天框里提出明确修改，但系统进入 revision mode，基于已有 `game_plan`、已生成 draft 和新消息创建新的 revision job。
- revision job 重新生成一版 draft，不覆盖旧产物；历史任务仍可点击回看。

发布流程：

1. 用户点击 Publish。
2. Publish 按钮进入 loading 状态，文案显示正在上传中。
3. 上传产物到对象存储。
4. 写入或更新 game meta。
5. 发布成功后显示成功提示。
6. 自动跳转 Home。
7. Home 列表新增刚发布游戏。

发布失败：

- 弹 Error 弹窗。
- 告诉用户可以重试 Publish。
- 调试 Console 打印失败原因和接口返回。

### 5.5 Create Console 输出

Create 页面不新增页面内调试区；调试信息输出到浏览器 DevTools Console。

Console 输出：

- 当前任务 ID。
- 任务名。
- 状态。
- 创建时间、开始时间、结束时间。
- 当前关键步骤。
- Agent 日志。
- 上传文件列表。
- 上传失败错误。
- 产物地址。
- draft game id。
- manifest URL。
- publish 请求状态。
- publish 成功后的 published game id。
- 失败原因。
- 错误日志。
- 用户应该如何重试。

页面内不展示调试面板；验收时打开 DevTools Console 查看输出。

## 6. Play 页面

Play 页面负责运行已发布游戏，同时承载游戏详情信息。

### 6.1 页面功能

必须实现：

- 点击 Home 游戏卡片进入 Play。
- 根据 `GET /api/games/{id}` 加载 game meta。
- 根据 meta 加载 manifest。
- 根据 manifest 加载远端 bundle。
- 使用 sandboxed iframe 运行游戏。
- 游戏详情显示在左侧，不做独立详情页。
- 展示标题、作者、发布时间、简介、标签、点赞数、游玩次数。
- 登录用户点击点赞图标可以点赞。
- 未登录用户点击点赞图标时弹出 Auth Modal。
- 提供返回首页入口。
- 未 load 完成时显示转圈 loading。
- 超时显示 Error 弹窗和重试入口。
- 加载失败显示 Error 弹窗和重试入口。
- 失败时提供重新开始按钮。

Play sandbox 运行边界：

- 页面不额外展示 sandbox 说明，避免干扰游玩。
- iframe 使用 `sandbox="allow-scripts"`。
- 不启用 `allow-same-origin`、`allow-forms`、`allow-popups`、`allow-top-navigation`。
- 生成游戏不能访问父页面 DOM、父页面 cookie/localStorage、摄像头、麦克风、剪贴板，也不能弹窗或跳转顶层页面。
- 父页面与 iframe 只通过 `postMessage` 通信。
- 允许的 iframe 消息类型为 `game_ready`、`game_error`、`game_exit`、`game_metric`。
- 父页面校验 `event.source`、消息 schema 和关联 `game_id`；未知消息忽略并输出 `console.warn`。

### 6.2 左侧详情栏

组件：

- 返回首页。
- 游戏标题。
- 作者。
- 发布时间。
- 点赞图标和点赞数。
- 游玩次数图标和游玩次数。
- 标签。
- 游戏简介。

说明：

- Game Detail 独立页放后续版本。
- MVP 的游戏详情信息直接放在 Play 左侧栏。

### 6.3 游戏运行区

组件：

- iframe 游戏容器。
- 转圈 loading。
- failed 状态。
- timeout 状态。
- 重新开始按钮，仅失败或超时时显示。

运行状态：

| 状态 | 页面表现 |
| --- | --- |
| loading_meta | 显示转圈 loading 和加载游戏信息。 |
| loading_manifest | 显示转圈 loading 和加载 manifest。 |
| loading_bundle | 显示转圈 loading 和加载游戏文件。 |
| ready | 显示可操作游戏。 |
| failed | 弹 Error，显示失败原因和重新开始按钮。 |
| timeout | 弹 Error，提示超时并显示重新开始按钮。 |
| exited | 显示返回首页或重新开始入口。 |

超时规则：

- meta 加载超过 `10s` 进入 timeout。
- manifest 加载超过 `10s` 进入 timeout。
- bundle / iframe ready 超过 `20s` 进入 timeout。
- timeout 需要告诉用户可重试。
- 调试 Console 打印超时阶段、耗时和 URL 摘要。
- 用户点击重新开始时重新加载整个 Play 链路。

### 6.4 Play Console 输出

Play 页面不新增页面内调试区；远端加载链路通过 DevTools Console 和浏览器底部状态栏 URL 证明。

Console 输出：

- `GET /api/games/{id}` 返回 JSON 摘要。
- manifest URL。
- manifest JSON。
- bundle base URL。
- iframe entry URL。
- manifest 加载状态。
- bundle 加载状态。
- 当前加载阶段。
- load 总时长。
- 各加载阶段耗时。
- timeout 信息。
- failed 错误日志。
- 登录用户点赞接口结果。
- 未登录用户点赞触发 Auth Modal 的原因。
- 游玩次数更新结果。

远端文件来源证明：

- URL 通过链接 href 体现：用户 hover 可点击链接时，浏览器底部状态栏显示资源 URL。
- manifest JSON 输出到 DevTools Console。
- 不在主视觉区域堆叠技术信息，避免影响游玩体验。

## 7. 调试 Console 输出规范

本文档中的 print 指浏览器 DevTools Console 输出，不是页面内组件。MVP 不新增页面内调试面板。

### 7.1 使用位置

- Home：Console 输出列表请求、排序、筛选、点赞结果或未登录点赞触发 Auth Modal 的原因。
- Create：Console 输出任务、Agent、上传、产物、发布状态。
- Play：Console 输出 meta、manifest、bundle、iframe、错误日志。
- Auth：成功弹窗展示用户态，Console 输出 session 摘要。

### 7.2 展示内容

Console 支持输出：

- 时间戳。
- 请求路径。
- 状态码。
- 业务状态。
- ID：user_id、job_id、game_id、session 检查结果。
- URL：manifest URL、artifact URL、iframe entry URL。可点击链接在 hover 时由浏览器底部状态栏显示真实目标地址。
- JSON：game meta、manifest、任务结果。
- 错误：error code、message、retry hint。

### 7.3 输出要求

- 不在页面中增加调试 UI。
- 使用 `console.info` 输出正常状态。
- 使用 `console.error` 输出失败状态。
- 不显示 secret、token、password、OAuth code。
- JSON 使用结构化对象输出，便于 DevTools 展开查看。

## 8. 后续版本明确不做

以下能力不进入 MVP 页面实现：

- 收藏。
- 独立游戏详情页。
- My Games / Profile。
- 平台维护者后台。
- 发布后编辑标题、简介、标签、封面。
- 取消发布。
- 完整版本管理 UI。
- Remix 派生。
- 安全沙箱可视化配置。
- 内容审核面板。
- 资源限额展示。
- 生成成本统计。
- GitHub OAuth 真实跑通。

## 9. 已定实现口径

以下页面相关问题已按 MVP 默认方案定稿：

- 未登录用户不能点赞，点击点赞图标时弹 Auth Modal。
- Play sandbox 边界只在实现和文档中体现，不在界面上解释。
- Play 前后端埋点不显示给用户，只写 Console、数据库事件和服务端日志。
- Play 超时后点击重新开始会重新加载整个 Play 链路。
