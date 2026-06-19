# AI Native 互动游戏平台 MVP 产品设计文档

## 1. 文档目标

本文档定义 AI Native 互动游戏平台 MVP 的产品范围、核心用户旅程、页面能力、业务状态、数据模型、接口边界、运行时协议、安全边界和已知取舍。

当前版本先不展开 Agent 内部设计，只定义用户可见的生成任务、任务日志、发布状态、Play 运行协议、Console 调试输出和页面交互边界。页面功能与布局以 [pages-design.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/pages-design.md) 为准。

## 2. 产品目标

MVP 需要在 2 天交付周期内打通完整闭环：

1. 用户可以通过邮箱注册/登录。
2. 未登录用户可以浏览首页游戏流并游玩已发布游戏。
3. 登录用户可以提交创意和文件素材，创建互动游戏生成任务。
4. 系统异步生成游戏产物，并展示任务状态、Agent 执行日志和错误原因。
5. 用户可以在 Create 生成面板中直接试玩 draft 游戏，试玩即 Preview，并确认发布。
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
- 点击点赞图标时弹出登录/注册弹窗，不执行点赞请求。
- 点击 Create、Publish、删除等受保护操作时，弹出登录/注册弹窗。

### 登录用户

- 可以创建生成任务。
- 可以上传任意文件作为素材。
- 可以查看自己的任务历史。
- 可以在 Create 生成面板中试玩自己的 draft 游戏。
- 可以点赞 published 游戏。
- 可以发布自己生成成功的 draft 游戏。
- 只能发布、编辑、删除自己的游戏或任务。

### 平台维护者

MVP 暂不实现平台维护者后台。平台维护者能力只在设计上保留扩展空间，包括内容审核、异常包处理、对象存储管理、任务稳定性监控和违规内容下架。

## 6. 核心用户旅程

### 未登录游客旅程

1. 进入 Home。
2. 浏览所有用户发布的游戏。
3. 选择排序：最新发布、最多游玩或最多点赞。
4. 可以搜索游戏、按标签筛选游戏；点击点赞图标时弹出登录/注册弹窗。
5. 点击游戏卡片。
6. 进入 Play。
7. Play 从后端获取游戏 meta。
8. Play 加载 MinIO 中的 `manifest.json` 和游戏 bundle。
9. 游戏在 sandboxed iframe 中运行。
10. 系统记录游玩次数和基础 play 事件。

### 登录用户旅程

1. 用户进入 Create。
2. 如果未登录，弹出登录/注册弹窗。
3. 登录后输入创意文本并上传任意文件素材。
4. 提交生成任务。
5. 后端创建 `generation_job`，状态为 `pending`。
6. 后台任务执行，状态更新为 `running`。
7. Create 页面任务历史实时展示任务状态和 Agent 执行日志。
8. 任务成功后状态为 `succeeded`，生成结果默认是 `draft`。
9. 用户在生成游戏面板中直接试玩 draft 游戏。
10. 用户点击 `Publish`。
11. Publish 按钮显示上传中。
12. 后端上传产物、保存 meta，并将游戏状态更新为 `published`。
13. 发布成功后跳转 Home。
14. Home 游戏流新增刚发布的游戏，可被所有用户游玩。

## 7. MVP 页面范围

| 页面 / 组件 | MVP 范围 | 说明 |
| --- | --- | --- |
| Home | 必做 | 展示所有 published 游戏，支持最新发布 / 最多游玩 / 最多点赞排序，支持搜索、标签筛选；点赞需要登录。 |
| Auth Modal | 必做 | 登录注册不做独立页面，统一用弹窗承载。 |
| Create | 必做 | 支持自然语言对话、任意文件上传、任务历史、状态、Agent 日志、试玩和发布。 |
| Play | 必做 | 动态加载远端 manifest 和 bundle，在 sandboxed iframe 中运行游戏，并在左侧承载轻量游戏详情。 |
| Game Detail | 不做 | 不做独立详情页；MVP 的游戏详情显示在 Play 左侧栏。 |
| My Games / Profile | 不做 | MVP 没有单独展示用户已发布游戏的地方。 |
| Admin Console | 不做 | 平台维护者后台放后续版本。 |

