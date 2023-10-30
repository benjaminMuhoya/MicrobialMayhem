#!/usr/bin/env python3

from superpower_menu import superpower_menu 

##Define the Environment
##1. Ph [high vs low] ##2. Temp [high vs low] ##3. Salinity [high vs low] ##4. Presence of antibiotics
##>> Given the above info, I defined six extreme environments and everything else is Neutral/Temperate
##>> SPECIAL POWERS >> Bacteria will have special powers if the env is in its favor.
##POWER == Halophile,Acidophile, Alkaliphile, Cryophile, Thermophile, Drug_resistance
##Most bacteria are neutrophiles hence 0 ...Acidophiles[-10] and alkaliphiles [+10]
##Thermophile can survive well in high temp (hence the reasone some of their enzymes are used for experiment e.g. Taq polymerase in PCR), Low temp slows most bacteria down unless they are cryophiles that do well in low temp, and then there is rtp
##Halophiles can tolerate extreme salinity
def calculate_score_env(env):
  ##env = input("Where do you want to fight? Choose your Environment: Salty, Alkaline, Hot, Cold, Acidic, in drugs")  
  Extreme = ('Alkaline','Hot','Cold','Acidic','Salty', 'in drugs')
  Value_of_Env ={'extreme':-10, 'neutral':0}

  Super_power = ('Drug resistant','Halophile','Acidophile','Thermophile','Cryophile','Alkaliphile')
  Value_of_power = {'super_bug':100,'under_dog':0}
  Special_attributes = superpower_menu()  
  if Special_attributes in Super_power:
    score = Value_of_power['super_bug']
  else:
    score = Value_of_power['under_dog']
  if env in Extreme:
    env_score = int(Value_of_Env['extreme'] + score)
  else:
    env_score = int(Value_of_Env['neutral'] + score)
  return env_score

  if __name__ == '__main__': #to make sure that this program doesn't run where it's imported, but only when we call it specifically
    calculate_score_env()
##End of Class
##Total_object = calculate_score_env('env')
##print('Extreme ENV is penalized -10, superpower gives you +100, otherwise 0 if nothing is selected then 0 is assigned, so, ===>>>>', Total_object, 'LETS BATTLE??')
##Does the class work here?
