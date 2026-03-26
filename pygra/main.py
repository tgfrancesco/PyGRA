"""
main.py — CLI entry point for PyGRA.
Handles --help before importing PyQt5 so it works without a display.
"""

import sys

HELP_TEXT = """
PyGRA — interactive scientific data plotter

Usage:
  pygra [file ...] [options]
  pygra --file FILE [--x COL] [--y COL] [--file FILE ...] [options]

Positional arguments:
  file                  One or more data files. The shell expands glob
                        patterns, e.g.:  pygra *wham_TI.dat

Options:
  -f, --file FILE       Load a data file (repeatable, alternative to positional)
  --x COL               x column index (0-based) for the preceding --file.
                        If given after all files, applies to all. Default: 0
  --y COL               y column index (0-based) for the preceding --file.
                        If given after all files, applies to all. Default: 1
  -l, --load FILE       Load a previously saved session (.json)
  -h, --help            Show this help message and exit

Examples:
  # open GUI with no files
  pygra

  # positional — shell expands the glob
  pygra *wham_TI.dat

  # same columns for all files
  pygra base.dat unique.dat --x 0 --y 3

  # per-file column specification
  pygra --file base.dat --x 0 --y 3 --file unique.dat --x 0 --y 5

  # load a saved session
  pygra --load session.json
"""


def _parse_interleaved(argv: list) -> dict:
    if any(tok in ("-h", "--help") for tok in argv):
        print(HELP_TEXT)
        sys.exit(0)

    files = []
    load  = None

    # First pass: collect files (from --file or positional) and any immediately following --x/--y
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok in ("--load", "-l"):
            i += 1
            load = argv[i] if i < len(argv) else None
        elif tok in ("--file", "-f"):
            i += 1
            if i < len(argv):
                files.append({"path": argv[i], "xcol": None, "ycol": None})
        elif tok == "--x" and files:
            i += 1
            try:    files[-1]["xcol"] = int(argv[i])
            except: pass
        elif tok == "--y" and files:
            i += 1
            try:    files[-1]["ycol"] = int(argv[i])
            except: pass
        elif not tok.startswith("-"):
            # positional argument: treat as a file path
            files.append({"path": tok, "xcol": None, "ycol": None})
        i += 1

    # Second pass: fill in defaults and propagate shared values
    explicit_x = next((f["xcol"] for f in files if f["xcol"] is not None), None)
    explicit_y = next((f["ycol"] for f in files if f["ycol"] is not None), None)

    for f in files:
        if f["xcol"] is None:
            f["xcol"] = explicit_x if explicit_x is not None else 0
        if f["ycol"] is None:
            f["ycol"] = explicit_y if explicit_y is not None else 1

    return {"files": files, "load": load}


def main():
    args = _parse_interleaved(sys.argv[1:])

    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QIcon
    from .mainwindow import MainWindow
    import os

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    logo = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pygra_logo.png")
    if os.path.exists(logo):
        app.setWindowIcon(QIcon(logo))

    win = MainWindow()

    if args["load"]:
        try:
            win._load_state_from_path(args["load"])
        except Exception as e:
            print(f"Warning: could not load session: {e}", file=sys.stderr)

    for f in args["files"]:
        win._load_file(f["path"], xcol=f["xcol"], ycol=f["ycol"])

    win.show()
    sys.exit(app.exec_())
