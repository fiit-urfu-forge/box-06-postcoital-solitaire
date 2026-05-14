"""Pipeline orchestration.

Drives the end-to-end batch run:
    - Resolves the input path (single file vs. directory scan via utils).
    - For each input file: opens it as a Pillow Image, applies each configured
      step in order by dispatching to operations.py, and writes the result to
      the output directory.
    - Handles per-file failures (log + continue) vs. fatal failures (halt).
    - Coordinates filename collision resolution and the `--overwrite` flag.
    - Tracks success/failure counts to drive the final exit code.
"""
