#!/usr/bin/env python3

#this script is so user inputs do not break our code
#we need make functions for each type of input: yes/no, integer, and writing string

#this is a yes/no input function
def yes_no_input(user_input):
  user_input = user_input.strip()
  if user_input in ['Y','Yes','yes','y']:
    fxn_out = 'YES'
  else:
    fxn_out = 'NO'
  return(fxn_out)

