# Codex Project Instructions

Use Chinese for user-facing responses in this project unless the user asks otherwise.

`superpowers-zh` is installed as Codex user-level skills under:

`/Users/root1/.codex/skills`

Do not use or recreate Claude Code project-level skill files such as `CLAUDE.md` or `.claude/skills`. When a task matches a `superpowers-zh` workflow, use the Codex-discovered user skill instead.

Common relevant skills:

- `using-superpowers`: check available skills before task work.
- `brainstorming`: use before creative feature or behavior changes.
- `systematic-debugging`: use before fixing bugs or abnormal behavior.
- `test-driven-development`: use before implementation when adding or changing behavior.
- `verification-before-completion`: use before claiming work is complete.
- `mcp-builder`: use when building MCP servers or tools.

If a skill conflicts with higher-priority system, developer, or explicit user instructions, follow the higher-priority instruction.

重要提示！！
写任何代码前必须完整阅读docs/@architecture.md
写任何代码前必须完整阅读docs/@design-document.md
要等用户确认step x.x完成后，再进行下一个stepx.x的操作。
文档职责区分：`docs/architecture.md` 只维护项目 layer/layout、目录边界和每个文件的作用；不要在里面写已实现功能索引、完成度汇总或待补齐边界。
`docs/architecture.md` 的文字描述必须使用短格式：`文件作用：xx 功能（Step x.x）、xx 功能（Step x.x）`；文件作用和功能都用几个字概括即可。
文档职责区分：`docs/progress.md` 维护已实现功能索引、完成度、待补齐边界，以及每个已验证 step 的改动说明。
实现 step x.x 并验证通过后，必须在 `docs/architecture.md` 中更新原有 layer/layout，标清楚新增或变化文件的作用，并在相关文件职责后标（Step x.x）体现是哪步引入或更新的。
实现 step x.x 并验证通过后，必须把新的进展添加到 `docs/progress.md` 中，解释做了哪些改动、对应实现了什么功能，并在已实现功能后标（Step x.x）。
实现 step x.x 并验证通过后，在对应 step x.x 里标注 ☑️ 已完成。
每次执行 step x.x 前，如果有疑惑的地方都要提问，和用户确认清楚。