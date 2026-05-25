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
    console.print(f"ARS source: {ars_status} {ars_detail}")
    console.print(f"Managed ARS: {summary['managed_ars_source']}")
    console.print(f"Env file:   {env_status} {summary['env_file']}")

    table = make_table(title="Agent Detection", columns=["Agent", "Detected", "Skills", "MCP", "Notes"])
    for agent in summary["agents"]:
        table.add_row(
            agent.name,
            status_label(agent.detected),
            "yes" if agent.skill_supported else "no",
            "yes" if agent.mcp_supported else "no",
            agent.note,
        )
    console.print(table)


@app.command()
def install(
    ars_source: Annotated[str | None, typer.Option(help="Path to an existing Academic Research Suite source tree")] = None,
    env_file: Annotated[str, typer.Option(help="Private .env file for Paper Search MCP keys")] = str(DEFAULT_ENV_FILE),
    bootstrap: Annotated[
        bool,
        typer.Option(
            "--bootstrap/--no-bootstrap",
            help=f"Download ARS {ARS_REF} and experiment-agent {EXPERIMENT_AGENT_REF} if no local source exists",
        ),
    ] = True,
    replace_skills: Annotated[bool, typer.Option(help="Replace existing skill directories after backup")] = False,
    replace_mcp: Annotated[bool, typer.Option(help="Replace existing paper-search-mcp entries after backup")] = False,
    include_codex: Annotated[bool, typer.Option(help="Also install the Codex skill adapter if safe")] = False,
    dry_run: Annotated[bool, typer.Option(help="Preview changes without writing files")] = False,
    yes: Annotated[bool, typer.Option("--yes", help="Skip confirmation prompts")] = False,
) -> None:
    """Install skill adapters and MCP configs with one guided command."""
    _show_banner_once()
    config = load_config()
    try:
        resolved = resolve_ars_source(explicit=ars_source, config=config, bootstrap=bootstrap, dry_run=dry_run)
    except RuntimeError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    ars_path = resolved.path
    env_path = Path(env_file).expanduser().resolve()
    skill_agents = _selected_skill_agents(include_codex)
    mcp_agents = default_mcp_agents()

    if not skill_agents and not mcp_agents:
        console.print("[red]No supported agents were detected on this machine.[/red]")
        raise typer.Exit(code=1)

    summary = make_table(title="Install Plan", columns=["Type", "Targets"])
    summary.add_row("ARS source", f"{ars_path} ({resolved.mode}; {resolved.message})")
    summary.add_row("Env file", str(env_path))
    summary.add_row("Skill adapters", ", ".join(skill_agents) if skill_agents else "none")
    summary.add_row("MCP configs", ", ".join(mcp_agents) if mcp_agents else "none")
    summary.add_row("Conflict policy", f"skills={'replace' if replace_skills else 'adopt/skip'}, mcp={'replace' if replace_mcp else 'adopt/skip'}")
    console.print(summary)

    if not yes and not dry_run:
        typer.confirm("Apply this installation plan?", abort=True)

    with console.status("Applying installation plan...", spinner="dots"):
        results = install_all(
            ars_source=ars_path,
            env_file=env_path,
            skill_agents=skill_agents,
            mcp_agents=mcp_agents,
            replace_skills=replace_skills,
            replace_mcp=replace_mcp,
            dry_run=dry_run,
            ars_source_mode=resolved.mode,
            ars_version=resolved.version,
        )

    result_table = make_table(title="Install Results", columns=["Status", "Message"])
    for message in results:
        result_table.add_row("done", message)
    console.print(result_table)

    console.print(
        Panel.fit(
            f"[bold green]Next[/bold green]\nRun `[white]{SHORT_NAME.lower()} verify[/white]` to confirm everything.\nAdd your paper-search keys to `[white]{env_path}[/white]`.\n\nClaude Code: run\n[cyan]{claude_command(env_path)}[/cyan]",
            border_style="green",
        )
    )


@app.command()
def verify() -> None:
    """Verify that skill adapters and MCP registrations are in place."""
    _show_banner_once()
    config = load_config()
    ars_source = discover_ars_source(config)

    skill_table = make_table(title="Skill Verification", columns=["Agent", "Status", "Details"])
    any_failure = False
    for agent in config.installed_skill_agents or [item.name for item in detect_agents() if item.skill_supported and item.detected and item.name != "codex"]:
        ok, detail = verify_skill(agent, ars_source)
        skill_table.add_row(agent, status_label(ok), detail)
        any_failure = any_failure or not ok
    console.print(skill_table)

    mcp_table = make_table(title="MCP Verification", columns=["Agent", "Status", "Details"])
    for agent in config.installed_mcp_agents or default_mcp_agents():
        ok, detail = verify_mcp(agent)
        mcp_table.add_row(agent, status_label(ok), detail)
        any_failure = any_failure or not ok
    console.print(mcp_table)

    if any_failure:
        console.print("[yellow]Verification found items that need attention. Run `aat doctor` or `aat install --replace-skills`.[/yellow]")
        raise typer.Exit(code=1)
    console.print("[bold green]Everything looks healthy.[/bold green]")


@app.command()
def repair(
    dry_run: Annotated[bool, typer.Option(help="Preview repair actions")] = False,
    yes: Annotated[bool, typer.Option("--yes", help="Skip confirmation prompts")] = False,
) -> None:
    """Re-apply the last saved configuration."""
    _show_banner_once()
    config = load_config()
    if not config.ars_source or not config.env_file:
        console.print("[red]No saved installation config found. Run `aat install` first.[/red]")
        raise typer.Exit(code=1)
    if not yes and not dry_run:
        typer.confirm("Re-apply the last saved installation configuration?", abort=True)
    with console.status("Repairing installation...", spinner="dots"):
        results = install_all(
            ars_source=Path(config.ars_source).expanduser().resolve(),
            env_file=Path(config.env_file).expanduser().resolve(),
            skill_agents=config.installed_skill_agents,
            mcp_agents=config.installed_mcp_agents,
            replace_skills=True,
            replace_mcp=True,
            dry_run=dry_run,
            ars_source_mode=config.ars_source_mode,
            ars_version=config.ars_version,
        )
    table = make_table(title="Repair Results", columns=["Status", "Message"])
    for message in results:
        table.add_row("done", message)
    console.print(table)


@app.command("self-check")
def self_check_command() -> None:
    """Run local health checks for the AAT runtime."""
    _show_banner_once()
    checks = self_check(load_config())
    table = make_table(title="Self Check", columns=["Check", "Status", "Details"])
    failed = False
    for item in checks:
        table.add_row(item.name, status_label(item.ok), item.detail)
        failed = failed or not item.ok
    console.print(table)
    if failed:
        console.print("[yellow]Some checks need attention. Run `aat install` or update the missing dependency/configuration.[/yellow]")
        raise typer.Exit(code=1)


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
