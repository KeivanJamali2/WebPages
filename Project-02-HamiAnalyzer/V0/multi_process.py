import subprocess
import time
from pathlib import Path
import os
from dotenv import load_dotenv
load_dotenv()


script = Path(os.environ.get("SCRIPT_FILE"))
executer = Path(os.environ.get("EXECUTOR"))

i_values = [105001, 105002, 105003, 105004, 105005, 105006, 105007, 105008, 105009, 105010,
            105011, 105012, 105013, 105014, 105015, 105016, 105017, 105018, 105019, 105266,
            105335, 105434, 105860, 105949]

name_values = [
    "حامی 001 واحد یزد",
    "حامی 002 واحد یزد",
    "حامی 003 واحد یزد",
    "حامی 004 واحد یزد",
    "حامی 005 واحد یزد",
    "حامی 006 واحد یزد",
    "حامی 007 واحد یزد",
    "حامی 008 واحد یزد",
    "حامی 009 واحد یزد",
    "حامی 010 واحد یزد",
    "حامی 011 واحد یزد",
    "حامی 012 واحد یزد",
    "حامی 013 واحد یزد",
    "حامی 014 واحد یزد",
    "حامی 015 واحد یزد",
    "حامی 016 واحد یزد",
    "حامی 017 واحد یزد",
    "حامی 018 واحد یزد",
    "حامی 019 واحد یزد",
    "sup105266",
    "sup105335",
    "sup105434",
    "sup105860",
    "sup105949"
]
max_concurrent = 1
active_processes = []

for val in i_values:
    # Wait for a free slot
    while len(active_processes) >= max_concurrent:
        # Remove finished processes
        active_processes = [p for p in active_processes if p.poll() is None]
        time.sleep(1)
    print(f"Starting process for i={val}")
    # Start child process with unbuffered stdout (-u)
    name = name_values[i_values.index(val)]  # Get corresponding name for the ID
    p = subprocess.Popen([str(executer), "-u", str(script), str(val), name],)
    active_processes.append(p)
    time.sleep(30)  # stagger start

# Wait for all processes to finish
for p in active_processes:
    p.wait()
