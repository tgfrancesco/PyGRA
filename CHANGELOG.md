# Changelog

## [0.8.2] - 2026-05-14

### Added
- CLI: `--dx` and `--dy` options to specify error bar columns per file 
  or globally (same semantics as `--x`/`--y`)
- CLI: `-s`/`--downsampling N` option to load every N-th row, useful 
  for very large files (e.g. `pygra idx_*.csv --x 3 --y 4 -s 100`)

### Fixed
- CSV files with comma delimiter now load correctly (auto-delimiter detection)
- Lines starting with `#` are silently skipped without triggering a warning
- Non-numeric header lines (first line) are silently skipped

## [0.8.1] - 2026-04-30

### Added
- Series navigation dropdown above the tab panel for quick switching 
  between loaded series
- Double-click on a curve in the plot to jump to the corresponding 
  series tab

## [0.8.0] - 2026-04-13

### Added
- Fit range selection in Fit & Interpolation dialog: manual x min/x max 
  fields or "Use zoom range" checkbox to fit only the visible region
- Gaussian curve fit: fits A·exp(-(x-μ)²/2σ²) to (x,y) data using 
  scipy.optimize.curve_fit
- Exponential curve fit: fits A·exp(-x/τ)+C to (x,y) data

### Changed
- Distribution fits renamed for clarity: "Gaussian (distribution)", 
  "Exponential (distribution)", "Maxwell-Boltzmann (distribution)", 
  "Poisson (distribution)" — distinguishes them from the new curve fits

## [0.7.1] - 2026-04-07

### Added
- CI/CD workflow: automatic testing on macOS, Linux, and Windows via 
  GitHub Actions on every push and pull request (pytest + ruff)
- CI badge added to README

### Fixed
- Windows: series tab and plot label now show filename only instead of full path

## [0.7.0] - 2026-03-31

### Added
- Histogram 2D: new series mode with heatmap display, configurable bins (x/y 
  separately with auto option), colormap, log scale, colorbar, and 
  count/density normalisation
- Horizontal histogram: "Horizontal" checkbox in Histogram Appearance
- Color by value in 1D histogram: bars colored by height using a 
  configurable matplotlib colormap
- Percentage font size control in Histogram Appearance
- Draggable text annotations: add via ✎ Text toolbar button, drag to 
  reposition, double-click to edit (text, font size, color, bold, rotation), 
  right-click to delete, Shift+Enter for multiline text
- Help menu: "Documentation" opens pygra.readthedocs.io, "About PyGRA" 
  shows version, author, license and links
- Bold text options in Style settings for title, axis labels, ticks, 
  legend, and percentage labels
- Legend show/hide option in Style settings

### Changed
- dialogs.py split into dialogs_style.py, dialogs_analysis.py, dialogs_misc.py
- _plot() logic extracted into plot_engine.py
- Docstrings updated across dataset.py, fitting.py, dialogs, preferences.py, 
  state.py, palettes.py, plot_engine.py
- Updated project description to reflect full feature set

## [0.6.1] - 2026-03-28

### Fixed
- macOS DMG now includes Applications folder shortcut (drag-to-install)
- Documented macOS Gatekeeper and Windows SmartScreen security warnings

### Changed
- Documentation: Download moved to a dedicated page separate from Installation
- Documentation: added security notes for macOS and Windows first launch

## [0.6.0] - 2026-03-28

### Added
- Coordinate display: mouse coordinates (x, y) shown in real time in the toolbar when hovering over the plot
- Checkmark in View → Color palette menu to indicate the active palette
- Active palette name shown in the color picker pre-dialog ("Basic colors palette (active: ...)")
- GitHub Actions workflow: automatic builds for macOS (.dmg), Linux (.tar.gz), and Windows (.exe) on every release

### Fixed
- CLI parser: per-file `--x`/`--y` no longer bleed into subsequent files without explicit column settings
- Version aligned to `0.6.0` across `pyproject.toml`, `__init__.py`, and `state.py`
- Package data path corrected to include `logo/` directory

## [0.5.1] - 2026-03-27

