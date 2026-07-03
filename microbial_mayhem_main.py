#!/usr/bin/env python3
"""Graphical entry point for Microbial Mayhem."""
from __future__ import annotations

import math
import os
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "hide")
# SDL otherwise consumes the click that gives an inactive desktop window focus.
os.environ.setdefault("SDL_MOUSE_FOCUS_CLICKTHROUGH", "1")

import pygame

from bacterial_names import BacterialName, format_bacterial_name, sanitize_designation
from bacterial_catalog import BacteriumCatalogEntry, bgc_summary, choose_opponent, get_catalog, sample_catalog, search_catalog
from app_settings import AppSettings
from audio_manager import AudioManager
from colony_scoring import colony_growth_score, generate_opponent_cfu
from environment_icons import ENVIRONMENT_LABELS
from flavor_text import FlavorDeck, environment_result_flavor, environment_status_label, friendly_value, is_missing, result_message
from gui_helpers import pluralize, wrap_text
from presentation import THEME, environment_visual, fighter_visual, summary_ability, summary_arsenal_status
from preview_models import (
    COLONY_PRESETS, animation_time, colony_particles, environment_effect_text, environment_flavor,
    environment_particles, quadratic_path,
)
from scoring import ScoreBreakdown, score_battle
from ui_systems import (
    BATTLE_DURATION_SECONDS, BattleTimeline, InputController, ScreenTransition,
    VirtualViewport, battle_health as timeline_health, default_battle_cues, ease_out_cubic,
)

SCRIPT_DIR = Path(__file__).resolve().parent
WIDTH, HEIGHT = 1200, 820
FPS = 60

WELCOME = "WELCOME"
FIGHTER_SELECTION = "FIGHTER_SELECTION"
COLONY_SELECTION = "COLONY_SELECTION"
SECRETION_SELECTION = "SECRETION_SELECTION"
ENVIRONMENT_SELECTION = "ENVIRONMENT_SELECTION"
SUPERPOWER_SELECTION = "SUPERPOWER_SELECTION"
BATTLE_PREVIEW = "BATTLE_PREVIEW"
BATTLE_ANIMATION = "BATTLE_ANIMATION"
RESULTS = "RESULTS"
SETTINGS = "SETTINGS"

ONE_PLAYER = "1_player"
TWO_PLAYERS = "2_players"

ENVIRONMENTS = ["Neutral", "Salty", "Alkaline", "Hot", "Cold", "Acidic", "In the presence of antibiotics"]


@dataclass
class Button:
    rect: pygame.Rect
    text: str
    action: Callable[[], None]
    selected: bool = False
    enabled: bool = True
    small: bool = False
    bacterial_name: BacterialName | None = None
    secondary_text: str = ""
    fighter: BacteriumCatalogEntry | None = None
    control_id: str = ""
    tooltip: str = ""
    style: str = "button"


@dataclass
class FloatingText:
    text: str
    pos: pygame.Vector2
    color: tuple[int, int, int]
    born: int
    ttl: int = 1200


@dataclass
class GameState:
    screen: str = WELCOME
    game_mode: str | None = None
    player1_fighter: BacteriumCatalogEntry | None = None
    player2_fighter: BacteriumCatalogEntry | None = None
    active_player: int = 1
    player1_confirmed: bool = False
    player2_confirmed: bool = False
    setup_player: int = 1
    player1_colony_cfu: int = 100
    player1_colony_score: float = 5.0
    player1_colony_label: str = "Decent-sized colony"
    player1_colony_confirmed: bool = False
    player2_colony_cfu: int = 100
    player2_colony_score: float = 5.0
    player2_colony_label: str = "Decent-sized colony"
    player2_colony_confirmed: bool = False
    player1_arsenal_active: bool | None = None
    player2_arsenal_active: bool | None = None
    player_entry: BacteriumCatalogEntry | None = None
    colony_cfu: int = 100
    colony_score: int = 5
    colony_label: str = "Decent-sized colony"
    has_secretion: bool | None = None
    opponent_entry: BacteriumCatalogEntry | None = None
    opponent_colony_cfu: int = 0
    opponent_colony_score: float = 0.0
    opponent_has_secretion: bool = False
    popup_message: str = ""
    popup_until: int = 0
    environment: str | None = None
    player_score: float = 0.0
    opponent_score: float = 0.0
    winner_flag: str = "tie"
    winner_name: str = ""
    result_text: str = ""
    battle_seed: int = 0
    player_breakdown: ScoreBreakdown | None = None
    opponent_breakdown: ScoreBreakdown | None = None
    catalog_choices: list[BacteriumCatalogEntry] = field(default_factory=list)
    selected_catalog_entry: BacteriumCatalogEntry | None = None
    search_query: str = ""
    search_message: str = ""
    scroll_offset: int = 0
    show_all_bgcs: bool = False
    bgc_scroll: int = 0
    animation_started: int = 0
    animation_events: list[dict] = field(default_factory=list)
    next_event_index: int = 0
    displayed_player_score: float = 0.0
    displayed_opponent_score: float = 0.0
    floating_texts: list[FloatingText] = field(default_factory=list)
    transition_started: int = 0
    battle_log: list[str] = field(default_factory=list)
    selected_at: int = 0
    results_started: int = 0
    battle_elapsed_seconds: float = 0.0
    battle_previous_seconds: float = 0.0
    colony_selected_at: int = 0
    environment_selected_at: int = 0


def calculate_battle(state: GameState) -> None:
    player_breakdown, opponent_breakdown = score_battle(
        state.player_entry,
        state.opponent_entry,
        state.environment,
        state.colony_cfu,
        state.opponent_colony_cfu,
        bool(state.has_secretion),
        state.opponent_has_secretion,
        seed=state.battle_seed,
    )
    state.player_breakdown = player_breakdown
    state.opponent_breakdown = opponent_breakdown
    state.player_score = player_breakdown.total
    state.opponent_score = opponent_breakdown.total
    if state.player_score > state.opponent_score:
        state.winner_flag, state.winner_name, winner = "A", state.player_entry.full_name, state.player_entry
    elif state.player_score < state.opponent_score:
        state.winner_flag, state.winner_name, winner = "B", state.opponent_entry.full_name, state.opponent_entry
    else:
        state.winner_flag, state.winner_name, winner = "tie", f"{state.player_entry.full_name} and {state.opponent_entry.full_name}", None
    if winner:
        state.result_text = winner.description
    else:
        state.result_text = "That was a good fight! The microbes were tied. Both descriptions are shown below."


def reset_for_new_game(state: GameState) -> None:
    state.screen = WELCOME
    state.game_mode = None
    state.player1_fighter = None
    state.player2_fighter = None
    state.active_player = 1
    state.player1_confirmed = False
    state.player2_confirmed = False
    state.setup_player = 1
    state.player1_colony_cfu = 100
    state.player1_colony_score, state.player1_colony_label = colony_growth_score(100)
    state.player1_colony_confirmed = False
    state.player2_colony_cfu = 100
    state.player2_colony_score, state.player2_colony_label = colony_growth_score(100)
    state.player2_colony_confirmed = False
    state.player1_arsenal_active = None
    state.player2_arsenal_active = None
    state.player_entry = None
    state.colony_cfu = 100
    state.colony_score, state.colony_label = colony_growth_score(100)
    state.has_secretion = None
    state.opponent_entry = None
    state.opponent_colony_cfu = 0
    state.opponent_colony_score = 0.0
    state.opponent_has_secretion = False
    state.popup_message = ""
    state.popup_until = 0
    state.environment = None
    state.player_score = state.opponent_score = 0.0
    state.player_breakdown = state.opponent_breakdown = None
    state.winner_flag = "tie"
    state.winner_name = ""
    state.battle_seed = 0
    state.result_text = ""
    state.selected_catalog_entry = None
    state.search_query = ""
    state.search_message = ""
    state.scroll_offset = 0
    state.show_all_bgcs = False
    state.bgc_scroll = 0
    state.animation_events.clear()
    state.floating_texts.clear()
    state.battle_log.clear()
    state.next_event_index = 0
    state.displayed_player_score = 0.0
    state.displayed_opponent_score = 0.0
    state.battle_elapsed_seconds = 0.0
    state.battle_previous_seconds = 0.0


