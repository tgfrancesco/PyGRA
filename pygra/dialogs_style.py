"""
dialogs_style.py — color palette helpers and appearance/style dialogs
"""

import sys

from PyQt5.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QVBoxLayout, QHBoxLayout,
    QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox, QFrame,
    QLabel, QLineEdit, QPushButton, QColorDialog, QWidget,
)
from PyQt5.QtGui import QColor

from .constants import (
    DEFAULT_STYLE_SETTINGS, PLOT_THEMES,
    LINESTYLES, LINESTYLE_LABELS, MARKERS, MARKER_LABELS,
)


# ---------------------------------------------------------------------------
# Basic colors palette management
# ---------------------------------------------------------------------------

_DEFAULT_STANDARD = [
    "#000000","#ffffff","#808080","#c0c0c0","#800000","#ff0000","#808000","#ffff00",
    "#008000","#00ff00","#008080","#00ffff","#000080","#0000ff","#800080","#ff00ff",
    "#804000","#ff8000","#004080","#0080ff","#408000","#80ff00","#004040","#008080",
    "#400080","#8000ff","#804040","#ff8080","#408040","#80ff80","#004080","#0080c0",
    "#804080","#ff80ff","#808040","#ffff80","#400000","#ff4040","#004000","#40ff40",
    "#000040","#4040ff","#440044","#ff44ff","#444400","#ffff44","#004444","#44ffff",
]


def apply_basic_palette(name: str):
    """
    Replace the QColorDialog basic-colors grid with a named palette.

    The palette is tiled to fill all 48 slots.  If *name* is not found
    in :data:`palettes.PALETTES`, the Qt factory defaults are restored
    instead.

    Parameters
    ----------
    name : str
        Palette name as it appears in :data:`palettes.PALETTES`.
    """
    from .palettes import PALETTES
    colors = PALETTES.get(name, [])
    if not colors:
        restore_basic_palette()
        return
    tiled = []
    while len(tiled) < 48:
        tiled.extend(colors)
    for i, hex_c in enumerate(tiled[:48]):
        try:
            QColorDialog.setStandardColor(i, QColor(hex_c))
        except Exception as e:
            print(f"Warning: could not set standard color slot {i} ({hex_c!r}): {e}", file=sys.stderr)


def restore_basic_palette():
    """Reset the QColorDialog basic-colors grid to the Qt factory defaults."""
    for i, hex_c in enumerate(_DEFAULT_STANDARD):
        try:
            QColorDialog.setStandardColor(i, QColor(hex_c))
        except Exception as e:
            print(f"Warning: could not restore standard color slot {i} ({hex_c!r}): {e}", file=sys.stderr)


