"""
mainwindow.py — MainWindow with menu bar, fit layer management, custom toolbar
"""

import sys

import numpy as np
from scipy.interpolate import make_interp_spline

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QGroupBox, QGridLayout, QSplitter,
    QCheckBox, QTabWidget, QFileDialog, QMessageBox, QSizePolicy,
    QDialog, QShortcut, QAction, QPushButton, QFrame,
    QScrollArea, QMenu, QComboBox,
)
from PyQt5.QtCore import Qt, QTimer, QUrl
from PyQt5.QtGui import QKeySequence, QIcon, QDesktopServices

import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backend_bases import MouseButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from .constants import COLORS, DEFAULT_STYLE_SETTINGS
from .dataset import DataSet, apply_transform
from .dialogs import (
    StyleDialog, TransformDialog, StatsDialog, FitDialog,
    AppearanceDialog, DataEditorDialog, Hist2DAppearanceDialog,
    TextAnnotationDialog,
    apply_basic_palette, restore_basic_palette,
)
from .fitting import FIT_FUNCTIONS, fit_custom, fit_gaussian_curve, fit_exponential_curve
from .widgets import DatasetWidget
from .state import save_state, load_state
from .preferences import load_prefs, save_prefs, PREFS_PATH
from .plot_engine import render_plot


class FitLayer:
    """
    Data container for a single fit or interpolation curve.

    Instances are created by :meth:`MainWindow._fit_active` and stored
    in :attr:`MainWindow.fit_layers`.

    Parameters
    ----------
    label : str
        Display label shown in the fit panel and plot legend.
    x : numpy.ndarray
        x-coordinates of the fit curve.
    y : numpy.ndarray
        y-coordinates of the fit curve.
    color : str
        Hex color string for the curve.
    source_label : str
        Label of the dataset series this fit was computed from.
    linestyle : str, optional
        Matplotlib linestyle string.  Default is ``"--"``.
    linewidth : float, optional
        Line width in points.  Default is ``1.8``.

    Attributes
    ----------
    visible : bool
        Whether the layer is currently shown on the plot.
        Initialised to ``True``.
    """

    def __init__(self, label: str, x: np.ndarray, y: np.ndarray,
                 color: str, source_label: str,
                 linestyle: str = "--", linewidth: float = 1.8):
        self.label        = label
        self.x            = x
        self.y            = y
        self.color        = color
        self.source_label = source_label
        self.linestyle    = linestyle
        self.linewidth    = linewidth
        self.visible      = True


class FitLayerWidget(QWidget):
    """
    Row widget in the fit panel representing one :class:`FitLayer`.

    Displays a visibility checkbox, a color dot, the layer label with its
    source series, and a remove button.  Double-clicking the label row
    opens the fit-layer appearance editor.

    Parameters
    ----------
    layer : FitLayer
        The fit layer this widget controls.
    on_remove : callable
        Called with *layer* when the ✕ button is clicked.
    on_toggle : callable
        Called with ``(layer, visible: bool)`` when the checkbox changes.
    on_edit : callable
        Called with ``(layer, widget)`` on double-click.
    parent : QWidget, optional
        Parent widget.
    """

    def __init__(self, layer: FitLayer, on_remove, on_toggle, on_edit, parent=None):
        super().__init__(parent)
        self.layer   = layer
        self.on_edit = on_edit
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)

        self.chk = QCheckBox()
        self.chk.setChecked(layer.visible)
        self.chk.toggled.connect(lambda v: on_toggle(layer, v))
        layout.addWidget(self.chk)

        self.color_dot = QLabel("●")
        self.color_dot.setStyleSheet(f"color: {layer.color}; font-size: 14px;")
        layout.addWidget(self.color_dot)

        self.lbl = QLabel()
        self._refresh_label()
        self.lbl.setWordWrap(True)
        self.lbl.setToolTip("Double-click to edit appearance")
        layout.addWidget(self.lbl, stretch=1)

        rm_btn = QPushButton("✕")
        rm_btn.setFixedSize(22, 22)
        rm_btn.clicked.connect(lambda: on_remove(layer))
        layout.addWidget(rm_btn)

    def _refresh_label(self):
        self.lbl.setText(f"<b>{self.layer.label}</b>  <small>← {self.layer.source_label}</small>")

    def mouseDoubleClickEvent(self, event):
        if self.on_edit:
            self.on_edit(self.layer, self)


