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
- **Series tabs** — one tab per loaded series; each tab has column selectors,
  an Appearance button, a visibility checkbox, and a close button (✕)
- **Fit & interpolation layers** — lists active fit curves with visibility
  toggle, remove button, and double-click to edit style
- **Axis settings** — labels, title, log scale, limits
- **Plot** — renders the figure (also Ctrl+Enter)

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

Toolbar
~~~~~~~

The toolbar provides three navigation buttons:

- **🔍 Zoom** — click and drag to zoom into a region
- **✋ Pan** — click and drag to pan the view
- **⌂ Reset** — restore the original view
- **↺ Legend** — reset the legend to its automatic position

Color picker
~~~~~~~~~~~~

The color picker uses the Qt dialog (same appearance on all platforms).
The **Basic colors** grid can be replaced with any scientific palette via
**View → Color palette**. The chosen palette is saved in preferences and
restored at next launch.

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

User preferences
~~~~~~~~~~~~~~~~

PyGRA saves preferences automatically to ``~/.config/pygra/preferences.json``
when you close the application. These include:

- Window geometry and panel proportions
- Style settings (fonts, grid, theme, DPI)
- Last used color palette

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
