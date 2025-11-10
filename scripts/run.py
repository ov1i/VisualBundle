""" This file is a wrapper that helps users run the app """

import subprocess as sp
import os
import sys

python3_exe = "python3"
python_exe = "python"
MAIN_PATH = "main.py"

if os.name == 'nt':
    print("\n\n\tWindows detected\n\n")
    python3_exe = "python3.exe"
    python_exe = "python.exe"
else:
    print("\n\n\tLinux/MacOS detected\n\n")

python_path = os.path.join(".venv", "bin", python3_exe)

if not os.path.exists(python_path):
    python_path = os.path.join(".venv", "Scripts", python_exe)
    if not os.path.exists(python_path):
        print("\n\nError please check you have a virtual enviroment set up\n\n")
        sys.exit(-1)

if not os.path.exists(MAIN_PATH):
    print("\n\nError please check run.py script path\n\n")
    sys.exit(-1)

if os.path.exists(python_path) and os.path.exists(MAIN_PATH):
    command = python_path + " " + MAIN_PATH

    sp.run(command, check=True, shell=True)
else :
    print("\n\nUnknown error\n\n")
    sys.exit(-1)
