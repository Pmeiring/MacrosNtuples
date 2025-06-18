#!/bin/python3
print("Wrapper started")

import argparse
import os
import sys

automation_path = '/afs/cern.ch/work/p/pmeiring/private/CMS/l1tdpg/autoPlotter/MacrosNtuples/automation'

# Set up proxy for accessing remote files with xrootd
os.environ["X509_USER_PROXY"] = sys.argv[1].split(",")[0]
print(os.environ["X509_USER_PROXY"])

# Run command
concatenated_cmd = sys.argv[1].split(",")[1]
concatenated_cmd = concatenated_cmd.replace("___", " ")
concatenated_cmd = f'cd {automation_path}; ' + concatenated_cmd
print('command executed: ' + concatenated_cmd)
os.system(concatenated_cmd)
