#!/bin/python3

import argparse
import os

repository = '/afs/cern.ch/user/l/lebeling/MacrosNtuples'

# parse commands to be executed as arguments
parser = argparse.ArgumentParser(description="wrapper running script on htcondor")
parser.add_argument('cmd', nargs='+', type=str, help='commands to be executed')
args = parser.parse_args()

concatenated_cmd = ' '.join(args.cmd)
concatenated_cmd = concatenated_cmd.replace("___", " ")
concatenated_cmd = f'cd {repository}/automation; ' + concatenated_cmd

print('command executed: ' + concatenated_cmd)
os.system(concatenated_cmd)
