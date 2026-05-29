from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated

import typer
from rich import box
from rich.panel import Panel
from rich.table import Table

from academic_agent_toolkit.branding import SHORT_NAME
from academic_agent_toolkit.config import DEFAULT_ENV_FILE, load_config, save_config
from academic_agent_toolkit.installer import ensure_env_template
from academic_agent_toolkit.theme import Colors
from academic_agent_toolkit.ui import console

KEYS = [
    {
        "key": "PAPER_SEARCH_MCP_UNPAYWALL_EMAIL",
        "required": True,
        "recommended": False,
        "description": "Email for Unpaywall DOI-to-OA resolver; Unpaywall is disabled without it.",
        "how_to_get": "https://unpaywall.org/products/api",
        "validation": "email",
    },
    {
        "key": "PAPER_SEARCH_MCP_CORE_API_KEY",
        "required": False,
        "recommended": True,
        "description": "CORE open-access repository; improves rate limits and avoids timeouts.",
        "how_to_get": "https://core.ac.uk/services/api",
        "validation": None,
    },
    {
        "key": "PAPER_SEARCH_MCP_SEMANTIC_SCHOLAR_API_KEY",
        "required": False,
        "recommended": True,
        "description": "Semantic Scholar; works without a key but rate-limited. Key improves limits substantially.",
        "how_to_get": "https://www.semanticscholar.org/product/api",
        "validation": None,
    },
    {
        "key": "PAPER_SEARCH_MCP_GOOGLE_SCHOLAR_PROXY_URL",
        "required": False,
        "recommended": False,
        "description": "HTTP/HTTPS proxy URL to bypass Google Scholar bot-detection (CAPTCHA).",
        "how_to_get": "Your own proxy or provider URL",
        "validation": "url",
    },
    {
        "key": "PAPER_SEARCH_MCP_DOAJ_API_KEY",
        "required": False,
        "recommended": False,
        "description": "Directory of Open Access Journals; free key raises hourly rate limit.",
        "how_to_get": "https://doaj.org/apply-for-api-key/",
        "validation": None,
    },
    {
        "key": "PAPER_SEARCH_MCP_ZENODO_ACCESS_TOKEN",
        "required": False,
        "recommended": False,
        "description": "Zenodo token for accessing private records (public records work without it).",
        "how_to_get": "https://zenodo.org/account/settings/applications/",
        "validation": None,
    },
    {
        "key": "PAPER_SEARCH_MCP_IEEE_API_KEY",
        "required": False,
        "recommended": False,
        "description": "IEEE Xplore; required to activate the IEEE connector (skeleton otherwise).",
        "how_to_get": "https://developer.ieee.org/",
        "validation": None,
    },
    {
        "key": "PAPER_SEARCH_MCP_ACM_API_KEY",
        "required": False,
        "recommended": False,
        "description": "ACM Digital Library; required to activate the ACM connector (skeleton otherwise).",
        "how_to_get": "https://libraries.acm.org/digital-library/acm-open",
        "validation": None,
    },
]


def _validate_email(value: str) -> tuple[bool, str]:
    if not value.strip():
        return False, "email is required for Unpaywall; it cannot be empty"
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value):
        return False, "does not look like a valid email address"
    return True, ""


def _validate_url(value: str) -> tuple[bool, str]:
    if value.strip() and not value.startswith(("http://", "https://")):
        return False, "proxy URL must start with http:// or https://"
    return True, ""


_VALIDATORS = {"email": _validate_email, "url": _validate_url}


