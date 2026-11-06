"""
apex/core/capability_registry.py
Apex Application Compatibility Layer (AACL) Capability Registry.
"""
import os
import sys
from apex.core.application_state import ApplicationStateProfile

IS_WINDOWS = sys.platform.startswith("win")
IS_LINUX = sys.platform.startswith("linux")
IS_MACOS = (sys.platform == "darwin")


class CapabilityRegistry:
    """Discovers application capabilities and selects the proper AACL adapter."""
    @classmethod
    def inspect(cls, hwnd=None, title="", class_name="", client_size=(1280, 720)):
        t_low = (title or "").lower()
        c_low = (class_name or "").lower()

        # 1. DirectX / 3D Games (Roblox, Minecraft, Unity, Unreal)
        if any(g in t_low or g in c_low for g in [
            "roblox", "windowsclient", "minecraft", "lwjgl", "unity", "unreal", "valorant", "csgo", "fortnite"
        ]):
            return ApplicationStateProfile(
                profile_id="roblox_directx_game" if "roblox" in t_low or "windowsclient" in c_low else "directx_3d_game",
                executable="RobloxPlayerBeta.exe" if "roblox" in t_low else "GameEngine.exe",
                window_class=class_name or "WINDOWSCLIENT",
                title=title or "3D Game Client",
                client_size=client_size,
                adapter_type="DIRECTX_GAME_ADAPTER",
                capabilities={
                    "background_input": False,
                    "uia_scroll_pattern": False,
                    "frame_capture": "DXGI Desktop Duplication / WGC",
                    "requires_foreground": True,
                    "input_backend": "DirectInput / RawInput Hardware Synthesis",
                    "notes": "3D Game consumes RawInput/DirectInput; requires foreground hardware dispatch."
                }
            )

        # 2. Browsers (Chrome, Edge, Firefox, Brave)
        if any(b in t_low or b in c_low for b in ["chrome", "msedge", "firefox", "mozilla", "brave", "opera"]):
            return ApplicationStateProfile(
                profile_id="browser_adaptive_dom",
                executable="browser.exe",
                window_class=class_name or "Chrome_WidgetWin_1",
                title=title or "Web Browser",
                client_size=client_size,
                adapter_type="BROWSER_CDP_BIDI_ADAPTER",
                capabilities={
                    "background_input": True,
                    "uia_scroll_pattern": True,
                    "adaptive_scroll": True,
                    "frame_capture": "PrintWindow PW_RENDERFULLCONTENT / WGC",
                    "requires_foreground": False,
                    "input_backend": "ChildHWND Message Queue + CDP/BiDi Adaptive Scroll",
                    "notes": "Supports Dynamic Webpage Scroll Ratio (scrollTop / scrollHeight) & isolated clicks."
                }
            )

        # 3. Windows Modern UWP / WinUI Apps
        if "applicationframewindow" in c_low or "settings" in t_low or "calculator" in t_low:
            return ApplicationStateProfile(
                profile_id="windows_uwp_modern",
                executable="ApplicationFrameHost.exe",
                window_class=class_name or "ApplicationFrameWindow",
                title=title or "Windows UWP App",
                client_size=client_size,
                adapter_type="WINDOWS_UIA_WINRT_ADAPTER",
                capabilities={
                    "background_input": True,
                    "uia_scroll_pattern": True,
                    "frame_capture": "PrintWindow PW_RENDERFULLCONTENT",
                    "requires_foreground": False,
                    "input_backend": "UI Automation + Thread-Attached Message Queue",
                    "notes": "Supports UWP state restoration and Target Session dispatch."
                }
            )

        # 4. Notepad & Standard Win32 Apps
        if "notepad" in t_low or "notepad" in c_low:
            return ApplicationStateProfile(
                profile_id="notepad",
                executable="notepad.exe",
                window_class=class_name or "Notepad",
                title=title or "Notepad",
                client_size=client_size,
                adapter_type="WIN32_UIA_ADAPTER",
                capabilities={
                    "background_input": True,
                    "uia_scroll_pattern": True,
                    "frame_capture": "Win32 PrintWindow / WGC",
                    "requires_foreground": False,
                    "input_backend": "Isolated ChildHWND PostMessageW (VK + Mouse)",
                    "notes": "Full Target Session isolation supported."
                }
            )

        # 5. Linux X11 / Wayland
        if IS_LINUX:
            session_type = os.environ.get("XDG_SESSION_TYPE", "x11").lower()
            is_wayland = ("wayland" in session_type)
            return ApplicationStateProfile(
                profile_id=f"linux_{session_type}_app",
                executable="linux_bin",
                window_class=class_name or "X11Window",
                title=title or "Linux Application",
                client_size=client_size,
                adapter_type="LINUX_WAYLAND_PORTAL" if is_wayland else "LINUX_X11_XTEST",
                capabilities={
                    "background_input": not is_wayland,
                    "uia_scroll_pattern": True,
                    "frame_capture": "PipeWire ScreenCast" if is_wayland else "XGetImage",
                    "requires_foreground": is_wayland,
                    "input_backend": "XDG RemoteDesktop Portal / libei" if is_wayland else "X11 XTEST / XSendEvent",
                    "notes": "Wayland uses native portal permissions; X11 supports direct window targeting."
                }
            )

        return ApplicationStateProfile(
            profile_id="win32_desktop_app",
            executable="win32_app.exe",
            window_class=class_name or "Win32Window",
            title=title or "Desktop Application",
            client_size=client_size,
            adapter_type="WIN32_UIA_ADAPTER",
            capabilities={
                "background_input": True,
                "uia_scroll_pattern": True,
                "frame_capture": "Win32 PrintWindow / WGC",
                "requires_foreground": False,
                "input_backend": "Isolated ChildHWND PostMessageW (VK + Mouse)",
                "notes": "Full Target Session isolation supported."
            }
        )
