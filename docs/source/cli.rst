Command-line interface
======================

PyGRA can be launched with files and column settings directly from the terminal.

Basic usage
-----------

.. code-block:: bash

   # open GUI with no files
   pygra

   # load files (shell expands glob patterns)
   pygra *file*.dat

   # same columns for all files
   pygra file1.dat file2.dat --x 0 --y 3

   # per-file column specification
   pygra --file file1.dat --x 0 --y 3 --file file2.dat --x 0 --y 5

   # specify error bars
   pygra --file data.dat --x 0 --y 1 --dx 2 --dy 3

   # load every 100th row (useful for very large files)
   pygra idx_*.csv --x 3 --y 4 --downsampling 100

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
   * - ``--dx COL``
     - x error bar column index (0-based) for the preceding ``--file``.
       If given after all files, applies to all. Default: none.
   * - ``--dy COL``
     - y error bar column index (0-based) for the preceding ``--file``.
       If given after all files, applies to all. Default: none.
   * - ``-s``, ``--downsampling N``
     - Load every N-th row from all files. Useful for very large files.
       Default: 1 (no downsampling).
   * - ``-l``, ``--load FILE``
     - Load a previously saved session (``.json``).
   * - ``-h``, ``--help``
     - Show help message and exit.

Column assignment rules
-----------------------

- ``--x`` / ``--y`` / ``--dx`` / ``--dy`` immediately after ``--file`` apply to that specific file only
- ``--x`` / ``--y`` / ``--dx`` / ``--dy`` after all files apply to all of them
- Default columns: x=0, y=1, dx=0 (none), dy=0 (none)

Examples
--------

.. code-block:: bash

   # two files, different y columns
   pygra --file file1.dat --x 0 --y 3 --file file2.dat --x 0 --y 5

   # all matching files, same columns and error bars
   pygra *file*.dat --x 0 --y 1 --dy 2

   # large CSV files, load every 50th row
   pygra idx_*.csv --x 3 --y 4 -s 50

   # resume a previous session
   pygra --load my_analysis.json
