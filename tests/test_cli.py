"""Tests for pygra.main CLI parsing."""

import tempfile
import os

import numpy as np

from pygra.main import _parse_interleaved
from pygra.dataset import DataSet


class TestParseInterleaved:

    def test_per_file_columns_do_not_leak_to_later_files(self):
        args = _parse_interleaved(
            ["--file", "a.dat", "--x", "0", "--y", "3", "--file", "b.dat"]
        )
        assert args["files"] == [
            {"path": "a.dat", "xcol": 0, "ycol": 3, "dxcol": 0, "dycol": 0},
            {"path": "b.dat", "xcol": 0, "ycol": 1, "dxcol": 0, "dycol": 0},
        ]

    def test_trailing_columns_apply_globally_to_positional_files(self):
        args = _parse_interleaved(["a.dat", "b.dat", "--x", "2", "--y", "4"])
        assert args["files"] == [
            {"path": "a.dat", "xcol": 2, "ycol": 4, "dxcol": 0, "dycol": 0},
            {"path": "b.dat", "xcol": 2, "ycol": 4, "dxcol": 0, "dycol": 0},
        ]

    def test_mixed_per_file_and_trailing_global_columns(self):
        args = _parse_interleaved(
            ["--file", "a.dat", "--x", "1", "--file", "b.dat", "--y", "5"]
        )
        assert args["files"] == [
            {"path": "a.dat", "xcol": 1, "ycol": 5, "dxcol": 0, "dycol": 0},
            {"path": "b.dat", "xcol": 0, "ycol": 5, "dxcol": 0, "dycol": 0},
        ]

    def test_load_argument_is_preserved(self):
        args = _parse_interleaved(["--load", "session.json", "a.dat"])
        assert args["load"] == "session.json"
        assert args["files"] == [
            {"path": "a.dat", "xcol": 0, "ycol": 1, "dxcol": 0, "dycol": 0}
        ]

    def test_per_file_error_columns_do_not_leak_to_later_files(self):
        args = _parse_interleaved(
            ["--file", "a.dat", "--dx", "2", "--dy", "3", "--file", "b.dat"]
        )
        assert args["files"] == [
            {"path": "a.dat", "xcol": 0, "ycol": 1, "dxcol": 2, "dycol": 3},
            {"path": "b.dat", "xcol": 0, "ycol": 1, "dxcol": 0, "dycol": 0},
        ]

    def test_trailing_error_columns_apply_globally_to_positional_files(self):
        args = _parse_interleaved(["a.dat", "b.dat", "--dx", "2", "--dy", "3"])
        assert args["files"] == [
            {"path": "a.dat", "xcol": 0, "ycol": 1, "dxcol": 2, "dycol": 3},
            {"path": "b.dat", "xcol": 0, "ycol": 1, "dxcol": 2, "dycol": 3},
        ]

    def test_error_columns_default_to_zero(self):
        args = _parse_interleaved(["a.dat"])
        assert args["files"] == [
            {"path": "a.dat", "xcol": 0, "ycol": 1, "dxcol": 0, "dycol": 0}
        ]

    def test_downsampling_default_is_one(self):
        args = _parse_interleaved(["a.dat"])
        assert args["downsampling"] == 1

    def test_downsampling_long_flag(self):
        args = _parse_interleaved(["a.dat", "--downsampling", "10"])
        assert args["downsampling"] == 10

    def test_downsampling_short_flag(self):
        args = _parse_interleaved(["a.dat", "-s", "5"])
        assert args["downsampling"] == 5


class TestDataSetDownsampling:

    def _make_file(self, rows: int):
        """Write a two-column file with *rows* rows and return its path."""
        fd, path = tempfile.mkstemp(suffix=".dat")
        with os.fdopen(fd, "w") as f:
            for i in range(rows):
                f.write(f"{i} {i * 2}\n")
        return path

    def test_step_1_gives_all_rows(self):
        path = self._make_file(10)
        try:
            ds = DataSet(path, step=1)
            assert ds.nrows == 10
        finally:
            os.unlink(path)

    def test_step_2_gives_every_other_row(self):
        path = self._make_file(10)
        try:
            ds = DataSet(path, step=2)
            assert ds.nrows == 5
            assert np.array_equal(ds.arr[:, 0], np.arange(0, 10, 2, dtype=float))
        finally:
            os.unlink(path)

    def test_default_step_no_downsampling(self):
        path = self._make_file(6)
        try:
            ds = DataSet(path)
            assert ds.nrows == 6
            assert ds.downsample_step == 1
        finally:
            os.unlink(path)
