"""Tests for pygra.dataset: DataSet loading and apply_transform."""

import numpy as np
import pytest

from pygra.dataset import DataSet, apply_transform


# ---------------------------------------------------------------------------
# Helper: build a DataSet from a numpy array without touching the filesystem
# ---------------------------------------------------------------------------

def make_dataset(arr: np.ndarray) -> DataSet:
    ds = DataSet.__new__(DataSet)
    ds.path = "<test>"
    ds.name = "<test>"
    ds.raw = arr.tolist()
    ds.arr = arr.copy().astype(float)
    ds.skipped_rows = []
    return ds


# ---------------------------------------------------------------------------
# DataSet — file loading
# ---------------------------------------------------------------------------

class TestDataSetLoading:

    def test_valid_file_row_and_col_counts(self, tmp_path):
        p = tmp_path / "data.dat"
        p.write_text("1.0 2.0\n3.0 4.0\n5.0 6.0\n")
        ds = DataSet(str(p))
        assert ds.nrows == 3
        assert ds.ncols == 2

    def test_valid_file_values(self, tmp_path):
        p = tmp_path / "data.dat"
        p.write_text("1.0 2.0\n3.0 4.0\n5.0 6.0\n")
        ds = DataSet(str(p))
        np.testing.assert_array_equal(ds.col(0), [1.0, 3.0, 5.0])
        np.testing.assert_array_equal(ds.col(1), [2.0, 4.0, 6.0])

    def test_no_skipped_rows_on_valid_file(self, tmp_path):
        p = tmp_path / "data.dat"
        p.write_text("1.0 2.0\n3.0 4.0\n")
        ds = DataSet(str(p))
        assert ds.skipped_rows == []

    def test_comments_not_counted_as_skipped(self, tmp_path):
        p = tmp_path / "data.dat"
        p.write_text("# header\n\n1.0 2.0\n# inline comment\n3.0 4.0\n")
        ds = DataSet(str(p))
        assert ds.nrows == 2
        assert ds.skipped_rows == []

    def test_malformed_rows_skipped_count(self, tmp_path):
        p = tmp_path / "data.dat"
        p.write_text("1.0 2.0\nbad row here\n3.0 4.0\nalso bad\n5.0 6.0\n")
        ds = DataSet(str(p))
        assert ds.nrows == 3
        assert len(ds.skipped_rows) == 2

    def test_skipped_rows_record_line_numbers(self, tmp_path):
        p = tmp_path / "data.dat"
        p.write_text("1.0 2.0\nbad row\n3.0 4.0\n")
        ds = DataSet(str(p))
        linenos = [ln for ln, _ in ds.skipped_rows]
        assert linenos == [2]

    def test_skipped_rows_record_content(self, tmp_path):
        p = tmp_path / "data.dat"
        p.write_text("1.0 2.0\nhello world\n3.0 4.0\n")
        ds = DataSet(str(p))
        contents = [c for _, c in ds.skipped_rows]
        assert contents == ["hello world"]

    def test_empty_file_has_zero_cols_and_rows(self, tmp_path):
        p = tmp_path / "empty.dat"
        p.write_text("")
        ds = DataSet(str(p))
        assert ds.ncols == 0
        assert ds.nrows == 0

    def test_only_comments_file(self, tmp_path):
        p = tmp_path / "comments.dat"
        p.write_text("# only\n# comments\n")
        ds = DataSet(str(p))
        assert ds.ncols == 0
        assert ds.skipped_rows == []

    def test_col_out_of_range_returns_none(self, tmp_path):
        p = tmp_path / "data.dat"
        p.write_text("1.0 2.0\n3.0 4.0\n")
        ds = DataSet(str(p))
        assert ds.col(5) is None
        assert ds.col(-1) is None

    def test_col_returns_independent_copy(self, tmp_path):
        p = tmp_path / "data.dat"
        p.write_text("1.0 2.0\n3.0 4.0\n")
        ds = DataSet(str(p))
        c = ds.col(0)
        c[0] = 999.0
        assert ds.arr[0, 0] != 999.0

    def test_name_derived_from_path(self, tmp_path):
        p = tmp_path / "mydata.dat"
        p.write_text("1.0 2.0\n")
        ds = DataSet(str(p))
        assert ds.name == "mydata.dat"

    def test_mixed_valid_and_malformed_line_numbers(self, tmp_path):
        p = tmp_path / "data.dat"
        p.write_text("# comment\n1.0 2.0\nBAD\n3.0 4.0\nALSO BAD\n")
        ds = DataSet(str(p))
        linenos = [ln for ln, _ in ds.skipped_rows]
        assert linenos == [3, 5]

    def test_csv_comma_delimiter_values(self, tmp_path):
        p = tmp_path / "data.csv"
        p.write_text("1.0,2.0\n3.0,4.0\n5.0,6.0\n")
        ds = DataSet(str(p))
        assert ds.nrows == 3
        assert ds.ncols == 2
        np.testing.assert_array_equal(ds.col(0), [1.0, 3.0, 5.0])
        np.testing.assert_array_equal(ds.col(1), [2.0, 4.0, 6.0])

    def test_csv_comma_no_skipped_rows(self, tmp_path):
        p = tmp_path / "data.csv"
        p.write_text("1.0,2.0\n3.0,4.0\n")
        ds = DataSet(str(p))
        assert ds.skipped_rows == []

    def test_hash_comment_lines_not_in_skipped_rows(self, tmp_path):
        p = tmp_path / "data.dat"
        p.write_text("# column header\n1.0 2.0\n# note\n3.0 4.0\n")
        ds = DataSet(str(p))
        assert ds.skipped_rows == []
        assert ds.nrows == 2

    def test_header_line_skipped_silently(self, tmp_path):
        p = tmp_path / "data.dat"
        p.write_text("x y\n1.0 2.0\n3.0 4.0\n")
        ds = DataSet(str(p))
        assert ds.nrows == 2
        assert ds.skipped_rows == []

    def test_csv_header_line_skipped_silently(self, tmp_path):
        p = tmp_path / "data.csv"
        p.write_text("x,y\n1.0,2.0\n3.0,4.0\n")
        ds = DataSet(str(p))
        assert ds.nrows == 2
        assert ds.skipped_rows == []


