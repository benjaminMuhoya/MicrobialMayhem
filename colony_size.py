#!/usr/bin/env python
# Need to make a function so the program can run more than once
def colony_growth(cfu=0):
 cfu=int(input('How big is you colony? Choose a number between 0 and 1000'))
 #print(cfu)
 if cfu<10:
   colony_growth_score = 0
   message="This microbe is shit"
   print(f'CFU: {cfu} - {message}')
   print(f'Score: {colony_growth_score}')
 if 10<=cfu<=100:
   message="This microbe is doing a decent job"
   colony_growth_score = 5
   print(f'CFU: {cfu} - {message}')
   print(f'Score: {colony_growth_score}')
 if 100<cfu<=1000:
   message="This microbe rocks!"
   colony_growth_score = 10
   print(f'CFU: {cfu} - {message}')
   print(f'Score: {colony_growth_score}')  
   
 return colony_growth
# To close the function - type the name () 
colony_growth()
 

