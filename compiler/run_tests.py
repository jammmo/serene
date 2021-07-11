import subprocess
from pathlib import Path
from natsort import os_sorted
from colorama import Fore, Style, init as init_colorama

# Directory of this file ( /serene/compiler/ )
here = Path(__file__).parent.resolve()

init_colorama()

paths = os_sorted([Path(x) for x in here.glob("./tests/t*.sn")])
for p in paths:
    print()
    print('Testing', p.name, 'now...')
    serene_completed_process = subprocess.run(['python', 'serene', p, '-o', './temp/test_compiled'], cwd=here, capture_output=True, text=True)
    if serene_completed_process.returncode == 0:
        print(f"{Fore.GREEN}> Success!{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}{serene_completed_process.stderr}{Style.RESET_ALL}")
        print(f"{Fore.RED}{Style.BRIGHT}> Failed with error code {serene_completed_process.returncode}.{Style.RESET_ALL}")
