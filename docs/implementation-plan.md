# AI Native 互动游戏平台 MVP 实施计划索引

## 1. 文档目标

本文档是三端实施计划的总入口。具体执行步骤已拆分到三份可独立运行的端侧计划中：

- [backend-implementation-plan.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/backend-implementation-plan.md)
- [frontend-implementation-plan.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/frontend-implementation-plan.md)
- [agent-implementation-plan.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/agent-implementation-plan.md)

三端共享同一份接口契约：

- [api-contract.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/api-contract.md)

产品和页面事实来源：

- [design-document.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/design-document.md)
- [pages-design.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/pages-design.md)
- [design.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/design.md)

## 2. 拆分原则

- Backend 计划必须能在没有前端和真实 Agent 的情况下独立运行；Agent 未完成时使用 fake runner 验证任务状态流。
- Frontend 计划必须能在没有真实后端和 Agent 的情况下独立运行；后端未完成时使用符合 `api-contract.md` 的 mock 数据。
- Agent 计划必须能在没有前端的情况下独立运行；后端未接入时用固定 fixture 验证执行器输入输出、产物协议和日志。
- 三端不得修改接口字段名来适配自己实现；发现契约问题时，需要同步修改 [api-contract.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/api-contract.md)、[design-document.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/design-document.md) 和对应端侧计划。
- 每完成一个端侧任务，都必须更新 [architecture.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/architecture.md) 和 [progress.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/progress.md)。

## 3. 端侧计划入口

### Backend

执行文档：[backend-implementation-plan.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/backend-implementation-plan.md)

负责范围：

- 业务数据模型和迁移。
- MinIO 存储服务边界。
- Uploads API。
- Games API。
- 点赞 API。
- Play Events API。
- Jobs API。
- Agent 执行器接入边界。
- Publish API。
- seed published 游戏。

可独立运行策略：

- 用 HTTP 测试和后端单元测试验证 API。
- 用 fake Agent runner 验证 Jobs 状态流。
- 不等待前端页面完成。

### Frontend

执行文档：[frontend-implementation-plan.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/frontend-implementation-plan.md)

负责范围：

- 前端路由和 API 客户端。
- 全局导航和 Auth Modal。
- Home 游戏流、搜索、标签筛选、排序、点赞交互。
- Create 页面三栏布局、Create Session 对话阶段、建议答案、文件上传与素材绑定、游戏卡片、任务历史、任务与会话联动、生成后 revision 入口、Agent 日志展示、试玩和发布。
- Play meta / manifest / iframe 加载、sandbox 边界、timeout、Play Events、Console 输出。

可独立运行策略：

- 用 mock API 开发所有页面。
- mock 数据必须符合 [api-contract.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/api-contract.md)。
- 不直接调用 Agent。

### Agent

执行文档：[agent-implementation-plan.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/agent-implementation-plan.md)

负责范围：

- Agent 执行器稳定边界。
- 生成后修改 revision graph 或 revision mode 最小契约。
- Mock provider。
- OpenAI-compatible provider 适配。
- 静态游戏产物校验和打包。
- Agent 日志和失败原因。
- 后端联调 fixture。

可独立运行策略：

- 用固定输入 fixture 验证执行器。
- 输出必须满足后端接入边界。
- 不直接服务前端。

## 4. 最终接线顺序

1. Backend 完成 Auth 既有能力、Backend Step 1 至 Step 7 后，Frontend 可以从 mock 切换到真实 Auth / Games / Uploads / Create Sessions / Jobs / Play Events API。
2. Agent 完成 Agent Step 1 后，Backend Step 8 可以用真实执行器替换 fake runner。
3. Agent 完成 Agent Step 2 或 Step 3 后，Backend 可以生成真实 draft game。
4. Backend 完成 Backend Step 9 后，Frontend Create 的 Publish 能从 draft 发布到 Home。
5. Backend 完成 Backend Step 10 后，Frontend Home / Play 可以用 seed published 游戏进行游客链路验收。

## 5. 集成验收清单

### I1：接口契约联调

- [ ] 前端关闭 mock，指向真实后端。
- [ ] Auth 接口字段与 [api-contract.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/api-contract.md) 一致。
- [ ] Games 列表和 meta 字段与契约一致。
- [ ] Uploads API 字段与契约一致。
- [ ] Jobs API 字段与契约一致。
- [ ] Play Events API 字段与契约一致。
- [ ] 所有接口错误都使用统一错误格式。

### I2：游客 Home 到 Play 链路

- [ ] 未登录浏览器会话可以访问 Home。
- [ ] 可以执行排序、搜索和标签筛选。
- [ ] 未登录点击点赞弹 Auth Modal。
- [ ] 点击游戏卡片进入 Play。
- [ ] iframe 加载远端 MinIO 或 S3-compatible URL。
- [ ] Play loading、ready、failed、timeout 状态可验证。
- [ ] DevTools Console 输出 meta、manifest、entry URL、load 总时长和阶段耗时。

### I3：登录、Google OAuth 和点赞链路

- [ ] 邮箱注册后 session 生效。
- [ ] 退出登录后 session 失效。
- [ ] Google OAuth 首次登录创建用户和绑定记录。
- [ ] Google OAuth 再次登录复用同一 user id。
- [ ] 登录点赞成功更新点赞数。
- [ ] 未登录点赞不调用点赞接口。

### I4：Create 到 Publish 到 Home 链路

- [ ] 登录用户进入 Create。
- [ ] 上传至少一个文件。
- [ ] 输入自然语言创意。
- [ ] 点击建议答案或继续聊天补充需求。
- [ ] 在 `ready_to_confirm` 状态下查看游戏卡片。
- [ ] 可选点击 `换一换` 重新生成另一版方案。
- [ ] 点击 `生成`，先 `confirm` 当前 `create_session`，再基于 confirmed `session_id` 创建生成任务。
- [ ] 任务历史中的任务项返回 `session_id`，点击历史任务能恢复对应对话上下文。
- [ ] 等待任务 succeeded。
- [ ] 在生成面板试玩 draft。
- [ ] 可选在聊天区提出明确修改，创建新的 revision job，不覆盖旧 draft。
- [ ] 点击 Publish。
- [ ] 发布成功后跳转 Home。
- [ ] Home 新增刚发布游戏。
- [ ] 新游戏 Play iframe 加载 published manifest。

### I5：并发任务与权限隔离

- [ ] 同一用户连续提交至少 2 个任务。
- [ ] 两个任务有独立 job id。
- [ ] 两个任务状态独立更新。
- [ ] 一个任务失败不会影响另一个任务。
- [ ] 用户 B 不能访问用户 A 的任务、日志、draft 或发布接口。
- [ ] 游客不能访问 draft。
- [ ] published 游戏仍对所有人可访问。

### I6：最终交付检查

- [ ] 前端 lint 或 build 通过。
- [ ] 后端测试通过。
- [ ] 空数据库迁移成功。
- [ ] Docker Compose 可完整启动。
- [ ] 核心链路「登录/注册 -> 创意生成 -> 发布 -> Home 浏览 -> Play 游玩」通过。
- [ ] `docs/` 下文档没有与 [design-document.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/design-document.md)、[pages-design.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/pages-design.md) 相矛盾的旧口径。
