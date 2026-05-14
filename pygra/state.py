"""
state.py — save and load application state as JSON
"""

import json
import numpy as np


def save_state(path: str, dataset_widgets: list, axis_settings: dict,
               style_settings: dict, annotations: list | None = None):
    """
    Serialise the full application state to a JSON file.

    Parameters
    ----------
    path : str
        Destination file path.  Created or overwritten.
    dataset_widgets : list of DatasetWidget
        All active series panels.  Each widget's dataset data and visual
        configuration are included in the output.
    axis_settings : dict
        Axis labels, title, log-scale flags, and manual axis-limit strings
        as returned by ``MainWindow._get_axis_settings()``.
    style_settings : dict
        Global plot style settings (font sizes, grid, theme, DPI, legend).
    annotations : list of dict, optional
        Text annotations with keys ``"text"``, ``"x"``, ``"y"``,
        ``"fontsize"``, ``"color"``, ``"bold"``.

    Raises
    ------
    OSError
        If *path* cannot be opened for writing.
    """
    series = []
    for dw in dataset_widgets:
        cfg = dw.get_config()
        series.append({
            "path":   dw.dataset.path,
            "name":   dw.dataset.name,
            "data":   dw.dataset.arr.tolist(),
            "config": cfg,
        })
    state = {
        "version":        "0.8.2",
        "series":         series,
        "axis_settings":  axis_settings,
        "style_settings": style_settings,
        "annotations":    annotations or [],
    }
    with open(path, "w") as f:
        json.dump(state, f, indent=2)


def load_state(path: str) -> dict:
    """
    Load application state from a JSON session file.

    Reads a file produced by :func:`save_state` and converts each
    series ``"data"`` field from a nested list back to a NumPy array.

    Parameters
    ----------
    path : str
        Path to a ``.json`` session file.

    Returns
    -------
    dict
        State dictionary with keys ``"version"``, ``"series"``,
        ``"axis_settings"``, and ``"style_settings"``.  The ``"data"``
        value inside each series entry is a 2-D ``numpy.ndarray``.

    Raises
    ------
    OSError
        If *path* does not exist or cannot be read.
    json.JSONDecodeError
        If the file is not valid JSON.
    KeyError
        If the file does not contain a ``"series"`` key.
    """
    with open(path) as f:
        state = json.load(f)
    for s in state["series"]:
        s["data"] = np.array(s["data"])
    return state
