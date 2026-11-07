"""
apex/tests/test_architecture.py
Automated Test Suite verifying Phase 0 through Phase 6 of the Apex Automation Engine Architecture.
"""
import unittest
from pathlib import Path
from apex.core.coordinate_spaces import CoordinateSpace, CoordinateConverter
from apex.core.geometry import Vertex2D, Vector2D
from apex.core.event_model import InteractionEvent
from apex.core.application_state import ApplicationStateProfile
from apex.core.capability_registry import CapabilityRegistry
from apex.core.runtime_coordinator import RuntimeCoordinator
from apex.adapters.browsers.adaptive_scroll import AdaptiveScrollEngine


class TestApexArchitecture(unittest.TestCase):
    def test_vertex_vector_resolution_across_resize(self):
        # Record in Notepad at 1280x720: Start U=0.20, V=0.35 -> End U=0.68, V=0.35
        v0 = Vertex2D.from_client(256, 252, 1280, 720)
        v1 = Vertex2D.from_client(870, 252, 1280, 720)
        vec = Vector2D.between(v0, v1)
        self.assertAlmostEqual(v0.u, 0.20, places=2)
        self.assertAlmostEqual(v0.v, 0.35, places=2)
        self.assertAlmostEqual(vec.du, 0.48, places=2)

        # Replay when Notepad is resized to 1920x1080
        rx0, ry0 = v0.resolve_to_client(1920, 1080)
        rx1, ry1 = v1.resolve_to_client(1920, 1080)
        self.assertEqual((rx0, ry0), (384, 378))
        self.assertEqual((rx1, ry1), (1305, 378))

    def test_adaptive_scroll_engine(self):
        # 75% scroll on 8,000px page (viewport 800px -> scrollable 7,200px, scrollTop 5,400px)
        ratio = AdaptiveScrollEngine.calculate_scroll_ratio(5400, 8000, 800)
        self.assertAlmostEqual(ratio, 0.75, places=3)
        # Replay on 14,000px page (viewport 1,000px -> scrollable 13,000px)
        new_scroll_top = AdaptiveScrollEngine.resolve_target_scroll_top(ratio, 14000, 1000)
        self.assertEqual(new_scroll_top, 9750)

    def test_aacl_profiles_and_sensitive_redaction(self):
        prof_np = CapabilityRegistry.inspect(None, "Untitled - Notepad", "Notepad")
        self.assertEqual(prof_np.profile_id, "notepad")
        self.assertTrue(prof_np.capabilities["background_input"])
        self.assertTrue(prof_np.capabilities["window_message_input"])
        self.assertIn("queued-unverified", prof_np.capabilities["input_verification"])

        prof_rb = CapabilityRegistry.inspect(None, "Roblox", "WINDOWSCLIENT")
        self.assertEqual(prof_rb.adapter_type, "FOREGROUND_GAME_INPUT")
        self.assertFalse(prof_rb.capabilities["window_message_input"])
        self.assertTrue(prof_rb.capabilities["requires_foreground"])

        self.assertTrue(ApplicationStateProfile.is_sensitive_context("My Bank Password Login"))
        self.assertFalse(ApplicationStateProfile.is_sensitive_context("Untitled - Notepad"))


    def test_target_window_coordinate_and_message_packing(self):
        from apex.adapters.windows.target_session import TargetWindowSession

        self.assertEqual(TargetWindowSession.clamp_client_point(-4, 999, 800, 600), (0, 599))
        self.assertEqual(TargetWindowSession.resolve_normalized_point(0.5, 1.0, 800, 600), (400, 599))
        self.assertEqual(TargetWindowSession.pack_client_lparam(0x1234, 0x5678), 0x56781234)
        self.assertEqual(TargetWindowSession.pack_screen_lparam(-1, -2), 0xFFFEFFFF)
        self.assertEqual(TargetWindowSession.pack_wheel_wparam(-120), 0xFF880000)

    def test_target_input_router_selects_application_appropriate_route(self):
        from apex.core.input_router import InputRouter

        router = InputRouter()
        normal_route, normal_profile = router.select_route(None, "Untitled - Notepad", "Notepad")
        game_route, game_profile = router.select_route(None, "Roblox", "WINDOWSCLIENT")
        browser_route, browser_profile = router.select_route(None, "Firefox", "MozillaWindowClass")

        self.assertEqual(normal_route, InputRouter.ROUTE_WINDOW_MESSAGES)
        self.assertEqual(game_route, InputRouter.ROUTE_FOREGROUND_SENDINPUT)
        self.assertEqual(browser_route, InputRouter.ROUTE_FOREGROUND_SENDINPUT)
        self.assertIn("queued", normal_profile.capabilities["input_verification"])
        self.assertTrue(game_profile.capabilities["requires_foreground"])
        self.assertTrue(browser_profile.capabilities["requires_foreground"])

    def test_runtime_coordinator_event_schema(self):
        rc = RuntimeCoordinator()
        evt = rc.build_event(
            timestamp=1.25, category="MOUSE", action_type="DRAG",
            hwnd=12345, title="Untitled - Notepad", class_name="Notepad",
            client_size=(1280, 720), start_cx=256, start_cy=252, end_cx=870, end_cy=252,
            duration_ms=420
        )
        self.assertEqual(evt["coordinate_space"], CoordinateSpace.WINDOW_NORMALIZED)
        self.assertEqual(evt["target"]["profile"], "notepad")
        self.assertEqual(evt["duration_ms"], 420)


    def test_legacy_entrypoints_match_the_canonical_studio_source(self):
        root = Path(__file__).resolve().parents[2]
        canonical = (root / "apex" / "ui" / "studio_app.py").read_bytes()
        self.assertEqual((root / "apex_autoclicker.py").read_bytes(), canonical)
        self.assertEqual((root / "apex_autoclicker_fixed.py").read_bytes(), canonical)


if __name__ == "__main__":
    unittest.main()
