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
dotnet tool install --global wix --version 6.0.2
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


### WiX Toolset licensing note

The MSI build is pinned to WiX Toolset **6.0.2** rather than installing the
latest major release automatically. WiX v6 introduced the Open Source
Maintenance Fee (OSMF); the published terms require sponsorship for
revenue-generating users above the stated annual-revenue threshold. WiX v7
adds an explicit EULA-acceptance gate, so CI must not silently accept it.
Review the current [WiX OSMF terms](https://docs.firegiant.com/wix/osmf/) before
using WiX to build or distribute revenue-generating products. To use WiX v7,
review and accept its EULA explicitly under the applicable terms first.


## Target-window input and virtual cursor behavior

Apex locks a Windows target by its top-level HWND plus process/thread identity,
and stores interactions in the target's client coordinate space. The session
revalidates that identity before dispatch so a closed/reused HWND cannot silently
receive later events.

The virtual cursor is **visual feedback only**. It draws a bounded cursor and
interaction indicators; it does not itself deliver mouse or keyboard input.

The runtime selects an input route for every locked target:

- **Target HWND messages** are queued to the locked target window or an
  eligible child control without moving the physical desktop cursor. This is
  the same target-session backend for every compatible selected application;
  it is not a Roblox-specific path. Every recipient HWND is checked to ensure
  it belongs to the captured top-level target.
- Mouse-down pins that button to the child HWND that received it. Movement and
  mouse-up remain on that child even when the pointer crosses another child
  control. Key-down records its focused child HWND, scan code, and extended-key
  state; key-up returns to that same child. Scroll targets the child under the
  virtual pointer. Cancellation attempts to release all buttons and keys still
  owned by the session.
- This is still a best-effort message-driven Win32 route. A successful
  `PostMessageW` call confirms only that Windows queued a message; it does not
  confirm that the application processed it. Apps using Raw Input, DirectInput,
  custom render/input loops, or some modern window frameworks may ignore these
  messages. A target HWND being validated does not force its app to accept a
  synthetic message.
- **Foreground SendInput** is used for game clients (including Roblox),
  Raw Input-style apps, browsers without a connected browser-protocol adapter,
  and other foreground-only targets. This fallback is not window-isolated:
  Apex asks for approval, activates the locked target, and checks the target
  before each input call. `SendInput` enters the shared desktop input stream,
  so the physical mouse/keyboard are not independently available during those
  actions. Switching focus stops playback rather than sending input to the
  newly focused application.

This is a target-window-first design, not arbitrary DLL injection. Apex does not
inject code into other processes or bypass game anti-cheat systems. True
background input for an arbitrary custom-rendered application requires that
application to expose a supported automation interface or an Apex Bridge
integration.

The Windows CI suite verifies the routing logic, press ownership, cleanup
behavior, and builds the application/installers. Its input tests use a fake
target session; they do not launch Notepad, Firefox, or Roblox. Manual
interactive validation on Windows is still needed for each application
profile. In particular, the current Roblox client remains a foreground/shared
input route: a visual cursor overlay is not a second hardware cursor, and
ordinary external Win32 messages cannot be assumed to drive Roblox's own input
pipeline. True background input for a custom-rendered/Raw Input application
requires an application-supported bridge or a separately designed integration;
Apex must report that limitation instead of claiming the input is isolated.
