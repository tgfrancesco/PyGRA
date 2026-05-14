"""PyGRA — interactive scientific data plotter"""

from .dataset import DataSet, apply_transform  # noqa: F401
from .widgets import DatasetWidget  # noqa: F401
from .dialogs import StyleDialog, TransformDialog, StatsDialog  # noqa: F401
from .mainwindow import MainWindow  # noqa: F401
from .state import save_state, load_state  # noqa: F401
from .main import main  # noqa: F401
from .preferences import load_prefs, save_prefs  # noqa: F401

__version__ = "0.8.2"
__author__ = "Francesco Tosti Guerra"
