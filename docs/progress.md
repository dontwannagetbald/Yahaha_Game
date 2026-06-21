# 项目进度记录

本文档记录已实现功能、对应实施计划 step，以及尚未落地或需要补齐的边界。项目 layer、目录边界和文件职责维护在 [architecture.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/architecture.md)。

### 2026-06-21：Create 生成后改为聊天触发修改 ☑️ 已完成

- 已调整确认卡片展示逻辑：用户确认游戏卡片后，卡片继续留在聊天区作为原始方案记录，但 `确认 / 重新生成` 按钮只在 `ready_to_confirm` 阶段显示，进入 confirmed 或生成中后会隐藏（Frontend Step 6.12）。
- 已在生成成功后追加 AI 提示气泡“有想要修改的地方欢迎随时告诉我～”，引导用户通过聊天框继续提出修改，不再依赖右侧操作按钮（Frontend Step 6.12）。
- 已移除右侧游戏面板里的“重做”按钮；用户在成功态聊天框发送修改需求时，前端会立即追加用户消息和 AI 气泡“好的，这就为您修改”，并基于当前 succeeded 任务调用 `POST /api/jobs/{job_id}/revisions` 创建 revision job（Frontend Step 6.12）。
- 已保持旧卡片不变，不再因为 revision 生成新卡片；修改结果只通过右侧选中的新 revision 任务和游戏预览体现（Frontend Step 6.12）。
- 已更新 `frontend/scripts/check-create-confirm-card.mjs`、`check-create-chat-event.mjs`、`check-create-redo-revision.mjs` 和 `check-create-layout.mjs`，锁定确认后隐藏按钮、聊天气泡、聊天触发 revision 和右侧移除重做按钮（Frontend Step 6.12）。
- 已验证 `cd frontend && npm run test:create-redo-revision`、`npm run test:create-confirm-card`、`npm run test:create-chat-event`、`npm run test:create-layout`、`npm run build` 通过（Frontend Step 6.12）。

### 2026-06-21：Create 成功态封面入口与预览舞台 ☑️ 已完成

- 已把 `Create` 成功态右侧预览改为“封面先行，点击开始游玩后再挂载 iframe”；前端按 `job_id` 记忆本页已开始的任务，切到别的任务再切回同一任务时会继续直接显示游戏，不会每次都重置到封面（Frontend Step 6.11）。
- 已在 `backend/app/jobs.py` 的任务序列化补齐 `cover_url`，并在 `frontend/src/App.tsx` / `frontend/src/mock/runtime.ts` 映射到 `CreateTaskItem`，让成功态封面优先使用真实游戏封面，拿不到时再回退默认封面（Frontend Step 6.11）。
- 已重构 `frontend/src/pages/CreatePage.tsx` 与 `frontend/src/pages/create.css` 的成功态沙盒结构，新增封面舞台、开始按钮和独立运行内框；运行 iframe 改为挂在带安全内边距的 `preview-runtime-shell` 内，减少游戏最右侧贴边被裁掉的情况（Frontend Step 6.11）。
- 已保留沙盒下方可点击 `Bundle URL`，确保你之前要求的独立打开 draft bundle 入口仍可用（Frontend Step 6.11）。
- 已更新 `backend/tests/test_jobs.py` 与 `frontend/scripts/check-create-layout.mjs`，分别锁定 `job cover_url` 返回和“封面入口后再挂载 iframe”的 Create 成功态结构（Frontend Step 6.11）。
- 已验证 `cd backend && ../.venv/bin/python -m pytest tests/test_jobs.py -q`、`cd frontend && npm run test:create-layout`、`cd frontend && npm run build` 通过（Frontend Step 6.11）。

### 2026-06-21：Home 页游戏标签中文化补齐 ☑️ 已完成

- 已定位主页标签仍显示英文的根因：`frontend/src/lib/games.ts` 的 `mapGameTagToChinese()` 映射表缺少首页真实高频标签 `casual / runner / co-op`，导致卡片与精选区直接回退显示原始英文（Frontend Step 4）。
- 已按后端 `MVP_TAGS={adventure, action, strategy, puzzle, arcade, survival, simulation, racing, rhythm, roleplay, casual, educational}` 对齐前端双向标签映射；显示侧补齐 `simulation/rhythm/roleplay/educational` 等标准标签中文名，请求侧 `mapChineseTagToGameTag()` 会把中文筛选词翻回 canonical tag，避免中文筛选命中不到英文存储标签（Frontend Step 4）。
- 已同步将 Home 页筛选菜单改为 `全部类型 + 12 个 MVP 标签中文项`，移除与当前标准集合不一致的旧筛选文案（Frontend Step 4）。
- 已更新 `frontend/scripts/check-play-page.mjs` 和 `frontend/scripts/check-home-api.mjs`，分别锁定标签映射覆盖和 Home Games API 的中文标签回转行为（Frontend Step 4）。
- 已验证 `cd frontend && npm run test:play-page`、`npm run test:home-api`、`npm run build` 通过（Frontend Step 4）。

### 2026-06-21：Create 任务列表支持删除历史任务 ☑️ 已完成

- 已补充后端 `DELETE /api/jobs/{job_id}`，删除范围收敛为单条历史任务；只允许删除自己的已结束任务，`pending/running` 会返回 `409`，并在删除前解绑子 revision 的 `parent_job_id` 与素材 `job_id`，避免脏引用残留（Step 8.5、Frontend Step 6.10）。
- 已在 `backend/tests/test_jobs.py` 增加删除回归，覆盖“删任务不删会话”“非本人不可删除”“生成中任务不可删除”三条核心边界（Step 8.5）。
- 已在 `frontend/src/api/jobs.ts`、`frontend/src/App.tsx` 和 `frontend/src/pages/CreatePage.tsx` 接入任务删除按钮与调用链路；删除当前选中任务后，会自动切到剩余最新任务，若没有历史任务则新建空白会话，避免右侧残留已删除任务的旧内容（Frontend Step 6.10）。
- 已在 `frontend/src/mock/runtime.ts` 补齐 mock 删除行为，并在 `frontend/src/pages/create.css` 调整任务项结构为“选择按钮 + 删除按钮”，避免按钮嵌套并对生成中任务禁用删除（Frontend Step 6.10）。
- 已验证 `cd backend && ../.venv/bin/python -m pytest tests/test_jobs.py tests/test_create_sessions.py -q` 与 `cd frontend && npm run build` 通过；结果分别为 `30 passed` 和 `vite build` 成功（Step 8.5、Frontend Step 6.10）。

### Backend Real Generation：Coding/Asset 真实 provider 接入 ☑️ 已完成

- 已定位前端生成后仍像“本地写死”的根因：`generation_graph.draft_game_code()` 硬编码使用 `MockLLMProvider(response=_mock_code_response(state))`，导致 Coding Agent 即使在 `LLM_PROVIDER=openai-compatible` 时也不会调用真实大模型生成 HTML/CSS/JS（Backend Real Generation）。
- 已改为按环境选择 Coding provider：`LLM_PROVIDER=mock` 时保留 deterministic 本地模板，非 mock 时调用 `provider_from_env()`，让 Coding Agent 真正请求配置的大模型生成 bundle 代码（Backend Real Generation）。
- 已发现 backend 容器未传入 `ASSET_IMAGE_PROVIDER / OPENAI_IMAGE_*`，导致 Asset Agent 图像仍走 mock PNG；已在 `docker-compose.yml` 和 `.env.example` 补齐图像 provider 环境变量（Backend Real Generation）。
- 已新增回归测试锁定非 mock 配置下 `draft_game_code` 必须调用配置 provider，并验证生成的 `game.js` 来自 provider 返回值；已验证 `cd lan_agents && .venv/bin/python -m pytest tests/integration_tests/test_generation_graph.py tests/unit_tests/test_coding_agent.py tests/unit_tests/test_generation_provider.py -q` 通过，结果为 `19 passed`（Backend Real Generation）。
- 已验证 `cd backend && ../.venv/bin/python -m pytest -q` 通过，结果为 `108 passed`（Backend Real Generation）。

### Backend Agent Debug：兼容 max_completion_tokens 模型参数 ☑️ 已完成

- 已定位 `Orchestrator failed while building parallel contracts` 的根因：`OpenAICompatibleLLMProvider.complete_json()` 对 chat completions 固定发送 `max_tokens`，但当前配置模型拒绝该参数并要求使用 `max_completion_tokens`（Backend Agent Debug）。
- 已在 chat completions 请求遇到 `Unsupported parameter: max_tokens ... Use max_completion_tokens instead` 时自动重试一次，并将 payload 中的 `max_tokens` 替换为 `max_completion_tokens`；Responses API 分支继续使用现有 `max_output_tokens`（Backend Agent Debug）。
- 已新增 provider 回归测试，断言第一次请求使用 `max_tokens`、收到 400 后第二次请求改用 `max_completion_tokens` 且成功解析 JSON，避免 Orchestrator 因模型参数方言失败（Backend Agent Debug）。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_llm_provider.py -q`、`cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_generation_orchestrator.py tests/unit_tests/test_generation_provider.py tests/integration_tests/test_generation_graph.py -q` 和 `cd lan_agents && .venv/bin/langgraph validate` 通过（Backend Agent Debug）。

### Backend Agent Debug：拦截静态封面 bundle 冒充可玩游戏 ☑️ 已完成

- 已定位“Create 右侧预览看起来像封面而不是游戏”的后端根因：当前 `runtime_check` 只校验 `canvas / game.js / game_ready / render signal`，静态标题页只要循环重绘也会被误判为可玩 bundle（Backend Agent Debug）。
- 已在 `lan_agents/src/agent/generation_graph/tools/runtime_check.py` 增加最小交互门禁，要求 `game.js` 至少包含键盘、鼠标、指针或触摸输入信号；缺失时 `interaction_signal_found=false`，整体 `passed=false`（Backend Agent Debug）。
- 已在 `lan_agents/src/agent/generation_graph/coding_agent/debug_code_with_assets/node.py` 把“缺交互”纳入 `unresolved_issues`，并在修复成功时记录 `Restored player input controls`，避免 Debug Agent 把静态封面页当成已修好（Backend Agent Debug）。
- 已在 `lan_agents/src/agent/generation_graph/validator_agent/validate_final_delivery/node.py` 为运行时失败详情补齐 `player input controls missing`，最终验收会明确拒绝“能画画面但不可交互”的 bundle（Backend Agent Debug）。
- 已同步更新 generation graph mock bundle、validator/coding debug 测试基线，保证通过验收的样例至少具备最小输入控制（Backend Agent Debug）。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_coding_debug.py tests/unit_tests/test_validator_agent.py -q`、`cd lan_agents && .venv/bin/python -m pytest tests/integration_tests/test_generation_graph.py -q`、`cd backend && ../.venv/bin/python -m pytest tests/test_agent_runner.py -q` 通过（Backend Agent Debug）。

### Backend Agent Debug：补齐 game_ready 运行协议兜底 ☑️ 已完成

- 已定位 `game_ready signal missing` 的根因：Validator 拦截是正确的，真正缺口在上游 Coding/Debug 产物协议；真实模型可能生成可渲染、可交互的 `game.js`，但遗漏向父 iframe 发送 `game_ready`（Backend Agent Debug）。
- 已新增 `lan_agents/src/agent/generation_graph/tools/runtime_protocol.py`，提供确定性 `ensure_game_ready_signal()`，在不放宽 Validator 的前提下为 `game.js` 补齐 `window.parent.postMessage({ type: 'game_ready' }, '*')`（Backend Agent Debug）。
- 已在 `draft_code` 阶段和 `debug_code_with_assets` 阶段都接入 ready 兜底；Debug 阶段会记录 `game_ready_signal_missing` 已修复，并在重新运行 runtime check 后清空 unresolved issue（Backend Agent Debug）。
- 已增强 Coding/Debug prompt，明确 `game_js` 初始化完成后必须发送 `game_ready`，降低真实 LLM 继续漏掉运行协议的概率（Backend Agent Debug）。
- 已新增回归测试覆盖 provider 遗漏 ready、Debug 无 LLM 时补 ready，以及 Validator/generation graph 最终验收不放松；已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_coding_agent.py tests/unit_tests/test_coding_debug.py -q`、`cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_validator_agent.py tests/integration_tests/test_generation_graph.py -q` 和 `cd lan_agents && .venv/bin/langgraph validate` 通过（Backend Agent Debug）。

### Backend Agent Debug：避免 suggestions 缺失导致聊天发送失败 ☑️ 已完成

- 已定位“消息发送失败，模型没有返回追问和可点击建议”的根因：DesignPlanner 在 `collecting` 阶段把模型返回 `assistant_message` 或 `suggestions` 缺失视为硬错误，直接抛出 `ProviderError`，没有退回到本地缺字段追问（Backend Agent Debug）。
- 已在 `lan_agents/src/agent/conversation_graph/nodes/_helpers.py` 为 `followup_for_missing_fields()` 补齐每个关键字段的本地建议答案，包含 `title / style / controls / win_condition / lose_condition` 等常见缺口（Backend Agent Debug）。
- 已在 `lan_agents/src/agent/conversation_graph/services/design_planner.py` 改为优先回退到 deterministic follow-up：模型缺 `assistant_message`、缺 `suggestions` 或两者都缺时，不再直接报错，而是基于 `missing_fields` 生成本地追问和可点击建议，并记录 `planner_diagnostics`（Backend Agent Debug）。
- 已在 `backend/app/create_sessions.py` 和 `backend/app/main.py` 增加结构化错误透传；当 provider 真正失败时，后端会返回 `error.details`，携带 `reason / missing_fields / provider_error` 等上下文（Backend Agent Debug）。
- 已在 `frontend/src/api/client.ts` 与 `frontend/src/lib/errors.ts` 接入 `error.details` 解析和弹窗透传，前端 ErrorDialog 现在可以展示详细错误 JSON，而不只是一句总提示（Frontend Step 6.6、Backend Agent Debug）。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_design_planner.py -q`、`cd backend && ../.venv/bin/python -m pytest tests/test_create_sessions.py -q`、`cd frontend && npm run test:api-error-parsing`、`cd frontend && npm run build` 通过（Backend Agent Debug）。

### Backend Artifact Storage：Agent bundle 入库与发布复制 ☑️ 已完成

- 已将 Agent 生成的本地 bundle 上传到对象存储 draft 前缀：`drafts/{user_id}/{job_id}/v1/`，覆盖 `manifest.json / index.html / style.css / game.js / assets/*`，避免前端拿到容器内 `/app/output/...` 本地路径（Backend Artifact Storage）。
- 已让 draft 预览统一走后端 owner-only artifact 代理：`/api/jobs/{job_id}/artifacts/{relative_path}`，job/game 返回 `manifest_url=/api/jobs/{job_id}/artifacts/manifest.json` 与 `artifact_base_url=/api/jobs/{job_id}/artifacts/`，前端可用同源 cookie 读取 draft bundle（Backend Artifact Storage）。
- 已扩展对象存储服务，支持 `get_object / list_object_keys / copy_object`，用于 draft 代理读取和 Publish 复制对象（Backend Artifact Storage）。
- 已在发布 draft 时查找关联的 succeeded generation job；若 job 的 `artifact_prefix` 是 `drafts/`，则复制全部 draft 对象到 `published/{game_id}/v1/`，再将游戏 URL 切换为公开 published 地址（Backend Artifact Storage）。
- 已补齐旧任务保护：如果历史 job 仍保存 `/app/output/...` 绝对本地路径且容器重建后文件已丢失，artifact 代理会直接返回 404，不再误把本地路径拼成 MinIO key 导致黑屏或异常（Backend Artifact Storage）。
- 已补充后端测试覆盖本地 bundle 入库、artifact 代理读取、旧路径 404 和 publish 复制；已验证 `cd backend && ../.venv/bin/python -m pytest -q` 通过，结果为 `108 passed`（Backend Artifact Storage）。

### Frontend Preview Debug：Create 成功态游戏沙盒防止溢出 ☑️ 已完成

- 已定位 Create 成功态“游戏沙盒区域”溢出的根因：当前容器只有基础 `div` 样式，没有像 Play 页那样对内部运行内容做裁切和尺寸约束；一旦放入 iframe、canvas 或图片视频，内容容易顶出面板边界（Frontend Preview Debug）。
- 已在 `frontend/src/pages/create.css` 为 `.preview-frame.preview-sandbox` 增加 `position: relative` 与 `overflow: hidden`，并将内部对齐改为 stretch，保证成功态预览内容始终被裁切在圆角沙盒内（Frontend Preview Debug）。
- 已为成功态沙盒补齐内部内容约束：`iframe` 固定 `width/height: 100%`，`canvas / img / video` 统一限制 `max-width: 100%` 与 `max-height: 100%`，避免实际游戏界面超出范围（Frontend Preview Debug）。
- 已在 `frontend/src/App.tsx` 把 job 详情里的 `manifest_url / artifact_base_url` 映射进当前任务视图，避免轮询后预览字段丢失，Create 成功态可以持续拿到真实 draft 入口（Frontend Preview Debug）。
- 已在 `frontend/src/pages/CreatePage.tsx` 为成功态接入真实 `iframe` 预览，优先使用 `artifact_base_url + index.html`，兜底从 `manifest_url` 派生入口；不再只渲染空白占位 `div`（Frontend Preview Debug）。
- 已定位“Bundle URL 单独打开能跑，但 Create 内嵌白屏”的关键环境差异：右侧预览 iframe 之前使用 `sandbox="allow-scripts"`，会把同源 artifact 页面降成 opaque origin；独立标签页正常的 bundle，在该 sandbox 环境里可能直接白屏（Frontend Preview Debug）。
- 已将 Create 右侧预览 iframe 调整为 `sandbox="allow-scripts allow-same-origin"`，保持脚本可运行的同时恢复同源 artifact 运行环境，避免“独立开页正常、内嵌白屏”的差异（Frontend Preview Debug）。
- 已在 `frontend/src/pages/CreatePage.tsx` 和 `frontend/src/pages/create.css` 为沙盒下方补齐可点击 `Bundle URL` 链接，支持单独打开当前 draft bundle，并保持链接位于沙盒底部（Frontend Preview Debug）。
- 已更新 `frontend/scripts/check-create-layout.mjs`，锁定成功态沙盒必须具备裁切能力和 iframe/canvas 尺寸约束，防止后续回归（Frontend Preview Debug）。
- 已验证 `cd frontend && npm run test:create-layout`、`cd frontend && npm run build` 通过（Frontend Preview Debug）。

### Frontend Step 6.6：Create 成功态重做创建 revision job ☑️ 已完成

