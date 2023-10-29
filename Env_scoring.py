#!/usr/bin/env python3
import sys
import re

##Define the Environment
##1. Ph [high vs low] ##2. Temp [high vs low] ##3. Salinity [high vs low] ##4. Presence of antibiotics
##>> Given the above info, I defined six extreme environments and everything else is Neutral/Temperate
##>> SPECIAL POWERS >> Bacteria will have special powers if the env is in its favor.
##POWER == Halophile,Acidophile, Alkaliphile, Cryophile, Thermophile, Drug_resistance
##Most bacteria are neutrophiles hence 0 ...Acidophiles[-10] and alkaliphiles [+10]
##Thermophile can survive well in high temp (hence the reasone some of their enzymes are used for experiment e.g. Taq polymerase in PCR), Low temp slows most bacteria down unless they are cryophiles that do well in low temp, and then there is rtp


##Halophiles can tolerate extreme salinity
env = input("Where do you want to fight? Choose your Environment")
def calculate_score_env(env):
  Extreme = ('Alkaline','Hot','Cold','Acidic','Salty', 'in drugs')
  Value_of_Env ={'extreme':-10, 'neutral':0}
  Super_power = ('Drug resistant','Halophile','Acidophile','Thermophile','Cryophile','Alkaliphile')
  Value_of_power = {'super_bug':100,'under_dog':0}
  Special_attributes = input("Does you Fighter have any super powers?")  
  if Special_attributes in Super_power:
    score = Value_of_power['super_bug']
  else:
    score = Value_of_power['under_dog']
  if env in Extreme:
    env_score = int(Value_of_Env['extreme'] + score)
  else:
    env_score = int(Value_of_Env['neutral'] + score)
  return env_score

##End of Class
Total_object = calculate_score_env(env)
print('Here is the score for each line checked', Total_object)
