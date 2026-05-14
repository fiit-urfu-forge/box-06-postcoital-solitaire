"""Shared helpers used across the CLI, pipeline, and operations.

Includes:
    - Input file discovery: scan a directory (flat, non-recursive) for files
      with case-insensitive .jpg / .jpeg extensions, or accept a single file.
    - Output filename collision resolution: case-insensitive name comparison
      against existing files (on disk and within the current batch), appending
      `_` characters before the extension until the name is free.
    - Logging setup (per-file progress, errors, warnings).
"""
