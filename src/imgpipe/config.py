"""Pipeline config loading and validation.

Responsibilities:
    - Read the YAML config file from disk.
    - Validate it against Pydantic models for each operation type (discriminated
      union on the `action` field).
    - Enforce structural rules from the spec (non-empty `steps`, `rotate.degrees`
      must be a multiple of 90, `resize` requires at least one of width/height,
      etc.).
    - Surface validation errors with enough context (step index, key) to be
      actionable for the user.
"""