# ---------------------------------------------------------------------------
# apply_transform
# ---------------------------------------------------------------------------

@pytest.fixture
def ds():
    """Five-row, two-column dataset: col0=[1..5], col1=[2,4,6,8,10]."""
    arr = np.array([[1.0, 2.0],
                    [2.0, 4.0],
                    [3.0, 6.0],
                    [4.0, 8.0],
                    [5.0, 10.0]])
    return make_dataset(arr)


def cfg(op, col=0, val=1.0, new_col=True, **extra):
    return {"op": op, "col": col, "val": val, "new_col": new_col, **extra}


class TestApplyTransformArithmetic:

    def test_multiply_by_constant(self, ds):
        result = apply_transform(ds, cfg("multiply by constant", col=0, val=3.0))
        np.testing.assert_array_almost_equal(result, [3.0, 6.0, 9.0, 12.0, 15.0])

    def test_divide_by_constant(self, ds):
        result = apply_transform(ds, cfg("divide by constant", col=0, val=2.0))
        np.testing.assert_array_almost_equal(result, [0.5, 1.0, 1.5, 2.0, 2.5])

    def test_divide_by_zero_raises(self, ds):
        with pytest.raises(ValueError, match="zero"):
            apply_transform(ds, cfg("divide by constant", col=0, val=0))

    def test_add_constant(self, ds):
        result = apply_transform(ds, cfg("add constant", col=0, val=10.0))
        np.testing.assert_array_almost_equal(result, [11.0, 12.0, 13.0, 14.0, 15.0])

    def test_subtract_constant(self, ds):
        result = apply_transform(ds, cfg("subtract constant", col=0, val=1.0))
        np.testing.assert_array_almost_equal(result, [0.0, 1.0, 2.0, 3.0, 4.0])


class TestApplyTransformNormalize:

    def test_normalize_by_max(self, ds):
        result = apply_transform(ds, cfg("normalize by max", col=0))
        assert result.max() == pytest.approx(1.0)
        np.testing.assert_array_almost_equal(result, [0.2, 0.4, 0.6, 0.8, 1.0])

    def test_normalize_by_max_zero_raises(self):
        ds_zero = make_dataset(np.zeros((3, 2)))
        with pytest.raises(ValueError, match="zero"):
            apply_transform(ds_zero, cfg("normalize by max", col=0))

    def test_normalize_by_value(self, ds):
        result = apply_transform(ds, cfg("normalize by value", col=0, val=5.0))
        np.testing.assert_array_almost_equal(result, [0.2, 0.4, 0.6, 0.8, 1.0])

    def test_normalize_by_value_zero_raises(self, ds):
        with pytest.raises(ValueError, match="zero"):
            apply_transform(ds, cfg("normalize by value", col=0, val=0))


class TestApplyTransformDerivativeAndSmoothing:

    def test_numerical_derivative_linear(self, ds):
        # col1 = 2 * col0  →  dy/dx = 2.0 everywhere
        result = apply_transform(
            ds, {"op": "numerical derivative (dy/dx)", "col": 1, "xcol": 0,
                 "val": 0, "new_col": True}
        )
        np.testing.assert_array_almost_equal(result, [2.0, 2.0, 2.0, 2.0, 2.0])

    def test_numerical_derivative_invalid_xcol(self, ds):
        with pytest.raises(ValueError, match="does not exist"):
            apply_transform(
                ds, {"op": "numerical derivative (dy/dx)", "col": 0, "xcol": 99,
                     "val": 0, "new_col": True}
            )

    def test_moving_average_preserves_linear_signal(self, ds):
        # Savitzky-Golay with polyorder=1 is exact for linear data
        result = apply_transform(ds, cfg("moving average", col=0, val=3))
        np.testing.assert_array_almost_equal(result, [1.0, 2.0, 3.0, 4.0, 5.0], decimal=5)

    def test_moving_average_same_length_as_input(self, ds):
        result = apply_transform(ds, cfg("moving average", col=0, val=3))
        assert len(result) == ds.nrows


class TestApplyTransformErrorsAndSideEffects:

    def test_invalid_column_raises(self, ds):
        with pytest.raises(ValueError, match="does not exist"):
            apply_transform(ds, cfg("multiply by constant", col=99))

    def test_unknown_op_raises(self, ds):
        with pytest.raises(ValueError, match="Unknown operation"):
            apply_transform(ds, cfg("nonexistent op", col=0))

    def test_new_col_true_appends_column(self, ds):
        ncols_before = ds.ncols
        apply_transform(ds, cfg("multiply by constant", col=0, val=2.0, new_col=True))
        assert ds.ncols == ncols_before + 1

    def test_new_col_false_replaces_column_in_place(self, ds):
        ncols_before = ds.ncols
        apply_transform(ds, cfg("multiply by constant", col=0, val=2.0, new_col=False))
        assert ds.ncols == ncols_before
        np.testing.assert_array_almost_equal(ds.col(0), [2.0, 4.0, 6.0, 8.0, 10.0])

    def test_return_value_matches_new_column(self, ds):
        result = apply_transform(ds, cfg("add constant", col=0, val=100.0, new_col=True))
        np.testing.assert_array_equal(result, ds.col(ds.ncols - 1))
