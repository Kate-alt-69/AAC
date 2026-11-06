# Apex Auto-Clicker 1.1

**Initial distribution release:** `v1.0.0`  
**Publisher:** Kastrick

Apex is a Python desktop automation and macro-studio application. The product
version, distribution release version, and macro data schema version are
tracked separately: product `1.1`, release `v1.0.0`, macro schema `11.0`.

## Run from source

1. Install Python 3.10 or newer (64-bit Python on Windows).
2. Install the application dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

3. Launch Apex:

   ```bash
   python apex_autoclicker.py
   ```

On Windows, `RUN_APEX.bat` is also provided.

## Build the application and installers

The general-purpose build entry point detects the host OS and runs its native
script (`.ps1` / `.bat` on Windows, `.sh` on Linux):

```bash
python build.py --target all
```

Useful options:

```bash
python build.py --target app                 # Build only the application
python build.py --target all --clean         # Clean PyInstaller cache first
python build.py --target all --skip-tests    # Skip unit tests
python build.py --target installers --installer-format exe
python build.py --target installers --installer-format msi
```

The Windows `all` target creates:

- `dist/windows/app/apex-autoclicker.exe` — standalone application.
- `dist/installers/Apex-Auto-Clicker-Setup-1.0.0-x64.exe` — Inno Setup installer.
- `dist/installers/Apex-Auto-Clicker-1.0.0-x64.msi` — Windows Installer package.

Both Windows installers default to:

```text
C:\Program Files\kastrick's_software\aac\apex-autoclicker.exe
```

The installer requests administrator approval because `Program Files` is a
machine-wide installation location. The installer creates a Start Menu shortcut;
the Inno Setup installer also offers an optional desktop shortcut.

### Windows build prerequisites

- Python 3.10+ (64-bit) and packages from `requirements.txt`.
- Inno Setup 6 (the `ISCC.exe` compiler) for the setup `.exe`.
- .NET SDK and WiX Toolset CLI (`wix`) for the `.msi`.
- PowerShell, or Windows Command Prompt as a fallback.

Install WiX as a global .NET tool when needed:

```powershell
dotnet tool install --global wix
```

Install Inno Setup from [jrsoftware.org](https://jrsoftware.org/isinfo.php).

### Linux build

On Linux, `python3 build.py --target all` builds the one-file application and a
portable `.tar.gz` package under `dist/`. Linux input/capture capabilities still
depend on the desktop session and the adapters implemented by Apex; producing a
Linux binary does not imply full X11/Wayland runtime compatibility.

macOS packaging is not included in this release's build scripts.

## Project structure

- `apex/core/` — event model, geometry, coordinate spaces, routing and runtime coordination.
- `apex/recording/` — recording and gesture modules.
- `apex/runtime/` — cursor and runtime feedback modules.
- `apex/adapters/` — Windows, Linux, browser and custom-application adapters.
- `apex/ui/studio_app.py` — canonical desktop UI implementation.
- `build.py` — cross-platform build orchestrator.
- `build_backend.py` — shared PyInstaller and installer build implementation.
- `scripts/` — native build entry points.
- `installer/windows/` — Inno Setup and WiX installer definitions.

## Release notes

The `v1.0.0` tag identifies the first distributable release. The application
window reports product version `1.1`. Macro schema `11.0` remains independent
so existing macro readers and migration logic are not coupled to app releases.

See [BUILDING.md](BUILDING.md) for detailed build and troubleshooting notes.
