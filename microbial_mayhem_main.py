#!/usr/bin/env python3

#this is the file where the main scripting will go
#it is NOT the class file, it is NOT a method/function file
def microbe_input(microbe_int):
  variable = 0
  if microbe_int == 1 or microbe_int == 2 or microbe_int == 3:
    variable = microbe_int
  return(variable)


def main():
  print('Welcome to Microbial Mayhem!\nChoose two microbes to fight!')
  user_in = input('Press o for microbe a options')
  if user_in == 'o':
    print('microbe1\nmicrobe2\nmicrobe3')
    microbe_in_1 = int(input('Type in which microbe you want microbe A to be by pressing 1, 2, or 3'))
#define microbe a
    if microbe_input(microbe_in_1) != 0:
      microbe_a = microbe_in_1
      microbe_a_env = int(input('What is the environment your microbe lives in? Enter a number.')) 
      microbe_a_colony = int(input('What is the colony size?'))
      microbe_a_sec = input('Does your microbe have the type VI system?')
      print(f'Microbe A is: microbe {microbe_a}. Now choose microbe B.')

#define microbe b
  microbe_in_2 = int(input('Type in which microbe you want microbe B to be by pressing 1, 2, or 3'))
  if microbe_input(microbe_in_2) != 0:
    microbe_b = microbe_in_2
    microbe_b_env = int(input('What is the environment your microbe lives in? Enter a number.'))
    mircobe_b_colony = int(input('What is the colony size?'))
    microbe_b_sec = input('Does your microbe have the type VI system?')
    print(f'Microbe B is: microbe {microbe_b}. Lets battle!')
    



if __name__ == "__main__":
  main()
