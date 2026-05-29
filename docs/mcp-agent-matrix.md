# MCP Agent Matrix

Research date: 2026-05-28.

This matrix records the current MCP config surface checked from official docs or upstream project docs. It is the contract used by the `aat` CLI installer.

| Agent | Config location | Top-level key | Local stdio shape | Source |
|---|---|---|---|---|
| Codex | `~/.codex/config.toml` or project `.codex/config.toml` | `[mcp_servers.<name>]` | `command`, `args`, `env`, optional `cwd` | OpenAI Codex MCP docs: `https://developers.openai.com/codex/mcp` |
| OpenCode | `~/.config/opencode/opencode.json` or project `opencode.json` | `mcp` | `{ "type": "local", "command": [...] }`; local env is `environment` in current config schema | OpenCode MCP docs: `https://opencode.ai/docs/mcp-servers` |
| Claude Code | CLI-managed user/local/project scopes; project `.mcp.json` uses `mcpServers` | `mcpServers` | `{ "command": "...", "args": [], "env": {} }` | Claude Code MCP docs: `https://docs.anthropic.com/en/docs/claude-code/mcp` |
| Cursor | `~/.cursor/mcp.json` or project `.cursor/mcp.json` | `mcpServers` | `{ "command": "...", "args": [], "env": {} }` | Cursor MCP docs: `https://docs.cursor.com/en/context/mcp` |
| VS Code | User profile MCP config or workspace `.vscode/mcp.json` | `servers` | `{ "type": "stdio", "command": "...", "args": [], "env": {} }` | VS Code MCP docs: `https://code.visualstudio.com/docs/copilot/customization/mcp-servers` |
| GitHub Copilot CLI | `~/.copilot/mcp-config.json` | `mcpServers` | `{ "type": "local" | "stdio", "command": "...", "args": [], "env": {}, "tools": [""] }` | GitHub Copilot CLI docs: `https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers` |
| Zed | `~/.config/zed/settings.json` | `context_servers` | `{ "source": "custom", "enabled": true, "command": "...", "args": [], "env": {} }` | Zed MCP docs: `https://zed.dev/docs/ai/mcp.html` |

## Important Notes

- Zed has native global skills at `~/.agents/skills/` and project-local skills at `.agents/skills/`. AAT installs `~/.agents/skills/academic-research-suite` and writes an AAT-managed block to `~/.agents/AGENTS.md` for global Zed instructions.
- VS Code MCP config uses `servers`, not `mcpServers`.
- GitHub Copilot CLI currently documents `~/.copilot/mcp-config.json` with `mcpServers`; older IDE-oriented examples may use `servers`.
- GitHub Copilot now supports skills from `~/.agents/skills/` and `~/.copilot/skills/` (global) and `.github/skills/`, `.claude/skills/`, `.agents/skills/` (project). AAT symlinks the canonical `~/.agents/skills/academic-research-suite` to `~/.copilot/skills/academic-research-suite` so Copilot picks it up natively.
- Claude Code stores per-server MCP JSON files under `~/.claude/mcp/`; AAT writes `~/.claude/mcp/paper-search-mcp.json` directly because the installed Claude CLI on Linux does not accept the older `--scope` flag.
- Paper Search MCP documents `PAPER_SEARCH_MCP_ENV_FILE` as a custom env-file path. This toolkit prefers that single variable over copying API keys into every agent config.
- AAT adopts existing `paper-search-mcp` registrations by default. It only replaces them when the user passes `--replace-mcp`.
- `aat uninstall` removes managed JSON/TOML/JSONC entries where it can do so safely. Zed settings are edited textually and backed up first so comments or malformed JSONC outside the managed entry do not force a full-file rewrite.