- 已修正 Create 右侧成功态 `重做` 链路：前端不再复用 confirmed `create_session` 调用 `POST /api/jobs`，而是基于当前选中任务调用 `POST /api/jobs/{job_id}/revisions` 创建 revision job，避免触发 `Generation job already exists`（Frontend Step 6.6）。
- 已在 `frontend/src/api/jobs.ts` 增加 `createRevisionJob()`，封装 revision job 创建接口和 raw response 调试日志（Frontend Step 6.6）。
- 已在 `frontend/src/App.tsx` 增加重做 revision 建任务链路，创建成功后会立刻把新 job 插入任务列表顶部、切换选中任务并显示 `pending` 初始日志，同时保留 `parent_job_id` 和 `revision_intent`，避免用户误以为按钮无效（Frontend Step 6.6）。
- 已在 `frontend/src/pages/CreatePage.tsx` 为成功态 `重做` 按钮接入真实回调和 `重做中` 状态，防止重复点击（Frontend Step 6.6）。
- 已新增 `frontend/scripts/check-create-redo-revision.mjs` 和 `npm run test:create-redo-revision`，锁定重做必须走 revision API，防止回归到初始生成接口（Frontend Step 6.6）。
- 已验证 `cd frontend && npm run test:create-redo-revision`、`cd frontend && npm run test:create-tasks`、`cd frontend && npm run build` 均通过（Frontend Step 6.6）。

### Backend Preview Debug：修复 draft artifact URL 契约 ☑️ 已完成

- 已定位 `artifact_base_url=null` 的根因：`GET /api/jobs/{job_id}` 只返回了 `artifact_prefix` 和 `manifest_url`，没有序列化 `artifact_base_url`；同时 `manifest_url` 来自 Agent 容器内本地路径 `/app/output/...`，浏览器无法直接访问（Backend Preview Debug）。
- 已新增 owner-only artifact 读取路由 `GET /api/jobs/{job_id}/artifacts/{relative_path}`，从 job 的 `artifact_prefix` 安全读取生成的 `manifest.json / index.html / style.css / game.js / assets/*`，并阻止绝对路径和 `..` 越界访问（Backend Preview Debug）。
- 已将 job 详情中的 `manifest_url` 改为 `/api/jobs/{job_id}/artifacts/manifest.json`，并补齐 `artifact_base_url=/api/jobs/{job_id}/artifacts/`，让前端可以用同源 cookie 读取 draft 产物并拼 iframe 入口（Backend Preview Debug）。
- 已补充 `backend/tests/test_jobs.py::test_job_detail_exposes_browser_accessible_artifact_urls`，覆盖 job 详情 URL 和 artifact 文件读取；已验证 `cd backend && ../.venv/bin/python -m pytest tests/test_jobs.py tests/test_agent_runner.py -q` 通过（Backend Preview Debug）。

### Frontend Debug：打印 Create Job 原始响应 ☑️ 已完成

- 已在 `frontend/src/api/jobs.ts` 打印 `GET /api/jobs`、`POST /api/jobs`、`GET /api/jobs/{job_id}` 和 `GET /api/jobs/{job_id}/logs` 的 raw response，便于在 DevTools Console 里确认后端真实返回了哪些任务、产物和日志字段（Frontend Debug）。
- 已在 `frontend/src/App.tsx` 打印当前选中任务的 raw job、raw logs、UI task 和 preview inputs，包括 `game_id / artifact_prefix / manifest_url / artifact_base_url`，用于定位 succeeded 后预览不显示是字段缺失、前端未映射还是 iframe 未接入（Frontend Debug）。
- 已更新 `frontend/scripts/check-create-tasks.mjs` 锁定 raw response 日志标签，防止后续调试日志被误删（Frontend Debug）。
- 已验证 `cd frontend && npm run test:create-tasks`、`cd frontend && npm run build` 均通过（Frontend Debug）。

### Frontend Publish：Create 成功态发布链路 ☑️ 已完成

- 已在 `frontend/src/api/games.ts` 增加 `publishGame(gameId)`，调用后端 `POST /api/games/{game_id}/publish` 并复用 `toUiGame` 映射返回游戏。
- 已为 Create 任务项补齐 `game_id`，轮询到 `succeeded` 后通过 job 返回的 draft `game_id` 启用发布按钮。
- 已在 `frontend/src/App.tsx` 增加 `handlePublishCreateGame` 和 `publishingGameId`，发布中禁用按钮并显示“发布中”，失败走统一 ErrorDialog。
- 发布成功后更新本地游戏列表、刷新 latest Home 列表、输出 `Publish 成功` Console 日志，并跳转 Home。
- 已新增 `frontend/scripts/check-create-publish.mjs` 与 `npm run test:create-publish`，锁定发布 API、发布按钮接线、发布中状态和成功跳转。

### Backend Agent Debug：打印 runtime check 具体失败原因 ☑️ 已完成

- 已定位 `runtime_check_failed` 只显示泛化原因的根因：`validate_final_delivery` 读取到 `debug_report.runtime_check.passed=false` 后只写入固定文案 `Runtime check did not pass.`，没有把缺 `game_ready`、缺渲染信号、JS 语法错误、缺 canvas、缺 `game.js` 引用等具体字段写入 issue message（Backend Agent Debug）。
- 已定位“每次生成都失败”的环境根因：真实 backend 容器基于 `python:3.12-slim`，镜像内没有 Node.js，而 `run_headless_runtime_check()` 需要执行 `node --check game.js`；这会导致 Validator 在检查真实游戏代码前固定失败（Backend Agent Debug）。
- 已增强 Validator 失败报告：`validation_report.issues[]` 现在会包含 `runtime_details`，`error_message` 会拼出首个失败 issue 的具体 message，例如 `game_ready signal missing; render signal missing`，前端失败弹窗会随 `validation_report` 一起展示完整 JSON（Backend Agent Debug）。
- 已为 backend Docker 镜像安装 `nodejs`，让真实容器中的 Agent Validator 可以执行 JS 语法检查；并对 runtime failure details 去重，避免 `node is unavailable for JS syntax validation` 同时从 `node_available=false` 和 `syntax_error` 重复出现（Backend Agent Debug）。
- 已增强 `LangGraphGenerationRunner`：失败或成功 final state 中的 `agent_logs` 会转成 `AgentRunResult.logs`，后端落库后 Create 页 Agent 日志面板也能显示 `validator_agent` 的具体错误，而不只显示 `finalize_failure started/completed` 生命周期日志（Backend Agent Debug）。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_validator_agent.py tests/integration_tests/test_generation_graph.py -q`、`cd backend && ../.venv/bin/python -m pytest tests/test_agent_runner.py tests/test_jobs.py tests/test_config.py -q` 均通过（Backend Agent Debug）。

### Frontend Step 6.9：Create 进度条映射真实 Agent 节点 ☑️ 已完成

- 已将 Create 右侧生成进度从按 `generation_job.status` 粗粒度硬编码，改为读取 `agentLogs.step` 映射真实 generation graph 六个阶段：`init_generation_context`、`orchestrator`、`coding_agent`、`asset_agent`、`debug_agent`、`validator_agent`（Frontend Step 6.9）。
- 已移除旧的「分析创意 / 生成游戏文件 / 上传产物」三段猜测式文案，改为「初始化生成上下文」「Orchestrator 编排方案」「Coding Agent 生成代码」「Asset Agent 生成素材」「Debug Agent 联调修复」「Validator Agent 验收」等可与日志 step 对齐的节点文案（Frontend Step 6.9）。
- 已将进度百分比改为只按上述六个 Agent 阶段折算：只有阶段真正完成后才累计 `1/6`，运行中的阶段不再预支半步进度；因此进度条会从 `0%` 起步，不会在第二阶段刚开始时直接跳到 `25%`（Frontend Step 6.9）。
- 已新增 `frontend/scripts/check-create-agent-progress.mjs` 与 `npm run test:create-agent-progress`，锁定六阶段节点映射、旧文案移除和 `getJobProgressView(currentJobStatus, agentLogs)` 调用，避免后续回退（Frontend Step 6.9）。
- 已验证 `cd frontend && npm run test:create-agent-progress`、`npm run test:create-layout` 和 `npm run build` 均通过（Frontend Step 6.9）。

### 2026-06-21：重绘总体架构图为脑图式插图

- 已将 README 引用的总体架构图 [architecture-overview.svg](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/images/architecture-overview.svg) 重绘为脑图式布局，改为“中心节点 + 一级分支 + 叶子节点”的结构，减少交叉连线，便于在 Markdown 中直接阅读整体关系（Doc Sync 2026-06-21）。
- 新图聚焦展示 `User Entry`、`Frontend`、`Backend`、`Agents`、`Data & Storage` 五个主分支，并保留本地 Demo 访问端口、核心后端能力、Agent 角色和远端产物存储位置（Doc Sync 2026-06-21）。

### 2026-06-21：拆分独立数据模型文档

- 已将 [design-document.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/design-document.md) 中与数据模型直接相关的内容独立整理为 [data-model.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/data-model.md)，便于 README、接口契约和数据库实现统一引用（Doc Sync 2026-06-21）。
- 已在 README 的“数据模型”小节补充核心模型列表说明，并改为优先引用独立的数据模型文档，而不是只指向整份产品设计文档（Doc Sync 2026-06-21）。
- 已在 [architecture.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/architecture.md) 中补齐 `docs/data-model.md` 的文件职责登记，保持文档清单与仓库现状一致（Doc Sync 2026-06-21）。

### 2026-06-21：将总体架构图改为插图文件

- 已将 README 中无法稳定显示的 Mermaid 架构图替换为仓库内 SVG 插图 [architecture-overview.svg](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/images/architecture-overview.svg)，便于在本地 Markdown 预览和代码托管平台中直接显示（Doc Sync 2026-06-21）。
- 已在 [architecture.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/architecture.md) 中登记 `docs/images/` 文档插图目录，保持文档清单与实际资源一致（Doc Sync 2026-06-21）。

### 2026-06-21：修复上传素材后的重复 AI 回复

- 已定位上传截图后出现两条消息的根因：后端正常记录 `upload_assets` system 消息，但 conversation graph 的 `build_user_response` 会复用上一轮 `assistant_response.message`，导致欢迎语或旧追问被再次包装成新的 assistant 气泡（Agent Step 1.26）。
- 已调整 `update_material_usage`，上传素材只合并 `material_usage.assets`，不再改变对话状态为 `ready_to_confirm`（Agent Step 1.26）。
- 已调整 `build_user_response`，`upload_assets` 事件不再生成追问、不再复用旧欢迎语、不再返回旧 suggestions；方案未完整时返回空 assistant 文案，方案已完整时只保留确认卡片数据（Agent Step 1.26）。
- 已补充 agent 回归测试，覆盖上传事件不能复用 stale assistant 文案；已补充后端回归测试，覆盖空 assistant 文案不会追加到消息历史（Agent Step 1.26）。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest -q`、`cd lan_agents && .venv/bin/langgraph validate`、`cd backend && ../.venv/bin/python -m pytest tests/test_create_sessions.py tests/test_health.py -q` 均通过（Agent Step 1.26）。

### 2026-06-21：修复 LLM provider 配置与错误原因透传

- 已定位聊天发送失败的根因：`OPENAI_COMPATIBLE_BASE_URL=https://www.api4model.com` 会请求到 HTML 页面；改为 `https://www.api4model.com/v1` 后，接口返回明确的 `HTTP 401 Invalid token`，说明当前 key 对该 provider 不可用（Agent Step 1.27）。
- 已更新根目录 `.env`，将 `OPENAI_COMPATIBLE_BASE_URL` 改为 `/v1` endpoint，并移除 `OPENAI_COMPATIBLE_MODEL` 外层引号，减少 Docker Compose 环境解析歧义（Agent Step 1.27）。
- 已调整 `DesignPlanner` 和 OpenAI-compatible provider，后端 alert 会包含 provider 的安全底层原因，例如 HTTP 状态码和服务返回的错误摘要，不再只显示泛化的 provider failed（Agent Step 1.27）。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest -q`、`cd backend && ../.venv/bin/python -m pytest tests/test_create_sessions.py tests/test_health.py -q`，并重建 backend 容器后确认容器内 `/health` 正常（Agent Step 1.27）。

### 2026-06-21：修正 Design Agent “只差一个问题”误报

- 已将 `missing_game_plan_fields` 和 `missing_field_count` 加入 DesignPlanner prompt payload，让模型基于真实缺口数量判断是否可以使用“最后一个问题 / 只差一个”等收尾表达（Agent Step 1.28）。
- 已更新 DesignPlanner system prompt，只有 `missing_field_count == 1` 时才允许使用收尾表达；缺口数量大于 1 时必须说“下一个关键设定”或“先确认其中一项”（Agent Step 1.28）。
- 已增强语气层进度守卫：当缺失字段超过 1 个时，清理模型输出里的“只差一个关键设定 / 最大关键的问题 / 最后一个问题”等误导性说法；即使只剩 1 个字段，也会清理模型自带的“只差一个”夸张表达，但保留系统生成的“最后确认”（Agent Step 1.28）。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest -q`、`cd lan_agents && .venv/bin/langgraph validate`、`cd backend && ../.venv/bin/python -m pytest tests/test_create_sessions.py tests/test_health.py -q` 通过（Agent Step 1.28）。

### 2026-06-21：补齐 Design Agent 对话上下文记忆

- 已定位上下文缺失根因：后端已持久化 `create_session_messages` 并返回给前端展示，但调用 LangGraph 的 `_state_for_graph()` 没有把消息历史传入 state；`ConversationState` 和 DesignPlanner prompt 也没有 `conversation_history` 字段（Agent Step 1.29）。
- 已在 `ConversationState` 增加 `conversation_history`，并在 DesignPlanner prompt payload 中加入裁剪后的最近可见对话历史，模型可读取用户此前回答、AI 追问和上传事件摘要（Agent Step 1.29）。
- 已在 DesignPlanner system prompt 中明确要求结合 `conversation_history` 理解用户已经回答过什么，避免重复追问已明确的信息（Agent Step 1.29）。
- 已修改后端 `handle_create_session_event`，在每次事件调用 graph 前加载当前 session 既有 messages，并以 `role/content` 形式传入 graph；当前新消息仍通过 `user_event` 传入，避免重复进入历史（Agent Step 1.29）。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest -q`、`cd lan_agents && .venv/bin/langgraph validate`、`cd backend && ../.venv/bin/python -m pytest tests/test_create_sessions.py tests/test_health.py -q` 通过（Agent Step 1.29）。

### 2026-06-21：修复模型 suggestions 返回后不展示

- 已定位 raw LLM 返回了 `suggestions` 但界面不展示的两类原因：agent 的建议语义匹配保护对商店/扭蛋玩法动词覆盖不足，可能把“扮演 / 经营 / 抽盲盒 / 集齐”等玩法建议误清空；前端也用 `createSessionSending` 隐藏 suggestions，可能在响应落地但发送状态尚未释放时遮住建议按钮（Agent Step 1.30）。
- 已扩展 `build_user_response` 的 gameplay 建议匹配关键词，保留扮演、经营、整理、抽、集齐等上下文相关建议，同时保留对明显错位建议的清理机制（Agent Step 1.30）。
- 已调整 Create 页 suggestions 展示条件：发送中仍禁用按钮点击，但不再隐藏已经返回的 `assistant_response.suggestions`（Agent Step 1.30）。
- 已补充 agent 回归测试，覆盖商店扭蛋主题的模型 suggestions 不被清空；已更新前端检查脚本，锁定 suggestions 不再被 `createSessionSending` 遮住（Agent Step 1.30）。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest -q`、`cd frontend && npm run test:create-chat-event && npm run build`、`cd backend && ../.venv/bin/python -m pytest tests/test_create_sessions.py tests/test_health.py -q` 通过（Agent Step 1.30）。

### 2026-06-21：移除 suggestions 本地字段匹配过滤

- 已删除 `build_user_response` 中“建议和追问字段不匹配就清空”的本地关键词限制，Design Agent 返回的字符串 suggestions 会直接透传给前端（Agent Step 1.31）。
- 已将原本要求错位建议清空的测试改为保留模型 suggestions，只保留字符串格式、安全响应、stale followup 替换和无本地兜底等约束（Agent Step 1.31）。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_responses.py -q`、`cd lan_agents && .venv/bin/langgraph validate`、`cd frontend && npm run test:create-chat-event && npm run build`、`cd backend && ../.venv/bin/python -m pytest tests/test_create_sessions.py tests/test_health.py -q` 通过；`cd lan_agents && .venv/bin/python -m pytest -q` 当前仍有第二阶段 `coding_agent` 绝对路径检测相关失败，和本次第一阶段 suggestions 变更无关（Agent Step 1.31）。

### 2026-06-21：修复 Design Agent 重复追问已回答字段

- 已定位重复问问题的根因：用户用“可爱明亮的商店风 / 像素风”这类短答回应上一轮风格追问时，deterministic plan 层没有把答案落到 `game_plan.style`；如果模型 patch 也没补该字段，`missing_confirmable_game_plan_fields` 会继续认为风格缺失（Agent Step 1.32）。
- 已在 `DesignPlanner` 增加上一轮追问字段吸收逻辑，根据 `assistant_response.message` 或 `conversation_history` 中最近 assistant 追问识别用户正在回答的必填字段，并把短答写入对应 `game_plan` 字段（Agent Step 1.32）。
- 已补充回归测试，覆盖上一轮追问来自 `assistant_response` 和来自持久化 `conversation_history` 两种场景，确保回答风格后不再把 `style` 视为缺失字段（Agent Step 1.32）。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_design_planner.py tests/unit_tests/test_responses.py tests/unit_tests/test_nodes.py tests/integration_tests/test_conversation_flows.py tests/integration_tests/test_graph.py -q`、`cd frontend && npm run test:create-chat-event`、`cd backend && ../.venv/bin/python -m pytest tests/test_create_sessions.py tests/test_health.py -q` 和 `cd lan_agents && .venv/bin/langgraph validate` 通过（Agent Step 1.32）。

### 2026-06-21：限制 Design Agent 最多五轮追问

