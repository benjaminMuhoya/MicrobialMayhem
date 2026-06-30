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

from bacterial_names import BacterialName, format_bacterial_name, sanitize_designation
from bacterial_catalog import BacteriumCatalogEntry, bgc_summary, choose_opponent, get_catalog, sample_catalog, search_catalog
from colony_scoring import colony_growth_score, generate_opponent_cfu
from environment_icons import ENVIRONMENT_LABELS
from gui_helpers import pluralize, wrap_text
from scoring import ScoreBreakdown, score_battle

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
    show_all_bgcs: bool = False
    bgc_scroll: int = 0
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
    state.show_all_bgcs = False
    state.bgc_scroll = 0
    state.animation_events.clear()
    state.floating_texts.clear()


class MicrobialMayhemGUI:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Microbial Mayhem")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 30)
        self.big = pygame.font.Font(None, 72)
        self.mid = pygame.font.Font(None, 42)
        self.small = pygame.font.Font(None, 24)
        self.font_italic = pygame.font.Font(None, 30)
        self.font_italic.set_italic(True)
        self.small_italic = pygame.font.Font(None, 24)
        self.small_italic.set_italic(True)
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
                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((max(WIDTH, event.w), max(HEIGHT, event.h)), pygame.RESIZABLE)
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
            if self.state.show_all_bgcs and self.state.selected_catalog_entry:
                maximum = max(0, len(self.state.selected_catalog_entry.accessions) - 12)
                self.state.bgc_scroll = max(0, min(maximum, self.state.bgc_scroll - event.y))
                return
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
            self.state.search_message = f"No bacteria matched '{self.state.search_query}'. Try a genus, species, or strain."

    def confirm_fighter(self) -> None:
        if self.state.selected_catalog_entry:
            self.state.player_entry = self.state.selected_catalog_entry
            self.state.opponent_entry = choose_opponent(self.state.player_entry.catalog_id, catalog=self.catalog)
            self.state.opponent_has_secretion = random.choice([True, False])
            self.set_screen(COLONY_SELECTION)

    def select_catalog_entry(self, entry: BacteriumCatalogEntry) -> None:
        self.state.selected_catalog_entry = entry
        self.state.show_all_bgcs = False
        self.state.bgc_scroll = 0

    def slider_hit(self, pos: tuple[int, int]) -> bool:
        return self.slider_rect.inflate(30, 34).collidepoint(pos)

    def update_slider(self, x: int) -> None:
        ratio = max(0, min(1, (x - self.slider_rect.left) / self.slider_rect.width))
        self.state.colony_cfu = int(round(ratio * 1000))
        self.state.colony_score, self.state.colony_label = colony_growth_score(self.state.colony_cfu)

    def add_button(self, rect, text, action, selected=False, enabled=True, small=False) -> None:
        self.buttons.append(Button(pygame.Rect(rect), text, action, selected, enabled, small))

    def add_name_button(self, rect, name: BacterialName, action, selected=False, secondary_text="") -> None:
        self.buttons.append(Button(pygame.Rect(rect), name.plain, action, selected, True, True, name, secondary_text))

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

    def draw_wrapped(self, text: str, rect, font, color, line_gap=4) -> int:
        y = rect.top
        for line in self.wrap(text, font, rect.width):
            self.text(line, font, color, topleft=(rect.left, y))
            y += font.get_height() + line_gap
            if y > rect.bottom - font.get_height():
                break
        return y

    def draw_welcome(self) -> None:
        self.panel((235, 105, 730, 470))
        self.text("MICROBIAL MAYHEM", self.big, (146, 255, 167), center=(WIDTH // 2, 205))
        msg = "Build a tiny champion, pick an extreme arena, and battle a surprise microbial opponent in a colorful science showdown."
        self.draw_wrapped(msg, pygame.Rect(320, 285, 560, 145), self.font, (245, 250, 255), line_gap=8)
        if self.catalog_error:
            self.draw_wrapped(self.catalog_error, pygame.Rect(320, 390, 560, 80), self.small, (255, 238, 133))
        self.add_button((480, 485, 240, 68), "Start Game", lambda: self.set_screen(FIGHTER_SELECTION), enabled=not self.catalog_error)

    def draw_fighter_selection(self) -> None:
        self.panel((30, 25, 1140, 770))
        self.text(f"Choose a {self.catalog_source} bacterial fighter", self.mid, (255, 238, 133), center=(WIDTH // 2, 58))
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
            self.add_name_button((69, y, 410, 45), name, lambda e=entry: self.select_catalog_entry(e), selected=selected, secondary_text=secondary)
        if len(self.state.catalog_choices) > 10:
            track = pygame.Rect(486, list_panel.y + 14, 8, 520)
            pygame.draw.rect(self.screen, (70, 90, 105), track, border_radius=6)
            thumb_h = max(35, int(track.height * 10 / len(self.state.catalog_choices)))
            max_offset = max(1, len(self.state.catalog_choices) - 10)
            thumb_y = track.y + int((track.height - thumb_h) * self.state.scroll_offset / max_offset)
            pygame.draw.rect(self.screen, (146, 255, 167), (track.x, thumb_y, track.width, thumb_h), border_radius=6)

        self.draw_selected_organism_card(info_panel)
        self.add_button((480, 735, 240, 48), "Confirm Fighter", self.confirm_fighter, enabled=self.state.selected_catalog_entry is not None)

    def draw_selected_organism_card(self, rect: pygame.Rect) -> None:
        clip_before = self.screen.get_clip()
        self.screen.set_clip(rect.inflate(-16, -16))
        x, y = rect.x + 14, rect.y + 14
        if not self.state.selected_catalog_entry:
            self.draw_wrapped("Select an organism from the list to view its MIBiG-backed identity, traits, biosynthetic products, colony metadata, and a curious fact.", pygame.Rect(x, y, rect.width - 28, rect.height - 28), self.small, (245, 250, 255))
            self.screen.set_clip(clip_before)
            return
        entry = self.state.selected_catalog_entry
        name = format_bacterial_name(entry.full_name)
        self.text("SELECTED FIGHTER", self.small, (255, 238, 133), topleft=(x, y))
        y += 25
        self.draw_scientific_name(name, x, y, self.font, max_width=rect.width - 28)
        y += 31
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
        details = name.expanded_details or "No additional designation supplied"
        rows = [
            ("Designation", details),
            ("Strain", sanitize_designation(entry.strain) or "Not specified"),
            ("Taxonomy", sanitize_designation(entry.taxonomy_group)),
        ]
        for label, value in rows:
            self.text(label, self.small, (255, 238, 133), topleft=(x, y))
            y = self.draw_wrapped(value, pygame.Rect(x + 108, y, rect.width - 142, 42), self.small, (245, 250, 255), 2)
            y += 5

        count = len(entry.accessions)
        self.text("Known BGCs", self.small, (255, 238, 133), topleft=(x, y))
        self.text(str(count), self.font, (146, 255, 167), topleft=(x + 108, y - 3))
        preview = ", ".join(entry.accessions[:3]) or "No matched MIBiG BGCs"
        if count > 3:
            preview += f"  +{count - 3} more"
            self.add_button((rect.right - 165, rect.bottom - 43, 140, 30), "View all BGCs", lambda: setattr(self.state, "show_all_bgcs", True), small=True)
        y = self.draw_wrapped(preview, pygame.Rect(x + 150, y, rect.width - 184, 42), self.small, (245, 250, 255), 2) + 5

        y = self.draw_labeled_chips("Products", entry.products, x, y, rect.width - 28, (50, 145, 175))
        y = self.draw_labeled_chips("Activities", entry.activities, x, y, rect.width - 28, (120, 100, 190))
        sections = [
            ("Colony", entry.colony_appearance),
            ("Habitat", entry.isolation_habitat),
            ("Fun fact", entry.curious_fact),
        ]
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
            self.text("None reported", self.small, (245, 250, 255), topleft=(x + 108, y))
            return y + 25
        return self.draw_chips(labels, x + 108, y, width - 108, color, max_items=3, max_rows=2)

    def draw_trait_chips(self, entry: BacteriumCatalogEntry, x: int, y: int, width: int, max_items=4) -> int:
        labels = ["Antimicrobial producer" if evidence.trait == "Antimicrobial production" else evidence.trait for evidence in entry.traits]
        if not labels:
            self.text("Environmental traits unknown", self.small, (245, 250, 255), topleft=(x, y))
            return y + 25
        return self.draw_chips(labels, x, y, width, (120, 100, 190), max_items=max_items)

    def draw_choice_grid(self, title, choices, attr, screen_name) -> None:
        self.panel((170, 55, 860, 590))
        self.text(title, self.mid, (255, 238, 133), center=(WIDTH // 2, 105))
        for idx, (label, value) in enumerate(choices):
            col, row = idx % 2, idx // 2
            rect = (235 + col * 390, 160 + row * 82, 340, 58)
            button_label = ENVIRONMENT_LABELS[value] if screen_name == ENVIRONMENT_SELECTION else label
            self.add_button(rect, button_label, lambda v=value: setattr(self.state, attr, v), getattr(self.state, attr) == value)
        selected = getattr(self.state, attr) is not None
        next_screen = {
            FIGHTER_SELECTION: COLONY_SELECTION,
            ENVIRONMENT_SELECTION: BATTLE_PREVIEW,
        }[screen_name]
        self.add_button((490, 585, 220, 54), "Continue", lambda: self.after_choice(next_screen), enabled=selected)

    def after_choice(self, next_screen: str) -> None:
        if next_screen == BATTLE_PREVIEW and self.state.player_breakdown is None:
            if self.state.opponent_entry is None:
                self.state.opponent_entry = choose_opponent(self.state.player_entry.catalog_id, catalog=self.catalog)
                self.state.opponent_has_secretion = random.choice([True, False])
            self.state.battle_seed = random.randrange(1_000_000)
            self.state.opponent_colony_cfu = generate_opponent_cfu(self.state.battle_seed)
            self.state.opponent_colony_score, _ = colony_growth_score(self.state.opponent_colony_cfu)
            calculate_battle(self.state)
        self.set_screen(next_screen)

    def draw_colony(self) -> None:
        self.panel((225, 95, 750, 510))
        self.text("Set colony size", self.mid, (255, 238, 133), center=(WIDTH // 2, 150))
        self.text(f"{self.state.colony_cfu} CFU", self.big, (146, 255, 167), center=(WIDTH // 2, 260))
        pygame.draw.rect(self.screen, (160, 180, 190), self.slider_rect, border_radius=8)
        knob_x = self.slider_rect.left + int(self.slider_rect.width * self.state.colony_cfu / 1000)
        pygame.draw.circle(self.screen, (255, 112, 166), (knob_x, self.slider_rect.centery), 20)
        self.text(f"{self.state.colony_label}  |  Score: {self.state.colony_score}", self.font, (245, 250, 255), center=(WIDTH // 2, 410))
        self.add_button((490, 505, 220, 54), "Continue", lambda: self.set_screen(SECRETION_SELECTION))

    def draw_secretion(self) -> None:
        self.panel((35, 25, 1130, 770))
        self.text("Bring your BGC arsenal?", self.mid, (255, 238, 133), center=(WIDTH // 2, 65))
        self.draw_arsenal_panel("Your fighter", self.state.player_entry, pygame.Rect(65, 105, 515, 445), bool(self.state.has_secretion))
        self.draw_arsenal_panel("Opponent scout report", self.state.opponent_entry, pygame.Rect(620, 105, 515, 445), self.state.opponent_has_secretion)
        player_bgc_count = len(self.state.player_entry.accessions) if self.state.player_entry else 0
        msg = f"Your fighter has {player_bgc_count} known BGC{'s' if player_bgc_count != 1 else ''}. Bring this chemical toolkit into battle?"
        self.draw_wrapped(msg, pygame.Rect(275, 575, 650, 58), self.font, (245, 250, 255))
        self.add_button((320, 650, 210, 58), "Yes", self.choose_bgc_arsenal_yes, selected=self.state.has_secretion is True)
        self.add_button((670, 650, 210, 58), "No", lambda: setattr(self.state, "has_secretion", False), selected=self.state.has_secretion is False)
        self.add_button((490, 728, 220, 44), "Continue", lambda: self.set_screen(ENVIRONMENT_SELECTION), enabled=self.state.has_secretion is not None)

    def draw_arsenal_panel(self, title: str, entry: BacteriumCatalogEntry, rect: pygame.Rect, brings_arsenal: bool) -> None:
        pygame.draw.rect(self.screen, (10, 24, 38, 185), rect, border_radius=16)
        pygame.draw.rect(self.screen, (108, 231, 218), rect, 1, border_radius=16)
        x, y = rect.x + 14, rect.y + 12
        self.text(title.upper(), self.small, (255, 238, 133), topleft=(x, y))
        y += 25
        name = format_bacterial_name(entry.full_name)
        self.draw_scientific_name(name, x, y, self.font, max_width=rect.width - 28)
        y += 35
        status_color = (146, 255, 167) if brings_arsenal and entry.accessions else (255, 238, 133)
        self.text(f"{len(entry.accessions)} known BGCs", self.font, (245, 250, 255), topleft=(x, y))
        self.text(f"Arsenal {'ACTIVE' if brings_arsenal and entry.accessions else 'INACTIVE'}", self.small, status_color, topleft=(rect.right - 165, y + 4))
        y += 34
        bgcs = ", ".join(entry.accessions[:3]) or "No matched MIBiG records"
        if len(entry.accessions) > 3:
            bgcs += f"  +{len(entry.accessions) - 3} more"
        y = self.draw_wrapped(bgcs, pygame.Rect(x, y, rect.width - 28, 42), self.small, (245, 250, 255), 2) + 5
        self.text("Traits", self.small, (255, 238, 133), topleft=(x, y))
        y = self.draw_trait_chips(entry, x + 75, y, rect.width - 103, max_items=3)
        y = self.draw_labeled_chips("Products", entry.products, x, y, rect.width - 28, (50, 145, 175))
        y = self.draw_labeled_chips("Activities", entry.activities, x, y, rect.width - 28, (120, 100, 190))
        if y < rect.bottom - 60:
            self.text("Habitat", self.small, (255, 238, 133), topleft=(x, y))
            self.draw_wrapped(sanitize_designation(entry.isolation_habitat), pygame.Rect(x + 82, y, rect.width - 110, rect.bottom - y - 12), self.small, (245, 250, 255), 2)

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
        rect = pygame.Rect(270, 40, 660, 70)
        surf = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(surf, (12, 30, 48, 235), surf.get_rect(), border_radius=18)
        pygame.draw.rect(surf, (255, 238, 133, 230), surf.get_rect(), 2, border_radius=18)
        self.screen.blit(surf, rect)
        self.draw_wrapped(self.state.popup_message, rect.inflate(-28, -20), self.small, (255, 255, 255))

    def draw_preview(self) -> None:
        self.panel((155, 60, 890, 680))
        self.text("Battle preview", self.mid, (255, 238, 133), center=(WIDTH // 2, 110))
        rows = [
            ("Your microbe", format_bacterial_name(self.state.player_entry.full_name)),
            ("Opponent", format_bacterial_name(self.state.opponent_entry.full_name)),
            ("Environment", self.state.environment),
            ("Your colony", f"{self.state.colony_cfu} CFU ({self.state.colony_label}, +{self.state.colony_score:.1f})"),
            ("Opponent colony", f"{self.state.opponent_colony_cfu} CFU (+{self.state.opponent_colony_score:.1f})"),
            ("Your BGC arsenal", f"{'Yes' if self.state.has_secretion else 'No'} ({self.active_bgc_count(self.state.player_entry, bool(self.state.has_secretion))} active BGCs)"),
            ("Opponent BGC arsenal", f"{'Yes' if self.state.opponent_has_secretion else 'No'} ({self.active_bgc_count(self.state.opponent_entry, self.state.opponent_has_secretion)} active BGCs)"),
        ]
        y = 165
        for label, value in rows:
            self.text(f"{label}:", self.font, (146, 255, 167), topleft=(255, y))
            if isinstance(value, BacterialName):
                self.draw_scientific_name(value, 510, y, self.font, (245, 250, 255), 470)
            else:
                self.draw_wrapped(str(value), pygame.Rect(510, y, 470, 42), self.font, (245, 250, 255), 2)
            y += 57
        self.add_button((480, 650, 240, 62), "Battle!", self.start_animation)

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
        self.panel((155 + shake, 50, 890, 610), 205)
        self.text("MICROBIAL BATTLE!", self.mid, (255, 238, 133), center=(WIDTH // 2 + shake, 95))
        while self.state.next_event_index < len(self.state.animation_events) and elapsed >= self.state.animation_events[self.state.next_event_index]["time"]:
            ev = self.state.animation_events[self.state.next_event_index]
            self.state.displayed_player_score = ev["player"]
            self.state.displayed_opponent_score = ev["opponent"]
            pos = pygame.Vector2(820 if ev["target"] == "opponent" else 380, 300)
            self.state.floating_texts.append(FloatingText(ev["text"], pos, (255, 230, 120), pygame.time.get_ticks()))
            self.state.next_event_index += 1
        p_pos = (380 + int(math.sin(elapsed / 160) * 22), 330)
        o_pos = (820 - int(math.sin(elapsed / 170) * 22), 330)
        self.draw_microbe(p_pos, (77, 220, 146), format_bacterial_name(self.state.player_entry.full_name).scientific, self.state.displayed_player_score, self.state.player_score)
        self.draw_microbe(o_pos, (255, 112, 166), format_bacterial_name(self.state.opponent_entry.full_name).scientific, self.state.displayed_opponent_score, self.state.opponent_score)
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
        headline = "VICTORY!" if self.state.winner_flag == "A" else "DEFEAT!" if self.state.winner_flag == "B" else "TIE!"
        self.text(headline, self.big, (146, 255, 167), center=(WIDTH // 2, 80))
        if self.state.winner_flag == "tie":
            winner_heading = "Evenly matched!"
            self.text(winner_heading, self.mid, (255, 238, 133), center=(WIDTH // 2, 137))
        else:
            winner = self.state.player_entry if self.state.winner_flag == "A" else self.state.opponent_entry
            self.draw_winner_heading(format_bacterial_name(winner.full_name), 123)
        self.text(f"You {self.state.player_score:.1f}  vs  Opponent {self.state.opponent_score:.1f}", self.font, (245, 250, 255), center=(WIDTH // 2, 182))
        player_rect = pygame.Rect(75, 215, 500, 305)
        opp_rect = pygame.Rect(625, 215, 500, 305)
        self.draw_score_card("Player", self.state.player_breakdown, player_rect)
        self.draw_score_card("Opponent", self.state.opponent_breakdown, opp_rect)
        info_rect = pygame.Rect(85, 545, 1030, 90)
        pygame.draw.rect(self.screen, (10, 24, 38, 185), info_rect, border_radius=14)
        pygame.draw.rect(self.screen, (108, 231, 218), info_rect, 1, border_radius=14)
        self.draw_biological_note(info_rect.inflate(-20, -12))
        self.add_button((335, 680, 220, 58), "Play Again", lambda: reset_for_new_game(self.state))
        self.add_button((645, 680, 220, 58), "Quit", self.quit)

    def draw_score_card(self, label: str, breakdown: ScoreBreakdown, rect: pygame.Rect) -> None:
        pygame.draw.rect(self.screen, (10, 24, 38, 185), rect, border_radius=16)
        pygame.draw.rect(self.screen, (108, 231, 218), rect, 1, border_radius=16)
        x, y = rect.x + 14, rect.y + 12
        self.text(label.upper(), self.small, (146, 255, 167), topleft=(x, y))
        name = format_bacterial_name(breakdown.fighter_name)
        self.draw_scientific_name(name, x + 100, y, self.small, (146, 255, 167), rect.width - 128)
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
        product = winner.products[0] if winner.products else "no named product"
        activity = winner.activities[0] if winner.activities else "no reported activity"
        name = format_bacterial_name(winner.full_name)
        authority = f" ({name.expanded_details})" if name.expanded_details else ""
        return sanitize_designation(f"Bio note: {name.scientific}{authority} has {len(winner.accessions)} known BGC(s). Notable product/activity: {product}; {activity}. {winner.curious_fact}")

    def draw_biological_note(self, rect: pygame.Rect) -> None:
        winner = self.state.player_entry if self.state.winner_flag != "B" else self.state.opponent_entry
        name = format_bacterial_name(winner.full_name)
        x = self.text("Bio note: ", self.small, (255, 238, 133), topleft=(rect.x, rect.y)).right
        x = self.text(name.scientific, self.small_italic, (245, 250, 255), topleft=(x, rect.y)).right
        if name.authority and x + self.small.size(f" — {name.authority}")[0] < rect.right:
            self.text(f" — {name.authority}", self.small, (245, 250, 255), topleft=(x, rect.y))
        product = sanitize_designation(winner.products[0]) if winner.products else "no named product"
        activity = sanitize_designation(winner.activities[0]) if winner.activities else "no reported activity"
        body = f"{len(winner.accessions)} known BGC(s). Notable product/activity: {product}; {activity}. {sanitize_designation(winner.curious_fact)}"
        self.draw_wrapped(body, pygame.Rect(rect.x, rect.y + 26, rect.width, rect.height - 26), self.small, (245, 250, 255), 2)

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
            if b.bacterial_name:
                name = b.bacterial_name
                scientific = name.scientific
                secondary = b.secondary_text or name.short_secondary
                self.text(scientific, self.small_italic, (255, 255, 255), center=(b.rect.centerx, b.rect.centery - (8 if secondary else 0)))
                if secondary:
                    if self.small.size(secondary)[0] > b.rect.width - 24:
                        secondary = secondary[:42].rstrip() + "…"
                    self.text(secondary, self.small, (255, 255, 255), center=(b.rect.centerx, b.rect.centery + 11))
                continue
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
