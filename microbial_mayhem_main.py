#!/usr/bin/env python3

#this is the file where the main scripting will go
#it is NOT the class file, it is NOT a method/function file

#The following lines import all of our methods in our class
import sec_sys


#this is the main function where things are run
def main():
  print('Welcome to Microbial Mayhem!\nChoose two microbes to fight!')
  user_in = input('Press o +return for microbe options: ')
  if user_in == 'o':
    print('M. tuberculosis\nV. paramaris\nA. nidulans')
    microbe_a_species = input('Type in your choice for Microbe A: ')
    #should be an integer value, from 1-100 
    microbe_a_colony = input('Please enter the size of your colony, size 1-1000: ') 
    #a yes or a no
    microbe_a_sec = sec_sys.calc_secretion(input('Does your microbe have a secretion system? Yes or No?: '))
 
    #now, define b
    microbe_b_species = input('Type in your choice for Microbe B: ')
    #should be an integer value, from 1-100 
    microbe_b_colony = input('Please enter the size of your colony, size 1-1000: ')
    #a yes or a no
    microbe_b_sec = sec_sys.calc_secretion(input('Does your microbe have a secretion system? Yes or No?: '))
  
    #enter one environment for the microbes to battle
    microbe_env = input('Please enter one of the following environments where your microbes will battle: Alkaline, Hot, Cold, Acidic, Salty: ')
    #microbes are set
    print(f'Microbe A is {microbe_a_species} and Microbe B is {microbe_b_species}. Lets battle!')
  #now, call class attributes - working on this now  



#this is the battle function, which compares the score of microbe A and microbe B
  def battle(microbeA,microbeB):
    if microbeA.compete > microbeB.compete:
      return microbeA
    elif microbeB.compete > microbeA.compete:
      return microbeB
    else:
      return microbeA, microbeB    
#After A and B fight
#microbe_a_total =
#microbe_b_total =


if __name__ == "__main__":
  main()
