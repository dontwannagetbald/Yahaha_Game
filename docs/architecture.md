# 项目 Layer 与文件职责

本文档只维护当前项目 layer、目录边界和文件职责。完成度、已实现功能和待补齐边界记录在 [progress.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/progress.md)。

```text
.
├── AGENTS.md                         协作规则：中文响应（Step 0.1）、文档分工（Step 0.1）
├── README.md                         启动说明：Compose 命令（Step 1.3）、检查命令（Step 1.3）
├── prd.md                            原始需求：需求留存（Step 0.1）、验收约束（Step 0.1）
├── .env.example                      环境样例：数据库变量（Step 0.3）、前后端地址（Step 0.3）
├── .gitignore                        忽略规则：依赖排除（Step 0.1）、缓存排除（Step 0.1）
├── docker-compose.yml                本地编排：PostgreSQL 服务（Step 1.1）、前后端服务（Step 1.1）
├── backend/                          后端层：API 边界（Step 0.2）、测试边界（Step 0.2）
│   ├── Dockerfile                    后端镜像：依赖安装（Step 1.1）、服务启动（Step 1.1）
│   ├── .dockerignore                 构建忽略：缓存排除（Step 1.1）、镜像瘦身（Step 1.1）
│   ├── requirements.txt              依赖清单：FastAPI 依赖（Step 2.1）、数据库依赖（Step 2.2）
│   ├── pytest.ini                    测试配置：导入路径（Step 2.1）
│   ├── app/                          应用包：代码边界（Step 0.2）
│   │   ├── __init__.py               包标记：模块导入（Step 0.2）
│   │   ├── config.py                 配置读取：环境加载（Step 2.2）、数据库地址（Step 2.2）
│   │   ├── db.py                     数据库层：异步引擎（Step 2.2）、会话依赖（Step 2.2）
│   │   └── main.py                   API 入口：健康检查（Step 2.1）、就绪检查（Step 2.2）
│   └── tests/                        测试层：后端测试（Step 0.2）
│       └── test_health.py            健康测试：接口断言（Step 2.1）
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
│   └── src/                          前端源码：页面入口（Step 0.2）
│       ├── main.tsx                  渲染入口：Root 创建（Step 8.1）、样式加载（Step 8.1）
│       ├── App.tsx                   应用壳：占位页面（Step 8.1）、API 地址展示（Step 8.1）
│       ├── styles.css                全局样式：基础字体（Step 8.1）、页面壳样式（Step 8.1）
│       └── vite-env.d.ts             类型声明：Vite 类型（Step 8.1）
├── deployment/                       部署层：目录边界（Step 0.2）
│   └── .gitkeep                      占位文件：目录保留（Step 0.2）
├── scripts/                          脚本层：目录边界（Step 0.2）
│   └── .gitkeep                      占位文件：目录保留（Step 0.2）
└── docs/                             文档层：设计文档（Step 0.2）、交付记录（Step 0.2）
    ├── architecture.md               架构文档：Layer 维护（Step 0.1）、文件职责（Step 0.2）
    ├── design-document.md            产品设计：用户旅程（Step 0.1）、数据模型（Step 0.1）
    ├── design.md                     设计系统：视觉规则（Step 0.1）、组件规则（Step 0.1）
    ├── implementation-plan.md        实施计划：Step 指令（Step 0.1）、验证条件（Step 0.1）
    ├── tech-stack.md                 技术栈：选型记录（Step 0.1）、架构方向（Step 0.1）
    └── progress.md                   进度文档：功能索引（Step 0.1）、待补边界（Step 0.1）
```
