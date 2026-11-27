Usage
=====

Starting PyGRA
--------------

.. code-block:: bash

   pygra

Interface overview
------------------

Left panel
~~~~~~~~~~

- **Load files** — opens one or more data files
- **Series selector** — dropdown menu to quickly navigate between loaded 
  series without scrolling through tabs
- **Series tabs** — one tab per loaded series; each tab has column selectors,
  mode selector (Series / Histogram / Histogram 2D), Appearance button,
  visibility checkbox, and a close button (✕)
- **Fit & interpolation layers** — lists active fit curves with visibility
  toggle, remove button, and double-click to edit style
- **Axis settings** — labels, title, log scale, limits
- **Plot** — renders the figure (also Ctrl+Enter)
- **Double-click on a curve** in the plot to automatically switch to the 
  corresponding series tab in the left panel

Menu bar
~~~~~~~~

.. list-table::
   :widths: 15 40 15
   :header-rows: 1

   * - Menu
     - Action
     - Shortcut
   * - File
     - Load session
     - Ctrl+L
   * - File
     - Save session
     - Ctrl+S
   * - File
     - Save figure
     - Ctrl+E
   * - File
     - Export active data
     - —
   * - Edit
     - Undo
     - Ctrl+Z
   * - Edit
     - Redo
     - Ctrl+Shift+Z
   * - Analysis
     - Transform data
     - Ctrl+T
   * - Analysis
     - Statistics
     - Ctrl+I
   * - Analysis
     - Edit data
     - Ctrl+D
   * - Analysis
     - Fit & Interpolation
     - Ctrl+F
   * - View
     - Style settings
     - Ctrl+,
   * - View
     - Color palette
     - —
   * - View
     - Save preferences
     - —
   * - View
     - Reset preferences
     - —
   * - Help
     - Documentation
     - —
   * - Help
     - About PyGRA
     - —

Toolbar
~~~~~~~
- **↶ ↷ Undo / Redo** — step back or forward through changes to data,
  appearance, fits, annotations, legend position and settings
- **🔍 Zoom** — click and drag to zoom into a region
- **✋ Pan** — click and drag to pan the view
- **⌂ Reset** — restore the original axis limits after zoom/pan
  (does not affect data or settings)
- **↺ Legend** — reset the legend to its automatic position
- **✎ Text** — add a draggable text annotation to the plot
- **Coordinate display** — x and y values under the cursor, shown in real
  time on the right side of the toolbar when hovering over the plot

Undo / Redo
~~~~~~~~~~~

**Edit → Undo** (Ctrl+Z) and **Redo** (Ctrl+Shift+Z), or the ↶ ↷ toolbar
buttons. Undo covers loading, closing and reordering series, appearance,
mode changes, transforms, data edits, fits, annotations, legend position and
style/axis settings. Undoing a Transform or an Edit data restores the
previous dataset contents. Dragging the legend or an annotation counts as a
single step.

Showing/hiding a fit layer, dragging histogram percentage labels and
changing the color palette are not part of the history.

Right y-axis
~~~~~~~~~~~~

Tick **Right y-axis** in the axis settings of the left panel, then open
**Appearance** for a series and tick **Use right y-axis**. The right axis has
its own label, log scale and y min/max, shown only when it is enabled. The
legend combines entries from both axes.

.. note::
   The right y-axis applies to line/scatter series. Histograms are always
   drawn on the left axis.

Error bars and confidence bands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In Series mode each series can use symmetric errors (**dx**, **dy**) or
asymmetric errors (**dy low (-)**, **dy high (+)**), given as distances from
y, not absolute values. In **Appearance**, *Error style* chooses between
bars, a shaded band (``fill_between``) or both, and *Band alpha* sets the
transparency. *Z-order* decides which curve is drawn on top.

Fit & Interpolation
~~~~~~~~~~~~~~~~~~~

**Analysis → Fit & Interpolation** (Ctrl+F) offers spline, linear,
polynomial, Gaussian and Exponential curve fits, a custom formula, and
distribution fits for histograms (Gaussian, Exponential, Maxwell-Boltzmann,
Poisson). The fit can be restricted to a window with **x min / x max** or
with **Use zoom range**.

.. note::
   Curve fits work on (x, y) points in Series mode. Distribution fits work
   on the values of a histogram, so they appear as "(distribution)" in the
   method list. The custom formula follows the mode of the series: points in
   Series mode, histogram in Histogram mode.

Plot modes
~~~~~~~~~~

Each series can be displayed in one of three modes, selectable via radio
buttons in the series tab:

**Series** — standard x/y line or scatter plot with optional error bars.

**Histogram** — 1D histogram of a selected column. Options in Appearance:

- Bin count (manual or auto) and normalisation (count / density / probability)
- Horizontal orientation
- Color by value — bars colored using a matplotlib colormap based on height
- Percentage labels with configurable font size and bold option
- Show/hide percentages

**Histogram 2D** — 2D density map of two columns. Options in Appearance:

- Bins x / bins y (manual or auto)
- Colormap (viridis, plasma, coolwarm, etc.)
- Normalisation (count / density)
- Log scale for the color axis
- Colorbar on/off

Text annotations
~~~~~~~~~~~~~~~~

Click **✎ Text** in the toolbar to add a text annotation to the plot.
A dialog allows you to set:

- Text content (Shift+Enter for newline)
- Font size and bold
- Color
- Rotation angle (degrees)

Once placed, annotations can be:

- **Dragged** — click and drag to reposition
- **Edited** — double-click to reopen the dialog
- **Deleted** — right-click → Delete

Annotation positions are preserved across replots and saved in sessions.

Color picker
~~~~~~~~~~~~

The color picker uses the Qt dialog (same appearance on all platforms).
The **Basic colors** grid can be replaced with any scientific palette via
**View → Color palette**. A checkmark indicates the active palette, and
the name of the active palette is shown in the color picker itself
("Basic colors palette (active: ...)"). The chosen palette is saved in
preferences and restored at next launch.

On **Linux**, the **Pick Screen Color** button captures any color visible on
screen. On **macOS** and **Windows** this button is hidden, as platform
security restrictions prevent capturing colors outside the dialog window.

Custom colors added via **Add to Custom Colors** are saved in preferences
and restored at next launch on all platforms.

Draggable legend
~~~~~~~~~~~~~~~~

After plotting, click and drag the legend to reposition it anywhere on the
figure. The position is preserved across subsequent plots. Click **↺ Legend**
in the toolbar to reset to automatic positioning.

Legend style options are available in **View → Style settings**: frame on/off,
background transparency, number of columns, symbol size, default position,
and show/hide toggle.

Style settings
~~~~~~~~~~~~~~

**View → Style settings** (Ctrl+,) controls global appearance:

- Font sizes for title, axis labels, ticks, and legend
- Bold text options for each element independently
- Major/minor tick spacing and grid
- Plot theme (default, dark, seaborn, ggplot, bmh, grayscale)
- Figure size and DPI for saving
- Legend options (position, frame, transparency, columns, symbol size)

User preferences
~~~~~~~~~~~~~~~~

PyGRA saves preferences automatically to ``~/.config/pygra/preferences.json``
when you close the application. These include:

- Window geometry and panel proportions
- Style settings (fonts, grid, theme, DPI, figure size)
- Last used color palette
- Custom colors

Use **View → Save preferences** to save at any time, or
**View → Reset preferences** to restore defaults.

File format
-----------

Files should be whitespace-delimited with one data point per row.
Lines starting with ``#`` are treated as comments and ignored.

.. code-block:: text

   # x   y    dy
   0     1.0  0.05
   1     2.3  0.08
   2     1.8  0.06
