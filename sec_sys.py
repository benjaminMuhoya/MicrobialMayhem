#!/usr/bin/env python3

def calc_secretion(prg_input,counter=0):
  
  if prg_input == 'YES':
    counter = counter + 5
  else:
    counter = counter - 5
    
  return(counter)


