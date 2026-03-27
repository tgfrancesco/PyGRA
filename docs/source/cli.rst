Command-line interface
======================

PyGRA can be launched with files and column settings directly from the terminal.

Basic usage
-----------

.. code-block:: bash

   # open GUI with no files
   pygra

   # load files (shell expands glob patterns)
   pygra *wham_TI.dat

   # same columns for all files
   pygra file1.dat file2.dat --x 0 --y 3

   # per-file column specification
   pygra --file file1.dat --x 0 --y 3 --file file2.dat --x 0 --y 5

   # load a saved session
   pygra --load session.json

   # show help
   pygra --help

Options
-------

.. list-table::
   :widths: 25 55
   :header-rows: 1

   * - Option
     - Description
   * - ``file`` (positional)
     - One or more data files. Shell glob patterns are expanded automatically.
   * - ``-f``, ``--file FILE``
     - Load a data file (alternative to positional, repeatable).
   * - ``--x COL``
     - x column index (0-based) for the preceding ``--file``.
       If given after all files, applies to all. Default: 0.
   * - ``--y COL``
     - y column index (0-based) for the preceding ``--file``.
       If given after all files, applies to all. Default: 1.
   * - ``-l``, ``--load FILE``
     - Load a previously saved session (``.json``).
   * - ``-h``, ``--help``
     - Show help message and exit.

Column assignment rules
-----------------------

- ``--x`` / ``--y`` immediately after ``--file`` apply to that specific file only
- ``--x`` / ``--y`` after all files apply to all of them
- Default columns are x=0, y=1

Examples
--------

.. code-block:: bash

   # two files, different y columns
   pygra --file base.dat --x 0 --y 3 --file unique.dat --x 0 --y 5

   # all matching files, same columns
   pygra *wham_TI.dat --x 0 --y 3

   # resume a previous session
   pygra --load my_analysis.json
