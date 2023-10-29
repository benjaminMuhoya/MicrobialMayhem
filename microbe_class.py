#!/usr/bin/env python3

import math
import json
import os
import random

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
        if self.species == "E.coli":
            species = "Escherichia coli"
        if self.species == "M.tuberculosis":
            species = "Mycobacterium tuberculosis H37Rv"
        if self.species == "V.maris":
            species = "Verrucosispora maris AB-18-032"
        if self.species == "M.alcalica":
            species = "Methylophaga alcalica"
        if self.species == "S.aureus":
            species = "Staphylococcus aureus"
        if self.species == "V.neptunius":
            species = "Vibrio neptunius"
        if self.species == "P.fluorescens":
            species = "Pseudomonas fluorescens"
        if self.species == "K.pneumoniae":
            species = "Klebsiella pneumoniae"
        try:
            organism = mibig[species]['cluster']['organism_name']
            BGC_score = 0
			#name= f"Microbe fighter name: {mibig[microbe]['cluster']['organism_name']}"
			#BGC_class: f"\tBGC class: {mibig[microbe]['cluster']['biosyn_class'][0]}"
            for compound in mibig[species]['cluster']['compounds']:
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
        return float(BGC_score) 

    def defense(self):

        microbe = self.species

        #define the input and output files path
        in_directory = './defense_files_input'
        out_directory = './defense_files_output'

        #initialize defense system scores dictionary 
        defense_scores_dict = {}

        #iterate through files in directory
        for file in os.listdir(in_directory):

            #open each file and read, open new file to write 
            with open(f'{in_directory}/{file}', 'r') as file_in, open(f'{out_directory}/{file}', 'w') as file_out:
                for line in file_in:
                    line = line.rstrip()
                    line_list = line.split(',')

                    #check if line has various defense systems, if it does, write to file_out
                    if line_list[2].startswith("CRISPR"):
                        file_out.write(f'{line_list[2]}\t')
                    if line_list[2].startswith("CBASS"):
                        file_out.write(f'{line_list[2]}\t')
                    if line_list[2].startswith("Abi"):
                        file_out.write(f'{line_list[2]}\t')
                    if line_list[2].startswith("Argo"):
                        file_out.write(f'{line_list[2]}\t')
                    if line_list[2].startswith("RM"):
                        file_out.write(f'{line_list[2]}\t')
                    else:
                        continue

        #iterate through files with defense systems and read
        for file in os.listdir(out_directory):

            #open each file with defense systems and read to count the number of defense sys.
            with open(f'{out_directory}/{file}', 'r') as file_in:
                for line in file_in:
                    line = line.rstrip()
                    line_list = line.split('\t')
                    defense_score = len(line_list)
                    defense_scores_dict[file] = defense_score

                #remove output files from directory
                os.remove(f'{out_directory}/{file}')

        #extract user inputted microbe's defense score
        defense_score = float(defense_scores_dict[microbe])
        return defense_score
    
    def strength(self):
        if self.kin_select > 5:
            fitness = float((self.growth_rate - 0.5) * 4)
        else:
            fitness = float(self.growth_rate - 0.5)
        #print(fitness)
        scores_list = [self.BGC_content(), self.defense(), fitness]
        score = sum(scores_list)
        return score

microbe1 = Microbe('K.pneumoniae', 3, 2)
#print(microbe1.BGC_content())
#print(microbe1.defense())
print(microbe1.strength())
