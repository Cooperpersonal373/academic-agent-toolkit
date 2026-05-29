from __future__ import annotations

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.traceback import install as install_rich_traceback

from academic_agent_toolkit.branding import APP_NAME, BANNER
from academic_agent_toolkit.theme import Colors


install_rich_traceback(show_locals=False)
console = Console()


def show_banner() -> None:
    console.print(
        Panel.fit(
            f"[bold {Colors.TEXT}]{BANNER}[/bold {Colors.TEXT}]\n\n[bold {Colors.TEXT}]{APP_NAME}[/bold {Colors.TEXT}]",
            border_style=Colors.BORDER,
            box=box.DOUBLE,
            padding=(1, 2),
        )
    )


def make_table(*, title: str, columns: list[str]) -> Table:
    table = Table(title=title, box=box.ROUNDED, header_style=f"bold {Colors.PRIMARY}", border_style=Colors.BORDER)
    for column in columns:
        table.add_column(column)
    return table


def status_label(ok: bool) -> str:
    return f"[{Colors.SUCCESS}]ok[/{Colors.SUCCESS}]" if ok else f"[{Colors.WARNING}]check[/{Colors.WARNING}]"
