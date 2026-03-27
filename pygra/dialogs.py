"""
dialogs.py — all application dialogs
"""

import numpy as np

from PyQt5.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QVBoxLayout, QHBoxLayout,
    QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox, QFrame,
    QLabel, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QGroupBox, QColorDialog, QMessageBox,
)
from PyQt5.QtGui import QColor

from .constants import (
    DEFAULT_STYLE_SETTINGS, TRANSFORM_OPS, PLOT_THEMES,
    LINESTYLES, LINESTYLE_LABELS, MARKERS, MARKER_LABELS,
)


def pick_color(current: str, parent=None) -> str:
    """
    Open a QColorDialog pre-loaded with saved custom colors.
    Returns new hex color string, or current if cancelled.
    Saves chosen custom colors back to preferences.
    """
    from PyQt5.QtGui import QColor
    try:
        from .preferences import load_prefs, save_prefs
        prefs = load_prefs()
        custom = prefs.get("custom_colors", [])
    except Exception:
        custom = []

    # populate QColorDialog custom color slots (max 16)
    for i, hex_c in enumerate(custom[:16]):
        try:
            QColorDialog.setCustomColor(i, QColor(hex_c))
        except Exception:
            pass

    c = QColorDialog.getColor(QColor(current), parent,
                              options=QColorDialog.DontUseNativeDialog)
    if not c.isValid():
        return current

    # collect custom colors back from dialog
    new_custom = []
    for i in range(16):
        try:
            cc = QColorDialog.customColor(i)
            if cc.isValid() and cc.name() != "#000000":
                new_custom.append(cc.name())
        except Exception:
            pass

    try:
        prefs["custom_colors"] = list(dict.fromkeys(new_custom))[:16]
        save_prefs(prefs)
    except Exception:
        pass

    return c.name()

# All fit/interpolation methods in one list
FIT_METHODS = [
    "spline",
    "linear fit",
    "polynomial fit",
    "Gaussian",
    "Exponential",
    "Maxwell-Boltzmann",
    "Poisson",
    "Custom...",
]

# Formula strings for display (read-only for predefined)
FIT_FORMULAS = {
    "spline":            "cubic spline interpolation",
    "linear fit":        "y = a·x + b",
    "polynomial fit":    "y = a₀ + a₁·x + ... + aₙ·xⁿ",
    "Gaussian":          "f(x) = 1/(σ√2π) · exp(-(x-μ)²/2σ²)",
    "Exponential":       "f(x) = λ · exp(-λ·x)",
    "Maxwell-Boltzmann": "f(x) = √(2/π) · x²/a³ · exp(-x²/2a²)",
    "Poisson":           "P(k) = μᵏ · e⁻ᵘ / k!",
    "Custom...":         "",
}


# ---------------------------------------------------------------------------
# StyleDialog  (global style: fonts, ticks, grid, theme, DPI)
# ---------------------------------------------------------------------------

class StyleDialog(QDialog):
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

        self.fig_size_auto = QCheckBox("Use current window size")
        self.fig_size_auto.setChecked(s.get("fig_size_auto", True))
        self.fig_size_auto.toggled.connect(self._toggle_fig_size)
        form.addRow("Figure size (for save):", self.fig_size_auto)

        self.fig_w = QDoubleSpinBox(); self.fig_w.setRange(1, 100); self.fig_w.setSingleStep(0.5)
        self.fig_w.setValue(s.get("fig_w", 8.0)); self.fig_w.setSuffix(" in")
        form.addRow("Width:", self.fig_w)

        self.fig_h = QDoubleSpinBox(); self.fig_h.setRange(1, 100); self.fig_h.setSingleStep(0.5)
        self.fig_h.setValue(s.get("fig_h", 5.0)); self.fig_h.setSuffix(" in")
        form.addRow("Height:", self.fig_h)

        # set initial enabled state
        auto = s.get("fig_size_auto", True)
        self.fig_w.setEnabled(not auto)
        self.fig_h.setEnabled(not auto)

        self._sep(form)

        # legend options
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

        layout.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _sep(self, form):
        sep = QFrame(); sep.setFrameShape(QFrame.HLine); sep.setFrameShadow(QFrame.Sunken)
        form.addRow(sep)

    def _toggle_fig_size(self, auto: bool):
        self.fig_w.setEnabled(not auto)
        self.fig_h.setEnabled(not auto)

    def get_settings(self) -> dict:
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
            "fig_size_auto":   self.fig_size_auto.isChecked(),
            "fig_w":           self.fig_w.value(),
            "fig_h":           self.fig_h.value(),
            "legend_loc":      self.legend_loc.currentText(),
            "legend_frameon":  self.legend_frameon.isChecked(),
            "legend_alpha":    self.legend_alpha.value(),
            "legend_ncols":    self.legend_ncols.value(),
            "legend_handlelength": self.legend_handlelength.value(),
        }


