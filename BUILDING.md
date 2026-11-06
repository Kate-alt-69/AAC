# Building Apex

## Version identifiers

`apex/version.py` is the authoritative version source:

- `PRODUCT_VERSION = "1.1"` — version displayed by the application.
- `RELEASE_VERSION = "1.0.0"` and `RELEASE_TAG = "v1.0.0"` — first distributable release.
- `MACRO_SCHEMA_VERSION = "11.0"` — serialized macro format; do not bump this for ordinary application releases.

## Build commands

Run from the repository root:

```bash
python build.py --target all
```

`build.py` runs the unit tests first, selects the current OS script, and returns
the native script's exit code. Use `--skip-tests` only when intentionally
skipping the test gate.

Targets:

- `app`: package the application only.
- `installers`: package the app and create platform installer/archive output.
- `all`: same as `installers` (default).

Windows accepts `--installer-format exe`, `msi`, or `all`. Linux produces a
portable tarball; it does not produce Windows installer formats.

## Windows

The build is x64 and uses:

1. PyInstaller to produce `dist/windows/app/apex-autoclicker.exe`.
2. Inno Setup 6 (`ISCC.exe`) to produce the guided setup executable.
3. WiX Toolset CLI (`wix`) to produce the MSI package.

Install Python dependencies first:

```powershell
py -3 -m pip install -r requirements.txt
```

Install the external installer tools separately. Inno Setup is available from
https://jrsoftware.org/isinfo.php. WiX can be installed through the .NET SDK:

```powershell
dotnet tool install --global wix
```

Close and reopen the terminal after installing a global .NET tool so its tool
path is refreshed. The build reports a clear missing-tool error and does not
claim that an installer was produced when its compiler is unavailable.

Before distributing installers commercially, review the current terms of both
build tools: Inno Setup asks commercial users to purchase a commercial license,
and WiX v6 documents an Open Source Maintenance Fee for revenue-generating use.
These are build-time tools and are not bundled into the Apex installer. Check the
current vendor terms for your exact use case:

- https://jrsoftware.org/ishelp/topic_whatisinnosetup.htm
- https://docs.firegiant.com/wix/whatsnew/releasenotes/

Default installation directory for both Windows installer formats:

```text
{ProgramFiles}\kastrick's_software\aac\apex-autoclicker.exe
```

This is a per-machine installation and requires elevation. User-created macro
files and settings should remain in the user's profile, not beside the Program
Files executable.

## Linux

Install the project dependencies with the platform's package manager and pip,
then run:

```bash
python3 -m pip install -r requirements.txt
python3 build.py --target all
```

The output is a standalone executable plus a portable `.tar.gz` archive. Native
X11/Wayland input permissions and capture APIs are a separate runtime
compatibility concern and are not inferred from a successful package build.

## Build output and cleanup

- `build/` contains PyInstaller intermediate files.
- `dist/` contains application and installer artifacts.
- Both directories are ignored by Git.
- `--clean` asks PyInstaller to clean its cache before building; it does not
  delete unrelated project files.

## Troubleshooting

- `PyInstaller is not installed`: run `python -m pip install -r requirements.txt`.
- `ISCC.exe` missing: install Inno Setup 6 and ensure its compiler is on PATH
  (the build also checks its common Program Files locations).
- `wix` missing: install the .NET SDK, install the global WiX tool, then reopen
  the terminal.
- MSI or setup EXE missing after compilation: the backend treats this as a
  failed build rather than reporting success.


## Automated checks and repository security

The repository workflows live under `.github/workflows/`:

- `quality.yml` compiles the maintained Python package/entry points, runs the
  unit tests and Ruff checks on Windows and Linux, and builds the Windows
  application plus both installer formats.
- `codeql.yml` runs CodeQL security analysis for Python on pull requests,
  pushes to `master`, and a weekly schedule.
- `dependency-review.yml` checks dependency manifest changes in pull requests. It requires GitHub's Dependency Graph to be enabled under repository Settings → Security and quality → Advanced Security.
- `.github/dependabot.yml` schedules weekly updates for pip requirements and
  GitHub Actions dependencies.

These workflows provide CI quality checks and CodeQL code scanning. They do
not enable repository-level Dependabot alerting, secret-scanning alerts, or
push protection; review those controls under the repository's **Settings →
Security and quality → Advanced Security** page.

GitHub Code Quality is a separate paid product, not the same thing as a
repository-defined CI workflow. Its current availability and billing are
described in GitHub's [Code Quality documentation](https://docs.github.com/en/code-security/how-tos/maintain-quality-code/enable-code-quality).