- 已将第一阶段提问预算设为最多五轮，使用 `user_requirements.revision_count` 判断当前聊天轮次；第 6 次 chat 起 `should_force_complete_plan=true`，Design Agent 必须停止追问并补全方案（Agent Step 1.33）。
- 已在 `DesignPlanner` prompt payload 中加入 `design_chat_round`、`max_question_rounds` 和 `should_force_complete_plan`，并在 system prompt 明确超过五轮后 `assistant_message` 和 `suggestions` 必须为空，由模型基于已有上下文补全缺失必填字段（Agent Step 1.33）。
- 已增加结构兜底：如果超过五轮后模型仍漏填必填字段，系统会基于已有 `user_requirements / game_plan / user_event` 补齐结构字段、生成 `introduction` 并直接进入 `ready_to_confirm`，避免继续卡在追问 loop（Agent Step 1.33）。
- 已补充回归测试，覆盖超过五轮时 prompt 强制完成、模型补齐后出卡，以及模型漏字段时仍自动完成方案三种场景（Agent Step 1.33）。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_design_planner.py tests/unit_tests/test_responses.py tests/unit_tests/test_nodes.py tests/unit_tests/test_plan_generation.py tests/integration_tests/test_conversation_flows.py tests/integration_tests/test_graph.py -q`、`cd backend && ../.venv/bin/python -m pytest tests/test_create_sessions.py tests/test_health.py -q` 和 `cd lan_agents && .venv/bin/langgraph validate` 通过（Agent Step 1.33）。

### 2026-06-21：修复模型空追问导致无建议按钮

- 已定位“问游戏名但没有 suggestions”的根因：`DesignPlanner` 在 collecting 阶段允许模型返回空 `assistant_message` 和空 `suggestions`，随后 `build_user_response` 会退回本地 `followup_for_missing_fields("title")`；该本地追问固定没有 suggestions（Agent Step 1.34）。
- 已调整 `DesignPlanner` 模型契约：collecting 阶段如果模型没有返回追问和可点击建议，直接抛出 `ProviderError("模型没有返回追问和可点击建议，请重试。")`，不再静默使用本地无建议追问（Agent Step 1.34）。
- 已保留现有“有追问但无 suggestions”错误契约，确保前端要么展示模型返回的 suggestions，要么 alert 明确错误原因（Agent Step 1.34）。
- 已调整默认 `MockLLMProvider` 和 prompt 记录测试 provider，让本地/CI mock 默认返回符合契约的追问和 suggestions；显式空响应测试仍能覆盖错误路径（Agent Step 1.34）。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_design_planner.py tests/unit_tests/test_responses.py tests/unit_tests/test_nodes.py tests/unit_tests/test_plan_generation.py tests/integration_tests/test_conversation_flows.py tests/integration_tests/test_graph.py -q`、`cd backend && ../.venv/bin/python -m pytest tests/test_create_sessions.py tests/test_health.py -q` 和 `cd lan_agents && .venv/bin/langgraph validate` 通过（Agent Step 1.34）。

### 2026-06-21：修复模型追问被 stale 守卫误替换

- 已定位“模型返回胜利条件追问和 suggestions，但前端显示问游戏名且无 suggestions”的根因：`build_user_response._is_stale_followup()` 只按关键词判断，看到模型文案里有“魔女学徒这个角色”且 `game_plan.characters` 已存在，就误判为 stale 角色追问并替换成本地 title 追问（Agent Step 1.35）。
- 已将 stale 判断改为先识别当前 assistant 文案真正追问的字段，再判断该字段是否已存在；同时把“胜利 / 失败 / 操作”等显式追问优先级放到“角色”上下文描述之前（Agent Step 1.35）。
- 已补充回归测试，覆盖模型文案同时提到角色和胜利条件时，必须保留模型的胜利条件追问和四条 suggestions（Agent Step 1.35）。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_design_planner.py tests/unit_tests/test_responses.py tests/unit_tests/test_nodes.py tests/unit_tests/test_plan_generation.py tests/integration_tests/test_conversation_flows.py tests/integration_tests/test_graph.py -q`、`cd backend && ../.venv/bin/python -m pytest tests/test_create_sessions.py tests/test_health.py -q` 和 `cd lan_agents && .venv/bin/langgraph validate` 通过（Agent Step 1.35）。

### 2026-06-21：优化 Design Agent 高效追问策略

- 已在 `DesignPlanner` system prompt 中加入“在最短时间内补齐 `game_plan`”目标，要求模型每轮优先选择信息增益最高的问题，避免把可合并确认的信息拆成多轮（Agent Step 1.36）。
- 已要求模型在一个简短问题中尽量合并相近缺失字段，例如角色目标、胜负条件、操作方式；同时避免变成冗长表单（Agent Step 1.36）。
- 已要求模型返回的 suggestions 尽量覆盖多个缺失字段的组合答案，让用户点一次就能补齐更多方案信息（Agent Step 1.36）。
- 已补充 prompt 回归测试，锁定“最短时间内补齐 `game_plan` / 一次补齐最多缺失字段 / suggestions 覆盖多个缺失字段组合答案”三条提示语约束（Agent Step 1.36）。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_design_planner.py tests/unit_tests/test_responses.py tests/unit_tests/test_nodes.py tests/unit_tests/test_plan_generation.py tests/integration_tests/test_conversation_flows.py tests/integration_tests/test_graph.py -q`、`cd backend && ../.venv/bin/python -m pytest tests/test_create_sessions.py tests/test_health.py -q` 和 `cd lan_agents && .venv/bin/langgraph validate` 通过（Agent Step 1.36）。

### 2026-06-21：移除本地替换模型追问逻辑

- 已删除 `build_user_response` 中基于关键词判断 stale followup 和 optional followup 的本地替换逻辑；模型返回的 `assistant_response.message` 与 `suggestions` 会进入前端响应，不再被替换成固定标题、风格或胜负条件追问（Agent Step 1.37）。
- 已保留 `friendly_design_message` 的轻量语气/icon 包装和错误进度话术清理，但不再由 response 层决定“问什么”；提问质量继续通过 `DesignPlanner` system prompt、模型输出契约和 provider 错误显式暴露来约束（Agent Step 1.37）。
- 已将 response 回归测试改为锁定模型追问透传：即使模型问题看起来重复或涉及可选细节，也不再本地替换；若要优化问题，应调整 prompt 约束而不是 response 节点规则（Agent Step 1.37）。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_responses.py -q`、`cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_design_planner.py tests/unit_tests/test_responses.py tests/unit_tests/test_nodes.py tests/unit_tests/test_plan_generation.py tests/integration_tests/test_conversation_flows.py tests/integration_tests/test_graph.py -q`、`cd backend && ../.venv/bin/python -m pytest tests/test_create_sessions.py tests/test_health.py -q` 和 `cd lan_agents && .venv/bin/langgraph validate` 通过（Agent Step 1.37）。

### 2026-06-21：约束 Design Agent 不重复相似追问

- 已定位“连续问操作/胜负条件、不问标题”的根因：`DesignPlanner` 虽然先用 deterministic fallback 吸收当前用户回答，但发给 LLM 的 prompt 仍按旧 `state.game_plan` 计算缺失字段，导致模型以为角色、胜负、操作仍缺失，继续问相似问题（Agent Step 1.38）。
- 已将 fallback 后的最新 `game_plan` 用于 LLM prompt payload 的 `game_plan / missing_game_plan_fields / missing_field_count`，让模型看到当前轮用户回答后真实剩余缺口（Agent Step 1.38）。
- 已新增 `asked_game_plan_fields` prompt 字段，记录历史 assistant 已追问过的设计字段，并在 system prompt 中明确禁止继续追问语义相同或高度相似的问题；如果用户刚回答过这些字段，模型必须先写入 `game_plan_patch`，再选择新的缺失字段追问（Agent Step 1.38）。
- 已在 system prompt 中明确：当 `title` 仍缺失，且玩法、角色、胜利条件、操作方式中至少两个已明确时，下一轮应优先询问标题，或让 suggestions 给出 2 到 4 个贴合题材的标题选项（Agent Step 1.38）。
- 已增强上一轮多字段追问的短答吸收：按追问字段在文本中的出现顺序吸收多段用户回答，并补充“获胜”作为 `win_condition` 标记，避免“操作和失败条件”这类问题被反向吸收（Agent Step 1.38）。
- 已补充回归测试，覆盖 prompt 使用 fallback 后最新 plan、禁止相似追问、缺标题优先和 asked fields payload；已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_design_planner.py tests/unit_tests/test_responses.py tests/unit_tests/test_nodes.py tests/unit_tests/test_plan_generation.py tests/integration_tests/test_conversation_flows.py tests/integration_tests/test_graph.py -q`、`cd backend && ../.venv/bin/python -m pytest tests/test_create_sessions.py tests/test_health.py -q` 和 `cd lan_agents && .venv/bin/langgraph validate` 通过（Agent Step 1.38）。

### 2026-06-21：让第一阶段 regenerate 调用 LLM

- 已定位“重新生成后简介变化不明显”的根因：`regenerate` 路由直接进入 `regenerate_plan`，旧实现只用本地 `REGENERATE_VARIANTS` 给标题加后缀，并用 `summarize_game_introduction()` 拼固定前缀，没有调用 `DesignPlanner` 或任何 LLM provider（Agent Step 1.39）。
- 已新增 `RegeneratePlanner` 服务，复用现有 `LLMProvider.complete_json()`，在用户点击“换一换/重新生成方案卡片”时请求模型重新生成 `title / introduction / tags`（Agent Step 1.39）。
- 已在 regenerate prompt 中明确：新卡片必须与 `user_requirements / game_plan / material_usage` 保持一致，但标题和简介要明显不同；禁止修改玩法、角色、胜负条件、操作方式和素材用途（Agent Step 1.39）。
- 已将 `regenerate_plan` 节点改为调用 `RegeneratePlanner().regenerate(state)`；真实 provider 可生成新的卡片表达，mock provider 字段不完整时仍保留 deterministic fallback，保证本地和 CI 不因无 key 阻塞（Agent Step 1.39）。
- 已新增 `test_regenerate_planner.py`，覆盖 LLM 卡片变体、prompt 约束和节点 provider 调用；已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_design_planner.py tests/unit_tests/test_regenerate_planner.py tests/unit_tests/test_responses.py tests/unit_tests/test_nodes.py tests/unit_tests/test_plan_generation.py tests/integration_tests/test_conversation_flows.py tests/integration_tests/test_graph.py -q`、`cd backend && ../.venv/bin/python -m pytest tests/test_create_sessions.py tests/test_health.py -q` 和 `cd lan_agents && .venv/bin/langgraph validate` 通过（Agent Step 1.39）。

### 2026-06-21：修复第一轮对话过早生成确认卡

- 已定位根因：`DesignPlanner` 之前会完全信任 LLM 返回的 `game_plan_patch`，导致用户只说“冰雪奇缘的游戏”时，模型自行补齐标题、角色、胜负条件和操作方式，系统误判 `game_plan` 已完整并直接返回确认卡（Agent Step 1.40）。
- 已增加早期出卡门禁：在未超过 5 轮提问预算时，LLM 只能写入用户已明确表达、已有状态、上一轮追问对应字段或安全派生字段；不能替用户凭空决定 title、style、characters、win_condition、lose_condition、controls 等关键字段（Agent Step 1.40）。
- 已保留超过五轮后的自动补全能力：`should_force_complete_plan=true` 时仍允许模型基于上下文补齐缺失字段并生成确认卡（Agent Step 1.40）。
- 已新增回归测试覆盖“第一轮 LLM 过度补全也不能出卡”和“超过五轮后仍可自动补全出卡”；已验证 `LLM_PROVIDER=mock .venv/bin/python` 复现“我想做个冰雪奇缘的游戏”返回 `conversation_status=collecting` 且 `card=null`（Agent Step 1.40）。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_design_planner.py tests/unit_tests/test_responses.py tests/unit_tests/test_nodes.py tests/unit_tests/test_plan_generation.py tests/integration_tests/test_conversation_flows.py tests/integration_tests/test_graph.py -q` 通过，结果为 `58 passed`（Agent Step 1.40）。

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
- Create Sessions API：已新增确认前会话表、素材会话绑定、会话创建、`chat / upload_assets / regenerate / confirm` 事件和会话读取接口（Step 7.1-Step 7.20）。
- Backend Agent 接入：Create Sessions 后端已通过 `conversation_runner` 调用 `lan_agents` 的 `conversation_graph`，并为 backend 容器补齐 `lan_agents/src`、LangGraph 依赖和 LLM/LangSmith 环境变量透传（Backend Agent Step 1）。
- Backend Agent 空白会话修正：Create 自动创建空会话时不再触发 `invalid` 路由，后端会写入可恢复的 assistant 欢迎消息并等待用户首条消息（Backend Agent Step 1）。
- 任务接口：已改造 `POST /api/jobs`，只从 confirmed `create_session` 创建初始生成任务，保存会话快照并返回 `session_id`（Step 8.1-Step 8.8、Step 8.15-Step 8.16）。
- 执行器边界：已实现 fake runner、会话快照输入、后台状态迁移、Agent 日志落库和 draft game 创建，后端创建任务后可自动推进到 `succeeded / failed`（Step 8.9-Step 8.14）。
- Seed 游戏数据：已提供可重复执行的 published 可玩游戏写入，包含真实数据库记录、`published/*` 静态 bundle、public manifest/entry 地址，便于首页和游戏卡片联调（Step 10）。
- 独立 Agent 原型：已新增根目录 `agent/`，可在不接前后端的情况下本地运行 `conversation -> generation -> manifest` 全链路，并产出静态 bundle、校验结果和 provider 配置边界（Agent Prototype Step 1）。
- LangGraph 部署配置：已新增 `agent/langgraph.json`、`agent/my_agent/agent.py` 和 `agent/my_agent/requirements.txt`，可导出真实 `CompiledStateGraph` 并按 LangGraph 平台约定声明依赖与环境变量入口（Agent Prototype Step 1）。
- LangSmith tracing：已在独立 `agent/` 原型中接入 `LANGSMITH_TRACING / LANGSMITH_API_KEY / LANGSMITH_PROJECT / LANGSMITH_ENDPOINT` 配置、graph run metadata 和 runner tracing context（Agent Prototype Step 1）。
- Agent 新框架 Step 1.1：已在 `lan_agents/` 暴露 `conversation` graph，`langgraph.json` 指向 `conversation_graph`，`.env.example` 补齐 LangSmith 变量样例，并验证本地 pytest、graph validate、LangGraph dev server 加载 `graph_id=conversation`、LangSmith metadata 提交和一次 `conversation` run trace（Agent Step 1.1）。
- Agent 新框架 Step 1.2：已在 `lan_agents/src/agent/state.py` 定义第一阶段 `ConversationState`，包含 `user_requirements`、`game_plan`、`material_usage`、`user_event`、`assistant_response`、`handoff_to_generation` 和 `conversation_status`；`material_usage` 保持仅 `assets`，`assistant_response.suggestions` 为列表，并验证 graph 输出包含完整状态字段（Agent Step 1.2）。
- Agent 新框架 Step 1.3-1.5：已新增第一阶段确定性节点、事件路由和条件边 graph，支持 `chat / upload_assets / regenerate / confirm / invalid` 分支；`update_requirements` 可规则化吸收聊天需求、修改约束、偏好画像和素材用途提示（Agent Step 1.3、Agent Step 1.4、Agent Step 1.5）。
- Agent 新框架 Step 1.5a：已将 `lan_agents/src/agent/` 拆为 `conversation_graph/` 和 `generation_graph/` 子图边界，conversation 内部按 `nodes / routes / events` 分层，每个 node 独立目录，顶层 `graph.py` 仅保留 LangGraph 导出兼容（Agent Step 1.5a）。
- Agent 新框架 Step 1.5b：已固化确认卡片门控规则，普通聊天优先追问补齐 `game_plan`，仅当关键字段完整时返回 `assistant_response.card` 和 `generate/regenerate` 动作（Agent Step 1.5b）。
- Agent 新框架 Step 1 完整阶段：已完成第一阶段 `conversation_graph` 的素材用途、安全标签、换一换、确认校验、响应脱敏、fixture、README 和 LangSmith Studio 可见性验证（Agent Step 1.6-Step 1.12）。
- Agent 新框架 Step 1.13：已新增统一 LLM provider 抽象和 `DesignPlanner`，第一阶段只把 `generate_or_refine_plan` 接入 provider，默认 mock 保持确定性，OpenAI-compatible provider 从环境变量读取配置（Agent Step 1.13）。
- Agent 新框架 Step 1.14：已补齐真实 provider 多轮对话链路，支持从根目录或 `lan_agents/` `.env` 读取配置，模型可返回部分 `game_plan`、追问文案和简短建议；未补齐时继续 `collecting`，补齐后进入 `ready_to_confirm` 并返回 card（Agent Step 1.14）。
- Agent 新框架 Step 1.15：已补齐 provider 预检工具和推荐模型样例，第一阶段推荐 `gpt-5.4-mini`，预检只输出 SET/UNSET 与模型名，不泄露 API key 或 base URL（Agent Step 1.15）。
- Agent 新框架 Step 1.16：已新增第一阶段完整对话 demo runner，可打印 `pretty_print_messages`、每轮 agent 日志、最终 `game_plan` 和 card，用于本地验收真实模型追问到确认卡片链路（Agent Step 1.16）。
- Agent 新框架 Step 1.17：已新增 Design Agent 语气 skill，在不改 `assistant_response` schema 的前提下，为追问和确认消息增加亲和语气、单个上下文 icon，并校验建议和追问语义匹配（Agent Step 1.17）。
- Agent 新框架 Step 1.18：已将完整 MVP tag 集合注入 DesignPlanner system prompt，让外部模型明确可选标签，同时继续保留 `normalize_tags` 确定性兜底（Agent Step 1.18）。
- Agent 新框架 Step 1.19：已将 `game_plan.introduction` 改为最终派生字段，Design Agent 不再追问简介，而是在除简介外的关键方案字段完整后自动总结详细介绍并出卡（Agent Step 1.19）。
- Agent 新框架 Step 1.20：已优化 Design Agent 语气层，追问开场会根据当前缺失字段和方案进度动态变化，并清理模型误报“只差一步”的措辞（Agent Step 1.20）。
- Agent 新框架 Step 1.21：已让 Design Agent 语气包装具备幂等性，避免 planner 与 response 节点双层调用时重复出现“我们先把关键设定搭起来”等开场（Agent Step 1.21）。
- Agent 新框架 Step 1.22：已将上一轮 assistant 文案传给 DesignPlanner prompt 并要求模型不要复用，同时在语气层折叠模型正文内重复开场（Agent Step 1.22）。
- Agent 新框架 Step 1.23：已修复追问与建议错位问题，玩法方向问题不再回退到“星星小猫”等标题建议（Agent Step 1.23）。
- Agent 新框架 Step 1.24：已限制 Design Agent 只追问第一阶段必填字段，并拦截“特别能力”等可选细节追问，避免收集 loop 卡住（Agent Step 1.24）。
- Agent 新框架 Step 1.25：已移除本地写死创意建议兜底，建议按钮只接受模型按上下文返回的 suggestions（Agent Step 1.25）。
- Agent 新框架 Step 1.26：已修复上传素材后重复 assistant 气泡问题，`upload_assets` 只更新 `material_usage.assets`，不复用旧欢迎语、旧追问或旧建议（Agent Step 1.26）。
- Agent 新框架 Step 1.27：已修正 OpenAI-compatible base URL 配置，并让 provider 错误向前端透传安全原因；当前 api4model 返回 `Invalid token`，需要替换有效 key 后才能真实生成（Agent Step 1.27）。
- Agent 新框架 Step 1.28：已让 Design Agent 根据真实缺失字段数量判断进度，避免在还缺多个设定时说“只差一个 / 最后一个问题”（Agent Step 1.28）。
- Agent 新框架 Step 1.29：已把会话消息历史传入 conversation graph 和 DesignPlanner prompt，补齐真实多轮上下文记忆（Agent Step 1.29）。
- Agent 新框架 Step 1.30：已修复模型返回 suggestions 后被 agent 误清空或被前端发送状态遮住的问题（Agent Step 1.30）。
- Agent 新框架 Step 1.31：已移除 suggestions 本地字段匹配过滤，模型返回的字符串建议直接进入前端展示（Agent Step 1.31）。
- Agent 新框架 Step 1.32：已修复用户短答上一轮追问时未落盘导致重复追问的问题（Agent Step 1.32）。
- Agent 新框架 Step 1.33：已限制第一阶段最多五轮追问，超过后自动补全方案并出确认卡片（Agent Step 1.33）。
- Agent 新框架 Step 1.34：已禁止模型空追问空建议落入本地无建议追问，保障 collecting 阶段 suggestions 契约（Agent Step 1.34）。
- Agent 新框架 Step 1.35：已修复模型追问被 stale 守卫误判为已回答字段并替换成本地追问的问题（Agent Step 1.35）。
- Agent 新框架 Step 1.36：已要求 Design Agent 用信息增益最高的问题和组合 suggestions 在最短时间内补齐方案（Agent Step 1.36）。
- Agent 新框架 Step 1.37：已移除 response 层本地替换模型追问逻辑，提问优化改由 DesignPlanner prompt 和模型契约约束（Agent Step 1.37）。
- Agent 新框架 Step 1.38：已让 DesignPlanner prompt 使用当前轮 fallback 后的最新方案，并通过 asked fields 和标题优先规则约束模型不重复相似追问（Agent Step 1.38）。
- Agent 新框架 Step 1.39：已让第一阶段 `regenerate` 调用 LLM provider 生成新的确认卡片标题、简介和标签，同时保留核心玩法字段（Agent Step 1.39）。
- Agent 新框架 Step 2：已建立第二阶段 `generation_graph` state、tools、fixture 和 provider smoke 基线；真实 OpenAI-compatible provider 已通过 `generation_provider_smoke` 返回 `{"ok": true, "stage": "generation_provider_smoke", "summary": "ready"}`，并补齐 code fence / 前后缀文本 / 非标准外层 envelope 的 JSON 解析容错（Agent Step 2）。
- 前端 Create Step 6.4：Create 相关后端错误会通过 `window.alert` 弹出后端返回的错误原因，同时保留页面错误状态（Frontend Step 6.4）。
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

