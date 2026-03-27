"""
constants.py — shared style constants
"""

MARKERS = ["o", "s", "^", "D", "v", "P", "X", "*", "h", "none"]
MARKER_LABELS = [
    "circle", "square", "triangle up", "diamond", "triangle down",
    "plus (filled)", "x (filled)", "star", "hexagon", "none",
]

LINESTYLES = ["-", "--", "-.", ":", "none"]
LINESTYLE_LABELS = ["solid", "dashed", "dash-dot", "dotted", "none"]

COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
]

TRANSFORM_OPS = [
    "multiply by constant",
    "divide by constant",
    "add constant",
    "subtract constant",
    "normalize by max",
    "normalize by value",
    "numerical derivative (dy/dx)",
    "moving average",
]

HIST_BINS = ["auto", "sqrt", "sturges", "fd", "manual"]
HIST_NORM = ["count", "density", "probability"]
HIST_FITS = ["none", "Gaussian", "Exponential", "Maxwell-Boltzmann", "Poisson", "Custom..."]

PLOT_THEMES = [
    "default", "dark_background", "seaborn-v0_8-darkgrid",
    "seaborn-v0_8-whitegrid", "ggplot", "bmh", "grayscale",
]

DEFAULT_STYLE_SETTINGS = {
    "title_fs":   14,
    "label_fs":   13,
    "tick_fs":    11,
    "legend_fs":  11,
    "major_x":    0.0,
    "major_y":    0.0,
    "minor_x":    0,
    "minor_y":    0,
    "grid_major": True,
    "grid_minor": False,
    "theme":      "default",
    "dpi":        150,
    "legend_loc":          "best",
    "legend_frameon":      True,
    "legend_alpha":        1.0,
    "legend_ncols":        1,
    "legend_handlelength": 2.0,
}
