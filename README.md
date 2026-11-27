# PyGRA

<p align="center">
  <img src="logo/pygra_logo.png" width="340" alt="PyGRA logo — a sleepy sloth on a graph"/>
  <br>
  <img src="https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey" alt="Platform">
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="License">
  <img src="https://img.shields.io/badge/python-3.11+-yellow" alt="Python Version">
  <a href="https://pygra.readthedocs.io/en/latest/"><img src="https://readthedocs.org/projects/pygra/badge/?version=latest" alt="Documentation"></a>
  <a href="https://github.com/tgfrancesco/PyGRA/actions/workflows/ci.yml"><img src="https://github.com/tgfrancesco/PyGRA/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
</p>

**PyGRA** is a cross-platform interactive scientific data plotter built with Python, PyQt5, and Matplotlib. It provides a graphical interface for loading, visualising, transforming, and fitting multi-column data files — with histogram analysis, 2D density plots, draggable annotations, and publication-ready figure export.

📖 **[Documentation](https://pygra.readthedocs.io/en/latest/)**

## Features

- Load multiple whitespace-delimited or CSV data files (`.dat`, `.txt`, `.csv`, ...)
- Per-series column selection for x, y, symmetric (dx, dy) and asymmetric (dy low / dy high) error bars
- Error bars, confidence band (`fill_between`), or both
- Series navigation dropdown and draggable tabs (tab order sets plot and legend order)
- Double-click on a plot curve to jump to the corresponding series tab
- Multiple plots from the same file with independent settings
- Three plot modes per series: Series, Histogram (1D, optionally horizontal, colored by value, with percentage labels) and Histogram 2D (heatmap with colorbar)
- Right y-axis with its own label, log scale and limits; each series can be assigned to either axis
- Z-order control to choose which curve is drawn on top
- Fit & Interpolation: spline, linear, polynomial, Gaussian / Exponential curve fits, custom formula, and distribution fits (Gaussian, Exponential, Maxwell-Boltzmann, Poisson)
- Fit range: restrict the fit to a manual x window or to the current zoom
- Fit results appear automatically as overlay curves, listed in a dedicated panel with per-layer visibility, remove and style controls
- Undo / Redo (Ctrl+Z / Ctrl+Shift+Z) for loading, closing, appearance, transforms, data edits, fits, annotations, legend position and settings
- Draggable text annotations (editable, rotatable, multiline)
- Draggable legend with style options (frame, transparency, columns, symbol size, position)
- Data transforms: multiply/divide/add/subtract, normalize, numerical derivative, moving average
- Edit data in a table (add/delete rows, non-destructive)
- Statistics dialog per series
- Color picker with scientific palette browser (colorblind-friendly, matplotlib, sequential, CSS)
- Axis labels, title, log scale, manual limits, fonts (with bold options), ticks and grid
- Plot themes (default, dark, seaborn, ggplot, bmh, grayscale)
- Configurable figure size and DPI; save figure as PNG, PDF, SVG
- Save/load full sessions as JSON
- Persistent user preferences (window geometry, style, color palette)
- Command-line options for columns, error bars and downsampling of very large files

## Download

Pre-built installers are available on the [Releases page](https://github.com/tgfrancesco/PyGRA/releases/latest):

| Platform | File | Notes |
|----------|------|-------|
| macOS | `PyGRA-macos.dmg` | Open the DMG and drag PyGRA to Applications |
| Linux | `PyGRA-linux.tar.gz` | Extract and run `./PyGRA/PyGRA` |
| Windows | `PyGRA.exe` | Run directly |

No Python installation required.

> **macOS:** on first launch, go to **System Settings → Privacy & Security → Open Anyway**
> if macOS blocks the app. This is a one-time step.

> **Windows:** Windows may show a SmartScreen warning.
> Click **"More info" → "Run anyway"** to proceed.

## Installation

### With conda (recommended)

```bash
conda env create -f environment.yml
conda activate pygra
```

Or install into an existing environment:

```bash
conda activate oxdna
pip install -e .
```

### With pip

```bash
pip install -r requirements.txt
pip install -e .
```

### Linux: dock/launcher icon

On Linux, run the provided install script once after installation to register the icon and add PyGRA to the application launcher:

```bash
bash install_icon_linux.sh
```

This copies the icon to `~/.local/share/icons` and creates a `.desktop` file in `~/.local/share/applications`. You may need to log out and back in for the icon to appear in the dock.

## Usage

```bash
pygra
```

**Left panel:**
- **Load files** — opens one or more data files
- **Series selector** — dropdown to switch quickly between loaded series
- **Series tabs** — one tab per series (drag to reorder, ✕ to close); each tab has the mode selector (Series / Histogram / Histogram 2D), column selectors, Appearance button and visibility checkbox
- **Fit & interpolation layers** — active fit curves with visibility toggle, remove button, and double-click to edit style
- **Axis settings** — labels, title, log scale, limits, optional right y-axis
- **Plot** — renders the figure (also Ctrl+Enter)
- **Double-click on a curve** in the plot to switch to the corresponding series tab

**Toolbar:**
- **↶ ↷** — undo / redo
- **🔍 Zoom / ✋ Pan** — navigate the plot
- **⌂ Reset** — restore the original axis limits after zoom/pan (does not affect data or settings)
- **↺ Legend** — reset the legend to its automatic position
- **✎ Text** — add a draggable text annotation
- Live x / y coordinates under the cursor

**Menu bar:**

| Menu     | Action                     | Shortcut     |
|----------|----------------------------|--------------|
| File     | Load session               | Ctrl+L       |
| File     | Save session               | Ctrl+S       |
| File     | Save figure                | Ctrl+E       |
| File     | Export active data         | —            |
| Edit     | Undo                       | Ctrl+Z       |
| Edit     | Redo                       | Ctrl+Shift+Z |
| Analysis | Transform data             | Ctrl+T       |
| Analysis | Statistics                 | Ctrl+I       |
| Analysis | Edit data                  | Ctrl+D       |
| Analysis | Fit & Interpolation        | Ctrl+F       |
| View     | Style settings             | Ctrl+,       |
| View     | Color palette              | —            |
| View     | Save preferences           | —            |
| View     | Reset preferences          | —            |
| Help     | Documentation, About       | —            |

### Right y-axis

Tick **Right y-axis** in the axis settings of the left panel, then open **Appearance** for a series and tick **Use right y-axis** to draw it on the right axis. The right axis has its own label, log scale and y min/max, which appear only when it is enabled. The legend combines the entries from both axes.

> **Note:** the right y-axis applies to line/scatter series. Histograms are always drawn on the left axis, and the log scale and limits of the left axis do not affect the right one (it has its own controls).

### Color picker

The color picker uses the Qt dialog (same appearance on all platforms). The **Basic colors** grid can be replaced with any scientific palette via **View → Color palette**. The chosen palette is saved in preferences and restored at next launch.

On **Linux**, the **Pick Screen Color** button captures any color visible on screen. On **macOS** and **Windows** this button is hidden, as platform security restrictions prevent capturing colors outside the dialog window.

Custom colors added via **Add to Custom Colors** are saved in preferences and restored at next launch on all platforms.

### Command-line interface

```bash
# open GUI with no files
pygra

# positional arguments — shell expands the glob
pygra *file*.dat

# same columns for all files
pygra file1.dat file2.dat --x 0 --y 3

# per-file column specification
pygra --file file1.dat --x 0 --y 3 --file file2.dat --x 0 --y 5

# specify symmetric error bars
pygra --file data.dat --x 0 --y 1 --dy 2

# specify asymmetric error bars (e.g. bootstrap q16/q84)
pygra --file data.dat --x 0 --y 1 --dy_low 2 --dy_high 3

# large files — load every 50th row
pygra idx_*.csv --x 3 --y 4 -s 50

# load a saved session
pygra --load session.json

# help
pygra --help
```
**CLI rules:**
- Files can be passed as positional arguments: `pygra *.dat` works as expected
- `--x` / `--y` / `--dx` / `--dy` / `--dy_low` / `--dy_high` immediately after `--file` apply to that specific file only
- `--x` / `--y` / `--dx` / `--dy` / `--dy_low` / `--dy_high` after all files apply to all of them
- Default columns: x=0, y=1, dx=0 (none), dy=0 (none), dy_low=0 (none), dy_high=0 (none)
- `-s` / `--downsampling N` loads every N-th row from all files — useful for very large files

## File format

Whitespace-delimited or comma-separated (CSV), one row per data point. 
Lines starting with `#` and non-numeric header lines are ignored automatically.

```
# x   y    dy
0     1.0  0.05
1     2.3  0.08
2     1.8  0.06
```

## Project structure

```
PyGRA/
├── pygra.py                  # convenience script
├── pyproject.toml
├── environment.yml
├── requirements.txt
├── install_icon_linux.sh     # Linux icon installer
├── README.md
├── CHANGELOG.md
├── LICENSE
├── logo/                     # application icons
├── docs/                     # Sphinx documentation (Read the Docs)
├── tests/                    # pytest suite
└── pygra/
    ├── __init__.py
    ├── main.py               # CLI entry point (pygra command)
    ├── constants.py          # shared constants and defaults
    ├── dataset.py            # data loading and transforms
    ├── fitting.py            # distribution and curve fits
    ├── palettes.py           # scientific color palettes
    ├── dialogs.py            # compatibility shim for the dialog modules
    ├── dialogs_style.py      # appearance, style and color dialogs
    ├── dialogs_analysis.py   # fit, transform, statistics, data editor
    ├── dialogs_misc.py       # text annotation and palette dialogs
    ├── widgets.py            # DatasetWidget (per-series panel)
    ├── mainwindow.py         # MainWindow, fit layers, mouse interaction
    ├── plot_engine.py        # figure rendering
    ├── history.py            # undo/redo history
    ├── state.py              # session save/load
    └── preferences.py        # persistent user preferences
```

## Dependencies

- Python >= 3.11
- numpy >= 1.24
- scipy >= 1.10
- matplotlib >= 3.7
- PyQt5 >= 5.15

## Development

```bash
pip install -e .
pip install pytest pytest-cov ruff
python -m pytest tests/ -q
ruff check .
```

Tests do not require a display. On Linux, use `python -m pytest` rather than bare `pytest` to make sure the active environment is used. A GitHub Actions workflow runs tests and linting on macOS, Linux and Windows for every push.

## License

MIT — see [LICENSE](LICENSE).

## Author

Francesco Tosti Guerra
