"""
dialogs_analysis.py — data analysis dialogs: fit, transform, stats, editor
"""

import numpy as np

from PyQt5.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QVBoxLayout, QHBoxLayout,
    QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox,
    QLabel, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QMessageBox,
)
from PyQt5.QtCore import Qt

from .constants import TRANSFORM_OPS
from .dialogs_style import pick_color


# Ordered list of all fit/interpolation methods shown in FitDialog.
# Distribution methods ("Gaussian", "Exponential", etc.) delegate to
# fitting.FIT_FUNCTIONS; the others are implemented directly in MainWindow.
FIT_METHODS = [
    "spline",
    "linear fit",
    "polynomial fit",
    "Gaussian curve",
    "Exponential curve",
    "Gaussian (distribution)",
    "Exponential (distribution)",
    "Maxwell-Boltzmann (distribution)",
    "Poisson (distribution)",
    "Custom...",
]

# Human-readable formula string for each predefined method, displayed
# read-only in FitDialog.  Empty string for "Custom..." (user-supplied).
FIT_FORMULAS = {
    "spline":                        "cubic spline interpolation",
    "linear fit":                    "y = a·x + b",
    "polynomial fit":                "y = a₀ + a₁·x + ... + aₙ·xⁿ",
    "Gaussian curve":                "f(x) = A · exp(-(x-μ)²/2σ²)",
    "Exponential curve":             "f(x) = A · exp(-x/τ) + C",
    "Gaussian (distribution)":       "f(x) = 1/(σ√2π) · exp(-(x-μ)²/2σ²)",
    "Exponential (distribution)":    "f(x) = λ · exp(-λ·x)",
    "Maxwell-Boltzmann (distribution)": "f(x) = √(2/π) · x²/a³ · exp(-x²/2a²)",
    "Poisson (distribution)":        "P(k) = μᵏ · e⁻ᵘ / k!",
    "Custom...":                     "",
}


# ---------------------------------------------------------------------------
# FitDialog  (fit + interpolation unified)
# ---------------------------------------------------------------------------

