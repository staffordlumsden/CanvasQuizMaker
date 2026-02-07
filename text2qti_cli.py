#!/usr/bin/env python3
from __future__ import annotations

import datetime as _dt
import shutil
import subprocess
import sys
from pathlib import Path


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
        title="Select a text2qti .txt file",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
    )


def _resolve_text2qti_cmd(repo_root: Path) -> Path:
    return repo_root / ".venv" / "bin" / "text2qti"


def main() -> int:
    repo_root = Path(__file__).resolve().parent
    selected = _pick_file()
    if not selected:
        print("No file selected. Exiting.")
        return 1

    quiz_path = Path(selected).expanduser().resolve()
    if quiz_path.suffix.lower() != ".txt":
        print(f"Error: expected a .txt file, got: {quiz_path}", file=sys.stderr)
        return 1
    if not quiz_path.exists():
        print(f"Error: file not found: {quiz_path}", file=sys.stderr)
        return 1

    text2qti_cmd = _resolve_text2qti_cmd(repo_root)
    if not text2qti_cmd.exists():
        print("Error: text2qti is not installed in .venv.", file=sys.stderr)
        print("Run: .venv/bin/python -m pip install .", file=sys.stderr)
        return 1

    print(f"Converting: {quiz_path}")
    result = subprocess.run(
        [str(text2qti_cmd), str(quiz_path)],
        text=True,
        capture_output=True,
    )
    if result.stdout:
        print(result.stdout)
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        print("text2qti failed. See output above.", file=sys.stderr)
        return result.returncode

    output_zip = quiz_path.with_suffix(".zip")
    if not output_zip.exists():
        print(
            f"Error: expected output zip not found: {output_zip}",
            file=sys.stderr,
        )
        return 1

    desktop = Path.home() / "Desktop"
    desktop.mkdir(parents=True, exist_ok=True)
    dest = desktop / output_zip.name
    if dest.exists():
        stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        dest = desktop / f"{output_zip.stem}-{stamp}{output_zip.suffix}"

    shutil.move(str(output_zip), str(dest))
    print(f"Saved to: {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
