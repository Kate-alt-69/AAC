#!/usr/bin/env python3
"""Backward-compatible alias for the cross-platform build entry point."""
from build import main


if __name__ == "__main__":
    raise SystemExit(main())