class FitDialog(QDialog):
    """
    Unified fit and interpolation dialog.

    Predefined methods display their formula read-only.  The custom
    formula and parameter-name fields are enabled only when
    ``"Custom..."`` is selected.  The polynomial degree spinner is
    enabled only for ``"polynomial fit"``.

    Parameters
    ----------
    cfg : dict
        Previous fit configuration used to restore dialog state.
        Expected keys: ``"fit_method"``, ``"poly_deg"``,
        ``"custom_formula"``, ``"custom_params"``, ``"fit_color"``.
    parent : QWidget, optional
        Parent widget.
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
        self.method.setCurrentText(self._cfg.get("fit_method", "Gaussian (distribution)"))
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

        self.custom_p0 = QLineEdit(self._cfg.get("custom_p0", ""))
        self.custom_p0.setPlaceholderText("leave empty for auto")
        form.addRow("Initial parameters (comma-sep):", self.custom_p0)

        # fit line color
        self.color_btn = QPushButton()
        self._refresh_btn(self.color_btn, self._color)
        self.color_btn.clicked.connect(self._pick_color)
        form.addRow("Fit line color:", self.color_btn)

        # --- fit range ---
        form.addRow(QLabel(""))  # spacer
        form.addRow(QLabel("<b>Fit range</b>"))

        self.use_zoom = QCheckBox("Use zoom range")
        self.use_zoom.setChecked(self._cfg.get("fit_use_zoom", False))
        self.use_zoom.stateChanged.connect(self._on_zoom_toggled)
        form.addRow(self.use_zoom)

        self.xmin_spin = QDoubleSpinBox()
        self.xmin_spin.setRange(-1e15, 1e15)
        self.xmin_spin.setValue(self._cfg.get("fit_xmin", -1e10))
        self.xmin_spin.setDecimals(6)
        self.xmin_spin.setSpecialValueText("auto")
        form.addRow("x min:", self.xmin_spin)

        self.xmax_spin = QDoubleSpinBox()
        self.xmax_spin.setRange(-1e15, 1e15)
        self.xmax_spin.setValue(self._cfg.get("fit_xmax", 1e10))
        self.xmax_spin.setDecimals(6)
        self.xmax_spin.setSpecialValueText("auto")
        form.addRow("x max:", self.xmax_spin)

        layout.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        self._on_method_changed(self.method.currentText())
        self._on_zoom_toggled(self.use_zoom.checkState())

    def _on_zoom_toggled(self, state):
        enabled = not bool(state)
        self.xmin_spin.setEnabled(enabled)
        self.xmax_spin.setEnabled(enabled)

    def _on_method_changed(self, method: str):
        is_custom = method == "Custom..."
        is_poly   = method == "polynomial fit"
        self.formula_lbl.setText(FIT_FORMULAS.get(method, ""))
        self.formula_lbl.setVisible(not is_custom)
        self.custom_formula.setEnabled(is_custom)
        self.custom_params.setEnabled(is_custom)
        self.custom_p0.setEnabled(is_custom)
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
        """
        Return the fit configuration chosen by the user.

        Returns
        -------
        dict
            Keys: ``"fit_method"`` (str), ``"poly_deg"`` (int),
            ``"custom_formula"`` (str), ``"custom_params"`` (list of str),
            ``"fit_color"`` (str).
        """
        xmin_val = self.xmin_spin.value()
        xmax_val = self.xmax_spin.value()
        return {
            "fit_method":     self.method.currentText(),
            "poly_deg":       self.poly_deg.value(),
            "custom_formula": self.custom_formula.text().strip(),
            "custom_params":  self.custom_params.text().strip().split(),
            "custom_p0":      self.custom_p0.text().strip(),
            "fit_color":      self._color,
            "fit_xmin":       xmin_val,
            "fit_xmax":       xmax_val,
            "fit_use_zoom":   self.use_zoom.isChecked(),
        }


# ---------------------------------------------------------------------------
# TransformDialog
# ---------------------------------------------------------------------------

class TransformDialog(QDialog):
    """
    Data-transform configuration dialog.

    Allows the user to select a column, choose a transform operation
    from :data:`constants.TRANSFORM_OPS`, supply a scalar value or
    window size, specify an x-column for derivative operations, and
    decide whether to append a new column or overwrite the target.

    Parameters
    ----------
    ncols : int
        Number of columns currently in the active dataset; used to set
        the range of the column spinboxes.
    parent : QWidget, optional
        Parent widget.
    """

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
        """
        Return the transform configuration chosen by the user.

        Returns
        -------
        dict
            Keys: ``"col"`` (int), ``"op"`` (str), ``"val"`` (float),
            ``"xcol"`` (int), ``"new_col"`` (bool).
        """
        return {
            "col":     self.col_spin.value(),
            "op":      self.op.currentText(),
            "val":     self.val.value(),
            "xcol":    self.xcol_spin.value(),
            "new_col": self.new_col.isChecked(),
        }


# ---------------------------------------------------------------------------
# StatsDialog
# ---------------------------------------------------------------------------

class StatsDialog(QDialog):
    """
    Read-only statistics table for all columns of a dataset.

    Displays mean, median, standard deviation, min, max, and row count
    for each column.

    Parameters
    ----------
    dataset : DataSet
        The dataset whose column statistics are displayed.
    parent : QWidget, optional
        Parent widget.
    """

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

    Changes are applied directly to ``dataset.arr`` and ``dataset.raw``
    on acceptance; the original file on disk is never modified.  Rows
    can be deleted and new zero-filled rows can be appended.

    Parameters
    ----------
    dataset : DataSet
        The dataset to edit.  Modified in-place when the dialog is accepted.
    parent : QWidget, optional
        Parent widget.
    """

    def __init__(self, dataset, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Edit data — {dataset.name}")
        self.dataset = dataset
        self._build()
        self.resize(700, 500)

    def _build(self):
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
        self.dataset.arr = np.array(data)
        self.dataset.raw = data
        self.accept()
