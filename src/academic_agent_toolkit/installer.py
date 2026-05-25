from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from collections.abc import Callable

from academic_agent_toolkit.config import DATA_DIR, DEFAULT_ENV_FILE, ToolkitConfig, save_config


SERVER_NAME = "paper-search-mcp"
MCP_COMMAND = ["uv", "run", "--with", "paper-search-mcp", "python", "-m", "paper_search_mcp.server"]
ARS_REPO_URL = "https://github.com/Imbad0202/academic-research-skills"
ARS_REF = "v3.9.4.2"
ARS_ARCHIVE_URL = f"{ARS_REPO_URL}/archive/refs/tags/{ARS_REF}.zip"
EXPERIMENT_AGENT_REPO_URL = "https://github.com/Imbad0202/experiment-agent"
EXPERIMENT_AGENT_REF = "v1.1.0"
EXPERIMENT_AGENT_ARCHIVE_URL = f"{EXPERIMENT_AGENT_REPO_URL}/archive/refs/tags/{EXPERIMENT_AGENT_REF}.zip"
MANAGED_ARS_VERSION = f"{ARS_REF}+experiment-agent-{EXPERIMENT_AGENT_REF}"
CORE_ARS_SKILLS = [
    "deep-research",
    "academic-paper",
    "academic-paper-reviewer",
    "academic-pipeline",
]
REQUIRED_ARS_SKILLS = [
    *CORE_ARS_SKILLS,
    "experiment-agent",
]

SKILL_TARGETS = {
    "claude": Path.home() / ".claude" / "skills" / "academic-research-suite",
    "opencode": Path.home() / ".config" / "opencode" / "skills" / "academic-research-suite",
    "cursor": Path.home() / ".cursor" / "skills" / "academic-research-suite",
    "copilot": Path.home() / ".copilot" / "skills" / "academic-research-suite",
    "codex": Path.home() / ".codex" / "skills" / "academic-research-suite",
}

JSON_TARGETS = {
    "opencode": (Path.home() / ".config" / "opencode" / "opencode.json", "mcp"),
    "cursor": (Path.home() / ".cursor" / "mcp.json", "mcpServers"),
    "vscode-user": (Path.home() / ".config" / "Code" / "User" / "mcp.json", "servers"),
    "vscode-global": (Path.home() / ".vscode" / "mcp.json", "servers"),
    "copilot": (Path.home() / ".copilot" / "mcp-config.json", "mcpServers"),
    "zed": (Path.home() / ".config" / "zed" / "settings.json", "context_servers"),
}

DISCOVERY_HINTS = {
    "claude": Path.home() / ".claude",
    "opencode": Path.home() / ".config" / "opencode",
    "cursor": Path.home() / ".cursor",
    "copilot": Path.home() / ".copilot",
    "codex": Path.home() / ".codex",
    "vscode-user": Path.home() / ".config" / "Code" / "User",
    "vscode-global": Path.home() / ".vscode",
    "zed": Path.home() / ".config" / "zed",
}

ARS_SOURCE_CANDIDATES = [
    DATA_DIR / "ars" / MANAGED_ARS_VERSION / "source",
    Path.home() / ".codex" / "skills" / "academic-research-suite" / "ars",
    Path.home() / ".claude" / "skills" / "academic-research-suite" / "ars",
    Path.home() / ".config" / "opencode" / "skills" / "academic-research-suite" / "ars",
    Path.home() / ".cursor" / "skills" / "academic-research-suite" / "ars",
    Path.home() / ".copilot" / "skills" / "academic-research-suite" / "ars",
]

