from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import questionary
from questionary import Choice, Separator, Style
from rich import box
from rich.panel import Panel
from rich.table import Table

from academic_agent_toolkit.branding import APP_NAME, BANNER, SHORT_NAME
from academic_agent_toolkit.config import DEFAULT_ENV_FILE
from academic_agent_toolkit.theme import Colors
from academic_agent_toolkit.ui import console


PANEL_WIDTH = 77

TUI_STYLE = Style(
    [
        ("question", "bold"),
        ("pointer", f"fg:{Colors.PRIMARY} bold"),
        ("highlighted", f"fg:{Colors.PRIMARY} bold"),
        ("selected", f"fg:{Colors.SUCCESS}"),
        ("separator", f"fg:{Colors.TEXT_MUTED}"),
        ("instruction", f"fg:{Colors.TEXT_SECONDARY}"),
        ("answer", f"fg:{Colors.SUCCESS} bold"),
        ("disabled", f"fg:{Colors.TEXT_MUTED} italic"),
    ]
)


@dataclass(frozen=True)
class TuiScreen:
    key: str
    title: str
    subtitle: str
    detail: str
    command: str
    result_hint: str


SCREENS = [
    TuiScreen(
        key="doctor",
        title="Doctor",
        subtitle="Environment readiness report",
        detail="Check detected agents, ARS source, managed install paths, and Paper Search MCP env readiness before changing anything.",
        command="aat doctor",
        result_hint="Use this first when something feels off or before a fresh install.",
    ),
    TuiScreen(
        key="install",
        title="Install",
        subtitle="Install skills and MCP configs",
        detail="Build a guided install plan for supported agents, resolve the ARS source, then write managed skill adapters and MCP config entries.",
        command="aat install",
        result_hint="You will still get a confirmation prompt before files are written.",
    ),
    TuiScreen(
        key="setup-keys",
        title="Setup Keys",
        subtitle="Configure Paper Search MCP API keys",
        detail="Walk through required and optional Paper Search MCP credentials with validation and safe defaults.",
        command="aat setup-keys",
        result_hint="Required keys keep prompting until valid; optional keys can be skipped.",
    ),
    TuiScreen(
        key="verify",
        title="Verify",
        subtitle="Confirm everything is in place",
        detail="Verify installed skill adapters and MCP registrations against the saved or discovered installation source.",
        command="aat verify",
        result_hint="Run this after install, repair, or manual config changes.",
    ),
    TuiScreen(
        key="self-check",
        title="Self-Check",
        subtitle="Validate runtime prerequisites",
        detail="Validate Python, uv, ARS source, Paper Search MCP env file, and agent detection in one compact report.",
        command="aat self-check",
        result_hint="This is the fastest sanity check for local machine readiness.",
    ),
    TuiScreen(
        key="repair",
        title="Repair",
        subtitle="Re-apply the last saved installation",
        detail="Use the saved config to re-apply skills and MCP entries with replacement enabled for AAT-managed files.",
        command="aat repair",
        result_hint="Useful after updating agents, changing configs, or recovering a broken setup.",
    ),
    TuiScreen(
        key="update",
        title="Update",
        subtitle="Check for AAT updates",
        detail="Check PyPI for the latest AAT release, upgrade through the detected install method, then optionally re-apply the saved setup.",
        command="aat update",
        result_hint="Requires network access and a detectable pip or uv installation method.",
    ),
    TuiScreen(
        key="uninstall",
        title="Uninstall",
        subtitle="Remove AAT-managed files",
        detail="Safely remove managed skill adapters and MCP registrations without deleting adopted user-authored entries.",
        command="aat uninstall",
        result_hint="You will still get a confirmation prompt before removing anything.",
    ),
]


SCREEN_BY_KEY = {screen.key: screen for screen in SCREENS}


def _footer(text: str = "↑/↓ move  j/k move  enter select  q back/quit  ctrl+c exit") -> Panel:
    return Panel(f"[dim {Colors.TEXT_SECONDARY}]{text}[/]", box=box.SIMPLE, border_style=Colors.BORDER_SUBTLE, width=PANEL_WIDTH)


def _render_shell(title: str, subtitle: str, body: Table | Panel | str, *, footer: str | None = None) -> None:
    console.clear()
    console.print(
        Panel(
            f"[bold {Colors.TEXT}]{SHORT_NAME}[/bold {Colors.TEXT}] [dim {Colors.TEXT_SECONDARY}]::[/] [{Colors.PRIMARY}]{title}[/]\n[dim {Colors.TEXT_SECONDARY}]{subtitle}[/]",
            title=APP_NAME,
            border_style=Colors.BORDER_ACTIVE,
            box=box.ROUNDED,
            padding=(1, 2),
            width=PANEL_WIDTH,
        )
    )
    console.print(body)
    console.print(_footer(footer or "↑/↓ move  j/k move  enter select  q back/quit  ctrl+c exit"))


