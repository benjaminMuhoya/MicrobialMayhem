#! /usr/bin/env python3
import re

def env_menu():
    env_list = ['Salty', 'Alkaline', 'Hot', 'Cold', 'Acidic', 'In the presence of antibiotics']
    exit_while = 0
    while exit_while == 0:
        n=1
        print("Select an environment where you want to fight from the following list and hit ENTER:")
        for mic in env_list:
            print(f"\t{mic} - PRESS {n}. ")
            n+=1
        print("Your environment: ")
        environment = input()
        try:
            environment = int(environment)
            if environment > 0 and environment < 7:
                print(f"Your environment is {env_list[environment-1]}")
                env_input = env_list[environment-1]
                found = re.search(r".*\((.*)\)",env_input)
                if found:
                    #print(found.group(1))
                    env_input=found.group(1)
                exit_while = 1
            else:
	            print("Please select a valid option")
        except ValueError:
            print("Please select a valid option")
    return env_input

