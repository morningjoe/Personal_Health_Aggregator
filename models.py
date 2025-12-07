"""Compatibility shim re-exporting models from `tool.models`.

This file preserves the original import path (`models`) for backwards
compatibility while the actual implementation lives in the `tool` package.
"""

from tool.models import *  # noqa: F401,F403

