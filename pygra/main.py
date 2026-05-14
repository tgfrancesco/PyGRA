"""
main.py — CLI entry point for PyGRA.
Handles --help before importing PyQt5 so it works without a display.
"""

import sys

HELP_TEXT = """
PyGRA — interactive scientific data plotter

Usage:
  pygra [file ...] [options]
  pygra --file FILE [--x COL] [--y COL] [--dx COL] [--dy COL] [--file FILE ...] [options]

Positional arguments:
  file                  One or more data files. The shell expands glob
                        patterns, e.g.:  pygra *wham_TI.dat

Options:
  -f, --file FILE       Load a data file (repeatable, alternative to positional)
  --x COL               x column index (0-based) for the preceding --file.
                        If given after all files, applies to all. Default: 0
  --y COL               y column index (0-based) for the preceding --file.
                        If given after all files, applies to all. Default: 1
  --dx COL              x error bar column index (0-based) for the preceding
                        --file. If given after all files, applies to all.
                        Default: 0 (no x error bars)
  --dy COL              y error bar column index (0-based) for the preceding
                        --file. If given after all files, applies to all.
                        Default: 0 (no y error bars)
  -s, --downsampling N  Load every N-th row from each file (default: 1, no downsampling)
  -l, --load FILE       Load a previously saved session (.json)
  -h, --help            Show this help message and exit

Examples:
  # open GUI with no files
  pygra

  # positional — shell expands the glob
  pygra *file*.dat

  # same columns for all files
  pygra file1.dat file2.dat --x 0 --y 3

  # per-file column specification
  pygra --file file1.dat --x 0 --y 3 --file file2.dat --x 0 --y 5

  # specify error bars
  pygra --file data.dat --x 0 --y 1 --dy 2

  # load every 100th row (useful for large files)
  pygra idx_*.csv --x 3 --y 4 --downsampling 100

  # load a saved session
  pygra --load session.json
"""


def _parse_interleaved(argv: list) -> dict:
    """
    Parse the command-line argument list into a structured dict.

    Supports interleaved ``--file``/``--x``/``--y``/``--dx``/``--dy`` groups so that each
    ``--file`` can carry its own column specification, and also handles
    positional file arguments and trailing column options that apply
    to all files.  Prints :data:`HELP_TEXT` and exits if ``-h`` or
    ``--help`` is present.

    Parameters
    ----------
    argv : list of str
        Argument strings, typically ``sys.argv[1:]``.

    Returns
    -------
    dict
        ``{"files": list[dict], "load": str | None, "downsampling": int}``
        where each file dict has keys ``"path"`` (str), ``"xcol"`` (int),
        ``"ycol"`` (int), ``"dxcol"`` (int), and ``"dycol"`` (int).
    """
    if any(tok in ("-h", "--help") for tok in argv):
        print(HELP_TEXT)
        sys.exit(0)

    files = []
    load = None
    downsampling = 1
    global_cols = {"xcol": None, "ycol": None, "dxcol": None, "dycol": None}
    col_options = {
        "--x": "xcol",
        "--y": "ycol",
        "--dx": "dxcol",
        "--dy": "dycol",
    }
    defaults = {"xcol": 0, "ycol": 1, "dxcol": 0, "dycol": 0}

    def _has_subsequent_file(start: int) -> bool:
        """Return True if argv[start:] contains another file argument."""
        j = start
        while j < len(argv):
            nxt = argv[j]
            if nxt in ("--file", "-f"):
                return True
            if nxt in ("--load", "-l", "--x", "--y", "--dx", "--dy",
                       "--downsampling", "-s"):
                j += 2
                continue
            if not nxt.startswith("-"):
                return True
            j += 1
        return False

    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok in ("--load", "-l"):
            i += 1
            load = argv[i] if i < len(argv) else None
        elif tok in ("--downsampling", "-s"):
            i += 1
            try:
                downsampling = max(1, int(argv[i]))
            except (ValueError, IndexError):
                pass
        elif tok in ("--file", "-f"):
            i += 1
            if i < len(argv):
                files.append(
                    {
                        "path": argv[i],
                        "xcol": None,
                        "ycol": None,
                        "dxcol": None,
                        "dycol": None,
                    }
                )
        elif tok in col_options and files:
            i += 1
            try:
                value = int(argv[i])
            except (ValueError, IndexError):
                value = None
            if value is not None:
                key = col_options[tok]
                if _has_subsequent_file(i + 1):
                    files[-1][key] = value
                else:
                    global_cols[key] = value
        elif not tok.startswith("-"):
            files.append(
                {"path": tok, "xcol": None, "ycol": None, "dxcol": None, "dycol": None}
            )
        i += 1

    for f in files:
        for key, default in defaults.items():
            if f[key] is None:
                f[key] = global_cols[key] if global_cols[key] is not None else default

    return {"files": files, "load": load, "downsampling": downsampling}


def main():
    """
    Entry point for the ``pygra`` command-line interface.

    Parses ``sys.argv``, creates the Qt application and
    :class:`~pygra.mainwindow.MainWindow`, optionally restores a saved
    session or pre-loads data files, then starts the Qt event loop.
    """
    args = _parse_interleaved(sys.argv[1:])

    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QIcon
    from .mainwindow import MainWindow
    import os

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # search for icon in logo/ subfolder first, then package root
    pkg_root = os.path.dirname(os.path.dirname(__file__))
    logo = None
    for candidate in [
        os.path.join(pkg_root, "logo", "pygra_dock_icon.png"),
        os.path.join(pkg_root, "logo", "pygra_logo.png"),
        os.path.join(pkg_root, "pygra_logo.png"),
    ]:
        if os.path.exists(candidate):
            logo = candidate
            break
    if logo:
        icon = QIcon(logo)
        app.setWindowIcon(icon)
        # on Linux, also set the taskbar/dock icon via the window icon
        # (requires a .desktop file for full dock integration — see README)

    win = MainWindow()

    if args["load"]:
        try:
            win._load_state_from_path(args["load"])
        except Exception as e:
            print(f"Warning: could not load session: {e}", file=sys.stderr)

    for f in args["files"]:
        win._load_file(
            f["path"],
            xcol=f["xcol"],
            ycol=f["ycol"],
            dxcol=f["dxcol"],
            dycol=f["dycol"],
            step=args["downsampling"],
        )

    win.show()
    sys.exit(app.exec_())
