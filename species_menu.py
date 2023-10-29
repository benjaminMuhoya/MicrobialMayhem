#! /usr/bin/env python3
import re

def species_menu():
    species_list = ['Escherichia coli (E.coli)', 'Mycobacterium tuberculosis(M.tuberculosis)', 'Verrucosispora maris (V.maris)', 'Methylophaga alcalica (M.alcalica)', 'Staphylococcus aureus (S.aureus)', 'Vibrio neptunius (V.neptunius)','Pseudomonas fluorescens (P.fluorescens)', 'Klebsiella pneumoniae (K.pneumoniae)']
    exit_while = 0
    while exit_while == 0:
        n=1
        print("Select a microbe fighter from the following list and hit ENTER:")
        for mic in species_list:
            print(f"\t{mic} - PRESS {n}. ")
            n+=1
        print("Your fighter: ")
        species = input()
        try:
            species = int(species)
            if species > 0 and species < 9:
                print(f"Your fighter is {species_list[species-1]}")
                species_input = species_list[species-1]
                found = re.search(r".*\((.*)\)",species_input)
                if found:
                    #print(found.group(1))
                    species_input=found.group(1)
                exit_while = 1
            else:
	            print("Please select a valid option")
        except ValueError:
            print("Please select a valid option")
    return species_input

#species_menu()