## 8. 页面设计

### 8.1 全局导航

导航包含：

- 产品名 `Yahaha_Play`。
- `主页` 入口。
- `创建游戏` 入口。
- 登录状态区域。

未登录时显示默认头像和 `登录`，点击打开 Auth Modal。已登录时显示 OAuth 或本地账号头像和昵称，展开后可以 `退出登录`。

点击 `创建游戏` 时，如果未登录，弹出 Auth Modal，不跳转；退出登录后头像切换为默认头像，再次访问受保护入口时按未登录逻辑处理。

导航在 Home 和 Play 中可以采用透明或深色叠层；在 Create 中采用深色固定导航，优先保证工作流可读性。

### 8.2 Auth Modal

Auth 不做独立页面，使用一个弹窗承载登录、注册和退出后的重新登录。

能力：

- 邮箱注册。
- 邮箱登录。
- Google 第三方登录，MVP 需要真实跑通。
- GitHub 第三方登录入口只保留占位或 disabled，后续版本再真实跑通。
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
- 登录成功后关闭弹窗，顶部头像和昵称更新，并显示成功弹窗或成功提示。
- 登录失败、注册失败、OAuth 回调失败均显示明确 Error 弹窗或表单错误提示。

第三方登录：

- Google OAuth 作为 MVP 加分项真实接入，完成授权跳转、回调处理、账号创建或绑定、session 写入和受保护页面访问控制。
- GitHub OAuth 先完成设计与数据模型，不在 MVP 中真实跑通。
- 第三方登录成功后，如果邮箱已存在，则绑定到已有用户；如果邮箱不存在，则创建新用户并绑定 OAuth 身份。
- 授权回调成功后回到应用，展示当前 OAuth 账号头像和昵称；账号绑定结果不做独立页面展示，表现与普通登录一致。
- 账号绑定结果需要可验证：数据库中存在 `oauth_accounts` 记录，`GET /api/auth/me` 能返回登录用户信息。

### 8.3 Home

Home 展示所有用户发布的 `published` 游戏列表，不区分官方示例和用户生成。

卡片字段：

- 封面。
- 标题。
- 作者。
- 标签。
- 发布时间。
- 简介，默认不常驻显示，只在 hover 浮层展示。
- 点赞图标和点赞数。
- 游玩次数。

排序：

- 最新发布。
- 最多游玩。
- 最多点赞。

筛选与搜索：

- 支持搜索框。
- 支持标签筛选。

交互：

- 点击卡片主体进入 Play。
- 标签不是 Play 入口，只作为标签展示。
- 登录用户点击点赞图标后触发点赞动作。
- 未登录用户点击点赞图标时弹出 Auth Modal，不执行点赞请求。
- 点赞动作与卡片进入 Play 的点击区域需要避免冲突。

MVP 不做：

- 收藏。
- 独立游戏详情页。

空状态：

- 如果没有 published 游戏，展示引导文案和 Create CTA。
- 测试数据至少 seed 3 个示例游戏，其中至少 1 个需要来自 Create 发布闭环。

### 8.4 Create

Create 是创作者工作台。MVP 采用左侧任务列表、对话上传区和生成游戏显示面板的布局。页面以自然语言对话为主，不做结构化表单输入。

已确认产品能力：

- 需要登录。
- 支持自然语言创意输入。
- 支持任意文件上传。
- 点击附件 icon 选择文件。
- 上传成功后的文件列表显示在用户聊天框下方。
- 用户可以并发提交多个生成任务。
- 用户提交任务后可以离开页面，回来继续查看任务状态。
- 左侧任务列表展示任务历史。
- 每条任务在任务名后实时显示状态：`pending / running / succeeded / failed`。
- 每条任务展示创建时间和结果摘要。
- Agent 执行步骤和当前关键步骤显示在生成游戏的 Agent 记录区域。
- 任务成功后生成结果默认是 `draft`。
- 生成成功后直接显示可试玩游戏，试玩即 Preview。
- Publish 按钮放在游戏旁边。
- 用户点击 `Publish` 后按钮显示上传中。
- 发布成功后跳转 Home，Home 新增用户刚刚发布的游戏。

