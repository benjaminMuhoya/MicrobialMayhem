#!/usr/bin/env python3

import random

## Definition of microbe class

class Microbe(object_input):

    # define class attributes
    
    def __init__(self, name, bgc_content, kin_selection):
        
        # baseline attributes, affected by methods.

        self.name = name
        self.growth_rate = 1
        self.bgc_content = bgc_content 
        # dict(bgc_content) = {'gene1' : 0 (absence), 'gene2' : 1 (presence)}
        self.kin_select = int(kin_selection)
        self.colony_size = int(colony_size) * (0.5 * self.kin_select)
        
        # calculate impact of kin selection on microbe strength
        

    # define class method: microbe strength (based on attributes and species gene content)
    # consider removing strength function from class

    def compete(self):
        if self.kin_select > 0:
            self.compete = (self.growth_rate - self.kin_select) * 10
        else:
            self.compete = self.growth_rate
        self.compete = sum(sum(bgc_content.values)(), self.growth_rate)
        return self.compete

# create battle function

def battle(microbe1, microbe2):
    if microbe1.compete > microbe2.compete:
        return microbe1
    elif microbe2.compete > microbe1.compete:
        return microbe2
    else:
        return random.choice([microbe1, microbe2])

def main():

    # create microbe options with features

    species1 = Microbe('Species', bgc_content, kin_selection = 0)
    species2 = Microbe('Species', bgc_content, kin_selection = 1)

    # get user input for microbe 

    print("Choose two microbes to battle!")
    print("Option 1: [sp name]")
    print("Option 2: [sp name]")

    choice1 = int(input("Choose first microbe (enter number): "))
    choice2 = int(input("Choose second microbe (enter number): "))

    if choice1 == 1:
        m1 = ____
    else:
        m1 = ____

    if choice2 == 1:
        m2 = ____
    else:
        m2 = ____

    # get user input for colony size

    ## note: try to make prettier with a function. (ideally, would use colony size for kin selection value)
    cfu1 = int(input('How big is you colony 1? Choose a number between 0 and 1000')
    cfu2 = int(input('How big is colony 2? Choose a number between 0 and 1000')

    # get user input for environment variable

    print("Choose an environment type:")
    print("Options: Alkaline, Hot, Cold, Acidic, Salty, Temperate")

    env = input("Pick one of the above. Where do you want to fight?!")

    def calc_env_impact():
        ___________

    sp1_strength = sum(int(species1.compete(), cfu1, ___, ___))
    sp2_strength = sum(int(species2.compete(), cfu2, ___, ___))

    # commence battle

    winner = battle(sp1_strength, sp2_strength)
    print(f'The winner is {winner.name}!')


if __name__ == "__main__":
    main()
           
            
        
