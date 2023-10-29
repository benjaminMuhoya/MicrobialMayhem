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
from Env_scoring import calculate_score_env 
from species_dict import spp_dict # dictionary of species attributes

def main():
  
  print('Welcome to Microbial Mayhem!\nChoose two microbes to fight!')
  
  user_in = input('Press o +return for microbe options: ')
  
  if user_in == 'o':
    print('M.tuberculosis\nV.maris\nM.alcalica\nS.aureaus\nV.neptunius\nP.fluorescens\nK.pneumoniae\nE.coli')
    
    #define microbe a
    a_species = input('Type in your choice for Microbe A: ')
    
    #should be an integer value, from 1-100 
    microbe_a_colony = colony_size.colony_growth() 
    
    #a yes or a no
    microbe_a_sec = sec_sys.calc_secretion(input('Does your microbe have a type VI secretion system? These area toxin-injection weapons for attacking neighbors.\nYes or No?: '))

    #now, define microbe b
    b_species = input('Type in your choice for Microbe B: ')
    
    #should be an integer value, from 1-100 
    microbe_b_colony = colony_size.colony_growth()
    
    #a yes or a no
    microbe_b_sec = sec_sys.calc_secretion(input('Does your microbe have a secretion system? Yes or No?: '))
  
    #enter one environment for the microbes to battle
#    env = input('Please enter one of the following environments where your microbes will battle: Alkaline, Hot, Cold, Acidic, Salty: ')
    
#    env_score = calculate_env_score(env)

    print(f'Microbe A is {microbe_a_species} and Microbe B is {microbe_b_species}. Lets battle!')

  #now, call class attributes - working on this now
  #Need growth rate and kin selection from dictionary that Clare and Tiffany are making 

  microbeA = microbe_class.Microbe(species = a_species, growth_rate = int(spp_dict[a_species][growth_rate]), kin_select = int(spp_dict[a_species][kin_select]))
  microbeB = microve_class.Microbe(species = b_species, growth_rate = int(spp_dict[microbe_b_species][growth_rate]), kin_select = int(spp_dict[b_species][kin_select]))

  A_total = sum(microbeA.score(), (colony_size * microbeA.growth_rate())) #add in env_score
  B_total = sum(microbeB.score(), (colony_size * microbeB.growth_rate())) #add in env_score

  #Who wins? A or B?
 
  winner = max(A_total, B_total)

# determine winner by comparing Microbe() scores

#  def battle(microbeA,microbeB):
#    if microbeA.compete > microbeB.compete:
#      return microbeA
#    elif microbeB.compete > microbeA.compete:
#      return microbeB
#    else:
#      return microbeA, microbeB    

if __name__ == "__main__":
  main()