class MicrobialMayhemGUI:
    def __init__(self) -> None:
        pygame.init()
        self.display = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        self.screen = pygame.Surface((WIDTH, HEIGHT)).convert()
        self.viewport = VirtualViewport(WIDTH, HEIGHT)
        pygame.display.set_caption("Microbial Mayhem")
        self.clock = pygame.time.Clock()
        self.settings = AppSettings.load()
        self.input = InputController()
        self.transition = ScreenTransition()
        self.battle_timeline: BattleTimeline | None = None
        self.flavor = FlavorDeck(f"session-{random.randrange(1_000_000_000)}")
        self.input_debug = os.environ.get("MICROBIAL_MAYHEM_INPUT_DEBUG") == "1"
        self.last_window_mouse = (0, 0)
        font_candidates = (
            Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        )
        font_path = next((str(path) for path in font_candidates if path.exists()), None)

        self.font_path = font_path
        self.configure_fonts()
        self.audio = AudioManager(SCRIPT_DIR / "assets" / "audio", self.settings)
        self.state = GameState()
        self.catalog_error = ""
        try:
            self.catalog = list(get_catalog())
        except FileNotFoundError as exc:
            self.catalog = []
            self.catalog_error = str(exc)
        sources = sorted({entry.source for entry in self.catalog if entry.source})
        self.catalog_source = "/".join(sources) if sources else "database"
        self.buttons: list[Button] = []
        self.slider_rect = pygame.Rect(330, 340, 540, 12)
        self.dragging_slider = False
        self.background = self.load_background()
        if self.catalog:
            self.refresh_catalog_choices()
        self.audio.set_phase("setup", pygame.time.get_ticks())

    def configure_fonts(self) -> None:
        def make_font(size: int, *, bold=False, italic=False):
            size = max(11, round(size * self.settings.text_scale))
            result = pygame.font.Font(self.font_path, size)
            result.set_bold(bold)
            result.set_italic(italic)
            return result

        self.font = make_font(25)
        self.big = make_font(64, bold=True)
        self.mid = make_font(36, bold=True)
        self.small = make_font(18)
        self.tiny = make_font(14, bold=True)
        self.font_italic = make_font(25, italic=True)
        self.small_italic = make_font(18, italic=True)

    def load_background(self) -> pygame.Surface | None:
        for name in ("lightning.jpeg", "Mayhem.png", "May.png"):
            path = SCRIPT_DIR / name
            if path.exists():
                try:
                    image = pygame.image.load(str(path)).convert()
                    scale = max(WIDTH / image.get_width(), HEIGHT / image.get_height())
                    scaled = pygame.transform.smoothscale(image, (int(image.get_width() * scale), int(image.get_height() * scale)))
                    return scaled.subsurface(pygame.Rect((scaled.get_width() - WIDTH) // 2, (scaled.get_height() - HEIGHT) // 2, WIDTH, HEIGHT)).copy()
                except pygame.error:
                    continue
        return None

    def run(self) -> None:
        running = True
        try:
            self.draw((-10_000, -10_000), 0)
            self.present()
            while running:
                dt = self.clock.tick(FPS)
                now = pygame.time.get_ticks()
                self.audio.update(now)
                self.last_window_mouse = pygame.mouse.get_pos()
                mouse = self.viewport.to_virtual(self.last_window_mouse) or (-10_000, -10_000)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.VIDEORESIZE:
                        self.display = pygame.display.set_mode((max(480, event.w), max(320, event.h)), pygame.RESIZABLE)
                        self.viewport = VirtualViewport(*self.display.get_size())
                    else:
                        self.handle_event(event)
                self.draw(mouse, dt)
                self.present()
        finally:
            self.audio.shutdown()
            pygame.quit()

    def present(self) -> None:
        self.display.fill((2, 7, 14))
        scaled = pygame.transform.smoothscale(self.screen, self.viewport.size)
        self.display.blit(scaled, self.viewport.offset)
        pygame.display.flip()

    def event_position(self, event: pygame.event.Event) -> tuple[int, int] | None:
        if hasattr(event, "pos"):
            return self.viewport.to_virtual(event.pos)
        if event.type in {pygame.FINGERDOWN, pygame.FINGERUP, pygame.FINGERMOTION}:
            window = self.display.get_size()
            return self.viewport.to_virtual((round(event.x * window[0]), round(event.y * window[1])))
        return None

    def handle_event(self, event: pygame.event.Event) -> None:
        now = pygame.time.get_ticks()
        if event.type == pygame.WINDOWFOCUSLOST:
            self.input.cancel_press()
            self.dragging_slider = False
            return
        if event.type == pygame.JOYHATMOTION and event.value != (0, 0):
            self.input.move_focus(self.buttons, 1 if event.value[0] > 0 or event.value[1] < 0 else -1); return
        if event.type == pygame.JOYBUTTONDOWN and event.button == 0:
            button = self.input.activate_focused(self.buttons, now)
            if button: self.activate_button(button)
            return
        if event.type == pygame.JOYBUTTONDOWN and event.button in {1, 6}:
            self.navigate_back(); return
        if event.type == pygame.KEYDOWN and event.key in {pygame.K_TAB, pygame.K_DOWN, pygame.K_RIGHT}:
            self.input.move_focus(self.buttons, 1); return
        if event.type == pygame.KEYDOWN and event.key in {pygame.K_UP, pygame.K_LEFT}:
            self.input.move_focus(self.buttons, -1); return
        if event.type == pygame.KEYDOWN and event.key in {pygame.K_RETURN, pygame.K_SPACE}:
            button = self.input.activate_focused(self.buttons, now)
            if button:
                self.activate_button(button)
            elif self.state.screen == FIGHTER_SELECTION and event.key == pygame.K_RETURN:
                self.apply_search()
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.navigate_back(); return
        if self.state.screen == FIGHTER_SELECTION and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.state.search_query = self.state.search_query[:-1]
            elif event.unicode and event.unicode.isprintable():
                self.state.search_query += event.unicode
            return
        if self.state.screen == FIGHTER_SELECTION and event.type == pygame.MOUSEWHEEL:
            if self.state.show_all_bgcs and self.state.selected_catalog_entry:
                maximum = max(0, len(self.state.selected_catalog_entry.accessions) - 12)
                self.state.bgc_scroll = max(0, min(maximum, self.state.bgc_scroll - event.y))
                return
            max_offset = max(0, len(self.state.catalog_choices) - 10)
            self.state.scroll_offset = max(0, min(max_offset, self.state.scroll_offset - event.y))
            return
        pointer_down = event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 or event.type == pygame.FINGERDOWN
        pointer_up = event.type == pygame.MOUSEBUTTONUP and event.button == 1 or event.type == pygame.FINGERUP
        pointer_move = event.type == pygame.MOUSEMOTION or event.type == pygame.FINGERMOTION
        position = self.event_position(event)
        if pointer_down:
            if self.state.screen == COLONY_SELECTION and position and self.slider_hit(position):
                self.dragging_slider = True
                self.update_slider(position[0])
                return
            self.input.pointer_down(self.buttons, position)
            return
        if pointer_up:
            if self.dragging_slider:
                self.dragging_slider = False
                self.input.cancel_press()
                return
            button = self.input.pointer_up(self.buttons, position, now)
            if button:
                self.activate_button(button)
            return
        if pointer_move:
            self.input.update_hover(self.buttons, position)
        if pointer_move and self.dragging_slider and position:
            self.update_slider(position[0])

    def activate_button(self, button: Button) -> None:
        self.audio.play("click")
        button.action()

    def navigate_back(self) -> None:
        if self.state.screen == FIGHTER_SELECTION:
            if self.state.game_mode == TWO_PLAYERS and self.state.active_player == 2:
                self.return_to_player1_selection()
            else:
                self.return_to_opening(preserve_mode=True)
            return
        if self.state.screen == COLONY_SELECTION and self.state.game_mode == TWO_PLAYERS:
            if self.state.setup_player == 2:
                self.load_setup_player(1)
                self.set_screen(SECRETION_SELECTION)
            else:
                self.state.active_player = 2
                self.state.player2_confirmed = False
                self.state.selected_catalog_entry = self.state.player2_fighter
                self.set_screen(FIGHTER_SELECTION)
            return
        if self.state.screen == SECRETION_SELECTION and self.state.game_mode == TWO_PLAYERS:
            self.load_setup_player(self.state.setup_player)
            self.set_screen(COLONY_SELECTION)
            return
        if self.state.screen == ENVIRONMENT_SELECTION and self.state.game_mode == TWO_PLAYERS:
            self.load_setup_player(2)
            self.set_screen(SECRETION_SELECTION)
            return
        if self.state.screen == RESULTS:
            self.main_menu()
            return
        previous = {
            SETTINGS: WELCOME,
            COLONY_SELECTION: FIGHTER_SELECTION,
            SECRETION_SELECTION: COLONY_SELECTION,
            ENVIRONMENT_SELECTION: SECRETION_SELECTION,
            BATTLE_PREVIEW: ENVIRONMENT_SELECTION,
        }.get(self.state.screen)
        if previous:
            self.set_screen(previous)
        elif self.state.screen == WELCOME:
            self.quit()

    def refresh_catalog_choices(self) -> None:
        self.state.catalog_choices = sample_catalog(10, catalog=self.catalog)
        if self.state.game_mode == TWO_PLAYERS and self.state.active_player == 2 and self.state.player1_fighter:
            if all(entry.catalog_id != self.state.player1_fighter.catalog_id for entry in self.state.catalog_choices):
                self.state.catalog_choices[0] = self.state.player1_fighter
        self.state.selected_catalog_entry = None
        self.state.scroll_offset = 0
        self.state.show_all_bgcs = False
        self.state.bgc_scroll = 0
        self.state.search_message = f"Showing {len(self.state.catalog_choices)} random database-derived bacteria."

    def apply_search(self) -> None:
        results = search_catalog(self.state.search_query, self.catalog)
        self.state.catalog_choices = results
        self.state.selected_catalog_entry = None
        self.state.scroll_offset = 0
        self.state.show_all_bgcs = False
        self.state.bgc_scroll = 0
        if results:
            self.state.search_message = f"Found {len(results)} match(es) for '{self.state.search_query}'."
        else:
            self.state.search_message = f"The database went quiet on '{self.state.search_query}'. Try another genus, species, or strain."

    def confirm_fighter(self) -> bool:
        entry = self.state.selected_catalog_entry
        if not entry or self.state.game_mode not in {ONE_PLAYER, TWO_PLAYERS}:
            return False
        if self.state.active_player == 2 and not self.can_select_fighter(entry):
            self.show_popup("Player 1 already claimed this microbe. Choose a different rival.")
            return False
        if self.state.active_player == 1:
            self.state.player1_fighter = entry
            self.state.player_entry = entry
            self.state.player1_confirmed = True
            self.state.player2_fighter = None
            self.state.player2_confirmed = False
            self.state.opponent_entry = None
            if self.state.game_mode == TWO_PLAYERS:
                self.state.active_player = 2
                self.state.selected_catalog_entry = None
                self.state.search_query = ""
                self.state.search_message = "Player 1 locked in. Player 2, choose a different rival."
                self.show_popup("PLAYER 1 LOCKED IN · Player 2, choose your rival!", 1100)
                self.set_screen(FIGHTER_SELECTION)
                return True
            self.state.player2_fighter = choose_opponent(entry.catalog_id, catalog=self.catalog)
            self.state.opponent_entry = self.state.player2_fighter
            self.state.player2_confirmed = True
            self.state.opponent_has_secretion = random.choice([True, False])
            self.state.player2_arsenal_active = self.state.opponent_has_secretion
            self.load_setup_player(1)
            self.set_screen(COLONY_SELECTION)
            return True
        self.state.player2_fighter = entry
        self.state.opponent_entry = entry
        self.state.player2_confirmed = True
        self.state.player2_colony_cfu = 100
        self.state.player2_colony_score, self.state.player2_colony_label = colony_growth_score(100)
        self.state.player2_colony_confirmed = False
        self.state.player2_arsenal_active = None
        self.state.opponent_has_secretion = False
        self.load_setup_player(1)
        self.show_popup("PLAYER 2 LOCKED IN · Matchup complete!", 900)
        self.set_screen(COLONY_SELECTION)
        return True

    def load_setup_player(self, player: int) -> None:
        self.state.setup_player = player
        if player == 1:
            self.state.colony_cfu = self.state.player1_colony_cfu
            self.state.colony_score = self.state.player1_colony_score
            self.state.colony_label = self.state.player1_colony_label
            self.state.has_secretion = self.state.player1_arsenal_active
        else:
            self.state.colony_cfu = self.state.player2_colony_cfu
            self.state.colony_score = self.state.player2_colony_score
            self.state.colony_label = self.state.player2_colony_label
            self.state.has_secretion = self.state.player2_arsenal_active

    def sync_setup_aliases(self) -> None:
        self.state.colony_cfu = self.state.player1_colony_cfu
        self.state.colony_score = self.state.player1_colony_score
        self.state.colony_label = self.state.player1_colony_label
        self.state.opponent_colony_cfu = self.state.player2_colony_cfu
        self.state.opponent_colony_score = self.state.player2_colony_score
        self.state.has_secretion = self.state.player1_arsenal_active
        self.state.opponent_has_secretion = bool(self.state.player2_arsenal_active)

    def can_select_fighter(self, entry: BacteriumCatalogEntry) -> bool:
        return not (
            self.state.game_mode == TWO_PLAYERS
            and self.state.active_player == 2
            and self.state.player1_fighter is not None
            and entry.catalog_id == self.state.player1_fighter.catalog_id
        )

    def select_catalog_entry(self, entry: BacteriumCatalogEntry) -> bool:
        if not self.can_select_fighter(entry):
            self.show_popup("This fighter is already in the arena for Player 1.")
            return False
        self.state.selected_catalog_entry = entry
        self.state.selected_at = pygame.time.get_ticks()
        self.audio.play("select")
        self.state.show_all_bgcs = False
        self.state.bgc_scroll = 0
        return True

    def select_game_mode(self, game_mode: str) -> None:
        if game_mode not in {ONE_PLAYER, TWO_PLAYERS}:
            raise ValueError(f"Unsupported game mode: {game_mode}")
        if self.state.game_mode != game_mode:
            self.return_to_opening(preserve_mode=False)
        self.state.game_mode = game_mode
        self.state.active_player = 1
        self.audio.play("select")

    def start_game(self) -> None:
        if not self.state.game_mode or self.catalog_error:
            return
        mode = self.state.game_mode
        reset_for_new_game(self.state)
        self.state.game_mode = mode
        self.state.active_player = 1
        self.refresh_catalog_choices()
        self.set_screen(FIGHTER_SELECTION)

    def return_to_player1_selection(self) -> None:
        previous = self.state.player1_fighter
        self.state.active_player = 1
        self.state.player1_confirmed = False
        self.state.player2_fighter = None
        self.state.player2_confirmed = False
        self.state.player_entry = previous
        self.state.opponent_entry = None
        self.state.selected_catalog_entry = previous
        self.state.search_query = ""
        self.state.search_message = "Player 2 selection cleared. Player 1 may confirm or choose a new fighter."
        self.set_screen(FIGHTER_SELECTION)

    def return_to_opening(self, preserve_mode: bool) -> None:
        mode = self.state.game_mode if preserve_mode else None
        reset_for_new_game(self.state)
        self.state.game_mode = mode
        self.refresh_catalog_choices()
        self.set_screen(WELCOME)

    def main_menu(self) -> None:
        self.return_to_opening(preserve_mode=False)

    def slider_hit(self, pos: tuple[int, int]) -> bool:
        return self.slider_rect.inflate(30, 34).collidepoint(pos)

    def update_slider(self, x: int) -> None:
        ratio = max(0, min(1, (x - self.slider_rect.left) / self.slider_rect.width))
        self.state.colony_cfu = int(round(ratio * 1000))
        self.state.colony_score, self.state.colony_label = colony_growth_score(self.state.colony_cfu)
        self.store_current_colony_setup()
        self.state.colony_selected_at = pygame.time.get_ticks()

    def store_current_colony_setup(self) -> None:
        if self.state.setup_player == 1:
            self.state.player1_colony_cfu = self.state.colony_cfu
            self.state.player1_colony_score = self.state.colony_score
            self.state.player1_colony_label = self.state.colony_label
        else:
            self.state.player2_colony_cfu = self.state.colony_cfu
            self.state.player2_colony_score = self.state.colony_score
            self.state.player2_colony_label = self.state.colony_label

    def setup_fighter(self) -> BacteriumCatalogEntry | None:
        return self.state.player1_fighter if self.state.setup_player == 1 else self.state.player2_fighter

    def button_id(self, rect, text: str) -> str:
        r = pygame.Rect(rect)
        return f"{self.state.screen}:{text}:{r.x}:{r.y}"

    def add_button(self, rect, text, action, selected=False, enabled=True, small=False, tooltip="", style="button") -> None:
        self.buttons.append(Button(pygame.Rect(rect), text, action, selected, enabled, small, control_id=self.button_id(rect, text), tooltip=tooltip, style=style))

    def add_name_button(self, rect, name: BacterialName, action, selected=False, secondary_text="") -> None:
        self.buttons.append(Button(pygame.Rect(rect), name.plain, action, selected, True, True, name, secondary_text, control_id=self.button_id(rect, name.plain)))

    def add_fighter_button(self, rect, entry: BacteriumCatalogEntry, action, selected=False, secondary_text="", enabled=True) -> None:
        name = format_bacterial_name(entry.full_name)
        self.buttons.append(Button(pygame.Rect(rect), name.plain, action, selected, enabled, True, name, secondary_text, entry, self.button_id(rect, entry.catalog_id)))

    def draw(self, mouse, dt) -> None:
        self.screen.set_clip(None)
        self.buttons = []
        self.draw_background()
        if self.state.screen == WELCOME:
            self.draw_welcome()
        elif self.state.screen == FIGHTER_SELECTION:
            self.draw_fighter_selection()
        elif self.state.screen == COLONY_SELECTION:
            self.draw_colony()
        elif self.state.screen == SECRETION_SELECTION:
            self.draw_secretion()
        elif self.state.screen == ENVIRONMENT_SELECTION:
            self.draw_environment_selection()
        elif self.state.screen == BATTLE_PREVIEW:
            self.draw_preview()
        elif self.state.screen == BATTLE_ANIMATION:
            self.draw_animation(dt)
        elif self.state.screen == RESULTS:
            self.draw_results()
        elif self.state.screen == SETTINGS:
            self.draw_settings()
        self.draw_popup()
        self.draw_buttons(mouse)
        self.draw_tooltip()
        self.draw_transition()
        if self.input_debug:
            self.draw_input_debug(mouse)
        ids = {button.control_id for button in self.buttons if button.enabled}
        if self.input.focused_id not in ids:
            self.input.focused_id = next(iter(ids), None)

    def draw_background(self) -> None:
        if self.state.screen in {ENVIRONMENT_SELECTION, BATTLE_PREVIEW, BATTLE_ANIMATION} and self.state.environment:
            self.draw_arena_background(self.state.environment)
            return
        if self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill((18, 36, 58))
            for i in range(70):
                x = (i * 137) % WIDTH
                y = (i * 83) % HEIGHT
                pygame.draw.circle(self.screen, (40, 130, 120), (x, y), 3 + i % 9)
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 12, 25, 125))
        self.screen.blit(overlay, (0, 0))
        self.draw_ambient_particles()

    def draw_ambient_particles(self) -> None:
        now = 0 if self.settings.reduced_motion else pygame.time.get_ticks() / 1000
        motion = 0 if self.settings.reduced_motion else now
        for i in range(30):
            x = int((i * 173 + motion * (5 + i % 4)) % (WIDTH + 50) - 25)
            y = int((i * 97 + math.sin(motion * .55 + i) * 18) % HEIGHT)
            color = THEME.yellow if i % 7 == 0 else THEME.cyan
            pygame.draw.circle(self.screen, color, (x, y), 2 + i % 4, 1)

    def draw_arena_background(self, environment: str) -> None:
        visual = environment_visual(environment)
        for y in range(HEIGHT):
            mix = y / HEIGHT
            color = tuple(int(a + (b - a) * mix) for a, b in zip(visual.top, visual.bottom))
            pygame.draw.line(self.screen, color, (0, y), (WIDTH, y))
        now = pygame.time.get_ticks() / 1000
        for i in range(34):
            x = int((i * 97 + now * (13 + i % 5)) % (WIDTH + 80) - 40)
            y = 120 + (i * 71) % 590 + int(math.sin(now * 1.2 + i) * 10)
            size = 2 + i % 5
            if visual.ambient == "crosses":
                pygame.draw.line(self.screen, visual.particle, (x - size, y), (x + size, y), 2)
                pygame.draw.line(self.screen, visual.particle, (x, y - size), (x, y + size), 2)
            elif visual.ambient == "rings":
                pygame.draw.circle(self.screen, visual.particle, (x, y), size + 3, 1)
            else:
                pygame.draw.circle(self.screen, visual.particle, (x, y), size, 1)
        pygame.draw.ellipse(self.screen, (8, 18, 31), (-100, 590, 1400, 260))
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veil.fill((4, 9, 18, 40))
        self.screen.blit(veil, (0, 0))

    def draw_transition(self) -> None:
        progress = self.transition.progress(pygame.time.get_ticks(), self.settings.reduced_motion)
        if progress >= 1:
            return
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veil.fill((THEME.ink[0], THEME.ink[1], THEME.ink[2], int(185 * (1 - progress))))
        self.screen.blit(veil, (0, 0))

    def panel(self, rect, alpha=215) -> pygame.Rect:
        r = pygame.Rect(rect)
        surf = pygame.Surface(r.size, pygame.SRCALPHA)
        pygame.draw.rect(surf, (12, 30, 48, alpha), surf.get_rect(), border_radius=24)
        pygame.draw.rect(surf, (108, 231, 218, 210), surf.get_rect(), 3, border_radius=24)
        self.screen.blit(surf, r)
        return r

    def text(self, text, font, color, center=None, topleft=None) -> pygame.Rect:
        surf = font.render(text, True, color)
        rect = surf.get_rect()
        if center:
            rect.center = center
        if topleft:
            rect.topleft = topleft
        self.screen.blit(surf, rect)
        return rect

    def draw_scientific_name(self, name: BacterialName, x: int, y: int, font=None, color=(146, 255, 167), max_width=None) -> int:
        """Draw genus/species in italics and all qualifiers in regular type."""
        font = font or self.font
        italic = self.small_italic if font is self.small else self.font_italic
        segments = []
        if name.genus:
            segments.append((name.genus, italic))
        if name.species:
            segments.append(((" " if segments else "") + name.species, italic))
        if name.rank and name.infraspecific:
            segments.append((f" {name.rank} {name.infraspecific}", font))
        if not segments:
            segments.append((name.plain, font))
        width = sum(segment_font.size(text)[0] for text, segment_font in segments)
        if max_width and width > max_width and name.species:
            segments = [(name.genus, italic), (f" {name.species}", italic)]
        cx = x
        for value, segment_font in segments:
            cx = self.text(value, segment_font, color, topleft=(cx, y)).right
        return font.get_height()

    def draw_winner_heading(self, name: BacterialName, y: int) -> None:
        suffix = " wins!"
        total_width = self.font_italic.size(name.scientific)[0] + self.font.size(suffix)[0]
        x = WIDTH // 2 - total_width // 2
        x = self.text(name.scientific, self.font_italic, (255, 238, 133), topleft=(x, y)).right
        self.text(suffix, self.font, (255, 238, 133), topleft=(x, y))

    def wrap(self, text: str, font, width: int) -> list[str]:
        return wrap_text(text, width, lambda candidate: font.size(candidate)[0])

    def display_value(self, value, context="general", key="value") -> str:
        return friendly_value(value, context, deck=self.flavor, key=key)

    def draw_wrapped(self, text: str, rect, font, color, line_gap=4) -> int:
        y = rect.top
        for line in self.wrap(text, font, rect.width):
            self.text(line, font, color, topleft=(rect.left, y))
            y += font.get_height() + line_gap
            if y > rect.bottom - font.get_height():
                break
        return y

    def draw_welcome(self) -> None:
        self.panel((215, 70, 770, 580))
        now = pygame.time.get_ticks() / 1000
        title_y = 165 if self.settings.reduced_motion else 165 + int(math.sin(now * 1.2) * 5)
        glow = 4 + int((math.sin(now * 1.8) + 1) * 2)
        self.text("MICROBIAL MAYHEM", self.big, (35, 80, 74), center=(WIDTH // 2 + glow, title_y + glow))
        self.text("MICROBIAL MAYHEM", self.big, THEME.mint, center=(WIDTH // 2, title_y))
        msg = "Build a tiny champion, pick an extreme arena, and settle a colorful microbial showdown."
        self.draw_wrapped(msg, pygame.Rect(310, 235, 580, 80), self.font, THEME.text, line_gap=8)
        self.text("CHOOSE GAME MODE", self.tiny, THEME.yellow, center=(WIDTH // 2, 337))
        self.add_button((350, 365, 230, 72), "1 Player", lambda: self.select_game_mode(ONE_PLAYER), selected=self.state.game_mode == ONE_PLAYER, tooltip="Solo battle against an automatically selected rival.")
        self.add_button((620, 365, 230, 72), "2 Players", lambda: self.select_game_mode(TWO_PLAYERS), selected=self.state.game_mode == TWO_PLAYERS, tooltip="Local versus: both players choose a fighter on this device.")
        if self.state.game_mode == ONE_PLAYER:
            mode_text = "SOLO BATTLE · The database will choose a different rival."
        elif self.state.game_mode == TWO_PLAYERS:
            mode_text = "LOCAL VERSUS · Player 2 chooses the rival fighter."
        else:
            mode_text = "Select 1 Player or 2 Players to begin."
        self.text(mode_text, self.small, THEME.muted, center=(WIDTH // 2, 470))
        if self.catalog_error:
            self.draw_wrapped(self.catalog_error, pygame.Rect(320, 485, 560, 50), self.small, THEME.yellow)
        self.add_button((375, 520, 270, 70), "Start Game", self.start_game, enabled=bool(self.state.game_mode) and not self.catalog_error)
        self.add_button((670, 520, 155, 70), "Settings", lambda: self.set_screen(SETTINGS), small=True)

    def draw_settings(self) -> None:
        self.panel((220, 55, 760, 710))
        self.text("SETTINGS & ACCESSIBILITY", self.mid, THEME.yellow, center=(WIDTH // 2, 105))
        rows = [
            ("Reduced motion", self.settings.reduced_motion, lambda: self.toggle_setting("reduced_motion"), "Replaces large movement with shorter fades and state changes."),
            ("High contrast", self.settings.high_contrast, lambda: self.toggle_setting("high_contrast"), "Strengthens borders and focus indicators."),
            ("Master mute", self.settings.muted, lambda: self.toggle_setting("muted"), "Mutes music and sound effects."),
        ]
        y = 165
        for label, value, action, tip in rows:
            self.text(label, self.font, THEME.text, topleft=(315, y + 14))
            self.add_button((690, y, 180, 54), "ON" if value else "OFF", action, selected=value, tooltip=tip)
            y += 76
        self.text(f"Text scale  {self.settings.text_scale:.2f}×", self.font, THEME.text, topleft=(315, y + 14))
        self.add_button((690, y, 80, 54), "−", lambda: self.adjust_setting("text_scale", -.1))
        self.add_button((790, y, 80, 54), "+", lambda: self.adjust_setting("text_scale", .1))
        y += 76
        self.text(f"Music volume  {round(self.settings.music_volume * 100)}%", self.font, THEME.text, topleft=(315, y + 14))
        self.add_button((690, y, 80, 54), "−", lambda: self.adjust_setting("music_volume", -.1))
        self.add_button((790, y, 80, 54), "+", lambda: self.adjust_setting("music_volume", .1))
        y += 76
        self.text(f"Effects volume  {round(self.settings.sfx_volume * 100)}%", self.font, THEME.text, topleft=(315, y + 14))
        self.add_button((690, y, 80, 54), "−", lambda: self.adjust_setting("sfx_volume", -.1))
        self.add_button((790, y, 80, 54), "+", lambda: self.adjust_setting("sfx_volume", .1))
        self.add_button((350, 650, 230, 54), "Replay Tips", self.replay_onboarding, small=True)
        self.add_button((620, 650, 230, 54), "Back", lambda: self.set_screen(WELCOME))

    def toggle_setting(self, name: str) -> None:
        setattr(self.settings, name, not getattr(self.settings, name))
        self.settings.save()
        if name == "muted":
            self.audio.apply_settings(pygame.time.get_ticks())

    def adjust_setting(self, name: str, amount: float) -> None:
        setattr(self.settings, name, getattr(self.settings, name) + amount)
        self.settings.normalized().save()
        if name == "text_scale":
            self.configure_fonts()
        elif name == "music_volume":
            self.audio.set_music_volume(self.settings.music_volume)

    def replay_onboarding(self) -> None:
        self.settings.onboarding_complete = False
        self.settings.save()
        if self.state.game_mode:
            self.start_game()
        else:
            self.set_screen(WELCOME)

    def draw_fighter_selection(self) -> None:
        self.panel((30, 25, 1140, 770))
        active = self.state.active_player
        accent = THEME.mint if active == 1 else THEME.coral
        heading = f"PLAYER {active}: CHOOSE YOUR FIGHTER"
        self.text(heading, self.mid, accent, center=(WIDTH // 2, 58))
        search_rect = pygame.Rect(65, 88, 430, 42)
        pygame.draw.rect(self.screen, (245, 250, 255), search_rect, border_radius=10)
        query = self.state.search_query or "Search scientific name, genus, or strain..."
        color = (20, 32, 45) if self.state.search_query else (105, 115, 125)
        self.text(query[:42], self.small, color, topleft=(search_rect.x + 12, search_rect.y + 12))
        self.add_button((510, 87, 115, 44), "Search", self.apply_search, small=True)
        self.add_button((640, 87, 255, 44), "Show 10 Different Bacteria", self.refresh_catalog_choices, small=True)
        self.text(self.state.search_message, self.small, (245, 250, 255), topleft=(65, 137))

        list_panel = pygame.Rect(55, 165, 445, 555)
        info_panel = pygame.Rect(520, 165, 625, 555)
        pygame.draw.rect(self.screen, (10, 24, 38, 170), list_panel, border_radius=14)
        pygame.draw.rect(self.screen, (10, 24, 38, 190), info_panel, border_radius=14)
        pygame.draw.rect(self.screen, (108, 231, 218), list_panel, 1, border_radius=14)
        pygame.draw.rect(self.screen, (108, 231, 218), info_panel, 1, border_radius=14)

        list_top = list_panel.y + 14
        visible = self.state.catalog_choices[self.state.scroll_offset:self.state.scroll_offset + 10]
        for idx, entry in enumerate(visible):
            y = list_top + idx * 52
            name = format_bacterial_name(entry.full_name)
            strain = sanitize_designation(entry.strain)
            secondary = f"Strain {strain}" if strain.casefold() not in {"", "no", "none", "unknown", "not specified"} else name.short_secondary
            selected = self.state.selected_catalog_entry and entry.catalog_id == self.state.selected_catalog_entry.catalog_id
            available = self.can_select_fighter(entry)
            if not available:
                secondary = "PLAYER 1 CLAIMED · Choose a different rival"
            self.add_fighter_button((69, y, 410, 45), entry, lambda e=entry: self.select_catalog_entry(e), selected=selected, secondary_text=secondary, enabled=available)
        if len(self.state.catalog_choices) > 10:
            track = pygame.Rect(486, list_panel.y + 14, 8, 520)
            pygame.draw.rect(self.screen, (70, 90, 105), track, border_radius=6)
            thumb_h = max(35, int(track.height * 10 / len(self.state.catalog_choices)))
            max_offset = max(1, len(self.state.catalog_choices) - 10)
            thumb_y = track.y + int((track.height - thumb_h) * self.state.scroll_offset / max_offset)
            pygame.draw.rect(self.screen, (146, 255, 167), (track.x, thumb_y, track.width, thumb_h), border_radius=6)

        self.draw_selected_organism_card(info_panel)
        confirm_label = f"LOCK PLAYER {active}"
        self.add_button((480, 735, 240, 48), confirm_label, self.confirm_fighter, enabled=self.state.selected_catalog_entry is not None and self.can_select_fighter(self.state.selected_catalog_entry))
        if self.state.game_mode == TWO_PLAYERS and active == 2 and self.state.player1_fighter:
            self.draw_locked_fighter_badge(pygame.Rect(905, 84, 240, 70))
        self.draw_onboarding_tip("Choose a fighter card, then inspect its ability, habitat, and detailed biological evidence.", pygame.Rect(750, 735, 390, 48))

    def draw_locked_fighter_badge(self, rect: pygame.Rect) -> None:
        entry = self.state.player1_fighter
        surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(surface, (*THEME.panel_light, 245), surface.get_rect(), border_radius=14)
        pygame.draw.rect(surface, (*THEME.mint, 230), surface.get_rect(), 2, border_radius=14)
        self.screen.blit(surface, rect)
        self.draw_bacterium_sprite(entry, (rect.x + 34, rect.centery), .26, phase=pygame.time.get_ticks() / 550)
        self.text("PLAYER 1 LOCKED", self.tiny, THEME.mint, topleft=(rect.x + 65, rect.y + 12))
        name = format_bacterial_name(entry.full_name).scientific
        short_name = name if self.small_italic.size(name)[0] <= rect.width - 78 else name[:18].rstrip() + "…"
        self.text(short_name, self.small_italic, THEME.text, topleft=(rect.x + 65, rect.y + 37))

    def draw_selected_organism_card(self, rect: pygame.Rect) -> None:
        clip_before = self.screen.get_clip()
        self.screen.set_clip(rect.inflate(-16, -16))
        x, y = rect.x + 14, rect.y + 14
        if not self.state.selected_catalog_entry:
            if self.state.game_mode == TWO_PLAYERS and self.state.active_player == 2 and self.state.player1_fighter:
                self.text("PLAYER 1 IS READY", self.small, THEME.mint, topleft=(x, y))
                self.draw_bacterium_sprite(self.state.player1_fighter, (rect.centerx, y + 120), .9, phase=pygame.time.get_ticks() / 500)
                p1_name = format_bacterial_name(self.state.player1_fighter.full_name)
                self.draw_scientific_name(p1_name, x, y + 210, self.font, THEME.text, rect.width - 28)
                self.text("PLAYER 2", self.small, THEME.coral, topleft=(x, y + 270))
                self.draw_wrapped("Choose a different organism to build the rival side of this matchup.", pygame.Rect(x, y + 300, rect.width - 28, 80), self.font, THEME.text, 5)
            else:
                self.draw_wrapped("Select an organism from the list to view its MIBiG-backed identity, traits, biosynthetic products, colony metadata, and a curious fact.", pygame.Rect(x, y, rect.width - 28, rect.height - 28), self.small, (245, 250, 255))
            self.screen.set_clip(clip_before)
            return
        entry = self.state.selected_catalog_entry
        name = format_bacterial_name(entry.full_name)
        visual = fighter_visual(entry)
        self.text("SELECTED FIGHTER", self.small, (255, 238, 133), topleft=(x, y))
        y += 25
        self.draw_scientific_name(name, x, y, self.font, max_width=rect.width - 190)
        self.text(visual.epithet, self.small, THEME.mint, topleft=(x, y + 29))
        selected_age = max(0, pygame.time.get_ticks() - self.state.selected_at)
        pop = 1.0 if self.settings.reduced_motion else .92 + .08 * ease_out_cubic(selected_age / 320)
        self.draw_bacterium_sprite(entry, (rect.right - 92, y + 37), 0.58 * pop, facing=-1, phase=pygame.time.get_ticks() / 500)
        y += 82
        if self.state.show_all_bgcs:
            self.text(f"ALL {len(entry.accessions)} MIBIG BGC IDS", self.small, (255, 238, 133), topleft=(x, y))
            y += 28
            visible = entry.accessions[self.state.bgc_scroll:self.state.bgc_scroll + 12]
            for accession in visible:
                self.text(accession, self.small, (245, 250, 255), topleft=(x + 8, y))
                y += 25
            if len(entry.accessions) > 12:
                start = self.state.bgc_scroll + 1
                end = self.state.bgc_scroll + len(visible)
                self.text(f"Showing {start}–{end}; use the mouse wheel to scroll", self.small, (146, 255, 167), topleft=(x, rect.bottom - 65))
            self.add_button((rect.right - 145, rect.bottom - 43, 120, 30), "Back", lambda: setattr(self.state, "show_all_bgcs", False), small=True)
            self.screen.set_clip(clip_before)
            return
        rows = [
            ("Morphology", sanitize_designation(entry.cell_shape) if not is_missing(entry.cell_shape) else f"{visual.morphology.title()} procedural art; recorded shape unavailable"),
            ("Ability", visual.ability),
            ("Habitat", visual.habitat),
        ]
        for label, value in rows:
            self.text(label, self.small, (255, 238, 133), topleft=(x, y))
            y = self.draw_wrapped(value, pygame.Rect(x + 125, y, rect.width - 159, 42), self.small, (245, 250, 255), 2)
            y += 5

        count = len(entry.accessions)
        self.text("Known BGCs", self.small, (255, 238, 133), topleft=(x, y))
        self.text(str(count), self.font, (146, 255, 167), topleft=(x + 122, y - 3))
        preview = ", ".join(entry.accessions[:3]) or self.display_value(None, "arsenal", f"{entry.catalog_id}:selection:bgc")
        if count > 3:
            preview += f"  +{count - 3} more"
            self.add_button((rect.right - 165, rect.bottom - 43, 140, 30), "View all BGCs", lambda: setattr(self.state, "show_all_bgcs", True), small=True)
        y = self.draw_wrapped(preview, pygame.Rect(x + 150, y, rect.width - 184, 42), self.small, (245, 250, 255), 2) + 5

        y = self.draw_labeled_chips("Products", entry.products, x, y, rect.width - 28, (50, 145, 175))
        y = self.draw_labeled_chips("Activities", entry.activities, x, y, rect.width - 28, (120, 100, 190))
        sections = [("Battle bio", self.display_value(entry.curious_fact or entry.description, "general", f"{entry.catalog_id}:bio"))]
        for title, body in sections:
            if y > rect.bottom - 48:
                break
            self.text(title, self.small, (255, 238, 133), topleft=(x, y))
            y = self.draw_wrapped(sanitize_designation(body), pygame.Rect(x + 108, y, rect.width - 142, 46), self.small, (245, 250, 255), 2) + 5
        self.screen.set_clip(clip_before)

    def draw_chips(self, labels, x: int, y: int, width: int, color, max_items=4, max_rows=2) -> int:
        unique = []
        for raw in labels:
            label = sanitize_designation(raw)
            if label and label.casefold() not in {item.casefold() for item in unique}:
                unique.append(label)
        shown = unique[:max_items]
        if len(unique) > max_items:
            shown.append(f"+{len(unique) - max_items} more")
        if not shown:
            return y
        cx, cy, row = x, y, 1
        for label in shown:
            label = label if len(label) <= 34 else label[:31].rstrip() + "…"
            chip_w = min(width, max(76, self.small.size(label)[0] + 20))
            if cx > x and cx + chip_w > x + width:
                row += 1
                if row > max_rows:
                    break
                cx, cy = x, cy + 27
            pygame.draw.rect(self.screen, color, (cx, cy, chip_w, 22), border_radius=11)
            self.text(label, self.small, (255, 255, 255), center=(cx + chip_w // 2, cy + 11))
            cx += chip_w + 7
        return cy + 27

    def draw_labeled_chips(self, title, labels, x, y, width, color) -> int:
        self.text(title, self.small, (255, 238, 133), topleft=(x, y))
        if not labels:
            context = "activity"
            message = self.display_value(None, context, f"chips:{title}:{x}:{y}")
            return self.draw_wrapped(message, pygame.Rect(x + 108, y, width - 108, 42), self.tiny, THEME.muted, 2) + 3
        return self.draw_chips(labels, x + 108, y, width - 108, color, max_items=3, max_rows=2)

    def draw_trait_chips(self, entry: BacteriumCatalogEntry, x: int, y: int, width: int, max_items=4) -> int:
        labels = ["Antimicrobial producer" if evidence.trait == "Antimicrobial production" else evidence.trait for evidence in entry.traits]
        if not labels:
            message = self.display_value(None, "trait", f"{entry.catalog_id}:traits")
            return self.draw_wrapped(message, pygame.Rect(x, y, width, 40), self.tiny, THEME.muted, 2) + 3
        return self.draw_chips(labels, x, y, width, (120, 100, 190), max_items=max_items)

    def draw_choice_grid(self, title, choices, attr, screen_name) -> None:
        self.panel((170, 55, 860, 590))
        self.text(title, self.mid, (255, 238, 133), center=(WIDTH // 2, 105))
        for idx, (label, value) in enumerate(choices):
            col, row = idx % 2, idx // 2
            rect = (235 + col * 390, 160 + row * 82, 340, 58)
            button_label = ENVIRONMENT_LABELS[value] if screen_name == ENVIRONMENT_SELECTION else label
            tip = "Environment evidence can modify scoring; unknown evidence is not treated as a negative." if screen_name == ENVIRONMENT_SELECTION else ""
            self.add_button(rect, button_label, lambda v=value: setattr(self.state, attr, v), getattr(self.state, attr) == value, tooltip=tip)
        selected = getattr(self.state, attr) is not None
        next_screen = {
            FIGHTER_SELECTION: COLONY_SELECTION,
            ENVIRONMENT_SELECTION: BATTLE_PREVIEW,
        }[screen_name]
        self.add_button((490, 585, 220, 54), "Continue", lambda: self.after_choice(next_screen), enabled=selected)
        if screen_name == ENVIRONMENT_SELECTION:
            self.draw_onboarding_tip("Arena effects visualize environmental pressure; the scoring module still determines its effect.", pygame.Rect(350, 675, 500, 55))

    def draw_environment_selection(self) -> None:
        self.text("CHOOSE THE BATTLEGROUND", self.mid, THEME.yellow, center=(WIDTH // 2, 48))
        self.text("Every arena uses the existing environment evidence rules shown below.", self.small, THEME.text, center=(WIDTH // 2, 82))
        rects = [pygame.Rect(65 + i * 270, 112, 250, 190) for i in range(4)]
        rects += [pygame.Rect(200 + i * 300, 330, 250, 190) for i in range(3)]
        seed = f"{self.state.player_entry.catalog_id}:{self.state.opponent_entry.catalog_id}" if self.state.player_entry and self.state.opponent_entry else "arena"
        for environment, rect in zip(ENVIRONMENTS, rects):
            selected = self.state.environment == environment
            control_id = self.button_id(rect, environment)
            hovered = self.input.hovered_id == control_id
            self.draw_environment_card(environment, rect, seed, selected, hovered)
            self.add_button(
                rect, environment, lambda value=environment: self.choose_environment(value),
                selected=selected, tooltip="Preview this arena and inspect its actual environment score rule.", style="card",
            )

        detail = pygame.Rect(150, 548, 900, 112)
        surface = pygame.Surface(detail.size, pygame.SRCALPHA)
        pygame.draw.rect(surface, (*THEME.panel, 238), surface.get_rect(), border_radius=20)
        pygame.draw.rect(surface, (*THEME.yellow, 225), surface.get_rect(), 2, border_radius=20)
        self.screen.blit(surface, detail)
        if self.state.environment:
            visual = environment_visual(self.state.environment)
            self.text(f"{visual.title.upper()}  ·  {environment_flavor(self.state.environment)}", self.small, THEME.yellow, topleft=(detail.x + 22, detail.y + 17))
            effect = environment_effect_text(self.state.player_entry, self.state.opponent_entry, self.state.environment)
            self.draw_wrapped(effect, pygame.Rect(detail.x + 22, detail.y + 49, detail.width - 44, 50), self.small, THEME.text, 3)
        else:
            self.text("Pick an arena to reveal its documented scoring rule.", self.font, THEME.text, center=detail.center)
        self.add_button((470, 690, 260, 58), "ENTER THIS ARENA", lambda: self.after_choice(BATTLE_PREVIEW), enabled=self.state.environment is not None)

    def choose_environment(self, environment: str) -> None:
        self.state.environment = environment
        self.state.environment_selected_at = pygame.time.get_ticks()
        self.audio.play("select")

    def draw_environment_card(self, environment: str, rect: pygame.Rect, seed: str, selected: bool, hovered: bool) -> None:
        visual = environment_visual(environment)
        lift = 0 if self.settings.reduced_motion or not hovered else 5
        scale = 6 if selected else 0
        card = rect.inflate(scale, scale).move(0, -lift)
        surface = pygame.Surface(card.size, pygame.SRCALPHA)
        for y in range(card.height):
            mix = y / max(1, card.height)
            color = tuple(int(a + (b - a) * mix) for a, b in zip(visual.top, visual.bottom))
            pygame.draw.line(surface, color, (0, y), (card.width, y))
        mask = pygame.Surface(card.size, pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=18)
        surface.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        self.screen.blit(surface, card)
        pygame.draw.rect(self.screen, THEME.yellow if selected else visual.particle, card, 4 if selected else 2, border_radius=18)
        if selected and not self.settings.reduced_motion:
            glow = 5 + int((math.sin(pygame.time.get_ticks() / 170) + 1) * 3)
            pygame.draw.rect(self.screen, visual.particle, card.inflate(glow, glow), 2, border_radius=22)
        preview_rect = pygame.Rect(card.x + 10, card.y + 38, card.width - 20, 92)
        self.draw_environment_particles(environment, preview_rect, seed)
        self.text(visual.title.upper(), self.tiny, THEME.text, center=(card.centerx, card.y + 20))
        flavor_lines = self.wrap(environment_flavor(environment), self.tiny, card.width - 18)[:2]
        start_y = card.bottom - 42 if len(flavor_lines) == 1 else card.bottom - 54
        for index, line in enumerate(flavor_lines):
            self.text(line, self.tiny, THEME.text, center=(card.centerx, start_y + index * (self.tiny.get_height() + 1)))
        internal = ENVIRONMENT_LABELS[environment]
        self.text(internal, self.tiny, visual.particle, center=(card.centerx, card.bottom - 14))

    def draw_environment_particles(self, environment: str, rect: pygame.Rect, seed: str) -> None:
        visual = environment_visual(environment)
        now = pygame.time.get_ticks() / 1000
        for particle in environment_particles(environment, seed):
            motion = animation_time(now, self.settings.reduced_motion) * particle.speed
            x = rect.x + ((particle.x + math.sin(motion + particle.phase) * .035) % 1) * rect.width
            direction = -1 if environment in {"Hot", "Acidic"} else 1
            y = rect.y + ((particle.y + direction * motion * .055) % 1) * rect.height
            size = max(2, int(particle.size * min(rect.width, rect.height)))
            point = (int(x), int(y))
            if environment == "Cold":
                pygame.draw.line(self.screen, visual.particle, (point[0] - size, point[1]), (point[0] + size, point[1]), 1)
                pygame.draw.line(self.screen, visual.particle, (point[0], point[1] - size), (point[0], point[1] + size), 1)
            elif environment == "In the presence of antibiotics":
                pygame.draw.line(self.screen, visual.particle, (point[0] - size, point[1]), (point[0] + size, point[1]), 2)
                pygame.draw.line(self.screen, visual.particle, (point[0], point[1] - size), (point[0], point[1] + size), 2)
            elif environment == "Salty":
                crystal = [(point[0], point[1] - size), (point[0] + size, point[1]), (point[0], point[1] + size), (point[0] - size, point[1])]
                pygame.draw.polygon(self.screen, visual.particle, crystal, 1)
            elif environment == "Alkaline":
                pygame.draw.circle(self.screen, visual.particle, point, size + 2, 1)
            elif environment == "Hot":
                pygame.draw.circle(self.screen, visual.particle, point, size + 1, 1)
                pygame.draw.line(self.screen, visual.particle, (point[0], point[1] - size * 2), (point[0] + size, point[1] - size * 3), 1)
            elif environment == "Acidic":
                pygame.draw.circle(self.screen, visual.particle, point, size + 2, 2)
            else:
                pygame.draw.circle(self.screen, visual.particle, point, size)

    def after_choice(self, next_screen: str) -> None:
        if next_screen == BATTLE_PREVIEW and self.state.player_breakdown is None:
            if self.state.opponent_entry is None:
                if self.state.game_mode == TWO_PLAYERS:
                    self.show_popup("Player 2 must lock in a rival before entering the arena.")
                    self.set_screen(FIGHTER_SELECTION)
                    self.state.active_player = 2
                    return
                self.state.opponent_entry = choose_opponent(self.state.player_entry.catalog_id, catalog=self.catalog)
                self.state.player2_fighter = self.state.opponent_entry
                self.state.opponent_has_secretion = random.choice([True, False])
                self.state.player2_arsenal_active = self.state.opponent_has_secretion
            if self.state.game_mode == TWO_PLAYERS:
                self.sync_setup_aliases()
                if not self.battle_setup_complete():
                    self.show_popup("Both players must lock their colony and arsenal before entering the arena.")
                    return
            self.state.battle_seed = random.randrange(1_000_000)
            if self.state.game_mode != TWO_PLAYERS:
                self.state.opponent_colony_cfu = generate_opponent_cfu(self.state.battle_seed)
                self.state.opponent_colony_score, _ = colony_growth_score(self.state.opponent_colony_cfu)
                self.state.player2_colony_cfu = self.state.opponent_colony_cfu
                self.state.player2_colony_score, self.state.player2_colony_label = colony_growth_score(self.state.opponent_colony_cfu)
            calculate_battle(self.state)
        self.set_screen(next_screen)

    def battle_setup_complete(self) -> bool:
        fighters_ready = bool(
            self.state.player1_confirmed and self.state.player2_confirmed
            and self.state.player1_fighter and self.state.player2_fighter
        )
        if not fighters_ready or not self.state.environment:
            return False
        if self.state.game_mode == TWO_PLAYERS:
            return bool(
                self.state.player1_colony_confirmed
                and self.state.player2_colony_confirmed
                and self.state.player1_arsenal_active is not None
                and self.state.player2_arsenal_active is not None
            )
        return self.state.player1_colony_confirmed and self.state.player1_arsenal_active is not None

    def draw_colony(self) -> None:
        self.panel((35, 24, 1130, 772))
        heading = f"PLAYER {self.state.setup_player} · BUILD YOUR COLONY" if self.state.game_mode == TWO_PLAYERS else "BUILD YOUR COLONY"
        accent = THEME.mint if self.state.setup_player == 1 else THEME.coral
        self.text(heading, self.mid, accent, center=(WIDTH // 2, 58))
        self.text("Tune the CFU count, or grab a quick preset. The battle formula stays exactly the same.", self.small, THEME.muted, center=(WIDTH // 2, 92))
        preset_rects = [pygame.Rect(70 + i * 214, 600, 194, 105) for i in range(len(COLONY_PRESETS))]
        preview_cfu = self.state.colony_cfu
        for preset, rect in zip(COLONY_PRESETS, preset_rects):
            control_id = self.button_id(rect, preset.title)
            if self.input.hovered_id == control_id:
                preview_cfu = preset.cfu
                break

        dish = pygame.Rect(70, 125, 500, 430)
        details = pygame.Rect(610, 125, 520, 430)
        pygame.draw.ellipse(self.screen, (190, 231, 224), dish)
        pygame.draw.ellipse(self.screen, (38, 91, 102), dish.inflate(-18, -18))
        pygame.draw.ellipse(self.screen, (15, 43, 59), dish.inflate(-38, -38))
        self.text("LIVE COLONY PREVIEW", self.tiny, THEME.mint, center=(dish.centerx, dish.y + 28))
        self.draw_colony_preview(dish.inflate(-48, -58), preview_cfu)
        if preview_cfu != self.state.colony_cfu:
            self.text(f"Hover preview · {preview_cfu} CFU", self.tiny, THEME.yellow, center=(dish.centerx, dish.bottom - 35))

        panel = pygame.Surface(details.size, pygame.SRCALPHA)
        pygame.draw.rect(panel, (*THEME.panel_light, 225), panel.get_rect(), border_radius=24)
        pygame.draw.rect(panel, (*THEME.cyan, 210), panel.get_rect(), 2, border_radius=24)
        self.screen.blit(panel, details)
        selected_label = f"PLAYER {self.state.setup_player} COLONY" if self.state.game_mode == TWO_PLAYERS else "SELECTED COLONY"
        self.text(selected_label, self.tiny, THEME.yellow, topleft=(details.x + 30, details.y + 26))
        self.text(f"{self.state.colony_cfu} CFU", self.big, THEME.mint, topleft=(details.x + 28, details.y + 55))
        self.text(self.state.colony_label, self.font, THEME.text, topleft=(details.x + 31, details.y + 132))
        preset = min(COLONY_PRESETS, key=lambda item: abs(item.cfu - self.state.colony_cfu))
        self.text(preset.flavor, self.small, THEME.yellow, topleft=(details.x + 31, details.y + 171))
        self.text(f"Colony score contribution  +{self.state.colony_score:.1f}", self.font, THEME.text, topleft=(details.x + 31, details.y + 218))
        self.slider_rect = pygame.Rect(details.x + 35, details.y + 292, details.width - 70, 14)
        pygame.draw.rect(self.screen, (77, 100, 112), self.slider_rect, border_radius=8)
        fill = self.slider_rect.copy(); fill.width = int(self.slider_rect.width * self.state.colony_cfu / 1000)
        pygame.draw.rect(self.screen, THEME.cyan, fill, border_radius=8)
        knob_x = self.slider_rect.left + int(self.slider_rect.width * self.state.colony_cfu / 1000)
        confirm_age = pygame.time.get_ticks() - self.state.colony_selected_at
        pulse = 0 if self.settings.reduced_motion or confirm_age > 420 else int(6 * (1 - confirm_age / 420))
        pygame.draw.circle(self.screen, THEME.yellow, (knob_x, self.slider_rect.centery), 18 + pulse)
        pygame.draw.circle(self.screen, THEME.coral, (knob_x, self.slider_rect.centery), 12)
        self.text("0", self.tiny, THEME.muted, topleft=(self.slider_rect.x, self.slider_rect.bottom + 12))
        self.text("1000 CFU", self.tiny, THEME.muted, topleft=(self.slider_rect.right - 65, self.slider_rect.bottom + 12))
        formula = f"Actual rule: CFU contributes +{self.state.colony_score:.1f} points through the shared diminishing-returns formula (maximum +10)."
        self.draw_wrapped(formula, pygame.Rect(details.x + 31, details.y + 350, details.width - 62, 58), self.tiny, THEME.muted, 2)

        for preset, rect in zip(COLONY_PRESETS, preset_rects):
            selected = self.state.colony_cfu == preset.cfu
            hovered = self.input.hovered_id == self.button_id(rect, preset.title)
            lift = 0 if self.settings.reduced_motion or not hovered else 4
            card = rect.move(0, -lift)
            color = THEME.panel_light if not selected else (63, 59, 104)
            pygame.draw.rect(self.screen, color, card, border_radius=16)
            pygame.draw.rect(self.screen, THEME.yellow if selected else THEME.cyan, card, 3 if selected else 1, border_radius=16)
            self.text(preset.title.upper(), self.tiny, THEME.yellow if selected else THEME.mint, center=(card.centerx, card.y + 20))
            self.text(f"{preset.cfu} CFU", self.small, THEME.text, center=(card.centerx, card.y + 45))
            flavor_lines = self.wrap(preset.flavor, self.tiny, card.width - 20)[:2]
            line_gap = self.tiny.get_height() + 1
            start_y = card.y + 69 if len(flavor_lines) == 1 else card.y + 67
            for line_index, line in enumerate(flavor_lines):
                self.text(line, self.tiny, THEME.muted, center=(card.centerx, start_y + line_index * line_gap))
            tooltip = f"Set {preset.cfu} CFU. The current colony formula contributes +{colony_growth_score(preset.cfu)[0]:.1f} points."
            self.add_button(rect, preset.title, lambda value=preset.cfu: self.choose_colony_size(value), selected=selected, tooltip=tooltip, style="card")
        lock_label = f"LOCK PLAYER {self.state.setup_player} COLONY" if self.state.game_mode == TWO_PLAYERS else "LOCK IN COLONY"
        self.add_button((450, 727, 300, 54), lock_label, self.confirm_colony_setup)

    def choose_colony_size(self, cfu: int) -> None:
        self.state.colony_cfu = cfu
        self.state.colony_score, self.state.colony_label = colony_growth_score(cfu)
        self.store_current_colony_setup()
        self.state.colony_selected_at = pygame.time.get_ticks()
        self.audio.play("select")

    def confirm_colony_setup(self) -> None:
        self.store_current_colony_setup()
        if self.state.setup_player == 1:
            self.state.player1_colony_confirmed = True
        else:
            self.state.player2_colony_confirmed = True
        self.set_screen(SECRETION_SELECTION)

    def draw_colony_preview(self, rect: pygame.Rect, cfu: int) -> None:
        fighter = self.setup_fighter()
        seed = fighter.catalog_id if fighter else "colony"
        visual = fighter_visual(fighter) if fighter else None
        now = pygame.time.get_ticks() / 1000
        for particle in colony_particles(cfu, seed):
            motion = animation_time(now, self.settings.reduced_motion) * particle.speed
            x = rect.x + particle.x * rect.width + math.sin(motion + particle.phase) * 7
            y = rect.y + particle.y * rect.height + math.cos(motion * .8 + particle.phase) * 5
            radius = max(3, int(particle.size * min(rect.width, rect.height)))
            primary = visual.primary if visual else THEME.mint
            secondary = visual.secondary if visual else THEME.cyan
            pygame.draw.circle(self.screen, primary, (int(x), int(y)), radius)
            pygame.draw.circle(self.screen, secondary, (int(x), int(y)), radius, 2)
            if particle.kind == "dividing" and radius > 5:
                offset = int(math.sin(motion + particle.phase) * radius * .3)
                pygame.draw.line(self.screen, secondary, (int(x + offset), int(y - radius + 2)), (int(x - offset), int(y + radius - 2)), 2)

    def draw_secretion(self) -> None:
        self.panel((35, 25, 1130, 770))
        setup_player = self.state.setup_player
        heading = f"PLAYER {setup_player} · ACTIVATE BIOSYNTHETIC ARSENAL?" if self.state.game_mode == TWO_PLAYERS else "Bring your BGC arsenal?"
        self.text(heading, self.mid, THEME.mint if setup_player == 1 else THEME.coral, center=(WIDTH // 2, 65))
        active_entry = self.setup_fighter()
        other_entry = self.state.player2_fighter if setup_player == 1 else self.state.player1_fighter
        active_choice = self.state.player1_arsenal_active if setup_player == 1 else self.state.player2_arsenal_active
        other_choice = self.state.player2_arsenal_active if setup_player == 1 else self.state.player1_arsenal_active
        if self.state.game_mode == TWO_PLAYERS:
            left_label = f"Player {setup_player} settings"
            right_label = "Player 2 fighter preview" if setup_player == 1 else "Player 1 locked setup"
        else:
            left_label, right_label = "Your fighter", "Automated rival scout report"
        self.draw_arsenal_panel(left_label, active_entry, pygame.Rect(65, 105, 515, 445), active_choice)
        self.draw_arsenal_panel(right_label, other_entry, pygame.Rect(620, 105, 515, 445), other_choice)
        player_bgc_count = len(active_entry.accessions) if active_entry else 0
        msg = f"This fighter has {player_bgc_count} known BGC{'s' if player_bgc_count != 1 else ''}. Activate this documented chemical toolkit?"
        self.draw_wrapped(msg, pygame.Rect(275, 575, 650, 58), self.font, (245, 250, 255))
        arsenal_tip = "A biosynthetic gene cluster (BGC) can contribute a documented chemical arsenal when known records are available."
        self.add_button((320, 650, 210, 58), "Yes", self.choose_bgc_arsenal_yes, selected=active_choice is True, tooltip=arsenal_tip)
        self.add_button((670, 650, 210, 58), "No", lambda: self.choose_arsenal(False), selected=active_choice is False, tooltip=arsenal_tip)
        continue_label = f"LOCK PLAYER {setup_player} ARSENAL" if self.state.game_mode == TWO_PLAYERS else "Continue"
        self.add_button((450, 728, 300, 44), continue_label, self.confirm_arsenal_setup, enabled=active_choice is not None)

    def draw_arsenal_panel(self, title: str, entry: BacteriumCatalogEntry, rect: pygame.Rect, brings_arsenal: bool | None) -> None:
        pygame.draw.rect(self.screen, (10, 24, 38, 185), rect, border_radius=16)
        pygame.draw.rect(self.screen, (108, 231, 218), rect, 1, border_radius=16)
        x, y = rect.x + 14, rect.y + 12
        self.text(title.upper(), self.small, (255, 238, 133), topleft=(x, y))
        y += 25
        name = format_bacterial_name(entry.full_name)
        self.draw_scientific_name(name, x, y, self.font, max_width=rect.width - 28)
        y += 35
        status_color = THEME.muted if brings_arsenal is None else (146, 255, 167) if brings_arsenal and entry.accessions else (255, 238, 133)
        self.text(f"{len(entry.accessions)} known BGCs", self.font, (245, 250, 255), topleft=(x, y))
        status = "PENDING" if brings_arsenal is None else "ACTIVE" if brings_arsenal and entry.accessions else "INACTIVE"
        self.text(f"Arsenal {status}", self.small, status_color, topleft=(rect.right - 165, y + 4))
        y += 34
        bgcs = ", ".join(entry.accessions[:3]) or self.display_value(None, "arsenal", f"{entry.catalog_id}:arsenal-panel")
        if len(entry.accessions) > 3:
            bgcs += f"  +{len(entry.accessions) - 3} more"
        y = self.draw_wrapped(bgcs, pygame.Rect(x, y, rect.width - 28, 42), self.small, (245, 250, 255), 2) + 5
        self.text("Traits", self.small, (255, 238, 133), topleft=(x, y))
        y = self.draw_trait_chips(entry, x + 75, y, rect.width - 103, max_items=3)
        y = self.draw_labeled_chips("Products", entry.products, x, y, rect.width - 28, (50, 145, 175))
        y = self.draw_labeled_chips("Activities", entry.activities, x, y, rect.width - 28, (120, 100, 190))
        if y < rect.bottom - 60:
            self.text("Habitat", self.small, (255, 238, 133), topleft=(x, y))
            habitat = self.display_value(entry.isolation_habitat, "habitat", f"{entry.catalog_id}:arsenal-habitat")
            self.draw_wrapped(habitat, pygame.Rect(x + 82, y, rect.width - 110, rect.bottom - y - 12), self.small, (245, 250, 255), 2)

    def choose_bgc_arsenal_yes(self) -> None:
        self.choose_arsenal(True)
        if self.active_bgc_count(self.setup_fighter(), True) == 0:
            self.show_popup("No matched BGC arsenal appears in these records. The database is keeping this toolkit classified.")

    def choose_arsenal(self, active: bool) -> None:
        self.state.has_secretion = active
        if self.state.setup_player == 1:
            self.state.player1_arsenal_active = active
        else:
            self.state.player2_arsenal_active = active

    def confirm_arsenal_setup(self) -> None:
        choice = self.state.player1_arsenal_active if self.state.setup_player == 1 else self.state.player2_arsenal_active
        if choice is None:
            return
        if self.state.game_mode == TWO_PLAYERS and self.state.setup_player == 1:
            self.load_setup_player(2)
            self.show_popup("PLAYER 1 SETUP LOCKED · Player 2, configure your colony!", 1000)
            self.set_screen(COLONY_SELECTION)
            return
        if self.state.game_mode == TWO_PLAYERS:
            self.sync_setup_aliases()
        else:
            self.state.player1_arsenal_active = bool(self.state.has_secretion)
            self.state.player1_colony_cfu = self.state.colony_cfu
            self.state.player1_colony_score = self.state.colony_score
            self.state.player1_colony_label = self.state.colony_label
        self.set_screen(ENVIRONMENT_SELECTION)

    def active_bgc_count(self, entry: BacteriumCatalogEntry, brings_arsenal: bool) -> int:
        return len(entry.accessions) if entry and brings_arsenal else 0

    def show_popup(self, message: str, duration_ms=2800) -> None:
        self.state.popup_message = message
        self.state.popup_until = pygame.time.get_ticks() + duration_ms

    def draw_popup(self) -> None:
        if not self.state.popup_message or pygame.time.get_ticks() > self.state.popup_until:
            return
        rect = pygame.Rect(270, 40, 660, 70)
        surf = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(surf, (12, 30, 48, 235), surf.get_rect(), border_radius=18)
        pygame.draw.rect(surf, (255, 238, 133, 230), surf.get_rect(), 2, border_radius=18)
        self.screen.blit(surf, rect)
        self.draw_wrapped(self.state.popup_message, rect.inflate(-28, -20), self.small, (255, 255, 255))

    def draw_onboarding_tip(self, message: str, rect: pygame.Rect) -> None:
        if self.settings.onboarding_complete:
            return
        surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(surface, (*THEME.panel, 238), surface.get_rect(), border_radius=12)
        pygame.draw.rect(surface, (*THEME.yellow, 235), surface.get_rect(), 2, border_radius=12)
        self.screen.blit(surface, rect)
        self.draw_wrapped("TIP  " + message, rect.inflate(-14, -10), self.tiny, THEME.text, 2)

    def draw_tooltip(self) -> None:
        button = next((b for b in self.buttons if b.control_id == self.input.hovered_id and b.tooltip), None)
        if not button:
            return
        rect = pygame.Rect(330, 748, 540, 54)
        surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(surface, (*THEME.ink, 245), surface.get_rect(), border_radius=12)
        pygame.draw.rect(surface, (*THEME.yellow, 230), surface.get_rect(), 1, border_radius=12)
        self.screen.blit(surface, rect)
        self.draw_wrapped(button.tooltip, rect.inflate(-14, -9), self.tiny, THEME.text, 2)

    def draw_input_debug(self, virtual_mouse) -> None:
        hovered = self.input.hovered_id or "—"
        pressed = self.input.pressed_id or "—"
        focused = self.input.focused_id or "—"
        active = self.transition.active(pygame.time.get_ticks(), self.settings.reduced_motion)
        lines = [
            f"window {self.last_window_mouse}  virtual {virtual_mouse}",
            f"hover {hovered[:48]}", f"pressed {pressed[:48]}",
            f"focus {focused[:48]}", f"transition {active}",
        ]
        box = pygame.Rect(8, 8, 405, 92)
        pygame.draw.rect(self.screen, (0, 0, 0), box)
        for i, line in enumerate(lines):
            self.text(line, self.tiny, THEME.yellow, topleft=(14, 12 + i * 16))

    def draw_bacterium_sprite(self, entry: BacteriumCatalogEntry, pos, scale=1.0, facing=1, phase=0.0, state="idle") -> None:
        """Draw an original procedural fighter; catalog values remain untouched."""
        visual = fighter_visual(entry)
        idle_motion = 0 if self.settings.reduced_motion else math.sin(phase) * 5 * scale
        if state == "victory" and not self.settings.reduced_motion:
            idle_motion -= abs(math.sin(phase * 1.7)) * 18 * scale
        if state == "defeat":
            idle_motion += 26 * scale
            scale *= .86
        x, y = int(pos[0]), int(pos[1] + idle_motion)
        radius = max(7, int(48 * scale))
        primary, secondary, accent = visual.primary, visual.secondary, visual.accent
        if state == "hit":
            primary = tuple(min(255, c + 90) for c in primary)
        if state == "ability":
            for ring in range(3, 0, -1):
                pygame.draw.circle(self.screen, accent, (x, y), radius + ring * 12, max(1, ring))
        # Appendages sit behind the cell body.
        if visual.has_flagella:
            points = [(x - facing * radius, y + radius // 3)]
            for i in range(1, 6):
                points.append((x - facing * (radius + i * radius // 2), y + int(math.sin(phase * 2 + i) * radius * .35)))
            pygame.draw.aalines(self.screen, accent, False, points, max(1, int(2 * scale)))
        if visual.has_pili and scale > .35:
            for i in range(7):
                angle = i * math.tau / 7 + .2
                start = (x + int(math.cos(angle) * radius * .75), y + int(math.sin(angle) * radius * .75))
                end = (x + int(math.cos(angle) * radius * 1.15), y + int(math.sin(angle) * radius * 1.15))
                pygame.draw.line(self.screen, secondary, start, end, max(1, int(2 * scale)))
        if visual.morphology == "coccus":
            offsets = ((-22, -12), (15, -18), (24, 16), (-15, 20), (0, 0))
            for ox, oy in offsets:
                pygame.draw.circle(self.screen, primary, (x + int(ox * scale), y + int(oy * scale)), int(28 * scale))
                pygame.draw.circle(self.screen, secondary, (x + int(ox * scale), y + int(oy * scale)), int(28 * scale), max(1, int(3 * scale)))
        elif visual.morphology == "bacillus":
            body = pygame.Rect(0, 0, radius * 2, int(radius * 1.15)); body.center = (x, y)
            pygame.draw.rect(self.screen, primary, body, border_radius=body.height // 2)
            pygame.draw.rect(self.screen, secondary, body, max(1, int(4 * scale)), border_radius=body.height // 2)
        elif visual.morphology in {"spiral", "filamentous"}:
            points = []
            for i in range(15):
                px = x - radius + int(i * radius * 2 / 14)
                amp = radius * (.38 if visual.morphology == "spiral" else .22)
                py = y + int(math.sin(i * .9 + phase) * amp)
                points.append((px, py))
            pygame.draw.lines(self.screen, secondary, False, points, max(4, int(20 * scale)))
            pygame.draw.lines(self.screen, primary, False, points, max(3, int(14 * scale)))
        else:
            points = []
            for i in range(12):
                angle = i * math.tau / 12
                r = radius * (.78 + .2 * math.sin(i * 4.7))
                points.append((x + int(math.cos(angle) * r), y + int(math.sin(angle) * r)))
            pygame.draw.polygon(self.screen, primary, points)
            pygame.draw.lines(self.screen, secondary, True, points, max(1, int(4 * scale)))
        if visual.has_capsule:
            pygame.draw.ellipse(self.screen, (*accent, 80), (x - radius - 8, y - radius + 2, radius * 2 + 16, radius * 2 - 4), max(1, int(3 * scale)))
        if visual.has_spores:
            pygame.draw.circle(self.screen, accent, (x - facing * radius // 3, y), max(3, radius // 5))
        if state == "defend":
            shield = pygame.Rect(x - radius - 22, y - radius - 18, radius * 2 + 44, radius * 2 + 36)
            pygame.draw.arc(self.screen, THEME.cyan, shield, -.9, 2.1, max(3, int(6 * scale)))
        if state == "stunned":
            for i in range(3):
                sx = x - radius // 2 + i * radius // 2
                sy = y - radius - 18 - (i % 2) * 8
                pygame.draw.circle(self.screen, THEME.yellow, (sx, sy), max(2, int(4 * scale)))
        # A tiny expressive face gives procedural placeholders a shared identity.
        eye_y = y - max(2, radius // 7)
        eye_dx = max(3, radius // 4)
        for ex in (x - eye_dx, x + eye_dx):
            pygame.draw.circle(self.screen, THEME.ink, (ex, eye_y), max(1, int(3 * scale)))
        if scale > .45:
            mouth = (x - radius // 5, y, radius * 2 // 5, radius // 3)
            if state == "defeat":
                pygame.draw.arc(self.screen, THEME.ink, mouth, math.pi, math.tau, max(1, int(2 * scale)))
            else:
                pygame.draw.arc(self.screen, THEME.ink, mouth, 0, math.pi, max(1, int(2 * scale)))

    def draw_preview(self) -> None:
        arena = environment_visual(self.state.environment)
        age = max(0.0, (pygame.time.get_ticks() - self.state.transition_started) / 1000)
        if self.settings.reduced_motion:
            age = 2.0
        entry_progress = ease_out_cubic(age / .48)
        detail_progress = ease_out_cubic(max(0, age - .32) / .38)
        self.text(arena.title.upper(), self.tiny, arena.particle, center=(WIDTH // 2, 48))
        self.text("READY TO CULTURE CHAOS?", self.mid, THEME.text, center=(WIDTH // 2, 83))
        self.text(arena.subtitle, self.small, THEME.muted, center=(WIDTH // 2, 119))
        left_x = int(-440 + (85 + 440) * entry_progress)
        right_x = int(1220 + (695 - 1220) * entry_progress)
        left_label = "PLAYER 1" if self.state.game_mode == TWO_PLAYERS else "YOUR FIGHTER"
        right_label = "PLAYER 2" if self.state.game_mode == TWO_PLAYERS else "AUTOMATED RIVAL"
        self.draw_versus_fighter(self.state.player_entry, pygame.Rect(left_x, 155, 420, 455), left_label, self.state.player1_colony_cfu, self.state.player1_arsenal_active, 1, detail_progress)
        self.draw_versus_fighter(self.state.opponent_entry, pygame.Rect(right_x, 155, 420, 455), right_label, self.state.player2_colony_cfu, self.state.player2_arsenal_active, -1, detail_progress)
        impact = ease_out_cubic(max(0, age - .2) / .28)
        radius = max(1, int(58 * impact))
        pygame.draw.circle(self.screen, THEME.coral, (WIDTH // 2, 345), radius)
        if impact > .55:
            self.text("VS", self.mid, (255, 255, 255), center=(WIDTH // 2, 345))
        ready = age >= 1.05 and self.battle_setup_complete()
        self.add_button((460, 670, 280, 66), "ENTER THE ARENA", self.start_animation, enabled=ready)
        self.draw_onboarding_tip("Trait evidence, colony size, arsenal records, and arena conditions shape this showdown.", pygame.Rect(360, 748, 480, 48))

    def draw_versus_fighter(self, entry, rect, label, cfu, arsenal, facing, reveal=1.0) -> None:
        card = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(card, (*THEME.panel, 225), card.get_rect(), border_radius=24)
        pygame.draw.rect(card, (*THEME.cyan, 220), card.get_rect(), 2, border_radius=24)
        self.screen.blit(card, rect)
        self.text(label, self.tiny, THEME.yellow, center=(rect.centerx, rect.y + 28))
        self.draw_bacterium_sprite(entry, (rect.centerx, rect.y + 155), 1.15, facing=facing, phase=pygame.time.get_ticks() / 500)
        if reveal > .25:
            name = format_bacterial_name(entry.full_name)
            for i, line in enumerate(self.wrap(name.scientific, self.font_italic, rect.width - 50)[:2]):
                self.text(line, self.font_italic, THEME.text, center=(rect.centerx, rect.y + 260 + i * 26))
        if reveal > .55:
            visual = fighter_visual(entry)
            self.text(visual.epithet, self.small, THEME.mint, center=(rect.centerx, rect.y + 320))
            y = rect.y + 350
            y = self.draw_versus_stat("SPECIAL ABILITY", summary_ability(entry), rect, y, THEME.yellow)
            y = self.draw_versus_stat("COLONY SIZE", f"{cfu} CFU", rect, y, THEME.text)
            arsenal_status = summary_arsenal_status(entry, arsenal)
            self.draw_versus_stat("ARSENAL STATUS", arsenal_status, rect, y, THEME.text)

    def draw_versus_stat(self, label: str, value: str, rect: pygame.Rect, y: int, value_color) -> int:
        label_x = rect.x + 28
        value_x = rect.x + 175
        value_width = rect.right - value_x - 22
        self.text(label, self.tiny, THEME.muted, topleft=(label_x, y))
        font = self.tiny
        lines = self.wrap(value, font, value_width)
        size = max(9, round(14 * self.settings.text_scale))
        while (len(lines) > 2 or any(font.size(line)[0] > value_width for line in lines)) and size > 9:
            size -= 1
            font = pygame.font.Font(self.font_path, size)
            font.set_bold(True)
            lines = self.wrap(value, font, value_width)
        line_height = font.get_height() + 1
        for index, line in enumerate(lines):
            self.text(line, font, value_color, topleft=(value_x, y + index * line_height))
        return y + max(self.tiny.get_height(), len(lines) * line_height) + 7

    def start_animation(self) -> None:
        if not self.battle_setup_complete():
            self.show_popup("Battle setup is incomplete. Confirm both fighters, colony settings, arsenal choices, and the shared environment.")
            return
        self.set_screen(BATTLE_ANIMATION)
        self.state.animation_started = pygame.time.get_ticks()
        self.state.next_event_index = 0
        self.state.displayed_player_score = 0
        self.state.displayed_opponent_score = 0
        self.state.floating_texts = []
        self.state.battle_log = [f"Battle begins in the {environment_visual(self.state.environment).title}!"]
        self.state.battle_elapsed_seconds = 0.0
        self.state.battle_previous_seconds = 0.0
        cues = default_battle_cues(
            fighter_visual(self.state.player_entry).ability,
            fighter_visual(self.state.opponent_entry).ability,
            self.state.winner_flag,
        )
        self.battle_timeline = BattleTimeline(cues)
        if not self.settings.onboarding_complete:
            self.settings.onboarding_complete = True
            self.settings.save()

    def draw_animation(self, dt) -> None:
        now_ms = pygame.time.get_ticks()
        elapsed = max(0.0, (now_ms - self.state.animation_started) / 1000)
        timeline = self.battle_timeline
        if timeline is None:
            cues = default_battle_cues("Ability", "Ability", self.state.winner_flag)
            timeline = self.battle_timeline = BattleTimeline(cues)
        previous = self.state.battle_previous_seconds
        for cue in timeline.crossed(previous, elapsed):
            self.apply_battle_cue(cue, now_ms)
        self.state.battle_previous_seconds = elapsed
        self.state.battle_elapsed_seconds = elapsed
        cue = timeline.active_cue(elapsed)
        cue_age = elapsed - cue.at
        arena = environment_visual(self.state.environment)
        shake = 0
        if not self.settings.reduced_motion and cue.kind in {"attack", "counter", "ability", "finish"} and cue_age < .16:
            shake = int(math.sin(now_ms / 22) * 4)
        self.text(arena.title.upper(), self.tiny, arena.particle, center=(WIDTH // 2 + shake, 30))
        entrance = ease_out_cubic(min(1.0, elapsed / 1.0)) if not self.settings.reduced_motion else 1.0
        p_pos = [int(-130 + 480 * entrance), 365]
        o_pos = [int(1330 - 480 * entrance), 365]
        player_state, opponent_state = "idle", "idle"
        if cue.kind in {"attack", "counter", "ability", "finish"} and cue_age < .5:
            if cue.actor in {"player", "both"}:
                p_pos[0] += 0 if self.settings.reduced_motion else 42; player_state = "ability" if cue.kind == "ability" else "attack"
                opponent_state = "hit" if cue.kind != "finish" else "defeat"
            if cue.actor in {"opponent", "both"}:
                o_pos[0] -= 0 if self.settings.reduced_motion else 42; opponent_state = "ability" if cue.kind == "ability" else "attack"
                player_state = "hit" if cue.kind != "finish" else "defeat"
        elif cue.kind == "defend" and cue_age < .65:
            opponent_state = "defend"
        elif cue.kind == "dodge" and cue_age < .6:
            player_state = "dodge"; p_pos[0] -= 0 if self.settings.reduced_motion else 38
        elif cue.kind == "environment" and cue_age < .65:
            player_state = "stunned"
        elif cue.kind == "resolution":
            if self.state.winner_flag == "A": player_state, opponent_state = "victory", "defeat"
            elif self.state.winner_flag == "B": player_state, opponent_state = "defeat", "victory"
        if not self.settings.reduced_motion:
            p_pos[0] += int(math.sin(elapsed * 9.3) * 4); p_pos[1] += int(math.sin(elapsed * 7.1) * 3)
            o_pos[0] += int(math.sin(elapsed * 8.7 + 2) * 4); o_pos[1] += int(math.sin(elapsed * 6.8 + 1) * 3)
        p_pos[0] += shake; o_pos[0] += shake
        next_cue = next((future for future in timeline.cues if future.at > elapsed), None)
        if next_cue and next_cue.kind in {"attack", "counter", "ability", "finish"} and next_cue.at - elapsed < .3:
            actor_pos = p_pos if next_cue.actor == "player" else o_pos
            anticipation = 1 - (next_cue.at - elapsed) / .3
            radius = int(76 + anticipation * 25)
            pygame.draw.circle(self.screen, THEME.yellow, actor_pos, radius, 2)
        self.draw_bacterium_sprite(self.state.player_entry, p_pos, 1.42, 1, elapsed * 3, player_state)
        self.draw_bacterium_sprite(self.state.opponent_entry, o_pos, 1.42, -1, elapsed * 2.8, opponent_state)
        if cue.kind in {"attack", "counter", "ability", "finish"} and cue_age < .42 and cue.actor in {"player", "opponent"}:
            start, end = (p_pos, o_pos) if cue.actor == "player" else (o_pos, p_pos)
            color = fighter_visual(self.state.player_entry if cue.actor == "player" else self.state.opponent_entry).accent
            arc = {"attack": -55, "counter": 65, "ability": -105, "finish": -30}[cue.kind]
            if cue.actor == "opponent": arc *= -1
            path = quadratic_path(tuple(start), tuple(end), arc)
            travel = max(2, min(len(path), int(len(path) * cue_age / .42) + 2))
            visible = [(int(x), int(y)) for x, y in path[:travel]]
            pygame.draw.aalines(self.screen, color, False, visible)
            pygame.draw.lines(self.screen, color, False, visible, 5 if cue.kind != "finish" else 8)
            for i, point in enumerate(visible[-7:]):
                pygame.draw.circle(self.screen, color, point, 3 + i % 3)
        self.draw_battle_foreground(arena, elapsed, cue)
        player_hp, opponent_hp = timeline_health(timeline.progress(elapsed), self.state.winner_flag)
        player_label = "PLAYER 1" if self.state.game_mode == TWO_PLAYERS else "YOU"
        opponent_label = "PLAYER 2" if self.state.game_mode == TWO_PLAYERS else "RIVAL"
        self.draw_battle_hud(self.state.player_entry, pygame.Rect(55, 58, 440, 72), player_hp, player_label)
        self.draw_battle_hud(self.state.opponent_entry, pygame.Rect(705, 58, 440, 72), opponent_hp, opponent_label, right=True)
        now = pygame.time.get_ticks()
        for ft in self.state.floating_texts[:]:
            age = now - ft.born
            if age > ft.ttl:
                self.state.floating_texts.remove(ft)
                continue
            ft.pos.y -= 0.06 * dt
            label = ft.text if len(ft.text) <= 24 else ft.text[:21].rstrip() + "…"
            self.text(label, self.small, ft.color, center=(int(ft.pos.x), int(ft.pos.y)))
        log_rect = pygame.Rect(250, 600, 700, 104)
        log = pygame.Surface(log_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(log, (*THEME.panel, 215), log.get_rect(), border_radius=16)
        self.screen.blit(log, log_rect)
        for i, line in enumerate(self.state.battle_log[-3:]):
            self.text(line[:92], self.small, THEME.text if i == len(self.state.battle_log[-3:]) - 1 else THEME.muted, topleft=(log_rect.x + 18, log_rect.y + 14 + i * 27))
        self.add_button((1010, 735, 135, 42), "Skip", self.finish_animation, small=True, tooltip="Jump straight to the battle result.")
        self.text(f"{min(BATTLE_DURATION_SECONDS, elapsed):.1f} / {BATTLE_DURATION_SECONDS:.1f}s", self.tiny, THEME.muted, topleft=(55, 755))
        if timeline.complete(elapsed):
            self.finish_animation()

    def draw_battle_foreground(self, arena, elapsed: float, cue) -> None:
        seed = f"{self.state.battle_seed}:{arena.key}:foreground"
        particles = environment_particles(arena.key, seed, count=24)
        motion_time = animation_time(elapsed, self.settings.reduced_motion)
        for index, particle in enumerate(particles):
            x = int((particle.x + math.sin(motion_time * particle.speed + particle.phase) * .04) * WIDTH)
            y = int(430 + ((particle.y - motion_time * .045 * particle.speed) % 1) * 185)
            size = max(2, int(particle.size * 70))
            if arena.key == "In the presence of antibiotics":
                pygame.draw.line(self.screen, arena.particle, (x - size, y), (x + size, y), 2)
                pygame.draw.line(self.screen, arena.particle, (x, y - size), (x, y + size), 2)
            elif arena.key == "Cold":
                pygame.draw.circle(self.screen, arena.particle, (x, y), size, 1)
            elif arena.key == "Salty":
                pygame.draw.polygon(self.screen, arena.particle, [(x, y - size), (x + size, y), (x, y + size), (x - size, y)], 1)
            else:
                pygame.draw.circle(self.screen, arena.particle, (x, y), size, 1 if index % 2 else 2)
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        if arena.key == "Hot":
            for i in range(5):
                x = 120 + i * 250 + int(math.sin(motion_time + i) * 25)
                pygame.draw.arc(overlay, (*arena.particle, 65), (x, 430, 110, 180), 1.0, 2.3, 5)
        elif arena.key == "Cold":
            pygame.draw.rect(overlay, (205, 242, 255, 28), (0, 470, WIDTH, 135))
        elif arena.key == "In the presence of antibiotics":
            scan_y = 505 if self.settings.reduced_motion else int(455 + (elapsed * 48) % 135)
            pygame.draw.rect(overlay, (*arena.particle, 35), (0, scan_y, WIDTH, 12))
        elif arena.key == "Acidic":
            pygame.draw.rect(overlay, (196, 229, 65, 18), (0, 500, WIDTH, 115))
        if cue.kind == "finish" and 0 <= elapsed - cue.at < .55:
            for i in range(24):
                angle = i * math.tau / 24
                distance = 40 + (elapsed - cue.at) * 240
                x = WIDTH // 2 + int(math.cos(angle) * distance)
                y = 360 + int(math.sin(angle) * distance * .55)
                pygame.draw.circle(overlay, (*THEME.yellow, 190), (x, y), 4 + i % 4)
        self.screen.blit(overlay, (0, 0))

    def apply_battle_cue(self, cue, now_ms: int) -> None:
        self.state.displayed_player_score = self.state.player_score * cue.player_fraction
        self.state.displayed_opponent_score = self.state.opponent_score * cue.opponent_fraction
        actor = self.state.player_entry if cue.actor == "player" else self.state.opponent_entry if cue.actor == "opponent" else None
        if cue.kind == "environment":
            p_status = environment_status_label(self.state.player_breakdown.environment_status)
            o_status = environment_status_label(self.state.opponent_breakdown.environment_status)
            line = f"Arena pressure: you {p_status}; rival {o_status}."
        elif actor:
            line = f"{format_bacterial_name(actor.full_name).scientific}: {cue.text}."
        else:
            line = cue.text
        self.state.battle_log.append(line)
        self.state.battle_log = self.state.battle_log[-3:]
        if cue.target in {"player", "opponent"}:
            base_x = 380 if cue.target == "player" else 820
            pos = pygame.Vector2(base_x + ((self.state.next_event_index % 3) - 1) * 46, 288 - (self.state.next_event_index % 2) * 38)
            self.state.floating_texts.append(FloatingText(cue.text, pos, THEME.yellow, now_ms))
        self.state.next_event_index += 1
        arsenal_active = (
            self.state.player1_arsenal_active if cue.actor == "player"
            else self.state.player2_arsenal_active if cue.actor == "opponent"
            else False
        )
        self.audio.play_battle_cue(cue.kind, arsenal_active=bool(arsenal_active))

    def draw_battle_hud(self, entry, rect, hp, label, right=False) -> None:
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(panel, (*THEME.panel, 225), panel.get_rect(), border_radius=15)
        self.screen.blit(panel, rect)
        name = format_bacterial_name(entry.full_name).scientific
        self.text(f"{label}  {name[:34]}", self.small_italic, THEME.text, topleft=(rect.x + 14, rect.y + 10))
        bar = pygame.Rect(rect.x + 14, rect.y + 42, rect.width - 72, 15)
        pygame.draw.rect(self.screen, (48, 60, 70), bar, border_radius=8)
        fill = bar.copy(); fill.width = int(bar.width * hp / 100)
        pygame.draw.rect(self.screen, THEME.mint if hp > 35 else THEME.coral, fill, border_radius=8)
        self.text(f"{hp}", self.tiny, THEME.text, topleft=(bar.right + 10, bar.y - 1))

    def finish_animation(self) -> None:
        if self.state.screen != BATTLE_ANIMATION:
            return
        self.state.displayed_player_score = self.state.player_score
        self.state.displayed_opponent_score = self.state.opponent_score
        self.set_screen(RESULTS)

    def draw_microbe(self, pos, color, name, score, max_score) -> None:
        pygame.draw.circle(self.screen, color, pos, 58)
        for angle in range(0, 360, 45):
            end = (pos[0] + int(math.cos(math.radians(angle)) * 78), pos[1] + int(math.sin(math.radians(angle)) * 78))
            pygame.draw.line(self.screen, color, pos, end, 4)
        lines = self.wrap(sanitize_designation(name), self.small_italic, 230)[:2]
        for index, line in enumerate(lines):
            self.text(line, self.small_italic, (245, 250, 255), center=(pos[0], pos[1] + 90 + index * 20))
        bar = pygame.Rect(pos[0] - 90, pos[1] + 120, 180, 16)
        pygame.draw.rect(self.screen, (45, 55, 70), bar, border_radius=8)
        denom = max(abs(max_score), 1)
        fill = bar.copy(); fill.width = int(bar.width * min(1, abs(score) / denom))
        pygame.draw.rect(self.screen, (146, 255, 167), fill, border_radius=8)
        self.text(f"Score {score:.1f}", self.small, (245, 250, 255), center=(pos[0], pos[1] + 154))

    def draw_results(self) -> None:
        self.panel((45, 25, 1110, 770))
        age = max(0.0, (pygame.time.get_ticks() - self.state.results_started) / 1000)
        if self.settings.reduced_motion:
            age = 3.0
        headline = self.result_headline()
        category, flavor = result_message(
            self.state.player_score, self.state.opponent_score, self.state.winner_flag,
            self.flavor, str(self.state.battle_seed),
        )
        if age >= .08:
            bounce = 0 if self.settings.reduced_motion else int(abs(math.sin(age * 5)) * max(0, 10 - age * 8))
            color = THEME.mint if self.state.winner_flag == "A" else THEME.coral if self.state.winner_flag == "B" else THEME.yellow
            self.text(headline, self.big, (25, 56, 60), center=(WIDTH // 2 + 4, 69 + bounce))
            self.text(headline, self.big, color, center=(WIDTH // 2, 65 + bounce))
        if age >= .18:
            self.text(flavor, self.font, THEME.yellow, center=(WIDTH // 2, 115))
        if age >= .28:
            if self.state.winner_flag == "tie":
                self.text("Evenly matched!", self.small, THEME.text, center=(WIDTH // 2, 148))
            else:
                winner = self.state.player_entry if self.state.winner_flag == "A" else self.state.opponent_entry
                self.draw_winner_heading(format_bacterial_name(winner.full_name), 141)
            self.draw_bacterium_sprite(self.state.player_entry, (150, 142), .5, 1, age * 4, "victory" if self.state.winner_flag == "A" else "defeat")
            self.draw_bacterium_sprite(self.state.opponent_entry, (1050, 142), .5, -1, age * 4, "victory" if self.state.winner_flag == "B" else "defeat")
        if age >= .42:
            count = ease_out_cubic(min(1, (age - .42) / .6))
            left = "Player 1" if self.state.game_mode == TWO_PLAYERS else "You"
            right = "Player 2" if self.state.game_mode == TWO_PLAYERS else "Automated Rival"
            self.text(f"{left} {self.state.player_score * count:.1f}  vs  {right} {self.state.opponent_score * count:.1f}", self.font, THEME.text, center=(WIDTH // 2, 195))
        card_progress = ease_out_cubic(max(0, age - .58) / .38)
        if card_progress > 0:
            offset = int(36 * (1 - card_progress))
            player_rect = pygame.Rect(75, 225 + offset, 500, 292)
            opp_rect = pygame.Rect(625, 225 + offset, 500, 292)
            left_card = "Player 1" if self.state.game_mode == TWO_PLAYERS else "Player 1"
            right_card = "Player 2" if self.state.game_mode == TWO_PLAYERS else "Automated Rival"
            self.draw_score_card(left_card, self.state.player_breakdown, player_rect)
            self.draw_score_card(right_card, self.state.opponent_breakdown, opp_rect)
        info_rect = pygame.Rect(85, 528, 1030, 135)
        if age >= .92:
            info_progress = ease_out_cubic(min(1, (age - .92) / .35))
            info_rect.y += int(24 * (1 - info_progress))
            pygame.draw.rect(self.screen, (10, 24, 38, 185), info_rect, border_radius=14)
            pygame.draw.rect(self.screen, (108, 231, 218), info_rect, 1, border_radius=14)
            self.draw_biological_note(info_rect.inflate(-20, -12))
        if age >= 1.15:
            self.add_button((205, 680, 225, 62), "REMATCH", self.rematch)
            self.add_button((485, 680, 230, 62), "CHANGE FIGHTERS", self.change_fighter, small=True)
            self.add_button((770, 680, 225, 62), "MAIN MENU", self.main_menu, small=True)

    def result_headline(self) -> str:
        if self.state.game_mode == TWO_PLAYERS:
            return "PLAYER 1 WINS!" if self.state.winner_flag == "A" else "PLAYER 2 WINS!" if self.state.winner_flag == "B" else "TIE!"
        return "VICTORY!" if self.state.winner_flag == "A" else "DEFEAT!" if self.state.winner_flag == "B" else "TIE!"

    def rematch(self) -> None:
        if not self.state.player1_fighter or not self.state.player2_fighter:
            return
        self.state.player_entry = self.state.player1_fighter
        self.state.opponent_entry = self.state.player2_fighter
        self.state.battle_seed = random.randrange(1_000_000)
        if self.state.game_mode == TWO_PLAYERS:
            self.sync_setup_aliases()
        else:
            self.state.opponent_colony_cfu = generate_opponent_cfu(self.state.battle_seed)
            self.state.opponent_colony_score, self.state.player2_colony_label = colony_growth_score(self.state.opponent_colony_cfu)
            self.state.player2_colony_cfu = self.state.opponent_colony_cfu
            self.state.player2_colony_score = self.state.opponent_colony_score
        calculate_battle(self.state)
        self.start_animation()

    def change_fighter(self) -> None:
        mode = self.state.game_mode
        reset_for_new_game(self.state)
        self.state.game_mode = mode
        self.state.active_player = 1
        self.refresh_catalog_choices()
        self.set_screen(FIGHTER_SELECTION)

    def draw_score_card(self, label: str, breakdown: ScoreBreakdown, rect: pygame.Rect) -> None:
        pygame.draw.rect(self.screen, (10, 24, 38, 185), rect, border_radius=16)
        winner_card = (label == "Player 1" and self.state.winner_flag == "A") or (label in {"Player 2", "Automated Rival"} and self.state.winner_flag == "B")
        pygame.draw.rect(self.screen, THEME.yellow if winner_card else (108, 231, 218), rect, 3 if winner_card else 1, border_radius=16)
        x, y = rect.x + 14, rect.y + 12
        label_rect = self.text(label.upper(), self.small, (146, 255, 167), topleft=(x, y))
        name = format_bacterial_name(breakdown.fighter_name)
        name_x = label_rect.right + 18
        self.draw_scientific_name(name, name_x, y, self.small, (146, 255, 167), rect.right - name_x - 14)
        y += 30
        for component in breakdown.components:
            if component.name == "Base":
                continue
            value = f"{component.value:+.1f}"
            self.text(component.name, self.small, (245, 250, 255), topleft=(x, y))
            self.text(value, self.small, (255, 238, 133), topleft=(rect.right - 70, y))
            y += 22
        self.text(f"Final score: {breakdown.total:.1f}", self.font, (255, 238, 133), topleft=(x, rect.bottom - 34))

    def draw_score_breakdown(self, label: str, breakdown: ScoreBreakdown, x: int, y: int) -> None:
        self.text(f"{label}:", self.small, (146, 255, 167), topleft=(x, y))
        self.draw_scientific_name(format_bacterial_name(breakdown.fighter_name), x + 95, y, self.small, (146, 255, 167), 300)
        y += 24
        self.text(f"Colony size: {breakdown.colony_cfu} CFU", self.small, (255, 238, 133), topleft=(x, y))
        y += 22
        for component in breakdown.components:
            self.text(f"{component.value:+.1f} {component.name}", self.small, (245, 250, 255), topleft=(x, y))
            y += 22

    def evidence_summary(self, player: BacteriumCatalogEntry, opponent: BacteriumCatalogEntry) -> str:
        def one(entry: BacteriumCatalogEntry) -> str:
            accessions = ", ".join(entry.accessions[:4])
            traits = entry.trait_summary()
            return f"{format_bacterial_name(entry.full_name).plain}: {traits}; MIBiG {accessions}. {sanitize_designation(entry.description)}"
        return one(player) + " " + one(opponent)

    def biological_result_summary(self) -> str:
        winner = self.state.player_entry if self.state.winner_flag == "A" else self.state.opponent_entry if self.state.winner_flag == "B" else self.state.player_entry
        product = self.display_value(winner.products[0] if winner.products else None, "activity", f"{winner.catalog_id}:result-product").rstrip(".")
        activity = self.display_value(winner.activities[0] if winner.activities else None, "activity", f"{winner.catalog_id}:result-activity").rstrip(".")
        name = format_bacterial_name(winner.full_name)
        authority = f" ({name.expanded_details})" if name.expanded_details else ""
        fact = self.display_value(winner.curious_fact, "result", f"{winner.catalog_id}:result-fact").rstrip(".")
        return sanitize_designation(f"Bio note: {name.scientific}{authority} has {len(winner.accessions)} known BGC(s). Product/activity records: {product}; {activity}. {fact}") + "."

    def draw_biological_note(self, rect: pygame.Rect) -> None:
        winner = self.state.player_entry if self.state.winner_flag != "B" else self.state.opponent_entry
        name = format_bacterial_name(winner.full_name)
        x = self.text("Bio note: ", self.small, (255, 238, 133), topleft=(rect.x, rect.y)).right
        x = self.text(name.scientific, self.small_italic, (245, 250, 255), topleft=(x, rect.y)).right
        if name.authority and x + self.small.size(f" — {name.authority}")[0] < rect.right:
            self.text(f" — {name.authority}", self.small, (245, 250, 255), topleft=(x, rect.y))
        winner_breakdown = self.state.player_breakdown if self.state.winner_flag != "B" else self.state.opponent_breakdown
        colony_label = colony_growth_score(winner_breakdown.colony_cfu)[1]
        arena_line = environment_result_flavor(self.state.environment)
        missing_detail = not winner.products or not winner.activities or is_missing(winner.curious_fact)
        if missing_detail:
            known = sanitize_designation(winner.products[0]) if winner.products else sanitize_designation(winner.activities[0]) if winner.activities else ""
            known_line = f" Available record: {known}." if known else ""
            body = f"{len(winner.accessions)} known BGC(s).{known_line} {arena_line} Winner colony: {winner_breakdown.colony_cfu} CFU ({colony_label}). Some biological details remain unresolved. That is why we need more research."
        else:
            product = sanitize_designation(winner.products[0])
            activity = sanitize_designation(winner.activities[0])
            body = f"{len(winner.accessions)} known BGC(s). Product/activity record: {product}; {activity}. {sanitize_designation(winner.curious_fact)} {arena_line} Winner colony: {winner_breakdown.colony_cfu} CFU ({colony_label})."
        self.draw_wrapped(body, pygame.Rect(rect.x, rect.y + 26, rect.width, rect.height - 26), self.tiny, (245, 250, 255), 2)

    def draw_buttons(self, mouse) -> None:
        self.input.update_hover(self.buttons, mouse)
        now = pygame.time.get_ticks() / 1000
        for b in self.buttons:
            hovered = b.enabled and b.rect.collidepoint(mouse)
            pressed = hovered and self.input.pressed_id == b.control_id
            if b.style == "card":
                if hovered or pressed or self.input.focused_id == b.control_id:
                    color = THEME.yellow if self.input.focused_id == b.control_id else THEME.mint
                    pygame.draw.rect(self.screen, color, b.rect.inflate(6, 6), 4 if pressed else 2, border_radius=20)
                continue
            if not b.enabled:
                color = (80, 90, 105)
            elif b.selected:
                pulse = 0 if self.settings.reduced_motion else int((math.sin(now * 4) + 1) * 12)
                color = (255, 100 + pulse, 155 + pulse // 2)
            elif hovered:
                color = (70, 200, 190)
            else:
                color = (38, 120, 150)
            shadow = b.rect.move(0, 4)
            pygame.draw.rect(self.screen, (5, 12, 20), shadow, border_radius=16)
            button_rect = b.rect.move(0, 2 if pressed else 0)
            pygame.draw.rect(self.screen, color, button_rect, border_radius=16)
            border = THEME.yellow if self.settings.high_contrast else (235, 250, 255)
            pygame.draw.rect(self.screen, border, button_rect, 3 if self.settings.high_contrast else 2, border_radius=16)
            if self.input.focused_id == b.control_id and b.enabled:
                pygame.draw.rect(self.screen, THEME.yellow, button_rect.inflate(8, 8), 3, border_radius=20)
            if b.bacterial_name:
                name = b.bacterial_name
                scientific = name.scientific
                secondary = b.secondary_text or name.short_secondary
                name_x = b.rect.centerx + (20 if b.fighter else 0)
                if b.fighter:
                    previous_clip = self.screen.get_clip()
                    self.screen.set_clip(button_rect)
                    self.draw_bacterium_sprite(b.fighter, (button_rect.x + 30, button_rect.centery), .25, phase=pygame.time.get_ticks() / 600)
                    self.screen.set_clip(previous_clip)
                self.text(scientific, self.small_italic, (255, 255, 255), center=(name_x, b.rect.centery - (8 if secondary else 0)))
                if secondary:
                    if self.small.size(secondary)[0] > b.rect.width - 24:
                        secondary = secondary[:42].rstrip() + "…"
                    self.text(secondary, self.tiny, (229, 242, 247), center=(name_x, b.rect.centery + 11))
                continue
            font = self.small if b.small or len(b.text) > 28 or self.font.size(b.text)[0] > b.rect.width - 18 else self.font
            if len(self.wrap(b.text, font, b.rect.width - 18)) > 1 and font.get_height() * 2 > b.rect.height - 8:
                font = self.tiny
            for i, line in enumerate(self.wrap(b.text, font, b.rect.width - 18)[:2]):
                y = b.rect.centery - (font.get_height() * (1 if len(self.wrap(b.text, font, b.rect.width - 18)) > 1 else 0) // 2) + i * font.get_height()
                self.text(line, font, (255, 255, 255), center=(b.rect.centerx, y))

    def set_screen(self, screen: str) -> None:
        self.state.screen = screen
        self.state.transition_started = pygame.time.get_ticks()
        phase = "battle" if screen == BATTLE_ANIMATION else "results" if screen == RESULTS else "setup"
        accent = None
        if screen == RESULTS:
            accent = "victory" if self.state.winner_flag == "A" else "defeat" if self.state.winner_flag == "B" else "clash"
        self.audio.set_phase(phase, self.state.transition_started, accent=accent)
        self.transition.start(self.state.transition_started)
        self.input.cancel_press()
        self.input.focused_id = None
        self.input.last_activation_id = None
        self.buttons = []
        if screen == RESULTS:
            self.state.results_started = self.state.transition_started

    def quit(self) -> None:
        pygame.event.post(pygame.event.Event(pygame.QUIT))


def main() -> None:
    MicrobialMayhemGUI().run()


if __name__ == "__main__":
    main()
