"""imgpipe — declarative, config-driven image processing pipeline CLI.

Public package marker. Submodules:
    main       — Typer CLI entrypoint and command wiring.
    config     — YAML loading and Pydantic schema for pipeline configs.
    pipeline   — Orchestrates step execution across one or more input files.
    operations — All image operation implementations (crop, resize, color_correct, rotate, flip, blur).
    utils      — File discovery, filename collision resolution, logging helpers.
"""

__version__ = "0.1.0"
