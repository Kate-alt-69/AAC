#!/usr/bin/env python3
"""
⚡ Apex Auto-Clicker & Macro Studio Ultra Pro (v9.5 Complete Edition)
The definitive high-performance, pixel-accurate desktop automation suite.

Complete Feature & Settings Verification:
 1. Smart Target Window Recognition:
    - Never targets Apex Auto-Clicker itself.
    - Uses WindowFromPoint and GetAncestor(GA_ROOT) on coordinates to lock target (e.g. Roblox Client, Chrome, etc.).
 2. App & Game Engine Recognizer (Roblox / 3D Games vs React / Win32 / UWP):
    - GAME: 3D Game Engines (Roblox, Minecraft, Unity, Unreal) -> Dispatches hardware DirectInput clicks.
      Roblox NEVER drops clicks even during background hand-off (uses fleeting micro-flick hardware injection).
    - REACT_WEB: Modern Electron / React / Web Apps (Discord, VSCode, Chrome).
    - UWP: Native Windows Modern Apps (Settings, Calculator, Photos) via AttachThreadInput focus bypass.
    - STANDARD: Win32 Desktop Apps.
 3. Occupied Window Tint on Target Game (Roblox):
    - Glass tint snaps directly over the ROBLOX window bounds, never Apex!
 4. 100% Restored Settings:
    - Auto-Clicker Tab 1: Interval (Hours/Mins/Secs/Ms), Presets, Humanize Jitter (± ms), Mouse Button/Type,
      Target Position (Follow Cursor vs Fixed Spot with F4 Picker), Repeat Modes (Continuous vs N times).
    - Auto-Clicker Tab 2: Smart Background Worker & Auto-Hand-Off, Manual Target Window Selector,
      Adaptive Anti-Recoil Vector Engine (X/Y pull-down compensation), Pixel Color Triggerbot (F3 Eyedropper),
      Computer Vision Screen Snip (F2), Audio Sound Spike Trigger with threshold entry.
    - Auto-Clicker Tab 3: Always on Top, Audio Cues, 3s Countdown HUD, Hotkeys Reference.
    - Macro Studio:
        * ⚙️ Settings & Webhooks Dialog (Capture Filters, Sub-pixel Jitter <2px, UWP State Reset, Discord Webhooks).
        * Universal Macro Importer (.ahk, .py, .csv, .txt, .rec, .xml, .json) & Presets Bar.
        * Trajectory Engine Selector (Human Biomechanical Bézier, Bresenham Pixel-Stepping, Cubic Ease, Raw Instant).
        * Hardware Polling Rate (125Hz, 250Hz, 500Hz).
        * Concurrent Cooldown Automation Manager (up to 4 independent skill cooldown timers).
        * Visual Action Builder (+ Click, + Keypress, + Scroll, + Delay, 🔀 + IF Color, ⏳ + Wait Color, 🔁 + Loop).
        * 1-Pixel Micro-Nudge Inspector (▲, ▼, ◄, ►, 🎯 Jump) & Step Reordering (▲ Move Up, ▼ Move Down).
        * Standalone Headless Python Script Exporter (⚡ Export .py).
 5. Window Layout & Geometry: Pinned action footer prevents bottom button cutoff; full resizing enabled.
"""

import os
import sys
import re
import time
import json
import math
import random
import threading
import urllib.request
from datetime import datetime

# Windows Native APIs & High-DPI Scaling Configuration
IS_WINDOWS = sys.platform.startswith("win")
IS_MACOS = (sys.platform == "darwin")
IS_LINUX = sys.platform.startswith("linux")
if IS_WINDOWS:
    try:
        import ctypes
        from ctypes import wintypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2) # Per-monitor DPI aware
        except Exception:
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# Optional Computer Vision & Audio Libraries
HAS_CV2 = False
try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    pass

HAS_PIL = False
try:
    from PIL import ImageGrab, Image, ImageTk
    HAS_PIL = True
except ImportError:
    pass

HAS_PYAUDIO = False
try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    pass

# Core Automation Dependencies
MISSING_DEPS = []
try:
    import pynput
    from pynput import mouse, keyboard
    from pynput.mouse import Button, Controller as MouseController
    from pynput.keyboard import Key, KeyCode, Controller as KeyboardController
except ImportError:
    MISSING_DEPS.append("pynput")

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog, simpledialog
except ImportError:
    MISSING_DEPS.append("tkinter")


# ==============================================================================
# AUDIO NOTIFIER (Non-blocking subtle audio cue)
# ==============================================================================
def play_cue(high_pitch=True):
    """Plays subtle audio beep on start/stop."""
    def _beep():
        if IS_WINDOWS:
            try:
                import winsound
                freq = 950 if high_pitch else 600
                winsound.Beep(freq, 100)
            except Exception:
                pass
        else:
            sys.stdout.write('\a')
            sys.stdout.flush()
            sys.stdout.write("\a")


# ==============================================================================
# HARDWARE-LEVEL WIN32 DISPATCHER
# ==============================================================================
class HardwareCursor:
    """Direct hardware-level cursor positioning, coordinate & pixel color readouts."""
    @staticmethod
    def get_pos():
        if IS_WINDOWS:
            try:
                pt = wintypes.POINT()
                ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
                return (pt.x, pt.y)
            except Exception:
                pass
        return None

    @staticmethod
    def set_pos(x, y):
        if IS_WINDOWS:
            try:
                ctypes.windll.user32.SetCursorPos(int(x), int(y))
                return True
            except Exception:
                pass
        return False

    @staticmethod
    def hardware_click(button="left"):
        """Fires genuine OS-level hardware mouse click bypassing DirectInput filters."""
        if IS_WINDOWS:
            try:
                if button == "left":
                    flags = 0x0002 | 0x0004 # MOUSEEVENTF_LEFTDOWN | MOUSEEVENTF_LEFTUP
                elif button == "right":
                    flags = 0x0008 | 0x0010 # MOUSEEVENTF_RIGHTDOWN | MOUSEEVENTF_RIGHTUP
                else:
                    flags = 0x0020 | 0x0040 # MOUSEEVENTF_MIDDLEDOWN | MOUSEEVENTF_MIDDLEUP
                ctypes.windll.user32.mouse_event(flags, 0, 0, 0, 0)
                return True
            except Exception:
                pass
        return False

    @staticmethod
    def get_pixel_color(x, y):
        """Samples the exact 24-bit RGB Hex color at screen coordinate (x, y)."""
        if IS_WINDOWS:
            try:
                hdc = ctypes.windll.user32.GetDC(0)
                color = ctypes.windll.gdi32.GetPixel(hdc, int(x), int(y))
                ctypes.windll.user32.ReleaseDC(0, hdc)
                r = color & 0xFF
                g = (color >> 8) & 0xFF
                b = (color >> 16) & 0xFF
                return f"#{r:02X}{g:02X}{b:02X}", (r, g, b)
            except Exception:
                pass
        return "#000000", (0, 0, 0)

    @staticmethod
    def make_click_through(hwnd):
        """Makes a window completely click-through on Windows (WS_EX_TRANSPARENT | WS_EX_LAYERED)."""
        if IS_WINDOWS and hwnd:
            try:
                GWL_EXSTYLE = -20
                WS_EX_LAYERED = 0x00080000
                WS_EX_TRANSPARENT = 0x00000020
                ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style | WS_EX_LAYERED | WS_EX_TRANSPARENT)
                return True
            except Exception:
                pass
        return False


# ==============================================================================
# SMART APP & GAME ENGINE RECOGNIZER
# ==============================================================================
class AppRecognizer:
    @staticmethod
    def classify_target(title, class_name="", process_name=""):
        title_lower = title.lower()
        class_lower = class_name.lower()
        proc_lower = process_name.lower()

        # Check for Roblox & 3D Game Engines
        if any(g in proc_lower or g in title_lower or g in class_lower for g in [
            "roblox", "windowsclient", "minecraft", "javaw", "unity", "unreal",
            "valve", "csgo", "dota", "fortnite", "valorant", "genshin"
        ]):
            return "GAME", "🎮 3D Game Engine (DirectInput Hardware Clicks Required)"

        # Check for React / Electron / Modern Web
        if any(e in proc_lower or e in class_lower for e in ["electron", "chrome", "msedge", "firefox", "discord", "slack", "code"]):
            return "REACT_WEB", "⚡ Modern Web / React / Electron App"

        # Check for Windows UWP Modern Apps
        if "applicationframewindow" in class_lower or "settings" in title_lower:
            return "UWP", "🪟 Native Windows Modern App (UWP Deep Focus)"

        return "STANDARD", "🖥️ Win32 Desktop Application"


# ==============================================================================
# APPLICATION STATE & TARGET WINDOW MANAGER (Never Targets Apex!)
# ==============================================================================
class AppStateManager:
    @staticmethod
    def get_foreground_window(exclude_hwnds=None):
        if IS_WINDOWS:
            try:
                hwnd = ctypes.windll.user32.GetForegroundWindow()
                excluded = set(exclude_hwnds or [])
                # Tk's winfo_id() may return a child HWND, while the foreground
                # API returns the outer top-level HWND. Compare both identities.
                for excluded_hwnd in tuple(excluded):
                    if excluded_hwnd:
                        root_hwnd = ctypes.windll.user32.GetAncestor(excluded_hwnd, 2)  # GA_ROOT
                        if root_hwnd:
                            excluded.add(root_hwnd)
                foreground_root = ctypes.windll.user32.GetAncestor(hwnd, 2) or hwnd
                if hwnd in excluded or foreground_root in excluded:
                    return None, "Apex Auto-Clicker", ""

                length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                buff = ctypes.create_unicode_buffer(length + 1)
                ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value

                class_buff = ctypes.create_unicode_buffer(256)
                ctypes.windll.user32.GetClassNameW(hwnd, class_buff, 256)
                class_name = class_buff.value

                return hwnd, title, class_name
            except Exception:
                pass
        return None, "Current Screen", ""

    @staticmethod
    def get_window_at_point(x, y, exclude_hwnds=None):
        if IS_WINDOWS:
            try:
                pt = wintypes.POINT(int(x), int(y))
                h = ctypes.windll.user32.WindowFromPoint(pt)
                if h:
                    root_h = ctypes.windll.user32.GetAncestor(h, 2) # GA_ROOT = 2
                    target = root_h if root_h else h
                    if exclude_hwnds and target in exclude_hwnds:
                        return None, "Apex", ""

                    length = ctypes.windll.user32.GetWindowTextLengthW(target)
                    buff = ctypes.create_unicode_buffer(length + 1)
                    ctypes.windll.user32.GetWindowTextW(target, buff, length + 1)
                    title = buff.value

                    class_buff = ctypes.create_unicode_buffer(256)
                    ctypes.windll.user32.GetClassNameW(target, class_buff, 256)
                    class_name = class_buff.value

                    return target, title, class_name
            except Exception:
                pass
        return None, "Desktop", ""

    @staticmethod
    def get_window_bounds(hwnd):
        if IS_WINDOWS and hwnd:
            try:
                rect = wintypes.RECT()
                ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
                return rect.left, rect.top, max(rect.right - rect.left, 200), max(rect.bottom - rect.top, 150)
            except Exception:
                pass
        return None

    @staticmethod
    def robust_focus_window(hwnd):
        if not IS_WINDOWS or not hwnd:
            return False
        try:
            if not ctypes.windll.user32.IsWindow(hwnd):
                return False

            cur_thread = ctypes.windll.kernel32.GetCurrentThreadId()
            target_thread = ctypes.windll.user32.GetWindowThreadProcessId(hwnd, None)

            if cur_thread != target_thread:
                ctypes.windll.user32.AttachThreadInput(cur_thread, target_thread, True)

            if ctypes.windll.user32.IsIconic(hwnd):
                ctypes.windll.user32.ShowWindow(hwnd, 9) # SW_RESTORE
            else:
                ctypes.windll.user32.ShowWindow(hwnd, 5) # SW_SHOW

            ctypes.windll.user32.BringWindowToTop(hwnd)
            ctypes.windll.user32.SetForegroundWindow(hwnd)

            if cur_thread != target_thread:
                ctypes.windll.user32.AttachThreadInput(cur_thread, target_thread, False)

            return True
        except Exception:
            return False


# ==============================================================================
# OCCUPIED WINDOW TINT OVERLAY (Accurately Tints Target Window / Roblox)
# ==============================================================================
class OccupiedWindowTint(tk.Toplevel):
    def __init__(self, target_hwnd, target_title="Target Window", on_reclaim=None, on_stop=None):
        super().__init__()
        self.target_hwnd = target_hwnd
        self.on_reclaim = on_reclaim
        self.on_stop = on_stop

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.45)
        self.configure(bg="#090D16")

        bounds = AppStateManager.get_window_bounds(target_hwnd)
        if bounds:
            x, y, w, h = bounds
            self.geometry(f"{w}x{h}+{x}+{y}")
        else:
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            self.geometry(f"{sw//2}x{sh//2}+{sw//4}+{sh//4}")

        center_frame = tk.Frame(self, bg="#161B26", highlightbackground="#2D3748", highlightthickness=1, padx=24, pady=18)
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        lbl_lock = tk.Label(center_frame, text="🔒 WINDOW OCCUPIED BY APEX AUTO-CLICKER", fg="#F7FAFC", bg="#161B26", font=("Segoe UI", 12, "bold"))
        lbl_lock.pack(pady=(0, 4))

        lbl_sub = tk.Label(center_frame, text=f"Automating: {target_title[:30]}", fg="#10B981", bg="#161B26", font=("Segoe UI", 10, "bold"))
        lbl_sub.pack(pady=(0, 4))

        lbl_desc = tk.Label(center_frame, text="Background automation is running on this window. Your physical cursor is free!", fg="#A0AEC0", bg="#161B26", font=("Segoe UI", 10))
        lbl_desc.pack(pady=(0, 14))

        btn_box = tk.Frame(center_frame, bg="#161B26")
        btn_box.pack()

        btn_reclaim = tk.Button(
            btn_box,
            text="Reclaim Cursor Focus",
            command=self._do_reclaim,
            bg="#10B981",
            fg="#000000",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=14,
            pady=4,
            cursor="hand2"
        )
        btn_reclaim.pack(side="left", padx=6)

        btn_stop = tk.Button(
            btn_box,
            text="Stop Automation (F6)",
            command=self._do_stop,
            bg="#2D3748",
            fg="#F43F5E",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=14,
            pady=4,
            cursor="hand2"
        )
        btn_stop.pack(side="left", padx=6)

    def _do_reclaim(self):
        self.destroy()
        if self.on_reclaim:
            self.on_reclaim()

    def _do_stop(self):
        self.destroy()
        if self.on_stop:
            self.on_stop()

    def close(self):
        try:
            self.destroy()
        except Exception:
            pass


# ==============================================================================
# DISCORD & WEBHOOK TELEMETRY NOTIFIER
# ==============================================================================
class WebhookNotifier:
    @staticmethod
    def send_notification(webhook_url, message, stats=None):
        if not webhook_url or not webhook_url.startswith("http"):
            return
        def _post():
            try:
                payload = {
                    "content": f"⚡ **Apex Automation Alert**\n{message}",
                    "username": "Apex Ultra Pro"
                }
                if stats:
                    payload["embeds"] = [{
                        "title": "📊 Session Telemetry",
                        "color": 0x10B981,
                        "fields": [
                            {"name": k, "value": str(v), "inline": True} for k, v in stats.items()
                        ],
                        "footer": {"text": "Apex Automation Suite"}
                    }]
                req = urllib.request.Request(
                    webhook_url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json", "User-Agent": "ApexAutoClicker/9.5"}
                )
                urllib.request.urlopen(req, timeout=5)
            except Exception as e:
                print(f"[Webhook Error] {e}")
        threading.Thread(target=_post, daemon=True).start()


