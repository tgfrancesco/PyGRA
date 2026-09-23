"""Tests for session save/load round-trips (pygra.state + MainWindow._apply_state)."""

import os

import numpy as np
import pytest

from pygra.dataset import DataSet
from pygra.state import save_state, load_state


def make_dataset(arr: np.ndarray, name: str = "d") -> DataSet:
    ds = DataSet.__new__(DataSet)
    ds.path = f"<{name}>"
    ds.name = name
    ds.raw = arr.tolist()
    ds.arr = arr.copy().astype(float)
    ds.skipped_rows = []
    return ds


class FakeDatasetWidget:
    def __init__(self, dataset, cfg, series_style, hist_style, hist2d_style):
        self.dataset = dataset
        self._cfg = cfg
        self._series_style = series_style
        self._hist_style = hist_style
        self._hist2d_style = hist2d_style

    def get_config(self):
        return dict(self._cfg)


def test_save_state_stores_every_style_dict(tmp_path):
    ds = make_dataset(np.arange(12.0).reshape(3, 4))
    dw = FakeDatasetWidget(
        ds,
        cfg={"hist_mode": True, "dy_low_col": 2, "dy_high_col": 3},
        series_style={"error_style": "Both", "band_alpha": 0.4, "zorder": 7,
                      "color": "#ff0000"},
        hist_style={"hist_nbins": 42, "color": "#00ff00"},
        hist2d_style={"colormap": "magma"},
    )
    path = tmp_path / "s.json"
    annotations = [{"text": "hi", "x": 0.1, "y": 0.2}]
    save_state(str(path), [dw], {}, {}, annotations)

    state = load_state(str(path))
    s = state["series"][0]
    assert s["config"]["dy_low_col"] == 2
    assert s["config"]["dy_high_col"] == 3
    assert s["series_style"]["zorder"] == 7
    assert s["series_style"]["error_style"] == "Both"
    assert s["series_style"]["band_alpha"] == 0.4
    assert s["series_style"]["color"] == "#ff0000"
    assert s["hist_style"]["color"] == "#00ff00"
    assert s["hist2d_style"]["colormap"] == "magma"
    assert state["annotations"] == annotations
    np.testing.assert_array_equal(s["data"], ds.arr)


@pytest.fixture(scope="module")
def qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    QtWidgets = pytest.importorskip("PyQt5.QtWidgets")
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    yield app


def _roundtrip(win, tmp_path):
    path = tmp_path / "session.json"
    save_state(str(path), win.dataset_widgets, win._get_axis_settings(),
               win.style_settings, win._annotations)
    win._load_state_from_path(str(path))
    return win.dataset_widgets


def test_mainwindow_roundtrip_restores_series_fields(qapp, tmp_path):
    from pygra.mainwindow import MainWindow

    win = MainWindow()
    ds = make_dataset(np.arange(30.0).reshape(5, 6))
    win.datasets.append(ds)
    dw = win._add_dataset_widget(ds)
    dw.set_mode("series")
    dw.dy_low_col.setValue(2)
    dw.dy_high_col.setValue(3)
    dw._series_style.update(error_style="Both", band_alpha=0.4, zorder=7)
    win._annotations = [{"text": "hi", "x": 0.1, "y": 0.2, "fontsize": 12,
                         "color": "#000000", "bold": False}]

    (restored,) = _roundtrip(win, tmp_path)
    assert restored.dy_low_col.value() == 2
    assert restored.dy_high_col.value() == 3
    assert restored._series_style["error_style"] == "Both"
    assert restored._series_style["band_alpha"] == 0.4
    assert restored._series_style["zorder"] == 7
    assert win._annotations[0]["text"] == "hi"


def test_mainwindow_roundtrip_keeps_inactive_mode_styles(qapp, tmp_path):
    from pygra.mainwindow import MainWindow

    win = MainWindow()
    ds = make_dataset(np.arange(30.0).reshape(5, 6))
    win.datasets.append(ds)
    dw = win._add_dataset_widget(ds)
    dw._series_style.update(zorder=9, color="#ff0000")
    dw._hist_style.update(hist_nbins=42, color="#00ff00")
    dw._hist2d_style.update(colormap="magma", bins_x=17)
    dw.xcol2.setValue(3)
    dw.ycol2.setValue(4)
    dw.hcol.setValue(5)
    dw.set_mode("hist2d")

    (restored,) = _roundtrip(win, tmp_path)
    assert restored._rb_hist2d.isChecked()
    assert restored.xcol2.value() == 3
    assert restored.ycol2.value() == 4
    assert restored.hcol.value() == 5
    assert restored._hist2d_style["colormap"] == "magma"
    assert restored._hist2d_style["bins_x"] == 17
    assert restored._series_style["zorder"] == 9
    assert restored._series_style["color"] == "#ff0000"
    assert restored._hist_style["hist_nbins"] == 42
    assert restored._hist_style["color"] == "#00ff00"
