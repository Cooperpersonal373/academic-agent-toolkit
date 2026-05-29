"""Midnight Academic — professional color palette for AAT CLI."""
from __future__ import annotations


class Colors:
    """Semantic color tokens. Use as [#HEX]text[/] in Rich markup."""

    # ── Identity / Primary ──
    PRIMARY = "#38bdf8"        # sky-400 — calm, confident
    PRIMARY_DARK = "#0ea5e9"   # sky-500
    PRIMARY_SOFT = "#7dd3fc"   # sky-300

    # ── Accent / Intelligence ──
    ACCENT = "#fbbf24"         # amber-400 — warmth, wisdom
    ACCENT_SOFT = "#f59e0b"    # amber-500

    # ── Status ──
    SUCCESS = "#34d399"        # emerald-400
    WARNING = "#fbbf24"        # amber-400
    ERROR = "#f87171"          # red-400
    INFO = "#60a5fa"           # blue-400
    MUTED_OK = "#64748b"       # slate-500

    # ── Text ──
    TEXT = "#f8fafc"           # slate-50 — primary readable
    TEXT_SECONDARY = "#94a3b8"  # slate-400 — captions, hints
    TEXT_MUTED = "#475569"      # slate-600 — very dim
    TEXT_DARK = "#1e293b"      # slate-800

    # ── UI surfaces ──
    BORDER = "#334155"          # slate-700 — normal panels
    BORDER_ACTIVE = "#38bdf8"   # sky-400 — active/selected panels
    BORDER_SUBTLE = "#475569"   # slate-600 — footers, hints
    BORDER_HEADER = "#1e293b"   # slate-800 — dark headers
    BORDER_WARNING = "#f59e0b"  # amber-500


class Styles:
    """Pre-built Rich markup snippets."""

    @staticmethod
    def brand(text: str) -> str:
        return f"[bold {Colors.PRIMARY}]{text}[/]"

    @staticmethod
    def brand_dim(text: str) -> str:
        return f"[dim {Colors.PRIMARY_SOFT}]{text}[/]"

    @staticmethod
    def title(text: str) -> str:
        return f"[bold {Colors.TEXT}]{text}[/]"

    @staticmethod
    def subtitle(text: str) -> str:
        return f"[dim {Colors.TEXT_SECONDARY}]{text}[/]"

    @staticmethod
    def muted(text: str) -> str:
        return f"[dim {Colors.TEXT_MUTED}]{text}[/]"

    @staticmethod
    def success(text: str) -> str:
        return f"[bold {Colors.SUCCESS}]{text}[/]"

    @staticmethod
    def warning(text: str) -> str:
        return f"[bold {Colors.WARNING}]{text}[/]"

    @staticmethod
    def error(text: str) -> str:
        return f"[bold {Colors.ERROR}]{text}[/]"

    @staticmethod
    def info(text: str) -> str:
        return f"[bold {Colors.INFO}]{text}[/]"

    @staticmethod
    def accent(text: str) -> str:
        return f"[bold {Colors.ACCENT}]{text}[/]"

    @staticmethod
    def status_ok() -> str:
        return f"[{Colors.SUCCESS}]ok[/]"

    @staticmethod
    def status_check() -> str:
        return f"[{Colors.WARNING}]check[/]"

    @staticmethod
    def panel_title(text: str) -> str:
        return f"[bold {Colors.TEXT}]{text}[/]"