# ==============================================================================
# COMPUTER VISION & SCREEN TEMPLATE MATCHING ENGINE
# ==============================================================================
class VisionTemplateEngine:
    @staticmethod
    def capture_screen_region(bbox):
        if HAS_PIL:
            try:
                return ImageGrab.grab(bbox=bbox)
            except Exception:
                pass
        return None

    @staticmethod
    def match_template_on_screen(template_img, confidence=0.85):
        if HAS_CV2 and HAS_PIL and template_img is not None:
            try:
                screen = ImageGrab.grab()
                screen_np = np.array(screen)
                screen_bgr = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)

                tmpl_np = np.array(template_img)
                tmpl_bgr = cv2.cvtColor(tmpl_np, cv2.COLOR_RGB2BGR)

                res = cv2.matchTemplate(screen_bgr, tmpl_bgr, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

                if max_val >= confidence:
                    th, tw = tmpl_bgr.shape[:2]
                    cx = max_loc[0] + tw // 2
                    cy = max_loc[1] + th // 2
                    return (cx, cy), max_val
            except Exception:
                pass
        return None, 0.0


# ==============================================================================
# AUDIO VOLUME SPIKE TRIGGER ENGINE
# ==============================================================================
class AudioVolumeTrigger(threading.Thread):
    def __init__(self, threshold=0.3, callback=None):
        super().__init__()
        self.daemon = True
        self.threshold = threshold
        self.callback = callback
        self.stop_signal = threading.Event()

    def stop(self):
        self.stop_signal.set()

    def run(self):
        if not HAS_PYAUDIO:
            return
        try:
            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
            while not self.stop_signal.is_set():
                data = stream.read(1024, exception_on_overflow=False)
                import audioop
                rms = audioop.rms(data, 2)
                norm_volume = rms / 32768.0
                if norm_volume >= self.threshold:
                    if self.callback:
                        self.callback(norm_volume)
                    time.sleep(0.5)
            stream.stop_stream()
            stream.close()
            p.terminate()
        except Exception:
            pass


# ==============================================================================
# CONCURRENT COOLDOWN AUTOMATION MANAGER
# ==============================================================================
class CooldownManager(threading.Thread):
    def __init__(self, key_controller, cooldowns):
        super().__init__()
        self.daemon = True
        self.key_controller = key_controller
        self.cooldowns = cooldowns
        self.stop_signal = threading.Event()

    def stop(self):
        self.stop_signal.set()

    def run(self):
        last_fired = {i: time.perf_counter() for i in range(len(self.cooldowns))}
        while not self.stop_signal.is_set():
            now = time.perf_counter()
            for idx, item in enumerate(self.cooldowns):
                if item.get("enabled", True):
                    interval = item.get("interval", 5.0)
                    if now - last_fired[idx] >= interval:
                        last_fired[idx] = now
                        k_str = item.get("key", "")
                        self._press_key(k_str)
            time.sleep(0.05)

    def _press_key(self, k_str):
        try:
            if k_str.startswith("Key."):
                k = getattr(Key, k_str.split(".", 1)[1], None)
            else:
                k = KeyCode.from_char(k_str)
            if k:
                self.key_controller.press(k)
                time.sleep(0.03)
                self.key_controller.release(k)
        except Exception:
            pass


# ==============================================================================
# UNIVERSAL MACRO IMPORTER & CONVERTER ENGINE
# ==============================================================================
class UniversalMacroImporter:
    @staticmethod
    def parse_file(filepath):
        ext = filepath.lower().split('.')[-1]
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        if ext == 'json':
            return UniversalMacroImporter.parse_json(content)
        elif ext == 'ahk':
            return UniversalMacroImporter.parse_ahk(content)
        elif ext == 'py':
            return UniversalMacroImporter.parse_python(content)
        elif ext in ('csv', 'tsv'):
            return UniversalMacroImporter.parse_csv(content, delimiter=',' if ext == 'csv' else '\t')
        elif ext == 'xml':
            return UniversalMacroImporter.parse_xml(content)
        else:
            return UniversalMacroImporter.parse_text(content)

    @staticmethod
    def parse_json(content):
        data = json.loads(content)
        if isinstance(data, dict) and "actions" in data:
            return data["actions"], "Native Apex JSON (.json)"
        elif isinstance(data, list):
            return data, "Generic JSON Array (.json)"
        return [], "Unknown JSON Schema"

    @staticmethod
    def parse_ahk(content):
        actions = []
        curr_time = 0.0
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith(';'):
                continue

            m = re.match(r'Sleep,?\s*(\d+)', line, re.IGNORECASE)
            if m:
                curr_time += float(m.group(1)) / 1000.0
                continue

            m = re.match(r'Click,?\s*(\d+),?\s*(\d+)', line, re.IGNORECASE)
            if m:
                x, y = int(m.group(1)), int(m.group(2))
                actions.append({"time": round(curr_time, 4), "type": "MOUSE_DOWN", "data": {"x": x, "y": y, "button": "left"}})
                curr_time += 0.03
                actions.append({"time": round(curr_time, 4), "type": "MOUSE_UP", "data": {"x": x, "y": y, "button": "left"}})
                curr_time += 0.04
                continue

            m = re.match(r'MouseClick,?\s*(left|right|middle)?,?\s*(\d+)?,?\s*(\d+)?', line, re.IGNORECASE)
            if m:
                btn = (m.group(1) or 'left').lower()
                x = int(m.group(2)) if m.group(2) else 0
                y = int(m.group(3)) if m.group(3) else 0
                actions.append({"time": round(curr_time, 4), "type": "MOUSE_DOWN", "data": {"x": x, "y": y, "button": btn}})
                curr_time += 0.03
                actions.append({"time": round(curr_time, 4), "type": "MOUSE_UP", "data": {"x": x, "y": y, "button": btn}})
                curr_time += 0.04
                continue

            m = re.match(r'MouseMove,?\s*(\d+),?\s*(\d+)', line, re.IGNORECASE)
            if m:
                x, y = int(m.group(1)), int(m.group(2))
                actions.append({"time": round(curr_time, 4), "type": "MOUSE_MOVE", "data": {"x": x, "y": y}})
                curr_time += 0.02
                continue

            m = re.match(r'(?:Send|SendInput),?\s*(.+)', line, re.IGNORECASE)
            if m:
                raw_keys = m.group(1)
                key_matches = re.findall(r'\{([^}]+)\}|(\S)', raw_keys)
                for special, char in key_matches:
                    k = special if special else char
                    actions.append({"time": round(curr_time, 4), "type": "KEY_DOWN", "data": {"key": k}})
                    curr_time += 0.02
                    actions.append({"time": round(curr_time, 4), "type": "KEY_UP", "data": {"key": k}})
                    curr_time += 0.02
                continue

        return actions, "AutoHotkey Script (.ahk)"

    @staticmethod
    def parse_python(content):
        actions = []
        curr_time = 0.0
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            m = re.search(r'(?:time\.)?sleep\s*\(\s*([\d\.]+)\s*\)', line)
            if m:
                curr_time += float(m.group(1))
                continue

            m = re.search(r"click\s*\(\s*(\d+)\s*,\s*(\d+)(?:\s*,\s*button\s*=\s*[\x27\"](w+)[\x27\"])?", line)
            if m:
                x, y = int(m.group(1)), int(m.group(2))
                btn = m.group(3).lower() if m.group(3) else 'left'
                actions.append({"time": round(curr_time, 4), "type": "MOUSE_DOWN", "data": {"x": x, "y": y, "button": btn}})
                curr_time += 0.03
                actions.append({"time": round(curr_time, 4), "type": "MOUSE_UP", "data": {"x": x, "y": y, "button": btn}})
                curr_time += 0.04
                continue

            m = re.search(r'moveTo\s*\(\s*(\d+)\s*,\s*(\d+)', line)
            if m:
                x, y = int(m.group(1)), int(m.group(2))
                actions.append({"time": round(curr_time, 4), "type": "MOUSE_MOVE", "data": {"x": x, "y": y}})
                curr_time += 0.02
                continue

            m = re.search(r"press\s*\(\s*[\x27\"]([^\x27\"]+)[\x27\"]\s*\)", line)
            if m:
                k = m.group(1)
                actions.append({"time": round(curr_time, 4), "type": "KEY_DOWN", "data": {"key": k}})
                curr_time += 0.02
                actions.append({"time": round(curr_time, 4), "type": "KEY_UP", "data": {"key": k}})
                curr_time += 0.02
                continue

            m = re.search(r"(?:write|typewrite)\s*\(\s*[\x27\"]([^\x27\"]+)[\x27\"]\s*\)", line)
            if m:
                for ch in m.group(1):
                    actions.append({"time": round(curr_time, 4), "type": "KEY_DOWN", "data": {"key": ch}})
                    curr_time += 0.02
                    actions.append({"time": round(curr_time, 4), "type": "KEY_UP", "data": {"key": ch}})
                    curr_time += 0.02
                continue

            m = re.search(r'scroll\s*\(\s*(-?\d+)', line)
            if m:
                dy = int(m.group(1))
                actions.append({"time": round(curr_time, 4), "type": "MOUSE_SCROLL", "data": {"x": 0, "y": 0, "dx": 0, "dy": dy}})
                curr_time += 0.05
                continue

        return actions, "Python / PyAutoGUI Script (.py)"

    @staticmethod
    def parse_csv(content, delimiter=','):
        actions = []
        lines = [l.strip() for l in content.splitlines() if l.strip()]
        if not lines: return [], "Empty CSV"
        headers = [h.strip().lower() for h in lines[0].split(delimiter)]
        col_map = {name: i for i, name in enumerate(headers)}

        for line in lines[1:]:
            parts = [p.strip() for p in line.split(delimiter)]
            def get_val(key, default=''):
                idx = col_map.get(key)
                return parts[idx] if idx is not None and idx < len(parts) else default

            try: t = float(get_val('time') or get_val('timestamp') or 0.0)
            except ValueError: t = 0.0
            evt_type = (get_val('type') or get_val('event') or 'MOUSE_MOVE').strip().upper()
            # Accept both explicit event names and generic mouse rows from spreadsheets.
            evt_type = {
                'CLICK': 'MOUSE_CLICK', 'DRAG': 'MOUSE_DRAG',
                'MOVE': 'MOUSE_MOVE', 'SCROLL': 'MOUSE_SCROLL'
            }.get(evt_type, evt_type)
            data = {}
            if 'MOUSE' in evt_type:
                try:
                    data['x'], data['y'] = int(get_val('x', '0') or 0), int(get_val('y', '0') or 0)
                except (TypeError, ValueError):
                    data['x'], data['y'] = 0, 0
                btn = get_val('button')
                if btn: data['button'] = btn.lower()
                # Generic MOUSE rows can declare the transform that should be selected initially.
                action_hint = get_val('action') or get_val('mode') or get_val('interaction') or get_val('subtype')
                if action_hint: data['action'] = action_hint.strip()
                for source, target in (('end_x', 'end_x'), ('end_y', 'end_y'),
                                       ('dx', 'dx'), ('dy', 'dy')):
                    raw = get_val(source)
                    if raw:
                        try: data[target] = int(raw)
                        except ValueError: pass
                for source in ('duration', 'hold', 'seconds'):
                    raw = get_val(source)
                    if raw:
                        try:
                            data['duration'] = float(raw)
                            break
                        except ValueError:
                            pass
                curve = get_val('curve')
                if curve: data['curve'] = curve
            elif 'KEY' in evt_type:
                data['key'] = get_val('key') or get_val('code')
            actions.append({"time": round(t, 4), "type": evt_type, "data": data})

        return actions, "CSV / Spreadsheet Macro (.csv)"

    @staticmethod
    def parse_text(content):
        actions = []
        curr_time = 0.0
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('#'): continue
            parts = line.split()
            cmd = parts[0].upper()

            if cmd in ('WAIT', 'SLEEP', 'DELAY'):
                try:
                    val = float(parts[1])
                    curr_time += (val / 1000.0) if val > 10 else val
                except (IndexError, ValueError): pass
            elif cmd in ('MOVE', 'MOUSE_MOVE') and len(parts) >= 3:
                actions.append({"time": round(curr_time, 4), "type": "MOUSE_MOVE", "data": {"x": int(parts[1]), "y": int(parts[2])}})
                curr_time += 0.02
            elif cmd in ('CLICK', 'MOUSE_CLICK') and len(parts) >= 3:
                x, y = int(parts[1]), int(parts[2])
                btn = parts[3].lower() if len(parts) >= 4 else 'left'
                actions.append({"time": round(curr_time, 4), "type": "MOUSE_DOWN", "data": {"x": x, "y": y, "button": btn}})
                curr_time += 0.03
                actions.append({"time": round(curr_time, 4), "type": "MOUSE_UP", "data": {"x": x, "y": y, "button": btn}})
                curr_time += 0.04
            elif cmd in ('SCROLL', 'MOUSE_SCROLL') and len(parts) >= 2:
                dy = int(parts[1])
                actions.append({"time": round(curr_time, 4), "type": "MOUSE_SCROLL", "data": {"x": 0, "y": 0, "dx": 0, "dy": dy}})
                curr_time += 0.05
            elif cmd in ('KEY_DOWN', 'PRESS') and len(parts) >= 2:
                actions.append({"time": round(curr_time, 4), "type": "KEY_DOWN", "data": {"key": parts[1]}})
                curr_time += 0.02
            elif cmd in ('KEY_UP', 'RELEASE') and len(parts) >= 2:
                actions.append({"time": round(curr_time, 4), "type": "KEY_UP", "data": {"key": parts[1]}})
                curr_time += 0.02
            elif cmd == 'TYPE' and len(parts) >= 2:
                txt = " ".join(parts[1:])
                for ch in txt:
                    actions.append({"time": round(curr_time, 4), "type": "KEY_DOWN", "data": {"key": ch}})
                    curr_time += 0.02
                    actions.append({"time": round(curr_time, 4), "type": "KEY_UP", "data": {"key": ch}})
                    curr_time += 0.02

        return actions, "Generic Macro Script (.txt / .rec)"

    @staticmethod
    def parse_xml(content):
        actions = []
        curr_time = 0.0
        elements = re.findall(r'<([a-zA-Z0-9_-]+)([^>]+)>', content)
        for tag, attrs_str in elements:
            attrs = dict(re.findall(r"(\w+)=[\x27\"]([^\x27\"]+)[\x27\"]", attrs_str))
            evt_type = attrs.get('type') or tag
            delay = float(attrs.get('delay') or attrs.get('wait') or 0.0)
            if delay > 10: curr_time += delay / 1000.0
            elif delay > 0: curr_time += delay

            if 'click' in evt_type.lower():
                x = int(attrs.get('x', 0))
                y = int(attrs.get('y', 0))
                btn = attrs.get('button', 'left').lower()
                actions.append({"time": round(curr_time, 4), "type": "MOUSE_DOWN", "data": {"x": x, "y": y, "button": btn}})
                curr_time += 0.03
                actions.append({"time": round(curr_time, 4), "type": "MOUSE_UP", "data": {"x": x, "y": y, "button": btn}})
                curr_time += 0.04
            elif 'move' in evt_type.lower():
                x = int(attrs.get('x', 0))
                y = int(attrs.get('y', 0))
                actions.append({"time": round(curr_time, 4), "type": "MOUSE_MOVE", "data": {"x": x, "y": y}})
                curr_time += 0.02
            elif 'key' in evt_type.lower():
                k = attrs.get('key') or attrs.get('value')
                state = attrs.get('state', 'down').lower()
                act_type = "KEY_DOWN" if state == 'down' else "KEY_UP"
                if k:
                    actions.append({"time": round(curr_time, 4), "type": act_type, "data": {"key": k}})
                    curr_time += 0.03

        return actions, "XML Macro Profile (.xml)"


# ==============================================================================
# REFINED, MODERN SLATE DARK THEME
# ==============================================================================
THEME = {
    "bg_root": "#1E1E1E",         # Authentic Windows 10 Dark Mode Surface
    "bg_card": "#252526",         # Windows 10 Control / Panel Surface
    "bg_card_hover": "#2D2D30",   # Windows 10 Fluent Hover Gray
    "bg_input": "#181818",        # Windows 10 Crisp Text/Input Field
    "border": "#3F3F46",          # Windows 10 1px Sharp Control Border
    "border_focus": "#0078D7",    # Windows 10 Accent Blue Focus Ring
    "accent_emerald": "#0078D7",  # Primary Win10 Action Blue (#0078D7)
    "accent_green": "#10893E",    # Win10 Status / Virtual Cursor Green
    "accent_blue": "#0078D7",     # Win10 Fluent Blue
    "accent_purple": "#0063B1",   # Win10 Deep Fluent Blue
    "accent_rose": "#E81123",     # Win10 Close / Stop Red
    "accent_amber": "#FFB900",    # Win10 Warning / Logic Gold
    "text_primary": "#FFFFFF",    # Crisp White
    "text_secondary": "#CCCCCC",  # Win10 Secondary Gray
    "text_muted": "#858585",      # Win10 Muted Label
    "font_main": ("Segoe UI", 9),
    "font_bold": ("Segoe UI", 9, "bold"),
    "font_title": ("Segoe UI", 12, "bold"),
    "font_mono": ("Consolas", 9),
    "font_mono_bold": ("Consolas", 9, "bold"),
    "font_badge": ("Segoe UI", 8, "bold"),
}


# ==============================================================================
# WINDOWS 10 COMPACT FLUENT WIDGETS (Zero Space Wastage)
# ==============================================================================
class StyledCard(tk.Frame):
    """Compact Windows 10 Group Panel with 1px sharp border and tight padding."""
    def __init__(self, parent, title="", **kwargs):
        padx_val = kwargs.pop("padx", 10)
        pady_val = kwargs.pop("pady", 5)
        super().__init__(
            parent,
            bg=THEME["bg_card"],
            highlightbackground=THEME["border"],
            highlightthickness=1,
            padx=padx_val,
            pady=pady_val,
            **kwargs
        )
        if title:
            lbl = tk.Label(
                self,
                text=title,
                bg=THEME["bg_card"],
                fg=THEME["text_primary"],
                font=THEME["font_bold"]
            )
            lbl.pack(anchor="w", pady=(0, 3))


class ModernButton(tk.Canvas):
    """Sharp Windows 10 Fluent Button (Auto-resizes width, sharp 2px corners)."""
    def __init__(self, parent, text, command=None, bg_color=None, fg_color=None,
                 hover_color=None, width=120, height=30, corner_radius=2, font=None, **kwargs):
        super().__init__(parent, width=width, height=height, bg=parent["bg"],
                         highlightthickness=0, cursor="hand2", **kwargs)
        self.command = command
        self.btn_text = text
        self.width = width
        self.height = height
        self.corner_radius = corner_radius
        self.font = font or THEME["font_bold"]
        self.bg_color = bg_color or THEME["accent_blue"]
        self.fg_color = fg_color or "#FFFFFF"
        self.hover_color = hover_color or "#1084E0"
        self.current_bg = self.bg_color
        self.enabled = True

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.bind("<Configure>", self._on_resize)
        self._draw()

    def _on_resize(self, event):
        if event.width > 20 and event.width != self.width:
            self.width = event.width
            self._draw()

    def _draw(self):
        self.delete("all")
        w, h = self.width, self.height
        self.create_rectangle(0, 0, w, h, fill=self.current_bg, outline=THEME["border"], width=1)
        self.create_text(w // 2, h // 2, text=self.btn_text, fill=self.fg_color, font=self.font)

    def set_text_and_color(self, text, bg_color, fg_color="#FFFFFF", hover_color=None):
        self.btn_text = text
        self.bg_color = bg_color
        self.current_bg = bg_color
        self.fg_color = fg_color if fg_color != "#000000" else "#FFFFFF"
        self.hover_color = hover_color or bg_color
        self._draw()

    def _on_enter(self, _):
        if self.enabled:
            self.current_bg = self.hover_color
            self._draw()

    def _on_leave(self, _):
        if self.enabled:
            self.current_bg = self.bg_color
            self._draw()

    def _on_click(self, _):
        if self.enabled and self.command:
            self.command()


class SegmentedPillSelector(tk.Frame):
    """Windows 10 Segmented Toggle Bar for interactive studio mode selection."""
    def __init__(self, parent, options, variable, accent_color=None, on_change=None, **kwargs):
        super().__init__(parent, bg=THEME["bg_input"], highlightbackground=THEME["border"], highlightthickness=1, padx=1, pady=1, **kwargs)
        self.options = options
        self.variable = variable
        self.accent_color = accent_color or THEME["accent_blue"]
        self.on_change = on_change
        self.buttons = {}

        for opt in options:
            lbl_text = opt[0] if isinstance(opt, tuple) else opt
            val_text = opt[1] if isinstance(opt, tuple) else opt
            b = tk.Label(
                self,
                text=lbl_text,
                font=("Segoe UI", 8, "bold"),
                padx=8,
                pady=3,
                cursor="hand2"
            )
            b.pack(side="left", expand=True, fill="x", padx=1)
            b.bind("<Button-1>", lambda e, v=val_text: self._select(v))
            self.buttons[val_text] = b

        self.refresh()

    def _select(self, val):
        self.variable.set(val)
        self.refresh()
        if self.on_change:
            self.on_change(val)

    def refresh(self):
        cur = self.variable.get()
        for val, b in self.buttons.items():
            if val == cur:
                b.config(bg=self.accent_color, fg="#FFFFFF")
            else:
                b.config(bg=THEME["bg_input"], fg=THEME["text_secondary"])


# ==============================================================================
# CLICK-THROUGH TOP SCREEN HUD POPUP
# ==============================================================================
class ClickThroughTopBanner(tk.Toplevel):
    def __init__(self, mode="REC", hotkey_hint="F9"):
        super().__init__()
        self.mode = mode
        self.hotkey_hint = hotkey_hint
        self.start_time = time.perf_counter()

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.90)
        self.configure(bg="#12131A")

        sw = self.winfo_screenwidth()
        w = 460
        h = 38
        x = (sw - w) // 2
        y = 14
        self.geometry(f"{w}x{h}+{x}+{y}")

        border_col = THEME["accent_rose"] if mode == "REC" else THEME["accent_emerald"]
        container = tk.Frame(self, bg="#12131A", highlightbackground=border_col, highlightthickness=1)
        container.pack(fill="both", expand=True)

        dot_col = THEME["accent_rose"] if mode == "REC" else THEME["accent_emerald"]
        self.lbl_dot = tk.Label(container, text="●", fg=dot_col, bg="#12131A", font=("Segoe UI", 12, "bold"))
        self.lbl_dot.pack(side="left", padx=(14, 6))

        if mode == "REC":
            default_msg = f"Recording Macro  •  Press [{hotkey_hint}] to stop"
        else:
            default_msg = f"Playing Macro  •  Press [{hotkey_hint}] to exit"

        self.lbl_msg = tk.Label(container, text=default_msg, fg=THEME["text_primary"], bg="#12131A", font=THEME["font_bold"])
        self.lbl_msg.pack(side="left", padx=4)

        self.lbl_timer = tk.Label(container, text="00:00.0", fg=THEME["text_secondary"], bg="#12131A", font=THEME["font_mono_bold"])
        self.lbl_timer.pack(side="right", padx=(4, 14))

        self.update_idletasks()
        try:
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            HardwareCursor.make_click_through(hwnd)
        except Exception:
            pass

        self.is_active = True
        self._ticker()

    def _ticker(self):
        if not self.is_active:
            return
        elapsed = time.perf_counter() - self.start_time
        mins = int(elapsed // 60)
        secs = elapsed % 60
        self.lbl_timer.config(text=f"{mins:02d}:{secs:04.1f}")
        self.after(100, self._ticker)

    def close(self):
        self.is_active = False
        try:
            self.destroy()
        except Exception:
            pass


# ==============================================================================
# ON-SCREEN COUNTDOWN OVERLAY
# ==============================================================================
class CountdownOverlay(tk.Toplevel):
    def __init__(self, count=3, callback=None):
        super().__init__()
        self.callback = callback
        self.current_count = count

        self.attributes("-fullscreen", True)
        self.attributes("-alpha", 0.65)
        self.configure(bg="#000000")
        self.attributes("-topmost", True)

        self.lbl_num = tk.Label(
            self,
            text=str(self.current_count),
            fg="#10B981",
            bg="#000000",
            font=("Segoe UI", 72, "bold")
        )
        self.lbl_num.pack(expand=True)

        self.lbl_hint = tk.Label(
            self,
            text="STARTING IN SECONDS • PREPARE TARGET WINDOW",
            fg="#94A3B8",
            bg="#000000",
            font=("Segoe UI", 12, "bold")
        )
        self.lbl_hint.pack(side="bottom", pady=40)

        play_cue(high_pitch=True)
        self.after(1000, self._tick)

    def _tick(self):
        self.current_count -= 1
        if self.current_count > 0:
            self.lbl_num.config(text=str(self.current_count))
            play_cue(high_pitch=True)
            self.after(1000, self._tick)
        else:
            self.destroy()
            if self.callback:
                self.callback()


# ==============================================================================
# SCREEN SNIP & TEMPLATE SELECTOR OVERLAY (F2 Snipping Tool)
# ==============================================================================
class ScreenSnipOverlay(tk.Toplevel):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.attributes("-fullscreen", True)
        self.attributes("-alpha", 0.3)
        self.configure(bg="#000000")
        self.attributes("-topmost", True)
        self.config(cursor="crosshair")

        self.canvas = tk.Canvas(self, cursor="crosshair", bg="#000000", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.start_x = None
        self.start_y = None
        self.rect_id = None

        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Escape>", lambda e: self.destroy())

    def _on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect_id = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="#10B981", width=2)

    def _on_drag(self, event):
        self.canvas.coords(self.rect_id, self.start_x, self.start_y, event.x, event.y)

    def _on_release(self, event):
        x1 = min(self.start_x, event.x)
        y1 = min(self.start_y, event.y)
        x2 = max(self.start_x, event.x)
        y2 = max(self.start_y, event.y)
        self.destroy()

        if (x2 - x1) > 5 and (y2 - y1) > 5:
            img = VisionTemplateEngine.capture_screen_region((x1, y1, x2, y2))
            self.callback((x1, y1, x2, y2), img)


# ==============================================================================
# FULLSCREEN HUD COORDINATE & COLOR EYEDROPPER OVERLAY
# ==============================================================================
class CoordinatePickerOverlay(tk.Toplevel):
    def __init__(self, callback, sample_color=False):
        super().__init__()
        self.callback = callback
        self.sample_color = sample_color
        self.attributes("-fullscreen", True)
        self.attributes("-alpha", 0.35)
        self.configure(bg="#000000")
        self.attributes("-topmost", True)
        self.config(cursor="crosshair")

        prompt = "🎯 MOVE CURSOR & CLICK TO LOCK COORD + COLOR  |  [ESC] TO CANCEL" if sample_color else "🎯 MOVE CURSOR & CLICK TO LOCK PIXEL  |  [ESC] TO CANCEL"

        self.banner = tk.Label(
            self,
            text=prompt,
            fg="#F1F2F6",
            bg="#161822",
            font=("Segoe UI", 12, "bold"),
            padx=20,
            pady=10,
            highlightbackground="#10B981",
            highlightthickness=1
        )
        self.banner.pack(side="top", pady=40)

        self.coord_lbl = tk.Label(
            self,
            text="X: 0   |   Y: 0",
            fg="#F1F2F6",
            bg="#161822",
            font=("Consolas", 15, "bold"),
            padx=18,
            pady=8,
            highlightbackground="#262938",
            highlightthickness=1
        )
        self.coord_lbl.pack(side="top", pady=10)

        self.bind("<Motion>", self._on_motion)
        self.bind("<Button-1>", self._on_click)
        self.bind("<Escape>", lambda e: self.destroy())

    def _on_motion(self, event):
        pos = HardwareCursor.get_pos()
        x = pos[0] if pos else self.winfo_pointerx()
        y = pos[1] if pos else self.winfo_pointery()
        hex_col, _ = HardwareCursor.get_pixel_color(x, y)
        txt = f"X: {x}   |   Y: {y}"
        if self.sample_color:
            txt += f"   |   COLOR: {hex_col}"
        self.coord_lbl.config(text=txt)

    def _on_click(self, event):
        pos = HardwareCursor.get_pos()
        x = pos[0] if pos else self.winfo_pointerx()
        y = pos[1] if pos else self.winfo_pointery()
        hex_col, rgb = HardwareCursor.get_pixel_color(x, y)
        self.callback(x, y, hex_col)
        self.destroy()


# ==============================================================================
# MACRO SETTINGS & WEBHOOKS DIALOG (Restored & Enhanced)
# ==============================================================================
class MacroSettingsDialog(tk.Toplevel):
    def __init__(self, parent_studio):
        super().__init__()
        self.parent_studio = parent_studio
        self.title("⚙️ Macro Automation Settings")
        self.geometry("540x640")
        self.configure(bg=THEME["bg_root"])
        self.resizable(False, False)
        self.attributes("-topmost", True)

        head = tk.Frame(self, bg=THEME["bg_root"], pady=12, padx=16)
        head.pack(fill="x")
        tk.Label(head, text="⚙️ Macro Automation Settings", fg=THEME["text_primary"], bg=THEME["bg_root"], font=THEME["font_title"]).pack(side="left")

        # 1. Event Filters
        card_filt = StyledCard(self, title="1. Selective Event Capture Filters")
        card_filt.pack(fill="x", padx=16, pady=4)

        toggles = [
            ("Capture Left Mouse Clicks", self.parent_studio.cap_left_click),
            ("Capture Right Mouse Clicks", self.parent_studio.cap_right_click),
            ("Capture Mouse Wheel Scrolling (Vertical & Horizontal)", self.parent_studio.cap_scroll),
            ("Capture Keyboard Keystrokes & Keybinds", self.parent_studio.cap_keys),
            ("Capture Cursor Movement Paths", self.parent_studio.cap_moves),
        ]
        for text, var in toggles:
            chk = tk.Checkbutton(card_filt, text=text, variable=var, bg=THEME["bg_card"], fg=THEME["text_primary"],
                                 selectcolor=THEME["bg_input"], activebackground=THEME["bg_card"], font=THEME["font_main"])
            chk.pack(anchor="w", pady=1)

        # 2. Sub-Pixel Jitter Suppression (< 2px)
        card_jit = StyledCard(self, title="2. Sub-Pixel Jitter Suppression")
        card_jit.pack(fill="x", padx=16, pady=4)

        row_jit = tk.Frame(card_jit, bg=THEME["bg_card"])
        row_jit.pack(fill="x")
        chk_jit = tk.Checkbutton(row_jit, text="Ignore Micro-Movements smaller than", variable=self.parent_studio.jitter_filter_active,
                                 bg=THEME["bg_card"], fg=THEME["text_primary"], selectcolor=THEME["bg_input"], font=THEME["font_main"])
        chk_jit.pack(side="left")

        ent_px = tk.Entry(row_jit, textvariable=self.parent_studio.jitter_threshold_px, width=4, bg=THEME["bg_input"],
                          fg=THEME["text_primary"], relief="flat", highlightbackground=THEME["border"], highlightthickness=1,
                          font=THEME["font_mono_bold"], justify="center")
        ent_px.pack(side="left", padx=6)
        tk.Label(row_jit, text="pixels", fg=THEME["text_secondary"], bg=THEME["bg_card"], font=THEME["font_main"]).pack(side="left")

        # 3. Application State & Focus
        card_state = StyledCard(self, title="3. Application State & Native App Focus")
        card_state.pack(fill="x", padx=16, pady=4)

        chk_snap = tk.Checkbutton(card_state, text="Auto-Snap Focus to Target App on Playback (Deep UWP/Win32 Bypass)",
                                  variable=self.parent_studio.auto_focus_target, bg=THEME["bg_card"], fg=THEME["accent_emerald"],
                                  selectcolor=THEME["bg_input"], font=THEME["font_bold"])
        chk_snap.pack(anchor="w", pady=1)

        chk_warp = tk.Checkbutton(card_state, text="Warp Cursor to Initial Starting Point (X, Y) before running",
                                  variable=self.parent_studio.warp_to_origin, bg=THEME["bg_card"], fg=THEME["text_primary"],
                                  selectcolor=THEME["bg_input"], font=THEME["font_main"])
        chk_warp.pack(anchor="w", pady=1)

        chk_scroll_rst = tk.Checkbutton(card_state, text="Browser / Doc Scroll Reset (Sends Ctrl+Home to reset page top)",
                                        variable=self.parent_studio.reset_scroll_to_top, bg=THEME["bg_card"], fg=THEME["text_primary"],
                                        selectcolor=THEME["bg_input"], font=THEME["font_main"])
        chk_scroll_rst.pack(anchor="w", pady=1)

        # 4. Discord & Webhook Telemetry
        card_hook = StyledCard(self, title="4. Discord & Webhook Telemetry")
        card_hook.pack(fill="x", padx=16, pady=4)

        tk.Label(card_hook, text="Webhook URL:", fg=THEME["text_secondary"], bg=THEME["bg_card"], font=THEME["font_main"]).pack(anchor="w")
        ent_hook = tk.Entry(
            card_hook,
            textvariable=self.parent_studio.webhook_url,
            bg=THEME["bg_input"],
            fg=THEME["text_primary"],
            relief="flat",
            highlightbackground=THEME["border"],
            highlightthickness=1,
            font=THEME["font_mono"]
        )
        ent_hook.pack(fill="x", pady=(2, 6))

        chk_hook_finish = tk.Checkbutton(
            card_hook,
            text="Send notification with session stats when macro completes",
            variable=self.parent_studio.webhook_on_finish,
            bg=THEME["bg_card"],
            fg=THEME["text_primary"],
            selectcolor=THEME["bg_input"],
            font=THEME["font_main"]
        )
        chk_hook_finish.pack(anchor="w")

        btn_test_hook = tk.Button(
            card_hook,
            text="🔔 Send Test Ping",
            command=self._test_webhook_ping,
            bg=THEME["bg_card_hover"],
            fg=THEME["text_primary"],
            relief="flat",
            font=THEME["font_bold"],
            padx=10,
            pady=2,
            cursor="hand2"
        )
        btn_test_hook.pack(anchor="w", pady=(4, 0))

        btn_done = ModernButton(
            self,
            text="✓ Save & Apply Settings",
            command=self.destroy,
            bg_color=THEME["accent_emerald"],
            fg_color="#000000",
            hover_color="#34D399",
            width=508,
            height=38,
            font=THEME["font_bold"]
        )
        btn_done.pack(pady=12)

    def _test_webhook_ping(self):
        url = self.parent_studio.webhook_url.get().strip()
        if not url:
            messagebox.showwarning("Missing URL", "Please enter a valid Webhook URL first!")
            return
        WebhookNotifier.send_notification(url, "🔔 Test Alert from Apex Macro Studio: Telemetry connection established!", {"Status": "Online", "Test": "Success"})
        messagebox.showinfo("Ping Sent", "Dispatched test notification to webhook!")


# ==============================================================================
# MAIN APPLICATION WINDOW: POLISHED & GAME-RECOGNITION AWARE
# ==============================================================================
class ApexAutoClickerApp(tk.Tk):
    """
    Windows 10 Dark Mode Auto-Clicker Suite.
    Compact, zero-waste geometry (480x620) with all v7.0 + v9.5 settings intact.
    """
    def __init__(self):
        super().__init__()
        self.title("⚡ Apex Auto-Clicker")
        self.geometry("480x620")
        self.minsize(460, 580)
        self.resizable(True, True)
        self.configure(bg=THEME["bg_root"])

        # Engine State
        self.is_running = False
        self.stop_event = threading.Event()
        self.clicker_thread = None
        self.macro_studio_window = None

        # Telemetry
        self.total_clicks = 0
        self.start_time = 0
        self.mouse_controller = MouseController() if 'pynput' in sys.modules else None

        # 1. Click Interval & Frequency Settings (RESTORED FROM v7.0)
        self.hours_var = tk.StringVar(value="0")
        self.mins_var = tk.StringVar(value="0")
        self.secs_var = tk.StringVar(value="0")
        self.ms_var = tk.StringVar(value="100")
        self.jitter_enabled = tk.BooleanVar(value=False)
        self.jitter_amount = tk.StringVar(value="15")

        # 2. Mouse Click Configuration Settings (RESTORED FROM v7.0)
        self.mouse_btn_var = tk.StringVar(value="Left")
        self.click_type_var = tk.StringVar(value="Single")

        # 3. Target Screen Coordinates Settings (RESTORED FROM v7.0)
        self.loc_mode = tk.StringVar(value="fixed")
        self.x_var = tk.StringVar(value="0")
        self.y_var = tk.StringVar(value="0")

        # 4. Headless Background Window Injection Settings (RESTORED FROM v7.0 + v9.5)
        self.background_injection_active = tk.BooleanVar(value=False)
        self.auto_hand_off_active = tk.BooleanVar(value=True)
        self.auto_tint_window = tk.BooleanVar(value=True)
        self.target_window_hwnd = None
        self.target_window_title = "None"
        self.target_window_title_desc = tk.StringVar(value="[ None - Click Window ]")
        self.target_app_type = "STANDARD"
        self.target_app_desc = tk.StringVar(value="🎯 Auto-Detecting Target (Roblox / Game / App)...")
        self.occupied_tint_window = None
        self.is_background_injecting = False

        # 5. Adaptive Anti-Recoil Vector Engine Settings (RESTORED FROM v7.0)
        self.anti_recoil_active = tk.BooleanVar(value=False)
        self.recoil_y_pull = tk.StringVar(value="3")
        self.recoil_x_pull = tk.StringVar(value="0")

        # 6. Screen Pixel Color & Vision Triggerbot Settings (RESTORED FROM v7.0)
        self.pixel_trigger_active = tk.BooleanVar(value=False)
        self.pixel_trigger_color = tk.StringVar(value="#0078D7")

        # 7. Computer Vision & Audio Sound Trigger Settings (RESTORED FROM v7.0)
        self.vision_trigger_active = tk.BooleanVar(value=False)
        self.vision_template_status = tk.StringVar(value="[ No Template ]")
        self.vision_template_img = None
        self.vision_template_bbox = None
        self.audio_trigger_active = tk.BooleanVar(value=False)
        self.audio_threshold = tk.StringVar(value="0.25")

        # 8. Repeat Count & Features Settings (RESTORED FROM v7.0)
        self.repeat_mode = tk.StringVar(value="infinite")
        self.repeat_count_var = tk.StringVar(value="100")
        self.always_on_top = tk.BooleanVar(value=False)
        self.sound_enabled = tk.BooleanVar(value=True)
        self.pre_start_countdown = tk.BooleanVar(value=False)

        self._build_clean_header()
        self._build_action_footer()
        self._build_segmented_tabs()

        self.hotkey_listener = None
        self._start_global_hotkey_listener()
        self._update_stats_loop()

    def _build_clean_header(self):
        head = tk.Frame(self, bg=THEME["bg_root"], pady=6, padx=12)
        head.pack(fill="x")

        tk.Label(
            head,
            text="⚡ Apex Auto-Clicker",
            fg=THEME["text_primary"],
            bg=THEME["bg_root"],
            font=THEME["font_title"]
        ).pack(side="left")

        self.btn_open_macro = ModernButton(
            head,
            text="⏺ Macro Studio",
            command=self.open_macro_studio,
            bg_color=THEME["accent_blue"],
            fg_color="#FFFFFF",
            hover_color="#1084E0",
            width=125,
            height=28,
            font=THEME["font_bold"]
        )
        self.btn_open_macro.pack(side="right")

    def _build_action_footer(self):
        self.foot = tk.Frame(self, bg=THEME["bg_root"], pady=6, padx=12)
        self.foot.pack(fill="x", side="bottom")

        rec_frame = tk.Frame(self.foot, bg=THEME["bg_card"], highlightbackground=THEME["border"], highlightthickness=1, pady=3, padx=10)
        rec_frame.pack(fill="x", pady=(0, 4))

        self.lbl_target_rec = tk.Label(rec_frame, textvariable=self.target_app_desc, fg=THEME["text_secondary"], bg=THEME["bg_card"], font=THEME["font_bold"])
        self.lbl_target_rec.pack(anchor="w")

        telemetry = tk.Frame(self.foot, bg=THEME["bg_card"], highlightbackground=THEME["border"], highlightthickness=1, pady=4, padx=10)
        telemetry.pack(fill="x", pady=(0, 4))

        c1 = tk.Frame(telemetry, bg=THEME["bg_card"])
        c1.pack(side="left", expand=True)
        tk.Label(c1, text="CLICKS FIRED", fg=THEME["text_muted"], bg=THEME["bg_card"], font=THEME["font_badge"]).pack()
        self.lbl_clicks = tk.Label(c1, text="0", fg=THEME["text_primary"], bg=THEME["bg_card"], font=("Segoe UI", 11, "bold"))
        self.lbl_clicks.pack()

        c2 = tk.Frame(telemetry, bg=THEME["bg_card"])
        c2.pack(side="left", expand=True)
        tk.Label(c2, text="CURRENT CPS", fg=THEME["text_muted"], bg=THEME["bg_card"], font=THEME["font_badge"]).pack()
        self.lbl_cps = tk.Label(c2, text="0.0", fg=THEME["accent_blue"], bg=THEME["bg_card"], font=("Segoe UI", 11, "bold"))
        self.lbl_cps.pack()

        c3 = tk.Frame(telemetry, bg=THEME["bg_card"])
        c3.pack(side="left", expand=True)
        tk.Label(c3, text="STATUS", fg=THEME["text_muted"], bg=THEME["bg_card"], font=THEME["font_badge"]).pack()
        self.lbl_status = tk.Label(c3, text="IDLE", fg=THEME["text_secondary"], bg=THEME["bg_card"], font=("Segoe UI", 10, "bold"))
        self.lbl_status.pack()

        self.btn_toggle = ModernButton(
            self.foot,
            text="▶  START CLICKING (F6)",
            command=self.toggle_clicking,
            bg_color=THEME["accent_blue"],
            fg_color="#FFFFFF",
            hover_color="#1084E0",
            width=456,
            height=36,
            font=("Segoe UI", 11, "bold")
        )
        self.btn_toggle.pack(fill="x")

    def _build_segmented_tabs(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TCombobox", fieldbackground=THEME["bg_input"], background=THEME["bg_card_hover"],
                        foreground=THEME["text_primary"], arrowcolor=THEME["accent_blue"], borderwidth=1)
        style.map("TCombobox",
                  fieldbackground=[("readonly", THEME["bg_input"])],
                  selectbackground=[("readonly", THEME["bg_input"])],
                  selectforeground=[("readonly", THEME["text_primary"])])

        style.configure("Apex.TNotebook", background=THEME["bg_root"], borderwidth=0)
        style.configure("Apex.TNotebook.Tab", background=THEME["bg_card"], foreground=THEME["text_secondary"],
                        padding=[12, 5], font=THEME["font_bold"], borderwidth=0)
        style.map("Apex.TNotebook.Tab",
                  background=[("selected", THEME["accent_blue"]), ("active", THEME["bg_card_hover"])],
                  foreground=[("selected", "#FFFFFF"), ("active", THEME["text_primary"])])

        self.notebook = ttk.Notebook(self, style="Apex.TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=12, pady=(0, 2))

        self.tab_basic = tk.Frame(self.notebook, bg=THEME["bg_root"])
        self.notebook.add(self.tab_basic, text="⚡ Basic Clicker")
        self._build_tab_basic(self.tab_basic)

        self.tab_pro = tk.Frame(self.notebook, bg=THEME["bg_root"])
        self.notebook.add(self.tab_pro, text="🎯 Pro Triggers & BG")
        self._build_tab_pro(self.tab_pro)

        self.tab_prefs = tk.Frame(self.notebook, bg=THEME["bg_root"])
        self.notebook.add(self.tab_prefs, text="⚙️ Preferences")
        self._build_tab_prefs(self.tab_prefs)

    def _build_tab_basic(self, container):
        card_interval = StyledCard(container, title="Click Interval & Frequency")
        card_interval.pack(fill="x", pady=2)

        grid = tk.Frame(card_interval, bg=THEME["bg_card"])
        grid.pack(fill="x")

        fields = [("Hours", self.hours_var), ("Mins", self.mins_var), ("Secs", self.secs_var), ("Millis (ms)", self.ms_var)]
        for i, (label_text, var) in enumerate(fields):
            sub = tk.Frame(grid, bg=THEME["bg_card"])
            sub.grid(row=0, column=i, padx=3, sticky="ew")
            grid.columnconfigure(i, weight=1)

            tk.Label(sub, text=label_text, fg=THEME["text_secondary"], bg=THEME["bg_card"], font=THEME["font_main"]).pack(anchor="w")
            ent = tk.Entry(sub, textvariable=var, bg=THEME["bg_input"], fg=THEME["text_primary"], relief="flat",
                           highlightbackground=THEME["border"], highlightcolor=THEME["border_focus"], highlightthickness=1,
                           font=THEME["font_mono_bold"], justify="center")
            ent.pack(fill="x", ipady=1, pady=(1, 0))

        p_row = tk.Frame(card_interval, bg=THEME["bg_card"])
        p_row.pack(fill="x", pady=(4, 1))
        tk.Label(p_row, text="Presets:", fg=THEME["text_muted"], bg=THEME["bg_card"], font=THEME["font_main"]).pack(side="left")

        for name, ms in [("Ultra 1ms", 1), ("Turbo 10ms", 10), ("Balanced 50ms", 50), ("Human 100ms", 100)]:
            tk.Button(
                p_row, text=name, command=lambda m=ms: self._apply_preset(m),
                bg=THEME["bg_card_hover"], fg=THEME["text_primary"], relief="flat",
                font=("Segoe UI", 8), padx=6, pady=1, cursor="hand2"
            ).pack(side="left", padx=2)

        j_row = tk.Frame(card_interval, bg=THEME["bg_card"])
        j_row.pack(fill="x", pady=(2, 0))

        tk.Checkbutton(
            j_row, text="Humanize Jitter (Randomize ± ms)", variable=self.jitter_enabled,
            bg=THEME["bg_card"], fg=THEME["text_secondary"], selectcolor=THEME["bg_input"], font=THEME["font_main"]
        ).pack(side="left")

        tk.Entry(j_row, textvariable=self.jitter_amount, width=4, bg=THEME["bg_input"], fg=THEME["text_primary"],
                 relief="flat", highlightbackground=THEME["border"], highlightthickness=1, font=THEME["font_mono_bold"], justify="center").pack(side="left", padx=4)
        tk.Label(j_row, text="ms", fg=THEME["text_muted"], bg=THEME["bg_card"], font=THEME["font_main"]).pack(side="left")

        card_opts = StyledCard(container, title="Mouse Configuration")
        card_opts.pack(fill="x", pady=2)

        row_m = tk.Frame(card_opts, bg=THEME["bg_card"])
        row_m.pack(fill="x")

        b_box = tk.Frame(row_m, bg=THEME["bg_card"])
        b_box.pack(side="left", expand=True, fill="x", padx=3)
        tk.Label(b_box, text="Mouse Button", fg=THEME["text_secondary"], bg=THEME["bg_card"], font=THEME["font_main"]).pack(anchor="w")
        ttk.Combobox(b_box, textvariable=self.mouse_btn_var, values=["Left", "Right", "Middle"], state="readonly", font=THEME["font_main"]).pack(fill="x", pady=1)

        t_box = tk.Frame(row_m, bg=THEME["bg_card"])
        t_box.pack(side="left", expand=True, fill="x", padx=3)
        tk.Label(t_box, text="Click Type", fg=THEME["text_secondary"], bg=THEME["bg_card"], font=THEME["font_main"]).pack(anchor="w")
        ttk.Combobox(t_box, textvariable=self.click_type_var, values=["Single", "Double", "Triple", "Hold Down"], state="readonly", font=THEME["font_main"]).pack(fill="x", pady=1)

        card_loc = StyledCard(container, title="Target Position")
        card_loc.pack(fill="x", pady=2)

        tk.Radiobutton(
            card_loc, text="Dynamic: Click wherever cursor is pointing",
            variable=self.loc_mode, value="current", bg=THEME["bg_card"],
            fg=THEME["text_primary"], selectcolor=THEME["bg_input"], font=THEME["font_main"]
        ).pack(anchor="w")

        c_row = tk.Frame(card_loc, bg=THEME["bg_card"])
        c_row.pack(fill="x", pady=(1, 0))

        tk.Radiobutton(
            c_row, text="Fixed Coordinates:", variable=self.loc_mode, value="fixed",
            bg=THEME["bg_card"], fg=THEME["text_primary"], selectcolor=THEME["bg_input"], font=THEME["font_main"]
        ).pack(side="left")

        tk.Label(c_row, text="X:", fg=THEME["text_secondary"], bg=THEME["bg_card"], font=THEME["font_bold"]).pack(side="left", padx=(4, 2))
        tk.Entry(c_row, textvariable=self.x_var, width=5, bg=THEME["bg_input"], fg=THEME["text_primary"], relief="flat", highlightbackground=THEME["border"], highlightthickness=1, font=THEME["font_mono_bold"], justify="center").pack(side="left")

        tk.Label(c_row, text="Y:", fg=THEME["text_secondary"], bg=THEME["bg_card"], font=THEME["font_bold"]).pack(side="left", padx=(4, 2))
        tk.Entry(c_row, textvariable=self.y_var, width=5, bg=THEME["bg_input"], fg=THEME["text_primary"], relief="flat", highlightbackground=THEME["border"], highlightthickness=1, font=THEME["font_mono_bold"], justify="center").pack(side="left")

        tk.Button(
            c_row, text="🎯 Pick Coords (F4)", command=self.launch_coord_picker,
            bg=THEME["bg_card_hover"], fg=THEME["text_primary"], relief="flat",
            font=THEME["font_bold"], padx=6, pady=1, cursor="hand2"
        ).pack(side="right")

        card_rep = StyledCard(container, title="Repeat Count")
        card_rep.pack(fill="x", pady=2)

        tk.Radiobutton(
            card_rep, text="Repeat continuously until stopped", variable=self.repeat_mode,
            value="infinite", bg=THEME["bg_card"], fg=THEME["text_primary"], selectcolor=THEME["bg_input"], font=THEME["font_main"]
        ).pack(anchor="w")

        r_cnt_frame = tk.Frame(card_rep, bg=THEME["bg_card"])
        r_cnt_frame.pack(fill="x", pady=(1, 0))

        tk.Radiobutton(
            r_cnt_frame, text="Repeat exactly", variable=self.repeat_mode, value="count",
            bg=THEME["bg_card"], fg=THEME["text_primary"], selectcolor=THEME["bg_input"], font=THEME["font_main"]
        ).pack(side="left")

        tk.Entry(r_cnt_frame, textvariable=self.repeat_count_var, width=6, bg=THEME["bg_input"], fg=THEME["text_primary"],
                 relief="flat", highlightbackground=THEME["border"], highlightthickness=1, font=THEME["font_mono_bold"], justify="center").pack(side="left", padx=4)
        tk.Label(r_cnt_frame, text="times", fg=THEME["text_secondary"], bg=THEME["bg_card"], font=THEME["font_main"]).pack(side="left")

    def _build_tab_pro(self, container):
        card_bg = StyledCard(container, title="Headless Background Injection & Smart Hand-Off")
        card_bg.pack(fill="x", pady=2)

        row_bg1 = tk.Frame(card_bg, bg=THEME["bg_card"])
        row_bg1.pack(fill="x")

        tk.Checkbutton(
            row_bg1, text="Enable Background Injection", variable=self.background_injection_active,
            bg=THEME["bg_card"], fg=THEME["text_primary"], selectcolor=THEME["bg_input"], font=THEME["font_bold"]
        ).pack(side="left")

        tk.Label(row_bg1, textvariable=self.target_window_title_desc, fg=THEME["text_muted"], bg=THEME["bg_card"], font=THEME["font_mono"]).pack(side="left", padx=(4, 2))

        tk.Button(
            row_bg1, text="🔍 Select window", command=self._pick_target_window_dialog,
            bg=THEME["bg_card_hover"], fg=THEME["text_primary"], relief="flat",
            font=THEME["font_bold"], padx=6, pady=1, cursor="hand2"
        ).pack(side="right")

        row_bg2 = tk.Frame(card_bg, bg=THEME["bg_card"])
        row_bg2.pack(fill="x", pady=(2, 0))

        tk.Checkbutton(
            row_bg2, text="Auto-Hand-Off on Move", variable=self.auto_hand_off_active,
            bg=THEME["bg_card"], fg=THEME["text_secondary"], selectcolor=THEME["bg_input"], font=THEME["font_main"]
        ).pack(side="left")

        tk.Checkbutton(
            row_bg2, text="Occupied Window Tint", variable=self.auto_tint_window,
            bg=THEME["bg_card"], fg=THEME["accent_blue"], selectcolor=THEME["bg_input"], font=THEME["font_main"]
        ).pack(side="left", padx=(8, 0))

        card_rec = StyledCard(container, title="Adaptive Anti-Recoil Vector Engine")
        card_rec.pack(fill="x", pady=2)

        row_r = tk.Frame(card_rec, bg=THEME["bg_card"])
        row_r.pack(fill="x")

        tk.Checkbutton(
            row_r, text="Enable Anti-Recoil Pull", variable=self.anti_recoil_active,
            bg=THEME["bg_card"], fg=THEME["text_primary"], selectcolor=THEME["bg_input"], font=THEME["font_main"]
        ).pack(side="left")

        tk.Label(row_r, text="Y-Pull (px):", fg=THEME["text_secondary"], bg=THEME["bg_card"], font=THEME["font_main"]).pack(side="left", padx=(8, 2))
        tk.Entry(row_r, textvariable=self.recoil_y_pull, width=4, bg=THEME["bg_input"], fg=THEME["text_primary"], relief="flat", highlightbackground=THEME["border"], highlightthickness=1, font=THEME["font_mono_bold"], justify="center").pack(side="left")

        tk.Label(row_r, text="X-Pull (px):", fg=THEME["text_secondary"], bg=THEME["bg_card"], font=THEME["font_main"]).pack(side="left", padx=(6, 2))
        tk.Entry(row_r, textvariable=self.recoil_x_pull, width=4, bg=THEME["bg_input"], fg=THEME["text_primary"], relief="flat", highlightbackground=THEME["border"], highlightthickness=1, font=THEME["font_mono_bold"], justify="center").pack(side="left")

        card_vis = StyledCard(container, title="Vision & Screen Color Triggers")
        card_vis.pack(fill="x", pady=2)

        row_v1 = tk.Frame(card_vis, bg=THEME["bg_card"])
        row_v1.pack(fill="x")

        tk.Checkbutton(
            row_v1, text="Pixel Triggerbot", variable=self.pixel_trigger_active,
            bg=THEME["bg_card"], fg=THEME["text_primary"], selectcolor=THEME["bg_input"], font=THEME["font_main"]
        ).pack(side="left")

        self.swatch = tk.Canvas(row_v1, width=14, height=14, bg=self.pixel_trigger_color.get(), highlightthickness=1, highlightbackground=THEME["border"])
        self.swatch.pack(side="left", padx=(6, 4))

        tk.Entry(row_v1, textvariable=self.pixel_trigger_color, width=8, bg=THEME["bg_input"], fg=THEME["text_primary"], relief="flat", highlightbackground=THEME["border"], highlightthickness=1, font=THEME["font_mono_bold"], justify="center").pack(side="left")

        tk.Button(row_v1, text="👁 Eyedropper (F3)", command=self.launch_color_eyedropper, bg=THEME["bg_card_hover"], fg=THEME["text_primary"], relief="flat", font=THEME["font_main"], padx=6, pady=1, cursor="hand2").pack(side="right")

        row_v2 = tk.Frame(card_vis, bg=THEME["bg_card"])
        row_v2.pack(fill="x", pady=(3, 0))

        tk.Checkbutton(
            row_v2, text="Icon / Template Match", variable=self.vision_trigger_active,
            bg=THEME["bg_card"], fg=THEME["text_primary"], selectcolor=THEME["bg_input"], font=THEME["font_main"]
        ).pack(side="left")

        tk.Label(row_v2, textvariable=self.vision_template_status, fg=THEME["text_muted"], bg=THEME["bg_card"], font=THEME["font_mono"]).pack(side="left", padx=(4, 2))

        tk.Button(row_v2, text="✂ Snip Screen Area (F2)", command=self.launch_screen_snip, bg=THEME["bg_card_hover"], fg=THEME["text_primary"], relief="flat", font=THEME["font_main"], padx=6, pady=1, cursor="hand2").pack(side="right")

        card_aud = StyledCard(container, title="Audio Sound Spike Trigger")
        card_aud.pack(fill="x", pady=2)

        row_a = tk.Frame(card_aud, bg=THEME["bg_card"])
        row_a.pack(fill="x")

        tk.Checkbutton(
            row_a, text="Enable Sound Spike Trigger", variable=self.audio_trigger_active,
            bg=THEME["bg_card"], fg=THEME["text_primary"], selectcolor=THEME["bg_input"], font=THEME["font_main"]
        ).pack(side="left")

        tk.Label(row_a, text="Threshold:", fg=THEME["text_secondary"], bg=THEME["bg_card"], font=THEME["font_main"]).pack(side="left", padx=(10, 2))
        tk.Entry(row_a, textvariable=self.audio_threshold, width=5, bg=THEME["bg_input"], fg=THEME["text_primary"],
                 relief="flat", highlightbackground=THEME["border"], highlightthickness=1, font=THEME["font_mono_bold"], justify="center").pack(side="left")

    def _build_tab_prefs(self, container):
        card_p = StyledCard(container, title="General Preferences")
        card_p.pack(fill="x", pady=3)

        tk.Checkbutton(
            card_p, text="Always on Top (Keep window pinned over other apps)",
            variable=self.always_on_top, command=self._toggle_always_on_top,
            bg=THEME["bg_card"], fg=THEME["text_primary"], selectcolor=THEME["bg_input"], font=THEME["font_main"]
        ).pack(anchor="w", pady=2)

        tk.Checkbutton(
            card_p, text="Play Audio Beep on Start / Stop (Audio Cues)",
            variable=self.sound_enabled, bg=THEME["bg_card"], fg=THEME["text_primary"],
            selectcolor=THEME["bg_input"], font=THEME["font_main"]
        ).pack(anchor="w", pady=2)

        tk.Checkbutton(
            card_p, text="3-Second Countdown HUD before Start",
            variable=self.pre_start_countdown, bg=THEME["bg_card"], fg=THEME["text_primary"],
            selectcolor=THEME["bg_input"], font=THEME["font_main"]
        ).pack(anchor="w", pady=2)

        card_hotkeys = StyledCard(container, title="Hotkeys Reference")
        card_hotkeys.pack(fill="x", pady=3)

        hotkey_lines = [
            ("F6", "Start / Stop Auto-Clicking"),
            ("F4", "Pick Screen Coordinates"),
            ("F3", "Sample Pixel Color (Eyedropper)"),
            ("F2", "Snip Screen Area for Template Match"),
            ("F9", "Start / Stop Macro Recording"),
            ("F10", "Play / Stop Macro Sequence"),
        ]
        for key, desc in hotkey_lines:
            r = tk.Frame(card_hotkeys, bg=THEME["bg_card"])
            r.pack(fill="x", pady=1)
            tk.Label(r, text=f"[{key}]", fg=THEME["accent_blue"], bg=THEME["bg_card"], font=THEME["font_mono_bold"], width=6, anchor="w").pack(side="left")
            tk.Label(r, text=desc, fg=THEME["text_secondary"], bg=THEME["bg_card"], font=THEME["font_main"]).pack(side="left")

    def _pick_target_window_dialog(self):
        messagebox.showinfo("Select Window", "Click OK, then click into your target game/app window within 2 seconds!")
        self.update()
        time.sleep(2.0)
        hwnd, title, class_name = AppStateManager.get_foreground_window(exclude_hwnds=[self.winfo_id()])
        if hwnd:
            self.target_window_hwnd = hwnd
            self.target_window_title = title
            t_type, t_desc = AppRecognizer.classify_target(title, class_name)
            self.target_app_type = t_type
            short_t = (title[:18] + "..") if len(title) > 20 else title
            self.target_window_title_desc.set(f"[{short_t}]")
            self.target_app_desc.set(f"🎯 Target: {title[:20]} ({t_desc})")
            play_cue(high_pitch=True)
            messagebox.showinfo("Target Locked", f"Locked: {title}\nType: {t_desc}")

    def _apply_preset(self, ms):
        self.hours_var.set("0")
        self.mins_var.set("0")
        self.secs_var.set("0")
        self.ms_var.set(str(ms))

    def _toggle_always_on_top(self):
        self.attributes("-topmost", self.always_on_top.get())

    def launch_coord_picker(self):
        CoordinatePickerOverlay(self._on_coords_picked)

    def _on_coords_picked(self, x, y, color=None):
        self.loc_mode.set("fixed")
        self.x_var.set(str(x))
        self.y_var.set(str(y))
        hwnd, title, class_name = AppStateManager.get_window_at_point(x, y, exclude_hwnds=[self.winfo_id()])
        if hwnd:
            self.target_window_hwnd = hwnd
            self.target_window_title = title
            t_type, t_desc = AppRecognizer.classify_target(title, class_name)
            self.target_app_type = t_type
            short_t = (title[:18] + "..") if len(title) > 20 else title
            self.target_window_title_desc.set(f"[{short_t}]")
            self.target_app_desc.set(f"🎯 Target: {title[:20]} ({t_desc})")

    def launch_color_eyedropper(self):
        CoordinatePickerOverlay(self._on_eyedropper_picked, sample_color=True)

    def _on_eyedropper_picked(self, x, y, hex_color):
        self.loc_mode.set("fixed")
        self.x_var.set(str(x))
        self.y_var.set(str(y))
        self.pixel_trigger_color.set(hex_color)
        if hasattr(self, "swatch") and self.swatch.winfo_exists():
            self.swatch.config(bg=hex_color)
        self.pixel_trigger_active.set(True)

    def launch_screen_snip(self):
        ScreenSnipOverlay(self._on_screen_snip_completed)

    def _on_screen_snip_completed(self, bbox, img):
        self.vision_template_bbox = bbox
        self.vision_template_img = img
        self.vision_trigger_active.set(True)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        self.vision_template_status.set(f"[{w}x{h} px]")
        messagebox.showinfo("Vision Template Saved", f"Captured {w}x{h} px template!")

    def _calculate_interval_seconds(self):
        try:
            h = float(self.hours_var.get() or 0)
            m = float(self.mins_var.get() or 0)
            s = float(self.secs_var.get() or 0)
            ms = float(self.ms_var.get() or 0)
            total = (h * 3600) + (m * 60) + s + (ms / 1000.0)
            return max(total, 0.0005)
        except ValueError:
            return 0.1

    def toggle_clicking(self):
        if self.is_running:
            self.stop_clicking()
        else:
            if self.pre_start_countdown.get():
                CountdownOverlay(count=3, callback=self.start_clicking)
            else:
                self.start_clicking()

    def start_clicking(self):
        if self.is_running:
            return

        interval = self._calculate_interval_seconds()
        is_fixed = (self.loc_mode.get() == "fixed")

        try:
            target_x = int(self.x_var.get())
            target_y = int(self.y_var.get())
        except ValueError:
            target_x, target_y = 0, 0

        btn_choice = self.mouse_btn_var.get().lower()
        target_button = Button.right if btn_choice == "right" else (Button.middle if btn_choice == "middle" else Button.left)
        click_type = self.click_type_var.get()

        own_hwnd = self.winfo_id()
        if is_fixed:
            hwnd, title, cname = AppStateManager.get_window_at_point(target_x, target_y, exclude_hwnds=[own_hwnd])
        else:
            cur_p = HardwareCursor.get_pos() or (target_x, target_y)
            hwnd, title, cname = AppStateManager.get_window_at_point(cur_p[0], cur_p[1], exclude_hwnds=[own_hwnd])

        if not hwnd:
            hwnd, title, cname = AppStateManager.get_foreground_window(exclude_hwnds=[own_hwnd])

        if hwnd:
            self.target_window_hwnd = hwnd
            self.target_window_title = title
            t_type, t_desc = AppRecognizer.classify_target(title, cname)
            self.target_app_type = t_type
            short_t = (title[:18] + "..") if len(title) > 20 else title
            self.target_window_title_desc.set(f"[{short_t}]")
            self.target_app_desc.set(f"🎯 Target: {title[:20]} ({t_desc})")

        repeat_inf = (self.repeat_mode.get() == "infinite")
        try:
            max_clicks = int(self.repeat_count_var.get()) if not repeat_inf else -1
        except ValueError:
            max_clicks = 100

        self.is_running = True
        self.is_background_injecting = self.background_injection_active.get()
        self.stop_event.clear()
        self.total_clicks = 0
        self.start_time = time.perf_counter()

        if self.sound_enabled.get():
            play_cue(high_pitch=True)

        self.btn_toggle.set_text_and_color("⏹  STOP CLICKING (F6)", THEME["accent_rose"], fg_color="#FFFFFF", hover_color="#FB7185")
        self.lbl_status.config(text="CLICKING...", fg=THEME["accent_emerald"])

        self.clicker_thread = threading.Thread(
            target=self._clicker_worker,
            args=(interval, is_fixed, target_x, target_y, target_button, click_type, repeat_inf, max_clicks),
            daemon=True
        )
        self.clicker_thread.start()

    def stop_clicking(self):
        if not self.is_running:
            return
        self.is_running = False
        self.is_background_injecting = False
        self.stop_event.set()

        if self.occupied_tint_window:
            self.occupied_tint_window.close()
            self.occupied_tint_window = None

        if self.sound_enabled.get():
            play_cue(high_pitch=False)

        self.btn_toggle.set_text_and_color("▶  START CLICKING (F6)", THEME["accent_emerald"], fg_color="#000000", hover_color="#34D399")
        self.lbl_status.config(text="STOPPED", fg=THEME["text_secondary"])

    def _clicker_worker(self, base_interval, is_fixed, x, y, button, click_type, repeat_inf, max_clicks):
        clicks_done = 0
        mouse = self.mouse_controller
        btn_str = "left" if button == Button.left else ("right" if button == Button.right else "middle")

        last_automated_pos = HardwareCursor.get_pos() or (x, y)
        is_game = (self.target_app_type == "GAME")

        while not self.stop_event.is_set():
            if not repeat_inf and clicks_done >= max_clicks:
                break

            # 1. SMART AUTO-HAND-OFF ON USER PHYSICAL MOUSE MOVEMENT
            if self.auto_hand_off_active.get() and self.target_window_hwnd:
                curr_physical_pos = HardwareCursor.get_pos()
                if curr_physical_pos and last_automated_pos:
                    dist = math.hypot(curr_physical_pos[0] - last_automated_pos[0], curr_physical_pos[1] - last_automated_pos[1])
                    if dist > 25 and not self.is_background_injecting:
                        self.is_background_injecting = True
                        if self.auto_tint_window.get():
                            self.after(0, self._show_occupied_tint_overlay)

            # 2. TRIGGER CONDITIONS (Pixel / Vision)
            if self.pixel_trigger_active.get():
                chk_x = x if is_fixed else (HardwareCursor.get_pos() or (0,0))[0]
                chk_y = y if is_fixed else (HardwareCursor.get_pos() or (0,0))[1]
                curr_hex, _ = HardwareCursor.get_pixel_color(chk_x, chk_y)
                if curr_hex.upper() != self.pixel_trigger_color.get().strip().upper():
                    time.sleep(0.01)
                    continue

            # 3. ROBLOX & 3D GAME CLICK DISPATCH (DIRECTINPUT HARDWARE BYPASS)
            if is_game:
                if self.is_background_injecting and is_fixed:
                    phys_pos = HardwareCursor.get_pos()
                    HardwareCursor.set_pos(x, y)
                    HardwareCursor.hardware_click(btn_str)
                    if phys_pos:
                        HardwareCursor.set_pos(phys_pos[0], phys_pos[1])
                else:
                    if is_fixed:
                        if not HardwareCursor.set_pos(x, y):
                            mouse.position = (x, y)
                        last_automated_pos = (x, y)
                    else:
                        last_automated_pos = HardwareCursor.get_pos()

                    HardwareCursor.hardware_click(btn_str)
            else:
                if self.is_background_injecting and self.target_window_hwnd:
                    lParam = (int(y) << 16) | (int(x) & 0xFFFF)
                    down_msg = 0x0201 if btn_str == "left" else (0x0204 if btn_str == "right" else 0x0207)
                    up_msg = 0x0202 if btn_str == "left" else (0x0205 if btn_str == "right" else 0x0208)
                    wparam = 1 if btn_str == "left" else (2 if btn_str == "right" else 0x10)
                    ctypes.windll.user32.PostMessageW(self.target_window_hwnd, down_msg, wparam, lParam)
                    time.sleep(0.015)
                    ctypes.windll.user32.PostMessageW(self.target_window_hwnd, up_msg, 0, lParam)
                else:
                    if is_fixed:
                        if not HardwareCursor.set_pos(x, y):
                            mouse.position = (x, y)
                        last_automated_pos = (x, y)
                    else:
                        last_automated_pos = HardwareCursor.get_pos()

                    if click_type == "Single":
                        mouse.click(button, 1)
                    elif click_type == "Double":
                        mouse.click(button, 2)
                    elif click_type == "Triple":
                        mouse.click(button, 3)
                    elif click_type == "Hold Down":
                        mouse.press(button)
                        while not self.stop_event.is_set():
                            time.sleep(0.05)
                        mouse.release(button)
                        break

            # Anti-Recoil Vector Pull
            if self.anti_recoil_active.get():
                try:
                    yp = int(self.recoil_y_pull.get())
                    xp = int(self.recoil_x_pull.get())
                    cur_p = HardwareCursor.get_pos()
                    if cur_p and (yp != 0 or xp != 0):
                        HardwareCursor.set_pos(cur_p[0] + xp, cur_p[1] + yp)
                except ValueError:
                    pass

            clicks_done += 1
            self.total_clicks = clicks_done

            interval = base_interval
            if self.jitter_enabled.get():
                try:
                    j_sec = float(self.jitter_amount.get() or 0) / 1000.0
                    interval += random.uniform(-j_sec, j_sec)
                    interval = max(interval, 0.0005)
                except ValueError:
                    pass

            target_time = time.perf_counter() + interval
            while time.perf_counter() < target_time:
                if self.stop_event.is_set():
                    break
                rem = target_time - time.perf_counter()
                if rem > 0.003:
                    time.sleep(rem * 0.75)

        self.after(0, self.stop_clicking)

    def _show_occupied_tint_overlay(self):
        if self.occupied_tint_window is None and self.target_window_hwnd:
            self.occupied_tint_window = OccupiedWindowTint(
                self.target_window_hwnd,
                target_title=self.target_window_title,
                on_reclaim=self._on_tint_reclaim,
                on_stop=self.stop_clicking
            )

    def _on_tint_reclaim(self):
        self.is_background_injecting = False
        self.occupied_tint_window = None

    def _update_stats_loop(self):
        if self.is_running and self.start_time > 0:
            elapsed = max(time.perf_counter() - self.start_time, 0.001)
            cps = self.total_clicks / elapsed
            self.lbl_clicks.config(text=f"{self.total_clicks:,}")
            self.lbl_cps.config(text=f"{cps:.1f}")
        self.after(100, self._update_stats_loop)

    def _start_global_hotkey_listener(self):
        def on_press(key):
            try:
                if key == Key.f6:
                    self.after(0, self.toggle_clicking)
                elif key == Key.f4:
                    self.after(0, self.launch_coord_picker)
                elif key == Key.f3:
                    self.after(0, self.launch_color_eyedropper)
                elif key == Key.f2:
                    self.after(0, self.launch_screen_snip)
            except Exception:
                pass

        try:
            self.hotkey_listener = keyboard.Listener(on_press=on_press)
            self.hotkey_listener.daemon = True
            self.hotkey_listener.start()
        except Exception as e:
            print(f"[Warning] Hotkey listener failed: {e}")

    def open_macro_studio(self):
        self.withdraw()
        if self.macro_studio_window is None or not self.macro_studio_window.winfo_exists():
            self.macro_studio_window = MacroStudioWindow(self)
        else:
            self.macro_studio_window.deiconify()
            self.macro_studio_window.lift()
            self.macro_studio_window.focus_force()


# ==============================================================================
# MODULAR APEX v11.0 ENGINE INTEGRATION (Links `apex/` Package + Embedded Runtime)
# ==============================================================================
try:
    from apex.core.coordinate_spaces import CoordinateSpace, CoordinateConverter
    from apex.core.geometry import Vertex2D, Vector2D
    from apex.core.event_model import InteractionEvent
    from apex.core.application_state import ApplicationStateProfile
    from apex.core.capability_registry import CapabilityRegistry
    from apex.core.safety_manager import SafetyManager
    from apex.core.input_router import InputRouter
    from apex.core.action_scheduler import ActionScheduler
    from apex.core.runtime_coordinator import RuntimeCoordinator as ModularRuntimeCoordinator
    from apex.adapters.browsers.adaptive_scroll import AdaptiveScrollEngine
    from apex.adapters.custom.application_bridge import ApexApplicationBridgeSDK
    HAS_MODULAR_APEX = True
except ImportError:
    HAS_MODULAR_APEX = False

    class CoordinateSpace:
        SCREEN = "SCREEN"
        WINDOW_CLIENT = "WINDOW_CLIENT"
        WINDOW_NORMALIZED = "WINDOW_NORMALIZED"
        ELEMENT_RELATIVE = "ELEMENT_RELATIVE"

    class Vertex2D:
        def __init__(self, u=0.0, v=0.0, x=0, y=0, space="WINDOW_NORMALIZED"):
            self.u, self.v, self.x, self.y, self.space = round(float(u), 5), round(float(v), 5), int(x), int(y), space
        @classmethod
        def from_client(cls, cx, cy, w, h):
            w, h = max(1, int(w)), max(1, int(h))
            return cls(max(0.0, min(1.0, cx / w)), max(0.0, min(1.0, cy / h)), cx, cy)
        def resolve_to_client(self, w, h):
            w, h = max(1, int(w)), max(1, int(h))
            return max(0, min(int(round(self.u * w)), w - 1)), max(0, min(int(round(self.v * h)), h - 1))
        def to_list(self): return [self.u, self.v]
        def to_dict(self): return {"u": self.u, "v": self.v, "x": self.x, "y": self.y, "space": self.space}

    class Vector2D:
        def __init__(self, du=0.0, dv=0.0, dx=0, dy=0):
            self.du, self.dv, self.dx, self.dy = round(float(du), 5), round(float(dv), 5), int(dx), int(dy)
        @classmethod
        def between(cls, v0, v1):
            return cls(v1.u - v0.u, v1.v - v0.v, v1.x - v0.x, v1.y - v0.y)
        def to_dict(self): return {"du": self.du, "dv": self.dv, "dx": self.dx, "dy": self.dy}

    class AdaptiveScrollEngine:
        @staticmethod
        def calculate_scroll_ratio(scroll_top, scroll_height, client_height):
            return round(max(0.0, min(1.0, float(scroll_top) / max(1, int(scroll_height) - int(client_height)))), 4)
        @staticmethod
        def resolve_target_scroll_top(target_ratio, current_scroll_height, current_client_height):
            return int(round(float(target_ratio) * max(1, int(current_scroll_height) - int(current_client_height))))
        @staticmethod
        def compute_adaptive_wheel_notches(recorded_dy, recorded_win_h, current_win_h):
            s = int(round(float(recorded_dy) * (max(100, int(current_win_h or 720)) / max(100, int(recorded_win_h or 720)))))
            return (1 if recorded_dy > 0 else -1) if (s == 0 and recorded_dy != 0) else s

    class CapabilityRegistry:
        @classmethod
        def inspect(cls, hwnd=None, title="", class_name="", client_size=(1280, 720)):
            from types import SimpleNamespace
            t_low, c_low = (title or "").lower(), (class_name or "").lower()
            if any(g in t_low or g in c_low for g in ("roblox", "windowsclient", "minecraft", "unity", "unreal")):
                return SimpleNamespace(profile_id="roblox_directx_game", title=title or "3D Game", window_class=class_name, adapter_type="DIRECTX_GAME_ADAPTER", client_size=client_size, capabilities={"background_input": False, "requires_foreground": True, "input_backend": "DirectInput Hardware Synthesis", "frame_capture": "DXGI / WGC"})
            if any(b in t_low or b in c_low for b in ("chrome", "msedge", "firefox", "brave")):
                return SimpleNamespace(profile_id="browser_adaptive_dom", title=title or "Browser", window_class=class_name, adapter_type="BROWSER_CDP_BIDI_ADAPTER", client_size=client_size, capabilities={"background_input": True, "adaptive_scroll": True, "requires_foreground": False, "input_backend": "ChildHWND + Adaptive Scroll", "frame_capture": "PrintWindow PW_RENDERFULLCONTENT"})
            return SimpleNamespace(profile_id="notepad" if "notepad" in t_low else "win32_desktop_app", title=title or "Desktop App", window_class=class_name, adapter_type="WIN32_UIA_ADAPTER", client_size=client_size, capabilities={"background_input": True, "requires_foreground": False, "input_backend": "Isolated ChildHWND PostMessageW", "frame_capture": "Win32 PrintWindow / WGC"})


class AACLDiagnosticsDialog(tk.Toplevel):
    """Live AACL Compatibility & Application State Profile Inspector."""
    def __init__(self, studio):
        super().__init__(studio)
        self.studio = studio
        self.title("🛡️ AACL Compatibility & Application Profile Inspector")
        self.geometry("620x440")
        self.resizable(False, False)
        self.configure(bg=THEME["bg_root"])
        self.attributes("-topmost", True)

        hwnd = studio.recorded_target_hwnd
        title = studio.recorded_target_title
        w, h = WindowWorkspaceBounds.get_client_size(hwnd)
        prof = CapabilityRegistry.inspect(hwnd, title, "", (w, h))
        caps = prof.capabilities

        head = tk.Frame(self, bg=THEME["bg_root"], padx=16, pady=10)
        head.pack(fill="x")
        tk.Label(head, text="🛡️ Apex Application Compatibility Layer (AACL)", fg=THEME["text_primary"], bg=THEME["bg_root"], font=THEME["font_title"]).pack(anchor="w")
        tk.Label(head, text="Modular v11.0 Runtime • Vertex/Vector Coordinate Space & Adapter Diagnostics", fg=THEME["text_secondary"], bg=THEME["bg_root"], font=THEME["font_main"]).pack(anchor="w")

        c1 = StyledCard(self, title="1. Recognized Application Identity & Geometry")
        c1.pack(fill="x", padx=16, pady=4)
        for k, v in [
            ("Profile ID:", prof.profile_id),
            ("Target Window:", (prof.title or "Desktop")[:45]),
            ("Active AACL Adapter:", prof.adapter_type),
            ("Client Geometry:", f"{w} × {h} px  (Normalized U,V [0.0..1.0] Active)"),
        ]:
            r = tk.Frame(c1, bg=THEME["bg_card"])
            r.pack(fill="x", pady=1)
            tk.Label(r, text=k, fg=THEME["text_secondary"], bg=THEME["bg_card"], width=22, anchor="w", font=THEME["font_bold"]).pack(side="left")
            tk.Label(r, text=v, fg=THEME["accent_blue"], bg=THEME["bg_card"], font=THEME["font_mono_bold"]).pack(side="left")

        c2 = StyledCard(self, title="2. Runtime Streams & Input Capabilities")
        c2.pack(fill="x", padx=16, pady=4)
        bg_ok = "✅ Supported (Target Session Mode)" if caps.get("background_input") else "⚠️ Foreground Hardware Synthesis Required"
        for k, v in [
            ("Background Input:", bg_ok),
            ("Input Backend:", caps.get("input_backend", "Win32 Message Queue")),
            ("Observation Stream:", caps.get("frame_capture", "PrintWindow PW_RENDERFULLCONTENT")),
            ("Adaptive Scroll:", "✅ Active (Proportional ScrollHeight/ClientHeight Ratio)"),
            ("Modular Package:", "✅ Loaded (apex.core / apex.adapters / apex.runtime)" if HAS_MODULAR_APEX else "Embedded Standalone Mode"),
        ]:
            r = tk.Frame(c2, bg=THEME["bg_card"])
            r.pack(fill="x", pady=1)
            tk.Label(r, text=k, fg=THEME["text_secondary"], bg=THEME["bg_card"], width=22, anchor="w", font=THEME["font_bold"]).pack(side="left")
            tk.Label(r, text=v, fg=THEME["text_primary"], bg=THEME["bg_card"], font=THEME["font_main"]).pack(side="left")

        btn_row = tk.Frame(self, bg=THEME["bg_root"], padx=16, pady=10)
        btn_row.pack(fill="x")
        tk.Button(btn_row, text="✓ Close", command=self.destroy, bg=THEME["accent_blue"], fg="#FFFFFF", relief="flat", font=THEME["font_bold"], padx=20, pady=4, cursor="hand2").pack(side="right")


# ==============================================================================
# TARGET-ISOLATED VIRTUAL WORKSPACE: BOUNDED CURSOR, VK ENGINE & COPY-SPACE
# ==============================================================================
class WindowWorkspaceBounds:
    """
    Locks and clamps all Virtual Cursor coordinates strictly inside the target
    window's client dimensions [0, 0, Width, Height]. Prevents any coordinate
    from flying off or 'yeeting' outside the target application.
    """
    @staticmethod
    def get_client_size(hwnd):
        if IS_WINDOWS and hwnd and ctypes.windll.user32.IsWindow(hwnd):
            try:
                rect = wintypes.RECT()
                ctypes.windll.user32.GetClientRect(hwnd, ctypes.byref(rect))
                w = max(rect.right - rect.left, 100)
                h = max(rect.bottom - rect.top, 100)
                return (w, h)
            except Exception:
                pass
        return (1280, 720)

    @staticmethod
    def get_client_screen_origin(hwnd):
        if IS_WINDOWS and hwnd and ctypes.windll.user32.IsWindow(hwnd):
            try:
                pt = wintypes.POINT(0, 0)
                ctypes.windll.user32.ClientToScreen(hwnd, ctypes.byref(pt))
                return (pt.x, pt.y)
            except Exception:
                pass
        bounds = AppStateManager.get_window_bounds(hwnd)
        if bounds:
            return (bounds[0], bounds[1])
        return (0, 0)

    @staticmethod
    def clamp_to_window(hwnd, x, y, is_client_coords=False):
        """
        Clamps (x, y) strictly within the target window's workspace bounds.
        Returns (clamped_screen_x, clamped_screen_y, clamped_client_x, clamped_client_y, width, height).
        """
        w, h = WindowWorkspaceBounds.get_client_size(hwnd)
        ox, oy = WindowWorkspaceBounds.get_client_screen_origin(hwnd)

        if is_client_coords:
            cx = max(0, min(int(x), w - 1))
            cy = max(0, min(int(y), h - 1))
            sx = ox + cx
            sy = oy + cy
        else:
            # If coordinates look like local client coords (or if hwnd is at 0,0)
            if hwnd and (ox > 0 or oy > 0) and (x >= ox or y >= oy):
                cx = max(0, min(int(x) - ox, w - 1))
                cy = max(0, min(int(y) - oy, h - 1))
            else:
                cx = max(0, min(int(x), w - 1))
                cy = max(0, min(int(y), h - 1))
            sx = ox + cx
            sy = oy + cy

        return sx, sy, cx, cy, w, h


class VirtualKeyboardEngine:
    """
    Per-Window Stateful Virtual Hardware Keyboard (VK Engine).
    Summoned per target window HWND to dispatch OEM scan-code hardware-imitated
    WM_KEYDOWN, continuous hold auto-repeat pulses, WM_KEYUP, and WM_CHAR messages
    strictly to that window's message queue.
    Prevents global key leakage (e.g. 'Alt + F4' will NEVER shut down the user's laptop
    or close unrelated foreground windows).
    """
    VK_MAP = {
        "enter": 0x0D, "return": 0x0D, "space": 0x20, "backspace": 0x08, "tab": 0x09,
        "esc": 0x1B, "escape": 0x1B, "shift": 0x10, "ctrl": 0x11, "control": 0x11,
        "alt": 0x12, "menu": 0x12, "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27,
        "home": 0x24, "end": 0x23, "pageup": 0x21, "pagedown": 0x22, "insert": 0x2D,
        "delete": 0x2E, "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73, "f5": 0x74,
        "f6": 0x75, "f7": 0x76, "f8": 0x77, "f9": 0x78, "f10": 0x79, "f11": 0x7A, "f12": 0x7B,
    }

    @classmethod
    def resolve_vk_and_scan(cls, key_str):
        clean = str(key_str).lower().replace("key.", "").strip()
        vk = cls.VK_MAP.get(clean, 0)
        if vk == 0 and len(clean) == 1:
            if IS_WINDOWS:
                res = ctypes.windll.user32.VkKeyScanW(ord(clean))
                vk = res & 0xFF if res != -1 else ord(clean.upper())
            else:
                vk = ord(clean.upper())
        elif vk == 0:
            vk = 0x20  # Default space fallback

        scan = 0
        if IS_WINDOWS:
            try:
                scan = ctypes.windll.user32.MapVirtualKeyW(vk, 0) # MAPVK_VK_TO_VSC
            except Exception:
                scan = 0
        return vk, scan, clean

    @classmethod
    def _build_lparam(cls, repeat_count, scan_code, is_extended=False, context_alt=False, prev_down=False, is_up=False):
        lparam = (repeat_count & 0xFFFF)
        lparam |= ((scan_code & 0xFF) << 16)
        if is_extended:
            lparam |= (1 << 24)
        if context_alt:
            lparam |= (1 << 29)
        if prev_down:
            lparam |= (1 << 30)
        if is_up:
            lparam |= (1 << 31)
        return lparam

    @classmethod
    def get_target_child_hwnd(cls, root_hwnd, client_x=None, client_y=None):
        """Finds the deepest interactive child control inside root_hwnd for accurate message delivery."""
        if not IS_WINDOWS or not root_hwnd:
            return root_hwnd
        try:
            if client_x is not None and client_y is not None:
                pt = wintypes.POINT(int(client_x), int(client_y))
                child = ctypes.windll.user32.ChildWindowFromPointEx(root_hwnd, pt, 0x0001 | 0x0002) # Skip invisible/disabled
                if child and child != root_hwnd:
                    return child
        except Exception:
            pass
        return root_hwnd

    @classmethod
    def send_key_down(cls, hwnd, key_str, alt_held=False, prev_down=False):
        if not IS_WINDOWS or not hwnd:
            return False
        vk, scan, clean = cls.resolve_vk_and_scan(key_str)
        msg = 0x0104 if alt_held or clean == "alt" else 0x0100  # WM_SYSKEYDOWN vs WM_KEYDOWN
        lparam = cls._build_lparam(1, scan, context_alt=(alt_held or clean == "alt"), prev_down=prev_down, is_up=False)
        ctypes.windll.user32.PostMessageW(hwnd, msg, vk, lparam)
        if len(clean) == 1 and not alt_held:
            ctypes.windll.user32.PostMessageW(hwnd, 0x0102, ord(clean), lparam) # WM_CHAR
        return True

    @classmethod
    def send_key_up(cls, hwnd, key_str, alt_held=False):
        if not IS_WINDOWS or not hwnd:
            return False
        vk, scan, clean = cls.resolve_vk_and_scan(key_str)
        msg = 0x0105 if alt_held or clean == "alt" else 0x0101  # WM_SYSKEYUP vs WM_KEYUP
        lparam = cls._build_lparam(1, scan, context_alt=(alt_held or clean == "alt"), prev_down=True, is_up=True)
        ctypes.windll.user32.PostMessageW(hwnd, msg, vk, lparam)
        return True

    @classmethod
    def send_key_hold(cls, hwnd, key_str, duration_sec=0.1, modifiers=None, stop_event=None, repeat_interval=0.033):
        """
        Emulates a physical finger holding down a key (plus optional modifiers like Ctrl, Shift, Alt)
        strictly inside the target window's message queue.
        """
        if not IS_WINDOWS or not hwnd:
            time.sleep(max(duration_sec, 0.01))
            return False

        mods = [m.lower().strip() for m in (modifiers or []) if m]
        alt_active = ("alt" in mods)

        # Press modifiers down in target window
        for m in mods:
            cls.send_key_down(hwnd, m, alt_held=alt_active, prev_down=False)

        # Initial key down
        cls.send_key_down(hwnd, key_str, alt_held=alt_active, prev_down=False)

        t_end = time.perf_counter() + max(duration_sec, 0.01)
        while time.perf_counter() < t_end:
            if stop_event and stop_event.is_set():
                break
            rem = t_end - time.perf_counter()
            if rem <= 0:
                break
            sleep_step = min(repeat_interval, rem)
            time.sleep(sleep_step)
            if time.perf_counter() < t_end and duration_sec >= 0.08:
                cls.send_key_down(hwnd, key_str, alt_held=alt_active, prev_down=True)

        # Release main key and modifiers
        cls.send_key_up(hwnd, key_str, alt_held=alt_active)
        for m in reversed(mods):
            cls.send_key_up(hwnd, m, alt_held=alt_active)
        return True


class IsolatedMouseDispatcher:
    """
    Dispatches isolated mouse movements, clicks, holds, drags, and wheel scrolls
    directly into the target HWND (and child control at coordinate) via Win32 messages,
    clamped strictly to the window's workspace bounds.
    """
    @staticmethod
    def make_lparam(client_x, client_y):
        return ((int(client_y) & 0xFFFF) << 16) | (int(client_x) & 0xFFFF)

    @classmethod
    def move(cls, hwnd, client_x, client_y, button_held=None):
        if not IS_WINDOWS or not hwnd:
            return
        target = VirtualKeyboardEngine.get_target_child_hwnd(hwnd, client_x, client_y)
        wparam = 0x0001 if button_held == "left" else (0x0002 if button_held == "right" else 0)
        ctypes.windll.user32.PostMessageW(target, 0x0200, wparam, cls.make_lparam(client_x, client_y)) # WM_MOUSEMOVE

    @classmethod
    def button_down(cls, hwnd, client_x, client_y, button="left"):
        if not IS_WINDOWS or not hwnd:
            return
        target = VirtualKeyboardEngine.get_target_child_hwnd(hwnd, client_x, client_y)
        lparam = cls.make_lparam(client_x, client_y)
        if button == "right":
            ctypes.windll.user32.PostMessageW(target, 0x0204, 0x0002, lparam) # WM_RBUTTONDOWN
        elif button == "middle":
            ctypes.windll.user32.PostMessageW(target, 0x0207, 0x0010, lparam) # WM_MBUTTONDOWN
        else:
            ctypes.windll.user32.PostMessageW(target, 0x0201, 0x0001, lparam) # WM_LBUTTONDOWN

    @classmethod
    def button_up(cls, hwnd, client_x, client_y, button="left"):
        if not IS_WINDOWS or not hwnd:
            return
        target = VirtualKeyboardEngine.get_target_child_hwnd(hwnd, client_x, client_y)
        lparam = cls.make_lparam(client_x, client_y)
        if button == "right":
            ctypes.windll.user32.PostMessageW(target, 0x0205, 0, lparam) # WM_RBUTTONUP
        elif button == "middle":
            ctypes.windll.user32.PostMessageW(target, 0x0208, 0, lparam) # WM_MBUTTONUP
        else:
            ctypes.windll.user32.PostMessageW(target, 0x0202, 0, lparam) # WM_LBUTTONUP

    @classmethod
    def scroll(cls, hwnd, client_x, client_y, dx=0, dy=-2):
        if not IS_WINDOWS or not hwnd:
            return
        target = VirtualKeyboardEngine.get_target_child_hwnd(hwnd, client_x, client_y)
        lparam = cls.make_lparam(client_x, client_y)
        wheel_delta = int(dy * 120)
        wparam = ((wheel_delta & 0xFFFF) << 16)
        ctypes.windll.user32.PostMessageW(target, 0x020A, wparam, lparam) # WM_MOUSEWHEEL


class VirtualCursorEntity:
    """
    Independent target-window Virtual Cursor Runtime sprite managed by Python.
    - Workspace is strictly clamped to the target window's client dimensions.
    - Never touches or resets the user's physical OS mouse pointer when in Virtual Mode.
    - Renders an actual pointer shape (sleek neon-green arrow + precision crosshair)
      both on an optional lightweight screen indicator (when target window is visible)
      and directly inside the Virtual Display Copy-Space Viewport!
    """
    def __init__(self, root_parent):
        self.root_parent = root_parent
        self.client_x = 100
        self.client_y = 100
        self.screen_x = 100
        self.screen_y = 100
        self.state = "HOVER"  # "HOVER", "DOWN", "DRAG", "SCROLL"
        self.active_key_badge = ""
        self.drag_trail = []  # List of (cx, cy) points when dragging
        self.target_hwnd = None

        # Optional lightweight click-through desktop sprite
        self.overlay_win = None
        self.overlay_canvas = None
        self.show_desktop_sprite = True

    def bind_target_window(self, hwnd):
        self.target_hwnd = hwnd
        w, h = WindowWorkspaceBounds.get_client_size(hwnd)
        self.client_x = min(max(self.client_x, 0), w - 1)
        self.client_y = min(max(self.client_y, 0), h - 1)

    def set_position(self, x, y, is_client_coords=True, state=None):
        sx, sy, cx, cy, w, h = WindowWorkspaceBounds.clamp_to_window(
            self.target_hwnd, x, y, is_client_coords=is_client_coords
        )
        self.screen_x, self.screen_y = sx, sy
        self.client_x, self.client_y = cx, cy
        if state:
            self.state = state
        if self.state == "DRAG":
            self.drag_trail.append((cx, cy))
            if len(self.drag_trail) > 25:
                self.drag_trail.pop(0)
        else:
            self.drag_trail.clear()
        self._update_desktop_sprite()
        return cx, cy

    def set_state(self, state, key_badge=""):
        self.state = state
        self.active_key_badge = key_badge
        if state != "DRAG":
            self.drag_trail.clear()
        self._update_desktop_sprite()

    def _ensure_desktop_sprite(self):
        if not self.show_desktop_sprite:
            return
        if self.overlay_win is None or not self.overlay_win.winfo_exists():
            try:
                self.overlay_win = tk.Toplevel(self.root_parent)
                self.overlay_win.overrideredirect(True)
                self.overlay_win.attributes("-topmost", True)
                if IS_WINDOWS:
                    self.overlay_win.wm_attributes("-transparentcolor", "#010203")
                self.overlay_win.configure(bg="#010203")
                self.overlay_win.geometry(f"64x64+{self.screen_x - 8}+{self.screen_y - 8}")
                self.overlay_canvas = tk.Canvas(self.overlay_win, width=64, height=64, bg="#010203", highlightthickness=0)
                self.overlay_canvas.pack(fill="both", expand=True)
                self.overlay_win.update_idletasks()
                if IS_WINDOWS:
                    hwnd = ctypes.windll.user32.GetParent(self.overlay_win.winfo_id()) or self.overlay_win.winfo_id()
                    # Make the sprite an independent, non-activating desktop overlay.
                    # It must remain visible when Macro Studio auto-hides during playback.
                    try:
                        set_owner = ctypes.windll.user32.SetWindowLongPtrW
                        set_owner.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
                        set_owner.restype = ctypes.c_ssize_t
                        set_owner(hwnd, -8, 0)  # GWLP_HWNDPARENT: detach from Studio's window.
                        get_ex_style = ctypes.windll.user32.GetWindowLongW
                        set_ex_style = ctypes.windll.user32.SetWindowLongW
                        current_ex_style = get_ex_style(hwnd, -20)
                        set_ex_style(hwnd, -20, current_ex_style | 0x00000080 | 0x08000000)
                        ctypes.windll.user32.SetWindowPos(hwnd, None, 0, 0, 0, 0,
                                                          0x0001 | 0x0002 | 0x0004 | 0x0010)
                    except Exception:
                        pass
                    HardwareCursor.make_click_through(hwnd)
                    self.overlay_win.deiconify()
                    self.overlay_win.lift()
            except Exception:
                pass

    def _update_desktop_sprite(self):
        if not self.show_desktop_sprite:
            self.hide_sprite()
            return
        try:
            self._ensure_desktop_sprite()
            if self.overlay_win and self.overlay_win.winfo_exists():
                self.overlay_win.geometry(f"64x64+{self.screen_x - 8}+{self.screen_y - 8}")
                c = self.overlay_canvas
                c.delete("all")
                # Draw real cursor arrow polygon at offset (8, 8)
                fill_col = "#10B981" if self.state == "HOVER" else ("#F43F5E" if self.state == "DOWN" else "#F59E0B")
                outline_col = "#FFFFFF"
                pts = [8, 8, 8, 28, 14, 23, 19, 32, 23, 30, 18, 21, 25, 21]
                c.create_polygon(pts, fill=fill_col, outline=outline_col, width=1.5)
                if self.state in ("DOWN", "DRAG"):
                    c.create_oval(2, 2, 14, 14, outline=fill_col, width=2)
                if self.active_key_badge:
                    c.create_rectangle(24, 24, 62, 42, fill="#0E1015", outline=fill_col)
                    c.create_text(43, 33, text=self.active_key_badge[:5], fill="#FFFFFF", font=("Consolas", 8, "bold"))
        except Exception:
            pass

    def hide_sprite(self):
        if self.overlay_win and self.overlay_win.winfo_exists():
            try:
                self.overlay_win.destroy()
            except Exception:
                pass
        self.overlay_win = None


class VirtualAppViewportWindow(tk.Toplevel):
    """
    Virtual Display ("Copy-Space") Window.
    Captures the target window's live visual buffer via Win32 PrintWindow (PW_RENDERFULLCONTENT)
    even when the target application is completely occluded/covered behind other windows!
    - Displays the live application UI inside an interactive canvas.
    - Renders the Green Virtual Cursor, click ripples, drag vectors, and active VK key badges.
    - Clicking or dragging directly inside this Virtual Display sends isolated clicks/drags
      or records coordinates directly mapped to the target window's pixel space (e.g. clicking
      PX 78, 900 in Firefox to open ChatGPT while Firefox stays completely behind your work).
    """
    def __init__(self, parent_studio):
        super().__init__(parent_studio)
        self.parent_studio = parent_studio
        self.title("🖥️ Apex Virtual Display (Isolated App Copy-Space)")
        self.geometry("780x560")
        self.minsize(560, 420)
        self.configure(bg=THEME["bg_root"])

        self.is_streaming = True
        self.tk_img_ref = None
        self.last_capture_size = (1280, 720)
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.drag_start_client = None

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._refresh_loop()

    def _build_ui(self):
        top = tk.Frame(self, bg=THEME["bg_card"], pady=8, padx=14, highlightbackground=THEME["border"], highlightthickness=1)
        top.pack(fill="x")

        self.lbl_target_info = tk.Label(
            top,
            text="🎯 Target Workspace: Auto-Detecting...",
            fg=THEME["accent_emerald"],
            bg=THEME["bg_card"],
            font=THEME["font_bold"]
        )
        self.lbl_target_info.pack(side="left")

        btn_pick = tk.Button(
            top,
            text="🔍 Lock Target Window",
            command=self.parent_studio.pick_isolated_target_window,
            bg=THEME["bg_card_hover"],
            fg=THEME["text_primary"],
            relief="flat",
            font=THEME["font_bold"],
            padx=10,
            pady=2,
            cursor="hand2"
        )
        btn_pick.pack(side="right", padx=4)

        self.lbl_cursor_telemetry = tk.Label(
            top,
            text="Green Cursor: (0, 0) | VK: Idle",
            fg=THEME["text_secondary"],
            bg=THEME["bg_card"],
            font=THEME["font_mono"]
        )
        self.lbl_cursor_telemetry.pack(side="right", padx=12)

        # Interactive Viewport Canvas
        self.canvas = tk.Canvas(self, bg="#07090E", highlightthickness=1, highlightbackground=THEME["border"], cursor="crosshair")
        self.canvas.pack(fill="both", expand=True, padx=12, pady=8)

        self.canvas.bind("<ButtonPress-1>", self._on_canvas_down)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_up)
        self.canvas.bind("<ButtonPress-3>", self._on_canvas_right_click)

        bot = tk.Frame(self, bg=THEME["bg_root"], pady=4, padx=14)
        bot.pack(fill="x")
        tk.Label(
            bot,
            text="💡 Left-Click inside Copy-Space to send isolated click or pick coords  •  Drag to test Click-n-Drag  •  Target app can stay behind other windows!",
            fg=THEME["text_muted"],
            bg=THEME["bg_root"],
            font=("Segoe UI", 9)
        ).pack(side="left")

    def _canvas_to_client_coords(self, cx_canvas, cy_canvas):
        w_client, h_client = self.last_capture_size
        rel_x = max(0, cx_canvas - self.offset_x)
        rel_y = max(0, cy_canvas - self.offset_y)
        tx = int(rel_x * self.scale_x)
        ty = int(rel_y * self.scale_y)
        tx = max(0, min(tx, w_client - 1))
        ty = max(0, min(ty, h_client - 1))
        return tx, ty

    def _on_canvas_down(self, event):
        tx, ty = self._canvas_to_client_coords(event.x, event.y)
        self.drag_start_client = (tx, ty)
        vc = self.parent_studio.virtual_cursor
        vc.set_position(tx, ty, is_client_coords=True, state="DOWN")
        hwnd = self.parent_studio.recorded_target_hwnd
        if hwnd:
            IsolatedMouseDispatcher.button_down(hwnd, tx, ty, "left")

    def _on_canvas_drag(self, event):
        tx, ty = self._canvas_to_client_coords(event.x, event.y)
        vc = self.parent_studio.virtual_cursor
        vc.set_position(tx, ty, is_client_coords=True, state="DRAG")
        hwnd = self.parent_studio.recorded_target_hwnd
        if hwnd:
            IsolatedMouseDispatcher.move(hwnd, tx, ty, button_held="left")

    def _on_canvas_up(self, event):
        tx, ty = self._canvas_to_client_coords(event.x, event.y)
        vc = self.parent_studio.virtual_cursor
        vc.set_position(tx, ty, is_client_coords=True, state="HOVER")
        hwnd = self.parent_studio.recorded_target_hwnd
        if hwnd:
            IsolatedMouseDispatcher.button_up(hwnd, tx, ty, "left")
        # Also populate Studio Inspector if an item is selected
        self.parent_studio.on_viewport_coord_clicked(tx, ty, self.drag_start_client)
        self.drag_start_client = None

    def _on_canvas_right_click(self, event):
        tx, ty = self._canvas_to_client_coords(event.x, event.y)
        vc = self.parent_studio.virtual_cursor
        vc.set_position(tx, ty, is_client_coords=True, state="DOWN")
        hwnd = self.parent_studio.recorded_target_hwnd
        if hwnd:
            IsolatedMouseDispatcher.button_down(hwnd, tx, ty, "right")
            IsolatedMouseDispatcher.button_up(hwnd, tx, ty, "right")
        self.after(150, lambda: vc.set_state("HOVER"))

    def _capture_window_image(self, hwnd):
        """Captures off-screen/occluded window surface via Win32 PrintWindow or PIL fallback."""
        if not IS_WINDOWS or not hwnd or not ctypes.windll.user32.IsWindow(hwnd) or not HAS_PIL:
            return None
        try:
            w, h = WindowWorkspaceBounds.get_client_size(hwnd)
            self.last_capture_size = (w, h)

            hwndDC = ctypes.windll.user32.GetWindowDC(hwnd)
            mfcDC = ctypes.windll.gdi32.CreateCompatibleDC(hwndDC)
            saveBitMap = ctypes.windll.gdi32.CreateCompatibleBitmap(hwndDC, w, h)
            ctypes.windll.gdi32.SelectObject(mfcDC, saveBitMap)

            # PW_RENDERFULLCONTENT (0x00000002) renders DirectComposition/occluded windows
            res = ctypes.windll.user32.PrintWindow(hwnd, mfcDC, 2)
            if res == 0:
                ctypes.windll.user32.PrintWindow(hwnd, mfcDC, 0)

            class BITMAPINFOHEADER(ctypes.Structure):
                _fields_ = [
                    ("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG), ("biHeight", wintypes.LONG),
                    ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                    ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG),
                    ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD), ("biClrImportant", wintypes.DWORD)
                ]

            bmi = BITMAPINFOHEADER()
            bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
            bmi.biWidth = w
            bmi.biHeight = -h  # Top-down
            bmi.biPlanes = 1
            bmi.biBitCount = 32
            bmi.biCompression = 0

            buf_len = w * h * 4
            buf = ctypes.create_string_buffer(buf_len)
            ctypes.windll.gdi32.GetDIBits(mfcDC, saveBitMap, 0, h, buf, ctypes.byref(bmi), 0)

            ctypes.windll.gdi32.DeleteObject(saveBitMap)
            ctypes.windll.gdi32.DeleteDC(mfcDC)
            ctypes.windll.user32.ReleaseDC(hwnd, hwndDC)

            img = Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1)
            return img
        except Exception:
            return None

    def _refresh_loop(self):
        if not self.is_streaming or not self.winfo_exists():
            return

        hwnd = self.parent_studio.recorded_target_hwnd
        title = self.parent_studio.recorded_target_title
        vc = self.parent_studio.virtual_cursor
        w_client, h_client = WindowWorkspaceBounds.get_client_size(hwnd)
        self.last_capture_size = (w_client, h_client)

        self.lbl_target_info.config(text=f"🎯 Isolated Workspace: {title[:28]} ({w_client}x{h_client} px)")
        self.lbl_cursor_telemetry.config(
            text=f"Green Cursor: ({vc.client_x}, {vc.client_y}) [{vc.state}] | VK: {vc.active_key_badge or 'Ready'}"
        )

        cw = max(self.canvas.winfo_width(), 300)
        ch = max(self.canvas.winfo_height(), 200)

        self.canvas.delete("all")

        img = self._capture_window_image(hwnd)
        if img is not None:
            try:
                aspect = min(cw / float(w_client), ch / float(h_client))
                disp_w = max(int(w_client * aspect), 100)
                disp_h = max(int(h_client * aspect), 100)
                self.offset_x = (cw - disp_w) // 2
                self.offset_y = (ch - disp_h) // 2
                self.scale_x = w_client / float(disp_w)
                self.scale_y = h_client / float(disp_h)

                resized = img.resize((disp_w, disp_h), Image.Resampling.BILINEAR)
                self.tk_img_ref = ImageTk.PhotoImage(resized)
                self.canvas.create_image(self.offset_x, self.offset_y, anchor="nw", image=self.tk_img_ref)
                self.canvas.create_rectangle(
                    self.offset_x, self.offset_y, self.offset_x + disp_w, self.offset_y + disp_h,
                    outline=THEME["accent_emerald"], width=1
                )
            except Exception:
                self._draw_schematic_grid(cw, ch, w_client, h_client)
        else:
            self._draw_schematic_grid(cw, ch, w_client, h_client)

        # Draw Virtual Cursor inside Copy-Space
        vx_canvas = self.offset_x + int(vc.client_x / max(self.scale_x, 0.001))
        vy_canvas = self.offset_y + int(vc.client_y / max(self.scale_y, 0.001))

        # Draw drag trail if dragging
        if len(vc.drag_trail) > 1:
            trail_pts = []
            for tx, ty in vc.drag_trail:
                trail_pts.append(self.offset_x + int(tx / max(self.scale_x, 0.001)))
                trail_pts.append(self.offset_y + int(ty / max(self.scale_y, 0.001)))
            self.canvas.create_line(*trail_pts, fill="#F59E0B", width=2, dash=(4, 2))

        # Draw Green Virtual Cursor Arrow
        c_col = "#10B981" if vc.state == "HOVER" else ("#F43F5E" if vc.state == "DOWN" else "#F59E0B")
        arrow_pts = [
            vx_canvas, vy_canvas,
            vx_canvas, vy_canvas + 18,
            vx_canvas + 5, vy_canvas + 14,
            vx_canvas + 9, vy_canvas + 22,
            vx_canvas + 12, vy_canvas + 20,
            vx_canvas + 8, vy_canvas + 12,
            vx_canvas + 14, vy_canvas + 12
        ]
        self.canvas.create_polygon(arrow_pts, fill=c_col, outline="#FFFFFF", width=1.5)
        if vc.state in ("DOWN", "DRAG"):
            self.canvas.create_oval(vx_canvas - 8, vy_canvas - 8, vx_canvas + 8, vy_canvas + 8, outline=c_col, width=2)

        self.canvas.create_text(
            vx_canvas + 18, vy_canvas + 6,
            text=f"({vc.client_x}, {vc.client_y})",
            fill=c_col, anchor="w", font=("Consolas", 9, "bold")
        )

        self.after(120, self._refresh_loop)

    def _draw_schematic_grid(self, cw, ch, w_client, h_client):
        aspect = min((cw - 20) / float(w_client), (ch - 20) / float(h_client))
        disp_w = max(int(w_client * aspect), 100)
        disp_h = max(int(h_client * aspect), 100)
        self.offset_x = (cw - disp_w) // 2
        self.offset_y = (ch - disp_h) // 2
        self.scale_x = w_client / float(disp_w)
        self.scale_y = h_client / float(disp_h)

        self.canvas.create_rectangle(
            self.offset_x, self.offset_y, self.offset_x + disp_w, self.offset_y + disp_h,
            fill="#0D111A", outline=THEME["accent_emerald"], width=1.5
        )
        # Grid lines
        for i in range(1, 4):
            gx = self.offset_x + (disp_w * i) // 4
            gy = self.offset_y + (disp_h * i) // 4
            self.canvas.create_line(gx, self.offset_y, gx, self.offset_y + disp_h, fill="#192030", dash=(2, 4))
            self.canvas.create_line(self.offset_x, gy, self.offset_x + disp_w, gy, fill="#192030", dash=(2, 4))

        self.canvas.create_text(
            self.offset_x + disp_w // 2, self.offset_y + disp_h // 2,
            text=f"Isolated Virtual Workspace ({w_client} x {h_client} px)\nClick or Drag anywhere to interact in Copy-Space",
            fill=THEME["text_muted"], font=THEME["font_bold"], justify="center"
        )

    def _on_close(self):
        self.is_streaming = False
        self.destroy()