# ---------------------------------------------------------------------------
# TransformDialog
# ---------------------------------------------------------------------------

class TransformDialog(QDialog):
    def __init__(self, ncols: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Transform data")
        self.ncols = ncols
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.col_spin = QSpinBox(); self.col_spin.setRange(0, self.ncols - 1)
        form.addRow("Target column:", self.col_spin)

        self.op = QComboBox(); self.op.addItems(TRANSFORM_OPS)
        form.addRow("Operation:", self.op)

        self.val = QDoubleSpinBox(); self.val.setRange(-1e12, 1e12); self.val.setValue(1.0); self.val.setDecimals(6)
        form.addRow("Value / window size:", self.val)

        self.xcol_spin = QSpinBox(); self.xcol_spin.setRange(0, self.ncols - 1)
        form.addRow("x column (for derivative):", self.xcol_spin)

        self.new_col = QCheckBox("Add as new column (don't overwrite)")
        self.new_col.setChecked(True)
        form.addRow(self.new_col)

        layout.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_config(self) -> dict:
        return {
            "col":     self.col_spin.value(),
            "op":      self.op.currentText(),
            "val":     self.val.value(),
            "xcol":    self.xcol_spin.value(),
            "new_col": self.new_col.isChecked(),
        }


# ---------------------------------------------------------------------------
# AppearanceDialog  (line, marker, colors)
# ---------------------------------------------------------------------------

class AppearanceDialog(QDialog):
    """Per-series visual appearance: label, line, marker, colors."""

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
        return {
            "label":      self.label_edit.text(),
            "linestyle":  LINESTYLES[self.linestyle.currentIndex()],
            "linewidth":  self.linewidth.value(),
            "marker":     MARKERS[self.marker.currentIndex()],
            "markersize": self.markersize.value(),
            "color":      self._color,
            "face_color": self._face_color,
        }


# ---------------------------------------------------------------------------
# HistAppearanceDialog
# ---------------------------------------------------------------------------

class HistAppearanceDialog(QDialog):
    """Histogram visual appearance: bins, normalisation, colors."""

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
        return {
            "hist_bins":  self.hist_bins.currentText(),
            "hist_nbins": self.hist_nbins.value(),
            "hist_norm":  self.hist_norm.currentText(),
            "color":      self._color,
            "face_color": self._face_color,
        }


# ---------------------------------------------------------------------------
# FitDialog  (fit + interpolation unified)
# ---------------------------------------------------------------------------

class FitDialog(QDialog):
    """
    Unified fit & interpolation dialog.
    Predefined methods show their formula (read-only).
    Custom fields enabled only when 'Custom...' is selected.
    """

    def __init__(self, cfg: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fit & Interpolation")
        self._cfg = dict(cfg)
        self._color = cfg.get("fit_color", "#d62728")
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.method = QComboBox()
        self.method.addItems(FIT_METHODS)
        self.method.setCurrentText(self._cfg.get("fit_method", "Gaussian"))
        self.method.currentTextChanged.connect(self._on_method_changed)
        form.addRow("Method:", self.method)

        # polynomial degree (only for polynomial fit)
        self.poly_deg = QSpinBox(); self.poly_deg.setRange(1, 10); self.poly_deg.setValue(self._cfg.get("poly_deg", 3))
        form.addRow("Polynomial degree:", self.poly_deg)

        # formula display
        self.formula_lbl = QLabel()
        self.formula_lbl.setWordWrap(True)
        self.formula_lbl.setStyleSheet("font-style: italic; color: #555;")
        form.addRow("Formula:", self.formula_lbl)

        # custom fields
        self.custom_formula = QLineEdit(self._cfg.get("custom_formula", "a * exp(-b * x)"))
        form.addRow("Custom formula:", self.custom_formula)

        custom_params_default = self._cfg.get("custom_params", ["a", "b"])
        if isinstance(custom_params_default, list):
            custom_params_default = " ".join(custom_params_default)
        self.custom_params = QLineEdit(custom_params_default)
        form.addRow("Custom params (space-sep):", self.custom_params)

        # fit line color
        self.color_btn = QPushButton()
        self._refresh_btn(self.color_btn, self._color)
        self.color_btn.clicked.connect(self._pick_color)
        form.addRow("Fit line color:", self.color_btn)

        layout.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        self._on_method_changed(self.method.currentText())

    def _on_method_changed(self, method: str):
        is_custom = method == "Custom..."
        is_poly   = method == "polynomial fit"
        self.formula_lbl.setText(FIT_FORMULAS.get(method, ""))
        self.formula_lbl.setVisible(not is_custom)
        self.custom_formula.setEnabled(is_custom)
        self.custom_params.setEnabled(is_custom)
        self.poly_deg.setEnabled(is_poly)

    def _refresh_btn(self, btn, color):
        btn.setStyleSheet(
            f"background-color: {color}; border: 1px solid #888; "
            f"border-radius: 4px; min-width: 80px; padding: 4px;"
        )
        btn.setText(color)

    def _pick_color(self):
        new_color = pick_color(self._color, self)
        if new_color != self._color:
            self._color = new_color
            self._refresh_btn(self.color_btn, self._color)

    def get_config(self) -> dict:
        return {
            "fit_method":     self.method.currentText(),
            "poly_deg":       self.poly_deg.value(),
            "custom_formula": self.custom_formula.text().strip(),
            "custom_params":  self.custom_params.text().strip().split(),
            "fit_color":      self._color,
        }


# ---------------------------------------------------------------------------
# StatsDialog
# ---------------------------------------------------------------------------

class StatsDialog(QDialog):
    def __init__(self, dataset, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Statistics — {dataset.name}")
        self.dataset = dataset
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            f"<b>{self.dataset.name}</b>  —  "
            f"{self.dataset.nrows} rows, {self.dataset.ncols} cols"
        ))
        table = QTableWidget(self.dataset.ncols, 7)
        table.setHorizontalHeaderLabels(["col", "mean", "median", "std", "min", "max", "N"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for i in range(self.dataset.ncols):
            col = self.dataset.col(i)
            for j, v in enumerate([
                str(i),
                f"{np.mean(col):.6g}", f"{np.median(col):.6g}",
                f"{np.std(col):.6g}",  f"{np.min(col):.6g}",
                f"{np.max(col):.6g}",  str(len(col)),
            ]):
                item = QTableWidgetItem(v)
                item.setFlags(item.flags() & ~0x2)
                table.setItem(i, j, item)
        layout.addWidget(table)
        btns = QDialogButtonBox(QDialogButtonBox.Close)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)
        self.resize(640, 120 + self.dataset.ncols * 30)


# ---------------------------------------------------------------------------
# DataEditorDialog
# ---------------------------------------------------------------------------

class DataEditorDialog(QDialog):
    """
    Editable table view of a dataset.
    Changes are applied to a copy — the original file is never modified.
    Rows can be deleted; new rows can be added.
    """

    def __init__(self, dataset, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Edit data — {dataset.name}")
        self.dataset = dataset
        self._build()
        self.resize(700, 500)

    def _build(self):
        from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QHBoxLayout
        from PyQt5.QtCore import Qt

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            f"<b>{self.dataset.name}</b>  —  editing a copy. Original file is not modified."
        ))

        nr, nc = self.dataset.nrows, self.dataset.ncols
        self.table = QTableWidget(nr, nc)
        self.table.setHorizontalHeaderLabels([f"col {i}" for i in range(nc)])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        for i in range(nr):
            for j in range(nc):
                val = self.dataset.arr[i, j]
                item = QTableWidgetItem(f"{val:.10g}")
                self.table.setItem(i, j, item)

        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add row")
        add_btn.clicked.connect(self._add_row)
        del_btn = QPushButton("Delete selected rows")
        del_btn.clicked.connect(self._del_rows)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._apply)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _add_row(self):
        from PyQt5.QtWidgets import QTableWidgetItem
        row = self.table.rowCount()
        self.table.insertRow(row)
        for j in range(self.table.columnCount()):
            self.table.setItem(row, j, QTableWidgetItem("0"))

    def _del_rows(self):
        rows = sorted(
            set(idx.row() for idx in self.table.selectedIndexes()),
            reverse=True,
        )
        for r in rows:
            self.table.removeRow(r)

    def _apply(self):
        nr = self.table.rowCount()
        nc = self.table.columnCount()
        data = []
        for i in range(nr):
            row = []
            for j in range(nc):
                item = self.table.item(i, j)
                try:
                    row.append(float(item.text()) if item else 0.0)
                except ValueError:
                    QMessageBox.warning(self, "Invalid value",
                                        f"Non-numeric value at row {i+1}, col {j}.")
                    return
            data.append(row)
        import numpy as np
        self.dataset.arr = np.array(data)
        self.dataset.raw = data
        self.accept()
