# SRS Draft — Image Pipeline CLI (Revised)

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
| Config validation | Pydantic |

---

## Supported Formats (v1)

- **Input:** JPEG only (`.jpg`, `.jpeg`, case-insensitive). Files with other extensions in the input directory are skipped silently.
- **Output:** JPEG only.
- **No transparency / alpha channels.** Any image whose pixel mode would imply transparency is out of scope; v1 assumes plain RGB JPEGs in, plain RGB JPEGs out.
- **EXIF data is ignored entirely on read and not written on output.** This includes the orientation tag — pixels are processed in their raw stored orientation.
- **ICC color profiles are ignored on read and not written on output.** All processing is treated as plain sRGB-ish RGB; no color management is performed.

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
- `--overwrite` — overwrite existing output files instead of auto-renaming (default: false)
- `--dry-run` — validate config and list files that would be processed, no writes

---

## Config File Format

```yaml
pipeline:
  name: "my-pipeline"       # optional, cosmetic
  output_quality: 90        # optional; 1–100, JPEG quality

  steps:
    - action: crop
      width: 800
      height: 600
      center_x: 960
      center_y: 540

    - action: resize
      width: 1024            # optional if height given
      height: 768            # optional if width given

    - action: color_correct
      property: brightness   # brightness | gamma | temperature | hue | saturation
      value: 1.2

    - action: rotate
      degrees: 90            # must be a multiple of 90; positive = clockwise

    - action: flip
      axis: horizontal       # horizontal | vertical

    - action: blur
      radius: 3              # gaussian blur pixel radius
```

Steps are executed **in order, top to bottom**. The output of each step is the input to the next.

**`steps` must contain at least one entry.** An empty or missing `steps` list is a validation error.

---

## Operations — Detailed Spec

### `crop`
Crops the image to `width` × `height`. The crop window is centered on pixel coordinates (`center_x`, `center_y`). If the crop window extends beyond the image boundary, the app **errors out on that file** (no silent padding — fail loudly).

| Param | Type | Required |
|---|---|---|
| width | int (px) | ✅ |
| height | int (px) | ✅ |
| center_x | int (px) | ✅ |
| center_y | int (px) | ✅ |

### `resize`
Resizes the image. Uses Pillow's `LANCZOS` resampling.

- If both `width` and `height` are given, the image is resized to those exact dimensions (aspect ratio may change).
- If only `width` is given, `height` is computed to preserve the original aspect ratio.
- If only `height` is given, `width` is computed to preserve the original aspect ratio.
- At least one of `width` / `height` must be provided. Neither given → validation error.

| Param | Type | Required |
|---|---|---|
| width | int (px) | one of width/height |
| height | int (px) | one of width/height |

### `color_correct`
Adjusts a single tonal/color property.

| Property | Value semantics | Implementation |
|---|---|---|
| brightness | multiplier (1.0 = original, >1 brighter, <1 darker) | `ImageEnhance.Brightness` |
| saturation | multiplier (1.0 = original, 0 = grayscale) | `ImageEnhance.Color` |
| gamma | multiplier (1.0 = no change, >1 = brighter midtones, <1 = darker midtones). Applied per channel as `output = input ^ (1 / value)` on normalized [0, 1] values. | LUT via `point()` |
| hue | degree offset, −180 to +180 (positive shifts hue clockwise on the color wheel) | shift H channel after `convert('HSV')`, then `convert('RGB')` |
| temperature | integer offset −100 (coolest, more blue) to +100 (warmest, more red/yellow). At ±100, the red and blue channels are scaled by ±30% in opposing directions; intermediate values interpolate linearly. | manual R/B channel scaling |

Note: `exposure` has been removed; it overlapped with `brightness`.

### `rotate`
Rotates clockwise by `degrees`. **Must be a multiple of 90** (positive or negative). Non-multiples of 90 → validation error. Arbitrary-angle rotation is out of scope for v1.

Canvas resizes automatically to fit the rotated image:
- 90° / 270° (and their negatives): dimensions swap (e.g. 600×800 → 800×600).
- 180°: dimensions unchanged.
- 0° / 360°: no-op (allowed but does nothing).

Implementation: `Image.rotate(-degrees, expand=True)` (Pillow rotates counterclockwise by default; negate to make positive = clockwise).

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

- If `--input` is a directory, the app processes all files matching: `*.jpg`, `*.jpeg` (case-insensitive).
- Subdirectories are **not** recursed into (flat scan only).
- Output filenames mirror input filenames (always with `.jpg` extension on output).
- Files are processed sequentially (parallel processing = v2 concern).
- If one file fails, log the error and **continue** processing remaining files; exit code reflects partial failure.

### Output filename collision handling

The app assumes a **case-insensitive filesystem** when checking for collisions, so `Photo.jpg` and `photo.jpg` are treated as the same name.

A collision occurs when:
- An output file with the candidate name already exists on disk, OR
- Another file processed earlier in the same batch already wrote to that name.

**Default behavior (no `--overwrite`):** append `_` characters before the extension until the name is free.
- `photo.jpg` exists → write to `photo_.jpg`
- `photo.jpg` and `photo_.jpg` exist → write to `photo__.jpg`
- …and so on.

**With `--overwrite`:** overwrite the existing file; no renaming.

---

## Error Handling

| Scenario | Behavior |
|---|---|
| Unrecognized `action` in config | Fail at validation, halt before any processing |
| Missing required param | Fail at validation |
| Empty or missing `steps` list | Fail at validation |
| `rotate.degrees` not a multiple of 90 | Fail at validation |
| `resize` with neither `width` nor `height` | Fail at validation |
| Crop window out of bounds | Fail on that file, continue batch |
| Input file unreadable / not a valid JPEG | Fail on that file, continue batch |
| Output dir not writable | Fail immediately, halt all processing |
| Output file already exists, `--overwrite` is false | Auto-rename with trailing `_` before extension |
| Output file already exists, `--overwrite` is true | Overwrite |

---

## Project Structure (suggested)

```
imgpipe/
├── main.py           # Typer app entrypoint
├── config.py         # YAML loading + Pydantic validation
├── pipeline.py       # Orchestrates step execution across files
├── operations.py     # All operation implementations (crop, resize, color_correct, rotate, flip, blur)
└── utils.py          # File discovery, filename collision resolution, logging helpers
```

Operations live in a single file since each implementation is small; if the file grows past a comfortable size in future versions, split it into a package then.

---

## Out of Scope (v1)

- Parallel/async batch processing
- Plugin or custom operation support
- Non-JPEG formats (PNG, SVG, WebP, RAW, TIFF, animated images, etc.)
- Transparency / alpha channels
- EXIF handling of any kind (including orientation auto-correction)
- ICC color profile handling
- Undo / history
- GUI or web interface
- Conditional steps (e.g. "only crop if width > 1000")
- Arbitrary-angle rotation
