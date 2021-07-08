import subprocess
from pathlib import Path
from natsort import os_sorted

paths = os_sorted([Path(x) for x in Path('.').glob("./tests/t*.sn")])
for p in paths:
    print()
    print('Testing', p)
    serene_completed_process = subprocess.run(['python', 'serene', p, '-o', './temp/generated.cc'], stdout=subprocess.DEVNULL)
    if serene_completed_process.returncode == 0:
        print('> Success! Compiling to C++')
        gcc_completed_process = subprocess.run(['g++', './temp/generated.cc', '-o', './temp/compiled'])
        if gcc_completed_process.returncode == 0:
            print('> Success again!')
        else:
            print('> Failed with error code', gcc_completed_process.returncode)
    else:
        print('> Failed with error code', serene_completed_process.returncode)