自然语言与结构化信息：

- 不单独提供玩法、风格、角色、胜负条件等固定字段。
- 用户可以直接用自然语言描述想做的游戏。
- AI 可以追问缺失信息。
- AI 最后输出确认卡片，供用户确认后开始生成。
- 最终确认卡片展示 AI 理解出的游戏标题、一句话简介、游戏类型、核心玩法、胜负条件、操作方式、使用到的素材、标签和封面建议。
- 用户可以直接在最终确认卡片里修改这些字段。

布局组件：

- 左侧任务列表：任务名、状态、创建时间、结果摘要、`+ 新建任务`。
- 聊天与上传区：Agent 欢迎消息、AI 追问、用户消息、最终确认卡片、输入框、附件 icon、发送 icon、文件列表。
- 生成游戏显示面板：idle、pending、running、succeeded、failed、timeout 状态，进度条、Agent 记录、可试玩游戏、Publish 按钮。

暂不实现：

- 发布后编辑标题、简介、标签、封面。
- 用户已发布游戏管理页。
- 取消发布。
- 生成中 Cancel。
- Remix 派生。
- 版本管理 UI。
- 安全沙箱可视化配置。
- 内容审核面板。
- 资源限额展示。
- 生成成本统计。

### 8.5 Play

Play 页面负责动态加载并运行远端游戏，同时在左侧承载轻量游戏详情。MVP 不做独立 Game Detail 页面。

页面状态：

| 状态 | 行为 |
| --- | --- |
| loading_meta | 显示转圈 loading，并提示正在加载游戏信息。 |
| loading_manifest | 显示转圈 loading，并提示正在加载 manifest。 |
| loading_bundle | 显示转圈 loading，并提示正在加载游戏文件。 |
| ready | 在 sandboxed iframe 中展示可操作游戏。 |
| failed | 弹 Error，展示失败原因、重试按钮和返回首页入口。 |
| timeout | 弹 Error，提示超时并显示重试入口。 |
| exited | 提供返回首页和重新开始入口。 |

展示信息：

- 游戏标题。
- 作者。
- 发布时间。
- 简介。
- 标签。
- 点赞图标和点赞数。
- 游玩次数。
- 返回 Home。
- 失败或超时时显示重新开始。

点赞规则：

- 登录用户点击点赞图标后调用点赞接口。
- 未登录用户点击点赞图标时弹出 Auth Modal，不执行点赞请求。
- MVP 点赞只做新增点赞，不做取消点赞。

运行机制：

- 前端请求 `GET /api/games/{id}` 获取 meta。
- 前端从 meta 中读取 `manifest_url`。
- 前端加载 MinIO public-read `manifest.json`。
- 前端将 `index.html` 作为 iframe 入口。
- iframe 使用 sandbox 限制能力。
- meta 加载超过 `10s`、manifest 加载超过 `10s`、bundle / iframe ready 超过 `20s` 时进入 timeout。
- 用户点击重新开始时重新加载整个 Play 链路。

Sandbox 运行边界：

- 页面不额外展示 sandbox 说明，避免干扰游玩。
- iframe 使用 `sandbox="allow-scripts"`。
- 不启用 `allow-same-origin`、`allow-forms`、`allow-popups`、`allow-top-navigation`。
- 生成游戏不能访问父页面 DOM、父页面 cookie/localStorage、摄像头、麦克风、剪贴板，也不能弹窗或跳转顶层页面。
- 父页面与 iframe 只通过 `postMessage` 通信。
- 允许的 iframe 消息类型为 `game_ready`、`game_error`、`game_exit`、`game_metric`。
- 父页面校验 `event.source`、消息 schema 和关联 `game_id`；未知消息忽略并输出 `console.warn`。

Play 必须能证明游戏文件来自 MinIO 或 S3-compatible URL，而不是本地硬编码组件。证明方式：

