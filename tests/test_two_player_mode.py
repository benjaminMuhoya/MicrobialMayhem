import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

import microbial_mayhem_main as game
from microbial_mayhem_main import (
    BATTLE_ANIMATION, BATTLE_PREVIEW, COLONY_SELECTION, ENVIRONMENT_SELECTION,
    FIGHTER_SELECTION, ONE_PLAYER, RESULTS, SECRETION_SELECTION, TWO_PLAYERS,
    WELCOME, MicrobialMayhemGUI,
)


def draw_and_find(app, text, enabled=True):
    app.draw((-100, -100), 16)
    return next(button for button in app.buttons if button.text == text and (not enabled or button.enabled))


def click(app, button):
    position = app.viewport.to_window(button.rect.center)
    app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=position))
    app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=position))


def touch(app, button):
    position = app.viewport.to_window(button.rect.center)
    width, height = app.display.get_size()
    values = dict(x=position[0] / width, y=position[1] / height, finger_id=1)
    app.handle_event(pygame.event.Event(pygame.FINGERDOWN, **values))
    app.handle_event(pygame.event.Event(pygame.FINGERUP, **values))


def test_two_player_selection_back_validation_results_and_resets(monkeypatch):
    app = MicrobialMayhemGUI()
    app.settings.onboarding_complete = True

    # Keyboard, controller, and touch all use the shared mode controls.
    one = draw_and_find(app, "1 Player")
    app.input.focused_id = one.control_id
    app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, unicode=""))
    assert app.state.game_mode == ONE_PLAYER
    two = draw_and_find(app, "2 Players")
    app.input.focused_id = two.control_id
    app.handle_event(pygame.event.Event(pygame.JOYBUTTONDOWN, button=0))
    assert app.state.game_mode == TWO_PLAYERS
    one = draw_and_find(app, "1 Player")
    touch(app, one)
    assert app.state.game_mode == ONE_PLAYER
    click(app, draw_and_find(app, "2 Players"))
    assert app.state.game_mode == TWO_PLAYERS
    touch(app, draw_and_find(app, "Start Game"))
    assert app.state.screen == FIGHTER_SELECTION and app.state.active_player == 1
    app.navigate_back()
    assert app.state.screen == WELCOME and app.state.game_mode == TWO_PLAYERS
    touch(app, draw_and_find(app, "Start Game"))
    assert app.state.screen == FIGHTER_SELECTION and app.state.active_player == 1

    # Any call to random opponent selection in two-player mode is a regression.
    monkeypatch.setattr(game, "choose_opponent", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("random opponent used")))
    app.draw((-100, -100), 16)
    player1_button = next(button for button in app.buttons if button.fighter and button.enabled)
    click(app, player1_button)
    player1 = app.state.selected_catalog_entry
    click(app, draw_and_find(app, "LOCK PLAYER 1"))
    assert app.state.player1_fighter is player1
    assert app.state.player_entry is player1
    assert app.state.opponent_entry is None
    assert app.state.active_player == 2 and app.state.player1_confirmed

    # Back from Player 2 returns to Player 1 and clears the incomplete rival.
    app.navigate_back()
    assert app.state.screen == FIGHTER_SELECTION and app.state.active_player == 1
    assert app.state.player2_fighter is None and not app.state.player2_confirmed
    assert app.state.selected_catalog_entry is player1
    click(app, draw_and_find(app, "LOCK PLAYER 1"))
    assert app.state.active_player == 2

    # Player 1 remains visible, disabled, and rejected by shared validation.
    app.draw((-100, -100), 16)
    claimed = next(button for button in app.buttons if button.fighter and button.fighter.catalog_id == player1.catalog_id)
    assert not claimed.enabled and "PLAYER 1 CLAIMED" in claimed.secondary_text
    assert app.select_catalog_entry(player1) is False
    assert app.state.selected_catalog_entry is None

    rival_button = next(button for button in app.buttons if button.fighter and button.enabled and button.fighter.catalog_id != player1.catalog_id)
    click(app, rival_button)
    player2 = app.state.selected_catalog_entry
    click(app, draw_and_find(app, "LOCK PLAYER 2"))
    assert app.state.screen == COLONY_SELECTION
    assert app.state.player2_fighter is player2
    assert app.state.opponent_entry is player2
    assert player1.catalog_id != player2.catalog_id
    assert not app.battle_setup_complete()

    click(app, draw_and_find(app, "Tiny Squad"))
    click(app, draw_and_find(app, "LOCK PLAYER 1 COLONY"))
    assert app.state.screen == SECRETION_SELECTION
    click(app, draw_and_find(app, "Yes"))
    click(app, draw_and_find(app, "LOCK PLAYER 1 ARSENAL"))
    assert app.state.screen == COLONY_SELECTION and app.state.setup_player == 2
    app.navigate_back()
    assert app.state.screen == SECRETION_SELECTION and app.state.setup_player == 1
    click(app, draw_and_find(app, "LOCK PLAYER 1 ARSENAL"))
    assert app.state.screen == COLONY_SELECTION and app.state.setup_player == 2
    click(app, draw_and_find(app, "Packed Colony"))
    click(app, draw_and_find(app, "LOCK PLAYER 2 COLONY"))
    assert app.state.screen == SECRETION_SELECTION
    app.navigate_back()
    assert app.state.screen == COLONY_SELECTION and app.state.setup_player == 2
    assert app.state.colony_cfu == 750
    click(app, draw_and_find(app, "LOCK PLAYER 2 COLONY"))
    click(app, draw_and_find(app, "No"))
    click(app, draw_and_find(app, "LOCK PLAYER 2 ARSENAL"))
    assert app.state.screen == ENVIRONMENT_SELECTION
    assert app.state.player1_colony_cfu == 50
    assert app.state.player2_colony_cfu == 750
    assert app.state.player1_arsenal_active is True
    assert app.state.player2_arsenal_active is False
    assert app.state.colony_cfu == 50 and app.state.opponent_colony_cfu == 750
    assert app.state.has_secretion is True and app.state.opponent_has_secretion is False
    click(app, draw_and_find(app, "Hot"))
    click(app, draw_and_find(app, "ENTER THIS ARENA"))
    assert app.state.screen == BATTLE_PREVIEW
    assert app.audio.requested_phase == "setup"
    assert app.battle_setup_complete()
    assert app.state.player_breakdown.colony_cfu == 50
    assert app.state.opponent_breakdown.colony_cfu == 750
    app.state.transition_started -= 1200
    click(app, draw_and_find(app, "ENTER THE ARENA"))
    assert app.state.screen == BATTLE_ANIMATION
    assert app.audio.requested_phase == "battle"
    click(app, draw_and_find(app, "Skip"))
    assert app.state.screen == RESULTS
    assert app.audio.requested_phase == "results"
    expected = "PLAYER 1 WINS!" if app.state.winner_flag == "A" else "PLAYER 2 WINS!" if app.state.winner_flag == "B" else "TIE!"
    assert app.result_headline() == expected

    # Rematch preserves fighters; Change Fighters preserves mode; Main Menu does not.
    colony_cfu, environment = app.state.colony_cfu, app.state.environment
    app.rematch()
    assert app.state.screen == BATTLE_ANIMATION
    assert app.state.player1_fighter is player1 and app.state.player2_fighter is player2
    assert app.state.colony_cfu == colony_cfu and app.state.environment == environment
    assert app.state.opponent_colony_cfu == 750
    app.finish_animation()
    app.change_fighter()
    assert app.state.screen == FIGHTER_SELECTION and app.state.game_mode == TWO_PLAYERS
    assert app.state.active_player == 1
    assert app.state.player1_fighter is None and app.state.player2_fighter is None
    app.main_menu()
    assert app.state.screen == WELCOME and app.state.game_mode is None
    assert app.state.player_entry is None and app.state.opponent_entry is None
    pygame.quit()
