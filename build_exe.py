#!/usr/bin/env python3
"""Backward-compatible alias for the cross-platform build entry point."""
from build import main


def build_executable() -> int:
    """Retain the original callable while delegating to the general build."""
    return main(["--target", "all"])


if __name__ == "__main__":
    raise SystemExit(main())
