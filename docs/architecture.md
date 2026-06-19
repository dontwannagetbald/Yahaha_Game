# 项目 Layer 与文件职责

本文档只维护当前项目 layer、目录边界和文件职责。完成度、已实现功能和待补齐边界记录在 [progress.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/progress.md)。

```text
.
├── AGENTS.md                         协作规则：中文响应（Step 0.1）、文档分工（Step 0.1）
├── README.md                         启动说明：Compose 命令（Step 1.3）、端口说明（Step 1.3）
├── prd.md                            原始需求：需求留存（Step 0.1）、验收约束（Step 0.1）
├── .env.example                      环境样例：前后端地址（Step 0.3）、存储模型变量（Step 0.3）
├── .gitignore                        忽略规则：依赖排除（Step 0.1）、缓存排除（Step 0.1）
├── docker-compose.yml                本地编排：基础服务（Step 1.1）、配置透传（Step 2.4）
├── backend/                          后端层：API 边界（Step 0.2）、测试边界（Step 0.2）
│   ├── Dockerfile                    后端镜像：依赖安装（Step 1.1）、迁移启动（Step 2.2）
│   ├── .dockerignore                 构建忽略：缓存排除（Step 1.1）、镜像瘦身（Step 1.1）
│   ├── requirements.txt              依赖清单：FastAPI 依赖（Step 2.1）、迁移依赖（Step 2.2）、Auth 测试依赖（Step 3）
│   ├── pytest.ini                    测试配置：导入路径（Step 2.1）
│   ├── alembic.ini                   迁移配置：脚本定位（Step 2.2）、连接配置（Step 2.2）
│   ├── app/                          应用包：代码边界（Step 0.2）
│   │   ├── __init__.py               包标记：模块导入（Step 0.2）
│   │   ├── auth.py                   认证路由：邮箱登录注册（Step 3）、Google 回跳（Step 3）、GitHub 占位（Step 3）
│   │   ├── config.py                 配置读取：根目录 .env（Step 3）、启动校验（Step 2.4）
│   │   ├── db.py                     数据库层：异步引擎（Step 2.2）、会话依赖（Step 2.2）
│   │   ├── main.py                   API 入口：健康检查（Step 2.1）、错误格式（Step 2.1）、Auth router 挂载（Step 3）
│   │   ├── models.py                 数据模型：users/sessions/oauth_accounts（Step 2.3）
│   │   ├── schemas.py                API schema：Auth 请求响应（Step 3）
│   │   └── security.py               安全工具：密码哈希与校验（Step 3）
│   ├── migrations/                   迁移层：迁移环境（Step 2.2）、版本目录（Step 2.2）
│   │   ├── env.py                    迁移入口：异步连接（Step 2.2）、配置注入（Step 2.2）
│   │   ├── script.py.mako            迁移模板：版本生成（Step 2.2）
│   │   └── versions/                 迁移版本：版本边界（Step 2.2）
│   │       └── 0001_initial.py       初始迁移：users/sessions/oauth_accounts（Step 2.3）
│   └── tests/                        测试层：后端测试（Step 0.2）
│       ├── test_auth.py              认证测试：邮箱登录注册（Step 3）、Google OAuth 回跳（Step 3）
│       ├── test_config.py            配置测试：根目录 .env（Step 3）、校验规则（Step 2.4）
│       └── test_health.py            健康测试：接口断言（Step 2.1）、就绪断言（Step 2.2）
├── frontend/                         前端层：SPA 边界（Step 0.2）、构建边界（Step 0.2）
│   ├── Dockerfile                    前端镜像：依赖安装（Step 1.1）、Vite 启动（Step 1.1）
│   ├── .dockerignore                 构建忽略：依赖排除（Step 1.1）、产物排除（Step 1.1）
│   ├── package.json                  包配置：脚本定义（Step 8.1）、依赖声明（Step 8.1）
│   ├── package-lock.json             依赖锁定：版本固定（Step 8.1）
│   ├── index.html                    HTML 入口：Root 挂载（Step 8.1）
│   ├── tsconfig.json                 TS 配置：前端编译（Step 8.1）
│   ├── tsconfig.node.json            Node TS 配置：Vite 编译（Step 8.1）
│   ├── vite.config.ts                Vite 配置：React 插件（Step 8.1）、开发服务（Step 8.1）
│   ├── vite.config.js                Vite 配置副本：待收敛
│   ├── vite.config.d.ts              类型声明：待评估
│   ├── src/                          前端源码：页面入口（Step 0.2）
│   │   ├── main.tsx                  渲染入口：Root 创建（Step 8.1）、样式加载（Step 8.1）
│   │   ├── App.tsx                   应用壳：静态页面（Frontend Step 1）、状态切换（Frontend Step 1）
│   │   ├── styles.css                全局样式：Yahaha 视觉（Frontend Step 1）、响应式布局（Frontend Step 1）
│   │   └── vite-env.d.ts             类型声明：Vite 类型（Step 8.1）
│   └── scripts/                      前端脚本：验证脚本（Frontend Step 1）
│       └── check-static-ui.mjs       静态检查：界面标记（Frontend Step 1）、禁用调试面板（Frontend Step 1）
├── deployment/                       部署层：目录边界（Step 0.2）
│   ├── .gitkeep                      占位文件：目录保留（Step 0.2）
│   └── minio-init.sh                 存储初始化：Bucket 创建（Step 1.2）、Prefix 策略（Step 1.2）
├── scripts/                          脚本层：目录边界（Step 0.2）
│   └── .gitkeep                      占位文件：目录保留（Step 0.2）
└── docs/                             文档层：设计文档（Step 0.2）、交付记录（Step 0.2）
    ├── architecture.md               架构文档：Layer 维护（Step 0.1）、文件职责（Step 0.2）
    ├── design-document.md            产品设计：用户旅程（Step 0.1）、数据模型（Step 0.1）
    ├── api-contract.md               接口契约：前后端 API、错误格式
    ├── backend-implementation-plan.md 后端计划：API、存储、数据模型
    ├── frontend-implementation-plan.md 前端计划：页面、交互、mock
    ├── agent-implementation-plan.md   Agent 计划：执行器、产物协议
    ├── design.md                     设计系统：视觉规则（Step 0.1）、组件规则（Step 0.1）
    ├── implementation-plan.md        计划索引：三端入口、集成验收
    ├── pages-design.md               页面设计：页面组件、Console 输出规范
    ├── tech-stack.md                 技术栈：选型记录（Step 0.1）、架构方向（Step 0.1）
    └── progress.md                   进度文档：功能索引（Step 0.1）、待补边界（Step 0.1）
```
