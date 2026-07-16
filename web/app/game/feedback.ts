import type { GamePreferences } from "./preferences";

export type MusicPhase = "setup" | "battle" | "results";
export type SoundCue = "click" | "select" | "attack" | "impact" | "ability" | "arsenal" | "clash" | "final_hit" | "victory" | "defeat";

const tracks: Record<MusicPhase, string> = {
  setup: "./audio/music/setup_theme.wav",
  battle: "./audio/music/battle_theme.wav",
  results: "./audio/music/results_theme.wav",
};
const cues: Record<SoundCue, string> = {
  click: "./audio/sfx/click.wav", select: "./audio/sfx/select.wav", attack: "./audio/sfx/attack.wav",
  impact: "./audio/sfx/impact.wav", ability: "./audio/sfx/ability.wav", arsenal: "./audio/sfx/arsenal.wav",
  clash: "./audio/sfx/clash.wav", final_hit: "./audio/sfx/final_hit.wav", victory: "./audio/sfx/victory.wav", defeat: "./audio/sfx/defeat.wav",
};

class GameFeedback {
  private preferences: GamePreferences | null = null;
  private music: HTMLAudioElement | null = null;
  private phase: MusicPhase | null = null;
  private lastCue = new Map<SoundCue, number>();
  private unlocked = false;

  configure(preferences: GamePreferences) {
    this.preferences = preferences;
    if (this.music) this.music.volume = preferences.musicVolume;
    if (preferences.musicVolume <= 0) this.music?.pause();
  }

  unlock() {
    this.unlocked = true;
    if (this.phase) void this.startPhase(this.phase);
  }

  async startPhase(phase: MusicPhase) {
    this.phase = phase;
    if (typeof Audio === "undefined" || !this.unlocked || !this.preferences || this.preferences.musicVolume <= 0) return;
    if (this.music?.dataset.phase === phase) {
      if (this.music.paused) await this.music.play().catch(() => undefined);
      return;
    }
    this.music?.pause();
    const music = new Audio(tracks[phase]);
    music.dataset.phase = phase;
    music.loop = true;
    music.preload = "auto";
    music.volume = this.preferences.musicVolume;
    this.music = music;
    await music.play().catch(() => undefined);
  }

  cue(cue: SoundCue, strength: "light" | "medium" | "strong" = "light") {
    if (typeof Audio === "undefined" || !this.preferences || this.preferences.effectsVolume <= 0) return;
    const now = Date.now();
    if (now - (this.lastCue.get(cue) || 0) < 70) return;
    this.lastCue.set(cue, now);
    this.unlock();
    const sound = new Audio(cues[cue]);
    sound.preload = "auto";
    sound.volume = this.preferences.effectsVolume;
    void sound.play().catch(() => undefined);
    this.haptic(strength);
  }

  haptic(strength: "light" | "medium" | "strong" = "light") {
    if (!this.preferences?.haptics || typeof navigator === "undefined" || !("vibrate" in navigator)) return;
    navigator.vibrate(strength === "strong" ? 28 : strength === "medium" ? 16 : 8);
  }

  suspend() { this.music?.pause(); }
  resume() { if (this.phase && !document.hidden) void this.startPhase(this.phase); }
}

export const gameFeedback = new GameFeedback();