### Added
- 83 pytest tests covering `DataSet` loading, all `apply_transform` operations,
  all fit functions, and CLI parser behavior
  (`tests/test_dataset.py`, `tests/test_fitting.py`, `tests/test_cli.py`)

### Fixed
- Dataset loading now shows a warning dialog listing skipped row count, line
  numbers, and content instead of silently discarding malformed rows
- `fit_custom`: math functions (e.g. `exp`, `sin`) no longer overwrite numpy
  ufuncs in the formula namespace; array formulas now work correctly
- Replaced bare `except:` and `except Exception: pass` blocks across `main.py`,
  `dialogs.py`, `mainwindow.py`, `palettes.py`, and `preferences.py` with
  specific exception types and stderr warnings so failures are visible

## [0.5.0] - 2026-03-27

### Added
- Draggable legend: click and drag the legend anywhere on the plot; position persists across replots
- Legend style options in Style settings: frame on/off, background transparency, number of columns, symbol size, default position
- ↺ Legend button in toolbar to reset legend to automatic position
- Color palette browser: View → Color palette replaces the Basic colors grid in the color picker with scientific palettes (colorblind-friendly, matplotlib categorical, sequential/diverging, CSS color families)
- Custom colors saved to preferences and restored at next launch on all platforms
- Pick Screen Color hidden on macOS and Windows (platform limitation); works correctly on Linux
- Closeable series tabs: click ✕ to remove a series
- DataEditorDialog: Analysis → Edit data (Ctrl+D) — editable table, add/delete rows, non-destructive
- FitLayer double-click: edit label, line style, line width, and color of fit curves
- Persistent user preferences saved to `~/.config/pygra/preferences.json`: window geometry, splitter position, style settings, color palette
- View → Save preferences / Reset preferences
- Window geometry and panel proportions restored automatically on launch
- Save figure (Ctrl+E) added to File menu
- Configurable figure size (width × height in inches) for saving, independent of window size
- Resizable left panel (drag the splitter)
- Linux dock/launcher icon via `install_icon_linux.sh`
- Scientific palettes module (`palettes.py`): Okabe-Ito, Wong, Tol, tab10/20, Set1/2/3, Paired, Dark2, Pastel1, viridis, plasma, coolwarm, RdYlBu, CSS color families

### Fixed
- Colors from Appearance dialog now correctly applied to the plot
- Histogram mode no longer crashes with `KeyError: 'label'`
- CLI: positional file arguments supported (`pygra *.dat` works as expected)

### Changed
- Left panel width is now flexible (min 280px, max 500px) instead of fixed
- Label moved from series panel into Appearance dialog
- Qt color dialog used on all platforms (`DontUseNativeDialog`) for consistent appearance and custom color support

## [0.4.0] - 2026-03-26

### Changed — UI redesign
- "Plot" button always visible at bottom of left panel
- "Load files" button always visible at top of left panel
- Toolbar replaced with minimal custom toolbar: Zoom, Pan, Reset
- "Transform data" and "Statistics" moved to Analysis menu
- "Fit & Interpolation" unified in Analysis menu
- "Appearance" dialog separated from data panel; triggers auto-replot on OK
- Fit layers panel with per-layer visibility toggle, remove button, double-click to edit
- Cross-platform: macOS (menu in system bar), Linux, Windows

### Added
- FitDialog: formula shown read-only for predefined methods; Custom fields enabled only with "Custom..."
- Fit line color, style, width configurable per layer
- Ctrl+Enter shortcut for Plot

### Removed
- Undo/Redo
- Duplicate matplotlib toolbar buttons

## [0.3.0] - 2026-03-26

### Added
- Menu bar (File, Analysis, View)
- Distribution fits: Gaussian, Exponential, Maxwell-Boltzmann, Poisson, Custom
- Statistics dialog, data export, plot themes, DPI control

## [0.2.0] - 2026-03-20

### Added
- Multiple plots from the same file, histogram mode, data transforms
- Session save/load (JSON), CLI interface, interpolation overlays

## [0.1.0] - 2026-03-15

### Added
- Initial release