### Agent Step 1.1：配置 conversation graph 与 LangSmith ☑️ 已完成

- 已在 `lan_agents/langgraph.json` 中将 `conversation` 映射到 `./src/agent/graph.py:conversation_graph`。
- 已在 `lan_agents/src/agent/graph.py` 暴露可加载的 `conversation_graph`，并保留 `graph` 兼容别名。
- 已在 `lan_agents/.env.example` 中补齐 `LANGSMITH_TRACING`、`LANGSMITH_API_KEY` 和 `LANGSMITH_PROJECT`。
- 已验证 `lan_agents` 本地测试、`langgraph validate`、`langgraph dev` 加载和 LangSmith trace。

### Agent Step 1.2：定义第一阶段 ConversationState ☑️ 已完成

- 已新增 `lan_agents/src/agent/state.py`，定义 `ConversationState` 及默认 state factory。
- 已覆盖第一阶段业务状态：`user_requirements`、`game_plan`、`material_usage`，并补齐 `user_event`、`assistant_response`、`handoff_to_generation`、`conversation_status`。
- 已保持 `material_usage` 只包含 `assets`，避免提前加入第二阶段素材分析字段。
- 已确认 `assistant_response.suggestions` 是 `string[]`，`assistant_response.card` 默认为 `null`，后续由 `game_plan` 派生。
- 已更新 `lan_agents/src/agent/graph.py` 使用 `ConversationState`，当前占位节点会回传完整 state 以便 LangSmith 观测 schema。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_configuration.py tests/integration_tests/test_graph.py -q`、`cd lan_agents && .venv/bin/langgraph validate` 通过，并通过 LangGraph dev run 看到完整 state 字段。

### Agent Step 1.3：实现确定性节点骨架 ☑️ 已完成

- 已新增 `lan_agents/src/agent/nodes.py`，实现 `ingest_user_event`、`update_requirements`、`update_material_usage`、`generate_or_refine_plan`、`regenerate_plan`、`lock_confirmation`、`build_user_response`、`build_error_response`。
- 已保持节点只接收当前 state 并返回局部 state update，不在节点内部手动调用后续节点。
- 已让 `ingest_user_event` 校验 `chat / upload_assets / regenerate / confirm`，非法事件进入安全错误响应。
- 已让 `build_user_response` 输出 `message`、`suggestions`、由 `game_plan` 派生的 `card` 和 `actions`。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests -q` 通过。

### Agent Step 1.4：实现 conversation_graph 条件边 ☑️ 已完成

- 已新增 `lan_agents/src/agent/routing.py`，实现只读路由函数 `route_user_event`。
- 已更新 `lan_agents/src/agent/graph.py`，使用 `StateGraph(ConversationState)` 组装 `START -> ingest_user_event -> conditional_edges` 的第一阶段 graph。
- 已支持 `chat`、`upload_assets`、`regenerate`、`confirm`、`invalid` 五条分支，并分别连接到对应节点和终点。
- 已新增集成测试覆盖五类事件的终态和 `handoff_to_generation`。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/integration_tests -q` 和 `cd lan_agents && .venv/bin/langgraph validate` 通过。

### Agent Step 1.5：完善 update_requirements ☑️ 已完成

- 已让 `chat` 输入合并到 `user_requirements.intent_summary`，并根据关键词更新 `must_have`、`nice_to_have`、`constraints` 和 `preference_profile`。
- 已支持继续补充需求时递增 `revision_count`，并保留已有 `must_have`。
- 已支持用户用 `不要 / 改成 / 换成` 表达修改需求时写入 `constraints`。
- 已支持用户在聊天中提到素材用途时，同步更新已有 `material_usage.assets` 的保守用途。
- 已避免把已回答问题重复写回 `open_questions`。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests -q` 通过。

### Agent Step 1.5a：重构子图目录边界 ☑️ 已完成

- 已将第一阶段实现迁移到 `lan_agents/src/agent/conversation_graph/`，按 `nodes/`、`routes/`、`events/` 分层。
- 已将每个 conversation node 拆成独立目录，例如 `nodes/update_requirements/node.py`，避免继续维护大型扁平 `nodes.py`。
- 已新增 `lan_agents/src/agent/generation_graph/`，作为第二阶段后台生成子图边界；本步骤只预留目录，不实现生成业务。
- 已让 `lan_agents/src/agent/graph.py` 只负责导出 `conversation_graph` 和兼容别名 `graph`，真实编排迁移到 `conversation_graph/graph.py`。
- 已新增 `lan_agents/tests/unit_tests/test_project_structure.py`，约束子图目录和单节点目录结构。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest -q`、`cd lan_agents && .venv/bin/langgraph validate` 通过。

### Agent Step 1.5b：确认卡片门控 ☑️ 已完成

- 已明确第一阶段普通聊天不会每轮都返回确认卡片。
- 已让 `generate_or_refine_plan` 只根据用户已表达的信息更新部分 `game_plan`，不再强行填满标题、介绍、玩法、风格、角色、胜负条件和操作方式。
- 已新增 `missing_game_plan_fields`、`followup_for_missing_fields` 和显式字段抽取 helper，用于判断是否可以展示 card。
- 已让 `build_user_response` 在 `game_plan` 不完整时返回定制追问、简短建议、`card=null`、`actions=[]` 和 `conversation_status=collecting`。
- 已让 `build_user_response` 在 `game_plan` 完整时返回 `card={plan_id,title,introduction,tags}`、`actions=["generate","regenerate"]` 和 `conversation_status=ready_to_confirm`。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest -q` 通过。

### Agent Step 1.6：完善素材用途更新 ☑️ 已完成

- 已让 `update_material_usage` 只写入 `material_usage.assets` 业务数据，并保留安全字段：`asset_id`、`filename`、`mime_type`、`intended_use`、`usage_priority`、`user_hint`、`agent_note`。
- 已避免把 presigned URL、token、对象存储签名或完整密钥写入 state。
- 已覆盖图片、音频、视频、无 `user_hint` 和已有同 asset 更新。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_material_usage.py -q` 通过。

### Agent Step 1.7：完善方案生成和标签集合 ☑️ 已完成

- 已让 `generate_or_refine_plan` 根据 `user_requirements`、显式用户消息和当前 `game_plan` 更新方案字段。
- 已通过 `MVP_TAGS` 限制 `tags` 到 `adventure / action / strategy / puzzle / arcade / survival / simulation / racing / rhythm / roleplay / casual / educational`。
- 已确认非法 tag 会被过滤，空 tag 会回退到 `casual`。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_plan_generation.py -q` 通过。

### Agent Step 1.8：完善换一换方案 ☑️ 已完成

- 已让 `regenerate_plan` 刷新 `game_plan.plan_id` 和可见表达。
- 已通过集成测试确认 `user_requirements.must_have`、`user_requirements.constraints` 和 `material_usage.assets` 不丢失。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/integration_tests/test_conversation_flows.py -q` 通过。

### Agent Step 1.9：完善确认锁定 ☑️ 已完成

- 已让 `lock_confirmation` 在确认前校验 `game_plan` 是否具备标题、介绍、标签、玩法、风格、角色、胜负条件和操作方式。
- 已让 `lock_confirmation` 校验已上传素材都有 `intended_use`。
- 完整时设置 `handoff_to_generation=true` 和 `conversation_status=confirmed`；不完整时保持 `collecting` 并给出用户可读追问。
- 已验证完整方案确认成功、缺少胜负条件失败、素材缺用途失败。

### Agent Step 1.10：完善响应和错误边界 ☑️ 已完成

- 已确认 `assistant_response.card` 只包含 `plan_id`、`title`、`introduction`、`tags`。
- 已确认 `assistant_response.suggestions` 始终是字符串列表。
- 已让错误响应过滤 traceback、secret、token、presigned signature 等敏感内容。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_responses.py -q` 通过。

### Agent Step 1.11：新增 fixture 与 README ☑️ 已完成

- 已新增 `conversation_chat.json`、`conversation_upload_assets.json`、`conversation_regenerate.json`、`conversation_confirm.json`、`conversation_invalid.json` 五类 fixture。
- 已新增 fixture 安全测试，确认不包含真实用户隐私、密钥或完整 presigned URL。
- 已重写 `lan_agents/README.md`，说明本地安装、`langgraph validate`、`langgraph dev`、LangSmith 环境变量和 fixture 使用方式。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_fixtures.py -q` 通过。

### Agent Step 1.12：第一阶段收尾 ☑️ 已完成

- 已更新 `docs/architecture.md`，按短格式记录 `lan_agents/` 新增和变化文件职责。
- 已更新 `docs/progress.md`，记录第一阶段已实现能力、验证命令和 LangSmith 可见性。
- 已更新 `docs/agent-implementation-plan.md`，将 Step 1.6-Step 1.12 标记为完成。
- 已完成最终验证：`cd lan_agents && .venv/bin/python -m pytest -q`、`cd lan_agents && .venv/bin/langgraph validate`、`cd lan_agents && .venv/bin/langgraph dev`。

### Agent Step 1.13：接入第一阶段 LLM provider 边界 ☑️ 已完成

- 已新增 `lan_agents/src/agent/providers/`，提供统一 `LLMProvider`、`ProviderConfig`、`MockLLMProvider` 和 `OpenAICompatibleLLMProvider`。
- 已新增 `lan_agents/src/agent/conversation_graph/services/design_planner.py`，把 `generate_or_refine_plan` 的业务 prompt、schema、LLM patch 合并和 deterministic fallback 收敛到服务层。
- 已让 `generate_or_refine_plan` 只通过 `DesignPlanner` 更新 `game_plan`，路由、需求吸收、卡片门控和确认校验仍保持确定性。
- 已在 `lan_agents/.env.example` 和 `lan_agents/README.md` 中补充 `LLM_PROVIDER`、`OPENAI_COMPATIBLE_API_KEY`、`OPENAI_COMPATIBLE_BASE_URL`、`OPENAI_COMPATIBLE_MODEL` 和 `LLM_TIMEOUT_SECONDS`。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest -q` 通过，当前共 41 个测试。

### Agent Step 1.14：跑通真实 LLM 多轮完善方案链路 ☑️ 已完成

- 已让 `ProviderConfig.from_env()` 支持从当前目录及父目录 `.env` 读取模型配置，避免在 `lan_agents/` 和仓库根目录之间切换时丢失 provider 配置。
- 已扩展 `DesignPlanner` 输出契约，支持模型返回 `assistant_message` 和 `suggestions`；当 `game_plan` 仍缺字段时，Graph 会继续返回定制追问和简短建议。
- 已让 `build_user_response` 优先使用 `DesignPlanner` 写入的追问和建议；只有方案完整时才从 `game_plan` 派生 card。
- 已新增测试覆盖：`.env` 配置加载、模型部分补全继续 collecting、第二轮补齐进入 ready_to_confirm、planner 追问透传。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest -q` 通过，当前共 45 个测试；`cd lan_agents && .venv/bin/langgraph validate` 通过。
- 当前根目录 `.env` 已设置 OpenAI-compatible key、base URL 和 model；真实网络调用还需确认 `LLM_PROVIDER=openai-compatible` 后执行。

### Agent Step 1.15：收敛真实 provider 配置与推荐模型 ☑️ 已完成

- 已新增 `lan_agents/src/agent/providers/preflight.py`，可通过 `cd lan_agents && .venv/bin/python -m agent.providers.preflight` 检查当前 provider 配置。
- 已确认根目录 `.env` 中 `OPENAI_COMPATIBLE_API_KEY`、`OPENAI_COMPATIBLE_BASE_URL` 和 `OPENAI_COMPATIBLE_MODEL` 为 SET，但如果未设置 `LLM_PROVIDER=openai-compatible`，运行时仍会使用默认 mock。
- 已将第一阶段推荐模型写入 `lan_agents/.env.example` 和 `lan_agents/README.md`：`OPENAI_COMPATIBLE_MODEL=gpt-5.4-mini`。
- 已验证预检输出不会打印真实 API key 或 base URL。
- 已给 `build_user_response` 增加建议兜底：真实模型只返回追问、不返回建议时，会按缺失字段补 2 到 4 条简短建议。

### Agent Step 1.16：完整对话 demo runner ☑️ 已完成

- 已新增 `lan_agents/src/agent/conversation_graph/demo.py`，提供 `run_conversation_demo` 和 `pretty_print_messages`。
- demo runner 会多轮调用 `conversation_graph`，记录用户消息、AI 追问、建议、最终 card，以及本地 agent 日志。
- agent 日志为本地验收输出，不改变第一阶段 `ConversationState` 字段，也不替代后端确认后 `agent_logs` 表。
- 已修复真实模型可能漏填 `core_loop` 的问题：当已有 `gameplay` 但缺少 `core_loop` 时，DesignPlanner 会按玩法自动派生核心循环。
- 已修复真实模型重复追问已回答字段的问题：`build_user_response` 会按确定性 `game_plan` 校验模型追问，若追问字段已补齐则切换到当前真正缺失字段。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_conversation_demo.py -q`、`cd lan_agents && .venv/bin/python -m pytest -q` 和 `cd lan_agents && .venv/bin/langgraph validate` 通过。
- 已运行真实 provider demo，输出 `ready_to_confirm`、`actions=["generate","regenerate"]` 和最终 card。

### Agent Step 1.17：Design Agent 亲和语气 skill ☑️ 已完成

- 已新增 `lan_agents/src/agent/conversation_graph/services/tone.py`，统一包装 Design Agent 用户可见消息。
- 已保持 `assistant_response.message` 为 string，不新增 `icon` 字段，避免影响当前前后端契约。
- 已让 collecting 追问带一个合适 icon：如 `✨ / 🎮 / 🎨 / 🧩 / 🏁 / 🐾`，并加入简短鼓励式开场。
- 已让 ready message 改为更亲和的确认文案，同时保留 `actions=["generate","regenerate"]`。
- 已清理模型可能返回的额外 emoji，保证用户可见消息最多一个 icon。
- 已校验模型建议和当前追问字段匹配；例如问美术风格时，会返回风格建议而不是标题建议。

### Agent Step 1.18：向外部模型暴露 MVP 标签集合 ☑️ 已完成

- 已从 `MVP_TAGS` 常量生成 DesignPlanner system prompt 的标签列表，避免 prompt 和确定性过滤规则分叉。
- 当前外部模型可见标签集合为：`action / adventure / arcade / casual / educational / puzzle / racing / rhythm / roleplay / simulation / strategy / survival`。
- 已保留 `normalize_tags` 作为后处理兜底，模型返回非法 tag 时仍会过滤。
- 已新增测试确认 system prompt 包含完整 MVP tag 集合。

### Agent Step 1.19：简介最终派生规则 ☑️ 已完成

- 已将阶段一完整性判断拆分为“可确认字段”和“完整展示字段”：`introduction` 不再作为普通追问项阻塞需求收集。
- 已新增 `summarize_game_introduction`，当标题、标签、玩法、核心循环、风格、角色、胜负条件和操作方式完整后，基于 `user_requirements` 与 `game_plan` 自动总结详细简介。
- 已更新 DesignPlanner prompt，明确外部模型不要向用户追问卡片简介或介绍；简介必须在其他关键字段齐全后总结生成。
- 已新增回归测试覆盖完整方案缺简介时自动补简介并进入 `ready_to_confirm`，以及 response 不再追问用户简介。

### Agent Step 1.20：Design Agent 动态语气修正 ☑️ 已完成

- 已将 `friendly_design_message` 从固定“我已经抓到一些方向啦”改为按缺失字段数量和当前追问类型生成动态开场。
- 已清洗模型输出中“现在只差一个关键点 / 最后一步 / 最后一个问题”等不可靠进度措辞，避免仍缺多个字段时误导用户。
- 已保留单 icon 规则和上下文字段提示，例如围绕标题或角色生成“关于星星小猫”的短提示。
- 已新增语气回归测试覆盖动态开场、去除“只差”误报和不同进度下开场不重复。

### Agent Step 1.21：Design Agent 开场去重 ☑️ 已完成

- 已为 `friendly_design_message` 增加已生成开场识别，消息已经包含动态开场时只保留统一 icon，不再二次追加开场。
- 已新增回归测试覆盖模型已带开场和同一消息连续包装两次的场景，避免再次出现“我们先把关键设定搭起来”重复。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_design_tone.py -q`、`cd lan_agents && .venv/bin/python -m pytest -q` 和 `cd lan_agents && .venv/bin/langgraph validate` 通过。

### Agent Step 1.22：Design Agent 历史文案避复用 ☑️ 已完成

- 已在 DesignPlanner payload 中加入 `previous_assistant_message`，让真实模型能读取上一轮 AI 回复。
- 已更新 DesignPlanner system prompt，要求模型不要复用上一轮完整句子、开场白或追问，并在用户刚回答后承接新答案再换一种说法追问。
- 已在语气层折叠模型正文内部连续重复的动态开场，兜住模型仍输出“开场：开场：正文”的情况。
- 已新增回归测试覆盖 prompt 历史约束和模型正文重复开场折叠。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest -q` 和 `cd lan_agents && .venv/bin/langgraph validate` 通过。