def pick_color(current: str, parent=None) -> str:
    """
    Open a color picker dialog and return the chosen hex color.

    The basic-colors grid reflects whatever palette was last set via
    :func:`apply_basic_palette`.  Custom colors are restored from
    preferences before the dialog opens and saved back afterwards.
    On macOS the "Pick Screen Color" button is hidden because system
    security restrictions confine it to the dialog window.

    Parameters
    ----------
    current : str
        Hex color string shown as the initial selection (e.g.
        ``"#1f77b4"``).
    parent : QWidget, optional
        Parent widget for the dialog.

    Returns
    -------
    str
        Hex color string chosen by the user, or *current* if the dialog
        was cancelled.
    """
    try:
        from .preferences import load_prefs, save_prefs
        prefs = load_prefs()
        custom = prefs.get("custom_colors", [])
    except Exception as e:
        print(f"Warning: could not load color preferences: {e}", file=sys.stderr)
        custom = []
        prefs = {}

    saved_palette = prefs.get("last_basic_palette", "")
    palette_label = saved_palette if saved_palette else "Qt default"

    for i, hex_c in enumerate(custom[:16]):
        try:
            QColorDialog.setCustomColor(i, QColor(hex_c))
        except Exception as e:
            print(f"Warning: could not restore custom color slot {i} ({hex_c!r}): {e}", file=sys.stderr)

    title = f"Pick Color  —  Basic colors palette: {palette_label}"
    if sys.platform == "darwin":
        # On macOS, "Pick Screen Color" only captures within the dialog window
        # due to system security restrictions — hide it to avoid confusion
        cd = QColorDialog(QColor(current), parent)
        cd.setOptions(QColorDialog.DontUseNativeDialog)
        cd.setWindowTitle(title)
        try:
            from PyQt5.QtWidgets import QAbstractButton
            for btn in cd.findChildren(QAbstractButton):
                if "screen" in btn.text().lower():
                    btn.hide()
                    break
        except Exception as e:
            print(f"Warning: could not hide screen color picker button: {e}", file=sys.stderr)
        cd.exec_()
        c = cd.currentColor() if cd.result() == QDialog.Accepted else QColor()
    else:
        c = QColorDialog.getColor(
            QColor(current), parent,
            title=title,
            options=QColorDialog.DontUseNativeDialog,
        )
    if not c.isValid():
        return current

    new_custom = []
    for i in range(16):
        try:
            cc = QColorDialog.customColor(i)
            if cc.isValid() and cc.name() != "#000000":
                new_custom.append(cc.name())
        except Exception as e:
            print(f"Warning: could not read custom color slot {i}: {e}", file=sys.stderr)
    try:
        prefs["custom_colors"] = list(dict.fromkeys(new_custom))[:16]
        save_prefs(prefs)
    except Exception as e:
        print(f"Warning: could not save color preferences: {e}", file=sys.stderr)

    return c.name()


# ---------------------------------------------------------------------------
# StyleDialog  (global style: fonts, ticks, grid, theme, DPI)
# ---------------------------------------------------------------------------

