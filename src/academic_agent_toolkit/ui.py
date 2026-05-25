from __future__ import annotations

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.traceback import install as install_rich_traceback

from academic_agent_toolkit.branding import APP_NAME, BANNER


install_rich_traceback(show_locals=False)
console = Console()


def show_banner() -> None:
    console.print(
        Panel.fit(
            f"[bold cyan]{BANNER}[/bold cyan]\n\n[bold white]{APP_NAME}[/bold white]",
            border_style="bright_blue",
            box=box.DOUBLE,
            padding=(1, 2),
        )
    )


def make_table(*, title: str, columns: list[str]) -> Table:
    table = Table(title=title, box=box.ROUNDED, header_style="bold cyan", border_style="blue")
    for column in columns:
        table.add_column(column)
    return table


def status_label(ok: bool) -> str:
    return "[green]ok[/green]" if ok else "[yellow]check[/yellow]"
