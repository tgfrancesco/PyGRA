# Changelog

## [0.5.1] - 2026-03-27

### Added
- 79 pytest tests covering `DataSet` loading, all `apply_transform` operations, and all fit functions (`tests/test_dataset.py`, `tests/test_fitting.py`)

### Fixed
- Dataset loading now shows a warning dialog listing skipped row count, line numbers, and content instead of silently discarding malformed rows
- `fit_custom`: math functions (e.g. `exp`, `sin`) no longer overwrite numpy ufuncs in the formula namespace; array formulas now work correctly
- Replaced bare `except:` and `except Exception: pass` blocks across `main.py`, `dialogs.py`, `mainwindow.py`, `palettes.py`, and `preferences.py` with specific exception types and stderr warnings so failures are visible

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
- CLI: `--x`/`--y` after all `--file` arguments now correctly applies to all files
- Positional file arguments supported: `pygra *.dat` works as expected

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