- 资源 URL 通过链接 href 体现，用户 hover 可点击链接时，浏览器底部状态栏显示真实目标地址。
- `GET /api/games/{id}` 返回 JSON 摘要、manifest URL、manifest JSON、bundle base URL、iframe entry URL、加载状态、load 总时长、各阶段耗时和错误日志输出到浏览器 DevTools Console。
- 不在页面主视觉区域堆叠技术信息，避免影响游玩体验。

### 8.6 调试 Console 输出

本文档中的 print 指浏览器 DevTools Console 输出，不是页面内组件。MVP 不新增页面内调试面板。

Console 使用位置：

- Home：输出列表请求、排序、筛选、点赞结果。
- Create：输出任务、Agent、上传、产物、发布状态。
- Play：输出 meta、manifest、bundle、iframe、错误日志。
- Auth：成功弹窗展示用户态，Console 输出 session 摘要。

Console 输出要求：

- 使用 `console.info` 输出正常状态。
- 使用 `console.error` 输出失败状态。
- 不显示 secret、token、password、OAuth code。
- JSON 使用结构化对象输出，便于 DevTools 展开查看。

### 8.7 全局错误反馈

所有失败状态都需要统一显示 Error 弹窗或明确错误提示，并告诉用户如何重试。

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
| user_id | uuid | 系统唯一用户 ID，主键 |
| email | varchar nullable | 用户邮箱，不作为系统唯一身份 |
| password_hash | varchar nullable | 邮箱注册用户的密码哈希；OAuth-only 用户为空 |
| display_name | varchar nullable | 展示名，默认取邮箱前缀或第三方展示名 |
| avatar_url | text nullable | 头像 URL |
| created_at | timestamp | 创建时间 |
| updated_at | timestamp | 更新时间 |

约束：

- 系统身份唯一标识是 `user_id`，不是 email。
- `email` 不作为外键，也不作为系统主键。
- 邮箱注册场景中，本地密码账号不允许重复使用同一个 email。
- OAuth-only 用户允许 `password_hash = null`。

### oauth_accounts

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| oauth_id | uuid | OAuth 绑定 ID，主键 |
| user_id | uuid | 外键，关联 `users.user_id` |
| provider | varchar | `google / github` |
| provider_user_id | varchar | 第三方平台用户唯一 ID |
| provider_email | varchar | 第三方平台返回邮箱 |
| provider_name | varchar | 第三方平台展示名 |
| avatar_url | text | 第三方头像 URL |
| access_token_encrypted | text nullable | 加密后的访问令牌；MVP 可不长期保存 |
| refresh_token_encrypted | text nullable | 加密后的刷新令牌；MVP 可不长期保存 |
| created_at | timestamp | 绑定时间 |
| updated_at | timestamp | 更新时间 |

约束：

- `(provider, provider_user_id)` 唯一。
- 同一个用户可以绑定多个 provider。
- 第三方 token 不允许明文存储；如果 MVP 不需要调用第三方 API，登录后可以只保存 provider identity，不保存 access token。
- Google email 与已有邮箱注册账号相同且 `email_verified=true` 时，自动绑定到已有 `user_id`。
- Google email 相同但 Google `provider_user_id` 不同，不自动合并，避免误绑。
- OAuth-only 用户不能使用邮箱密码登录，除非后续实现设置密码。

### sessions

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| session_id | uuid | session ID，主键 |
| user_id | uuid | 外键，关联 `users.user_id` |
| expires_at | timestamp | 过期时间 |
| last_seen_at | timestamp nullable | 最近访问时间 |
| user_agent | text nullable | 登录设备 UA |
| ip_address | varchar nullable | 登录 IP |
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
| like_count | integer | 点赞次数 |
| published_at | timestamp | 发布时间 |
| created_at | timestamp | 创建时间 |
| updated_at | timestamp | 更新时间 |

### game_likes

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | uuid | 点赞记录 ID |
| game_id | uuid | 游戏 ID |
| user_id | uuid | 点赞用户 ID，关联 `users.user_id` |
| created_at | timestamp | 点赞时间 |

约束：

