#!/bin/bash
cd /afs/cern.ch/work/p/pmeiring/private/CMS/l1tdpg/CMSSW_15_0_0/src
cmsenv 
cd /afs/cern.ch/work/p/pmeiring/private/CMS/l1tdpg/MacrosNtuples/l1macros

#python3 performances_nano.py --max_events -1 -i $1 -o $2 -c $3
#python3 performances_nano.py --max_events -1 -i $1 -o $2 -c $3 -g Cert_Collisions2022_eraB_366403_367079_Golden.json
if [ -z "$4" ]
then
    python3 performances_nano.py --max_events -1 -i $1 -o $2 -c $3
else
    python3 performances_nano.py --max_events -1 -i $1 -o $2 -c $3 -g $4
fi

