"""Reusable input, viewport, tween, transition, and timeline primitives.

The types in this module intentionally avoid importing Pygame so they can be
tested without opening a display and reused by a future touch client.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, Protocol


VIRTUAL_SIZE = (1200, 820)
BATTLE_DURATION_SECONDS = 8.0


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def ease_out_cubic(value: float) -> float:
    p = 1.0 - clamp01(value)
    return 1.0 - p * p * p


def ease_in_out(value: float) -> float:
    value = clamp01(value)
    return 4 * value**3 if value < .5 else 1 - ((-2 * value + 2) ** 3) / 2


@dataclass(frozen=True)
class VirtualViewport:
    window_width: int
    window_height: int
    virtual_width: int = VIRTUAL_SIZE[0]
    virtual_height: int = VIRTUAL_SIZE[1]

    @property
    def scale(self) -> float:
        return min(self.window_width / self.virtual_width, self.window_height / self.virtual_height)

    @property
    def size(self) -> tuple[int, int]:
        return (round(self.virtual_width * self.scale), round(self.virtual_height * self.scale))

    @property
    def offset(self) -> tuple[int, int]:
        width, height = self.size
        return ((self.window_width - width) // 2, (self.window_height - height) // 2)

    def to_virtual(self, position: tuple[int, int]) -> tuple[int, int] | None:
        ox, oy = self.offset
        width, height = self.size
        x, y = position
        if x < ox or y < oy or x >= ox + width or y >= oy + height:
            return None
        return (int((x - ox) / self.scale), int((y - oy) / self.scale))

    def to_window(self, position: tuple[int, int]) -> tuple[int, int]:
        ox, oy = self.offset
        return (round(ox + position[0] * self.scale), round(oy + position[1] * self.scale))


class ButtonLike(Protocol):
    control_id: str
    enabled: bool
    rect: object
    action: Callable[[], None]


@dataclass
class InputController:
    """Own a complete pointer press/release and keyboard activation cycle."""
    activation_guard_ms: int = 160
    pressed_id: str | None = None
    hovered_id: str | None = None
    focused_id: str | None = None
    last_activation_ms: int = -10_000
    last_activation_id: str | None = None

    @staticmethod
    def _at(buttons: Iterable[ButtonLike], position: tuple[int, int] | None):
        if position is None:
            return None
        return next((button for button in buttons if button.enabled and button.rect.collidepoint(position)), None)

    def update_hover(self, buttons: Iterable[ButtonLike], position: tuple[int, int] | None) -> None:
        button = self._at(buttons, position)
        self.hovered_id = button.control_id if button else None

    def pointer_down(self, buttons: Iterable[ButtonLike], position: tuple[int, int] | None) -> None:
        button = self._at(buttons, position)
        self.pressed_id = button.control_id if button else None
        if button:
            self.focused_id = button.control_id

    def pointer_up(self, buttons: Iterable[ButtonLike], position: tuple[int, int] | None, now_ms: int):
        button = self._at(buttons, position)
        pressed_id, self.pressed_id = self.pressed_id, None
        if not button or button.control_id != pressed_id:
            return None
        return self._accept(button, now_ms)

    def cancel_press(self) -> None:
        self.pressed_id = None

    def _accept(self, button: ButtonLike, now_ms: int):
        if button.control_id == self.last_activation_id and now_ms - self.last_activation_ms < self.activation_guard_ms:
            return None
        self.last_activation_ms = now_ms
        self.last_activation_id = button.control_id
        self.focused_id = button.control_id
        return button

    def move_focus(self, buttons: list[ButtonLike], direction: int) -> None:
        enabled = [button for button in buttons if button.enabled]
        if not enabled:
            self.focused_id = None
            return
        ids = [button.control_id for button in enabled]
        current = ids.index(self.focused_id) if self.focused_id in ids else (-1 if direction > 0 else 0)
        self.focused_id = ids[(current + direction) % len(ids)]

    def activate_focused(self, buttons: list[ButtonLike], now_ms: int):
        button = next((button for button in buttons if button.enabled and button.control_id == self.focused_id), None)
        return self._accept(button, now_ms) if button else None


@dataclass
class ScreenTransition:
    duration_ms: int = 280
    started_ms: int = -10_000

    def start(self, now_ms: int) -> None:
        self.started_ms = now_ms

    def progress(self, now_ms: int, reduced_motion=False) -> float:
        duration = min(self.duration_ms, 90) if reduced_motion else self.duration_ms
        return clamp01((now_ms - self.started_ms) / max(1, duration))

    def active(self, now_ms: int, reduced_motion=False) -> bool:
        return self.progress(now_ms, reduced_motion) < 1.0


@dataclass(frozen=True)
class BattleCue:
    at: float
    kind: str
    actor: str = ""
    target: str = ""
    text: str = ""
    player_fraction: float = 0.0
    opponent_fraction: float = 0.0


def default_battle_cues(player_ability: str, opponent_ability: str, winner: str) -> tuple[BattleCue, ...]:
    finisher = "player" if winner == "A" else "opponent" if winner == "B" else "both"
    return (
        BattleCue(.35, "entrance", text="Fighters enter the arena"),
        BattleCue(1.05, "anticipate", text="Both colonies size each other up"),
        BattleCue(1.55, "attack", "player", "opponent", "Opening strike", .18, .05),
        BattleCue(2.25, "defend", "opponent", "player", "Biofilm guard", .24, .13),
        BattleCue(2.90, "counter", "opponent", "player", "Counterattack", .30, .30),
        BattleCue(3.65, "dodge", "player", "opponent", "Quick dodge", .37, .39),
        BattleCue(4.25, "ability", "player", "opponent", player_ability, .58, .47),
        BattleCue(5.05, "environment", "opponent", "player", "Arena pressure", .63, .61),
        BattleCue(5.65, "ability", "opponent", "player", opponent_ability, .70, .75),
        BattleCue(6.35, "pause", "", "", "The arena goes quiet…", .76, .80),
        BattleCue(6.85, "finish", finisher, "", "Finishing action", .91, .91),
        BattleCue(7.55, "resolution", finisher, "", "Battle resolved", 1.0, 1.0),
    )


@dataclass
class BattleTimeline:
    cues: tuple[BattleCue, ...]
    duration_seconds: float = BATTLE_DURATION_SECONDS

    def progress(self, elapsed_seconds: float) -> float:
        return clamp01(elapsed_seconds / self.duration_seconds)

    def complete(self, elapsed_seconds: float) -> bool:
        return elapsed_seconds >= self.duration_seconds

    def crossed(self, previous_seconds: float, elapsed_seconds: float) -> tuple[BattleCue, ...]:
        return tuple(cue for cue in self.cues if previous_seconds < cue.at <= elapsed_seconds)

    def active_cue(self, elapsed_seconds: float) -> BattleCue:
        active = self.cues[0]
        for cue in self.cues:
            if cue.at > elapsed_seconds:
                break
            active = cue
        return active


def battle_health(progress: float, winner: str) -> tuple[int, int]:
    """Readable presentation health; never reveals the winner before the finale."""
    progress = clamp01(progress)
    if progress < .82:
        # Both fighters trade momentum and remain visibly competitive.
        player = 100 - 55 * progress + 6 * max(0, progress - .48)
        opponent = 100 - 52 * progress - 5 * max(0, progress - .35)
        return round(max(42, player)), round(max(42, opponent))
    finale = ease_in_out((progress - .82) / .18)
    if winner == "A":
        return round(50 - 15 * finale), round(45 * (1 - finale))
    if winner == "B":
        return round(45 * (1 - finale)), round(50 - 15 * finale)
    return round(45 - 37 * finale), round(45 - 37 * finale)