- 点赞必须登录。
- 同一用户对同一游戏最多点赞一次，使用 `(game_id, user_id)` 唯一约束。
- MVP 点赞只做新增点赞，不做取消点赞。

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
| job_id | uuid nullable | 关联生成任务；文件可先上传，创建任务后再绑定 |
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
| event_type | varchar | `view / manifest_loaded / started / failed / timeout / exited` |
| metadata | jsonb | 阶段、耗时、错误原因、URL 类型等；不记录 secret |
| created_at | timestamp | 事件时间 |

## 12. 登录注册重点测试用例

系统唯一身份以 `users.user_id` 为准。OAuth 登录时，首次登录会同时创建 `users` 和 `oauth_accounts`；再次登录通过 `(provider, provider_user_id)` 找回同一个 `user_id`。

| ID | 场景 | 输入 / 前置条件 | 期望输出 | `users` 变化 | `oauth_accounts` 变化 |
| --- | --- | --- | --- | --- | --- |
| A01 | 邮箱注册成功 | 新 email + password | 注册成功并创建 session | 新增 1 条，`password_hash` 有值 | 无变化 |
| A02 | 邮箱注册重复 | 已存在本地密码账号 email | 注册失败，提示邮箱已注册 | 无变化 | 无变化 |
| A03 | 邮箱登录成功 | 已注册 email + 正确 password | 登录成功并创建 session | 无变化 | 无变化 |
| A04 | 邮箱登录密码错误 | 已注册 email + 错误 password | 登录失败 | 无变化 | 无变化 |
| A05 | OAuth-only 用户尝试邮箱登录 | 同 email 用户存在，但 `password_hash=null` | 登录失败，提示使用第三方登录或后续设置密码 | 无变化 | 无变化 |
| G01 | Google 首次登录 | Google 返回 `sub/email/name/avatar`，无对应绑定 | 登录成功并创建 session | 新增 1 条，`password_hash=null` | 新增 1 条，`provider=google` |
| G02 | Google 再次登录 | 同一个 Google `sub` 已绑定 | 登录成功，返回同一 `user_id` | 不新增，可更新展示名/头像 | 不新增，可更新 provider 信息 |
| G03 | Google email 命中邮箱注册账号 | Google `email_verified=true`，email 已有本地密码账号 | 自动绑定并登录已有 `user_id` | 不新增用户 | 新增 Google 绑定 |
| G04 | Google email 相同但 `sub` 不同 | 已有另一个 Google 绑定使用相同 email | 不自动合并，避免误绑；MVP 可创建新用户或拒绝并提示 | 不合并到旧用户 | 不覆盖旧绑定 |
| G05 | Google 回调 state 错误 | OAuth 回调 `state` 缺失或不匹配 | 登录失败 | 无变化 | 无变化 |
| G06 | Google token 换取失败 | code 无效或过期 | 登录失败 | 无变化 | 无变化 |
| G07 | Google 用户信息缺少 email 或 email 未验证 | Google profile 异常 | 登录失败或不自动绑定 | 无变化 | 无变化 |
| H01 | GitHub 登录入口 | MVP 未启用 | 返回暂未启用 | 无变化 | 无变化 |
| S01 | 查看 session | 有效 session cookie | `GET /api/auth/me` 返回 `user_id` 和用户信息 | 无变化 | 无变化 |
| S02 | 退出登录 | 有效 session cookie | session 失效，受保护页面不可访问 | 无变化 | 无变化 |

验收重点：

- session 表中保存 `user_id`，不使用 email 作为身份。
- Google 首次登录后必须同时存在 `users` 和 `oauth_accounts` 记录。
- Google 再次登录不能重复创建用户。
- GitHub OAuth 在 MVP 中只做未启用占位，不影响邮箱登录和 Google 登录。

## 13. API 设计

前后端字段、状态码、错误格式和 mock 约定以 [api-contract.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/api-contract.md) 为准；本节只保留产品级接口边界。