def _main_menu() -> str | None:
    table = Table.grid(padding=(0, 2))
    table.add_column(style=f"bold {Colors.PRIMARY}", no_wrap=True)
    table.add_column(style=Colors.TEXT)
    table.add_column(style=Colors.TEXT_SECONDARY)

    for screen in SCREENS:
        table.add_row(screen.title, screen.subtitle, screen.command)

    _render_shell(
        "Command Center",
        "Choose a workflow. Each section opens as its own screen before running anything.",
        Panel(table, border_style=Colors.BORDER, box=box.ROUNDED, padding=(1, 2), width=PANEL_WIDTH),
    )

    return questionary.select(
        "Open section",
        choices=[
            *[
                Choice(title=f"{screen.title:<10} — {screen.subtitle}", value=screen.key, shortcut_key=str(index))
                for index, screen in enumerate(SCREENS, start=1)
            ],
            Separator(),
            Choice(title="Quit", value="quit", shortcut_key="q"),
        ],
        qmark="",
        pointer="→",
        style=TUI_STYLE,
        use_arrow_keys=True,
        use_jk_keys=True,
        use_shortcuts=True,
        instruction="Use ↑/↓ or j/k. Enter opens. q quits.",
    ).ask()


def _section_screen(screen: TuiScreen) -> str | None:
    table = Table.grid(padding=(0, 2))
    table.add_column(style=f"bold {Colors.PRIMARY}", no_wrap=True)
    table.add_column(style=Colors.TEXT)
    table.add_row("What it does", screen.detail)
    table.add_row("Command", f"[bold {Colors.TEXT}]{screen.command}[/bold {Colors.TEXT}]")
    table.add_row("Note", screen.result_hint)

    _render_shell(
        screen.title,
        screen.subtitle,
        Panel(table, border_style=Colors.BORDER, box=box.ROUNDED, padding=(1, 2), width=PANEL_WIDTH),
        footer="↑/↓ move  j/k move  enter select  c continue  b/q back  ctrl+c exit",
    )

    return questionary.select(
        "Section actions",
        choices=[
            Choice(title="Continue — run this section", value="continue", shortcut_key="c"),
            Choice(title="Back     — return to command center", value="back", shortcut_key="b"),
            Choice(title="Quit", value="quit", shortcut_key="q"),
        ],
        qmark="",
        pointer="→",
        style=TUI_STYLE,
        use_arrow_keys=True,
        use_jk_keys=True,
        use_shortcuts=True,
        instruction="c continues. b or q goes back/quit. Enter selects.",
    ).ask()


def _continue_screen(screen: TuiScreen) -> str | None:
    console.print()
    return questionary.select(
        "Next",
        choices=[
            Choice(title="Back to command center", value="back", shortcut_key="b"),
            Choice(title="Run this section again", value="again", shortcut_key="r"),
            Choice(title="Quit", value="quit", shortcut_key="q"),
        ],
        qmark="",
        pointer="→",
        style=TUI_STYLE,
        use_arrow_keys=True,
        use_jk_keys=True,
        use_shortcuts=True,
        instruction="b back. r repeat. q quit.",
    ).ask()


def _execute_command(choice: str) -> None:
    from academic_agent_toolkit.cli import doctor, install, repair, state, uninstall, update, verify
    from academic_agent_toolkit.cli import self_check_command
    from academic_agent_toolkit.setup_keys import configure_keys

    state["show_banner"] = False

    runners: dict[str, Callable[[], None]] = {
        "doctor": doctor,
        "install": install,
        "verify": verify,
        "self-check": self_check_command,
        "repair": repair,
        "update": update,
        "uninstall": uninstall,
        "setup-keys": lambda: _run_setup_keys(configure_keys),
    }

    try:
        runners[choice]()
    except SystemExit:
        pass


def _run_setup_keys(configure_keys: Callable[[Path], None]) -> None:
    path = Path(DEFAULT_ENV_FILE).expanduser().resolve()
    console.print(
        Panel(
            f"[bold {Colors.TEXT}]{SHORT_NAME} setup-keys[/bold {Colors.TEXT}]\nInteractive credential setup for Paper Search MCP.",
            border_style=Colors.BORDER_ACTIVE,
            box=box.ROUNDED,
            padding=(1, 2),
            width=PANEL_WIDTH,
        )
    )
    configure_keys(path)


def run_tui() -> int:
    console.print(
        Panel.fit(
            f"[bold {Colors.TEXT}]{BANNER}[/bold {Colors.TEXT}]\n\n[bold {Colors.TEXT}]{APP_NAME}[/bold {Colors.TEXT}]",
            border_style=Colors.BORDER_ACTIVE,
            box=box.DOUBLE,
            padding=(1, 2),
        )
    )
    console.print(
        Panel(f"[dim {Colors.TEXT_SECONDARY}]Press Enter to open the Command Center[/]", border_style=Colors.BORDER_SUBTLE, box=box.SIMPLE, width=PANEL_WIDTH)
    )
    input()

    while True:
        choice = _main_menu()
        if choice is None or choice == "quit":
            console.print(f"\n[dim {Colors.TEXT_SECONDARY}]Goodbye![/]")
            return 0

        screen = SCREEN_BY_KEY[choice]
        action = _section_screen(screen)

        if action is None or action == "quit":
            console.print(f"\n[dim {Colors.TEXT_SECONDARY}]Goodbye![/]")
            return 0
        if action == "back":
            continue

        while action == "continue" or action == "again":
            console.clear()
            _execute_command(screen.key)
            action = _continue_screen(screen)
            if action is None or action == "quit":
                console.print(f"\n[dim {Colors.TEXT_SECONDARY}]Goodbye![/]")
                return 0

        if action == "back":
            continue
