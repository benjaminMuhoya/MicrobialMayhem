from app_settings import AppSettings
from audio_manager import AudioManager


class BrokenMixer:
    @staticmethod
    def get_init(): return False
    @staticmethod
    def init(): raise RuntimeError("no device")


class BrokenPygame:
    mixer = BrokenMixer()


def test_settings_round_trip_and_clamping(tmp_path):
    path = tmp_path / "settings.json"
    settings = AppSettings(reduced_motion=True, text_scale=5, music_volume=-1, onboarding_complete=True)
    assert settings.save(path)
    restored = AppSettings.load(path)
    assert restored.reduced_motion and restored.onboarding_complete
    assert restored.text_scale == 1.3 and restored.music_volume == 0


def test_missing_or_invalid_settings_are_safe(tmp_path):
    assert AppSettings.load(tmp_path / "missing.json") == AppSettings()
    bad = tmp_path / "bad.json"; bad.write_text("not json")
    assert AppSettings.load(bad) == AppSettings()


def test_missing_audio_device_and_assets_never_crash(tmp_path):
    manager = AudioManager(tmp_path, AppSettings(), BrokenPygame)
    assert not manager.enabled
    assert manager.register("click", "missing.wav") is False
    assert manager.play("click") is False
    assert manager.play_music("missing.ogg") is False
    manager.stop_music()


class FakeSound:
    def __init__(self, path):
        self.path = path
        self.volume = None
        self.plays = 0

    def set_volume(self, volume):
        self.volume = volume

    def play(self):
        self.plays += 1


class FakeMusic:
    def __init__(self):
        self.loads = []
        self.plays = []
        self.fadeouts = []
        self.stops = 0
        self.volume = None

    def load(self, path): self.loads.append(path)
    def set_volume(self, volume): self.volume = volume
    def play(self, loops, **kwargs): self.plays.append((loops, kwargs))
    def fadeout(self, milliseconds): self.fadeouts.append(milliseconds)
    def stop(self): self.stops += 1


class FakeMixer:
    def __init__(self):
        self.music = FakeMusic()
        self.created_sounds = []
        self.stop_calls = 0

    def get_init(self): return True
    def init(self): raise AssertionError("initialized mixer must not reinitialize")

    def Sound(self, path):
        sound = FakeSound(path)
        self.created_sounds.append(sound)
        return sound

    def stop(self): self.stop_calls += 1


class FakePygame:
    def __init__(self):
        self.mixer = FakeMixer()


def create_audio_tree(root):
    for path in (
        "music/setup_theme.wav", "music/battle_theme.wav", "music/results_theme.wav",
        "sfx/click.wav", "sfx/select.wav", "sfx/attack.wav", "sfx/impact.wav",
        "sfx/ability.wav", "sfx/arsenal.wav", "sfx/clash.wav", "sfx/final_hit.wav",
        "sfx/victory.wav", "sfx/defeat.wav",
    ):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"fake")


def test_audio_phases_preserve_setup_then_transition_to_battle_and_results(tmp_path):
    create_audio_tree(tmp_path)
    pygame = FakePygame()
    manager = AudioManager(tmp_path, AppSettings(), pygame)

    assert manager.set_phase("setup", 0)
    assert manager.current_phase == "setup"
    assert len(pygame.mixer.music.loads) == 1
    assert not manager.set_phase("setup", 50)
    assert not manager.set_phase("setup", 100)
    assert len(pygame.mixer.music.loads) == 1

    assert manager.set_phase("battle", 1000)
    assert manager.pending_phase == "battle" and manager.current_phase is None
    assert not manager.update(1459)
    assert manager.update(1460)
    assert manager.current_phase == "battle"
    assert pygame.mixer.music.loads[-1].endswith("battle_theme.wav")

    victory = manager.sounds["victory"]
    assert manager.set_phase("results", 2000, accent="victory")
    assert victory.plays == 1
    assert not manager.update(2519)
    assert manager.update(2520)
    assert manager.current_phase == "results"
    assert pygame.mixer.music.loads[-1].endswith("results_theme.wav")


def test_audio_respects_mute_and_independent_volume_settings(tmp_path):
    create_audio_tree(tmp_path)
    pygame = FakePygame()
    settings = AppSettings(muted=True)
    manager = AudioManager(tmp_path, settings, pygame)

    assert not manager.set_phase("setup", 0)
    assert not manager.play("click")
    assert not pygame.mixer.music.loads
    settings.muted = False
    manager.apply_settings(10)
    assert manager.current_phase == "setup"

    settings.sfx_volume = 0
    assert not manager.play("click")
    manager.set_music_volume(0)
    assert manager.current_phase is None
    manager.set_music_volume(.4)
    assert manager.current_phase == "setup"


def test_enabled_mixer_with_missing_assets_stays_safe(tmp_path):
    manager = AudioManager(tmp_path, AppSettings(), FakePygame())
    assert not manager.set_phase("setup", 0)
    assert not manager.play("attack")
    assert not manager.update(10_000)
    manager.shutdown()
