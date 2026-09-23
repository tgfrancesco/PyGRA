"""Tests for pygra.plot_engine: asymmetric error bars and confidence bands."""

import matplotlib
matplotlib.use("Agg")

import numpy as np
import pytest
from matplotlib.figure import Figure

from pygra.dataset import DataSet
from pygra.constants import DEFAULT_STYLE_SETTINGS
from pygra.plot_engine import render_plot


def make_dataset(arr: np.ndarray) -> DataSet:
    ds = DataSet.__new__(DataSet)
    ds.path = "<test>"
    ds.name = "<test>"
    ds.raw = arr.tolist()
    ds.arr = arr.copy().astype(float)
    ds.skipped_rows = []
    return ds


class FakeDatasetWidget:
    """Minimal stand-in for DatasetWidget: exposes .dataset and .get_config()."""

    def __init__(self, dataset, cfg):
        self.dataset = dataset
        self._cfg = cfg

    def get_config(self):
        return dict(self._cfg)


def base_cfg(**overrides):
    cfg = {
        "label": "series",
        "visible": True,
        "hist_mode": False,
        "hist2d_mode": False,
        "xcol": 0,
        "ycol": 1,
        "dxcol": -1,
        "dycol": -1,
        "dy_low_col": 0,
        "dy_high_col": 0,
        "hcol": 0,
        "linestyle": "-",
        "linewidth": 1.8,
        "marker": "o",
        "markersize": 5.0,
        "color": "#1f77b4",
        "face_color": "#1f77b4",
        "error_style": "Bars",
        "band_alpha": 0.25,
    }
    cfg.update(overrides)
    return cfg


@pytest.fixture
def ds():
    # cols: 0=x, 1=y, 2=dy_low, 3=dy_high, 4=dy (symmetric)
    arr = np.array([
        [1.0, 10.0, 0.5, 1.5, 1.0],
        [2.0, 20.0, 0.4, 1.2, 0.8],
        [3.0, 30.0, 0.6, 1.0, 0.9],
    ])
    return make_dataset(arr)


def render(dw):
    fig = Figure()
    ax = fig.add_subplot(111)
    render_plot(
        fig, ax, [dw], fit_layers=[], annotations=[],
        style_settings=dict(DEFAULT_STYLE_SETTINGS),
        axis_settings={}, legend_pos=None, pct_label_positions=[],
    )
    return fig, ax


class TestAsymmetricErrorColumnRetrieval:

    def test_has_asym_true_uses_two_columns(self, ds):
        cfg = base_cfg(dy_low_col=2, dy_high_col=3, error_style="Bars")
        dw = FakeDatasetWidget(ds, cfg)
        fig, ax = render(dw)
        containers = ax.containers
        assert len(containers) == 1
        err = containers[0]
        # asymmetric yerr: lower/upper differ
        lower = err.lines[2][0].get_segments()
        # sanity: at least one errorbar segment drawn per point
        assert len(lower) == ds.nrows

    def test_has_asym_false_when_col_is_zero(self, ds):
        cfg = base_cfg(dy_low_col=0, dy_high_col=0, dycol=4, error_style="Bars")
        dw = FakeDatasetWidget(ds, cfg)
        fig, ax = render(dw)
        assert len(ax.containers) == 1

    def test_has_asym_false_when_col_out_of_range(self, ds):
        cfg = base_cfg(dy_low_col=2, dy_high_col=99, error_style="Bars")
        dw = FakeDatasetWidget(ds, cfg)
        # dy_high_col=99 is out of range -> falls back to symmetric (dycol=-1 -> no error)
        fig, ax = render(dw)
        assert len(ax.containers) == 0

    def test_missing_keys_default_to_not_used(self, ds):
        cfg = base_cfg()
        del cfg["dy_low_col"]
        del cfg["dy_high_col"]
        dw = FakeDatasetWidget(ds, cfg)
        fig, ax = render(dw)
        # no error columns at all -> plain line, no errorbar container
        assert len(ax.containers) == 0


class TestErrorStyleRendering:

    def test_bars_style_draws_errorbar_no_fill(self, ds):
        cfg = base_cfg(dy_low_col=2, dy_high_col=3, error_style="Bars")
        dw = FakeDatasetWidget(ds, cfg)
        fig, ax = render(dw)
        assert len(ax.containers) == 1
        # errorbar caps/lines use LineCollections; no fill_between polygon added
        assert all(c.__class__.__name__ != "PolyCollection" for c in ax.collections)

    def test_band_style_draws_fill_between_no_errorbar(self, ds):
        cfg = base_cfg(dy_low_col=2, dy_high_col=3, error_style="Band (fill_between)")
        dw = FakeDatasetWidget(ds, cfg)
        fig, ax = render(dw)
        assert len(ax.containers) == 0
        assert len(ax.lines) == 1  # plain line plot
        assert len(ax.collections) >= 1  # fill_between polygon

    def test_band_style_symmetric_dycol(self, ds):
        cfg = base_cfg(dycol=4, error_style="Band (fill_between)")
        dw = FakeDatasetWidget(ds, cfg)
        fig, ax = render(dw)
        assert len(ax.containers) == 0
        assert len(ax.collections) >= 1

    def test_both_style_draws_errorbar_and_fill(self, ds):
        cfg = base_cfg(dy_low_col=2, dy_high_col=3, error_style="Both")
        dw = FakeDatasetWidget(ds, cfg)
        fig, ax = render(dw)
        assert len(ax.containers) == 1
        assert len(ax.collections) >= 1

    def test_band_alpha_applied(self, ds):
        cfg = base_cfg(dy_low_col=2, dy_high_col=3, error_style="Band (fill_between)",
                        band_alpha=0.6)
        dw = FakeDatasetWidget(ds, cfg)
        fig, ax = render(dw)
        poly = ax.collections[0]
        assert poly.get_alpha() == pytest.approx(0.6)
