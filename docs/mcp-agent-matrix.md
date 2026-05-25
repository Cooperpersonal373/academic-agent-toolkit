# MCP Agent Matrix

Research date: 2026-05-24.

This matrix records the current MCP config surface checked from official docs or upstream project docs. It is the contract used by the `aat` CLI installer.

| Agent | Config location | Top-level key | Local stdio shape | Source |
|---|---|---|---|---|
| Codex | `~/.codex/config.toml` or project `.codex/config.toml` | `[mcp_servers.<name>]` | `command`, `args`, `env`, optional `cwd` | OpenAI Codex MCP docs: `https://developers.openai.com/codex/mcp` |
| OpenCode | `~/.config/opencode/opencode.json` or project `opencode.json` | `mcp` | `{ "type": "local", "command": [...] }`; local env is `environment` in current config schema | OpenCode MCP docs: `https://opencode.ai/docs/mcp-servers` |
| Claude Code | CLI-managed user/local/project scopes; project `.mcp.json` uses `mcpServers` | `mcpServers` | `{ "command": "...", "args": [], "env": {} }` | Claude Code MCP docs: `https://docs.anthropic.com/en/docs/claude-code/mcp` |
| Cursor | `~/.cursor/mcp.json` or project `.cursor/mcp.json` | `mcpServers` | `{ "command": "...", "args": [], "env": {} }` | Cursor MCP docs: `https://docs.cursor.com/en/context/mcp` |
| VS Code | User profile MCP config or workspace `.vscode/mcp.json` | `servers` | `{ "type": "stdio", "command": "...", "args": [], "env": {} }` | VS Code MCP docs: `https://code.visualstudio.com/docs/copilot/customization/mcp-servers` |
| GitHub Copilot CLI | `~/.copilot/mcp-config.json` | `mcpServers` | `{ "type": "local" | "stdio", "command": "...", "args": [], "env": {}, "tools": [""] }` | GitHub Copilot CLI docs: `https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers` |
| Zed | `~/.config/zed/settings.json` | `context_servers` | `{ "command": "...", "args": [], "env": {} }` | Zed MCP docs: `https://zed.dev/docs/ai/mcp.html` |

## Important Notes

- Zed does not have a native filesystem `skills/` directory like Claude/Codex/OpenCode/Cursor. It uses rules/instructions and forwards configured `context_servers` to external agents through ACP.
- VS Code MCP config uses `servers`, not `mcpServers`.
- GitHub Copilot CLI currently documents `~/.copilot/mcp-config.json` with `mcpServers`; older IDE-oriented examples may use `servers`.
- Claude Code user-scope MCP is safest through `claude mcp add-json --scope user`; direct mutation of `~/.claude.json` is intentionally avoided.
- Paper Search MCP documents `PAPER_SEARCH_MCP_ENV_FILE` as a custom env-file path. This toolkit prefers that single variable over copying API keys into every agent config.
- AAT adopts existing `paper-search-mcp` registrations by default. It only replaces them when the user passes `--replace-mcp`.
- `aat uninstall` removes managed JSON/TOML entries where it can do so safely; JSONC files such as Zed settings may require manual cleanup if comments/trailing commas prevent safe rewriting.
