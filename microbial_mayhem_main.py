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

import microbe_class
import sec_sys
from microbe_info_output import output_statement
from species_dict import spp_dict

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

SPECIES = list(spp_dict.keys())
DISPLAY_NAMES = {
    "E.coli": "Escherichia coli",
    "M.tuberculosis": "Mycobacterium tuberculosis",
    "V.maris": "Verrucosispora maris",
    "M.alcalica": "Methylophaga alcalica",
    "S.aureus": "Staphylococcus aureus",
    "V.neptunius": "Vibrio neptunius",
    "P.fluorescens": "Pseudomonas fluorescens",
    "K.pneumoniae": "Klebsiella pneumoniae",
}
ENVIRONMENTS = ["Salty", "Alkaline", "Hot", "Cold", "Acidic", "In the presence of antibiotics"]
SUPERPOWERS = ["Halophile", "Alkaliphile", "Acidophile", "Thermophile", "Cryophile", "Drug resistant", "None"]
EXTREME_ENVS = {"Alkaline", "Hot", "Cold", "Acidic", "Salty", "in drugs", "In the presence of antibiotics"}
POWER_VALUES = {"Drug resistant", "Halophile", "Acidophile", "Thermophile", "Cryophile", "Alkaliphile"}


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
    player_species: str | None = None
    colony_cfu: int = 100
    colony_score: int = 5
    colony_label: str = "Decent-sized colony"
    has_secretion: bool | None = None
    opponent_species: str | None = None
    opponent_colony_score: int = 0
    opponent_secretion_score: int = 0
    environment: str | None = None
    superpower: str | None = None
    player_score: float = 0.0
    opponent_score: float = 0.0
    winner_flag: str = "tie"
    winner_species: str = ""
    result_text: str = ""
    animation_started: int = 0
    animation_events: list[dict] = field(default_factory=list)
    next_event_index: int = 0
    displayed_player_score: float = 0.0
    displayed_opponent_score: float = 0.0
    floating_texts: list[FloatingText] = field(default_factory=list)


def colony_growth_score(cfu: int) -> tuple[int, str]:
    """Reuse the original colony thresholds without terminal input."""
    if cfu < 10:
        return 0, "Tiny colony, you're risking it!"
    if 10 <= cfu <= 100:
        return 5, "Decent-sized colony"
    return 10, "Huuuge colony, you're playing safe"


def calculate_env_score(environment: str, superpower: str) -> int:
    """GUI-safe equivalent of Env_scoring.calculate_score_env."""
    power_score = 100 if superpower in POWER_VALUES else 0
    env_penalty = -10 if environment in EXTREME_ENVS else 0
    return env_penalty + power_score


def make_microbe(species: str) -> microbe_class.Microbe:
    return microbe_class.Microbe(species, spp_dict[species]["growth_rate"], spp_dict[species]["kin_select"])


def calculate_battle(state: GameState) -> None:
    player = make_microbe(state.player_species)
    opponent = make_microbe(state.opponent_species)
    env_score = calculate_env_score(state.environment, state.superpower)
    player_sec = sec_sys.calc_secretion("YES" if state.has_secretion else "NO")
    state.player_score = float(player.strength()) + float(state.colony_score * player.growth_rate) + float(env_score) + float(player_sec)
    state.opponent_score = float(opponent.strength()) + float(state.opponent_colony_score * opponent.growth_rate) + float(env_score) + float(state.opponent_secretion_score)
    if state.player_score > state.opponent_score:
        state.winner_flag, state.winner_species = "A", state.player_species
    elif state.player_score < state.opponent_score:
        state.winner_flag, state.winner_species = "B", state.opponent_species
    else:
        state.winner_flag = "tie"
        state.winner_species = f"{state.player_species} and {state.opponent_species}"
    state.result_text = output_statement(state.winner_flag, state.winner_species)


