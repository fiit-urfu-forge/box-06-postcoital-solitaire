# SRS Draft — Image Pipeline CLI

## Overview

A Python CLI tool that applies a deterministic, declarative sequence of image processing operations to one or more images, driven by a YAML config file. Think "Dockerfile for image editing."

---

## Goals

- Reproducible, config-driven image transformations
- Batch processing across multiple input files
- No GUI, no interactivity — pure CLI + config
- Simple enough that a config file is human-readable and writable by hand

---

## Tech Stack

| Concern | Choice |
|---|---|
| Language | Python 3.10+ |
| CLI parsing | Typer |
| Image processing | Pillow |
| Config format | YAML |

---

## CLI Interface

```bash
imgpipe run --config pipeline.yaml --input ./images/ --output ./out/
imgpipe run --config pipeline.yaml --input photo.jpg  # output defaults to ./out/
imgpipe validate --config pipeline.yaml              # dry-run, checks config validity
```

**Flags:**

- `--config` / `-c` — path to YAML pipeline file (required)
- `--input` / `-i` — path to a single image file or a directory (required)
- `--output` / `-o` — output directory (default: `./out/`, created if missing)
- `--overwrite` — allow overwriting existing output files (default: false)
- `--dry-run` — validate config and list files that would be processed, no writes

---

## Config File Format

```yaml
pipeline:
  name: "my-pipeline"       # optional, cosmetic
  output_format: jpeg       # optional; jpeg | png | webp; defaults to input format
  output_quality: 90        # optional; 1–100, applies to lossy formats

  steps:
    - action: crop
      width: 800
      height: 600
      center_x: 960
      center_y: 540

    - action: color_correct
      property: brightness   # brightness | gamma | temperature | hue | saturation | exposure
      value: 1.2             # multiplier or absolute depending on property (see below)

    - action: rotate
      degrees: 90            # must be a multiple of 90; positive = clockwise

    - action: flip
      axis: horizontal       # horizontal | vertical

    - action: blur
      radius: 3              # gaussian blur pixel radius
```

Steps are executed **in order, top to bottom**. The output of each step is the input to the next.

---

## Operations — Detailed Spec

### `crop`
Crops the image to `width` × `height`. The crop window is centered on pixel coordinates (`center_x`, `center_y`). If the crop window extends beyond the image boundary, the app **errors out** (no silent padding — fail loudly).

| Param | Type | Required |
|---|---|---|
| width | int (px) | ✅ |
| height | int (px) | ✅ |
| center_x | int (px) | ✅ |
| center_y | int (px) | ✅ |

### `color_correct`
Adjusts a single tonal/color property. All values are **multipliers** (1.0 = no change) except where noted.

| Property | Value semantics | Pillow mechanism |
|---|---|---|
| brightness | multiplier (1.0 = original) | `ImageEnhance.Brightness` |
| saturation | multiplier | `ImageEnhance.Color` |
| gamma | multiplier (applied as 1/γ curve) | manual LUT via `point()` |
| hue | degree offset, –180 to +180 | HSV shift via `ImageColor` + `convert()` |
| temperature | offset –100 (cool) to +100 (warm) | manual R/B channel curve |
| exposure | EV offset (0 = no change, +1 = 2× brighter) | manual curve via `point()` |

### `rotate`
Rotates clockwise by `degrees`. Must be a multiple of 90. Uses `Image.rotate()` with `expand=True` so canvas resizes to fit (no cropping corners). Non-multiple-of-90 values → validation error.

| Param | Type | Required |
|---|---|---|
| degrees | int | ✅ |

### `flip`
Mirrors the image along the specified axis.

| `axis` value | Pillow op |
|---|---|
| `horizontal` | `Image.FLIP_LEFT_RIGHT` |
| `vertical` | `Image.FLIP_TOP_BOTTOM` |

### `blur`
Applies Gaussian blur. `radius` maps directly to `ImageFilter.GaussianBlur(radius=R)`.

| Param | Type | Required |
|---|---|---|
| radius | int or float | ✅ |

---

## Batch Processing Behavior

- If `--input` is a directory, the app processes all files matching: `*.jpg`, `*.jpeg`, `*.png`, `*.webp` (case-insensitive)
- Subdirectories are **not** recursed into (flat scan only) — keep it simple for v1
- Output filenames mirror input filenames; output format extension is rewritten if `output_format` is set
- Files are processed sequentially (parallel processing = v2 concern)
- If one file fails, log the error and **continue** processing remaining files; exit code reflects partial failure

---

## Error Handling

| Scenario | Behavior |
|---|---|
| Unrecognized `action` in config | Fail at validation, halt before any processing |
| Missing required param | Fail at validation |
| Crop window out of bounds | Fail on that file, continue batch |
| Input file unreadable / not an image | Fail on that file, continue batch |
| Output dir not writable | Fail immediately, halt all processing |
| `--overwrite` is false and output exists | Skip that file, emit a warning |

---

## Project Structure (suggested)

```
imgpipe/
├── main.py           # Typer app entrypoint
├── config.py         # YAML loading + Pydantic/dataclass validation
├── pipeline.py       # Orchestrates step execution across files
├── operations/
│   ├── crop.py
│   ├── color_correct.py
│   ├── rotate.py
│   ├── flip.py
│   └── blur.py
└── utils.py          # File discovery, logging helpers
```

---

## Out of Scope (v1)

- Parallel/async batch processing
- Plugin or custom operation support
- Non-raster formats (SVG, RAW, TIFF with layers)
- Undo / history
- GUI or web interface
- Conditional steps (e.g. "only crop if width > 1000")