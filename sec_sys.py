#!/usr/bin/env python3

def calc_secretion(prg_input,counter=0):
  sec_YES_m = 'You have confirmed that your organism has a type VI secretion system'
  sec_NO_m = 'You have confirmed that your organism does not have a type VI secretion system'
  if prg_input == 'Yes':
    print(f'{sec_YES_m}')
    counter = counter + 5
  else:
    print(f'{sec_NO_m}')
    counter = counter - 5
    
  return(counter)


