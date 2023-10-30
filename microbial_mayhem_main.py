#!/usr/bin/env python3

#this is the file where the main scripting will go
#it is NOT the class file, it is NOT a method/function file

#The following lines import all of our methods into our main file

import colony_size
import sec_sys
import math
import json
import os
import microbe_class
import general_usr_in
import Env_scoring
from species_dict import spp_dict
import random
from microbe_info_output import output_statement 


#from Env_scoring import calculate_score_env
#this is the main function where things are run
def main():
  print('\nWelcome to Microbial Mayhem!\n')
  with open('pic2.txt','r') as pic_obj:
    print(pic_obj.read())
  
  user_in = input('\nPress o +return for microbe options: ')
  
  if user_in == 'o':
    print('\nM.tuberculosis\nV.maris\nM.alcalica\nS.aureaus\nV.neptunius\nP.fluorescens\nK.pneumoniae\nE.coli\n')
    
    #define microbe a
    microbe_a_species = input('\nType in your choice for Microbe A: ')
    
    #should be an integer value, from 1-100 
    microbe_a_colony = colony_size.colony_growth() 
    
    #a yes or a no
    microbe_a_sec = sec_sys.calc_secretion(general_usr_in.yes_no_input(input('\nDoes your microbe have a secretion system? These area toxin-injection weapons for attacking neighbors.\nYes or No?: ')))

    ## set random microbe b
    species_list = list(spp_dict.keys())

    rand_b_species = random.choice(species_list)
    rand_b_colony = random.randrange(1,1000)
    rand_b_sec = sec_sys.calc_secretion(random.choice(['Yes', 'No']))
    
    print(f'\nYour opponent is {rand_b_species}!\n')
##input('Please enter one of the following environments where your microbes will battle: Alkaline, Hot, Cold, Acidic, Salty: ')
    #microbes are set
 # print(f'Microbe A is {microbe_a_species} and Microbe B is {microbe_b_species}. Lets battle!')
    env = input("\nWhere do you want to fight? Choose your Environment: Salty, Alkaline, Hot, Cold, Acidic, or Antibiotic culture ")
    env_score = Env_scoring.calculate_score_env('env')

    print(f'\nMicrobe A is {microbe_a_species} and Microbe B is {rand_b_species}. Lets battle!\n')

  microbeA = microbe_class.Microbe(microbe_a_species, spp_dict[microbe_a_species]['growth_rate'], spp_dict[microbe_a_species]['kin_select'])
##########################################This is the part that isn't working
  randB = microbe_class.Microbe(rand_b_species, spp_dict[rand_b_species]['growth_rate'], spp_dict[rand_b_species]['kin_select'])

  A_total = float(microbeA.strength()) + float((microbe_a_colony * microbeA.growth_rate)) + float(env_score) + float(microbe_a_sec)

  B_total = float(randB.strength()) + float((rand_b_colony * randB.growth_rate)) + float(env_score) + float(rand_b_sec)
#######################################
  #Who wins? A or B?
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



if __name__ == "__main__":
  main()
