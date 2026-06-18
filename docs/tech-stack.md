# AI Native 互动游戏平台 - 技术栈

## 已确定技术栈

| 模块 | 技术选型 | 说明 |
| --- | --- | --- |
| 前端 | React + Vite + Ant Design | 以 SPA 方式构建创作者和玩家 Web 应用。Ant Design 用于快速实现表单、上传控件、卡片、表格、进度状态和基础布局。 |
| 后端 | FastAPI | 提供认证、游戏列表、生成任务、上传回调、发布流程和 Play 元数据等 REST API。 |
| 数据库 | PostgreSQL | 存储用户、服务端会话、游戏、生成版本、生成任务、上传素材、Agent 日志和游玩事件。 |
| 对象存储 | MinIO | 使用 S3 兼容的本地对象存储，保存生成游戏 bundle、manifest、封面图和创作者上传素材。后续可无缝迁移到真实 S3/OSS。 |
| Agent 框架 | LangGraph | 编排多步骤生成流程，包括需求解析、游戏策划、代码生成、校验、打包和元数据生成。 |
| 队列 / 异步任务 | FastAPI BackgroundTasks | MVP 使用 FastAPI 内置后台任务执行生成流程，不引入 Celery。任务状态持久化到 PostgreSQL，方便前端查询进度。 |
| 模型服务 | OpenAI-compatible API 为主，Mock provider 兜底 | Demo 和生产路径使用真实 OpenAI-compatible API。Mock provider 仅用于本地兜底、确定性测试和 CI。所需配置写入 `.env.example`，不提交真实密钥。 |
| 部署方式 | Docker Compose | 本地通过一条或少量命令启动前端、后端、PostgreSQL、MinIO，以及可选的 seed/setup 任务。 |

## 初始架构方向

- 前端通过 HTTP 调用 FastAPI，并根据服务端会话状态渲染受保护页面。
- 后端负责认证、DB-backed session、数据库写入、对象存储签名/上传、生成任务生命周期和已发布游戏元数据。
- Create 请求会先创建持久化的 `generation_job` 记录，再通过 `BackgroundTasks` 运行 LangGraph 工作流。
- 生成结果会被打包为静态 Web 资产，并上传到 MinIO 的稳定对象路径下。
- Play 页面先从后端获取游戏 meta，再从 MinIO 加载对应的 `manifest.json`，最后通过 sandboxed iframe 运行生成的游戏 bundle。
- PostgreSQL 是发布状态、作者、标签、对象路径、manifest URL 和任务进度的事实来源。

## 产品架构决策

### 模型服务

- 主路径使用真实 OpenAI-compatible API。
- Mock provider 仅用于本地兜底和 CI，不作为主要 Demo 能力。
- `.env.example` 需要包含 base URL、API key、model name、provider 选择等环境变量，但不能包含真实密钥。

### 认证与会话

- 使用服务端 session。
- Session ID 存储在 `httpOnly` cookie 中。
- FastAPI session middleware 负责读写会话，会话数据落 PostgreSQL。
- 受保护 API 和 Create 页面必须校验有效登录态。

### 游戏产物格式

每个生成游戏版本以静态 bundle 形式存储，标准结构如下：

```text
manifest.json
index.html
style.css
game.js
assets/*
```

`manifest.json` 是 Play runtime 的核心协议，至少需要包含标题、简介、入口文件、资源列表、操作说明、生成版本和兼容性信息。

### 存储访问策略

- 存储后端使用 MinIO S3-compatible bucket。
- 已发布游戏产物使用 public-read URL，方便 Play 页面直接加载。
- 草稿产物、创作者上传素材和私有源文件使用 presigned URL。
- Create 支持任意文件上传，后端需要记录文件名、MIME type、大小、object key 和用途说明，并通过文件大小限制、扩展名/MIME 校验、下载隔离和后续内容审核降低风险。
- 数据库同时存储 object key 和可访问 URL，保证后续迁移到真实 S3/OSS 时不破坏业务边界。

### Play 运行时

- React Play 页面从 FastAPI 获取游戏 meta。
- Play 页面根据 meta 中的地址从 MinIO 加载 `manifest.json`。
- 生成游戏 bundle 在 sandboxed iframe 中运行。
- 加载或运行失败时必须展示明确错误态，不能白屏。

## 已确认边界

- Create 首版支持任意文件上传。
- 上传文件默认作为私有素材保存，通过 presigned URL 授权访问。
- Agent 可以读取文件元信息和已授权的素材 URL，但生成后的公开游戏产物必须与原始上传素材分开存储。
