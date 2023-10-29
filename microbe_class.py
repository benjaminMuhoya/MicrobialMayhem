#!/usr/bin/env python3

import math
import json
import os

temporal_dict = { }
mibig = { }


class Microbe():

    # define class attributes

    def __init__(self, species, growth_rate, kin_select):

        # baseline attributes, affected by methods.

        self.species = str(species)
        self.growth_rate = int(growth_rate)
        self.kin_select = int(kin_select)

        # calculate impact of kin selection on microbe strength

    # set default value of growth_rate here, add to it with user input in main() by 
    # calling Microbe.growth_rate()

    growth_rate = 1
    attributes = []
    # define class method: microbe strength (based on attributes and species gene content)
    ### ERROR TO TROUBLESHOOT HERE! mibig is not being created and is son getting it
    #mibig = "stromg"
    #print(mibig)
    #temporal_dict = { }
    def Get_database():
        path=os.listdir("./mibig_json/")
        #print(mibig)
        for filename in path:
            with open("./mibig_json/"+filename, "r") as json_file_read:
                json_data = json_file_read.read()
                temporal_dict = json.loads(json_data)
                name = temporal_dict['cluster']['organism_name']
                mibig[name]={ }
                mibig[name]=temporal_dict
        return mibig

    def BGC_content(self):
        BGC_score=0
        mibig = Microbe.Get_database()
        try:
            organism = mibig[self.species]['cluster']['organism_name']
            BGC_score = 0
			#name= f"Microbe fighter name: {mibig[microbe]['cluster']['organism_name']}"
			#BGC_class: f"\tBGC class: {mibig[microbe]['cluster']['biosyn_class'][0]}"
            for compound in mibig[self.species]['cluster']['compounds']:
				#gene = f"\tGene (gear)of microbe: {compound['compound']} +1"
                BGC_score +=1
                try:
                    if compound['chem_acts']:
                        for activity in compound['chem_acts']:
						#print(f"\t\tEnhanced activity: {activity['activity']} +1") 
                            BGC_score+= 1
                except KeyError:
                    continue
        except KeyError:
             print("Please provide a valid microbial fighter species")
        return BGC_score 
				
    
    def strength(self):
        if self.kin_select > 0:
            self.fitness = (self.growth_rate - self.kin_select) * 10
        else:
            self.fitness = self.growth_rate
        attributes = [self.bgc_content, self.growth_rate, self.fitness]
        self.strength = sum(attributes)
        return self.strength
 
microbe1 = Microbe("Mycobacterium tuberculosis H37Rv", 1, 2)
print(microbe1.BGC_content())
#iGC_content(self)
#print(microbe1.BGC_score())
