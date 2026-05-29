<img src="public/banner.png" alt="Academic Agent Toolkit Banner" style="border-radius: 15px;">

# Academic Agent Toolkit (AAT)

**One command to install academic research skills and paper search across all your AI coding agents.**

Students and researchers use different AI agents (Claude Code, OpenCode, Cursor, Copilot, Codex). Each agent needs different config formats, different file locations, and different skill setups. AAT handles all of that so you can focus on your research.

---

## What you get

| Component | What it does |
|---|---|
| Academic Research Suite | Deep research, lit reviews, systematic reviews, paper drafting, peer review, experiment planning |
| Experiment Agent | Study protocol design, statistical interpretation, reproducibility validation |
| Paper Search MCP | Search 20+ academic sources (arXiv, PubMed, Semantic Scholar, Crossref...) and download PDFs |

All configured across every supported agent in one command. No manual JSON/TOML editing.

---

## Installation

**Prerequisites:** Python 3.11+, [uv](https://docs.astral.sh/uv/getting-started/installation/).

Pick one:

```bash
# No install — run directly (always latest from PyPI)
uvx academic-agent-toolkit doctor

# Persistent install (stays in your PATH)
uv tool install academic-agent-toolkit
aat doctor

# Standard pip
pip install academic-agent-toolkit
aat doctor
```

## Quick Start

```bash
aat doctor      # See what agents are detected
aat install     # Install everything (skills + MCP)
aat setup-keys  # Configure API keys interactively
aat verify      # Confirm everything works
```

---

## How it works

**New users** — `aat install` downloads Academic Research Suite and Experiment Agent automatically, creates a private `.env` file for your API keys, installs one canonical skill in `~/.agents/skills/academic-research-suite`, and configures Paper Search MCP in every detected agent.

**Existing users** — AAT adopts your existing ARS installation and Paper Search MCP registrations. It skips what you already have and only manages what's missing. Use `--replace-skills` or `--replace-mcp` if you want AAT to take over an existing setup.

The `.agents/` layout is the source of truth. Agents with native skill directories get symlinks to the canonical `.agents` skill instead of duplicated copies.

---

## Commands

| Command | What it does |
|---|---|
| `aat doctor` | Show environment readiness and agent detection |
| `aat install` | Install skill adapters and MCP configs with a guided plan |
| `aat setup-keys` | Configure Paper Search MCP API keys interactively |
| `aat verify` | Confirm everything is in place |
| `aat self-check` | Validate runtime prerequisites (Python, uv, ARS source, env file) |
| `aat repair` | Re-apply the last saved installation |
| `aat update` | Check PyPI, upgrade AAT, then re-apply the saved installation |
| `aat uninstall` | Remove AAT-managed files safely (does not touch your own configs) |

---

## API Keys

Paper Search MCP works without most keys, but some sources need credentials. AAT helps you set them up interactively with `aat setup-keys`.

| Variable | Required? | Recommended? | Where to get it |
|---|---|---|---|
| `PAPER_SEARCH_MCP_UNPAYWALL_EMAIL` | **yes** | — | [unpaywall.org](https://unpaywall.org/products/api) |
| `PAPER_SEARCH_MCP_CORE_API_KEY` | no | yes | [core.ac.uk](https://core.ac.uk/services/api) |
| `PAPER_SEARCH_MCP_SEMANTIC_SCHOLAR_API_KEY` | no | yes | [semanticscholar.org](https://www.semanticscholar.org/product/api) |
| `PAPER_SEARCH_MCP_GOOGLE_SCHOLAR_PROXY_URL` | no | no | Your proxy provider |
| `PAPER_SEARCH_MCP_DOAJ_API_KEY` | no | no | [doaj.org](https://doaj.org/apply-for-api-key/) |
| `PAPER_SEARCH_MCP_ZENODO_ACCESS_TOKEN` | no | no | [zenodo.org](https://zenodo.org/account/settings/applications/) |
| `PAPER_SEARCH_MCP_IEEE_API_KEY` | no | no | [developer.ieee.org](https://developer.ieee.org/) |
| `PAPER_SEARCH_MCP_ACM_API_KEY` | no | no | [acm.org](https://libraries.acm.org/digital-library/acm-open) |

Keys are stored in a single private file (`~/.config/paper-search-mcp/.env` by default). Paper Search MCP reads them automatically via `PAPER_SEARCH_MCP_ENV_FILE`. No keys are duplicated across agent configs.

---

## Supported Agents

**Skill adapters** (agent-optimized routers for Academic Research Suite):

- Zed (`~/.agents/skills/` native global skill)
- Claude Code
- OpenCode
- Cursor
- GitHub Copilot (`~/.agents/skills/` and `~/.copilot/skills/` global skills)
- Codex

GitHub Copilot loads skills from `~/.agents/skills/` and `~/.copilot/skills/` globally, and from `.github/skills/`, `.claude/skills/`, and `.agents/skills/` per project. AAT already installs the canonical skill to `~/.agents/skills/` and symlinks to `~/.copilot/skills/`, so Copilot picks it up automatically. VS Code does not expose a global skills directory — it is configured for MCP only.

**MCP configuration** (Paper Search MCP registration):

- Claude Code
- OpenCode
- Cursor
- Codex
- VS Code (user and global)
- GitHub Copilot
- Zed

See `docs/mcp-agent-matrix.md` for the exact config format used per agent.

---

## Install flags

| Flag | Purpose |
|---|---|
| `--no-bootstrap` | Skip automatic ARS download; requires an existing source |
| `--ars-source PATH` | Use a specific ARS source tree |
| `--env-file PATH` | Use a custom `.env` file path |
| `--replace-skills` | Back up and replace existing skill directories |
| `--replace-mcp` | Back up and replace existing MCP entries |
| `--dry-run --yes` | Preview the full plan without writing files |

---

## Uninstall

```bash
aat uninstall
```

Removes only files AAT created. Your existing hand-written configs and skill directories are never touched. Optional flags:

- `--remove-env` also removes the Paper Search MCP env file
- `--remove-managed-ars` also removes AAT's downloaded ARS source

---

## Where files live

| What | Location |
|---|---|
| AAT config | `~/.config/academic-agent-toolkit/config.json` |
| Canonical global skill | `~/.agents/skills/academic-research-suite/` |
| Zed global agent instructions block | `~/.agents/AGENTS.md` |
| Managed ARS source | `~/.local/share/academic-agent-toolkit/ars/` |
| Paper Search MCP env | `~/.config/paper-search-mcp/.env` (default) |
| Skill symlinks | `~/.claude/skills/`, `~/.config/opencode/skills/`, `~/.cursor/skills/`, `~/.codex/skills/` |

---

## Upstream projects

AAT is an integration layer. It bundles and configures these upstream projects with their permission:

- [academic-research-skills](https://github.com/Imbad0202/academic-research-skills) by Imbad0202
- [experiment-agent](https://github.com/Imbad0202/experiment-agent) by Imbad0202
- [paper-search-mcp](https://github.com/openags/paper-search-mcp) by openags

---

## License

MIT — see [LICENSE](LICENSE).