### Auth

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/auth/register` | 邮箱注册 |
| POST | `/api/auth/login` | 邮箱登录，写入 httpOnly session cookie |
| POST | `/api/auth/logout` | 退出登录 |
| GET | `/api/auth/me` | 获取当前 session 用户 |
| GET | `/api/auth/oauth/google/start` | 发起 Google OAuth 授权跳转 |
| GET | `/api/auth/oauth/google/callback` | Google OAuth 回调，完成账号创建/绑定并写入 session |
| GET | `/api/auth/oauth/github/start` | GitHub OAuth 授权跳转；MVP 可返回未启用状态或仅保留路由设计 |
| GET | `/api/auth/oauth/github/callback` | GitHub OAuth 回调设计占位；后续版本实现 |

OAuth 回调处理规则：

- 校验 `state`，防止 CSRF。
- 用授权码换取 token。
- 获取 provider 用户信息。
- 优先通过 `(provider, provider_user_id)` 查找绑定账号。
- 如未绑定，通过 provider email 查找已有用户并绑定。
- 如邮箱不存在，创建新用户并绑定。
- 创建服务端 session，写入 httpOnly cookie。
- 回跳前端原始页面或默认 Home/Create。

### Games

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | `/api/games` | 公开 | 获取 published 游戏列表，支持 `sort=latest/play_count/like_count`、搜索和标签筛选 |
| GET | `/api/games/{game_id}` | 公开或 owner | 获取游戏 meta；draft 仅 owner 可访问 |
| POST | `/api/games/{game_id}/publish` | owner | 发布 draft 游戏 |
| POST | `/api/games/{game_id}/like` | 登录 | 点赞游戏 |
| DELETE | `/api/games/{game_id}` | owner | 删除自己的 draft 或未发布产物 |

MVP 暂不提供发布后编辑接口。发布后编辑标题、简介、标签、封面放后续版本。

### Create Jobs

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| POST | `/api/jobs` | 登录 | 创建生成任务 |
| GET | `/api/jobs` | 登录 | 获取自己的任务历史 |
| GET | `/api/jobs/{job_id}` | owner | 获取任务详情、状态和产物地址；产物地址用于 Console 输出与验收 |
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
| POST | `/api/play-events` | 公开 | 记录 view、manifest_loaded、started、failed、timeout、exited 等事件 |

## 14. 权限规则

- Home published 列表公开。
- Play published 游戏公开。
- 搜索和标签筛选公开。
- 点赞需要登录；未登录点击点赞图标时弹 Auth Modal。
- Create 页面必须登录。
- 生成任务只对创建者可见。
- draft 游戏只对 owner 可见。
- Publish 只能由 owner 执行。
- Delete 只能由 owner 执行。
- 发布后的游戏进入公开列表。
- 发布后编辑游戏信息不在 MVP 范围内。

## 15. 安全设计

### 会话安全

- 使用服务端 session。
- Session ID 通过 `httpOnly` cookie 存储。
- Cookie 设置 `SameSite=Lax`。
- 生产环境启用 `Secure`。
- 密码使用强哈希算法存储，不能明文保存。
- Google OAuth 必须使用 `state` 参数防止 CSRF。
- OAuth client secret 只能存在后端环境变量中，不能暴露给前端。
- 第三方 access token 如需保存必须加密；MVP 优先不长期保存 token。

### 上传安全

- 任意文件上传只进入私有 MinIO 路径。
- 后端校验文件大小和基础 MIME 信息。
- 上传文件不在后端执行。
- Agent 只能通过授权 URL 读取素材。
- 公开产物和原始上传素材分开存储。

### Play 隔离

- 生成游戏在 sandboxed iframe 中运行。
- iframe 使用 `sandbox="allow-scripts"`，只允许脚本运行。
- iframe 不启用 `allow-same-origin`、`allow-forms`、`allow-popups`、`allow-top-navigation`。
- iframe 禁止访问父页面 DOM。
- iframe 禁止读取父页面 cookie/localStorage。
- iframe 禁止打开弹窗或跳转顶层页面。
- iframe 禁止访问摄像头、麦克风和剪贴板。
- 父页面与 iframe 仅通过 `postMessage` 白名单通信，允许 `game_ready`、`game_error`、`game_exit`、`game_metric`。
- 父页面必须校验消息来源和 schema，未知消息忽略并输出 `console.warn`。
- 后端不执行生成游戏中的 JS。
- published bundle 只作为静态文件加载。
- Play 加载失败时展示错误态，不白屏。
- Play 加载超时时展示错误态和重试入口。

### 密钥安全

- `.env.example` 只列变量名和用途，不提交真实密钥。
- OpenAI-compatible API key 只存在后端环境变量中。
- 前端不能直接接触模型服务密钥。

## 16. 埋点与可观测性

MVP 埋点不做用户可见看板，只写 Console、数据库事件和服务端日志。

前端 Console 至少输出：

- 游戏列表曝光或请求。
- Home 搜索、标签筛选、排序请求。
- 登录用户点赞成功 / 失败。
- 未登录用户点赞触发 Auth Modal。
- Play view。
- Play load 总时长。
- Play meta、manifest、bundle / iframe ready 各阶段耗时。
- manifest 加载成功 / 失败。
- iframe 启动成功 / 失败。
- Play 加载超时。
- 生成任务创建。
- 生成任务状态变化。
- 文件上传成功 / 失败。
- Publish 成功 / 失败。

后端数据库事件至少记录：

- Play `view`。
- Play `manifest_loaded`。
- Play `started`。
- Play `failed`。
- Play `timeout`。
- Play `exited`。
- 生成任务状态变化。
- Publish 成功 / 失败。

服务端日志至少记录：

- 认证失败与 OAuth 回调失败。
- 文件上传登记失败。
- 生成任务异常。
- Publish 异常。
- Play events 写入异常。

埋点元数据规则：

- 可以记录 `stage`、`duration_ms`、`error_code`、`url_type`、`game_id`、`job_id`。
- 不记录 secret、token、password、OAuth code、presigned URL 完整签名。

任务可观测性：

- 每个任务展示 Agent 执行日志摘要。
- 每个任务保留错误原因。
- 每个任务保留产物路径或 manifest URL。

## 17. 测试数据

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
- 点赞数和游玩次数。

## 18. 已知取舍

- Auth 不做独立页面，统一使用弹窗。
- 未登录用户可以浏览和游玩，但不能创建、发布或点赞。
- 独立 Game Detail 不进入 MVP；Play 左侧承载轻量游戏详情。
- 搜索、标签筛选、登录后点赞进入 MVP。
- 收藏不进入 MVP。
- 发布后编辑标题、简介、标签、封面不进入 MVP。
- 取消发布不进入 MVP。
- 用户已发布游戏管理页不进入 MVP。
- 平台维护者后台不进入 MVP。
- Create 页面布局以 [pages-design.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/pages-design.md) 为准。
- Agent 内部编排不在本文档展开。
- 异步任务使用 FastAPI BackgroundTasks，不引入 Celery。
- Play sandbox 边界不在界面上解释，只在实现和文档中体现。
- Play 前后端埋点不显示给用户，只写 Console、数据库事件和服务端日志。
- Create 上传素材用途由 AI 自动推断，并允许用户在最终确认卡片里修改。
- Play 超时阈值采用 meta `10s`、manifest `10s`、bundle / iframe ready `20s`，重试时重新加载整个 Play 链路。

## 19. 后续版本规划

如果再给 1 周，建议优先迭代：

1. 用户作品管理页：展示自己的 draft、published 和 deleted 游戏。
2. 发布后编辑游戏 meta：标题、简介、标签、封面。
3. 取消发布和重新发布。
4. 收藏和分享。
5. 任务 Retry、Cancel 和版本管理。
6. Remix 派生。
7. 安全沙箱可视化配置、内容审核、资源限额和生成成本统计。
8. 平台维护者后台：内容审核、任务监控、产物下架。
9. GitHub OAuth 真实跑通，以及多 provider 账号绑定管理。
10. Play 性能统计：manifest 加载耗时、iframe ready 耗时、运行错误率。

## 20. 待实现前再次确认

以下问题尚未最终确认。进入对应实现前需要再次讨论：

### 20.1 Agent 设计

- LangGraph 工作流节点如何拆分。
- 是否需要 planner、asset analyzer、game designer、code generator、validator、packager 等角色。
- Mock provider 与真实 OpenAI-compatible provider 的切换边界。
- Agent 日志展示粒度和错误分类。
- Agent 失败后是否允许用户点击 retry，以及 retry 是否进入 MVP。
