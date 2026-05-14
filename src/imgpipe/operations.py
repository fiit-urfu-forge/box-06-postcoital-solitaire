"""Image operation implementations.

One function per `action` defined in the spec:
    - crop          — center-anchored crop, errors if window is out of bounds.
    - resize        — LANCZOS resample; one or both of width/height.
    - color_correct — single-property tonal/color adjustment
                      (brightness | saturation | gamma | hue | temperature).
    - rotate        — multiples of 90 only; canvas resizes to fit.
    - flip          — horizontal or vertical mirror.
    - blur          — Gaussian blur by pixel radius.

Each operation takes a Pillow Image plus its already-validated params and
returns a new Image. No I/O happens here.

Kept as a single file for v1; if it grows past a comfortable size, split into
an `operations/` package later.
"""
