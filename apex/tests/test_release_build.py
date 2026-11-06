import shutil
import unittest
from pathlib import Path, PureWindowsPath

import build
from apex import __version__
from apex.version import (
    MACRO_SCHEMA_VERSION,
    PRODUCT_VERSION,
    RELEASE_TAG,
    RELEASE_VERSION,
)
from build_backend import expected_app_path, windows_install_directory


class TestReleaseBuildMetadata(unittest.TestCase):
    def test_product_and_release_versions_are_separate_from_macro_schema(self):
        self.assertEqual(__version__, "1.1")
        self.assertEqual(PRODUCT_VERSION, "1.1")
        self.assertEqual(RELEASE_VERSION, "1.0.0")
        self.assertEqual(RELEASE_TAG, "v1.0.0")
        self.assertEqual(MACRO_SCHEMA_VERSION, "11.0")

    def test_windows_install_directory_matches_requested_layout(self):
        path = windows_install_directory(PureWindowsPath(r"C:\Program Files"))
        self.assertEqual(str(path), r"C:\Program Files\kastrick's_software\aac")

    def test_platform_app_artifact_names(self):
        root = Path("/repo")
        self.assertEqual(
            expected_app_path("windows", root),
            root / "dist/windows/app/apex-autoclicker.exe",
        )
        self.assertEqual(
            expected_app_path("linux", root),
            root / "dist/linux/app/apex-autoclicker",
        )

    def test_installer_definitions_use_the_requested_install_layout(self):
        root = Path(__file__).resolve().parents[2]
        inno_script = (root / "installer" / "windows" / "ApexAutoClicker.iss").read_text(encoding="utf-8")
        wix_script = (root / "installer" / "windows" / "Product.wxs").read_text(encoding="utf-8")

        self.assertIn(r"DefaultDirName={autopf}\kastrick's_software\aac", inno_script)
        self.assertIn(r"OutputDir=..\..\dist\installers", inno_script)
        self.assertIn('Name="kastrick\'s_software"', wix_script)
        self.assertIn('Name="aac"', wix_script)
        self.assertIn('Version="$(var.ProductVersion).0"', wix_script)

    def test_platform_build_script_selection(self):
        root = Path("/repo")
        expected_windows = (
            "build_windows.ps1"
            if (shutil.which("pwsh") or shutil.which("powershell"))
            else "build_windows.bat"
        )
        self.assertEqual(
            build.get_platform_script("win32", root),
            root / "scripts" / expected_windows,
        )
        self.assertEqual(
            build.get_platform_script("linux", root),
            root / "scripts/build_linux.sh",
        )


if __name__ == "__main__":
    unittest.main()
