"""
dialogs.py — compatibility shim

All dialog classes and helpers live in the submodules:
  dialogs_style.py    — color palette helpers, StyleDialog, AppearanceDialog,
                        HistAppearanceDialog, Hist2DAppearanceDialog
  dialogs_analysis.py — FitDialog, TransformDialog, StatsDialog, DataEditorDialog
  dialogs_misc.py     — TextAnnotationDialog, PaletteDialog
"""

from .dialogs_style import *
from .dialogs_analysis import *
from .dialogs_misc import *
