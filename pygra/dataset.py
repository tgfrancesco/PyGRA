"""
dataset.py — data loading and transform operations
"""

import csv
from pathlib import Path

import numpy as np
from scipy.signal import savgol_filter


def _can_float(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False


class DataSet:
    """
    Load a whitespace-delimited data file into a NumPy array.

    Lines beginning with ``#`` and blank lines are silently ignored.
    Rows that cannot be fully converted to floats are skipped and
    recorded in :attr:`skipped_rows`.

    Parameters
    ----------
    path : str
        Absolute or relative path to the data file.

    Attributes
    ----------
    path : str
        Path passed to the constructor.
    name : str
        Filename component of *path* (basename).
    raw : list of list of float
        Parsed data rows as a nested list, populated during loading.
    arr : numpy.ndarray
        2-D float64 array of shape ``(nrows, ncols)``.
        Shape is ``(0, 0)`` when no valid rows were found.
    skipped_rows : list of tuple[int, str]
        ``(line_number, raw_content)`` for every row that could not be
        parsed.  Line numbers are 1-based.
    """

    def __init__(self, path: str):
        """
        Parameters
        ----------
        path : str
            Path to the data file to load.
        """
        self.path = path
        self.name = Path(path).name
        self.raw: list = []
        self._load()

    def _load(self):
        self.skipped_rows: list[tuple[int, str]] = []
        with open(self.path) as f:
            lines = f.readlines()

        # Detect delimiter from the first non-comment, non-empty line
        use_csv = False
        for raw_line in lines:
            stripped = raw_line.strip()
            if stripped and not stripped.startswith('#'):
                use_csv = ',' in stripped
                break

        header_consumed = False
        for lineno, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()
            if not line or line.startswith('#'):
                continue

            if use_csv:
                tokens = [t.strip() for t in next(csv.reader([line]))]
            else:
                tokens = line.split()

            try:
                row = [float(t) for t in tokens]
            except ValueError:
                if not header_consumed and not any(_can_float(t) for t in tokens):
                    header_consumed = True
                    continue
                self.skipped_rows.append((lineno, line))
                continue

            self.raw.append(row)
            header_consumed = True

        self.arr = np.array(self.raw) if self.raw else np.empty((0, 0))

    @property
    def ncols(self) -> int:
        """
        Number of columns in the loaded data.

        Returns
        -------
        int
            ``arr.shape[1]`` when the array is 2-D and non-empty,
            otherwise ``0``.
        """
        return self.arr.shape[1] if self.arr.ndim == 2 and self.arr.size > 0 else 0

    @property
    def nrows(self) -> int:
        """
        Number of data rows.

        Returns
        -------
        int
            ``arr.shape[0]``.
        """
        return self.arr.shape[0]

    def col(self, idx: int):
        """
        Return a copy of column *idx*.

        Parameters
        ----------
        idx : int
            Column index (0-based).

        Returns
        -------
        numpy.ndarray or None
            Copy of the column as a 1-D float64 array, or ``None`` if
            *idx* is out of range.
        """
        if idx < 0 or idx >= self.ncols:
            return None
        return self.arr[:, idx].copy()


def apply_transform(dataset: DataSet, cfg: dict) -> np.ndarray:
    """
    Apply a transform operation to one column of a DataSet.

    Parameters
    ----------
    dataset : DataSet
        The dataset to modify.  Extended in-place when
        ``cfg["new_col"]`` is ``True``; column overwritten when ``False``.
    cfg : dict
        Transform configuration with the following keys:

        ``"col"`` : int
            Target column index.
        ``"op"`` : str
            Operation name; must be one of the strings in
            :data:`constants.TRANSFORM_OPS`.
        ``"val"`` : float
            Scalar operand for arithmetic and normalisation operations,
            or window size for the moving average.
        ``"xcol"`` : int, optional
            x-column index; required when *op* is
            ``"numerical derivative (dy/dx)"``.
        ``"new_col"`` : bool, optional
            If ``True`` (default) the result is appended as a new column;
            if ``False`` it overwrites column ``"col"``.

    Returns
    -------
    numpy.ndarray
        1-D array containing the transform result.

    Raises
    ------
    ValueError
        If the target column does not exist, if division or normalisation
        by zero is attempted, or if *op* is not a recognised operation.
    """
    col = dataset.col(cfg["col"])
    if col is None:
        raise ValueError(f"Column {cfg['col']} does not exist.")

    op  = cfg["op"]
    val = cfg["val"]

    if op == "multiply by constant":
        result = col * val
    elif op == "divide by constant":
        if val == 0:
            raise ValueError("Cannot divide by zero.")
        result = col / val
    elif op == "add constant":
        result = col + val
    elif op == "subtract constant":
        result = col - val
    elif op == "normalize by max":
        m = np.max(np.abs(col))
        if m == 0:
            raise ValueError("Max is zero, cannot normalize.")
        result = col / m
    elif op == "normalize by value":
        if val == 0:
            raise ValueError("Cannot normalize by zero.")
        result = col / val
    elif op == "numerical derivative (dy/dx)":
        xcol = dataset.col(cfg["xcol"])
        if xcol is None:
            raise ValueError(f"x column {cfg['xcol']} does not exist.")
        result = np.gradient(col, xcol)
    elif op == "moving average":
        w = max(3, int(val))
        if w % 2 == 0:
            w += 1
        wl = min(w, len(col) - (0 if len(col) % 2 != 0 else 1))
        result = savgol_filter(col, window_length=wl, polyorder=1)
    else:
        raise ValueError(f"Unknown operation: {op}")

    if cfg.get("new_col", True):
        dataset.arr = np.column_stack([dataset.arr, result])
    else:
        dataset.arr[:, cfg["col"]] = result

    return result
