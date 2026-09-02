#!/usr/bin/env python3
"""Skill-local entrypoint. Hosts should call this file, not improvise a search."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
