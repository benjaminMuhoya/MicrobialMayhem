#!/usr/bin/env python3
"""Graphical interface for playing Microbial Mayhem."""

from __future__ import annotations

import random
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

import colony_size
import microbe_class
import Env_scoring
import sec_sys
from microbe_info_output import output_statement
from species_dict import spp_dict

try:  # playsound is optional – the GUI still works without it
  from playsound import playsound
except ImportError:  # pragma: no cover - optional dependency
  playsound = None


ASCII_ART_FILE = Path(__file__).with_name("pic3.txt")
INTRO_AUDIO_FILE = Path(__file__).with_name("microbial_mayhem_intro.mp3")


class MicrobialMayhemApp:
  """Tkinter front-end that wraps the original game logic."""

  def __init__(self, root: tk.Tk) -> None:
    self.root = root
    self.root.title("Microbial Mayhem")
    self.root.geometry("840x720")

    self.species_options = [
      ("Escherichia coli (E.coli)", "E.coli"),
      ("Mycobacterium tuberculosis (M.tuberculosis)", "M.tuberculosis"),
      ("Verrucosispora maris (V.maris)", "V.maris"),
      ("Methylophaga alcalica (M.alcalica)", "M.alcalica"),
      ("Staphylococcus aureus (S.aureus)", "S.aureus"),
      ("Vibrio neptunius (V.neptunius)", "V.neptunius"),
      ("Pseudomonas fluorescens (P.fluorescens)", "P.fluorescens"),
      ("Klebsiella pneumoniae (K.pneumoniae)", "K.pneumoniae"),
    ]
    self.species_lookup = {key: label for (label, key) in self.species_options}

    self.environment_options = [
      ("Salty", "Salty"),
      ("Alkaline", "Alkaline"),
      ("Hot", "Hot"),
      ("Cold", "Cold"),
      ("Acidic", "Acidic"),
      ("In the presence of antibiotics", "In the presence of antibiotics"),
    ]

    self.superpower_options = [
      ("Halophile", "Halophile"),
      ("Alkaliphile", "Alkaliphile"),
      ("Acidophile", "Acidophile"),
      ("Thermophile", "Thermophile"),
      ("Cryophile", "Cryophile"),
      ("Drug resistant", "Drug resistant"),
      ("None :(", "None :("),
    ]
    self.superpower_lookup = {label: value for (label, value) in self.superpower_options}

    self.start_frame: ttk.Frame | None = None
    self.form_frame: ttk.Frame | None = None
    self.result_text: tk.Text | None = None
    self.summary_var = tk.StringVar()
    self.opponent_var = tk.StringVar()

    self._setup_styles()
    self._build_start_screen()

  # ------------------------------------------------------------------ UI setup
  def _setup_styles(self) -> None:
    style = ttk.Style(self.root)
    style.configure("TFrame", padding=20)
    style.configure("Title.TLabel", font=("Helvetica", 18, "bold"))
    style.configure("Subtitle.TLabel", font=("Helvetica", 12))
    style.configure("Section.TLabel", font=("Helvetica", 12, "bold"))
    style.configure("Summary.TLabel", font=("Helvetica", 11))
    style.configure("TButton", padding=(10, 5))

  def _build_start_screen(self) -> None:
    if self.form_frame is not None:
      self.form_frame.destroy()
      self.form_frame = None

    self.start_frame = ttk.Frame(self.root)
    self.start_frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(
      self.start_frame,
      text="Welcome to Microbial Mayhem!",
      style="Title.TLabel",
    ).pack(pady=(0, 10))

    art = self._load_ascii_art()
    art_label = tk.Label(
      self.start_frame,
      text=art,
      font=("Courier New", 10),
      justify=tk.LEFT,
      bg="black",
      fg="#00ff9c",
      bd=5,
      relief=tk.RIDGE,
      padx=10,
      pady=10,
    )
    art_label.pack(fill=tk.X, padx=10, pady=(0, 15))

    ttk.Label(
      self.start_frame,
      text="Prepare your champion microbe and take on a random challenger!",
      style="Subtitle.TLabel",
    ).pack(pady=(0, 20))

    button_frame = ttk.Frame(self.start_frame)
    button_frame.pack()

    ttk.Button(
      button_frame,
      text="Start Battle",
      command=self._build_form_screen,
    ).grid(row=0, column=0, padx=5)

    ttk.Button(
      button_frame,
      text="Play Intro Sound",
      command=self._play_intro_audio,
    ).grid(row=0, column=1, padx=5)

    if playsound is None:
      ttk.Label(
        self.start_frame,
        text="(Install the playsound package to enable the intro theme)",
        foreground="#888888",
      ).pack(pady=(10, 0))

  def _build_form_screen(self) -> None:
    if self.start_frame is not None:
      self.start_frame.destroy()
      self.start_frame = None

    self.summary_var.set("")
    self.opponent_var.set("")

    self.form_frame = ttk.Frame(self.root)
    self.form_frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(
      self.form_frame,
      text="Customize Your Microbe",
      style="Title.TLabel",
    ).grid(row=0, column=0, columnspan=2, pady=(0, 20))

    # Microbe selection -------------------------------------------------
    ttk.Label(
      self.form_frame,
      text="Select your fighter:",
      style="Section.TLabel",
    ).grid(row=1, column=0, sticky=tk.W)
    self.species_var = tk.StringVar(value=self.species_options[0][0])
    species_combo = ttk.Combobox(
      self.form_frame,
      textvariable=self.species_var,
      values=[label for (label, _) in self.species_options],
      state="readonly",
      width=45,
    )
    species_combo.grid(row=1, column=1, sticky=tk.EW, pady=5)

    # Colony size -------------------------------------------------------
    ttk.Label(
      self.form_frame,
      text="Colony size (CFU):",
      style="Section.TLabel",
    ).grid(row=2, column=0, sticky=tk.W)
    self.colony_var = tk.DoubleVar(value=100)
    colony_scale = ttk.Scale(
      self.form_frame,
      from_=0,
      to=1000,
      orient=tk.HORIZONTAL,
      variable=self.colony_var,
      command=lambda *_: self._update_colony_readout(),
    )
    colony_scale.grid(row=2, column=1, sticky=tk.EW, pady=5)
    self.colony_readout = ttk.Label(self.form_frame, text="100")
    self.colony_readout.grid(row=2, column=2, padx=(10, 0))

    # Secretion system --------------------------------------------------
    ttk.Label(
      self.form_frame,
      text="Secretion system:",
      style="Section.TLabel",
    ).grid(row=3, column=0, sticky=tk.W)
    self.secretion_var = tk.StringVar(value="YES")
    secretion_frame = ttk.Frame(self.form_frame)
    secretion_frame.grid(row=3, column=1, sticky=tk.W, pady=5)
    ttk.Radiobutton(
      secretion_frame,
      text="Yes",
      value="YES",
      variable=self.secretion_var,
    ).pack(side=tk.LEFT, padx=5)
    ttk.Radiobutton(
      secretion_frame,
      text="No",
      value="NO",
      variable=self.secretion_var,
    ).pack(side=tk.LEFT, padx=5)

    # Environment -------------------------------------------------------
    ttk.Label(
      self.form_frame,
      text="Battlefield environment:",
      style="Section.TLabel",
    ).grid(row=4, column=0, sticky=tk.W)
    self.environment_var = tk.StringVar(value=self.environment_options[0][0])
    environment_combo = ttk.Combobox(
      self.form_frame,
      textvariable=self.environment_var,
      values=[label for (label, _) in self.environment_options],
      state="readonly",
      width=45,
    )
    environment_combo.grid(row=4, column=1, sticky=tk.EW, pady=5)

    # Super power -------------------------------------------------------
    ttk.Label(
      self.form_frame,
      text="Microbe super power:",
      style="Section.TLabel",
    ).grid(row=5, column=0, sticky=tk.W)
    self.superpower_var = tk.StringVar(value=self.superpower_options[-1][0])
    superpower_combo = ttk.Combobox(
      self.form_frame,
      textvariable=self.superpower_var,
      values=[label for (label, _) in self.superpower_options],
      state="readonly",
      width=45,
    )
    superpower_combo.grid(row=5, column=1, sticky=tk.EW, pady=5)

    # Action buttons ----------------------------------------------------
    ttk.Button(
      self.form_frame,
      text="Battle!",
      command=self._run_battle,
    ).grid(row=6, column=0, columnspan=2, pady=(20, 10))

    ttk.Button(
      self.form_frame,
      text="Start Over",
      command=self._build_start_screen,
    ).grid(row=6, column=2, padx=10)

    # Results -----------------------------------------------------------
    separator = ttk.Separator(self.form_frame, orient=tk.HORIZONTAL)
    separator.grid(row=7, column=0, columnspan=3, sticky=tk.EW, pady=15)

    ttk.Label(
      self.form_frame,
      textvariable=self.opponent_var,
      style="Summary.TLabel",
    ).grid(row=8, column=0, columnspan=3, sticky=tk.W)

    ttk.Label(
      self.form_frame,
      textvariable=self.summary_var,
      style="Summary.TLabel",
    ).grid(row=9, column=0, columnspan=3, sticky=tk.W, pady=(5, 10))

    self.result_text = tk.Text(
      self.form_frame,
      height=10,
      wrap=tk.WORD,
      font=("Helvetica", 11),
    )
    self.result_text.grid(row=10, column=0, columnspan=3, sticky=tk.NSEW)
    self.form_frame.rowconfigure(10, weight=1)
    self.form_frame.columnconfigure(1, weight=1)
    self.result_text.configure(state=tk.DISABLED)
    self._update_result_panel("Ready to battle! Configure your microbe and press Battle!.")

  # ---------------------------------------------------------------- battle
  def _update_colony_readout(self) -> None:
    self.colony_readout.configure(text=str(int(float(self.colony_var.get()))))

  def _run_battle(self) -> None:
    try:
      colony_value = int(float(self.colony_var.get()))
    except (TypeError, ValueError):
      messagebox.showerror("Invalid value", "Please choose a colony size between 0 and 1000.")
      return

    species_display = self.species_var.get()
    species_key = next((key for (label, key) in self.species_options if label == species_display), None)
    if species_key is None:
      messagebox.showerror("Selection error", "Please select a microbe fighter.")
      return

    colony_score = colony_size.colony_growth(colony_value, show_feedback=False)
    secretion_score = sec_sys.calc_secretion(self.secretion_var.get())

    environment_display = self.environment_var.get()
    environment_value = next((value for (label, value) in self.environment_options if label == environment_display), environment_display)

    superpower_display = self.superpower_var.get()
    superpower_value = self.superpower_lookup.get(superpower_display, None)

    env_score = Env_scoring.calculate_score_env(environment_value, special_attributes=superpower_value)

    if superpower_display.startswith("None"):
      superpower_label = "None"
    else:
      superpower_label = superpower_display

    # Prepare the opponent --------------------------------------------
    species_list = list(spp_dict.keys())
    opponent_species_key = random.choice(species_list)
    opponent_display = self.species_lookup.get(opponent_species_key, opponent_species_key)
    opponent_colony_score = random.choice([0, 5, 10])
    opponent_secretion_score = sec_sys.calc_secretion(random.choice(["YES", "NO"]))

    microbe_a = microbe_class.Microbe(
      species_key,
      spp_dict[species_key]['growth_rate'],
      spp_dict[species_key]['kin_select'],
    )
    microbe_b = microbe_class.Microbe(
      opponent_species_key,
      spp_dict[opponent_species_key]['growth_rate'],
      spp_dict[opponent_species_key]['kin_select'],
    )

    total_a = float(microbe_a.strength()) + float(colony_score * microbe_a.growth_rate) + float(env_score) + float(secretion_score)
    total_b = float(microbe_b.strength()) + float(opponent_colony_score * microbe_b.growth_rate) + float(env_score) + float(opponent_secretion_score)

    if total_a > total_b:
      user_winner = 'A'
      microbe_winner = species_key
    elif total_b > total_a:
      user_winner = 'B'
      microbe_winner = opponent_species_key
    else:
      user_winner = 'tie'
      microbe_winner = f"{species_key} and {opponent_species_key}"

    summary_lines = [
      f"Your microbe: {species_display} (CFU {colony_value}, colony score {colony_score})",
      f"Secretion system score: {secretion_score}",
      f"Super power: {superpower_label}",
      f"Environment: {environment_display} (bonus {env_score})",
      f"Your total score: {total_a:.1f} | Opponent total score: {total_b:.1f}",
    ]

    opponent_summary = (
      f"Opponent: {opponent_display} (colony score {opponent_colony_score}, "
      f"secretion score {opponent_secretion_score})"
    )

    self.opponent_var.set(opponent_summary)
    self.summary_var.set("\n".join(summary_lines))

    result_message = output_statement(user_winner, microbe_winner)
    self._update_result_panel(result_message)

  # ------------------------------------------------------------ utilities
  def _update_result_panel(self, message: str) -> None:
    if self.result_text is None:
      return

    self.result_text.configure(state=tk.NORMAL)
    self.result_text.delete("1.0", tk.END)
    self.result_text.insert(tk.END, message)
    self.result_text.configure(state=tk.DISABLED)

  def _load_ascii_art(self) -> str:
    if ASCII_ART_FILE.exists():
      return ASCII_ART_FILE.read_text(encoding="utf-8")
    return "Prepare for battle!"

  def _play_intro_audio(self) -> None:
    if playsound is None:
      messagebox.showinfo(
        "Audio unavailable",
        "Install the 'playsound' package to enable audio playback.",
      )
      return

    if not INTRO_AUDIO_FILE.exists():
      messagebox.showerror("Audio missing", "Could not find the intro soundtrack file.")
      return

    try:
      playsound(str(INTRO_AUDIO_FILE))
    except Exception as exc:  # pragma: no cover - best effort playback
      messagebox.showerror("Playback error", f"Could not play audio: {exc}")


def main() -> None:
  root = tk.Tk()
  MicrobialMayhemApp(root)
  root.mainloop()


if __name__ == "__main__":
  main()
