#!/usr/bin/env python3

def calc_secretion(prg_input,counter=0):
  sec_conf = 'You have confirmed that your organism has a type VI secretion system'
  print(f'{sec_conf}')
  if prg_input == 'YES':
    counter = counter + 5
    
  return(counter)


