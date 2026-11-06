#!/usr/bin/env python3
"""Shared PyInstaller and installer backend invoked by OS-specific scripts."""
from __future__ import annotations

import argparse
import importlib.util
import platform
import shutil
import subprocess
import sys
import tarfile
from collections.abc import Sequence
from pathlib import Path

from apex.version import (
    EXECUTABLE_BASENAME,
    EXECUTABLE_NAME_WINDOWS,
    PRODUCT_NAME,
    PRODUCT_VERSION,
    RELEASE_VERSION,
)

ROOT = Path(__file__).resolve().parent
INSTALL_RELATIVE_PARTS = ("kastrick's_software", "aac")


def expected_app_path(platform_name: str, root: Path = ROOT) -> Path:
    filename = EXECUTABLE_NAME_WINDOWS if platform_name == "windows" else EXECUTABLE_BASENAME
    return root / "dist" / platform_name / "app" / filename


def windows_install_directory(program_files: Path) -> Path:
    """Return the exact default per-machine Windows install directory."""
    return program_files.joinpath(*INSTALL_RELATIVE_PARTS)


def run(command: Sequence[str], description: str, cwd: Path = ROOT) -> None:
    print(f"[Apex Build] {description}")
    print("[Apex Build] " + subprocess.list2cmdline([str(part) for part in command]))
    subprocess.run([str(part) for part in command], cwd=cwd, check=True)


def build_application(platform_name: str, clean: bool = False) -> Path:
    if importlib.util.find_spec("PyInstaller") is None:
        raise RuntimeError(
            "PyInstaller is not installed. Run: python -m pip install -r requirements.txt"
        )
    if importlib.util.find_spec("pynput") is None:
        raise RuntimeError("pynput is not installed. Run: python -m pip install -r requirements.txt")
    if platform_name == "windows" and platform.architecture()[0] != "64bit":
        raise RuntimeError("The Windows v1.0.0 installers are x64. Use a 64-bit Python interpreter.")

    app_dir = ROOT / "dist" / platform_name / "app"
    app_dir.mkdir(parents=True, exist_ok=True)
    work_dir = ROOT / "build" / "pyinstaller" / platform_name
    spec_dir = ROOT / "build" / "spec"
    work_dir.mkdir(parents=True, exist_ok=True)
    spec_dir.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--name", EXECUTABLE_BASENAME,
        "--distpath", str(app_dir),
        "--workpath", str(work_dir),
        "--specpath", str(spec_dir),
        "--collect-submodules", "apex",
    ]
    if platform_name == "windows":
        command.extend([
            "--windowed",
            "--hidden-import", "pynput.keyboard._win32",
            "--hidden-import", "pynput.mouse._win32",
        ])
    elif sys.platform.startswith("linux"):
        command.extend([
            "--hidden-import", "pynput.keyboard._xorg",
            "--hidden-import", "pynput.mouse._xorg",
        ])
    if clean:
        command.append("--clean")
    command.append(str(ROOT / "apex_autoclicker.py"))
    run(command, f"Building {PRODUCT_NAME} {PRODUCT_VERSION} for {platform_name}.")

    executable = expected_app_path(platform_name)
    if not executable.is_file():
        raise RuntimeError(f"PyInstaller completed but the expected executable is missing: {executable}")
    print(f"[Apex Build] Application artifact: {executable}")
    return executable


def find_inno_compiler() -> str | None:
    candidate = shutil.which("ISCC.exe") or shutil.which("ISCC")
    if candidate:
        return candidate
    for path in (
        Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
        Path(r"C:\Program Files\Inno Setup 6\ISCC.exe"),
    ):
        if path.is_file():
            return str(path)
    return None


def find_wix_cli() -> str | None:
    return shutil.which("wix.exe") or shutil.which("wix")


def build_windows_installers(executable: Path, installer_format: str) -> list[Path]:
    output_dir = ROOT / "dist" / "installers"
    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts: list[Path] = []

    if installer_format in ("exe", "all"):
        iscc = find_inno_compiler()
        if not iscc:
            raise RuntimeError(
                "Inno Setup Compiler (ISCC.exe) is required for the setup .exe. "
                "Install Inno Setup 6 from https://jrsoftware.org/isinfo.php and rerun the build."
            )
        iss = ROOT / "installer" / "windows" / "ApexAutoClicker.iss"
        run([
            iscc,
            f"/DProductVersion={PRODUCT_VERSION}",
            f"/DReleaseVersion={RELEASE_VERSION}",
            f"/DAppExe={executable}",
            str(iss),
        ], "Building the Windows setup .exe with Inno Setup.")
        setup_exe = output_dir / f"Apex-Auto-Clicker-Setup-{RELEASE_VERSION}-x64.exe"
        if not setup_exe.is_file():
            raise RuntimeError(f"Inno Setup completed but the installer is missing: {setup_exe}")
        artifacts.append(setup_exe)

    if installer_format in ("msi", "all"):
        wix = find_wix_cli()
        if not wix:
            raise RuntimeError(
                "WiX Toolset CLI is required for the .msi. Install the .NET SDK and run "
                "'dotnet tool install --global wix', then reopen the terminal."
            )
        wxs = ROOT / "installer" / "windows" / "Product.wxs"
        msi = output_dir / f"Apex-Auto-Clicker-{RELEASE_VERSION}-x64.msi"
        run([
            wix, "build", "-arch", "x64",
            "-d", f"ProductVersion={PRODUCT_VERSION}",
            "-d", f"ReleaseVersion={RELEASE_VERSION}",
            "-d", f"AppExe={executable}",
            "-d", f"LicenseFile={ROOT / 'LICENSE'}",
            "-o", str(msi), str(wxs),
        ], "Building the Windows Installer package (.msi) with WiX Toolset.")
        if not msi.is_file():
            raise RuntimeError(f"WiX completed but the MSI is missing: {msi}")
        artifacts.append(msi)

    return artifacts


def build_linux_archive(executable: Path) -> Path:
    output_dir = ROOT / "dist" / "installers"
    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / f"Apex-Auto-Clicker-{RELEASE_VERSION}-linux-{platform.machine().lower()}.tar.gz"
    with tarfile.open(archive, "w:gz") as bundle:
        bundle.add(executable, arcname=EXECUTABLE_BASENAME)
        for filename in ("LICENSE", "README.md"):
            source = ROOT / filename
            if source.is_file():
                bundle.add(source, arcname=filename)
    print(f"[Apex Build] Linux portable archive: {archive}")
    return archive


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apex shared platform build backend.")
    parser.add_argument("--platform", choices=("windows", "linux"), required=True)
    parser.add_argument("--target", choices=("app", "installers", "all"), default="all")
    parser.add_argument("--installer-format", choices=("exe", "msi", "all"), default="all")
    parser.add_argument("--clean", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        executable = build_application(args.platform, clean=args.clean)
        if args.target in ("installers", "all"):
            artifacts = (
                build_windows_installers(executable, args.installer_format)
                if args.platform == "windows"
                else [build_linux_archive(executable)]
            )
            for artifact in artifacts:
                print(f"[Apex Build] Installer/package artifact: {artifact}")
    except subprocess.CalledProcessError as exc:
        print(f"[Apex Build] External build tool failed with exit code {exc.returncode}.", file=sys.stderr)
        return exc.returncode or 1
    except (OSError, RuntimeError, tarfile.TarError) as exc:
        print(f"[Apex Build] {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
