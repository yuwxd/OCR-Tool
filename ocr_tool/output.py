"""
Output formatting and display utilities.
Handles terminal rendering, file writing, and JSON export.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from .engine import OCRResult

_THEME = Theme({
    "info":    "bold cyan",
    "success": "bold green",
    "warning": "bold yellow",
    "error":   "bold red",
    "dim":     "grey50",
    "label":   "bold white",
})

console = Console(theme=_THEME, highlight=False)
err_console = Console(stderr=True, theme=_THEME)


def make_progress() -> Progress:
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    )


def print_banner() -> None:
    console.print()
    console.print(
        Panel.fit(
            "[bold white]OCR Tool[/bold white]  [dim]— Advanced text extraction[/dim]",
            border_style="cyan",
            padding=(0, 2),
        )
    )
    console.print()


def print_file_header(path: str) -> None:
    console.print(Rule(f"[dim]{Path(path).name}[/dim]", style="dim"))


def print_debug_table(results: list[OCRResult], show_all: bool = False) -> None:
    table = Table(
        "Engine", "Variant", "PSM", "Confidence", "Words", "Score",
        title="[dim]OCR pass results[/dim]",
        border_style="dim",
        header_style="bold dim",
        show_edge=True,
    )
    sorted_results = sorted(results, key=lambda r: r.score, reverse=True)
    for i, r in enumerate(sorted_results):
        style = "bold green" if i == 0 else ("dim" if not show_all and i > 4 else "")
        if not show_all and i > 4:
            break
        table.add_row(
            r.engine,
            r.variant,
            str(r.psm_mode) if r.psm_mode is not None else "—",
            f"{r.confidence:.1f}%",
            str(r.word_count),
            f"{r.score:.1f}",
            style=style,
        )
    console.print(table)


def print_result(result: OCRResult, show_meta: bool = True) -> None:
    if show_meta:
        meta = Text()
        meta.append("Engine: ", style="label")
        meta.append(result.engine, style="cyan")
        meta.append("  |  Confidence: ", style="label")
        conf_style = "green" if result.confidence >= 80 else ("yellow" if result.confidence >= 50 else "red")
        meta.append(f"{result.confidence:.1f}%", style=conf_style)
        meta.append("  |  Words: ", style="label")
        meta.append(str(result.word_count), style="white")
        meta.append("  |  Chars: ", style="label")
        meta.append(str(result.char_count), style="white")
        meta.append(f"  |  {result.elapsed_ms:.0f}ms", style="dim")
        console.print(meta)
        console.print()

    if result.warnings:
        for w in result.warnings:
            console.print(f"[warning]⚠  {w}[/warning]")
        console.print()

    if result.text:
        console.print(
            Panel(
                result.text,
                title="[dim]Extracted text[/dim]",
                border_style="green",
                padding=(1, 2),
            )
        )
    else:
        console.print("[warning]No text detected in this image.[/warning]")
    console.print()


def save_text(result: OCRResult, image_path: str, out_path: Optional[str] = None) -> str:
    if out_path is None:
        stem = Path(image_path).stem
        out_path = Path(image_path).parent / f"{stem}_ocr.txt"
    Path(out_path).write_text(result.text + "\n", encoding="utf-8")
    return str(out_path)


def save_json(result: OCRResult, image_path: str, out_path: Optional[str] = None) -> str:
    if out_path is None:
        stem = Path(image_path).stem
        out_path = Path(image_path).parent / f"{stem}_ocr.json"

    data = {
        "source": str(image_path),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "engine": result.engine,
        "confidence": round(result.confidence, 2),
        "psm_mode": result.psm_mode,
        "variant": result.variant,
        "word_count": result.word_count,
        "char_count": result.char_count,
        "elapsed_ms": round(result.elapsed_ms, 1),
        "warnings": result.warnings,
        "text": result.text,
    }
    Path(out_path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(out_path)


def copy_to_clipboard(text: str) -> bool:
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except Exception:
        return False


def print_success(msg: str) -> None:
    console.print(f"[success]✓  {msg}[/success]")


def print_warning(msg: str) -> None:
    console.print(f"[warning]⚠  {msg}[/warning]")


def print_error(msg: str) -> None:
    err_console.print(f"[error]✗  {msg}[/error]")
