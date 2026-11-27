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
