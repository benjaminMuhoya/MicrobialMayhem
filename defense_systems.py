#!/usr/bin/env python3

import random
import sys
import os

def defense(user_input):
  
  microbe = user_input

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