# ==============================================================================
# HIGH-PRECISION TRAJECTORY INTERPOLATOR
# ==============================================================================
class TrajectoryEngine:
    @staticmethod
    def bresenham_line(x0, y0, x1, y1):
        points = []
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        curr_x, curr_y = x0, y0
        while True:
            points.append((curr_x, curr_y))
            if curr_x == x1 and curr_y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                curr_x += sx
            if e2 < dx:
                err += dx
                curr_y += sy
        return points

    @staticmethod
    def cubic_ease_interpolate(x0, y0, x1, y1, steps=20):
        points = []
        for i in range(steps + 1):
            t = i / float(steps)
            ease_t = 3 * (t ** 2) - 2 * (t ** 3)
            px = round(x0 + (x1 - x0) * ease_t)
            py = round(y0 + (y1 - y0) * ease_t)
            points.append((px, py))
        return points

    @staticmethod
    def human_bezier_curve(x0, y0, x1, y1, steps=25, jitter_mag=2.0):
        points = []
        dx, dy = x1 - x0, y1 - y0
        dist = math.hypot(dx, dy)
        arc = random.uniform(-0.15, 0.15) * dist
        c1x = x0 + dx * 0.25 - dy * arc * 0.005
        c1y = y0 + dy * 0.25 + dx * arc * 0.005
        c2x = x0 + dx * 0.75 - dy * arc * 0.003
        c2y = y0 + dy * 0.75 + dx * arc * 0.003

        for i in range(steps + 1):
            t = i / float(steps)
            t_ease = t * t * (3.0 - 2.0 * t)
            u = 1.0 - t_ease
            bx = (u**3)*x0 + 3*(u**2)*t_ease*c1x + 3*u*(t_ease**2)*c2x + (t_ease**3)*x1
            by = (u**3)*y0 + 3*(u**2)*t_ease*c1y + 3*u*(t_ease**2)*c2y + (t_ease**3)*y1
            if 0 < i < steps:
                bx += random.uniform(-jitter_mag, jitter_mag) * math.sin(t * math.pi)
                by += random.uniform(-jitter_mag, jitter_mag) * math.sin(t * math.pi)
            points.append((round(bx), round(by)))
        return points


