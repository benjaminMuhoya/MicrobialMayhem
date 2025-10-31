#!/usr/bin/env python
"""Utility functions for determining colony size scores."""

# Need to make a function so the program can run more than once
def colony_growth(cfu=None, show_feedback=True):
  """Return the colony growth score.

  When ``cfu`` is ``None`` the user is prompted for input via the terminal,
  preserving the original behaviour for command line play. When a numeric
  ``cfu`` value is provided the score is calculated directly without prompting
  (which makes the function usable from the GUI).

  The ``show_feedback`` flag controls whether descriptive feedback is printed
  to stdout. It defaults to ``True`` for CLI use and should be set to ``False``
  when the caller wants to handle feedback elsewhere.
  """

  if cfu is None:
    cfu = int(input('\nHow big is you colony? Choose a number between 0 and 1000: '))
  else:
    cfu = int(cfu)

  if cfu < 10:
    colony_growth_score = 0
    message = "Tiny colony, you're risking it!"
  elif 10 <= cfu <= 100:
    message = "Decent-sized colony"
    colony_growth_score = 5
  elif 100 < cfu <= 1000:
    message = "Huuuge colony, you're playing safe"
    colony_growth_score = 10
  else:
    message = "That colony is off the charts!"
    colony_growth_score = 10

  if show_feedback:
    print(f'CFU: {cfu} - {message}')
    print(f'Score: {colony_growth_score}')

  return colony_growth_score
# To close the function - type the name ()

if __name__ == '__main__':  # to make sure that this program doesn't run where it's imported, but only when we call it specifically
  colony_growth()
