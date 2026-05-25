from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

from academic_agent_toolkit.branding import APP_NAME


CONFIG_DIR = Path.home() / ".config" / APP_NAME
CONFIG_PATH = CONFIG_DIR / "config.json"
DATA_DIR = Path.home() / ".local" / "share" / APP_NAME
DEFAULT_ENV_FILE = Path.home() / ".config" / "paper-search-mcp" / ".env"


@dataclass
class ToolkitConfig:
    ars_source: str | None = None
    ars_source_mode: str | None = None
    ars_version: str | None = None
    env_file: str | None = None
    installed_skill_agents: list[str] = field(default_factory=list)
    installed_mcp_agents: list[str] = field(default_factory=list)

    @property
    def ars_source_path(self) -> Path | None:
        return Path(self.ars_source).expanduser().resolve() if self.ars_source else None

    @property
    def env_file_path(self) -> Path | None:
        return Path(self.env_file).expanduser().resolve() if self.env_file else None


def load_config() -> ToolkitConfig:
    if not CONFIG_PATH.exists():
        return ToolkitConfig()
    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    known = {item.name for item in fields(ToolkitConfig)}
    return ToolkitConfig(**{key: value for key, value in data.items() if key in known})


def save_config(config: ToolkitConfig) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(asdict(config), indent=2) + "\n", encoding="utf-8")
