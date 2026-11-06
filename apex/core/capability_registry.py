"""
Apex Application Compatibility Layer capability profiles.

Profiles describe available/expected input routes; they do not claim that a
message was processed merely because Windows accepted it into a queue.
"""
import os
import sys

from apex.core.application_state import ApplicationStateProfile

IS_WINDOWS = sys.platform.startswith("win")
IS_LINUX = sys.platform.startswith("linux")
IS_MACOS = sys.platform == "darwin"


class CapabilityRegistry:
    """Classify an application and expose conservative, operation-level routes."""

    GAME_MARKERS = (
        "roblox", "windowsclient", "minecraft", "lwjgl", "unity", "unreal",
        "valorant", "csgo", "fortnite", "genshin", "directx", "vulkan",
    )
    BROWSER_MARKERS = (
        "chrome", "msedge", "firefox", "mozilla", "brave", "opera",
        "chromium", "webkit",
    )

    @classmethod
    def inspect(cls, hwnd=None, title="", class_name="", client_size=(1280, 720), executable=""):
        t_low = (title or "").lower()
        c_low = (class_name or "").lower()
        e_low = os.path.basename(executable or "").lower()
        identity = " ".join((t_low, c_low, e_low))

        if any(marker in identity for marker in cls.GAME_MARKERS):
            is_roblox = "roblox" in identity or "windowsclient" in identity
            return ApplicationStateProfile(
                profile_id="roblox_client" if is_roblox else "foreground_game",
                executable=e_low or ("RobloxPlayerBeta.exe" if is_roblox else "game.exe"),
                window_class=class_name or "GameWindow",
                title=title or ("Roblox" if is_roblox else "3D Game"),
                client_size=client_size,
                adapter_type="FOREGROUND_GAME_INPUT",
                capabilities={
                    "window_message_input": False,
                    "background_input": False,
                    "requires_foreground": True,
                    "input_backend": "Foreground SendInput (shared desktop stream)",
                    "frame_capture": "NOT_PROBED",
                    "input_verification": "foreground-guarded; application acceptance must be observed",
                    "notes": "Game/Raw Input clients commonly ignore posted HWND messages. No DLL injection or anti-cheat bypass is used.",
                },
            )

        if any(marker in identity for marker in cls.BROWSER_MARKERS):
            return ApplicationStateProfile(
                profile_id="browser_foreground_fallback",
                executable=e_low or "browser.exe",
                window_class=class_name or "BrowserWindow",
                title=title or "Web Browser",
                client_size=client_size,
                adapter_type="BROWSER_FOREGROUND_FALLBACK",
                capabilities={
                    "window_message_input": False,
                    "background_input": False,
                    "requires_foreground": True,
                    "input_backend": "Foreground SendInput; CDP/WebDriver adapters are not connected",
                    "frame_capture": "NOT_PROBED",
                    "input_verification": "foreground-guarded; application acceptance must be observed",
                    "notes": "Browser protocol adapters are planned but not active in this runtime path.",
                },
            )

        if "applicationframewindow" in c_low or "windows.ui.core" in c_low or "calculator" in identity:
            return ApplicationStateProfile(
                profile_id="windows_modern_app",
                executable=e_low or "ApplicationFrameHost.exe",
                window_class=class_name or "ApplicationFrameWindow",
                title=title or "Windows Modern App",
                client_size=client_size,
                adapter_type="FOREGROUND_WINDOWS_INPUT",
                capabilities={
                    "window_message_input": False,
                    "background_input": False,
                    "requires_foreground": True,
                    "input_backend": "Foreground SendInput (shared desktop stream)",
                    "frame_capture": "NOT_PROBED",
                    "input_verification": "foreground-guarded; semantic UIA adapter not yet connected",
                    "notes": "Modern windowless controls may not process posted keyboard/mouse messages.",
                },
            )

        # Classic Win32/message-driven windows can be addressed without taking
        # foreground focus, but PostMessage is explicitly best-effort.
        is_notepad = "notepad" in identity or c_low in ("edit", "richedit20w", "richedit50w")
        return ApplicationStateProfile(
            profile_id="classic_win32" if not is_notepad else "notepad",
            executable=e_low or ("notepad.exe" if is_notepad else "win32_app.exe"),
            window_class=class_name or ("Notepad" if is_notepad else "Win32Window"),
            title=title or ("Notepad" if is_notepad else "Desktop Application"),
            client_size=client_size,
            adapter_type="WIN32_WINDOW_MESSAGE_ADAPTER",
            capabilities={
                "window_message_input": True,
                "background_input": True,
                "requires_foreground": False,
                "input_backend": "Target HWND PostMessageW (best-effort queueing)",
                "frame_capture": "NOT_PROBED",
                "input_verification": "queued-unverified; target app may ignore messages",
                "notes": "Input is scoped to the locked HWND. Raw Input/DirectInput applications require foreground system input.",
            },
        )
