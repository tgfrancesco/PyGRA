"""
history.py — bounded undo/redo stacks of application snapshots
"""

from collections import deque


class History:
    """
    Undo/redo history of opaque state snapshots.

    The caller pushes a snapshot *before* each change.  :meth:`undo` and
    :meth:`redo` take the current state so it can be moved to the
    opposite stack, and return the snapshot to restore.

    Parameters
    ----------
    max_size : int, optional
        Maximum number of undo steps kept.  The oldest snapshot is
        dropped when the limit is exceeded.  Default is ``30``.
    """

    def __init__(self, max_size: int = 30):
        self.max_size = max_size
        self._undo: deque = deque(maxlen=max_size)
        self._redo: deque = deque(maxlen=max_size)

    def push(self, state):
        """Record *state* as an undo step and clear the redo stack."""
        self._undo.append(state)
        self._redo.clear()

    def undo(self, current_state):
        """
        Step back one snapshot.

        Parameters
        ----------
        current_state
            The state at the time of the call; moved to the redo stack.

        Returns
        -------
        object or None
            The previous snapshot, or ``None`` if there is nothing to undo.
        """
        if not self._undo:
            return None
        self._redo.append(current_state)
        return self._undo.pop()

    def redo(self, current_state):
        """
        Step forward one snapshot.

        Parameters
        ----------
        current_state
            The state at the time of the call; moved to the undo stack.

        Returns
        -------
        object or None
            The next snapshot, or ``None`` if there is nothing to redo.
        """
        if not self._redo:
            return None
        self._undo.append(current_state)
        return self._redo.pop()

    def can_undo(self) -> bool:
        return bool(self._undo)

    def can_redo(self) -> bool:
        return bool(self._redo)

    def clear(self):
        """Drop all undo and redo snapshots."""
        self._undo.clear()
        self._redo.clear()
