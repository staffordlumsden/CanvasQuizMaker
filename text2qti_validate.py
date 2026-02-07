#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from contextlib import contextmanager
from pathlib import Path

from text2qti.config import Config
from text2qti.err import Text2qtiError
from text2qti.qti import QTI
from text2qti.quiz import GroupStart, Question, Quiz, TextRegion


def _pick_file() -> str:
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception as exc:  # pragma: no cover - import-time failure
        print("Error: tkinter is not available. Install tk/tcl for your Python.", file=sys.stderr)
        print(f"Details: {exc}", file=sys.stderr)
        return ""

    root = tk.Tk()
    root.withdraw()
    try:
        root.attributes("-topmost", True)
    except Exception:
        pass

    return filedialog.askopenfilename(
        title="Select a text2qti .txt file to validate",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
    )


@contextmanager
def _pushd(path: Path):
    cwd = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(cwd)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="text2qti_validate",
        description="Validate that a .txt file follows Text2QTI format and can be converted to QTI.",
    )
    parser.add_argument("file", nargs="?", help="Path to a Text2QTI .txt file")
    parser.add_argument(
        "--no-gui",
        action="store_true",
        help="Do not open a file picker when no file path is provided",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help='Print only "VALID" or "INVALID"',
    )
    return parser.parse_args()


def _resolve_file(args: argparse.Namespace) -> Path:
    if args.file:
        return Path(args.file).expanduser().resolve()
    if args.no_gui:
        raise Text2qtiError("No file path provided. Pass a .txt file path or omit --no-gui to use a file picker.")
    selected = _pick_file()
    if not selected:
        raise Text2qtiError("No file selected.")
    return Path(selected).expanduser().resolve()


def _validate_file(file_path: Path) -> tuple[int, int, int, int | float]:
    if file_path.suffix.lower() != ".txt":
        raise Text2qtiError(f'Expected a ".txt" file, got "{file_path.name}"')
    try:
        text = file_path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        raise Text2qtiError(f'File "{file_path}" does not exist')
    except PermissionError as exc:
        raise Text2qtiError(f'File "{file_path}" cannot be read due to permission error:\n{exc}')
    except UnicodeDecodeError as exc:
        raise Text2qtiError(f'File "{file_path}" is not encoded in valid UTF-8:\n{exc}')

    config = Config()
    config.load()

    with _pushd(file_path.parent):
        quiz = Quiz(text, config=config, source_name=file_path.as_posix())
        # Build QTI in memory to verify that parsing output is fully convertible.
        QTI(quiz)

    question_count = sum(isinstance(item, Question) for item in quiz.questions_and_delims)
    group_count = sum(isinstance(item, GroupStart) for item in quiz.questions_and_delims)
    text_region_count = sum(isinstance(item, TextRegion) for item in quiz.questions_and_delims)
    return question_count, group_count, text_region_count, quiz.points_possible


def main() -> int:
    args = _parse_args()
    try:
        file_path = _resolve_file(args)
        question_count, group_count, text_region_count, points_possible = _validate_file(file_path)
    except Text2qtiError as exc:
        if args.quiet:
            print("INVALID")
        else:
            print("INVALID")
            print(f"File: {file_path if 'file_path' in locals() else '(not selected)'}")
            print(str(exc))
        return 1
    except Exception as exc:  # pragma: no cover - unexpected runtime failure
        if args.quiet:
            print("INVALID")
        else:
            print("INVALID")
            print(f"Unexpected error: {exc}")
        return 1

    if args.quiet:
        print("VALID")
        return 0

    print("VALID")
    print(f"File: {file_path}")
    print(f"Questions: {question_count}")
    print(f"Question groups: {group_count}")
    print(f"Text regions: {text_region_count}")
    print(f"Total points: {points_possible}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
