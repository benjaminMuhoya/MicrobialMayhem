#!/usr/bin/env python
# Need to make a function so the program can run more than once
def colony_growth(cfu=0):
 cfu=int(input('How big is you colony? Choose a number between 0 and 1000'))
 #print(cfu)
 if cfu<10:
   colony_growth_score = 0
   message="Tiny colony, you're risking it!"
   print(f'CFU: {cfu} - {message}')
   print(f'Score: {colony_growth_score}')
 if 10<=cfu<=100:
   message="Decent-sized colony"
   colony_growth_score = 5
   print(f'CFU: {cfu} - {message}')
   print(f'Score: {colony_growth_score}')
 if 100<cfu<=1000:
   message="Huuuge colony, you're playing safe"
   colony_growth_score = 10
   print(f'CFU: {cfu} - {message}')
   print(f'Score: {colony_growth_score}')  
   
 return colony_growth
# To close the function - type the name () 

if __name__ == '__main__': #to make sure that this program doesn't run where it's imported, but only when we call it specifically
  colony_growth()
 

