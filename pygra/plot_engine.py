"""
plot_engine.py — stateless plot rendering function

All matplotlib drawing logic lives here so that MainWindow._plot() is a
thin wrapper responsible only for reading UI state and updating instance
variables from the returned dict.
"""

import sys

import numpy as np
from matplotlib.ticker import AutoMinorLocator, MultipleLocator


def render_plot(fig, ax, dataset_widgets, fit_layers, annotations,
                style_settings, axis_settings, legend_pos,
                pct_label_positions):
    """
    Render all series, fits, axes, legend, and text annotations onto *ax*.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The figure that owns *ax* (needed for colorbar and layout).
    ax : matplotlib.axes.Axes
        The axes to draw on.  The caller is responsible for creating it
        (typically via ``fig.add_subplot(111)``).
    dataset_widgets : list of DatasetWidget
        Active series panels in display order.
    fit_layers : list
        Fit-layer objects with attributes ``visible``, ``x``, ``y``,
        ``linestyle``, ``linewidth``, ``color``, ``label``.
    annotations : list of dict
        Text annotation dicts with keys ``"x"``, ``"y"``, ``"text"``,
        ``"fontsize"``, ``"color"``, ``"bold"``, ``"rotation"``.
        Coordinates are in axes-fraction space (0–1).
    style_settings : dict
        Global style settings (font sizes, grid, bold flags, legend
        options, etc.).  See :data:`constants.DEFAULT_STYLE_SETTINGS`.
    axis_settings : dict
        Keys: ``"xl"`` (x-label str), ``"yl"`` (y-label str),
        ``"title"`` (str), ``"logx"`` (bool), ``"logy"`` (bool),
        ``"xmin"``, ``"xmax"``, ``"ymin"``, ``"ymax"`` (str, may be "").
    legend_pos : tuple or None
        ``(x, y)`` in axes-fraction coordinates for a dragged legend, or
        ``None`` to use the matplotlib ``loc`` setting.
    pct_label_positions : list
        Mutable list of ``(x, y)`` tuples (or ``None``) for dragged
        percentage labels.  The list is extended in-place as new labels
        are created.

    Returns
    -------
    dict
        ``"legend"``         — the :class:`~matplotlib.legend.Legend` or ``None``
        ``"pct_texts"``      — list of :class:`~matplotlib.text.Text` artists
        ``"annot_artists"``  — list of :class:`~matplotlib.text.Text` artists
    """
    ss = style_settings
    pct_texts     = []
    annot_artists = []
    legend        = None

    # ---- series ----
    for dw in dataset_widgets:
        cfg = dw.get_config()
        if not cfg["visible"]:
            continue
        ds = dw.dataset

        # histogram (1D)
        if cfg["hist_mode"]:
            data = ds.col(cfg["hcol"])
            if data is None:
                continue
            bins = (cfg["hist_nbins"] if cfg["hist_bins"] == "manual"
                    else cfg["hist_bins"])
            norm       = cfg["hist_norm"]
            horizontal = cfg.get("hist_horizontal", False)
            show_pct   = cfg.get("hist_show_pct", False)
            plot_kw = dict(label=cfg["label"], facecolor=cfg["color"],
                           edgecolor=cfg["face_color"], alpha=0.75)
            if norm == "probability":
                counts, edges = np.histogram(data, bins=bins)
                counts = counts / counts.sum()
                widths = np.diff(edges)
                if horizontal:
                    bars = ax.barh(edges[:-1], counts, height=widths,
                                   align="edge", **plot_kw)
                else:
                    bars = ax.bar(edges[:-1], counts, width=widths,
                                  align="edge", **plot_kw)
                patches   = list(bars)
                bar_vals  = [p.get_width() if horizontal else p.get_height()
                             for p in patches]
            else:
                n, _, patches = ax.hist(
                    data, bins=bins, density=(norm == "density"),
                    orientation="horizontal" if horizontal else "vertical",
                    **plot_kw)
                bar_vals = list(n)

            color_by_value = cfg.get("hist_color_by_value", False)
            if color_by_value and bar_vals:
                from matplotlib.cm import get_cmap
                from matplotlib.colors import Normalize
                cmap   = get_cmap(cfg.get("hist_colormap", "viridis"))
                norm_c = Normalize(vmin=min(bar_vals), vmax=max(bar_vals) or 1.0)
                for patch, val in zip(patches, bar_vals):
                    patch.set_facecolor(cmap(norm_c(val)))

            if show_pct:
                pct_fs = cfg.get("pct_fontsize", 9.0)
                total  = sum(bar_vals) or 1.0
                for patch, val in zip(patches, bar_vals):
                    pct = val / total * 100
                    idx = len(pct_texts)
                    if horizontal:
                        default_x = val
                        default_y = patch.get_y() + patch.get_height() / 2
                        ha, va = "left", "center"
                    else:
                        default_x = patch.get_x() + patch.get_width() / 2
                        default_y = val
                        ha, va = "center", "bottom"
                    if idx < len(pct_label_positions) and pct_label_positions[idx] is not None:
                        tx, ty = pct_label_positions[idx]
                    else:
                        tx, ty = default_x, default_y
                        if idx >= len(pct_label_positions):
                            pct_label_positions.append(None)
                    _pct_fw = "bold" if ss.get("pct_bold", False) else "normal"
                    txt = ax.text(tx, ty, f"{pct:.1f}%",
                                  ha=ha, va=va, fontsize=pct_fs,
                                  fontweight=_pct_fw, clip_on=False)
                    pct_texts.append(txt)
            continue

        # 2D histogram
        if cfg.get("hist2d_mode", False):
            x_data = ds.col(cfg["xcol"])
            y_data = ds.col(cfg["ycol"])
            if x_data is None or y_data is None:
                continue
            bx = (np.histogram_bin_edges(x_data, bins="auto")
                  if not cfg.get("bins_x") else cfg["bins_x"])
            by = (np.histogram_bin_edges(y_data, bins="auto")
                  if not cfg.get("bins_y") else cfg["bins_y"])
            norm_val = None
            if cfg.get("log_scale", False):
                from matplotlib.colors import LogNorm
                norm_val = LogNorm()
            h = ax.hist2d(x_data, y_data, bins=(bx, by),
                          cmap=cfg.get("colormap", "viridis"),
                          norm=norm_val,
                          density=(cfg.get("norm", "count") == "density"))
            if cfg.get("colorbar", True):
                fig.colorbar(h[3], ax=ax)
            continue

        # xy plot
        x = ds.col(cfg["xcol"])
        y = ds.col(cfg["ycol"])
        if x is None or y is None:
            continue
        dx = ds.col(cfg["dxcol"]) if cfg["dxcol"] >= 0 else None
        dy = ds.col(cfg["dycol"]) if cfg["dycol"] >= 0 else None

        dy_low_col  = cfg.get("dy_low_col", 0)
        dy_high_col = cfg.get("dy_high_col", 0)
        has_asym = (dy_low_col > 0 and dy_high_col > 0
                    and dy_low_col < ds.ncols and dy_high_col < ds.ncols)
        dy_low = dy_high = None
        if has_asym:
            dy_low  = ds.col(dy_low_col)
            dy_high = ds.col(dy_high_col)
            yerr = [dy_low, dy_high]
        else:
            yerr = dy

        error_style = cfg.get("error_style", "Bars")
        band_alpha  = cfg.get("band_alpha", 0.25)

        ls = cfg["linestyle"] if cfg["linestyle"] != "none" else "None"
        mk = cfg["marker"]    if cfg["marker"]    != "none" else "None"

        plot_kw = dict(
            linestyle=ls, linewidth=cfg["linewidth"],
            marker=mk, markersize=cfg["markersize"],
            color=cfg["color"],
            markerfacecolor=cfg["face_color"],
            markeredgecolor=cfg["color"],
            label=cfg["label"],
            zorder=cfg.get("zorder", 2),
        )

        has_err = has_asym or dy is not None or dx is not None
        show_bars = error_style in ("Bars", "Both")
        show_band = error_style in ("Band (fill_between)", "Both")

        if has_err and show_bars:
            err = ax.errorbar(x, y, xerr=dx, yerr=yerr, capsize=3, **plot_kw)
            # Matplotlib labels the ErrorbarContainer, but hit-testing uses
            # the inner Line2D from ax.get_lines().
            if err.lines and err.lines[0] is not None:
                err.lines[0].set_label(cfg["label"])
                err.set_label("_nolegend_")
        else:
            ax.plot(x, y, **plot_kw)

        if show_band:
            if has_asym:
                ax.fill_between(x, y - dy_low, y + dy_high,
                                 alpha=band_alpha, color=cfg["color"])
            elif dy is not None:
                ax.fill_between(x, y - dy, y + dy,
                                 alpha=band_alpha, color=cfg["color"])

    # ---- fit layers ----
    for layer in fit_layers:
        if layer.visible:
            ax.plot(layer.x, layer.y,
                    linestyle=layer.linestyle,
                    linewidth=layer.linewidth,
                    color=layer.color,
                    label=layer.label)

    # ---- axis configuration ----
    if axis_settings.get("logx"): ax.set_xscale("log")
    if axis_settings.get("logy"): ax.set_yscale("log")

    _lbl_fw   = "bold" if ss.get("label_bold",  False) else "normal"
    _title_fw = "bold" if ss.get("title_bold",  False) else "normal"
    _tick_fw  = "bold" if ss.get("tick_bold",   False) else "normal"

    if axis_settings.get("xl"):    ax.set_xlabel(axis_settings["xl"],    fontsize=ss["label_fs"], fontweight=_lbl_fw)
    if axis_settings.get("yl"):    ax.set_ylabel(axis_settings["yl"],    fontsize=ss["label_fs"], fontweight=_lbl_fw)
    if axis_settings.get("title"): ax.set_title(axis_settings["title"],  fontsize=ss["title_fs"], fontweight=_title_fw)

    ax.tick_params(labelsize=ss["tick_fs"])
    for lbl in ax.get_xticklabels() + ax.get_yticklabels():
        lbl.set_fontweight(_tick_fw)

    def _parse(s):
        try:   return float(s)
        except (ValueError, TypeError): return None

    xmin = _parse(axis_settings.get("xmin"))
    xmax = _parse(axis_settings.get("xmax"))
    ymin = _parse(axis_settings.get("ymin"))
    ymax = _parse(axis_settings.get("ymax"))
    if xmin is not None or xmax is not None: ax.set_xlim(left=xmin, right=xmax)
    if ymin is not None or ymax is not None: ax.set_ylim(bottom=ymin, top=ymax)

    if ss["major_x"] > 0: ax.xaxis.set_major_locator(MultipleLocator(ss["major_x"]))
    if ss["major_y"] > 0: ax.yaxis.set_major_locator(MultipleLocator(ss["major_y"]))
    if ss["minor_x"] > 0: ax.xaxis.set_minor_locator(AutoMinorLocator(ss["minor_x"]))
    if ss["minor_y"] > 0: ax.yaxis.set_minor_locator(AutoMinorLocator(ss["minor_y"]))
    if ss["grid_major"]: ax.grid(True, which="major", alpha=0.35)
    if ss["grid_minor"]: ax.grid(True, which="minor", alpha=0.15, linestyle=":")

    # ---- legend ----
    visible_cfgs = [dw.get_config() for dw in dataset_widgets
                    if dw.get_config()["visible"]]
    all_hist2d = bool(visible_cfgs) and all(c.get("hist2d_mode", False) for c in visible_cfgs)
    has_legend = (
        (any(dw.get_config()["label"] for dw in dataset_widgets) or fit_layers)
        and not all_hist2d
    )
    _, _labels = ax.get_legend_handles_labels()
    has_legend = has_legend and any(_labels)
    if ss.get("legend_show", True) and has_legend:
        leg_kw = dict(
            fontsize=ss["legend_fs"],
            frameon=ss.get("legend_frameon", True),
            ncols=ss.get("legend_ncols", 1),
            handlelength=ss.get("legend_handlelength", 2.0),
        )
        if ss.get("legend_bold", False):
            from matplotlib.font_manager import FontProperties
            leg_kw["prop"] = FontProperties(weight="bold", size=ss["legend_fs"])
        alpha = ss.get("legend_alpha", 1.0)
        leg = ax.legend(loc=ss.get("legend_loc", "best"), **leg_kw)
        if leg:
            leg.get_frame().set_alpha(alpha)
            if legend_pos is not None:
                leg.set_bbox_to_anchor(legend_pos, transform=ax.transAxes)
                leg._loc = 6  # "center left" as anchor reference
            legend = leg

    # ---- text annotations ----
    for ann in annotations:
        txt = ax.text(
            ann["x"], ann["y"], ann["text"],
            transform=ax.transAxes,
            fontsize=ann.get("fontsize", 12),
            color=ann.get("color", "#000000"),
            fontweight="bold" if ann.get("bold", False) else "normal",
            rotation=ann.get("rotation", 0.0),
            clip_on=False,
        )
        annot_artists.append(txt)

    return {
        "legend":        legend,
        "pct_texts":     pct_texts,
        "annot_artists": annot_artists,
    }
