#!/usr/bin/env python3

#this is the file where the main scripting will go
#it is NOT the class file, it is NOT a method/function file

#The following lines import all of our methods into our main file
import sys
import colony_size
import sec_sys
import math
import json
import os
import microbe_class
import general_usr_in
import Env_scoring
import ANIME_simple
from species_dict import spp_dict
import random
from microbe_info_output import output_statement 
from species_menu import species_menu
from option_menu_check import option_menu
from env_menu import env_menu
from playsound import playsound

#this is the main function where things are run
def main():
  print('\nWelcome to Microbial Mayhem!\n')
  
  #print ascii art 
  with open('pic3.txt','r') as pic_obj:
    print(pic_obj.read())

  #play Tiffany's opening soundtrack
  playsound('./microbial_mayhem_intro.mp3')
  
  # user_in = input('\nPress o +return for microbe options: ')
  user_in = option_menu()    

  if user_in == 'o':
    # microbe_a_species = input('\nType in your choice for Microbe A: ')
    microbe_a_species = species_menu()    

    # should be an integer value, from 1-100 
    microbe_a_colony = colony_size.colony_growth() 
    
    #a yes or a no
    microbe_a_sec = sec_sys.calc_secretion(general_usr_in.yes_no_input(input('\nDoes your microbe have a secretion system? These area toxin-injection weapons for attacking neighbors.\nYes or No?: ')))

    # set random microbe b
    species_list = list(spp_dict.keys()) 
    rand_b_species = random.choice(species_list)
    # assigns microbe b a random colony score
    rand_b_colony = random.choice([0, 5, 10])
    # assigns microbe b either yes or no for secretion system
    rand_b_sec = sec_sys.calc_secretion(random.choice(['Yes', 'No']))    
    # tells user who their opponent is
    print(f'\nYour opponent is {rand_b_species}!\n')
    # microbes are set
    # get environment from env_menu function
    env = env_menu()
    env_score = Env_scoring.calculate_score_env('env')
    # informs user of the two mircobes who are competing
    print(f'\nYour microbe is {microbe_a_species} and your opponent is {rand_b_species}. Lets battle!\n')
  # runs microbe A through all of the class methods
  microbeA = microbe_class.Microbe(microbe_a_species, spp_dict[microbe_a_species]['growth_rate'], spp_dict[microbe_a_species]['kin_select'])
  # runs microbe B through all of the class methods
  randB = microbe_class.Microbe(rand_b_species, spp_dict[rand_b_species]['growth_rate'], spp_dict[rand_b_species]['kin_select'])
  # sums the total score from each of the functions for microbe A, but not using the sum function!
  A_total = float(microbeA.strength()) + float((microbe_a_colony * microbeA.growth_rate)) + float(env_score) + float(microbe_a_sec)
  # sums the total score from each of the functions for microbe B, but not using the sum function!
  B_total = float(randB.strength()) + float((rand_b_colony * randB.growth_rate)) + float(env_score) + float(rand_b_sec)

  # Who wins? A or B?
  if A_total > B_total:
    user_winner = 'A'
    microbe_winner = microbe_a_species
  if A_total < B_total:
    user_winner = 'B'
    microbe_winner = rand_b_species
  if A_total == B_total:
    user_winner = 'tie'
    microbe_winner = f'{microbe_a_species} and {rand_b_species}'

  print(output_statement(user_winner, microbe_winner))
  ANIME_simple.Gui_pop('image') 


if __name__ == "__main__":
  main()