### Agent Step 1.23：Design Agent 建议与追问对齐 ☑️ 已完成

- 已确认 `星星小猫 / 森林快跑 / 滚石大冒险` 来自本地标题建议兜底，不是用户当前题材下的模型输出。
- 已让 `build_user_response` 将“追逐 / 躲避 / 关卡 / 任务 / 冒险”等追问识别为玩法方向问题。
- 已将 gameplay 兜底建议改为“追逐躲避 / 关卡冒险 / 任务挑战”，避免玩法追问下出现旧的小猫标题样例。
- 已收紧玩法建议匹配规则，避免仅包含“冒险”的标题建议被误判为匹配。
- 已新增回归测试覆盖“老鹰抓老鼠 + 像素风 + 追逐躲避/关卡任务”场景。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_responses.py -q`、`cd lan_agents && .venv/bin/python -m pytest -q` 和 `cd lan_agents && .venv/bin/langgraph validate` 通过。

### Agent Step 1.24：Design Agent 可选追问拦截 ☑️ 已完成

- 已确认重复问“特别能力”的根因是模型追问了第一阶段非必填可选细节，用户回答残留建议后仍不能填充必填 `game_plan` 字段。
- 已更新 DesignPlanner prompt，明确 `assistant_message` 只能追问 `title / tags / gameplay / core_loop / style / characters / win_condition / lose_condition / controls` 等必填字段。
- 已要求模型不要追问特别能力、皮肤、道具细节、关卡数量等可选扩展；这些可以融入已有字段，但不能阻塞确认卡片。
- 已在 `build_user_response` 中拦截“特别能力 / 特殊能力 / 技能 / 能力”等 optional followup，改回当前真正缺失字段的确定性追问。
- 已新增回归测试覆盖模型问“老鼠除了跑和跳，还想要哪种特别能力？”时自动替换为必填字段追问。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_responses.py tests/unit_tests/test_design_planner.py -q`、`cd lan_agents && .venv/bin/python -m pytest -q` 和 `cd lan_agents && .venv/bin/langgraph validate` 通过。

### Agent Step 1.25：移除本地写死建议兜底 ☑️ 已完成

