from dataclasses import dataclass

from ui_systems import (
    BATTLE_DURATION_SECONDS, BattleTimeline, InputController, ScreenTransition, VirtualViewport,
    battle_health, default_battle_cues,
)


class Rect:
    def __init__(self, x, y, w, h): self.values = x, y, w, h
    def collidepoint(self, pos):
        x, y, w, h = self.values
        return x <= pos[0] < x + w and y <= pos[1] < y + h


@dataclass
class Button:
    control_id: str
    rect: Rect
    action: object
    enabled: bool = True


def test_one_complete_click_activates_exactly_once():
    calls = []
    button = Button("start", Rect(10, 10, 100, 40), lambda: calls.append("called"))
    controller = InputController()
    controller.pointer_down([button], (20, 20))
    activated = controller.pointer_up([button], (20, 20), 1000)
    assert activated is button
    activated.action()
    assert calls == ["called"]
    assert controller.pointer_up([button], (20, 20), 1010) is None


def test_release_outside_never_activates_and_hold_never_repeats():
    button = Button("start", Rect(10, 10, 100, 40), lambda: None)
    controller = InputController()
    controller.pointer_down([button], (20, 20))
    assert controller.pointer_up([button], (400, 400), 1000) is None
    assert controller.pointer_up([button], (20, 20), 1200) is None
    controller.pointer_down([button], (20, 20))
    controller.cancel_press()
    assert controller.pointer_up([button], (20, 20), 1400) is None


def test_rapid_duplicate_click_is_guarded():
    button = Button("continue", Rect(0, 0, 100, 100), lambda: None)
    controller = InputController(activation_guard_ms=160)
    controller.pointer_down([button], (5, 5)); assert controller.pointer_up([button], (5, 5), 1000)
    controller.pointer_down([button], (5, 5)); assert controller.pointer_up([button], (5, 5), 1070) is None
    next_screen = Button("next-screen:first-card", Rect(0, 0, 100, 100), lambda: None)
    controller.pointer_down([next_screen], (5, 5))
    assert controller.pointer_up([next_screen], (5, 5), 1071) is next_screen


def test_virtual_coordinate_conversion_and_letterbox():
    view = VirtualViewport(1920, 1080)
    assert view.to_virtual(view.offset) == (0, 0)
    center = (view.offset[0] + view.size[0] // 2, view.offset[1] + view.size[1] // 2)
    converted = view.to_virtual(center)
    assert abs(converted[0] - 600) <= 1 and abs(converted[1] - 410) <= 1
    assert view.to_virtual((0, 0)) is None
    assert VirtualViewport(800, 600).scale < 1
    for size in ((800, 600), (1280, 720), (1920, 1080)):
        viewport = VirtualViewport(*size)
        point = (745, 511)
        converted = viewport.to_virtual(viewport.to_window(point))
        assert abs(converted[0] - point[0]) <= 1 and abs(converted[1] - point[1]) <= 1


def test_transition_completes_and_reduced_motion_is_shorter():
    transition = ScreenTransition(duration_ms=300)
    transition.start(1000)
    assert transition.active(1100)
    assert not transition.active(1300)
    assert not transition.active(1090, reduced_motion=True)


def test_battle_duration_and_events_are_frame_rate_independent():
    timeline = BattleTimeline(default_battle_cues("A", "B", "A"))
    assert timeline.duration_seconds == BATTLE_DURATION_SECONDS == 8.0
    for fps in (24, 30, 60, 144):
        elapsed = 0.0; seen = []
        while not timeline.complete(elapsed):
            previous = elapsed; elapsed += 1 / fps
            seen.extend(timeline.crossed(previous, elapsed))
        assert elapsed < 8.0 + 1 / fps + 1e-6
        assert len(seen) == len(timeline.cues)


def test_winner_is_hidden_until_finale_and_correct_at_end():
    assert min(battle_health(.75, "A")) >= 42
    assert battle_health(1.0, "A")[1] == 0
    assert battle_health(1.0, "B")[0] == 0
    assert battle_health(1.0, "tie") == (8, 8)