def _parse_env(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    if not path.exists():
        return result
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        result[key.strip()] = value.strip()
    return result


def _write_env(path: Path, values: dict[str, str]) -> None:
    existing = _parse_env(path)
    merged = {**existing, **values}
    lines = [f"{key}={merged[key]}" for key in sorted(merged)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def show_keys_table() -> Table:
    table = Table(title="Paper Search MCP - API Keys", box=box.ROUNDED, header_style=f"bold {Colors.PRIMARY}", border_style=Colors.BORDER)
    table.add_column("Variable", style=Colors.TEXT)
    table.add_column("Required?", width=9)
    table.add_column("Recommended?", width=12)
    table.add_column("Description")
    for spec in KEYS:
        required = f"[bold {Colors.ERROR}]yes[/bold {Colors.ERROR}]" if spec["required"] else "optional"
        recommended = f"[bold {Colors.SUCCESS}]yes[/bold {Colors.SUCCESS}]" if spec.get("recommended") else "optional"
        table.add_row(spec["key"], required, recommended, spec["description"])
    return table


def configure_keys(env_file: Path, *, dry_run: bool = False) -> None:
    console.print(show_keys_table())
    if dry_run:
        console.print(Panel.fit(f"[{Colors.WARNING}]Dry-run: would walk through each key interactively.[/]", border_style=Colors.WARNING))
        return
    if not env_file.exists():
        ensure_env_template(env_file)
    console.print(
        Panel.fit(
            f"[{Colors.TEXT}]Press Enter to skip an optional key. Required keys will prompt until valid.[/]\nLeave the field empty to keep the current value (shown in brackets).",
            border_style=Colors.BORDER_ACTIVE,
        )
    )

    existing = _parse_env(env_file)
    new_values: dict[str, str] = {}

    for spec in KEYS:
        key = spec["key"]
        current = existing.get(key, "")
        is_required = spec["required"]
        label = f"[bold {Colors.ERROR}]REQUIRED[/bold {Colors.ERROR}]" if is_required else "optional"

        console.print(f"\n[bold {Colors.TEXT}]{key}[/bold {Colors.TEXT}] ({label})")
        console.print(f"[dim {Colors.TEXT_SECONDARY}]{spec['description']}[/]")
        console.print(f"[dim {Colors.TEXT_SECONDARY}]Get it: {spec['how_to_get']}[/]")

        while True:
            prompt_text = f"Value [{current or 'empty'}]: "
            value = typer.prompt(prompt_text, default="", show_default=False)
            if not value.strip():
                if is_required and not current:
                    console.print(f"[{Colors.ERROR}]This key is required. Please provide a value.[/]")
                    continue
                break
            validator = _VALIDATORS.get(spec.get("validation") or "")
            if validator:
                ok, msg = validator(value)
                if not ok:
                    console.print(f"[{Colors.ERROR}]{msg}[/]")
                    if is_required:
                        continue
                    break
            new_values[key] = value
            break

    if not new_values:
        console.print(f"[{Colors.WARNING}]No new keys were entered. Env file unchanged.[/]")
        return

    if dry_run:
        console.print(f"\n[{Colors.SUCCESS}]Would write {len(new_values)} key(s) to {env_file}[/]")
        for key, value in sorted(new_values.items()):
            masked = value[:4] + "****" if len(value) > 4 else "****"
            console.print(f"  [dim {Colors.TEXT_SECONDARY}]{key}={masked}[/]")
        return

    _write_env(env_file, new_values)
    console.print(f"[{Colors.SUCCESS}]Wrote {len(new_values)} key(s) to {env_file}[/]")
    config = load_config()
    config.env_file = str(env_file)
    save_config(config)


def register_key_command(app: typer.Typer) -> None:
    @app.command("setup-keys")
    def setup_keys(
        env_file: Annotated[str, typer.Option(help=f"Path to the .env file (default {DEFAULT_ENV_FILE})")] = str(
            DEFAULT_ENV_FILE
        ),
        dry_run: Annotated[bool, typer.Option(help="Preview changes without writing")] = False,
    ) -> None:
        """Configure Paper Search MCP API keys interactively with guidance per key."""
        from academic_agent_toolkit.cli import _show_banner_once

        _show_banner_once()
        path = Path(env_file).expanduser().resolve()
        console.print(
            Panel.fit(
                f"[bold {Colors.TEXT}]{SHORT_NAME} setup-keys[/bold {Colors.TEXT}]\nInteractive credential setup for Paper Search MCP.",
                border_style=Colors.BORDER_ACTIVE,
            )
        )
        configure_keys(path, dry_run=dry_run)
        console.print(
            f"\n[bold {Colors.SUCCESS}]Done.[/bold {Colors.SUCCESS}] Keys are stored in [{Colors.TEXT}]{path}[/].\n"
            f"Paper Search MCP reads them via [{Colors.TEXT}]PAPER_SEARCH_MCP_ENV_FILE[/] automatically."
        )
