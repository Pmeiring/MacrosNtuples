#!/bin/python3

import os, argparse, yaml
from glob import glob
from utils import run_command, write_queue, htcondor_flag, dqm_prefix

# load config
config_dict = yaml.safe_load(open('config.yaml', 'r'))

htcondor = htcondor_flag()

# main logic: glob files merged root files and make plots
for label, config in config_dict.items():
    pattern = os.path.join(dqm_prefix, '**', label,'**', 'merged')
    merged_dirs = glob(pattern, recursive=True)

    for merged_dir in merged_dirs:

        # abort plotting if all .png files are newer than all .root files
        t_newest, t_oldest = 0, 0
        root_files = glob(f"{merged_dir}/*.root")
        png_files = glob(f"{merged_dir}/*/*.png")
        if len(root_files) > 0: t_newest = max(os.path.getctime(f) for f in root_files)
        if len(png_files) > 0: t_oldest = min(os.path.getctime(f) for f in png_files)
        if t_oldest > t_newest: 
            print('skipping: ' + merged_dir)
            continue

        for cmd in config["plotting"]:
            plotdir="MuonJet" if "MuonJet" in cmd else "ZToTauTau" if "ZToTauTau" in cmd else "PhotonJet" if "PhotonJet" in cmd else "ZToEE"
            print(80*"#"+'\n'+f"plotting for {merged_dir}")
            os.makedirs(merged_dir + '/' + plotdir, exist_ok=True)
            os.system('cp /eos/user/p/pmeiring/www/L1Trigger/00_index.php %s/%s/index.php'%(merged_dir,plotdir))
            cmd = cmd.replace("$OUTDIR", merged_dir)
            print(cmd)
            if htcondor: write_queue(cmd) 
            else: run_command(cmd, merged_dir + '/log.txt')
