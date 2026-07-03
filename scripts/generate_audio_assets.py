#!/usr/bin/env python3
"""Generate Microbial Mayhem's original lightweight PCM audio assets.

The sounds are synthesized from simple waveforms and deterministic noise. They
contain no samples, recordings, or third-party musical material.
"""
from __future__ import annotations

import math
import random
import struct
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "assets" / "audio"
SAMPLE_RATE = 22_050
TAU = math.tau


def tone(frequency: float, t: float, shape: str = "sine") -> float:
    phase = (frequency * t) % 1.0
    if shape == "triangle":
        return 1.0 - 4.0 * abs(phase - .5)
    if shape == "square":
        return 1.0 if phase < .5 else -1.0
    return math.sin(TAU * phase)


def pulse(t: float, interval: float, decay: float) -> float:
    return math.exp(-((t % interval) / decay))


def write_wav(path: Path, duration: float, render) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frames = bytearray()
    total = round(duration * SAMPLE_RATE)
    for index in range(total):
        t = index / SAMPLE_RATE
        value = max(-1.0, min(1.0, render(t)))
        frames.extend(struct.pack("<h", round(value * 32767)))
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(SAMPLE_RATE)
        output.writeframes(frames)


def soft_edges(t: float, duration: float, edge: float = .08) -> float:
    return min(1.0, t / edge, (duration - t) / edge)


def setup_theme(t: float) -> float:
    duration = 12.0
    notes = (261.63, 311.13, 392.0, 466.16, 392.0, 311.13, 349.23, 466.16)
    note = notes[int(t / .375) % len(notes)]
    local = t % .375
    pluck = math.exp(-local * 7.5) * tone(note, t, "triangle")
    shimmer = math.exp(-local * 4.0) * tone(note * 2, t) * .18
    pad = sum(tone(freq, t) for freq in (65.41, 77.78, 98.0)) / 3
    bubble = tone(523.25 + 12 * math.sin(t * 1.7), t) * pulse(t + .11, 1.5, .08)
    return soft_edges(t, duration) * (.20 * pluck + .07 * shimmer + .075 * pad + .025 * bubble)


def battle_theme(t: float) -> float:
    duration = 8.0
    beat = .4
    roots = (65.41, 65.41, 77.78, 58.27, 65.41, 87.31, 77.78, 58.27)
    root = roots[int(t / beat) % len(roots)]
    bass = tone(root, t, "triangle") * (.55 + .45 * pulse(t, beat, .13))
    kick_age = t % beat
    kick = math.sin(TAU * (68 - 40 * min(kick_age / .16, 1)) * kick_age) * math.exp(-kick_age * 18)
    snare_age = (t + beat) % (beat * 2)
    snare_noise = random.Random(int(t * SAMPLE_RATE) + 811).uniform(-1, 1)
    snare = snare_noise * math.exp(-snare_age * 22) if snare_age < .18 else 0
    hat_age = t % (beat / 2)
    hat_noise = random.Random(int(t * SAMPLE_RATE) + 293).uniform(-1, 1)
    hat = hat_noise * math.exp(-hat_age * 55)
    lead_notes = (261.63, 311.13, 392.0, 349.23, 466.16, 392.0, 311.13, 293.66)
    lead = tone(lead_notes[int(t / .2) % len(lead_notes)], t, "square") * pulse(t, .2, .07)
    return soft_edges(t, duration, .05) * (.14 * bass + .22 * kick + .055 * snare + .018 * hat + .045 * lead)


def results_theme(t: float) -> float:
    duration = 12.0
    pad = sum(tone(freq, t) for freq in (55.0, 82.41, 110.0, 146.83)) / 4
    slow = .65 + .35 * math.sin(TAU * t / 6)
    bell_notes = (220.0, 277.18, 329.63, 415.30, 329.63, 246.94)
    bell_local = t % 2.0
    bell = tone(bell_notes[int(t / 2) % len(bell_notes)], t) * math.exp(-bell_local * 2.1)
    overtone = tone(bell_notes[int(t / 2) % len(bell_notes)] * 2.01, t) * math.exp(-bell_local * 3.5)
    strange = tone(174.61 + 7 * math.sin(t * .37), t) * .025
    return soft_edges(t, duration, .12) * (.09 * pad * slow + .075 * bell + .025 * overtone + strange)


def effect(duration: float, recipe, name: str) -> None:
    write_wav(AUDIO / "sfx" / f"{name}.wav", duration, recipe)


def make_effects() -> None:
    effect(.12, lambda t: .25 * tone(560 + 900 * t, t) * math.exp(-t * 24), "click")
    effect(.22, lambda t: .28 * tone(440 + 700 * t, t, "triangle") * math.exp(-t * 11), "select")
    effect(.30, lambda t: .34 * tone(185 + 420 * t, t, "triangle") * math.exp(-t * 8), "attack")
    effect(.28, lambda t: .48 * random.Random(int(t * SAMPLE_RATE) + 17).uniform(-1, 1) * math.exp(-t * 17) + .18 * tone(75, t) * math.exp(-t * 9), "impact")
    effect(.58, lambda t: .24 * tone(260 + 720 * t, t) * math.exp(-t * 2.8) + .10 * tone(520 + 900 * t, t), "ability")
    effect(.72, lambda t: .20 * tone(140 + 1000 * t, t, "triangle") * math.exp(-t * 2) + .08 * tone(880, t) * math.sin(math.pi * min(1, t / .5)), "arsenal")
    effect(.42, lambda t: .20 * tone(95, t, "triangle") * math.exp(-t * 5) + .12 * random.Random(int(t * SAMPLE_RATE) + 99).uniform(-1, 1) * math.exp(-t * 10), "clash")
    effect(.62, lambda t: .42 * tone(max(42, 210 - 220 * t), t, "triangle") * math.exp(-t * 4) + .18 * random.Random(int(t * SAMPLE_RATE) + 71).uniform(-1, 1) * math.exp(-t * 9), "final_hit")
    victory_notes = (523.25, 659.25, 783.99, 1046.5)
    effect(1.0, lambda t: .20 * tone(victory_notes[min(3, int(t / .2))], t) * math.exp(-(t % .2) * 3), "victory")
    defeat_notes = (392.0, 311.13, 246.94, 196.0)
    effect(1.0, lambda t: .18 * tone(defeat_notes[min(3, int(t / .22))], t, "triangle") * math.exp(-(t % .22) * 3), "defeat")


def main() -> None:
    write_wav(AUDIO / "music" / "setup_theme.wav", 12.0, setup_theme)
    write_wav(AUDIO / "music" / "battle_theme.wav", 8.0, battle_theme)
    write_wav(AUDIO / "music" / "results_theme.wav", 12.0, results_theme)
    make_effects()
    print(f"Generated original audio in {AUDIO}")


if __name__ == "__main__":
    main()
