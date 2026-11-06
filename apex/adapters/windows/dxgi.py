"""
apex/adapters/windows/dxgi.py
DXGI Desktop Duplication & DirectX Game Compatibility Profile (Roblox, Unity, Unreal).
"""

class DXGIDirectXAdapter:
    @staticmethod
    def get_game_diagnostics(title="Roblox"):
        return {
            "engine": "DirectX / RawInput Game Engine",
            "target": title,
            "background_postmessage_supported": False,
            "recommended_input": "Foreground DirectInput / SendInput Hardware Synthesis",
            "anti_cheat_safe": True
        }