- 已移除 `followup_for_missing_fields` 中所有本地写死创意建议，只保留确定当前缺失字段的追问文案。
- 已移除 `build_user_response` 对空 suggestions 的本地补全；模型未返回建议时前端不显示建议按钮。
- 已将错位 suggestions 的处理从“替换成本地写死建议”改为“清空 suggestions”，避免旧样例污染当前上下文。
- 已将 DesignPlanner provider 失败和 collecting 阶段缺少模型 suggestions 改为抛出 `ProviderError`，不再用本地 deterministic 建议掩盖模型契约问题。
- 已让后端 Create Sessions 捕获 conversation graph 异常并返回 502 JSON error，前端可直接 alert 后端返回的错误原因。
- 已更新 DesignPlanner prompt，明确 suggestions 必须由模型根据当前题材、`game_plan` 和 `assistant_message` 生成，不能使用固定模板或测试样例。
- 已将 demo 默认输入从旧的小猫样例改为中性追逐类样例，避免运行示例被误认为产品兜底。
- 已新增根目录 `.dockerignore`，避免 backend 镜像复制 `__pycache__` 或旧 `.pyc` 字节码导致旧建议字符串残留。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest -q`、`cd lan_agents && .venv/bin/langgraph validate`、`cd backend && ../.venv/bin/python -m pytest tests/test_create_sessions.py tests/test_health.py -q` 和 `cd frontend && npm run test:create-chat-event` 通过。

### Agent Step 2：接通第二阶段真实 LLM provider 基线 ☑️ 已完成

- 已新增 `lan_agents/src/agent/generation_graph/state.py`，定义第二阶段 `GenerationState`，覆盖 `job_context`、`development_brief`、`asset_work_order`、`asset_manifest_plan`、`processed_assets`、`debug_report`、`validation_report` 等生成态字段。
- 已在 `lan_agents/src/agent/generation_graph/` 下补齐第二阶段基础目录：`orchestrator/`、`asset_agent/`、`coding_agent/`、`validator_agent/`、`tools/`、`fixtures/`。
- 已新增确定性工具边界占位：`workspace.py`、`asset_registry.py`、`schema_guard.py`、`logging.py`、`path_safety.py`，供后续 Orchestrator / Asset / Coding / Validator 复用。
- 已新增 `generation_confirmed_session.json`，覆盖 image / video / audio / generic file 四类上传素材，并确保 fixture 只保留安全 object key 与本地测试路径。
- 已新增 `agent.generation_graph.tools.provider_smoke`，复用第一阶段 `LLMProvider / OpenAICompatibleLLMProvider` 验证第二阶段真实 provider，不另起一套模型接入层。
- 已增强 OpenAI-compatible 响应解析，支持标准 JSON、```json fenced content、带前缀文本的 JSON，以及 debug 模式下的 raw/content preview；错误摘要保持脱敏，不暴露 key、token、presigned URL 或 traceback。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_generation_state.py tests/unit_tests/test_generation_provider.py -q`、`cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_llm_provider.py tests/unit_tests/test_generation_provider.py -q` 通过。
- 已由用户本机验证 `cd lan_agents && LLM_DEBUG_INVALID_JSON_PREVIEW=true .venv/bin/python -m agent.generation_graph.tools.provider_smoke` 返回 `ok=true`，满足 Step 2 真实 provider smoke 门禁。

### 2026-06-21：实现 Agent Step 3 Orchestrator 并发契约 ☑️ 已完成

- 已新增 `lan_agents/src/agent/generation_graph/orchestrator/planner.py`、`build_parallel_contracts/node.py` 和 `demo.py`，建立第二阶段 Orchestrator 的独立规划器、节点入口和 smoke runner。
- 已让 Orchestrator 产出 `development_brief`、`asset_work_order`、`asset_manifest_plan`、`game_spec` 四份契约，并把本周素材范围收口为三张图：`assets/background.png`、`assets/player.png`、`assets/cover.png`。
- 已把 `asset_manifest_plan` 扩展为可验收的三图合同，覆盖 `runtime_required`、`display_only`、`logical_width`、`logical_height`、`alpha_required`、`background`、`fit`、`derived_from`、`title_source` 等字段。
- 已固化逻辑分辨率约束：`background.png` 为 `1280x720`，`player.png` 为 `256x256` 透明底 `RGBA PNG`；`cover.png` 的旧派生规则已在后续 Agent Step 7 改为独立生成。
- 已加入 deterministic fallback：当真实模型漏掉 `asset_manifest_plan`、`development_brief` 或 `asset_work_order` 时，会基于 confirmed session 和上传素材生成三图最小对齐合同；无上传素材时也会自动规划生成背景图、玩家图和封面图。
- 已把 Orchestrator system prompt 收敛成三图专用契约提示词，只保留并发执行、路径对齐、尺寸、透明底和封面派生约束，减少真实 provider 发散风险。
- 已新增并更新 `tests/unit_tests/test_generation_orchestrator.py`，覆盖三图路径一致、越界路径拒绝、Coding/Asset 并发边界、透明底要求、封面派生规则、无上传 fallback、prompt 收敛和真实模型常见字段别名归一。
- 已增强 `asset_manifest_plan` 归一化：将 `background` 的 `opaque / scene_background / transparent_rgba` 等别名归一为 `scene / transparent`，将 `source` 的 `uploaded_asset / user_uploaded / ai_generated` 等别名归一为 `uploaded / generated / fallback`，将 `kind` 的 `png / sprite_png / background_image` 等别名归一为 `image`。
- 已将三个 MVP target path 的固定合同字段按路径强制归一：`background.png` 不派生、`player.png` 透明底；`cover.png` 的旧派生字段已在后续 Agent Step 7 改为空并独立生成。
- 已补齐 `asset_manifest_plan.source` 与 `asset_work_order` 的对齐逻辑：同一 `target_path` 如来自 uploaded task，会回写为 `uploaded`；来自 generated task，会回写为 `generated`，避免真实模型在 manifest 中自报来源与任务分派不一致。
- 已为 Orchestrator 增加非图片/视频附件参考链路：`image/*` 和 `video/*` 仍进入素材计划；其他附件只作为临时模型参考，用于 `development_brief`、`game_spec`、代码说明书和素材用途解释，不进入 `asset_manifest_plan` 或运行时资源路径。
- 已为 OpenAI-compatible provider 增加 Responses API 附件路径：可读本地参考文件会先以 `purpose=user_data` 上传到 Files API，再以 `input_file` 传给 Responses API，调用结束后尝试删除临时 `file_id`，不长期保存。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_generation_orchestrator.py -q` 通过。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_generation_provider.py tests/unit_tests/test_llm_provider.py -q` 通过。
- 已验证 `cd lan_agents && env LLM_PROVIDER=mock .venv/bin/python -m agent.generation_graph.orchestrator.demo --fixture src/agent/generation_graph/fixtures/generation_confirmed_session.json` 能输出完整三图合同，其中 `player.png` 已带透明底约束；`cover.png` 的旧派生约束已在后续 Agent Step 7 改为独立生成。
- 已将第二阶段 demo 放到 backend 容器内验证真实 provider 路径；已验证 `docker compose exec -T backend sh -lc 'cd /app && python -m agent.generation_graph.orchestrator.demo --fixture /app/lan_agents/src/agent/generation_graph/fixtures/generation_confirmed_session.json'` 成功输出 `development_brief`、`asset_work_order`、`asset_manifest_plan`、`game_spec` 和 `generation_status=planning`。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_generation_orchestrator.py tests/unit_tests/test_generation_state.py tests/unit_tests/test_generation_provider.py tests/integration_tests/test_graph.py -q`、`cd lan_agents && .venv/bin/langgraph validate` 和 backend 容器内 `/health` 通过。

### 2026-06-21：实现 Agent Step 4 Asset Agent 三图本地骨架（待真实图像模型接入）

- 已新增 `lan_agents/src/agent/generation_graph/asset_agent/prompt_builder.py`，为 `background.png` 和 `player.png` 分别生成独立 prompt；fixed prompt 内先声明优秀游戏 UI 设计师 system role，再只放当前图片类型定义。
- 已固定背景图 prompt：`1280x720`、单屏游戏舞台、无 UI、无文字、适合玩法空间。
- 已固定玩家图 prompt：模型生成画布 `1024x1024`、最终导出 `256x256`、单角色完整轮廓、适合 2D sprite，并使用纯品红 `#FF00FF` 幕布方便后处理抠图。
- 已新增 `asset_agent/tools/png_codec.py` 和 `image_processing.py`，在无 Pillow/OpenCV 的本地环境中也能生成可测试 RGBA PNG、读取 PNG 尺寸，并导出透明背景玩家图。
- 已新增 `asset_agent/run_asset_agent/node.py`，实现本地确定性 Asset Agent：写入 `assets/background.png`、`assets/player.png`、`assets/cover.png`，输出 `processed_assets`、`asset_analysis` 和 `asset_notes`。
- 已新增 `asset_agent/demo.py`，支持用 confirmed session fixture 本地跑 Asset Agent smoke。
- 已新增 `tests/unit_tests/test_asset_agent.py`，覆盖背景/玩家 prompt 分离、`#FF00FF` 品红幕布、三图落盘、`player.png` RGBA 透明底和敏感字段不泄漏。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_asset_agent.py -q` 通过。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_generation_orchestrator.py tests/unit_tests/test_asset_agent.py -q` 通过。
- 已验证 `cd lan_agents && .venv/bin/python -m agent.generation_graph.asset_agent.demo --fixture src/agent/generation_graph/fixtures/generation_confirmed_session.json` 能输出三张图路径和 `generation_status=assets_generated`。
- 已验证 `cd lan_agents && .venv/bin/langgraph validate` 通过。
- 当前 Step 4 仍未最终完成：真实图像大模型调用、视频关键帧抽取和 Pillow/OpenCV 生产级后处理尚未接入。

### 2026-06-21：实现 Agent Step 5 Coding Agent 草稿生成 ☑️ 已完成

- 已新增 `lan_agents/src/agent/generation_graph/coding_agent/draft_code/node.py`，实现 Coding Agent 的最小草稿生成节点：调用 LLM 生成 `index.html`、`style.css`、`game.js`，在 `artifact_workspace` 内安全落盘，并派生 `manifest_draft`。
- 已新增 `lan_agents/src/agent/generation_graph/coding_agent/demo.py` 和 `src/agent/generation_graph/fixtures/development_brief.json`，支持按计划中的 `python -m agent.generation_graph.coding_agent.demo --fixture ...` 方式本地 smoke。
- 已补齐 `generation_graph/tools/path_safety.py` 和 `workspace.py` 的最小实现，用于限定写入根目录并统一写 bundle 文本文件。
- Coding Agent 现在会拒绝外网 CDN、远程 URL、secret-like 文本、绝对本地路径以及未出现在 `asset_manifest_plan` 中的 `assets/*` 引用。
- `manifest_draft.assets` 不再信任模型自报，而是从实际 HTML/CSS/JS 代码中的 `assets/*` 引用提取，再与 `asset_manifest_plan.target_path` 对齐生成。
- 已补齐 `code_artifacts.files` 和 `code_artifacts.referenced_asset_paths`，让 Step 6 的 `join_assets_and_code / debug_code_with_assets` 可以直接复用 Coding Agent 的产物路径与资源引用摘要，不需要再次猜测 bundle 结构。
- 已把 `draft_code` 的真实 provider 调用收敛为更稳定的输出模式：提高 token 预算、使用确定性温度、强化 compact/JSON-safe prompt，并对 `invalid JSON` 做一次有限重试；`coding_notes` 也支持 provider 偶发返回单字符串时自动归一为列表。
- 已新增 `tests/unit_tests/test_coding_agent.py`，覆盖四文件落盘、workspace 边界、外链拒绝和合同外资源拒绝。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_coding_agent.py -q` 通过。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_coding_agent.py tests/unit_tests/test_generation_orchestrator.py -q` 和 `cd lan_agents && .venv/bin/langgraph validate` 通过。
- 已验证 `cd lan_agents && env LLM_PROVIDER=mock .venv/bin/python -m agent.generation_graph.coding_agent.demo --fixture src/agent/generation_graph/fixtures/development_brief.json` 能输出 `index.html`、`style.css`、`game.js`、`manifest_draft.json` 的绝对路径和 `generation_status=code_drafted`。
- 已在 backend 容器内完成真实 OpenAI-compatible smoke：`docker compose exec -T backend sh -lc 'cd /app && LLM_TIMEOUT_SECONDS=120 python - <<... draft_code(state) ...'` 成功返回 `generation_status=code_drafted`，并确认输出 `index.html / style.css / game.js / manifest_draft.json` 四类文件摘要、`referenced_asset_paths` 和 `manifest_title`。
- 已额外确认 `docker compose exec -T backend sh -lc 'cd /app && python -m agent.generation_graph.tools.provider_smoke'` 返回 `{\"ok\": true, \"stage\": \"generation_provider_smoke\", \"summary\": \"ready\"}`，说明容器内 provider 基线正常。

### Backend Agent Debug：validation_report 错误弹窗 ☑️ 已完成

- 已在 `GenerationJob` 增加 `validation_report` JSON 字段，并新增 `0005_job_validation_report` 迁移。
- 已让 `LangGraphGenerationRunner` 在最终状态失败时保留 `validation_report`，后台任务失败后写入 job。
- 已让 `GET /api/jobs` 和 `GET /api/jobs/{job_id}` 返回 `validation_report`，前端轮询失败任务时可拿到完整报告。
- 已扩展 Create 任务类型、Jobs 客户端、错误弹窗数据结构和 ErrorDialog，任务失败时通过 error 弹窗展示完整格式化 JSON。
- 已新增 `check-validation-report-error.mjs` 静态检查，覆盖 `validation_report` 字段、详情弹窗和失败标题。
- 已验证 `.venv/bin/pytest backend/tests/test_agent_runner.py -k "validation_report or status_flow" -v`、`.venv/bin/pytest backend/tests/test_migrations.py -v`、`.venv/bin/pytest backend/tests -q`、`node frontend/scripts/check-validation-report-error.mjs` 和 `npm --prefix frontend run build` 通过。

### Frontend Step 6.4：Create 后端错误 alert ☑️ 已完成

- 已新增 `alertCreateBackendError`，Create 任务历史、会话创建、会话恢复和聊天发送的后端错误会调用 `window.alert`。
- alert 内容使用 `createUserError` 从 `ApiError.message` 提取的后端错误原因，不额外写死替代原因。
- 已确认后端 Agent 错误会以 JSON error 返回，前端 `parseApiError` 会保留 `error.message` 并在 Create 发送失败时 alert。
- 已保留原有页面错误状态与 Console 输出，alert 只作为用户即时反馈。
- 已清空 frontend mock runtime 中写死的 suggestions，避免 mock 模式展示非模型生成建议。
- 已更新 `check-create-chat-event.mjs` 覆盖 alert 约束。
- 已验证 `cd frontend && npm run test:create-chat-event`、`npm run test:create-session-state` 和 `npm run build` 通过。

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

### Step 7.1：为 Create Sessions 表编写迁移测试 ☑️ 已完成

- 已在 `backend/tests/test_migrations.py` 中新增 `create_sessions` 表结构测试。
- 测试覆盖字段、索引、`users.user_id` 外键、`confirmed_at` 可空，以及 `collecting / ready_to_confirm / confirmed / error` 状态约束。
- 已将 Alembic SQL 输出检查扩展到 `CREATE TABLE create_sessions`。
- 已验证红灯：`.venv/bin/pytest backend/tests/test_migrations.py -k create_sessions -v` 失败原因指向 `create_sessions` 表和迁移 SQL 尚不存在。

### Step 7.2：实现 Create Sessions 表迁移 ☑️ 已完成

- 已在 `backend/app/models.py` 中新增 `CreateSession` 模型，并关联到 `User.create_sessions`。
- 已新增 `backend/migrations/versions/0003_create_sessions.py`，创建 `create_sessions` 表、状态 check constraint、用户外键和 `user_id/status/created_at/updated_at` 索引。
- 已保持 `user_requirements`、`game_plan`、`material_usage`、`assistant_response` 为 JSON 字段，`confirmed_at` 允许为空。
- 已验证 `.venv/bin/pytest backend/tests/test_migrations.py -k create_sessions -v` 通过。

### Step 7.3-Step 7.4：实现 uploaded_assets 会话绑定 ☑️ 已完成

- 已在 `backend/tests/test_migrations.py` 中新增 `uploaded_assets.session_id` 迁移测试，覆盖 nullable、外键和索引。
- 已在 `backend/app/models.py` 中为 `UploadedAsset` 增加 nullable `session_id`，关联 `create_sessions.id`，并保留既有 `job_id` 任务绑定。
- 已在 `backend/migrations/versions/0003_create_sessions.py` 中补齐 `uploaded_assets.session_id` 列、外键和索引。
- 已验证 `.venv/bin/pytest backend/tests/test_migrations.py -k uploaded_assets_session -v` 通过。

### Step 7.5-Step 7.20：实现 Create Sessions API ☑️ 已完成

- 已新增 `backend/app/create_sessions.py`，实现 `POST /api/create-sessions`、`POST /api/create-sessions/{session_id}/events` 和 `GET /api/create-sessions/{session_id}`。
- 已在 `backend/app/main.py` 挂载 Create Sessions router，并对创建、事件和读取接口接入登录/owner 权限。
- 已通过后端 conversation runner 调用 `lan_agents.conversation_graph` 生成 `user_requirements`、`game_plan`、`material_usage` 和 `assistant_response`，其中游戏卡片只从 `game_plan.plan_id/title/introduction/tags` 派生。
- 已实现 `chat` 更新需求和方案、`upload_assets` 只更新 `material_usage.assets`、`regenerate` 保留需求和素材用途并刷新方案、`confirm` 标记 `confirmed` 并返回 `handoff_to_generation=true`。
- 已确保 `confirm` 不创建 `generation_job`，后台生成仍由后续 Jobs API 改造承接。
- 已新增 `backend/tests/test_create_sessions.py`，覆盖登录保护、跨用户素材拒绝、事件校验、建议答案、换一换、确认和会话恢复。
- 已验证 `.venv/bin/pytest backend/tests/test_create_sessions.py -v`、`.venv/bin/pytest backend/tests/test_migrations.py -k "create_sessions or uploaded_assets_session" -v`、`.venv/bin/pytest backend/tests/test_uploads.py backend/tests/test_jobs.py -q` 通过。

### Backend Agent Step 1：接入真实 lan_agents conversation graph ☑️ 已完成

- 已新增 `backend/app/conversation_runner.py`，作为后端调用 `lan_agents` `conversation_graph` 的唯一边界，负责 lazy import、状态归一和卡片投影兜底。
- 已将 `backend/app/create_sessions.py` 从本地 deterministic `_build_plan/_build_response` 改为调用 `conversation_runner.run_conversation_graph`，创建会话和事件处理都走同一 graph state。
- 已保留后端侧权限、owner 素材校验和 `uploaded_assets.session_id` 绑定，Agent 只负责更新 `user_requirements`、`game_plan`、`material_usage`、`assistant_response`、`conversation_status` 和 `handoff_to_generation`。
- 已调整 `backend/Dockerfile` 与 `docker-compose.yml`，让 backend 镜像复制 `lan_agents/src`，设置 `PYTHONPATH=/app:/app/lan_agents/src`，并透传 `LLM_PROVIDER`、`OPENAI_COMPATIBLE_*`、`LANGSMITH_*`、`LAN_AGENTS_SRC_PATH`。
- 已在 `backend/requirements.txt` 增加 `langgraph` 依赖，并在 `.env.example` 补齐后端调用真实 Agent 所需环境变量。
- 已新增测试断言 Create Sessions API 会使用配置的 conversation graph，而不是继续走本地 stub。
- 已修复空白 Create 会话误触发 `invalid` 路由的问题：无 `initial_message` 且无素材时，`POST /api/create-sessions` 直接创建空白 `collecting` 会话，不调用 graph、不写入错误消息，等待用户首条输入。
- 已新增空白会话回归测试，验证 `assistant_response.message` 和 `messages[0]` 都保存“您好呀，今天想要尝试做个什么样的游戏呢✨？”，避免欢迎语只存在于前端临时 UI。

### Step 7.21：为 Create Session 消息历史编写迁移测试 ☑️ 已完成

- 已在 `backend/tests/test_migrations.py` 中新增 `create_session_messages` 表结构测试。
- 测试覆盖 `session_id`、`role`、`content`、`payload`、`created_at` 字段，`create_sessions.id` 外键，`user / assistant / system` role 约束，以及 `session_id / created_at` 查询索引。
- 已验证红灯：`.venv/bin/pytest backend/tests/test_migrations.py -k create_session_messages -v` 失败原因指向 `create_session_messages` 表尚不存在。

### Step 7.22：实现 Create Session 消息历史表 ☑️ 已完成

- 已在 `backend/app/models.py` 中新增 `CreateSessionMessage` 模型，并通过 `CreateSession.messages` 建立会话消息关系。
- 已在 `backend/migrations/versions/0003_create_sessions.py` 中新增 `create_session_messages` 表，包含 `session_id` 外键、`role` check constraint、`payload` JSON、`created_at` 和查询索引。
- 已扩展 Alembic SQL 测试，确认升级 SQL 会创建 `create_session_messages` 表。
- 已验证 `.venv/bin/pytest backend/tests/test_migrations.py -v`、`.venv/bin/pytest backend/tests/test_create_sessions.py -v` 和 `.venv/bin/pytest backend/tests -q` 通过。

### Step 7.23：为 Create Session 消息写入编写测试 ☑️ 已完成

- 已在 `backend/tests/test_create_sessions.py` 中新增消息历史写入测试，覆盖带 `initial_message` 创建会话、`chat` 事件追加用户和 AI 消息、`upload_assets / regenerate / confirm` 事件追加可回看的事件消息。
- 已断言响应包含 `messages`，消息按时间正序返回，AI 消息 payload 保存建议答案、卡片快照和 actions。
- 已断言上传素材消息只保存安全元信息，不回传完整 presigned URL 签名或 `object_key` 中的敏感片段。
- 已验证红灯：`.venv/bin/pytest backend/tests/test_create_sessions.py -k session_messages -v` 失败原因指向响应缺少 `messages`。

### Step 7.24：实现 Create Session 消息写入和返回 ☑️ 已完成

- 已在 `backend/app/create_sessions.py` 中实现 `CreateSessionMessage` 写入和序列化，`POST /api/create-sessions`、`POST /api/create-sessions/{session_id}/events`、`GET /api/create-sessions/{session_id}` 都返回按时间正序排列的 `messages`。
- 已让 `chat` 事件写入用户消息和 AI 消息；`upload_assets / regenerate / confirm` 写入 system 事件消息，并继续追加最近一轮 AI 回复。
- 已保持 `assistant_response` 只代表最近一轮 AI 回复，完整聊天气泡以 `messages` 为准；Agent 状态事实来源仍是 `user_requirements`、`game_plan` 和 `material_usage`。
- 已验证 `.venv/bin/pytest backend/tests/test_create_sessions.py -k session_messages -v`、`.venv/bin/pytest backend/tests/test_create_sessions.py -v`、`.venv/bin/pytest backend/tests/test_migrations.py -v` 和 `.venv/bin/pytest backend/tests -q` 通过。

### Step 7：实现 Jobs API 基础 ☑️ 已完成

- 已新增 `backend/app/jobs.py`，实现 `POST /api/jobs`、`GET /api/jobs`、`GET /api/jobs/{job_id}` 和 `GET /api/jobs/{job_id}/logs`。
- 已对创建任务接入登录保护，并创建 `pending` 状态任务。
- 已限制单任务最多绑定 5 个素材，并校验所有 `asset_id` 必须属于当前用户；创建成功后会把素材绑定到任务。
- 已将任务列表限制为当前用户，并按 `created_at` 倒序返回；详情和日志仅 owner 可读。
- 已对任务日志按时间正序返回，并在响应前脱敏敏感文本与 presigned URL 签名。
- 已新增 `backend/tests/test_jobs.py`，覆盖登录保护、创建成功、素材归属、数量限制、列表详情权限和日志脱敏。
- 已验证 `pytest backend/tests/test_jobs.py -q` 与 `pytest backend/tests -q` 通过。

### Step 8：接入 Agent Runner 边界 ☑️ 已完成

- 已在 `backend/app/models.py` 和 `backend/migrations/versions/0003_create_sessions.py` 中为 `generation_jobs` 增加 `create_session_id`、`parent_job_id`、`revision_intent`、`user_requirements`、`game_plan`、`material_usage`，并建立会话和父任务索引（Step 8.1-Step 8.2）。
- 已将 `POST /api/jobs` 改为只接收 confirmed `session_id` 和可选 `prompt`，后端从 owner 的 `create_session` 读取快照创建任务，不信任前端提交的 `game_plan/material_usage`（Step 8.3-Step 8.4）。
- 已实现会话权限和重复创建规则：非 owner 或未 confirmed 会话不能创建任务；同一个 confirmed session 只能创建一个初始生成 job，后续修改由 revision job 承接（Step 8.5-Step 8.6）。
- 已实现素材绑定规则：任务创建时从 `material_usage.assets` 解析素材，校验素材属于当前用户且已绑定当前 session，最多 5 个，创建后写入 `uploaded_assets.job_id` 并保留 `session_id`（Step 8.7-Step 8.8）。
- 已更新 `AgentRunInput`，加入 `session_id`、`user_requirements`、`game_plan`、`material_usage`；`confirmation` 仅作为从 `game_plan` 派生的兼容快照（Step 8.9-Step 8.10）。
- 已保留 fake runner、后台状态迁移、Agent 日志落库和 draft game 创建，创建任务后可自动推进到 `succeeded / failed`（Step 8.11-Step 8.14）。
- 已让 `GET /api/jobs` 和 `GET /api/jobs/{job_id}` 返回 `session_id`、`parent_job_id`、任务快照和产物信息，用于前端点击历史任务恢复对应 Create 对话（Step 8.15-Step 8.16）。
- 已新增 `POST /api/jobs/{job_id}/revisions`，只允许 owner 基于 `succeeded / failed` 任务创建 revision job；`pending / running` 返回 409，新 job 保留原 `create_session_id` 和快照，写入 `parent_job_id` 与 `revision_intent`，不覆盖旧 job 或旧 draft（Step 8.17-Step 8.18）。
- 已新增和更新 `backend/tests/test_jobs.py`、`backend/tests/test_agent_runner.py`、`backend/tests/test_migrations.py` 覆盖会话创建任务、快照落库、素材绑定、Runner 输入、状态流、draft 关联和查询字段。

### Step 9：实现 Publish API ☑️ 已完成

- 已新增 `POST /api/games/{game_id}/publish`，游客返回 401，非 owner 看不到别人的 draft，owner 只能发布自己的 draft，非 draft 重复发布返回 409（Step 9.1-Step 9.2）。
- 已实现发布时将 draft 元信息切换到 `published/{game_id}/v1/` public URL，更新 `manifest_url`、`artifact_base_url`，并移除 draft presigned query；当前为后端契约级路径转存，不在本 Step 真实复制对象内容（Step 9.3-Step 9.4）。
- 已实现发布状态更新：`status=published`、写入 `published_at`，保留 draft 的标题、简介、标签和封面元信息；发布后游戏进入 `GET /api/games` 列表，且不新增发布后 meta 编辑接口（Step 9.5-Step 9.6）。
- 已新增 `backend/tests/test_publish.py`，覆盖发布权限、public URL、发布后列表可见和无 meta 编辑接口。
- 已验证 `.venv/bin/pytest backend/tests/test_publish.py -v` 通过，结果为 `3 passed`。

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
- 已实现 `python3 -m app.runner conversation --input fixtures/sample_request.json`，可从 prompt 产出游戏卡片和结构化对话状态。
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

### 2026-06-21：拆分 Create 任务状态与会话状态

- 已新增 `frontend/src/api/create-sessions.ts`，封装 `POST /api/create-sessions` 新建会话和 `GET /api/create-sessions/{session_id}` 读取旧会话（Frontend Step 6.2）。
- 已在 `frontend/src/App.tsx` 拆分 `selectedTaskId`、`selectedCreateSessionId`、`currentJobStatus`、`createSession` 和 `isConversationLocked`，点击历史任务通过 `task.session_id` 恢复旧会话，`+ 新建任务` 才创建新会话（Frontend Step 6.2）。
- 已在 `frontend/src/pages/CreatePage.tsx` 优先使用 `createSession.messages` 渲染聊天气泡，并用 `assistant_response.card/suggestions` 渲染当前卡片和建议；`pending/running` 时禁用输入、上传、建议、确认和重新生成（Frontend Step 6.2）。
- 已在 `frontend/src/mock/runtime.ts` 补齐 mock create session、任务 `session_id` 和消息历史，方便后端消息历史未完全落地前验证前端状态模型（Frontend Step 6.2）。
- 已新增 `frontend/scripts/check-create-session-state.mjs` 与 `npm run test:create-session-state`，锁定任务 ID 与会话 ID 分离、历史任务 GET 恢复和新建任务 POST 创建的边界（Frontend Step 6.2）。

### 2026-06-21：接入 Create 第一阶段聊天发送

- 已在 `frontend/src/api/create-sessions.ts` 新增 `sendCreateSessionEvent()`，封装 `POST /api/create-sessions/{session_id}/events` 的 `chat / upload_assets / regenerate / confirm` 事件入口（Frontend Step 6.3）。
- 已在 `frontend/src/App.tsx` 接入第一阶段 `chat` 发送处理：校验空输入、锁定态和 `collecting / ready_to_confirm` 状态，发送中禁用重复提交，成功后用响应更新 `createSession.messages`、`assistant_response` 和 suggestions（Frontend Step 6.3）。
- 已在 `frontend/src/pages/CreatePage.tsx` 为发送按钮和 textarea Enter 绑定发送逻辑，`Shift+Enter` 保持换行；建议按钮保持只回填输入框，不自动发送（Frontend Step 6.3）。
- 已调整 `frontend/src/pages/CreatePage.tsx` 的发送体验：发送动作触发后立即清空输入框，接口失败时再恢复原文本，避免发送中残留刚输入的提示词（Frontend Step 6.3）。
- 已在 `frontend/src/mock/runtime.ts` 补齐 mock `chat` 事件，追加用户消息和 AI 消息，方便 mock 模式验证对话刷新（Frontend Step 6.3）。
- 已在 `frontend/src/pages/CreatePage.tsx` 和 `frontend/src/pages/create.css` 将用户消息行调整为右侧头像布局：优先展示当前用户 `avatar_url`，无头像时使用淡紫色文字占位；AI 消息仍保持左侧布局（Frontend Step 6.3）。
- 已在 `frontend/src/pages/create.css` 将聊天气泡最大宽度限制为对话框的 `2/3`，并为用户消息头像与气泡保留明确间距（Frontend Step 6.3）。
- 已在 `frontend/src/pages/create.css` 为聊天滚动区增加右侧安全内边距，并将滚动条细化为 `6px`，避免滚动条压住右侧用户头像（Frontend Step 6.3）。
- 已在 `frontend/src/App.tsx` 为用户发送消息增加本地 optimistic 气泡，按下 Enter 或点击发送后立即显示用户发言；接口成功后再以服务端 `messages` 替换（Frontend Step 6.3）。
- 已在 `frontend/src/App.tsx` 将第一阶段聊天发送改为“立即 user、延迟 thinking”：用户消息先本地乐观显示，若请求超过 `2s` 仍未返回才插入 AI `思考中...` 占位；请求返回后统一以服务端 `messages` 替换，请求失败则清理临时消息（Frontend Step 6.3）。
- 已在 `frontend/src/pages/CreatePage.tsx` 为消息流补上自动滚底：无论是用户本地气泡还是延迟出现的 AI `思考中...` 占位，都能在插入时自动滚到最底部（Frontend Step 6.3）。
- 已在 `frontend/src/components/TopNav.tsx`、`frontend/src/pages/CreatePage.tsx`、`frontend/src/styles.css` 和 `frontend/src/pages/create.css` 将默认用户头像统一为紫色渐变圆头像，并显示用户昵称或邮箱前缀首字；默认头像已移除实心紫色 fallback，紫色渐变透明度与 AI 头像保持一致（Frontend Step 6.3）。
- 已移除 Create 聊天区空消息时的“正在准备对话 / 开始对话”占位渲染；没有消息时保持聊天流为空，只保留恢复中和错误态提示（Frontend Step 6.3）。
- 已将 Create 左侧任务列表默认状态改为折叠，保留点击“任务列表”后展开历史任务与新建任务入口的交互（Frontend Step 6.3）。
- 已修正建议答案展示条件：发送中无论最后一条临时消息是用户气泡还是延迟出现的 AI `思考中...` 占位，上一轮 suggestions 都会立即隐藏，等待 AI 新回复返回后再展示新 suggestions（Frontend Step 6.3）。
- 已新增 `frontend/scripts/check-create-chat-event.mjs` 与 `npm run test:create-chat-event`，锁定 `/events` 客户端、按钮发送、Enter 发送、发送中禁用和建议只回填的边界（Frontend Step 6.3）。
- 已验证 `cd frontend && npm run test:create-chat-event`、`npm run test:create-suggestions`、`npm run test:create-session-state`、`npm run test:create-confirm-card` 和 `npm run build` 均通过（Frontend Step 6.3）。
- 已验证 `cd frontend && npm run test:create-session-state`、`npm run test:create-tasks`、`npm run test:create-suggestions`、`npm run test:create-confirm-card` 和 `npm run build` 均通过（Frontend Step 6.2）。

## 尚未落地或需补齐的边界

- 后端尚未实现真实生成产物落盘、Publish API 和端到端生成闭环。
- 后端 Jobs API 仍需补齐 revision job 创建契约，支撑生成后修改；初始生成任务已返回 `session_id` 并可定位旧会话。
- 前端已完成页面与路由骨架，但尚未全面接通 Home、Create、Play 与后端真实业务数据链路；Create 页面仍需继续完成第一阶段 `confirm` 动作、Step 6.6 的创建任务调用、任务轮询和 revision 入口交互。
- Agent 仍需补齐生成后修改的 `revision_graph` 或 revision mode 最小契约，确保生成后聊天修改不混入第一阶段 `conversation_graph`。
- `frontend/vite.config.ts`、`frontend/vite.config.js` 和 `frontend/vite.config.d.ts` 当前存在职责重叠，后续推进 Step 8.1 时应统一配置来源。
- 后续实施计划需按前端、后端、Agent 三端拆分，并以接口契约保证并行开发一致性。
- 独立 `agent/` 原型当前优先使用本地 Graph 兼容层；真实 `langgraph` 包安装仍受当前会话网络/审批环境限制，后续拿到依赖后可切换到真实包验证。
- 独立 `agent/` 原型尚未接回 `backend/app/agent_runner.py`，目前只作为本地调试和工作流验证入口。

## 文档一致性更新记录

### 2026-06-21：统一 Create 任务/会话联动与生成后修改契约

- 已确认新模型不会推翻现有 Create Sessions 架构；它补齐的是 `generation_job -> create_session` 的反查关系，以及生成后 revision loop 的独立边界。
- 已统一 `POST /api/create-sessions` 与 `GET /api/create-sessions/{session_id}` 的职责：前者只创建新对话，后者只读取旧对话；历史任务切换必须通过 `job.session_id` 读取旧会话。
- 已补充完整聊天气泡恢复契约：后端需要 `create_session_messages` 或等价 `messages` 历史；`assistant_response` 只代表最近一轮 AI 回复。
- 已更新 [design-document.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/design-document.md)，明确创建链路由 `create_session` 驱动，生成执行由 `generation_job` 驱动，生成后修改进入 revision mode / revision graph 并创建新 revision job。
- 已更新 [api-contract.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/api-contract.md)，要求 `POST /api/jobs`、`GET /api/jobs` 和 `GET /api/jobs/{job_id}` 返回或保留 `session_id`，并新增 `POST /api/jobs/{job_id}/revisions` 后续版本契约。
- 已更新 [pages-design.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/pages-design.md)，修正旧的“确认卡片可直接编辑”口径，改为聊天驱动 `game_plan` 修改；同时明确 `pending / running` 锁定和 `succeeded / failed` 进入 revision 入口。
- 已更新 [frontend-implementation-plan.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/frontend-implementation-plan.md)，将 Frontend Step 6.2-Step 6.8 改为 `selectedTaskId / selectedCreateSessionId / currentJobStatus / isConversationLocked` 模型。
- 已更新 [backend-implementation-plan.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/backend-implementation-plan.md)，补齐 Jobs 查询返回 `session_id`、revision 字段迁移和 revision job 最小契约步骤。
- 已更新 [agent-orchestration-design.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/agent-orchestration-design.md) 和 [agent-implementation-plan.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/agent-implementation-plan.md)，明确 `revision_graph` 独立于第一阶段 `conversation_graph`。

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

### 2026-06-21：完成 Frontend Step 6.4 文件上传与素材绑定

- 已新增 `frontend/src/api/uploads.ts`，封装 `POST /api/uploads/presign`、对象存储 `PUT` 直传、`POST /api/uploads/complete` 和 20MB 前端限制常量（Frontend Step 6.4）。
- 已将 Create 附件选择从本地文件名展示升级为上传状态：超过 20MB 的文件直接显示失败；可上传文件进入“上传中”；上传完成后通过 `upload_assets` 事件绑定到当前 `create_session`，并从 `material_usage.assets` 渲染为“已绑定”（Frontend Step 6.4）。
- 已在 `frontend/src/App.tsx` 串起 `presign -> PUT -> complete -> sendCreateSessionEvent(type="upload_assets")`，成功后更新会话、素材列表和 Console 摘要；失败时保留当前会话并展示可重试错误（Frontend Step 6.4）。
- 已更新 mock Create Session 运行时，支持 `upload_assets` 事件写入 `material_usage.assets` 和 system 消息，便于本地 mock 模式验证附件绑定（Frontend Step 6.4）。
- 已在 `frontend/src/pages/CreatePage.tsx` 过滤 `upload_assets` system 消息，上传素材不再显示为 AI 聊天气泡，前端仅通过附件列表展示“已绑定”（Frontend Step 6.4）。
- 已新增 `frontend/scripts/check-create-upload-assets.mjs` 和 `npm run test:create-upload-assets`，并验证 `npm run test:create-upload-assets`、`npm run test:create-chat-event`、`npm run test:create-layout`、`npm run build` 均通过（Frontend Step 6.4）。

### 2026-06-21：打通 Create 重新生成方案返回链路

- 已确认“点击重新生成像没反应”的根因不在按钮是否发出 `regenerate` 请求，而在于后端返回的新方案对用户可见字段变化太弱，叠加前端当前的卡片替换策略后看起来像“没有返回新方案”。
- 已在 `frontend/src/App.tsx` 为 `regenerate` 接入独立发送态和确认卡片 loading 态，点击 `重新生成` 后会发送 `POST /api/create-sessions/{session_id}/events` 的 `regenerate` 事件，并在返回前让卡片显示 `生成中...`（Frontend Step 6.5）。
- 已在 `frontend/src/pages/CreatePage.tsx` 将带卡片的 assistant 返回改为“只更新游戏卡片，不重复新增 AI 聊天气泡”；确认卡片当前只展示标题和简介，方便直接看出方案是否换了一版（Frontend Step 6.5）。
- 已在 `frontend/src/mock/runtime.ts` 补齐 mock `regenerate` 变体，确保本地 mock 模式下每次换一版都会明显变化 `plan_id`、标题和简介（Frontend Step 6.5）。
- 已在 `lan_agents/src/agent/conversation_graph/nodes/regenerate_plan/node.py` 强化真实 `regenerate` 行为：保留原有需求和素材约束，但每次都会明确刷新 `plan_id`、标题和简介，不再只悄悄更换内部字段（Frontend Step 6.5）。
- 已在 `backend/tests/test_create_sessions.py` 和 `lan_agents/tests/integration_tests/test_conversation_flows.py` 补强 `regenerate` 断言，锁定“保留 requirements/material_usage，同时返回新可见方案”的行为（Frontend Step 6.5）。
- 已验证 `cd frontend && npm run test:create-confirm-card`、`cd frontend && npm run test:create-chat-event`、`cd frontend && npm run build`、`./.venv/bin/python -m pytest backend/tests/test_create_sessions.py -k regenerate -q`、`cd lan_agents && .venv/bin/python -m pytest tests/integration_tests/test_conversation_flows.py -k regenerate -q` 均通过（Frontend Step 6.5）。

### 2026-06-21：修复浏览器直传 MinIO 的 presigned URL 主机

- 已定位 PNG 上传失败的根因：后端使用 Docker 内网 `MINIO_ENDPOINT=http://minio:9000` 生成 presigned upload URL，浏览器无法解析 `minio` 主机，导致前端 `fetch(upload_url)` 报 `Failed to fetch`。
- 已调整 `backend/app/storage.py`，内部 S3 操作继续使用 `MINIO_ENDPOINT`，但 presigned read/upload URL 改用 `MINIO_PUBLIC_ENDPOINT` 签名，确保浏览器拿到 `http://localhost:9000/...`。
- 已更新 `backend/tests/test_storage.py`，断言私有前缀 presigned URL 使用 public endpoint，并验证 `./.venv/bin/pytest backend/tests/test_storage.py backend/tests/test_uploads.py -v` 通过。

### 2026-06-21：改为 Asset Agent 始终独立生成封面图

- 已将 Orchestrator 图像合同调整为：`assets/cover.png` 始终进入 `asset_manifest_plan`，作为 `display_only=true` 的展示封面；`background.png` 和 `player.png` 仍由 Orchestrator 根据上传素材和游戏需要决定是否进入素材生成路径（Agent Step 7）。
- 已移除封面“由背景图 + 标题派生”的合同：`cover.png` 现在强制 `source=generated`、`derived_from=""`、`title_source=""`，并要求 Asset Agent 按游戏内容、画风和可用参考素材独立生成（Agent Step 7）。
- 已为 Asset Agent 增加独立 `cover` prompt 和生成分支；真实 image client 模式下会为 `cover.png` 单独调用图像生成接口，mock 模式下写入确定性封面图（Agent Step 7）。
- 已让 Coding Agent 的 `manifest_draft.cover` 指向 `assets/cover.png`，但 `manifest_draft.assets` 和代码引用仍只记录真实运行时引用的素材路径，避免封面被误当成游戏运行依赖（Agent Step 7）。
- 已同步更新 `docs/agent-orchestration-design.md`、`docs/agent-implementation-plan.md` 和 `docs/architecture.md`，明确封面独立生成、运行时资源与展示资源分离（Agent Step 7）。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_generation_orchestrator.py tests/unit_tests/test_asset_agent.py tests/integration_tests/test_generation_graph.py tests/unit_tests/test_generation_demo.py -q` 通过，结果为 `26 passed`（Agent Step 7）。

### 2026-06-21：收口 Agent Step 4 三图 Asset Agent 本地骨架

- 已修正 Orchestrator 三图契约兜底：`asset_manifest_plan` 固定补齐 `assets/background.png`、`assets/player.png`、`assets/cover.png`，并允许旧两图 LLM brief 被规范化为三图 `allowed_asset_paths`（Agent Step 3、Agent Step 4）。
- 已让 Orchestrator fallback 使用上传视频作为背景参考、上传图片作为玩家参考；`cover.png` 的旧派生声明已在后续 Agent Step 7 改为空并改由 Asset Agent 独立生成（Agent Step 3、Agent Step 4、Agent Step 7）。
- 已让 Asset Agent 本地确定性边界写出三张图：`background.png` 为 `1280x720`，`player.png` 为 `256x256 RGBA` 透明底，`cover.png` 为 `1280x720` 展示封面（Agent Step 4）。
- 已补强 `tests/unit_tests/test_generation_orchestrator.py` 和 `tests/unit_tests/test_asset_agent.py`，覆盖三图路径、透明玩家图、cover display-only、视频/图片参考和无上传素材 fallback（Agent Step 4）。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_generation_orchestrator.py tests/unit_tests/test_asset_agent.py -q` 通过，结果为 `15 passed`。
- 已验证 Orchestrator mock demo 输出三图合同，Asset Agent demo 输出三张 PNG，`cd lan_agents && .venv/bin/langgraph validate` 通过。

### 2026-06-21：接入 Agent Step 4 真实图像模型客户端边界

- 已新增 `asset_agent/tools/image_model.py`，通过 `ASSET_IMAGE_PROVIDER=openai-compatible` 接入 OpenAI-compatible `/images/generations`，解析 `b64_json` 并写入目标 PNG 文件（Agent Step 4）。
- 已新增 `OPENAI_IMAGE_MODEL`、`OPENAI_IMAGE_BACKGROUND_SIZE=1280x720`、`OPENAI_IMAGE_PLAYER_SOURCE_SIZE=1024x1024` 等环境样例；默认 `ASSET_IMAGE_PROVIDER=mock`，避免本地测试误触发联网或费用（Agent Step 4）。
- 已让 `run_asset_agent` 在启用真实 image client 时调用背景图和玩家原图生成；`cover.png` 已在后续 Agent Step 7 改为独立调用图像生成接口，玩家最终透明底仍由品红幕布后处理导出（Agent Step 4、Agent Step 7）。
- 已新增 `tests/unit_tests/test_image_model.py`，覆盖 image provider payload、固定尺寸传参、`b64_json` 解析和 PNG 落盘（Agent Step 4）。
- 已更新 `tests/unit_tests/test_asset_agent.py`，覆盖三图输出和真实 image client 注入调用，确认背景请求 `1280x720`、玩家源图请求 `1024x1024`（Agent Step 4）。
- 已修复 Orchestrator/Asset Agent 的三图合同回归：fallback 固定补齐图像合同，视频可作为背景参考，图片可作为玩家参考，cover 强制 display-only；cover 的旧派生规则已在后续 Agent Step 7 改为独立生成（Agent Step 4、Agent Step 7）。
- 已根据真实 provider smoke 反馈增强错误诊断：文件上传返回缺失 `id/file_id` 时会显示脱敏响应预览；图片生成超时会明确提示当前超时时长和 `OPENAI_IMAGE_TIMEOUT_SECONDS`，默认图片超时已调到 `180s`（Agent Step 4）。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_generation_orchestrator.py tests/unit_tests/test_asset_agent.py tests/unit_tests/test_image_model.py -q` 通过，结果为 `18 passed`（Agent Step 4）。
- 已验证 `cd lan_agents && .venv/bin/python -m agent.generation_graph.asset_agent.demo --fixture src/agent/generation_graph/fixtures/generation_confirmed_session.json` 输出三张图：`assets/background.png`、`assets/player.png`、`assets/cover.png`（Agent Step 4）。
- 已验证 `cd lan_agents && .venv/bin/langgraph validate` 通过，结果为 `1 graph found`（Agent Step 4）。
- 已尝试真实联网 image provider smoke：`ASSET_IMAGE_PROVIDER=openai-compatible ... asset_agent.demo --workspace output/asset-demo-real`，但当前 Codex 审批器因 `codex-auto-review model_price_error` 拒绝联网提权；因此真实 image provider smoke 仍待在可联网审批环境补跑（Agent Step 4）。
- 当前仍未完成真实联网 image provider smoke；生产级透明抠图还待 Pillow/OpenCV 或等价图像处理依赖补齐（Agent Step 4）。

### 2026-06-21：完成 Agent Step 6 Coding Debug 自调试链路

- 已新增 `lan_agents/src/agent/generation_graph/tools/asset_references.py` 和 `runtime_check.py`，分别用于检查 bundle/manifest 资源引用对齐，以及在本地无浏览器依赖环境下执行 `node --check` + 静态信号的运行时兜底检查（Agent Step 6）。
- 已新增 `lan_agents/src/agent/generation_graph/coding_agent/debug_code_with_assets/node.py`，实现 `runtime_check -> LLM patch -> runtime_check` 的单轮自修复流程；素材缺失、manifest 不一致和 JS 启动问题都会收敛到 `debug_report`，且不会越权改写 `asset_work_order`（Agent Step 6）。
- 已补充 `debug_code_with_assets` 的 manifest 对齐逻辑：修复后会把 `manifest_draft.assets` 同步到 bundle 实际引用路径，避免 JS 已修好但 manifest 残留 stale 资源导致假阳性未解决问题（Agent Step 6）。
- 已新增 `lan_agents/src/agent/generation_graph/coding_agent/debug_demo.py` 和 `lan_agents/fixtures/integrated_bundle_context.json`，支持按计划中的 `python -m agent.generation_graph.coding_agent.debug_demo --fixture fixtures/integrated_bundle_context.json` 方式本地复现 Debug 节点（Agent Step 6）。
- 已重写并补强 `tests/unit_tests/test_generation_orchestrator.py` 与 `test_asset_agent.py` 的三图合同断言，稳定覆盖 `background.png / player.png / cover.png`、视频背景参考、cover display-only 规则和无上传 fallback；cover 派生断言已在后续 Agent Step 7 改为独立生成断言（Agent Step 3、Agent Step 4、Agent Step 6、Agent Step 7）。
- 已新增并验证 `tests/unit_tests/test_coding_debug.py`，覆盖缺素材留痕、JS 语法修复、一轮修复失败停止三类核心调试边界（Agent Step 6）。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_generation_orchestrator.py tests/unit_tests/test_asset_agent.py tests/unit_tests/test_coding_agent.py tests/unit_tests/test_coding_debug.py -q` 通过，结果为 `28 passed`（Agent Step 6）。
- 已验证 `cd lan_agents && .venv/bin/langgraph validate` 通过，结果为 `1 graph found`；已验证 `cd lan_agents && .venv/bin/python -m agent.generation_graph.coding_agent.debug_demo --fixture fixtures/integrated_bundle_context.json` 输出 `debug_report.attempted=true`、`unresolved_issues=[]`（Agent Step 6）。

### 2026-06-21：修复 OpenAI-compatible 附件上传 file id 解析

- 已让 `OpenAICompatibleLLMProvider` 兼容标准 OpenAI 顶层 `id`、`file_id`，以及 OpenAI-compatible 服务常见的 `data.id`、`data.file_id` 包装返回，避免 `/files` 上传成功但解析失败（Agent Step 3）。
- 已在上传响应解析失败时附带安全 raw preview，方便继续定位第三方 provider 返回结构（Agent Step 3）。
- 已新增并验证包装式 `/files` 返回的单元测试；`cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_llm_provider.py -q` 通过，结果为 `11 passed`。

### 2026-06-21：补齐前端模型错误原因弹窗透传

- 已定位模型/Provider 错误显示链路的薄弱点：前端 API client 只解析 `error.message`，未兼容 FastAPI 默认或旁路返回的 `detail` 字段（Frontend Step 6.6）。
- 已让 `frontend/src/api/client.ts` 同时兼容字符串 `detail` 和对象 `detail.message/detail.code/detail.retry_hint`，并保持结构化 `error.message` 优先，确保模型错误原因能进入现有 Error 弹窗（Frontend Step 6.6）。
- 已新增 `frontend/scripts/check-api-error-parsing.mjs` 和 `npm run test:api-error-parsing`，用于锁定 Agent/Provider 错误原因透传行为（Frontend Step 6.6）。

### 2026-06-21：收口 Create 确认生成错误提示

- 已定位“点击游戏卡片生成按钮后弹出 `Unprocessable Entity`”的前端根因：FastAPI 默认 `422` 返回的是 `detail` 数组，而 `frontend/src/api/client.ts` 之前只兼容字符串和对象，最终回退成英文 HTTP 状态文案（Frontend Step 6.6）。
- 已让 `frontend/src/api/client.ts` 新增 `detail[]` 解析，优先提取首条校验错误；同时在 `frontend/src/lib/errors.ts` 为兜底场景补上一层用户友好的 `422` 中文提示，避免把纯技术状态文案直接暴露给用户（Frontend Step 6.6）。
- 已在 `frontend/src/App.tsx` 移除 failed job 的自动 `ErrorDialog` 弹窗链路，点击生成失败或任务后续失败时，不再无条件打断用户；失败原因保留在右侧生成面板和日志区域承载（Frontend Step 6.6、Frontend Step 6.7）。
- 已更新 `frontend/scripts/check-api-error-parsing.mjs` 与 `frontend/scripts/check-create-tasks.mjs`，分别锁定 `422 detail[]` 解析和“failed 任务不自动弹窗”的行为，防止回归（Frontend Step 6.6）。
- 已验证 `cd frontend && npm run test:api-error-parsing`、`cd frontend && npm run test:create-tasks`、`cd frontend && npm run build` 均通过（Frontend Step 6.6）。

### 2026-06-21：补齐 Agent 后台异常到前端失败链路

- 已定位真实图片模型错误未稳定展示的根因：`runner.run()` 直接抛出 provider 异常时，后端后台任务没有 catch，任务无法可靠写入 `failed/error_message`（Backend Agent Step 2）。
- 已在 `backend/app/jobs.py` 为 Agent 后台任务增加异常保护，任何 runner/provider 异常都会写入 `generation_jobs.status=failed`、`error_message` 和一条 `agent_runner` error 日志；错误消息会走统一脱敏后再落库和返回（Backend Agent Step 2）。
- 已让前端任务轮询持续同步 failed job 的 `error_message`，失败原因会留在右侧生成面板和日志区域承载，而不是自动弹出全局错误弹窗（Frontend Step 6.7）。
- 已新增回归覆盖：`backend/tests/test_agent_runner.py` 模拟 image provider 抛异常并断言任务失败、错误原因落库、日志存在且 secret 脱敏；前端 `check-create-tasks.mjs` 锁定任务轮询与失败态展示链路（Backend Agent Step 2、Frontend Step 6.7）。
- 已验证 `cd backend && ../.venv/bin/python -m pytest tests/test_agent_runner.py tests/test_jobs.py -q` 通过，结果为 `9 passed`；已验证 `cd frontend && npm run test:create-tasks`、`npm run test:api-error-parsing` 和 `npm run build` 均通过（Backend Agent Step 2、Frontend Step 6.7）。

### 2026-06-21：接入 Create 任务轮询与 Agent 日志面板

- 已在 `frontend/src/api/jobs.ts` 增加 `getJob(jobId)` 和 `getJobLogs(jobId)`，复用现有 `GET /api/jobs/{job_id}` 与 `GET /api/jobs/{job_id}/logs` 后端接口读取任务状态和 Agent 日志（Frontend Step 6.8）。
- 已在 `frontend/src/App.tsx` 为当前选中的 `pending/running` 任务接入 `1500ms` 轮询，持续刷新任务状态、任务列表、当前进度、失败弹窗和 `selectedAgentLogs`；任务进入 `succeeded/failed` 后停止轮询并保留最后日志（Frontend Step 6.8）。
- 已在 `frontend/src/pages/CreatePage.tsx` 和 `frontend/src/pages/create.css` 增加右侧生成面板的“Agent 执行日志”区域，展示 `step / level / message`，无日志时显示等待状态，轮询失败时显示刷新失败原因（Frontend Step 6.8）。
- 已在 `frontend/src/mock/runtime.ts` 增加 mock job 和 mock agent logs 查询，让 mock 模式也能看到日志面板效果（Frontend Step 6.8）。
- 已更新 `frontend/scripts/check-create-tasks.mjs` 与 `frontend/scripts/check-create-layout.mjs`，覆盖 Job 轮询、日志接口调用和日志面板渲染约束（Frontend Step 6.8）。
- 已验证 `cd frontend && npm run test:create-tasks`、`npm run test:create-layout`、`npm run test:create-confirm-card` 和 `npm run build` 均通过（Frontend Step 6.8）。

### 2026-06-21：接入真实 generation graph 节点日志

- 已新增 `LangGraphGenerationRunner`，后端可通过 `AGENT_RUNNER=langgraph` lazy import `lan_agents` 的 `generation_graph`，并把 confirmed session 快照转换为第二阶段 graph state（Backend Agent Step 3）。
- 已监听 LangGraph `astream_events(version="v2")` 的真实 graph 节点事件，只记录 `metadata.langgraph_node == event.name` 的节点 start/end/error，避免条件路由 runnable 被重复写入（Backend Agent Step 3）。
- 已复用 `jobs.py` 的 `emit_log` 钩子即时写入 `agent_logs`，真实 generation graph 每个节点开始、结束和异常都会被前端日志面板轮询到（Backend Agent Step 3）。
- 已新增 `AGENT_RUNNER` 配置；Docker Compose 默认 `langgraph` 跑真实图，`.env.example` 默认 `fake` 保持本地/CI 可控（Backend Agent Step 3）。
- 已新增 fake graph runner 单测，覆盖节点 start/end 日志、节点异常日志和结果映射；已验证 `cd backend && AGENT_RUNNER=fake ../.venv/bin/python -m pytest tests/test_agent_runner.py tests/test_jobs.py tests/test_config.py -q` 通过，结果为 `20 passed`（Backend Agent Step 3）。
- 已验证真实 generation graph mock 集成：`cd lan_agents && .venv/bin/python -m pytest tests/integration_tests/test_generation_graph.py -q` 通过，结果为 `3 passed`（Backend Agent Step 3）。

### 2026-06-21：统一 Generation Graph 的 Orchestrator/Coding/Asset 合同

- 已将 Orchestrator 当前合同从旧“三图固定合同”收敛为“背景/人物可选 + 封面必选合同”：`assets/background.png` 与 `assets/player.png` 按需进入 `asset_manifest_plan`，`assets/cover.png` 始终作为 display-only 展示资产进入 `asset_manifest_plan`（Agent Step 7）。
- 已让 Orchestrator 判定用户上传图片/视频分别作为背景或人物参考；无图片/视频上传时默认优先让 Coding Agent 用代码绘制背景和人物，不调用 Asset Agent（Agent Step 7）。
- 已新增并归一化 `coding_agent_brief` 与 `asset_agent_brief`，并检查两者、`development_brief.allowed_asset_paths` 和 `asset_manifest_plan` 的资产路径一致性（Agent Step 7）。
- 已实现 `generation_graph` 完整编排：Orchestrator 先产出合同，Coding Agent 先生成代码；若存在背景/人物资产需求则调用 Asset Agent 后再进入 Coding Debug，否则直接进入 Coding Debug（Agent Step 7）。
- 已更新 Asset Agent 只处理 Orchestrator 要求的背景/人物图，并始终生成 Orchestrator 规划的独立 `cover.png`；无运行时视觉素材时仍会生成封面图（Agent Step 7）。
- 已新增 `tests/integration_tests/test_generation_graph.py`，覆盖“无图直接代码生成并 debug”和“有图生成素材后 debug”两条路径（Agent Step 7）。
- 已新增 `agent.generation_graph.demo`，支持 `--workspace` 固定输出目录、`--no-visual-assets` 对比无图分支，并打印 Orchestrator 决策、两个子 Agent brief、生成文件、manifest 与 debug report，便于人工检查（Agent Step 7）。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest -q` 通过，结果为 `144 passed`；已验证 `cd lan_agents && .venv/bin/langgraph validate` 通过，结果为 `2 graphs found`（Agent Step 7）。

### 2026-06-21：修复 Asset Agent 上传图只搬运不 refine 的问题

- 已为 `asset_agent/tools/image_model.py` 增加 OpenAI-compatible `/images/edits` 调用，使用 multipart 传入参考图、prompt、size、quality 和 `output_format=png`，用于上传背景/角色图的真实 refine（Agent Step 7）。
- 已调整 `run_asset_agent`：当 Orchestrator 判定 `uploaded_reference` 且 `ASSET_IMAGE_PROVIDER=openai-compatible` 时，背景图调用 `edit_png` 生成 `assets/background.png`，角色图调用 `edit_png` 生成 `assets/player_raw.png` 后再导出透明 `assets/player.png`；不再把上传图直接 resize 后冒充 refine（Agent Step 7）。
- 已修正角色后处理：新增 `write_chroma_keyed_player_from_source`，从模型输出的 raw PNG 读取像素、按角落背景色/alpha 做抠图并缩放到 `256x256`，不再忽略模型输出重新画固定 mock 角色（Agent Step 7）。

### 2026-06-21：完成 Validator Agent 最终交付验收

- 已新增 `validate_final_delivery` 节点，作为第二阶段最终质量门禁；它只做确定性验收，不调用 Coding/Asset 返修，也不输出 `repair_decision` 或 `repair_instruction`（Agent Step 7）。
- 已覆盖 `manifest.json`、`index.html`、`style.css`、`game.js` 存在性，校验 manifest 的 `entry / styles / scripts / assets / cover / runtime / generatedAt`，并检查所有 bundle 路径都留在 `artifact_workspace` 内（Agent Step 7）。
- 已把 `assets/cover.png` 作为展示必需资产纳入硬门禁：即使不是 runtime asset，manifest 声明的 cover 文件缺失也会导致 Validator 失败（Agent Step 7）。
- 已扫描 secret、token、password、OAuth code、完整 presigned URL 和外网 CDN；失败输出只返回脱敏后的 `validation_report.issues`、`error_message` 和 `retry_hint`（Agent Step 7）。
- 已新增 Validator demo 与 `fixtures/validated_bundle_context.json`，可本地写入最小 bundle 并验证 `validation_report.valid=true`（Agent Step 7）。
- 已新增 `tests/unit_tests/test_validator_agent.py`，覆盖完整 bundle 通过、缺 cover、缺入口/运行资源、含 secret/CDN、缺 debug report 与 unresolved debug issue 等门禁（Agent Step 7）。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_validator_agent.py tests/unit_tests/test_coding_debug.py tests/integration_tests/test_generation_graph.py -q` 通过，结果为 `10 passed`；已验证 `cd lan_agents && .venv/bin/python -m agent.generation_graph.validator_agent.demo --fixture fixtures/validated_bundle_context.json` 输出 `generation_status=succeeded` 且 `validation_report.valid=true`；已验证 `cd lan_agents && .venv/bin/langgraph validate` 通过，结果为 `2 graphs found`；已验证 `cd lan_agents && .venv/bin/python -m pytest -q` 通过，结果为 `159 passed`（Agent Step 7）。

### 2026-06-21：收口 generation_graph 本地端到端链路

- 已在 `generation_graph` 中加入 `init_generation_context`、`join_assets_and_code`、`validate_final_delivery`、`finalize_success` 和 `finalize_failure`，让本地生成链路从 Orchestrator、Coding、Asset、Debug 继续进入 Validator 并输出最终状态（Agent Step 8）。
- 已将 Coding Agent 的 `manifest_draft` 在验收前写出为最终 `manifest.json`，Validator 会基于最终 manifest、入口文件、资源、封面和 debug report 做交付门禁（Agent Step 8）。
- 已为 `GenerationState` 增加最终 `status` 字段，成功路径输出 `status=succeeded`，失败路径输出 `status=failed`，并保留 `generation_status` 供图内阶段流转使用（Agent Step 8）。
- 已补强 generation graph 集成测试：覆盖无运行时视觉素材时只生成 `cover.png` 并成功、需要背景/角色素材时完整成功、Validator 失败时进入 failed 并返回 `failed_step/error_message/retry_hint/validation_report/agent_logs`（Agent Step 8）。
- 已更新 generation demo 输出，新增 `Validation Report` 和 `Artifact Result` 区块，便于人工检查 Step 8 收口结果（Agent Step 8）。
- 当前 Step 8 仍使用现有顺序 StateGraph 收口来保证稳定性，尚未实现真正并发 fan-out/reducer；真实 LangGraph dev Studio 可视化仍待补跑（Agent Step 8）。
- 已修复真实 LLM smoke 暴露的 Orchestrator 容错问题：当模型误把 `assets/cover.png` 放入 `uploaded_asset_tasks` 时，系统会忽略该上传任务并强制补回独立 generated cover task，而不是直接失败（Agent Step 8）。
- 已更新 `scripts/real_generation_smoke.py` 的 Step 8 成功判定，要求 `generation_status=succeeded`、`status=succeeded`、最终 `manifest.json` 存在、`validation_report.valid=true`、runtime/debug 检查通过且无 unresolved issues（Agent Step 8）。
- 已验证真实 LLM + mock 图片 smoke：`cd lan_agents && .venv/bin/python scripts/real_generation_smoke.py --fixture src/agent/generation_graph/fixtures/generation_confirmed_session.json --workspace output/real-generation-step8-smoke --skip-real-images` 输出 `generation_status=succeeded`、`status=succeeded`、`validation_valid=true`，并生成 `manifest.json/index.html/style.css/game.js/assets/*`（Agent Step 8）。
- 已验证真实 LLM + 真实图片 provider smoke：`cd lan_agents && .venv/bin/python scripts/real_generation_smoke.py --fixture src/agent/generation_graph/fixtures/generation_confirmed_session.json --workspace output/real-generation-step8-image-smoke` 输出 `generation_status=succeeded`、`status=succeeded`、`validation_valid=true`，且 `processed_asset_sources` 中 `background/player/cover` 均为 `image_model`（Agent Step 8）。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/integration_tests/test_generation_graph.py tests/unit_tests/test_generation_state.py tests/unit_tests/test_generation_demo.py tests/unit_tests/test_validator_agent.py -q` 通过，结果为 `15 passed`；已验证 `cd lan_agents && .venv/bin/python -m agent.generation_graph.demo --fixture src/agent/generation_graph/fixtures/generation_confirmed_session.json --workspace output/generation-step8-demo` 输出 `Validation Report.valid=true` 和 `Artifact Result.manifest_path`；已验证 `cd lan_agents && .venv/bin/python -m agent.generation_graph.demo --fixture src/agent/generation_graph/fixtures/generation_confirmed_session.json --workspace output/generation-step8-no-assets --no-visual-assets` 通过；已验证 `cd lan_agents && .venv/bin/langgraph validate` 通过，结果为 `2 graphs found`；已验证 `cd lan_agents && .venv/bin/python -m pytest -q` 通过，结果为 `160 passed`（Agent Step 8）。
- 已验证真实 smoke 修复后的回归：`cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_generation_orchestrator.py tests/unit_tests/test_generation_demo.py tests/integration_tests/test_generation_graph.py -q` 通过，结果为 `22 passed`；已验证 `cd lan_agents && .venv/bin/python -m pytest -q` 通过，结果为 `161 passed`；已验证 `cd lan_agents && .venv/bin/langgraph validate` 通过，结果为 `2 graphs found`（Agent Step 8）。
- 已将测试环境固定 `ASSET_IMAGE_PROVIDER=mock`，避免根目录 `.env` 切到真实图片 provider 后让单测误触发联网；真实 demo 仍通过显式环境配置走真实 provider（Agent Step 7）。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests/test_asset_agent.py tests/unit_tests/test_image_model.py tests/unit_tests/test_generation_orchestrator.py tests/integration_tests/test_generation_graph.py tests/unit_tests/test_generation_demo.py -q` 通过，结果为 `29 passed`（Agent Step 7）。

### 2026-06-21：补齐生成后修改 revision_graph 最小契约

- 已新增 `revision_graph`，独立于第一阶段 `conversation_graph` 和第二阶段 `generation_graph`，输入上一版任务、上一版 `game_plan`、上一版 `material_usage`、已生成产物摘要和用户本轮修改消息（Agent Step 11）。
- 已实现 `load_revision_context -> understand_revision_intent -> build_revision_patch/create_revision_job_payload` 与模糊修改追问分支；明确修改输出 `revision_intent`、`game_plan_patch`、`requires_regeneration=true`、用户可见 `assistant_response` 和 `revision_job_payload`（Agent Step 11）。
- 已保证模糊修改不创建 revision job payload；生成的 payload 带 `parent_job_id`，复用旧素材用途和旧产物摘要，不覆盖原始 job、原始 `create_session` 快照或旧 draft 路径（Agent Step 11）。
- 已加入敏感片段脱敏边界，revision 输出和日志不回显 secret、token、password、OAuth code 或完整 presigned URL 特征（Agent Step 11）。
- 已将 `revision_graph` 导出到 `agent.__init__`、`agent.graph` 和 `lan_agents/langgraph.json`；`langgraph validate` 现在识别 `conversation/generation/revision` 三个图（Agent Step 11）。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/integration_tests/test_revision_graph.py tests/unit_tests/test_project_structure.py tests/unit_tests/test_configuration.py -q` 通过，结果为 `8 passed`；已验证 `cd lan_agents && .venv/bin/langgraph validate` 通过，结果为 `3 graphs found`（Agent Step 11）。

### 2026-06-21：为 revision_graph 接入 LLM Provider

- 已新增 `RevisionPlanner` 服务，复用现有 `LLMProvider.complete_json()`，让生成后修改链路优先由当前配置的大模型理解用户修改并输出 `revision_intent/game_plan_patch/requires_regeneration/assistant_message/suggestions`（Agent Step 11）。
- 已在 prompt 中明确生成后修改不覆盖旧产物、不修改 `parent_job/base_material_usage/generated_result/create_session`，只允许修改 `game_plan` 的可控字段，并禁止输出 secret、token、password、OAuth code 或完整 presigned URL（Agent Step 11）。
- 已保留确定性 fallback：默认 mock provider 或模型返回非 revision schema 时，继续使用本地解析识别失败条件、雪地背景、主角替换等修改，避免本地和 CI 被真实模型阻塞（Agent Step 11）。
- 已让 `understand_revision_intent` 节点调用 `RevisionPlanner`，并新增 `test_revision_planner.py` 覆盖 provider 调用、prompt 约束、LLM patch 合并和节点调用（Agent Step 11）。

### 2026-06-21：生成成功后上传 draft bundle 到 MinIO

- 已在后端任务成功分支接入 draft bundle 上传：当 Agent runner 返回本地 `artifact_prefix` workspace 时，后端会遍历 `manifest.json / index.html / style.css / game.js / assets/*` 并上传到 `drafts/{user_id}/{job_id}/v1/*`（Backend Agent MinIO）。
- 已让 `generation_jobs.artifact_prefix` 保存 MinIO draft object prefix，不再把浏览器不可访问的本地 `/app/output/...` 作为最终产物前缀；job detail 继续返回 owner-only `/api/jobs/{job_id}/artifacts/...` 代理 URL（Backend Agent MinIO）。
- 已让 draft `Game.manifest_url`、`artifact_base_url` 和 `cover_url` 使用后端 artifact 代理地址，避免把私有 draft 的完整 presigned URL 暴露给前端并避免签名过期问题（Backend Agent MinIO）。
- 已为 `ObjectStorageService` 增加 `get_object`、`list_object_keys` 和 `copy_object` 边界；artifact 读取路由优先兼容旧本地路径，找不到本地路径时从 MinIO object 读取并返回正确 `Content-Type`（Backend Agent MinIO）。
- 已新增/修复后端测试覆盖 draft bundle 上传、artifact 代理读取、storage object 读取和 Python 3.9/FastAPI response 注解兼容；已验证相关后端测试通过（Backend Agent MinIO）。

### 2026-06-21：第一阶段 Design Agent 改为 LLM-first 填充方案 ☑️ 已完成

- 已收敛 `DesignPlanner` 边界：`game_plan` 的标题、标签、玩法、风格、角色、胜负条件和操作方式由 LLM patch 或用户显式字段提供，本地只做 schema 字段过滤、MVP 标签过滤、简介派生和完整性检查（Agent Step 1.41）。
- 已移除第一阶段本地题材推断：`update_requirements` 不再把“小猫/星星/森林/可爱/躲避”等关键词抽成 `must_have`、`nice_to_have` 或 `preference_profile`，只保留用户原话摘要、显式约束和素材用途同步（Agent Step 1.41）。
- 已移除本地追问兜底：当 plan 未完整且模型没有返回 `assistant_message` 或 `suggestions` 时，直接抛出带 `details.reason/missing_fields` 的 `ProviderError`；用户误点生成但方案未完整时，确认节点只返回缺字段提示，不再生成写死建议（Agent Step 1.41）。
- 已将 `normalize_tags` 调整为纯过滤器：空标签保持为空，不再本地默认补 `casual`；标签缺失会继续作为待补字段交给 LLM 处理（Agent Step 1.41）。
- 已更新回归测试，覆盖 LLM 首轮可完整出卡、超过五轮仍需 LLM 自行补全、本地不再补建议/补标签/猜需求、模型追问建议保持透传（Agent Step 1.41）。
- 已验证 `cd lan_agents && .venv/bin/python -m pytest tests/unit_tests tests/integration_tests -q` 通过，结果为 `178 passed`；已验证 `cd lan_agents && .venv/bin/langgraph validate` 通过，结果为 `3 graphs found`（Agent Step 1.41）。
