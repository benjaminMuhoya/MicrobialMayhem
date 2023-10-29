#! /usr/bin/env python3
import json
import sys
import os

## This is a JSON file parser from file downladed from MiBig database
# The datastructure from JSON file looks as a dictionary of dictionaries


#json_file = "BGC0000022.json"
#Create a dictionary from the json file
#Create a dictionary of dictionaries with multiple json files that have been download from one species (multiple BGC). Use name of the species as parental key of dictionary
mibig = { }
temporal_dict = { }


def Get_database():
	path=os.listdir("./mibig_json/")
	#print(path) #sanity check	
		#read the json file
	for filename in path:
		with open("./mibig_json/"+filename, "r") as json_file_read:
			json_data = json_file_read.read()
			temporal_dict = json.loads(json_data)
			species = temporal_dict['cluster']['organism_name']
			#print(f"This is species: {species}") #sanity check
			mibig[species]={ }
			mibig[species]=temporal_dict
	return mibig


def BGC_content(microbe):
	BGC_score=0
	try:
		organism = mibig[microbe]['cluster']['organism_name']
		#create a variable to save the score of microbe
		BGC_score = 0
		#for species in mibig:
		#BGC_score = 0
		#changelog isone of the parental keys but doesnt have important info
		#cluster is they key of the info we really want
		print(f"Microbe fighter name: {mibig[microbe]['cluster']['organism_name']}")
		print(f"\tBGC class: {mibig[microbe]['cluster']['biosyn_class'][0]}")

		#since they could have more than one compound made by the cluster
		#create loop in the list "compounds"
		for compound in mibig[microbe]['cluster']['compounds']:
			print(f"\tGene (gear)of microbe: {compound['compound']} +1")
			BGC_score +=1
			#Noticed that not all json files in the database have a description
			#Additional description could make the microbe stronger
			try:
				if compound['chem_acts']:
					for activity in compound['chem_acts']:
						print(f"\t\tEnhanced activity: {activity['activity'    ]} +1")
						BGC_score+= 1
			except KeyError:
				continue
		print(f"Score: {BGC_score}")
	except KeyError:
		print("Please provide a valid microbial fighter species")
	return BGC_score

try:
	microbe = sys.argv[1]
	print(f"user provided microbe: {microbe}")
	mibig = Get_database()
	BGC_content(microbe)

	#Will store the entire database in final json file
	with open("mibig_database.json","w") as file_out:
		json.dump(mibig,file_out)
except IndexError:
    print("Please provide a microbe fighter")