SKILL_TEMPLATES = {
    "codex": """---
name: academic-research-suite
description: >
  Codex adapter for academic research workflows: deep research, literature
  review, systematic review, manuscript drafting, paper review, citation checks,
  research-to-paper pipelines, and experiment planning. Use for ARS aliases such
  as ars-plan, ars-outline, ars-lit-review, ars-revision, and ars-full.
metadata:
  adapter_runtime: codex
---

# Academic Research Suite for Codex

Use this file as the router. Do not load the full suite by default. Read one workflow entrypoint from `ars/`, then load only the files needed for the current phase.

| Intent | Read first |
|---|---|
| Deep research, literature review, systematic review, meta-analysis, fact checking, research question refinement | `ars/deep-research/WORKFLOW.md` or `ars/deep-research/SKILL.md` |
| Paper writing, outline, abstract, revision, citation formatting, AI disclosure, format guidance | `ars/academic-paper/WORKFLOW.md` or `ars/academic-paper/SKILL.md` |
| Peer review simulation, editorial decision, review calibration | `ars/academic-paper-reviewer/WORKFLOW.md` or `ars/academic-paper-reviewer/SKILL.md` |
| End-to-end research-to-paper workflow | `ars/academic-pipeline/WORKFLOW.md` or `ars/academic-pipeline/SKILL.md` |
| Experiment planning, study protocol, statistical interpretation, reproducibility validation | `ars/experiment-agent/WORKFLOW.md` or `ars/experiment-agent/SKILL.md` |

If the user has only a broad paper topic or tentative title without a clear research question, route to the `ars/deep-research` entrypoint in Socratic mode first and ask 3-5 narrowing questions.

Alias routing: treat `/ars-*` and `ars-*` command names as prompt recipes under `ars/commands/`, then route to the matching workflow. If slash-prefixed input is reserved by the client, tell the user to use the plain alias form.

Codex runtime mapping: upstream Claude Code agents are role prompts to execute inline unless the user explicitly asks for delegation or parallel agents.
""",
    "claude": """---
name: academic-research-suite
description: >
  Claude adapter for academic research workflows: deep research, literature
  review, systematic review, manuscript drafting, paper review, citation checks,
  research-to-paper pipelines, and experiment planning.
metadata:
  adapter_runtime: claude
---

# Academic Research Suite for Claude Code

Use this file as the router. Do not load the full suite by default. Read one workflow entrypoint from `ars/`, then load only the files needed for the current phase.

| Intent | Read first |
|---|---|
| Deep research, literature review, systematic review, meta-analysis, fact checking, research question refinement | `ars/deep-research/WORKFLOW.md` or `ars/deep-research/SKILL.md` |
| Paper writing, outline, abstract, revision, citation formatting, AI disclosure, format guidance | `ars/academic-paper/WORKFLOW.md` or `ars/academic-paper/SKILL.md` |
| Peer review simulation, editorial decision, review calibration | `ars/academic-paper-reviewer/WORKFLOW.md` or `ars/academic-paper-reviewer/SKILL.md` |
| End-to-end research-to-paper workflow | `ars/academic-pipeline/WORKFLOW.md` or `ars/academic-pipeline/SKILL.md` |
| Experiment planning, study protocol, statistical interpretation, reproducibility validation | `ars/experiment-agent/WORKFLOW.md` or `ars/experiment-agent/SKILL.md` |

If the user has only a broad paper topic or tentative title without a clear research question, route to the `ars/deep-research` entrypoint in Socratic mode first and ask 3-5 narrowing questions.

Claude runtime mapping: use native Claude Code skills, native slash commands where available, and MCP paper search for current literature checks.
""",
    "opencode": """---
name: academic-research-suite
description: >
  OpenCode adapter for academic research workflows: deep research, literature
  review, systematic review, manuscript drafting, paper review, citation checks,
  research-to-paper pipelines, and experiment planning. Use for ARS aliases such
  as ars-plan, ars-outline, ars-lit-review, ars-revision, and ars-full.
metadata:
  adapter_runtime: opencode
---

# Academic Research Suite for OpenCode

Use this file as the router. Do not load the full suite by default. Read one workflow entrypoint from `ars/`, then load only the files needed for the current phase.

| Intent | Read first |
|---|---|
| Deep research, literature review, systematic review, meta-analysis, fact checking, research question refinement | `ars/deep-research/WORKFLOW.md` or `ars/deep-research/SKILL.md` |
| Paper writing, outline, abstract, revision, citation formatting, AI disclosure, format guidance | `ars/academic-paper/WORKFLOW.md` or `ars/academic-paper/SKILL.md` |
| Peer review simulation, editorial decision, review calibration | `ars/academic-paper-reviewer/WORKFLOW.md` or `ars/academic-paper-reviewer/SKILL.md` |
| End-to-end research-to-paper workflow | `ars/academic-pipeline/WORKFLOW.md` or `ars/academic-pipeline/SKILL.md` |
| Experiment planning, study protocol, statistical interpretation, reproducibility validation | `ars/experiment-agent/WORKFLOW.md` or `ars/experiment-agent/SKILL.md` |

If the user has only a broad paper topic or tentative title without a clear research question, route to the `ars/deep-research` entrypoint in Socratic mode first and ask 3-5 narrowing questions.

OpenCode runtime mapping: upstream ARS agent/team references are role prompts unless the user explicitly requests subagent delegation. Use MCP paper search for current literature and source verification.
""",
    "cursor": """---
name: academic-research-suite
description: >
  Cursor adapter for academic research workflows: deep research, literature
  review, systematic review, manuscript drafting, paper review, citation checks,
  research-to-paper pipelines, and experiment planning.
metadata:
  adapter_runtime: cursor
---

# Academic Research Suite for Cursor

Use this file as the router. Do not load the full suite by default. Read one workflow entrypoint from `ars/`, then load only the files needed for the current phase.

| Intent | Read first |
|---|---|
| Deep research, literature review, systematic review, meta-analysis, fact checking, research question refinement | `ars/deep-research/WORKFLOW.md` or `ars/deep-research/SKILL.md` |
| Paper writing, outline, abstract, revision, citation formatting, AI disclosure, format guidance | `ars/academic-paper/WORKFLOW.md` or `ars/academic-paper/SKILL.md` |
| Peer review simulation, editorial decision, review calibration | `ars/academic-paper-reviewer/WORKFLOW.md` or `ars/academic-paper-reviewer/SKILL.md` |
| End-to-end research-to-paper workflow | `ars/academic-pipeline/WORKFLOW.md` or `ars/academic-pipeline/SKILL.md` |
| Experiment planning, study protocol, statistical interpretation, reproducibility validation | `ars/experiment-agent/WORKFLOW.md` or `ars/experiment-agent/SKILL.md` |

If the user has only a broad paper topic or tentative title without a clear research question, route to the `ars/deep-research` entrypoint in Socratic mode first and ask 3-5 narrowing questions.

Cursor runtime mapping: use the skill as a lightweight router and rely on MCP paper search for current literature retrieval and checking.
""",
    "copilot": """---
name: academic-research-suite
description: >
  Copilot adapter for academic research workflows: deep research, literature
  review, systematic review, manuscript drafting, paper review, citation checks,
  research-to-paper pipelines, and experiment planning.
metadata:
  adapter_runtime: copilot
---

# Academic Research Suite for GitHub Copilot

Use this file as the router. Do not load the full suite by default. Read one workflow entrypoint from `ars/`, then load only the files needed for the current phase.

| Intent | Read first |
|---|---|
| Deep research, literature review, systematic review, meta-analysis, fact checking, research question refinement | `ars/deep-research/WORKFLOW.md` or `ars/deep-research/SKILL.md` |
| Paper writing, outline, abstract, revision, citation formatting, AI disclosure, format guidance | `ars/academic-paper/WORKFLOW.md` or `ars/academic-paper/SKILL.md` |
| Peer review simulation, editorial decision, review calibration | `ars/academic-paper-reviewer/WORKFLOW.md` or `ars/academic-paper-reviewer/SKILL.md` |
| End-to-end research-to-paper workflow | `ars/academic-pipeline/WORKFLOW.md` or `ars/academic-pipeline/SKILL.md` |
| Experiment planning, study protocol, statistical interpretation, reproducibility validation | `ars/experiment-agent/WORKFLOW.md` or `ars/experiment-agent/SKILL.md` |

If the user has only a broad paper topic or tentative title without a clear research question, route to the `ars/deep-research` entrypoint in Socratic mode first and ask 3-5 narrowing questions.

Copilot runtime mapping: treat the skill as routing context and use MCP paper search for fresh citations and validation.
""",
}


