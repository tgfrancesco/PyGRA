"""
widgets.py — DatasetWidget: compact per-series panel
"""

import numpy as np

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QPushButton, QLabel,
    QSpinBox, QCheckBox, QScrollArea, QFrame,
    QMessageBox, QFileDialog, QHBoxLayout, QRadioButton, QButtonGroup,
)

from .constants import MARKERS, MARKER_LABELS, LINESTYLES, LINESTYLE_LABELS
from .dialogs import AppearanceDialog, HistAppearanceDialog, Hist2DAppearanceDialog


class DatasetWidget(QWidget):
    """
    Compact per-series control panel embedded in the left tab widget.

    Shows dataset name and dimensions, a histogram-mode toggle, column
    selectors for x, y, dx, dy (line mode) or a single column (histogram
    mode), an Appearance button, a duplicate-series button, and a
    visibility checkbox.  Style details are edited through
    :class:`~dialogs.AppearanceDialog` or
    :class:`~dialogs.HistAppearanceDialog`.

    Parameters
    ----------
    dataset : DataSet
        The dataset this widget controls.
    color : str
        Initial hex color string for the series (e.g. ``"#1f77b4"``).
    on_duplicate : callable, optional
        Called with *dataset* when the "Add another plot" button is
        clicked.
    on_replot : callable, optional
        Called with no arguments whenever a style change requires a
        full replot.
    parent : QWidget, optional
        Parent widget.
    """

    def __init__(self, dataset, color: str, on_duplicate=None,
                 on_replot=None, parent=None):
        super().__init__(parent)
        self.dataset      = dataset
        self.on_duplicate = on_duplicate
        self.on_replot    = on_replot   # callable: triggers a full replot

        # series style
        self._series_style = {
            "label":      dataset.name,
            "linestyle":  "-",
            "linewidth":  1.8,
            "marker":     "o",
            "markersize": 5.0,
            "color":      color,
            "face_color": color,
            "error_style": "Bars",
            "band_alpha":  0.25,
        }
        # histogram style
        self._hist_style = {
            "hist_bins":           "auto",
            "hist_nbins":          20,
            "hist_norm":           "count",
            "hist_horizontal":     False,
            "hist_show_pct":       False,
            "pct_fontsize":        9.0,
            "hist_color_by_value": False,
            "hist_colormap":       "viridis",
            "color":               color,
            "face_color":          color,
        }
        # 2D histogram style
        self._hist2d_style = {
            "bins_x":    0,          # 0 = auto
            "bins_y":    0,          # 0 = auto
            "colormap":  "viridis",
            "norm":      "count",
            "log_scale": False,
            "colorbar":  True,
        }

        self._build()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        inner  = QWidget()
        layout = QGridLayout(inner)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(5)

        nc = self.dataset.ncols
        nr = self.dataset.nrows

        layout.addWidget(QLabel(f"<b>{self.dataset.name}</b>"), 0, 0, 1, 4)
        layout.addWidget(QLabel(f"{nr} rows, {nc} cols"),       1, 0, 1, 4)

        # mode radio buttons
        self._mode_group = QButtonGroup(self)
        self._rb_series  = QRadioButton("Series")
        self._rb_hist    = QRadioButton("Histogram")
        self._rb_hist2d  = QRadioButton("Histogram 2D")
        self._rb_series.setChecked(True)
        self._mode_group.addButton(self._rb_series,  0)
        self._mode_group.addButton(self._rb_hist,    1)
        self._mode_group.addButton(self._rb_hist2d,  2)
        rb_widget = QWidget()
        rb_layout = QHBoxLayout(rb_widget)
        rb_layout.setContentsMargins(0, 0, 0, 0)
        rb_layout.addWidget(self._rb_series)
        rb_layout.addWidget(self._rb_hist)
        rb_layout.addWidget(self._rb_hist2d)
        layout.addWidget(rb_widget, 2, 0, 1, 4)
        self._mode_group.buttonClicked.connect(lambda _: self._toggle_mode())

        def col_spin(default):
            s = QSpinBox()
            s.setMinimum(-1)
            s.setMaximum(max(0, nc - 1))
            s.setValue(default if default < nc else -1)
            s.setSpecialValueText("—")
            s.setFixedWidth(55)
            return s

        # series columns (x, y, dx, dy)
        self._lbl_x  = QLabel("x:");  self.xcol  = col_spin(0)
        self._lbl_y  = QLabel("y:");  self.ycol  = col_spin(1)
        self._lbl_dx = QLabel("dx:"); self.dxcol = col_spin(-1)
        self._lbl_dy = QLabel("dy:"); self.dycol = col_spin(-1)
        layout.addWidget(self._lbl_x,  3, 0); layout.addWidget(self.xcol,  3, 1)
        layout.addWidget(self._lbl_y,  3, 2); layout.addWidget(self.ycol,  3, 3)
        layout.addWidget(self._lbl_dx, 4, 0); layout.addWidget(self.dxcol, 4, 1)
        layout.addWidget(self._lbl_dy, 4, 2); layout.addWidget(self.dycol, 4, 3)

        # asymmetric error columns (dy low, dy high)
        self._lbl_dy_low  = QLabel("dy low:");  self.dy_low_col  = col_spin(-1)
        self._lbl_dy_high = QLabel("dy high:"); self.dy_high_col = col_spin(-1)
        layout.addWidget(self._lbl_dy_low,  5, 0); layout.addWidget(self.dy_low_col,  5, 1)
        layout.addWidget(self._lbl_dy_high, 5, 2); layout.addWidget(self.dy_high_col, 5, 3)

        # histogram column
        self._lbl_hcol = QLabel("column:")
        self.hcol = col_spin(0)
        layout.addWidget(self._lbl_hcol, 3, 0); layout.addWidget(self.hcol, 3, 1)

        # hist2d columns
        self._lbl_xcol2 = QLabel("x:"); self.xcol2 = col_spin(0)
        self._lbl_ycol2 = QLabel("y:"); self.ycol2 = col_spin(1)
        layout.addWidget(self._lbl_xcol2, 3, 0); layout.addWidget(self.xcol2, 3, 1)
        layout.addWidget(self._lbl_ycol2, 3, 2); layout.addWidget(self.ycol2, 3, 3)

        # appearance button
        self.appear_btn = QPushButton("Appearance...")
        self.appear_btn.clicked.connect(self._open_appearance)
        layout.addWidget(self.appear_btn, 6, 0, 1, 4)

        # duplicate
        dup_btn = QPushButton("Add another plot from this file")
        dup_btn.clicked.connect(self._duplicate)
        layout.addWidget(dup_btn, 7, 0, 1, 4)

        # visibility
        self.visible = QCheckBox("visible"); self.visible.setChecked(True)
        layout.addWidget(self.visible, 8, 0, 1, 4)

        scroll.setWidget(inner)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        self._toggle_mode()

    # ------------------------------------------------------------------
    # Mode switching
    # ------------------------------------------------------------------

    def _toggle_mode(self):
        series = self._rb_series.isChecked()
        hist   = self._rb_hist.isChecked()
        hist2d = self._rb_hist2d.isChecked()
        for w in [self._lbl_x,  self.xcol,  self._lbl_y,  self.ycol,
                  self._lbl_dx, self.dxcol, self._lbl_dy, self.dycol,
                  self._lbl_dy_low, self.dy_low_col,
                  self._lbl_dy_high, self.dy_high_col]:
            w.setVisible(series)
        for w in [self._lbl_hcol, self.hcol]:
            w.setVisible(hist)
        for w in [self._lbl_xcol2, self.xcol2, self._lbl_ycol2, self.ycol2]:
            w.setVisible(hist2d)

    def set_mode(self, mode: str):
        """
        Set display mode programmatically.

        Parameters
        ----------
        mode : str
            One of ``"series"``, ``"histogram"``, or ``"hist2d"``.
        """
        if mode == "histogram":
            self._rb_hist.setChecked(True)
        elif mode == "hist2d":
            self._rb_hist2d.setChecked(True)
        else:
            self._rb_series.setChecked(True)
        self._toggle_mode()

    # ------------------------------------------------------------------
    # Appearance
    # ------------------------------------------------------------------

    def _open_appearance(self):
        if self._rb_hist.isChecked():
            cfg = dict(self._hist_style)
            dlg = HistAppearanceDialog(cfg, self)
            if dlg.exec_():
                self._hist_style.update(dlg.get_config())
                if self.on_replot:
                    self.on_replot()
        elif self._rb_hist2d.isChecked():
            cfg = dict(self._hist2d_style)
            dlg = Hist2DAppearanceDialog(cfg, self)
            if dlg.exec_():
                self._hist2d_style.update(dlg.get_config())
                if self.on_replot:
                    self.on_replot()
        else:
            cfg = dict(self._series_style)
            dlg = AppearanceDialog(cfg, self)
            if dlg.exec_():
                self._series_style.update(dlg.get_config())
                if self.on_replot:
                    self.on_replot()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _duplicate(self):
        if self.on_duplicate:
            self.on_duplicate(self.dataset)

    def refresh_col_ranges(self):
        """
        Update the maximum value of all column spinboxes.

        Should be called after the underlying dataset gains or loses
        columns (e.g. after a transform operation adds a new column).
        """
        nc = max(0, self.dataset.ncols - 1)
        for w in [self.xcol, self.ycol, self.dxcol, self.dycol,
                  self.dy_low_col, self.dy_high_col,
                  self.hcol, self.xcol2, self.ycol2]:
            w.setMaximum(nc)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_config(self) -> dict:
        """
        Return the current widget configuration as a plotting dict.

        In series mode the result includes series-style keys; in histogram
        mode it includes histogram-style keys; in hist2d mode it includes
        hist2d-style keys.

        Returns
        -------
        dict
            Keys always present: ``"label"`` (str), ``"visible"`` (bool),
            ``"hist_mode"`` (bool), ``"hist2d_mode"`` (bool), ``"xcol"``,
            ``"ycol"``, ``"dxcol"``, ``"dycol"``, ``"dy_low_col"``,
            ``"dy_high_col"``, ``"hcol"`` (int).
            In hist2d mode ``"xcol"`` and ``"ycol"`` reflect the hist2d
            column spinboxes.  Additional style keys are merged from the
            active style dict.
        """
        hist   = self._rb_hist.isChecked()
        hist2d = self._rb_hist2d.isChecked()
        cfg = {
            "label":      self._series_style.get("label", self.dataset.name),
            "visible":    self.visible.isChecked(),
            "hist_mode":  hist,
            "hist2d_mode": hist2d,
            "xcol":  self.xcol2.value() if hist2d else self.xcol.value(),
            "ycol":  self.ycol2.value() if hist2d else self.ycol.value(),
            "dxcol": self.dxcol.value(),
            "dycol": self.dycol.value(),
            "dy_low_col":  self.dy_low_col.value(),
            "dy_high_col": self.dy_high_col.value(),
            "hcol":  self.hcol.value(),
        }
        if hist:
            cfg.update(self._hist_style)
        elif hist2d:
            cfg.update(self._hist2d_style)
        else:
            cfg.update(self._series_style)
        return cfg