def reset_for_new_game(state: GameState) -> None:
    state.screen = WELCOME
    state.player_species = None
    state.colony_cfu = 100
    state.colony_score, state.colony_label = colony_growth_score(100)
    state.has_secretion = None
    state.opponent_species = None
    state.opponent_colony_score = 0
    state.opponent_secretion_score = 0
    state.environment = None
    state.superpower = None
    state.player_score = state.opponent_score = 0.0
    state.result_text = ""
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
            self.draw_choice_grid("Choose your microbial fighter", [(DISPLAY_NAMES[s], s) for s in SPECIES], "player_species", FIGHTER_SELECTION)
        elif self.state.screen == COLONY_SELECTION:
            self.draw_colony()
        elif self.state.screen == SECRETION_SELECTION:
            self.draw_secretion()
        elif self.state.screen == ENVIRONMENT_SELECTION:
            self.draw_choice_grid("Choose the fighting environment", [(e, e) for e in ENVIRONMENTS], "environment", ENVIRONMENT_SELECTION)
        elif self.state.screen == SUPERPOWER_SELECTION:
            self.draw_choice_grid("Choose a microbial superpower", [(s, s) for s in SUPERPOWERS], "superpower", SUPERPOWER_SELECTION)
        elif self.state.screen == BATTLE_PREVIEW:
            self.draw_preview()
        elif self.state.screen == BATTLE_ANIMATION:
            self.draw_animation(dt)
        elif self.state.screen == RESULTS:
            self.draw_results()
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
        lines, current = [], ""
        for word in text.replace("\n", " \n ").split():
            if word == "\n":
                lines.append(current)
                current = ""
                continue
            candidate = (current + " " + word).strip()
            if font.size(candidate)[0] <= width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

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

    def draw_choice_grid(self, title, choices, attr, screen_name) -> None:
        self.panel((70, 55, 860, 590))
        self.text(title, self.mid, (255, 238, 133), center=(WIDTH // 2, 105))
        for idx, (label, value) in enumerate(choices):
            col, row = idx % 2, idx // 2
            rect = (135 + col * 390, 160 + row * 82, 340, 58)
            self.add_button(rect, label, lambda v=value: setattr(self.state, attr, v), getattr(self.state, attr) == value)
        selected = getattr(self.state, attr) is not None
        next_screen = {
            FIGHTER_SELECTION: COLONY_SELECTION,
            ENVIRONMENT_SELECTION: SUPERPOWER_SELECTION,
            SUPERPOWER_SELECTION: BATTLE_PREVIEW,
        }[screen_name]
        self.add_button((390, 585, 220, 54), "Continue", lambda: self.after_choice(next_screen), enabled=selected)

    def after_choice(self, next_screen: str) -> None:
        if next_screen == BATTLE_PREVIEW and self.state.opponent_species is None:
            choices = [s for s in SPECIES if s != self.state.player_species] or SPECIES
            self.state.opponent_species = random.choice(choices)
            self.state.opponent_colony_score = random.choice([0, 5, 10])
            self.state.opponent_secretion_score = sec_sys.calc_secretion(random.choice(["YES", "NO"]))
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
        self.text("Secretion system?", self.mid, (255, 238, 133), center=(WIDTH // 2, 150))
        msg = "Secretion systems are toxin-injection weapons bacteria can use to attack neighboring microbes. Choose whether your fighter brings one to battle."
        self.draw_wrapped(msg, pygame.Rect(220, 210, 560, 110), self.font, (245, 250, 255))
        self.add_button((245, 360, 210, 78), "Yes", lambda: setattr(self.state, "has_secretion", True), selected=self.state.has_secretion is True)
        self.add_button((545, 360, 210, 78), "No", lambda: setattr(self.state, "has_secretion", False), selected=self.state.has_secretion is False)
        self.add_button((390, 515, 220, 54), "Continue", lambda: self.set_screen(ENVIRONMENT_SELECTION), enabled=self.state.has_secretion is not None)

    def draw_preview(self) -> None:
        self.panel((105, 60, 790, 600))
        self.text("Battle preview", self.mid, (255, 238, 133), center=(WIDTH // 2, 110))
        rows = [
            ("Your microbe", DISPLAY_NAMES[self.state.player_species]),
            ("Opponent", DISPLAY_NAMES[self.state.opponent_species]),
            ("Environment", self.state.environment),
            ("Superpower", self.state.superpower),
            ("Colony", f"{self.state.colony_cfu} CFU ({self.state.colony_label})"),
            ("Secretion system", "Yes" if self.state.has_secretion else "No"),
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
        self.draw_microbe(p_pos, (77, 220, 146), DISPLAY_NAMES[self.state.player_species], self.state.displayed_player_score, self.state.player_score)
        self.draw_microbe(o_pos, (255, 112, 166), DISPLAY_NAMES[self.state.opponent_species], self.state.displayed_opponent_score, self.state.opponent_score)
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
        self.text(f"{self.state.winner_species} WINS!", self.mid, (255, 238, 133), center=(WIDTH // 2, 155))
        self.text(f"Final scores: You {self.state.player_score:.1f}  |  Opponent {self.state.opponent_score:.1f}", self.font, (245, 250, 255), center=(WIDTH // 2, 210))
        self.draw_wrapped(self.state.result_text, pygame.Rect(155, 255, 690, 250), self.font, (245, 250, 255))
        self.add_button((260, 585, 200, 54), "Play Again", lambda: reset_for_new_game(self.state))
        self.add_button((540, 585, 200, 54), "Quit", self.quit)

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
