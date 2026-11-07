#!/usr/bin/env python3
"""Cross-platform entry point for Apex application and installer builds.

This script runs the native build wrapper for the current operating system.
The wrappers delegate to build_backend.py so build logic remains shared.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def get_platform_script(platform_name: str, root: Path = ROOT) -> Path:
    """Return the native build script for a Python platform identifier."""
    if platform_name.startswith("win"):
        ps1 = root / "scripts" / "build_windows.ps1"
        bat = root / "scripts" / "build_windows.bat"
        powershell_available = shutil.which("pwsh") or shutil.which("powershell")
        if powershell_available and ps1.is_file():
            return ps1
        return bat
    if platform_name.startswith("linux"):
        return root / "scripts" / "build_linux.sh"
    raise RuntimeError(
        f"No native build script is configured for platform '{platform_name}'. "
        "This release currently supports Windows and Linux build hosts."
    )


def build_script_command(
    platform_name: str,
    script: Path,
    target: str,
    installer_format: str,
    clean: bool = False,
) -> list[str]:
    """Construct a shell-safe command for the selected native script."""
    common = ["--target", target, "--installer-format", installer_format]
    if clean:
        common.append("--clean")

    if platform_name.startswith("win"):
        powershell = shutil.which("pwsh") or shutil.which("powershell")
        if script.suffix.lower() == ".ps1":
            if not powershell:
                raise RuntimeError("PowerShell was not found. Install PowerShell or use scripts/build_windows.bat.")
            return [
                powershell,
                "-NoLogo",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script),
                "-Target",
                target,
                "-InstallerFormat",
                installer_format,
                *( ["-Clean"] if clean else [] ),
            ]
        cmd = shutil.which("cmd.exe") or shutil.which("cmd")
        if not cmd:
            raise RuntimeError("cmd.exe was not found; cannot run the Windows batch build script.")
        return [cmd, "/c", str(script), *common]

    bash = shutil.which("bash")
    if not bash:
        raise RuntimeError("bash was not found; install Bash to run scripts/build_linux.sh.")
    return [bash, str(script), *common]


def run_tests() -> None:
    command = [sys.executable, "-m", "unittest", "discover", "-s", "apex/tests", "-v"]
    print("[Apex Build] Running project tests...")
    subprocess.run(command, cwd=ROOT, check=True)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Apex Auto-Clicker and its platform installers.")
    parser.add_argument("--target", choices=("app", "installers", "all"), default="all",
                        help="Build only the app, installers (including the app), or everything (default: all).")
    parser.add_argument("--installer-format", choices=("exe", "msi", "all"), default="all",
                        help="Windows installer formats to create (default: both .exe and .msi).")
    parser.add_argument("--clean", action="store_true", help="Ask PyInstaller to clean its build cache first.")
    parser.add_argument("--skip-tests", action="store_true", help="Skip the unit test suite before building.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if not args.skip_tests:
            run_tests()
        script = get_platform_script(sys.platform)
        if not script.is_file():
            raise RuntimeError(f"The platform build script is missing: {script}")
        command = build_script_command(
            sys.platform, script, args.target, args.installer_format, args.clean
        )
        print(f"[Apex Build] Platform: {sys.platform}")
        print(f"[Apex Build] Script: {script.relative_to(ROOT)}")
        print(f"[Apex Build] Target: {args.target}")
        child_env = os.environ.copy()
        child_env["APEX_PYTHON"] = sys.executable
        subprocess.run(command, cwd=ROOT, env=child_env, check=True)
    except subprocess.CalledProcessError as exc:
        print(f"[Apex Build] Build command failed with exit code {exc.returncode}.", file=sys.stderr)
        return exc.returncode or 1
    except (OSError, RuntimeError) as exc:
        print(f"[Apex Build] {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
