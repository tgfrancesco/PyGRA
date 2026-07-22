"""
fitting.py — fit functions for histogram and xy data
"""

import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import norm, expon, maxwell, poisson


def fit_gaussian(data: np.ndarray):
    """
    Fit a Gaussian (normal) distribution to *data* using MLE.

    Parameters
    ----------
    data : numpy.ndarray
        1-D array of sample values.

    Returns
    -------
    x : numpy.ndarray
        300 evenly-spaced points spanning ``[data.min(), data.max()]``.
    y : numpy.ndarray
        Gaussian PDF evaluated at each point in *x*.
    label : str
        Human-readable label including the fitted μ and σ.
    params : dict
        ``{"μ": float, "σ": float}`` — fitted mean and standard deviation.
    """
    mu, sigma = norm.fit(data)
    x = np.linspace(data.min(), data.max(), 300)
    y = norm.pdf(x, mu, sigma)
    label = f"Gaussian  μ={mu:.4g}  σ={sigma:.4g}"
    return x, y, label, {"μ": mu, "σ": sigma}


def fit_exponential(data: np.ndarray):
    """
    Fit an exponential distribution to *data* with fixed location (loc=0).

    Parameters
    ----------
    data : numpy.ndarray
        1-D array of non-negative sample values.

    Returns
    -------
    x : numpy.ndarray
        300 evenly-spaced points spanning ``[data.min(), data.max()]``.
    y : numpy.ndarray
        Exponential PDF evaluated at each point in *x*.
    label : str
        Human-readable label including the fitted rate λ.
    params : dict
        ``{"λ": float}`` — fitted rate parameter (1 / scale).
    """
    loc, scale = expon.fit(data, floc=0)
    x = np.linspace(data.min(), data.max(), 300)
    y = expon.pdf(x, loc=loc, scale=scale)
    lam = 1.0 / scale
    label = f"Exponential  λ={lam:.4g}"
    return x, y, label, {"λ": lam}


def fit_maxwell_boltzmann(data: np.ndarray):
    """
    Fit a Maxwell-Boltzmann distribution to *data* with fixed location (loc=0).

    Parameters
    ----------
    data : numpy.ndarray
        1-D array of positive sample values.

    Returns
    -------
    x : numpy.ndarray
        300 evenly-spaced points spanning
        ``[max(data.min(), 0), data.max()]``.
    y : numpy.ndarray
        Maxwell-Boltzmann PDF evaluated at each point in *x*.
    label : str
        Human-readable label including the fitted scale parameter *a*.
    params : dict
        ``{"a": float}`` — fitted scale parameter.
    """
    loc, scale = maxwell.fit(data, floc=0)
    x = np.linspace(max(data.min(), 0), data.max(), 300)
    y = maxwell.pdf(x, loc=loc, scale=scale)
    label = f"Maxwell-Boltzmann  a={scale:.4g}"
    return x, y, label, {"a": scale}


def fit_poisson(data: np.ndarray):
    """
    Estimate the Poisson parameter μ from *data* and compute the PMF.

    The estimator is the sample mean, which is the MLE for the Poisson
    distribution.

    Parameters
    ----------
    data : numpy.ndarray
        1-D array of non-negative integer-valued samples (stored as float).

    Returns
    -------
    x : numpy.ndarray
        Integer x-values from ``int(data.min())`` to ``int(data.max())``
        inclusive, cast to float.
    y : numpy.ndarray
        Poisson PMF values at each integer in *x*.
    label : str
        Human-readable label including the estimated μ.
    params : dict
        ``{"μ": float}`` — estimated mean (sample mean of *data*).
    """
    mu = data.mean()
    x_int = np.arange(int(data.min()), int(data.max()) + 1)
    y = poisson.pmf(x_int, mu)
    label = f"Poisson  μ={mu:.4g}"
    return x_int.astype(float), y, label, {"μ": mu}


def fit_gaussian_curve(x: np.ndarray, y: np.ndarray):
    """
    Fit A * exp(-(x - mu)**2 / (2 * sigma**2)) to xy data.

    Parameters
    ----------
    x : numpy.ndarray
        1-D array of x values.
    y : numpy.ndarray
        1-D array of y values.

    Returns
    -------
    x_fine : numpy.ndarray
        300 evenly-spaced points spanning ``[x.min(), x.max()]``.
    y_fine : numpy.ndarray
        Fitted curve evaluated at each point in *x_fine*.
    label : str
        Human-readable label including the fitted parameters.
    params : dict
        ``{"A": float, "μ": float, "σ": float}``.
    """
    A0    = float(np.max(y))
    mu0   = float(x[np.argmax(y)])
    sig0  = float(np.std(x)) or 1.0

    def model(x_, A, mu, sigma):
        return A * np.exp(-(x_ - mu) ** 2 / (2 * sigma ** 2))

    popt, _ = curve_fit(model, x, y, p0=[A0, mu0, sig0], maxfev=10000)
    A, mu, sigma = popt
    x_fine = np.linspace(x.min(), x.max(), 300)
    y_fine = model(x_fine, *popt)
    label = f"Gaussian curve  A={A:.4g}  μ={mu:.4g}  σ={sigma:.4g}"
    return x_fine, y_fine, label, {"A": A, "μ": mu, "σ": sigma}


