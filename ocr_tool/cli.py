from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from . import __version__
from .engine import OCRResult, PSM_MODES, extract
from .output import (
    console,
    copy_to_clipboard,
    make_progress,
    print_banner,
    print_error,
    print_file_header,
    print_result,
    print_success,
    print_warning,
    save_json,
    save_text,
)
from .preprocess import SUPPORTED_EXTENSIONS, build_variants, load_image

app = typer.Typer(
    name="ocr",
    help="Advanced OCR — extract text from images with high accuracy.",
    add_completion=False,
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"OCR Tool v{__version__}")
        raise typer.Exit()


def _setup_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(levelname)s %(name)s: %(message)s",
    )


def _collect_files(
    paths: list[Path],
    directory: Optional[Path],
    recursive: bool,
) -> list[Path]:
    files: list[Path] = []

    for p in paths:
        if not p.exists():
            print_warning(f"Path not found, skipping: {p}")
            continue
        if p.is_dir():
            _add_dir_files(files, p, recursive)
        elif p.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(p)
        else:
            print_warning(f"Unsupported format, skipping: {p.name}")

    if directory:
        if not directory.is_dir():
            print_error(f"Not a directory: {directory}")
            raise typer.Exit(1)
        _add_dir_files(files, directory, recursive)

    return files


def _add_dir_files(out: list[Path], directory: Path, recursive: bool) -> None:
    pattern = "**/*" if recursive else "*"
    for f in sorted(directory.glob(pattern)):
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
            out.append(f)


def _process_file(
    path: Path,
    lang: str,
    psm: Optional[list[int]],
    use_easyocr: bool,
    output_format: str,
    output_dir: Optional[Path],
    clipboard: bool,
    debug: bool,
    show_meta: bool,
) -> Optional[OCRResult]:
    print_file_header(str(path))

    out_dir = output_dir or path.parent

    try:
        if debug:
            console.print(f"  [dim]Loading {path}[/dim]")
        image = load_image(str(path))

        if debug:
            console.print(f"  [dim]Building preprocessing variants[/dim]")
        variants = build_variants(image, debug=debug)

        if debug:
            console.print(
                f"  [dim]Running OCR: {len(variants)} variants × {len(psm or PSM_MODES)} PSM modes[/dim]"
            )
        result = extract(
            variants,
            lang=lang,
            psm_modes=psm,
            use_easyocr=use_easyocr,
            debug=debug,
        )

    except FileNotFoundError as e:
        print_error(str(e))
        return None
    except ValueError as e:
        print_error(str(e))
        return None
    except RuntimeError as e:
        print_error(str(e))
        return None
    except Exception as e:
        print_error(f"Unexpected error on {path.name}: {e}")
        if debug:
            import traceback
            traceback.print_exc()
        return None

    print_result(result, show_meta=show_meta)

    saved_paths: list[str] = []

    if output_format in ("txt", "both"):
        out_path = out_dir / f"{path.stem}_ocr.txt"
        saved = save_text(result, str(path), str(out_path))
        saved_paths.append(saved)

    if output_format in ("json", "both"):
        out_path = out_dir / f"{path.stem}_ocr.json"
        saved = save_json(result, str(path), str(out_path))
        saved_paths.append(saved)

    for sp in saved_paths:
        print_success(f"Saved: {sp}")

    if clipboard and result.text:
        ok = copy_to_clipboard(result.text)
        if ok:
            print_success("Copied to clipboard.")
        else:
            print_warning("Clipboard copy failed (install pyperclip: pip install pyperclip).")

    return result


@app.command()
def main(
    images: Annotated[
        Optional[list[Path]],
        typer.Argument(
            help="Image file(s) to process. Accepts multiple files or drag-and-drop.",
            show_default=False,
        ),
    ] = None,
    directory: Annotated[
        Optional[Path],
        typer.Option("--dir", "-d", help="Process all images in a directory.", show_default=False),
    ] = None,
    recursive: Annotated[
        bool,
        typer.Option("--recursive", "-r", help="Search directory recursively."),
    ] = False,
    lang: Annotated[
        str,
        typer.Option("--lang", "-l", help="Tesseract language code (e.g. eng, pol, deu, fra)."),
    ] = "eng",
    psm: Annotated[
        Optional[str],
        typer.Option(
            "--psm",
            help="Comma-separated PSM modes to test (e.g. 6,11). Default: test all.",
        ),
    ] = None,
    output_format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format: none | txt | json | both."),
    ] = "none",
    output_dir: Annotated[
        Optional[Path],
        typer.Option("--output-dir", "-o", help="Directory for output files."),
    ] = None,
    clipboard: Annotated[
        bool,
        typer.Option("--clipboard", "-c", help="Copy result to clipboard."),
    ] = False,
    easyocr: Annotated[
        bool,
        typer.Option("--easyocr", "-e", help="Enable EasyOCR fallback for low-confidence results."),
    ] = False,
    no_meta: Annotated[
        bool,
        typer.Option("--no-meta", help="Hide confidence/engine metadata from output."),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option("--debug", help="Show preprocessing and per-pass OCR debug info."),
    ] = False,
    version: Annotated[
        Optional[bool],
        typer.Option("--version", "-v", callback=_version_callback, is_eager=True),
    ] = None,
) -> None:
    _setup_logging(debug)
    print_banner()

    if not images and directory is None:
        print_error("Provide at least one image file or use --dir.")
        raise typer.Exit(1)

    files = _collect_files(images or [], directory, recursive)

    if not files:
        print_error("No supported image files found.")
        raise typer.Exit(1)

    psm_list: Optional[list[int]] = None
    if psm:
        try:
            psm_list = [int(x.strip()) for x in psm.split(",")]
        except ValueError:
            print_error("--psm must be comma-separated integers, e.g. --psm 6,11")
            raise typer.Exit(1)

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

    total = len(files)
    success = 0

    if total > 1:
        console.print(f"[info]Processing {total} file(s)...[/info]\n")

    with make_progress() as progress:
        task = progress.add_task("Processing images...", total=total, visible=(total > 1))

        for path in files:
            result = _process_file(
                path=path,
                lang=lang,
                psm=psm_list,
                use_easyocr=easyocr,
                output_format=output_format,
                output_dir=output_dir,
                clipboard=clipboard,
                debug=debug,
                show_meta=not no_meta,
            )
            if result is not None:
                success += 1
            progress.advance(task)

    if total > 1:
        console.print(
            f"\n[success]Done:[/success] {success}/{total} file(s) processed successfully."
        )
