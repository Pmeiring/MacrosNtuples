# Parse arguments
DATASET=$1; shift
ERA=$1; shift

# Check if a valid proxy exists (at least 1 hour remaining)
if voms-proxy-info --exists --valid 1:00 > /dev/null 2>&1; then
    echo "Active proxy found with sufficient validity."
else
    echo "No active proxy found or proxy expired. Activating..."
    echo "dummypwd" | voms-proxy-init --voms cms
    export X509_USER_PROXY=/afs/cern.ch/user/p/pmeiring/x509up_u111185
    echo "dummypwd" | voms-proxy-init --voms cms --valid 144:0
fi

# Query DAS to obtain a list of datasets
rm -f files_das.txt
cmd="/cvmfs/cms.cern.ch/common/dasgoclient -query='dataset=/${DATASET}/${ERA}-PromptReco-v*/NANOAOD'"
dgc_datasets=$(eval "$cmd")

# Query again to obtain all files, and put them in a list
for dataset in $dgc_datasets; do
    echo "Processing dataset: $dataset"
    cmd="/cvmfs/cms.cern.ch/common/dasgoclient -query='file dataset=$dataset'"
    # dgc_files=$(eval "$cmd"); echo $dgc_files >> files_das.txt
    eval "$cmd" | while read -r file; do
    	echo "root://xrootd-cms.infn.it/$file" >> files_das.txt
	done
done