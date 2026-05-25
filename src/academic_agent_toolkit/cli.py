from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.panel import Panel

from academic_agent_toolkit import __version__
from academic_agent_toolkit.branding import APP_NAME, SHORT_NAME
from academic_agent_toolkit.config import DEFAULT_ENV_FILE, load_config
from academic_agent_toolkit.installer import (
    ARS_REF,
    EXPERIMENT_AGENT_REF,
    claude_command,
    default_mcp_agents,
    default_skill_agents,
    detect_agents,
    discover_ars_source,
    doctor_summary,
    install_all,
    resolve_ars_source,
    self_check,
    uninstall_all,
    verify_mcp,
    verify_skill,
)
from academic_agent_toolkit.setup_keys import register_key_command
from academic_agent_toolkit.ui import console, make_table, show_banner, status_label


app = typer.Typer(
    name=SHORT_NAME.lower(),
    help="Plug-and-play setup for Academic Research Suite skills and Paper Search MCP across your AI agents.",
    no_args_is_help=True,
    rich_markup_mode="rich",
    pretty_exceptions_show_locals=False,
)

state = {"show_banner": True}


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"[bold cyan]{SHORT_NAME}[/bold cyan] [white]v{__version__}[/white]  —  {APP_NAME}")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: Annotated[bool | None, typer.Option("--version", callback=_version_callback, is_eager=True, help="Show version and exit")] = None,
    no_banner: Annotated[bool, typer.Option("--no-banner", help="Disable the startup banner")] = False,
) -> None:
    state["show_banner"] = not no_banner


def _show_banner_once() -> None:
    if state["show_banner"]:
        show_banner()
        state["show_banner"] = False


def _selected_skill_agents(include_codex: bool) -> list[str]:
    agents = default_skill_agents()
    if include_codex and "codex" not in agents and any(item.name == "codex" and item.detected for item in detect_agents()):
        agents.append("codex")
    return agents


@app.command()
def doctor() -> None:
    """Show environment readiness before installation."""
    _show_banner_once()
    config = load_config()
    summary = doctor_summary(config)
    console.print(Panel.fit("[bold white]Doctor report[/bold white]", border_style="cyan"))

    env_status = status_label(summary["env_exists"])
    ars_status = status_label(summary["ars_valid"])
    ars_detail = summary["ars_source"] or f"not installed; can bootstrap {summary['ars_ref']}"
    console.print(f"  ARS source: {ars_status} {ars_detail}")
    console.print(f"  Managed ARS: {summary['managed_ars_source']}")
    console.print(f"  Env file:   {env_status} {summary['env_file']}")

    table = make_table(title="Agent Detection", columns=["Agent", "Detected", "Skills", "MCP", "Notes"])
    for agent in summary["agents"]:
        table.add_row(
            agent.name,
            status_label(agent.detected),
            "yes" if agent.skill_supported else "no",
            "yes" if agent.mcp_supported else "no",
            agent.note,
        )
    console.print()
    console.print(table)


@app.command()
def uninstall(
    dry_run: Annotated[bool, typer.Option(help="Preview uninstall actions")] = False,
    remove_env: Annotated[bool, typer.Option(help="Also remove the Paper Search MCP env file")] = False,
    remove_managed_ars: Annotated[bool, typer.Option(help="Also remove AAT's downloaded ARS source")] = False,
    yes: Annotated[bool, typer.Option("--yes", help="Skip confirmation prompts")] = False,
) -> None:
    """Remove AAT-managed adapters and MCP registrations safely."""
    _show_banner_once()
    config = load_config()
    console.print(
        Panel.fit(
            "[bold white]Uninstall only removes AAT-managed files.[/bold white]\nExisting user skills or hand-written MCP entries are adopted/skipped, not destroyed.",
            border_style="yellow",
        )
    )
    if not yes and not dry_run:
        typer.confirm("Remove AAT-managed installation?", abort=True)
    results = uninstall_all(
        config=config,
        dry_run=dry_run,
        remove_env=remove_env,
        remove_managed_ars=remove_managed_ars,
    )
    table = make_table(title="Uninstall Results", columns=["Status", "Message"])
    for message in results:
        table.add_row("done", message)
    console.print(table)


@app.command("bootstrap-source", hidden=True)
def bootstrap_source(
    ars_source: Annotated[str, typer.Option(help="Persist the ARS source path for future installs")],
) -> None:
    """Persist a preferred ARS source path."""
    path = Path(ars_source).expanduser().resolve()
    if not path.exists():
        console.print(f"[red]ARS source does not exist: {path}[/red]")
        raise typer.Exit(code=1)
    config = load_config()
    config.ars_source = str(path)
    config.ars_source_mode = "explicit"
    config.ars_version = None
    from academic_agent_toolkit.config import save_config

    save_config(config)
    console.print(f"[green]Saved ARS source:[/green] {path}")


register_key_command(app)


def main() -> int:
    app()
    return 0
