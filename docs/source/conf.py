# Configuration file for the Sphinx documentation builder.
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------
import os
import sys
sys.path.insert(0, os.path.abspath('../..'))  # points to PyGRA/ root

# -- Project information -----------------------------------------------------
project = 'PyGRA'
copyright = '2026, Francesco Tosti Guerra'
author = 'Francesco Tosti Guerra'
release = '0.5.1'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',    # reads docstrings automatically
    'sphinx.ext.napoleon',   # supports NumPy/Google docstring style
    'sphinx.ext.viewcode',   # adds links to source code
    'sphinx.ext.autosummary',
]

# Napoleon settings (NumPy style)
napoleon_numpy_docstring = True
napoleon_google_docstring = False
napoleon_include_init_with_doc = True

# Autodoc settings
autodoc_member_order = 'bysource'
autodoc_typehints = 'description'

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

html_theme_options = {
    'navigation_depth': 3,
    'titles_only': False,
}
