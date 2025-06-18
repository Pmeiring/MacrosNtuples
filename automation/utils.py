import os, subprocess, argparse, uproot, re, csv
import pandas as pd
from datetime import datetime
from collections import defaultdict

#dqm_prefix = '/eos/cms/store/group/dpg_trigger/comm_trigger/L1Trigger/cmsl1dpg/www/DQM/T0PromptNanoMonit'
dqm_prefix = "/eos/user/p/pmeiring/www/L1Trigger/l1dpg/DQM"
tier0 = "/eos/cms/tier0/store/data"


def run_command(cmd, log_file = "log.txt"):
    with open(log_file, "a") as f:
        subprocess.run(cmd, shell=True, stdout=f, stderr=f) 


def parse_file(fname):
        dataset = fname.split("/")[7]
        run = int("".join(fname.split("/")[11:13]))
        base_fname = fname.split("/")[-1].replace(".root","")
        era = fname.split("/")[6]
        reco_version = fname.split("/")[9]

        year = ''.join([char for char in era if char.isdigit()])
        label = ''.join([char for char in dataset if not char.isdigit()])
        
        #return f"{year}/{label}/{era}/{run}/{base_fname}"
        return f"/{label}/{era}/{dataset}/{reco_version}/{run}/{base_fname}"


def write_queue(script, infile = "", outdir = ""):
    cmd = script.replace("$INFILE", infile).replace("$OUTDIR", outdir)
    cmd = cmd.replace(" ", "___")
    with open("queue.txt", "a") as f:
        f.write(cmd + "\n")


# return weeks as dict with runnum as key -> weeks[runx] = 42
def get_weeks(year=2024):
    oms_path = f"/eos/cms/store/group/tsg/STEAM/OMSRateNtuple/{year}/physics.root"
    with uproot.open(oms_path) as f:
        df = f["tree"].arrays(
            filter_name = ['run', 'year', 'month', 'day'],
            library = "pd"
        )
    df['date'] = pd.to_datetime(df[['year', 'month', 'day']])
    df['week'] = df['date'].dt.isocalendar().week

    min_run = df.groupby('week')['run'].min()
    max_run = df.groupby('week')['run'].max()
    
    weeks = {}
    for _, row in df.iterrows():
        w = row['week']
        r = row['run']
        min_r = min_run[w]
        max_r = max_run[w]
        weeks[r] = f'Week{w}_{min_r}-{max_r}'

    return weeks

def get_weeks_v2(csv_path="run_weeks.csv"):
    run_week_dict = {}
    try:
        with open(csv_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    run = int(row["RunNumber"])
                    full_week = row["ISO_Week"]
                    # Extract just the week number (e.g., '2025-W22' -> '22')
                    week_only = full_week.split("-W")[1]
                    run_week_dict[run] = week_only
                except (ValueError, KeyError, IndexError):
                    continue  # Skip malformed rows
    except FileNotFoundError:
        print(f"File not found: {csv_path}")
    except Exception as e:
        print(f"Error reading CSV: {e}")

    return run_week_dict

def generate_weekDict(year=2025):
    run_week_dict = {}
    week_run_dict = defaultdict(list)

    for era in os.listdir(tier0):
        if not era.startswith(f"Run{year}"):
            continue

        era_path = os.path.join(tier0, era, "L1Accept/RAW/v1/000/")
        if not os.path.isdir(era_path):
            continue

        for root, dirs, files in os.walk(era_path):
            if not root.endswith("/00000"):
                continue

            match = re.search(r"/(\d{3})/(\d{3})/00000$", root)
            if not match:
                continue

            run_number = int(match.group(1) + match.group(2))

            # Get parent directory of "00000", i.e., the run directory
            run_dir = os.path.dirname(root)

            try:
                dir_stat = os.stat(run_dir)
                # Use st_mtime (last modification time) or st_ctime (creation time on some systems)
                timestamp = dir_stat.st_mtime
                dt = datetime.fromtimestamp(timestamp)
                iso_week = dt.strftime("%G-W%V")
                run_week_dict[run_number] = iso_week
                week_run_dict[iso_week].append(run_number)
            except Exception:
                continue  # Skip if stats can't be read

    with open("run_weeks.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["RunNumber", "ISO_Week"])
        for run, week in sorted(run_week_dict.items()):
            writer.writerow([run, week])

    with open("week_runs.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ISO_Week", "RunNumbers"])
        for week, runs in sorted(week_run_dict.items()):
            run_list_str = " ".join(str(r) for r in sorted(runs))
            writer.writerow([week, run_list_str])


def hadd(target, files, htcondor = False):
    os.makedirs(os.path.dirname(target), exist_ok=True)

    # abort if merged file already exists, and it is newer than all base files
    if os.path.exists(target):
        target_time = os.path.getctime(target)
        files_time = max([os.path.getctime(file) for file in files])
        if target_time > files_time:
            print(f"skipping {target} - newer than all base files")
            return

    print(f"Hadding files with target {target}")
    cmd = f'hadd -f {target} ' + ' '.join(files)
    if htcondor: write_queue(cmd)
    else: run_command(cmd, os.path.dirname(target)+"/log.txt")


def htcondor_flag():
    parser = argparse.ArgumentParser()
    parser.add_argument('--htcondor', action='store_true', help='run on ht condor')
    args = parser.parse_args()
    if args.htcondor: os.system('rm -rf queue.txt')
    return args.htcondor


def clean(files):
    return  [file for file in files if os.path.getsize(file) >= 1600]
