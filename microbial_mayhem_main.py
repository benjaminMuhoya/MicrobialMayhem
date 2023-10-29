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


#from Env_scoring import calculate_score_env
#this is the main function where things are run
def main():
  print('Welcome to Microbial Mayhem!')
  with open('pic2.txt','r') as pic_obj:
    print(pic_obj.read())
  
  user_in = input('Press o +return for microbe options: ')
  
  if user_in == 'o':
    print('M.tuberculosis\nV.maris\nM.alcalica\nS.aureaus\nV.neptunius\nP.fluorescens\nK.pneumoniae\nE.coli')
    
    #define microbe a
    a_species = input('Type in your choice for Microbe A: ')
    
    #should be an integer value, from 1-100 
    microbe_a_colony = colony_size.colony_growth() 
    
    #a yes or a no
    microbe_a_sec = sec_sys.calc_secretion(general_usr_in.yes_no_input(input('Does your microbe have a secretion system? These area toxin-injection weapons for attacking neighbors.\nYes or No?:'))

    #now, define microbe b
    b_species = input('Type in your choice for Microbe B: ')
    
    #should be an integer value, from 1-100 
    microbe_b_colony = colony_size.colony_growth()
    
    #a yes or a no
    microbe_b_sec = sec_sys.calc_secretion(input('Does your microbe have a secretion system? Yes or No?: '))
  
    #enter one environment for the microbes to battle
#    microbe_env = calculate_score_env('env')


##input('Please enter one of the following environments where your microbes will battle: Alkaline, Hot, Cold, Acidic, Salty: ')
    #microbes are set
 # print(f'Microbe A is {microbe_a_species} and Microbe B is {microbe_b_species}. Lets battle!')
    env = input("Where do you want to fight? Choose your Environment: Salty, Alkaline, Hot, Cold, Acidic, or in drugs: ")
    microbe_env = Env_scoring.calculate_score_env('env')

    print(f'Microbe A is {microbe_a_species} and Microbe B is {microbe_b_species}. Lets battle!')

  #now, call class attributes - working on this now
  #Need growth rate and kin selection from dictionary that Clare and Tiffany are making 
  ##microbe_B_def = Microbe(microbe_b_species,[ENTER GROWTH RATE],[ENTER KIN SELECT])
  

#if microbe_a_total > microbe_b_total:
 # print ('Microbe A wins!')
#if microbe_b_total > microbe_a_total:
 # print('Microbe B wins!')
#if microbe_a_total == microbe_b_total:
 # print('Microbe A and B both survived!')

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