class StyleDialog(QDialog):
    """
    Global style settings dialog.

    Controls font sizes for title, axis labels, ticks, and legend;
    major and minor tick spacing; grid visibility; plot theme; save DPI;
    and legend appearance (position, frame, alpha, columns, symbol size).

    Parameters
    ----------
    settings : dict
        Current style settings (see :data:`constants.DEFAULT_STYLE_SETTINGS`).
    parent : QWidget, optional
        Parent widget.
    """

    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Style settings")
        self.settings = dict(settings)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        s = self.settings

        self.title_fs  = QSpinBox(); self.title_fs.setRange(6, 40);  self.title_fs.setValue(s.get("title_fs", 14))
        self.label_fs  = QSpinBox(); self.label_fs.setRange(6, 40);  self.label_fs.setValue(s.get("label_fs", 13))
        self.tick_fs   = QSpinBox(); self.tick_fs.setRange(6, 40);   self.tick_fs.setValue(s.get("tick_fs",   11))
        self.legend_fs = QSpinBox(); self.legend_fs.setRange(6, 40); self.legend_fs.setValue(s.get("legend_fs", 11))
        form.addRow("Title font size:",       self.title_fs)
        form.addRow("Axis label font size:",  self.label_fs)
        form.addRow("Tick label font size:",  self.tick_fs)
        form.addRow("Legend font size:",      self.legend_fs)

        self._sep(form)

        self.major_x = QDoubleSpinBox(); self.major_x.setRange(0, 1e9); self.major_x.setValue(s.get("major_x", 0)); self.major_x.setSpecialValueText("auto")
        self.major_y = QDoubleSpinBox(); self.major_y.setRange(0, 1e9); self.major_y.setValue(s.get("major_y", 0)); self.major_y.setSpecialValueText("auto")
        self.minor_x = QSpinBox(); self.minor_x.setRange(0, 20); self.minor_x.setValue(s.get("minor_x", 0)); self.minor_x.setSpecialValueText("off")
        self.minor_y = QSpinBox(); self.minor_y.setRange(0, 20); self.minor_y.setValue(s.get("minor_y", 0)); self.minor_y.setSpecialValueText("off")
        form.addRow("Major tick spacing x:", self.major_x)
        form.addRow("Major tick spacing y:", self.major_y)
        form.addRow("Minor ticks x:",        self.minor_x)
        form.addRow("Minor ticks y:",        self.minor_y)

        self._sep(form)

        self.grid_major = QCheckBox(); self.grid_major.setChecked(s.get("grid_major", True))
        self.grid_minor = QCheckBox(); self.grid_minor.setChecked(s.get("grid_minor", False))
        form.addRow("Major grid:", self.grid_major)
        form.addRow("Minor grid:", self.grid_minor)

        self._sep(form)

        self.theme = QComboBox(); self.theme.addItems(PLOT_THEMES)
        self.theme.setCurrentText(s.get("theme", "default"))
        form.addRow("Plot theme:", self.theme)

        self.dpi = QSpinBox(); self.dpi.setRange(72, 600); self.dpi.setValue(s.get("dpi", 150))
        form.addRow("Save DPI:", self.dpi)

        self._sep(form)

        # legend options
        self.legend_show = QCheckBox()
        self.legend_show.setChecked(s.get("legend_show", True))
        form.addRow("Show legend:", self.legend_show)

        LEGEND_LOCS = ["best", "upper right", "upper left", "lower left",
                       "lower right", "right", "center left", "center right",
                       "lower center", "upper center", "center"]
        self.legend_loc = QComboBox()
        self.legend_loc.addItems(LEGEND_LOCS)
        self.legend_loc.setCurrentText(s.get("legend_loc", "best"))
        form.addRow("Legend position:", self.legend_loc)

        self.legend_frameon = QCheckBox()
        self.legend_frameon.setChecked(s.get("legend_frameon", True))
        form.addRow("Legend frame:", self.legend_frameon)

        self.legend_alpha = QDoubleSpinBox()
        self.legend_alpha.setRange(0.0, 1.0); self.legend_alpha.setSingleStep(0.1)
        self.legend_alpha.setValue(s.get("legend_alpha", 1.0))
        form.addRow("Legend background alpha (0=transparent):", self.legend_alpha)

        self.legend_ncols = QSpinBox()
        self.legend_ncols.setRange(1, 10); self.legend_ncols.setValue(s.get("legend_ncols", 1))
        form.addRow("Legend columns:", self.legend_ncols)

        self.legend_handlelength = QDoubleSpinBox()
        self.legend_handlelength.setRange(0.5, 10.0); self.legend_handlelength.setSingleStep(0.5)
        self.legend_handlelength.setValue(s.get("legend_handlelength", 2.0))
        form.addRow("Legend symbol size:", self.legend_handlelength)

        self._sep(form)

        # bold text options
        self.title_bold  = QCheckBox(); self.title_bold.setChecked(s.get("title_bold",  False))
        self.label_bold  = QCheckBox(); self.label_bold.setChecked(s.get("label_bold",  False))
        self.tick_bold   = QCheckBox(); self.tick_bold.setChecked(s.get("tick_bold",    False))
        self.legend_bold = QCheckBox(); self.legend_bold.setChecked(s.get("legend_bold", False))
        self.pct_bold    = QCheckBox(); self.pct_bold.setChecked(s.get("pct_bold",      False))
        form.addRow("Bold title:",        self.title_bold)
        form.addRow("Bold axis labels:",  self.label_bold)
        form.addRow("Bold tick labels:",  self.tick_bold)
        form.addRow("Bold legend:",       self.legend_bold)
        form.addRow("Bold percentages:",  self.pct_bold)

        layout.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _sep(self, form):
        sep = QFrame(); sep.setFrameShape(QFrame.HLine); sep.setFrameShadow(QFrame.Sunken)
        form.addRow(sep)

    def get_settings(self) -> dict:
        """
        Return the current dialog values as a style-settings dict.

        Returns
        -------
        dict
            Updated style settings compatible with
            :data:`constants.DEFAULT_STYLE_SETTINGS`.
        """
        return {
            "title_fs":   self.title_fs.value(),
            "label_fs":   self.label_fs.value(),
            "tick_fs":    self.tick_fs.value(),
            "legend_fs":  self.legend_fs.value(),
            "major_x":    self.major_x.value(),
            "major_y":    self.major_y.value(),
            "minor_x":    self.minor_x.value(),
            "minor_y":    self.minor_y.value(),
            "grid_major": self.grid_major.isChecked(),
            "grid_minor": self.grid_minor.isChecked(),
            "theme":           self.theme.currentText(),
            "dpi":             self.dpi.value(),
            "legend_show":     self.legend_show.isChecked(),
            "legend_loc":      self.legend_loc.currentText(),
            "legend_frameon":  self.legend_frameon.isChecked(),
            "legend_alpha":    self.legend_alpha.value(),
            "legend_ncols":    self.legend_ncols.value(),
            "legend_handlelength": self.legend_handlelength.value(),
            "title_bold":  self.title_bold.isChecked(),
            "label_bold":  self.label_bold.isChecked(),
            "tick_bold":   self.tick_bold.isChecked(),
            "legend_bold": self.legend_bold.isChecked(),
            "pct_bold":    self.pct_bold.isChecked(),
        }


