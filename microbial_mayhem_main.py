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

import pygame

from bacterial_catalog import BacteriumCatalogEntry, bgc_summary, choose_opponent, get_catalog, sample_catalog, search_catalog
from colony_scoring import colony_growth_score, generate_opponent_cfu
from environment_icons import ENVIRONMENT_ICONS
from gui_helpers import pluralize, wrap_text
from scoring import ScoreBreakdown, score_battle

SCRIPT_DIR = Path(__file__).resolve().parent
WIDTH, HEIGHT = 1000, 720
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

ENVIRONMENTS = ["Salty", "Alkaline", "Hot", "Cold", "Acidic", "In the presence of antibiotics"]


@dataclass
class Button:
    rect: pygame.Rect
    text: str
    action: Callable[[], None]
    selected: bool = False
    enabled: bool = True
    small: bool = False


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
    animation_started: int = 0
    animation_events: list[dict] = field(default_factory=list)
    next_event_index: int = 0
    displayed_player_score: float = 0.0
    displayed_opponent_score: float = 0.0
    floating_texts: list[FloatingText] = field(default_factory=list)


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
    state.result_text = ""
    state.selected_catalog_entry = None
    state.search_query = ""
    state.search_message = ""
    state.scroll_offset = 0
    state.animation_events.clear()
    state.floating_texts.clear()


