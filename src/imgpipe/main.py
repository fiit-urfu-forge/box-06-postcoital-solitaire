"""Typer CLI entrypoint.

Defines the `imgpipe` command-line interface and its subcommands:
    - `imgpipe run`      — load config, scan inputs, run pipeline, write outputs.
    - `imgpipe validate` — load and validate a config without processing any files.

Exposes a module-level `app` (a typer.Typer instance) used as the console-script
entry point declared in pyproject.toml.
"""
