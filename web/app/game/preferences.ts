export interface GamePreferences {
  musicVolume: number;
  effectsVolume: number;
  haptics: boolean;
  reducedMotion: boolean;
  captions: boolean;
  introSeen: boolean;
}
export const DEFAULT_PREFERENCES: GamePreferences = {
  musicVolume: 0.65,
  effectsVolume: 0.8,
  haptics: true,
  reducedMotion: false,
  captions: true,
  introSeen: false,
};

export function normalizePreferences(value: Partial<GamePreferences> | undefined): GamePreferences {
  return {
    ...DEFAULT_PREFERENCES,
    ...value,
    musicVolume: Math.min(1, Math.max(0, Number(value?.musicVolume ?? DEFAULT_PREFERENCES.musicVolume))),
    effectsVolume: Math.min(1, Math.max(0, Number(value?.effectsVolume ?? DEFAULT_PREFERENCES.effectsVolume))),
  };
}
