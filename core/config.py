"""Pipeline mode switch shared by the pipeline and the validators.

Lives in its own module so `core.validation` can read the mode without
importing `core.pipeline` (which imports the validators).
"""

import os

MOCK_FALSE_VALUES = {"0", "false", "no", "off", "n", "disabled"}


def mock_enabled() -> bool:
    """Return True unless MOCK explicitly disables the deterministic pipeline."""
    return os.getenv("MOCK", "1").strip().lower() not in MOCK_FALSE_VALUES


def max_input_chars() -> int:
    """Cap on raw text handed to core entrypoints (mirrors api/web's limit).

    core has no import on api's settings, so it reads the same env var
    directly -- input limits are enforced here too, not just at the api
    layer, since core must be safe called directly (evals, future callers).
    """
    return int(os.getenv("MAX_TEXT_CHARS", "50000"))