class MicrobialMayhemGUI:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Microbial Mayhem")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 30)
        self.big = pygame.font.Font(None, 72)
        self.mid = pygame.font.Font(None, 42)
        self.small = pygame.font.Font(None, 24)
        self.state = GameState()
        self.catalog = list(get_catalog())
        self.refresh_catalog_choices()
        self.buttons: list[Button] = []
        self.slider_rect = pygame.Rect(230, 340, 540, 12)
        self.dragging_slider = False
        self.background = self.load_background()

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
        while running:
            dt = self.clock.tick(FPS)
            mouse = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                else:
                    self.handle_event(event)
            self.draw(mouse, dt)
            pygame.display.flip()
        pygame.quit()

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.state.screen == FIGHTER_SELECTION and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.state.search_query = self.state.search_query[:-1]
            elif event.key == pygame.K_RETURN:
                self.apply_search()
            elif event.unicode and event.unicode.isprintable():
                self.state.search_query += event.unicode
            return
        if self.state.screen == FIGHTER_SELECTION and event.type == pygame.MOUSEWHEEL:
            max_offset = max(0, len(self.state.catalog_choices) - 10)
            self.state.scroll_offset = max(0, min(max_offset, self.state.scroll_offset - event.y))
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.state.screen == COLONY_SELECTION and self.slider_hit(event.pos):
                self.dragging_slider = True
                self.update_slider(event.pos[0])
                return
            for button in self.buttons:
                if button.enabled and button.rect.collidepoint(event.pos):
                    button.action()
                    return
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging_slider = False
        if event.type == pygame.MOUSEMOTION and self.dragging_slider:
            self.update_slider(event.pos[0])

    def refresh_catalog_choices(self) -> None:
        self.state.catalog_choices = sample_catalog(10, catalog=self.catalog)
        self.state.selected_catalog_entry = None
        self.state.scroll_offset = 0
        self.state.search_message = f"Showing {len(self.state.catalog_choices)} random database-derived bacteria."

    def apply_search(self) -> None:
        results = search_catalog(self.state.search_query, self.catalog)
        self.state.catalog_choices = results
        self.state.selected_catalog_entry = results[0] if results else None
        self.state.scroll_offset = 0
        if results:
            self.state.search_message = f"Found {len(results)} match(es) for '{self.state.search_query}'."
        else:
            self.state.search_message = f"No bacteria matched '{self.state.search_query}'. Try a genus, species, or strain."

    def confirm_fighter(self) -> None:
        if self.state.selected_catalog_entry:
            self.state.player_entry = self.state.selected_catalog_entry
            self.set_screen(COLONY_SELECTION)

    def slider_hit(self, pos: tuple[int, int]) -> bool:
        return self.slider_rect.inflate(30, 34).collidepoint(pos)

    def update_slider(self, x: int) -> None:
        ratio = max(0, min(1, (x - self.slider_rect.left) / self.slider_rect.width))
        self.state.colony_cfu = int(round(ratio * 1000))
        self.state.colony_score, self.state.colony_label = colony_growth_score(self.state.colony_cfu)

    def add_button(self, rect, text, action, selected=False, enabled=True, small=False) -> None:
        self.buttons.append(Button(pygame.Rect(rect), text, action, selected, enabled, small))

    def draw(self, mouse, dt) -> None:
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
            self.draw_choice_grid("Choose the fighting environment", [(e, e) for e in ENVIRONMENTS], "environment", ENVIRONMENT_SELECTION)
        elif self.state.screen == BATTLE_PREVIEW:
            self.draw_preview()
        elif self.state.screen == BATTLE_ANIMATION:
            self.draw_animation(dt)
        elif self.state.screen == RESULTS:
            self.draw_results()
        self.draw_popup()
        self.draw_buttons(mouse)

    def draw_background(self) -> None:
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

    def wrap(self, text: str, font, width: int) -> list[str]:
        return wrap_text(text, width, lambda candidate: font.size(candidate)[0])

    def draw_wrapped(self, text: str, rect, font, color, line_gap=4) -> int:
        y = rect.top
        for line in self.wrap(text, font, rect.width):
            self.text(line, font, color, topleft=(rect.left, y))
            y += font.get_height() + line_gap
            if y > rect.bottom - font.get_height():
                break
        return y

    def draw_welcome(self) -> None:
        self.panel((135, 105, 730, 470))
        self.text("MICROBIAL MAYHEM", self.big, (146, 255, 167), center=(WIDTH // 2, 205))
        msg = "Build a tiny champion, pick an extreme arena, and battle a surprise microbial opponent in a colorful science showdown."
        self.draw_wrapped(msg, pygame.Rect(220, 285, 560, 145), self.font, (245, 250, 255), line_gap=8)
        self.add_button((380, 455, 240, 68), "Start Game", lambda: self.set_screen(FIGHTER_SELECTION))

    def draw_fighter_selection(self) -> None:
        self.panel((35, 35, 930, 650))
        self.text("Choose a MIBiG bacterial fighter", self.mid, (255, 238, 133), center=(WIDTH // 2, 70))
        search_rect = pygame.Rect(70, 105, 360, 40)
        pygame.draw.rect(self.screen, (245, 250, 255), search_rect, border_radius=10)
        query = self.state.search_query or "Search scientific name, genus, or strain..."
        color = (20, 32, 45) if self.state.search_query else (105, 115, 125)
        self.text(query[:34], self.small, color, topleft=(search_rect.x + 12, search_rect.y + 11))
        self.add_button((445, 103, 105, 44), "Search", self.apply_search, small=True)
        self.add_button((565, 103, 235, 44), "Show 10 Different Bacteria", self.refresh_catalog_choices, small=True)
        self.text(self.state.search_message, self.small, (245, 250, 255), topleft=(70, 153))

        list_panel = pygame.Rect(70, 185, 505, 420)
        info_panel = pygame.Rect(600, 185, 330, 420)
        pygame.draw.rect(self.screen, (10, 24, 38, 170), list_panel, border_radius=14)
        pygame.draw.rect(self.screen, (10, 24, 38, 190), info_panel, border_radius=14)
        pygame.draw.rect(self.screen, (108, 231, 218), list_panel, 1, border_radius=14)
        pygame.draw.rect(self.screen, (108, 231, 218), info_panel, 1, border_radius=14)

        list_top = list_panel.y + 12
        visible = self.state.catalog_choices[self.state.scroll_offset:self.state.scroll_offset + 10]
        for idx, entry in enumerate(visible):
            y = list_top + idx * 39
            label = f"{entry.full_name}"
            selected = self.state.selected_catalog_entry and entry.catalog_id == self.state.selected_catalog_entry.catalog_id
            self.add_button((82, y, 480, 34), label, lambda e=entry: setattr(self.state, "selected_catalog_entry", e), selected=selected, small=True)
        if len(self.state.catalog_choices) > 10:
            track = pygame.Rect(565, list_panel.y + 12, 8, 392)
            pygame.draw.rect(self.screen, (70, 90, 105), track, border_radius=6)
            thumb_h = max(35, int(track.height * 10 / len(self.state.catalog_choices)))
            max_offset = max(1, len(self.state.catalog_choices) - 10)
            thumb_y = track.y + int((track.height - thumb_h) * self.state.scroll_offset / max_offset)
            pygame.draw.rect(self.screen, (146, 255, 167), (track.x, thumb_y, track.width, thumb_h), border_radius=6)

        self.draw_selected_organism_card(info_panel)
        self.add_button((380, 620, 240, 48), "Confirm Fighter", self.confirm_fighter, enabled=self.state.selected_catalog_entry is not None)

    def draw_selected_organism_card(self, rect: pygame.Rect) -> None:
        clip_before = self.screen.get_clip()
        self.screen.set_clip(rect.inflate(-16, -16))
        x, y = rect.x + 14, rect.y + 14
        if not self.state.selected_catalog_entry:
            self.draw_wrapped("Select an organism from the list to view its MIBiG-backed identity, traits, biosynthetic products, colony metadata, and a curious fact.", pygame.Rect(x, y, rect.width - 28, rect.height - 28), self.small, (245, 250, 255))
            self.screen.set_clip(clip_before)
            return
        entry = self.state.selected_catalog_entry
        y = self.draw_wrapped(entry.full_name, pygame.Rect(x, y, rect.width - 28, 48), self.font, (146, 255, 167))
        lines = [
            f"Battle name: {entry.display_name}",
            f"Strain: {entry.strain or 'not specified'}",
            f"Taxonomy group: {entry.taxonomy_group}",
            bgc_summary(entry),
            f"MIBiG: {', '.join(entry.accessions[:4])}",
        ]
        for line in lines:
            self.text(line, self.small, (245, 250, 255), topleft=(x, y + 4))
            y += 22
        y += 4
        self.draw_trait_chips(entry, x, y, rect.width - 28)
        y += 58
        details = [
            f"Products: {', '.join(entry.products[:3]) or 'No named product available.'}",
            f"Compound classes: {', '.join(entry.compound_classes[:3]) or 'No compound class annotation available.'}",
            f"Activities: {', '.join(entry.activities[:3]) or 'No reported activity available.'}",
            f"Colony appearance: {entry.colony_appearance}",
            f"Curious fact: {entry.curious_fact}",
        ]
        self.draw_wrapped(" ".join(details), pygame.Rect(x, y, rect.width - 28, rect.bottom - y - 12), self.small, (245, 250, 255))
        self.screen.set_clip(clip_before)

    def draw_trait_chips(self, entry: BacteriumCatalogEntry, x: int, y: int, width: int) -> None:
        traits = entry.traits or []
        if not traits:
            self.text("Environmental traits unknown", self.small, (255, 238, 133), topleft=(x, y))
            return
        cx, cy = x, y
        for evidence in traits[:6]:
            label = evidence.trait if evidence.trait != "Antimicrobial production" else "Antimicrobial producer"
            chip_w = min(width, max(88, self.small.size(label)[0] + 18))
            if cx + chip_w > x + width:
                cx, cy = x, cy + 24
            color = (77, 160, 210) if evidence.evidence_level.startswith("Direct") else (120, 100, 190)
            pygame.draw.rect(self.screen, color, (cx, cy, chip_w, 20), border_radius=10)
            self.text(label, self.small, (255, 255, 255), center=(cx + chip_w // 2, cy + 10))
            cx += chip_w + 6

    def draw_choice_grid(self, title, choices, attr, screen_name) -> None:
        self.panel((70, 55, 860, 590))
        self.text(title, self.mid, (255, 238, 133), center=(WIDTH // 2, 105))
        for idx, (label, value) in enumerate(choices):
            col, row = idx % 2, idx // 2
            rect = (135 + col * 390, 160 + row * 82, 340, 58)
            button_label = f"{ENVIRONMENT_ICONS.get(value, '')}  {label}" if screen_name == ENVIRONMENT_SELECTION else label
            self.add_button(rect, button_label, lambda v=value: setattr(self.state, attr, v), getattr(self.state, attr) == value)
        selected = getattr(self.state, attr) is not None
        next_screen = {
            FIGHTER_SELECTION: COLONY_SELECTION,
            ENVIRONMENT_SELECTION: BATTLE_PREVIEW,
        }[screen_name]
        self.add_button((390, 585, 220, 54), "Continue", lambda: self.after_choice(next_screen), enabled=selected)

    def after_choice(self, next_screen: str) -> None:
        if next_screen == BATTLE_PREVIEW and self.state.opponent_entry is None:
            self.state.opponent_entry = choose_opponent(self.state.player_entry.catalog_id, catalog=self.catalog)
            self.state.battle_seed = random.randrange(1_000_000)
            self.state.opponent_colony_cfu = generate_opponent_cfu(self.state.battle_seed)
            self.state.opponent_colony_score, _ = colony_growth_score(self.state.opponent_colony_cfu)
            self.state.opponent_has_secretion = random.choice([True, False])
            calculate_battle(self.state)
        self.set_screen(next_screen)

    def draw_colony(self) -> None:
        self.panel((125, 95, 750, 510))
        self.text("Set colony size", self.mid, (255, 238, 133), center=(WIDTH // 2, 150))
        self.text(f"{self.state.colony_cfu} CFU", self.big, (146, 255, 167), center=(WIDTH // 2, 260))
        pygame.draw.rect(self.screen, (160, 180, 190), self.slider_rect, border_radius=8)
        knob_x = self.slider_rect.left + int(self.slider_rect.width * self.state.colony_cfu / 1000)
        pygame.draw.circle(self.screen, (255, 112, 166), (knob_x, self.slider_rect.centery), 20)
        self.text(f"{self.state.colony_label}  |  Score: {self.state.colony_score}", self.font, (245, 250, 255), center=(WIDTH // 2, 410))
        self.add_button((390, 505, 220, 54), "Continue", lambda: self.set_screen(SECRETION_SELECTION))

    def draw_secretion(self) -> None:
        self.panel((125, 95, 750, 510))
        self.text("Bring your BGC arsenal?", self.mid, (255, 238, 133), center=(WIDTH // 2, 150))
        msg = "Some bacteria carry biosynthetic gene clusters that can produce useful chemical weapons. Should your fighter bring its known arsenal into battle?"
        self.draw_wrapped(msg, pygame.Rect(220, 210, 560, 120), self.font, (245, 250, 255))
        self.add_button((245, 360, 210, 78), "Yes", self.choose_bgc_arsenal_yes, selected=self.state.has_secretion is True)
        self.add_button((545, 360, 210, 78), "No", lambda: setattr(self.state, "has_secretion", False), selected=self.state.has_secretion is False)
        self.add_button((390, 515, 220, 54), "Continue", lambda: self.set_screen(ENVIRONMENT_SELECTION), enabled=self.state.has_secretion is not None)

    def choose_bgc_arsenal_yes(self) -> None:
        self.state.has_secretion = True
        if self.active_bgc_count(self.state.player_entry, True) == 0:
            self.show_popup("Your fighter has no known BGC arsenal. Good luck—you’re fighting with the basics!")

    def active_bgc_count(self, entry: BacteriumCatalogEntry, brings_arsenal: bool) -> int:
        return len(entry.accessions) if entry and brings_arsenal else 0

    def show_popup(self, message: str) -> None:
        self.state.popup_message = message
        self.state.popup_until = pygame.time.get_ticks() + 2800

    def draw_popup(self) -> None:
        if not self.state.popup_message or pygame.time.get_ticks() > self.state.popup_until:
            return
        rect = pygame.Rect(170, 40, 660, 70)
        surf = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(surf, (12, 30, 48, 235), surf.get_rect(), border_radius=18)
        pygame.draw.rect(surf, (255, 238, 133, 230), surf.get_rect(), 2, border_radius=18)
        self.screen.blit(surf, rect)
        self.draw_wrapped(self.state.popup_message, rect.inflate(-28, -20), self.small, (255, 255, 255))

    def draw_preview(self) -> None:
        self.panel((105, 60, 790, 600))
        self.text("Battle preview", self.mid, (255, 238, 133), center=(WIDTH // 2, 110))
        rows = [
            ("Your microbe", self.state.player_entry.display_name),
            ("Opponent", self.state.opponent_entry.display_name),
            ("Environment", self.state.environment),
            ("Your colony", f"{self.state.colony_cfu} CFU ({self.state.colony_label}, +{self.state.colony_score:.1f})"),
            ("Opponent colony", f"{self.state.opponent_colony_cfu} CFU (+{self.state.opponent_colony_score:.1f})"),
            ("Your BGC arsenal", f"{'Yes' if self.state.has_secretion else 'No'} ({self.active_bgc_count(self.state.player_entry, bool(self.state.has_secretion))} active BGCs)"),
            ("Opponent BGC arsenal", f"{'Yes' if self.state.opponent_has_secretion else 'No'} ({self.active_bgc_count(self.state.opponent_entry, self.state.opponent_has_secretion)} active BGCs)"),
        ]
        y = 170
        for label, value in rows:
            self.text(f"{label}:", self.font, (146, 255, 167), topleft=(230, y))
            self.text(str(value), self.font, (245, 250, 255), topleft=(460, y))
            y += 48
        self.add_button((380, 560, 240, 68), "Battle!", self.start_animation)

    def start_animation(self) -> None:
        self.state.screen = BATTLE_ANIMATION
        self.state.animation_started = pygame.time.get_ticks()
        self.state.next_event_index = 0
        self.state.displayed_player_score = 0
        self.state.displayed_opponent_score = 0
        self.state.floating_texts = []
        events = []
        player_steps = [self.state.player_score * x for x in (0.25, 0.5, 0.75, 1.0)]
        opp_steps = [self.state.opponent_score * x for x in (0.25, 0.5, 0.75, 1.0)]
        for i in range(4):
            events.append({"time": 600 + i * 1050, "target": "opponent", "player": player_steps[i], "opponent": opp_steps[max(0, i - 1)], "text": f"+{player_steps[i] - (player_steps[i-1] if i else 0):.0f}"})
            events.append({"time": 1050 + i * 1050, "target": "player", "player": player_steps[i], "opponent": opp_steps[i], "text": "Critical Hit!" if i == 2 else f"+{opp_steps[i] - (opp_steps[i-1] if i else 0):.0f}"})
        self.state.animation_events = events

    def draw_animation(self, dt) -> None:
        elapsed = pygame.time.get_ticks() - self.state.animation_started
        shake = int(math.sin(elapsed / 45) * 5) if self.state.next_event_index < len(self.state.animation_events) else 0
        self.panel((55 + shake, 50, 890, 610), 205)
        self.text("MICROBIAL BATTLE!", self.mid, (255, 238, 133), center=(WIDTH // 2 + shake, 95))
        while self.state.next_event_index < len(self.state.animation_events) and elapsed >= self.state.animation_events[self.state.next_event_index]["time"]:
            ev = self.state.animation_events[self.state.next_event_index]
            self.state.displayed_player_score = ev["player"]
            self.state.displayed_opponent_score = ev["opponent"]
            pos = pygame.Vector2(710 if ev["target"] == "opponent" else 280, 300)
            self.state.floating_texts.append(FloatingText(ev["text"], pos, (255, 230, 120), pygame.time.get_ticks()))
            self.state.next_event_index += 1
        p_pos = (280 + int(math.sin(elapsed / 160) * 22), 330)
        o_pos = (720 - int(math.sin(elapsed / 170) * 22), 330)
        self.draw_microbe(p_pos, (77, 220, 146), self.state.player_entry.display_name, self.state.displayed_player_score, self.state.player_score)
        self.draw_microbe(o_pos, (255, 112, 166), self.state.opponent_entry.display_name, self.state.displayed_opponent_score, self.state.opponent_score)
        beam_color = (255, 245, 140) if (elapsed // 420) % 2 == 0 else (130, 240, 255)
        pygame.draw.line(self.screen, beam_color, p_pos, o_pos, 5)
        now = pygame.time.get_ticks()
        for ft in self.state.floating_texts[:]:
            age = now - ft.born
            if age > ft.ttl:
                self.state.floating_texts.remove(ft)
                continue
            ft.pos.y -= 0.06 * dt
            self.text(ft.text, self.font, ft.color, center=(int(ft.pos.x), int(ft.pos.y)))
        if elapsed >= 5200:
            self.state.displayed_player_score = self.state.player_score
            self.state.displayed_opponent_score = self.state.opponent_score
            self.state.screen = RESULTS

    def draw_microbe(self, pos, color, name, score, max_score) -> None:
        pygame.draw.circle(self.screen, color, pos, 58)
        for angle in range(0, 360, 45):
            end = (pos[0] + int(math.cos(math.radians(angle)) * 78), pos[1] + int(math.sin(math.radians(angle)) * 78))
            pygame.draw.line(self.screen, color, pos, end, 4)
        self.text(name, self.small, (245, 250, 255), center=(pos[0], pos[1] + 95))
        bar = pygame.Rect(pos[0] - 90, pos[1] + 120, 180, 16)
        pygame.draw.rect(self.screen, (45, 55, 70), bar, border_radius=8)
        denom = max(abs(max_score), 1)
        fill = bar.copy(); fill.width = int(bar.width * min(1, abs(score) / denom))
        pygame.draw.rect(self.screen, (146, 255, 167), fill, border_radius=8)
        self.text(f"Score {score:.1f}", self.small, (245, 250, 255), center=(pos[0], pos[1] + 154))

    def draw_results(self) -> None:
        self.panel((75, 45, 850, 630))
        headline = "VICTORY!" if self.state.winner_flag == "A" else "DEFEAT!" if self.state.winner_flag == "B" else "TIE!"
        self.text(headline, self.big, (146, 255, 167), center=(WIDTH // 2, 95))
        self.text(f"{self.state.winner_name[:42]} WINS!", self.mid, (255, 238, 133), center=(WIDTH // 2, 155))
        self.text(f"Final scores: You {self.state.player_score:.1f}  |  Opponent {self.state.opponent_score:.1f}", self.font, (245, 250, 255), center=(WIDTH // 2, 210))
        self.draw_score_breakdown("Player", self.state.player_breakdown, 120, 245)
        self.draw_score_breakdown("Opponent", self.state.opponent_breakdown, 540, 245)
        evidence = self.evidence_summary(self.state.player_entry, self.state.opponent_entry)
        self.draw_wrapped(evidence, pygame.Rect(120, 455, 760, 95), self.small, (245, 250, 255))
        self.add_button((260, 585, 200, 54), "Play Again", lambda: reset_for_new_game(self.state))
        self.add_button((540, 585, 200, 54), "Quit", self.quit)

    def draw_score_breakdown(self, label: str, breakdown: ScoreBreakdown, x: int, y: int) -> None:
        self.text(f"{label}: {breakdown.fighter_name[:26]}", self.small, (146, 255, 167), topleft=(x, y))
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
            return f"{entry.display_name}: {traits}; MIBiG {accessions}. {entry.description}"
        return one(player) + " " + one(opponent)

    def draw_buttons(self, mouse) -> None:
        for b in self.buttons:
            hovered = b.enabled and b.rect.collidepoint(mouse)
            if not b.enabled:
                color = (80, 90, 105)
            elif b.selected:
                color = (255, 112, 166)
            elif hovered:
                color = (70, 200, 190)
            else:
                color = (38, 120, 150)
            pygame.draw.rect(self.screen, color, b.rect, border_radius=16)
            pygame.draw.rect(self.screen, (235, 250, 255), b.rect, 2, border_radius=16)
            font = self.small if b.small or len(b.text) > 28 else self.font
            for i, line in enumerate(self.wrap(b.text, font, b.rect.width - 18)[:2]):
                y = b.rect.centery - (font.get_height() * (1 if len(self.wrap(b.text, font, b.rect.width - 18)) > 1 else 0) // 2) + i * font.get_height()
                self.text(line, font, (255, 255, 255), center=(b.rect.centerx, y))

    def set_screen(self, screen: str) -> None:
        self.state.screen = screen

    def quit(self) -> None:
        pygame.event.post(pygame.event.Event(pygame.QUIT))


def main() -> None:
    MicrobialMayhemGUI().run()


if __name__ == "__main__":
    main()