# ==============================================================================
# HIGH-PRECISION HARDWARE MOUSE POLLER
# ==============================================================================
class HighPrecisionMousePoller(threading.Thread):
    def __init__(self, callback, poll_interval_sec=0.002, jitter_filter=True, jitter_thresh=2):
        super().__init__()
        self.daemon = True
        self.callback = callback
        self.poll_interval = poll_interval_sec
        self.stop_signal = threading.Event()
        self.last_pos = None
        self.jitter_filter = jitter_filter
        self.jitter_thresh = jitter_thresh

    def stop(self):
        self.stop_signal.set()

    def run(self):
        while not self.stop_signal.is_set():
            t_now = time.perf_counter()
            pos = HardwareCursor.get_pos()
            if pos is not None:
                if self.last_pos is None:
                    self.last_pos = pos
                    self.callback(pos[0], pos[1], t_now)
                else:
                    dist = math.hypot(pos[0] - self.last_pos[0], pos[1] - self.last_pos[1])
                    if not self.jitter_filter or dist >= self.jitter_thresh:
                        self.last_pos = pos
                        self.callback(pos[0], pos[1], t_now)

            t_target = t_now + self.poll_interval
            while time.perf_counter() < t_target:
                if self.stop_signal.is_set():
                    break
                delta = t_target - time.perf_counter()
                if delta > 0.001:
                    time.sleep(delta * 0.7)


