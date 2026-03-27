"""
preferences.py — persistent user preferences
Stored in ~/.config/pygra/preferences.json
"""

import json
import os
from pathlib import Path

from .constants import DEFAULT_STYLE_SETTINGS

PREFS_PATH = Path.home() / ".config" / "pygra" / "preferences.json"

DEFAULT_PREFS = {
    # window geometry
    "window_x":      100,
    "window_y":      100,
    "window_w":      1200,
    "window_h":      760,
    "splitter_pos":  330,   # left panel width in pixels

    # style settings (mirrors DEFAULT_STYLE_SETTINGS)
    **DEFAULT_STYLE_SETTINGS,

    # saved custom colors (list of hex strings)
    "custom_colors": [],
}


def load_prefs() -> dict:
    """Load preferences from disk. Returns defaults if file doesn't exist."""
    prefs = dict(DEFAULT_PREFS)
    if PREFS_PATH.exists():
        try:
            with open(PREFS_PATH) as f:
                saved = json.load(f)
            prefs.update(saved)
        except Exception:
            pass
    return prefs


def save_prefs(prefs: dict):
    """Save preferences to disk."""
    PREFS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PREFS_PATH, "w") as f:
        json.dump(prefs, f, indent=2)
