#!/usr/bin/env python3

#this is the file where the main scripting will go
#it is NOT the class file, it is NOT a method/function file
def microbe_input(microbe_str):
  variable = ''
  if microbe_str:
    variable = microbe_str
  return(variable)

def microbe_env_inputs(pH,salt,temp)
  var1 = ''
  var2 = ''
  var3 = ''
  if pH:
    

#this is the main function where things are run
def main():
  print('Welcome to Microbial Mayhem!\nChoose two microbes to fight!')
  user_in = input('Press o for microbe a options')
  if user_in == 'o':
    print('Mycobacterium tuberculosis\nVerrucosis paramaris\nAspergillus nidulans')
    microbe_in_1 = (input('Type in which microbe you want microbe A to be by typing it in from the options'))
#define microbe a
    if microbe_input(microbe_in_1):
      microbe_a = microbe_in_1
      microbe_a_pH
      microbe_a_colony = int(input('What is the colony size?'))
      microbe_a_sec = input('Does your microbe have the type VI system?')
      print(f'Microbe A is: {microbe_a}. Now choose microbe B.')

#define microbe b
  microbe_in_2 = int(input('Type in which microbe you want microbe B to be by typing it in from the options'))
  if microbe_input(microbe_in_2):
    microbe_b = microbe_in_2
    microbe_b_env = int(input('What is the environment your microbe lives in? Enter a number.'))
    mircobe_b_colony = int(input('What is the colony size?'))
    microbe_b_sec = input('Does your microbe have the type VI system?')
    print(f'Microbe B is: {microbe_b}. Lets battle!')
    
#After A and B fight
#microbe_a_total =
#microbe_b_total =


if __name__ == "__main__":
  main()
