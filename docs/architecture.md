# 项目 Layer 与文件职责

本文档只维护当前项目 layer、目录边界和文件职责。完成度、已实现功能和待补齐边界记录在 [progress.md](/Users/root1/workspace/Yahaha_Game/Yahaha_Game/docs/progress.md)。

```text
.
├── AGENTS.md                         协作规则：中文响应（Step 0.1）、文档分工（Step 0.1）
├── README.md                         启动说明：Compose 命令（Step 1.3）、端口说明（Step 1.3）
├── prd.md                            原始需求：需求留存（Step 0.1）、验收约束（Step 0.1）
├── .env.example                      环境样例：前后端地址（Step 0.3）、Agent runner 开关（Backend Agent Step 3）
├── .gitignore                        忽略规则：依赖排除（Step 0.1）、缓存排除（Step 0.1）
├── .dockerignore                     镜像忽略：pycache 排除（Agent Step 1.25）、依赖排除（Agent Step 1.25）
├── docker-compose.yml                本地编排：基础服务（Step 1.1）、真实 Agent runner（Backend Agent Step 3）、前端 Profile（Frontend Step 3.4）
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
│   │   │   ├── state.py              状态模型：游戏卡片（Agent Prototype Step 1）、对话状态（Agent Prototype Step 1）
│   │   │   ├── conversation_graph.py 对话图：游戏卡片产出（Agent Prototype Step 1）、对话状态沉淀（Agent Prototype Step 1）
│   │   │   └── generation_graph.py   生成图：素材分析（Agent Prototype Step 1）、bundle 校验（Agent Prototype Step 1）
│   │   ├── agents/                   Agent 节点：设计节点（Agent Prototype Step 1）、校验节点（Agent Prototype Step 1）
│   │   │   ├── design_agent.py       设计节点：游戏卡片（Agent Prototype Step 1）、对话状态（Agent Prototype Step 1）
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
│   │       ├── state.py              状态导出：游戏卡片（Agent Prototype Step 1）、校验报告（Agent Prototype Step 1）
│   │       └── tools.py              工具导出：manifest/bundle/logging（Agent Prototype Step 1）
│   ├── fixtures/                     原型样本：请求样本（Agent Prototype Step 1）
│   │   └── sample_request.json       样本输入：对话 fixture（Agent Prototype Step 1）、生成 fixture（Agent Prototype Step 1）
│   └── tests/                        原型测试：对话图测试（Agent Prototype Step 1）、CLI 测试（Agent Prototype Step 1）
│       ├── conftest.py               测试配置：包路径注入（Agent Prototype Step 1）
│       ├── test_conversation_graph.py 对话测试：游戏卡片（Agent Prototype Step 1）、对话状态（Agent Prototype Step 1）
│       ├── test_generation_graph.py  生成测试：bundle 产出（Agent Prototype Step 1）、校验失败（Agent Prototype Step 1）
│       ├── test_langsmith_tracing.py tracing 测试：配置解析（Agent Prototype Step 1）、runner tracing（Agent Prototype Step 1）
│       └── test_runner_cli.py        CLI 测试：子命令帮助（Agent Prototype Step 1）、provider 校验（Agent Prototype Step 1）
├── lan_agents/                       Agent 新框架：LangGraph 模板（Agent Step 1.1）、本地 Studio（Agent Step 1.1）、子图分层（Agent Step 1.5a）
│   ├── .env.example                  Agent 环境样例：LangSmith 变量（Agent Step 1.1）、推荐模型变量（Agent Step 1.15）
│   ├── langgraph.json                Graph 配置：conversation 导出（Agent Step 1.1）、generation 导出（Agent Step 7）、revision 导出（Agent Step 11）
│   ├── pyproject.toml                Agent 包配置：依赖声明（Agent Step 1.1）
│   ├── README.md                     Agent 说明：本地运行（Agent Step 1.11）、provider 预检（Agent Step 1.15）
│   ├── fixtures/                     Agent 样本：调试 bundle fixture（Agent Step 6）
│   ├── src/agent/                    Agent 包：graph 导出（Agent Step 1.1）、状态模型（Agent Step 1.2）、子图边界（Agent Step 1.5a）
│   │   ├── __init__.py               包导出：conversation_graph（Agent Step 1.1）、revision_graph（Agent Step 11）
│   │   ├── graph.py                  顶层导出：conversation_graph 兼容（Agent Step 1.5a）、generation_graph 导出（Agent Step 7）、revision_graph 导出（Agent Step 11）
│   │   ├── state.py                  状态模型：对话需求（Agent Step 1.2）、消息历史（Agent Step 1.29）
│   │   ├── providers/                Provider 层：mock LLM（Agent Step 1.13）、模型契约（Agent Step 1.34）
│   │   │   ├── __init__.py           Provider 导出：统一入口（Agent Step 1.13）、预检导出（Agent Step 1.15）
│   │   │   ├── base.py               Provider 基础：配置读取（Agent Step 1.13）、接口协议（Agent Step 1.13）
│   │   │   ├── mock.py               Mock provider：测试响应（Agent Step 1.13）、CI 兜底（Agent Step 1.13）
│   │   │   ├── openai_compatible.py  OpenAI provider：chat completions（Agent Step 1.13）、Responses 附件（Agent Step 3）、包装 file id（Agent Step 3）
│   │   │   └── preflight.py          Provider 预检：配置脱敏（Agent Step 1.15）、推荐模型（Agent Step 1.15）
│   │   ├── conversation_graph/       对话子图：阶段 A 编排（Agent Step 1.5a）、节点分层（Agent Step 1.5a）
│   │   │   ├── __init__.py           子图导出：conversation_graph（Agent Step 1.5a）
│   │   │   ├── demo.py               对话演示：pretty print（Agent Step 1.16）、中性样例（Agent Step 1.25）
│   │   │   ├── graph.py              对话编排：条件边（Agent Step 1.4）、子图入口（Agent Step 1.5a）
│   │   │   ├── events/               事件契约：用户事件（Agent Step 1.5a）
│   │   │   │   ├── __init__.py       事件导出：VALID_EVENT_TYPES（Agent Step 1.5a）
│   │   │   │   └── user_event.py     事件定义：chat/upload/regenerate/confirm（Agent Step 1.5a）
│   │   │   ├── routes/               路由层：事件分支（Agent Step 1.5a）
│   │   │   │   ├── __init__.py       路由导出：route_user_event（Agent Step 1.5a）
│   │   │   │   └── route_user_event/ 路由节点：事件路由（Agent Step 1.5a）
│   │   │   ├── services/             服务层：DesignPlanner（Agent Step 1.13）、早期出卡门禁（Agent Step 1.40）
│   │   │   │   └── tone.py           语气 skill：亲和文案（Agent Step 1.17）、进度守卫（Agent Step 1.28）
│   │   │   └── nodes/                节点层：单节点目录（Agent Step 1.5a）、模型响应透传（Agent Step 1.37）
│   │   ├── generation_graph/         生成子图：阶段 B 边界（Agent Step 1.5a）、完整编排（Agent Step 8）
│   │   │   ├── demo.py               生成演示：固定输出目录（Agent Step 7）、验收摘要（Agent Step 8）
│   │   │   ├── graph.py              生成编排：Orchestrator/Coding/Asset/Debug 流程（Agent Step 7）、Validator 收口（Agent Step 8）
│   │   │   ├── state.py              状态模型：生成任务 state（Agent Step 2）、最终 status（Agent Step 8）
│   │   │   ├── fixtures/             子图样本：confirmed session（Agent Step 2）
│   │   │   ├── orchestrator/         编排节点：并发契约（Agent Step 3）
│   │   │   │   ├── __init__.py       包标记：Orchestrator 导出（Agent Step 3）
│   │   │   │   ├── planner.py        规划器：背景/人物合同（Agent Step 7）、独立封面合同（Agent Step 7）、子 Agent brief（Agent Step 7）
│   │   │   │   ├── demo.py           演示入口：Orchestrator 三图 smoke（Agent Step 3）
│   │   │   │   └── build_parallel_contracts/ 节点目录：并发契约节点（Agent Step 3）
│   │   │   │       ├── __init__.py   节点导出：build_parallel_contracts（Agent Step 3）
│   │   │   │       └── node.py       节点实现：三图合同生成（Agent Step 3）、Planner 调用（Agent Step 3）
│   │   │   ├── asset_agent/          素材节点：三图生成（Agent Step 4）
│   │   │   │   ├── __init__.py       包导出：run_asset_agent（Agent Step 4）
│   │   │   │   ├── demo.py           演示入口：Asset smoke（Agent Step 4）
│   │   │   │   ├── prompt_builder.py Prompt 构建：背景/玩家 prompt（Agent Step 4）、独立封面 prompt（Agent Step 7）
│   │   │   │   ├── run_asset_agent/  节点目录：素材生成节点（Agent Step 4）
│   │   │   │   │   ├── __init__.py   节点导出：run_asset_agent（Agent Step 4）
│   │   │   │   │   └── node.py       节点实现：背景/人物落盘（Agent Step 7）、独立封面生成（Agent Step 7）、上传图 refine（Agent Step 7）
│   │   │   │   └── tools/            素材工具：PNG 编码（Agent Step 4）、品红抠图（Agent Step 4）、图像模型（Agent Step 4）
│   │   │   │       ├── __init__.py   包标记：工具导入（Agent Step 4）
│   │   │   │       ├── image_model.py 图像模型：图片生成（Agent Step 4）、图片编辑（Agent Step 7）
│   │   │   │       ├── image_processing.py 图像处理：背景 mock（Agent Step 4）、角色抠图（Agent Step 7）
│   │   │   │       └── png_codec.py  PNG 工具：RGBA 写入（Agent Step 4）、尺寸读取（Agent Step 4）
│   │   │   ├── coding_agent/         代码节点：草稿生成（Agent Step 5）、自调试（Agent Step 6）
│   │   │   │   ├── __init__.py       包标记：Coding Agent 导出（Agent Step 5）
│   │   │   │   ├── demo.py           演示入口：Coding smoke（Agent Step 5）
│   │   │   │   ├── debug_demo.py     演示入口：Debug smoke（Agent Step 6）、bundle 修复（Agent Step 6）
│   │   │   │   ├── draft_code/       节点目录：草稿代码节点（Agent Step 5）
│   │   │   │   │   ├── __init__.py   节点导出：draft_code（Agent Step 5）
│   │   │   │   │   └── node.py       节点实现：代码落盘（Agent Step 5）、稳态重试（Agent Step 5）
│   │   │   │   └── debug_code_with_assets/ 节点目录：调试代码节点（Agent Step 6）
│   │   │   │       ├── __init__.py   节点导出：debug_code_with_assets（Agent Step 6）
│   │   │   │       └── node.py       节点实现：运行时检查（Agent Step 6）、一轮修复（Agent Step 6）
│   │   │   ├── validator_agent/      验收节点：最终验收（Agent Step 7）、安全扫描（Agent Step 7）
│   │   │   │   ├── __init__.py       包导出：Validator 节点（Agent Step 7）
│   │   │   │   ├── demo.py           演示入口：Validator smoke（Agent Step 7）
│   │   │   │   └── validate_final_delivery/ 节点目录：最终交付验收（Agent Step 7）
│   │   │   │       ├── __init__.py   节点导出：validate_final_delivery（Agent Step 7）
│   │   │   │       └── node.py       节点实现：manifest 校验（Agent Step 7）、runtime 详情（Backend Agent Debug）
│   │   │   └── tools/                子图工具：provider smoke（Agent Step 2）、路径/日志边界（Agent Step 2）、调试检查（Agent Step 6）
│   │   └── revision_graph/           修改子图：生成后修改（Agent Step 11）、revision payload（Agent Step 11）
│   │       ├── __init__.py           子图导出：revision_graph（Agent Step 11）
│   │       ├── graph.py              修改编排：清晰/模糊路由（Agent Step 11）、payload 收口（Agent Step 11）
│   │       ├── state.py              状态模型：revision 输入（Agent Step 11）、payload 输出（Agent Step 11）
│   │       ├── routes/               路由层：修改意图路由（Agent Step 11）
│   │       └── nodes/                节点层：上下文加载（Agent Step 11）、patch 生成（Agent Step 11）
│   └── tests/                        Agent 测试：图加载（Agent Step 1.1）、状态契约（Agent Step 1.2）、结构边界（Agent Step 1.5a）、fixture 覆盖（Agent Step 1.11）
│       ├── fixtures/                 测试样本：五类事件（Agent Step 1.11）、安全输入（Agent Step 1.11）
│       ├── conftest.py               测试配置：anyio 后端（Agent Step 1.1）、mock provider 固定（Agent Step 7）
│       ├── integration_tests/        集成测试：conversation 加载（Agent Step 1.1）、分支执行（Agent Step 1.4）、确认流（Agent Step 1.9）
│       │   ├── test_conversation_flows.py 流程测试：regenerate 保留（Agent Step 1.8）、confirm 校验（Agent Step 1.9）
│       │   ├── test_generation_graph.py 生成图测试：资产路由（Agent Step 7）、最终收口（Agent Step 8）
│       │   ├── test_revision_graph.py 修改图测试：清晰修改（Agent Step 11）、模糊追问（Agent Step 11）
│       │   └── test_graph.py         图测试：conversation invoke（Agent Step 1.1）、状态输出（Agent Step 1.2）、事件路由（Agent Step 1.4）
│       └── unit_tests/               单元测试：配置断言（Agent Step 1.1）、节点断言（Agent Step 1.3）、响应协议（Agent Step 1.10）
│           ├── test_configuration.py 配置测试：Pregel 实例（Agent Step 1.1）、revision 默认状态（Agent Step 11）
│           ├── test_design_planner.py 设计测试：LLM patch 合并（Agent Step 1.13）、早期出卡门禁（Agent Step 1.40）
│           ├── test_design_tone.py   语气测试：单 icon（Agent Step 1.17）、进度守卫（Agent Step 1.28）
│           ├── test_fixtures.py      fixture 测试：事件覆盖（Agent Step 1.11）、敏感信息（Agent Step 1.11）
│           ├── test_asset_agent.py  Asset 测试：背景/人物落盘（Agent Step 7）、独立封面生成（Agent Step 7）、上传图 refine（Agent Step 7）
│           ├── test_coding_agent.py Coding 测试：落盘边界（Agent Step 5）、稳定输出（Agent Step 5）
│           ├── test_coding_debug.py Coding 测试：运行时修复（Agent Step 6）、失败留痕（Agent Step 6）
│           ├── test_generation_provider.py Provider 测试：阶段 B smoke（Agent Step 2）、错误分类（Agent Step 2）
│           ├── test_image_model.py  图片模型测试：生成 payload（Agent Step 4）、编辑 payload（Agent Step 7）
│           ├── test_generation_orchestrator.py Orchestrator 测试：契约对齐（Agent Step 3）、背景/人物决策（Agent Step 7）
│           ├── test_generation_demo.py 生成演示测试：输出摘要（Agent Step 7）、双分支产物（Agent Step 7）
│           ├── test_generation_state.py 状态测试：阶段 B state（Agent Step 2）、子 Agent brief（Agent Step 7）
│           ├── test_llm_provider.py  Provider 测试：响应解析（Agent Step 1.27）、Responses 附件（Agent Step 3）
│           ├── test_material_usage.py 素材测试：安全字段（Agent Step 1.6）、上传合并（Agent Step 1.26）
│           ├── test_nodes.py         节点测试：局部更新（Agent Step 1.3）、需求吸收（Agent Step 1.5）
│           ├── test_plan_generation.py 方案测试：标签过滤（Agent Step 1.7）、简介总结（Agent Step 1.19）、card 字段（Agent Step 1.10）
│           ├── test_project_structure.py 结构测试：子图目录（Agent Step 1.5a）、revision 节点目录（Agent Step 11）
│           ├── test_validator_agent.py Validator 测试：bundle 验收（Agent Step 7）、runtime 详情（Backend Agent Debug）
│           ├── test_regenerate_planner.py 换一换测试：LLM 卡片变体（Agent Step 1.39）、核心字段保留（Agent Step 1.39）
│           ├── test_responses.py     响应测试：建议格式（Agent Step 1.10）、模型响应透传（Agent Step 1.37）
│           └── test_routing.py       路由测试：事件分支（Agent Step 1.4）、非法事件（Agent Step 1.4）
├── backend/                          后端层：API 边界（Step 0.2）、测试边界（Step 0.2）
│   ├── Dockerfile                    后端镜像：依赖安装（Step 1.1）、Agent 源码复制（Agent Step 3）、Node runtime（Backend Agent Debug）
│   ├── .dockerignore                 构建忽略：缓存排除（Step 1.1）、镜像瘦身（Step 1.1）
│   ├── requirements.txt              依赖清单：FastAPI 依赖（Step 2.1）、迁移依赖（Step 2.2）、Auth 测试依赖（Step 3）
│   ├── pytest.ini                    测试配置：导入路径（Step 2.1）
│   ├── alembic.ini                   迁移配置：脚本定位（Step 2.2）、连接配置（Step 2.2）
│   ├── app/                          应用包：代码边界（Step 0.2）
│   │   ├── __init__.py               包标记：模块导入（Step 0.2）
│   │   ├── auth.py                   认证路由：邮箱登录注册（Step 3）、注册头像上传（Frontend Step 3.4）、可选鉴权（Step 4）、游客识别（Step 6）
│   │   ├── agent_runner.py           执行器边界：会话快照输入（Step 8.10）、final state 日志（Backend Agent Debug）
│   │   ├── config.py                 配置读取：根目录 .env（Step 3）、Agent runner 开关（Backend Agent Step 3）
│   │   ├── db.py                     数据库层：异步引擎（Step 2.2）、会话依赖（Step 2.2）
│   │   ├── main.py                   API 入口：健康检查（Step 2.1）、Create Sessions 挂载（Step 7.6）、Swagger 文档（Step 2.5）
│   │   ├── models.py                 数据模型：认证表（Step 2.3）、validation report（Backend Agent Debug）
│   │   ├── schemas.py                API schema：Auth 响应（Step 3）、注册头像 schema（Frontend Step 3.4）、Uploads 响应（Step 3）
│   │   ├── conversation_runner.py    Agent 桥接：lan_agents 图调用（Backend Agent Step 1）、状态归一（Backend Agent Step 1）
│   │   ├── create_sessions.py        会话路由：创建会话（Step 7.6）、历史入图（Agent Step 1.29）
│   │   ├── games.py                  游戏路由：列表筛选（Step 4）、发布接口（Step 9.2）、发布 URL（Step 9.4）
│   │   ├── jobs.py                   任务路由：会话创建任务（Step 8.4）、同会话重做创建（Frontend Step 6.6）、validation report 返回（Backend Agent Debug）
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
│   │       ├── 0002_business_tables.py 业务迁移：游戏任务表（Step 1）、事件日志表（Step 1）
│   │       ├── 0003_create_sessions.py 会话迁移：Create 会话表（Step 7.2）、任务快照（Step 8.2）
│   │       ├── 0004_repair_generation_jobs_session_snapshot.py 修复迁移：任务快照（Step 8.2）、revision 字段（Step 8.17）
│   │       └── 0005_job_validation_report.py 调试迁移：validation report（Backend Agent Debug）
│   └── tests/                        测试层：后端测试（Step 0.2）
│       ├── test_auth.py              认证测试：邮箱登录注册（Step 3）、注册头像上传（Frontend Step 3.4）、Google OAuth 回跳（Step 3）
│       ├── test_agent_runner.py      执行器测试：快照输入（Step 8.9）、final state 日志（Backend Agent Debug）
│       ├── test_config.py            配置测试：根目录 .env（Step 3）、runner 配置（Backend Agent Step 3）、Docker runtime（Backend Agent Debug）
│       ├── test_health.py            健康测试：接口断言（Step 2.1）、就绪断言（Step 2.2）
│       ├── test_migrations.py        迁移测试：Create 会话断言（Step 7.1）、validation report 断言（Backend Agent Debug）
│       ├── test_create_sessions.py   会话测试：消息历史（Step 7.23）、历史入图（Agent Step 1.29）
│       ├── test_games.py             游戏测试：公开列表（Step 4）、详情权限（Step 4）
│       ├── test_likes.py             点赞测试：登录保护（Step 5）、幂等计数（Step 5）
│       ├── test_jobs.py              任务测试：会话创建任务（Step 8.3）、同会话重做创建（Frontend Step 6.6）、revision job（Step 8.17）、日志权限（Step 7）
│       ├── test_play_events.py       事件测试：游客上报（Step 6）、脱敏规则（Step 6）
│       ├── test_publish.py           发布测试：发布权限（Step 9.1）、发布可见（Step 9.5）
│       ├── test_seed.py              种子测试：published 幂等（Step 10）、bundle 契约（Step 10）
│       ├── test_storage.py           存储测试：对象路径（Step 2）、链接边界（Step 2）
│       └── test_uploads.py           上传测试：presign 接口（Step 3）、complete 落库（Step 3）
├── frontend/                         前端层：SPA 边界（Step 0.2）、构建边界（Step 0.2）
│   ├── Dockerfile                    前端镜像：依赖安装（Step 1.1）、Vite 启动（Step 1.1）、可选容器开发（Frontend Step 3.4）
│   ├── .dockerignore                 构建忽略：依赖排除（Step 1.1）、产物排除（Step 1.1）
│   ├── package.json                  包配置：脚本定义（Step 8.1）、Agent 进度校验（Frontend Step 6.9）
│   ├── package-lock.json             依赖锁定：版本固定（Step 8.1）
│   ├── index.html                    HTML 入口：Root 挂载（Step 8.1）
│   ├── tsconfig.json                 TS 配置：前端编译（Step 8.1）
│   ├── tsconfig.node.json            Node TS 配置：Vite 编译（Step 8.1）
│   ├── vite.config.ts                Vite 配置：React 插件（Step 8.1）、开发服务（Step 8.1）、本地 API 代理（Frontend Step 3.4）
│   ├── vite.config.js                Vite 配置副本：待收敛
│   ├── vite.config.d.ts              类型声明：待评估
│   ├── src/                          前端源码：页面入口（Step 0.2）
│   │   ├── main.tsx                  渲染入口：Root 创建（Step 8.1）、BrowserRouter 挂载（Frontend Step 3.4）
│   │   ├── App.tsx                   应用壳：真实路由（Frontend Step 3.4）、Create 发布链路（Frontend Publish）、重做建任务（Frontend Step 6.6）
│   │   ├── api/                      前端 API：请求边界（Frontend Step 2.1）
│   │   │   ├── client.ts             请求入口：cookie 请求（Frontend Step 2.1）、detail 错误解析（Frontend Step 6.6）
│   │   │   ├── auth.ts               Auth 客户端：登录注册（Frontend Step 2.1）、当前用户（Frontend Step 2.1）
│   │   │   ├── create-sessions.ts    Create 客户端：新建会话（Frontend Step 6.2）、事件发送（Frontend Step 6.3）、重新生成契约（Frontend Step 6.5）
│   │   │   ├── games.ts              Games 客户端：列表查询（Frontend Step 4）、发布请求（Frontend Publish）
│   │   │   ├── jobs.ts               Jobs 客户端：任务创建（Frontend Step 6.6）、Job raw 日志（Frontend Debug）
│   │   │   ├── play.ts               Play 客户端：manifest 加载（Frontend Step 5）、事件上报（Frontend Step 5）、iframe 地址解析（Frontend Step 5）
│   │   │   └── uploads.ts            上传客户端：presign 请求（Frontend Step 6.4）、文件直传（Frontend Step 6.4）
│   │   ├── components/               前端组件：导航边界（Frontend Step 3.4）、Auth 弹窗（Frontend Step 3.4）
│   │   │   ├── TopNav.tsx            顶部导航：Home/Create 导航（Frontend Step 3.4）、头像昵称展示（Frontend Step 3.4）、登录区（Frontend Step 3.4）
│   │   │   ├── AuthModal.tsx         Auth 弹窗：表单交互（Frontend Step 3.4）、昵称默认头像注册（Frontend Step 3.4）、字段状态浮层（Frontend Step 3.4）
│   │   │   └── auth-modal.css        Auth 样式：弹窗布局（Frontend Step 3.4）、错误提示（Frontend Step 3.4）、紧凑表单状态位（Frontend Step 3.4）
│   │   ├── lib/                      前端基础库：Console 输出（Frontend Step 3.3）、错误摘要（Frontend Step 3.2）
│   │   │   ├── console.ts            Console 工具：结构化输出（Frontend Step 3.3）、敏感字段脱敏（Frontend Step 3.3）
│   │   │   ├── errors.ts             错误工具：统一弹窗数据（Frontend Step 3.2）、详情字段（Backend Agent Debug）
│   │   │   └── games.ts              游戏映射：卡片字段格式化（Frontend Step 4）、封面兜底（Frontend Step 4）
│   │   ├── mock/                     前端 mock：开关边界（Frontend Step 3.1）、静态数据（Frontend Step 3.1）
│   │   │   └── runtime.ts            mock 运行时：环境开关（Frontend Step 3.1）、validation report mock（Backend Agent Debug）
│   │   ├── pages/                    前端页面：路由页面（Frontend Step 3.4）、页面样式（Frontend Step 3.4）
│   │   │   ├── HomePage.tsx          首页页面：精选推荐选取（Frontend Step 3.4）、Games 列表查询参数（Frontend Step 4）、排序搜索筛选（Frontend Step 4）、Home 点赞入口（Frontend Step 4）
│   │   │   ├── home.css              首页样式：官网式首屏（Frontend Step 3.4）、筛选下划线（Frontend Step 3.4）、搜索空态样式（Frontend Step 3.4）、卡片点赞覆盖层（Frontend Step 4）
│   │   │   ├── CreatePage.tsx        创建页：任务工作台（Frontend Step 3.4）、发布按钮（Frontend Publish）、重做按钮（Frontend Step 6.6）
│   │   │   ├── create.css            创建页样式：工作台布局（Frontend Step 3.4）、卡片加载态（Frontend Step 6.5）、日志面板（Frontend Step 6.8）
│   │   │   ├── PlayPage.tsx          游玩页：无导航布局（Frontend Step 3.4）、点赞与同类流（Frontend Step 3.4）、Games 点赞同步（Frontend Step 4）、manifest/iframe 运行链路（Frontend Step 5）、事件上报与重试（Frontend Step 5）
│   │   │   └── play.css              游玩页样式：满屏自适应（Frontend Step 3.4）、舞台贴屏布局（Frontend Step 3.4）、Play 独立背景（Frontend Step 3.4）、封面进度条蒙版（Frontend Step 3.4）、运行失败态与 iframe（Frontend Step 5）
│   │   ├── styles.css                全局样式：Yahaha 视觉（Frontend Step 1）、错误详情样式（Backend Agent Debug）
│   │   ├── types/                    前端类型：页面类型（Frontend Step 3.4）、游戏类型（Frontend Step 3.4）
│   │   │   └── ui.ts                 UI 类型：页面枚举（Frontend Step 3.4）、展示模型（Frontend Step 3.4）、Games 查询枚举（Frontend Step 4）
│   │   └── vite-env.d.ts             类型声明：Vite 类型（Step 8.1）
│   └── scripts/                      前端脚本：验证脚本（Frontend Step 1）
│       ├── check-static-ui.mjs       静态检查：界面标记（Frontend Step 1）、禁用调试面板（Frontend Step 1）
│       ├── check-auth-client.mjs     Auth 检查：请求入口（Frontend Step 2.1）、本地代理约束（Frontend Step 3.4）、敏感字段约束（Frontend Step 2.1）
│       ├── check-api-error-parsing.mjs API 检查：detail 错误解析（Frontend Step 6.6）、弹窗原因透传（Frontend Step 6.6）
│       ├── check-current-user.mjs    当前用户检查：启动恢复（Frontend Step 2.2）、昵称头像约束（Frontend Step 2.2）
│       ├── check-auth-ui.mjs         Auth 界面检查：表单交互（Frontend Step 2.8）、OAuth 占位（Frontend Step 2.8）
│       ├── check-app-infra.mjs       基础设施检查：mock 开关（Frontend Step 3.1）、Console/错误边界（Frontend Step 3.3）
│       ├── check-routing-structure.mjs 路由检查：页面拆分（Frontend Step 3.4）、Play 无导航（Frontend Step 3.4）
│       ├── check-home-filters.mjs    首页检查：排序搜索逻辑（Frontend Step 4）、放大镜样式（Frontend Step 3.4）、Home 点赞入口（Frontend Step 4）
│       ├── check-home-api.mjs        首页检查：Games API 编排（Frontend Step 4）、查询参数请求（Frontend Step 4）
│       ├── check-play-page.mjs       Play 检查：点赞交互（Frontend Step 4）、同类游戏流（Frontend Step 3.4）
│       ├── check-play-runtime.mjs    Play 检查：manifest/iframe 链路（Frontend Step 5）、事件上报（Frontend Step 5）、重试入口（Frontend Step 5）
│       ├── check-create-layout.mjs   Create 检查：单侧栏折叠任务区（Frontend Step 3.4）、日志面板（Frontend Step 6.8）
│       ├── check-create-session-state.mjs Create 检查：任务会话状态（Frontend Step 6.2）、历史恢复（Frontend Step 6.2）
│       ├── check-validation-report-error.mjs Create 检查：validation report 弹窗（Backend Agent Debug）
│       ├── check-create-chat-event.mjs Create 检查：聊天发送（Frontend Step 6.3）、建议展示（Agent Step 1.30）
│       ├── check-create-tasks.mjs   Create 检查：任务历史（Frontend Step 6.2）、Job raw 日志（Frontend Debug）
│       ├── check-create-confirm-card.mjs Create 检查：确认卡片（Frontend Step 6.5）、重新生成交互（Frontend Step 6.5）
│       ├── check-create-upload-assets.mjs Create 检查：上传绑定（Frontend Step 6.4）、上传气泡过滤（Frontend Step 6.4）
│       ├── check-create-agent-progress.mjs Create 检查：六阶段完成占比（Frontend Step 6.9）、旧文案防回归（Frontend Step 6.9）
│       └── check-create-publish.mjs Create 检查：发布链路（Frontend Publish）
├── deployment/                       部署层：目录边界（Step 0.2）
│   ├── .gitkeep                      占位文件：目录保留（Step 0.2）
│   └── minio-init.sh                 存储初始化：Bucket 创建（Step 1.2）、Prefix 策略（Step 1.2）
├── scripts/                          脚本层：目录边界（Step 0.2）
│   ├── .gitkeep                      占位文件：目录保留（Step 0.2）
│   └── seed_backend.py               种子脚本：published 写入（Step 10）、本地执行入口（Step 10）
└── docs/                             文档层：设计文档（Step 0.2）、交付记录（Step 0.2）
    ├── architecture.md               架构文档：Layer 维护（Step 0.1）、文件职责（Step 0.2）
    ├── design-document.md            产品设计：用户旅程（Step 0.1）、revision 边界（Doc Sync 2026-06-21）
    ├── api-contract.md               接口契约：前后端 API、消息历史（Doc Sync 2026-06-21）
    ├── backend-implementation-plan.md 后端计划：API、revision 任务（Doc Sync 2026-06-21）
    ├── frontend-implementation-plan.md 前端计划：页面、任务会话状态（Doc Sync 2026-06-21）
    ├── agent-implementation-plan.md   Agent 计划：执行器、revision graph（Doc Sync 2026-06-21）
    ├── agent-orchestration-design.md  Agent 设计：多 Agent 工作流（Agent Prototype Step 1）、revision graph（Doc Sync 2026-06-21）
    ├── data-model.md                 数据模型：核心实体（Doc Sync 2026-06-21）、关系约束（Doc Sync 2026-06-21）
    ├── design.md                     设计系统：视觉规则（Step 0.1）、组件规则（Step 0.1）
    ├── images/                       文档插图：架构图（Doc Sync 2026-06-21）
    ├── implementation-plan.md        计划索引：三端入口、revision 验收（Doc Sync 2026-06-21）
    ├── pages-design.md               页面设计：页面组件、任务会话交互（Doc Sync 2026-06-21）
    ├── superpowers/                  计划文档：实现计划（Agent Prototype Step 1）
    ├── tech-stack.md                 技术栈：选型记录（Step 0.1）、revision 方向（Doc Sync 2026-06-21）
    └── progress.md                   进度文档：功能索引（Step 0.1）、待补边界（Doc Sync 2026-06-21）
```