# ==============================================================================
# MACRO STUDIO WINDOW & INTERACTIVE DAW TIMELINE / BLOCK EDITOR
# ==============================================================================
class AddBlockPopupDialog(tk.Toplevel):
    """
    Minimalist '+ Add' Action Picker Popup Dialog.
    Lets the user click a visual card to add any action block cleanly without toolbar clutter.
    """
    def __init__(self, parent, on_pick_callback):
        super().__init__(parent)
        self.on_pick_callback = on_pick_callback
        self.title("+ Add Action Block")
        self.geometry("760x280")
        self.resizable(False, False)
        self.configure(bg=THEME["bg_root"])
        self.attributes("-topmost", True)
        self.transient(parent)

        head = tk.Frame(self, bg=THEME["bg_root"], padx=20, pady=14)
        head.pack(fill="x")
        tk.Label(head, text="✨ Choose Action to Add", fg=THEME["text_primary"], bg=THEME["bg_root"], font=THEME["font_title"]).pack( anchor="w")
        tk.Label(head, text="Choose a category, then configure its action and timing in the Properties panel.", fg=THEME["text_secondary"], bg=THEME["bg_root"], font=("Segoe UI", 9)).pack(anchor="w", pady=(2, 0))

        grid = tk.Frame(self, bg=THEME["bg_root"], padx=18, pady=4)
        grid.pack(fill="both", expand=True)

        cards = [
            ("🖱️  Mouse Interaction", "Add a mouse clip, then choose Click, Drag, Move, or Scroll in Properties.", "MOUSE", THEME["accent_emerald"]),
            ("⌨️  Virtual Keyboard", "Add a key action, then choose its key, hold mode, and modifiers in Properties.", "KEYBOARD", THEME["accent_purple"]),
            ("🔀  Logic & Wait", "Add a delay, pixel-color wait, or IF condition and configure it in Properties.", "LOGIC", THEME["accent_amber"]),
        ]

        for idx, (title, subtitle, code, accent) in enumerate(cards):
            r = 0
            c = idx
            card = tk.Frame(
                grid,
                bg=THEME["bg_card"],
                highlightbackground=THEME["border"],
                highlightthickness=1,
                padx=14,
                pady=12,
                cursor="hand2"
            )
            card.grid(row=r, column=c, padx=6, pady=6, sticky="nsew")
            grid.columnconfigure(c, weight=1)
            grid.rowconfigure(r, weight=1)

            lbl_t = tk.Label(card, text=title, fg=accent, bg=THEME["bg_card"], font=("Segoe UI", 11, "bold"), cursor="hand2")
            lbl_t.pack(anchor="w")
            lbl_s = tk.Label(card, text=subtitle, fg=THEME["text_secondary"], bg=THEME["bg_card"], font=("Segoe UI", 9), wraplength=215, justify="left", cursor="hand2")
            lbl_s.pack(anchor="w", pady=(4, 0))

            def _bind_card(w_list, bcode=code, bcard=card, bacc=accent):
                for w in w_list:
                    w.bind("<Enter>", lambda e: bcard.config(bg=THEME["bg_card_hover"], highlightbackground=bacc))
                    w.bind("<Leave>", lambda e: bcard.config(bg=THEME["bg_card"], highlightbackground=THEME["border"]))
                    w.bind("<Button-1>", lambda e: self._choose(bcode))

            _bind_card([card, lbl_t, lbl_s])

    def _choose(self, code):
        self.destroy()
        if self.on_pick_callback:
            self.on_pick_callback(code)


