#!/usr/bin/env python3

import math
import json
import os

class Microbe(object_input):
	mibig = { }
	temporal_dict = { }
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
	mibig = Get_database()
	BGC_content(self.species)

	def Get_database():
		path=os.listdir("./mibig_json/")
		for filename in path:
			with open("./mibig_json/"+filename, "r") as json_file_read:
				json_data = json_file_read.read()
				temporal_dict = json.loads(json_data)
				species = temporal_dict['cluster']['organism_name']
				mibig[species]={ }
				mibig[species]=temporal_dict
		return mibig

	def BGC_content(self.species):
		BGC_score=0
		try:
			organism = mibig[microbe]['cluster']['organism_name']
			BGC_score = 0
			#name= f"Microbe fighter name: {mibig[microbe]['cluster']['organism_name']}"
			#BGC_class: f"\tBGC class: {mibig[microbe]['cluster']['biosyn_class'][0]}"
			for compound in mibig[microbe]['cluster']['compounds']:
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
        self.strength = sum(sum(bgc_content.values()), self.growth_rate)
    return self.strength
 


