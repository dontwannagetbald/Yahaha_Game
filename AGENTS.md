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
每当用户验证step x.x后，必须把新的架构洞察添加到 architecture.md 中解释每个文件涵盖的的功能与文件的整体作用。
每当用户验证step x.x后，在step x.x里标注☑️已完成。