@dataclass
class AgentStatus:
    name: str
    detected: bool
    skill_supported: bool
    mcp_supported: bool
    note: str = ""


@dataclass
class ResolvedArsSource:
    path: Path
    mode: str
    version: str | None
    message: str


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def backup(path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    target = path.with_name(f"{path.name}.bak-{stamp}")
    shutil.copy2(path, target)
    return target


def managed_ars_source_path() -> Path:
    return DATA_DIR / "ars" / MANAGED_ARS_VERSION / "source"


def _validate_skill_source(path: Path, required_skills: list[str]) -> tuple[bool, str]:
    missing = [
        item
        for item in required_skills
        if not ((path / item / "WORKFLOW.md").exists() or (path / item / "SKILL.md").exists())
    ]
    if missing:
        return False, "missing entrypoint for " + ", ".join(missing)
    return True, "ARS workflow source is valid"


def validate_ars_source(path: Path) -> tuple[bool, str]:
    return _validate_skill_source(path, REQUIRED_ARS_SKILLS)


def validate_core_ars_source(path: Path) -> tuple[bool, str]:
    return _validate_skill_source(path, CORE_ARS_SKILLS)


def locate_ars_source(root: Path) -> Path | None:
    return locate_source(root, validate_ars_source)


def locate_core_ars_source(root: Path) -> Path | None:
    return locate_source(root, validate_core_ars_source)


def locate_source(root: Path, validator: Callable[[Path], tuple[bool, str]]) -> Path | None:
    candidates = [root]
    candidates.extend(item for item in root.iterdir() if item.is_dir())
    for candidate in candidates:
        ok, _ = validator(candidate)
        if ok:
            return candidate.resolve()
        nested = candidate / "ars"
        if nested.exists():
            ok, _ = validator(nested)
            if ok:
                return nested.resolve()
    return None


def locate_experiment_agent_source(root: Path) -> Path | None:
    candidates = [root]
    candidates.extend(item for item in root.iterdir() if item.is_dir())
    for candidate in candidates:
        if (candidate / "SKILL.md").exists() and (candidate / "agents").is_dir():
            return candidate.resolve()
    return None


def download_and_extract_archive(url: str, archive: Path, extract_dir: Path) -> None:
    try:
        urllib.request.urlretrieve(url, archive)
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not download archive from {url}: {exc}") from exc
    with zipfile.ZipFile(archive) as zip_file:
        zip_file.extractall(extract_dir)


def bootstrap_ars_source(*, dry_run: bool = False) -> ResolvedArsSource:
    target = managed_ars_source_path()
    ok, _ = validate_ars_source(target) if target.exists() else (False, "missing managed ARS source")
    if ok:
        return ResolvedArsSource(target.resolve(), "managed", MANAGED_ARS_VERSION, "using managed ARS source")
    if dry_run:
        return ResolvedArsSource(
            target.resolve(),
            "managed",
            MANAGED_ARS_VERSION,
            f"would download ARS {ARS_REF} and experiment-agent {EXPERIMENT_AGENT_REF}",
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="aat-ars-") as temp_dir:
        temp_path = Path(temp_dir)
        ars_extract = temp_path / "ars-extract"
        experiment_extract = temp_path / "experiment-extract"
        download_and_extract_archive(ARS_ARCHIVE_URL, temp_path / "ars.zip", ars_extract)
        download_and_extract_archive(EXPERIMENT_AGENT_ARCHIVE_URL, temp_path / "experiment-agent.zip", experiment_extract)

        source = locate_core_ars_source(ars_extract)
        if source is None:
            raise RuntimeError(f"Downloaded ARS archive did not contain required workflows: {ARS_ARCHIVE_URL}")
        experiment_source = locate_experiment_agent_source(experiment_extract)
        if experiment_source is None:
            raise RuntimeError(
                f"Downloaded experiment-agent archive did not contain a valid skill: {EXPERIMENT_AGENT_ARCHIVE_URL}"
            )
        staged_source = temp_path / "managed-source"
        shutil.copytree(source, staged_source, symlinks=True)
        shutil.copytree(experiment_source, staged_source / "experiment-agent", symlinks=True)
        ok, detail = validate_ars_source(staged_source)
        if not ok:
            raise RuntimeError(f"Composed ARS source is invalid: {detail}")
        if target.exists():
            backup_target = target.with_name(f"source.backup-{datetime.now().strftime('%Y%m%d%H%M%S')}")
            target.rename(backup_target)
        shutil.copytree(staged_source, target, symlinks=True)
    return ResolvedArsSource(
        target.resolve(),
        "managed",
        MANAGED_ARS_VERSION,
        f"downloaded ARS {ARS_REF} and experiment-agent {EXPERIMENT_AGENT_REF}",
    )


def discover_ars_source(config: ToolkitConfig | None = None) -> Path | None:
    if config and config.ars_source:
        candidate = Path(config.ars_source).expanduser().resolve()
        ok, _ = validate_ars_source(candidate) if candidate.exists() else (False, "missing")
        if ok:
            return candidate
    for candidate in ARS_SOURCE_CANDIDATES:
        ok, _ = validate_ars_source(candidate) if candidate.exists() else (False, "missing")
        if ok:
            return candidate.resolve()
    return None


def resolve_ars_source(
    *,
    explicit: str | None,
    config: ToolkitConfig,
    bootstrap: bool,
    dry_run: bool,
) -> ResolvedArsSource:
    if explicit:
        root = Path(explicit).expanduser().resolve()
        candidate = locate_ars_source(root) if root.exists() and root.is_dir() else None
        if candidate is None:
            raise RuntimeError(f"ARS source is invalid: {root}")
        return ResolvedArsSource(candidate, "explicit", None, "using explicit ARS source")

    if config.ars_source:
        configured = Path(config.ars_source).expanduser().resolve()
        ok, _ = validate_ars_source(configured) if configured.exists() else (False, "missing")
        if ok:
            return ResolvedArsSource(
                configured,
                config.ars_source_mode or "adopted",
                config.ars_version,
                "using saved ARS source",
            )

    for candidate in ARS_SOURCE_CANDIDATES:
        ok, _ = validate_ars_source(candidate) if candidate.exists() else (False, "missing")
        if ok:
            mode = "managed" if candidate == managed_ars_source_path() else "adopted"
            version = MANAGED_ARS_VERSION if mode == "managed" else None
            return ResolvedArsSource(candidate.resolve(), mode, version, f"{mode} existing ARS source")

    if bootstrap:
        return bootstrap_ars_source(dry_run=dry_run)
    raise RuntimeError("Could not find ARS locally and bootstrap is disabled. Pass --ars-source or remove --no-bootstrap.")


def detect_agents() -> list[AgentStatus]:
    return [
        AgentStatus("claude", DISCOVERY_HINTS["claude"].exists(), True, True, "Claude Code skills + CLI-managed MCP"),
        AgentStatus("opencode", DISCOVERY_HINTS["opencode"].exists(), True, True, "OpenCode skills + opencode.json MCP"),
        AgentStatus("cursor", DISCOVERY_HINTS["cursor"].exists(), True, True, "Cursor skills + mcp.json MCP"),
        AgentStatus("copilot", DISCOVERY_HINTS["copilot"].exists(), True, True, "Copilot skills + mcp-config MCP"),
        AgentStatus("codex", DISCOVERY_HINTS["codex"].exists(), True, True, "Codex skill install is optional and cautious"),
        AgentStatus("vscode-user", DISCOVERY_HINTS["vscode-user"].exists(), False, True, "VS Code MCP only"),
        AgentStatus("vscode-global", DISCOVERY_HINTS["vscode-global"].exists(), False, True, "VS Code MCP only"),
        AgentStatus("zed", DISCOVERY_HINTS["zed"].exists(), False, True, "Zed MCP only; no native skills dir"),
    ]


def default_skill_agents() -> list[str]:
    return [status.name for status in detect_agents() if status.detected and status.skill_supported and status.name != "codex"]


def default_mcp_agents() -> list[str]:
    return [status.name for status in detect_agents() if status.detected and status.mcp_supported]


def ensure_env_template(path: Path) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# Paper Search MCP credentials",
                "# Run: aat setup-keys  for interactive guided configuration",
                "",
                "PAPER_SEARCH_MCP_UNPAYWALL_EMAIL=you@example.com",
                "PAPER_SEARCH_MCP_CORE_API_KEY=",
                "PAPER_SEARCH_MCP_SEMANTIC_SCHOLAR_API_KEY=",
                "PAPER_SEARCH_MCP_GOOGLE_SCHOLAR_PROXY_URL=",
                "PAPER_SEARCH_MCP_DOAJ_API_KEY=",
                "PAPER_SEARCH_MCP_ZENODO_ACCESS_TOKEN=",
                "PAPER_SEARCH_MCP_IEEE_API_KEY=",
                "PAPER_SEARCH_MCP_ACM_API_KEY=",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return True


def json_server(agent: str, env_file: Path) -> dict:
    env = {"PAPER_SEARCH_MCP_ENV_FILE": str(env_file)}
    if agent == "opencode":
        return {"type": "local", "enabled": True, "command": MCP_COMMAND, "environment": env}
    if agent in {"vscode-user", "vscode-global"}:
        return {"type": "stdio", "command": MCP_COMMAND[0], "args": MCP_COMMAND[1:], "env": env}
    if agent == "copilot":
        return {"type": "local", "command": MCP_COMMAND[0], "args": MCP_COMMAND[1:], "env": env}
    if agent == "zed":
        return {"command": MCP_COMMAND[0], "args": MCP_COMMAND[1:], "env": env}
    return {"command": MCP_COMMAND[0], "args": MCP_COMMAND[1:], "env": env}


def claude_command(env_file: Path) -> str:
    config = json.dumps(json_server("claude", env_file), separators=(",", ":"))
    return f"claude mcp add-json {SERVER_NAME} --scope user '{config}'"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def install_skill(agent: str, ars_source: Path, replace: bool, dry_run: bool) -> str:
    target = SKILL_TARGETS[agent]
    if agent == "codex" and str(ars_source).startswith(str(target.resolve())):
        raise RuntimeError(
            "Refusing to replace Codex skill because the ARS source lives inside the same Codex target path. Use --ars-source with a separate checkout first."
        )
    if dry_run:
        return f"would install skill adapter for {agent} at {target}"
    target.parent.mkdir(parents=True, exist_ok=True)
    desired = SKILL_TEMPLATES[agent].strip() + "\n"
    if target.exists() or target.is_symlink():
        skill_file = target / "SKILL.md"
        link_file = target / "ars"
        if (
            target.is_dir()
            and skill_file.exists()
            and skill_file.read_text(encoding="utf-8") == desired
            and link_file.is_symlink()
            and link_file.resolve() == ars_source
        ):
            return f"skill already installed for {agent}"
        if not replace:
            return f"skipped existing skill for {agent}; rerun with --replace-skills"
        backup_target = target.with_name(f"{target.name}.backup-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        target.rename(backup_target)
    target.mkdir(parents=True, exist_ok=True)
    (target / "SKILL.md").write_text(desired, encoding="utf-8")
    link = target / "ars"
    if link.exists() or link.is_symlink():
        link.unlink()
    link.symlink_to(ars_source, target_is_directory=True)
    return f"installed skill adapter for {agent}"


def merge_json_config(agent: str, env_file: Path, dry_run: bool, replace: bool) -> str:
    path, top_key = JSON_TARGETS[agent]
    try:
        data = load_json(path)
    except json.JSONDecodeError as exc:
        if agent == "zed":
            text = path.read_text(encoding="utf-8") if path.exists() else ""
            if SERVER_NAME in text:
                return "adopted existing zed MCP entry from JSONC settings"
            return f"skipped zed automatic merge because settings.json is JSONC: {exc}"
        raise RuntimeError(f"Invalid JSON in {path}: {exc}") from exc
    desired = json_server(agent, env_file)
    servers = data.setdefault(top_key, {})
    existing = servers.get(SERVER_NAME)
    if existing is not None and existing != desired and not replace:
        return f"adopted existing MCP config for {agent}; rerun with --replace-mcp to manage it"
    if dry_run:
        return f"would merge MCP config for {agent} into {path}"
    servers[SERVER_NAME] = desired
    if path.exists():
        backup(path)
    write_json(path, data)
    return f"merged MCP config for {agent}"


def codex_block(env_file: Path) -> str:
    return f"""# BEGIN academic-agent-toolkit:{SERVER_NAME}
[mcp_servers.{SERVER_NAME}]
command = \"{MCP_COMMAND[0]}\"
args = {json.dumps(MCP_COMMAND[1:])}

[mcp_servers.{SERVER_NAME}.env]
PAPER_SEARCH_MCP_ENV_FILE = \"{env_file}\"
# END academic-agent-toolkit:{SERVER_NAME}
"""


def merge_codex_config(env_file: Path, dry_run: bool, replace: bool) -> str:
    path = Path.home() / ".codex" / "config.toml"
    begin = f"# BEGIN academic-agent-toolkit:{SERVER_NAME}"
    end = f"# END academic-agent-toolkit:{SERVER_NAME}"
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    block = codex_block(env_file)
    if begin in current and end in current:
        before, rest = current.split(begin, 1)
        _, after = rest.split(end, 1)
        next_text = before.rstrip() + "\n\n" + block + after.lstrip("\n")
    elif SERVER_NAME in current and not replace:
        return "adopted existing MCP config for codex; rerun with --replace-mcp to manage it"
    else:
        next_text = current.rstrip() + "\n\n" + block
    if dry_run:
        return f"would merge MCP config for codex into {path}"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        backup(path)
    path.write_text(next_text, encoding="utf-8")
    return "merged MCP config for codex"


def install_all(
    *,
    ars_source: Path,
    env_file: Path,
    skill_agents: list[str],
    mcp_agents: list[str],
    replace_skills: bool,
    replace_mcp: bool,
    dry_run: bool,
    ars_source_mode: str | None = None,
    ars_version: str | None = None,
) -> list[str]:
    results: list[str] = []
    if dry_run:
        if not env_file.exists():
            results.append(f"would create env template at {env_file}")
    elif ensure_env_template(env_file):
        results.append(f"created env template at {env_file}")
    for agent in skill_agents:
        results.append(install_skill(agent, ars_source, replace_skills, dry_run))
    for agent in mcp_agents:
        if agent == "claude":
            results.append(f"run manually for claude: {claude_command(env_file)}")
        elif agent == "codex":
            results.append(merge_codex_config(env_file, dry_run, replace_mcp))
        else:
            results.append(merge_json_config(agent, env_file, dry_run, replace_mcp))
    if not dry_run:
        save_config(
            ToolkitConfig(
                ars_source=str(ars_source),
                ars_source_mode=ars_source_mode,
                ars_version=ars_version,
                env_file=str(env_file),
                installed_skill_agents=skill_agents,
                installed_mcp_agents=mcp_agents,
            )
        )
    return results


def verify_skill(agent: str, ars_source: Path | None) -> tuple[bool, str]:
    target = SKILL_TARGETS[agent]
    skill_file = target / "SKILL.md"
    link = target / "ars"
    if not target.exists() or not skill_file.exists() or not link.is_symlink():
        return False, "missing skill directory, SKILL.md, or ars symlink"
    if ars_source and link.resolve() != ars_source:
        return False, f"ars symlink points to {link.resolve()} instead of {ars_source}"
    return True, "skill adapter installed"


def verify_mcp(agent: str) -> tuple[bool, str]:
    if agent == "claude":
        return True, "Claude must be verified by running the printed claude mcp add-json command"
    if agent == "codex":
        path = Path.home() / ".codex" / "config.toml"
        if not path.exists():
            return False, "missing ~/.codex/config.toml"
        text = path.read_text(encoding="utf-8")
        return (SERVER_NAME in text, "managed Codex block present" if SERVER_NAME in text else "managed Codex block missing")
    path, top_key = JSON_TARGETS[agent]
    if not path.exists():
        return False, f"missing {path}"
    if agent == "zed":
        text = path.read_text(encoding="utf-8")
        return (SERVER_NAME in text, "paper-search-mcp entry found in JSONC" if SERVER_NAME in text else "paper-search-mcp entry missing")
    try:
        data = load_json(path)
    except json.JSONDecodeError as exc:
        return False, f"invalid JSON: {exc}"
    return (SERVER_NAME in data.get(top_key, {}), f"{SERVER_NAME} found" if SERVER_NAME in data.get(top_key, {}) else f"{SERVER_NAME} missing")


def is_managed_skill(agent: str) -> bool:
    target = SKILL_TARGETS[agent]
    skill_file = target / "SKILL.md"
    if agent not in SKILL_TEMPLATES or not skill_file.exists():
        return False
    expected = SKILL_TEMPLATES[agent].strip() + "\n"
    try:
        return skill_file.read_text(encoding="utf-8") == expected
    except OSError:
        return False


def uninstall_skill(agent: str, dry_run: bool) -> str:
    target = SKILL_TARGETS[agent]
    if not target.exists() and not target.is_symlink():
        return f"skill adapter for {agent} was not installed"
    if not is_managed_skill(agent):
        return f"skipped non-managed skill for {agent}"
    if dry_run:
        return f"would remove skill adapter for {agent} from {target}"
    if target.is_symlink() or target.is_file():
        target.unlink()
    else:
        shutil.rmtree(target)
    return f"removed skill adapter for {agent}"


def remove_json_config(agent: str, env_file: Path, dry_run: bool) -> str:
    path, top_key = JSON_TARGETS[agent]
    if not path.exists():
        return f"MCP config for {agent} was not installed"
    try:
        data = load_json(path)
    except json.JSONDecodeError as exc:
        if agent == "zed" and SERVER_NAME in path.read_text(encoding="utf-8"):
            return f"skipped zed MCP removal because settings.json is JSONC: {exc}"
        return f"MCP config for {agent} was not installed"
    servers = data.get(top_key, {})
    if SERVER_NAME not in servers:
        return f"MCP config for {agent} was not installed"
    if servers[SERVER_NAME] != json_server(agent, env_file):
        return f"skipped non-managed MCP config for {agent}"
    if dry_run:
        return f"would remove MCP config for {agent} from {path}"
    del servers[SERVER_NAME]
    backup(path)
    write_json(path, data)
    return f"removed MCP config for {agent}"


def remove_codex_config(dry_run: bool) -> str:
    path = Path.home() / ".codex" / "config.toml"
    begin = f"# BEGIN academic-agent-toolkit:{SERVER_NAME}"
    end = f"# END academic-agent-toolkit:{SERVER_NAME}"
    if not path.exists():
        return "MCP config for codex was not installed"
    current = path.read_text(encoding="utf-8")
    if begin not in current or end not in current:
        return "skipped non-managed MCP config for codex"
    before, rest = current.split(begin, 1)
    _, after = rest.split(end, 1)
    next_text = before.rstrip() + "\n" + after.lstrip("\n")
    if dry_run:
        return f"would remove MCP config for codex from {path}"
    backup(path)
    path.write_text(next_text, encoding="utf-8")
    return "removed MCP config for codex"


def uninstall_all(
    *,
    config: ToolkitConfig,
    dry_run: bool,
    remove_env: bool,
    remove_managed_ars: bool,
) -> list[str]:
    results: list[str] = []
    skill_agents = config.installed_skill_agents or list(SKILL_TARGETS)
    mcp_agents = config.installed_mcp_agents or ["claude", "codex", *JSON_TARGETS]
    env_file = config.env_file_path or DEFAULT_ENV_FILE
    for agent in skill_agents:
        if agent in SKILL_TARGETS:
            results.append(uninstall_skill(agent, dry_run))
    for agent in mcp_agents:
        if agent == "claude":
            results.append("remove Claude MCP manually with: claude mcp remove paper-search-mcp --scope user")
        elif agent == "codex":
            results.append(remove_codex_config(dry_run))
        elif agent in JSON_TARGETS:
            results.append(remove_json_config(agent, env_file, dry_run))
    if remove_env and env_file.exists():
        if dry_run:
            results.append(f"would remove env file at {env_file}")
        else:
            env_file.unlink()
            results.append(f"removed env file at {env_file}")
    if remove_managed_ars:
        managed = managed_ars_source_path()
        if managed.exists():
            if dry_run:
                results.append(f"would remove managed ARS source at {managed}")
            else:
                shutil.rmtree(managed)
                results.append(f"removed managed ARS source at {managed}")
    if not dry_run:
        save_config(ToolkitConfig(env_file=str(env_file) if env_file.exists() else None))
    return results


def self_check(config: ToolkitConfig | None = None) -> list[CheckResult]:
    current = config or ToolkitConfig()
    results = [
        CheckResult(
            "Python",
            sys.version_info >= (3, 11),
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        ),
        CheckResult("uv", shutil.which("uv") is not None, shutil.which("uv") or "not found in PATH"),
    ]
    source = discover_ars_source(current)
    if source:
        ok, detail = validate_ars_source(source)
        results.append(CheckResult("ARS source", ok, f"{source} ({detail})"))
    else:
        results.append(CheckResult("ARS source", True, f"not installed yet; AAT can bootstrap {MANAGED_ARS_VERSION}"))
    env_file = current.env_file_path or DEFAULT_ENV_FILE
    if env_file.exists():
        text = env_file.read_text(encoding="utf-8", errors="ignore")
        configured = "you@example.com" not in text
        results.append(CheckResult("Paper Search env", configured, f"{env_file}" + ("" if configured else " contains starter placeholders")))
    else:
        results.append(CheckResult("Paper Search env", False, f"missing {env_file}; install will create a template"))
    detected = [agent.name for agent in detect_agents() if agent.detected]
    results.append(CheckResult("Agent detection", bool(detected), ", ".join(detected) if detected else "no supported agent config dirs found"))
    return results


def doctor_summary(config: ToolkitConfig | None = None) -> dict:
    current = config or ToolkitConfig()
    ars_source = discover_ars_source(current)
    ars_valid = validate_ars_source(ars_source)[0] if ars_source else False
    env_file = current.env_file_path or DEFAULT_ENV_FILE
    return {
        "ars_source": ars_source,
        "ars_valid": ars_valid,
        "managed_ars_source": managed_ars_source_path(),
        "ars_ref": MANAGED_ARS_VERSION,
        "env_file": env_file,
        "env_exists": env_file.exists(),
        "agents": detect_agents(),
    }