class MainWindow(QMainWindow):
    """
    Application main window for PyGRA.

    Manages the left-side series panel (one :class:`~widgets.DatasetWidget`
    per series tab), the matplotlib canvas, axis controls, a fit-layer
    panel, the menu bar, and a custom toolbar.  Application state can be
    saved and restored as JSON session files.

    Attributes
    ----------
    datasets : list of DataSet
        All loaded datasets.  A single dataset may be shared between
        multiple series widgets (via the duplicate action).
    dataset_widgets : list of DatasetWidget
        One widget per visible series tab, in tab order.
    fit_layers : list of FitLayer
        Fit and interpolation curves currently overlaid on the plot.
    style_settings : dict
        Active global style settings; mirrors
        :data:`constants.DEFAULT_STYLE_SETTINGS`.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyGRA — interactive plotter")
        self.resize(1200, 760)
        self.datasets:        list = []
        self.dataset_widgets: list = []
        self.fit_layers:      list = []       # list of FitLayer
        self._prefs = load_prefs()
        self.style_settings = {k: self._prefs.get(k, v)
                               for k, v in DEFAULT_STYLE_SETTINGS.items()}
        self._legend_pos = None
        self._dragging_legend = False
        self._pct_text_artists: list = []
        self._pct_label_positions: list = []   # (x, y) per artist, or None for default
        self._pct_series_key: tuple = ()
        self._dragging_pct_idx: int = -1
        self._annotations: list = []           # list of annotation dicts
        self._annot_artists: list = []         # matplotlib Text objects, rebuilt each _plot()
        self._dragging_annot_idx: int = -1
        self._palette_actions: dict = {}
        self._syncing_series_nav = False
        self._build_ui()
        self._build_menu()
        self._restore_geometry()

    # ------------------------------------------------------------------
    # Menu bar
    # ------------------------------------------------------------------

    def _build_menu(self):
        mb = self.menuBar()

        file_menu = mb.addMenu("File")
        self._act(file_menu, "Load session...",    "Ctrl+L", self._load_state)
        file_menu.addSeparator()
        self._act(file_menu, "Save session...",    "Ctrl+S", self._save_state)
        self._act(file_menu, "Save figure...",     "Ctrl+E", self._save_figure)
        file_menu.addSeparator()
        self._act(file_menu, "Export active data...", None,  self._export_active)

        analysis_menu = mb.addMenu("Analysis")
        self._act(analysis_menu, "Transform data...",        "Ctrl+T", self._transform_active)
        self._act(analysis_menu, "Statistics...",            "Ctrl+I", self._stats_active)
        self._act(analysis_menu, "Edit data...",             "Ctrl+D", self._edit_data_active)
        analysis_menu.addSeparator()
        self._act(analysis_menu, "Fit & Interpolation...",   "Ctrl+F", self._fit_active)

        view_menu = mb.addMenu("View")
        self._act(view_menu, "Style settings...", "Ctrl+,", self._open_style)
        view_menu.addSeparator()

        # Color palette submenu
        from PyQt5.QtWidgets import QMenu, QActionGroup
        from .palettes import PALETTE_GROUPS
        palette_menu = view_menu.addMenu("Color palette")
        ag = QActionGroup(self)
        ag.setExclusive(True)
        default_act = palette_menu.addAction("Qt default")
        default_act.setCheckable(True)
        default_act.triggered.connect(lambda: self._set_palette(""))
        ag.addAction(default_act)
        self._palette_actions[""] = default_act
        palette_menu.addSeparator()
        for group, names in PALETTE_GROUPS.items():
            grp_menu = palette_menu.addMenu(group)
            for name in names:
                act = grp_menu.addAction(name)
                act.setCheckable(True)
                act.triggered.connect(lambda checked, n=name: self._set_palette(n))
                ag.addAction(act)
                self._palette_actions[name] = act

        view_menu.addSeparator()
        self._act(view_menu, "Save preferences",  None,     self._save_preferences)
        self._act(view_menu, "Reset preferences", None,     self._reset_preferences)

        help_menu = mb.addMenu("Help")
        self._act(help_menu, "Documentation",  None, self._open_docs)
        self._act(help_menu, "About PyGRA",    None, self._about)

        # plot shortcut (also triggered by the Plot button)
        from PyQt5.QtWidgets import QShortcut
        from PyQt5.QtGui import QKeySequence
        QShortcut(QKeySequence("Ctrl+Return"), self).activated.connect(self._plot)

    def _open_docs(self):
        QDesktopServices.openUrl(QUrl("https://pygra.readthedocs.io"))

    def _about(self):
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel
        from PyQt5.QtGui import QPixmap
        from PyQt5.QtCore import Qt
        from pygra import __version__
        import os

        dlg = QDialog(self)
        dlg.setWindowTitle("About PyGRA")
        lay = QVBoxLayout(dlg)
        lay.setSpacing(6)

        logo_path = os.path.join(os.path.dirname(__file__),
                                 "..", "logo", "pygra_logo.png")
        logo_path = os.path.normpath(logo_path)
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path).scaledToWidth(
                120, Qt.SmoothTransformation)
            logo_lbl = QLabel()
            logo_lbl.setPixmap(pix)
            logo_lbl.setAlignment(Qt.AlignCenter)
            lay.addWidget(logo_lbl)

        for text, align in [
            ("<b>PyGRA</b>",                        Qt.AlignCenter),
            (f"Version {__version__}",              Qt.AlignCenter),
            ("Interactive scientific data plotter", Qt.AlignCenter),
            ("Author: Francesco Tosti Guerra",      Qt.AlignCenter),
            ("License: MIT",                        Qt.AlignCenter),
        ]:
            lbl = QLabel(text)
            lbl.setAlignment(align)
            lay.addWidget(lbl)

        for url, label in [
            ("https://github.com/tgfrancesco/PyGRA",  "GitHub"),
            ("https://pygra.readthedocs.io",          "Documentation"),
        ]:
            lnk = QLabel(f'<a href="{url}">{label}</a>')
            lnk.setAlignment(Qt.AlignCenter)
            lnk.setOpenExternalLinks(True)
            lay.addWidget(lnk)

        from PyQt5.QtWidgets import QDialogButtonBox
        btns = QDialogButtonBox(QDialogButtonBox.Close)
        btns.rejected.connect(dlg.reject)
        lay.addWidget(btns)
        dlg.exec_()

    def _act(self, menu, label, shortcut, slot):
        a = QAction(label, self)
        if shortcut:
            a.setShortcut(shortcut)
        a.triggered.connect(slot)
        menu.addAction(a)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)

        self._splitter = QSplitter(Qt.Horizontal)
        splitter = self._splitter
        root.addWidget(splitter)

        # ---- LEFT PANEL ----
        left = QWidget(); left.setMinimumWidth(280); left.setMaximumWidth(500)
        lv = QVBoxLayout(left); lv.setContentsMargins(6, 6, 6, 6); lv.setSpacing(6)

        # load button
        load_btn = QPushButton("Load files...")
        load_btn.clicked.connect(self._load_files)
        lv.addWidget(load_btn)

        self._series_combo = QComboBox()
        self._series_combo.setPlaceholderText("Go to series...")
        self._series_combo.setToolTip("Go to series...")
        self._series_combo.currentIndexChanged.connect(self._on_series_combo_changed)
        lv.addWidget(self._series_combo)

        # series tabs
        self.datasets_tab = QTabWidget()
        self.datasets_tab.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.datasets_tab.setTabsClosable(True)
        self.datasets_tab.tabCloseRequested.connect(self._close_tab)
        self.datasets_tab.currentChanged.connect(self._on_datasets_tab_changed)
        lv.addWidget(self.datasets_tab, stretch=1)

        # fit layer panel
        fit_group = QGroupBox("Fit & interpolation layers")
        fit_group.setMaximumHeight(180)
        fg = QVBoxLayout(fit_group)
        self._fit_scroll = QScrollArea()
        self._fit_scroll.setWidgetResizable(True)
        self._fit_scroll.setFrameShape(QFrame.NoFrame)
        self._fit_container = QWidget()
        self._fit_layout    = QVBoxLayout(self._fit_container)
        self._fit_layout.setContentsMargins(0, 0, 0, 0)
        self._fit_layout.setSpacing(2)
        self._fit_layout.addStretch()
        self._fit_scroll.setWidget(self._fit_container)
        fg.addWidget(self._fit_scroll)
        lv.addWidget(fit_group)

        # axis settings
        axis_group = QGroupBox("Axis settings")
        ag = QGridLayout(axis_group); ag.setSpacing(4)
        ag.addWidget(QLabel("x label:"), 0, 0); self.xl = QLineEdit(); ag.addWidget(self.xl, 0, 1)
        ag.addWidget(QLabel("y label:"), 1, 0); self.yl = QLineEdit(); ag.addWidget(self.yl, 1, 1)
        ag.addWidget(QLabel("title:"),   2, 0); self.title_edit = QLineEdit(); ag.addWidget(self.title_edit, 2, 1)
        self.logx = QCheckBox("log x"); self.logy = QCheckBox("log y")
        ag.addWidget(self.logx, 3, 0); ag.addWidget(self.logy, 3, 1)
        ag.addWidget(QLabel("x min:"), 4, 0); self.xmin = QLineEdit(); self.xmin.setPlaceholderText("auto"); ag.addWidget(self.xmin, 4, 1)
        ag.addWidget(QLabel("x max:"), 5, 0); self.xmax = QLineEdit(); self.xmax.setPlaceholderText("auto"); ag.addWidget(self.xmax, 5, 1)
        ag.addWidget(QLabel("y min:"), 6, 0); self.ymin = QLineEdit(); self.ymin.setPlaceholderText("auto"); ag.addWidget(self.ymin, 6, 1)
        ag.addWidget(QLabel("y max:"), 7, 0); self.ymax = QLineEdit(); self.ymax.setPlaceholderText("auto"); ag.addWidget(self.ymax, 7, 1)
        lv.addWidget(axis_group)

        # plot button
        plot_btn = QPushButton("Plot")
        plot_btn.setFixedHeight(38)
        font = plot_btn.font(); font.setBold(True); plot_btn.setFont(font)
        plot_btn.clicked.connect(self._plot)
        lv.addWidget(plot_btn)

        splitter.addWidget(left)

        # ---- RIGHT PANEL ----
        right = QWidget(); rv = QVBoxLayout(right); rv.setContentsMargins(0, 0, 0, 0)

        # minimal custom toolbar — backed by a hidden NavigationToolbar2QT
        from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT

        self.fig    = Figure(figsize=(7, 5), tight_layout=True)
        self.canvas = FigureCanvas(self.fig)

        self._nav = NavigationToolbar2QT(self.canvas, self)
        self._nav.hide()   # hidden: we drive it through our own buttons

        tb_row = QHBoxLayout(); tb_row.setSpacing(4); tb_row.setContentsMargins(4, 4, 4, 0)
        self._zoom_btn = QPushButton("🔍 Zoom")
        self._pan_btn  = QPushButton("✋ Pan")
        self._home_btn = QPushButton("⌂ Reset")
        self._zoom_btn.setCheckable(True)
        self._pan_btn.setCheckable(True)
        for b in [self._zoom_btn, self._pan_btn, self._home_btn]:
            b.setFixedHeight(28)
            tb_row.addWidget(b)
        tb_row.addStretch()
        self._coord_label = QLabel("—")
        self._coord_label.setFixedHeight(28)
        self._coord_label.setMinimumWidth(200)
        self._coord_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        from PyQt5.QtGui import QFont
        if sys.platform == "darwin":
            _mono_family = "Menlo"
        elif sys.platform == "win32":
            _mono_family = "Courier New"
        else:
            _mono_family = "DejaVu Sans Mono"
        _mono = QFont(_mono_family)
        _mono.setStyleHint(QFont.Monospace)
        self._coord_label.setFont(_mono)
        tb_row.addWidget(self._coord_label)
        rv.addLayout(tb_row)
        rv.addWidget(self.canvas)

        self._reset_leg_btn = QPushButton("↺ Legend")
        self._reset_leg_btn.setFixedHeight(28)
        self._reset_leg_btn.setToolTip("Reset legend to automatic position")
        self._reset_leg_btn.clicked.connect(self._reset_legend_pos)
        tb_row.insertWidget(3, self._reset_leg_btn)

        self._annot_btn = QPushButton("✎ Text")
        self._annot_btn.setFixedHeight(28)
        self._annot_btn.setToolTip("Add text annotation")
        self._annot_btn.clicked.connect(self._add_annotation)
        tb_row.insertWidget(4, self._annot_btn)

        self._zoom_btn.toggled.connect(self._toggle_zoom)
        self._pan_btn.toggled.connect(self._toggle_pan)
        self._home_btn.clicked.connect(self._home)

        # legend drag events
        self.canvas.mpl_connect("button_press_event",   self._on_mouse_press)
        self.canvas.mpl_connect("motion_notify_event",  self._on_mouse_move)
        self.canvas.mpl_connect("button_release_event", self._on_mouse_release)

        splitter.addWidget(right)
        splitter.setStretchFactor(1, 1)

    # ------------------------------------------------------------------
    # Custom toolbar
    # ------------------------------------------------------------------

    def _toggle_zoom(self, on: bool):
        if on:
            self._pan_btn.setChecked(False)
            self._nav.zoom()
        else:
            # call zoom again to deactivate if currently in zoom mode
            if "zoom" in str(self._nav.mode):
                self._nav.zoom()

    def _toggle_pan(self, on: bool):
        if on:
            self._zoom_btn.setChecked(False)
            self._nav.pan()
        else:
            if "pan" in str(self._nav.mode):
                self._nav.pan()

    def _home(self):
        self._zoom_btn.setChecked(False)
        self._pan_btn.setChecked(False)
        self._nav.home()

    def _reset_legend_pos(self):
        """Reset legend to automatic positioning."""
        self._legend_pos = None
        self._plot()

    # ------------------------------------------------------------------
    # Geometry / preferences
    # ------------------------------------------------------------------

    def _restore_geometry(self):
        p = self._prefs
        self.move(p.get("window_x", 100), p.get("window_y", 100))
        self.resize(p.get("window_w", 1200), p.get("window_h", 760))
        sp = p.get("splitter_pos", 330)
        total = self._splitter.width() or (p.get("window_w", 1200))
        self._splitter.setSizes([sp, max(1, total - sp)])
        # restore saved color palette
        saved_palette = p.get("last_basic_palette", "")
        if saved_palette:
            apply_basic_palette(saved_palette)
        def _check_palette_action():
            act = self._palette_actions.get(saved_palette) or self._palette_actions.get("")
            if act:
                act.setChecked(True)
        QTimer.singleShot(0, _check_palette_action)

    def _collect_geometry(self) -> dict:
        geo  = self.geometry()
        sizes = self._splitter.sizes()
        return {
            "window_x":   geo.x(),
            "window_y":   geo.y(),
            "window_w":   geo.width(),
            "window_h":   geo.height(),
            "splitter_pos": sizes[0] if sizes else 330,
        }

    def _set_palette(self, name: str):
        """Apply a color palette to the basic colors grid and save to prefs."""
        if name:
            apply_basic_palette(name)
        else:
            restore_basic_palette()
        self._prefs["last_basic_palette"] = name
        if name in self._palette_actions:
            self._palette_actions[name].setChecked(True)
        try:
            from .preferences import save_prefs
            prefs = dict(self._prefs)
            prefs.update(self._collect_geometry())
            prefs.update(self.style_settings)
            save_prefs(prefs)
        except Exception as e:
            print(f"Warning: could not save preferences: {e}", file=sys.stderr)

    def _save_preferences(self):
        """Save current geometry + style settings as user preferences."""
        prefs = dict(self._prefs)
        prefs.update(self._collect_geometry())
        prefs.update(self.style_settings)
        # preserve custom colors
        prefs["custom_colors"] = self._prefs.get("custom_colors", [])
        save_prefs(prefs)
        self._prefs = prefs
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "Preferences saved",
                                f"Preferences saved to:\n{PREFS_PATH}")

    def _reset_preferences(self):
        from PyQt5.QtWidgets import QMessageBox
        from .preferences import DEFAULT_PREFS
        reply = QMessageBox.question(self, "Reset preferences",
                                     "Reset all preferences to defaults?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            save_prefs(dict(DEFAULT_PREFS))
            self._prefs = dict(DEFAULT_PREFS)
            QMessageBox.information(self, "Done",
                                    "Preferences reset. Restart PyGRA to apply.")

    def closeEvent(self, event):
        """Auto-save geometry on close."""
        prefs = dict(self._prefs)
        prefs.update(self._collect_geometry())
        save_prefs(prefs)
        super().closeEvent(event)

    # ------------------------------------------------------------------
    # Legend drag
    # ------------------------------------------------------------------

    def _on_mouse_press(self, event):
        if self._zoom_btn.isChecked() or self._pan_btn.isChecked():
            return
        ax = self.fig.axes[0] if self.fig.axes else None
        if ax is None:
            return

        # check annotation artists
        self._dragging_annot_idx = -1
        for i, txt in enumerate(self._annot_artists):
            try:
                hit, _ = txt.contains(event)
            except Exception:
                hit = False
            if not hit:
                continue
            if event.button == 3:                          # right-click → delete
                menu = QMenu(self)
                del_act = menu.addAction("Delete annotation")
                from PyQt5.QtGui import QCursor
                chosen = menu.exec_(QCursor.pos())
                if chosen == del_act:
                    self._annotations.pop(i)
                    self._plot()
                return
            if event.dblclick:                             # double-click → edit
                dlg = TextAnnotationDialog(self._annotations[i], self)
                if dlg.exec_():
                    cfg = dlg.get_config()
                    self._annotations[i].update(cfg)
                    self._plot()
                return
            self._dragging_annot_idx = i                   # single left-click → drag
            return

        # check percentage labels
        self._dragging_pct_idx = -1
        for i, txt in enumerate(self._pct_text_artists):
            try:
                if txt.contains(event)[0]:
                    self._dragging_pct_idx = i
                    return
            except Exception:
                pass

        if event.dblclick and event.button in (1, MouseButton.LEFT):
            if self._activate_tab_for_clicked_curve(ax, event):
                return

        # check legend
        leg = ax.get_legend()
        if leg and leg.contains(event)[0]:
            self._dragging_legend = True

    def _activate_tab_for_clicked_curve(self, ax, event) -> bool:
        """Switch to the series tab for a double-clicked plot line."""
        if event.inaxes is not ax:
            return False
        for line in ax.get_lines():
            old_pickradius = None
            try:
                old_pickradius = line.get_pickradius()
                line.set_pickradius(8)
                hit, _ = line.contains(event)
            except Exception:
                hit = False
            finally:
                try:
                    if old_pickradius is not None:
                        line.set_pickradius(old_pickradius)
                except Exception:
                    pass
            if not hit:
                continue
            label = line.get_label()
            for index, dw in enumerate(self.dataset_widgets):
                if label == dw.get_config().get("label"):
                    self.datasets_tab.setCurrentIndex(index)
                    return True
        return False

    def _on_mouse_move(self, event):
        # coordinate display
        if event.inaxes is not None and not (self._zoom_btn.isChecked() or self._pan_btn.isChecked()):
            self._coord_label.setText(f"x = {event.xdata:.4g}   y = {event.ydata:.4g}")
        else:
            self._coord_label.setText("—")

        # drag annotation
        if self._dragging_annot_idx >= 0:
            ax = self.fig.axes[0] if self.fig.axes else None
            if ax is not None:
                try:
                    fx, fy = ax.transAxes.inverted().transform((event.x, event.y))
                    txt = self._annot_artists[self._dragging_annot_idx]
                    txt.set_position((fx, fy))
                    self._annotations[self._dragging_annot_idx]["x"] = fx
                    self._annotations[self._dragging_annot_idx]["y"] = fy
                    self.canvas.draw_idle()
                except (ValueError, RuntimeError, IndexError):
                    pass
            return

        # drag percentage label
        if self._dragging_pct_idx >= 0:
            ax = self.fig.axes[0] if self.fig.axes else None
            if ax is not None and event.xdata is not None:
                try:
                    x_d, y_d = ax.transData.inverted().transform((event.x, event.y))
                    txt = self._pct_text_artists[self._dragging_pct_idx]
                    txt.set_position((x_d, y_d))
                    while len(self._pct_label_positions) <= self._dragging_pct_idx:
                        self._pct_label_positions.append(None)
                    self._pct_label_positions[self._dragging_pct_idx] = (x_d, y_d)
                    self.canvas.draw_idle()
                except (ValueError, RuntimeError, IndexError):
                    pass
            return

        if not self._dragging_legend:
            return
        ax = self.fig.axes[0] if self.fig.axes else None
        if ax is None:
            return
        # convert display (pixel) coords to axes fraction via transform
        try:
            inv = ax.transAxes.inverted()
            fx, fy = inv.transform((event.x, event.y))
        except (ValueError, RuntimeError):
            return
        self._legend_pos = (fx, fy)
        leg = ax.get_legend()
        if leg:
            leg.set_bbox_to_anchor((fx, fy), transform=ax.transAxes)
            leg._loc = 6
            self.canvas.draw_idle()

    def _on_mouse_release(self, event):
        self._dragging_legend = False
        self._dragging_pct_idx = -1
        self._dragging_annot_idx = -1

    # ------------------------------------------------------------------
    # File actions
    # ------------------------------------------------------------------

    def _load_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Open data files", "",
            "Data files (*.dat *.txt *.csv *);;All files (*)",
        )
        for path in paths:
            self._load_file(path)

    def _load_file(self, path: str, xcol: int = 0, ycol: int = 1,
                   dxcol: int = 0, dycol: int = 0, step: int = 1):
        try:
            ds = DataSet(path, step=step)
            if ds.skipped_rows:
                n = len(ds.skipped_rows)
                examples = "\n".join(
                    f"  line {ln}: {content}"
                    for ln, content in ds.skipped_rows[:5]
                )
                tail = f"\n  … and {n - 5} more" if n > 5 else ""
                QMessageBox.warning(
                    self, "Rows skipped",
                    f"{n} row{'s' if n != 1 else ''} could not be parsed in:\n{path}\n\n"
                    f"Non-numeric content was ignored:\n{examples}{tail}"
                )
            if ds.ncols == 0:
                QMessageBox.warning(self, "Empty file", f"No numeric data in:\n{path}")
                return None
            self.datasets.append(ds)
            dw = self._add_dataset_widget(ds)
            if xcol != 0 and xcol < ds.ncols: dw.xcol.setValue(xcol)
            if ycol != 1 and ycol < ds.ncols: dw.ycol.setValue(ycol)
            if dxcol > 0 and dxcol < ds.ncols: dw.dxcol.setValue(dxcol)
            if dycol > 0 and dycol < ds.ncols: dw.dycol.setValue(dycol)
            return dw
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load {path}:\n{e}")
            return None

    def _add_dataset_widget(self, ds: DataSet) -> DatasetWidget:
        color = COLORS[len(self.dataset_widgets) % len(COLORS)]
        n = sum(1 for dw in self.dataset_widgets if dw.dataset is ds)
        tab_name = ds.name if n == 0 else f"{ds.name} [{n + 1}]"
        dw = DatasetWidget(
            ds, color,
            on_duplicate=self._add_dataset_widget,
            on_replot=self._refresh_series_combo_and_plot,
        )
        self.dataset_widgets.append(dw)
        self.datasets_tab.addTab(dw, tab_name)
        self.datasets_tab.setCurrentWidget(dw)
        self._refresh_series_combo()
        return dw

    def _close_tab(self, index: int):
        """Remove a series tab and its associated data."""
        if index < 0 or index >= len(self.dataset_widgets):
            return
        dw = self.dataset_widgets[index]
        # also remove the dataset if no other widget references it
        ds = dw.dataset
        self.dataset_widgets.pop(index)
        self.datasets_tab.removeTab(index)
        other_refs = [w for w in self.dataset_widgets if w.dataset is ds]
        if not other_refs and ds in self.datasets:
            self.datasets.remove(ds)
        self._refresh_series_combo()

    def _on_series_combo_changed(self, index: int):
        if self._syncing_series_nav:
            return
        if 0 <= index < self.datasets_tab.count():
            self._syncing_series_nav = True
            self.datasets_tab.setCurrentIndex(index)
            self._syncing_series_nav = False

    def _on_datasets_tab_changed(self, index: int):
        if self._syncing_series_nav:
            return
        if index != self._series_combo.currentIndex():
            self._syncing_series_nav = True
            self._series_combo.setCurrentIndex(index)
            self._syncing_series_nav = False

    def _refresh_series_combo(self):
        current = self.datasets_tab.currentIndex()
        self._syncing_series_nav = True
        self._series_combo.clear()
        for dw in self.dataset_widgets:
            label = dw.get_config().get("label") or dw.dataset.name
            self._series_combo.addItem(label)
        if 0 <= current < self._series_combo.count():
            self._series_combo.setCurrentIndex(current)
        self._syncing_series_nav = False

    def _refresh_series_combo_and_plot(self):
        self._refresh_series_combo()
        self._plot()

    def _export_active(self):
        idx = self.datasets_tab.currentIndex()
        if idx < 0 or idx >= len(self.dataset_widgets):
            return
        ds = self.dataset_widgets[idx].dataset
        path, _ = QFileDialog.getSaveFileName(
            self, "Export data", ds.name + "_export.dat",
            "Data files (*.dat *.txt);;All files (*)"
        )
        if path:
            try:
                header = "  ".join(f"col{i}" for i in range(ds.ncols))
                np.savetxt(path, ds.arr, header=header, fmt="%.10g")
                QMessageBox.information(self, "Exported", f"Data saved to:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    # ------------------------------------------------------------------
    # View actions
    # ------------------------------------------------------------------

    def _open_style(self):
        dlg = StyleDialog(self.style_settings, self)
        if dlg.exec_() == QDialog.Accepted:
            self.style_settings = dlg.get_settings()

    # ------------------------------------------------------------------
    # Analysis actions
    # ------------------------------------------------------------------

    def _active_widget(self):
        idx = self.datasets_tab.currentIndex()
        if 0 <= idx < len(self.dataset_widgets):
            return self.dataset_widgets[idx]
        return None

    def _transform_active(self):
        dw = self._active_widget()
        if not dw:
            return
        dlg = TransformDialog(dw.dataset.ncols, self)
        if dlg.exec_() != QDialog.Accepted:
            return
        cfg = dlg.get_config()
        try:
            apply_transform(dw.dataset, cfg)
            dw.refresh_col_ranges()
            msg = (f"New column {dw.dataset.ncols - 1} added."
                   if cfg["new_col"] else f"Column {cfg['col']} updated.")
            QMessageBox.information(self, "Done", msg)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _stats_active(self):
        dw = self._active_widget()
        if dw:
            StatsDialog(dw.dataset, self).exec_()

    def _edit_data_active(self):
        """Open a table editor for the active series data."""
        dw = self._active_widget()
        if not dw:
            return
        dlg = DataEditorDialog(dw.dataset, self)
        if dlg.exec_() == QDialog.Accepted:
            dw.refresh_col_ranges()
            self._plot()

    def _fit_active(self):
        dw = self._active_widget()
        if not dw:
            return
        cfg = dw.get_config()

        # build fit dialog with last settings if available
        fit_cfg = getattr(dw, "_last_fit_cfg", {
            "fit_method":     "Gaussian (distribution)",
            "poly_deg":       3,
            "custom_formula": "a * exp(-b * x)",
            "custom_params":  ["a", "b"],
            "fit_color":      "#d62728",
        })
        dlg = FitDialog(fit_cfg, self)
        if dlg.exec_() != QDialog.Accepted:
            return
        fit_cfg = dlg.get_config()
        dw._last_fit_cfg = fit_cfg

        method = fit_cfg["fit_method"]
        color  = fit_cfg["fit_color"]

        # pick data column
        if cfg["hist_mode"]:
            data = dw.dataset.col(cfg["hcol"])
        else:
            data = dw.dataset.col(cfg["xcol"])

        if data is None:
            QMessageBox.warning(self, "Fit", "No data in selected column.")
            return

        x_src = dw.dataset.col(cfg["xcol"]) if not cfg["hist_mode"] else None
        y_src = dw.dataset.col(cfg["ycol"]) if not cfg["hist_mode"] else None

        # --- resolve fit x range ---
        if fit_cfg.get("fit_use_zoom", False):
            ax = self.fig.axes[0] if self.fig.axes else None
            if ax:
                xmin, xmax = ax.get_xlim()
            else:
                xmin, xmax = None, None
        else:
            raw_min = fit_cfg.get("fit_xmin", -1e10)
            raw_max = fit_cfg.get("fit_xmax",  1e10)
            xmin = raw_min if raw_min > -1e9 else None
            xmax = raw_max if raw_max <  1e9 else None

        if x_src is not None and y_src is not None:
            mask = np.ones(len(x_src), dtype=bool)
            if xmin is not None:
                mask &= x_src >= xmin
            if xmax is not None:
                mask &= x_src <= xmax
            x_src = x_src[mask]
            y_src = y_src[mask]

        if cfg["hist_mode"]:
            if xmin is not None:
                data = data[data >= xmin]
            if xmax is not None:
                data = data[data <= xmax]

        try:
            if method in ("spline", "linear fit", "polynomial fit"):
                if x_src is None or y_src is None:
                    QMessageBox.warning(self, "Fit", "Interpolation requires x and y columns.")
                    return
                x_plot_min = xmin if xmin is not None else x_src.min()
                x_plot_max = xmax if xmax is not None else x_src.max()
                xi = np.linspace(x_plot_min, x_plot_max, 300)
                if method == "spline":
                    idx_s = np.argsort(x_src)
                    from scipy.interpolate import make_interp_spline as mbs
                    spl = mbs(x_src[idx_s], y_src[idx_s], k=min(3, len(x_src) - 1))
                    yi = spl(xi)
                    lbl = "spline"
                elif method == "linear fit":
                    p = np.polyfit(x_src, y_src, 1)
                    yi = np.polyval(p, xi)
                    lbl = f"linear  a={p[0]:.4g}  b={p[1]:.4g}"
                else:
                    deg = fit_cfg["poly_deg"]
                    p   = np.polyfit(x_src, y_src, deg)
                    yi  = np.polyval(p, xi)
                    lbl = f"poly deg={deg}"
                xf, yf = xi, yi

            elif method in ("Gaussian curve", "Exponential curve"):
                if x_src is None or y_src is None:
                    QMessageBox.warning(self, "Fit", "Curve fit requires x and y columns.")
                    return
                if method == "Gaussian curve":
                    xf, yf, lbl, params = fit_gaussian_curve(x_src, y_src)
                else:
                    xf, yf, lbl, params = fit_exponential_curve(x_src, y_src)
                param_str = "\n".join(f"  {k} = {v:.6g}" for k, v in params.items())
                QMessageBox.information(self, f"Fit: {method}", f"{lbl}\n\nParameters:\n{param_str}")

            elif method == "Custom...":
                xf, yf, lbl, params = fit_custom(
                    data, fit_cfg["custom_formula"], fit_cfg["custom_params"]
                )
                param_str = "\n".join(f"  {k} = {v:.6g}" for k, v in params.items())
                QMessageBox.information(self, "Custom fit", f"{lbl}\n\nParameters:\n{param_str}")

            else:
                xf, yf, lbl, params = FIT_FUNCTIONS[method](data)

                # scale PDF to match histogram normalisation
                if cfg["hist_mode"]:
                    norm = cfg.get("hist_norm", "count")
                    bins = cfg["hist_nbins"] if cfg["hist_bins"] == "manual" else cfg["hist_bins"]
                    counts, edges = np.histogram(data, bins=bins)
                    bin_width = np.mean(np.diff(edges))
                    if norm == "count":
                        # PDF × N × bin_width gives expected counts per bin
                        yf = yf * counts.sum() * bin_width
                    elif norm == "probability":
                        # PDF × bin_width gives probability per bin
                        yf = yf * bin_width
                    # density: no scaling needed, PDF already in correct units

                param_str = "\n".join(f"  {k} = {v:.6g}" for k, v in params.items())
                QMessageBox.information(self, f"Fit: {method}", f"{lbl}\n\nParameters:\n{param_str}")

            layer = FitLayer(
                label=lbl,
                x=xf, y=yf,
                color=color,
                source_label=cfg["label"] or dw.dataset.name,
            )
            self.fit_layers.append(layer)
            self._add_fit_layer_widget(layer)
            self._plot()

        except Exception as e:
            QMessageBox.critical(self, "Fit error", str(e))

    # ------------------------------------------------------------------
    # Fit layer panel
    # ------------------------------------------------------------------

    def _add_fit_layer_widget(self, layer: FitLayer):
        w = FitLayerWidget(
            layer,
            on_remove=self._remove_fit_layer,
            on_toggle=self._toggle_fit_layer,
            on_edit=self._edit_fit_layer,
        )
        # insert before the trailing stretch
        count = self._fit_layout.count()
        self._fit_layout.insertWidget(count - 1, w)

    def _remove_fit_layer(self, layer: FitLayer):
        self.fit_layers.remove(layer)
        # rebuild fit panel
        self._rebuild_fit_panel()
        self._plot()

    def _toggle_fit_layer(self, layer: FitLayer, visible: bool):
        layer.visible = visible
        self._plot()

    def _edit_fit_layer(self, layer: FitLayer, widget: "FitLayerWidget"):
        """Open appearance dialog for a fit layer on double-click."""
        from PyQt5.QtWidgets import (QDialog, QDialogButtonBox,
                                     QFormLayout, QVBoxLayout, QLineEdit,
                                     QPushButton, QComboBox, QDoubleSpinBox)
        from .constants import LINESTYLES, LINESTYLE_LABELS

        dlg = QDialog(self)
        dlg.setWindowTitle("Edit fit layer")
        layout = QVBoxLayout(dlg)
        form = QFormLayout()

        label_edit = QLineEdit(layer.label)
        form.addRow("Label:", label_edit)

        ls_combo = QComboBox()
        ls_combo.addItems(LINESTYLE_LABELS)
        ls = layer.linestyle if layer.linestyle != "None" else "--"
        if ls in LINESTYLES:
            ls_combo.setCurrentIndex(LINESTYLES.index(ls))
        form.addRow("Line style:", ls_combo)

        lw_spin = QDoubleSpinBox()
        lw_spin.setRange(0.1, 10); lw_spin.setSingleStep(0.5)
        lw_spin.setValue(layer.linewidth)
        form.addRow("Line width:", lw_spin)

        _color = [layer.color]
        color_btn = QPushButton(layer.color)
        color_btn.setStyleSheet(
            f"background-color: {layer.color}; border: 1px solid #888; "
            f"border-radius: 4px; padding: 4px 8px;"
        )
        def pick_color():
            from .dialogs import pick_color as _pick
            new_c = _pick(_color[0], dlg)
            if new_c != _color[0]:
                _color[0] = new_c
                color_btn.setText(_color[0])
                color_btn.setStyleSheet(
                    f"background-color: {_color[0]}; border: 1px solid #888; "
                    f"border-radius: 4px; padding: 4px 8px;"
                )
        color_btn.clicked.connect(pick_color)
        form.addRow("Line color:", color_btn)

        layout.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)

        if dlg.exec_() == QDialog.Accepted:
            layer.label     = label_edit.text()
            layer.linestyle = LINESTYLES[ls_combo.currentIndex()]
            layer.linewidth = lw_spin.value()
            layer.color     = _color[0]
            widget._refresh_label()
            widget.color_dot.setStyleSheet(f"color: {layer.color}; font-size: 14px;")
            self._plot()

    def _rebuild_fit_panel(self):
        # clear all widgets except the stretch
        while self._fit_layout.count() > 1:
            item = self._fit_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for layer in self.fit_layers:
            self._add_fit_layer_widget(layer)

    # ------------------------------------------------------------------
    # Session save / load
    # ------------------------------------------------------------------

    def _get_axis_settings(self) -> dict:
        return {
            "xl": self.xl.text(), "yl": self.yl.text(),
            "title": self.title_edit.text(),
            "logx": self.logx.isChecked(), "logy": self.logy.isChecked(),
            "xmin": self.xmin.text(), "xmax": self.xmax.text(),
            "ymin": self.ymin.text(), "ymax": self.ymax.text(),
        }

    def _apply_axis_settings(self, s: dict):
        self.xl.setText(s.get("xl", ""))
        self.yl.setText(s.get("yl", ""))
        self.title_edit.setText(s.get("title", ""))
        self.logx.setChecked(s.get("logx", False))
        self.logy.setChecked(s.get("logy", False))
        self.xmin.setText(s.get("xmin", "")); self.xmax.setText(s.get("xmax", ""))
        self.ymin.setText(s.get("ymin", "")); self.ymax.setText(s.get("ymax", ""))

    def _save_state(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save session", "session.json", "JSON (*.json);;All files (*)"
        )
        if not path:
            return
        try:
            save_state(path, self.dataset_widgets,
                       self._get_axis_settings(), self.style_settings,
                       self._annotations)
            QMessageBox.information(self, "Saved", f"Session saved to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _load_state(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Load session", "", "JSON (*.json);;All files (*)"
        )
        if not paths:
            return
        try:
            self._apply_state(load_state(paths[0]))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _load_state_from_path(self, path: str):
        self._apply_state(load_state(path))

    def _apply_state(self, state: dict):
        self.datasets.clear()
        self.dataset_widgets.clear()
        self.fit_layers.clear()
        self._rebuild_fit_panel()
        while self.datasets_tab.count():
            self.datasets_tab.removeTab(0)

        for s in state["series"]:
            ds = DataSet.__new__(DataSet)
            ds.path = s["path"]; ds.name = s["name"]
            ds.raw  = s["data"].tolist(); ds.arr  = s["data"]
            self.datasets.append(ds)
            dw = self._add_dataset_widget(ds)
            cfg = s["config"]
            dw.xcol.setValue(cfg.get("xcol", 0))
            dw.ycol.setValue(cfg.get("ycol", 1))
            dw.dxcol.setValue(cfg.get("dxcol", -1))
            dw.dycol.setValue(cfg.get("dycol", -1))
            dw._series_style["label"] = cfg.get("label", ds.name)
            if cfg.get("hist2d_mode", False):
                dw.set_mode("hist2d")
            elif cfg.get("hist_mode", False):
                dw.set_mode("histogram")
            else:
                dw.set_mode("series")
            dw.visible.setChecked(cfg.get("visible", True))
            for k in dw._series_style:
                if k in cfg: dw._series_style[k] = cfg[k]
            for k in dw._hist_style:
                if k in cfg: dw._hist_style[k] = cfg[k]
            for k in dw._hist2d_style:
                if k in cfg: dw._hist2d_style[k] = cfg[k]

        self._apply_axis_settings(state.get("axis_settings", {}))
        self.style_settings = state.get("style_settings", dict(DEFAULT_STYLE_SETTINGS))
        self._annotations = state.get("annotations", [])
        self._refresh_series_combo()

    def _add_annotation(self):
        """Open TextAnnotationDialog and add a new annotation at axes centre."""
        dlg = TextAnnotationDialog(parent=self)
        if not dlg.exec_():
            return
        cfg = dlg.get_config()
        cfg["x"] = 0.5
        cfg["y"] = 0.5
        self._annotations.append(cfg)
        self._plot()

    # ------------------------------------------------------------------
    # Plot
    # ------------------------------------------------------------------

    def _plot(self):
        import matplotlib.pyplot as plt
        ss    = self.style_settings
        theme = ss.get("theme", "default")
        try:
            plt.rcdefaults() if theme == "default" else plt.style.use(theme)
        except Exception as e:
            print(f"Warning: could not apply theme '{theme}': {e}", file=sys.stderr)

        self.fig.clear()
        ax = self.fig.add_subplot(111)

        # reset pct-label positions when the series identity changes
        new_pct_key = tuple(
            (dw.dataset.name, dw.get_config()["hcol"],
             dw.get_config()["hist_bins"], dw.get_config()["hist_nbins"],
             dw.get_config().get("hist_horizontal", False))
            for dw in self.dataset_widgets
            if dw.get_config()["visible"]
            and dw.get_config()["hist_mode"]
            and dw.get_config().get("hist_show_pct", False)
        )
        if new_pct_key != self._pct_series_key:
            self._pct_label_positions = []
            self._pct_series_key = new_pct_key

        result = render_plot(
            fig=self.fig,
            ax=ax,
            dataset_widgets=self.dataset_widgets,
            fit_layers=self.fit_layers,
            annotations=self._annotations,
            style_settings=self.style_settings,
            axis_settings=self._get_axis_settings(),
            legend_pos=self._legend_pos,
            pct_label_positions=self._pct_label_positions,
        )

        self._current_legend  = result["legend"]
        self._pct_text_artists = result["pct_texts"]
        self._annot_artists    = result["annot_artists"]

        self.canvas.draw()

    def _save_figure(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save figure", "plot.png",
            "PNG (*.png);;PDF (*.pdf);;SVG (*.svg);;All files (*)",
        )
        if not path:
            return
        dpi = self.style_settings.get("dpi", 150)
        auto = self.style_settings.get("fig_size_auto", True)
        if auto:
            self.fig.savefig(path, dpi=dpi, bbox_inches="tight")
        else:
            w = self.style_settings.get("fig_w", 8.0)
            h = self.style_settings.get("fig_h", 5.0)
            orig_size = self.fig.get_size_inches()
            self.fig.set_size_inches(w, h)
            self.fig.savefig(path, dpi=dpi, bbox_inches="tight")
            self.fig.set_size_inches(*orig_size)
            self.canvas.draw_idle()
