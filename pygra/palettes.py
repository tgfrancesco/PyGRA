"""
palettes.py — scientific color palettes for PyGRA
"""

import numpy as np


def _mpl_palette(name: str, n: int) -> list:
    """Extract n colors from a matplotlib colormap."""
    try:
        import matplotlib.pyplot as plt
        cmap = plt.get_cmap(name)
        return [_rgba_to_hex(cmap(i / (n - 1))) for i in range(n)]
    except Exception:
        return []


def _rgba_to_hex(rgba) -> str:
    r, g, b = [int(x * 255) for x in rgba[:3]]
    return f"#{r:02x}{g:02x}{b:02x}"


def _css_hex(r, g, b):
    return f"#{r:02x}{g:02x}{b:02x}"


# ---------------------------------------------------------------------------
# Palette definitions
# ---------------------------------------------------------------------------

PALETTES = {}

# Okabe-Ito (colorblind-friendly, 8 colors)
PALETTES["Okabe-Ito"] = [
    "#000000", "#e69f00", "#56b4e9", "#009e73",
    "#f0e442", "#0072b2", "#d55e00", "#cc79a7",
]

# Wong (colorblind-friendly, 8 colors)
PALETTES["Wong"] = [
    "#000000", "#e69f00", "#56b4e9", "#009e73",
    "#f0e442", "#0072b2", "#d55e00", "#cc79a7",
]

# Paul Tol's colorblind-safe
PALETTES["Tol Bright"] = [
    "#4477aa", "#ee6677", "#228833", "#ccbb44",
    "#66ccee", "#aa3377", "#bbbbbb",
]

PALETTES["Tol Muted"] = [
    "#332288", "#117733", "#44aa99", "#88ccee",
    "#ddcc77", "#cc6677", "#aa4499", "#882255",
    "#999933", "#661100", "#6699cc", "#888888",
]

# Matplotlib categorical
PALETTES["tab10"] = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
]

PALETTES["tab20"] = [
    "#1f77b4", "#aec7e8", "#ff7f0e", "#ffbb78", "#2ca02c",
    "#98df8a", "#d62728", "#ff9896", "#9467bd", "#c5b0d5",
    "#8c564b", "#c49c94", "#e377c2", "#f7b6d2", "#7f7f7f",
    "#c7c7c7", "#bcbd22", "#dbdb8d", "#17becf", "#9edae5",
]

PALETTES["Set1"] = [
    "#e41a1c", "#377eb8", "#4daf4a", "#984ea3",
    "#ff7f00", "#ffff33", "#a65628", "#f781bf", "#999999",
]

PALETTES["Set2"] = [
    "#66c2a5", "#fc8d62", "#8da0cb", "#e78ac3",
    "#a6d854", "#ffd92f", "#e5c494", "#b3b3b3",
]

PALETTES["Set3"] = [
    "#8dd3c7", "#ffffb3", "#bebada", "#fb8072", "#80b1d3",
    "#fdb462", "#b3de69", "#fccde5", "#d9d9d9", "#bc80bd",
    "#ccebc5", "#ffed6f",
]

PALETTES["Paired"] = [
    "#a6cee3", "#1f78b4", "#b2df8a", "#33a02c",
    "#fb9a99", "#e31a1c", "#fdbf6f", "#ff7f00",
    "#cab2d6", "#6a3d9a", "#ffff99", "#b15928",
]

PALETTES["Dark2"] = [
    "#1b9e77", "#d95f02", "#7570b3", "#e7298a",
    "#66a61e", "#e6ab02", "#a6761d", "#666666",
]

PALETTES["Pastel1"] = [
    "#fbb4ae", "#b3cde3", "#ccebc5", "#decbe4",
    "#fed9a6", "#ffffcc", "#e5d8bd", "#fddaec", "#f2f2f2",
]

# Sequential (sampled at 8 points)
for _name in ["viridis", "plasma", "inferno", "magma", "cividis",
              "coolwarm", "RdYlBu", "Spectral", "PuOr"]:
    _cols = _mpl_palette(_name, 8)
    if _cols:
        PALETTES[_name] = _cols

# CSS named colors (grouped by hue family)
PALETTES["CSS Reds"] = [
    "#ff0000", "#dc143c", "#b22222", "#8b0000",
    "#ff6347", "#ff4500", "#ff7f50", "#fa8072",
]
PALETTES["CSS Blues"] = [
    "#0000ff", "#0000cd", "#00008b", "#000080",
    "#4169e1", "#1e90ff", "#00bfff", "#87ceeb",
]
PALETTES["CSS Greens"] = [
    "#008000", "#006400", "#228b22", "#2e8b57",
    "#32cd32", "#7cfc00", "#90ee90", "#00ff7f",
]
PALETTES["CSS Purples"] = [
    "#800080", "#8b008b", "#9400d3", "#4b0082",
    "#8a2be2", "#9932cc", "#ba55d3", "#da70d6",
]
PALETTES["CSS Neutrals"] = [
    "#000000", "#2f2f2f", "#555555", "#808080",
    "#aaaaaa", "#d3d3d3", "#f0f0f0", "#ffffff",
]
PALETTES["CSS Warm"] = [
    "#ff8c00", "#ffa500", "#ffd700", "#ffff00",
    "#adff2f", "#ff69b4", "#ff1493", "#c71585",
]

PALETTE_GROUPS = {
    "Colorblind-friendly": ["Okabe-Ito", "Wong", "Tol Bright", "Tol Muted"],
    "Matplotlib categorical": ["tab10", "tab20", "Set1", "Set2", "Set3",
                                "Paired", "Dark2", "Pastel1"],
    "Sequential / diverging": ["viridis", "plasma", "inferno", "magma",
                                "cividis", "coolwarm", "RdYlBu", "Spectral", "PuOr"],
    "CSS colors": ["CSS Reds", "CSS Blues", "CSS Greens",
                   "CSS Purples", "CSS Neutrals", "CSS Warm"],
}
