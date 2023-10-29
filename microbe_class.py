#!/usr/bin/env python3

import math

class Microbe(object_input):

    # define class attributes

    def __init__(self, species, bgc_content, growth_rate, kin_select):

        # baseline attributes, affected by methods.

        self.species = str(species)
        self.growth_rate = int(growth_rate)
        self.bgc_content = bgc_content
        self.kin_select = int(kin_select)

        # calculate impact of kin selection on microbe strength

    # set default value of growth_rate here, add to it with user input in main() by 
    # calling Microbe.growth_rate()

    growth_rate = 1

    # define class method: microbe strength (based on attributes and species gene content)
    
    def strength(self):
        if self.kin_select > 0:
            self.fitness = (self.growth_rate - self.kin_select) * 10
        else:
            self.fitness = self.growth_rate
        self.strength = sum(sum(bgc_content.values()), self.growth_rate)
    return self.strength
 


