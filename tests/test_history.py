"""Tests for pygra.history: the undo/redo History stack."""

from pygra.history import History


def test_empty_history():
    h = History()
    assert not h.can_undo()
    assert not h.can_redo()
    assert h.undo("cur") is None
    assert h.redo("cur") is None


def test_push_and_undo():
    h = History()
    h.push("a")
    h.push("b")
    assert h.can_undo()
    assert h.undo("c") == "b"
    assert h.undo("b") == "a"
    assert not h.can_undo()
    assert h.undo("a") is None


def test_undo_then_redo():
    h = History()
    h.push("a")
    assert h.undo("b") == "a"
    assert h.can_redo()
    assert h.redo("a") == "b"
    assert not h.can_redo()
    assert h.can_undo()
    assert h.undo("b") == "a"


def test_multiple_undo_redo_round_trip():
    h = History()
    for s in ("s0", "s1", "s2"):
        h.push(s)
    cur = "s3"
    for expected in ("s2", "s1", "s0"):
        prev = h.undo(cur)
        assert prev == expected
        cur = prev
    for expected in ("s1", "s2", "s3"):
        nxt = h.redo(cur)
        assert nxt == expected
        cur = nxt
    assert not h.can_redo()


def test_push_clears_redo():
    h = History()
    h.push("a")
    h.undo("b")
    assert h.can_redo()
    h.push("c")
    assert not h.can_redo()
    assert h.redo("d") is None


def test_max_size_drops_oldest():
    h = History(max_size=3)
    for i in range(5):
        h.push(i)
    assert [h.undo("x") for _ in range(3)] == [4, 3, 2]
    assert not h.can_undo()


def test_redo_respects_max_size():
    h = History(max_size=2)
    h.push("a")
    h.push("b")
    h.undo("c")
    h.push("d")      # undo stack: a, d
    assert h.undo("e") == "d"
    assert h.redo("d") == "e"
    assert h.undo("e") == "d"
    assert h.undo("d") == "a"
    assert not h.can_undo()


def test_default_max_size_is_30():
    h = History()
    for i in range(40):
        h.push(i)
    n = 0
    while h.can_undo():
        h.undo(None)
        n += 1
    assert n == 30


def test_clear():
    h = History()
    h.push("a")
    h.push("b")
    h.undo("c")
    h.clear()
    assert not h.can_undo()
    assert not h.can_redo()


# ---------------------------------------------------------------------------
# Dataset contents in snapshots
# ---------------------------------------------------------------------------

import numpy as np
import pytest

from pygra.dataset import DataSet, apply_transform
from pygra.history import snapshot_datasets, restore_datasets, clamp_column


def _make_dataset(arr):
    ds = DataSet.__new__(DataSet)
    ds.path = ds.name = "<test>"
    ds.arr = np.asarray(arr, dtype=float)
    ds.raw = ds.arr.tolist()
    ds.skipped_rows = []
    return ds


@pytest.mark.parametrize("new_col", [True, False])
def test_transform_then_restore_gives_original_array(new_col):
    ds = _make_dataset([[1, 2], [3, 4], [5, 6]])
    original = ds.arr.copy()
    original_arr = ds.arr
    snap = snapshot_datasets([ds])

    apply_transform(ds, {"col": 1, "op": "multiply by constant",
                         "val": 10.0, "new_col": new_col})
    assert ds.arr is not original_arr                  # replaced, not in place
    np.testing.assert_array_equal(original_arr, original)
    assert ds.ncols == (3 if new_col else 2)

    restore_datasets(snap)
    assert ds.arr is original_arr
    np.testing.assert_array_equal(ds.arr, original)
    assert ds.ncols == 2


@pytest.mark.parametrize("new_col", [True, False])
def test_restore_then_redo_round_trip(new_col):
    ds = _make_dataset([[1, 2], [3, 4]])
    before = snapshot_datasets([ds])
    apply_transform(ds, {"col": 0, "op": "add constant",
                         "val": 1.0, "new_col": new_col})
    after = snapshot_datasets([ds])
    transformed = ds.arr.copy()

    restore_datasets(before)
    np.testing.assert_array_equal(ds.arr, [[1, 2], [3, 4]])
    restore_datasets(after)
    np.testing.assert_array_equal(ds.arr, transformed)


def test_restore_puts_back_raw():
    ds = _make_dataset([[1, 2]])
    raw = ds.raw
    snap = snapshot_datasets([ds])
    ds.arr = np.array([[9.0, 9.0]])
    ds.raw = [[9.0, 9.0]]
    restore_datasets(snap)
    assert ds.raw is raw


def test_restore_without_raw_attribute():
    ds = _make_dataset([[1, 2]])
    del ds.raw
    snap = snapshot_datasets([ds])
    ds.arr = np.zeros((1, 3))
    restore_datasets(snap)
    assert ds.arr.shape == (1, 2)
    assert not hasattr(ds, "raw")


def test_clamp_column():
    assert clamp_column(1, 3, optional=False) == 1
    assert clamp_column(2, 2, optional=False) == 1
    assert clamp_column(2, 2, optional=True) == -1
    assert clamp_column(-1, 2, optional=False) == -1
    assert clamp_column(0, 0, optional=False) == -1