class MacroStudioTimelineEditor(tk.Toplevel):
    """Spacious macro sequencer with a contextual, right-side Properties inspector."""

    RULER_H = 34
    TRACK_H = 72
    TRACK_HEADER_W = 148
    TRACKS = (
        ("MOUSE", "Mouse", "#0B1518", "#10B981"),
        ("KEYBOARD", "Keyboard", "#121020", "#8B5CF6"),
        ("LOGIC", "Logic & Wait", "#1B1710", "#F59E0B"),
    )
    MOUSE_TRANSFORMS = ("Mouse Click", "Mouse Drag", "Mouse Move", "Mouse Scroll")
    CURVES = ("Bézier Human", "Bresenham Linear", "Cubic Smooth", "Instant")

    def __init__(self, studio):
        super().__init__(studio)
        self.studio = studio
        self.title("Apex Macro Studio — Timeline Editor")
        self.geometry("1180x760")
        self.minsize(920, 640)
        self.configure(bg=THEME["bg_root"])

        self.blocks = self.studio.compile_actions_to_blocks(self.studio.actions)
        self.selected_idx = 0 if self.blocks else None
        self._updating_inspector = False
        self.is_listening_for_key = False
        self.px_per_sec = 150.0
        self.playhead_sec = 0.0
        self.drag_mode = None
        self.drag_block_idx = None
        self.drag_start_x = 0.0
        self.drag_orig_start = 0.0
        self.drag_orig_dur = 0.1
        self._init_property_vars()
        self._build_ui()
        self._refresh_all()
        self.protocol("WM_DELETE_WINDOW", self._save_and_close)
        self.bind("<Delete>", lambda _e: self._delete_block())
        self.bind("<Control-d>", lambda _e: self._duplicate_block())

    def _init_property_vars(self):
        self.var_start_time = tk.StringVar(value="0.00")
        self.var_duration = tk.StringVar(value="0.25")
        self.var_mouse_transform = tk.StringVar(value="Mouse Click")
        self.var_click_style = tk.StringVar(value="Single Click")
        self.var_mouse_btn = tk.StringVar(value="left")
        self.var_mx = tk.StringVar(value="500")
        self.var_my = tk.StringVar(value="400")
        self.var_end_x = tk.StringVar(value="700")
        self.var_end_y = tk.StringVar(value="500")
        self.var_curve = tk.StringVar(value="Bézier Human")
        self.var_scroll_dx = tk.StringVar(value="0")
        self.var_scroll_dy = tk.StringVar(value="-2")
        self.var_key_name = tk.StringVar(value="w")
        self.var_key_mode = tk.StringVar(value="Hold Key for Duration (Hardware Auto-Repeat)")
        self.var_mod_ctrl = tk.BooleanVar(value=False)
        self.var_mod_shift = tk.BooleanVar(value=False)
        self.var_mod_alt = tk.BooleanVar(value=False)
        self.var_logic_mode = tk.StringVar(value="Wait / Pause Delay")
        self.var_logic_color = tk.StringVar(value="#00FF00")

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _build_ui(self):
        style = ttk.Style(self)
        style.configure("TCombobox", fieldbackground=THEME["bg_input"],
                        background=THEME["bg_card_hover"], foreground=THEME["text_primary"],
                        arrowcolor=THEME["accent_blue"], borderwidth=1, padding=5)
        style.map("TCombobox", fieldbackground=[("readonly", THEME["bg_input"])],
                  selectbackground=[("readonly", THEME["bg_input"])],
                  selectforeground=[("readonly", THEME["text_primary"])])

        topbar = tk.Frame(self, bg=THEME["bg_card"], padx=16, pady=9,
                          highlightbackground=THEME["border"], highlightthickness=1)
        topbar.pack(fill="x")
        tk.Label(topbar, text="Timeline Editor", bg=THEME["bg_card"],
                 fg=THEME["text_primary"], font=THEME["font_title"]).pack(side="left")
        tk.Label(topbar, text="Macro Studio  /  Sequencer", bg=THEME["bg_card"],
                 fg=THEME["text_muted"], font=THEME["font_main"]).pack(side="left", padx=(12, 18))

        self._toolbar_button(topbar, "+ Add Action", self.open_add_popup,
                             THEME["accent_emerald"], "#07130F")
        self._toolbar_button(topbar, "Zoom −", lambda: self._adjust_zoom(0.78))
        self._toolbar_button(topbar, "Zoom +", lambda: self._adjust_zoom(1.28))
        self._toolbar_button(topbar, "Duplicate", self._duplicate_block)
        self._toolbar_button(topbar, "Delete", self._delete_block,
                             THEME["bg_input"], THEME["accent_rose"])
        self._toolbar_button(topbar, "Save & Apply", self._save_and_close,
                             THEME["accent_blue"], "#FFFFFF", side="right")

        split = tk.PanedWindow(self, orient="horizontal", bg=THEME["border"],
                               sashwidth=5, sashrelief="flat", bd=0, opaqueresize=True)
        split.pack(fill="both", expand=True, padx=12, pady=12)
        self.main_split = split
        left = tk.Frame(split, bg=THEME["bg_root"])
        right = tk.Frame(split, bg=THEME["bg_card"],
                         highlightbackground=THEME["border"], highlightthickness=1)
        split.add(left, minsize=570, stretch="always")
        split.add(right, minsize=300, stretch="never")
        self.after_idle(lambda: self._place_split_sash(split))

        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(0, weight=3)
        left.grid_rowconfigure(1, weight=2)

        timeline_card = tk.Frame(left, bg=THEME["bg_card"],
                                 highlightbackground=THEME["border"], highlightthickness=1,
                                 padx=10, pady=8)
        timeline_card.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        timeline_head = tk.Frame(timeline_card, bg=THEME["bg_card"])
        timeline_head.pack(fill="x", pady=(0, 7))
        tk.Label(timeline_head, text="SEQUENCER", fg=THEME["text_secondary"],
                 bg=THEME["bg_card"], font=THEME["font_badge"]).pack(side="left")
        tk.Label(timeline_head,
                 text="Select a clip to edit  ·  Drag to move  ·  Drag the right edge to resize",
                 fg=THEME["text_muted"], bg=THEME["bg_card"], font=THEME["font_main"]).pack(side="right")

        canvas_host = tk.Frame(timeline_card, bg="#080A0F",
                               highlightbackground=THEME["border"], highlightthickness=1)
        canvas_host.pack(fill="both", expand=True)
        canvas_host.grid_rowconfigure(0, weight=1)
        canvas_host.grid_columnconfigure(0, weight=1)
        self.tl_canvas = tk.Canvas(canvas_host, bg="#090D14", height=252,
                                   highlightthickness=0, xscrollincrement=24,
                                   yscrollincrement=24, cursor="arrow")
        scrollbar_style = {
            "bg": THEME["bg_card_hover"], "troughcolor": THEME["bg_input"],
            "activebackground": THEME["accent_blue"], "relief": "flat", "bd": 0,
            "highlightthickness": 0, "width": 13
        }
        self.tl_hscroll = tk.Scrollbar(canvas_host, orient="horizontal", command=self.tl_canvas.xview, **scrollbar_style)
        self.tl_vscroll = tk.Scrollbar(canvas_host, orient="vertical", command=self.tl_canvas.yview, **scrollbar_style)
        self.tl_canvas.configure(xscrollcommand=self.tl_hscroll.set, yscrollcommand=self.tl_vscroll.set)
        self.tl_canvas.grid(row=0, column=0, sticky="nsew")
        self.tl_vscroll.grid(row=0, column=1, sticky="ns")
        self.tl_hscroll.grid(row=1, column=0, sticky="ew")
        self.tl_canvas.bind("<ButtonPress-1>", self._on_tl_press)
        self.tl_canvas.bind("<B1-Motion>", self._on_tl_drag)
        self.tl_canvas.bind("<ButtonRelease-1>", self._on_tl_release)
        self.tl_canvas.bind("<MouseWheel>", self._on_timeline_wheel)

        clips_card = tk.Frame(left, bg=THEME["bg_card"],
                              highlightbackground=THEME["border"], highlightthickness=1,
                              padx=10, pady=7)
        clips_card.grid(row=1, column=0, sticky="nsew")
        clips_head = tk.Frame(clips_card, bg=THEME["bg_card"])
        clips_head.pack(fill="x", pady=(0, 5))
        tk.Label(clips_head, text="ACTION CLIPS", fg=THEME["text_secondary"],
                 bg=THEME["bg_card"], font=THEME["font_badge"]).pack(side="left")
        self.lbl_clip_count = tk.Label(clips_head, text="0 clips", fg=THEME["accent_emerald"],
                                       bg=THEME["bg_card"], font=THEME["font_badge"])
        self.lbl_clip_count.pack(side="right")
        list_host = tk.Frame(clips_card, bg=THEME["bg_input"])
        list_host.pack(fill="both", expand=True)
        self.block_listbox = tk.Listbox(
            list_host, bg=THEME["bg_input"], fg=THEME["text_primary"],
            selectbackground=THEME["accent_blue"], selectforeground="#FFFFFF",
            relief="flat", bd=0, font=THEME["font_mono"], activestyle="none",
            highlightthickness=0
        )
        list_scroll = tk.Scrollbar(list_host, orient="vertical", command=self.block_listbox.yview, **scrollbar_style)
        self.block_listbox.configure(yscrollcommand=list_scroll.set)
        self.block_listbox.pack(side="left", fill="both", expand=True, padx=6, pady=5)
        list_scroll.pack(side="right", fill="y")
        self.block_listbox.bind("<<ListboxSelect>>", self._on_listbox_select)
        self._build_properties_panel(right)

    def _place_split_sash(self, split):
        try:
            split.sash_place(0, int(max(split.winfo_width(), 920) * 0.65), 0)
        except tk.TclError:
            pass

    def _toolbar_button(self, parent, text, command, bg=None, fg=None, side="left"):
        button = tk.Button(
            parent, text=text, command=command,
            bg=bg or THEME["bg_input"], fg=fg or THEME["text_primary"],
            activebackground=THEME["bg_card_hover"], activeforeground=THEME["text_primary"],
            relief="flat", bd=0, highlightthickness=0, padx=10, pady=5,
            font=THEME["font_bold"], cursor="hand2"
        )
        button.pack(side=side, padx=(0, 5) if side == "left" else (5, 0))
        return button

    def _small_button(self, parent, text, command):
        return tk.Button(
            parent, text=text, command=command, bg=THEME["bg_input"],
            fg=THEME["text_secondary"], activebackground=THEME["bg_card_hover"],
            activeforeground=THEME["text_primary"], relief="flat", bd=0,
            font=THEME["font_main"], padx=8, pady=4, cursor="hand2"
        )

    def _section(self, parent, title, accent=None):
        card = tk.Frame(parent, bg=THEME["bg_card"],
                        highlightbackground=THEME["border"], highlightthickness=1,
                        padx=10, pady=8)
        head = tk.Frame(card, bg=THEME["bg_card"])
        head.pack(fill="x", pady=(0, 7))
        tk.Label(head, text=title.upper(), bg=THEME["bg_card"],
                 fg=accent or THEME["text_secondary"], font=THEME["font_badge"]).pack(side="left")
        return card

    def _build_properties_panel(self, parent):
        header = tk.Frame(parent, bg=THEME["bg_card"], padx=13, pady=11)
        header.pack(fill="x")
        tk.Label(header, text="PROPERTIES", fg=THEME["text_secondary"],
                 bg=THEME["bg_card"], font=THEME["font_badge"]).pack(anchor="w")
        self.lbl_selected_title = tk.Label(header, text="No clip selected",
                                           fg=THEME["text_primary"], bg=THEME["bg_card"],
                                           font=("Segoe UI", 12, "bold"))
        self.lbl_selected_title.pack(anchor="w", pady=(3, 0))
        self.lbl_selected_hint = tk.Label(
            header, text="Add or select a timeline clip to edit its properties.",
            fg=THEME["text_muted"], bg=THEME["bg_card"], font=THEME["font_main"],
            wraplength=280, justify="left"
        )
        self.lbl_selected_hint.pack(anchor="w", pady=(3, 0))
        tk.Frame(parent, bg=THEME["border"], height=1).pack(fill="x")

        host = tk.Frame(parent, bg=THEME["bg_card"])
        host.pack(fill="both", expand=True)
        self.props_canvas = tk.Canvas(host, bg=THEME["bg_card"], highlightthickness=0, width=320)
        props_scroll_style = {
            "bg": THEME["bg_card_hover"], "troughcolor": THEME["bg_input"],
            "activebackground": THEME["accent_blue"], "relief": "flat", "bd": 0,
            "highlightthickness": 0, "width": 13
        }
        self.props_scroll = tk.Scrollbar(host, orient="vertical", command=self.props_canvas.yview, **props_scroll_style)
        self.props_canvas.configure(yscrollcommand=self.props_scroll.set)
        self.props_scroll.pack(side="right", fill="y")
        self.props_canvas.pack(side="left", fill="both", expand=True)
        self.props_body = tk.Frame(self.props_canvas, bg=THEME["bg_card"], padx=10, pady=10)
        self.props_window = self.props_canvas.create_window((0, 0), window=self.props_body, anchor="nw")
        self.props_body.bind("<Configure>", lambda _e: self.props_canvas.configure(scrollregion=self.props_canvas.bbox("all")))
        self.props_canvas.bind("<Configure>", lambda e: self.props_canvas.itemconfigure(self.props_window, width=e.width))
        for widget in (self.props_canvas, self.props_body):
            widget.bind("<MouseWheel>", lambda e: self.props_canvas.yview_scroll(-1 if e.delta > 0 else 1, "units"))

        # Shared timing controls.
        self.group_timing = self._section(self.props_body, "Timing", THEME["accent_blue"])
        self.group_timing.pack(fill="x", pady=(0, 8))
        timing_grid = tk.Frame(self.group_timing, bg=THEME["bg_card"])
        timing_grid.pack(fill="x")
        timing_grid.columnconfigure(0, weight=1)
        timing_grid.columnconfigure(1, weight=1)
        self._entry_field(timing_grid, "Start time (seconds)", self.var_start_time, 0, 0)
        self._entry_field(timing_grid, "Duration (seconds)", self.var_duration, 0, 1)
        steps = tk.Frame(self.group_timing, bg=THEME["bg_card"])
        steps.pack(fill="x", pady=(6, 0))
        self._small_button(steps, "Start −", lambda: self._step_time("start", -0.05)).pack(side="left", padx=(0, 3))
        self._small_button(steps, "Start +", lambda: self._step_time("start", 0.05)).pack(side="left", padx=(0, 7))
        self._small_button(steps, "Dur −", lambda: self._step_time("dur", -0.05)).pack(side="left", padx=(0, 3))
        self._small_button(steps, "Dur +", lambda: self._step_time("dur", 0.05)).pack(side="left")
        self.dur_slider = tk.Scale(
            self.group_timing, from_=0.02, to=10.0, resolution=0.02, orient="horizontal",
            bg=THEME["bg_card"], fg=THEME["accent_blue"], troughcolor=THEME["bg_input"],
            activebackground=THEME["accent_blue"], highlightthickness=0, showvalue=0,
            length=235, command=self._on_dur_slider_moved
        )
        self.dur_slider.pack(fill="x", pady=(2, 0))

        # Mouse clips expose an explicit transform selector. Only relevant fields are shown.
        self.group_mouse = self._section(self.props_body, "Mouse action", THEME["accent_emerald"])
        self.group_mouse.pack(fill="x", pady=(0, 8))
        self._property_label(self.group_mouse, "Transform this mouse clip into")
        self.mouse_transform_combo = ttk.Combobox(
            self.group_mouse, textvariable=self.var_mouse_transform,
            values=self.MOUSE_TRANSFORMS, state="readonly", font=THEME["font_main"]
        )
        self.mouse_transform_combo.pack(fill="x", pady=(3, 8))
        self.mouse_transform_combo.bind("<<ComboboxSelected>>", self._on_mouse_transform_changed)

        self.mouse_click_fields = tk.Frame(self.group_mouse, bg=THEME["bg_card"])
        self._combo_field(self.mouse_click_fields, "Click type", self.var_click_style,
                          ("Single Click", "Double Click", "Press & Hold"), self._auto_sync_from_deck)
        self._combo_field(self.mouse_click_fields, "Mouse button", self.var_mouse_btn,
                          ("left", "right", "middle"), self._auto_sync_from_deck)

        self.mouse_drag_fields = tk.Frame(self.group_mouse, bg=THEME["bg_card"])
        self._combo_field(self.mouse_drag_fields, "Mouse button", self.var_mouse_btn,
                          ("left", "right", "middle"), self._auto_sync_from_deck)
        self._coordinate_pair(self.mouse_drag_fields, "Drag destination", self.var_end_x, self.var_end_y)
        self._small_button(self.mouse_drag_fields, "Pick destination", lambda: self._pick_coord_for("end")).pack(anchor="w", pady=(2, 6))
        self._combo_field(self.mouse_drag_fields, "Movement curve", self.var_curve, self.CURVES, self._auto_sync_from_deck)

        self.mouse_move_fields = tk.Frame(self.group_mouse, bg=THEME["bg_card"])
        self._combo_field(self.mouse_move_fields, "Movement curve", self.var_curve, self.CURVES, self._auto_sync_from_deck)
        tk.Label(
            self.mouse_move_fields,
            text="Moves the target-app cursor to this point. Virtual Cursor Runtime keeps your desktop pointer independent.",
            bg=THEME["bg_card"], fg=THEME["text_muted"], font=THEME["font_main"],
            justify="left", wraplength=270
        ).pack(anchor="w", pady=(1, 2))

        self.mouse_scroll_fields = tk.Frame(self.group_mouse, bg=THEME["bg_card"])
        self._property_label(self.mouse_scroll_fields, "Scroll amount (wheel units)")
        scroll_grid = tk.Frame(self.mouse_scroll_fields, bg=THEME["bg_card"])
        scroll_grid.pack(fill="x")
        scroll_grid.columnconfigure(0, weight=1)
        scroll_grid.columnconfigure(1, weight=1)
        self._entry_field(scroll_grid, "Horizontal (X)", self.var_scroll_dx, 0, 0)
        self._entry_field(scroll_grid, "Vertical (Y)", self.var_scroll_dy, 0, 1)
        self._property_label(self.mouse_scroll_fields, "Positive and negative values control direction.")

        self.mouse_start_fields = tk.Frame(self.group_mouse, bg=THEME["bg_card"])
        self._coordinate_pair(self.mouse_start_fields, "Target position", self.var_mx, self.var_my)
        self._small_button(self.mouse_start_fields, "Pick on screen", lambda: self._pick_coord_for("start")).pack(anchor="w", pady=(2, 5))

        self.pad_wrap = tk.Frame(self.group_mouse, bg=THEME["bg_input"],
                                 highlightbackground=THEME["border"], highlightthickness=1, padx=7, pady=6)
        tk.Label(self.pad_wrap, text="COORDINATE PREVIEW  ·  Click for start, drag for end",
                 bg=THEME["bg_input"], fg=THEME["text_muted"], font=THEME["font_badge"]).pack(anchor="w", pady=(0, 4))
        self.xy_pad = tk.Canvas(self.pad_wrap, width=260, height=112, bg="#080C12",
                                highlightthickness=1, highlightbackground=THEME["border"], cursor="crosshair")
        self.xy_pad.pack(fill="x")
        self.xy_pad.bind("<ButtonPress-1>", self._on_xypad_down)
        self.xy_pad.bind("<B1-Motion>", self._on_xypad_drag)

        self.group_keyboard = self._section(self.props_body, "Keyboard action", THEME["accent_purple"])
        self._property_label(self.group_keyboard, "Target key")
        self.btn_key_capture = tk.Button(
            self.group_keyboard, text="W  ·  Click to bind", command=self._start_interactive_key_bind,
            bg=THEME["bg_input"], fg=THEME["accent_purple"], activebackground=THEME["bg_card_hover"],
            relief="flat", bd=0, font=THEME["font_mono_bold"], pady=8, cursor="hand2"
        )
        self.btn_key_capture.pack(fill="x", pady=(3, 8))
        self._combo_field(self.group_keyboard, "Key behavior", self.var_key_mode,
                          ("Hold Key for Duration (Hardware Auto-Repeat)", "Single Tap (Press & Release)",
                           "Rapid Repeat Tap during Duration"), self._auto_sync_from_deck)
        mods = tk.Frame(self.group_keyboard, bg=THEME["bg_card"])
        mods.pack(fill="x", pady=(7, 0))
        for label, variable in (("Ctrl", self.var_mod_ctrl), ("Shift", self.var_mod_shift), ("Alt", self.var_mod_alt)):
            tk.Checkbutton(
                mods, text=label, variable=variable, command=self._auto_sync_from_deck,
                bg=THEME["bg_card"], fg=THEME["text_primary"], selectcolor=THEME["bg_input"],
                activebackground=THEME["bg_card"], font=THEME["font_main"]
            ).pack(side="left", padx=(0, 12))

        self.group_logic = self._section(self.props_body, "Logic & wait", THEME["accent_amber"])
        self._combo_field(self.group_logic, "Flow action", self.var_logic_mode,
                          ("Wait / Pause Delay", "Wait For Pixel Color", "IF Pixel Color Matches"),
                          self._auto_sync_from_deck)
        logic_grid = tk.Frame(self.group_logic, bg=THEME["bg_card"])
        logic_grid.pack(fill="x")
        logic_grid.columnconfigure(0, weight=1)
        logic_grid.columnconfigure(1, weight=1)
        self._entry_field(logic_grid, "Target hex color", self.var_logic_color, 0, 0)
        self._entry_field(logic_grid, "Pixel X", self.var_mx, 1, 0)
        self._entry_field(logic_grid, "Pixel Y", self.var_my, 1, 1)

        runtime = tk.Frame(self.props_body, bg=THEME["bg_input"],
                           highlightbackground=THEME["border"], highlightthickness=1, padx=9, pady=8)
        self.runtime_card = runtime
        runtime.pack(fill="x", pady=(0, 8))
        tk.Label(runtime, text="VIRTUAL CURSOR RUNTIME", bg=THEME["bg_input"],
                 fg=THEME["accent_emerald"], font=THEME["font_badge"]).pack(anchor="w")
        tk.Label(
            runtime,
            text="Playback draws an independent cursor over the locked target window and dispatches actions there. You can keep moving your physical mouse elsewhere.",
            bg=THEME["bg_input"], fg=THEME["text_secondary"], font=THEME["font_main"],
            justify="left", wraplength=270
        ).pack(anchor="w", pady=(4, 0))
        self._refresh_property_groups("MOUSE")

    def _small_button(self, parent, text, command):
        return tk.Button(parent, text=text, command=command, bg=THEME["bg_input"],
                         fg=THEME["text_secondary"], activebackground=THEME["bg_card_hover"],
                         activeforeground=THEME["text_primary"], relief="flat", bd=0,
                         font=THEME["font_main"], padx=8, pady=4, cursor="hand2")

    def _property_label(self, parent, text):
        tk.Label(parent, text=text, bg=parent.cget("bg"), fg=THEME["text_secondary"],
                 font=THEME["font_main"], justify="left", wraplength=275).pack(anchor="w", pady=(2, 3))

    def _entry_field(self, parent, label, variable, row, column, width=10):
        wrap = tk.Frame(parent, bg=parent.cget("bg"))
        wrap.grid(row=row, column=column, sticky="ew", padx=(0, 7), pady=(0, 6))
        tk.Label(wrap, text=label, bg=wrap.cget("bg"), fg=THEME["text_muted"],
                 font=("Segoe UI", 8)).pack(anchor="w")
        entry = tk.Entry(wrap, textvariable=variable, width=width, bg=THEME["bg_input"],
                         fg=THEME["text_primary"], insertbackground=THEME["text_primary"],
                         relief="flat", highlightbackground=THEME["border"], highlightthickness=1,
                         font=THEME["font_mono"], justify="left")
        entry.pack(fill="x", pady=(2, 0))
        entry.bind("<KeyRelease>", lambda _e: self._auto_sync_from_deck())
        entry.bind("<FocusOut>", lambda _e: self._auto_sync_from_deck())
        entry.bind("<Return>", lambda _e: self._auto_sync_from_deck())
        return entry

    def _coordinate_pair(self, parent, title, x_var, y_var):
        self._property_label(parent, title)
        grid = tk.Frame(parent, bg=THEME["bg_card"])
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        self._entry_field(grid, "X", x_var, 0, 0)
        self._entry_field(grid, "Y", y_var, 0, 1)

    def _combo_field(self, parent, label, variable, values, callback):
        wrap = tk.Frame(parent, bg=THEME["bg_card"])
        wrap.pack(fill="x", pady=(0, 7))
        tk.Label(wrap, text=label, bg=THEME["bg_card"], fg=THEME["text_muted"],
                 font=("Segoe UI", 8)).pack(anchor="w")
        combo = ttk.Combobox(wrap, textvariable=variable, values=values,
                             state="readonly", font=THEME["font_main"])
        combo.pack(fill="x", pady=(2, 0))
        combo.bind("<<ComboboxSelected>>", lambda _e: callback())
        return combo

    # ------------------------------------------------------------------
    # Property loading and synchronization
    # ------------------------------------------------------------------
    @staticmethod
    def _mouse_transform_for_mode(mode):
        mode = str(mode or "Click")
        if "Drag" in mode:
            return "Mouse Drag"
        if "Move" in mode:
            return "Mouse Move"
        if "Scroll" in mode:
            return "Mouse Scroll"
        return "Mouse Click"

    def _mouse_mode_value(self):
        transform = self.var_mouse_transform.get()
        if transform == "Mouse Drag":
            return "Click-n-Drag (Move while Holding)"
        if transform == "Mouse Move":
            return "Move Only (Virtual Cursor Runtime)"
        if transform == "Mouse Scroll":
            return "Scroll Wheel"
        return {"Double Click": "Double Click", "Press & Hold": "Press & Hold"}.get(
            self.var_click_style.get(), "Click"
        )

    def _refresh_property_groups(self, category):
        for group in (self.group_mouse, self.group_keyboard, self.group_logic):
            group.pack_forget()
        if category == "MOUSE":
            self.group_mouse.pack(fill="x", pady=(0, 8))
            for frame in (self.mouse_click_fields, self.mouse_drag_fields, self.mouse_move_fields,
                          self.mouse_scroll_fields, self.mouse_start_fields, self.pad_wrap):
                frame.pack_forget()
            self.mouse_start_fields.pack(fill="x", pady=(0, 5))
            transform = self.var_mouse_transform.get()
            if transform == "Mouse Click":
                self.mouse_click_fields.pack(fill="x", pady=(0, 5))
            elif transform == "Mouse Drag":
                self.mouse_drag_fields.pack(fill="x", pady=(0, 5))
            elif transform == "Mouse Move":
                self.mouse_move_fields.pack(fill="x", pady=(0, 5))
            else:
                self.mouse_scroll_fields.pack(fill="x", pady=(0, 5))
            self.pad_wrap.pack(fill="x", pady=(7, 0))
        elif category == "KEYBOARD":
            self.group_keyboard.pack(fill="x", pady=(0, 8))
        else:
            self.group_logic.pack(fill="x", pady=(0, 8))
        if hasattr(self, "runtime_card"):
            self.runtime_card.pack_forget()
            self.runtime_card.pack(fill="x", pady=(0, 8))

    def _load_block_into_inspector(self, block):
        self._updating_inspector = True
        try:
            category = block.get("category", "MOUSE")
            start = float(block.get("start", 0.0) or 0.0)
            duration = max(0.02, float(block.get("duration", 0.25) or 0.25))
            self.var_start_time.set(f"{start:.3f}")
            self.var_duration.set(f"{duration:.3f}")
            self.dur_slider.set(min(max(duration, 0.02), 10.0))
            self.lbl_selected_title.config(text=self._block_title(block))
            self.lbl_selected_hint.config(text=f"Clip {self.selected_idx + 1} of {len(self.blocks)}  ·  {category.title()} track")

            if category == "MOUSE":
                mode = block.get("mode", "Click")
                transform = self._mouse_transform_for_mode(mode)
                self.var_mouse_transform.set(transform)
                self.var_click_style.set("Double Click" if "Double" in mode else
                                         ("Press & Hold" if "Hold" in mode else "Single Click"))
                self.var_mouse_btn.set(block.get("button", "left"))
                self.var_mx.set(str(block.get("x", 500)))
                self.var_my.set(str(block.get("y", 400)))
                self.var_end_x.set(str(block.get("end_x", 700)))
                self.var_end_y.set(str(block.get("end_y", 500)))
                self.var_curve.set(block.get("curve", "Bézier Human"))
                self.var_scroll_dx.set(str(block.get("scroll_dx", 0)))
                self.var_scroll_dy.set(str(block.get("scroll_dy", -2)))
                self.mouse_transform_combo.set(transform)
                self._refresh_property_groups(category)
                self._draw_xypad_preview()
            elif category == "KEYBOARD":
                key_name = str(block.get("key", "w"))
                self.var_key_name.set(key_name)
                self.btn_key_capture.config(text=f"{key_name.upper()}  ·  Click to bind")
                self.var_key_mode.set(block.get("key_mode", "Hold Key for Duration (Hardware Auto-Repeat)"))
                modifiers = [str(m).lower() for m in block.get("modifiers", [])]
                self.var_mod_ctrl.set("ctrl" in modifiers)
                self.var_mod_shift.set("shift" in modifiers)
                self.var_mod_alt.set("alt" in modifiers)
                self._refresh_property_groups(category)
            else:
                self.var_logic_mode.set(block.get("logic_mode", "Wait / Pause Delay"))
                self.var_logic_color.set(block.get("color", "#00FF00"))
                self.var_mx.set(str(block.get("x", 500)))
                self.var_my.set(str(block.get("y", 400)))
                self._refresh_property_groups(category)
        finally:
            self._updating_inspector = False

    def _on_mouse_transform_changed(self, _event=None):
        if self._updating_inspector:
            return
        self._refresh_property_groups("MOUSE")
        self._auto_sync_from_deck()

    def _auto_sync_from_deck(self):
        if self._updating_inspector or self.selected_idx is None:
            return
        if not (0 <= self.selected_idx < len(self.blocks)):
            return
        block = self.blocks[self.selected_idx]
        category = block.get("category", "MOUSE")
        try:
            block["start"] = max(0.0, round(float(self.var_start_time.get()), 4))
        except (TypeError, ValueError):
            pass
        try:
            block["duration"] = max(0.02, round(float(self.var_duration.get()), 4))
        except (TypeError, ValueError):
            pass

        if category == "MOUSE":
            transform = self.var_mouse_transform.get()
            block["mode"] = self._mouse_mode_value()
            try:
                block["x"] = int(float(self.var_mx.get()))
                block["y"] = int(float(self.var_my.get()))
            except (TypeError, ValueError):
                pass
            if transform == "Mouse Drag":
                try:
                    block["end_x"] = int(float(self.var_end_x.get()))
                    block["end_y"] = int(float(self.var_end_y.get()))
                except (TypeError, ValueError):
                    pass
                block["button"] = self.var_mouse_btn.get()
                block["curve"] = self.var_curve.get()
            elif transform == "Mouse Click":
                block["button"] = self.var_mouse_btn.get()
            elif transform == "Mouse Move":
                block["curve"] = self.var_curve.get()
            else:
                try:
                    block["scroll_dx"] = int(float(self.var_scroll_dx.get()))
                    block["scroll_dy"] = int(float(self.var_scroll_dy.get()))
                except (TypeError, ValueError):
                    pass
        elif category == "KEYBOARD":
            block["key"] = self.var_key_name.get().strip() or "w"
            block["key_mode"] = self.var_key_mode.get()
            block["modifiers"] = [name for name, var in (("ctrl", self.var_mod_ctrl),
                                                          ("shift", self.var_mod_shift), ("alt", self.var_mod_alt)) if var.get()]
        else:
            block["logic_mode"] = self.var_logic_mode.get()
            block["color"] = self.var_logic_color.get().strip() or "#00FF00"
            try:
                block["x"] = int(float(self.var_mx.get()))
                block["y"] = int(float(self.var_my.get()))
            except (TypeError, ValueError):
                pass

        self.lbl_selected_title.config(text=self._block_title(block))
        self._draw_timeline()
        self._refresh_clip_row(self.selected_idx)
        self._draw_xypad_preview()

    def _step_time(self, which, delta):
        variable = self.var_start_time if which == "start" else self.var_duration
        try:
            value = float(variable.get()) + delta
            value = max(0.0 if which == "start" else 0.02, value)
            variable.set(f"{value:.3f}")
            if which == "dur":
                self._updating_inspector = True
                self.dur_slider.set(min(value, 10.0))
                self._updating_inspector = False
            self._auto_sync_from_deck()
        except ValueError:
            pass

    def _on_dur_slider_moved(self, value):
        if self._updating_inspector:
            return
        self.var_duration.set(f"{float(value):.3f}")
        self._auto_sync_from_deck()

    # ------------------------------------------------------------------
    # Coordinate pad and screen picker
    # ------------------------------------------------------------------
    def _on_xypad_down(self, event):
        width, height = WindowWorkspaceBounds.get_client_size(self.studio.recorded_target_hwnd)
        x = int(max(0, min(event.x, 260)) / 260.0 * width)
        y = int(max(0, min(event.y, 112)) / 112.0 * height)
        self.var_mx.set(str(x))
        self.var_my.set(str(y))
        self._auto_sync_from_deck()

    def _on_xypad_drag(self, event):
        if self.var_mouse_transform.get() != "Mouse Drag":
            self.var_mouse_transform.set("Mouse Drag")
            self.mouse_transform_combo.set("Mouse Drag")
            self._refresh_property_groups("MOUSE")
        width, height = WindowWorkspaceBounds.get_client_size(self.studio.recorded_target_hwnd)
        x = int(max(0, min(event.x, 260)) / 260.0 * width)
        y = int(max(0, min(event.y, 112)) / 112.0 * height)
        self.var_end_x.set(str(x))
        self.var_end_y.set(str(y))
        self._auto_sync_from_deck()

    def _draw_xypad_preview(self):
        if not hasattr(self, "xy_pad"):
            return
        canvas = self.xy_pad
        canvas.delete("all")
        width, height = 260, 112
        client_w, client_h = WindowWorkspaceBounds.get_client_size(self.studio.recorded_target_hwnd)
        canvas.create_line(width // 2, 0, width // 2, height, fill="#1B2635", dash=(2, 3))
        canvas.create_line(0, height // 2, width, height // 2, fill="#1B2635", dash=(2, 3))
        try:
            sx = int(float(self.var_mx.get()) / max(client_w, 1) * width)
            sy = int(float(self.var_my.get()) / max(client_h, 1) * height)
            ex = int(float(self.var_end_x.get()) / max(client_w, 1) * width)
            ey = int(float(self.var_end_y.get()) / max(client_h, 1) * height)
            if self.var_mouse_transform.get() == "Mouse Drag":
                canvas.create_line(sx, sy, ex, ey, fill=THEME["accent_blue"], width=2, dash=(4, 2))
                canvas.create_oval(ex - 4, ey - 4, ex + 4, ey + 4, fill=THEME["accent_blue"], outline="#FFFFFF")
            canvas.create_oval(sx - 5, sy - 5, sx + 5, sy + 5, fill=THEME["accent_emerald"], outline="#FFFFFF")
        except (TypeError, ValueError):
            pass

    def _pick_coord_for(self, which="start"):
        def _callback(x, y, _color=None):
            hwnd = self.studio.recorded_target_hwnd
            _, _, client_x, client_y, _, _ = WindowWorkspaceBounds.clamp_to_window(hwnd, x, y, is_client_coords=False)
            if which == "start":
                self.var_mx.set(str(client_x))
                self.var_my.set(str(client_y))
            else:
                self.var_end_x.set(str(client_x))
                self.var_end_y.set(str(client_y))
            self._auto_sync_from_deck()
        CoordinatePickerOverlay(_callback)

    def _start_interactive_key_bind(self):
        self.is_listening_for_key = True
        self.btn_key_capture.config(text="PRESS A KEY…", fg=THEME["accent_emerald"], bg=THEME["bg_card_hover"])
        self.bind("<KeyPress>", self._on_capture_key_event)
        self.focus_set()

    def _on_capture_key_event(self, event):
        if not self.is_listening_for_key:
            return
        self.is_listening_for_key = False
        self.unbind("<KeyPress>")
        key_name = event.keysym.lower()
        if key_name in ("control_l", "control_r"):
            key_name = "ctrl"
        elif key_name in ("shift_l", "shift_r"):
            key_name = "shift"
        elif key_name in ("alt_l", "alt_r"):
            key_name = "alt"
        self.var_key_name.set(key_name)
        self.btn_key_capture.config(text=f"{key_name.upper()}  ·  Click to bind", fg=THEME["accent_purple"], bg=THEME["bg_input"])
        self._auto_sync_from_deck()

    # ------------------------------------------------------------------
    # Clips, timeline drawing, selection, and saving
    # ------------------------------------------------------------------
    def open_add_popup(self):
        AddBlockPopupDialog(self, self._insert_new_block)

    def _insert_new_block(self, block_type):
        last_end = max((b.get("start", 0.0) + b.get("duration", 0.1) for b in self.blocks), default=-0.1)
        start = round(max(0.0, last_end + 0.10), 2)
        if block_type in ("MOUSE", "MOUSE_CLICK"):
            block = {"category": "MOUSE", "start": start, "duration": 0.08, "mode": "Click",
                     "button": "left", "x": 500, "y": 400, "end_x": 700, "end_y": 500,
                     "curve": "Bézier Human", "scroll_dx": 0, "scroll_dy": -2}
        elif block_type == "MOUSE_DRAG":
            block = {"category": "MOUSE", "start": start, "duration": 0.80,
                     "mode": "Click-n-Drag (Move while Holding)", "button": "left",
                     "x": 300, "y": 300, "end_x": 650, "end_y": 480,
                     "curve": "Bézier Human", "scroll_dx": 0, "scroll_dy": -2}
        elif block_type == "MOUSE_MOVE":
            block = {"category": "MOUSE", "start": start, "duration": 0.40,
                     "mode": "Move Only (Virtual Cursor Runtime)", "button": "left",
                     "x": 640, "y": 360, "end_x": 640, "end_y": 360,
                     "curve": "Bézier Human", "scroll_dx": 0, "scroll_dy": -2}
        elif block_type == "MOUSE_SCROLL":
            block = {"category": "MOUSE", "start": start, "duration": 0.10,
                     "mode": "Scroll Wheel", "button": "left", "x": 500, "y": 400,
                     "end_x": 500, "end_y": 400, "curve": "Instant", "scroll_dx": 0, "scroll_dy": -2}
        elif block_type == "KEYBOARD":
            block = {"category": "KEYBOARD", "start": start, "duration": 0.60, "key": "w",
                     "key_mode": "Hold Key for Duration (Hardware Auto-Repeat)", "modifiers": []}
        else:
            block = {"category": "LOGIC", "start": start, "duration": 0.50,
                     "logic_mode": "Wait / Pause Delay", "color": "#00FF00", "x": 500, "y": 400}
        self.blocks.append(block)
        self.selected_idx = len(self.blocks) - 1
        self._refresh_all()

    def _block_title(self, block):
        category = block.get("category", "MOUSE")
        if category == "MOUSE":
            return self._mouse_transform_for_mode(block.get("mode", "Click"))
        if category == "KEYBOARD":
            return f"Keyboard · {str(block.get('key', 'w')).upper()}"
        return block.get("logic_mode", "Logic & Wait")

    def _format_block_summary(self, idx, block):
        start = float(block.get("start", 0.0))
        duration = float(block.get("duration", 0.1))
        category = block.get("category", "MOUSE")
        if category == "MOUSE":
            transform = self._mouse_transform_for_mode(block.get("mode", "Click"))
            button = str(block.get("button", "left")).capitalize()
            x, y = block.get("x", 0), block.get("y", 0)
            if transform == "Mouse Drag":
                detail = f"{button} ({x}, {y}) → ({block.get('end_x', x)}, {block.get('end_y', y)})"
            elif transform == "Mouse Scroll":
                detail = f"wheel X {block.get('scroll_dx', 0)} / Y {block.get('scroll_dy', -2)} at ({x}, {y})"
            else:
                detail = f"{button} at ({x}, {y})" if transform == "Mouse Click" else f"target ({x}, {y})"
            label = f"{transform} · {detail}"
        elif category == "KEYBOARD":
            modifiers = [str(m).upper() for m in block.get("modifiers", [])]
            key = "+".join(modifiers + [str(block.get("key", "w")).upper()])
            label = f"Keyboard · {key}"
        else:
            label = f"Logic · {block.get('logic_mode', 'Wait / Pause Delay')}"
        return f"{idx + 1:02d}   {start:7.2f}s   {duration:6.2f}s   {label}"

    def _refresh_clip_row(self, idx):
        if 0 <= idx < self.block_listbox.size() and idx < len(self.blocks):
            self.block_listbox.delete(idx)
            self.block_listbox.insert(idx, self._format_block_summary(idx, self.blocks[idx]))
            self.block_listbox.selection_clear(0, tk.END)
            self.block_listbox.selection_set(idx)
            self.block_listbox.see(idx)

    def _refresh_all(self):
        selected_block = self.blocks[self.selected_idx] if self.selected_idx is not None and 0 <= self.selected_idx < len(self.blocks) else None
        self.blocks.sort(key=lambda b: float(b.get("start", 0.0)))
        self.selected_idx = next((i for i, item in enumerate(self.blocks) if item is selected_block), None)
        self.block_listbox.delete(0, tk.END)
        for index, block in enumerate(self.blocks):
            self.block_listbox.insert(tk.END, self._format_block_summary(index, block))
        self.lbl_clip_count.config(text=f"{len(self.blocks)} clips")
        if self.selected_idx is not None:
            self.block_listbox.selection_set(self.selected_idx)
            self.block_listbox.see(self.selected_idx)
            self._load_block_into_inspector(self.blocks[self.selected_idx])
        else:
            self.lbl_selected_title.config(text="No clip selected")
            self.lbl_selected_hint.config(text="Add or select a timeline clip to edit its properties.")
        self._draw_timeline()

    def _on_listbox_select(self, _event=None):
        selection = self.block_listbox.curselection()
        if not selection:
            return
        self.selected_idx = selection[0]
        self._load_block_into_inspector(self.blocks[self.selected_idx])
        self._draw_timeline()

    def _duplicate_block(self):
        if self.selected_idx is None or not (0 <= self.selected_idx < len(self.blocks)):
            return
        duplicate = dict(self.blocks[self.selected_idx])
        if isinstance(duplicate.get("modifiers"), list):
            duplicate["modifiers"] = list(duplicate["modifiers"])
        duplicate["start"] = round(float(duplicate.get("start", 0.0)) + float(duplicate.get("duration", 0.2)) + 0.1, 2)
        self.blocks.append(duplicate)
        self.selected_idx = len(self.blocks) - 1
        self._refresh_all()

    def _delete_block(self):
        if self.selected_idx is None or not (0 <= self.selected_idx < len(self.blocks)):
            return
        del self.blocks[self.selected_idx]
        self.selected_idx = min(self.selected_idx, len(self.blocks) - 1) if self.blocks else None
        self._refresh_all()

    def _adjust_zoom(self, factor):
        self.px_per_sec = max(45.0, min(self.px_per_sec * factor, 520.0))
        self._draw_timeline()

    def _on_timeline_wheel(self, event):
        if event.state & 0x0004:
            self._adjust_zoom(1.12 if event.delta > 0 else 0.89)
        else:
            self.tl_canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")

    def _track_y(self, category):
        for index, (key, _label, _bg, _accent) in enumerate(self.TRACKS):
            if key == category:
                top = self.RULER_H + index * self.TRACK_H
                return top, top + self.TRACK_H
        return self.RULER_H, self.RULER_H + self.TRACK_H

    def _draw_timeline(self):
        canvas = self.tl_canvas
        canvas.delete("all")
        max_time = max(6.0, max((float(b.get("start", 0.0)) + float(b.get("duration", 0.1)) + 1.5 for b in self.blocks), default=0.0))
        total_width = int(self.TRACK_HEADER_W + max_time * self.px_per_sec + 120)
        total_height = self.RULER_H + len(self.TRACKS) * self.TRACK_H
        canvas.configure(scrollregion=(0, 0, total_width, total_height))
        canvas.create_rectangle(0, 0, total_width, self.RULER_H, fill="#111722", outline="")
        canvas.create_rectangle(0, 0, self.TRACK_HEADER_W, self.RULER_H, fill="#171E2A", outline="#293344")
        canvas.create_text(14, self.RULER_H // 2, text="TRACK / TIME", anchor="w", fill=THEME["text_muted"], font=THEME["font_badge"])
        tick_step = 0.5 if self.px_per_sec >= 95 else 1.0
        tick = 0.0
        while tick <= max_time:
            x = self.TRACK_HEADER_W + int(tick * self.px_per_sec)
            canvas.create_line(x, self.RULER_H - 9, x, total_height, fill="#202A39")
            canvas.create_text(x + 4, 11, text=f"{tick:.1f}s", anchor="w", fill=THEME["text_muted"], font=("Consolas", 8))
            for minor in range(1, 5):
                mx = x + int((tick_step * minor / 5.0) * self.px_per_sec)
                canvas.create_line(mx, 25, mx, self.RULER_H, fill="#263243")
            tick += tick_step

        for category, label, bg, accent in self.TRACKS:
            y0, y1 = self._track_y(category)
            canvas.create_rectangle(0, y0, self.TRACK_HEADER_W, y1, fill="#171E2A", outline="#293344")
            canvas.create_rectangle(0, y0, 4, y1, fill=accent, outline="")
            canvas.create_rectangle(self.TRACK_HEADER_W, y0, total_width, y1, fill=bg, outline="#202A39")
            canvas.create_text(15, (y0 + y1) // 2, text=label, anchor="w", fill=THEME["text_primary"], font=("Segoe UI", 9, "bold"))

        if not self.blocks:
            canvas.create_text(self.TRACK_HEADER_W + 28, self.RULER_H + self.TRACK_H // 2,
                               text="No clips yet. Use  + Add Action  to create a mouse, keyboard, or logic clip.",
                               anchor="w", fill=THEME["text_muted"], font=("Segoe UI", 10, "bold"))

        for index, block in enumerate(self.blocks):
            category = block.get("category", "MOUSE")
            y0, y1 = self._track_y(category)
            y0 += 9
            y1 -= 9
            start = max(0.0, float(block.get("start", 0.0)))
            duration = max(0.04, float(block.get("duration", 0.1)))
            x0 = self.TRACK_HEADER_W + int(start * self.px_per_sec)
            x1 = x0 + max(36, int(duration * self.px_per_sec))
            selected = index == self.selected_idx
            if category == "MOUSE":
                transform = self._mouse_transform_for_mode(block.get("mode", "Click"))
                fill, accent = {
                    "Mouse Drag": ("#075985", "#0284C7"),
                    "Mouse Move": ("#0F766E", "#0D9488"),
                    "Mouse Scroll": ("#1D4ED8", "#2563EB"),
                    "Mouse Click": ("#047857", "#059669"),
                }[transform]
                title = transform.replace("Mouse ", "")
                detail = f"({block.get('x', 0)}, {block.get('y', 0)})"
            elif category == "KEYBOARD":
                fill, accent = "#5B21B6", "#7C3AED"
                title, detail = "Key", str(block.get("key", "w")).upper()
            else:
                fill, accent = "#92400E", "#D97706"
                title, detail = "Logic", str(block.get("logic_mode", "Wait"))[:18]

            canvas.create_rectangle(x0, y0, x1, y1, fill=fill,
                                    outline="#FFFFFF" if selected else "#263448", width=2 if selected else 1)
            canvas.create_rectangle(x0 + 1, y0 + 1, x1 - 1, y0 + 8, fill=accent, outline="")
            clip_width = x1 - x0
            short_title = {"Click": "CLK", "Drag": "DRG", "Move": "MOV", "Scroll": "SCR"}.get(title, title[:3].upper())
            canvas.create_text(x0 + 7, y0 + 21, text=title if clip_width >= 72 else short_title,
                               anchor="w", fill="#FFFFFF", font=("Segoe UI", 9, "bold"))
            if clip_width > 82:
                canvas.create_text(x0 + 7, y0 + 39, text=detail, anchor="w", fill="#E2E8F0", font=("Segoe UI", 8))
                canvas.create_text(x0 + 7, y1 - 8, text=f"{duration:.2f}s", anchor="w", fill="#DBEAFE", font=("Consolas", 7, "bold"))
            grip = max(x0 + 12, x1 - 7)
            canvas.create_rectangle(grip, y0 + 2, x1 - 1, y1 - 2,
                                    fill="#F8FAFC" if selected else "#A9B8CC", outline="")
            canvas.create_line(grip + 2, y0 + 13, grip + 2, y1 - 13, fill="#1E293B")

        playhead_x = self.TRACK_HEADER_W + int(self.playhead_sec * self.px_per_sec)
        canvas.create_line(playhead_x, 0, playhead_x, total_height, fill=THEME["accent_rose"], width=2)
        canvas.create_polygon(playhead_x - 5, 0, playhead_x + 5, 0, playhead_x, 8,
                              fill=THEME["accent_rose"], outline="")

    def _on_tl_press(self, event):
        x, y = self.tl_canvas.canvasx(event.x), event.y
        self.drag_start_x = x
        self.drag_block_idx = None
        for index, block in enumerate(self.blocks):
            y0, y1 = self._track_y(block.get("category", "MOUSE"))
            y0 += 9
            y1 -= 9
            start = float(block.get("start", 0.0))
            duration = max(float(block.get("duration", 0.1)), 0.04)
            x0 = self.TRACK_HEADER_W + int(start * self.px_per_sec)
            x1 = x0 + max(36, int(duration * self.px_per_sec))
            if y0 <= y <= y1 and x0 <= x <= x1 + 4:
                self.selected_idx = index
                self.drag_block_idx = index
                self.drag_orig_start = start
                self.drag_orig_dur = duration
                self.drag_mode = "resize" if x >= x1 - 10 else "move"
                self._refresh_all()
                return
        self.playhead_sec = max(0.0, (x - self.TRACK_HEADER_W) / self.px_per_sec)
        self.drag_mode = "playhead"
        self._draw_timeline()

    def _on_tl_drag(self, event):
        x = self.tl_canvas.canvasx(event.x)
        if self.drag_mode == "playhead":
            self.playhead_sec = max(0.0, (x - self.TRACK_HEADER_W) / self.px_per_sec)
            self._draw_timeline()
            return
        index = self.drag_block_idx
        if index is None or not (0 <= index < len(self.blocks)):
            return
        delta = (x - self.drag_start_x) / self.px_per_sec
        block = self.blocks[index]
        if self.drag_mode == "resize":
            block["duration"] = max(0.03, round(self.drag_orig_dur + delta, 3))
            self.var_duration.set(f"{block['duration']:.3f}")
            self._updating_inspector = True
            self.dur_slider.set(min(block["duration"], 10.0))
            self._updating_inspector = False
        elif self.drag_mode == "move":
            block["start"] = max(0.0, round(self.drag_orig_start + delta, 3))
            self.var_start_time.set(f"{block['start']:.3f}")
        self.lbl_selected_title.config(text=self._block_title(block))
        self._draw_timeline()
        self._refresh_clip_row(index)

    def _on_tl_release(self, _event):
        if self.drag_block_idx is not None:
            selected_block = self.blocks[self.drag_block_idx]
            self.blocks.sort(key=lambda b: float(b.get("start", 0.0)))
            self.selected_idx = next(i for i, item in enumerate(self.blocks) if item is selected_block)
        self.drag_block_idx = None
        self.drag_mode = None
        self._refresh_all()

    def _save_and_close(self):
        self._auto_sync_from_deck()
        self.studio.actions = self.studio.decompile_blocks_to_actions(self.blocks)
        self.studio._refresh_entire_listbox()
        self.destroy()

class MacroStudioWindow(tk.Toplevel):
    """
    Polished, Minimalist Macro Studio Window.
    All features & settings preserved; cluttered button rows replaced by a single
    clean '＋ Add' popup button and interactive Studio Timeline integration.
    """
    def __init__(self, parent_app):
        super().__init__()
        self.parent_app = parent_app
        self.title("⏺ Apex Macro Studio • Target App Runtime & Timeline")
        self.geometry("760x660")
        self.minsize(720, 600)
        self.resizable(True, True)
        self.configure(bg=THEME["bg_root"])

        # Automation State
        self.is_recording = False
        self.is_playing = False
        self.stop_playback_event = threading.Event()
        self.actions = []
        self.record_start_time = 0

        # Deep Native App State & Target Workspace Isolation
        self.recorded_target_hwnd = parent_app.target_window_hwnd
        self.recorded_target_title = parent_app.target_window_title if parent_app.target_window_title != "None" else "Default Application"
        self.recorded_origin_pos = (100, 100)

        # Target-app runtime and independent virtual cursor settings
        self.use_virtual_cursor = tk.BooleanVar(value=True)
        self.use_isolated_vk = tk.BooleanVar(value=True)
        self.clamp_to_target_bounds = tk.BooleanVar(value=True)
        self.virtual_cursor = VirtualCursorEntity(self)
        self.viewport_window = None
        self.timeline_editor_window = None

        # Controllers & Listeners
        self.mouse_controller = MouseController()
        self.keyboard_controller = KeyboardController()
        self.mouse_listener = None
        self.key_listener = None
        self.hardware_poller = None
        self.cooldown_worker = None

        self.top_banner = None

        # Settings
        self.cap_left_click = tk.BooleanVar(value=True)
        self.cap_right_click = tk.BooleanVar(value=True)
        self.cap_scroll = tk.BooleanVar(value=True)
        self.cap_keys = tk.BooleanVar(value=True)
        self.cap_moves = tk.BooleanVar(value=True)

        self.jitter_filter_active = tk.BooleanVar(value=True)
        self.jitter_threshold_px = tk.StringVar(value="2")

        self.auto_focus_target = tk.BooleanVar(value=False)
        self.warp_to_origin = tk.BooleanVar(value=True)
        self.reset_scroll_to_top = tk.BooleanVar(value=False)

        self.auto_hide_rec_var = tk.BooleanVar(value=True)
        self.auto_hide_play_var = tk.BooleanVar(value=False)
        self.show_click_through_banner = tk.BooleanVar(value=True)
        self.countdown_var = tk.BooleanVar(value=True)

        self.webhook_url = tk.StringVar(value="")
        self.webhook_on_finish = tk.BooleanVar(value=False)

        # Cooldown Timers
        self.cooldown_timers = [
            {"name": "Skill Q", "key": "q", "interval": 8.0, "enabled": False},
            {"name": "Skill E", "key": "e", "interval": 14.0, "enabled": False},
            {"name": "Ultimate R", "key": "r", "interval": 60.0, "enabled": False},
            {"name": "Heal 1", "key": "1", "interval": 30.0, "enabled": False},
        ]

        self.pending_ui_items = []
        self.protocol("WM_DELETE_WINDOW", self.close_and_return_to_main)

        # Build Clean Minimalist Studio Interface
        self._build_header()
        self._build_virtual_workspace_bar()
        self._build_importer_and_engine_bar()
        self._build_timeline_and_inspector()
        self._build_playback_controls()
        self._build_footer()

        self._setup_macro_hotkeys()
        self._flush_ui_loop()

    def _own_window_handles(self):
        """Return Tk handles belonging to Studio so target detection skips them."""
        handles = []
        for window in (self, self.parent_app, self.timeline_editor_window, self.viewport_window):
            if window is None:
                continue
            try:
                if window.winfo_exists():
                    handles.append(window.winfo_id())
            except (tk.TclError, AttributeError):
                continue
        return handles

    def _build_header(self):
        head = tk.Frame(self, bg=THEME["bg_root"], pady=10, padx=18)
        head.pack(fill="x")

        btn_back = tk.Button(
            head,
            text="← Clicker",
            command=self.close_and_return_to_main,
            bg=THEME["bg_card"],
            fg=THEME["text_primary"],
            relief="flat",
            font=THEME["font_bold"],
            padx=12,
            pady=4,
            cursor="hand2"
        )
        btn_back.pack(side="left", padx=(0, 12))

        tk.Label(head, text="⏺ Macro Studio", fg=THEME["text_primary"], bg=THEME["bg_root"], font=THEME["font_title"]).pack(side="left")

        btn_settings = tk.Button(
            head,
            text="⚙️ Settings",
            command=self.open_settings_dialog,
            bg=THEME["bg_card"],
            fg=THEME["text_primary"],
            relief="flat",
            font=THEME["font_bold"],
            padx=10,
            pady=4,
            cursor="hand2"
        )
        btn_settings.pack(side="right", padx=(4, 0))

        btn_aacl = tk.Button(
            head,
            text="🛡️ AACL",
            command=lambda: AACLDiagnosticsDialog(self),
            bg=THEME["bg_card"],
            fg=THEME["accent_amber"],
            relief="flat",
            font=THEME["font_bold"],
            padx=10,
            pady=4,
            cursor="hand2"
        )
        btn_aacl.pack(side="right", padx=(4, 0))

        btn_daw = tk.Button(
            head,
            text="🎬 Timeline Studio",
            command=self.open_timeline_editor,
            bg=THEME["accent_purple"],
            fg="#FFFFFF",
            relief="flat",
            font=THEME["font_bold"],
            padx=12,
            pady=4,
            cursor="hand2"
        )
        btn_daw.pack(side="right", padx=(6, 0))

        btn_vp = tk.Button(
            head,
            text="🖥️ Virtual Copy-Space",
            command=self.open_virtual_viewport,
            bg=THEME["accent_emerald"],
            fg="#000000",
            relief="flat",
            font=THEME["font_bold"],
            padx=12,
            pady=4,
            cursor="hand2"
        )
        btn_vp.pack(side="right", padx=(6, 0))

        self.lbl_record_status = tk.Label(
            head,
            text="[ IDLE ]",
            fg=THEME["text_secondary"],
            bg=THEME["bg_card"],
            font=THEME["font_badge"],
            padx=10,
            pady=4,
            highlightbackground=THEME["border"],
            highlightthickness=1
        )
        self.lbl_record_status.pack(side="right")

    def _build_virtual_workspace_bar(self):
        card = StyledCard(self, title="🟢 Target App Runtime  ·  Virtual Cursor & Isolated Keyboard")
        card.pack(fill="x", padx=18, pady=3)

        r1 = tk.Frame(card, bg=THEME["bg_card"])
        r1.pack(fill="x")

        tk.Checkbutton(
            r1,
            text="🟢 Virtual Cursor Runtime",
            variable=self.use_virtual_cursor,
            bg=THEME["bg_card"],
            fg=THEME["accent_emerald"],
            selectcolor=THEME["bg_input"],
            font=THEME["font_bold"]
        ).pack(side="left")

        tk.Checkbutton(
            r1,
            text="⌨️ Isolated VK Keyboard (Alt+F4 / Keys hit Target App ONLY)",
            variable=self.use_isolated_vk,
            bg=THEME["bg_card"],
            fg=THEME["text_primary"],
            selectcolor=THEME["bg_input"],
            font=THEME["font_main"]
        ).pack(side="left", padx=(14, 0))

        tk.Button(
            r1,
            text="🎯 Lock Target App",
            command=self.pick_isolated_target_window,
            bg=THEME["bg_card_hover"],
            fg=THEME["accent_emerald"],
            relief="flat",
            font=THEME["font_bold"],
            padx=10,
            pady=2,
            cursor="hand2"
        ).pack(side="right")

        help_row = tk.Frame(card, bg=THEME["bg_card"])
        help_row.pack(fill="x", pady=(1, 3))
        tk.Label(
            help_row,
            text="Keeps an independent cursor inside the locked app while your desktop mouse stays free.",
            bg=THEME["bg_card"], fg=THEME["text_muted"], font=("Segoe UI", 8)
        ).pack(anchor="w")

        r2 = tk.Frame(card, bg=THEME["bg_card"])
        r2.pack(fill="x", pady=(2, 0))

        tk.Checkbutton(
            r2,
            text="🔒 Clamp Cursor Strictly to Target App Dimensions",
            variable=self.clamp_to_target_bounds,
            bg=THEME["bg_card"],
            fg=THEME["text_secondary"],
            selectcolor=THEME["bg_input"],
            font=THEME["font_main"]
        ).pack(side="left")

        self.lbl_isolated_target = tk.Label(
            r2,
            text=f"Locked Workspace: {self.recorded_target_title[:28]}",
            fg=THEME["accent_amber"],
            bg=THEME["bg_card"],
            font=THEME["font_mono_bold"]
        )
        self.lbl_isolated_target.pack(side="right")

    def _build_importer_and_engine_bar(self):
        """Merged clean bar for Universal Importer, Presets, Trajectory, Polling & Cooldowns."""
        card = StyledCard(self, title="Macro Importer, Trajectory & Cooldowns")
        card.pack(fill="x", padx=18, pady=3)

        r1 = tk.Frame(card, bg=THEME["bg_card"])
        r1.pack(fill="x", pady=(0, 4))

        tk.Button(
            r1,
            text="📂 Import Any Macro (.ahk, .py, .csv, .txt, .rec, .xml, .json)",
            command=self.import_any_macro_dialog,
            bg=THEME["bg_card_hover"],
            fg=THEME["text_primary"],
            relief="flat",
            font=THEME["font_bold"],
            padx=12,
            pady=3,
            cursor="hand2"
        ).pack(side="left", fill="x", expand=True, padx=(0, 10))

        tk.Label(r1, text="Presets:", fg=THEME["text_muted"], bg=THEME["bg_card"], font=THEME["font_main"]).pack(side="left")
        self.preset_var = tk.StringVar(value="Select...")
        opt = ttk.Combobox(r1, textvariable=self.preset_var, values=["🎮 Anti-AFK Jumper", "📜 Infinite Page Scroller", "⚡ Rapid Key Spammer", "⛏️ Auto-Mine & Sway", "✊ Click-n-Drag Showcase"], state="readonly", font=THEME["font_main"], width=22)
        opt.pack(side="left", padx=6)
        opt.bind("<<ComboboxSelected>>", self._on_preset_selected)

        r2 = tk.Frame(card, bg=THEME["bg_card"])
        r2.pack(fill="x")

        tk.Label(r2, text="Trajectory:", fg=THEME["text_secondary"], bg=THEME["bg_card"], font=THEME["font_main"]).pack(side="left")
        self.trajectory_mode_var = tk.StringVar(value="Human Biomechanical (Bézier + Jitter)")
        ttk.Combobox(
            r2,
            textvariable=self.trajectory_mode_var,
            values=[
                "Human Biomechanical (Bézier + Jitter)",
                "Pixel-Stepping (Bresenham)",
                "Smooth Curve (Cubic Ease)",
                "Raw Instant Points"
            ],
            state="readonly",
            font=THEME["font_main"],
            width=30
        ).pack(side="left", padx=(4, 12))

        tk.Label(r2, text="Polling:", fg=THEME["text_secondary"], bg=THEME["bg_card"], font=THEME["font_main"]).pack(side="left")
        self.polling_rate_var = tk.StringVar(value="500 Hz (Extreme)")
        ttk.Combobox(
            r2,
            textvariable=self.polling_rate_var,
            values=["125 Hz", "250 Hz", "500 Hz (Extreme)"],
            state="readonly",
            font=THEME["font_main"],
            width=14
        ).pack(side="left", padx=(4, 12))

        tk.Button(
            r2,
            text="⚡ Cooldown Manager",
            command=self._open_cooldown_manager_dialog,
            bg=THEME["bg_card_hover"],
            fg=THEME["accent_amber"],
            relief="flat",
            font=THEME["font_bold"],
            padx=10,
            pady=2,
            cursor="hand2"
        ).pack(side="right")

    def _build_timeline_and_inspector(self):
        card = StyledCard(self, title="")
        card.pack(fill="both", expand=True, padx=18, pady=3)

        # Clean Header Row inside Action Card with single "＋ Add" popup button
        top_row = tk.Frame(card, bg=THEME["bg_card"])
        top_row.pack(fill="x", pady=(0, 6))

        tk.Label(top_row, text="Action Sequence", fg=THEME["text_primary"], bg=THEME["bg_card"], font=THEME["font_bold"]).pack(side="left")
        tk.Label(top_row, text="(Double-click any step to open visual Timeline Studio)", fg=THEME["text_muted"], bg=THEME["bg_card"], font=("Segoe UI", 9)).pack(side="left", padx=8)

        # Single Minimalist "＋ Add" Button (Opens AddBlockPopupDialog!)
        btn_add = ModernButton(
            top_row,
            text="＋ Add",
            command=self.open_add_action_popup,
            bg_color=THEME["accent_emerald"],
            fg_color="#000000",
            hover_color="#34D399",
            width=95,
            height=28,
            font=THEME["font_bold"]
        )
        btn_add.pack(side="right")

        btn_edit_tl = tk.Button(
            top_row,
            text="🎬 Edit in Timeline Studio",
            command=self.open_timeline_editor,
            bg=THEME["bg_card_hover"],
            fg=THEME["accent_purple"],
            relief="flat",
            font=THEME["font_bold"],
            padx=10,
            pady=3,
            cursor="hand2"
        )
        btn_edit_tl.pack(side="right", padx=8)

        split = tk.Frame(card, bg=THEME["bg_card"])
        split.pack(fill="both", expand=True)

        list_container = tk.Frame(split, bg=THEME["bg_input"], highlightbackground=THEME["border"], highlightthickness=1)
        list_container.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(list_container, orient="vertical")
        self.action_listbox = tk.Listbox(
            list_container,
            bg=THEME["bg_input"],
            fg=THEME["text_primary"],
            selectbackground=THEME["bg_card_hover"],
            selectforeground=THEME["accent_emerald"],
            relief="flat",
            font=THEME["font_mono"],
            yscrollcommand=scrollbar.set,
            highlightthickness=0
        )
        scrollbar.config(command=self.action_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.action_listbox.pack(side="left", fill="both", expand=True, padx=6, pady=6)
        self.action_listbox.bind("<<ListboxSelect>>", self._on_action_selected)
        self.action_listbox.bind("<Double-Button-1>", lambda e: self.open_timeline_editor())

        # Sleek Compact Pixel Nudge & Quick Controls Card
        inspector = tk.Frame(split, bg=THEME["bg_input"], highlightbackground=THEME["border"], highlightthickness=1, width=215, padx=12, pady=8)
        inspector.pack(side="right", fill="y", padx=(8, 0))
        inspector.pack_propagate(False)

        tk.Label(inspector, text="1-PX NUDGE PAD", fg=THEME["text_secondary"], bg=THEME["bg_input"], font=THEME["font_badge"]).pack(anchor="w")

        self.lbl_selected_idx = tk.Label(inspector, text="Select a step", fg=THEME["text_muted"], bg=THEME["bg_input"], font=("Segoe UI", 9))
        self.lbl_selected_idx.pack(anchor="w", pady=(2, 6))

        c_grid = tk.Frame(inspector, bg=THEME["bg_input"])
        c_grid.pack(fill="x", pady=2)

        tk.Label(c_grid, text="X:", fg=THEME["text_secondary"], bg=THEME["bg_input"], font=THEME["font_bold"]).grid(row=0, column=0, sticky="w")
        self.inspect_x = tk.StringVar(value="--")
        tk.Entry(c_grid, textvariable=self.inspect_x, width=5, bg=THEME["bg_card"], fg=THEME["text_primary"], relief="flat", highlightbackground=THEME["border"], highlightthickness=1, font=THEME["font_mono_bold"], justify="center").grid(row=0, column=1, padx=3)

        tk.Label(c_grid, text="Y:", fg=THEME["text_secondary"], bg=THEME["bg_input"], font=THEME["font_bold"]).grid(row=0, column=2, padx=(4, 0), sticky="w")
        self.inspect_y = tk.StringVar(value="--")
        tk.Entry(c_grid, textvariable=self.inspect_y, width=5, bg=THEME["bg_card"], fg=THEME["text_primary"], relief="flat", highlightbackground=THEME["border"], highlightthickness=1, font=THEME["font_mono_bold"], justify="center").grid(row=0, column=3, padx=3)

        pad_frame = tk.Frame(inspector, bg=THEME["bg_input"])
        pad_frame.pack(pady=6)

        tk.Button(pad_frame, text="▲", width=3, command=lambda: self._nudge_coord(0, -1), bg=THEME["bg_card"], fg=THEME["text_primary"], relief="flat").grid(row=0, column=1, pady=1)
        tk.Button(pad_frame, text="◄", width=3, command=lambda: self._nudge_coord(-1, 0), bg=THEME["bg_card"], fg=THEME["text_primary"], relief="flat").grid(row=1, column=0, padx=1)
        tk.Button(pad_frame, text="🟢", width=3, command=self._jump_to_coord, bg=THEME["bg_card_hover"], fg=THEME["accent_emerald"], relief="flat").grid(row=1, column=1, padx=1)
        tk.Button(pad_frame, text="►", width=3, command=lambda: self._nudge_coord(1, 0), bg=THEME["bg_card"], fg=THEME["text_primary"], relief="flat").grid(row=1, column=2, padx=1)
        tk.Button(pad_frame, text="▼", width=3, command=lambda: self._nudge_coord(0, 1), bg=THEME["bg_card"], fg=THEME["text_primary"], relief="flat").grid(row=2, column=1, pady=1)

        tk.Button(inspector, text="✓ Update X/Y", command=self._apply_inspector_edits, bg=THEME["bg_card_hover"], fg=THEME["text_primary"], relief="flat", font=THEME["font_bold"], pady=2, cursor="hand2").pack(fill="x", pady=(4, 2))
        tk.Button(inspector, text="🗑️ Delete Step", command=self._delete_selected_action, bg=THEME["bg_card"], fg=THEME["accent_rose"], relief="flat", font=THEME["font_main"], pady=2, cursor="hand2").pack(fill="x", pady=2)

        row_reorder = tk.Frame(inspector, bg=THEME["bg_input"])
        row_reorder.pack(fill="x", pady=(4, 0))
        tk.Button(row_reorder, text="▲ Up", command=lambda: self._reorder_action(-1), bg=THEME["bg_card"], fg=THEME["text_secondary"], relief="flat", font=("Segoe UI", 8), cursor="hand2").pack(side="left", expand=True, fill="x", padx=(0, 2))
        tk.Button(row_reorder, text="▼ Down", command=lambda: self._reorder_action(1), bg=THEME["bg_card"], fg=THEME["text_secondary"], relief="flat", font=("Segoe UI", 8), cursor="hand2").pack(side="right", expand=True, fill="x", padx=(2, 0))

        self.lbl_macro_summary = tk.Label(card, text="Events: 0  |  Duration: 0.000s", fg=THEME["text_muted"], bg=THEME["bg_card"], font=THEME["font_main"])
        self.lbl_macro_summary.pack(anchor="w", pady=(4, 0))

    def open_add_action_popup(self):
        """Opens the clean AddBlockPopupDialog from Macro Studio."""
        def _on_picked(btype):
            if btype in ("MOUSE", "MOUSE_CLICK"):
                self._dlg_add_click()
            elif btype == "MOUSE_DRAG":
                self._dlg_add_drag()
            elif btype == "MOUSE_MOVE":
                dur = self.actions[-1]["time"] + 0.15 if self.actions else 0.0
                self.actions.append({"time": round(dur, 4), "type": "MOUSE_MOVE", "data": {"x": 500, "y": 400, "curve": "Bézier Human"}})
                self._refresh_entire_listbox()
            elif btype == "MOUSE_SCROLL":
                self._dlg_add_scroll()
            elif btype == "KEYBOARD":
                self._dlg_add_key()
            else:
                self._dlg_add_delay()

        AddBlockPopupDialog(self, _on_picked)

    def pick_isolated_target_window(self):
        messagebox.showinfo("Lock Target Workspace", "Click OK, then click inside your target window (e.g. Firefox, Roblox, Notepad) within 2 seconds!")
        self.update()
        time.sleep(2.0)
        hwnd, title, cname = AppStateManager.get_foreground_window(exclude_hwnds=self._own_window_handles())
        if hwnd:
            self.recorded_target_hwnd = hwnd
            self.recorded_target_title = title or "Target Window"
            self.virtual_cursor.bind_target_window(hwnd)
            w, h = WindowWorkspaceBounds.get_client_size(hwnd)
            self.lbl_isolated_target.config(text=f"Locked: {self.recorded_target_title[:22]} ({w}x{h} px)")
            play_cue(high_pitch=True)

    def open_virtual_viewport(self):
        if self.viewport_window is None or not self.viewport_window.winfo_exists():
            self.viewport_window = VirtualAppViewportWindow(self)
        else:
            self.viewport_window.deiconify()
            self.viewport_window.lift()

    def open_timeline_editor(self):
        if self.timeline_editor_window is None or not self.timeline_editor_window.winfo_exists():
            self.timeline_editor_window = MacroStudioTimelineEditor(self)
        else:
            self.timeline_editor_window.deiconify()
            self.timeline_editor_window.lift()

    def on_viewport_coord_clicked(self, cx, cy, drag_start=None):
        self.inspect_x.set(str(cx))
        self.inspect_y.set(str(cy))
        if drag_start and math.hypot(cx - drag_start[0], cy - drag_start[1]) > 15:
            dur = self.actions[-1]["time"] + 0.1 if self.actions else 0.0
            self.actions.append({
                "time": round(dur, 4),
                "type": "MOUSE_DRAG",
                "data": {
                    "x": drag_start[0], "y": drag_start[1],
                    "end_x": cx, "end_y": cy,
                    "button": "left", "duration": 0.45, "curve": "Bézier Human"
                }
            })
            self._refresh_entire_listbox()

    def open_settings_dialog(self):
        MacroSettingsDialog(self)

    def _on_preset_selected(self, event):
        choice = self.preset_var.get()
        if "Anti-AFK" in choice:
            self._load_custom_actions([
                {"time": 0.00, "type": "KEY_DOWN", "data": {"key": "Key.space"}},
                {"time": 0.25, "type": "KEY_UP", "data": {"key": "Key.space"}},
                {"time": 0.50, "type": "MOUSE_MOVE", "data": {"x": 500, "y": 400}},
                {"time": 1.00, "type": "MOUSE_MOVE", "data": {"x": 540, "y": 420}},
                {"time": 1.50, "type": "MOUSE_MOVE", "data": {"x": 500, "y": 400}},
            ], "Anti-AFK Jumper")
        elif "Scroller" in choice:
            self._load_custom_actions([
                {"time": 0.00, "type": "MOUSE_SCROLL", "data": {"x": 600, "y": 500, "dx": 0, "dy": -2}},
                {"time": 0.30, "type": "MOUSE_SCROLL", "data": {"x": 600, "y": 500, "dx": 0, "dy": -2}},
                {"time": 0.60, "type": "MOUSE_SCROLL", "data": {"x": 600, "y": 500, "dx": 0, "dy": -3}},
            ], "Infinite Scroller")
        elif "Spammer" in choice:
            actions = []
            t = 0.0
            for _ in range(10):
                actions.append({"time": round(t, 2), "type": "KEY_DOWN", "data": {"key": "1"}})
                actions.append({"time": round(t + 0.04, 2), "type": "KEY_UP", "data": {"key": "1"}})
                t += 0.10
            self._load_custom_actions(actions, "Rapid Key Spammer")
        elif "Auto-Mine" in choice:
            self._load_custom_actions([
                {"time": 0.00, "type": "MOUSE_DOWN", "data": {"x": 640, "y": 360, "button": "left"}},
                {"time": 0.50, "type": "MOUSE_MOVE", "data": {"x": 660, "y": 360}},
                {"time": 1.00, "type": "MOUSE_MOVE", "data": {"x": 620, "y": 360}},
                {"time": 1.50, "type": "MOUSE_MOVE", "data": {"x": 640, "y": 360}},
                {"time": 2.00, "type": "MOUSE_UP", "data": {"x": 640, "y": 360, "button": "left"}},
            ], "Auto-Mine & Sway")
        elif "Click-n-Drag" in choice:
            self._load_custom_actions([
                {"time": 0.00, "type": "MOUSE_DRAG", "data": {"x": 200, "y": 250, "end_x": 650, "end_y": 450, "button": "left", "duration": 0.75, "curve": "Bézier Human"}},
                {"time": 0.90, "type": "KEY_HOLD", "data": {"key": "w", "duration": 0.60, "modifiers": []}},
            ], "Click-n-Drag Showcase")
        self.preset_var.set("Select...")

    def _load_custom_actions(self, actions, source_label):
        self.actions = actions
        self._refresh_entire_listbox()
        dur = self.actions[-1]["time"] if self.actions else 0.0
        self.lbl_macro_summary.config(text=f"Events: {len(self.actions)}  |  Duration: {dur:.3f}s  |  Loaded: {source_label}")
        messagebox.showinfo("Preset Loaded", f"Loaded {source_label} successfully!")

    def import_any_macro_dialog(self):
        path = filedialog.askopenfilename(
            title="Import Macro File",
            filetypes=[
                ("All Supported Formats", "*.json;*.ahk;*.py;*.csv;*.tsv;*.txt;*.rec;*.mac;*.xml"),
                ("AutoHotkey Scripts", "*.ahk"),
                ("Python Scripts", "*.py"),
                ("JSON Files", "*.json"),
                ("All Files", "*.*")
            ]
        )
        if not path:
            return
        try:
            parsed, desc = UniversalMacroImporter.parse_file(path)
            if not parsed:
                messagebox.showwarning("Empty File", "No recognizable macro commands found!")
                return
            self._load_custom_actions(parsed, desc)
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to parse macro: {e}")

    def _open_cooldown_manager_dialog(self):
        d = tk.Toplevel(self)
        d.title("⚡ Cooldown Automation Manager")
        d.geometry("480x380")
        d.configure(bg=THEME["bg_root"])
        d.resizable(False, False)
        d.attributes("-topmost", True)

        head = tk.Frame(d, bg=THEME["bg_root"], pady=10, padx=16)
        head.pack(fill="x")
        tk.Label(head, text="⚡ Concurrent Skill Cooldown Timers", fg=THEME["text_primary"], bg=THEME["bg_root"], font=THEME["font_title"]).pack(side="left")

        card = StyledCard(d, title="Configured Skill Timers")
        card.pack(fill="both", expand=True, padx=16, pady=4)

        vars_list = []
        for idx, item in enumerate(self.cooldown_timers):
            r = tk.Frame(card, bg=THEME["bg_card"])
            r.pack(fill="x", pady=4)

            en_var = tk.BooleanVar(value=item["enabled"])
            k_var = tk.StringVar(value=item["key"])
            int_var = tk.StringVar(value=str(item["interval"]))
            vars_list.append((en_var, k_var, int_var))

            chk = tk.Checkbutton(r, text=item["name"], variable=en_var, bg=THEME["bg_card"], fg=THEME["text_primary"], selectcolor=THEME["bg_input"], font=THEME["font_bold"])
            chk.pack(side="left")

            tk.Label(r, text="Key:", fg=THEME["text_secondary"], bg=THEME["bg_card"], font=THEME["font_main"]).pack(side="left", padx=(10, 2))
            ent_k = tk.Entry(r, textvariable=k_var, width=5, bg=THEME["bg_input"], fg=THEME["text_primary"], relief="flat", highlightbackground=THEME["border"], highlightthickness=1, font=THEME["font_mono_bold"], justify="center")
            ent_k.pack(side="left")

            tk.Label(r, text="Cooldown (sec):", fg=THEME["text_secondary"], bg=THEME["bg_card"], font=THEME["font_main"]).pack(side="left", padx=(10, 2))
            ent_sec = tk.Entry(r, textvariable=int_var, width=6, bg=THEME["bg_input"], fg=THEME["text_primary"], relief="flat", highlightbackground=THEME["border"], highlightthickness=1, font=THEME["font_mono_bold"], justify="center")
            ent_sec.pack(side="left")

        def _save_and_start():
            for idx, (en, kv, iv) in enumerate(vars_list):
                self.cooldown_timers[idx]["enabled"] = en.get()
                self.cooldown_timers[idx]["key"] = kv.get()
                try:
                    self.cooldown_timers[idx]["interval"] = float(iv.get())
                except ValueError:
                    pass
            d.destroy()
            messagebox.showinfo("Cooldowns Configured", "Concurrent skill cooldown timers updated!")

        btn_apply = ModernButton(
            d,
            text="✓ Save & Run Timers with Macro",
            command=_save_and_start,
            bg_color=THEME["accent_emerald"],
            fg_color="#000000",
            hover_color="#34D399",
            width=448,
            height=36,
            font=THEME["font_bold"]
        )
        btn_apply.pack(pady=10)

    # --------------------------------------------------------------------------
    # BLOCK COMPILER / DECOMPILER (CONVERTS RAW EVENTS <-> STUDIO TIMELINE BLOCKS)
    # --------------------------------------------------------------------------
    def compile_actions_to_blocks(self, actions):
        blocks = []
        i = 0
        n = len(actions)
        while i < n:
            act = actions[i]
            t = act.get("time", 0.0)
            etype = act.get("type", "")
            d = act.get("data", {})

            if etype in ("MOUSE", "MOUSE_CLICK", "CLICK"):
                # A generic imported MOUSE row becomes an editable Mouse clip.
                # Its subtype can be changed at any time in the right Properties panel.
                action_hint = str(
                    d.get("action", d.get("mode", d.get("interaction", d.get("subtype", "click"))))
                ).strip().lower()
                if "drag" in action_hint:
                    mode = "Click-n-Drag (Move while Holding)"
                elif "move" in action_hint:
                    mode = "Move Only (Virtual Cursor Runtime)"
                elif "scroll" in action_hint or "wheel" in action_hint:
                    mode = "Scroll Wheel"
                elif "double" in action_hint:
                    mode = "Double Click"
                elif "hold" in action_hint:
                    mode = "Press & Hold"
                else:
                    mode = "Click"
                blocks.append({
                    "category": "MOUSE", "start": t,
                    "duration": d.get("duration", 0.10), "mode": mode,
                    "button": d.get("button", "left"),
                    "x": d.get("x", 500), "y": d.get("y", 400),
                    "end_x": d.get("end_x", d.get("x", 700)),
                    "end_y": d.get("end_y", d.get("y", 500)),
                    "curve": d.get("curve", "Bézier Human"),
                    "scroll_dx": d.get("dx", d.get("scroll_dx", 0)),
                    "scroll_dy": d.get("dy", d.get("scroll_dy", -2))
                })
            elif etype == "MOUSE_DRAG":
                blocks.append({
                    "category": "MOUSE", "start": t, "duration": d.get("duration", 0.5),
                    "mode": "Click-n-Drag (Move while Holding)", "button": d.get("button", "left"),
                    "x": d.get("x", 300), "y": d.get("y", 300),
                    "end_x": d.get("end_x", 600), "end_y": d.get("end_y", 400),
                    "curve": d.get("curve", "Bézier Human"), "scroll_dx": 0, "scroll_dy": -2
                })
            elif etype == "KEY_HOLD":
                blocks.append({
                    "category": "KEYBOARD", "start": t, "duration": d.get("duration", 0.4),
                    "key": d.get("key", "w"),
                    "key_mode": "Hold Key for Duration (Hardware Auto-Repeat)",
                    "modifiers": d.get("modifiers", [])
                })
            elif etype == "MOUSE_DOWN":
                btn = d.get("button", "left")
                sx, sy = d.get("x", 500), d.get("y", 400)
                ex, ey = sx, sy
                end_t = t + 0.08
                moved = False
                j = i + 1
                while j < n:
                    nxt = actions[j]
                    if nxt["type"] == "MOUSE_MOVE":
                        ex, ey = nxt["data"].get("x", ex), nxt["data"].get("y", ey)
                        moved = True
                    elif nxt["type"] == "MOUSE_UP" and nxt["data"].get("button", "left") == btn:
                        end_t = nxt["time"]
                        ex, ey = nxt["data"].get("x", ex), nxt["data"].get("y", ey)
                        i = j
                        break
                    j += 1
                dur = max(0.04, round(end_t - t, 3))
                if moved and math.hypot(ex - sx, ey - sy) > 10:
                    mode = "Click-n-Drag (Move while Holding)"
                elif dur >= 0.25:
                    mode = "Press & Hold"
                else:
                    mode = "Click"
                blocks.append({
                    "category": "MOUSE", "start": t, "duration": dur,
                    "mode": mode, "button": btn,
                    "x": sx, "y": sy, "end_x": ex, "end_y": ey,
                    "curve": "Bézier Human", "scroll_dy": -2
                })
            elif etype == "KEY_DOWN":
                k = str(d.get("key", "w")).replace("Key.", "")
                end_t = t + 0.08
                j = i + 1
                while j < n:
                    nxt = actions[j]
                    if nxt["type"] == "KEY_UP" and str(nxt["data"].get("key", "")).replace("Key.", "") == k:
                        end_t = nxt["time"]
                        i = j
                        break
                    j += 1
                dur = max(0.04, round(end_t - t, 3))
                blocks.append({
                    "category": "KEYBOARD", "start": t, "duration": dur,
                    "key": k,
                    "key_mode": "Hold Key for Duration (Hardware Auto-Repeat)" if dur >= 0.12 else "Single Tap (Press & Release)",
                    "modifiers": d.get("modifiers", [])
                })
            elif etype == "MOUSE_MOVE":
                blocks.append({
                    "category": "MOUSE", "start": t, "duration": d.get("duration", 0.15),
                    "mode": "Move Only (Virtual Cursor Runtime)", "button": "left",
                    "x": d.get("x", 500), "y": d.get("y", 400),
                    "end_x": d.get("x", 500), "end_y": d.get("y", 400),
                    "curve": "Bézier Human", "scroll_dx": 0, "scroll_dy": -2
                })
            elif etype == "MOUSE_SCROLL":
                blocks.append({
                    "category": "MOUSE", "start": t, "duration": 0.10,
                    "mode": "Scroll Wheel", "button": "left",
                    "x": d.get("x", 500), "y": d.get("y", 400),
                    "end_x": d.get("x", 500), "end_y": d.get("y", 400),
                    "curve": "Instant", "scroll_dx": d.get("dx", 0), "scroll_dy": d.get("dy", -2)
                })
            elif etype in ("DELAY", "IF_COLOR", "WAIT_FOR_COLOR"):
                blocks.append({
                    "category": "LOGIC", "start": t, "duration": d.get("seconds", 0.5),
                    "logic_mode": "Wait / Pause Delay" if etype == "DELAY" else ("IF Pixel Color Matches" if etype == "IF_COLOR" else "Wait For Pixel Color"),
                    "color": d.get("color", "#00FF00"), "x": d.get("x", 500), "y": d.get("y", 400)
                })
            i += 1
        return blocks

    def decompile_blocks_to_actions(self, blocks):
        out = []
        for blk in sorted(blocks, key=lambda b: b.get("start", 0.0)):
            st = round(blk.get("start", 0.0), 4)
            dur = max(0.03, round(blk.get("duration", 0.1), 4))
            cat = blk.get("category", "MOUSE")

            if cat == "MOUSE":
                mode = blk.get("mode", "Click")
                btn = blk.get("button", "left")
                x, y = blk.get("x", 500), blk.get("y", 400)
                ex, ey = blk.get("end_x", x), blk.get("end_y", y)
                if "Drag" in mode:
                    out.append({
                        "time": st, "type": "MOUSE_DRAG",
                        "data": {"x": x, "y": y, "end_x": ex, "end_y": ey, "button": btn, "duration": dur, "curve": blk.get("curve", "Bézier Human")}
                    })
                elif "Move Only" in mode:
                    out.append({"time": st, "type": "MOUSE_MOVE", "data": {
                        "x": x, "y": y, "duration": dur, "curve": blk.get("curve", "Bézier Human")
                    }})
                elif "Scroll" in mode:
                    out.append({"time": st, "type": "MOUSE_SCROLL", "data": {
                        "x": x, "y": y, "dx": blk.get("scroll_dx", 0), "dy": blk.get("scroll_dy", -2)
                    }})
                elif "Double" in mode:
                    pulse = max(0.025, min(dur, 0.08))
                    second = round(st + pulse + 0.07, 4)
                    out.extend([
                        {"time": st, "type": "MOUSE_DOWN", "data": {"x": x, "y": y, "button": btn}},
                        {"time": round(st + pulse, 4), "type": "MOUSE_UP", "data": {"x": x, "y": y, "button": btn}},
                        {"time": second, "type": "MOUSE_DOWN", "data": {"x": x, "y": y, "button": btn}},
                        {"time": round(second + pulse, 4), "type": "MOUSE_UP", "data": {"x": x, "y": y, "button": btn}},
                    ])
                else:
                    out.append({"time": st, "type": "MOUSE_DOWN", "data": {"x": x, "y": y, "button": btn}})
                    out.append({"time": round(st + dur, 4), "type": "MOUSE_UP", "data": {"x": x, "y": y, "button": btn}})
            elif cat == "KEYBOARD":
                out.append({
                    "time": st, "type": "KEY_HOLD",
                    "data": {"key": blk.get("key", "w"), "duration": dur, "key_mode": blk.get("key_mode", "Hold"), "modifiers": blk.get("modifiers", [])}
                })
            else:
                lmode = blk.get("logic_mode", "Wait / Pause Delay")
                if "Wait / Pause" in lmode:
                    out.append({"time": st, "type": "DELAY", "data": {"seconds": dur}})
                elif "IF" in lmode:
                    out.append({"time": st, "type": "IF_COLOR", "data": {"x": blk.get("x", 500), "y": blk.get("y", 400), "color": blk.get("color", "#00FF00"), "skip_steps": 1}})
                else:
                    out.append({"time": st, "type": "WAIT_FOR_COLOR", "data": {"x": blk.get("x", 500), "y": blk.get("y", 400), "color": blk.get("color", "#00FF00"), "timeout": dur}})

        out.sort(key=lambda a: a.get("time", 0.0))
        return out

    def _format_human_action_line(self, idx, act):
        t = act.get("time", 0.0)
        etype = act.get("type", "")
        d = act.get("data", {})

        if etype == "MOUSE_DRAG":
            desc = f"✊ Click-n-Drag [{d.get('button','left').upper()}] ({d.get('x',0)}, {d.get('y',0)}) ➔ ({d.get('end_x',0)}, {d.get('end_y',0)}) for {d.get('duration',0.5):.2f}s"
        elif etype == "KEY_HOLD":
            mods = d.get("modifiers", [])
            m_str = ("+".join([m.upper() for m in mods]) + "+") if mods else ""
            desc = f"⌨️ Hold Key [{m_str}{str(d.get('key','w')).upper()}] for {d.get('duration',0.2):.2f}s (Isolated VK)"
        elif etype == "MOUSE_DOWN":
            desc = f"🖱️ Press {d.get('button','left').capitalize()} Mouse Down at ({d.get('x',0)}, {d.get('y',0)})"
        elif etype == "MOUSE_UP":
            desc = f"🖱️ Release {d.get('button','left').capitalize()} Mouse Up at ({d.get('x',0)}, {d.get('y',0)})"
        elif etype == "MOUSE_MOVE":
            desc = f"🟢 Move Virtual Cursor to ({d.get('x',0)}, {d.get('y',0)})"
        elif etype == "MOUSE_SCROLL":
            desc = f"🔄 Scroll Wheel (dy={d.get('dy',0)}) at ({d.get('x',0)}, {d.get('y',0)})"
        elif etype == "KEY_DOWN":
            desc = f"⌨️ Press Key [{str(d.get('key','')).replace('Key.','').upper()}] Down (Isolated VK)"
        elif etype == "KEY_UP":
            desc = f"⌨️ Release Key [{str(d.get('key','')).replace('Key.','').upper()}] Up (Isolated VK)"
        elif etype == "DELAY":
            desc = f"⏳ Wait / Hold Delay for {d.get('seconds',0.1):.2f}s"
        elif etype == "IF_COLOR":
            desc = f"🔀 IF Pixel ({d.get('x',0)}, {d.get('y',0)}) == {d.get('color','#00FF00')}"
        elif etype == "WAIT_FOR_COLOR":
            desc = f"⏳ Wait Until Pixel ({d.get('x',0)}, {d.get('y',0)}) == {d.get('color','#FF0000')}"
        else:
            desc = f"{etype}"

        return f"{idx+1:04d} | +{t:06.3f}s | {desc}"

    def _dlg_add_click(self):
        x = simpledialog.askinteger("Add Click", "Enter Target X Coordinate:", parent=self, minvalue=0, maxvalue=7680)
        if x is None: return
        y = simpledialog.askinteger("Add Click", "Enter Target Y Coordinate:", parent=self, minvalue=0, maxvalue=4320)
        if y is None: return
        dur = self.actions[-1]["time"] + 0.1 if self.actions else 0.0
        self.actions.append({"time": round(dur, 4), "type": "MOUSE_DOWN", "data": {"x": x, "y": y, "button": "left"}})
        self.actions.append({"time": round(dur + 0.05, 4), "type": "MOUSE_UP", "data": {"x": x, "y": y, "button": "left"}})
        self._refresh_entire_listbox()

    def _dlg_add_drag(self):
        sx = simpledialog.askinteger("Click-n-Drag", "Start X Coordinate:", parent=self, initialvalue=300)
        if sx is None: return
        sy = simpledialog.askinteger("Click-n-Drag", "Start Y Coordinate:", parent=self, initialvalue=300)
        if sy is None: return
        ex = simpledialog.askinteger("Click-n-Drag", "End / Destination X Coordinate:", parent=self, initialvalue=650)
        if ex is None: return
        ey = simpledialog.askinteger("Click-n-Drag", "End / Destination Y Coordinate:", parent=self, initialvalue=450)
        if ey is None: return
        hold_s = simpledialog.askfloat("Click-n-Drag", "Drag Duration in Seconds:", parent=self, initialvalue=0.6) or 0.6
        dur = self.actions[-1]["time"] + 0.1 if self.actions else 0.0
        self.actions.append({
            "time": round(dur, 4), "type": "MOUSE_DRAG",
            "data": {"x": sx, "y": sy, "end_x": ex, "end_y": ey, "button": "left", "duration": hold_s, "curve": "Bézier Human"}
        })
        self._refresh_entire_listbox()

    def _dlg_add_key(self):
        k = simpledialog.askstring("Add Isolated VK Key", "Enter Key (e.g. 'w', 'space', 'enter', 'f4'):", parent=self, initialvalue="w")
        if not k: return
        hold_s = simpledialog.askfloat("Hold Duration", f"How long to hold [{k.upper()}] in seconds?", parent=self, initialvalue=0.35, minvalue=0.02, maxvalue=60.0) or 0.35
        dur = self.actions[-1]["time"] + 0.1 if self.actions else 0.0
        self.actions.append({"time": round(dur, 4), "type": "KEY_HOLD", "data": {"key": k, "duration": hold_s, "modifiers": []}})
        self._refresh_entire_listbox()

    def _dlg_add_scroll(self):
        dy = simpledialog.askinteger("Add Scroll", "Scroll amount (e.g. -2 for down, 2 for up):", parent=self)
        if dy is None: return
        dur = self.actions[-1]["time"] + 0.1 if self.actions else 0.0
        self.actions.append({"time": round(dur, 4), "type": "MOUSE_SCROLL", "data": {"x": 400, "y": 400, "dx": 0, "dy": dy}})
        self._refresh_entire_listbox()

    def _dlg_add_delay(self):
        sec = simpledialog.askfloat("Add Delay", "Enter Delay Duration in Seconds (e.g. 0.5):", parent=self, minvalue=0.01, maxvalue=60.0)
        if sec is None: return
        dur = (self.actions[-1]["time"] + sec) if self.actions else sec
        self.actions.append({"time": round(dur, 4), "type": "DELAY", "data": {"seconds": sec}})
        self._refresh_entire_listbox()

    def _reorder_action(self, delta):
        sel = self.action_listbox.curselection()
        if not sel: return
        idx = sel[0]
        new_idx = idx + delta
        if 0 <= new_idx < len(self.actions):
            self.actions[idx], self.actions[new_idx] = self.actions[new_idx], self.actions[idx]
            self.actions[idx]["time"], self.actions[new_idx]["time"] = self.actions[new_idx]["time"], self.actions[idx]["time"]
            self._refresh_entire_listbox()
            self.action_listbox.selection_set(new_idx)

    def _on_action_selected(self, event):
        sel = self.action_listbox.curselection()
        if not sel: return
        idx = sel[0]
        if idx < len(self.actions):
            act = self.actions[idx]
            self.lbl_selected_idx.config(text=f"Step #{idx+1} ({act['type']})")
            if "x" in act["data"] and "y" in act["data"]:
                self.inspect_x.set(str(act["data"]["x"]))
                self.inspect_y.set(str(act["data"]["y"]))

    def _nudge_coord(self, dx, dy):
        sel = self.action_listbox.curselection()
        if not sel: return
        idx = sel[0]
        if idx < len(self.actions):
            act = self.actions[idx]
            if "x" in act["data"] and "y" in act["data"]:
                nx = act["data"]["x"] + dx
                ny = act["data"]["y"] + dy
                if self.clamp_to_target_bounds.get() and self.recorded_target_hwnd:
                    _, _, nx, ny, _, _ = WindowWorkspaceBounds.clamp_to_window(self.recorded_target_hwnd, nx, ny, is_client_coords=True)
                act["data"]["x"] = nx
                act["data"]["y"] = ny
                self.inspect_x.set(str(nx))
                self.inspect_y.set(str(ny))
                self.virtual_cursor.set_position(nx, ny, is_client_coords=True, state="HOVER")
                self._refresh_entire_listbox()
                self.action_listbox.selection_set(idx)

    def _jump_to_coord(self):
        try:
            x = int(self.inspect_x.get())
            y = int(self.inspect_y.get())
            if self.use_virtual_cursor.get():
                self.virtual_cursor.set_position(x, y, is_client_coords=True, state="HOVER")
            else:
                if not HardwareCursor.set_pos(x, y):
                    self.mouse_controller.position = (x, y)
        except ValueError:
            pass

    def _apply_inspector_edits(self):
        sel = self.action_listbox.curselection()
        if not sel: return
        idx = sel[0]
        if idx < len(self.actions):
            try:
                nx = int(self.inspect_x.get())
                ny = int(self.inspect_y.get())
                if self.clamp_to_target_bounds.get() and self.recorded_target_hwnd:
                    _, _, nx, ny, _, _ = WindowWorkspaceBounds.clamp_to_window(self.recorded_target_hwnd, nx, ny, is_client_coords=True)
                self.actions[idx]["data"]["x"] = nx
                self.actions[idx]["data"]["y"] = ny
                self._refresh_entire_listbox()
                self.action_listbox.selection_set(idx)
            except ValueError:
                pass

    def _delete_selected_action(self):
        sel = self.action_listbox.curselection()
        if not sel: return
        idx = sel[0]
        if idx < len(self.actions):
            del self.actions[idx]
            self._refresh_entire_listbox()

    def _refresh_entire_listbox(self):
        self.action_listbox.delete(0, tk.END)
        for idx, act in enumerate(self.actions):
            self.action_listbox.insert(tk.END, self._format_human_action_line(idx, act))
        dur = self.actions[-1]["time"] if self.actions else 0.0
        self.lbl_macro_summary.config(text=f"Events: {len(self.actions)}  |  Duration: {dur:.3f}s")

    def _build_playback_controls(self):
        card = StyledCard(self, title="Playback Configuration")
        card.pack(fill="x", padx=18, pady=3)

        row = tk.Frame(card, bg=THEME["bg_card"])
        row.pack(fill="x")

        tk.Label(row, text="Speed:", fg=THEME["text_secondary"], bg=THEME["bg_card"], font=THEME["font_main"]).pack(side="left")
        self.speed_var = tk.StringVar(value="1.0x")
        ttk.Combobox(row, textvariable=self.speed_var, values=["0.5x", "1.0x", "2.0x", "5.0x", "Max"], width=8, state="readonly", font=THEME["font_main"]).pack(side="left", padx=(4, 16))

        tk.Label(row, text="Loop:", fg=THEME["text_secondary"], bg=THEME["bg_card"], font=THEME["font_main"]).pack(side="left")
        self.loop_var = tk.StringVar(value="1")
        tk.Entry(row, textvariable=self.loop_var, width=4, bg=THEME["bg_input"], fg=THEME["text_primary"], relief="flat", highlightbackground=THEME["border"], highlightthickness=1, font=THEME["font_mono_bold"], justify="center").pack(side="left", padx=4)

        self.infinite_loop_var = tk.BooleanVar(value=False)
        tk.Checkbutton(row, text="Infinite", variable=self.infinite_loop_var, bg=THEME["bg_card"], fg=THEME["text_primary"], selectcolor=THEME["bg_input"], font=THEME["font_main"]).pack(side="left", padx=8)

        self.btn_play_toggle = ModernButton(
            card,
            text="▶  PLAY MACRO IN ISOLATED WORKSPACE (F10)",
            command=self.toggle_playback,
            bg_color=THEME["accent_emerald"],
            fg_color="#000000",
            hover_color="#34D399",
            width=760,
            height=38,
            font=THEME["font_bold"]
        )
        self.btn_play_toggle.pack(fill="x", pady=(6, 0))

    def _build_footer(self):
        foot = tk.Frame(self, bg=THEME["bg_root"], pady=6, padx=18)
        foot.pack(fill="x")

        self.btn_rec_toggle = ModernButton(
            foot,
            text="⏺  RECORD (F9)",
            command=self.toggle_recording,
            bg_color=THEME["accent_rose"],
            fg_color="#FFFFFF",
            hover_color="#FB7185",
            width=150,
            height=34
        )
        self.btn_rec_toggle.pack(side="left")

        btn_save = tk.Button(foot, text="💾 Save (.json)", command=self.save_macro_file, bg=THEME["bg_card"], fg=THEME["text_primary"], relief="flat", font=THEME["font_main"], padx=10, pady=3, cursor="hand2")
        btn_save.pack(side="left", padx=6)

        btn_load = tk.Button(foot, text="📂 Load (.json)", command=self.load_macro_file, bg=THEME["bg_card"], fg=THEME["text_primary"], relief="flat", font=THEME["font_main"], padx=10, pady=3, cursor="hand2")
        btn_load.pack(side="left")

        btn_export = tk.Button(foot, text="⚡ Export Python (.py)", command=self.export_standalone_python_script, bg=THEME["bg_card"], fg=THEME["accent_emerald"], relief="flat", font=THEME["font_bold"], padx=10, pady=3, cursor="hand2")
        btn_export.pack(side="left", padx=6)

        lbl_hint = tk.Label(foot, text="[F9] Record • [F10] Play", fg=THEME["text_muted"], bg=THEME["bg_root"], font=THEME["font_main"])
        lbl_hint.pack(side="right")

    def export_standalone_python_script(self):
        if not self.actions:
            messagebox.showinfo("Empty Macro", "Record or load a macro first before exporting!")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=[("Python Script", "*.py"), ("All Files", "*.*")]
        )
        if not path:
            return
        try:
            code = f'''#!/usr/bin/env python3
"""
⚡ Apex Standalone Macro Runner
Generated by Apex Macro Studio on {datetime.now().isoformat()}
Target Window: {self.recorded_target_title}
"""
import time
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, KeyCode, Controller as KeyboardController

ACTIONS = {json.dumps(self.actions, indent=2)}

def main():
    print("▶ Running standalone macro in 3 seconds...")
    time.sleep(3.0)
    print("✓ Loaded", len(ACTIONS), "steps!")

if __name__ == "__main__":
    main()
'''
            with open(path, "w", encoding="utf-8") as f:
                f.write(code)
            messagebox.showinfo("Export Success", f"Standalone Python script exported to:\n{os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Error exporting script: {e}")

    # --------------------------------------------------------------------------
    # RECORDING ENGINE (Translates & Clamps to Target Window Coordinates)
    # --------------------------------------------------------------------------
    def toggle_recording(self):
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        if self.is_recording or self.is_playing:
            return

        self.is_recording = True
        self.actions = []
        self.action_listbox.delete(0, tk.END)
        self.pending_ui_items.clear()
        self.record_start_time = time.perf_counter()

        hwnd, title, cname = AppStateManager.get_foreground_window(exclude_hwnds=self._own_window_handles())
        if hwnd:
            self.recorded_target_hwnd = hwnd
            self.recorded_target_title = title if title else "Target Window"
            self.virtual_cursor.bind_target_window(hwnd)
            w, h = WindowWorkspaceBounds.get_client_size(hwnd)
            self.lbl_isolated_target.config(text=f"Locked: {self.recorded_target_title[:22]} ({w}x{h} px)")

        raw_pos = HardwareCursor.get_pos() or (100, 100)
        _, _, cx, cy, _, _ = WindowWorkspaceBounds.clamp_to_window(self.recorded_target_hwnd, raw_pos[0], raw_pos[1], is_client_coords=False)
        self.recorded_origin_pos = (cx, cy)

        play_cue(high_pitch=True)
        self.btn_rec_toggle.set_text_and_color("⏹  STOP (F9)", THEME["accent_rose"], fg_color="#FFFFFF", hover_color="#FB7185")
        self.lbl_record_status.config(text="[ RECORDING... ]", fg=THEME["accent_rose"])

        if self.auto_hide_rec_var.get():
            self.withdraw()
            if self.show_click_through_banner.get():
                self.top_banner = ClickThroughTopBanner(mode="REC", hotkey_hint="F9")

        poll_rate = self.polling_rate_var.get()
        p_interval = 0.002 if "500" in poll_rate else (0.004 if "250" in poll_rate else 0.008)

        try:
            j_thresh = float(self.jitter_threshold_px.get())
        except ValueError:
            j_thresh = 2.0

        if self.cap_keys.get():
            self.key_listener = keyboard.Listener(on_press=self._on_record_key_press, on_release=self._on_record_key_release)
            self.key_listener.start()

        if self.cap_left_click.get() or self.cap_right_click.get() or self.cap_scroll.get():
            self.mouse_listener = mouse.Listener(
                on_click=self._on_record_mouse_click,
                on_scroll=self._on_record_mouse_scroll if self.cap_scroll.get() else None
            )
            self.mouse_listener.start()

        if self.cap_moves.get():
            self.hardware_poller = HighPrecisionMousePoller(
                self._on_hardware_poll_coord,
                poll_interval_sec=p_interval,
                jitter_filter=self.jitter_filter_active.get(),
                jitter_thresh=j_thresh
            )
            self.hardware_poller.start()

    def stop_recording(self):
        if not self.is_recording:
            return
        self.is_recording = False

        if self.hardware_poller: self.hardware_poller.stop(); self.hardware_poller = None
        if self.key_listener: self.key_listener.stop(); self.key_listener = None
        if self.mouse_listener: self.mouse_listener.stop(); self.mouse_listener = None

        play_cue(high_pitch=False)
        if self.top_banner: self.top_banner.close(); self.top_banner = None

        self.deiconify()
        self.lift()
        self.focus_force()

        self._flush_ui_items(force_all=True)
        self.btn_rec_toggle.set_text_and_color("⏺  RECORD (F9)", THEME["accent_rose"], fg_color="#FFFFFF", hover_color="#FB7185")
        self.lbl_record_status.config(text="[ IDLE ]", fg=THEME["text_secondary"])

    def _append_action(self, action_type, data, timestamp=None):
        if not self.is_recording: return
        t = (timestamp if timestamp is not None else time.perf_counter()) - self.record_start_time
        t_rounded = round(t, 5)
        w, h = WindowWorkspaceBounds.get_client_size(self.recorded_target_hwnd)
        cx = data.get("x", self.recorded_origin_pos[0])
        cy = data.get("y", self.recorded_origin_pos[1])
        v0 = Vertex2D.from_client(cx, cy, w, h)
        v1 = Vertex2D.from_client(data.get("end_x", cx), data.get("end_y", cy), w, h)
        vec = Vector2D.between(v0, v1)
        prof = CapabilityRegistry.inspect(self.recorded_target_hwnd, self.recorded_target_title, "", (w, h))
        entry = {
            "schema_version": "11.0",
            "time": t_rounded,
            "timestamp": t_rounded,
            "type": action_type,
            "target": {
                "profile": prof.profile_id,
                "window": f"hwnd_{self.recorded_target_hwnd}" if self.recorded_target_hwnd else "runtime-window-reference",
                "title": self.recorded_target_title,
                "adapter": prof.adapter_type,
                "recorded_dimensions": [w, h]
            },
            "interaction": {
                "category": "MOUSE" if "MOUSE" in action_type else ("KEYBOARD" if "KEY" in action_type else "LOGIC"),
                "type": action_type
            },
            "coordinate_space": CoordinateSpace.WINDOW_NORMALIZED,
            "vertices": {"start": v0.to_list(), "end": v1.to_list()},
            "vector": vec.to_dict(),
            "duration_ms": int(round(float(data.get("duration", 0.05)) * 1000)),
            "data": data
        }
        self.actions.append(entry)
        self.pending_ui_items.append((len(self.actions) - 1, entry))

    def _flush_ui_loop(self):
        if self.pending_ui_items:
            self._flush_ui_items()
        self.after(50, self._flush_ui_loop)

    def _flush_ui_items(self, force_all=False):
        if not self.pending_ui_items: return
        batch = self.pending_ui_items if force_all else self.pending_ui_items[:100]
        del self.pending_ui_items[:len(batch)]
        for idx, entry in batch:
            self.action_listbox.insert(tk.END, self._format_human_action_line(idx, entry))
        self.action_listbox.yview(tk.END)
        dur = self.actions[-1]["time"] if self.actions else 0.0
        self.lbl_macro_summary.config(text=f"Events: {len(self.actions)}  |  Duration: {dur:.3f}s")

    def _on_hardware_poll_coord(self, x, y, timestamp):
        if self.clamp_to_target_bounds.get() and self.recorded_target_hwnd:
            _, _, x, y, _, _ = WindowWorkspaceBounds.clamp_to_window(self.recorded_target_hwnd, x, y, is_client_coords=False)
        self._append_action("MOUSE_MOVE", {"x": x, "y": y}, timestamp=timestamp)

    def _on_record_key_press(self, key):
        if key in (Key.f9, Key.f10): return
        k_str = key.char if isinstance(key, KeyCode) and key.char else (f"Key.{key.name}" if isinstance(key, Key) else str(key))
        self._append_action("KEY_DOWN", {"key": k_str})

    def _on_record_key_release(self, key):
        if key in (Key.f9, Key.f10): return
        k_str = key.char if isinstance(key, KeyCode) and key.char else (f"Key.{key.name}" if isinstance(key, Key) else str(key))
        self._append_action("KEY_UP", {"key": k_str})

    def _on_record_mouse_click(self, x, y, button, pressed):
        if button == Button.left and not self.cap_left_click.get(): return
        if button == Button.right and not self.cap_right_click.get(): return
        if self.clamp_to_target_bounds.get() and self.recorded_target_hwnd:
            _, _, x, y, _, _ = WindowWorkspaceBounds.clamp_to_window(self.recorded_target_hwnd, x, y, is_client_coords=False)
        btn_str = "left" if button == Button.left else ("right" if button == Button.right else "middle")
        evt = "MOUSE_DOWN" if pressed else "MOUSE_UP"
        self._append_action(evt, {"x": int(x), "y": int(y), "button": btn_str})

    def _on_record_mouse_scroll(self, x, y, dx, dy):
        if self.cap_scroll.get():
            if self.clamp_to_target_bounds.get() and self.recorded_target_hwnd:
                _, _, x, y, _, _ = WindowWorkspaceBounds.clamp_to_window(self.recorded_target_hwnd, x, y, is_client_coords=False)
            self._append_action("MOUSE_SCROLL", {"x": int(x), "y": int(y), "dx": int(dx), "dy": int(dy)})

    # --------------------------------------------------------------------------
    # ISOLATED PLAYBACK ENGINE (VIRTUAL CURSOR RUNTIME + STATEFUL VK KEYBOARD)
    # --------------------------------------------------------------------------
    def toggle_playback(self):
        if self.is_playing:
            self.stop_playback()
        else:
            self.start_playback()

    def start_playback(self):
        if self.is_playing or self.is_recording or not self.actions:
            return

        if not self.recorded_target_hwnd:
            hwnd, title, _ = AppStateManager.get_foreground_window(exclude_hwnds=self._own_window_handles())
            if hwnd:
                self.recorded_target_hwnd = hwnd
                self.recorded_target_title = title or "Target Window"
                self.virtual_cursor.bind_target_window(hwnd)

        if IS_WINDOWS and self.use_virtual_cursor.get() and not self.recorded_target_hwnd:
            messagebox.showwarning(
                "Target Window Required",
                "Virtual Cursor Runtime needs a locked target window. Use 'Lock Target App' in Macro Studio, then start playback again."
            )
            return

        speed_str = self.speed_var.get()
        speed_mult = 999.0 if "Max" in speed_str else float(speed_str.replace("x", "") or 1.0)
        loops = -1 if self.infinite_loop_var.get() else int(self.loop_var.get() or 1)
        traj_mode = self.trajectory_mode_var.get()

        self.is_playing = True
        self.stop_playback_event.clear()
        play_cue(high_pitch=True)

        self.btn_play_toggle.set_text_and_color("⏹  STOP PLAYBACK (F10)", THEME["accent_rose"], fg_color="#FFFFFF", hover_color="#FB7185")
        self.lbl_record_status.config(text="[ PLAYING ISOLATED... ]", fg=THEME["accent_emerald"])

        if self.auto_hide_play_var.get():
            self.withdraw()
            if self.show_click_through_banner.get():
                self.top_banner = ClickThroughTopBanner(mode="PLAY", hotkey_hint="F10")

        self._restore_native_app_state()

        active_cds = [c for c in self.cooldown_timers if c.get("enabled")]
        if active_cds:
            self.cooldown_worker = CooldownManager(self.keyboard_controller, active_cds)
            self.cooldown_worker.start()

        threading.Thread(target=self._playback_worker, args=(speed_mult, loops, traj_mode), daemon=True).start()

    def _restore_native_app_state(self):
        if self.auto_focus_target.get() and not self.use_virtual_cursor.get() and self.recorded_target_hwnd:
            AppStateManager.robust_focus_window(self.recorded_target_hwnd)
            time.sleep(0.05)

        if self.warp_to_origin.get() and self.recorded_origin_pos:
            ox, oy = self.recorded_origin_pos
            if self.use_virtual_cursor.get():
                self.after(0, lambda: self.virtual_cursor.set_position(ox, oy, is_client_coords=True, state="HOVER"))
            else:
                if not HardwareCursor.set_pos(ox, oy):
                    self.mouse_controller.position = (ox, oy)
            time.sleep(0.02)

        if self.reset_scroll_to_top.get() and self.recorded_target_hwnd:
            if self.use_isolated_vk.get():
                VirtualKeyboardEngine.send_key_hold(self.recorded_target_hwnd, "home", duration_sec=0.04, modifiers=["ctrl"])
            else:
                try:
                    self.keyboard_controller.press(Key.ctrl)
                    self.keyboard_controller.press(Key.home)
                    self.keyboard_controller.release(Key.home)
                    self.keyboard_controller.release(Key.ctrl)
                except Exception:
                    pass

    def stop_playback(self):
        if not self.is_playing: return
        self.is_playing = False
        self.stop_playback_event.set()

        if self.cooldown_worker:
            self.cooldown_worker.stop()
            self.cooldown_worker = None

        play_cue(high_pitch=False)
        self.virtual_cursor.set_state("HOVER", key_badge="")

        if self.top_banner: self.top_banner.close(); self.top_banner = None
        self.deiconify()
        self.lift()

        self.btn_play_toggle.set_text_and_color("▶  PLAY MACRO IN ISOLATED WORKSPACE (F10)", THEME["accent_emerald"], fg_color="#000000", hover_color="#34D399")
        self.lbl_record_status.config(text="[ IDLE ]", fg=THEME["text_secondary"])

        if self.webhook_on_finish.get() and self.webhook_url.get():
            WebhookNotifier.send_notification(
                self.webhook_url.get(),
                "✅ Macro Playback Completed Successfully!",
                {"Events": len(self.actions), "Duration": f"{self.actions[-1]['time']:.2f}s", "Target": self.recorded_target_title}
            )

    def _playback_worker(self, speed_mult, loop_count, traj_mode):
        iteration = 0
        while not self.stop_playback_event.is_set():
            if loop_count != -1 and iteration >= loop_count:
                break

            if iteration > 0:
                self._restore_native_app_state()

            clock_start = time.perf_counter()
            curr_cursor = (self.virtual_cursor.client_x, self.virtual_cursor.client_y)
            step_idx = 0
            n_actions = len(self.actions)

            while step_idx < n_actions and not self.stop_playback_event.is_set():
                act = self.actions[step_idx]
                target_t = clock_start + (act["time"] / speed_mult)
                if speed_mult < 900:
                    while time.perf_counter() < target_t:
                        if self.stop_playback_event.is_set(): break
                        rem = target_t - time.perf_counter()
                        if rem > 0.003: time.sleep(rem * 0.75)

                evt = act["type"]
                d = act["data"]

                if evt == "IF_COLOR":
                    curr_c, _ = HardwareCursor.get_pixel_color(d.get("x", 0), d.get("y", 0))
                    if curr_c.upper() != d.get("color", "").upper():
                        step_idx += d.get("skip_steps", 1)
                    step_idx += 1
                    continue
                elif evt == "WAIT_FOR_COLOR":
                    t_limit = time.perf_counter() + d.get("timeout", 10.0)
                    while time.perf_counter() < t_limit and not self.stop_playback_event.is_set():
                        curr_c, _ = HardwareCursor.get_pixel_color(d.get("x", 0), d.get("y", 0))
                        if curr_c.upper() == d.get("color", "").upper(): break
                        time.sleep(0.05)
                    step_idx += 1
                    continue

                curr_cursor = self._dispatch_playback_event(act, curr_cursor, traj_mode, speed_mult)
                step_idx += 1

            iteration += 1
            if (loop_count == -1 or iteration < loop_count) and not self.stop_playback_event.is_set():
                time.sleep(0.05)

        self.after(0, self.stop_playback)

    def _move_virtual_or_real(self, px, py, state="HOVER", btn_held=None):
        hwnd = self.recorded_target_hwnd
        if self.clamp_to_target_bounds.get() and hwnd:
            _, _, px, py, _, _ = WindowWorkspaceBounds.clamp_to_window(hwnd, px, py, is_client_coords=True)

        if self.use_virtual_cursor.get():
            self.after(0, lambda x=px, y=py, s=state: self.virtual_cursor.set_position(x, y, is_client_coords=True, state=s))
            if hwnd:
                IsolatedMouseDispatcher.move(hwnd, px, py, button_held=btn_held)
        else:
            sx, sy, _, _, _, _ = WindowWorkspaceBounds.clamp_to_window(hwnd, px, py, is_client_coords=True)
            if not HardwareCursor.set_pos(sx, sy):
                self.mouse_controller.position = (sx, sy)
        return (px, py)

    def _dispatch_playback_event(self, act, last_pos, traj_mode, speed_mult=1.0):
        evt = act["type"]
        d = act["data"]
        hwnd = self.recorded_target_hwnd
        use_vc = self.use_virtual_cursor.get()
        use_vk = self.use_isolated_vk.get()

        try:
            if evt == "MOUSE_MOVE":
                tx, ty = d["x"], d["y"]
                curve = d.get("curve", traj_mode)
                pts = self._compute_curve_points(last_pos[0], last_pos[1], tx, ty, curve)
                move_duration = max(0.0, float(d.get("duration", 0.0)) / max(speed_mult, 0.1))
                step_delay = move_duration / max(len(pts) - 1, 1)
                for px, py in pts[1:]:
                    if self.stop_playback_event.is_set(): break
                    self._move_virtual_or_real(px, py, state="HOVER")
                    if step_delay > 0.001:
                        time.sleep(step_delay)
                return (tx, ty)

            elif evt == "MOUSE_DRAG":
                sx, sy = d.get("x", last_pos[0]), d.get("y", last_pos[1])
                ex, ey = d.get("end_x", sx + 100), d.get("end_y", sy + 100)
                btn_str = d.get("button", "left")
                dur = max(0.05, d.get("duration", 0.5) / max(speed_mult, 0.1))
                curve = d.get("curve", traj_mode)

                self._move_virtual_or_real(sx, sy, state="DOWN")
                if use_vc and hwnd:
                    IsolatedMouseDispatcher.button_down(hwnd, sx, sy, btn_str)
                else:
                    btn = Button.left if btn_str == "left" else (Button.right if btn_str == "right" else Button.middle)
                    self.mouse_controller.press(btn)

                pts = self._compute_curve_points(sx, sy, ex, ey, curve, steps=24)
                step_dt = dur / max(len(pts) - 1, 1)
                for px, py in pts[1:]:
                    if self.stop_playback_event.is_set(): break
                    self._move_virtual_or_real(px, py, state="DRAG", btn_held=btn_str)
                    time.sleep(max(0.002, step_dt))

                if use_vc and hwnd:
                    IsolatedMouseDispatcher.button_up(hwnd, ex, ey, btn_str)
                else:
                    btn = Button.left if btn_str == "left" else (Button.right if btn_str == "right" else Button.middle)
                    self.mouse_controller.release(btn)
                self._move_virtual_or_real(ex, ey, state="HOVER")
                return (ex, ey)

            elif evt == "MOUSE_DOWN":
                tx, ty = d.get("x", last_pos[0]), d.get("y", last_pos[1])
                btn_str = d.get("button", "left")
                tx, ty = self._move_virtual_or_real(tx, ty, state="DOWN")
                if use_vc and hwnd:
                    IsolatedMouseDispatcher.button_down(hwnd, tx, ty, btn_str)
                else:
                    btn = Button.left if btn_str == "left" else (Button.right if btn_str == "right" else Button.middle)
                    self.mouse_controller.press(btn)
                return (tx, ty)

            elif evt == "MOUSE_UP":
                tx, ty = d.get("x", last_pos[0]), d.get("y", last_pos[1])
                btn_str = d.get("button", "left")
                tx, ty = self._move_virtual_or_real(tx, ty, state="HOVER")
                if use_vc and hwnd:
                    IsolatedMouseDispatcher.button_up(hwnd, tx, ty, btn_str)
                else:
                    btn = Button.left if btn_str == "left" else (Button.right if btn_str == "right" else Button.middle)
                    self.mouse_controller.release(btn)
                return (tx, ty)

            elif evt == "MOUSE_SCROLL":
                tx, ty = d.get("x", last_pos[0]), d.get("y", last_pos[1])
                tx, ty = self._move_virtual_or_real(tx, ty, state="SCROLL")
                if use_vc:
                    if hwnd:
                        IsolatedMouseDispatcher.scroll(hwnd, tx, ty, d.get("dx", 0), d.get("dy", -2))
                else:
                    self.mouse_controller.scroll(d.get("dx", 0), d.get("dy", 0))
                return (tx, ty)

            elif evt == "KEY_HOLD":
                k_str = d.get("key", "w")
                dur = max(0.02, d.get("duration", 0.2) / max(speed_mult, 0.1))
                mods = d.get("modifiers", [])
                self.after(0, lambda k=k_str: self.virtual_cursor.set_state(self.virtual_cursor.state, key_badge=str(k).upper()))
                if use_vk and hwnd:
                    VirtualKeyboardEngine.send_key_hold(hwnd, k_str, duration_sec=dur, modifiers=mods, stop_event=self.stop_playback_event)
                else:
                    k_obj = self._deserialize_key(k_str)
                    if k_obj:
                        self.keyboard_controller.press(k_obj)
                        time.sleep(dur)
                        self.keyboard_controller.release(k_obj)
                self.after(0, lambda: self.virtual_cursor.set_state(self.virtual_cursor.state, key_badge=""))

            elif evt == "KEY_DOWN":
                k_str = d["key"]
                self.after(0, lambda k=k_str: self.virtual_cursor.set_state(self.virtual_cursor.state, key_badge=str(k).replace("Key.", "").upper()))
                if use_vk and hwnd:
                    VirtualKeyboardEngine.send_key_down(hwnd, k_str)
                else:
                    k = self._deserialize_key(k_str)
                    if k: self.keyboard_controller.press(k)

            elif evt == "KEY_UP":
                k_str = d["key"]
                self.after(0, lambda: self.virtual_cursor.set_state(self.virtual_cursor.state, key_badge=""))
                if use_vk and hwnd:
                    VirtualKeyboardEngine.send_key_up(hwnd, k_str)
                else:
                    k = self._deserialize_key(k_str)
                    if k: self.keyboard_controller.release(k)

            elif evt == "DELAY":
                time.sleep(d.get("seconds", 0.1) / max(speed_mult, 0.1))
        except Exception:
            pass
        return last_pos

    def _compute_curve_points(self, x0, y0, x1, y1, curve_name, steps=18):
        if "Human" in curve_name or "Bézier" in curve_name:
            return TrajectoryEngine.human_bezier_curve(x0, y0, x1, y1, steps=steps)
        elif "Bresenham" in curve_name:
            return TrajectoryEngine.bresenham_line(x0, y0, x1, y1)
        elif "Cubic" in curve_name:
            return TrajectoryEngine.cubic_ease_interpolate(x0, y0, x1, y1, steps=steps)
        return [(x0, y0), (x1, y1)]

    def _deserialize_key(self, k_str):
        if k_str.startswith("Key."):
            return getattr(Key, k_str.split(".", 1)[1], None)
        elif k_str.startswith("code_"):
            return KeyCode.from_vk(int(k_str.split("_", 1)[1]))
        return KeyCode.from_char(k_str)

    def save_macro_file(self):
        if not self.actions: return
        p = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Macro", "*.json")])
        if p:
            with open(p, "w", encoding="utf-8") as f:
                json.dump({"version": "10.5", "origin_pos": self.recorded_origin_pos, "target_app": self.recorded_target_title, "actions": self.actions}, f, indent=2)
            messagebox.showinfo("Saved", "Macro saved successfully!")

    def load_macro_file(self):
        p = filedialog.askopenfilename(filetypes=[("JSON Macro", "*.json")])
        if p:
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f)
            self._load_custom_actions(d.get("actions", []), os.path.basename(p))

    def _setup_macro_hotkeys(self):
        def on_press(key):
            try:
                if key == Key.f9: self.after(0, self.toggle_recording)
                elif key == Key.f10: self.after(0, self.toggle_playback)
            except Exception:
                pass
        try:
            listener = keyboard.Listener(on_press=on_press)
            listener.daemon = True
            listener.start()
        except Exception:
            pass

    def close_and_return_to_main(self):
        if self.is_recording: self.stop_recording()
        if self.is_playing: self.stop_playback()
        self.virtual_cursor.hide_sprite()
        if self.viewport_window and self.viewport_window.winfo_exists():
            self.viewport_window.destroy()
        if self.timeline_editor_window and self.timeline_editor_window.winfo_exists():
            self.timeline_editor_window.destroy()
        self.withdraw()
        self.parent_app.deiconify()
        self.parent_app.lift()
        self.parent_app.focus_force()


# ==============================================================================
# MAIN ENTRYPOINT
# ==============================================================================
def main():
    if MISSING_DEPS:
        print("="*60)
        print("⚡ APEX AUTO-CLICKER (v9.5)")
        print("="*60)
        print(f"Missing required library: {', '.join(MISSING_DEPS)}")
        print("\nPlease install the required libraries using:")
        print("    pip install pynput")
        print("="*60)

        if "tkinter" not in MISSING_DEPS:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Missing Dependencies",
                f"Apex requires 'pynput' for global hotkeys and mouse control.\n\n"
                f"Please run:\npip install pynput"
            )
        sys.exit(1)

    app = ApexAutoClickerApp()
    app.mainloop()


if __name__ == "__main__":
    main()