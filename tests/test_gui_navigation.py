import os
from copy import deepcopy

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from microbial_mayhem_main import (
    BATTLE_ANIMATION, BATTLE_PREVIEW, COLONY_SELECTION, ENVIRONMENT_SELECTION,
    FIGHTER_SELECTION, ONE_PLAYER, RESULTS, SECRETION_SELECTION, SETTINGS, WELCOME,
    MicrobialMayhemGUI,
)
from ui_systems import VirtualViewport


def send_click(app, button, release=None):
    window_down = app.viewport.to_window(button.rect.center)
    window_up = app.viewport.to_window(release or button.rect.center)
    app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=window_down))
    app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=window_up))


def button_named(app, name):
    app.draw((-100, -100), 16)
    return next(button for button in app.buttons if button.text == name and button.enabled)


def test_single_click_navigation_scaled_coordinates_release_and_skip():
    app = MicrobialMayhemGUI()
    app.settings.onboarding_complete = True
    app.viewport = VirtualViewport(800, 600)
    assert app.audio.requested_phase == "setup"

    app.draw((-100, -100), 16)
    assert next(button for button in app.buttons if button.text == "Start Game").enabled is False
    assert next(button for button in app.buttons if button.text == "Settings").enabled is True
    send_click(app, next(button for button in app.buttons if button.text == "Settings"))
    assert app.state.screen == SETTINGS and app.state.game_mode is None
    send_click(app, button_named(app, "Back"))
    assert app.state.screen == WELCOME and app.state.game_mode is None
    app.draw((-100, -100), 16)
    send_click(app, next(button for button in app.buttons if button.text == "1 Player"))
    assert app.state.game_mode == ONE_PLAYER

    # A complete press released elsewhere owns no action.
    start = button_named(app, "Start Game")
    send_click(app, start, release=(1100, 780))
    assert app.state.screen == WELCOME

    # The same control works with one normal click through scaled coordinates.
    start = button_named(app, "Start Game")
    send_click(app, start)
    assert app.state.screen == FIGHTER_SELECTION

    app.draw((-100, -100), 16)
    fighter = next(button for button in app.buttons if button.fighter)
    send_click(app, fighter)
    assert app.state.selected_catalog_entry is not None
    send_click(app, button_named(app, "LOCK PLAYER 1"))
    assert app.state.screen == COLONY_SELECTION
    assert app.state.player1_fighter is app.state.player_entry
    assert app.state.player2_fighter is app.state.opponent_entry
    assert app.state.player1_fighter.catalog_id != app.state.player2_fighter.catalog_id
    send_click(app, button_named(app, "LOCK IN COLONY"))
    assert app.state.screen == SECRETION_SELECTION
    send_click(app, button_named(app, "Yes"))
    send_click(app, button_named(app, "Continue"))
    assert app.state.screen == ENVIRONMENT_SELECTION
    send_click(app, button_named(app, "Hot"))
    send_click(app, button_named(app, "ENTER THIS ARENA"))
    assert app.state.screen == BATTLE_PREVIEW
    assert app.audio.requested_phase == "setup"

    app.state.transition_started -= 1200
    send_click(app, button_named(app, "ENTER THE ARENA"))
    assert app.state.screen == BATTLE_ANIMATION
    assert app.audio.requested_phase == "battle"
    calculated_winner = app.state.winner_flag
    send_click(app, button_named(app, "Skip"))
    assert app.state.screen == RESULTS
    assert app.audio.requested_phase == "results"
    assert app.state.winner_flag == calculated_winner

    # Missing result fields and every supported text scale render safely.
    winner_attr = "player_entry" if app.state.winner_flag != "B" else "opponent_entry"
    winner = deepcopy(getattr(app.state, winner_attr))
    winner.products = []; winner.activities = []; winner.curious_fact = ""
    setattr(app.state, winner_attr, winner)
    assert app.biological_result_summary().endswith("That is why we need more research.")
    app.state.results_started -= 2000
    app.transition.started_ms -= 2000
    for scale in (.85, 1.0, 1.3):
        app.settings.text_scale = scale
        app.configure_fonts()
        app.draw((-100, -100), 16)

    # Reduced motion keeps essential colony and environment information visible.
    app.settings.reduced_motion = True
    app.set_screen(COLONY_SELECTION); app.draw((-100, -100), 16)
    app.set_screen(ENVIRONMENT_SELECTION); app.draw((-100, -100), 16)
    pygame.quit()