# ---------------------------------------------------------------------------
# AppearanceDialog  (line, marker, colors)
# ---------------------------------------------------------------------------

class AppearanceDialog(QDialog):
    """
    Per-series visual appearance dialog: label, line, marker, and colors.

    Parameters
    ----------
    cfg : dict
        Current series style configuration.  Expected keys:
        ``"label"``, ``"linestyle"``, ``"linewidth"``, ``"marker"``,
        ``"markersize"``, ``"color"``, ``"face_color"``.
    parent : QWidget, optional
        Parent widget.
    """

    def __init__(self, cfg: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Appearance")
        self._color      = cfg.get("color",      "#1f77b4")
        self._face_color = cfg.get("face_color", "#1f77b4")
        self._cfg = dict(cfg)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        # label
        self.label_edit = QLineEdit(self._cfg.get("label", ""))
        form.addRow("Label:", self.label_edit)

        # line
        self.linestyle = QComboBox(); self.linestyle.addItems(LINESTYLE_LABELS)
        ls = self._cfg.get("linestyle", "-")
        if ls in LINESTYLES: self.linestyle.setCurrentIndex(LINESTYLES.index(ls))
        form.addRow("Line style:", self.linestyle)

        self.linewidth = QDoubleSpinBox()
        self.linewidth.setRange(0.1, 10); self.linewidth.setSingleStep(0.5)
        self.linewidth.setValue(self._cfg.get("linewidth", 1.8))
        form.addRow("Line width:", self.linewidth)

        # marker
        self.marker = QComboBox(); self.marker.addItems(MARKER_LABELS)
        mk = self._cfg.get("marker", "o")
        if mk in MARKERS: self.marker.setCurrentIndex(MARKERS.index(mk))
        form.addRow("Marker:", self.marker)

        self.markersize = QDoubleSpinBox()
        self.markersize.setRange(1, 30); self.markersize.setSingleStep(0.5)
        self.markersize.setValue(self._cfg.get("markersize", 5))
        form.addRow("Marker size:", self.markersize)

        # colors
        self.color_btn = QPushButton()
        self._refresh_btn(self.color_btn, self._color)
        self.color_btn.clicked.connect(lambda: self._pick("line"))
        form.addRow("Line / edge color:", self.color_btn)

        self.face_btn = QPushButton()
        self._refresh_btn(self.face_btn, self._face_color)
        self.face_btn.clicked.connect(lambda: self._pick("face"))
        form.addRow("Marker fill color:", self.face_btn)

        # error bar / band style
        self.error_style = QComboBox()
        self.error_style.addItems(["Bars", "Band (fill_between)", "Both"])
        self.error_style.setCurrentText(self._cfg.get("error_style", "Bars"))
        form.addRow("Error style:", self.error_style)

        self.band_alpha = QDoubleSpinBox()
        self.band_alpha.setRange(0.0, 1.0); self.band_alpha.setSingleStep(0.05)
        self.band_alpha.setValue(self._cfg.get("band_alpha", 0.25))
        form.addRow("Band alpha:", self.band_alpha)

        self.zorder = QSpinBox(); self.zorder.setRange(1, 10)
        self.zorder.setValue(self._cfg.get("zorder", 2))
        form.addRow("Z-order:", self.zorder)

        layout.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _refresh_btn(self, btn, color):
        btn.setStyleSheet(
            f"background-color: {color}; border: 1px solid #888; "
            f"border-radius: 4px; min-width: 80px; padding: 4px;"
        )
        btn.setText(color)

    def _pick(self, target):
        current = self._color if target == "line" else self._face_color
        new_color = pick_color(current, self)
        if new_color != current:
            if target == "line":
                self._color = new_color
                self._refresh_btn(self.color_btn, self._color)
            else:
                self._face_color = new_color
                self._refresh_btn(self.face_btn, self._face_color)

    def get_config(self) -> dict:
        """
        Return the appearance configuration chosen by the user.

        Returns
        -------
        dict
            Keys: ``"label"`` (str), ``"linestyle"`` (str),
            ``"linewidth"`` (float), ``"marker"`` (str),
            ``"markersize"`` (float), ``"color"`` (str),
            ``"face_color"`` (str), ``"error_style"`` (str),
            ``"band_alpha"`` (float), ``"zorder"`` (int).
        """
        return {
            "label":      self.label_edit.text(),
            "linestyle":  LINESTYLES[self.linestyle.currentIndex()],
            "linewidth":  self.linewidth.value(),
            "marker":     MARKERS[self.marker.currentIndex()],
            "markersize": self.markersize.value(),
            "color":      self._color,
            "face_color": self._face_color,
            "error_style": self.error_style.currentText(),
            "band_alpha":  self.band_alpha.value(),
            "zorder":      self.zorder.value(),
        }


# ---------------------------------------------------------------------------
# HistAppearanceDialog
# ---------------------------------------------------------------------------

class HistAppearanceDialog(QDialog):
    """
    Histogram visual appearance dialog: bins, normalisation, orientation, and colors.

    Parameters
    ----------
    cfg : dict
        Current histogram style configuration.  Expected keys:
        ``"hist_bins"`` (str), ``"hist_nbins"`` (int), ``"hist_norm"`` (str),
        ``"hist_horizontal"`` (bool), ``"hist_show_pct"`` (bool),
        ``"pct_fontsize"`` (float), ``"hist_color_by_value"`` (bool),
        ``"hist_colormap"`` (str), ``"color"`` (str), ``"face_color"`` (str).
    parent : QWidget, optional
        Parent widget.
    """

    def __init__(self, cfg: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Histogram appearance")
        self._color      = cfg.get("color",      "#1f77b4")
        self._face_color = cfg.get("face_color", "#1f77b4")
        self._cfg = dict(cfg)
        self._build()

    def _build(self):
        from .constants import HIST_BINS, HIST_NORM
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.hist_bins = QComboBox(); self.hist_bins.addItems(HIST_BINS)
        self.hist_bins.setCurrentText(self._cfg.get("hist_bins", "auto"))
        form.addRow("Bins:", self.hist_bins)

        self.hist_nbins = QSpinBox(); self.hist_nbins.setRange(1, 1000)
        self.hist_nbins.setValue(self._cfg.get("hist_nbins", 20))
        self.hist_nbins.setEnabled(self._cfg.get("hist_bins", "auto") == "manual")
        self.hist_bins.currentTextChanged.connect(
            lambda t: self.hist_nbins.setEnabled(t == "manual")
        )
        form.addRow("N bins (manual only):", self.hist_nbins)

        self.hist_norm = QComboBox(); self.hist_norm.addItems(HIST_NORM)
        self.hist_norm.setCurrentText(self._cfg.get("hist_norm", "count"))
        form.addRow("Normalisation:", self.hist_norm)

        self.hist_horizontal = QCheckBox()
        self.hist_horizontal.setChecked(self._cfg.get("hist_horizontal", False))
        form.addRow("Horizontal:", self.hist_horizontal)

        self.hist_show_pct = QCheckBox()
        self.hist_show_pct.setChecked(self._cfg.get("hist_show_pct", False))
        form.addRow("Show percentages:", self.hist_show_pct)

        self.pct_fontsize = QDoubleSpinBox()
        self.pct_fontsize.setRange(6.0, 24.0); self.pct_fontsize.setSingleStep(0.5)
        self.pct_fontsize.setValue(self._cfg.get("pct_fontsize", 9.0))
        form.addRow("Percentage font size:", self.pct_fontsize)

        self.hist_color_by_value = QCheckBox()
        self.hist_color_by_value.setChecked(self._cfg.get("hist_color_by_value", False))
        form.addRow("Color by value:", self.hist_color_by_value)

        _CMAPS = ["viridis", "plasma", "inferno", "magma", "cividis",
                  "coolwarm", "RdYlBu", "hot", "jet", "Spectral", "turbo", "rainbow"]
        self._cmap_label = QLabel("Colormap:")
        self.hist_colormap = QComboBox(); self.hist_colormap.addItems(_CMAPS)
        self.hist_colormap.setCurrentText(self._cfg.get("hist_colormap", "viridis"))
        form.addRow(self._cmap_label, self.hist_colormap)
        _cbv = self._cfg.get("hist_color_by_value", False)
        self._cmap_label.setVisible(_cbv); self.hist_colormap.setVisible(_cbv)
        self.hist_color_by_value.toggled.connect(self._cmap_label.setVisible)
        self.hist_color_by_value.toggled.connect(self.hist_colormap.setVisible)

        self.fill_btn = QPushButton()
        self._refresh_btn(self.fill_btn, self._color)
        self.fill_btn.clicked.connect(lambda: self._pick("fill"))
        form.addRow("Fill color:", self.fill_btn)

        self.edge_btn = QPushButton()
        self._refresh_btn(self.edge_btn, self._face_color)
        self.edge_btn.clicked.connect(lambda: self._pick("edge"))
        form.addRow("Edge color:", self.edge_btn)

        layout.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _refresh_btn(self, btn, color):
        btn.setStyleSheet(
            f"background-color: {color}; border: 1px solid #888; "
            f"border-radius: 4px; min-width: 80px; padding: 4px;"
        )
        btn.setText(color)

    def _pick(self, target):
        current = self._color if target == "fill" else self._face_color
        new_color = pick_color(current, self)
        if new_color != current:
            if target == "fill":
                self._color = new_color
                self._refresh_btn(self.fill_btn, self._color)
            else:
                self._face_color = new_color
                self._refresh_btn(self.edge_btn, self._face_color)

    def get_config(self) -> dict:
        """
        Return the histogram appearance configuration chosen by the user.

        Returns
        -------
        dict
            Keys: ``"hist_bins"`` (str), ``"hist_nbins"`` (int),
            ``"hist_norm"`` (str), ``"hist_horizontal"`` (bool),
            ``"hist_show_pct"`` (bool), ``"pct_fontsize"`` (float),
            ``"hist_color_by_value"`` (bool), ``"hist_colormap"`` (str),
            ``"color"`` (str), ``"face_color"`` (str).
        """
        return {
            "hist_bins":           self.hist_bins.currentText(),
            "hist_nbins":          self.hist_nbins.value(),
            "hist_norm":           self.hist_norm.currentText(),
            "hist_horizontal":     self.hist_horizontal.isChecked(),
            "hist_show_pct":       self.hist_show_pct.isChecked(),
            "pct_fontsize":        self.pct_fontsize.value(),
            "hist_color_by_value": self.hist_color_by_value.isChecked(),
            "hist_colormap":       self.hist_colormap.currentText(),
            "color":               self._color,
            "face_color":          self._face_color,
        }


# ---------------------------------------------------------------------------
# Hist2DAppearanceDialog
# ---------------------------------------------------------------------------

class Hist2DAppearanceDialog(QDialog):
    """
    2D-histogram visual appearance dialog.

    Parameters
    ----------
    cfg : dict
        Current 2D-histogram style configuration.  Expected keys:
        ``"bins_x"``, ``"bins_y"`` (int, 0 = auto), ``"colormap"``,
        ``"norm"``, ``"log_scale"``, ``"colorbar"``.
    parent : QWidget, optional
        Parent widget.
    """

    _COLORMAPS = ["viridis", "plasma", "inferno", "magma", "cividis",
                  "coolwarm", "RdYlBu", "hot", "jet"]

    def __init__(self, cfg: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("2D Histogram appearance")
        self._cfg = dict(cfg)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        def _bins_row(key, label):
            row_w = QWidget()
            row_l = QHBoxLayout(row_w)
            row_l.setContentsMargins(0, 0, 0, 0)
            spin = QSpinBox(); spin.setRange(2, 500)
            val = self._cfg.get(key, 0)
            is_auto = (val == 0)
            spin.setValue(val if val > 0 else 50)
            spin.setEnabled(not is_auto)
            auto_cb = QCheckBox("Auto")
            auto_cb.setChecked(is_auto)
            auto_cb.toggled.connect(lambda on, s=spin: s.setEnabled(not on))
            row_l.addWidget(spin); row_l.addWidget(auto_cb)
            form.addRow(label, row_w)
            return spin, auto_cb

        self.bins_x, self.bins_x_auto = _bins_row("bins_x", "Bins x:")
        self.bins_y, self.bins_y_auto = _bins_row("bins_y", "Bins y:")

        self.colormap = QComboBox(); self.colormap.addItems(self._COLORMAPS)
        self.colormap.setCurrentText(self._cfg.get("colormap", "viridis"))
        form.addRow("Colormap:", self.colormap)

        self.norm = QComboBox(); self.norm.addItems(["count", "density"])
        self.norm.setCurrentText(self._cfg.get("norm", "count"))
        form.addRow("Normalisation:", self.norm)

        self.log_scale = QCheckBox()
        self.log_scale.setChecked(self._cfg.get("log_scale", False))
        form.addRow("Log scale (color):", self.log_scale)

        self.colorbar = QCheckBox()
        self.colorbar.setChecked(self._cfg.get("colorbar", True))
        form.addRow("Show colorbar:", self.colorbar)

        layout.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_config(self) -> dict:
        """
        Return the 2D-histogram appearance configuration chosen by the user.

        Returns
        -------
        dict
            Keys: ``"bins_x"`` (int, 0 = auto), ``"bins_y"`` (int, 0 = auto),
            ``"colormap"`` (str), ``"norm"`` (str), ``"log_scale"`` (bool),
            ``"colorbar"`` (bool).
        """
        return {
            "bins_x":    0 if self.bins_x_auto.isChecked() else self.bins_x.value(),
            "bins_y":    0 if self.bins_y_auto.isChecked() else self.bins_y.value(),
            "colormap":  self.colormap.currentText(),
            "norm":      self.norm.currentText(),
            "log_scale": self.log_scale.isChecked(),
            "colorbar":  self.colorbar.isChecked(),
        }
