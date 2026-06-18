# AI Native 互动游戏平台架构记录

本文档记录实施计划推进过程中形成的架构洞察。每完成一个 step 后，补充相关文件边界、模块职责和后续实现约束。

## Step 0.1：仓库现状确认

当前仓库以 `docs/` 作为产品设计、技术选型、实施计划和架构记录的事实来源。根目录的 `prd.md` 保留原始需求输入；`docs/design-document.md` 是 MVP 产品范围、业务状态、数据模型、接口边界、运行时协议和安全边界的整理版；`docs/tech-stack.md` 记录已确认技术栈；`docs/design.md` 记录 Yahaha 风格设计系统；`docs/implementation-plan.md` 定义分阶段执行计划；`docs/architecture.md` 用于持续补充实现后的架构洞察；`docs/progress.md` 预留为交付进度记录。

仓库当前分支为 `main`，首次提交前所有项目文件均处于未跟踪状态。提交时需要避免纳入本地依赖、构建产物、虚拟环境、系统缓存和测试缓存，确保源码仓库只保留可复现项目结构与必要配置。

## Step 0.2：项目目录结构

根目录按前端、后端、部署、脚本和文档划分边界：

- `frontend/`：React + Vite + Ant Design 前端应用目录，承载 SPA 入口、路由、全局样式、前端 Dockerfile、TypeScript 和 Vite 配置。后续 Home、Create、Play 和 Auth Modal 都在该目录内实现。
- `backend/`：FastAPI 后端应用目录，承载 API 入口、配置读取、数据库连接、后端 Dockerfile、依赖声明和测试。后续认证、游戏列表、生成任务、上传、发布和 Play 事件接口都在该目录内实现。
- `deployment/`：部署相关文件目录，当前使用 `.gitkeep` 保留目录边界。后续可放置 MinIO 初始化、环境部署说明、反向代理或其他部署编排文件。
- `scripts/`：项目脚本目录，当前使用 `.gitkeep` 保留目录边界。后续可放置 seed、迁移辅助、示例游戏上传、验收检查和运维脚本。
- `docs/`：设计与交付文档目录，保留产品设计、技术栈、实施计划、架构记录和进度记录，不承载运行时代码。

当前目录结构已经为前端、后端、部署、脚本和文档建立清晰边界，但业务能力仍需按后续 step 逐步实现和验证。
