#! /usr/bin/env python3
import re

def superpower_menu():
    superpower_list = ['Halophile', 'Alkaliphile', 'Acidophile', 'Thermophile', 'Cryophile', 'Drug resistant', 'None :(']
    exit_while = 0
    while exit_while == 0:
        n=1
        print("\nSelect from the following list if your microbe has a super power and hit ENTER:")
        for mic in superpower_list:
            print(f"\t{mic} - PRESS {n}. ")
            n+=1
        print("Your microbe's superpower: ")
        superpower = input()
        try:
            superpower = int(superpower)
            if superpower > 0 and superpower < 8:
                print(f"Your microbe's super power is {superpower_list[superpower-1]}")
                superpower_input = superpower_list[superpower-1]
                found = re.search(r".*\((.*)\)",superpower_input)
                if found:
                    #print(found.group(1))
                    superpower_input=found.group(1)
                exit_while = 1
            else:
	            print("Please select a valid option")
        except ValueError:
            print("Please select a valid option")
    return superpower_input

