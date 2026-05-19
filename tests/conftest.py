"""Shared pytest configuration for the ``tests/`` package."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_BACKEND_PARENT = _REPO_ROOT / "packaging"
# The in-tree PEP 517 backend lives outside the installed package, so make it
# importable for ``tests/test_pep517_backend.py``. Done here rather than via a
# per-test ``sys.path.insert`` so the modification has a single, discoverable
# home.
if str(_BACKEND_PARENT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_PARENT))
