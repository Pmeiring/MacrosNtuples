#!/bin/bash

LOCKFILE="cron.lock"
LOGFILE="cron.log"

# Exit if lock file exists
if [ -e "$LOCKFILE" ]; then
    # echo "Lock file exists: another job is running." $(date)
    exit 1
fi

# Define a cleanup function in case of exit
function cleanup() {
    rm -f "$LOCKFILE"
    rm -f "$LOGFILE"
}

# Define a waiting function for condor jobs to finish
function waitForCondor() {
    while true; do
        out=$(condor_q 2>&1)
        echo "$out" | grep -q "Failed to fetch ads" && { echo "[waitForCondor] condor_q failed, retrying..."; sleep 60; continue; }
        echo "$out" | grep -q "$1" || { echo "[waitForCondor] Job $1 finished."; break; }
        sleep 60
    done
}

# Create lock file - cron_job is in running state
touch "$LOCKFILE"
trap cleanup EXIT

# Submit histomaker to condor and wait for jobs to finish
echo "Filling histograms..."
python3 make_hists.py --htcondor
condor_submit submit.txt | tee submitinfo
cluster=$(cat submitinfo | grep "submitted to cluster" | sed "s/.*cluster //; s/\.//")
waitForCondor $cluster

# Merge files locally
echo "Merging files..."
python3 merge_per_run.py
python3 -c 'from utils import generate_weekDict; generate_weekDict()'
cp week_runs.csv /eos/user/p/pmeiring/www/L1Trigger/l1dpg/DQM/Weekly/week_runs.txt
python3 merge_per_era.py
python3 merge_total.py

# Submit plotmaker to condor and wait for jobs to finish
echo "Producing plots..."
python3 make_plots.py --htcondor
condor_submit submit.txt | tee submitinfo
cluster=$(cat submitinfo | grep "submitted to cluster" | sed "s/.*cluster //; s/\.//")
waitForCondor $cluster

date
echo "All done!"