def fit_exponential_curve(x: np.ndarray, y: np.ndarray):
    """
    Fit A * exp(-x / tau) + C to xy data.

    Parameters
    ----------
    x : numpy.ndarray
        1-D array of x values.
    y : numpy.ndarray
        1-D array of y values.

    Returns
    -------
    x_fine : numpy.ndarray
        300 evenly-spaced points spanning ``[x.min(), x.max()]``.
    y_fine : numpy.ndarray
        Fitted curve evaluated at each point in *x_fine*.
    label : str
        Human-readable label including the fitted parameters.
    params : dict
        ``{"A": float, "τ": float, "C": float}``.
    """
    C0   = float(np.min(y))
    A0   = float(np.max(y) - C0)
    x_range = float(x.max() - x.min())
    tau0 = x_range / 3.0 if x_range > 0 else 1.0

    def model(x_, A, tau, C):
        return A * np.exp(-x_ / tau) + C

    popt, _ = curve_fit(model, x, y, p0=[A0, tau0, C0], maxfev=10000)
    A, tau, C = popt
    x_fine = np.linspace(x.min(), x.max(), 300)
    y_fine = model(x_fine, *popt)
    label = f"Exponential curve  A={A:.4g}  τ={tau:.4g}  C={C:.4g}"
    return x_fine, y_fine, label, {"A": A, "τ": tau, "C": C}


def fit_custom(x_or_data, y_or_none, formula, param_names, p0=None):
    """
    Fit a user-defined formula to xy data or to a density histogram.

    The formula is evaluated in a sandboxed namespace that exposes NumPy
    ufuncs (e.g. ``exp``, ``sin``, ``sqrt``) and math constants.  NumPy
    ufuncs take priority over their scalar ``math`` counterparts so that
    array formulas work correctly.

    Parameters
    ----------
    x_or_data : numpy.ndarray
        In xy mode (``y_or_none`` is not ``None``): x coordinates.
        In histogram mode (``y_or_none`` is ``None``): 1-D sample values
        from which a density histogram is built.
    y_or_none : numpy.ndarray or None
        y coordinates for xy mode, or ``None`` to enable histogram mode.
    formula : str
        Python expression in terms of ``x`` and the names listed in
        *param_names*.  Example: ``"a * exp(-b * x)"``.
    param_names : list of str
        Names of the free parameters appearing in *formula*.
    p0 : list of float, optional
        Initial parameter guesses.  When ``None`` (default), each
        parameter is initialised to ``mean(|y|)`` (xy mode) or
        ``mean(|histogram counts|)`` (histogram mode).

    Returns
    -------
    x : numpy.ndarray
        300 evenly-spaced points spanning the input x range.
    y : numpy.ndarray
        Formula evaluated at *x* with the optimised parameters.
    label : str
        Human-readable label listing each fitted parameter value.
    params : dict
        Mapping of parameter name → fitted float value.

    Raises
    ------
    scipy.optimize.OptimizeWarning
        If the covariance of the parameters could not be estimated.
    RuntimeError
        If the least-squares minimisation fails entirely.
    """
    import math
    safe_ns = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
    safe_ns.update({k: getattr(np, k) for k in dir(np) if not k.startswith("_")})

    def model(x, *params):
        ns = dict(safe_ns)
        ns["x"] = x
        for name, val in zip(param_names, params):
            ns[name] = val
        return eval(formula, {"__builtins__": {}}, ns)

    if y_or_none is not None:
        x_fit = x_or_data
        y_fit = y_or_none
        if p0 is None:
            scale = float(np.mean(np.abs(y_fit))) or 1.0
            p0 = [scale] * len(param_names)
    else:
        counts, edges = np.histogram(x_or_data, bins="auto", density=True)
        x_fit = 0.5 * (edges[:-1] + edges[1:])
        y_fit = counts
        if p0 is None:
            scale = float(np.mean(np.abs(counts)))
            p0 = [scale] * len(param_names)

    popt, _ = curve_fit(
        model, x_fit, y_fit, p0=p0,
        bounds=(-np.inf, np.inf), maxfev=10000,
    )
    x_fine = np.linspace(x_or_data.min(), x_or_data.max(), 300)
    y_fine = model(x_fine, *popt)
    params_dict = {n: v for n, v in zip(param_names, popt)}
    label = "Custom  " + "  ".join(f"{n}={v:.4g}" for n, v in params_dict.items())
    return x_fine, y_fine, label, params_dict


# Registry mapping fit-method names (as they appear in FitDialog) to the
# corresponding fit function.  Each function accepts a 1-D NumPy array and
# returns ``(x, y, label, params_dict)``.  Only distribution fits are
# included here; spline, polynomial, linear, and custom fits are handled
# separately in mainwindow because they operate on xy data, not histograms.
FIT_FUNCTIONS = {
    "Gaussian (distribution)":          fit_gaussian,
    "Exponential (distribution)":       fit_exponential,
    "Maxwell-Boltzmann (distribution)": fit_maxwell_boltzmann,
    "Poisson (distribution)":           fit_poisson,
}
