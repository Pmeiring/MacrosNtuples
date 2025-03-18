#!/bin/python3
import yaml, os
from glob import glob
from utils import htcondor_flag, parse_file, run_command, write_queue, tier0, dqm_prefix

config_file = yaml.safe_load(open('config.yaml', 'r'))

htcondor = htcondor_flag()


for label, config in config_file.items():
    
    #step 1 - find all files on tier 0
    fnames = [glob(f"{tier0}/{era}/{dataset}/NANOAOD/PromptReco-v*/*/*/*/*/*.root") 
              for era in config["eras"] for dataset in config["datasets"]]
    fnames = [item for sublist in fnames for item in sublist]

    #step 2 - remove files that have already been processed
    for file in fnames:
        output_path = dqm_prefix + parse_file(file)
        num_root_files = len(glob(f"{output_path}/*.root"))
        if num_root_files > 0: fnames.remove(file)


    #step 3 - run scripts
    #enumerate over all files
    for i, file in enumerate(fnames):
        if not htcondor and i == 10: break

        print(f"Processing file {file}")

        output_path = dqm_prefix + parse_file(file)

        for cmd in config["scripts"]:
            cmd = cmd.replace("$OUTDIR", output_path)
            cmd = cmd.replace("$INFILE", file)

            os.makedirs(output_path, exist_ok=True)

            if htcondor: write_queue(cmd)
            else: run_command(cmd, output_path + "/log.txt")