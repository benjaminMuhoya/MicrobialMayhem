#! /usr/bin/env python3

## Code to make sure that user inputs options at the beginning of the game

def option_menu():
  exit_while = 0
  while exit_while == 0:
    user_in = input('\nPress o +return for microbe options: ')
    try:
      if user_in == "o" or user_in=="O":
        exit_while = 1
      else:
        print("Please select a valid option")
    except ValueError:
      print("Please select a valid option")
  return user_in

#option_menu()
