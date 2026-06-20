# 项目 Layer 与文件职责

本文档只维护当前项目 layer、目录边界和文件职责。完成度、已实现功能和待补齐边界记录在 [progress.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/progress.md)。

```text
.
├── AGENTS.md                         协作规则：中文响应（Step 0.1）、文档分工（Step 0.1）
├── README.md                         启动说明：Compose 命令（Step 1.3）、端口说明（Step 1.3）
├── prd.md                            原始需求：需求留存（Step 0.1）、验收约束（Step 0.1）
├── .env.example                      环境样例：前后端地址（Step 0.3）、存储模型变量（Step 0.3）
├── .gitignore                        忽略规则：依赖排除（Step 0.1）、缓存排除（Step 0.1）
├── docker-compose.yml                本地编排：基础服务（Step 1.1）、配置透传（Step 2.4）、前端 Profile（Frontend Step 3.4）
├── agent/                            Agent 原型层：独立调试（Agent Prototype Step 1）、LangGraph 流程（Agent Prototype Step 1）
│   ├── README.md                     原型说明：本地命令（Agent Prototype Step 1）、运行边界（Agent Prototype Step 1）
│   ├── pyproject.toml                原型配置：pytest 入口（Agent Prototype Step 1）、依赖占位（Agent Prototype Step 1）
│   ├── .env.example                  原型样例：provider 变量（Agent Prototype Step 1）、模型变量（Agent Prototype Step 1）
│   ├── langgraph.json                部署配置：图导出入口（Agent Prototype Step 1）、环境引用（Agent Prototype Step 1）
│   ├── app/                          Agent 包：对话图（Agent Prototype Step 1）、生成图（Agent Prototype Step 1）
│   │   ├── __init__.py               包标记：模块导入（Agent Prototype Step 1）
│   │   ├── runner.py                 调试入口：conversation CLI（Agent Prototype Step 1）、generate CLI（Agent Prototype Step 1）
│   │   ├── tracing.py                tracing 边界：LangSmith 配置（Agent Prototype Step 1）、run metadata（Agent Prototype Step 1）
│   │   ├── graph/                    图层：状态模型（Agent Prototype Step 1）、图兼容层（Agent Prototype Step 1）
│   │   │   ├── compat.py             图兼容：StateGraph 兜底（Agent Prototype Step 1）、顺序编排（Agent Prototype Step 1）
│   │   │   ├── state.py              状态模型：确认卡片（Agent Prototype Step 1）、设计状态（Agent Prototype Step 1）
│   │   │   ├── conversation_graph.py 对话图：确认卡片产出（Agent Prototype Step 1）、设计状态沉淀（Agent Prototype Step 1）
│   │   │   └── generation_graph.py   生成图：素材分析（Agent Prototype Step 1）、bundle 校验（Agent Prototype Step 1）
│   │   ├── agents/                   Agent 节点：设计节点（Agent Prototype Step 1）、校验节点（Agent Prototype Step 1）
│   │   │   ├── design_agent.py       设计节点：确认卡片（Agent Prototype Step 1）、设计状态（Agent Prototype Step 1）
│   │   │   ├── asset_agent.py        素材节点：素材摘要（Agent Prototype Step 1）、用途建议（Agent Prototype Step 1）
│   │   │   ├── spec_builder.py       规格节点：game spec（Agent Prototype Step 1）、实现约束（Agent Prototype Step 1）
│   │   │   ├── developer_agent.py    开发节点：静态 bundle（Agent Prototype Step 1）、manifest 产出（Agent Prototype Step 1）
│   │   │   └── validator_agent.py    校验节点：文件完整性（Agent Prototype Step 1）、错误摘要（Agent Prototype Step 1）
│   │   ├── providers/                Provider 层：mock provider（Agent Prototype Step 1）、OpenAI 校验（Agent Prototype Step 1）
│   │   │   ├── mock_provider.py      Mock provider：本地兜底（Agent Prototype Step 1）、无密钥模式（Agent Prototype Step 1）
│   │   │   └── openai_compatible.py  OpenAI provider：配置校验（Agent Prototype Step 1）、真实接入占位（Agent Prototype Step 1）
│   │   └── tools/                    Tool 层：素材摘要（Agent Prototype Step 1）、bundle 写入（Agent Prototype Step 1）
│   │       ├── asset_tools.py        素材工具：类型摘要（Agent Prototype Step 1）、字段抽取（Agent Prototype Step 1）
│   │       ├── bundle_tools.py       产物工具：HTML/CSS/JS 写入（Agent Prototype Step 1）、manifest 落盘（Agent Prototype Step 1）
│   │       ├── logging_tools.py      日志工具：统一日志字典（Agent Prototype Step 1）、步骤摘要（Agent Prototype Step 1）
│   │       └── manifest_tools.py     manifest 工具：协议字段（Agent Prototype Step 1）、时间戳生成（Agent Prototype Step 1）
│   ├── my_agent/                     部署包：图导出（Agent Prototype Step 1）、requirements 边界（Agent Prototype Step 1）
│   │   ├── __init__.py               包标记：部署包导入（Agent Prototype Step 1）
│   │   ├── agent.py                  图导出：conversation graph（Agent Prototype Step 1）、generation graph（Agent Prototype Step 1）
│   │   ├── requirements.txt          依赖清单：LangGraph 运行依赖（Agent Prototype Step 1）、LangSmith tracing（Agent Prototype Step 1）
│   │   └── utils/                    包装工具：nodes 导出（Agent Prototype Step 1）、state 导出（Agent Prototype Step 1）
│   │       ├── __init__.py           包标记：utils 导入（Agent Prototype Step 1）
│   │       ├── nodes.py              节点导出：设计/素材/开发/校验节点（Agent Prototype Step 1）
│   │       ├── state.py              状态导出：确认卡片（Agent Prototype Step 1）、校验报告（Agent Prototype Step 1）
│   │       └── tools.py              工具导出：manifest/bundle/logging（Agent Prototype Step 1）
│   ├── fixtures/                     原型样本：请求样本（Agent Prototype Step 1）
│   │   └── sample_request.json       样本输入：对话 fixture（Agent Prototype Step 1）、生成 fixture（Agent Prototype Step 1）
│   └── tests/                        原型测试：对话图测试（Agent Prototype Step 1）、CLI 测试（Agent Prototype Step 1）
│       ├── conftest.py               测试配置：包路径注入（Agent Prototype Step 1）
│       ├── test_conversation_graph.py 对话测试：确认卡片（Agent Prototype Step 1）、设计状态（Agent Prototype Step 1）
│       ├── test_generation_graph.py  生成测试：bundle 产出（Agent Prototype Step 1）、校验失败（Agent Prototype Step 1）
│       ├── test_langsmith_tracing.py tracing 测试：配置解析（Agent Prototype Step 1）、runner tracing（Agent Prototype Step 1）
│       └── test_runner_cli.py        CLI 测试：子命令帮助（Agent Prototype Step 1）、provider 校验（Agent Prototype Step 1）
├── backend/                          后端层：API 边界（Step 0.2）、测试边界（Step 0.2）
│   ├── Dockerfile                    后端镜像：依赖安装（Step 1.1）、迁移启动（Step 2.2）
│   ├── .dockerignore                 构建忽略：缓存排除（Step 1.1）、镜像瘦身（Step 1.1）
│   ├── requirements.txt              依赖清单：FastAPI 依赖（Step 2.1）、迁移依赖（Step 2.2）、Auth 测试依赖（Step 3）
│   ├── pytest.ini                    测试配置：导入路径（Step 2.1）
│   ├── alembic.ini                   迁移配置：脚本定位（Step 2.2）、连接配置（Step 2.2）
│   ├── app/                          应用包：代码边界（Step 0.2）
│   │   ├── __init__.py               包标记：模块导入（Step 0.2）
│   │   ├── auth.py                   认证路由：邮箱登录注册（Step 3）、注册头像上传（Frontend Step 3.4）、可选鉴权（Step 4）、游客识别（Step 6）
│   │   ├── agent_runner.py           执行器边界：fake runner（Step 8）、状态结果（Step 8）、日志载荷（Step 8）
│   │   ├── config.py                 配置读取：根目录 .env（Step 3）、启动校验（Step 2.4）
│   │   ├── db.py                     数据库层：异步引擎（Step 2.2）、会话依赖（Step 2.2）
│   │   ├── main.py                   API 入口：健康检查（Step 2.1）、Games/Jobs/Events 挂载（Step 4/6/7）、Swagger 文档（Step 2.5）
│   │   ├── models.py                 数据模型：认证表（Step 2.3）、业务表（Step 1）
│   │   ├── schemas.py                API schema：Auth 响应（Step 3）、注册头像 schema（Frontend Step 3.4）、Uploads 响应（Step 3）
│   │   ├── games.py                  游戏路由：列表筛选（Step 4）、详情权限（Step 4）、点赞接口（Step 5）
│   │   ├── jobs.py                   任务路由：创建任务（Step 7）、任务查询（Step 7）、日志脱敏（Step 7）
│   │   ├── play_events.py            事件路由：游客上报（Step 6）、计数规则（Step 6）、元数据脱敏（Step 6）
│   │   ├── seed.py                   种子服务：published 可玩游戏（Step 10）、静态 bundle 组装（Step 10）
│   │   ├── storage.py                存储服务：对象路径（Step 2）、头像公开路径（Frontend Step 3.4）、签名链接（Step 2）
│   │   ├── uploads.py                上传路由：presign 接口（Step 3）、complete 接口（Step 3）
│   │   └── security.py               安全工具：密码哈希与校验（Step 3）
│   ├── migrations/                   迁移层：迁移环境（Step 2.2）、版本目录（Step 2.2）
│   │   ├── env.py                    迁移入口：异步连接（Step 2.2）、配置注入（Step 2.2）
│   │   ├── script.py.mako            迁移模板：版本生成（Step 2.2）
│   │   └── versions/                 迁移版本：版本边界（Step 2.2）
│   │       ├── 0001_initial.py       初始迁移：认证表基线（Step 2.3）
│   │       └── 0002_business_tables.py 业务迁移：游戏任务表（Step 1）、事件日志表（Step 1）
│   └── tests/                        测试层：后端测试（Step 0.2）
│       ├── test_auth.py              认证测试：邮箱登录注册（Step 3）、注册头像上传（Frontend Step 3.4）、Google OAuth 回跳（Step 3）
│       ├── test_agent_runner.py      执行器测试：输入边界（Step 8）、状态流（Step 8）、draft 关联（Step 8）
│       ├── test_config.py            配置测试：根目录 .env（Step 3）、校验规则（Step 2.4）
│       ├── test_health.py            健康测试：接口断言（Step 2.1）、就绪断言（Step 2.2）
│       ├── test_migrations.py        迁移测试：业务表断言（Step 1）、Alembic SQL 断言（Step 1）
│       ├── test_games.py             游戏测试：公开列表（Step 4）、详情权限（Step 4）
│       ├── test_likes.py             点赞测试：登录保护（Step 5）、幂等计数（Step 5）
│       ├── test_jobs.py              任务测试：创建绑定（Step 7）、日志权限（Step 7）
│       ├── test_play_events.py       事件测试：游客上报（Step 6）、脱敏规则（Step 6）
│       ├── test_seed.py              种子测试：published 幂等（Step 10）、bundle 契约（Step 10）
│       ├── test_storage.py           存储测试：对象路径（Step 2）、链接边界（Step 2）
│       └── test_uploads.py           上传测试：presign 接口（Step 3）、complete 落库（Step 3）
├── frontend/                         前端层：SPA 边界（Step 0.2）、构建边界（Step 0.2）
│   ├── Dockerfile                    前端镜像：依赖安装（Step 1.1）、Vite 启动（Step 1.1）、可选容器开发（Frontend Step 3.4）
│   ├── .dockerignore                 构建忽略：依赖排除（Step 1.1）、产物排除（Step 1.1）
│   ├── package.json                  包配置：脚本定义（Step 8.1）、路由校验脚本（Frontend Step 3.4）、首页筛选校验脚本（Frontend Step 3.4）
│   ├── package-lock.json             依赖锁定：版本固定（Step 8.1）
│   ├── index.html                    HTML 入口：Root 挂载（Step 8.1）
│   ├── tsconfig.json                 TS 配置：前端编译（Step 8.1）
│   ├── tsconfig.node.json            Node TS 配置：Vite 编译（Step 8.1）
│   ├── vite.config.ts                Vite 配置：React 插件（Step 8.1）、开发服务（Step 8.1）、本地 API 代理（Frontend Step 3.4）
│   ├── vite.config.js                Vite 配置副本：待收敛
│   ├── vite.config.d.ts              类型声明：待评估
│   ├── src/                          前端源码：页面入口（Step 0.2）
│   │   ├── main.tsx                  渲染入口：Root 创建（Step 8.1）、BrowserRouter 挂载（Frontend Step 3.4）
│   │   ├── App.tsx                   应用壳：真实路由（Frontend Step 3.4）、全局状态编排（Frontend Step 3.4）、Home 游戏流请求编排（Frontend Step 4）、Play meta 加载路由（Frontend Step 5）
│   │   ├── api/                      前端 API：请求边界（Frontend Step 2.1）
│   │   │   ├── client.ts             请求入口：cookie 请求（Frontend Step 2.1）、错误解析（Frontend Step 2.1）
│   │   │   ├── auth.ts               Auth 客户端：登录注册（Frontend Step 2.1）、当前用户（Frontend Step 2.1）
│   │   │   ├── games.ts              Games 客户端：列表查询（Frontend Step 4）、详情查询（Frontend Step 4）、点赞请求（Frontend Step 4）
│   │   │   └── play.ts               Play 客户端：manifest 加载（Frontend Step 5）、事件上报（Frontend Step 5）、iframe 地址解析（Frontend Step 5）
│   │   ├── components/               前端组件：导航边界（Frontend Step 3.4）、Auth 弹窗（Frontend Step 3.4）
│   │   │   ├── TopNav.tsx            顶部导航：Home/Create 导航（Frontend Step 3.4）、头像昵称展示（Frontend Step 3.4）、登录区（Frontend Step 3.4）
│   │   │   ├── AuthModal.tsx         Auth 弹窗：表单交互（Frontend Step 3.4）、昵称默认头像注册（Frontend Step 3.4）、字段状态浮层（Frontend Step 3.4）
│   │   │   └── auth-modal.css        Auth 样式：弹窗布局（Frontend Step 3.4）、错误提示（Frontend Step 3.4）、紧凑表单状态位（Frontend Step 3.4）
│   │   ├── lib/                      前端基础库：Console 输出（Frontend Step 3.3）、错误摘要（Frontend Step 3.2）
│   │   │   ├── console.ts            Console 工具：结构化输出（Frontend Step 3.3）、敏感字段脱敏（Frontend Step 3.3）
│   │   │   ├── errors.ts             错误工具：统一弹窗数据（Frontend Step 3.2）、重试建议（Frontend Step 3.2）
│   │   │   └── games.ts              游戏映射：卡片字段格式化（Frontend Step 4）、封面兜底（Frontend Step 4）
│   │   ├── mock/                     前端 mock：开关边界（Frontend Step 3.1）、静态数据（Frontend Step 3.1）
│   │   │   └── runtime.ts            mock 运行时：环境开关（Frontend Step 3.1）、Auth/Home/Create/Play 数据（Frontend Step 3.1）、Games 查询点赞 mock（Frontend Step 4）、Play manifest mock（Frontend Step 5）
│   │   ├── pages/                    前端页面：路由页面（Frontend Step 3.4）、页面样式（Frontend Step 3.4）
│   │   │   ├── HomePage.tsx          首页页面：精选推荐选取（Frontend Step 3.4）、Games 列表查询参数（Frontend Step 4）、排序搜索筛选（Frontend Step 4）、Home 点赞入口（Frontend Step 4）
│   │   │   ├── home.css              首页样式：官网式首屏（Frontend Step 3.4）、筛选下划线（Frontend Step 3.4）、搜索空态样式（Frontend Step 3.4）、卡片点赞覆盖层（Frontend Step 4）
│   │   │   ├── CreatePage.tsx        创建页：任务工作台（Frontend Step 3.4）、单侧栏任务对话一体化（Frontend Step 3.4）、多附件选择删除（Frontend Step 3.4）、Create Console（Frontend Step 3.4）
│   │   │   ├── create.css            创建页样式：工作台布局（Frontend Step 3.4）、单侧栏折叠任务区（Frontend Step 3.4）、输入区浮动按钮（Frontend Step 3.4）、附件 chip 删除态（Frontend Step 3.4）、右侧生成面板（Frontend Step 3.4）
│   │   │   ├── PlayPage.tsx          游玩页：无导航布局（Frontend Step 3.4）、点赞与同类流（Frontend Step 3.4）、Games 点赞同步（Frontend Step 4）、manifest/iframe 运行链路（Frontend Step 5）、事件上报与重试（Frontend Step 5）
│   │   │   └── play.css              游玩页样式：满屏自适应（Frontend Step 3.4）、舞台贴屏布局（Frontend Step 3.4）、Play 独立背景（Frontend Step 3.4）、封面进度条蒙版（Frontend Step 3.4）、运行失败态与 iframe（Frontend Step 5）
│   │   ├── styles.css                全局样式：Yahaha 视觉（Frontend Step 1）、官网式导航比例（Frontend Step 3.4）、共享壳层样式（Frontend Step 3.4）
│   │   ├── types/                    前端类型：页面类型（Frontend Step 3.4）、游戏类型（Frontend Step 3.4）
│   │   │   └── ui.ts                 UI 类型：页面枚举（Frontend Step 3.4）、展示模型（Frontend Step 3.4）、Games 查询枚举（Frontend Step 4）
│   │   └── vite-env.d.ts             类型声明：Vite 类型（Step 8.1）
│   └── scripts/                      前端脚本：验证脚本（Frontend Step 1）
│       ├── check-static-ui.mjs       静态检查：界面标记（Frontend Step 1）、禁用调试面板（Frontend Step 1）
│       ├── check-auth-client.mjs     Auth 检查：请求入口（Frontend Step 2.1）、本地代理约束（Frontend Step 3.4）、敏感字段约束（Frontend Step 2.1）
│       ├── check-current-user.mjs    当前用户检查：启动恢复（Frontend Step 2.2）、昵称头像约束（Frontend Step 2.2）
│       ├── check-auth-ui.mjs         Auth 界面检查：表单交互（Frontend Step 2.8）、OAuth 占位（Frontend Step 2.8）
│       ├── check-app-infra.mjs       基础设施检查：mock 开关（Frontend Step 3.1）、Console/错误边界（Frontend Step 3.3）
│       ├── check-routing-structure.mjs 路由检查：页面拆分（Frontend Step 3.4）、Play 无导航（Frontend Step 3.4）
│       ├── check-home-filters.mjs    首页检查：排序搜索逻辑（Frontend Step 4）、放大镜样式（Frontend Step 3.4）、Home 点赞入口（Frontend Step 4）
│       ├── check-home-api.mjs        首页检查：Games API 编排（Frontend Step 4）、查询参数请求（Frontend Step 4）
│       ├── check-play-page.mjs       Play 检查：点赞交互（Frontend Step 4）、同类游戏流（Frontend Step 3.4）
│       ├── check-play-runtime.mjs    Play 检查：manifest/iframe 链路（Frontend Step 5）、事件上报（Frontend Step 5）、重试入口（Frontend Step 5）
│       └── check-create-layout.mjs   Create 检查：单侧栏折叠任务区（Frontend Step 3.4）、对话输入合并（Frontend Step 3.4）
├── deployment/                       部署层：目录边界（Step 0.2）
│   ├── .gitkeep                      占位文件：目录保留（Step 0.2）
│   └── minio-init.sh                 存储初始化：Bucket 创建（Step 1.2）、Prefix 策略（Step 1.2）
├── scripts/                          脚本层：目录边界（Step 0.2）
│   ├── .gitkeep                      占位文件：目录保留（Step 0.2）
│   └── seed_backend.py               种子脚本：published 写入（Step 10）、本地执行入口（Step 10）
└── docs/                             文档层：设计文档（Step 0.2）、交付记录（Step 0.2）
    ├── architecture.md               架构文档：Layer 维护（Step 0.1）、文件职责（Step 0.2）
    ├── design-document.md            产品设计：用户旅程（Step 0.1）、数据模型（Step 0.1）
    ├── api-contract.md               接口契约：前后端 API、错误格式
    ├── backend-implementation-plan.md 后端计划：API、存储、数据模型
    ├── frontend-implementation-plan.md 前端计划：页面、交互、mock
    ├── agent-implementation-plan.md   Agent 计划：执行器、产物协议
    ├── agent-orchestration-design.md  Agent 设计：多 Agent 工作流（Agent Prototype Step 1）、状态字段（Agent Prototype Step 1）
    ├── design.md                     设计系统：视觉规则（Step 0.1）、组件规则（Step 0.1）
    ├── implementation-plan.md        计划索引：三端入口、集成验收
    ├── pages-design.md               页面设计：页面组件、Console 输出规范
    ├── superpowers/                  计划文档：实现计划（Agent Prototype Step 1）
    ├── tech-stack.md                 技术栈：选型记录（Step 0.1）、架构方向（Step 0.1）
    └── progress.md                   进度文档：功能索引（Step 0.1）、待补边界（Step 0.1）
```
